"""Telnyx API client."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientResponseError

from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class TelnyxClient:
    """Small Telnyx API client used by the integration."""

    def __init__(
        self,
        hass,
        api_key: str,
        messaging_profile_id: str | None = None,
        call_control_connection_id: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._hass = hass
        self._api_key = api_key
        self._messaging_profile_id = messaging_profile_id
        self._call_control_connection_id = call_control_connection_id

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
            json=payload,
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

    def _require_connection_id(self) -> str:
        """Return the configured Call Control connection ID."""
        if not self._call_control_connection_id:
            raise ServiceValidationError(
                "Configure a Call Control connection ID in the Telnyx config entry"
            )
        return self._call_control_connection_id

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
        """Start a voice call backed by TeXML."""
        payload: dict[str, Any] = {
            "connection_id": self._require_connection_id(),
            "to": to_number,
            "texml": texml,
        }
        if from_number:
            payload["from"] = from_number
        return await self._request("post", "/calls", payload)

    async def send_voice_api_call(
        self,
        to_number: str,
        message: str,
        from_number: str | None = None,
    ) -> dict[str, Any]:
        """Start a voice API call and speak text into it."""
        payload: dict[str, Any] = {
            "connection_id": self._require_connection_id(),
            "to": to_number,
        }
        if from_number:
            payload["from"] = from_number
        call_response = await self._request("post", "/calls", payload)
        call_control_id = (
            call_response.get("data", {}).get("call_control_id")
            or call_response.get("data", {}).get("id")
            or call_response.get("call_control_id")
        )
        if not call_control_id:
            raise ServiceValidationError("Telnyx did not return a call_control_id")

        speak_response = await self._request(
            "post",
            f"/calls/{call_control_id}/actions/speak",
            {"payload": message, "payload_type": "text"},
        )
        return {"call": call_response, "speak": speak_response}

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
