"""Validate HTML link and image destinations in portfolio Markdown documents."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs_links import check_links  # noqa: E402


class HtmlLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "docs").mkdir()

    def write(self, name: str, text: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_html_anchor_and_image_relative_targets_are_validated(self) -> None:
        self.write(
            "README.md",
            '<a href="docs/guide.md#overview">Guide</a>\n'
            '<img src="docs/diagram.svg" alt="Diagram">\n'
            '<a href="docs/missing.md">Missing</a>\n'
            '<img src="docs/absent.png">Absent</img>\n',
        )
        self.write("docs/guide.md", "# Overview\n")
        self.write("docs/diagram.svg", "<svg />\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("README.md:3:", problems[0])
        self.assertIn("docs/missing.md", problems[0])
        self.assertIn("README.md:4:", problems[1])
        self.assertIn("docs/absent.png", problems[1])

    def test_multiline_html_attributes_retain_opening_tag_source_line(self) -> None:
        self.write(
            "README.md",
            "# Portfolio\n"
            '<a class="guide"\n'
            '   href="docs/guide.md#missing">Read</a>\n',
        )
        self.write("docs/guide.md", "# Existing\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("README.md:2:", problems[0])
        self.assertIn("unknown Markdown heading", problems[0])

    def test_html_entities_and_unquoted_attributes_are_resolved(self) -> None:
        self.write(
            "README.md",
            '<a href="docs/teams&amp;data.md">Teams</a>\n'
            "<img src=docs/chart.svg alt=Chart>\n",
        )
        self.write("docs/teams&data.md", "# Teams\n")
        self.write("docs/chart.svg", "<svg />\n")
        self.assertEqual(check_links(self.root), [])

    def test_html_in_code_blocks_comments_and_inline_code_is_ignored(self) -> None:
        self.write(
            "README.md",
            '`<a href="docs/missing-one.md">literal</a>`\n'
            "<!-- <a href='docs/missing-two.md'>comment</a> -->\n"
            "```html\n"
            '<img src="docs/missing-three.png">\n'
            "```\n"
            "    <a href='docs/missing-four.md'>indented example</a>\n",
        )
        self.assertEqual(check_links(self.root), [])

    def test_html_unsafe_schemes_and_credentials_use_existing_guards(self) -> None:
        self.write(
            "README.md",
            '<a href="javascript:alert(1)">Bad</a>\n'
            '<a href="https://user:secret@example.org/private">Private</a>\n'
            '<a href="https://example.org/docs">External</a>\n',
        )
        problems = check_links(self.root)
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("unsafe URL scheme", problems[0])
        self.assertIn("credentials in HTTP(S) URL", problems[1])
        self.assertNotIn("secret", " ".join(problems))

    def test_html_and_markdown_links_are_both_checked(self) -> None:
        self.write(
            "README.md",
            "[Markdown](docs/missing-one.md)\n"
            '<a href="docs/missing-two.md">HTML</a>\n',
        )
        problems = check_links(self.root)
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("missing-one", problems[0])
        self.assertIn("missing-two", problems[1])


if __name__ == "__main__":
    unittest.main()
