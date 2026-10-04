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
CUSTOM = {
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


async def _pick(hass: HomeAssistant, flow_id: str, source: str):
    return await hass.config_entries.flow.async_configure(
        flow_id, {"source": source}
    )


async def test_preset_happy_path(hass: HomeAssistant) -> None:
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(FETCH, return_value="0.0.22"):
        result = await _pick(hass, result["flow_id"], "carpodgo_t4_plus")
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "name": "CarPodGo T4 Plus",
        "version": "0.0.22",
    }

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "CarPodGo T4 Plus"
    assert result["data"] == {"source": "carpodgo_t4_plus"}
    assert result["result"].unique_id == "carpodgo_t4_plus"


async def test_preset_duplicate(hass: HomeAssistant) -> None:
    MockConfigEntry(
        domain=DOMAIN, unique_id="ambient_ws2000", data={"source": "ambient_ws2000"}
    ).add_to_hass(hass)
    result = await _start(hass)
    with patch(FETCH, return_value="2.0.4") as fetch:
        result = await _pick(hass, result["flow_id"], "ambient_ws2000")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    fetch.assert_not_called()


@pytest.mark.parametrize(
    ("exc", "error"),
    [
        (FetchError("x"), "cannot_connect"),
        (VersionNotFound("x"), "version_not_found"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_preset_errors_then_recover(hass: HomeAssistant, exc, error) -> None:
    result = await _start(hass)
    with patch(FETCH, side_effect=exc):
        result = await _pick(hass, result["flow_id"], "carpodgo_t4_plus")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    with patch(FETCH, return_value="0.0.22"):
        result = await _pick(hass, result["flow_id"], "carpodgo_t4_plus")
    assert result["step_id"] == "confirm"


async def _to_custom(hass: HomeAssistant) -> str:
    result = await _start(hass)
    result = await _pick(hass, result["flow_id"], "custom")
    assert result["step_id"] == "custom"
    return result["flow_id"]


async def test_custom_happy_path(hass: HomeAssistant) -> None:
    flow_id = await _to_custom(hass)
    with patch(FETCH, return_value="1.2.3"):
        result = await hass.config_entries.flow.async_configure(flow_id, CUSTOM)
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"]["version"] == "1.2.3"

    result = await hass.config_entries.flow.async_configure(flow_id, {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Gadget"
    assert result["data"] == {"source": "custom", **CUSTOM}
    assert result["result"].unique_id.startswith("custom_")
    assert len(result["result"].unique_id) == len("custom_") + 12


async def test_custom_invalid_url(hass: HomeAssistant) -> None:
    flow_id = await _to_custom(hass)
    with patch(FETCH, return_value="1") as fetch:
        result = await hass.config_entries.flow.async_configure(
            flow_id, {**CUSTOM, "url": "ftp://example.com/fw"}
        )
    assert result["errors"] == {"url": "invalid_url"}
    fetch.assert_not_called()


@pytest.mark.parametrize("pattern", ["([", "no group", "(a)(b)"])
async def test_custom_invalid_pattern(hass: HomeAssistant, pattern: str) -> None:
    flow_id = await _to_custom(hass)
    result = await hass.config_entries.flow.async_configure(
        flow_id, {**CUSTOM, "pattern": pattern}
    )
    assert result["errors"] == {"pattern": "invalid_pattern"}


@pytest.mark.parametrize(
    ("exc", "error"),
    [(FetchError("x"), "cannot_connect"), (VersionNotFound("x"), "version_not_found")],
)
async def test_custom_fetch_errors(hass: HomeAssistant, exc, error) -> None:
    flow_id = await _to_custom(hass)
    with patch(FETCH, side_effect=exc):
        result = await hass.config_entries.flow.async_configure(flow_id, CUSTOM)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "custom"
    assert result["errors"] == {"base": error}


async def test_custom_duplicate(hass: HomeAssistant) -> None:
    flow_id = await _to_custom(hass)
    with patch(FETCH, return_value="1.2.3"):
        await hass.config_entries.flow.async_configure(flow_id, CUSTOM)
        await hass.config_entries.flow.async_configure(flow_id, {})

    flow_id = await _to_custom(hass)
    with patch(FETCH, return_value="1.2.3"):
        result = await hass.config_entries.flow.async_configure(flow_id, CUSTOM)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def _noop(call: ServiceCall) -> None:
    """Dummy service handler."""


async def test_options_flow(hass: HomeAssistant) -> None:
    for name in ("mobile_app_phone", "send_message", "persistent_notification"):
        hass.services.async_register("notify", name, _noop)

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="carpodgo_t4_plus",
        data={"source": "carpodgo_t4_plus"},
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
