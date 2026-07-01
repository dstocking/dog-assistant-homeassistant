"""Button platform: one 'record now' button per activity."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ACTIVITIES, Activity
from .coordinator import DogAssistantConfigEntry, DogAssistantManager
from .entity import DogAssistantEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DogAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the activity buttons."""
    manager = entry.runtime_data.manager
    async_add_entities(ActivityButton(manager, activity) for activity in ACTIVITIES)


class ActivityButton(DogAssistantEntity, ButtonEntity):
    """Press to record an activity at the current time."""

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise the button for an activity."""
        super().__init__(manager, activity)
        self._attr_unique_id = f"{manager.entry.entry_id}_{activity.key}_button"
        self._attr_translation_key = activity.key

    async def async_press(self) -> None:
        """Record the activity now."""
        await self._manager.async_record(self._activity.key)
