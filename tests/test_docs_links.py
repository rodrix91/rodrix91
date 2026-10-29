"""Network-free regressions for the portfolio Markdown link checker."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs_links import check_links  # noqa: E402


class PortfolioLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()

    def write(self, path: str, body: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    def test_valid_links_and_heading_fragments(self) -> None:
        self.write("README.md", "[guide](docs/guide.md#five-minute-review)\n")
        self.write("docs/guide.md", "# Five-minute review\n[home](../README.md)\n")
        self.assertEqual(check_links(self.root), [])

    def test_missing_target_is_an_error(self) -> None:
        self.write("README.md", "[missing](docs/absent.md)\n")
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing local file", problems[0])

    def test_nonexistent_heading_is_an_error(self) -> None:
        self.write("README.md", "[guide](docs/guide.md#wrong-heading)\n")
        self.write("docs/guide.md", "# Real heading\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_external_links_and_fenced_examples_are_skipped(self) -> None:
        self.write(
            "README.md",
            "[GitHub](https://github.com/rodrix91) [email](mailto:test@example.com)\n"
            "~~~md\n[example](does-not-exist.md)\n~~~\n",
        )
        self.assertEqual(check_links(self.root), [])

    def test_code_fence_with_info_suffix_inside_is_not_closed(self) -> None:
        self.write(
            "README.md",
            "```text\n```python\n[example](missing.md)\n```\n",
        )
        self.assertEqual(check_links(self.root), [])

    def test_indented_fence_marker_does_not_hide_real_broken_links(self) -> None:
        # Four spaces introduce indented code, not a fenced code block.
        self.write("README.md", "    ```\n\n[broken](docs/missing.md)\n")
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_fence_with_trailing_text_does_not_create_heading_anchor(self) -> None:
        self.write("README.md", "[section](docs/guide.md#not-a-heading)\n")
        self.write(
            "docs/guide.md",
            "~~~markdown\n~~~not-a-closer\n# Not a heading\n~~~\n",
        )
        problems = check_links(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("unknown Markdown heading", problems[0])

    def test_valid_longer_closing_fence_and_trailing_spaces(self) -> None:
        self.write(
            "README.md",
            "````python\n[example](missing.md)\n`````   \n"
            "[guide](docs/guide.md#real-heading)\n",
        )
        self.write("docs/guide.md", "# Real heading\n")
        self.assertEqual(check_links(self.root), [])

    def test_inline_links_with_quoted_titles_and_fragments(self) -> None:
        self.write(
            "README.md",
            "[double](docs/guide.md \"Open the guide\")\n"
            "[single](docs/guide.md#intro 'Jump to intro')\n"
            "[website](https://github.com/rodrix91 \"Profile\")\n",
        )
        self.write("docs/guide.md", "# Intro\n")
        self.assertEqual(check_links(self.root), [])

    def test_angle_bracket_destination_with_spaces_and_title(self) -> None:
        self.write(
            "README.md",
            "[report](<docs/data quality.md> \"Data report\")\n",
        )
        self.write("docs/data quality.md", "# Data quality\n")
        self.assertEqual(check_links(self.root), [])

    def test_titled_link_to_missing_file_is_still_rejected(self) -> None:
        self.write("README.md", "[missing](docs/absent.md \"Missing report\")\n")
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_titled_link_to_missing_anchor_is_still_rejected(self) -> None:
        self.write("README.md", "[missing](docs/guide.md#absent 'Jump')\n")
        self.write("docs/guide.md", "# Present\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_titled_parent_traversal_is_still_rejected(self) -> None:
        self.write("README.md", "[outside](../../private.md \"Private\")\n")
        self.assertIn("path escapes repository", check_links(self.root)[0])

    def test_balanced_parentheses_in_local_link_destinations(self) -> None:
        self.write(
            "README.md",
            "[guide](docs/guide(v2).md)\n"
            "[nested](docs/report(quarter(4)).md)\n",
        )
        self.write("docs/guide(v2).md", "# Guide\n")
        self.write("docs/report(quarter(4)).md", "# Report\n")
        self.assertEqual(check_links(self.root), [])

    def test_quoted_title_with_parentheses_does_not_end_link(self) -> None:
        self.write("README.md", '[guide](docs/guide.md "Read (now)")\n')
        self.write("docs/guide.md", "# Guide\n")
        self.assertEqual(check_links(self.root), [])

    def test_missing_parenthesized_file_is_still_rejected(self) -> None:
        self.write("README.md", "[missing](docs/absent(v2).md)\n")
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_parenthesized_traversal_still_fails_closed(self) -> None:
        self.write("README.md", "[outside](../../outside(v2).md)\n")
        self.assertIn("path escapes repository", check_links(self.root)[0])

    def test_escaped_parenthesis_in_local_filename(self) -> None:
        self.write("README.md", r"[guide](docs/guide\(v2\).md)" + "\n")
        self.write("docs/guide(v2).md", "# Guide\n")
        self.assertEqual(check_links(self.root), [])

    def test_relative_parent_traversal_is_rejected(self) -> None:
        self.write("README.md", "[outside](../../secrets.txt)\n")
        self.assertIn("path escapes repository", check_links(self.root)[0])

    def test_percent_encoded_name_resolves(self) -> None:
        self.write("README.md", "[guide](docs/data%20quality.md)\n")
        self.write("docs/data quality.md", "# Data quality\n")
        self.assertEqual(check_links(self.root), [])

    def test_heading_link_with_parenthesized_filename_uses_label_slug(self) -> None:
        self.write("README.md", "[heading](docs/guide.md#release-notes)\n")
        self.write("docs/guide.md", "# [Release notes](guide(v2).md)\n")
        self.assertEqual(check_links(self.root), [])

    def test_heading_link_with_nested_parentheses_and_title(self) -> None:
        self.write("README.md", "[heading](docs/guide.md#next-release)\n")
        self.write(
            "docs/guide.md",
            '# [Next release](notes(v2(beta)).md "Notes (reviewed)")\n',
        )
        self.assertEqual(check_links(self.root), [])

    def test_multiple_linked_labels_in_same_heading(self) -> None:
        self.write("README.md", "[heading](docs/guide.md#part-a-and-part-b)\n")
        self.write(
            "docs/guide.md",
            "# [Part A](a(v2).md) and [Part B](b(v3).md)\n",
        )
        self.assertEqual(check_links(self.root), [])

    def test_unrelated_heading_fragment_still_fails(self) -> None:
        self.write("README.md", "[broken](docs/guide.md#release-notes-v2)\n")
        self.write("docs/guide.md", "# [Release notes](guide(v2).md)\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_duplicate_heading_slugs_are_numbered(self) -> None:
        self.write("README.md", "[two](docs/guide.md#hello-1)\n")
        self.write("docs/guide.md", "# Hello\n# Hello\n")
        self.assertEqual(check_links(self.root), [])

    def test_literal_heading_collides_with_generated_duplicate_slug(self) -> None:
        self.write(
            "README.md",
            "[first](docs/guide.md#guide)\n"
            "[second](docs/guide.md#guide-1)\n"
            "[third](docs/guide.md#guide-1-1)\n",
        )
        self.write("docs/guide.md", "# Guide\n# Guide\n# Guide-1\n")
        self.assertEqual(check_links(self.root), [])

    def test_duplicate_heading_skips_existing_literal_numbered_slug(self) -> None:
        self.write("README.md", "[third](docs/guide.md#results-2)\n")
        self.write("docs/guide.md", "# Results\n# Results-1\n# Results\n")
        self.assertEqual(check_links(self.root), [])

    def test_repeated_collision_suffix_increments_without_reusing_slug(self) -> None:
        self.write("README.md", "[fourth](docs/guide.md#guide-1-2)\n")
        self.write("docs/guide.md", "# Guide\n# Guide\n# Guide-1\n# Guide-1\n")
        self.assertEqual(check_links(self.root), [])

    def test_nonexistent_slug_after_collision_is_still_rejected(self) -> None:
        self.write("README.md", "[wrong](docs/guide.md#guide-2)\n")
        self.write("docs/guide.md", "# Guide\n# Guide\n# Guide-1\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_reference_links_and_collapsed_links_resolve(self) -> None:
        self.write(
            "README.md",
            "[Reviewer guide][PORTFOLIO GUIDE]\n"
            "[Manual][]\n"
            "[PORTFOLIO   GUIDE]: docs/guide.md#five-minute-review\n"
            "[Manual]: <docs/guide.md>\n",
        )
        self.write("docs/guide.md", "# Five-minute review\n")
        self.assertEqual(check_links(self.root), [])

    def test_reference_to_missing_file_is_rejected(self) -> None:
        self.write("README.md", "[Guide][ref]\n[ref]: docs/missing.md\n")
        self.assertIn("missing local file", check_links(self.root)[0])

    def test_reference_to_missing_heading_is_rejected(self) -> None:
        self.write("README.md", "[Guide][ref]\n[ref]: docs/guide.md#missing\n")
        self.write("docs/guide.md", "# Present\n")
        self.assertIn("unknown Markdown heading", check_links(self.root)[0])

    def test_undefined_reference_fails_closed(self) -> None:
        self.write("README.md", "[Guide][undocumented]\n")
        self.assertIn("undefined reference", check_links(self.root)[0])

    def test_duplicate_definitions_do_not_silently_override(self) -> None:
        self.write(
            "README.md",
            "[Guide][ref]\n[Ref]: docs/guide.md\n[ref]: docs/other.md\n",
        )
        self.write("docs/guide.md", "# Guide\n")
        self.assertIn("duplicate reference", check_links(self.root)[0])

    def test_inline_code_examples_are_not_links(self) -> None:
        self.write(
            "README.md",
            "Use "+chr(96)+"[x][undefined]"+chr(96)+" or "+chr(96)+"[z](missing.md)"+chr(96)+" in documentation.\n",
        )
        self.assertEqual(check_links(self.root), [])



if __name__ == "__main__":
    unittest.main()
