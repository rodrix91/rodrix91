"""Validate local Markdown links in the GitHub portfolio.

External links are intentionally not fetched: this is a deterministic,
network-free check of local pages and heading anchors.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(" + chr(96) + r"{3,}|~{3,})")
INLINE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def _prose_lines(content: str):
    """Yield numbered lines outside fenced Markdown code blocks."""
    fence_char = ""
    fence_length = 0
    for number, line in enumerate(content.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker = match.group(1)
            if not fence_char:
                fence_char, fence_length = marker[0], len(marker)
                continue
            if marker[0] == fence_char and len(marker) >= fence_length:
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


def check_links(root: Path) -> list[str]:
    """Return actionable errors for local relative links and heading fragments."""
    root = root.resolve()
    markdown_files = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
    problems: list[str] = []
    for source in markdown_files:
        if not source.is_file():
            problems.append(f"{source.relative_to(root)}: Markdown file is missing")
            continue
        for line_number, line in _prose_lines(source.read_text(encoding="utf-8")):
            for match in LINK.finditer(line):
                address = match.group(1).strip()
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
