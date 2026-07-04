"""Notify entities for Telnyx."""

from __future__ import annotations

from html import escape
from typing import override

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEFAULT_MESSAGING_FROM,
    CONF_DEFAULT_MESSAGING_TO,
    CONF_DEFAULT_VOICE_FROM,
    CONF_DEFAULT_VOICE_TO,
    DEFAULT_NAME,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Telnyx notify entities."""
    async_add_entities(
        [
            TelnyxMessagingNotifyEntity(entry),
            TelnyxTeXMLNotifyEntity(entry),
            TelnyxVoiceApiNotifyEntity(entry),
        ]
    )


class TelnyxBaseNotifyEntity(NotifyEntity):
    """Base class for Telnyx notify entities."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, entry: ConfigEntry, key: str, translation_key: str) -> None:
        """Initialize the entity."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = translation_key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEFAULT_NAME,
        )

    @property
    def _client(self):
        """Return the entry client."""
        return self.hass.data[DOMAIN][self._entry.entry_id].client

    def _require_value(self, config_key: str, label: str) -> str:
        """Return a required config value."""
        value = self._entry.data.get(config_key)
        if not value:
            raise ServiceValidationError(f"Configure {label} in the Telnyx config entry")
        return value


class TelnyxMessagingNotifyEntity(TelnyxBaseNotifyEntity):
    """Telnyx SMS notify entity."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(entry, "messaging", "messaging")

    @override
    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a message through Telnyx messaging."""
        sms_message = f"{title}: {message}" if title else message
        await self._client.send_sms(
            self._require_value(CONF_DEFAULT_MESSAGING_TO, "a default messaging target"),
            sms_message,
            self._entry.data.get(CONF_DEFAULT_MESSAGING_FROM),
        )


class TelnyxTeXMLNotifyEntity(TelnyxBaseNotifyEntity):
    """Telnyx TeXML voice notify entity."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(entry, "voice_texml", "voice_texml")

    @override
    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a voice call using TeXML."""
        texml = message.strip()
        if not texml.startswith("<"):
            combined = f"{title}. {message}" if title else message
            texml = f"<Response><Say>{escape(combined)}</Say></Response>"

        await self._client.send_texml_call(
            self._require_value(CONF_DEFAULT_VOICE_TO, "a default voice target"),
            texml,
            self._entry.data.get(CONF_DEFAULT_VOICE_FROM),
        )


class TelnyxVoiceApiNotifyEntity(TelnyxBaseNotifyEntity):
    """Telnyx Voice API notify entity."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(entry, "voice_api", "voice_api")

    @override
    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a voice API call."""
        voice_message = f"{title}. {message}" if title else message
        await self._client.send_voice_api_call(
            self._require_value(CONF_DEFAULT_VOICE_TO, "a default voice target"),
            voice_message,
            self._entry.data.get(CONF_DEFAULT_VOICE_FROM),
        )
