# Finance Control Amazon SNS für Home Assistant

Diese lokale App empfängt signierte Amazon-SNS-Meldungen. Python hört ausschließlich
auf `127.0.0.1:8787`; NGINX nimmt intern auf Port `8788` nur `POST /amazon/sns` an.
Eine bestehende Cloudflared-App kann bei Installation aus dem veröffentlichten
Repository an `b835283c-finance-control-amazon-sns:8788` weiterleiten. Nur bei
einer lokalen Installation lautet der Hostname `local-finance-control-amazon-sns`.
Nach einer Neuinstallation den tatsächlichen Hostnamen in den
Supervisor-Informationen prüfen, weil das Repository-Präfix abweichen kann.
Es gibt keinen freigegebenen Host-Port, keine Home-Assistant-API-Rechte
und keinen Zugriff auf die Finanzdatenbank.

Die Optionen sind `topic_arn`, `max_messages` (1 bis 10.000) und `bootstrap_only`.
Vor Bekanntgabe der ARN läuft die App mit leerem `topic_arn` und
`bootstrap_only: true`. Sie akzeptiert dann ausschließlich signierte
`SubscriptionConfirmation`-Nachrichten und schreibt deren ARN nach
`/config/discovered-topic-arns.json`. Die Liste enthält weder Token noch URL.
Danach die ausgewählte ARN eintragen und `bootstrap_only: false` setzen. Eine
fehlende oder ungültige ARN verhindert im Normalbetrieb den Start. Zugangsdaten
gehören nicht in die Optionen.
Bei einer Aktualisierung von Version 1.0.0 wird der Modus einmalig aus der
vorhandenen ARN abgeleitet: leer bedeutet Bootstrap, gesetzt bedeutet Normalbetrieb.
Eine gültige ARN erzwingt auch dann den Normalbetrieb, wenn Home Assistant beim
Upgrade zunächst den neuen Bootstrap-Standardwert ergänzt.

Die aktive Inbox liegt unter `/data/amazon-sns/inbox.sqlite`. Manuelle SQLite-
Snapshots können in das eigene `/config` geschrieben werden. Die App schließt mit
`backup_exclude: ["*"]` sämtliche Inhalte ihrer Daten- und Konfigurationsverzeichnisse
von App-Sicherungen aus. Die Supervisor-Metadaten enthalten weiter die Optionen;
deshalb werden dort ausschließlich Topic, Modus und Kapazität gespeichert. Eine
unabhängig konfigurierte Sicherung des gesamten `addon_configs`-Ordners ist hiervon
nicht geschützt.
Inbox und Snapshots enthalten Subscription-Token und bleiben außerhalb von Git und Drive.

Das ZIP entsteht mit `python scripts/build_amazon_sns_addon.py --output-dir
<Ordner-außerhalb-von-Git>`. Der Ordner muss außerhalb von Git liegen; vorhandene
ZIPs werden nicht ersetzt. Das Paket enthält ausschließlich diese Vorlage und
versionierte, erlaubte Quellcodedateien. Neue Module müssen zuvor gezielt mit
`git add` aufgenommen werden. Installation und privater Transfer stehen in
`docs/amazon-sns-home-assistant.md` im Finance-Control-Repository.
