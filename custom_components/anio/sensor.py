"""Sensor platform for Anio Smartwatch."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
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
    """Set up sensor entities for Anio."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["coordinator"]

    entities = []
    for device_id in coordinator.data:
        entities.extend([
            AnioBatterySensor(coordinator, device_id),
            AnioSignalSensor(coordinator, device_id),
            AnioTrackingModeSensor(coordinator, device_id),
        ])

    async_add_entities(entities)


class AnioBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Anio Smartwatch."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize base sensor."""
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


class AnioBatterySensor(AnioBaseSensor):
    """Battery sensor for Anio Smartwatch."""

    _attr_name = "Akkustand"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize battery sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_battery_{device_id}"

    @property
    def native_value(self) -> int | None:
        """Return native value of battery."""
        loc = self.coordinator.data.get(self._device_id, {}).get("location", {})
        det = self.coordinator.data.get(self._device_id, {}).get("detail", {})
        bat = loc.get("battery") if loc.get("battery") is not None else det.get("battery")
        return int(bat) if bat is not None else None


class AnioSignalSensor(AnioBaseSensor):
    """Signal strength sensor for Anio Smartwatch."""

    _attr_name = "Empfangsstärke"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize signal sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_signal_{device_id}"

    @property
    def native_value(self) -> int | None:
        """Return signal strength value."""
        det = self.coordinator.data.get(self._device_id, {}).get("detail", {})
        sig = det.get("signal") or det.get("gsmSignal")
        return int(sig) if sig is not None else None


class AnioTrackingModeSensor(AnioBaseSensor):
    """Tracking mode sensor for Anio Smartwatch."""

    _attr_name = "Ortungsmodus"
    _attr_icon = "mdi:map-clock"

    def __init__(self, coordinator: DataUpdateCoordinator, device_id: str) -> None:
        """Initialize tracking mode sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"anio_tracking_mode_{device_id}"

    @property
    def native_value(self) -> str | None:
        """Return current tracking mode."""
        det = self.coordinator.data.get(self._device_id, {}).get("detail", {})
        return det.get("trackingMode") or "Standard"
