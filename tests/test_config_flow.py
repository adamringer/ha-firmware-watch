"""Tests for the Firmware Watch config and options flows."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.firmware_watch.const import DOMAIN
from custom_components.firmware_watch.extract import VersionNotFound
from custom_components.firmware_watch.fetch import FetchError

FETCH = "custom_components.firmware_watch.config_flow.async_fetch_version"
SOURCE = {
    "name": "My Gadget",
    "url": "https://example.com/fw",
    "pattern": r"Firmware ([0-9.]+)",
}


@pytest.fixture(autouse=True)
def mock_setup_entry() -> Generator[AsyncMock]:
    """Avoid real entry setup."""
    with patch(
        "custom_components.firmware_watch.async_setup_entry", return_value=True
    ) as mock:
        yield mock


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def _submit(hass: HomeAssistant, flow_id: str, user_input: dict):
    return await hass.config_entries.flow.async_configure(flow_id, user_input)


async def test_happy_path(hass: HomeAssistant) -> None:
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    flow_id = result["flow_id"]

    with patch(FETCH, return_value="1.2.3"):
        result = await _submit(hass, flow_id, SOURCE)
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "name": "My Gadget",
        "version": "1.2.3",
    }

    result = await _submit(hass, flow_id, {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Gadget"
    assert result["data"] == SOURCE
    assert result["result"].unique_id.startswith("source_")
    assert len(result["result"].unique_id) == len("source_") + 12


async def test_invalid_url(hass: HomeAssistant) -> None:
    result = await _start(hass)
    with patch(FETCH, return_value="1") as fetch:
        result = await _submit(
            hass, result["flow_id"], {**SOURCE, "url": "ftp://example.com/fw"}
        )
    assert result["errors"] == {"url": "invalid_url"}
    fetch.assert_not_called()


@pytest.mark.parametrize("pattern", ["([", "no group", "(a)(b)"])
async def test_invalid_pattern(hass: HomeAssistant, pattern: str) -> None:
    result = await _start(hass)
    with patch(FETCH, return_value="1") as fetch:
        result = await _submit(
            hass, result["flow_id"], {**SOURCE, "pattern": pattern}
        )
    assert result["errors"] == {"pattern": "invalid_pattern"}
    fetch.assert_not_called()


@pytest.mark.parametrize(
    ("exc", "error"),
    [
        (FetchError("x"), "cannot_connect"),
        (VersionNotFound("x"), "version_not_found"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_fetch_errors(hass: HomeAssistant, exc, error) -> None:
    result = await _start(hass)
    with patch(FETCH, side_effect=exc):
        result = await _submit(hass, result["flow_id"], SOURCE)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}


async def test_entries_kept_as_defaults_after_error(hass: HomeAssistant) -> None:
    result = await _start(hass)
    with patch(FETCH, side_effect=FetchError("x")):
        result = await _submit(hass, result["flow_id"], SOURCE)
    defaults = {
        str(key): key.default() for key in result["data_schema"].schema
    }
    assert defaults == SOURCE

    with patch(FETCH, return_value="1.2.3"):
        result = await _submit(hass, result["flow_id"], SOURCE)
    assert result["step_id"] == "confirm"


async def test_duplicate(hass: HomeAssistant) -> None:
    result = await _start(hass)
    with patch(FETCH, return_value="1.2.3"):
        await _submit(hass, result["flow_id"], SOURCE)
        await _submit(hass, result["flow_id"], {})

    result = await _start(hass)
    with patch(FETCH, return_value="1.2.3") as fetch:
        result = await _submit(hass, result["flow_id"], SOURCE)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    fetch.assert_not_called()


async def _noop(call: ServiceCall) -> None:
    """Dummy service handler."""


async def test_options_flow(hass: HomeAssistant) -> None:
    for name in ("mobile_app_phone", "send_message", "persistent_notification"):
        hass.services.async_register("notify", name, _noop)

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="source_test",
        data=SOURCE,
        options={"notify_services": ["gone_service"]},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    selector = result["data_schema"].schema["notify_services"]
    assert selector.config["options"] == ["gone_service", "mobile_app_phone"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"notify_services": ["mobile_app_phone"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"notify_services": ["mobile_app_phone"]}
