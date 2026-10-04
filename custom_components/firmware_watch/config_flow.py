"""Config flow for Firmware Watch."""

from __future__ import annotations

from hashlib import sha256
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_NAME,
    CONF_NOTIFY_SERVICES,
    CONF_PATTERN,
    CONF_SOURCE,
    CONF_URL,
    DOMAIN,
    SOURCE_CUSTOM,
)
from .extract import InvalidPattern, VersionNotFound, compile_pattern
from .fetch import FetchError, async_fetch_version
from .sources import PRESETS

_LOGGER = logging.getLogger(__name__)

EXCLUDED_NOTIFY_SERVICES = frozenset({"notify", "send_message", "persistent_notification"})


class FirmwareWatchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Firmware Watch."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise flow state."""
        self._title = ""
        self._version = ""
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return FirmwareWatchOptionsFlow()

    async def _async_check(self, url: str, pattern: str) -> str | None:
        """Fetch the version; store it and return None, or return an error key."""
        try:
            self._version = await async_fetch_version(self.hass, url, pattern)
        except FetchError as err:
            _LOGGER.debug("Fetch failed: %s", err)
            return "cannot_connect"
        except VersionNotFound:
            return "version_not_found"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error fetching %s", url)
            return "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose a preset or a custom page."""
        errors: dict[str, str] = {}
        if user_input is not None:
            key = user_input[CONF_SOURCE]
            if key == SOURCE_CUSTOM:
                return await self.async_step_custom()
            preset = PRESETS[key]
            await self.async_set_unique_id(key)
            self._abort_if_unique_id_configured()
            error = await self._async_check(preset.url, preset.pattern)
            if error is None:
                self._title = preset.name
                self._data = {CONF_SOURCE: key}
                return await self.async_step_confirm()
            errors["base"] = error

        options = [
            SelectOptionDict(value=p.key, label=p.name) for p in PRESETS.values()
        ]
        options.append(SelectOptionDict(value=SOURCE_CUSTOM, label="Custom page"))
        schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE): SelectSelector(
                    SelectSelectorConfig(
                        options=options, mode=SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_custom(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Enter name, URL and pattern for a custom page."""
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            url = user_input[CONF_URL].strip()
            pattern = user_input[CONF_PATTERN]
            if not url.lower().startswith(("http://", "https://")):
                errors[CONF_URL] = "invalid_url"
            try:
                compile_pattern(pattern)
            except InvalidPattern:
                errors[CONF_PATTERN] = "invalid_pattern"
            if not errors:
                await self.async_set_unique_id(
                    "custom_" + sha256(f"{url}\n{pattern}".encode()).hexdigest()[:12]
                )
                self._abort_if_unique_id_configured()
                error = await self._async_check(url, pattern)
                if error is None:
                    self._title = name
                    self._data = {
                        CONF_SOURCE: SOURCE_CUSTOM,
                        CONF_NAME: name,
                        CONF_URL: url,
                        CONF_PATTERN: pattern,
                    }
                    return await self.async_step_confirm()
                errors["base"] = error

        defaults = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): TextSelector(),
                vol.Required(CONF_URL, default=defaults.get(CONF_URL, "")): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
                vol.Required(
                    CONF_PATTERN, default=defaults.get(CONF_PATTERN, "")
                ): TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="custom", data_schema=schema, errors=errors
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the found version and create the entry."""
        if user_input is not None:
            return self.async_create_entry(title=self._title, data=self._data)
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"name": self._title, "version": self._version},
        )


class FirmwareWatchOptionsFlow(OptionsFlow):
    """Choose which notify services get alerts."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select notify services."""
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_NOTIFY_SERVICES: user_input[CONF_NOTIFY_SERVICES]}
            )

        current: list[str] = list(self.config_entry.options.get(CONF_NOTIFY_SERVICES, []))
        registered = self.hass.services.async_services_for_domain("notify")
        names = (set(registered) - EXCLUDED_NOTIFY_SERVICES) | set(current)
        schema = vol.Schema(
            {
                vol.Optional(CONF_NOTIFY_SERVICES, default=current): SelectSelector(
                    SelectSelectorConfig(
                        options=sorted(names),
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
