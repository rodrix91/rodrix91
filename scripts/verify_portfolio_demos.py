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


_OPS_BOUNDED_SNIFF_PROBE = """
import io
import json
from pathlib import Path
from unittest import mock
from ops_field_brief.brief import read_csv
from ops_field_brief.validation import validate_csv_structure

class BoundedReader(io.TextIOWrapper):
    def __init__(self, content):
        super().__init__(io.BytesIO(content.encode("utf-8")),
                         encoding="utf-8", newline="")
    def read(self, size=-1):
        if size < 0:
            raise AssertionError("unbounded delimiter sniff")
        return super().read(size)

cases = []
for separator in (",", ";", "\\t", "|"):
    for newline in ("\\n", "\\r\\n", "\\r"):
        source = (f"id{separator}buyer{newline}"
                  f"A1{separator}Andes{newline}"
                  f"A2{separator}Tarija{newline}"
                  f"A3{separator}" + "x" * 9000 + newline)
        with mock.patch.object(Path, "open", return_value=BoundedReader(source)):
            rows = read_csv(Path("synthetic.csv"), delimiter=None, strict=True)
        validate_csv_structure(rows)
        cases.append({
            "separator": separator,
            "newline": newline,
            "rows": len(rows),
            "fields": list(rows.fieldnames),
            "source_lines": list(rows.source_lines),
            "last_value_length": len(rows[-1]["buyer"]),
        })
print(json.dumps(cases))
"""


def check_ops_bounded_sniff(report: Any) -> None:
    """Require the pinned operations source to pass twelve bounded sniff cases."""
    expected = {(separator, newline) for separator in (",", ";", "\t", "|")
                for newline in ("\n", "\r\n", "\r")}
    if not isinstance(report, list) or len(report) != len(expected):
        raise ValueError("ops bounded sniff demo: missing or extra delimiter cases")
    seen: set[tuple[str, str]] = set()
    for record in report:
        if not isinstance(record, dict):
            raise ValueError("ops bounded sniff demo: expected a JSON record")
        pair = (record.get("separator"), record.get("newline"))
        if (
            pair not in expected
            or pair in seen
            or record.get("rows") != 3
            or record.get("fields") != ["id", "buyer"]
            or record.get("source_lines") != [2, 3, 4]
            or record.get("last_value_length") != 9000
        ):
            raise ValueError("ops bounded sniff demo: invalid delimiter result")
        seen.add(pair)


