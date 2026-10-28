# Portfolio case study: from CSV quality to inventory decisions

**Purpose:** Show how three independent open-source projects can support a
reproducible supply-chain workflow, from trustworthy source files to
operational controls and inventory-policy analysis.

This is a **demonstration architecture**, not a claim of a deployed customer
integration or a single executable three-project pipeline. Each repository
ships its own synthetic examples and can be inspected and tested separately.

## 1. The business problem

An operations team receives CSV extracts from procurement, shipping and demand
planning. Common problems include missing business identifiers, repeated
shipments, inconsistent headers and unexpected missing values. Even after a
file is structurally valid, inventory decisions require explicit modelling
assumptions, backtesting and review.

The projects address **different layers** of this problem:

| Layer | Project | What the operator can verify |
|---|---|---|
| Data readiness | [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | Types, missingness, duplicates, expected columns and baseline drift |
| Operational integrity | [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | Required cells, complete business keys, duplicate-key limits, row counts and group concentration |
| Inventory analysis | [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | Demand patterns, ABC-XYZ classes, forecasts, safety stock, reorder points and simulated policies |

## 2. Reproducible examples

Run each command **from its own repository root** after cloning. These examples
do not share a data file: each synthetic fixture demonstrates its tool's
independent quality checks.

### A. Profile a small source extract

In `csv-quality-report` (Python 3.11+):

```bash
PYTHONPATH=src python -m csv_quality_report examples/tiny.csv --format json
```

The synthetic `tiny.csv` contains three data rows. Inspect the JSON report
for inferred types, null rates and duplicates before trusting upstream data.
In CI, this project can compare reports against earlier baselines and enforce
opt-in quality thresholds.

### B. Reject an export with broken business identifiers

In `ops-field-brief` (Python 3.10+):

```bash
PYTHONPATH=src python -m ops_field_brief examples/orders-incomplete-keys.csv \
  --required order_id --max-missing 1 \
  --key order_id,line_id --max-incomplete-keys 1 --json
```

The five-row fixture has two incomplete composite keys and one extra duplicate
complete key. The incomplete-key limit is one, so the command intentionally
**exits with code 1**: that is a successful demonstration of a quality-gate
failure, not an accepted clean file. Thresholds are configurable.

### C. Analyze inventory using synthetic demand history

In `inventory-policy-lab` (Python 3.11+):

```bash
PYTHONPATH=src python -m inventory_policy_lab examples/demand_synthetic.csv
```

The synthetic dataset represents twelve SKUs across twenty-four monthly
periods. Review ABC-XYZ segmentation, demand patterns, forecasts and
replenishment policies as **model outputs**, not approved purchase orders.
Simulation is not proof of financial impact at a real company.

## 3. Engineering quality and auditability

The table records completed passing GitHub Actions runs for **specific
commits**, not an estimate of all future commits or a claim of commercial
deployment. The latest evidence for these projects comes from all passing jobs on their
exact pull-request heads before verified squash merges; historical merged-main
CI checks are also linked in the project documentation.

| Repository | Tests | Coverage | GitHub Actions evidence |
|---|---:|---:|---|
| csv-quality-report | 1,793 | 100% line and branch | [9/9 jobs: strict malformed quoted CSV safeguard](https://github.com/rodrix91/csv-quality-report/actions/runs/40610110107) |
| ops-field-brief | 291 | 100% line and branch | [11/11 jobs: exact-head CR-only explicit stdin fix](https://github.com/rodrix91/ops-field-brief/actions/runs/40606326700) |
| inventory-policy-lab | 966 | 100% line and branch | [9/9 jobs: exact-head Unicode-equivalent ERP header protection](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40607684934) |

The [latest merged strict-CSV quoting safeguard (#224)](https://github.com/rodrix91/csv-quality-report/pull/224) rejects corrupted quoted cells before generating quality metrics, including gzip/standard-input exports, while preserving prior JSON reports on invalid data. The preceding [CSV metadata integrity safeguard (#223)](https://github.com/rodrix91/csv-quality-report/pull/223) preserves malformed half-quoted `sep=` headers as input, rather than stripping the first line. The [earlier CR-only delimiter improvement (#222)](https://github.com/rodrix91/csv-quality-report/pull/222) remains separately documented.

The [new explicit-stdin safeguard (#109)](https://github.com/rodrix91/ops-field-brief/pull/109) supports classic `CR` physical record endings with a selected separator and preserves existing strict CSV location diagnostics, BOM handling and LF/CRLF behavior. The earlier [CR-only auto-delimiter fix (#108)](https://github.com/rodrix91/ops-field-brief/pull/108) supports legacy carriage-return line endings, single-column stdin and Excel preambles with safe parsing and preserved diagnostics. The preceding [operational strict-CSV diagnostics PR #107](https://github.com/rodrix91/ops-field-brief/pull/107) adds physical file line numbers to existing logical-record errors, including multiline quoted fields, while preserving the 273-test [Excel example milestone (#106)](https://github.com/rodrix91/ops-field-brief/pull/106) as historical evidence.

All three matrices cover Linux, Windows and macOS, and include static
analysis, package verification and reusable GitHub Actions where
applicable. The [inventory Excel `sep=` PR #96](https://github.com/rodrix91/inventory-policy-lab/pull/96)
passed its exact-head CI matrix and was [squash-merged into `main`](https://github.com/rodrix91/inventory-policy-lab/commit/c684a73561cac75e2adb9f2dd5925a4bc337c1b9). The subsequent [merged synthetic Excel demonstration (#97)](https://github.com/rodrix91/inventory-policy-lab/pull/97) includes a runnable fixture at `examples/regional-excel.csv` and API/CLI regression checks. The latest 966-test snapshot includes the [Unicode ERP header safeguard (#100)](https://github.com/rodrix91/inventory-policy-lab/pull/100), which prevents silently selecting a case-equivalent duplicate header. The earlier 958-test snapshot covers the [validated year-zero monthly-period fix (#99)](https://github.com/rodrix91/inventory-policy-lab/pull/99), which rejects impossible month years and preserves already-written reports on failure. The earlier 950-test [physical CSV line diagnostic fix (#98)](https://github.com/rodrix91/inventory-policy-lab/pull/98) remains documented for audit history and correctly reports file lines after multiline quoted cells. The earlier 943-test Excel snapshot remains documented in the project README. For earlier tests and milestones, refer to each repository's
README and changelog; the underlying source history is preserved.

## 4. Responsible use

A rollout would start with representative exports, documented schema
assumptions and business-approved thresholds. Quality failures should halt
or quarantine processing. Inventory results need review of seasonality,
lead times, forecast errors, service-level choices and financial limits.
Private operational data and workflow logs require appropriate permissions.

These projects are **building blocks**, not an ERP, a deployed customer
integration or a substitute for human operational judgement.

## 5. Skills demonstrated

Python CLI development · automated regression tests · data-quality engineering ·
operations and supply-chain analytics · inventory modelling · secure
GitHub Actions · cross-platform CI · reproducibility · technical documentation.

**Resumen en español:** Los tres proyectos ilustran fases complementarias:
verificar la calidad de un CSV, controlar datos operativos y analizar políticas
de inventario. Los ejemplos son sintéticos e independientes, no una
implantación empresarial real ni resultados económicos demostrados.
