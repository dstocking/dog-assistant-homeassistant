"""Event platform: fires a discrete Logbook entry each time an activity is recorded."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ACTIVITIES, EVENT_RECORDED, Activity
from .coordinator import DogAssistantConfigEntry, DogAssistantManager
from .entity import DogAssistantEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DogAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the per-activity event entities."""
    manager = entry.runtime_data.manager
    async_add_entities(
        ActivityEventEntity(manager, activity) for activity in ACTIVITIES
    )


class ActivityEventEntity(DogAssistantEntity, EventEntity):
    """Fires whenever its activity is recorded, carrying any detail fields."""

    _attr_event_types = [EVENT_RECORDED]

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise the event entity."""
        super().__init__(manager, activity)
        self._attr_unique_id = f"{manager.entry.entry_id}_{activity.key}_event"
        self._attr_translation_key = f"{activity.key}_event"

    async def async_added_to_hass(self) -> None:
        """Subscribe to record events for this activity."""
        self.async_on_remove(
            self._manager.register_event_callback(self._activity.key, self._handle)
        )

    @callback
    def _handle(self, event_type: str, details: dict[str, Any]) -> None:
        self._trigger_event(event_type, details)
        self.async_write_ha_state()
