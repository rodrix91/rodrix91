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


def python_subprocess_env(project: Path) -> dict[str, str]:
    """Force UTF-8 output from child interpreters on every runner OS.

    Windows console code pages may otherwise encode Unicode JSON as cp1252,
    even when the parent subprocess reader explicitly expects UTF-8.
    """
    return {
        **os.environ,
        "PYTHONPATH": str(project / "src"),
        "PYTHONIOENCODING": "utf-8",
    }


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
            env=python_subprocess_env(project),
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
        env=python_subprocess_env(project),
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


_CSV_TOP_N_PROBE = """
import json
import tempfile
from pathlib import Path
from csv_quality_report.profile import profile_rows, profile_file, build_report
from csv_quality_report.reader import read_table

with tempfile.TemporaryDirectory() as temporary:
    source = Path(temporary) / "synthetic.csv"
    source.write_text("sku,qty\\nA,1\\nB,2\\nC,3\\n", encoding="utf-8")
    table = read_table(source)
    results = {}

    def unreadable_tokens():
        raise AssertionError("invalid top_n consumed na_tokens")
        yield "NA"

    for label, n in (
        ("-1", -1), ("-7", -7), ("true", True), ("false", False),
        ("float", 1.5), ("string", "2"), ("none", None),
    ):
        for api, run in (
            ("direct", lambda: profile_rows(
                ["sku", "qty"], iter([["A", "1"], ["B", "2"]]),
                top_n=n, na_tokens=unreadable_tokens())),
            ("memory", lambda: build_report(
                table, top_n=n, na_tokens=unreadable_tokens())),
            ("stream", lambda: profile_file(
                source, top_n=n, na_tokens=unreadable_tokens())),
            ("missing", lambda: profile_file(
                Path(temporary) / "missing.csv",
                top_n=n, na_tokens=unreadable_tokens())),
        ):
            name = f"{api}_{label}"
            try:
                run()
            except ValueError as exc:
                results[name] = str(exc)
            else:
                results[name] = "UNEXPECTED SUCCESS"
    direct = profile_rows(
        ["sku", "qty"], iter([["A", "1"], ["B", "2"], ["C", "3"]]), top_n=0
    )
    memory = build_report(table, top_n=0)
    stream = profile_file(source, top_n=0)
    valid = {
        "same_reports": memory == stream,
        "rows": stream.rows,
        "distinct": stream.columns[0].distinct,
        "top_n": stream.top_n,
        "empty_examples": (
            direct.columns[0].top_values == memory.columns[0].top_values
            == stream.columns[0].top_values == []
        ),
    }
print(json.dumps({"errors": results, "valid": valid}))
"""


def check_csv_top_n_contract(report: Any) -> None:
    """Verify non-negative integer limits without hiding valid counts."""
    expected_errors = {
        f"{api}_{label}": message
        for label, message in (
            ("-1", "top_n must be 0 or greater"),
            ("-7", "top_n must be 0 or greater"),
            ("true", "top_n must be a non-negative integer"),
            ("false", "top_n must be a non-negative integer"),
            ("float", "top_n must be a non-negative integer"),
            ("string", "top_n must be a non-negative integer"),
            ("none", "top_n must be a non-negative integer"),
        )
        for api in ("direct", "memory", "stream", "missing")
    }
    expected_valid = {
        "same_reports": True,
        "rows": 3,
        "distinct": 3,
        "top_n": 0,
        "empty_examples": True,
    }
    if not isinstance(report, dict) or report != {
        "errors": expected_errors,
        "valid": expected_valid,
    }:
        raise ValueError("csv top_n Python API demo: unexpected validation or metrics")


def verify_csv_top_n_contract(root: Path) -> str:
    """Check the pinned CSV source for consistent Python API limit validation."""
    project = (root / "csv-quality-report").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("csv top_n Python API demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _CSV_TOP_N_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"csv top_n Python API demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("csv top_n Python API demo: malformed JSON") from exc
    check_csv_top_n_contract(report)
    return "csv-quality-report strict top_n guard: PASS (28 invalid cases; zero unchanged)"


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
print(json.dumps(result))  # ASCII-safe JSON across Windows code pages
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
        env=python_subprocess_env(project),
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
        env=python_subprocess_env(project),
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
        env=python_subprocess_env(project),
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
        env=python_subprocess_env(project),
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
            env=python_subprocess_env(project),
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
            env=python_subprocess_env(project),
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
            env=python_subprocess_env(project),
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
            env=python_subprocess_env(project),
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
                env=python_subprocess_env(project),
                capture_output=True, text=True, encoding="utf-8",
                check=False, timeout=120,
            )
            check_baseline_rejection(
                result, previous, saved.read_text(encoding="utf-8"), expected_error
            )
    return "csv-quality-report nonfinite baselines: PASS (2 expected input exit 3)"


