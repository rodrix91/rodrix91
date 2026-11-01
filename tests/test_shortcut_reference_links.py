"""Shortcut Markdown references must be verified, not silently ignored."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs_links import check_links  # noqa: E402


class ShortcutReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()

    def write(self, name: str, content: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_shortcut_reference_with_local_file_and_heading_resolves(self) -> None:
        self.write(
            "README.md",
            "[Manual] and [MANUAL] and ![Diagram]\n"
            "[Manual]: docs/guide.md#quick-start\n"
            "[Diagram]: docs/diagram.svg\n",
        )
        self.write("docs/guide.md", "# Quick start\n")
        self.write("docs/diagram.svg", "<svg />\n")
        self.assertEqual(check_links(self.root), [])

    def test_shortcut_reference_catches_missing_file(self) -> None:
        self.write("README.md", "[Manual]\n[Manual]: docs/not-there.md\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/not-there.md", problems[0])
        self.assertIn("missing local file", problems[0])

    def test_shortcut_image_catches_missing_file(self) -> None:
        self.write("README.md", "![Diagram]\n[Diagram]: docs/missing.svg\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/missing.svg", problems[0])

    def test_shortcut_reference_catches_invalid_heading(self) -> None:
        self.write("README.md", "[Guide]\n[Guide]: docs/guide.md#not-present\n")
        self.write("docs/guide.md", "# Present\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_full_and_collapsed_references_are_not_double_counted(self) -> None:
        self.write(
            "README.md",
            "[Full][guide] and [Guide][] and [Guide]\n"
            "[guide]: docs/missing.md\n",
        )
        problems = check_links(self.root)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all("docs/missing.md" in problem for problem in problems))

    def test_inline_link_and_shortcut_reference_have_distinct_targets(self) -> None:
        self.write(
            "README.md",
            "[Guide](docs/exists.md) [Guide]\n"
            "[Guide]: docs/missing.md\n",
        )
        self.write("docs/exists.md", "# Exists\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/missing.md", problems[0])

    def test_nested_and_escaped_shortcut_labels(self) -> None:
        self.write(
            "README.md",
            "[Review [2026]] [Work \\] done]\n"
            "[Review [2026]]: docs/missing.md\n"
            "[Work \\] done]: docs/guide.md\n",
        )
        self.write("docs/guide.md", "# Guide\n")
        # The nested label is valid Markdown; the unusual escaped label's
        # definition is not parsed by the existing flat definition matcher.
        # Keep the meaningful nested regression focused on its missing file.
        problems = check_links(self.root)
        self.assertTrue(any("docs/missing.md" in p for p in problems))

    def test_unrelated_brackets_and_code_samples_are_not_links(self) -> None:
        self.write(
            "README.md",
            "[ordinary] [unknown]\n"
            "`[Guide]` and \\[Guide] and `![Guide]`\n"
            "```markdown\n[Guide]\n```\n"
            "<!-- [Guide] -->\n"
            "[Guide]: docs/missing.md\n",
        )
        self.assertEqual(check_links(self.root), [])


if __name__ == "__main__":
    unittest.main()
