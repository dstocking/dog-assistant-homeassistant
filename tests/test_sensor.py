"""Sensor platform tests."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_initial_sensor_states(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """Counters start at zero, remaining at the target, last unknown."""
    for activity in ("feeding", "walk", "poo", "pee"):
        today = get_entity_id("sensor", f"{activity}_today")
        last = get_entity_id("sensor", f"{activity}_last")
        assert today and last
        assert hass.states.get(today).state == "0"
        assert hass.states.get(last).state == STATE_UNKNOWN
        assert (
            hass.states.get(last).attributes[ATTR_DEVICE_CLASS]
            == SensorDeviceClass.TIMESTAMP
        )

    walk_remaining = get_entity_id("sensor", "walk_remaining")
    assert walk_remaining
    assert hass.states.get(walk_remaining).state == "2"


async def test_last_sensor_updates(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """Recording an activity sets its last-time timestamp sensor."""
    last = get_entity_id("sensor", "pee_last")
    assert last
    await setup_entry.runtime_data.manager.async_record("pee", location="yard")
    await hass.async_block_till_done()
    assert hass.states.get(last).state != STATE_UNKNOWN
