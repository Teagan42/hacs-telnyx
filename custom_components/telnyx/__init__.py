"""The Telnyx integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import web
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.components import webhook

from .client import TelnyxClient
from .const import (
    ATTR_CALL_CONTROL_ID,
    ATTR_CHANNELS,
    ATTR_DIGITS,
    ATTR_ENTRY_ID,
    ATTR_EVENT_TYPE,
    ATTR_FORMAT,
    ATTR_FROM,
    ATTR_MESSAGE,
    ATTR_PAYLOAD,
    ATTR_TEXML,
    ATTR_TO,
    ATTR_TRANSCRIPTION,
    CONF_API_KEY,
    CONF_MESSAGING_PROFILE_ID,
    CONF_WEBHOOK_ID,
    DOMAIN,
    EVENT_TELNYX,
    EVENT_TELNYX_TRANSCRIPTION,
    PLATFORMS,
    SERVICE_SEND_DTMF,
    SERVICE_SEND_SMS,
    SERVICE_SEND_TEXML,
    SERVICE_SEND_VOICE_API,
    SERVICE_START_RECORDING,
    SERVICE_STOP_RECORDING,
)


@dataclass
class TelnyxRuntimeData:
    """Runtime data for a Telnyx config entry."""

    client: TelnyxClient
    webhook_id: str


TelnyxConfigEntry = ConfigEntry[TelnyxRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Telnyx component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: TelnyxConfigEntry) -> bool:
    """Set up Telnyx from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    runtime_data = TelnyxRuntimeData(
        client=TelnyxClient(
            hass,
            entry.data[CONF_API_KEY],
            entry.data.get(CONF_MESSAGING_PROFILE_ID),
        ),
        webhook_id=entry.data[CONF_WEBHOOK_ID],
    )
    hass.data[DOMAIN][entry.entry_id] = runtime_data
    entry.runtime_data = runtime_data

    webhook.async_register(
        hass,
        DOMAIN,
        f"Telnyx {entry.title}",
        runtime_data.webhook_id,
        _async_handle_webhook,
        allowed_methods=("POST",),
    )

    await _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TelnyxConfigEntry) -> bool:
    """Unload a Telnyx config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        runtime_data = hass.data[DOMAIN].pop(entry.entry_id)
        webhook.async_unregister(hass, runtime_data.webhook_id)
        if not hass.data[DOMAIN]:
            await _async_unregister_services(hass)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: TelnyxConfigEntry) -> None:
    """Reload a Telnyx config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


