"""Config flow for Telnyx."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_API_KEY,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_PUBLIC_KEY,
    DEFAULT_NAME,
    DOMAIN,
    MESSAGING_KEYS,
    VOICE_KEYS,
)

CONF_STEP_ACTION = "step_action"
ACTION_BACK = "back"
ACTION_SAVE = "save"
REQUIRED_COMMON_KEYS = (CONF_API_KEY, CONF_WEBHOOK_PUBLIC_KEY)
STEP_ACTION_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(options=[ACTION_SAVE, ACTION_BACK])
)


class TelnyxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Telnyx."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._data: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the config menu."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["common", "voice", "messaging", "done"],
        )

    def _build_schema(self, keys: tuple[str, ...]) -> vol.Schema:
        """Build schema for a configurable section."""
        schema = vol.Schema(
            {
                **{vol.Optional(key): str for key in keys},
                vol.Required(CONF_STEP_ACTION, default=ACTION_SAVE): STEP_ACTION_SELECTOR,
            }
        )
        return self.add_suggested_values_to_schema(schema, self._data)

    def _store_step_values(self, keys: tuple[str, ...], user_input: dict[str, Any]) -> None:
        """Store user values for the current section."""
        for key in keys:
            if key not in user_input:
                continue
            value = user_input[key]
            if value:
                self._data[key] = value
                continue
            self._data.pop(key, None)

    async def _handle_section_step(
        self, step_id: str, keys: tuple[str, ...], user_input: dict[str, Any] | None
    ) -> config_entries.ConfigFlowResult:
        """Handle a section step with save/back actions."""
        if user_input is not None:
            action = user_input.get(CONF_STEP_ACTION, ACTION_SAVE)
            if action == ACTION_BACK:
                return await self.async_step_user()

            if keys == REQUIRED_COMMON_KEYS and (
                any(key in user_input and not user_input[key] for key in REQUIRED_COMMON_KEYS)
                or any(
                    key not in user_input and key not in self._data
                    for key in REQUIRED_COMMON_KEYS
                )
            ):
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=self._build_schema(keys),
                    errors={"base": "missing_required_common"},
                )

            self._store_step_values(keys, user_input)
            return await self.async_step_user()

        return self.async_show_form(step_id=step_id, data_schema=self._build_schema(keys))

    async def async_step_common(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle common settings."""
        return await self._handle_section_step("common", REQUIRED_COMMON_KEYS, user_input)

    async def async_step_voice(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle voice settings."""
        return await self._handle_section_step("voice", VOICE_KEYS, user_input)

    async def async_step_messaging(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle messaging settings."""
        return await self._handle_section_step("messaging", MESSAGING_KEYS, user_input)

    async def async_step_done(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Finalize configuration."""
        if any(key not in self._data for key in REQUIRED_COMMON_KEYS):
            return self.async_show_form(
                step_id="common",
                data_schema=self._build_schema(REQUIRED_COMMON_KEYS),
                errors={"base": "missing_required_common"},
            )

        unique_id = hashlib.sha256(self._data[CONF_API_KEY].encode("utf-8")).hexdigest()
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=DEFAULT_NAME,
            data={
                **self._data,
                CONF_WEBHOOK_ID: secrets.token_hex(16),
            },
        )
