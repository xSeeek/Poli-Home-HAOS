"""Button platform for Poli Home — triggers lock open action."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoliHomeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Poli Home button entities from a config entry."""
    coordinator: PoliHomeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[PoliHomeOpenButton] = []
    for device_id, device_data in coordinator.data.items():
        # The Hub Poli Connect appears as category "Switch"
        # Create open buttons for all Switch and DoorLock devices
        category = device_data.get("category", "")
        controller_type = device_data.get("controllerType", "")
        if category in ("Switch", "DoorLock", "Doorlock") or controller_type in ("Switch",):
            entities.append(
                PoliHomeOpenButton(coordinator, device_id, device_data)
            )

    if not entities:
        # Fallback: create buttons for all devices in case categories change
        _LOGGER.warning(
            "No Switch/DoorLock devices found by category. "
            "Creating buttons for all %d devices.",
            len(coordinator.data),
        )
        for device_id, device_data in coordinator.data.items():
            entities.append(
                PoliHomeOpenButton(coordinator, device_id, device_data)
            )

    async_add_entities(entities)


class PoliHomeOpenButton(CoordinatorEntity[PoliHomeCoordinator], ButtonEntity):
    """Button entity to trigger the lock's open action.

    The Hub Poli Connect controls an electric lock relay.
    It only supports a momentary open command via Device/SwitchLockUnlock.
    The lock re-engages automatically when the door is physically closed.
    """

    _attr_icon = "mdi:door-open"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoliHomeCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the open button."""
        super().__init__(coordinator)
        self._device_id = device_id

        device_name = device_data.get("description", f"Dispositivo {device_id}")
        home_name = device_data.get("_homeName", "")

        self._attr_unique_id = f"{DOMAIN}_{device_id}_open"
        self._attr_name = "Abrir"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"{device_name}" + (f" ({home_name})" if home_name else ""),
            "manufacturer": "ASSA ABLOY / Poli",
            "model": device_data.get("deviceModelDescription", "Poli Connect"),
            "sw_version": device_data.get("currentFirmwareVersion"),
        }

        # endpointAddress for the SwitchLockUnlock command
        params = device_data.get("deviceParameters", {})
        self._endpoint_address = str(params.get("endpointIndex", 2))

    async def async_press(self) -> None:
        """Handle the button press — send open command to the lock."""
        _LOGGER.info("Opening lock %s", self._device_id)
        success = await self.coordinator.api.open_lock(
            int(self._device_id),
            endpoint_address=self._endpoint_address,
        )
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to open lock %s", self._device_id)
