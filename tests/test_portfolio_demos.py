"""Focused regression tests for three independent portfolio CLI contracts."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_portfolio_demos import EXAMPLES, check_report  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