_INVENTORY_MA_WINDOW_PROBE = """
import json
from inventory_policy_lab import moving_average

def attempt(window):
    try:
        # Invalid window settings must fail before checking this bad demand.
        moving_average([-1.0, 3.0], window=window)
    except ValueError as exc:
        return str(exc)
    return "UNEXPECTED SUCCESS"

bad_windows = (
    ("true", True), ("false", False), ("fraction", 1.5),
    ("string", "2"), ("none", None), ("nan", float("nan")),
    ("infinity", float("inf")),
)
errors = {name: attempt(value) for name, value in bad_windows}
nonpositive = {"zero": attempt(0), "negative": attempt(-1)}
valid = [moving_average([2.0, 4.0, 9.0], window=n) for n in (1, 2, 8)]
print(json.dumps({"errors": errors, "nonpositive": nonpositive, "valid": valid}))
"""


def check_inventory_ma_window_contract(report: Any) -> None:
    """Verify that only positive integer moving-average windows are accepted."""
    expected_errors = {
        "true": "moving-average window must be a positive integer, got True",
        "false": "moving-average window must be a positive integer, got False",
        "fraction": "moving-average window must be a positive integer, got 1.5",
        "string": "moving-average window must be a positive integer, got '2'",
        "none": "moving-average window must be a positive integer, got None",
        "nan": "moving-average window must be a positive integer, got nan",
        "infinity": "moving-average window must be a positive integer, got inf",
    }
    expected_nonpositive = {
        "zero": "moving-average window must be at least 1, got 0",
        "negative": "moving-average window must be at least 1, got -1",
    }
    if not isinstance(report, dict) or report != {
        "errors": expected_errors,
        "nonpositive": expected_nonpositive,
        "valid": [9.0, 6.5, 5.0],
    }:
        raise ValueError("inventory moving-average window demo: invalid API contract")


def verify_inventory_ma_window_contract(root: Path) -> str:
    """Exercise a pinned inventory forecasting API with only synthetic values."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory moving-average window demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _INVENTORY_MA_WINDOW_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory moving-average window demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory moving-average window demo: malformed JSON") from exc
    check_inventory_ma_window_contract(report)
    return "inventory-policy-lab moving-average windows: PASS (9 rejected, 3 valid)"


_OPS_TOP_N_PROBE = """
import json
from ops_field_brief.brief import build_brief

rows = [
    {"shipment": "S1", "buyer": "Andes"},
    {"shipment": "S2", "buyer": "Paz"},
    {"shipment": "S3", "buyer": "Andes"},
]
invalid = (
    ("true", True), ("false", False), ("fraction", 1.5),
    ("string", "2"), ("none", None), ("nan", float("nan")),
    ("infinity", float("inf")), ("minus_infinity", -float("inf")),
)
errors = {}
for label, value in invalid:
    for group in (None, "buyer"):
        key = label + ("_group" if group else "_no_group")
        try:
            build_brief(rows, ["shipment", "buyer"], group=group, top_n=value)
        except ValueError as exc:
            errors[key] = str(exc)
        else:
            errors[key] = "UNEXPECTED SUCCESS"
try:
    build_brief(rows, ["shipment", "buyer"], group="buyer", top_n=-1)
except ValueError as exc:
    negative = str(exc)
else:
    negative = "UNEXPECTED SUCCESS"
zero = build_brief(rows, ["shipment", "buyer"], group="buyer", top_n=0)
one = build_brief(rows, ["shipment", "buyer"], group="buyer", top_n=1)
print(json.dumps({
    "errors": errors, "negative": negative,
    "zero": {
        "rows": zero.rows, "top": zero.top,
        "top_group_share": zero.top_group_share,
        "failed_fields": zero.failed_fields,
    },
    "one": {"top": one.top, "rows": one.rows},
}))
"""


def check_ops_top_n_contract(report: Any) -> None:
    """Fail on accidental boolean limits, invalid types or altered valid counts."""
    labels = (
        "true", "false", "fraction", "string", "none", "nan",
        "infinity", "minus_infinity",
    )
    expected = {
        f"{label}_{suffix}": "top must be a non-negative integer"
        for label in labels
        for suffix in ("no_group", "group")
    }
    if not isinstance(report, dict) or report != {
        "errors": expected,
        "negative": "top must be 0 or greater",
        "zero": {
            "rows": 3, "top": [], "top_group_share": 2 / 3, "failed_fields": [],
        },
        "one": {"top": [["Andes", 2]], "rows": 3},
    }:
        raise ValueError("ops-field-brief top-N demo: invalid group limit contract")


def verify_ops_top_n_contract(root: Path) -> str:
    """Exercise the pinned operational report API with only synthetic rows."""
    project = (root / "ops-field-brief").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("ops-field-brief top-N demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _OPS_TOP_N_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"ops-field-brief top-N demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("ops-field-brief top-N demo: malformed JSON") from exc
    check_ops_top_n_contract(payload)
    return "ops-field-brief top-N limit: PASS (16 invalid calls, 2 valid rankings)"


_INVENTORY_HOLDOUT_PROBE = """
import json
from inventory_policy_lab import backtest, naive

def guarded_model(history):
    calls.append(len(history))
    return 2.0

