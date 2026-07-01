"""Shared entity base for Dog Assistant entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, Activity
from .coordinator import DogAssistantManager


class DogAssistantEntity(Entity):
    """Base entity: one device per dog, translated names."""

    _attr_has_entity_name = True

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise common attributes for an activity entity."""
        self._manager = manager
        self._activity = activity
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)},
            name=manager.dog_name,
            manufacturer="Dog Assistant",
            model="Dog",
            entry_type=DeviceEntryType.SERVICE,
        )
