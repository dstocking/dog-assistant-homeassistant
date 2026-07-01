"""Binary sensor platform: whether a scheduled activity is still due today."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import TARGET_ACTIVITIES, Activity
from .coordinator import DogAssistantConfigEntry, DogAssistantManager
from .entity import DogAssistantEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DogAssistantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the 'due' binary sensors for scheduled activities."""
    manager = entry.runtime_data.manager
    async_add_entities(
        ActivityDueBinarySensor(manager, activity) for activity in TARGET_ACTIVITIES
    )


class ActivityDueBinarySensor(DogAssistantEntity, BinarySensorEntity):
    """On while a scheduled activity still needs doing today."""

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise the due binary sensor."""
        super().__init__(manager, activity)
        self._attr_unique_id = f"{manager.entry.entry_id}_{activity.key}_due"
        self._attr_translation_key = f"{activity.key}_due"

    async def async_added_to_hass(self) -> None:
        """Subscribe to manager updates."""
        self.async_on_remove(
            self._manager.register_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Whether the activity is still due."""
        return self._manager.due(self._activity.key)
