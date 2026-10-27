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

Read the row count, inferred column types and missing-value indicators. Then inspect [the CSV test suite](https://github.com/rodrix91/csv-quality-report/tree/main/tests) and [CI workflow](https://github.com/rodrix91/csv-quality-report/actions/workflows/ci.yml).

**2. Show a deliberately failed operational quality gate (Python 3.10+):**

```bash
PYTHONPATH=src python -m ops_field_brief examples/orders-incomplete-keys.csv \
  --required order_id --max-missing 1 \
  --key order_id,line_id --max-incomplete-keys 1 --json
```

Expected: **exit code 1**, because this synthetic fixture exceeds the configured allowance for incomplete composite keys. This is a *successful negative test*, not evidence that the dataset passed validation. See the [operations playbook](https://github.com/rodrix91/ops-field-brief/blob/main/docs/README.md).

**3. Explore reproducible inventory-policy scenarios (Python 3.11+):**

```bash
PYTHONPATH=src python -m inventory_policy_lab examples/demand_synthetic.csv
```

Examine forecast selection, service assumptions and inventory-policy replay results. These are illustrative model outputs, not purchase recommendations or verified commercial savings. See the [hand-checked example](https://github.com/rodrix91/inventory-policy-lab#worked-example-checked-by-hand).

## What a reviewer can verify

- **Reliability:** regression suites, CI status and source-distribution tests are visible in the three repositories.
- **Reproducibility:** development dependencies, test fixtures, documentation and version histories are tracked in Git.
- **Controls:** optional fail-closed quality gates are tested, including intentionally malformed or incomplete input.
- **Communication:** each README explains limitations and documents how to reproduce examples.

For a detailed design explanation, see the [portfolio case study](portfolio-case-study.md). For current checks and test counts, use the linked repositories' latest CI runs rather than treating an older count as a live measurement.

## Limits and responsible interpretation

The three examples are independent. No production adoption, enterprise deployment, measured financial return, third-party endorsement or certification is implied. Before any real operational use, verify data permissions, review source-specific assumptions, obtain business approval for thresholds and validate model decisions with domain stakeholders.

**Resumen en español:** Estos tres proyectos permiten revisar la calidad de datos, controlar la integridad de registros operativos y explorar políticas de inventario. Los ejemplos son sintéticos, reproducibles e independientes; no constituyen una implantación empresarial real.
