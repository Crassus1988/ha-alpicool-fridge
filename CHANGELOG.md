# Changelog

Alle nennenswerten Änderungen an dieser Integration werden hier dokumentiert.

## [0.3.1] - 2026-06-21

### Fixed
- `hacs.json` enthielt `zip_release`/`filename` – das sind Plugin/Theme-Keys, die
  bei einer Integration die HACS-Strukturvalidierung scheitern lassen ("Repository
  structure for vX.X.X is not compliant"). Auf die für Integrationen gültigen Keys
  reduziert (`name`, `render_readme`, `homeassistant`).

## [0.3.0] - 2026-06-20

### Added
- HACS-Unterstützung: `hacs.json`, `info.md`, `LICENSE` (MIT)
- Integration-Icon/Logo (`icon.png`, `logo.png`) für HACS-Store-Anzeige
- mdi-Icons für Entities (`mdi:fridge-outline` für climate, `mdi:current-dc` für
  den Spannungssensor)
- README um HACS-Installationsanleitung und Badges ergänzt

## [0.2.0] - 2026-06-20

### Fixed
- Setup brach ab ("Einrichtung wird nicht abgeschlossen"), weil beim allerersten
  Config-Entry-Refresh sofort geprüft wurde, ob schon ein Status-Report vorliegt –
  der kommt aber erst kurz nach dem Connect/Ping per Notification rein. Jetzt wird
  bis zu 15s auf die erste Notification gewartet, bevor ein Fehler geworfen wird.
- Beim Reconnect wird der "erste Report"-Status zurückgesetzt, damit nicht
  versehentlich auf einen veralteten Report von vor dem Disconnect zugegriffen wird.

### Added
- `WT-*` als zusätzliches BLE-Namenspräfix für Bluetooth-Discovery
  (manche Alpicool-kompatiblen Geräte nutzen "WT-XXXX" statt "A1-"/"AK-").

### Verified
- GATT-UUIDs (`00001234`/`00001235`/`00001236`) gegen die offizielle
  "Car Fridge Freezer" Android-APK (v2.3.5) abgeglichen – stimmen exakt mit
  unserer Implementierung überein.

## [0.1.0] - 2026-06-20

### Added
- Initiales Release: native BLE-Integration für Alpicool/ICECO-kompatible
  Kühlboxen, portiert aus dem Protokoll von jakub-hajek/alpicool-esp32-mqtt.
- `climate`-Entity (On/Off, Zieltemperatur, Eco-Preset)
- `sensor`-Entity für Versorgungsspannung
- `binary_sensor`-Entity für Tastensperre
- Automatische Bluetooth-Discovery (Namenspräfixe `A1-`, `AK1-`, `AK2-`, `AK3-`)
