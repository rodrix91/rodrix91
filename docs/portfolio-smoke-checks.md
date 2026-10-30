# Reproducible synthetic portfolio smoke checks

The [portfolio demo workflow](../.github/workflows/portfolio-demos.yml) independently exercises the three command-line examples in the [reviewer guide](portfolio-review-guide.md) on Python 3.14 (Linux, Windows, and macOS). These are three separate public code samples, not one production integration.

| Project | Pinned, reviewed source commit | Expected result |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | `3e97d1d986dd551224d1a2941737fedc5d086981` | Exit 0; 3 records, 1 missing quantity |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | `070bb56c6d2ab0488ba7f4f5cb72443ae2640ac6` | **Intentional exit 1**; 2 incomplete composite keys and 1 extra duplicate |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | `925eee4d23b1f6d9a14172fe64a84d67bb6d033b` | Exit 0; 12 distinct synthetic SKU outputs |

The three copy-and-pasteable Bash invocations in the English guide, Spanish guide, and case study are regression-tested against the actual commands used by the smoke workflow. The pinned source commits in this page are also compared with the workflow checkouts, so a future documentation-only edit cannot silently misdescribe what the CI ran.

The current snapshot also exercises the optional case-insensitive missing-value marker feature added in [csv-quality-report PR #232](https://github.com/rodrix91/csv-quality-report/pull/232): the checked-in [Bolivian operations example](../tests/fixtures/bolivia-mixed-na.csv) deliberately mixes `S/D` and `s/d` in a semicolon-delimited, decimal-comma weight column. Default exact matching reports one missing weight and infers a string; enabling `--na-ignore-case` reports two missing weights, infers numeric values, and leaves the original default JSON contract unchanged. Both CLI paths must return exit 0. This is a synthetic demonstration, not operational customer data.

The opt-in NFC normalization safeguard from [csv-quality-report PR #233](https://github.com/rodrix91/csv-quality-report/pull/233) is exercised independently using the synthetic [accented missing-marker fixture](../tests/fixtures/canonical-na-marker.csv). The two representations of `información` are visually identical but differ in Unicode encoding. Without `--na-ignore-case`, the `peso` column remains a string; with the option it is numeric and the missing count increases. Default exact matching and the original CSV bytes remain unchanged.

The [inventory replay validation from PR #111](https://github.com/rodrix91/inventory-policy-lab/pull/111) is also tested against the pinned source. A synthetic in-process Python probe runs **all three replay policies** with finite stock levels, then deliberately supplies `NaN` scalar levels, infinite per-period levels and invalid order quantities where applicable. All valid replays must report three periods and a 100% fill rate; malformed inputs must raise explicit, index-aware `ValueError` exceptions instead of returning misleading metrics. The negative probes are expected errors, not operational inventory data or failed GitHub Actions jobs.

The [bootstrap demand-input protection in inventory-policy-lab PR #112](https://github.com/rodrix91/inventory-policy-lab/pull/112) is checked against the immutable inventory source by an additional synthetic probe. It requires finite, non-negative historical and forecast demand, including a zero-period protection interval; eight negative/NaN/infinite examples must be rejected with the correct indexed input error **before drawing from the random generator**. Independent valid zero, constant and intermittent histories must retain zero/finite safety-stock outputs and seeded reproducibility. These are expected input-validation errors, not real customer data or failed CI jobs.

The [strict CSV sniffing fix in ops-field-brief PR #116](https://github.com/rodrix91/ops-field-brief/pull/116) has an additional independent, synthetic smoke test. The pinned project reads long **unquoted** fields that span the 8 KiB delimiter-sniff window, across comma, semicolon, tab and pipe delimiters and LF, CRLF and CR-only records. A wrapped real text stream rejects any unbounded `read()` during delimiter detection; all twelve combinations must return three correctly parsed rows with intact 9,000-character values and physical source lines. This guard is specific to `--strict-csv --delimiter auto`. It verifies reduced temporary memory use during delimiter selection, not constant-memory analysis or production-scale performance.

The [duplicate-key historical JSON fixture](../tests/fixtures/duplicate-baseline-rows.json) also checks the newest CSV safeguard: a baseline containing two `rows` properties must **fail with input exit 3** before any new profiling, and a preexisting report file must remain untouched. This is an intentional negative test, not a failed CI run. The fixture is synthetic and never contains real customer data.

Two more synthetic corrupted JSON baselines check the latest safeguards: [`NaN` as an unquoted token](../tests/fixtures/nonstandard-baseline-nan.json) and an [overflowing exponent `1e309`](../tests/fixtures/overflow-baseline-exponent.json). Both must **fail with input exit 3** without overwriting a previous JSON report. This verifies strict historical-baseline parsing, not a failure of the GitHub Actions workflow.

The harness checks exit status, JSON parsing, and concrete result invariants, not merely whether a Python process started. Its additional synthetic [canonical-Unicode fixture](../tests/fixtures/canonical-unicode-keys.csv) verifies that visually identical composed/decomposed labels stay distinct by default but trigger duplicate-key and counterparty-concentration checks when `--casefold-key --casefold-group` is selected. The explicit failure exit code 1 is expected for that optional quality gate; it is not a passed operational dataset. It runs only with bundled synthetic fixtures, requires no API keys and does not transmit or publish user data.

To rerun locally, clone each of the three projects into sibling folders with their repository names under the profile checkout. From the profile checkout run:

```bash
python -m unittest discover -s tests -p 'test_portfolio_demos.py' -v
python scripts/verify_portfolio_demos.py
```

The operations checkout includes reviewed Unicode NFC safety, fail-closed ambiguous delimiter handling and bounded strict sniffing; the inventory checkout includes validated backtesting inputs and finite replay-policy guards. These refreshed pins reflect the current merged `main` commits at the time of review, not floating branches. All source changes remain governed by each repository's own CI.

GitHub Actions pins specific source commits to prevent unreviewed upstream changes from silently changing the example results. Updating these pins requires reviewing the new source and rerunning all platform checks. The demonstrations are **not a deployed customer integration, real company data, verified financial savings, or production readiness**.
