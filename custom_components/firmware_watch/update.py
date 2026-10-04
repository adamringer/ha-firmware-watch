"""Update entity for Firmware Watch."""

from __future__ import annotations

from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import FirmwareWatchConfigEntry
from .coordinator import FirmwareWatchCoordinator
from .entity import FirmwareWatchEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FirmwareWatchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the update entity."""
    async_add_entities([FirmwareWatchUpdate(entry.runtime_data)])


class FirmwareWatchUpdate(FirmwareWatchEntity, UpdateEntity):
    """Shows whether the watched page has a new firmware version."""

    _attr_translation_key = "firmware"
    _attr_supported_features = UpdateEntityFeature.INSTALL

    def __init__(self, coordinator: FirmwareWatchCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry_id}_firmware"
        self._attr_release_url = coordinator.url
        self._attr_title = coordinator.source_name

    @property
    def installed_version(self) -> str | None:
        """Return the baseline version."""
        return self.coordinator.store.baseline

    @property
    def latest_version(self) -> str | None:
        """Return the latest version seen."""
        return self.coordinator.store.latest

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Acknowledge the new version (baseline := latest)."""
        await self.coordinator.async_acknowledge()
