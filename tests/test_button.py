"""Button platform tests."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_feed_button_records(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """Pressing the feed button updates the derived sensors."""
    button = get_entity_id("button", "feeding_button")
    today = get_entity_id("sensor", "feeding_today")
    remaining = get_entity_id("sensor", "feeding_remaining")
    last = get_entity_id("sensor", "feeding_last")
    assert button and today and remaining and last

    assert hass.states.get(today).state == "0"
    assert hass.states.get(remaining).state == "2"
    assert hass.states.get(last).state == STATE_UNKNOWN

    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: button}, blocking=True
    )
    await hass.async_block_till_done()

    assert hass.states.get(today).state == "1"
    assert hass.states.get(remaining).state == "1"
    assert hass.states.get(last).state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
