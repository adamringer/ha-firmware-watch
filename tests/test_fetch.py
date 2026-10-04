"""Tests for fetch.py."""

import aiohttp
import pytest

from custom_components.firmware_watch.const import USER_AGENT
from custom_components.firmware_watch.extract import VersionNotFound
from custom_components.firmware_watch.fetch import FetchError, async_fetch_version

from .conftest import load_fixture_text

URL = "https://www.carpodgo.com/pages/firmware-t4-plus"
PATTERN = r"T4 Plus Firmware Update:\s*Version\s+([0-9][0-9A-Za-z._-]*)"


async def test_success(hass, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=load_fixture_text("carpodgo_t4plus.html"))
    assert await async_fetch_version(hass, URL, PATTERN) == "0.0.22"
    headers = aioclient_mock.mock_calls[0][3]
    assert headers["User-Agent"] == USER_AGENT


async def test_http_error(hass, aioclient_mock) -> None:
    aioclient_mock.get(URL, status=404)
    with pytest.raises(FetchError):
        await async_fetch_version(hass, URL, PATTERN)


@pytest.mark.parametrize("exc", [aiohttp.ClientError, TimeoutError])
async def test_network_error(hass, aioclient_mock, exc) -> None:
    aioclient_mock.get(URL, exc=exc)
    with pytest.raises(FetchError):
        await async_fetch_version(hass, URL, PATTERN)


async def test_no_match(hass, aioclient_mock) -> None:
    aioclient_mock.get(URL, text="<p>nothing</p>")
    with pytest.raises(VersionNotFound):
        await async_fetch_version(hass, URL, PATTERN)
