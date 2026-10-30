"""Validate local Markdown links in the GitHub portfolio.

External links are intentionally not fetched: this is a deterministic,
network-free check of local pages and heading anchors.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))")
BACKTICK_RUN = re.compile(r"`+")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^ {0,3}(" + chr(96) + r"{3,}|~{3,})(.*)$")
INLINE_TARGET = re.compile(r"""^\s*(?:<([^>\n]+)>|([^\s<>\n]+))(?:[ \t]+(?:"[^"\n]*"|'[^'\n]*'))?[ \t]*$""")


def _escaped_by_backslash(line: str, offset: int) -> bool:
    """An odd-length preceding backslash run escapes the following character."""
    count = 0
    while offset > 0 and line[offset - 1] == "\\":
        count += 1
        offset -= 1
    return count % 2 == 1


def _inline_code_spans(line: str):
    """Yield code-span offsets, excluding escaped opening backticks.

    A closing delimiter must match the opening run length. Backslashes inside
    an actual code span are literal, so they do not escape closing backticks.
    """
    runs = list(BACKTICK_RUN.finditer(line))
    cursor = 0
    while cursor < len(runs):
        opening = runs[cursor]
        if _escaped_by_backslash(line, opening.start()):
            cursor += 1
            continue
        closing_index = next(
            (
                index
                for index in range(cursor + 1, len(runs))
                if len(runs[index].group()) == len(opening.group())
            ),
            None,
        )
        if closing_index is None:
            cursor += 1
            continue
        yield opening.start(), runs[closing_index].end()
        cursor = closing_index + 1


def _without_inline_code(line: str) -> str:
    """Remove actual Markdown inline code without hiding escaped delimiters."""
    parts: list[str] = []
    offset = 0
    for start, end in _inline_code_spans(line):
        parts.append(line[offset:start])
        offset = end
    parts.append(line[offset:])
    return "".join(parts)


