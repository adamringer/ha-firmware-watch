"""Button entity for Firmware Watch."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import FirmwareWatchConfigEntry
from .coordinator import FirmwareWatchCoordinator
from .entity import FirmwareWatchEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FirmwareWatchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the button."""
    async_add_entities([CheckNowButton(entry.runtime_data)])


class CheckNowButton(FirmwareWatchEntity, ButtonEntity):
    """Fetch the page now."""

    _attr_translation_key = "check_now"

    def __init__(self, coordinator: FirmwareWatchCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry_id}_check_now"

    @property
    def available(self) -> bool:
        """Stay pressable while checks are failing."""
        return True

    async def async_press(self) -> None:
        """Refresh now."""
        await self.coordinator.async_request_refresh()
