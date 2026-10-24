# Rodrigo Pantoja Navajas

I build practical Python tools focused on **data quality, automation, reproducibility, and clear technical communication**.

## Portfolio at a glance

| Project | Purpose | Engineering signal |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | Deep CSV profiling and pipeline quality gates | 100% line/branch coverage, strict typing, PEP 561, CITATION.cff, cross-platform CI |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | Fast operational completeness and concentration checks | 97 tests, 100% coverage, reusable GitHub Action, PEP 561 |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | Inventory policy, forecasting and replay for supply-chain decisions | 473 tests, 100% coverage, reusable GitHub Action, CITATION.cff |

The three projects are intentionally complementary: profile data quality, validate operational extracts, then model inventory decisions. All three publish `CITATION.cff` metadata for reproducible citation.

Across all three active projects, GitHub Actions dependencies are pinned by commit SHA, release artifacts include SHA-256 checksums, and current release workflows generate GitHub/Sigstore provenance attestations for wheels and source distributions.

## Detailed project snapshot

Three small standard-library Python tools for CSV and operations work:

- **csv-quality-report**: full profiling (types, locales, ranges, quality gates, baseline drift checks, freshness and allowed-value gates). Status: prototype / alpha; `main` is 0.22.0 with additional Unreleased work, while v0.21.0 remains the latest published release.
- **ops-field-brief**: operational completeness (fill rate, repeated keys, top groups, duplicate and row-count gates, plus an opt-in top-group concentration gate). Package version: 0.3.0 with additional Unreleased work; the first public GitHub release is still pending and tracked in [issue #16](https://github.com/rodrix91/ops-field-brief/issues/16). It supports automatic detection of comma, semicolon, tab, or pipe, `--version`, stdin and common spreadsheet encodings; it also exposes a reusable composite GitHub Action with `exit-code` and `passed` outputs. CI runs 93 tests on Python 3.10 through 3.13 on Ubuntu, plus Python 3.10 and 3.13 on Windows and macOS, smoke-tests the built wheel in a clean environment, tests the Action end to end, verifies the installed PEP 561 marker, enforces 100% line and branch coverage, and runs Ruff plus mypy.
- **inventory-policy-lab**: per-SKU inventory policy from demand history (ABC-XYZ, Syntetos-Boylan patterns, MASE-selected forecasts with opt-in damped Holt and Holt-Winters, normal or bootstrap safety stock, EOQ, and `(s, Q)` or periodic-review `(R, S)` policy replay in and out of sample, with levels that can follow a seasonal forecast, an opt-in bootstrap of forecast residuals, an opt-in rolling-origin replay that refits the policy every test period or every K periods with `--refit-every`, an opt-in periodic-review `(R, s, S)` policy, order, holding and stockout costs that price each out-of-sample replay, per SKU if needed, and an opt-in search of levels for cost, with an optional fill-rate floor and demand paths that refit the forecast on bootstrapped histories). Status: alpha (0.10.0).

## Featured project

### [csv-quality-report](https://github.com/rodrix91/csv-quality-report)

The [CSV Markdown-rendering fix (#190)](https://github.com/rodrix91/csv-quality-report/pull/190) now displays source names, column labels and sampled values literally instead of allowing CSV data to create links, HTML markup or extra table cells. JSON values remain unchanged. [PR CI](https://github.com/rodrix91/csv-quality-report/actions/runs/40136592228) passed all nine jobs, with **1,272 tests** and 100% coverage across the supported OS/Python matrix.

The [Action reliability fix (#189)](https://github.com/rodrix91/csv-quality-report/pull/189) prevents `--help`, `--version`, and accepted abbreviations from producing false-green CSV quality checks. Its [CI run](https://github.com/rodrix91/csv-quality-report/actions/runs/40133623926) passed all 9 jobs, including 1,269 tests with 100% coverage.

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
- PEP 561 `py.typed` marker for downstream type checkers
- GitHub Actions CI across Python 3.11, 3.12 and 3.13
- Dependabot
- MIT license
- reproducible development dependencies with hashes
- 100% line and branch test coverage, enforced in CI
- end-to-end tests on realistic export files, compared with hand-checked reports
- design decisions recorded as ADRs, and a maintained CHANGELOG
- security policy in [SECURITY.md](https://github.com/rodrix91/csv-quality-report/blob/main/SECURITY.md)
- software citation metadata in [CITATION.cff](https://github.com/rodrix91/csv-quality-report/blob/main/CITATION.cff), retained in the source distribution and linked from package metadata

Latest published release: [v0.21.0](https://github.com/rodrix91/csv-quality-report/releases/tag/v0.21.0). Current `main` reports version 0.22.0 and its CI runs **1,272 tests** with 100% line and branch coverage across Linux, macOS and Windows; the missing v0.22.0 release tag is tracked separately so newer Unreleased work is not mislabeled. Since v0.17.0 it adds `--min-rows`, `--max-age` with `--utc-offset` for the freshness of a date column on a fixed clock, `--allow-added-column` and `--allow-removed-column`, and Action inputs (`report-path`, `baseline`, `baseline-args`, `if-baseline-missing`) for daily comparisons against the previous report. Added in v0.17.0: `--allow-type-change [NAME=]FROM:TO` lets the schema gate (`--fail-on-schema-change`) tolerate an expected type widening, such as `int:float` for quantities that gain decimals, in every column or only in one. Since v0.16.0, `--unique-key NAMES` fails when two rows repeat a composite key (an invoice number plus a line number, where each column repeats on its own), and a read-only `--json-output` file is refused on every platform instead of being replaced.

> Status: prototype / alpha. The project is intentionally small and focused while I continue improving reliability, usability, documentation, and release readiness.

### [ops-field-brief](https://github.com/rodrix91/ops-field-brief)

The [Markdown report safety improvement](https://github.com/rodrix91/ops-field-brief/pull/54) now displays CSV-derived field names, business keys and group labels literally in operational tables and GitHub Action summaries, rather than treating pipes, links or newlines as Markdown. Original JSON values remain unchanged. Its [post-merge CI](https://github.com/rodrix91/ops-field-brief/actions/runs/40135920209) passed on `main`; the reviewed PR also passed 97 tests at 100% line/branch coverage and 11/11 checks.

The [threshold validation fix](https://github.com/rodrix91/ops-field-brief/pull/53) now rejects `NaN` for `--max-missing` instead of allowing missing-data checks to pass unexpectedly. The [validated workflow](https://github.com/rodrix91/ops-field-brief/actions/runs/40134621591) passed 93 tests and all 11 jobs on Linux, macOS and Windows.

A new [opt-in incomplete business key gate](https://github.com/rodrix91/ops-field-brief/pull/52) checks single or composite identifiers for blank components, such as an order without its line ID. It reports the count separately from duplicate keys, so operational pipelines can set their own acceptable limit without changing previous defaults.

The reusable Action now [fails closed on informational CLI flags](https://github.com/rodrix91/ops-field-brief/pull/51), preventing a workflow from reporting a successful CSV quality check when `--help` or `--version` ran instead. The fix is backed by [cross-platform CI and 90 regression tests](https://github.com/rodrix91/ops-field-brief/actions/runs/40132477212).

A small standard-library Python CLI that reports fill rate, repeated business keys, and top groups for one operational CSV. `--delimiter` accepts comma (default), semicolon, tab, or pipe, so Spanish and Latin American spreadsheet exports work without changing the default. `--encoding` defaults to utf-8 and accepts `cp1252` or `latin-1` for Windows Excel. A UTF-8 BOM is stripped, including on stdin. `N/D`, `s.d.`, and `N.D.` count as missing. A path of `-` reads from stdin. `--key order_id,line_id` supports composite business keys while preserving the original single-column behavior. `--min-rows N` can fail undersized operational extracts without changing the default zero-row behavior. `--top` can lower the group limit. A negative `--top` exits `2`. It complements csv-quality-report when the question is operational completeness rather than full profiling.

See [docs/related.md](https://github.com/rodrix91/csv-quality-report/blob/main/docs/related.md) in the flagship repository for how the tools fit together.

Package version: 0.3.0 with additional Unreleased work; a public GitHub release is still pending in [issue #16](https://github.com/rodrix91/ops-field-brief/issues/16). The repository now exposes a reusable composite GitHub Action for operational CSV gates. CI runs **97 tests** on Python 3.10 through 3.13 on Ubuntu, plus Python 3.10 and 3.13 on Windows and macOS; a dedicated quality job enforces **100% line and branch coverage** and requires Ruff lint/format plus mypy, while packaging and Action jobs validate the installed CLI and workflow integration end to end. Composite `--key` values use the full field tuple, header-only CSVs retain their column names for key/group validation, `--strict-csv` rejects duplicate or blank headers and ragged rows when explicitly enabled, and `--max-group-share` can fail an extract when one buyer, supplier, carrier, or other group exceeds an allowed share of rows. The scheduled autonomous audit is local-only; an optional external assessment requires both an explicit `--allow-external-api` flag and an API key. `--delimiter auto` detects comma, semicolon, tab, or pipe, and a tag-driven release workflow validates version tags and release artifacts before publication. The reusable Action now rejects absolute CSV paths, workspace traversal and escaping symlinks; unlike the CLI it does not accept stdin as an input path. See the [operations playbook](https://github.com/rodrix91/ops-field-brief/blob/main/docs/README.md) for reproducible quality gates and safe CI configuration. Not a production pipeline.

### [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab)

The [non-finite settings validation fix (#57)](https://github.com/rodrix91/inventory-policy-lab/pull/57) rejects `NaN` and infinite lead times, EOQ inputs, annualization factors and ABC-XYZ thresholds that could otherwise distort forecasts or reorder policies. Previously saved report files remain intact when configuration fails. The expanded suite contains 473 tests with 100% line and branch coverage.

The [CSV-to-Markdown SKU safety fix (#56)](https://github.com/rodrix91/inventory-policy-lab/pull/56) displays ERP identifiers literally in policy, backtest, out-of-sample replay, cost and notes sections, preventing CSV data from creating misleading table cells or links. The original JSON identifiers and inventory computations remain intact. The [PR workflow](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40137345720) passed 447 tests, strict mypy/Ruff and all 9 CI jobs with 100% line/branch coverage.

The [GitHub Action fail-closed fix](https://github.com/rodrix91/inventory-policy-lab/pull/55) blocks help/version commands and abbreviated output overrides that might otherwise report success without an inventory analysis. [CI evidence](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40133976558): 444 tests, 100% coverage, nine passing jobs across operating systems.

**Start with the [17-decision engineering index](https://github.com/rodrix91/inventory-policy-lab/blob/main/docs/README.md)** to see how forecasts, stock policies, validation, and cost tradeoffs fit together. The reusable GitHub Action now restricts CSV input paths to the caller's workspace, complementing its existing output-path safeguards.

A Python toolkit and CLI that turns a per-SKU demand history into an inventory policy: ABC classification by annual value, XYZ classification by demand variability, Syntetos-Boylan demand patterns (smooth, erratic, intermittent, lumpy), forecasting with naive, moving average, SES, Croston and SBA (plus damped Holt and Holt-Winters with `--trend-seasonal`) chosen per SKU by backtested MASE, safety stock and reorder points from demand and lead-time variability (normal formula or `--safety-stock bootstrap` seeded per SKU), EOQ, and a historical replay of the resulting (s, Q) policy, or of a periodic-review, order-up-to (R, S) policy with `--policy RS`, that reports fill rate, stockouts, average stock and backorders, with an out-of-sample replay (`--test-periods N`) that fits on the earlier periods and scores the last N. Markdown or JSON output, a reproducible synthetic dataset, a hand-checked worked example, and the formulas and their limits documented in the README.

Status: 0.10.0 (alpha). **473 tests**, 100% line and branch coverage, Ruff, strict mypy, GitHub citation metadata through `CITATION.cff`, a reusable composite GitHub Action for inventory-policy reports, and CI on Python 3.11 through 3.13 on Linux, with Python 3.11 and 3.13 also validated on Windows and macOS. Report-file writes are atomic: a failed write or replacement preserves the previous complete report, with regression coverage for replacement and `fsync` failures. When the normal-demand assumption is weak for lumpy SKUs, `--safety-stock bootstrap` resamples protection-interval demand from each SKU's history (ADR 0004). Trend and seasonal models are opt-in: on the 24-month synthetic example they do not change the out-of-sample results, because Holt-Winters needs two full seasons of training data (ADR 0006). With `--dynamic-levels` the order-up-to level follows the seasonal forecast month by month instead of one level for the year: on a 48-month synthetic series, out of sample, (R, S) with dynamic levels reached 100% fill rate with 105.5 units of average stock, against 99.6% and 289.0 for the static (s, Q); the bootstrap safety stock did worse with (R, S), and on the 24-month example the dynamic levels change nothing (ADR 0007). `--bootstrap-source residuals` bootstraps the rolling-origin forecast errors over the protection interval instead of demand, with an optional safety stock per period: on the 48-month series it raised the bootstrap's out-of-sample fill rate under (R, S) from 89.3% to 95.4% (96.3% per period), still below the normal formula's 100%, and on the 24-month example it did worse, so it stays opt-in (ADR 0008). `--rolling-origin` adds a replay of the test window that refits forecast, safety stock and levels at the start of every test period from the periods before it only: on the 24-month example it raised the out-of-sample fill rate of (s, Q) from 94.4% to 99.8% with about 5% more stock, while on the 48-month series it mostly bought stock (the normal (R, S) stayed at 100% with 42% more), so it is reported next to the fixed-origin replay, not instead of it (ADR 0009). Since 0.7.0 grid fits are cached and all prefixes of a history are scored in one pass, with byte-identical reports, so that run takes 0.22 s instead of 10.1 s (ADR 0010), and `--refit-every K` refits only every K test periods: on these two datasets the fill rate never rose with K, and on the 48-month series the normal (R, S) kept 100% while stock fell from 149.3 (monthly) to 105.5 (yearly) (ADR 0011). Since 0.8.0 `--order-cost`, `--holding-cost` and `--stockout-cost` price every out-of-sample replay without changing the policy (ADR 0012), and `--policy RsS` orders up to S = s + Q only when the position falls to s (ADR 0013). With example rates of 50 per order, 1 per unit-month and 10 per unit short, (R, S) with a monthly review was cheapest on the 48-month series, where it already served 100%, while on the 24-month example, where frozen forecasts left (R, S) at 90.9% fill rate, (R, s, S) reached 99.3% and was cheapest with a fixed origin; a three-month review was never cheapest at those rates. The ranking depends on the stockout cost, and the README gives the break-even points. Since 0.9.0 holding can be priced as a yearly share of each SKU's unit cost (`--holding-cost-rate`) and order and stockout costs read per SKU from optional columns (`--cost-columns`) (ADR 0014); at 25% a year of unit cost, (R, s, S) with a monthly review became the cheapest policy on the 24-month example. `--optimize-cost` searches each SKU's safety stock and order quantity (s and S = s + Q) for the lowest expected cost on demand paths built from the training periods only, then scores the pick out of sample (ADR 0015): it promised cost cuts of a third or more on training paths but beat both heuristics out of sample in only one of four cases and always lowered the fill rate, so it is documented as a diagnostic of overfitting, and (R, S) at a 0.98 service level was cheapest on the 48-month series.

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
- [ProgrammingAssignment2](https://github.com/rodrix91/ProgrammingAssignment2) (preserved R Programming assignment, now with an implemented matrix-inverse cache and [passing Linux, Windows and macOS regression checks](https://github.com/rodrix91/ProgrammingAssignment2/actions/runs/40122011625))
- [datasharing](https://github.com/rodrix91/datasharing) (data-sharing guide fork)

## Contact

[LinkedIn](https://www.linkedin.com/in/rodrigo-p-625862153)
