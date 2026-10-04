"""Tests for fetch.py."""

import aiohttp
import pytest

from custom_components.firmware_watch.const import USER_AGENT
from custom_components.firmware_watch.extract import VersionNotFound
from custom_components.firmware_watch.fetch import FetchError, async_fetch_version
from custom_components.firmware_watch.sources import PRESETS

from .conftest import load_fixture_text

PRESET = PRESETS["carpodgo_t4_plus"]


async def test_success(hass, aioclient_mock) -> None:
    aioclient_mock.get(PRESET.url, text=load_fixture_text("carpodgo_t4plus.html"))
    assert await async_fetch_version(hass, PRESET.url, PRESET.pattern) == "0.0.22"
    headers = aioclient_mock.mock_calls[0][3]
    assert headers["User-Agent"] == USER_AGENT


async def test_http_error(hass, aioclient_mock) -> None:
    aioclient_mock.get(PRESET.url, status=404)
    with pytest.raises(FetchError):
        await async_fetch_version(hass, PRESET.url, PRESET.pattern)


@pytest.mark.parametrize("exc", [aiohttp.ClientError, TimeoutError])
async def test_network_error(hass, aioclient_mock, exc) -> None:
    aioclient_mock.get(PRESET.url, exc=exc)
    with pytest.raises(FetchError):
        await async_fetch_version(hass, PRESET.url, PRESET.pattern)


async def test_no_match(hass, aioclient_mock) -> None:
    aioclient_mock.get(PRESET.url, text="<p>nothing</p>")
    with pytest.raises(VersionNotFound):
        await async_fetch_version(hass, PRESET.url, PRESET.pattern)
