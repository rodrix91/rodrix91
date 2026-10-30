# Reproducible synthetic portfolio smoke checks

The [portfolio demo workflow](../.github/workflows/portfolio-demos.yml) independently exercises the three command-line examples in the [reviewer guide](portfolio-review-guide.md) on Python 3.14 (Linux, Windows, and macOS). These are three separate public code samples, not one production integration.

| Project | Pinned, reviewed source commit | Expected result |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | `3e97d1d986dd551224d1a2941737fedc5d086981` | Exit 0; 3 records, 1 missing quantity |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | `d464ee60813d8dc986a317ee4c7d8b2d83232c49` | **Intentional exit 1**; 2 incomplete composite keys and 1 extra duplicate |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | `bad5e89b620f7d075673a0867a897ead1779c93d` | Exit 0; 12 distinct synthetic SKU outputs |

The three copy-and-pasteable Bash invocations in the English guide, Spanish guide, and case study are regression-tested against the actual commands used by the smoke workflow. The pinned source commits in this page are also compared with the workflow checkouts, so a future documentation-only edit cannot silently misdescribe what the CI ran.

The current snapshot also exercises the optional case-insensitive missing-value marker feature added in [csv-quality-report PR #232](https://github.com/rodrix91/csv-quality-report/pull/232): the checked-in [Bolivian operations example](../tests/fixtures/bolivia-mixed-na.csv) deliberately mixes `S/D` and `s/d` in a semicolon-delimited, decimal-comma weight column. Default exact matching reports one missing weight and infers a string; enabling `--na-ignore-case` reports two missing weights, infers numeric values, and leaves the original default JSON contract unchanged. Both CLI paths must return exit 0. This is a synthetic demonstration, not operational customer data.

The opt-in NFC normalization safeguard from [csv-quality-report PR #233](https://github.com/rodrix91/csv-quality-report/pull/233) is exercised independently using the synthetic [accented missing-marker fixture](../tests/fixtures/canonical-na-marker.csv). The two representations of `información` are visually identical but differ in Unicode encoding. Without `--na-ignore-case`, a typed `weight` column remains a string; with the option it is numeric and the missing count increases. Default exact matching and the original CSV bytes remain unchanged.

The [duplicate-key historical JSON fixture](../tests/fixtures/duplicate-baseline-rows.json) also checks the newest CSV safeguard: a baseline containing two `rows` properties must **fail with input exit 3** before any new profiling, and a preexisting report file must remain untouched. This is an intentional negative test, not a failed CI run. The fixture is synthetic and never contains real customer data.

Two more synthetic corrupted JSON baselines check the latest safeguards: [`NaN` as an unquoted token](../tests/fixtures/nonstandard-baseline-nan.json) and an [overflowing exponent `1e309`](../tests/fixtures/overflow-baseline-exponent.json). Both must **fail with input exit 3** without overwriting a previous JSON report. This verifies strict historical-baseline parsing, not a failure of the GitHub Actions workflow.

The harness checks exit status, JSON parsing, and concrete result invariants, not merely whether a Python process started. Its additional synthetic [canonical-Unicode fixture](../tests/fixtures/canonical-unicode-keys.csv) verifies that visually identical composed/decomposed labels stay distinct by default but trigger duplicate-key and counterparty-concentration checks when `--casefold-key --casefold-group` is selected. The explicit failure exit code 1 is expected for that optional quality gate; it is not a passed operational dataset. It runs only with bundled synthetic fixtures, requires no API keys and does not transmit or publish user data.

To rerun locally, clone each of the three projects into sibling folders with their repository names under the profile checkout. From the profile checkout run:

```bash
python -m unittest discover -s tests -p 'test_portfolio_demos.py' -v
python scripts/verify_portfolio_demos.py
```

The operations checkout includes reviewed Unicode NFC safety and fail-closed delimiter handling; the inventory checkout includes validated backtesting inputs. These refreshed pins reflect the current merged `main` commits at the time of review, not floating branches. All source changes remain governed by each repository's own CI.

GitHub Actions pins specific source commits to prevent unreviewed upstream changes from silently changing the example results. Updating these pins requires reviewing the new source and rerunning all platform checks. The demonstrations are **not a deployed customer integration, real company data, verified financial savings, or production readiness**.
