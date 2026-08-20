"""Device tracker platform for Anio Smartwatch."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
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
    """Set up device tracker entities for Anio."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["coordinator"]

    if not coordinator.data or not isinstance(coordinator.data, dict):
        _LOGGER.debug("Keine Koordinatordaten vorhanden für DeviceTracker-Setup")
        return

    entities = []
    for device_id in coordinator.data:
        entities.append(AnioDeviceTracker(coordinator, device_id))

    async_add_entities(entities)


class AnioDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Anio Smartwatch Device Tracker."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:smartwatch"

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"anio_tracker_{device_id}"

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

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if not self.coordinator.data:
            return None
        loc = self.coordinator.data.get(self._device_id, {}).get("location") or {}
        pos = loc.get("position")
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            try:
                return float(pos[0])
            except (ValueError, TypeError):
                pass
        if isinstance(pos, dict):
            lat = pos.get("latitude") or pos.get("lat")
            if lat is not None:
                try:
                    return float(lat)
                except (ValueError, TypeError):
                    pass
        lat = loc.get("latitude") or loc.get("lat")
        if lat is not None:
            try:
                return float(lat)
            except (ValueError, TypeError):
                pass
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if not self.coordinator.data:
            return None
        loc = self.coordinator.data.get(self._device_id, {}).get("location") or {}
        pos = loc.get("position")
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            try:
                return float(pos[1])
            except (ValueError, TypeError):
                pass
        if isinstance(pos, dict):
            lon = pos.get("longitude") or pos.get("lng")
            if lon is not None:
                try:
                    return float(lon)
                except (ValueError, TypeError):
                    pass
        lon = loc.get("longitude") or loc.get("lng")
        if lon is not None:
            try:
                return float(lon)
            except (ValueError, TypeError):
                pass
        return None

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the device in meters."""
        if not self.coordinator.data:
            return 20
        loc = self.coordinator.data.get(self._device_id, {}).get("location") or {}
        return loc.get("accuracy", 20)

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device tracker attributes."""
        if not self.coordinator.data:
            return {}
        loc = self.coordinator.data.get(self._device_id, {}).get("location") or {}
        return {
            "address": loc.get("address"),
            "location_type": loc.get("positionDeterminedBy") or loc.get("locatingType") or loc.get("type"),
            "updated_at": loc.get("date") or loc.get("updatedAt") or loc.get("createdAt"),
            "battery_level": loc.get("batteryLevel"),
            "signal_strength": loc.get("signalStrength"),
        }
