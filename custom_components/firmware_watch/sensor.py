"""Version sensors for Firmware Watch."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    """Set up the version sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [LatestVersionSensor(coordinator), InstalledVersionSensor(coordinator)]
    )


class LatestVersionSensor(FirmwareWatchEntity, SensorEntity):
    """The version the page shows now; unavailable while checks fail."""

    _attr_translation_key = "latest_version"

    def __init__(self, coordinator: FirmwareWatchCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry_id}_latest_version"

    @property
    def native_value(self) -> str | None:
        """Return the latest version seen."""
        return self.coordinator.store.latest


class InstalledVersionSensor(FirmwareWatchEntity, SensorEntity):
    """The acknowledged (baseline) version; stored locally, so always available."""

    _attr_translation_key = "installed_version"

    def __init__(self, coordinator: FirmwareWatchCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry_id}_installed_version"

    @property
    def available(self) -> bool:
        """Stay available while checks fail."""
        return True

    @property
    def native_value(self) -> str | None:
        """Return the baseline version."""
        return self.coordinator.store.baseline
