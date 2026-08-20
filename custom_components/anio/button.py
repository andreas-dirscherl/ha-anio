"""Button platform for Anio Smartwatch."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up button entities for Anio."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = entry_data["coordinator"]
    api: AnioApiClient = entry_data["api"]

    if not coordinator.data or not isinstance(coordinator.data, dict):
        _LOGGER.debug("Keine Koordinatordaten vorhanden für Button-Setup")
        return

    entities = []
    for device_id in coordinator.data:
        entities.extend([
            AnioFindButton(coordinator, api, device_id),
            AnioPowerOffButton(coordinator, api, device_id),
        ])

    async_add_entities(entities)


class AnioBaseButton(CoordinatorEntity, ButtonEntity):
    """Base button for Anio Smartwatch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: AnioApiClient,
        device_id: str,
    ) -> None:
        """Initialize base button."""
        super().__init__(coordinator)
        self._api = api
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


class AnioFindButton(AnioBaseButton):
    """Button to find/ring the watch."""

    _attr_name = "Uhr suchen (piepsen)"
    _attr_icon = "mdi:cellphone-sound"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: AnioApiClient,
        device_id: str,
    ) -> None:
        """Initialize find button."""
        super().__init__(coordinator, api, device_id)
        self._attr_unique_id = f"anio_find_{device_id}"

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.info("Sende Such-Signal an Anio Uhr %s", self._device_id)
        await self._api.async_find_device(self._device_id)


class AnioPowerOffButton(AnioBaseButton):
    """Button to remotely power off the watch."""

    _attr_name = "Uhr ausschalten"
    _attr_icon = "mdi:power"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: AnioApiClient,
        device_id: str,
    ) -> None:
        """Initialize power off button."""
        super().__init__(coordinator, api, device_id)
        self._attr_unique_id = f"anio_poweroff_{device_id}"

    async def async_press(self) -> None:
        """Press the button."""
        _LOGGER.info("Sende Ausschalt-Befehl an Anio Uhr %s", self._device_id)
        await self._api.async_power_off(self._device_id)
