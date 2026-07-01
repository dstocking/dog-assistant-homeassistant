"""Sensor platform: today's count, last time, and remaining per activity."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
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
    """Set up the activity sensors."""
    manager = entry.runtime_data.manager
    entities: list[SensorEntity] = []
    for activity in ACTIVITIES:
        entities.append(ActivityTodaySensor(manager, activity))
        entities.append(ActivityLastSensor(manager, activity))
        if activity.has_target:
            entities.append(ActivityRemainingSensor(manager, activity))
    async_add_entities(entities)


class _StatefulSensor(DogAssistantEntity, SensorEntity):
    """A sensor that refreshes whenever the manager changes."""

    async def async_added_to_hass(self) -> None:
        """Subscribe to manager updates."""
        self.async_on_remove(
            self._manager.register_listener(self.async_write_ha_state)
        )


class ActivityTodaySensor(_StatefulSensor):
    """Count of an activity recorded in the current daily period."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise the today-count sensor."""
        super().__init__(manager, activity)
        self._attr_unique_id = f"{manager.entry.entry_id}_{activity.key}_today"
        self._attr_translation_key = f"{activity.key}_today"

    @property
    def native_value(self) -> int:
        """Number of times recorded today."""
        return self._manager.count_today(self._activity.key)


class ActivityLastSensor(_StatefulSensor):
    """Timestamp of the most recent record of an activity."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise the last-time sensor."""
        super().__init__(manager, activity)
        self._attr_unique_id = f"{manager.entry.entry_id}_{activity.key}_last"
        self._attr_translation_key = f"last_{activity.key}"

    @property
    def native_value(self) -> datetime | None:
        """When the activity was last recorded."""
        return self._manager.last_time(self._activity.key)


class ActivityRemainingSensor(_StatefulSensor):
    """How many more times a scheduled activity is expected today."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: DogAssistantManager, activity: Activity) -> None:
        """Initialise the remaining sensor."""
        super().__init__(manager, activity)
        self._attr_unique_id = f"{manager.entry.entry_id}_{activity.key}_remaining"
        self._attr_translation_key = f"{activity.key}_remaining"

    @property
    def native_value(self) -> int:
        """Records still expected today."""
        return self._manager.remaining(self._activity.key)
