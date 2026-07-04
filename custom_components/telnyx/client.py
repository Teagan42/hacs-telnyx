"""Telnyx API client."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientResponseError

from homeassistant.helpers.aiohttp_client import async_get_clientsession


class TelnyxClient:
    """Small Telnyx API client used by the integration."""

    def __init__(self, hass, api_key: str, messaging_profile_id: str | None = None) -> None:
        """Initialize the client."""
        self._hass = hass
        self._api_key = api_key
        self._messaging_profile_id = messaging_profile_id

    async def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Perform an API request."""
        session = async_get_clientsession(self._hass)
        async with session.request(
            method,
            f"https://api.telnyx.com/v2{path}",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={"data": payload},
        ) as response:
            if response.status >= 400:
                raise ClientResponseError(
                    response.request_info,
                    response.history,
                    status=response.status,
                    message=await response.text(),
                    headers=response.headers,
                )
            return await response.json(content_type=None)

    async def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: str | None = None,
    ) -> dict[str, Any]:
        """Send an SMS message."""
        payload: dict[str, Any] = {"to": to_number, "text": message}
        if from_number:
            payload["from"] = from_number
        if self._messaging_profile_id:
            payload["messaging_profile_id"] = self._messaging_profile_id
        return await self._request("post", "/messages", payload)

    async def send_texml_call(
        self,
        to_number: str,
        texml: str,
        from_number: str | None = None,
    ) -> dict[str, Any]:
        """Start a voice call backed by TexML."""
        payload: dict[str, Any] = {"to": to_number, "texml": texml}
        if from_number:
            payload["from"] = from_number
        return await self._request("post", "/calls/texml", payload)

    async def send_voice_api_call(
        self,
        to_number: str,
        message: str,
        from_number: str | None = None,
    ) -> dict[str, Any]:
        """Start a voice API call with a speak command."""
        payload: dict[str, Any] = {
            "to": to_number,
            "command": "speak",
            "payload": {"text": message},
        }
        if from_number:
            payload["from"] = from_number
        return await self._request("post", "/calls", payload)

    async def send_dtmf(self, call_control_id: str, digits: str) -> dict[str, Any]:
        """Send DTMF digits to an active call."""
        return await self._request(
            "post",
            f"/calls/{call_control_id}/actions/send_dtmf",
            {"digits": digits},
        )

    async def start_recording(
        self,
        call_control_id: str,
        recording_format: str | None = None,
        channels: str | None = None,
    ) -> dict[str, Any]:
        """Start call recording."""
        payload: dict[str, Any] = {}
        if recording_format:
            payload["format"] = recording_format
        if channels:
            payload["channels"] = channels
        return await self._request(
            "post",
            f"/calls/{call_control_id}/actions/record_start",
            payload,
        )

    async def stop_recording(self, call_control_id: str) -> dict[str, Any]:
        """Stop call recording."""
        return await self._request(
            "post",
            f"/calls/{call_control_id}/actions/record_stop",
            {},
        )
