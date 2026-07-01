"""Config and options flow tests (targets 100% coverage of config_flow.py)."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dog_assistant.const import (
    CONF_RESET_TIME,
    DEFAULT_RESET_TIME,
    DOMAIN,
)


async def test_user_flow(hass: HomeAssistant) -> None:
    """A full user flow creates an entry with data + options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: "Joie", "feeding_target": 3, "walk_target": 1},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Joie"
    assert result["data"] == {CONF_NAME: "Joie"}
    assert result["options"]["feeding_target"] == 3
    assert result["options"]["walk_target"] == 1
    assert result["options"][CONF_RESET_TIME] == DEFAULT_RESET_TIME


async def test_single_instance(
    hass: HomeAssistant, mock_entry: MockConfigEntry
) -> None:
    """A second entry is not allowed."""
    mock_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_reconfigure(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Reconfigure renames the dog."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": setup_entry.entry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Rex"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert setup_entry.data[CONF_NAME] == "Rex"


async def test_options_flow(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Options flow updates targets and reset time."""
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"feeding_target": 4, "walk_target": 1, CONF_RESET_TIME: "06:00:00"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert setup_entry.options["feeding_target"] == 4
    assert setup_entry.options[CONF_RESET_TIME] == "06:00:00"
