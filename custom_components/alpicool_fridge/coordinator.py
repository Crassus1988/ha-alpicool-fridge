"""BLE connection + state coordinator for the Alpicool fridge."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CHAR_NOTIFY_UUID,
    CHAR_WRITE_UUID,
    PING_INTERVAL,
    UPDATE_INTERVAL,
)
from . import protocol

_LOGGER = logging.getLogger(__name__)


class AlpicoolCoordinator(DataUpdateCoordinator[protocol.StatusReport]):
    """Keeps a persistent BLE connection to the fridge and tracks its state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Alpicool Fridge",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.address = address
        self.entry = entry
        self._client: BleakClient | None = None
        self._connect_lock = asyncio.Lock()
        self._ping_task: asyncio.Task | None = None
        self._last_report: protocol.StatusReport | None = None
        self._first_report_event = asyncio.Event()

    @property
    def last_report(self) -> protocol.StatusReport | None:
        return self._last_report

    async def _async_update_data(self) -> protocol.StatusReport:
        await self._ensure_connected()
        if self._last_report is None:
            # Fridge only pushes a status report a short while after connecting
            # (and periodically afterwards). Give it a grace period instead of
            # failing immediately on the very first refresh.
            try:
                await asyncio.wait_for(self._first_report_event.wait(), timeout=15)
            except asyncio.TimeoutError as err:
                raise UpdateFailed(
                    "Connected, but fridge sent no status report within 15s "
                    "(check it's not still connected to the phone app, and "
                    "that the fridge is within Bluetooth range)"
                ) from err
        if self._last_report is None:
            raise UpdateFailed("No status report received from fridge yet")
        return self._last_report

    async def _ensure_connected(self) -> None:
        async with self._connect_lock:
            if self._client is not None and self._client.is_connected:
                return

            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if ble_device is None:
                raise UpdateFailed(
                    f"Fridge {self.address} not visible to any Bluetooth proxy/adapter"
                )

            try:
                client = await establish_connection(
                    BleakClient, ble_device, self.address
                )
            except (BleakError, asyncio.TimeoutError) as err:
                raise UpdateFailed(f"Could not connect to fridge: {err}") from err

            try:
                await client.start_notify(CHAR_NOTIFY_UUID, self._handle_notify)
            except BleakError as err:
                await client.disconnect()
                raise UpdateFailed(f"Could not subscribe to notifications: {err}") from err

            self._client = client
            self._first_report_event.clear()
            self._start_ping_task()
            _LOGGER.debug("Connected to fridge %s", self.address)

    def _handle_notify(self, _char, data: bytearray) -> None:
        report = protocol.parse_status_report(bytes(data))
        if report is None:
            _LOGGER.debug("Ignoring invalid/short notification (%d bytes)", len(data))
            return
        self._last_report = report
        self._first_report_event.set()
        self.async_set_updated_data(report)

    def _start_ping_task(self) -> None:
        if self._ping_task and not self._ping_task.done():
            return
        self._ping_task = self.hass.loop.create_task(self._ping_loop())

    async def _ping_loop(self) -> None:
        """The fridge drops the connection if it doesn't see traffic regularly."""
        while self._client is not None and self._client.is_connected:
            try:
                await self._client.write_gatt_char(
                    CHAR_WRITE_UUID, protocol.PING_MESSAGE, response=True
                )
            except BleakError as err:
                _LOGGER.debug("Ping failed, will reconnect on next update: %s", err)
                break
            await asyncio.sleep(PING_INTERVAL)

    async def async_send_command(self, payload: bytes) -> None:
        await self._ensure_connected()
        assert self._client is not None
        try:
            await self._client.write_gatt_char(CHAR_WRITE_UUID, payload, response=True)
        except BleakError as err:
            raise UpdateFailed(f"Failed to send command to fridge: {err}") from err

    async def async_set_temperature(self, temp_c: int) -> None:
        await self.async_send_command(protocol.build_set_temp_command(temp_c))

    async def async_set_on(self, on: bool) -> None:
        if self._last_report is None:
            raise UpdateFailed("Cannot toggle power before first status report")
        settings = self._last_report.settings
        settings.on = on
        await self.async_send_command(protocol.build_set_state_command(settings))

    async def async_set_eco(self, eco: bool) -> None:
        if self._last_report is None:
            raise UpdateFailed("Cannot toggle eco mode before first status report")
        settings = self._last_report.settings
        settings.eco_mode = eco
        await self.async_send_command(protocol.build_set_state_command(settings))

    async def async_shutdown(self) -> None:
        if self._ping_task:
            self._ping_task.cancel()
        if self._client is not None:
            await self._client.disconnect()
            self._client = None
