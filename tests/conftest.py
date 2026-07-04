"""Shared fixtures for Telnyx tests."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.telnyx.const import (
    CONF_API_KEY,
    CONF_DEFAULT_MESSAGING_FROM,
    CONF_DEFAULT_MESSAGING_TO,
    CONF_DEFAULT_VOICE_FROM,
    CONF_DEFAULT_VOICE_TO,
    CONF_WEBHOOK_ID,
    DOMAIN,
)


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Create a Telnyx config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Telnyx",
        entry_id="entry-1",
        data={
            CONF_API_KEY: "test-api-key",
            CONF_DEFAULT_MESSAGING_FROM: "+15550000001",
            CONF_DEFAULT_MESSAGING_TO: "+15550000002",
            CONF_DEFAULT_VOICE_FROM: "+15550000003",
            CONF_DEFAULT_VOICE_TO: "+15550000004",
            CONF_WEBHOOK_ID: "webhook-123",
        },
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading integrations from this repository."""
    yield
