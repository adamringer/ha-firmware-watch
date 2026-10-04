"""End-to-end tests for Firmware Watch setup, updates, alerts and button."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.firmware_watch.const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RETRY_INTERVAL,
)

from .conftest import load_fixture_text

NAME = "CarPodGo T4 Plus"
URL = "https://www.carpodgo.com/pages/firmware-t4-plus"
PATTERN = r"T4 Plus Firmware Update:\s*Version\s+([0-9][0-9A-Za-z._-]*)"
OLD = load_fixture_text("carpodgo_t4plus.html")
NEW = OLD.replace("0.0.22", "0.0.23")
UPDATE = "update.carpodgo_t4_plus_firmware"
BUTTON = "button.carpodgo_t4_plus_check_now"
LATEST = "sensor.carpodgo_t4_plus_latest_version"
INSTALLED = "sensor.carpodgo_t4_plus_installed_version"
NOTIF_KEY = "persistent_notification"


def _entry(options: dict | None = None) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={"name": NAME, "url": URL, "pattern": PATTERN},
        options=options or {},
        title=NAME,
    )


def _serve(mock: AiohttpClientMocker, body: str, status: int = 200) -> None:
    mock.clear_requests()
    mock.get(URL, text=body, status=status)


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    freezer.tick(DEFAULT_SCAN_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


def _notifications(hass: HomeAssistant) -> dict:
    return hass.data.get(NOTIF_KEY, {})


async def _stored(hass: HomeAssistant, entry: MockConfigEntry) -> dict | None:
    return await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_load()


@pytest.fixture
def notify_calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Register a fake notify.mobile_app_phone."""
    calls: list[ServiceCall] = []

    async def _handler(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register("notify", "mobile_app_phone", _handler)
    return calls


async def test_setup(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    _serve(aioclient_mock, OLD)
    entry = _entry()
    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get(UPDATE)
    assert state.state == "off"
    assert state.attributes["installed_version"] == "0.0.22"
    assert state.attributes["latest_version"] == "0.0.22"
    assert state.attributes["release_url"] == URL
    assert state.attributes["title"] == NAME
    assert hass.states.get(BUTTON) is not None
    assert hass.states.get(LATEST).state == "0.0.22"
    assert hass.states.get(INSTALLED).state == "0.0.22"
    assert er.async_get(hass).async_get(UPDATE).unique_id == f"{entry.entry_id}_firmware"
    assert await _stored(hass, entry) == {
        "baseline": "0.0.22",
        "latest": "0.0.22",
        "notified": None,
    }
    assert not _notifications(hass)


async def test_change_alerts_once_and_survives_reload(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
    notify_calls: list[ServiceCall],
) -> None:
    _serve(aioclient_mock, OLD)
    entry = _entry({"notify_services": ["mobile_app_phone"]})
    await _setup(hass, entry)

    _serve(aioclient_mock, NEW)
    with patch(
        "custom_components.firmware_watch.notify.persistent_notification.async_create",
        wraps=persistent_notification.async_create,
    ) as create:
        await _tick(hass, freezer)
        state = hass.states.get(UPDATE)
        assert state.state == "on"
        assert state.attributes["latest_version"] == "0.0.23"
        assert state.attributes["installed_version"] == "0.0.22"
        create.assert_called_once()
        assert create.call_args.kwargs["notification_id"] == f"{DOMAIN}_{entry.entry_id}"
        assert create.call_args.args[2] == f"New firmware: {NAME}"
        assert f"{DOMAIN}_{entry.entry_id}" in _notifications(hass)

        assert len(notify_calls) == 1
        data = notify_calls[0].data
        assert NAME in data["title"]
        for part in (NAME, "0.0.23", "0.0.22", URL):
            assert part in data["message"]

        # Same page again: no new alert.
        await _tick(hass, freezer)
        assert create.call_count == 1
        assert len(notify_calls) == 1

        # Restart: store persists, still on, no re-alert.
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(UPDATE).state == "on"
        assert create.call_count == 1
        assert len(notify_calls) == 1
    assert (await _stored(hass, entry))["notified"] == "0.0.23"


async def test_install_acknowledges(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    _serve(aioclient_mock, OLD)
    entry = _entry()
    await _setup(hass, entry)
    _serve(aioclient_mock, NEW)
    await _tick(hass, freezer)
    assert hass.states.get(UPDATE).state == "on"
    assert hass.states.get(LATEST).state == "0.0.23"
    assert hass.states.get(INSTALLED).state == "0.0.22"
    assert f"{DOMAIN}_{entry.entry_id}" in _notifications(hass)

    await hass.services.async_call(
        "update", "install", {"entity_id": UPDATE}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(UPDATE)
    assert state.state == "off"
    assert state.attributes["installed_version"] == "0.0.23"
    assert hass.states.get(INSTALLED).state == "0.0.23"
    assert hass.states.get(LATEST).state == "0.0.23"
    assert f"{DOMAIN}_{entry.entry_id}" not in _notifications(hass)
    assert (await _stored(hass, entry))["baseline"] == "0.0.23"


@pytest.mark.parametrize(
    ("status", "body"),
    [(500, "oops"), (200, "<html><body>nothing here</body></html>")],
)
async def test_failures_leave_state_alone(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
    notify_calls: list[ServiceCall],
    caplog: pytest.LogCaptureFixture,
    status: int,
    body: str,
) -> None:
    _serve(aioclient_mock, OLD)
    entry = _entry({"notify_services": ["mobile_app_phone"]})
    await _setup(hass, entry)
    before = await _stored(hass, entry)

    _serve(aioclient_mock, body, status)
    await _tick(hass, freezer)
    assert hass.states.get(UPDATE).state == "unavailable"
    assert hass.states.get(BUTTON).state != "unavailable"
    assert hass.states.get(LATEST).state == "unavailable"
    assert hass.states.get(INSTALLED).state == "0.0.22"
    assert await _stored(hass, entry) == before
    assert not notify_calls
    assert not _notifications(hass)
    assert NAME in caplog.text

    # Retries after RETRY_INTERVAL, not a full day.
    _serve(aioclient_mock, OLD)
    freezer.tick(RETRY_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 1
    state = hass.states.get(UPDATE)
    assert state.state == "off"
    assert state.attributes["installed_version"] == "0.0.22"

    # Back to the daily interval after a good check.
    _serve(aioclient_mock, OLD)
    freezer.tick(RETRY_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 0


async def test_setup_retry_when_site_down(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    _serve(aioclient_mock, "", 503)
    entry = _entry()
    await _setup(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert await _stored(hass, entry) is None


@pytest.mark.parametrize("mode", ["missing", "raising"])
async def test_notify_problems_still_save_state(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
    mode: str,
) -> None:
    if mode == "raising":

        async def _boom(call: ServiceCall) -> None:
            raise HomeAssistantError("push failed")

        hass.services.async_register("notify", "mobile_app_phone", _boom)

    _serve(aioclient_mock, OLD)
    entry = _entry({"notify_services": ["mobile_app_phone"]})
    await _setup(hass, entry)
    _serve(aioclient_mock, NEW)
    await _tick(hass, freezer)

    assert "notify.mobile_app_phone" in caplog.text
    assert f"{DOMAIN}_{entry.entry_id}" in _notifications(hass)
    assert (await _stored(hass, entry))["notified"] == "0.0.23"
    assert hass.states.get(UPDATE).state == "on"


async def test_check_now_button(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    _serve(aioclient_mock, OLD)
    entry = _entry()
    await _setup(hass, entry)
    _serve(aioclient_mock, NEW)
    await hass.services.async_call(
        "button", "press", {"entity_id": BUTTON}, blocking=True
    )
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 1
    assert hass.states.get(UPDATE).attributes["latest_version"] == "0.0.23"
    assert hass.states.get(UPDATE).state == "on"


async def test_remove_entry_removes_store(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    _serve(aioclient_mock, OLD)
    entry = _entry()
    await _setup(hass, entry)
    assert await _stored(hass, entry) is not None

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert await _stored(hass, entry) is None
