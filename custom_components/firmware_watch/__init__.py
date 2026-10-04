"""Firmware Watch: flag new versions on vendor firmware pages."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import FirmwareWatchCoordinator
from .store import FirmwareWatchStore

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SENSOR, Platform.UPDATE]

type FirmwareWatchConfigEntry = ConfigEntry[FirmwareWatchCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FirmwareWatchConfigEntry) -> bool:
    """Set up a config entry."""
    coordinator = FirmwareWatchCoordinator(hass, entry)
    await coordinator.async_load_store()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FirmwareWatchConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: FirmwareWatchConfigEntry) -> None:
    """Delete the entry's stored state."""
    await FirmwareWatchStore(hass, entry.entry_id).async_remove()
