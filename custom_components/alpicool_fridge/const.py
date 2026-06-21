"""Constants for the Alpicool Fridge integration."""
from __future__ import annotations

DOMAIN = "alpicool_fridge"

SERVICE_UUID = "00001234-0000-1000-8000-00805f9b34fb"
CHAR_WRITE_UUID = "00001235-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY_UUID = "00001236-0000-1000-8000-00805f9b34fb"

# How often we (re)send a ping so the fridge keeps the BLE link alive.
PING_INTERVAL = 2.0  # seconds
# How often we poll/refresh state in HA if no notification has arrived.
UPDATE_INTERVAL = 15  # seconds

MIN_TEMP = -20
MAX_TEMP = 20

NAME_PREFIXES = ("A1-", "AK1-", "AK2-", "AK3-", "WT-")
