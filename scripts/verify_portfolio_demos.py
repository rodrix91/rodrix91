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


_INVENTORY_REPLAY_PROBE = """
import json
import math
from inventory_policy_lab import simulate, simulate_periodic, simulate_rss

policies = (
    ("sQ", simulate, {"reorder_point": 3.0, "order_quantity": 2.0}, "reorder_point"),
    ("RS", simulate_periodic, {"order_up_to": 5.0, "review_period": 2}, "order_up_to"),
    ("RsS", simulate_rss, {"reorder_point": 3.0, "order_quantity": 2.0,
                           "review_period": 2}, "reorder_point"),
)
results = {}
for name, replay, settings, level in policies:
    valid = replay([1.0, 0.0, 2.0], lead_time=0.0, **settings)
    cases = {
        "scalar_nan": {level: math.nan},
        "dynamic_inf": {level: [3.0, 4.0, math.inf]},
    }
    if name != "RS":
        cases["quantity_nan"] = {"order_quantity": math.nan}
        cases["quantity_dynamic_inf"] = {"order_quantity": [2.0, 2.0, math.inf]}
    errors = {}
    for case, overrides in cases.items():
        try:
            replay([1.0, 0.0, 2.0], lead_time=0.0, warmup=2,
                   **{**settings, **overrides})
        except ValueError as exc:
            errors[case] = str(exc)
        else:
            errors[case] = "UNEXPECTED SUCCESS"
    results[name] = {
        "periods": valid.periods, "fill_rate": valid.fill_rate, "errors": errors
    }
print(json.dumps(results, allow_nan=False))
"""


def check_inventory_replay_levels(report: Any) -> None:
    """Require three valid replay outcomes and every documented invalid-level guard."""
    expected = {
        "sQ": {
            "scalar_nan": "reorder_point must be finite, got nan",
            "dynamic_inf": "reorder_point[2] must be finite, got inf",
            "quantity_nan": "order_quantity must be finite, got nan",
            "quantity_dynamic_inf": "order_quantity[2] must be finite, got inf",
        },
        "RS": {
            "scalar_nan": "order_up_to must be finite, got nan",
            "dynamic_inf": "order_up_to[2] must be finite, got inf",
        },
        "RsS": {
            "scalar_nan": "reorder_point must be finite, got nan",
            "dynamic_inf": "reorder_point[2] must be finite, got inf",
            "quantity_nan": "order_quantity must be finite, got nan",
            "quantity_dynamic_inf": "order_quantity[2] must be finite, got inf",
        },
    }
    if not isinstance(report, dict) or set(report) != set(expected):
        raise ValueError("inventory replay safety demo: unexpected policy set")
    for policy, required in expected.items():
        record = report[policy]
        if (
            not isinstance(record, dict)
            or record.get("periods") != 3
            or record.get("fill_rate") != 1.0
            or record.get("errors") != required
        ):
            raise ValueError(f"inventory replay safety demo: invalid {policy} outcome")


