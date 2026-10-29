"""Validate local Markdown links in the GitHub portfolio.

External links are intentionally not fetched: this is a deterministic,
network-free check of local pages and heading anchors.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK_START = re.compile(r"!?\[[^\]\n]*\]\(")
REFERENCE_LINK = re.compile(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]")
REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))")
INLINE_CODE = re.compile(r"(?<!"+chr(96)+r")("+chr(96)+r"+)(.*?)\1(?!"+chr(96)+r")")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^ {0,3}(" + chr(96) + r"{3,}|~{3,})(.*)$")
INLINE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
INLINE_TARGET = re.compile(r"""^\s*(?:<([^>\n]+)>|([^\s<>\n]+))(?:[ \t]+(?:"[^"\n]*"|'[^'\n]*'))?[ \t]*$""")


def _prose_lines(content: str):
    """Yield numbered lines outside fenced Markdown code blocks."""
    fence_char = ""
    fence_length = 0
    for number, line in enumerate(content.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker, suffix = match.groups()
            if not fence_char:
                # Markdown fence markers may be indented by no more than
                # three spaces; a backtick fence cannot have backticks in
                # its info string.
                if marker[0] != "`" or "`" not in suffix:
                    fence_char, fence_length = marker[0], len(marker)
                    continue
            elif marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                # A closing marker may be longer than the opener, but it
                # cannot have an info string or other trailing text.
                fence_char, fence_length = "", 0
                continue
        if not fence_char:
            yield number, line


def _anchors(content: str) -> set[str]:
    """Build GitHub-style heading slugs, with repeat-heading suffixes."""
    found: set[str] = set()
    repetitions: dict[str, int] = {}
    for _, line in _prose_lines(content):
        match = HEADING.match(line)
        if not match:
            continue
        heading = INLINE_LINK.sub(r"\1", match.group(1)).replace(chr(96), "")
        slug = re.sub(r"\s+", "-", re.sub(r"[^\w -]", "", heading.casefold()).strip())
        count = repetitions.get(slug, 0)
        repetitions[slug] = count + 1
        found.add(f"{slug}-{count}" if count else slug)
    return found


def _inline_target(address: str) -> str:
    """Strip an optional quoted Markdown title; preserve the path for validation.

    An angle-bracket destination may contain spaces. Unrecognized syntax stays
    untouched so it cannot be mistaken for a valid local link.
    """
    address = address.strip()
    parsed = INLINE_TARGET.fullmatch(address)
    return (parsed.group(1) or parsed.group(2)) if parsed else address


def _inline_addresses(line: str) -> list[str]:
    """Read balanced inline link destinations, including filenames with parentheses.

    A quoted optional title may itself contain parentheses. Skip escaped
    punctuation while searching for the matching closing link delimiter.
    """
    addresses: list[str] = []
    offset = 0
    while match := LINK_START.search(line, offset):
        start = match.end()
        depth = 0
        quote = ""
        in_angle = False
        escaped = False
        for index in range(start, len(line)):
            char = line[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if quote:
                if char == quote:
                    quote = ""
                continue
            if char == "<":
                in_angle = True
            elif char == ">":
                in_angle = False
            elif char in ("'", '"') and not in_angle and line[index - 1].isspace():
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    address = _inline_target(line[start:index])
                    addresses.append(re.sub(r"\\([()])", r"\1", address))
                    offset = index + 1
                    break
                depth -= 1
        else:
            offset = match.end()
    return addresses


def _reference_key(text: str) -> str:
    """Markdown reference labels ignore case and repeated whitespace."""
    return " ".join(text.split()).casefold()


def check_links(root: Path) -> list[str]:
    """Return actionable errors for inline and reference-style local links."""
    root = root.resolve()
    markdown_files = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
    problems: list[str] = []
    for source in markdown_files:
        if not source.is_file():
            problems.append(f"{source.relative_to(root)}: Markdown file is missing")
            continue

        prose = list(_prose_lines(source.read_text(encoding="utf-8")))
        references: dict[str, str] = {}
        for line_number, line in prose:
            definition = REFERENCE_DEFINITION.match(line)
            if definition is None:
                continue
            key = _reference_key(definition.group(1))
            if key in references:
                problems.append(
                    f"{source.relative_to(root)}:{line_number}: duplicate reference [{key}]"
                )
            else:
                references[key] = (definition.group(2) or definition.group(3)).strip()

        for line_number, line in prose:
            # A code sample is not a navigation link, even when inline.
            visible = INLINE_CODE.sub("", line)
            if REFERENCE_DEFINITION.match(visible):
                continue
            addresses = _inline_addresses(visible)
            for match in REFERENCE_LINK.finditer(visible):
                key = _reference_key(match.group(2) or match.group(1))
                if key not in references:
                    problems.append(
                        f"{source.relative_to(root)}:{line_number}: undefined reference [{key}]"
                    )
                else:
                    addresses.append(references[key])

            for address in addresses:
                parts = urlsplit(address)
                if parts.scheme or parts.netloc or address.startswith("//"):
                    continue
                relative = unquote(parts.path)
                target = (source.parent / relative).resolve() if relative else source
                label = f"{source.relative_to(root)}:{line_number}: {address!r}"
                if not target.is_relative_to(root):
                    problems.append(f"{label}: path escapes repository")
                elif not target.is_file():
                    problems.append(f"{label}: missing local file")
                elif parts.fragment and target.suffix.lower() == ".md":
                    fragment = unquote(parts.fragment).casefold()
                    if fragment not in _anchors(target.read_text(encoding="utf-8")):
                        problems.append(f"{label}: unknown Markdown heading #{fragment}")
    return problems


def main() -> int:
    problems = check_links(ROOT)
    if problems:
        for message in problems:
            print(message)
        return 1
    print("Portfolio local Markdown links and anchors: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