invalid = (
    ("true", True), ("false", False), ("one_float", 1.0),
    ("fraction", 1.5), ("string", "2"), ("none", None),
    ("nan", float("nan")), ("infinity", float("inf")),
    ("minus_infinity", -float("inf")),
)
calls = []
errors = {}
for label, value in invalid:
    try:
        backtest([-1.0, float("nan"), 3.0, 4.0], "custom", guarded_model, holdout=value)
    except ValueError as exc:
        errors[label] = str(exc)
    else:
        errors[label] = "UNEXPECTED SUCCESS"
nonpositive = {}
for label, value in (("zero", 0), ("negative", -1), ("too_large", 3)):
    try:
        backtest([1.0, 2.0, 3.0, 4.0], "naive", naive, holdout=value)
    except ValueError as exc:
        nonpositive[label] = str(exc)
    else:
        nonpositive[label] = "UNEXPECTED SUCCESS"
valid = backtest([10.0, 12.0, 8.0, 10.0, 14.0, 6.0, 10.0, 14.0], "naive", naive, holdout=2)
print(json.dumps({
    "errors": errors,
    "nonpositive": nonpositive,
    "calls": calls,
    "valid": {
        "forecasts": valid.forecasts, "mae": valid.mae,
        "rmse": valid.rmse, "bias": valid.bias, "mase": valid.mase,
    },
}))
"""


def check_inventory_holdout_contract(report: Any) -> None:
    """Validate early rejection and unchanged rolling-origin score contract."""
    expected = {
        "errors": {
            label: "backtest holdout must be a positive integer"
            for label in (
                "true", "false", "one_float", "fraction", "string", "none",
                "nan", "infinity", "minus_infinity",
            )
        },
        "nonpositive": {
            label: "backtest needs holdout >= 1 and at least 2 training periods"
            for label in ("zero", "negative", "too_large")
        },
        "calls": [],
        "valid": {
            "forecasts": [6.0, 10.0], "mae": 4.0,
            "rmse": 4.0, "bias": -4.0, "mase": 1.0,
        },
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("inventory backtest holdout demo: invalid holdout API contract")


def verify_inventory_holdout_contract(root: Path) -> str:
    """Check the exact pinned public backtest API using synthetic observations."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory backtest holdout demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _INVENTORY_HOLDOUT_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory backtest holdout demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory backtest holdout demo: malformed JSON") from exc
    check_inventory_holdout_contract(payload)
    return "inventory-policy-lab backtest holdout: PASS (12 expected errors, unchanged metrics)"


_INVENTORY_CUSTOM_FORECAST_PROBE = """
import json
from inventory_policy_lab import backtest, naive

bad_values = (
    ("true", True), ("false", False), ("numeric_string", "2"),
    ("none", None), ("complex", 1 + 2j), ("object", object()),
    ("huge_integer", 10**400),
)
errors = {}
for index in (3, 4):
    for label, invalid in bad_values:
        def model(history, bad=invalid, bad_index=index):
            return bad if len(history) == bad_index else 2.0
        try:
            backtest([3.0, 4.0, 5.0, 6.0, 7.0], "custom", model, holdout=2)
        except ValueError as exc:
            errors[f"{label}_{index}"] = str(exc)
        else:
            errors[f"{label}_{index}"] = "UNEXPECTED SUCCESS"
valid = backtest(
    [10.0, 12.0, 8.0, 10.0, 14.0, 6.0, 10.0, 14.0],
    "naive", naive, holdout=2,
)
zero = backtest([0.0, 0.0, 0.0, 0.0], "zero", lambda _: 0.0, holdout=1)
print(json.dumps({
    "errors": errors,
    "valid": {
        "forecasts": valid.forecasts, "mae": valid.mae,
        "rmse": valid.rmse, "bias": valid.bias, "mase": valid.mase,
    },
    "zero": {"forecasts": zero.forecasts, "mae": zero.mae, "mase": zero.mase},
}))
"""


def check_inventory_custom_forecast_contract(report: Any) -> None:
    """Reject invalid custom model types without changing valid backtests."""
    expected_errors = {
        f"{label}_{period}": f"custom forecast[{period}] must be finite and non-negative"
        for period in (3, 4)
        for label in (
            "true", "false", "numeric_string", "none",
            "complex", "object", "huge_integer",
        )
    }
    if not isinstance(report, dict) or report != {
        "errors": expected_errors,
        "valid": {
            "forecasts": [6.0, 10.0],
            "mae": 4.0, "rmse": 4.0, "bias": -4.0, "mase": 1.0,
        },
        "zero": {"forecasts": [0.0], "mae": 0.0, "mase": None},
    }:
        raise ValueError("inventory custom forecast demo: invalid model output contract")


def verify_inventory_custom_forecast_contract(root: Path) -> str:
    """Exercise pinned forecasting source with synthetic malformed model outputs."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory custom forecast demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _INVENTORY_CUSTOM_FORECAST_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory custom forecast demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory custom forecast demo: malformed JSON") from exc
    check_inventory_custom_forecast_contract(payload)
    return "inventory-policy-lab custom forecasts: PASS (14 invalid, 2 valid)"


_INVENTORY_ALPHA_PROBE = """
import json
from inventory_policy_lab import ses, croston, sba

