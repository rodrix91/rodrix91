# Rodrigo Pantoja Navajas

I build practical Python tools focused on **data quality, automation, reproducibility, and clear technical communication**.

**New to this portfolio?** [Start with the five-minute reviewer guide](docs/portfolio-review-guide.md) for reproducible examples, business questions and limitations.

## Portfolio at a glance

| Project | Purpose | Engineering signal |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | Deep CSV profiling, strict baseline rate checks and pipeline quality gates | 1,741 tests, 100% line/branch coverage, strict typing, PEP 561, CITATION.cff, cross-platform CI |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | Operational completeness, proportional key integrity and counterparty checks | 251 tests, 100% coverage, gzip CSV, reusable GitHub Action, hashed CI tooling, PEP 561 |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | Inventory policy, bounded replay, stable EOQ and forecasting for supply-chain decisions | 906 tests, 100% coverage, gzip and legacy-encoded CSV, reusable GitHub Action, CITATION.cff |

The three projects are intentionally complementary: profile data quality, validate operational extracts, then model inventory decisions. All three publish `CITATION.cff` metadata for reproducible citation.

**[Explore a reproducible supply-chain case study](docs/portfolio-case-study.md)** — three independent synthetic demos, the business questions they answer, and their verified engineering evidence. The examples do not imply a deployed customer integration.

**Pending public releases** (do not tag current main):  
- csv-quality-report v0.22.0 is ready at commit `8cd1d39d80426f985995ca2bfd0b23d06d8e23cc` (tracked in [issue #163](https://github.com/rodrix91/csv-quality-report/issues/163)).  
- ops-field-brief v0.3.0 is ready at commit `98e96160fc965bb382aca17301fb37da2ccec89f` (tracked in [issue #16](https://github.com/rodrix91/ops-field-brief/issues/16)).  

Across all three active projects, GitHub Actions dependencies are pinned by commit SHA, release artifacts include SHA-256 checksums, and current release workflows generate GitHub/Sigstore provenance attestations for wheels and source distributions.

## Detailed project snapshot

Three small standard-library Python tools for CSV and operations work:

- **csv-quality-report**: full profiling (types, locales, ranges, quality gates, baseline drift checks, freshness and allowed-value gates). Status: prototype / alpha; `main` is 0.22.0 with additional Unreleased work, while v0.21.0 remains the latest published release.
- **ops-field-brief**: operational completeness (fill rate, repeated keys, top groups, duplicate and row-count gates, plus opt-in case-insensitive duplicate identifiers, group concentration, minimum distinct groups, and maximum missing-group share gates). Package version: 0.3.0 with additional Unreleased work; the first public GitHub release is still pending and tracked in [issue #16](https://github.com/rodrix91/ops-field-brief/issues/16). It reads gzip-compressed `.gz` CSV exports directly, supports automatic detection of comma, semicolon, tab, or pipe, `--version`, stdin and common spreadsheet encodings; it also exposes a reusable composite GitHub Action with `exit-code` and `passed` outputs. The latest validated CI runs 251 tests on Python 3.10 through 3.13 on Ubuntu, plus Python 3.10 and 3.13 on Windows and macOS, smoke-tests the built wheel in a clean environment, tests the Action end to end, verifies the installed PEP 561 marker, enforces 100% line and branch coverage, and runs Ruff plus mypy.
- **inventory-policy-lab**: per-SKU inventory policy from demand history (ABC-XYZ, Syntetos-Boylan patterns, MASE-selected forecasts with opt-in damped Holt and Holt-Winters, normal or bootstrap safety stock, EOQ, and `(s, Q)` or periodic-review `(R, S)` policy replay in and out of sample, with levels that can follow a seasonal forecast, an opt-in bootstrap of forecast residuals, an opt-in rolling-origin replay that refits the policy every test period or every K periods with `--refit-every`, an opt-in periodic-review `(R, s, S)` policy, order, holding and stockout costs that price each out-of-sample replay, per SKU if needed, and an opt-in search of levels for cost, with an optional fill-rate floor and demand paths that refit the forecast on bootstrapped histories). Status: alpha (0.10.0). It accepts gzip-compressed `.csv.gz` demand histories directly without temporary extraction, plus explicitly encoded Excel/ERP CSV exports such as cp1252 and UTF-16.

## Featured project

### [csv-quality-report](https://github.com/rodrix91/csv-quality-report)

The [GitHub Action JSON accounting safeguard (#219)](https://github.com/rodrix91/csv-quality-report/pull/219) now rejects reports with inconsistent header counts, invalid or duplicated selected-column identities, and impossible duplicate-row totals before publishing a supposedly successful artifact. It retains valid full and `--columns` profiles without changing their JSON schema. The [exact-head CI run](https://github.com/rodrix91/csv-quality-report/actions/runs/40446427550) passed **1,741 tests**, **100% line and branch coverage**, Ruff, strict mypy, and **9/9** Linux/Windows/macOS, package and Action jobs. Earlier engineering milestones remain intact below.
