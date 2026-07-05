"""Tests for Telnyx setup and services."""

import base64
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from homeassistant.helpers import entity_registry as er

from custom_components.telnyx import _async_handle_webhook
from custom_components.telnyx.const import (
    ATTR_CALL_CONTROL_ID,
    ATTR_DIGITS,
    ATTR_MESSAGE,
    ATTR_TEXML,
    ATTR_TO,
    DOMAIN,
    EVENT_TELNYX,
    EVENT_TELNYX_TRANSCRIPTION,
    SERVICE_SEND_DTMF,
    SERVICE_SEND_SMS,
    SERVICE_SEND_TEXML,
    SERVICE_SEND_VOICE_API,
    SERVICE_START_RECORDING,
    SERVICE_STOP_RECORDING,
)


async def test_setup_entry_registers_entities_and_services(hass, config_entry) -> None:
    """Test config entry setup."""
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    assert {entry.unique_id for entry in entries} == {
        "entry-1_messaging",
        "entry-1_voice_api",
        "entry-1_voice_texml",
    }

    for service in (
        SERVICE_SEND_SMS,
        SERVICE_SEND_TEXML,
        SERVICE_SEND_VOICE_API,
        SERVICE_SEND_DTMF,
        SERVICE_START_RECORDING,
        SERVICE_STOP_RECORDING,
    ):
        assert hass.services.has_service(DOMAIN, service)


async def test_setup_entry_only_creates_configured_entities(
    hass, config_entry_messaging_only
) -> None:
    """Test that only entities for configured features are created."""
    config_entry_messaging_only.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry_messaging_only.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, config_entry_messaging_only.entry_id
    )
    unique_ids = {entry.unique_id for entry in entries}
    assert unique_ids == {"entry-2_messaging"}
    assert "entry-2_voice_api" not in unique_ids
    assert "entry-2_voice_texml" not in unique_ids


def _entity_id_by_unique_id(hass, config_entry, unique_id: str) -> str:
    """Look up an entity_id by unique_id."""
    entity_registry = er.async_get(hass)
    for entry in er.async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        if entry.unique_id == unique_id:
            return entry.entity_id
    raise AssertionError(f"Could not find entity for {unique_id}")


def _signed_request(private_key: Ed25519PrivateKey, payload: str) -> SimpleNamespace:
    """Build a signed webhook request."""
    timestamp = str(int(time.time()))
    signature = base64.b64encode(
        private_key.sign(f"{timestamp}|{payload}".encode("utf-8"))
    ).decode("utf-8")
    return SimpleNamespace(
        headers={
            "telnyx-timestamp": timestamp,
            "telnyx-signature-ed25519": signature,
        },
        text=AsyncMock(return_value=payload),
    )


async def test_notify_entities_send_messages(hass, config_entry) -> None:
    """Test Telnyx notify entities."""
    with (
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_sms",
            new=AsyncMock(),
        ) as send_sms,
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_texml_call",
            new=AsyncMock(),
        ) as send_texml,
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_voice_api_call",
            new=AsyncMock(),
        ) as send_voice_api,
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        messaging_entity_id = _entity_id_by_unique_id(
            hass, config_entry, "entry-1_messaging"
        )
        texml_entity_id = _entity_id_by_unique_id(
            hass, config_entry, "entry-1_voice_texml"
        )
        voice_api_entity_id = _entity_id_by_unique_id(
            hass, config_entry, "entry-1_voice_api"
        )

        await hass.services.async_call(
            "notify",
            "send_message",
            {ATTR_MESSAGE: "Hello", "title": "Alert"},
            target={"entity_id": messaging_entity_id},
            blocking=True,
        )
        await hass.services.async_call(
            "notify",
            "send_message",
            {ATTR_MESSAGE: "<Response><Say>Hello</Say></Response>"},
            target={"entity_id": texml_entity_id},
            blocking=True,
        )
        await hass.services.async_call(
            "notify",
            "send_message",
            {ATTR_MESSAGE: "Hello"},
            target={"entity_id": voice_api_entity_id},
            blocking=True,
        )

    send_sms.assert_awaited_once_with("+15550000002", "Alert: Hello", "+15550000001")
    send_texml.assert_awaited_once_with(
        "+15550000004",
        "<Response><Say>Hello</Say></Response>",
        "+15550000003",
    )
    send_voice_api.assert_awaited_once_with("+15550000004", "Hello", "+15550000003")


async def test_services_and_webhook_events(hass, config_entry, webhook_keys) -> None:
    """Test domain services and transcription webhook events."""
    private_key, _ = webhook_keys
    with (
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_sms",
            new=AsyncMock(),
        ) as send_sms,
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_texml_call",
            new=AsyncMock(),
        ) as send_texml,
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_voice_api_call",
            new=AsyncMock(),
        ) as send_voice_api,
        patch(
            "custom_components.telnyx.client.TelnyxClient.send_dtmf",
            new=AsyncMock(),
        ) as send_dtmf,
        patch(
            "custom_components.telnyx.client.TelnyxClient.start_recording",
            new=AsyncMock(),
        ) as start_recording,
        patch(
            "custom_components.telnyx.client.TelnyxClient.stop_recording",
            new=AsyncMock(),
        ) as stop_recording,
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_SMS,
            {ATTR_TO: "+1", ATTR_MESSAGE: "hello"},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_TEXML,
            {ATTR_TO: "+2", ATTR_TEXML: "<Response />"},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VOICE_API,
            {ATTR_TO: "+3", ATTR_MESSAGE: "speak"},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_DTMF,
            {ATTR_CALL_CONTROL_ID: "call-1", ATTR_DIGITS: "1234"},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_RECORDING,
            {ATTR_CALL_CONTROL_ID: "call-2", "format": "mp3", "channels": "dual"},
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP_RECORDING,
            {ATTR_CALL_CONTROL_ID: "call-3"},
            blocking=True,
        )

        telnyx_events = []
        transcription_events = []
        hass.bus.async_listen(EVENT_TELNYX, telnyx_events.append)
        hass.bus.async_listen(EVENT_TELNYX_TRANSCRIPTION, transcription_events.append)

        payload = (
            '{"data":{"event_type":"call.transcription","payload":'
            '{"call_control_id":"call-4","transcription":"press one"}}}'
        )
        request = _signed_request(private_key, payload)
        response = await _async_handle_webhook(hass, "webhook-123", request)
        await hass.async_block_till_done()

    assert response.status == 200
    send_sms.assert_awaited_once_with("+1", "hello", None)
    send_texml.assert_awaited_once_with("+2", "<Response />", None)
    send_voice_api.assert_awaited_once_with("+3", "speak", None)
    send_dtmf.assert_awaited_once_with("call-1", "1234")
    start_recording.assert_awaited_once_with("call-2", "mp3", "dual")
    stop_recording.assert_awaited_once_with("call-3")
    assert len(telnyx_events) == 1
    assert telnyx_events[0].data["event_type"] == "call.transcription"
    assert len(transcription_events) == 1
    assert transcription_events[0].data["transcription"] == "press one"
    assert transcription_events[0].data["call_control_id"] == "call-4"
