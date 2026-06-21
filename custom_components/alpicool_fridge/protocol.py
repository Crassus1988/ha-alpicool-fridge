"""Alpicool/ICECO BLE wire protocol.

Ported 1:1 from the C++ structs in jakub-hajek/alpicool-esp32-mqtt
(src/devices/fridge.h), which in turn are based on johnelliott/alpicoold
and klightspeed's protocol reverse engineering.

Frame layout (all multi-byte values little-endian, EXCEPT the trailing
checksum which is sent big-endian):

    [Preamble 0xFEFE (2B)] [DataLen (1B)] [CommandCode (1B)]
    [Payload (depends on command)] [Checksum (2B, big-endian)]

Checksum = (sum of every preceding byte in the frame) & 0xFFFF
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

PREAMBLE = 0xFEFE

CMD_STATUS_REPORT = 0x01
CMD_SET_STATE = 0x02
CMD_SET_TEMP = 0x05

DATALEN_SET_TEMP = 0x04
DATALEN_SET_STATE = 0x11

PING_MESSAGE = bytes([0xFE, 0xFE, 0x03, 0x01, 0x02, 0x00])

# struct format for the 14-byte "Settings" block (packed, no padding)
# Locked, On, EcoMode: bool (1B each)
# HLvl, TempSet, HighestTempSettingE2, LowestTempSettingE1,
# HysteresisE3, SoftStartDelayMinE4: int8 (1B each)
# CelsiusFahrenheitModeE5: bool (1B)
# TempCompGTEMinus6E6, TempCompGTEMinus12LTMinus6E7,
# TempCompLTMinus12E8, TempCompShutdownE9: int8 (1B each)
_SETTINGS_FMT = "<3b6b1b4b"  # 14 signed bytes total (bools packed as 0/1)
_SETTINGS_SIZE = struct.calcsize(_SETTINGS_FMT)

_SENSORS_FMT = "<4b"  # Temp, UB17, InputV1, InputV2
_SENSORS_SIZE = struct.calcsize(_SENSORS_FMT)


@dataclass
class Settings:
    locked: bool
    on: bool
    eco_mode: bool
    h_lvl: int
    temp_set: int
    highest_temp_e2: int
    lowest_temp_e1: int
    hysteresis_e3: int
    soft_start_delay_e4: int
    celsius_mode_e5: bool
    temp_comp_e6: int
    temp_comp_e7: int
    temp_comp_e8: int
    temp_comp_e9: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "Settings":
        vals = struct.unpack(_SETTINGS_FMT, data[:_SETTINGS_SIZE])
        return cls(
            locked=bool(vals[0]),
            on=bool(vals[1]),
            eco_mode=bool(vals[2]),
            h_lvl=vals[3],
            temp_set=vals[4],
            highest_temp_e2=vals[5],
            lowest_temp_e1=vals[6],
            hysteresis_e3=vals[7],
            soft_start_delay_e4=vals[8],
            celsius_mode_e5=bool(vals[9]),
            temp_comp_e6=vals[10],
            temp_comp_e7=vals[11],
            temp_comp_e8=vals[12],
            temp_comp_e9=vals[13],
        )

    def to_bytes(self) -> bytes:
        return struct.pack(
            _SETTINGS_FMT,
            int(self.locked),
            int(self.on),
            int(self.eco_mode),
            self.h_lvl,
            self.temp_set,
            self.highest_temp_e2,
            self.lowest_temp_e1,
            self.hysteresis_e3,
            self.soft_start_delay_e4,
            int(self.celsius_mode_e5),
            self.temp_comp_e6,
            self.temp_comp_e7,
            self.temp_comp_e8,
            self.temp_comp_e9,
        )


@dataclass
class Sensors:
    temp: int
    ub17: int
    input_v1: int
    input_v2: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "Sensors":
        vals = struct.unpack(_SENSORS_FMT, data[:_SENSORS_SIZE])
        return cls(temp=vals[0], ub17=vals[1], input_v1=vals[2], input_v2=vals[3])


@dataclass
class StatusReport:
    settings: Settings
    sensors: Sensors

    @property
    def actual_temperature(self) -> float:
        return float(self.sensors.temp)

    @property
    def desired_temperature(self) -> float:
        return float(self.settings.temp_set)

    @property
    def voltage(self) -> float:
        # whole volts + tenths of a volt, mirrors the C++ gateway logic
        return self.sensors.input_v1 + 0.1 * self.sensors.input_v2

    @property
    def is_on(self) -> bool:
        return self.settings.on

    @property
    def is_eco(self) -> bool:
        return self.settings.eco_mode


def _checksum(payload_without_checksum: bytes) -> int:
    return sum(payload_without_checksum) & 0xFFFF


def _append_checksum_be(body: bytes) -> bytes:
    """Append a big-endian 2-byte checksum computed over `body`."""
    chk = _checksum(body)
    return body + struct.pack(">H", chk)


def parse_status_report(data: bytes) -> StatusReport | None:
    """Parse a notification payload into a StatusReport, or None if invalid."""
    # Preamble(2) + DataLen(1) + CommandCode(1) + Settings(14) + Sensors(4) + Checksum(2)
    min_len = 2 + 1 + 1 + _SETTINGS_SIZE + _SENSORS_SIZE + 2
    if len(data) < min_len:
        return None

    preamble = struct.unpack("<H", data[0:2])[0]
    data_len = data[2]
    cmd_code = data[3]
    if preamble != PREAMBLE or cmd_code != CMD_STATUS_REPORT:
        return None

    settings_bytes = data[4 : 4 + _SETTINGS_SIZE]
    sensors_bytes = data[4 + _SETTINGS_SIZE : 4 + _SETTINGS_SIZE + _SENSORS_SIZE]

    received_checksum = struct.unpack(">H", data[min_len - 2 : min_len])[0]
    expected_checksum = _checksum(data[: min_len - 2])
    if received_checksum != expected_checksum:
        return None

    return StatusReport(
        settings=Settings.from_bytes(settings_bytes),
        sensors=Sensors.from_bytes(sensors_bytes),
    )


def build_set_temp_command(temp_c: int) -> bytes:
    """Build the 'set target temperature' command frame."""
    temp_c = max(-20, min(20, temp_c))
    body = struct.pack("<HBB", PREAMBLE, DATALEN_SET_TEMP, CMD_SET_TEMP) + struct.pack(
        "<b", temp_c
    )
    return _append_checksum_be(body)


def build_set_state_command(settings: Settings) -> bytes:
    """Build the 'set full state' command frame (on/off, eco, etc.)."""
    body = (
        struct.pack("<HBB", PREAMBLE, DATALEN_SET_STATE, CMD_SET_STATE)
        + settings.to_bytes()
    )
    return _append_checksum_be(body)
