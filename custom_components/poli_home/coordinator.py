"""DataUpdateCoordinator for Poli Home."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import PoliHomeApi, PoliHomeApiError, PoliHomeAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PoliHomeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Poli Home device data.

    Device data comes from the login response (accountData.homeList[].deviceList[]).
    Each update re-authenticates to get fresh device status since there is no
    separate status polling endpoint.
    """

    def __init__(self, hass: HomeAssistant, api: PoliHomeApi) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Poli Home API.

        Returns a dict mapping device_id (str) -> device_data.
        """
        try:
            devices = await self.api.refresh_devices()

            result: dict[str, Any] = {}
            for device in devices:
                device_id = str(device.get("deviceId", ""))
                if device_id:
                    result[device_id] = device

            return result

        except PoliHomeAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except PoliHomeApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
