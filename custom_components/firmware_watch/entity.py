"""Base entity for Firmware Watch."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FirmwareWatchCoordinator


class FirmwareWatchEntity(CoordinatorEntity[FirmwareWatchCoordinator]):
    """Base class for Firmware Watch entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FirmwareWatchCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.source_name,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator.url,
        )
