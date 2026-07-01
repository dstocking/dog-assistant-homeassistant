"""Service action tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dog_assistant.const import DOMAIN


async def test_record_walk_with_numbers(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """Numeric detail fields are accepted."""
    today = get_entity_id("sensor", "walk_today")
    assert today
    await hass.services.async_call(
        DOMAIN,
        "record_walk",
        {"duration": 30, "distance": 2.5, "walked_by": "Dana"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(today).state == "1"


async def test_record_poo_with_quality(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """The select detail field is accepted."""
    today = get_entity_id("sensor", "poo_today")
    assert today
    await hass.services.async_call(
        DOMAIN,
        "record_poo",
        {"quality": "soft", "location": "yard"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(today).state == "1"


async def test_record_pee_minimal(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """A record with no details still works."""
    today = get_entity_id("sensor", "pee_today")
    assert today
    await hass.services.async_call(DOMAIN, "record_pee", {}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(today).state == "1"


async def test_service_when_not_loaded(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Calling a service with no loaded entry raises a clear error."""
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "record_pee", {}, blocking=True)
