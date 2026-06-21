"""Binary sensor platform for the Alpicool fridge."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    async_add_entities([AlpicoolLockedSensor(coordinator, entry)])


class AlpicoolLockedSensor(CoordinatorEntity[AlpicoolCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Tastensperre"
    _attr_device_class = BinarySensorDeviceClass.LOCK

    def __init__(self, coordinator: AlpicoolCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_locked"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)}
        )

    @property
    def is_on(self) -> bool | None:
        report = self.coordinator.last_report
        return report.settings.locked if report else None
