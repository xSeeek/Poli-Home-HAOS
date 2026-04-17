"""Lock platform for Poli Home."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
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
    """Set up Poli Home lock entities from a config entry."""
    coordinator: PoliHomeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[PoliHomeLock] = []
    for device_id, device_data in coordinator.data.items():
        category = device_data.get("category", "")
        controller_type = device_data.get("controllerType", "")
        if category in ("Switch", "DoorLock", "Doorlock") or controller_type in ("Switch",):
            entities.append(
                PoliHomeLock(coordinator, device_id, device_data)
            )

    if not entities:
        # Fallback: create locks for all devices in case categories change
        _LOGGER.warning(
            "No Switch/DoorLock devices found by category. "
            "Creating locks for all %d devices.",
            len(coordinator.data),
        )
        for device_id, device_data in coordinator.data.items():
            entities.append(
                PoliHomeLock(coordinator, device_id, device_data)
            )

    async_add_entities(entities)


class PoliHomeLock(CoordinatorEntity[PoliHomeCoordinator], LockEntity):
    """Lock entity to trigger the lock's open action.

    The Hub Poli Connect controls an electric lock relay.
    It only supports a momentary open command via Device/SwitchLockUnlock.
    We expose it as a LockEntity so HomeKit and Matter handle it securely.
    """

    _attr_has_entity_name = True
    _attr_name = None  # Use device name implicitly

    def __init__(
        self,
        coordinator: PoliHomeCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._device_id = device_id

        device_name = device_data.get("description", f"Dispositivo {device_id}")
        home_name = device_data.get("_homeName", "")

        self._attr_unique_id = f"{DOMAIN}_{device_id}_lock"
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

    @property
    def is_locked(self) -> bool:
        """Return true if the lock is locked.
        
        Since this is a momentary electric strike, we assume it's always locked
        unless we are actively unlocking it.
        """
        return not getattr(self, "_is_unlocked", False)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        _LOGGER.info("Unlocking %s", self._device_id)
        
        # State transition: Mark as unlocked so HomeKit sees the change
        self._is_unlocked = True
        self.async_write_ha_state()

        success = await self.coordinator.api.open_lock(
            int(self._device_id),
            endpoint_address=self._endpoint_address,
        )
        if success:
            import asyncio
            # Wait 3 seconds to let HomeKit/Matter register the "Unlocked" state
            # and simulate the physical relay delay
            await asyncio.sleep(3)
            
            await self.coordinator.async_request_refresh()
            
        else:
            _LOGGER.error("Failed to unlock %s", self._device_id)
            
        # State transition: Re-lock automatically
        self._is_unlocked = False
        self.async_write_ha_state()

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        # No-op: the lock engages automatically after being opened
        self._is_unlocked = False
        self.async_write_ha_state()
        _LOGGER.debug("Lock command executed for %s (momentary lock)", self._device_id)
