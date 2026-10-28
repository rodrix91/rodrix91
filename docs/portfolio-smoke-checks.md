# Reproducible synthetic portfolio smoke checks

The [portfolio demo workflow](../.github/workflows/portfolio-demos.yml) independently exercises the three command-line examples in the [reviewer guide](portfolio-review-guide.md) on Python 3.14 (Linux, Windows, and macOS). These are three separate public code samples, not one production integration.

| Project | Pinned, reviewed source commit | Expected result |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | `aee95d06988b6143e0c8e0a2af378aa3cccc73fb` | Exit 0; 3 records, 1 missing quantity |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | `410501869119cc41cccb83e97d4a15f840767b94` | **Intentional exit 1**; 2 incomplete composite keys and 1 extra duplicate |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | `59b69e4c65c9abe8c0e9290564b2aae5471d477b` | Exit 0; 12 distinct synthetic SKU outputs |

The three copy-and-pasteable Bash invocations in the English guide, Spanish guide, and case study are regression-tested against the actual commands used by the smoke workflow. The pinned source commits in this page are also compared with the workflow checkouts, so a future documentation-only edit cannot silently misdescribe what the CI ran.

The [duplicate-key historical JSON fixture](../tests/fixtures/duplicate-baseline-rows.json) also checks the newest CSV safeguard: a baseline containing two `rows` properties must **fail with input exit 3** before any new profiling, and a preexisting report file must remain untouched. This is an intentional negative test, not a failed CI run. The fixture is synthetic and never contains real customer data.

The harness checks exit status, JSON parsing, and concrete result invariants, not merely whether a Python process started. Its additional synthetic [canonical-Unicode fixture](../tests/fixtures/canonical-unicode-keys.csv) verifies that visually identical composed/decomposed labels stay distinct by default but trigger duplicate-key and counterparty-concentration checks when `--casefold-key --casefold-group` is selected. The explicit failure exit code 1 is expected for that optional quality gate; it is not a passed operational dataset. It runs only with bundled synthetic fixtures, requires no API keys and does not transmit or publish user data.

To rerun locally, clone each of the three projects into sibling folders with their repository names under the profile checkout. From the profile checkout run:

```bash
python -m unittest discover -s tests -p 'test_portfolio_demos.py' -v
python scripts/verify_portfolio_demos.py
```

The operations checkout now includes the reviewed [Unicode NFC safety change (#112)](https://github.com/rodrix91/ops-field-brief/pull/112). The existing synthetic smoke fixture does not specifically exercise accented identifiers; those cases are covered by the operations repository's new regression tests.

GitHub Actions pins specific source commits to prevent unreviewed upstream changes from silently changing the example results. Updating these pins requires reviewing the new source and rerunning all platform checks. The demonstrations are **not a deployed customer integration, real company data, verified financial savings, or production readiness**.
