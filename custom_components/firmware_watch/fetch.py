"""Fetch a firmware page and extract its version."""

from __future__ import annotations

import re

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import REQUEST_TIMEOUT, USER_AGENT
from .extract import extract_version


class FetchError(Exception):
    """The page could not be downloaded."""


async def async_fetch_version(
    hass: HomeAssistant, url: str, pattern: str | re.Pattern[str]
) -> str:
    """Download url and return the version matched by pattern.

    Raises FetchError on network/HTTP problems; VersionNotFound propagates.
    """
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            headers={"User-Agent": USER_AGENT},
        ) as resp:
            resp.raise_for_status()
            html = await resp.text(errors="replace")
    except (aiohttp.ClientError, TimeoutError) as err:
        raise FetchError(f"Error fetching {url}: {err}") from err
    return extract_version(html, pattern)
