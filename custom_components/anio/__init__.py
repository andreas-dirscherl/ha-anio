"""The Anio Smartwatch integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AnioApiClient, AnioAuthError, AnioApiError
from .const import CONF_EMAIL, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Anio Smartwatch from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    session = async_get_clientsession(hass)
    api = AnioApiClient(email, password, session)

    try:
        await api.async_login()
    except AnioAuthError as err:
        _LOGGER.error("Authentifizierung für Anio fehlgeschlagen: %s", err)
        return False
    except AnioApiError as err:
        _LOGGER.error("Anio API Fehler beim Setup: %s", err)
        return False

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from Anio Cloud."""
        try:
            devices = await api.async_get_devices()
            data: dict[str, dict[str, Any]] = {}

            for dev in devices:
                device_id = dev.get("id") or dev.get("backendId")
                if not device_id:
                    continue

                detail = {}
                location = {}
                silence_times = []

                try:
                    detail = await api.async_get_device_detail(device_id)
                except Exception as err:
                    _LOGGER.warning("Fehler beim Abrufen der Details für %s: %s", device_id, err)

                try:
                    location = await api.async_get_location(device_id)
                except Exception as err:
                    _LOGGER.warning("Fehler beim Abrufen des Standorts für %s: %s", device_id, err)

                try:
                    silence_times = await api.async_get_silence_times(device_id)
                except Exception as err:
                    _LOGGER.warning("Fehler beim Abrufen der Ruhezeiten für %s: %s", device_id, err)

                data[device_id] = {
                    "info": dev,
                    "detail": detail,
                    "location": location,
                    "silence_times": silence_times,
                }

            return data
        except AnioAuthError as err:
            raise UpdateFailed(f"Authentifizierungsfehler: {err}") from err
        except AnioApiError as err:
            raise UpdateFailed(f"API Fehler beim Aktualisieren: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Erster DataRefresh fehlgeschlagen (Setup läuft trotzdem weiter): %s", err)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
