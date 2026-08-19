"""Binary sensor platform for Anio Smartwatch."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities for Anio."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["coordinator"]

    entities = []
    for device_id in coordinator.data:
        entities.extend([
            AnioOnlineBinarySensor(coordinator, device_id),
            AnioChargingBinarySensor(coordinator, device_id),
        ])

    async_add_entities(entities)


class AnioBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base binary sensor for Anio Smartwatch."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize base binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        info = self.coordinator.data.get(self._device_id, {}).get("info", {})
        device_name = info.get("name") or info.get("deviceName") or f"Anio Watch {self._device_id}"
        model = info.get("model") or "Anio 6"

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=model,
        )


class AnioOnlineBinarySensor(AnioBaseBinarySensor):
    """Online status binary sensor for Anio Smartwatch."""

    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize online sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_online_{device_id}"

    @property
    def is_on(self) -> bool | None:
        """Return true if device is online."""
        det = self.coordinator.data.get(self._device_id, {}).get("detail", {})
        info = self.coordinator.data.get(self._device_id, {}).get("info", {})
        online = det.get("online") if det.get("online") is not None else info.get("online")
        if online is None:
            return True
        return bool(online)


class AnioChargingBinarySensor(AnioBaseBinarySensor):
    """Charging status binary sensor for Anio Smartwatch."""

    _attr_name = "Wird geladen"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize charging sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_charging_{device_id}"

    @property
    def is_on(self) -> bool | None:
        """Return true if device is charging."""
        det = self.coordinator.data.get(self._device_id, {}).get("detail", {})
        charging = det.get("charging") or det.get("isCharging")
        return bool(charging) if charging is not None else None
