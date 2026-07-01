"""Shared fixtures for Dog Assistant tests."""

from __future__ import annotations

from collections.abc import Callable, Generator

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dog_assistant.const import CONF_RESET_TIME, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Enable loading the custom integration in every test."""
    yield


@pytest.fixture
def mock_entry() -> MockConfigEntry:
    """A config entry for a dog named Joie with default targets."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Joie",
        data={CONF_NAME: "Joie"},
        options={
            "feeding_target": 2,
            "walk_target": 2,
            CONF_RESET_TIME: "00:00:00",
        },
    )


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, mock_entry: MockConfigEntry
) -> MockConfigEntry:
    """Add and set up the config entry."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    return mock_entry


@pytest.fixture
def get_entity_id(hass: HomeAssistant) -> Callable[[str, str], str | None]:
    """Resolve an entity_id from its unique-id suffix."""

    def _get(platform: str, suffix: str) -> str | None:
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        registry = er.async_get(hass)
        return registry.async_get_entity_id(
            platform, DOMAIN, f"{entry.entry_id}_{suffix}"
        )

    return _get
