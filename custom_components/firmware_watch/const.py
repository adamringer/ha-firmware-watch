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
# Sent with every request. Some vendor sites (CarPodGo, behind Cloudflare)
# answer 403 to a request that has only a User-Agent; browser-style Accept and
# Accept-Language headers get a normal 200.
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

__all__ = [
    "CONF_NAME",
    "CONF_NOTIFY_SERVICES",
    "CONF_PATTERN",
    "CONF_URL",
    "DEFAULT_SCAN_INTERVAL",
    "DOMAIN",
    "REQUEST_HEADERS",
    "REQUEST_TIMEOUT",
    "RETRY_INTERVAL",
    "USER_AGENT",
]
