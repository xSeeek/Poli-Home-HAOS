"""Sensor platform for Poli Home — connection and battery status sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Poli Home binary sensor entities from a config entry."""
    coordinator: PoliHomeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []
    for device_id, device_data in coordinator.data.items():
        # Connectivity sensor
        entities.append(
            PoliHomeConnectivitySensor(coordinator, device_id, device_data)
        )
        # Low battery sensor
        entities.append(
            PoliHomeBatterySensor(coordinator, device_id, device_data)
        )

    async_add_entities(entities)


def _get_device_info(device_data: dict[str, Any], device_id: str) -> dict[str, Any]:
    """Build device info dict for HA device registry."""
    device_name = device_data.get("description", f"Dispositivo {device_id}")
    home_name = device_data.get("_homeName", "")
    return {
        "identifiers": {(DOMAIN, device_id)},
        "name": f"{device_name}" + (f" ({home_name})" if home_name else ""),
        "manufacturer": "ASSA ABLOY / Poli",
        "model": device_data.get("deviceModelDescription", "Poli Connect"),
        "sw_version": device_data.get("currentFirmwareVersion"),
    }


class PoliHomeConnectivitySensor(
    CoordinatorEntity[PoliHomeCoordinator], BinarySensorEntity
):
    """Binary sensor showing the device's connectivity status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Conexión"

    def __init__(
        self,
        coordinator: PoliHomeCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the connectivity sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_connectivity"
        self._attr_device_info = _get_device_info(device_data, device_id)

    @property
    def is_on(self) -> bool | None:
        """Return True if the device is online."""
        device = self.coordinator.data.get(self._device_id, {})
        return device.get("isOnline")


class PoliHomeBatterySensor(
    CoordinatorEntity[PoliHomeCoordinator], BinarySensorEntity
):
    """Binary sensor showing low battery warning.

    The API returns 'lowBattery' as a boolean — True means battery is low.
    """

    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_has_entity_name = True
    _attr_name = "Batería baja"

    def __init__(
        self,
        coordinator: PoliHomeCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{DOMAIN}_{device_id}_low_battery"
        self._attr_device_info = _get_device_info(device_data, device_id)

    @property
    def is_on(self) -> bool | None:
        """Return True if the battery is low."""
        device = self.coordinator.data.get(self._device_id, {})
        return device.get("lowBattery")
