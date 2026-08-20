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

    if not coordinator.data or not isinstance(coordinator.data, dict):
        _LOGGER.debug("Keine Koordinatordaten vorhanden für BinarySensor-Setup")
        return

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
        info = (
            self.coordinator.data.get(self._device_id, {}).get("info", {})
            if self.coordinator.data
            else {}
        )
        device_name = info.get("name") or info.get("deviceName") or f"Anio Watch {self._device_id}"
        model = info.get("model") or "Anio 6"

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=model,
        )


class AnioOnlineBinarySensor(AnioBaseBinarySensor):
    """Binary sensor for watch online status."""

    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize online binary sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_online_{device_id}"

    @property
    def is_on(self) -> bool:
        """Return true if device is connected."""
        if not self.coordinator.data:
            return True
        data = self.coordinator.data.get(self._device_id, {})
        loc = data.get("location") or {}
        det = data.get("detail") or {}
        info = data.get("info") or {}

        for src in (loc, det, info):
            for key in ("online", "isOnline", "connected", "state"):
                val = src.get(key)
                if val is not None:
                    if isinstance(val, str):
                        return val.lower() in ("online", "connected", "true", "1")
                    return bool(val)
        return True


class AnioChargingBinarySensor(AnioBaseBinarySensor):
    """Binary sensor for battery charging status."""

    _attr_name = "Wird geladen"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize charging binary sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_charging_{device_id}"

    @property
    def is_on(self) -> bool | None:
        """Return true if battery is charging."""
        if not self.coordinator.data:
            return False
        data = self.coordinator.data.get(self._device_id, {})
        loc = data.get("location") or {}
        det = data.get("detail") or {}
        info = data.get("info") or {}

        for src in (loc, det, info):
            for key in ("charging", "isCharging", "is_charging", "batteryCharging"):
                val = src.get(key)
                if val is not None:
                    return bool(val)
        return False
