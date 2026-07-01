"""Config and options flows for Dog Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_RESET_TIME,
    DEFAULT_RESET_TIME,
    DOMAIN,
    TARGET_ACTIVITIES,
    target_option,
)
from .coordinator import DogAssistantConfigEntry


def _target_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=20, step=1, mode=selector.NumberSelectorMode.BOX
        )
    )


def _target_fields(defaults: dict[str, Any]) -> dict[Any, Any]:
    fields: dict[Any, Any] = {}
    for activity in TARGET_ACTIVITIES:
        key = target_option(activity.key)
        default = defaults.get(key, activity.default_target)
        fields[vol.Required(key, default=default)] = _target_selector()
    return fields


def _targets_from_input(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        target_option(activity.key): int(user_input[target_option(activity.key)])
        for activity in TARGET_ACTIVITIES
    }


class DogAssistantConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup and reconfiguration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the dog's name and daily targets.

        A second entry is prevented by ``single_config_entry`` in the manifest,
        which aborts with ``single_instance_allowed`` before this step runs.
        """
        if user_input is not None:
            options = _targets_from_input(user_input)
            options[CONF_RESET_TIME] = DEFAULT_RESET_TIME
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_NAME: user_input[CONF_NAME]},
                options=options,
            )

        schema = vol.Schema(
            {vol.Required(CONF_NAME): selector.TextSelector(), **_target_fields({})}
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Rename the dog without recreating the entry."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry, data_updates={CONF_NAME: user_input[CONF_NAME]}
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=entry.data[CONF_NAME]): (
                    selector.TextSelector()
                )
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: DogAssistantConfigEntry,
    ) -> DogAssistantOptionsFlow:
        """Return the options flow."""
        return DogAssistantOptionsFlow()


class DogAssistantOptionsFlow(OptionsFlowWithReload):
    """Adjust daily targets and the reset time; reloads on save."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and save the options."""
        if user_input is not None:
            data = _targets_from_input(user_input)
            data[CONF_RESET_TIME] = user_input[CONF_RESET_TIME]
            return self.async_create_entry(data=data)

        options = self.config_entry.options
        fields = _target_fields(dict(options))
        fields[
            vol.Required(
                CONF_RESET_TIME,
                default=options.get(CONF_RESET_TIME, DEFAULT_RESET_TIME),
            )
        ] = selector.TimeSelector()
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
