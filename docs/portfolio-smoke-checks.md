# Reproducible synthetic portfolio smoke checks

The [portfolio demo workflow](../.github/workflows/portfolio-demos.yml) independently exercises the three command-line examples in the [reviewer guide](portfolio-review-guide.md) on Python 3.14 (Linux, Windows, and macOS). These are three separate public code samples, not one production integration.

| Project | Pinned, reviewed source commit | Expected result |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | `d9de64fd7bcb56b8eeec68696d396f58bb2b01c4` | Exit 0; 3 records, 1 missing quantity |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | `f35431b10cbe4b9277d0edbe83ece09b7bfb0992` | **Intentional exit 1**; 2 incomplete composite keys and 1 extra duplicate |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | `59b69e4c65c9abe8c0e9290564b2aae5471d477b` | Exit 0; 12 distinct synthetic SKU outputs |

The three copy-and-pasteable Bash invocations in the English guide, Spanish guide, and case study are regression-tested against the actual commands used by the smoke workflow. The pinned source commits in this page are also compared with the workflow checkouts, so a future documentation-only edit cannot silently misdescribe what the CI ran.

The harness checks exit status, JSON parsing, and concrete result invariants, not merely whether a Python process started. It runs only with bundled synthetic fixtures, requires no API keys and does not transmit or publish user data.

To rerun locally, clone each of the three projects into sibling folders with their repository names under the profile checkout. From the profile checkout run:

```bash
python -m unittest discover -s tests -p 'test_portfolio_demos.py' -v
python scripts/verify_portfolio_demos.py
```

GitHub Actions pins specific source commits to prevent unreviewed upstream changes from silently changing the example results. Updating these pins requires reviewing the new source and rerunning all platform checks. The demonstrations are **not a deployed customer integration, real company data, verified financial savings, or production readiness**.
