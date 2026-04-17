"""API client for Poli Home (Yale Connect / ASSA ABLOY)."""
from __future__ import annotations

import logging
import ssl
import uuid
from typing import Any

import aiohttp

from .const import (
    AUTH_HEADER,
    BASE_URL,
    BRAND_PLATFORM_GUID,
    BRAND_PLATFORM_HEADER,
    ENDPOINT_LOGIN,
    ENDPOINT_LOGOUT,
    ENDPOINT_SWITCH_LOCK_UNLOCK,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class PoliHomeApiError(Exception):
    """Base exception for Poli Home API errors."""


class PoliHomeAuthError(PoliHomeApiError):
    """Authentication error."""


class PoliHomeConnectionError(PoliHomeApiError):
    """Connection error."""


def _create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that bypasses certificate verification.

    Yale Connect's server uses a certificate whose CA has Basic Constraints
    not marked as critical, which causes standard verification to fail.
    """
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    return ssl_ctx


class PoliHomeApi:
    """Async API client for Poli Home smart locks.

    The API is hosted on Yale Connect services (ASSA ABLOY).
    All requests require:
      - Header 'brandPlatformGUID': brand+platform token
      - Header 'access-token': session token (after login)
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._email = email
        self._password = password
        self._access_token: str | None = None
        self._account_data: dict[str, Any] | None = None
        self._device_uuid: str = str(uuid.uuid4())
        self._base_url = BASE_URL
        self._ssl_context = _create_ssl_context()

    @property
    def is_authenticated(self) -> bool:
        """Return True if we have a valid access token."""
        return self._access_token is not None

    def _headers(self) -> dict[str, str]:
        """Return request headers with auth and brand tokens."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            BRAND_PLATFORM_HEADER: BRAND_PLATFORM_GUID,
        }
        if self._access_token:
            headers[AUTH_HEADER] = self._access_token
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        """Make an authenticated request to the API."""
        url = f"{self._base_url}{endpoint}"
        _LOGGER.debug("API request: %s %s", method, url)

        try:
            async with self._session.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ssl=self._ssl_context,
                **kwargs,
            ) as response:
                if response.status == 401:
                    _LOGGER.debug("Token expired (401), re-authenticating")
                    await self.authenticate()
                    async with self._session.request(
                        method,
                        url,
                        json=json_data,
                        params=params,
                        headers=self._headers(),
                        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                        ssl=self._ssl_context,
                        **kwargs,
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise PoliHomeAuthError(
                    f"Authentication failed: {err.status}"
                ) from err
            raise PoliHomeApiError(
                f"API error: {err.status} {err.message}"
            ) from err
        except aiohttp.ClientError as err:
            raise PoliHomeConnectionError(
                f"Connection error: {err}"
            ) from err

    async def authenticate(self) -> bool:
        """Authenticate with email and password via Account/Login.

        The login request requires mobileInformation alongside credentials.
        Returns the full account data with homes and devices.
        """
        try:
            url = f"{self._base_url}{ENDPOINT_LOGIN}"
            login_data = {
                "email": self._email,
                "password": self._password,
                "mobileInformation": {
                    "os": "Home Assistant",
                    "information": "PoliHAOS Integration",
                    "appVersion": "browser",
                    "pushToken": "",
                    "UUID": self._device_uuid,
                },
            }

            async with self._session.post(
                url,
                json=login_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    BRAND_PLATFORM_HEADER: BRAND_PLATFORM_GUID,
                },
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ssl=self._ssl_context,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                self._access_token = data.get("accessToken")
                self._account_data = data.get("accountData")

                if not self._access_token:
                    raise PoliHomeAuthError(
                        "Login succeeded but no accessToken in response"
                    )

                _LOGGER.info("Successfully authenticated with Poli Home API")
                return True

        except aiohttp.ClientResponseError as err:
            if err.status in (400, 401, 403):
                raise PoliHomeAuthError("Invalid email or password") from err
            raise PoliHomeApiError(f"Auth error: {err.status}") from err
        except aiohttp.ClientError as err:
            raise PoliHomeConnectionError(f"Connection error: {err}") from err

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch devices from the account data.

        Devices come from the login response: accountData.homeList[].deviceList[]
        Each device gets _homeName and _homeId injected for context.
        """
        if not self._account_data:
            await self.authenticate()

        devices = []
        if self._account_data:
            home_list = self._account_data.get("homeList", [])
            for home in home_list:
                device_list = home.get("deviceList", [])
                for device in device_list:
                    device["_homeName"] = home.get("description", "")
                    device["_homeId"] = home.get("homeId")
                    devices.append(device)

        return devices

    async def refresh_devices(self) -> list[dict[str, Any]]:
        """Re-authenticate to get fresh device data.

        Since device status comes from the login response,
        we need to re-login to refresh data.
        """
        await self.authenticate()
        return await self.get_devices()

    async def open_lock(self, device_id: int, endpoint_address: str = "2") -> bool:
        """Send the open/unlock command to a switch device.

        Uses Device/SwitchLockUnlock for Hub Poli Connect (Switch category).
        Requires:
          - deviceId: the numeric device ID
          - endpointAddress: the endpoint index (default "2", from deviceParameters.endpointIndex)

        The lock only supports a momentary open action —
        it re-locks automatically when the door is physically opened and closed.
        """
        _LOGGER.info("Opening lock (switch) %s endpoint %s", device_id, endpoint_address)

        try:
            await self._request(
                "POST",
                ENDPOINT_SWITCH_LOCK_UNLOCK,
                json_data={
                    "deviceId": device_id,
                    "endpointAddress": endpoint_address,
                },
            )
            return True
        except PoliHomeApiError as err:
            _LOGGER.error("Failed to open lock %s: %s", device_id, err)
            return False

    async def logout(self) -> None:
        """Logout from the API."""
        try:
            await self._request(
                "POST",
                ENDPOINT_LOGOUT,
                json_data={
                    "accessToken": self._access_token or "",
                    "deviceToken": "",
                },
            )
        except PoliHomeApiError:
            _LOGGER.debug("Logout request failed, ignoring")
        finally:
            self._access_token = None
            self._account_data = None
