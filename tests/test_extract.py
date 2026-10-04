"""Tests for extract.py and the README example patterns."""

from pathlib import Path
import re

import pytest

from custom_components.firmware_watch.extract import (
    InvalidPattern,
    VersionNotFound,
    compile_pattern,
    extract_version,
    page_text,
)

from .conftest import load_fixture_text

CARPODGO = r"T4 Plus Firmware Update:\s*Version\s+([0-9][0-9A-Za-z._-]*)"
AMBIENT_WS = r"WS-2000/WS-4000/WS-5000 Firmware ver\.?\s*([0-9][0-9A-Za-z._-]*)"
AMBIENT_OBSERVERIP = r"ObserverIP Firmware ([0-9.]+)"
YAMAHA = r"TSR-7850\S* Firmware Update Ver\.?\s*([0-9][0-9A-Za-z._-]*)"

# (fixture file, pattern, expected version): the examples listed in README.md.
README_EXAMPLES = [
    ("carpodgo_t4plus.html", CARPODGO, "0.0.22"),
    ("ambient_firmware.html", AMBIENT_WS, "2.0.4"),
    ("ambient_firmware.html", AMBIENT_OBSERVERIP, "4.6.2"),
    ("yamaha_tsr7850.html", YAMAHA, "2.17"),
]


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


@pytest.mark.parametrize(("fixture", "pattern", "expected"), README_EXAMPLES)
def test_readme_example(fixture: str, pattern: str, expected: str) -> None:
    assert extract_version(load_fixture_text(fixture), pattern) == expected


def test_readme_lists_every_example_pattern() -> None:
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    for _, pattern, _ in README_EXAMPLES:
        assert pattern in readme


def test_ambient_ws_pattern_does_not_return_observerip_version() -> None:
    html = load_fixture_text("ambient_firmware.html")
    assert extract_version(html, AMBIENT_WS) != "4.6.2"


def test_compiled_pattern_accepted() -> None:
    compiled = compile_pattern(r"v(\d+)")
    assert extract_version("<p>v12</p>", compiled) == "12"


def test_version_not_found() -> None:
    with pytest.raises(VersionNotFound):
        extract_version("<p>nothing here</p>", CARPODGO)


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


def test_yamaha_ignores_amazon_music_flyer() -> None:
    html = load_fixture_text("yamaha_tsr7850.html")
    assert "Amazon Music Firmware Update flyer" in page_text(html)
    assert extract_version(html, YAMAHA) == "2.17"


def test_user_agent_value() -> None:
    from custom_components.firmware_watch.const import USER_AGENT

    assert USER_AGENT == "Mozilla/5.0 (compatible; HomeAssistant-FirmwareWatch/0.1)"
