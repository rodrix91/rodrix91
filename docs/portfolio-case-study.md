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

These milestones were verified in exact-head GitHub Actions runs before
the corresponding source changes were squash-merged:

| Repository | Tests | Coverage | GitHub Actions evidence |
|---|---:|---:|---|
| csv-quality-report | 1,744 | 100% line and branch | [9/9 jobs — fail-closed UTF-16 decoding](https://github.com/rodrix91/csv-quality-report/actions/runs/40514885949) |
| ops-field-brief | 251 | 100% line and branch | [11/11 jobs — direct gzip CSV support](https://github.com/rodrix91/ops-field-brief/actions/runs/40447175148) |
| inventory-policy-lab | 906 | 100% line and branch | [9/9 jobs — explicit Excel/ERP input encodings](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40451743319) |

The cross-platform suites exercise Linux, Windows and macOS, with static
analysis, packaging and reusable GitHub Actions where applicable. Consult
each project's current CI and changelog for new commits and alpha limitations.

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
