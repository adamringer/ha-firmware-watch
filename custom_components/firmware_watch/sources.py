"""Built-in firmware source presets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .const import CONF_NAME, CONF_PATTERN, CONF_SOURCE, CONF_URL, SOURCE_CUSTOM


@dataclass(frozen=True)
class SourcePreset:
    """A pre-filled (name, url, pattern) source."""

    key: str
    name: str
    url: str
    pattern: str


PRESETS: dict[str, SourcePreset] = {
    "carpodgo_t4_plus": SourcePreset(
        key="carpodgo_t4_plus",
        name="CarPodGo T4 Plus",
        url="https://www.carpodgo.com/pages/firmware-t4-plus",
        pattern=r"T4 Plus Firmware Update:\s*Version\s+([0-9][0-9A-Za-z._-]*)",
    ),
    "ambient_ws2000": SourcePreset(
        key="ambient_ws2000",
        name="Ambient Weather WS-2000",
        url="https://ambientweather.com/firmware-update-alerts",
        pattern=(
            r"WS-2000/WS-4000/WS-5000 Firmware ver\.?\s*([0-9][0-9A-Za-z._-]*)"
        ),
    ),
    "yamaha_tsr_7850": SourcePreset(
        key="yamaha_tsr_7850",
        name="Yamaha TSR-7850",
        url=(
            "https://usa.yamaha.com/products/audio_visual/av_receivers_amps/"
            "tsr-7850/downloads.html"
        ),
        pattern=r"TSR-7850\S* Firmware Update Ver\.?\s*([0-9][0-9A-Za-z._-]*)",
    ),
}


def resolve_source(data: Mapping[str, Any]) -> tuple[str, str, str]:
    """Return (name, url, pattern) for a config entry's data."""
    key = data[CONF_SOURCE]
    if key == SOURCE_CUSTOM:
        return data[CONF_NAME], data[CONF_URL], data[CONF_PATTERN]
    preset = PRESETS[key]
    return preset.name, preset.url, preset.pattern
