"""Check three independent synthetic CLI examples documented in the portfolio."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
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


def check_canonical_unicode_gate(plain: Any, folded: Any) -> None:
    """Confirm the optional Unicode comparison flags catch hidden operational risks."""
    if not isinstance(plain, dict) or not isinstance(folded, dict):
        raise ValueError("Unicode operations smoke check requires JSON objects")
    if (
        plain["rows"] != 2
        or plain["duplicate_keys"] != 0
        or plain["distinct_groups"] != 2
        or plain["failed_duplicates"] is not False
        or plain["failed_group_share"] is not False
        or plain["failed_distinct_groups"] is not False
        or "casefold_key" in plain
        or "casefold_group" in plain
    ):
        raise ValueError("Unicode operations default unexpectedly merged distinct labels")
    if (
        folded["rows"] != 2
        or folded["duplicate_keys"] != 1
        or folded["distinct_groups"] != 1
        or folded["top_group_share"] != 1.0
        or folded["failed_duplicates"] is not True
        or folded["failed_group_share"] is not True
        or folded["failed_distinct_groups"] is not True
        or folded.get("casefold_key") is not True
        or folded.get("casefold_group") is not True
    ):
        raise ValueError("Unicode operations opt-in gates failed to detect canonical duplicates")


def verify_canonical_unicode_example(root: Path) -> str:
    """Run the opt-in NFC comparison in addition to the three base examples."""
    project = (root / "ops-field-brief").resolve()
    fixture = (root / "tests" / "fixtures" / "canonical-unicode-keys.csv").resolve()
    if not (project / "src").is_dir() or not fixture.is_file():
        raise FileNotFoundError("Unicode smoke check: missing operations code or fixture")
    common = (
        str(fixture), "--required", "order_id", "--key", "order_id",
        "--group", "buyer", "--max-duplicates", "0",
        "--max-group-share", "0.5", "--min-distinct-groups", "2", "--json",
    )
    reports: list[dict[str, Any]] = []
    for extra, expected_exit in (
        ((), 0),
        (("--casefold-key", "--casefold-group"), 1),
    ):
        result = subprocess.run(
            [sys.executable, "-m", "ops_field_brief", *common, *extra],
            cwd=project,
            env={**os.environ, "PYTHONPATH": str(project / "src")},
            capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=120,
        )
        if result.returncode != expected_exit:
            raise ValueError(
                f"Unicode operations smoke check: expected exit {expected_exit}, "
                f"got {result.returncode}; stderr={result.stderr[:600]!r}"
            )
        try:
            reports.append(json.loads(result.stdout))
        except json.JSONDecodeError as exc:
            raise ValueError("Unicode operations smoke check: invalid JSON") from exc
    check_canonical_unicode_gate(*reports)
    return (
        "ops-field-brief canonical Unicode: PASS "
        "(default exit 0, opt-in gate exit 1)"
    )


def check_baseline_rejection(
    result: subprocess.CompletedProcess[str],
    previous: str,
    after: str,
    expected_error: str = "duplicate baseline JSON key: 'rows'",
) -> None:
    """A corrupted historical JSON field must fail without a false success."""
    if (
        result.returncode != 3
        or result.stdout != ""
        or expected_error not in result.stderr
        or after != previous
    ):
        raise ValueError(
            "CSV baseline safeguard did not reject invalid JSON values "
            "while preserving the prior report"
        )


def verify_ambiguous_baseline_example(root: Path) -> str:
    """Prove the CSV baseline decoder rejects an ambiguous synthetic JSON file."""
    project = (root / "csv-quality-report").resolve()
    fixture = root / "tests" / "fixtures" / "duplicate-baseline-rows.json"
    if not (project / "src").is_dir() or not fixture.is_file():
        raise FileNotFoundError("Ambiguous baseline demo: source or fixture missing")
    previous = '{"status":"previously verified"}\n'
    with tempfile.TemporaryDirectory() as directory:
        saved = Path(directory) / "existing-report.json"
        saved.write_text(previous, encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, "-m", "csv_quality_report",
                "examples/tiny.csv", "--baseline", str(fixture.resolve()),
                "--format", "json", "--json-output", str(saved),
            ],
            cwd=project,
            env={**os.environ, "PYTHONPATH": str(project / "src")},
            capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=120,
        )
        check_baseline_rejection(result, previous, saved.read_text(encoding="utf-8"))
    return "csv-quality-report ambiguous baseline: PASS (expected input exit 3)"


def verify_nonfinite_baseline_examples(root: Path) -> str:
    """Reject nonstandard and overflowed JSON numbers without losing output."""
    project = (root / "csv-quality-report").resolve()
    cases = (
        (
            "nonstandard-baseline-nan.json",
            "non-standard baseline JSON numeric constant: NaN",
        ),
        (
            "overflow-baseline-exponent.json",
            "non-finite baseline JSON numeric value: 1e309",
        ),
    )
    if not (project / "src").is_dir():
        raise FileNotFoundError("Nonfinite baseline demo: CSV source checkout missing")
    previous = '{"status":"previously verified"}\n'
    with tempfile.TemporaryDirectory() as directory:
        saved = Path(directory) / "existing-report.json"
        for filename, expected_error in cases:
            fixture = (root / "tests" / "fixtures" / filename).resolve()
            if not fixture.is_file():
                raise FileNotFoundError(f"Nonfinite baseline demo fixture missing: {filename}")
            saved.write_text(previous, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable, "-m", "csv_quality_report",
                    "examples/tiny.csv", "--baseline", str(fixture),
                    "--format", "json", "--json-output", str(saved),
                ],
                cwd=project,
                env={**os.environ, "PYTHONPATH": str(project / "src")},
                capture_output=True, text=True, encoding="utf-8",
                check=False, timeout=120,
            )
            check_baseline_rejection(
                result, previous, saved.read_text(encoding="utf-8"), expected_error
            )
    return "csv-quality-report nonfinite baselines: PASS (2 expected input exit 3)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    options = parser.parse_args()
    try:
        root = options.root.resolve()
        outcomes = verify_examples(root)
        outcomes.append(verify_canonical_unicode_example(root))
        outcomes.append(verify_ambiguous_baseline_example(root))
        outcomes.append(verify_nonfinite_baseline_examples(root))
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as exc:
        print(f"Portfolio demo validation failed: {exc}", file=sys.stderr)
        return 1
    for outcome in outcomes:
        print(outcome)
    print("Three independent demos and all synthetic integrity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
