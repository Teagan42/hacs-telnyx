"""Shared fixtures for Telnyx tests."""

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.telnyx.const import (
    CONF_API_KEY,
    CONF_DEFAULT_MESSAGING_FROM,
    CONF_DEFAULT_MESSAGING_TO,
    CONF_DEFAULT_VOICE_FROM,
    CONF_DEFAULT_VOICE_TO,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_PUBLIC_KEY,
    DOMAIN,
)


@pytest.fixture
def webhook_keys() -> tuple[Ed25519PrivateKey, str]:
    """Create a webhook signing keypair."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, base64.b64encode(public_key).decode("utf-8")


@pytest.fixture
def config_entry(webhook_keys) -> MockConfigEntry:
    """Create a Telnyx config entry."""
    _, public_key = webhook_keys
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
            CONF_WEBHOOK_PUBLIC_KEY: public_key,
        },
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading integrations from this repository."""
    yield
