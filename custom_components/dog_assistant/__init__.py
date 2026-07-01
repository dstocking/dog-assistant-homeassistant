"""The Dog Assistant integration."""

from __future__ import annotations

from typing import Any

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, STORAGE_VERSION
from .coordinator import (
    DogAssistantConfigEntry,
    DogAssistantData,
    DogAssistantManager,
)
from .services import async_register_services

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.SENSOR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register services once for the integration."""
    async_register_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: DogAssistantConfigEntry
) -> bool:
    """Set up Dog Assistant from a config entry."""
    store: Store[dict[str, Any]] = Store(
        hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
    )
    manager = DogAssistantManager(hass, entry, store)
    await manager.async_load()
    entry.runtime_data = DogAssistantData(store=store, manager=manager)

    manager.async_schedule_reset()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DogAssistantConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
