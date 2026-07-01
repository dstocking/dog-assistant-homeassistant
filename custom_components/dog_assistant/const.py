"""Constants and the activity registry for the Dog Assistant integration.

Every entity, service and translation in this integration is generated from the
``ACTIVITIES`` registry below, so adding a new tracked activity (for example
``"meds"``) is a single entry here plus the matching translation strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

DOMAIN = "dog_assistant"

# Persistent store (``.storage/dog_assistant.<entry_id>``).
STORAGE_VERSION = 1
# Debounce window for writing the event log to disk.
SAVE_DELAY = 10

# How much history to keep in the persistent log.
MAX_LOG_ENTRIES = 5000

# Config entry data / options keys.
CONF_RESET_TIME = "reset_time"
DEFAULT_RESET_TIME = "00:00:00"


def target_option(activity_key: str) -> str:
    """Return the options key holding the daily target for an activity."""
    return f"{activity_key}_target"


# Event type fired by every activity's event entity.
EVENT_RECORDED = "recorded"


@dataclass(frozen=True)
class DetailField:
    """An optional detail that can be attached to a recorded activity."""

    name: str
    # Selector kind used both for the service schema and services.yaml.
    kind: str = "text"  # "text" | "number" | "select"
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class Activity:
    """One tracked activity (feeding, walk, poo, pee, ...)."""

    key: str
    #: Whether the activity has a configurable per-day target (and therefore
    #: gains "remaining" and "due" entities).
    has_target: bool = False
    default_target: int = 0
    details: tuple[DetailField, ...] = field(default_factory=tuple)

    @property
    def service_name(self) -> str:
        """Name of the ``record_*`` service action for this activity."""
        return f"record_{self.key}"


ACTIVITIES: tuple[Activity, ...] = (
    Activity(
        key="feeding",
        has_target=True,
        default_target=2,
        details=(
            DetailField("portion"),
            DetailField("food"),
            DetailField("fed_by"),
        ),
    ),
    Activity(
        key="walk",
        has_target=True,
        default_target=2,
        details=(
            DetailField("duration", kind="number"),
            DetailField("distance", kind="number"),
            DetailField("walked_by"),
        ),
    ),
    Activity(
        key="poo",
        details=(
            DetailField(
                "quality",
                kind="select",
                options=("normal", "soft", "hard", "diarrhea"),
            ),
            DetailField("location"),
            DetailField("notes"),
        ),
    ),
    Activity(
        key="pee",
        details=(
            DetailField("location"),
            DetailField("notes"),
        ),
    ),
)

ACTIVITIES_BY_KEY: dict[str, Activity] = {a.key: a for a in ACTIVITIES}
TARGET_ACTIVITIES: tuple[Activity, ...] = tuple(a for a in ACTIVITIES if a.has_target)


def parse_reset_time(raw: str) -> time:
    """Parse an ``HH:MM:SS`` reset-time string, falling back to midnight."""
    parts = raw.split(":")
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
        return time(hour=hour, minute=minute, second=second)
    except (ValueError, IndexError):
        return time(0, 0, 0)
