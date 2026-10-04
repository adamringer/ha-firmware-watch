"""Constants for Firmware Watch."""

from datetime import timedelta

from homeassistant.const import CONF_NAME, CONF_URL

DOMAIN = "firmware_watch"

CONF_SOURCE = "source"
CONF_PATTERN = "pattern"
CONF_NOTIFY_SERVICES = "notify_services"

SOURCE_CUSTOM = "custom"

DEFAULT_SCAN_INTERVAL = timedelta(days=1)
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = "Mozilla/5.0 (compatible; HomeAssistant-FirmwareWatch/0.1)"

__all__ = [
    "CONF_NAME",
    "CONF_NOTIFY_SERVICES",
    "CONF_PATTERN",
    "CONF_SOURCE",
    "CONF_URL",
    "DEFAULT_SCAN_INTERVAL",
    "DOMAIN",
    "REQUEST_TIMEOUT",
    "SOURCE_CUSTOM",
    "USER_AGENT",
]
