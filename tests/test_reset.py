"""Daily period, persistence and helper tests for the manager."""

from __future__ import annotations

from datetime import time, timedelta

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dog_assistant.const import (
    DOMAIN,
    MAX_LOG_ENTRIES,
    parse_reset_time,
)
from custom_components.dog_assistant.coordinator import DogAssistantManager


def test_parse_reset_time() -> None:
    """Valid strings parse; invalid ones fall back to midnight."""
    assert parse_reset_time("06:30:15") == time(6, 30, 15)
    assert parse_reset_time("06:30") == time(6, 30, 0)
    assert parse_reset_time("nonsense") == time(0, 0, 0)


async def test_count_ignores_previous_periods(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Only records within the current period are counted."""
    manager = setup_entry.runtime_data.manager
    old = (dt_util.now() - timedelta(days=2)).isoformat()
    now = dt_util.now().isoformat()
    manager._log.extend(
        [
            {"activity": "feeding", "ts": old},
            {"activity": "feeding", "ts": now},
        ]
    )
    assert manager.count_today("feeding") == 1
    assert manager.last_time("feeding") is not None


async def test_target_falls_back_on_bad_value(hass: HomeAssistant) -> None:
    """A non-numeric target option falls back to the default."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "X"},
        options={"feeding_target": "oops"},
    )
    entry.add_to_hass(hass)
    manager = DogAssistantManager(hass, entry, Store(hass, 1, "t"))
    assert manager.target("feeding") == 2


async def test_reset_handler_refreshes(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """The reset handler notifies listeners without error."""
    manager = setup_entry.runtime_data.manager
    await manager.async_record("feeding")
    await hass.async_block_till_done()
    manager._handle_reset(dt_util.now())
    await hass.async_block_till_done()


async def test_persistence_across_reload(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """The event log survives a reload."""
    manager = setup_entry.runtime_data.manager
    await manager.async_record("walk", walked_by="Dana")
    # Force a synchronous write rather than waiting for the debounced save.
    await manager._store.async_save(manager._data_to_save())

    assert await hass.config_entries.async_reload(setup_entry.entry_id)
    await hass.async_block_till_done()

    reloaded = setup_entry.runtime_data.manager
    assert reloaded.count_today("walk") == 1


async def test_log_is_pruned(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """The stored log is capped at MAX_LOG_ENTRIES."""
    manager = setup_entry.runtime_data.manager
    ts = dt_util.now().isoformat()
    manager._log.extend(
        {"activity": "pee", "ts": ts} for _ in range(MAX_LOG_ENTRIES + 5)
    )
    await manager.async_record("pee")
    assert len(manager._log) == MAX_LOG_ENTRIES
