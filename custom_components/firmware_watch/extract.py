"""Pure version extraction from HTML (no Home Assistant imports)."""

from __future__ import annotations

from html.parser import HTMLParser
import re

_SKIP_TAGS = frozenset({"script", "style", "noscript", "template"})


class InvalidPattern(ValueError):
    """The pattern is not a valid regex with exactly one capture group."""


class VersionNotFound(ValueError):
    """The pattern did not match the page."""


class _TextParser(HTMLParser):
    """Collect visible text, skipping script/style/noscript/template."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        self.parts.append(" ")

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        # Self-closing tags never get an end tag, so don't change skip depth.
        self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def page_text(html: str) -> str:
    """Return the page's visible text with whitespace collapsed."""
    parser = _TextParser()
    parser.feed(html)
    parser.close()
    # str.split() treats \xa0 (from &nbsp;) as whitespace.
    return " ".join("".join(parser.parts).split())


def compile_pattern(pattern: str) -> re.Pattern[str]:
    """Compile a pattern that must have exactly one capture group."""
    try:
        compiled = re.compile(pattern)
    except re.error as err:
        raise InvalidPattern(f"Invalid regular expression: {err}") from err
    if compiled.groups != 1:
        raise InvalidPattern(
            f"Pattern must have exactly one capture group, found {compiled.groups}"
        )
    return compiled


def extract_version(html: str, pattern: str | re.Pattern[str]) -> str:
    """Return group 1 of the first match against the page's visible text."""
    compiled = (
        compile_pattern(pattern) if isinstance(pattern, str) else pattern
    )
    if compiled.groups != 1:
        raise InvalidPattern("Pattern must have exactly one capture group")
    match = compiled.search(page_text(html))
    version = (match.group(1) or "").strip() if match else ""
    if not version:
        raise VersionNotFound("Pattern did not match the page")
    return version
