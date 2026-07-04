"""Tests for the Telnyx config flow."""

from custom_components.telnyx.const import CONF_WEBHOOK_ID, DOMAIN


async def test_user_flow_creates_entry(hass, webhook_keys) -> None:
    """Test the user config flow."""
    _, public_key = webhook_keys
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            "api_key": "secret",
            "webhook_public_key": public_key,
            "default_messaging_to": "+15550000002",
            "default_voice_to": "+15550000004",
        },
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Telnyx"
    assert result["data"]["api_key"] == "secret"
    assert result["data"][CONF_WEBHOOK_ID]
