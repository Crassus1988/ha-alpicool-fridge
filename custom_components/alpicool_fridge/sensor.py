"""Sensor platform for the Alpicool fridge."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AlpicoolCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AlpicoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlpicoolVoltageSensor(coordinator, entry)])


class AlpicoolVoltageSensor(CoordinatorEntity[AlpicoolCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Spannung"
    _attr_icon = "mdi:current-dc"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: AlpicoolCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_voltage"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)}
        )

    @property
    def native_value(self) -> float | None:
        report = self.coordinator.last_report
        return round(report.voltage, 2) if report else None
