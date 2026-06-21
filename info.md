# Alpicool / ICECO Fridge (BLE)

Native Home Assistant Integration für Alpicool/ICECO/BougeRV-kompatible
Kompressor-Kühlboxen über Bluetooth LE – **kein zusätzlicher ESP32 oder
MQTT-Gateway nötig**.

Erkennt Geräte automatisch per Bluetooth-Discovery (Namenspräfix `A1-`,
`AK1-`, `AK2-`, `AK3-` oder `WT-`).

## Features

- 🌡️ Zieltemperatur setzen (-20 °C bis 20 °C)
- 🔌 Ein/Aus
- 🌿 Eco-Modus als Preset
- ⚡ Versorgungsspannung als Sensor
- 🔒 Tastensperre als Binary Sensor

## Voraussetzung

Ein Bluetooth-Adapter oder ESPHome-Bluetooth-Proxy in HA-Reichweite des
Kühlschranks. Der Kühlschrank darf nicht gleichzeitig in der Hersteller-App
verbunden sein (nur eine BLE-Verbindung gleichzeitig möglich).

Ausführliche Doku siehe [README](README.md).