def verify_inventory_replay_levels(root: Path) -> str:
    """Exercise the immutable inventory checkout, including expected invalid inputs."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory replay safety demo: missing project source")
    result = subprocess.run(
        [sys.executable, "-c", _INVENTORY_REPLAY_PROBE],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory replay safety demo: expected exit 0, got {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory replay safety demo: invalid JSON") from exc
    check_inventory_replay_levels(report)
    return "inventory-policy-lab replay level safety: PASS (3 policies, 10 expected errors)"


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



def check_casefold_missing_marker_demo(plain: Any, folded: Any) -> None:
    """Verify an optional locale-specific missing-token flag without changing defaults."""
    if not isinstance(plain, dict) or not isinstance(folded, dict):
        raise ValueError("mixed-case missing-marker demo requires JSON objects")
    try:
        plain_columns = {column["name"]: column for column in plain["columns"]}
        folded_columns = {column["name"]: column for column in folded["columns"]}
        old_weight = plain_columns["weight_kg"]
        new_weight = folded_columns["weight_kg"]
        valid = (
            plain["rows"] == folded["rows"] == 4
            and set(plain_columns) == set(folded_columns) == {"order_id", "weight_kg", "status"}
            and old_weight["missing"] == 1
            and old_weight["type"] == "string"
            and new_weight["missing"] == 2
            and new_weight["type"] == "float"
            and "na_ignore_case" not in plain
            and folded.get("na_ignore_case") is True
        )
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("mixed-case missing-marker demo reported unexpected CSV types or gaps")


def verify_casefold_missing_marker_example(root: Path) -> str:
    """Demonstrate exact matching versus case-insensitive S/D markers in a CSV."""
    project = (root / "csv-quality-report").resolve()
    fixture = (root / "tests" / "fixtures" / "bolivia-mixed-na.csv").resolve()
    if not (project / "src").is_dir() or not fixture.is_file():
        raise FileNotFoundError("mixed-case missing-marker demo: source or fixture missing")
    common = (
        str(fixture), "--delimiter", ";", "--decimal-comma", "--na", "s/d",
        "--format", "json",
    )
    reports: list[dict[str, Any]] = []
    for extra in ((), ("--na-ignore-case",)):
        result = subprocess.run(
            [sys.executable, "-m", "csv_quality_report", *common, *extra],
            cwd=project,
            env={**os.environ, "PYTHONPATH": str(project / "src")},
            capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=120,
        )
        if result.returncode != 0:
            raise ValueError(
                "mixed-case missing-marker demo: expected exit 0; "
                f"got {result.returncode}; stderr={result.stderr[:600]!r}"
            )
        try:
            reports.append(json.loads(result.stdout))
        except json.JSONDecodeError as exc:
            raise ValueError("mixed-case missing-marker demo: invalid JSON") from exc
    check_casefold_missing_marker_demo(*reports)
    return "csv-quality-report mixed-case missing markers: PASS (default and opt-in exit 0)"


def check_canonical_missing_marker_demo(plain: Any, folded: Any) -> None:
    """Confirm NFC-equivalent missing markers are opt-in and keep defaults exact."""
    if not isinstance(plain, dict) or not isinstance(folded, dict):
        raise ValueError("canonical missing-marker demo requires JSON objects")
    try:
        baseline = plain["columns"]
        normalized = folded["columns"]
        valid = (
            plain["rows"] == folded["rows"] == 3
            and isinstance(baseline, list)
            and isinstance(normalized, list)
            and len(baseline) == len(normalized) == 1
            and baseline[0]["name"] == normalized[0]["name"] == "peso"
            and baseline[0]["type"] == "string"
            and baseline[0]["missing"] == 0
            and normalized[0]["type"] == "int"
            and normalized[0]["missing"] == 1
            and "na_ignore_case" not in plain
            and folded.get("na_ignore_case") is True
        )
    except (KeyError, TypeError, IndexError):
        valid = False
    if not valid:
        raise ValueError("canonical missing-marker demo failed its expected type/missing checks")


def verify_canonical_missing_marker_example(root: Path) -> str:
    """Exercise NFC-composed CLI marker against decomposed-accent CSV content."""
    project = (root / "csv-quality-report").resolve()
    fixture = (root / "tests" / "fixtures" / "canonical-na-marker.csv").resolve()
    if not (project / "src").is_dir() or not fixture.is_file():
        raise FileNotFoundError("canonical missing-marker demo: source or fixture missing")
    common = (str(fixture), "--na", "sin información", "--format", "json")
    reports: list[dict[str, Any]] = []
    for extra in ((), ("--na-ignore-case",)):
        result = subprocess.run(
            [sys.executable, "-m", "csv_quality_report", *common, *extra],
            cwd=project,
            env={**os.environ, "PYTHONPATH": str(project / "src")},
            capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=120,
        )
        if result.returncode != 0:
            raise ValueError(
                f"canonical missing-marker demo: expected exit 0; got {result.returncode}; "
                f"stderr={result.stderr[:600]!r}"
            )
        try:
            reports.append(json.loads(result.stdout))
        except json.JSONDecodeError as exc:
            raise ValueError("canonical missing-marker demo: invalid JSON") from exc
    check_canonical_missing_marker_demo(*reports)
    return "csv-quality-report NFC missing markers: PASS (default and opt-in exit 0)"


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
        outcomes.append(verify_casefold_missing_marker_example(root))
        outcomes.append(verify_canonical_missing_marker_example(root))
        outcomes.append(verify_inventory_replay_levels(root))
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
