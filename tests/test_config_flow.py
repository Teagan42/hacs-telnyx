"""Tests for the Telnyx config flow."""

from custom_components.telnyx.const import CONF_WEBHOOK_ID, DOMAIN


async def test_user_flow_creates_entry(hass, webhook_keys) -> None:
    """Test the menu-driven user config flow."""
    _, public_key = webhook_keys

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "common"},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "common"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "secret",
            "webhook_public_key": public_key,
            "step_action": "save",
        },
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "voice"},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "voice"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        data={
            "call_control_connection_id": "conn-123",
            "default_voice_to": "+15550000004",
            "step_action": "save",
        },
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "messaging"},
    )
    assert result["type"] == "form"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "default_messaging_to": "+15550000002",
            "step_action": "save",
        },
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "done"},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Telnyx"
    assert result["data"]["api_key"] == "secret"
    assert result["data"]["call_control_connection_id"] == "conn-123"
    assert result["data"]["default_voice_to"] == "+15550000004"
    assert result["data"]["default_messaging_to"] == "+15550000002"
    assert result["data"][CONF_WEBHOOK_ID]


async def test_flow_back_from_subsection_returns_menu(hass, webhook_keys) -> None:
    """Test subsection back returns to menu and does not save values."""
    _, public_key = webhook_keys
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "messaging"},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "messaging"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "default_messaging_to": "+15550000003",
            "step_action": "back",
        },
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "common"},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "common"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "secret",
            "webhook_public_key": public_key,
            "step_action": "save",
        },
    )
    assert result["type"] == "menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "done"},
    )
    assert result["type"] == "create_entry"
    assert "default_messaging_to" not in result["data"]
