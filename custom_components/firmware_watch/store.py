"""Persistent per-entry state for Firmware Watch."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1


class FirmwareWatchStore:
    """Baseline, latest and last-notified versions for one config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the store."""
        self._store: Store[dict[str, str | None]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}"
        )
        self.baseline: str | None = None
        self.latest: str | None = None
        self.notified: str | None = None

    async def async_load(self) -> None:
        """Load saved state, if any."""
        data = await self._store.async_load() or {}
        self.baseline = data.get("baseline")
        self.latest = data.get("latest")
        self.notified = data.get("notified")

    async def async_save(self) -> None:
        """Save state."""
        await self._store.async_save(
            {
                "baseline": self.baseline,
                "latest": self.latest,
                "notified": self.notified,
            }
        )

    async def async_remove(self) -> None:
        """Delete the store file."""
        await self._store.async_remove()
