"""Data coordinator for Firmware Watch."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_NAME,
    CONF_NOTIFY_SERVICES,
    CONF_PATTERN,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RETRY_INTERVAL,
)
from .extract import VersionNotFound
from .fetch import FetchError, async_fetch_version
from .notify import async_send_alerts, notification_id
from .store import FirmwareWatchStore

if TYPE_CHECKING:
    from . import FirmwareWatchConfigEntry

_LOGGER = logging.getLogger(__name__)


class FirmwareWatchCoordinator(DataUpdateCoordinator[str]):
    """Fetch the firmware page once a day and track version changes."""

    config_entry: FirmwareWatchConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: FirmwareWatchConfigEntry
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.source_name = entry.data[CONF_NAME]
        self.url = entry.data[CONF_URL]
        self.pattern = entry.data[CONF_PATTERN]
        self.store = FirmwareWatchStore(hass, entry.entry_id)

    async def async_load_store(self) -> None:
        """Load persisted state; call before the first refresh."""
        await self.store.async_load()

    async def _async_update_data(self) -> str:
        """Fetch the page and handle version changes."""
        store = self.store
        try:
            version = await async_fetch_version(self.hass, self.url, self.pattern)
        except (FetchError, VersionNotFound) as err:
            self.update_interval = RETRY_INTERVAL
            raise UpdateFailed(f"{self.source_name}: {err}") from err
        self.update_interval = DEFAULT_SCAN_INTERVAL

        changed = False
        if store.baseline is None:
            store.baseline = version
            changed = True
        if store.latest != version:
            store.latest = version
            changed = True
        if version != store.baseline and store.notified != version:
            await async_send_alerts(
                self.hass,
                self.config_entry.entry_id,
                list(self.config_entry.options.get(CONF_NOTIFY_SERVICES, [])),
                self.source_name,
                self.url,
                version,
                store.baseline,
            )
            store.notified = version
            changed = True
        if changed:
            await store.async_save()
        return version

    async def async_acknowledge(self) -> None:
        """Make the latest version the new baseline."""
        self.store.baseline = self.store.latest
        await self.store.async_save()
        persistent_notification.async_dismiss(
            self.hass, notification_id(self.config_entry.entry_id)
        )
        self.async_update_listeners()
