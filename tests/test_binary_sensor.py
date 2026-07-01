"""Binary sensor platform tests."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_due_clears_at_target(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """'Due' is on until the daily target is met."""
    due = get_entity_id("binary_sensor", "feeding_due")
    button = get_entity_id("button", "feeding_button")
    assert due and button

    assert hass.states.get(due).state == STATE_ON
    for _ in range(2):  # target is 2
        await hass.services.async_call(
            BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: button}, blocking=True
        )
    await hass.async_block_till_done()
    assert hass.states.get(due).state == STATE_OFF