def _get_runtime_data(hass: HomeAssistant, entry_id: str | None) -> TelnyxRuntimeData:
    """Return runtime data for a service call."""
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        raise ServiceValidationError("No Telnyx configuration entries are loaded")

    if entry_id:
        if entry_id not in entries:
            raise ServiceValidationError(f"Unknown Telnyx entry_id: {entry_id}")
        return entries[entry_id]

    return next(iter(entries.values()))


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register Telnyx services."""
    if hass.services.has_service(DOMAIN, SERVICE_SEND_SMS):
        return

    async def handle_send_sms(call: ServiceCall) -> None:
        runtime_data = _get_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        await runtime_data.client.send_sms(
            call.data[ATTR_TO],
            call.data[ATTR_MESSAGE],
            call.data.get(ATTR_FROM),
        )

    async def handle_send_texml(call: ServiceCall) -> None:
        runtime_data = _get_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        await runtime_data.client.send_texml_call(
            call.data[ATTR_TO],
            call.data[ATTR_TEXML],
            call.data.get(ATTR_FROM),
        )

    async def handle_send_voice_api(call: ServiceCall) -> None:
        runtime_data = _get_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        await runtime_data.client.send_voice_api_call(
            call.data[ATTR_TO],
            call.data[ATTR_MESSAGE],
            call.data.get(ATTR_FROM),
        )

    async def handle_send_dtmf(call: ServiceCall) -> None:
        runtime_data = _get_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        await runtime_data.client.send_dtmf(
            call.data[ATTR_CALL_CONTROL_ID],
            call.data[ATTR_DIGITS],
        )

    async def handle_start_recording(call: ServiceCall) -> None:
        runtime_data = _get_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        await runtime_data.client.start_recording(
            call.data[ATTR_CALL_CONTROL_ID],
            call.data.get(ATTR_FORMAT),
            call.data.get(ATTR_CHANNELS),
        )

    async def handle_stop_recording(call: ServiceCall) -> None:
        runtime_data = _get_runtime_data(hass, call.data.get(ATTR_ENTRY_ID))
        await runtime_data.client.stop_recording(call.data[ATTR_CALL_CONTROL_ID])

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_SMS,
        handle_send_sms,
        schema=vol.Schema(
            {
                vol.Required(ATTR_TO): cv.string,
                vol.Required(ATTR_MESSAGE): cv.string,
                vol.Optional(ATTR_FROM): cv.string,
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TEXML,
        handle_send_texml,
        schema=vol.Schema(
            {
                vol.Required(ATTR_TO): cv.string,
                vol.Required(ATTR_TEXML): cv.string,
                vol.Optional(ATTR_FROM): cv.string,
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_VOICE_API,
        handle_send_voice_api,
        schema=vol.Schema(
            {
                vol.Required(ATTR_TO): cv.string,
                vol.Required(ATTR_MESSAGE): cv.string,
                vol.Optional(ATTR_FROM): cv.string,
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_DTMF,
        handle_send_dtmf,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CALL_CONTROL_ID): cv.string,
                vol.Required(ATTR_DIGITS): cv.string,
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_RECORDING,
        handle_start_recording,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CALL_CONTROL_ID): cv.string,
                vol.Optional(ATTR_FORMAT): cv.string,
                vol.Optional(ATTR_CHANNELS): cv.string,
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_RECORDING,
        handle_stop_recording,
        schema=vol.Schema(
            {
                vol.Required(ATTR_CALL_CONTROL_ID): cv.string,
                vol.Optional(ATTR_ENTRY_ID): cv.string,
            }
        ),
    )


async def _async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister Telnyx services."""
    for service in (
        SERVICE_SEND_SMS,
        SERVICE_SEND_TEXML,
        SERVICE_SEND_VOICE_API,
        SERVICE_SEND_DTMF,
        SERVICE_START_RECORDING,
        SERVICE_STOP_RECORDING,
    ):
        hass.services.async_remove(DOMAIN, service)


async def _async_handle_webhook(
    hass: HomeAssistant,
    webhook_id: str,
    request: web.Request,
) -> web.Response:
    """Handle Telnyx webhook callbacks."""
    payload = await request.json()
    entry_id = next(
        (
            config_entry_id
            for config_entry_id, runtime_data in hass.data.get(DOMAIN, {}).items()
            if runtime_data.webhook_id == webhook_id
        ),
        None,
    )
    event_type = (
        payload.get("data", {}).get("event_type")
        or payload.get("event_type")
        or payload.get("type")
        or "unknown"
    )

    event_data = {
        ATTR_ENTRY_ID: entry_id,
        ATTR_EVENT_TYPE: event_type,
        ATTR_PAYLOAD: payload,
    }
    hass.bus.async_fire(EVENT_TELNYX, event_data)

    transcription = _extract_transcription(payload)
    if transcription is not None:
        hass.bus.async_fire(
            EVENT_TELNYX_TRANSCRIPTION,
            {
                **event_data,
                ATTR_TRANSCRIPTION: transcription,
                ATTR_CALL_CONTROL_ID: _extract_call_control_id(payload),
            },
        )

    return web.json_response({"status": "ok"})


def _extract_call_control_id(payload: dict[str, Any]) -> str | None:
    """Extract a call control ID from a webhook payload."""
    return (
        payload.get("data", {}).get("payload", {}).get("call_control_id")
        or payload.get("data", {}).get("call_control_id")
        or payload.get("call_control_id")
    )


def _extract_transcription(payload: dict[str, Any]) -> str | None:
    """Extract a transcription string from a webhook payload."""
    candidates = (
        payload.get("data", {}).get("payload", {}).get("transcription"),
        payload.get("data", {}).get("payload", {}).get("transcript"),
        payload.get("data", {}).get("payload", {}).get("text"),
        payload.get("data", {}).get("transcription"),
        payload.get("transcription"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return None
