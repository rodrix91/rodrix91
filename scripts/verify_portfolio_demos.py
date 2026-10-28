"""Check three independent synthetic CLI examples documented in the portfolio."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXAMPLES: tuple[tuple[str, str, tuple[str, ...], int], ...] = (
    ("csv-quality-report", "csv_quality_report", ("examples/tiny.csv", "--format", "json"), 0),
    (
        "ops-field-brief",
        "ops_field_brief",
        (
            "examples/orders-incomplete-keys.csv", "--required", "order_id",
            "--max-missing", "1", "--key", "order_id,line_id",
            "--max-incomplete-keys", "1", "--json",
        ),
        1,
    ),
    (
        "inventory-policy-lab", "inventory_policy_lab",
        ("examples/demand_synthetic.csv", "--format", "json"), 0,
    ),
)


def check_report(name: str, report: Any) -> None:
    """Validate the documented contract, including the intentional failed gate."""
    if not isinstance(report, dict):
        raise ValueError(f"{name}: expected JSON object")
    if name == "csv-quality-report":
        columns = {column["name"]: column for column in report["columns"]}
        if (
            report["rows"] != 3 or report["duplicate_rows"] != 0
            or set(columns) != {"item", "qty"} or columns["qty"]["missing"] != 1
        ):
            raise ValueError("csv-quality-report: unexpected CSV profile")
    elif name == "ops-field-brief":
        if (
            report["rows"] != 5 or report["incomplete_key_rows"] != 2
            or report["duplicate_keys"] != 1 or report["failed_incomplete_keys"] is not True
        ):
            raise ValueError("ops-field-brief: intentional quality gate did not fail as expected")
    elif name == "inventory-policy-lab":
        skus = report["skus"]
        if (
            not isinstance(skus, list) or len(skus) != 12
            or len({row["sku"] for row in skus}) != 12
            or "settings" not in report
        ):
            raise ValueError("inventory-policy-lab: unexpected synthetic inventory analysis")
    else:
        raise ValueError(f"unknown project: {name}")


def verify_examples(root: Path) -> list[str]:
    """Run each source tree separately; these are not stages of one pipeline."""
    outcomes = []
    for name, module, args, expected_exit in EXAMPLES:
        project = (root / name).resolve()
        if not (project / "src").is_dir() or not (project / args[0]).is_file():
            raise FileNotFoundError(f"{name}: source tree or synthetic fixture missing")
        run = subprocess.run(
            [sys.executable, "-m", module, *args],
            cwd=project,
            env={**os.environ, "PYTHONPATH": str(project / "src")},
            capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=120,
        )
        if run.returncode != expected_exit:
            raise ValueError(
                f"{name}: expected exit {expected_exit}; got {run.returncode}; "
                f"stderr={run.stderr[:600]!r}"
            )
        try:
            report = json.loads(run.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name}: output was not valid JSON") from exc
        check_report(name, report)
        outcomes.append(f"{name}: PASS (expected exit {expected_exit})")
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    options = parser.parse_args()
    try:
        outcomes = verify_examples(options.root.resolve())
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as exc:
        print(f"Portfolio demo validation failed: {exc}", file=sys.stderr)
        return 1
    for outcome in outcomes:
        print(outcome)
    print("All three independent, synthetic CLI demonstrations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
