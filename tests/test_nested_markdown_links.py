"""Regression tests for nested and escaped Markdown inline-link labels."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs_links import check_links  # noqa: E402


class NestedMarkdownLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def test_balanced_nested_link_label_is_checked(self) -> None:
        self.write("README.md", "[Read [review]](docs/guide.md)\n")
        self.write("docs/guide.md", "# Guide\n")
        self.assertEqual(check_links(self.root), [])

    def test_deeply_nested_missing_target_is_not_silently_ignored(self) -> None:
        self.write("README.md", "[Quarter [FY [2026]]](docs/missing.md)\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing local file", problems[0])

    def test_escaped_closing_bracket_in_label_does_not_hide_broken_link(self) -> None:
        self.write("README.md", r"[Quarter \] reviewed](docs/absent.md)" + "\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing local file", problems[0])

    def test_escaped_opening_bracket_is_literal_text(self) -> None:
        self.write("README.md", r"\[not a link](docs/absent.md)" + "\n")
        self.assertEqual(check_links(self.root), [])

    def test_double_escaped_backslash_before_link_still_checks_it(self) -> None:
        self.write("README.md", r"\\[guide](docs/absent.md)" + "\n")
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_nested_image_alt_label_destination_is_checked(self) -> None:
        self.write("README.md", "![Chart [Q4]](docs/chart-absent.png)\n")
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_nested_heading_link_label_generates_correct_anchor(self) -> None:
        self.write("README.md", "[review](docs/guide.md#review-2026)\n")
        self.write("docs/guide.md", "# [Review [2026]](../README.md)\n")
        self.assertEqual(check_links(self.root), [])

    def test_wrong_nested_heading_anchor_is_rejected(self) -> None:
        self.write("README.md", "[review](docs/guide.md#review-2027)\n")
        self.write("docs/guide.md", "# [Review [2026]](../README.md)\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_inline_code_containing_nested_link_is_not_navigation(self) -> None:
        self.write("README.md", "Use \x60[example [2026]](missing.md)\x60 in your docs.\n")
        self.assertEqual(check_links(self.root), [])

    def test_two_nested_links_on_same_line_are_both_checked(self) -> None:
        self.write(
            "README.md",
            "[one [Q1]](docs/first.md) and [two [Q2]](docs/second.md)\n",
        )
        self.write("docs/first.md", "# First\n")
        self.assertEqual(len(check_links(self.root)), 1)
        self.assertIn("docs/second.md", check_links(self.root)[0])


if __name__ == "__main__":
    unittest.main()
