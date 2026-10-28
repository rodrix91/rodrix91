# Portfolio review guide

**For hiring managers, operations leaders and technical reviewers.** This page is a short route through three independent open-source work samples. The repositories demonstrate reproducible analysis and engineering practices. They are **not** represented as production customer deployments.

## Business questions each tool helps answer

| Question | Work sample | What to inspect |
|---|---|---|
| Is an incoming data extract usable? | [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | Required columns, missing values, inferred types, duplicates and optional failure gates |
| Are operational identifiers and counterparties trustworthy? | [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | Required-field completeness, composite-key controls, duplicate limits and group concentration |
| How might an inventory policy perform against historical demand? | [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | ABC-XYZ segmentation, forecast backtests, safety stock, reorder points and policy replays |

## Five-minute hands-on review

Each command runs **separately, from the named repository's root**, on bundled **synthetic data**. Clone the repository first. These tools do not form a deployed end-to-end integration.

**1. Profile data quality (Python 3.11+):**

```bash
PYTHONPATH=src python -m csv_quality_report examples/tiny.csv --format json
```

Read the row count, inferred column types and missing-value indicators. Then inspect [the CSV test suite](https://github.com/rodrix91/csv-quality-report/tree/main/tests) and [CI workflow](https://github.com/rodrix91/csv-quality-report/actions/workflows/ci.yml). The [merged strict-quoted-CSV safeguard (#224)](https://github.com/rodrix91/csv-quality-report/pull/224) rejects malformed quoted records rather than silently profiling corrupted cells; [exact-head CI](https://github.com/rodrix91/csv-quality-report/actions/runs/40610110107) passed 1,793 tests, 100% line/branch coverage and 9/9 jobs. The earlier [Excel separator safeguard (#223)](https://github.com/rodrix91/csv-quality-report/pull/223) prevents malformed half-quoted `sep=` first lines from being silently discarded. The earlier [CR-only legacy CSV fix (#222)](https://github.com/rodrix91/csv-quality-report/pull/222) remains available for reviewing automatic delimiter detection.

**2. Show a deliberately failed operational quality gate (Python 3.10+):**

```bash
PYTHONPATH=src python -m ops_field_brief examples/orders-incomplete-keys.csv \
  --required order_id --max-missing 1 \
  --key order_id,line_id --max-incomplete-keys 1 --json
```

Expected: **exit code 1**, because this synthetic fixture exceeds the configured allowance for incomplete composite keys. This is a *successful negative test*, not evidence that the dataset passed validation. See the [operations playbook](https://github.com/rodrix91/ops-field-brief/blob/main/docs/README.md).

**3. Explore reproducible inventory-policy scenarios (Python 3.11+):**

```bash
PYTHONPATH=src python -m inventory_policy_lab examples/demand_synthetic.csv --format json
```

Examine the JSON report's forecast selection, service assumptions and inventory-policy replay results. The [regional Excel/ERP CSV milestone (#95)](https://github.com/rodrix91/inventory-policy-lab/pull/95) adds explicit comma, semicolon, tab and pipe input without changing the comma default. The subsequently [merged Excel `sep=` preamble enhancement (#96)](https://github.com/rodrix91/inventory-policy-lab/pull/96) recognizes an exact first-line hint when it matches the explicit delimiter: for a file beginning with `sep=;`, pass `--delimiter semicolon`. Contradictory or unsupported hints fail safely rather than guessing; see [940 passing tests, full coverage and 9/9 CI checks for the parser](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40550550444). The [subsequent merged PR #97](https://github.com/rodrix91/inventory-policy-lab/pull/97) adds an executable `examples/regional-excel.csv` fixture, tested with [943 passing tests and 9/9 CI checks](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40552823173).  The [new Unicode ERP header safeguard (#100)](https://github.com/rodrix91/inventory-policy-lab/pull/100) rejects case-equivalent duplicate consumed headers instead of silently choosing one; the [966-test exact-head CI](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40607684934) passed all nine jobs and full line/branch coverage. The earlier [month-year safeguard (#99)](https://github.com/rodrix91/inventory-policy-lab/pull/99) rejects impossible `0000-MM` dates without overwriting previous reports. The preceding [safeguard (#98)](https://github.com/rodrix91/inventory-policy-lab/pull/98) fixed source-line diagnostics after multiline quoted CSV fields. These are illustrative model outputs, not purchase recommendations or verified commercial savings. See the [hand-checked example](https://github.com/rodrix91/inventory-policy-lab#worked-example-checked-by-hand).

## Five-minute review on Windows PowerShell

Each block assumes a **different repository**, cloned and opened at its root.
Use PowerShell's environment-variable syntax instead of the Unix/macOS
`PYTHONPATH=src command` form above. Install the appropriate Python version
first (3.11+ for CSV and inventory; 3.10+ for operations). The sample files
below were checked against the corresponding repositories.

**In the `csv-quality-report` repository:**

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m csv_quality_report examples/tiny.csv --format json
$LASTEXITCODE  # expected: 0
Remove-Item Env:PYTHONPATH
```

**In the `ops-field-brief` repository:**

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m ops_field_brief examples/orders-incomplete-keys.csv --required order_id --max-missing 1 --key order_id,line_id --max-incomplete-keys 1 --json
$LASTEXITCODE  # expected: 1; an intentionally failed quality gate
Remove-Item Env:PYTHONPATH
```

**In the `inventory-policy-lab` repository:**

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m inventory_policy_lab examples/demand_synthetic.csv
$LASTEXITCODE  # expected: 0
Remove-Item Env:PYTHONPATH
```

The `$LASTEXITCODE` line must immediately follow the Python invocation;
otherwise it could reflect a different command. These are synthetic examples,
not a production environment or a connected three-stage pipeline. Windows is
included in each project's automated CI matrix, but these exact PowerShell
copy/paste snippets have not been separately executed interactively.

## What a reviewer can verify

- **Reliability:** regression suites, CI status and source-distribution tests are visible in the three repositories.
- **Reproducibility:** development dependencies, test fixtures, documentation and version histories are tracked in Git.
- **Controls:** optional fail-closed quality gates are tested, including intentionally malformed or incomplete input.
- **Communication:** each README explains limitations and documents how to reproduce examples.

For a detailed design explanation, see the [portfolio case study](portfolio-case-study.md). The latest checked operations stdin safeguard passed [291 tests and 11/11 exact-head CI jobs](https://github.com/rodrix91/ops-field-brief/actions/runs/40606326700) and was [merged as PR #109](https://github.com/rodrix91/ops-field-brief/pull/109). It handles CR-only legacy CSV with an explicit stdin delimiter, complementing the earlier [auto-delimiter and Excel `sep=` fix (#108)](https://github.com/rodrix91/ops-field-brief/pull/108) while preserving LF and CRLF. The preceding [PR #107](https://github.com/rodrix91/ops-field-brief/pull/107) reports physical source lines alongside logical row numbers on strict-structure errors. The earlier 273-test milestone added a [real synthetic Excel `sep=;` fixture](https://github.com/rodrix91/ops-field-brief/blob/main/examples/orders-excel-sep.csv) and an executable JSON quality-gate example. Earlier Unicode-safe rendering and Excel-header handling remain validated. For current checks and test counts, use the linked repositories' latest CI runs rather than treating an older count as a live measurement.

## Limits and responsible interpretation

The three examples are independent. No production adoption, enterprise deployment, measured financial return, third-party endorsement or certification is implied. Before any real operational use, verify data permissions, review source-specific assumptions, obtain business approval for thresholds and validate model decisions with domain stakeholders.

**Resumen en español:** Estos tres proyectos permiten revisar la calidad de datos, controlar la integridad de registros operativos y explorar políticas de inventario. Los ejemplos son sintéticos, reproducibles e independientes; no constituyen una implantación empresarial real.
