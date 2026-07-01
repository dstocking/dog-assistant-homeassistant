"""Service actions for recording activities with optional details."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import ACTIVITIES, DOMAIN, Activity
from .coordinator import DogAssistantConfigEntry, DogAssistantManager


def _build_schema(activity: Activity) -> vol.Schema:
    fields: dict[Any, Any] = {}
    for detail in activity.details:
        if detail.kind == "number":
            fields[vol.Optional(detail.name)] = vol.Coerce(float)
        elif detail.kind == "select":
            fields[vol.Optional(detail.name)] = vol.In(detail.options)
        else:
            fields[vol.Optional(detail.name)] = cv.string
    return vol.Schema(fields)


def _resolve_manager(hass: HomeAssistant) -> DogAssistantManager:
    """Return the manager for the single loaded entry, or raise."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            loaded: DogAssistantConfigEntry = entry
            return loaded.runtime_data.manager
    raise ServiceValidationError(
        translation_domain=DOMAIN, translation_key="not_configured"
    )


def _make_handler(
    hass: HomeAssistant, activity: Activity
) -> Callable[[ServiceCall], Coroutine[Any, Any, None]]:
    async def _handle(call: ServiceCall) -> None:
        manager = _resolve_manager(hass)
        await manager.async_record(activity.key, **dict(call.data))

    return _handle


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register a ``record_<activity>`` service for each activity."""
    for activity in ACTIVITIES:
        if hass.services.has_service(DOMAIN, activity.service_name):
            continue
        hass.services.async_register(
            DOMAIN,
            activity.service_name,
            _make_handler(hass, activity),
            schema=_build_schema(activity),
        )
