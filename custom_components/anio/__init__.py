"""The Anio Smartwatch integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AnioApiClient, AnioApiError, AnioAuthError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_APP_UUID,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

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
    access_token = entry.data.get(CONF_ACCESS_TOKEN)
    refresh_token = entry.data.get(CONF_REFRESH_TOKEN)
    app_uuid = entry.data.get(CONF_APP_UUID)

    session = async_get_clientsession(hass)

    def _on_tokens_updated(
        new_access_token: str,
        new_refresh_token: str | None,
        current_app_uuid: str,
    ) -> None:
        """Callback to save updated tokens in ConfigEntry data across HA restarts."""
        new_data = {
            **entry.data,
            CONF_ACCESS_TOKEN: new_access_token,
            CONF_REFRESH_TOKEN: new_refresh_token,
            CONF_APP_UUID: current_app_uuid,
        }
        hass.config_entries.async_update_entry(entry, data=new_data)

    api = AnioApiClient(
        email=email,
        password=password,
        session=session,
        access_token=access_token,
        refresh_token=refresh_token,
        app_uuid=app_uuid,
        on_tokens_updated=_on_tokens_updated,
    )

    # Initial token validation / login if no saved token exists
    if not access_token:
        try:
            await api.async_login()
        except AnioAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Anio Authentifizierung fehlgeschlagen: {err}"
            ) from err
        except AnioApiError as err:
            raise ConfigEntryNotReady(
                f"Anio Cloud nicht erreichbar: {err}"
            ) from err

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from Anio Cloud concurrently."""
        try:
            devices = await api.async_get_devices()
            data: dict[str, dict[str, Any]] = {}

            for dev in devices:
                device_id = dev.get("id") or dev.get("backendId")
                if not device_id:
                    continue

                results = await asyncio.gather(
                    api.async_get_device_detail(device_id),
                    api.async_get_location(device_id),
                    api.async_get_silence_times(device_id),
                    return_exceptions=True,
                )

                detail = results[0] if not isinstance(results[0], Exception) else {}
                location = results[1] if not isinstance(results[1], Exception) else {}
                silence_times = (
                    results[2] if not isinstance(results[2], Exception) else []
                )

                data[device_id] = {
                    "info": dev,
                    "detail": detail if isinstance(detail, dict) else {},
                    "location": location if isinstance(location, dict) else {},
                    "silence_times": (
                        silence_times if isinstance(silence_times, list) else []
                    ),
                }

            return data
        except AnioAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentifizierungsfehler beim Update: {err}"
            ) from err
        except AnioApiError as err:
            raise UpdateFailed(
                f"API Fehler beim Aktualisieren: {err}"
            ) from err

    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except (ConfigEntryAuthFailed, ConfigEntryNotReady):
        raise
    except Exception as err:
        _LOGGER.warning(
            "Erster DataRefresh fehlgeschlagen (Setup läuft weiter): %s", err
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (e.g. changed polling interval)."""
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    entry_data = hass.data[DOMAIN].get(entry.entry_id)
    if entry_data and "coordinator" in entry_data:
        coordinator: DataUpdateCoordinator = entry_data["coordinator"]
        coordinator.update_interval = timedelta(seconds=scan_interval)
        _LOGGER.info(
            "Anio Polling-Intervall auf %s Sekunden aktualisiert", scan_interval
        )
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
