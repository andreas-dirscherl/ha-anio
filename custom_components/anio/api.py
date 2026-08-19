"""API Client for Anio Smartwatch Cloud."""
import logging
import uuid
from typing import Any

import aiohttp

from .const import ACCEPT_LANGUAGE, BASE_URL, CLIENT_ID

_LOGGER = logging.getLogger(__name__)


class AnioApiError(Exception):
    """General Anio API Exception."""


class AnioAuthError(AnioApiError):
    """Authentication Exception."""


class AnioApiClient:
    """Anio Smartwatch API Client."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._email = email
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._app_uuid = str(uuid.uuid4())

    @property
    def _headers(self) -> dict[str, str]:
        """Get standard HTTP headers."""
        headers = {
            "Content-Type": "application/json",
            "client-id": CLIENT_ID,
            "app-uuid": self._app_uuid,
            "accept-language": ACCEPT_LANGUAGE,
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def async_login(self) -> dict[str, Any]:
        """Authenticate with email and password."""
        url = f"{BASE_URL}/v1/auth/login"
        payload = {
            "email": self._email,
            "password": self._password,
        }
        try:
            async with self._session.post(
                url, json=payload, headers=self._headers
            ) as resp:
                if resp.status in (401, 403):
                    raise AnioAuthError("Ungültige E-Mail-Adresse oder Passwort.")
                if resp.status != 200:
                    text = await resp.text()
                    raise AnioApiError(f"Login fehlgeschlagen ({resp.status}): {text}")
                data = await resp.json()
                self._access_token = data.get("accessToken")
                self._refresh_token = data.get("refreshToken")
                return data
        except aiohttp.ClientError as err:
            raise AnioApiError(f"Netzwerkfehler beim Anmelden: {err}") from err

    async def async_refresh_token(self) -> None:
        """Refresh access token using refresh token."""
        url = f"{BASE_URL}/v1/auth/refresh-access-token"
        headers = self._headers
        if self._refresh_token:
            headers["Authorization"] = f"Bearer {self._refresh_token}"

        try:
            async with self._session.post(url, headers=headers) as resp:
                if resp.status in (401, 403):
                    await self.async_login()
                    return
                if resp.status != 200:
                    await self.async_login()
                    return
                data = await resp.json()
                self._access_token = data.get("accessToken")
                if "refreshToken" in data:
                    self._refresh_token = data.get("refreshToken")
        except Exception:
            await self.async_login()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Execute HTTP request with automatic re-auth."""
        if not self._access_token:
            await self.async_login()

        url = f"{BASE_URL}{endpoint}"

        for attempt in range(2):
            try:
                async with self._session.request(
                    method, url, headers=self._headers, **kwargs
                ) as resp:
                    if resp.status == 401 and attempt == 0:
                        _LOGGER.debug("Token abgelaufen, erneuere Token...")
                        await self.async_refresh_token()
                        continue
                    if resp.status not in (200, 201, 204):
                        text = await resp.text()
                        raise AnioApiError(
                            f"API Fehler [{method} {endpoint}] HTTP {resp.status}: {text}"
                        )
                    if resp.status == 204:
                        return None
                    return await resp.json()
            except aiohttp.ClientError as err:
                raise AnioApiError(f"Netzwerkfehler bei {endpoint}: {err}") from err

        raise AnioAuthError("Authentifizierung nach Wiederholung fehlgeschlagen.")

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get list of linked watches."""
        res = await self._request("GET", "/v1/device/list")
        return res if isinstance(res, list) else []

    async def async_get_device_detail(self, device_id: str) -> dict[str, Any]:
        """Get details for a specific device."""
        return await self._request("GET", f"/v1/device/{device_id}")

    async def async_get_location(self, device_id: str) -> dict[str, Any]:
        """Get last location for a device."""
        return await self._request("GET", f"/v1/location/{device_id}/last")

    async def async_get_silence_times(self, device_id: str) -> list[dict[str, Any]]:
        """Get silence/school time config."""
        res = await self._request("GET", f"/v1/silence-time/{device_id}")
        return res if isinstance(res, list) else []

    async def async_enable_silence_time(self, device_id: str) -> None:
        """Enable silence time mode."""
        await self._request("POST", f"/v1/silence-time/{device_id}/enable")

    async def async_disable_silence_time(self, device_id: str) -> None:
        """Disable silence time mode."""
        await self._request("POST", f"/v1/silence-time/{device_id}/disable")

    async def async_find_device(self, device_id: str) -> None:
        """Trigger find watch sound."""
        await self._request("POST", f"/v1/device/{device_id}/find")

    async def async_power_off(self, device_id: str) -> None:
        """Remotely power off the watch."""
        await self._request("POST", f"/v1/device/{device_id}/poweroff")
