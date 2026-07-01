"""Event platform tests."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dog_assistant.const import DOMAIN


async def test_event_fires_with_details(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """Recording a feeding triggers the event entity with detail attributes."""
    event = get_entity_id("event", "feeding_event")
    assert event
    assert hass.states.get(event).state == STATE_UNKNOWN

    await hass.services.async_call(
        DOMAIN,
        "record_feeding",
        {"portion": "1 cup", "food": "kibble", "fed_by": "Dana"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(event)
    assert state.state != STATE_UNKNOWN
    assert state.attributes["event_type"] == "recorded"
    assert state.attributes["portion"] == "1 cup"
    assert state.attributes["fed_by"] == "Dana"
