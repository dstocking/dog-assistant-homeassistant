"""Setup/unload, entity creation, diagnostics and storage-load tests."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dog_assistant.const import DOMAIN
from custom_components.dog_assistant.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.dog_assistant.services import async_register_services


async def test_setup_and_unload(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """The entry loads and unloads cleanly."""
    assert setup_entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.NOT_LOADED


async def test_entities_created(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    get_entity_id: Callable[[str, str], str | None],
) -> None:
    """Scheduled activities get full entities; log activities do not get target ones."""
    assert get_entity_id("button", "feeding_button")
    assert get_entity_id("sensor", "feeding_today")
    assert get_entity_id("sensor", "feeding_last")
    assert get_entity_id("sensor", "feeding_remaining")
    assert get_entity_id("binary_sensor", "feeding_due")
    assert get_entity_id("event", "feeding_event")

    assert get_entity_id("button", "poo_button")
    assert get_entity_id("sensor", "poo_today")
    assert get_entity_id("event", "poo_event")
    # poo/pee have no target, so no remaining/due entities
    assert get_entity_id("sensor", "poo_remaining") is None
    assert get_entity_id("binary_sensor", "poo_due") is None


async def test_diagnostics(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Diagnostics reflect current state and recent log."""
    await setup_entry.runtime_data.manager.async_record("feeding", portion="1 cup")
    diag = await async_get_config_entry_diagnostics(hass, setup_entry)
    assert diag["name"] == "Joie"
    assert diag["activities"]["feeding"]["count_today"] == 1
    assert diag["activities"]["feeding"]["target"] == 2
    assert diag["activities"]["feeding"]["remaining"] == 1
    assert diag["activities"]["feeding"]["due"] is True
    assert diag["activities"]["poo"]["last"] is None
    assert len(diag["recent"]) == 1


async def test_load_skips_invalid_entries(
    hass: HomeAssistant, mock_entry: MockConfigEntry
) -> None:
    """A malformed stored entry is dropped on load."""
    mock_entry.add_to_hass(hass)
    store: Store[dict] = Store(hass, 1, f"{DOMAIN}.{mock_entry.entry_id}")
    await store.async_save(
        {
            "log": [
                {"bad": 1},
                {"activity": "pee", "ts": dt_util.now().isoformat()},
            ]
        }
    )
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    manager = mock_entry.runtime_data.manager
    assert manager.count_today("pee") == 1


async def test_register_services_idempotent(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Re-registering services is a no-op."""
    async_register_services(hass)
    assert hass.services.has_service(DOMAIN, "record_feeding")
