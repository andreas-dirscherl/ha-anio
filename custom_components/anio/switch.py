"""Switch platform for Anio Smartwatch (Quiet / School Mode)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .api import AnioApiClient
from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities for Anio."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["coordinator"]
    api: AnioApiClient = entry_data["api"]

    if not coordinator.data or not isinstance(coordinator.data, dict):
        _LOGGER.debug("Keine Koordinatordaten vorhanden für Switch-Setup")
        return

    entities = []
    for device_id in coordinator.data:
        entities.append(AnioSilenceTimeSwitch(coordinator, api, device_id))

    async_add_entities(entities)


class AnioSilenceTimeSwitch(CoordinatorEntity, SwitchEntity):
    """Switch for Anio Silence Time / School Mode."""

    _attr_has_entity_name = True
    _attr_name = "Schulmodus (Ruhezeit)"
    _attr_icon = "mdi:school"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: AnioApiClient,
        device_id: str,
    ) -> None:
        """Initialize silence time switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device_id
        self._attr_unique_id = f"anio_silence_time_{device_id}"

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
    def is_on(self) -> bool | None:
        """Return true if silence time is enabled."""
        if not self.coordinator.data:
            return False
        silence_times = self.coordinator.data.get(self._device_id, {}).get("silence_times", [])
        if not silence_times:
            return False
        for st in silence_times:
            if st.get("enabled") or st.get("active"):
                return True
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable silence time mode."""
        _LOGGER.info("Aktiviere Schulmodus für Anio Uhr %s", self._device_id)
        await self._api.async_enable_silence_time(self._device_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable silence time mode."""
        _LOGGER.info("Deaktiviere Schulmodus für Anio Uhr %s", self._device_id)
        await self._api.async_disable_silence_time(self._device_id)
        await self.coordinator.async_request_refresh()