invalid = (
    ("true", True),
    ("false", False),
    ("text", "0.5"),
    ("none", None),
    ("complex", 1 + 2j),
    ("list", [0.5]),
    ("dict", {"alpha": 0.5}),
    ("tuple", (0.5,)),
)
methods = (("ses", ses), ("croston", croston), ("sba", sba))
errors = {}
for method_name, method in methods:
    for label, value in invalid:
        try:
            method([-1.0, float("nan")], alpha=value)
        except ValueError as exc:
            errors[f"{method_name}:{label}"] = str(exc)
        else:
            errors[f"{method_name}:{label}"] = "UNEXPECTED SUCCESS"
valid = {
    "ses_integer": ses([2.0, 8.0, 4.0], alpha=1),
    "ses_half": ses([2.0, 8.0, 4.0], alpha=0.5),
    "croston_integer": croston([0.0, 0.0, 8.0, 0.0], alpha=1),
    "sba_integer": sba([0.0, 0.0, 8.0, 0.0], alpha=1),
}
print(json.dumps({"errors": errors, "valid": valid}))
"""


def check_inventory_alpha_contract(report: Any) -> None:
    """Validate numeric alpha boundaries and fail-closed input rejection."""
    invalid = (
        ("true", "True"), ("false", "False"), ("text", "0.5"),
        ("none", "None"), ("complex", "(1+2j)"), ("list", "[0.5]"),
        ("dict", "{'alpha': 0.5}"), ("tuple", "(0.5,)"),
    )
    expected_errors = {
        f"{method}:{label}": (
            f"{'ses' if method == 'ses' else 'croston'} "
            f"alpha must be in (0, 1], got {shown}"
        )
        for method in ("ses", "croston", "sba")
        for label, shown in invalid
    }
    expected = {
        "errors": expected_errors,
        "valid": {
            "ses_integer": 4.0,
            "ses_half": 4.5,
            "croston_integer": 8 / 3,
            "sba_integer": 4 / 3,
        },
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("inventory smoothing alpha demo: invalid API contract")


def verify_inventory_alpha_contract(root: Path) -> str:
    """Exercise pinned source against synthetic alpha values on every runner."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory smoothing alpha demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _INVENTORY_ALPHA_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory smoothing alpha demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory smoothing alpha demo: malformed JSON") from exc
    check_inventory_alpha_contract(payload)
    return "inventory-policy-lab smoothing alpha: PASS (24 invalid, 4 valid)"


_CSV_SKIP_COUNT_PROBE = """
import json
import tempfile
from pathlib import Path
from csv_quality_report.reader import open_rows, read_table
from csv_quality_report.profile import profile_file

invalid = (
    ("true", True), ("false", False), ("integral_float", 1.0),
    ("fraction", 1.5), ("text", "1"), ("none", None),
    ("nan", float("nan")), ("infinity", float("inf")),
    ("minus_infinity", -float("inf")),
)
apis = ("stream", "table", "profile")
options = ("skip_lines", "skip_footer")

def call(api, path, kwargs):
    if api == "stream":
        with open_rows(path, **kwargs):
            pass
    elif api == "table":
        read_table(path, **kwargs)
    else:
        profile_file(path, **kwargs)

errors = {}
negative = {}
for api in apis:
    for option in options:
        for label, value in invalid:
            key = f"{api}:{option}:{label}"
            try:
                call(api, "missing-synthetic-input.csv", {option: value})
            except ValueError as exc:
                errors[key] = str(exc)
            except Exception as exc:
                errors[key] = f"UNEXPECTED {type(exc).__name__}"
            else:
                errors[key] = "UNEXPECTED SUCCESS"
        key = f"{api}:{option}"
        try:
            call(api, "missing-synthetic-input.csv", {option: -1})
        except ValueError as exc:
            negative[key] = str(exc)
        except Exception as exc:
            negative[key] = f"UNEXPECTED {type(exc).__name__}"
        else:
            negative[key] = "UNEXPECTED SUCCESS"

with tempfile.TemporaryDirectory() as dirname:
    path = Path(dirname) / "export.csv"
    path.write_text("Title\\nid,buyer\\nS1,Andes\\nS2,Paz\\nTotal\\n", encoding="utf-8")
    with open_rows(path, skip_lines=1, skip_footer=1) as stream:
        streaming = list(stream)
    table = read_table(path, skip_lines=1, skip_footer=1)
    report = profile_file(path, skip_lines=1, skip_footer=1)
    valid = {
        "stream": streaming, "table": table.rows,
        "profile_rows": report.rows,
        "profile_skipped_lines": report.skipped_lines,
        "profile_skipped_footer": report.skipped_footer,
    }
print(json.dumps({"errors": errors, "negative": negative, "valid": valid}))
"""