def verify_ops_bounded_sniff(root: Path) -> str:
    """Run strict CSV long-record regression against the immutable ops checkout."""
    project = (root / "ops-field-brief").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("ops bounded sniff demo: missing operations source")
    result = subprocess.run(
        [sys.executable, "-c", _OPS_BOUNDED_SNIFF_PROBE],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"ops bounded sniff demo: expected exit 0, got {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("ops bounded sniff demo: invalid JSON") from exc
    check_ops_bounded_sniff(report)
    return "ops-field-brief bounded strict sniff: PASS (12 delimiters/newlines, no unbounded read)"


_NA_ITERATOR_PROBE = """
import json
import tempfile
from pathlib import Path
from csv_quality_report.profile import build_report, profile_file, profile_rows
from csv_quality_report.reader import read_table

with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "synthetic.csv"
    source.write_text(
        "sku,qty\\nA,7\\nS/D,3\\ns/d,4\\nA,8\\n", encoding="utf-8"
    )
    settings = {"unique_keys": [("sku",)]}
    folded_ref = profile_file(
        source, na_tokens=("s/d",), na_ignore_case=True, **settings
    )
    folded_file = profile_file(
        source, na_tokens=(x for x in ["s/d"]), na_ignore_case=True, **settings
    )
    folded_memory = build_report(
        read_table(source), na_tokens=(x for x in ["s/d"]),
        na_ignore_case=True, **settings
    )
    direct = profile_rows(
        ["sku", "qty"],
        [["A", "7"], ["S/D", "3"], ["s/d", "4"], ["A", "8"]],
        na_tokens=(x for x in ["s/d"]), na_ignore_case=True, **settings
    )
    exact_ref = profile_file(source, na_tokens=("s/d",), **settings)
    exact_gen = profile_file(source, na_tokens=(x for x in ["s/d"]), **settings)
    unicode_source = Path(directory) / "unicode.csv"
    unicode_source.write_text(
        "qty\\n5\\nSIN INFORMACIO\\u0301N\\n9\\n", encoding="utf-8"
    )
    unicode_marker = "sin información"
    unicode_ref = profile_file(
        unicode_source, na_tokens=(unicode_marker,), na_ignore_case=True
    )
    unicode_gen = profile_file(
        unicode_source, na_tokens=(x for x in [unicode_marker]),
        na_ignore_case=True
    )
    result = {
        "folded_parity": folded_ref == folded_file == folded_memory,
        "folded_missing": folded_file.columns[0].missing,
        "folded_metadata": list(folded_file.na_tokens),
        "folded_key": [
            folded_file.keys[0].checked,
            folded_file.keys[0].skipped,
            folded_file.keys[0].repeated,
        ],
        "direct_parity": direct.columns == folded_ref.columns
                         and direct.keys == folded_ref.keys,
        "exact_parity": exact_ref == exact_gen,
        "exact_missing": exact_gen.columns[0].missing,
        "exact_metadata": list(exact_gen.na_tokens),
        "unicode_parity": unicode_ref == unicode_gen,
        "unicode_missing": unicode_gen.columns[0].missing,
        "unicode_type": unicode_gen.columns[0].type,
        "unicode_metadata": list(unicode_gen.na_tokens),
    }
print(json.dumps(result, ensure_ascii=False))
"""


def check_na_iterator_contract(report: Any) -> None:
    """Require generator-to-tuple parity for missing counts, keys and metadata."""
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
    if not isinstance(report, dict) or report != expected:
        raise ValueError("csv token iterator demo: unexpected missing-value profile")


def verify_na_iterator_contract(root: Path) -> str:
    """Check real pinned CSV API with one-shot token iterables and synthetic rows."""
    project = (root / "csv-quality-report").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("csv token iterator demo: missing CSV source")
    result = subprocess.run(
        [sys.executable, "-c", _NA_ITERATOR_PROBE],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"csv token iterator demo: expected exit 0, got {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("csv token iterator demo: invalid JSON") from exc
    check_na_iterator_contract(report)
    return "csv-quality-report one-shot NA iterators: PASS (stream/memory/key/NFC)"


_RESIDUAL_FINITE_PROBE = """
import json
import math
import random
from inventory_policy_lab import residual_bootstrap_quantile

errors = {}
for period in (1, 2):
    for label, invalid in (("nan", math.nan), ("pos_inf", math.inf),
                           ("neg_inf", -math.inf)):
        source = {1: (-2.0, 1.0), 2: (-4.0, 3.0)}
        source[period] = (0.0, invalid, 1.0)
        rng = random.Random(31)
        state = rng.getstate()
        key = f"period_{period}_{label}"
        try:
            residual_bootstrap_quantile(
                source, 0.95, lead_time=1.0,
                lead_times=(1.0, 2.0), samples=8, rng=rng,
            )
        except ValueError as exc:
            errors[key] = {
                "message": str(exc), "rng_untouched": rng.getstate() == state
            }
        else:
            errors[key] = {"message": "UNEXPECTED SUCCESS", "rng_untouched": False}
unused = residual_bootstrap_quantile(
    {1: (-2.0,), 3: (math.nan,)},
    0.95, lead_time=1.0, samples=6, rng=random.Random(7),
)
zero = residual_bootstrap_quantile(
    {0: (math.nan,)}, 0.95, lead_time=0.0, samples=6,
)
negative = residual_bootstrap_quantile(
    {1: (-3.0,)}, 0.95, lead_time=1.0, samples=6,
)
rng = random.Random(99)
before = rng.getstate()
try:
    residual_bootstrap_quantile(
        {1: (math.nan,)}, 0.95, lead_time=1.0,
        lead_times=(1.0, 2.0), samples=8, rng=rng,
    )
except ValueError as exc:
    priority = {"message": str(exc), "rng_untouched": rng.getstate() == before}
else:
    priority = {"message": "UNEXPECTED SUCCESS", "rng_untouched": False}
print(json.dumps({
    "errors": errors, "unused": unused, "zero": zero,
    "negative": negative, "priority": priority,
}, allow_nan=False))
"""


def check_residual_bootstrap_finite(report: Any) -> None:
    """Require six indexed rejections and normal finite residual behavior."""
    expected = {
        f"period_{period}_{label}": f"errors[{period}][1] must be finite, got {value}"
        for period in (1, 2)
        for label, value in (("nan", "nan"), ("pos_inf", "inf"), ("neg_inf", "-inf"))
    }
    if not isinstance(report, dict):
        raise ValueError("residual bootstrap finite demo: expected JSON object")
    errors = report.get("errors")
    if (
        report.get("unused") != -2.0
        or report.get("zero") != 0.0
        or report.get("negative") != -3.0
        or report.get("priority") != {
            "message": "no forecast errors over 2 period(s)",
            "rng_untouched": True,
        }
        or not isinstance(errors, dict)
        or set(errors) != set(expected)
    ):
        raise ValueError("residual bootstrap finite demo: invalid protection-interval outcome")
    for label, message in expected.items():
        if errors[label] != {"message": message, "rng_untouched": True}:
            raise ValueError(f"residual bootstrap finite demo: invalid {label} guard")


def verify_residual_bootstrap_finite(root: Path) -> str:
    """Exercise the immutable inventory source without using customer data."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("residual bootstrap finite demo: missing inventory checkout")
    result = subprocess.run(
        [sys.executable, "-c", _RESIDUAL_FINITE_PROBE],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"residual bootstrap finite demo: expected exit 0, got {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("residual bootstrap finite demo: invalid JSON") from exc
    check_residual_bootstrap_finite(report)
    return "inventory-policy-lab residual bootstrap guard: PASS (6 indexed cases)"


_BOOTSTRAP_DEMAND_PROBE = """
import json
import math
import random
from inventory_policy_lab import bootstrap_safety_stock

valid_zero = bootstrap_safety_stock([0.0, 0.0], 0.95, 0.0, 2.0, samples=8)
valid_constant = bootstrap_safety_stock([5.0], 0.95, 5.0, 2.0, samples=8)
valid_intermit_a = bootstrap_safety_stock(
    [0.0, 1.0, 4.0], 0.95, 5.0 / 3.0, 2.0, samples=20,
    rng=random.Random(4),
)
valid_intermit_b = bootstrap_safety_stock(
    [0.0, 1.0, 4.0], 0.95, 5.0 / 3.0, 2.0, samples=20,
    rng=random.Random(4),
)
cases = (
    ("negative_observation", [-1.0, 0.0, 4.0], 2.0, 1.0),
    ("nan_observation_zero_interval", [1.0, math.nan, 4.0], 2.0, 0.0),
    ("infinite_observation", [1.0, 0.0, math.inf], 2.0, 1.0),
    ("negative_infinite_observation", [1.0, -math.inf, 4.0], 2.0, 1.0),
    ("negative_expected", [1.0, 0.0, 4.0], -1.0, 1.0),
    ("nan_expected_zero_interval", [1.0, 0.0, 4.0], math.nan, 0.0),
    ("infinite_expected", [1.0, 0.0, 4.0], math.inf, 1.0),
    ("negative_infinite_expected", [1.0, 0.0, 4.0], -math.inf, 1.0),
)
errors = {}
for label, history, expected, lead in cases:
    rng = random.Random(37)
    original_state = rng.getstate()
    try:
        bootstrap_safety_stock(
            history, 0.95, expected, lead, samples=8, rng=rng
        )
    except ValueError as exc:
        errors[label] = {
            "message": str(exc), "rng_untouched": rng.getstate() == original_state
        }
    else:
        errors[label] = {"message": "UNEXPECTED SUCCESS", "rng_untouched": False}
print(json.dumps({
    "valid_zero": valid_zero,
    "valid_constant": valid_constant,
    "intermittent_seeded": valid_intermit_a == valid_intermit_b,
    "errors": errors,
}, allow_nan=False))
"""


def check_inventory_bootstrap_demand(report: Any) -> None:
    """Verify demand-bootstrap input rejection and unchanged seeded behavior."""
    expected_errors = {
        "negative_observation": "demand[0] must be finite and non-negative, got -1.0",
        "nan_observation_zero_interval": "demand[1] must be finite and non-negative, got nan",
        "infinite_observation": "demand[2] must be finite and non-negative, got inf",
        "negative_infinite_observation": "demand[1] must be finite and non-negative, got -inf",
        "negative_expected": "demand_per_period must be finite and non-negative, got -1.0",
        "nan_expected_zero_interval": "demand_per_period must be finite and non-negative, got nan",
        "infinite_expected": "demand_per_period must be finite and non-negative, got inf",
        "negative_infinite_expected": "demand_per_period must be finite and non-negative, got -inf",
    }
    if not isinstance(report, dict):
        raise ValueError("inventory bootstrap demand demo: expected a JSON object")
    errors = report.get("errors")
    if (
        report.get("valid_zero") != [0.0, 0.0]
        or report.get("valid_constant") != [10.0, 0.0]
        or report.get("intermittent_seeded") is not True
        or not isinstance(errors, dict)
        or set(errors) != set(expected_errors)
    ):
        raise ValueError("inventory bootstrap demand demo: unexpected valid or error cases")
    for label, expected in expected_errors.items():
        if errors[label] != {"message": expected, "rng_untouched": True}:
            raise ValueError(f"inventory bootstrap demand demo: invalid {label} guard")


def verify_inventory_bootstrap_demand(root: Path) -> str:
    """Verify the pinned inventory checkout rejects invalid bootstrap demand."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory bootstrap demand demo: missing project source")
    result = subprocess.run(
        [sys.executable, "-c", _BOOTSTRAP_DEMAND_PROBE],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory bootstrap demand demo: expected exit 0; got {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory bootstrap demand demo: invalid JSON") from exc
    check_inventory_bootstrap_demand(report)
    return "inventory-policy-lab bootstrap demand guard: PASS (8 errors, seeded results)"


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
        outcomes.append(verify_na_iterator_contract(root))
        outcomes.append(verify_inventory_replay_levels(root))
        outcomes.append(verify_inventory_bootstrap_demand(root))
        outcomes.append(verify_residual_bootstrap_finite(root))
        outcomes.append(verify_ops_bounded_sniff(root))
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
