# Rodrigo Pantoja Navajas

I build practical Python tools focused on **data quality, automation, reproducibility, and clear technical communication**.

Three small standard-library Python tools for CSV and operations work:

- **csv-quality-report**: full profiling (types, locales, ranges, quality gates, baseline drift checks, freshness and allowed-value gates). Status: prototype / alpha (v0.21.0).
- **ops-field-brief**: operational completeness (fill rate, repeated keys, top groups, max-duplicates quality gate). Status: 0.1.0. `--delimiter` accepts comma, semicolon, tab, or pipe. `--encoding` defaults to utf-8 and accepts cp1252 or latin-1. A UTF-8 BOM is stripped, including on stdin. `N/D`, `s.d.`, and `N.D.` count as missing. A path of `-` reads from stdin. `--top` can lower the group limit. A negative `--top` exits `2`. `--max-duplicates` fails if repeated business keys exceed the threshold.
- **inventory-policy-lab**: per-SKU inventory policy from demand history (ABC-XYZ, Syntetos-Boylan patterns, MASE-selected forecasts with opt-in damped Holt and Holt-Winters, normal or bootstrap safety stock, EOQ, and `(s, Q)` or periodic-review `(R, S)` policy replay in and out of sample, with levels that can follow a seasonal forecast, an opt-in bootstrap of forecast residuals, an opt-in rolling-origin replay that refits the policy every test period or every K periods with `--refit-every`, an opt-in periodic-review `(R, s, S)` policy, order, holding and stockout costs that price each out-of-sample replay, per SKU if needed, and an opt-in search of levels for cost, with an optional fill-rate floor and demand paths that refit the forecast on bootstrapped histories). Status: alpha (0.10.0).

## Featured project

### [csv-quality-report](https://github.com/rodrix91/csv-quality-report)

A lightweight Python CLI that profiles CSV files before they enter a notebook or data pipeline.

**What it reports**
- inferred column types
- missing values and percentages
- distinct values
- numeric min/max
- top values
- duplicate rows
- Markdown or JSON output
- date and datetime ranges (ISO 8601, time zones compared as instants)
- configurable missing-value tokens such as `NA`, `null` or `s/d`

**Built for real-world exports**
- semicolon, tab and pipe separated files, with deterministic delimiter detection that refuses to guess
- decimal commas (`10,5`), thousands separators (`1.234,56`), day-first dates (`05/10/2026`), `VERDADERO`/`FALSO` or `Sí`/`No` flags and amounts with currency symbols or units (`Gs. 50.000`, `12,5 kg`) from Spanish, Portuguese and other comma-decimal locales
- spreadsheet exports in cp1252, Latin-1 or UTF-16 with `--encoding`, and very long text fields
- single-pass streaming: on a 1,000,000-row file, peak memory went from 873 MB to 234 MB with identical output
- quality gates for pipelines: `--max-missing`, `--max-duplicates`, required types, value ranges (`--range Peso=0:`), and baseline drift gates (`--max-row-drop`, `--max-missing-increase`, and `--max-missing-increase-column` for a limit per column), `--min-rows` (an export with only its header), `--max-age` (a stale date or datetime column), and `--allowed-values` (closed sets such as status codes) stop a bad extract with a dedicated exit code
- reads from pipes (`-`) and gzip-compressed files transparently, and can be used as a Python library
- flags mixed currencies or units in a column (pesos and dollars, kg and lb) instead of silently averaging them
- available as a GitHub Action: the report goes to the job summary and a failed check fails the job; inputs for a daily workflow that keeps a baseline report
- explains why a column is not numeric or a date by naming the stray values, and can require column types

