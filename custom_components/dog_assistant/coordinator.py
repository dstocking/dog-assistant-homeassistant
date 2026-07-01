"""Runtime state manager for the Dog Assistant integration.

This is intentionally *not* a :class:`DataUpdateCoordinator` — there is nothing
to poll. Instead the manager holds the persistent event log, derives the current
per-activity counts/timestamps from it, and notifies subscribed entities when a
new activity is recorded or the daily period rolls over.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ACTIVITIES_BY_KEY,
    CONF_RESET_TIME,
    DEFAULT_RESET_TIME,
    EVENT_RECORDED,
    MAX_LOG_ENTRIES,
    SAVE_DELAY,
    parse_reset_time,
    target_option,
)

type DogAssistantConfigEntry = ConfigEntry[DogAssistantData]

# One recorded activity: {"activity": str, "ts": ISO-8601 str, **details}.
type LogEntry = dict[str, Any]

# Callback invoked on an activity's event entity: (event_type, details).
type EventCallback = Callable[[str, dict[str, Any]], None]


@dataclass
class DogAssistantData:
    """Container stored on ``entry.runtime_data``."""

    store: Store[dict[str, Any]]
    manager: DogAssistantManager


@dataclass
class _Subscriptions:
    """Entity callbacks the manager notifies on change."""

    listeners: list[Callable[[], None]] = field(default_factory=list)
    events: dict[str, EventCallback] = field(default_factory=dict)


class DogAssistantManager:
    """Owns the event log and derives all entity state from it."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: DogAssistantConfigEntry,
        store: Store[dict[str, Any]],
    ) -> None:
        """Initialise the manager for a config entry."""
        self.hass = hass
        self.entry = entry
        self._store = store
        self._log: list[LogEntry] = []
        self._subs = _Subscriptions()

    async def async_load(self) -> None:
        """Load the persisted event log from disk."""
        data = await self._store.async_load()
        if data and isinstance(data.get("log"), list):
            self._log = [entry for entry in data["log"] if _valid_entry(entry)]

    # -- identity / configuration ------------------------------------------

    @property
    def dog_name(self) -> str:
        """Configured name of the dog."""
        return self.entry.data[CONF_NAME]

    def target(self, activity_key: str) -> int:
        """Configured daily target for a scheduled activity."""
        activity = ACTIVITIES_BY_KEY[activity_key]
        raw = self.entry.options.get(
            target_option(activity_key), activity.default_target
        )
        try:
            return int(raw)
        except (TypeError, ValueError):
            return activity.default_target

    def _reset_time(self) -> tuple[int, int, int]:
        raw = self.entry.options.get(CONF_RESET_TIME, DEFAULT_RESET_TIME)
        parsed = parse_reset_time(str(raw))
        return parsed.hour, parsed.minute, parsed.second

    def _period_start(self) -> datetime:
        """Start of the current daily period (most recent reset boundary)."""
        now = dt_util.now()
        hour, minute, second = self._reset_time()
        start = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        if start > now:
            start -= timedelta(days=1)
        return start

    # -- derived state -----------------------------------------------------

    def count_today(self, activity_key: str) -> int:
        """Number of times an activity was recorded in the current period."""
        start = self._period_start()
        return sum(
            1
            for entry in self._log
            if entry["activity"] == activity_key and _entry_time(entry) >= start
        )

    def last_time(self, activity_key: str) -> datetime | None:
        """Timestamp of the most recent record for an activity, if any."""
        times = [
            _entry_time(entry)
            for entry in self._log
            if entry["activity"] == activity_key
        ]
        return max(times) if times else None

    def remaining(self, activity_key: str) -> int:
        """Records still expected today for a scheduled activity."""
        return max(0, self.target(activity_key) - self.count_today(activity_key))

    def due(self, activity_key: str) -> bool:
        """Whether a scheduled activity still needs doing today."""
        return self.remaining(activity_key) > 0

    def recent(self, limit: int = 20) -> list[LogEntry]:
        """Most recent log entries (newest first) for diagnostics."""
        return list(reversed(self._log[-limit:]))

    # -- recording ---------------------------------------------------------

    async def async_record(self, activity_key: str, **details: Any) -> None:
        """Record an activity now, persist it, and notify entities."""
        clean = {k: v for k, v in details.items() if v is not None}
        entry: LogEntry = {
            "activity": activity_key,
            "ts": dt_util.now().isoformat(),
            **clean,
        }
        self._log.append(entry)
        if len(self._log) > MAX_LOG_ENTRIES:
            del self._log[:-MAX_LOG_ENTRIES]
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

        if (event_cb := self._subs.events.get(activity_key)) is not None:
            event_cb(EVENT_RECORDED, clean)
        self._notify_listeners()

    @callback
    def _data_to_save(self) -> dict[str, Any]:
        # Runs in an executor thread: return a plain, self-contained copy.
        return {"log": [dict(entry) for entry in self._log]}

    # -- subscriptions -----------------------------------------------------

    @callback
    def register_listener(self, update: Callable[[], None]) -> Callable[[], None]:
        """Register an entity state-write callback; returns an unsubscribe."""
        self._subs.listeners.append(update)

        def _remove() -> None:
            self._subs.listeners.remove(update)

        return _remove

    @callback
    def register_event_callback(
        self, activity_key: str, event_cb: EventCallback
    ) -> Callable[[], None]:
        """Register an event entity's trigger callback for an activity."""
        self._subs.events[activity_key] = event_cb

        def _remove() -> None:
            self._subs.events.pop(activity_key, None)

        return _remove

    @callback
    def _notify_listeners(self) -> None:
        for update in list(self._subs.listeners):
            update()

    # -- daily reset -------------------------------------------------------

    @callback
    def async_schedule_reset(self) -> None:
        """Schedule the daily period rollover to refresh derived state."""
        hour, minute, second = self._reset_time()
        unsub = async_track_time_change(
            self.hass, self._handle_reset, hour=hour, minute=minute, second=second
        )
        self.entry.async_on_unload(unsub)

    @callback
    def _handle_reset(self, now: datetime) -> None:
        self._notify_listeners()


def _valid_entry(entry: Any) -> bool:
    return (
        isinstance(entry, dict)
        and isinstance(entry.get("activity"), str)
        and isinstance(entry.get("ts"), str)
        and dt_util.parse_datetime(entry["ts"]) is not None
    )


def _entry_time(entry: LogEntry) -> datetime:
    parsed = dt_util.parse_datetime(entry["ts"])
    # Entries are validated on load, so ``parsed`` is never None here.
    assert parsed is not None
    return dt_util.as_local(parsed)
