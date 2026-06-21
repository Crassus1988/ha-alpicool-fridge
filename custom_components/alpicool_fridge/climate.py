"""Climate platform for the Alpicool fridge."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAX_TEMP, MIN_TEMP
from .coordinator import AlpicoolCoordinator

PRESET_ECO = "eco"
PRESET_NORMAL = "normal"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AlpicoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlpicoolClimate(coordinator, entry)])


class AlpicoolClimate(CoordinatorEntity[AlpicoolCoordinator], ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:fridge-outline"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [HVACMode.COOL, HVACMode.OFF]
    _attr_preset_modes = [PRESET_NORMAL, PRESET_ECO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: AlpicoolCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=entry.title,
            manufacturer="Alpicool / ICECO",
        )

    @property
    def current_temperature(self) -> float | None:
        report = self.coordinator.last_report
        return report.actual_temperature if report else None

    @property
    def target_temperature(self) -> float | None:
        report = self.coordinator.last_report
        return report.desired_temperature if report else None

    @property
    def hvac_mode(self) -> HVACMode:
        report = self.coordinator.last_report
        if report and report.is_on:
            return HVACMode.COOL
        return HVACMode.OFF

    @property
    def preset_mode(self) -> str:
        report = self.coordinator.last_report
        return PRESET_ECO if report and report.is_eco else PRESET_NORMAL

    @property
    def extra_state_attributes(self) -> dict:
        report = self.coordinator.last_report
        if not report:
            return {}
        return {"voltage": round(report.voltage, 2)}

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get("temperature")
        if temp is None:
            return
        await self.coordinator.async_set_temperature(int(temp))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.async_set_on(hvac_mode == HVACMode.COOL)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self.coordinator.async_set_on(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.coordinator.async_set_on(False)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.coordinator.async_set_eco(preset_mode == PRESET_ECO)
        await self.coordinator.async_request_refresh()
