"""Focused regression tests for three independent portfolio CLI contracts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_portfolio_demos import (  # noqa: E402
    EXAMPLES,
    check_baseline_rejection,
    check_canonical_unicode_gate,
    check_casefold_missing_marker_demo,
    check_canonical_missing_marker_demo,
    check_inventory_replay_levels,
    check_inventory_bootstrap_demand,
    check_residual_bootstrap_finite,
    check_na_iterator_contract,
    check_ops_bounded_sniff,
    check_report,
    python_subprocess_env,
)


class PortfolioDemoContractTests(unittest.TestCase):
    def test_child_python_explicitly_overrides_legacy_encoding(self) -> None:
        """A cp1252 environment must not corrupt UTF-8-only Unicode JSON."""
        with mock.patch.dict(
            os.environ,
            {"PYTHONIOENCODING": "cp1252", "PYTHONPATH": "old", "APP_KEEP": "yes"},
        ):
            child_env = python_subprocess_env(Path("synthetic-repo"))
        self.assertEqual(child_env["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(child_env["PYTHONPATH"], str(Path("synthetic-repo") / "src"))
        self.assertEqual(child_env["APP_KEEP"], "yes")
        output = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json; print(json.dumps({'city': 'Tarija • 東京'}, ensure_ascii=False))",
            ],
            env=child_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=15,
        )
        self.assertEqual(json.loads(output.stdout), {"city": "Tarija • 東京"})

    def test_all_portfolio_probes_use_explicit_child_encoding(self) -> None:
        script = (
            Path(__file__).resolve().parents[1] / "scripts" / "verify_portfolio_demos.py"
        ).read_text(encoding="utf-8")
        self.assertEqual(script.count("env=python_subprocess_env(project),"), 11)
        self.assertNotIn('env={**os.environ, "PYTHONPATH":', script)

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


    def test_ops_strict_sniff_checks_every_delimiter_and_line_ending(self) -> None:
        cases = [
            {
                "separator": separator,
                "newline": newline,
                "rows": 3,
                "fields": ["id", "buyer"],
                "source_lines": [2, 3, 4],
                "last_value_length": 9000,
            }
            for separator in (",", ";", "\t", "|")
            for newline in ("\n", "\r\n", "\r")
        ]
        check_ops_bounded_sniff(cases)
        variants = (
            cases[:-1],
            [*cases[:-1], cases[0]],
            [*cases[:-1], {**cases[-1], "rows": 2}],
            [*cases[:-1], {**cases[-1], "last_value_length": 8999}],
            [*cases[:-1], {**cases[-1], "source_lines": [2, 4, 5]}],
            [*cases[:-1], {**cases[-1], "separator": "?"}],
            [*cases[:-1], None],
        )
        for broken in variants:
            with self.subTest(broken=broken[-1] if broken else "missing"):
                with self.assertRaisesRegex(ValueError, "ops bounded sniff demo"):
                    check_ops_bounded_sniff(broken)

    def test_na_iterator_contract_detects_missingness_and_metadata_regressions(self) -> None:
        expected = {
            "folded_parity": True,
            "folded_missing": 2,
            "folded_metadata": ["s/d"],
            "folded_key": [2, 2, 1],
            "direct_parity": True,
            "exact_parity": True,
            "exact_missing": 1,
            "exact_metadata": ["s/d"],
            "unicode_parity": True,
            "unicode_missing": 1,
            "unicode_type": "int",
            "unicode_metadata": ["sin información"],
        }
        check_na_iterator_contract(expected)
        for key, wrong in (
            ("folded_missing", 0),
            ("folded_metadata", []),
            ("folded_key", [4, 0, 1]),
            ("direct_parity", False),
            ("exact_parity", False),
            ("unicode_parity", False),
            ("unicode_missing", 0),
            ("unicode_type", "string"),
            ("unicode_metadata", []),
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "csv token iterator demo"):
                    check_na_iterator_contract({**expected, key: wrong})
        with self.assertRaisesRegex(ValueError, "csv token iterator demo"):
            check_na_iterator_contract({k: v for k, v in expected.items() if k != "folded_key"})

    def test_residual_bootstrap_probe_contract_fails_closed(self) -> None:
        errors = {
            f"period_{period}_{label}": {
                "message": f"errors[{period}][1] must be finite, got {value}",
                "rng_untouched": True,
            }
            for period in (1, 2)
            for label, value in (("nan", "nan"), ("pos_inf", "inf"), ("neg_inf", "-inf"))
        }
        report = {
            "errors": errors,
            "unused": -2.0,
            "zero": 0.0,
            "negative": -3.0,
            "priority": {
                "message": "no forecast errors over 2 period(s)",
                "rng_untouched": True,
            },
        }
        check_residual_bootstrap_finite(report)
        with self.assertRaisesRegex(ValueError, "invalid protection-interval outcome"):
            check_residual_bootstrap_finite({**report, "zero": float("nan")})
        with self.assertRaisesRegex(ValueError, "invalid protection-interval outcome"):
            check_residual_bootstrap_finite({
                **report,
                "errors": {k: v for k, v in errors.items() if k != "period_1_nan"},
            })
        with self.assertRaisesRegex(ValueError, "invalid protection-interval outcome"):
            check_residual_bootstrap_finite({
                **report,
                "priority": {**report["priority"], "rng_untouched": False},
            })
        for key in errors:
            with self.subTest(key=key):
                for replacement in (
                    {**errors[key], "message": "UNEXPECTED SUCCESS"},
                    {**errors[key], "rng_untouched": False},
                ):
                    with self.assertRaisesRegex(ValueError, "invalid " + key):
                        check_residual_bootstrap_finite({
                            **report,
                            "errors": {**errors, key: replacement},
                        })

    def test_bootstrap_guard_fails_closed_on_missing_errors_or_rng_changes(self) -> None:
        errors = {
            "negative_observation": "demand[0] must be finite and non-negative, got -1.0",
            "nan_observation_zero_interval": "demand[1] must be finite and non-negative, got nan",
            "infinite_observation": "demand[2] must be finite and non-negative, got inf",
            "negative_infinite_observation": "demand[1] must be finite and non-negative, got -inf",
            "negative_expected": "demand_per_period must be finite and non-negative, got -1.0",
            "nan_expected_zero_interval": "demand_per_period must be finite and non-negative, got nan",
            "infinite_expected": "demand_per_period must be finite and non-negative, got inf",
            "negative_infinite_expected": "demand_per_period must be finite and non-negative, got -inf",
        }
        report = {
            "valid_zero": [0.0, 0.0],
            "valid_constant": [10.0, 0.0],
            "intermittent_seeded": True,
            "errors": {
                key: {"message": message, "rng_untouched": True}
                for key, message in errors.items()
            },
        }
        check_inventory_bootstrap_demand(report)
        with self.assertRaisesRegex(ValueError, "unexpected valid or error cases"):
            check_inventory_bootstrap_demand({**report, "intermittent_seeded": False})
        with self.assertRaisesRegex(ValueError, "unexpected valid or error cases"):
            check_inventory_bootstrap_demand({
                **report, "errors": {
                    key: value for key, value in report["errors"].items()
                    if key != "nan_expected_zero_interval"
                },
            })
        for label in errors:
            with self.subTest(label=label):
                original = report["errors"][label]
                for replacement in (
                    {**original, "message": "UNEXPECTED SUCCESS"},
                    {**original, "rng_untouched": False},
                ):
                    with self.assertRaisesRegex(ValueError, "invalid " + label):
                        check_inventory_bootstrap_demand({
                            **report,
                            "errors": {**report["errors"], label: replacement},
                        })

    def test_inventory_replay_safety_demo_contract_fails_closed(self) -> None:
        report = {
            "sQ": {
                "periods": 3,
                "fill_rate": 1.0,
                "errors": {
                    "scalar_nan": "reorder_point must be finite, got nan",
                    "dynamic_inf": "reorder_point[2] must be finite, got inf",
                    "quantity_nan": "order_quantity must be finite, got nan",
                    "quantity_dynamic_inf": "order_quantity[2] must be finite, got inf",
                },
            },
            "RS": {
                "periods": 3,
                "fill_rate": 1.0,
                "errors": {
                    "scalar_nan": "order_up_to must be finite, got nan",
                    "dynamic_inf": "order_up_to[2] must be finite, got inf",
                },
            },
            "RsS": {
                "periods": 3,
                "fill_rate": 1.0,
                "errors": {
                    "scalar_nan": "reorder_point must be finite, got nan",
                    "dynamic_inf": "reorder_point[2] must be finite, got inf",
                    "quantity_nan": "order_quantity must be finite, got nan",
                    "quantity_dynamic_inf": "order_quantity[2] must be finite, got inf",
                },
            },
        }
        check_inventory_replay_levels(report)
        with self.assertRaisesRegex(ValueError, "unexpected policy set"):
            check_inventory_replay_levels({**report, "RsS": None, "extra": {}})
        for policy in report:
            with self.subTest(policy=policy):
                with self.assertRaisesRegex(ValueError, "invalid " + policy):
                    check_inventory_replay_levels({
                        **report, policy: {**report[policy], "fill_rate": 0.0}
                    })
                with self.assertRaisesRegex(ValueError, "invalid " + policy):
                    check_inventory_replay_levels({
                        **report,
                        policy: {
                            **report[policy],
                            "errors": {**report[policy]["errors"], "scalar_nan": "UNEXPECTED SUCCESS"},
                        },
                    })
                with self.assertRaisesRegex(ValueError, "invalid " + policy):
                    check_inventory_replay_levels({
                        **report,
                        policy: {
                            **report[policy],
                            "errors": {
                                k: v for k, v in report[policy]["errors"].items()
                                if k != "dynamic_inf"
                            },
                        },
                    })

    def test_inventory_safety_probe_does_not_claim_live_data(self) -> None:
        from verify_portfolio_demos import _INVENTORY_REPLAY_PROBE

        self.assertIn("simulate_periodic", _INVENTORY_REPLAY_PROBE)
        self.assertIn("simulate_rss", _INVENTORY_REPLAY_PROBE)
        self.assertIn("math.nan", _INVENTORY_REPLAY_PROBE)
        self.assertIn("math.inf", _INVENTORY_REPLAY_PROBE)
        self.assertNotIn("requests", _INVENTORY_REPLAY_PROBE)

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

    def test_casefold_na_demo_checks_expected_missingness_and_type(self) -> None:
        def report(missing: int, inferred: str, enabled: bool) -> dict:
            result = {
                "rows": 4,
                "columns": [
                    {"name": "order_id", "missing": 0, "type": "string"},
                    {"name": "weight_kg", "missing": missing, "type": inferred},
                    {"name": "status", "missing": 0, "type": "string"},
                ],
            }
            if enabled:
                result["na_ignore_case"] = True
            return result

        default = report(1, "string", False)
        casefold = report(2, "float", True)
        check_casefold_missing_marker_demo(default, casefold)
        for changed in (
            report(2, "string", False),
            report(1, "float", True),
            {**casefold, "na_ignore_case": False},
            {**default, "rows": 0},
            {**casefold, "columns": []},
        ):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, "mixed-case missing-marker demo"):
                    if "na_ignore_case" in changed:
                        check_casefold_missing_marker_demo(default, changed)
                    else:
                        check_casefold_missing_marker_demo(changed, casefold)

    def test_casefold_na_demo_fixture_has_mixed_spelling_and_decimal_commas(self) -> None:
        import csv

        root = Path(__file__).resolve().parents[1]
        path = root / "tests" / "fixtures" / "bolivia-mixed-na.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter=";"))
        self.assertEqual(len(rows), 4)
        self.assertEqual(set(rows[0]), {"order_id", "weight_kg", "status"})
        self.assertEqual([row["weight_kg"] for row in rows], ["1,50", "S/D", "s/d", "2,25"])

    def test_nfc_missing_marker_demo_checks_exact_and_opt_in_contracts(self) -> None:
        plain = {
            "rows": 3, "columns": [{"name": "peso", "type": "string", "missing": 0}],
        }
        folded = {
            "rows": 3, "na_ignore_case": True,
            "columns": [{"name": "peso", "type": "int", "missing": 1}],
        }
        check_canonical_missing_marker_demo(plain, folded)
        for changed in (
            {**folded, "na_ignore_case": False},
            {**folded, "columns": [{"name": "peso", "type": "int", "missing": 0}]},
            {**folded, "columns": [{"name": "peso", "type": "string", "missing": 1}]},
            {**folded, "rows": 4},
        ):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, "canonical missing-marker demo"):
                    check_canonical_missing_marker_demo(plain, changed)
        with self.assertRaisesRegex(ValueError, "canonical missing-marker demo"):
            check_canonical_missing_marker_demo({**plain, "na_ignore_case": True}, folded)

    def test_nfc_missing_marker_fixture_is_genuinely_decomposed(self) -> None:
        import csv
        from unicodedata import normalize

        root = Path(__file__).resolve().parents[1]
        fixture = root / "tests" / "fixtures" / "canonical-na-marker.csv"
        with fixture.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual(list(rows[0]), ["peso"])
        source = rows[1]["peso"]
        self.assertEqual(normalize("NFC", source), "SIN INFORMACIÓN")
        self.assertNotEqual(source, normalize("NFC", source))
        self.assertEqual([rows[0]["peso"], rows[2]["peso"]], ["1", "2"])

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