**Engineering signals**
- Python 3.11+
- standard-library-only runtime
- automated tests
- Ruff linting and formatting checks
- strict mypy type checking
- GitHub Actions CI across Python 3.11, 3.12 and 3.13
- Dependabot
- MIT license
- reproducible development dependencies with hashes
- 100% line and branch test coverage, enforced in CI
- end-to-end tests on realistic export files, compared with hand-checked reports
- design decisions recorded as ADRs, and a maintained CHANGELOG
- security policy in [SECURITY.md](https://github.com/rodrix91/csv-quality-report/blob/main/SECURITY.md)

Latest release: [v0.21.0](https://github.com/rodrix91/csv-quality-report/releases/tag/v0.21.0), with 1,138 tests, 100% coverage, and CI on Linux, macOS and Windows. Since v0.17.0 it adds `--min-rows`, `--max-age` with `--utc-offset` for the freshness of a date column on a fixed clock, `--allow-added-column` and `--allow-removed-column`, and Action inputs (`report-path`, `baseline`, `baseline-args`, `if-baseline-missing`) for daily comparisons against the previous report. Added in v0.17.0: `--allow-type-change [NAME=]FROM:TO` lets the schema gate (`--fail-on-schema-change`) tolerate an expected type widening, such as `int:float` for quantities that gain decimals, in every column or only in one. Since v0.16.0, `--unique-key NAMES` fails when two rows repeat a composite key (an invoice number plus a line number, where each column repeats on its own), and a read-only `--json-output` file is refused on every platform instead of being replaced.

> Status: prototype / alpha. The project is intentionally small and focused while I continue improving reliability, usability, documentation, and release readiness.

### [ops-field-brief](https://github.com/rodrix91/ops-field-brief)

A small standard-library Python CLI that reports fill rate, repeated business keys, and top groups for one operational CSV. `--delimiter` accepts comma (default), semicolon, tab, or pipe, so Spanish and Latin American spreadsheet exports work without changing the default. `--encoding` defaults to utf-8 and accepts `cp1252` or `latin-1` for Windows Excel. A UTF-8 BOM is stripped, including on stdin. `N/D`, `s.d.`, and `N.D.` count as missing. A path of `-` reads from stdin. `--top` can lower the group limit. A negative `--top` exits `2`. It complements csv-quality-report when the question is operational completeness rather than full profiling.

See [docs/related.md](https://github.com/rodrix91/csv-quality-report/blob/main/docs/related.md) in the flagship repository for how the tools fit together.

Status: 0.1.0. Forty-four local unit tests passed, including semicolon, tab, pipe, an unknown delimiter, a duplicate header, `--help`, cp1252, a UTF-8 BOM, a UTF-8 BOM on stdin, `N/D`, `s.d.`, stdin, `--top`, `--top 0`, a negative `--top`, `--max-duplicates` allowing and failing repeated keys, a negative `--max-duplicates`, a quoted field with a comma, an escaped quote, a multiline quoted field, a trailing comma, a whitespace-only field, a tab-only field, three identical keys, two repeated keys, `--json`, and `--max-missing`. CI runs the same suite on Python 3.10 through 3.13. Not a production pipeline.

### [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab)

A Python toolkit and CLI that turns a per-SKU demand history into an inventory policy: ABC classification by annual value, XYZ classification by demand variability, Syntetos-Boylan demand patterns (smooth, erratic, intermittent, lumpy), forecasting with naive, moving average, SES, Croston and SBA (plus damped Holt and Holt-Winters with `--trend-seasonal`) chosen per SKU by backtested MASE, safety stock and reorder points from demand and lead-time variability (normal formula or `--safety-stock bootstrap` seeded per SKU), EOQ, and a historical replay of the resulting (s, Q) policy, or of a periodic-review, order-up-to (R, S) policy with `--policy RS`, that reports fill rate, stockouts, average stock and backorders, with an out-of-sample replay (`--test-periods N`) that fits on the earlier periods and scores the last N. Markdown or JSON output, a reproducible synthetic dataset, a hand-checked worked example, and the formulas and their limits documented in the README.

Status: 0.10.0 (alpha). 393 tests, 100% line and branch coverage, Ruff, strict mypy, and CI on Python 3.11 through 3.13. When the normal-demand assumption is weak for lumpy SKUs, `--safety-stock bootstrap` resamples protection-interval demand from each SKU's history (ADR 0004). Trend and seasonal models are opt-in: on the 24-month synthetic example they do not change the out-of-sample results, because Holt-Winters needs two full seasons of training data (ADR 0006). With `--dynamic-levels` the order-up-to level follows the seasonal forecast month by month instead of one level for the year: on a 48-month synthetic series, out of sample, (R, S) with dynamic levels reached 100% fill rate with 105.5 units of average stock, against 99.6% and 289.0 for the static (s, Q); the bootstrap safety stock did worse with (R, S), and on the 24-month example the dynamic levels change nothing (ADR 0007). `--bootstrap-source residuals` bootstraps the rolling-origin forecast errors over the protection interval instead of demand, with an optional safety stock per period: on the 48-month series it raised the bootstrap's out-of-sample fill rate under (R, S) from 89.3% to 95.4% (96.3% per period), still below the normal formula's 100%, and on the 24-month example it did worse, so it stays opt-in (ADR 0008). `--rolling-origin` adds a replay of the test window that refits forecast, safety stock and levels at the start of every test period from the periods before it only: on the 24-month example it raised the out-of-sample fill rate of (s, Q) from 94.4% to 99.8% with about 5% more stock, while on the 48-month series it mostly bought stock (the normal (R, S) stayed at 100% with 42% more), so it is reported next to the fixed-origin replay, not instead of it (ADR 0009). Since 0.7.0 grid fits are cached and all prefixes of a history are scored in one pass, with byte-identical reports, so that run takes 0.22 s instead of 10.1 s (ADR 0010), and `--refit-every K` refits only every K test periods: on these two datasets the fill rate never rose with K, and on the 48-month series the normal (R, S) kept 100% while stock fell from 149.3 (monthly) to 105.5 (yearly) (ADR 0011). Since 0.8.0 `--order-cost`, `--holding-cost` and `--stockout-cost` price every out-of-sample replay without changing the policy (ADR 0012), and `--policy RsS` orders up to S = s + Q only when the position falls to s (ADR 0013). With example rates of 50 per order, 1 per unit-month and 10 per unit short, (R, S) with a monthly review was cheapest on the 48-month series, where it already served 100%, while on the 24-month example, where frozen forecasts left (R, S) at 90.9% fill rate, (R, s, S) reached 99.3% and was cheapest with a fixed origin; a three-month review was never cheapest at those rates. The ranking depends on the stockout cost, and the README gives the break-even points. Since 0.9.0 holding can be priced as a yearly share of each SKU's unit cost (`--holding-cost-rate`) and order and stockout costs read per SKU from optional columns (`--cost-columns`) (ADR 0014); at 25% a year of unit cost, (R, s, S) with a monthly review became the cheapest policy on the 24-month example. `--optimize-cost` searches each SKU's safety stock and order quantity (s and S = s + Q) for the lowest expected cost on demand paths built from the training periods only, then scores the pick out of sample (ADR 0015): it promised cost cuts of a third or more on training paths but beat both heuristics out of sample in only one of four cases and always lowered the fill rate, so it is documented as a diagnostic of overfitting, and (R, S) at a 0.98 service level was cheapest on the 48-month series.

## Current focus

- Building small, useful developer and data tools
- Data-quality workflows and automation
- Reproducible Python projects
- Testing, documentation, and maintainable CLI design
- Open-source contributions where I can add concrete value
- Data quality for logistics, supply chain and trade datasets

## Languages & tools

Python · pytest · Ruff · mypy · Git · GitHub Actions · Markdown · CSV/data workflows · R

## Spoken languages

Spanish (native) · English · Portuguese · Italian

## Collaboration

I am interested in practical open-source projects involving Python, data tooling, automation, documentation, developer experience, and quality engineering.

I am especially glad to help where logistics or supply chain analytics, or Spanish-language and Latin American use cases, are underserved.

Contributing guidelines: [csv-quality-report](https://github.com/rodrix91/csv-quality-report/blob/main/CONTRIBUTING.md), [ops-field-brief](https://github.com/rodrix91/ops-field-brief/blob/main/CONTRIBUTING.md), and [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab/blob/main/CONTRIBUTING.md).

## Archived coursework

These repositories preserve early coursework and are not current product work:

- [datasciencecoursera](https://github.com/rodrix91/datasciencecoursera) (2020 Coursera R archive)
- [ProgrammingAssignment2](https://github.com/rodrix91/ProgrammingAssignment2) (R Programming assignment fork)
- [datasharing](https://github.com/rodrix91/datasharing) (data-sharing guide fork)

## Contact

[LinkedIn](https://www.linkedin.com/in/rodrigo-p-625862153)
