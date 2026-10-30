"""Cover nested, escaped reference links and their rendered Markdown anchors."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs_links import check_links  # noqa: E402


class NestedReferenceLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()

    def write(self, path: str, body: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    def test_balanced_nested_reference_link_resolves(self) -> None:
        self.write(
            "README.md", "[Review [2026]][guide]\n[guide]: docs/guide.md\n"
        )
        self.write("docs/guide.md", "# Guide\n")
        self.assertEqual(check_links(self.root), [])

    def test_nested_reference_with_unknown_id_fails_closed(self) -> None:
        self.write("README.md", "[Review [2026]][missing]\n")
        self.assertIn("undefined reference", check_links(self.root)[0])

    def test_nested_reference_with_missing_target_fails_closed(self) -> None:
        self.write(
            "README.md", "[Review [2026]][guide]\n[guide]: docs/absent.md\n"
        )
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_escaped_closing_bracket_in_link_text_still_checks_target(self) -> None:
        self.write(
            "README.md",
            r"[Review \] approved][guide]" + "\n"
            "[guide]: docs/absent.md\n",
        )
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_escaped_opening_bracket_does_not_start_reference_link(self) -> None:
        self.write("README.md", r"\[Example [2026]][undefined]" + "\n")
        self.assertEqual(check_links(self.root), [])

    def test_nested_reference_image_target_is_checked(self) -> None:
        self.write(
            "README.md",
            "![Chart [2026]][image]\n[image]: docs/missing.png\n",
        )
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_nested_reference_heading_anchor_matches_rendered_label(self) -> None:
        self.write("README.md", "[read](docs/guide.md#review-2026)\n")
        self.write(
            "docs/guide.md",
            "# [Review [2026]][manual]\n[manual]: ../README.md\n",
        )
        self.assertEqual(check_links(self.root), [])

    def test_wrong_nested_reference_heading_anchor_is_rejected(self) -> None:
        self.write("README.md", "[read](docs/guide.md#review-manual)\n")
        self.write(
            "docs/guide.md",
            "# [Review [2026]][manual]\n[manual]: ../README.md\n",
        )
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_multiple_reference_links_on_same_line(self) -> None:
        self.write(
            "README.md",
            "[Q [one]][first] and [Q [two]][second]\n"
            "[first]: docs/valid.md\n[second]: docs/missing.md\n",
        )
        self.write("docs/valid.md", "# Valid\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/missing.md", problems[0])

    def test_nested_reference_inside_inline_code_is_literal(self) -> None:
        self.write(
            "README.md", "Use \x60[Review [2026]][undefined]\x60 as an example.\n"
        )
        self.assertEqual(check_links(self.root), [])

    def test_regular_full_and_collapsed_references_still_work(self) -> None:
        self.write(
            "README.md",
            "[Guide][manual] and [Manual][]\n"
            "[manual]: docs/guide.md\n",
        )
        self.write("docs/guide.md", "# Guide\n")
        self.assertEqual(check_links(self.root), [])

    def test_inline_and_nested_reference_links_are_both_checked(self) -> None:
        self.write(
            "README.md",
            "[Inline](docs/valid.md) [Reference [Q4]][guide]\n"
            "[guide]: docs/missing.md\n",
        )
        self.write("docs/valid.md", "# Valid\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/missing.md", problems[0])


if __name__ == "__main__":
    unittest.main()