def check_csv_skip_count_contract(report: Any) -> None:
    """Fail closed on bad CSV skip-count types and altered valid rows."""
    errors = {
        f"{api}:{option}:{label}": f"{option} must be a non-negative integer"
        for api in ("stream", "table", "profile")
        for option in ("skip_lines", "skip_footer")
        for label in (
            "true", "false", "integral_float", "fraction", "text",
            "none", "nan", "infinity", "minus_infinity",
        )
    }
    negative = {
        f"{api}:{option}": f"{option} must be >= 0, got -1"
        for api in ("stream", "table", "profile")
        for option in ("skip_lines", "skip_footer")
    }
    expected = {
        "errors": errors,
        "negative": negative,
        "valid": {
            "stream": [["S1", "Andes"], ["S2", "Paz"]],
            "table": [["S1", "Andes"], ["S2", "Paz"]],
            "profile_rows": 2,
            "profile_skipped_lines": 1,
            "profile_skipped_footer": 1,
        },
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("csv skip-count demo: invalid public API contract")


def verify_csv_skip_count_contract(root: Path) -> str:
    """Exercise the exact pinned CSV reader with synthetic title/footer data."""
    project = (root / "csv-quality-report").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("csv skip-count demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _CSV_SKIP_COUNT_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"csv skip-count demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("csv skip-count demo: malformed JSON") from exc
    check_csv_skip_count_contract(payload)
    return "csv-quality-report skip counts: PASS (54 invalid, 6 negative, valid rows)"


_CSV_MAX_ROWS_PROBE = """
import json
import tempfile
from pathlib import Path
from csv_quality_report.reader import open_rows, read_table
from csv_quality_report.profile import profile_file

def read_with(api, path, max_rows):
    if api == "stream":
        with open_rows(path, max_rows=max_rows) as stream:
            rows = list(stream)
            return len(rows), stream.truncated
    if api == "table":
        data = read_table(path, max_rows=max_rows)
        return len(data.rows), data.truncated
    result = profile_file(path, max_rows=max_rows)
    return result.rows, result.truncated

invalid = (
    ("true", True), ("false", False), ("float", 1.0),
    ("fraction", 1.5), ("text", "1"), ("nan", float("nan")),
    ("infinity", float("inf")), ("minus_infinity", -float("inf")),
    ("object", object()),
)
errors = {}
negative = {}
for api in ("stream", "table", "profile"):
    for label, value in invalid:
        try:
            read_with(api, "missing-synthetic-input.csv", value)
        except ValueError as exc:
            errors[f"{api}:{label}"] = str(exc)
        except Exception as exc:
            errors[f"{api}:{label}"] = f"UNEXPECTED {type(exc).__name__}"
        else:
            errors[f"{api}:{label}"] = "UNEXPECTED SUCCESS"
    try:
        read_with(api, "missing-synthetic-input.csv", -1)
    except ValueError as exc:
        negative[api] = str(exc)
    except Exception as exc:
        negative[api] = f"UNEXPECTED {type(exc).__name__}"
    else:
        negative[api] = "UNEXPECTED SUCCESS"

with tempfile.TemporaryDirectory() as dirname:
    path = Path(dirname) / "records.csv"
    path.write_text(
        chr(10).join(("id,buyer", "S1,Andes", "S2,Paz", "")),
        encoding="utf-8",
    )
    valid = {}
    for api in ("stream", "table", "profile"):
        for label, value in (("unlimited", None), ("zero", 0), ("one", 1)):
            valid[f"{api}:{label}"] = read_with(api, path, value)
print(json.dumps({"errors": errors, "negative": negative, "valid": valid}))
"""


def check_csv_max_rows_contract(report: Any) -> None:
    """Require early typed limits and unchanged CSV truncation semantics."""
    expected = {
        "errors": {
            f"{api}:{label}": "max_rows must be a non-negative integer or None"
            for api in ("stream", "table", "profile")
            for label in (
                "true", "false", "float", "fraction", "text", "nan",
                "infinity", "minus_infinity", "object",
            )
        },
        "negative": {
            api: "max_rows must be >= 0, got -1"
            for api in ("stream", "table", "profile")
        },
        "valid": {
            f"{api}:{label}": value
            for api in ("stream", "table", "profile")
            for label, value in (
                ("unlimited", [2, False]),
                ("zero", [0, True]),
                ("one", [1, True]),
            )
        },
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("csv max-rows demo: invalid public API contract")


def verify_csv_max_rows_contract(root: Path) -> str:
    """Exercise pinned public CSV APIs using only synthetic demand rows."""
    project = (root / "csv-quality-report").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("csv max-rows demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _CSV_MAX_ROWS_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"csv max-rows demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("csv max-rows demo: malformed JSON") from exc
    check_csv_max_rows_contract(payload)
    return "csv-quality-report max-rows: PASS (27 invalid, 3 negative, 9 valid)"


_OPS_EXCEL_CASE_PROBE = """
import gzip
import io
import json
import tempfile
from pathlib import Path

from ops_field_brief.brief import _excel_sep_directive, build_brief, read_csv
from ops_field_brief.validation import validate_csv_structure

results = {}
for spelling in ("SEP=", "Sep=", "sEp="):
    text = chr(10).join((
        spelling + ";",
        "order_id;buyer",
        "A1;Andes",
        "A2;Paz",
        "",
    ))
    with tempfile.TemporaryDirectory() as dirname:
        for source in ("stdin", "file", "gzip"):
            path = Path(dirname) / ("orders.csv.gz" if source == "gzip" else "orders.csv")
            if source != "stdin":
                raw = text.encode("utf-8-sig")
                path.write_bytes(gzip.compress(raw) if source == "gzip" else raw)
            rows = (
                read_csv(
                    Path("-"), delimiter=None, strict=True,
                    stdin=io.StringIO(chr(0xfeff) + text),
                )
                if source == "stdin"
                else read_csv(path, delimiter=None, strict=True)
            )
            validate_csv_structure(rows)
            brief = build_brief(
                rows, ["order_id", "buyer"], key="order_id",
                group="buyer", max_duplicates=0,
            )
            results[f"{spelling}:{source}"] = {
                "header": list(rows.fieldnames),
                "lines": list(rows.source_lines),
                "rows": brief.rows,
                "duplicates": brief.duplicate_keys,
                "top": [list(item) for item in brief.top],
            }
explicit = read_csv(
    Path("-"), delimiter=";",
    stdin=io.StringIO(chr(10).join(("SEP=;", "order_id;buyer", "A1;Andes", ""))),
)
lookalikes = [
    _excel_sep_directive(text) is None
    for text in (
        "SEP=;extra" + chr(10) + "order_id;buyer",
        "sép=;" + chr(10) + "order_id;buyer",
        "SEP=:" + chr(10) + "order_id:buyer",
    )
]
print(json.dumps({
    "results": results,
    "explicit_header": list(explicit.fieldnames),
    "lookalikes": lookalikes,
}))
"""


def check_ops_excel_case_contract(report: Any) -> None:
    """Confirm declared Excel separators work only in exact auto mode."""
    rows = {
        "header": ["order_id", "buyer"],
        "lines": [3, 4],
        "rows": 2,
        "duplicates": 0,
        "top": [["Andes", 1], ["Paz", 1]],
    }
    expected = {
        "results": {
            f"{spelling}:{source}": rows
            for spelling in ("SEP=", "Sep=", "sEp=")
            for source in ("stdin", "file", "gzip")
        },
        "explicit_header": ["SEP=", ""],
        "lookalikes": [True, True, True],
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("ops Excel sep-case demo: invalid directive contract")


def verify_ops_excel_case_contract(root: Path) -> str:
    """Run mixed-case Excel directive probes against pinned ops source."""
    project = (root / "ops-field-brief").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("ops Excel sep-case demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _OPS_EXCEL_CASE_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"ops Excel sep-case demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("ops Excel sep-case demo: malformed JSON") from exc
    check_ops_excel_case_contract(payload)
    return "ops-field-brief Excel sep case: PASS (9 sources, exact-only detection)"


_INVENTORY_WARMUP_PROBE = """
import json
from inventory_policy_lab import simulate, simulate_periodic, simulate_rss

methods = (
    ("sq", simulate, {"reorder_point": 3.0, "order_quantity": 2.0}),
    ("rs", simulate_periodic, {"order_up_to": 5.0, "review_period": 2}),
    ("rss", simulate_rss, {
        "reorder_point": 3.0, "order_quantity": 2.0, "review_period": 2,
    }),
)
bad = (
    ("true", True), ("false", False), ("float", 1.0),
    ("fraction", 1.5), ("text", "1"), ("none", None),
    ("nan", float("nan")), ("infinity", float("inf")),
    ("minus_infinity", -float("inf")), ("object", object()),
)
errors = {}
bounds = {}
valid = {}
for name, method, settings in methods:
    for label, warmup in bad:
        try:
            method([-1.0, 2.0, 3.0], warmup=warmup, lead_time=0.0, **settings)
        except ValueError as exc:
            errors[f"{name}:{label}"] = str(exc)
        except Exception as exc:
            errors[f"{name}:{label}"] = f"UNEXPECTED {type(exc).__name__}"
        else:
            errors[f"{name}:{label}"] = "UNEXPECTED SUCCESS"
    for label, warmup in (("negative", -1), ("too_many", 4)):
        try:
            method([-1.0, 2.0, 3.0], warmup=warmup, lead_time=0.0, **settings)
        except ValueError as exc:
            bounds[f"{name}:{label}"] = str(exc)
        except Exception as exc:
            bounds[f"{name}:{label}"] = f"UNEXPECTED {type(exc).__name__}"
        else:
            bounds[f"{name}:{label}"] = "UNEXPECTED SUCCESS"
    for label, warmup in (("all_scored", 0), ("one_skipped", 1), ("all_skipped", 3)):
        result = method([1.0, 2.0, 3.0], warmup=warmup, lead_time=0.0, **settings)
        valid[f"{name}:{label}"] = [
            result.periods, result.total_demand, result.fill_rate is None,
        ]
print(json.dumps({"errors": errors, "bounds": bounds, "valid": valid}))
"""


def check_inventory_warmup_contract(report: Any) -> None:
    """Fail closed on invalid warmups and inaccurate replay scoring windows."""
    expected = {
        "errors": {
            f"{name}:{label}": "warmup must be an integer number of periods"
            for name in ("sq", "rs", "rss")
            for label in (
                "true", "false", "float", "fraction", "text",
                "none", "nan", "infinity", "minus_infinity", "object",
            )
        },
        "bounds": {
            f"{name}:{label}": "warmup must be between 0 and the number of periods"
            for name in ("sq", "rs", "rss")
            for label in ("negative", "too_many")
        },
        "valid": {
            f"{name}:{label}": result
            for name in ("sq", "rs", "rss")
            for label, result in (
                ("all_scored", [3, 6.0, False]),
                ("one_skipped", [2, 5.0, False]),
                ("all_skipped", [0, 0.0, True]),
            )
        },
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("inventory warmup demo: invalid scored-period contract")


def verify_inventory_warmup_contract(root: Path) -> str:
    """Exercise replay warmups in the exact pinned inventory source."""
    project = (root / "inventory-policy-lab").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("inventory warmup demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _INVENTORY_WARMUP_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"inventory warmup demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("inventory warmup demo: malformed JSON") from exc
    check_inventory_warmup_contract(payload)
    return "inventory-policy-lab warmup: PASS (30 invalid, 6 bounds, 9 valid)"


_CSV_FIELD_LIMIT_PROBE = """
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from csv_quality_report.profile import profile_file
from csv_quality_report.reader import open_rows, read_table

def read_with(api, path, size):
    if api == "stream":
        with open_rows(path, max_field_size=size) as stream:
            return len(list(stream))
    if api == "table":
        return len(read_table(path, max_field_size=size).rows)
    return profile_file(path, max_field_size=size).rows

bad = (
    ("true", True), ("false", False), ("float", 1.0),
    ("fraction", 1.5), ("text", "2"), ("nan", float("nan")),
    ("infinity", float("inf")), ("minus_infinity", -float("inf")),
    ("object", object()), ("zero", 0), ("negative", -1),
    ("too_large", sys.maxsize + 1), ("huge", 10**400),
)
errors = {}
restored = {}
before = csv.field_size_limit()
for api in ("stream", "table", "profile"):
    for label, value in bad:
        key = f"{api}:{label}"
        try:
            read_with(api, "missing-synthetic-file.csv", value)
        except ValueError as exc:
            errors[key] = str(exc)
        except Exception as exc:
            errors[key] = f"UNEXPECTED {type(exc).__name__}"
        else:
            errors[key] = "UNEXPECTED SUCCESS"
        restored[key] = csv.field_size_limit() == before

with tempfile.TemporaryDirectory() as dirname:
    file = Path(dirname) / "records.csv"
    file.write_text(
        chr(10).join(("id,region", "A1,Tarija", "A2,Jujuy", "")),
        encoding="utf-8",
    )
    valid = {}
    for api in ("stream", "table", "profile"):
        for label, limit in (("default", None), ("explicit", 128)):
            key = f"{api}:{label}"
            valid[key] = read_with(api, file, limit)
            restored[key] = csv.field_size_limit() == before

    cmd = subprocess.run(
        [sys.executable, "-m", "csv_quality_report", str(file),
         "--max-field-size", str(sys.maxsize + 1)],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    cli = [cmd.returncode, f"must be <= {sys.maxsize}" in cmd.stderr]

print(json.dumps({"errors": errors, "restored": restored, "valid": valid, "cli": cli}))
"""


def check_csv_field_limit_contract(report: Any) -> None:
    """Reject invalid parser limits without changing process-global CSV state."""
    errors = {}
    for api in ("stream", "table", "profile"):
        for label in (
            "true", "false", "float", "fraction", "text",
            "nan", "infinity", "minus_infinity", "object",
        ):
            errors[f"{api}:{label}"] = "max_field_size must be a positive integer"
        for label in ("zero", "negative", "too_large", "huge"):
            errors[f"{api}:{label}"] = (
                f"max_field_size must be between 1 and {sys.maxsize}"
            )
    expected = {
        "errors": errors,
        "restored": {
            **{key: True for key in errors},
            **{
                f"{api}:{label}": True
                for api in ("stream", "table", "profile")
                for label in ("default", "explicit")
            },
        },
        "valid": {
            f"{api}:{label}": 2
            for api in ("stream", "table", "profile")
            for label in ("default", "explicit")
        },
        "cli": [2, True],
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("csv field-size demo: invalid parser-state contract")


def verify_csv_field_limit_contract(root: Path) -> str:
    """Verify pinned source's parser-state protection using synthetic CSV."""
    project = (root / "csv-quality-report").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("csv field-size demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _CSV_FIELD_LIMIT_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"csv field-size demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("csv field-size demo: malformed JSON") from exc
    check_csv_field_limit_contract(payload)
    return "csv-quality-report field size: PASS (39 invalid, 6 valid, state restored, CLI)"


_OPS_QUOTED_EXCEL_PROBE = """
import gzip
import io
import json
import tempfile
from pathlib import Path

from ops_field_brief.brief import _excel_sep_directive, read_csv
from ops_field_brief.validation import validate_csv_structure

results = {}
quote = chr(34)
bom = chr(0xfeff)
with tempfile.TemporaryDirectory() as dirname:
    for label, delimiter in (
        ("semicolon", ";"), ("comma", ","), ("pipe", "|"), ("tab", chr(9))
    ):
        for spelling in ("sep=", "SEP=", "SeP="):
            first = quote + spelling + delimiter + quote
            content = chr(10).join((
                first, "order_id" + delimiter + "buyer",
                "A1" + delimiter + "Andes",
                "A2" + delimiter + "Paz", "",
            ))
            for source in ("stdin", "plain", "gzip"):
                path = Path(dirname) / (
                    "orders.csv.gz" if source == "gzip" else "orders.csv"
                )
                if source != "stdin":
                    payload = content.encode("utf-8-sig")
                    path.write_bytes(
                        gzip.compress(payload) if source == "gzip" else payload
                    )
                rows = (
                    read_csv(
                        Path("-"), delimiter=None, strict=True,
                        stdin=io.StringIO(bom + content),
                    )
                    if source == "stdin"
                    else read_csv(path, delimiter=None, strict=True)
                )
                validate_csv_structure(rows)
                results[f"{label}:{spelling}:{source}"] = {
                    "header": list(rows.fieldnames),
                    "lines": list(rows.source_lines),
                    "buyers": [row["buyer"] for row in rows],
                }

explicit = read_csv(
    Path("-"), delimiter=";", strict=True,
    stdin=io.StringIO(quote + "sep=;" + quote + chr(10) + "order_id;buyer" + chr(10)),
)
lookalikes = [
    _excel_sep_directive(item) is None
    for item in (
        quote + "sep=;;" + quote + chr(10) + "order_id;buyer",
        quote + "sep=;x" + chr(10) + "order_id;buyer",
        "sep=;" + quote + chr(10) + "order_id;buyer",
        quote + "sep=x" + quote + chr(10) + "order_id;buyer",
    )
]
print(json.dumps({
    "results": results,
    "explicit_header": list(explicit.fieldnames),
    "lookalikes": lookalikes,
}))
"""


def check_ops_quoted_excel_contract(report: Any) -> None:
    """Verify exact quoted separator declarations without swallowing CSV headers."""
    result = {
        "header": ["order_id", "buyer"],
        "lines": [3, 4],
        "buyers": ["Andes", "Paz"],
    }
    expected = {
        "results": {
            f"{label}:{spelling}:{source}": result
            for label in ("semicolon", "comma", "pipe", "tab")
            for spelling in ("sep=", "SEP=", "SeP=")
            for source in ("stdin", "plain", "gzip")
        },
        "explicit_header": ["sep=;"],
        "lookalikes": [True, True, True, True],
    }
    if not isinstance(report, dict) or report != expected:
        raise ValueError("ops quoted Excel demo: invalid separator contract")


def verify_ops_quoted_excel_contract(root: Path) -> str:
    """Execute synthetic quoted Excel CSVs against pinned ops source."""
    project = (root / "ops-field-brief").resolve()
    if not (project / "src").is_dir():
        raise FileNotFoundError("ops quoted Excel demo: missing source tree")
    result = subprocess.run(
        [sys.executable, "-c", _OPS_QUOTED_EXCEL_PROBE],
        cwd=project,
        env=python_subprocess_env(project),
        capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            f"ops quoted Excel demo: exit {result.returncode}; "
            f"stderr={result.stderr[:600]!r}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("ops quoted Excel demo: malformed JSON") from exc
    check_ops_quoted_excel_contract(payload)
    return "ops-field-brief quoted Excel: PASS (36 variants, 4 malformed)"


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
        outcomes.append(verify_csv_top_n_contract(root))
        outcomes.append(verify_csv_skip_count_contract(root))
        outcomes.append(verify_csv_max_rows_contract(root))
        outcomes.append(verify_csv_field_limit_contract(root))
        outcomes.append(verify_inventory_ma_window_contract(root))
        outcomes.append(verify_inventory_holdout_contract(root))
        outcomes.append(verify_inventory_custom_forecast_contract(root))
        outcomes.append(verify_inventory_alpha_contract(root))
        outcomes.append(verify_inventory_warmup_contract(root))
        outcomes.append(verify_inventory_replay_levels(root))
        outcomes.append(verify_inventory_bootstrap_demand(root))
        outcomes.append(verify_residual_bootstrap_finite(root))
        outcomes.append(verify_ops_top_n_contract(root))
        outcomes.append(verify_ops_excel_case_contract(root))
        outcomes.append(verify_ops_quoted_excel_contract(root))
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
