"""Focused regression tests for three independent portfolio CLI contracts."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_portfolio_demos import (  # noqa: E402
    EXAMPLES,
    check_baseline_rejection,
    check_canonical_unicode_gate,
    check_report,
)


class PortfolioDemoContractTests(unittest.TestCase):
    def test_project_names_and_exit_codes(self) -> None:
        self.assertEqual(
            [(name, code) for name, _, _, code in EXAMPLES],
            [("csv-quality-report", 0), ("ops-field-brief", 1), ("inventory-policy-lab", 0)],
        )

    def test_csv_result_detects_missing_quantities(self) -> None:
        report = {
            "rows": 3, "duplicate_rows": 0,
            "columns": [{"name": "item"}, {"name": "qty", "missing": 1}],
        }
        check_report("csv-quality-report", report)
        with self.assertRaisesRegex(ValueError, "unexpected CSV"):
            check_report("csv-quality-report", {**report, "rows": 4})

    def test_operational_negative_gate_is_intentional(self) -> None:
        report = {
            "rows": 5, "incomplete_key_rows": 2, "duplicate_keys": 1,
            "failed_incomplete_keys": True,
        }
        check_report("ops-field-brief", report)
        with self.assertRaisesRegex(ValueError, "intentional quality gate"):
            check_report("ops-field-brief", {**report, "failed_incomplete_keys": False})

    def test_inventory_has_twelve_distinct_synthetic_skus(self) -> None:
        report = {"skus": [{"sku": f"SKU-{n:03d}"} for n in range(12)], "settings": {}}
        check_report("inventory-policy-lab", report)
        with self.assertRaisesRegex(ValueError, "unexpected synthetic"):
            check_report("inventory-policy-lab", {**report, "skus": [{"sku": "A"}] * 12})

    def test_malformed_and_unknown_reports_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected JSON object"):
            check_report("csv-quality-report", [])
        with self.assertRaisesRegex(ValueError, "unknown project"):
            check_report("not-a-project", {})


    def test_reviewer_guides_match_verified_bash_commands(self) -> None:
        """Copyable English and Spanish commands must match the exercised CLI args."""
        import re
        import shlex

        root = Path(__file__).resolve().parents[1]
        guides = (
            "docs/portfolio-review-guide.md",
            "docs/guia-portafolio-es.md",
            "docs/portfolio-case-study.md",
        )
        for guide in guides:
            content = (root / guide).read_text(encoding="utf-8")
            commands: list[tuple[str, ...]] = []
            blocks = re.findall(
                r"(?ms)^" + chr(96) * 3 + r"bash[ \t]*\n(.*?)^"
                + chr(96) * 3 + r"[ \t]*$", content
            )
            for block in blocks:
                # Join shell line continuations, not arbitrary prose.
                for line in block.replace(chr(92) + "\n", " ").splitlines():
                    if line.strip().startswith("PYTHONPATH=src python -m "):
                        commands.append(tuple(shlex.split(line.strip())))
            for name, module, args, _ in EXAMPLES:
                with self.subTest(guide=guide, project=name):
                    expected = ("PYTHONPATH=src", "python", "-m", module, *args)
                    self.assertIn(expected, commands)


    def test_optional_unicode_quality_gate_detects_hidden_duplicates(self) -> None:
        default = {
            "rows": 2, "duplicate_keys": 0, "distinct_groups": 2,
            "failed_duplicates": False, "failed_group_share": False,
            "failed_distinct_groups": False,
        }
        enabled = {
            "rows": 2, "duplicate_keys": 1, "distinct_groups": 1,
            "top_group_share": 1.0,
            "failed_duplicates": True, "failed_group_share": True,
            "failed_distinct_groups": True,
            "casefold_key": True, "casefold_group": True,
        }
        check_canonical_unicode_gate(default, enabled)
        with self.assertRaisesRegex(ValueError, "opt-in gates"):
            check_canonical_unicode_gate(default, {**enabled, "duplicate_keys": 0})
        with self.assertRaisesRegex(ValueError, "default unexpectedly merged"):
            check_canonical_unicode_gate({**default, "duplicate_keys": 1}, enabled)

    def test_canonical_unicode_fixture_is_a_real_two_form_sample(self) -> None:
        import csv
        from unicodedata import normalize

        root = Path(__file__).resolve().parents[1]
        fixture = root / "tests" / "fixtures" / "canonical-unicode-keys.csv"
        with fixture.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertEqual(set(rows[0]), {"order_id", "buyer"})
        for field in ("order_id", "buyer"):
            self.assertNotEqual(rows[0][field], rows[1][field])
            self.assertEqual(normalize("NFC", rows[0][field]), normalize("NFC", rows[1][field]))

    def test_duplicate_baseline_fixture_preserves_both_conflicting_values(self) -> None:
        """A duplicate-key file cannot be replaced by an ordinary JSON dump."""
        import json

        root = Path(__file__).resolve().parents[1]
        fixture = root / "tests" / "fixtures" / "duplicate-baseline-rows.json"
        text = fixture.read_text(encoding="utf-8")
        members: list[list[tuple[str, object]]] = []

        def record_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
            members.append(pairs)
            return dict(pairs)

        baseline = json.loads(text, object_pairs_hook=record_pairs)
        self.assertEqual(baseline["rows"], 0)  # What permissive JSON decoding keeps.
        self.assertEqual(
            [value for key, value in members[-1] if key == "rows"], [3, 0]
        )

    def test_ambiguous_baseline_failure_must_preserve_verified_report(self) -> None:
        import subprocess

        previous = '{"status":"verified"}\n'
        rejected = subprocess.CompletedProcess(
            args=[], returncode=3, stdout="",
            stderr="error: duplicate baseline JSON key: 'rows'",
        )
        check_baseline_rejection(rejected, previous, previous)
        with self.assertRaisesRegex(ValueError, "CSV baseline safeguard"):
            check_baseline_rejection(rejected, previous, "{}")
        with self.assertRaisesRegex(ValueError, "CSV baseline safeguard"):
            check_baseline_rejection(
                subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr=""),
                previous,
                previous,
            )

    def test_nonfinite_baseline_fixtures_contain_real_numeric_tokens(self) -> None:
        import json
        import math

        root = Path(__file__).resolve().parents[1]
        fixtures = (
            ("nonstandard-baseline-nan.json", '"limit":NaN', "nan"),
            ("overflow-baseline-exponent.json", '"limit":1e309', "inf"),
        )
        for filename, token, expected in fixtures:
            with self.subTest(filename=filename):
                source = (
                    root / "tests" / "fixtures" / filename
                ).read_text(encoding="utf-8")
                self.assertIn(token, source)
                value = json.loads(source)["metadata"]["limit"]
                self.assertTrue(math.isnan(value) if expected == "nan" else math.isinf(value))

    def test_nonfinite_baseline_negative_checks_require_specific_errors(self) -> None:
        import subprocess

        previous = '{"status":"verified"}\n'
        for marker in (
            "non-standard baseline JSON numeric constant: NaN",
            "non-finite baseline JSON numeric value: 1e309",
        ):
            with self.subTest(error=marker):
                failed = subprocess.CompletedProcess(
                    args=[], returncode=3, stdout="", stderr=f"error: {marker}"
                )
                check_baseline_rejection(failed, previous, previous, marker)
                with self.assertRaisesRegex(ValueError, "CSV baseline safeguard"):
                    check_baseline_rejection(
                        failed, previous, '{"status":"overwritten"}\n', marker
                    )
                with self.assertRaisesRegex(ValueError, "CSV baseline safeguard"):
                    check_baseline_rejection(failed, previous, previous, "wrong error")

    def test_pinned_source_commits_match_reproduction_guide(self) -> None:
        """The workflow and public reproduction table must reference the same SHAs."""
        import re

        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/portfolio-demos.yml").read_text(
            encoding="utf-8"
        )
        guide = (root / "docs/portfolio-smoke-checks.md").read_text(encoding="utf-8")
        for name, _, _, _ in EXAMPLES:
            with self.subTest(project=name):
                pattern = (
                    r"repository:[ \t]+rodrix91/" + re.escape(name)
                    + r"[ \t]*\n[ \t]*ref:[ \t]*([a-f0-9]{40})"
                )
                match = re.search(pattern, workflow)
                self.assertIsNotNone(match, f"Missing SHA-pinned checkout for {name}")
                if match is None:
                    continue
                sha = match.group(1)
                self.assertIn(
                    f"[{name}](https://github.com/rodrix91/{name}) | "+chr(96)+sha+chr(96),
                    guide,
                )


if __name__ == "__main__":
    unittest.main()
