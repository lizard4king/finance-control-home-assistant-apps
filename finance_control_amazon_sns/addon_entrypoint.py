"""Home Assistant add-on supervisor for the loopback Amazon SNS receiver."""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import threading

from finance_control.amazon_sns_inbox import AmazonSnsInbox
from finance_control.amazon_sns_server import make_server
from finance_control.amazon_sns import SNS_TOPIC_ARN_PATTERN as TOPIC_ARN


OPTIONS_PATH = Path("/data/options.json")
OPTIONS_LIMIT = 8 * 1024
DATABASE_PATH = Path("/data/amazon-sns/inbox.sqlite")
DISCOVERED_TOPICS_PATH = Path("/config/discovered-topic-arns.json")


def _read_options() -> tuple[str | None, int, bool]:
    try:
        with OPTIONS_PATH.open("rb") as stream:
            raw = stream.read(OPTIONS_LIMIT + 1)
        if len(raw) > OPTIONS_LIMIT:
            raise ValueError
        options = json.loads(raw.decode("utf-8"))
        if not isinstance(options, dict) or set(options) not in (
            {"topic_arn", "max_messages"},
            {"topic_arn", "max_messages", "bootstrap_only"},
        ):
            raise ValueError
        topic = options["topic_arn"]
        maximum = options["max_messages"]
        requested_bootstrap = options.get("bootstrap_only", topic == "")
        if type(requested_bootstrap) is not bool or not isinstance(topic, str):
            raise ValueError
        if topic:
            if not TOPIC_ARN.fullmatch(topic):
                raise ValueError
            configured_topic = topic
            bootstrap_only = False
        else:
            if not requested_bootstrap:
                raise ValueError
            configured_topic = None
            bootstrap_only = True
        if type(maximum) is not int or not 1 <= maximum <= 10_000:
            raise ValueError
        return configured_topic, maximum, bootstrap_only
    except Exception:
        raise ValueError("invalid options") from None


def run() -> int:
    try:
        topic_arn, max_messages, bootstrap_only = _read_options()
    except ValueError:
        print("Add-on-Konfiguration ungültig; Start verweigert.", flush=True)
        return 2

    os.umask(0o077)
    inbox = None
    server = None
    nginx = None
    server_thread = None
    stopping = threading.Event()
    def request_stop(_signum, _frame) -> None:
        stopping.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        inbox = AmazonSnsInbox(DATABASE_PATH, max_messages=max_messages)
        server = make_server(
            inbox,
            expected_topic_arn=topic_arn,
            bootstrap_only=bootstrap_only,
            discovered_topics_path=DISCOVERED_TOPICS_PATH if bootstrap_only else None,
            port=8787,
        )
        server_thread = threading.Thread(target=server.serve_forever, name="sns-loopback", daemon=True)
        server_thread.start()

        nginx = subprocess.Popen(["nginx", "-g", "daemon off;"])

        mode = "Bootstrap" if bootstrap_only else "Normalbetrieb"
        print(f"Amazon SNS-Empfang gestartet ({mode}).", flush=True)
        while not stopping.wait(0.25):
            if nginx.poll() is not None or not server_thread.is_alive():
                raise RuntimeError("receiver stopped")
        return 0
    except Exception:
        print("Amazon SNS-Empfang konnte nicht gestartet werden.", flush=True)
        return 1
    finally:
        if nginx is not None and nginx.poll() is None:
            nginx.terminate()
            try:
                nginx.wait(timeout=5)
            except subprocess.TimeoutExpired:
                nginx.kill()
                nginx.wait(timeout=5)
        if server is not None and server_thread is not None and server_thread.is_alive():
            server.shutdown()
            server_thread.join(timeout=6)
        if server is not None:
            server.server_close()
        if inbox is not None:
            inbox.close()


if __name__ == "__main__":
    raise SystemExit(run())
