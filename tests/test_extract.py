"""Tests for extract.py and the built-in presets."""

import re

import pytest

from custom_components.firmware_watch.extract import (
    InvalidPattern,
    VersionNotFound,
    compile_pattern,
    extract_version,
    page_text,
)
from custom_components.firmware_watch.sources import PRESETS

from .conftest import load_fixture_text


def test_page_text_strips_script_style_tags() -> None:
    html = (
        "<html><head><style>.a{}</style><script>var v='Version 9';</script></head>"
        "<body><noscript>NS</noscript><template>TPL</template>"
        "<p>Hello</p><p>World</p></body></html>"
    )
    assert page_text(html) == "Hello World"


def test_page_text_entities_and_whitespace() -> None:
    assert page_text("<p>a&nbsp;&nbsp;b\n\n c &amp; d &lt;e&gt;</p>") == "a b c & d <e>"


def test_page_text_excludes_meta_attributes() -> None:
    html = load_fixture_text("carpodgo_t4plus.html")
    text = page_text(html)
    assert "Release Highlights: Optimized CarPlay Swipe SmoothnessRefined" not in text
    assert "T4 Plus Firmware Update:" in text
    assert re.search(r"Version\s+0\.0\.22", text)


def test_carpodgo_preset() -> None:
    html = load_fixture_text("carpodgo_t4plus.html")
    assert extract_version(html, PRESETS["carpodgo_t4_plus"].pattern) == "0.0.22"


def test_ambient_preset() -> None:
    html = load_fixture_text("ambient_firmware.html")
    assert extract_version(html, PRESETS["ambient_ws2000"].pattern) == "2.0.4"


def test_ambient_observerip_not_matched_by_preset() -> None:
    html = load_fixture_text("ambient_firmware.html")
    assert extract_version(html, PRESETS["ambient_ws2000"].pattern) != "4.6.2"


def test_custom_pattern() -> None:
    html = load_fixture_text("ambient_firmware.html")
    assert extract_version(html, r"ObserverIP Firmware ([0-9.]+)") == "4.6.2"


def test_compiled_pattern_accepted() -> None:
    compiled = compile_pattern(r"v(\d+)")
    assert extract_version("<p>v12</p>", compiled) == "12"


def test_version_not_found() -> None:
    with pytest.raises(VersionNotFound):
        extract_version("<p>nothing here</p>", PRESETS["carpodgo_t4_plus"].pattern)


def test_empty_group_is_not_found() -> None:
    with pytest.raises(VersionNotFound):
        extract_version("<p>v</p>", r"v(\d*)")


@pytest.mark.parametrize("pattern", ["([", r"no group", r"(a)(b)"])
def test_invalid_pattern(pattern: str) -> None:
    with pytest.raises(InvalidPattern):
        compile_pattern(pattern)


def test_case_sensitive() -> None:
    with pytest.raises(VersionNotFound):
        extract_version("<p>version 1</p>", r"Version (\d)")


def test_yamaha_preset() -> None:
    html = load_fixture_text("yamaha_tsr7850.html")
    assert extract_version(html, PRESETS["yamaha_tsr_7850"].pattern) == "2.17"


def test_yamaha_ignores_amazon_music_flyer() -> None:
    html = load_fixture_text("yamaha_tsr7850.html")
    assert "Amazon Music Firmware Update flyer" in page_text(html)
    assert extract_version(html, PRESETS["yamaha_tsr_7850"].pattern) == "2.17"


def test_user_agent_value() -> None:
    from custom_components.firmware_watch.const import USER_AGENT

    assert USER_AGENT == "Mozilla/5.0 (compatible; HomeAssistant-FirmwareWatch/0.1)"