def _without_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Remove Markdown HTML comments, including comments spanning lines.

    Keep a separating space where a comment starts so unrelated Markdown
    tokens on either side cannot accidentally join into a new link.
    """
    visible: list[str] = []
    offset = 0
    while offset < len(line):
        if in_comment:
            closing = line.find("-->", offset)
            if closing == -1:
                break
            offset = closing + 3
            in_comment = False
            continue

        opening = line.find("<!--", offset)
        # Escaped openers and markers inside inline code are visible text.
        while opening != -1 and (
            _escaped_by_backslash(line, opening)
            or any(start <= opening < end for start, end in _inline_code_spans(line))
        ):
            opening = line.find("<!--", opening + 4)
        if opening == -1:
            visible.append(line[offset:])
            break
        visible.extend((line[offset:opening], " "))
        offset = opening + 4
        in_comment = True
    return "".join(visible), in_comment


def _prose_lines(content: str):
    """Yield numbered visible lines outside fences and HTML comments."""
    fence_char = ""
    fence_length = 0
    in_comment = False
    for number, line in enumerate(content.splitlines(), 1):
        if fence_char:
            # Comments appearing inside code fences are literal examples.
            match = FENCE.match(line)
            if match:
                marker, suffix = match.groups()
                if marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                    fence_char, fence_length = "", 0
            continue

        visible, in_comment = _without_html_comments(line, in_comment)
        match = FENCE.match(visible)
        if match:
            marker, suffix = match.groups()
            # Backtick fence info strings may not contain backticks.
            if marker[0] != chr(96) or chr(96) not in suffix:
                fence_char, fence_length = marker[0], len(marker)
                continue
        yield number, visible

def _github_lower(text: str) -> str:
    """Lowercase headings without full case folding (which expands ß to ss).

    GitHub also lowercases uppercase Greek sigma to σ independently of its
    position; Python's context-sensitive lower() makes word-final Σ into ς.
    """
    return text.replace("Σ", "σ").lower()


def _anchors(content: str) -> set[str]:
    """Build GitHub-style heading slugs, with repeat-heading suffixes."""
    found: set[str] = set()
    for _, line in _prose_lines(content):
        match = HEADING.match(line)
        if not match:
            continue
        heading = _heading_link_labels(match.group(1)).replace(chr(96), "")
        slug = re.sub(r"\s+", "-", re.sub(r"[^\w -]", "", _github_lower(heading)).strip())
        # A literal heading such as "Guide-1" can collide with the generated
        # suffix of a repeated "Guide" heading. Reserve every final slug,
        # not just the occurrence count of each unsuffixed heading.
        candidate = slug
        number = 0
        while candidate in found:
            number += 1
            candidate = f"{slug}-{number}"
        found.add(candidate)
    return found


def _inline_target(address: str) -> str:
    """Strip an optional quoted Markdown title; preserve the path for validation.

    An angle-bracket destination may contain spaces. Unrecognized syntax stays
    untouched so it cannot be mistaken for a valid local link.
    """
    address = address.strip()
    parsed = INLINE_TARGET.fullmatch(address)
    return (parsed.group(1) or parsed.group(2)) if parsed else address


def _link_end(line: str, start: int) -> int | None:
    """End of a link, ignoring literal parentheses inside angle destinations."""
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
        elif char == "(" and not in_angle:
            # Parentheses inside <...> are literal destination characters,
            # even when unbalanced. They do not nest the link delimiter.
            depth += 1
        elif char == ")" and not in_angle:
            if depth == 0:
                return index
            depth -= 1
    return None


def _bracketed_links(line: str, following: str):
    """Find nested, escaped link labels followed by the requested delimiter.

    Labels may include balanced square brackets; scanning only with a flat
    regular expression silently ignores such Markdown navigation links.
    """
    cursor = 0
    while cursor < len(line):
        start = cursor
        if line[cursor] == "!" and line[cursor + 1 : cursor + 2] == "[":
            opening = cursor + 1
        elif line[cursor] == "[":
            opening = cursor
        else:
            cursor += 1
            continue

        escapes = 0
        previous = start - 1
        while previous >= 0 and line[previous] == "\\":
            escapes += 1
            previous -= 1
        if escapes % 2:
            cursor = opening + 1
            continue

        depth = 1
        index = opening + 1
        escaped = False
        while index < len(line) and depth:
            char = line[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
            index += 1

        if depth == 0 and line[index : index + 1] == following:
            yield start, index + 1, line[opening + 1 : index - 1]
            cursor = index + 1
        else:
            cursor = opening + 1


def _inline_link_starts(line: str):
    """Find inline Markdown links and image links, including nested labels."""
    yield from _bracketed_links(line, "(")


def _reference_links(line: str):
    """Yield complete full/collapsed reference links with balanced link text.

    The reference ID itself is a flat label as required by CommonMark, but
    the visible link text can contain nested or backslash-escaped brackets.
    """
    for start, key_start, label in _bracketed_links(line, "["):
        index = key_start
        escaped = False
        while index < len(line):
            char = line[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "[":
                break
            elif char == "]":
                yield start, index + 1, label, line[key_start:index]
                break
            index += 1


def _reference_label_text(prose: str) -> str:
    """Replace each reference link with its visible label for heading anchors."""
    parts: list[str] = []
    offset = 0
    for start, end, label, _ in _reference_links(prose):
        if start < offset:
            continue
        parts.extend((prose[offset:start], label))
        offset = end
    parts.append(prose[offset:])
    return "".join(parts)


def _inline_addresses(line: str) -> list[str]:
    """Read balanced inline link destinations, including escaped parentheses."""
    addresses: list[str] = []
    for _, destination_start, _ in _inline_link_starts(line):
        end = _link_end(line, destination_start)
        if end is None:
            continue
        address = _inline_target(line[destination_start:end])
        addresses.append(re.sub(r"\\([()])", r"\1", address))
    return addresses


def _heading_link_labels(heading: str) -> str:
    """Use rendered link labels while retaining literal text inside inline code."""

    def prose_labels(prose: str) -> str:
        pieces: list[str] = []
        offset = 0
        for start, destination_start, label in _inline_link_starts(prose):
            if start < offset:
                continue
            end = _link_end(prose, destination_start)
            if end is None:
                continue
            pieces.append(prose[offset:start])
            pieces.append(label)
            offset = end + 1
        pieces.append(prose[offset:])
        return _reference_label_text("".join(pieces))

    # Inline code displays its brackets, parentheses and reference suffix
    # literally, so it must not undergo link-label substitutions.
    pieces: list[str] = []
    offset = 0
    for start, end in _inline_code_spans(heading):
        pieces.append(prose_labels(heading[offset:start]))
        pieces.append(heading[start:end])
        offset = end
    pieces.append(prose_labels(heading[offset:]))
    return "".join(pieces)


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
            visible = _without_inline_code(line)
            if REFERENCE_DEFINITION.match(visible):
                continue
            addresses = _inline_addresses(visible)
            for _, _, label, reference_id in _reference_links(visible):
                key = _reference_key(reference_id or label)
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
                    fragment = _github_lower(unquote(parts.fragment))
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
