"""Tests for the Telnyx API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from custom_components.telnyx.client import TelnyxClient

EXPECTED_HEADERS = {
    "Authorization": "Bearer " + "test-api-key",
    "Content-Type": "application/json",
}
EXPECTED_FORM_HEADERS = {
    "Authorization": "Bearer " + "test-api-key",
    "Content-Type": "application/x-www-form-urlencoded",
}


class _MockResponse:
    """Minimal async response wrapper for client tests."""

    def __init__(self, payload: dict) -> None:
        """Initialize the mock response."""
        self.status = 200
        self.request_info = MagicMock()
        self.history = ()
        self.headers = {}
        self._payload = payload

    async def __aenter__(self):
        """Enter the async response context."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the async response context."""
        return False

    async def json(self, content_type=None):
        """Return JSON payload."""
        return self._payload

    async def text(self):
        """Return payload text."""
        return str(self._payload)


async def test_send_sms_uses_raw_json_payload(hass) -> None:
    """Test that SMS requests are sent as raw Telnyx JSON."""
    requests: list[tuple[str, str, dict]] = []
    session = MagicMock()

    def _request(method, url, **kwargs):
        requests.append((method, url, kwargs))
        return _MockResponse({"data": {"id": "msg-123"}})

    session.request.side_effect = _request

    with patch(
        "custom_components.telnyx.client.async_get_clientsession", return_value=session
    ):
        client = TelnyxClient(hass, "test-api-key", "profile-123", "conn-123")
        await client.send_sms("+15550000002", "hello", "+15550000001")

    assert requests == [
        (
            "post",
            "https://api.telnyx.com/v2/messages",
            {
                "headers": EXPECTED_HEADERS,
                "json": {
                    "to": "+15550000002",
                    "text": "hello",
                    "from": "+15550000001",
                    "messaging_profile_id": "profile-123",
                },
            },
        )
    ]


async def test_send_texml_call_uses_texml_endpoint_and_form_payload(hass) -> None:
    """Test that TeXML calls use the TeXML endpoint and form payload."""
    requests: list[tuple[str, str, dict]] = []
    session = MagicMock()

    def _request(method, url, **kwargs):
        requests.append((method, url, kwargs))
        return _MockResponse({"data": {"call_control_id": "call-123"}})

    session.request.side_effect = _request

    with patch(
        "custom_components.telnyx.client.async_get_clientsession", return_value=session
    ):
        client = TelnyxClient(hass, "test-api-key", None, "conn-123")
        await client.send_texml_call(
            "+15550000004", "<Response />", "+15550000003"
        )

    assert requests == [
        (
            "post",
            "https://api.telnyx.com/v2/texml/calls/conn-123",
            {
                "headers": EXPECTED_FORM_HEADERS,
                "data": {
                    "To": "+15550000004",
                    "Texml": "<Response />",
                    "From": "+15550000003",
                },
            },
        )
    ]


async def test_send_voice_api_call_creates_call_then_speaks(hass) -> None:
    """Test the voice API client flow uses separate create and speak requests."""
    requests: list[tuple[str, str, dict]] = []
    session = MagicMock()
    responses = [
        _MockResponse({"data": {"call_control_id": "call-123"}}),
        _MockResponse({"data": {"result": "queued"}}),
    ]

    def _request(method, url, **kwargs):
        requests.append((method, url, kwargs))
        return responses.pop(0)

    session.request.side_effect = _request

    with patch(
        "custom_components.telnyx.client.async_get_clientsession", return_value=session
    ):
        client = TelnyxClient(hass, "test-api-key", None, "conn-123")
        result = await client.send_voice_api_call(
            "+15550000004", "Hello from Home Assistant", "+15550000003"
        )

    assert result == {
        "call": {"data": {"call_control_id": "call-123"}},
        "speak": {"data": {"result": "queued"}},
    }
    assert requests == [
        (
            "post",
            "https://api.telnyx.com/v2/calls",
            {
                "headers": EXPECTED_HEADERS,
                "json": {
                    "connection_id": "conn-123",
                    "to": "+15550000004",
                    "from": "+15550000003",
                },
            },
        ),
        (
            "post",
            "https://api.telnyx.com/v2/calls/call-123/actions/speak",
            {
                "headers": EXPECTED_HEADERS,
                "json": {
                    "payload": "Hello from Home Assistant",
                    "payload_type": "text",
                },
            },
        ),
    ]
