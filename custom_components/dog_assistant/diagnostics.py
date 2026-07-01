"""Diagnostics for Dog Assistant."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import ACTIVITIES
from .coordinator import DogAssistantConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: DogAssistantConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    manager = entry.runtime_data.manager
    activities: dict[str, Any] = {}
    for activity in ACTIVITIES:
        last = manager.last_time(activity.key)
        info: dict[str, Any] = {
            "count_today": manager.count_today(activity.key),
            "last": last.isoformat() if last else None,
        }
        if activity.has_target:
            info["target"] = manager.target(activity.key)
            info["remaining"] = manager.remaining(activity.key)
            info["due"] = manager.due(activity.key)
        activities[activity.key] = info

    return {
        "name": manager.dog_name,
        "options": dict(entry.options),
        "activities": activities,
        "recent": manager.recent(),
    }
