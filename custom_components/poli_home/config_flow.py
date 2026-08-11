"""Config flow for Poli Home integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import PoliHomeApi, PoliHomeAuthError, PoliHomeConnectionError
from .const import CONF_DEVICE_IDS, CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class PoliHomeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Poli Home."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._email: str | None = None
        self._password: str | None = None
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — user enters email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Prevent duplicate entries for the same account
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            # Test the credentials and fetch devices
            session = async_get_clientsession(self.hass)
            api = PoliHomeApi(session, email, password)

            try:
                await api.authenticate()
                devices = await api.get_devices()
            except PoliHomeAuthError:
                errors["base"] = "invalid_auth"
            except PoliHomeConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during authentication")
                errors["base"] = "unknown"
            else:
                _LOGGER.info(
                    "Poli Home login OK. Found %d device(s)", len(devices)
                )
                for d in devices:
                    _LOGGER.info(
                        "  Device: %s (id=%s, category=%s, online=%s)",
                        d.get("description"),
                        d.get("deviceId"),
                        d.get("category"),
                        d.get("isOnline"),
                    )

                if not devices:
                    errors["base"] = "no_devices_found"
                else:
                    self._email = email
                    self._password = password
                    self._devices = devices

                    # If there's only one device, skip selection
                    if len(devices) == 1:
                        device = devices[0]
                        device_id = str(device.get("deviceId", ""))
                        device_name = device.get("description", device_id)
                        return self.async_create_entry(
                            title=f"Poli Home - {device_name}",
                            data={
                                CONF_EMAIL: email,
                                CONF_PASSWORD: password,
                                CONF_DEVICE_IDS: [device_id],
                            },
                        )

                    # Multiple devices — show selection step
                    return await self.async_step_select_devices()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the device selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_ids = user_input.get(CONF_DEVICE_IDS, [])
            if not selected_ids:
                errors["base"] = "no_devices_selected"
            else:
                # Find friendly names for the entry title
                names = []
                for dev in self._devices:
                    if str(dev.get("deviceId", "")) in selected_ids:
                        names.append(dev.get("description", str(dev.get("deviceId"))))
                title = f"Poli Home - {', '.join(names)}"

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_EMAIL: self._email,
                        CONF_PASSWORD: self._password,
                        CONF_DEVICE_IDS: selected_ids,
                    },
                )

        # Build device options for the selector UI
        options: list[SelectOptionDict] = []
        for device in self._devices:
            device_id = str(device.get("deviceId", ""))
            desc = device.get("description", "Sin nombre")
            category = device.get("category", "")
            home_name = device.get("_homeName", "")
            online = "Online" if device.get("isOnline") else "Offline"
            label = f"{desc} ({category}) [{online}]"
            if home_name:
                label += f" - {home_name}"
            options.append(
                SelectOptionDict(value=device_id, label=label)
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_IDS): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="select_devices",
            data_schema=schema,
            errors=errors,
        )
