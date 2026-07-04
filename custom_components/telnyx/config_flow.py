"""Config flow for Telnyx."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_API_KEY,
    CONF_CALL_CONTROL_CONNECTION_ID,
    CONF_DEFAULT_MESSAGING_FROM,
    CONF_DEFAULT_MESSAGING_TO,
    CONF_DEFAULT_VOICE_FROM,
    CONF_DEFAULT_VOICE_TO,
    CONF_MESSAGING_PROFILE_ID,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_PUBLIC_KEY,
    DEFAULT_NAME,
    DOMAIN,
)


STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_WEBHOOK_PUBLIC_KEY): str,
        vol.Optional(CONF_CALL_CONTROL_CONNECTION_ID): str,
        vol.Optional(CONF_MESSAGING_PROFILE_ID): str,
        vol.Optional(CONF_DEFAULT_MESSAGING_FROM): str,
        vol.Optional(CONF_DEFAULT_MESSAGING_TO): str,
        vol.Optional(CONF_DEFAULT_VOICE_FROM): str,
        vol.Optional(CONF_DEFAULT_VOICE_TO): str,
    }
)


class TelnyxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Telnyx."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            unique_id = hashlib.sha256(
                user_input[CONF_API_KEY].encode("utf-8")
            ).hexdigest()
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    **{key: value for key, value in user_input.items() if value},
                    CONF_WEBHOOK_ID: secrets.token_hex(16),
                },
            )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)
