"""Constants for Firmware Watch."""

from datetime import timedelta

from homeassistant.const import CONF_NAME, CONF_URL

DOMAIN = "firmware_watch"

CONF_PATTERN = "pattern"
CONF_NOTIFY_SERVICES = "notify_services"

DEFAULT_SCAN_INTERVAL = timedelta(days=1)
# After a failed check, retry sooner so one bad fetch doesn't leave the entity
# unavailable for a day.
RETRY_INTERVAL = timedelta(hours=1)
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = "Mozilla/5.0 (compatible; HomeAssistant-FirmwareWatch/0.1)"

__all__ = [
    "CONF_NAME",
    "CONF_NOTIFY_SERVICES",
    "CONF_PATTERN",
    "CONF_URL",
    "DEFAULT_SCAN_INTERVAL",
    "DOMAIN",
    "REQUEST_TIMEOUT",
    "RETRY_INTERVAL",
    "USER_AGENT",
]
