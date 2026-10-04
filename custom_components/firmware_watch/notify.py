"""Alerts for new firmware versions."""

from __future__ import annotations

import logging

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def notification_id(entry_id: str) -> str:
    """Return the persistent notification id for an entry."""
    return f"{DOMAIN}_{entry_id}"


async def async_send_alerts(
    hass: HomeAssistant,
    entry_id: str,
    notify_services: list[str],
    name: str,
    url: str,
    latest: str,
    baseline: str | None,
) -> None:
    """Create the persistent notification and call the chosen notify services.

    Never raises: a failing push must not cause repeated alerts.
    """
    title = f"New firmware: {name}"
    text = f"{name} has firmware {latest} (baseline {baseline})."
    persistent_notification.async_create(
        hass,
        f"{text}\n\n[Firmware page]({url})",
        title,
        notification_id=notification_id(entry_id),
    )
    for service in notify_services:
        if not hass.services.has_service("notify", service):
            _LOGGER.warning(
                "Notify service notify.%s is not available; skipping alert for %s",
                service,
                name,
            )
            continue
        try:
            await hass.services.async_call(
                "notify",
                service,
                {"title": title, "message": f"{text} {url}"},
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.warning("Notify service notify.%s failed: %s", service, err)
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Unexpected error calling notify.%s", service, exc_info=True
            )
