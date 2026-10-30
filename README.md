# Rodrigo Pantoja Navajas

I build practical Python tools focused on **data quality, automation, reproducibility, and clear technical communication**.

[![CSV quality CI](https://github.com/rodrix91/csv-quality-report/actions/workflows/ci.yml/badge.svg)](https://github.com/rodrix91/csv-quality-report/actions/workflows/ci.yml)
[![Operations CI](https://github.com/rodrix91/ops-field-brief/actions/workflows/ci.yml/badge.svg)](https://github.com/rodrix91/ops-field-brief/actions/workflows/ci.yml)
[![Inventory CI](https://github.com/rodrix91/inventory-policy-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/rodrix91/inventory-policy-lab/actions/workflows/ci.yml)
[![Profile documentation CI](https://github.com/rodrix91/rodrix91/actions/workflows/docs.yml/badge.svg)](https://github.com/rodrix91/rodrix91/actions/workflows/docs.yml)
[![Synthetic portfolio demos](https://github.com/rodrix91/rodrix91/actions/workflows/portfolio-demos.yml/badge.svg)](https://github.com/rodrix91/rodrix91/actions/workflows/portfolio-demos.yml)

**Reproducible CLI demonstrations:** [Three independent, pinned synthetic examples with automated checks](docs/portfolio-smoke-checks.md), including explicit UTF-8 subprocess output on Linux, Windows and macOS.

**New to this portfolio?** [Start with the five-minute reviewer guide](docs/portfolio-review-guide.md) for reproducible examples, business questions and limitations. **¿Prefieres español?** [Consulta la guía de evaluación en español](docs/guia-portafolio-es.md), con comandos, resultados previstos y límites documentados.

## Portfolio at a glance

| Project | Purpose | Engineering signal |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | Deep CSV profiling, strict baseline rate checks and pipeline quality gates | 1,842 tests, 100% line/branch coverage, clean-wheel CLI tested on Linux/Windows/macOS, one-shot generator-safe missing markers, NFC-safe opt-in case-insensitive missing markers for Spanish-language exports, duplicate and non-finite historical JSON safeguards, strict ISO hours including Python 3.14, malformed-quote rejection, Excel `sep=` metadata checks, CR-only CSV support, PEP 561, cross-platform CI |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | Operational completeness, proportional key integrity and counterparty checks | 313 tests, 100% coverage, bounded strict CSV delimiter sniff, fail-closed ambiguous delimiter detection, installed wheel and CLI smoke-tested on Linux/Windows/macOS, NFC-safe opt-in key/group/header checks, explicit/auto stdin CR-only CSV and precise multiline error lines, executable Excel sep= sample, gzip CSV, safe Unicode Markdown, reusable GitHub Action, hashed CI tooling, PEP 561 |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | Inventory policy, bounded replay, stable EOQ and forecasting for supply-chain decisions | 1,178 tests, 100% coverage, clean-wheel CLI verified on Linux/Windows/macOS, overflow-safe forecast means, validated backtest actuals and custom predictions, finite scalar/dynamic inventory replay levels, validated bootstrap demand and forecast-residual inputs, strict naive/moving-average/SES/Croston/SBA and coefficient-of-variation demand validation, Unicode-safe ERP headers and validated monthly calendar years, accurate multiline CSV error locations, runnable Excel `sep=` demo, regional CSV separators, gzip and legacy-encoded CSV, reusable GitHub Action, CITATION.cff |

## Latest verified engineering results (29 October 2026, Bolivia time)

These are **CI-verified snapshots**, not estimates of stars, downloads, adoption, or
production deployments. The historical milestones and reproducible case studies
remain documented below.

Python **3.14 is now explicitly listed in the package metadata** of all three projects, after passing their Linux, Windows and macOS test matrices. Python 3.10 remains supported by `ops-field-brief`; the other two projects require Python 3.11 or newer. These are tested compatibility claims, not claims of deployment or adoption.

| Repository | Verified evidence | Recent improvement |
|---|---|---|
| [csv-quality-report](https://github.com/rodrix91/csv-quality-report) | [1,842 tests, 100% line/branch coverage and 15/15 exact-head PR CI jobs passed](https://github.com/rodrix91/csv-quality-report/actions/runs/40998191268) | [Merged PR #234](https://github.com/rodrix91/csv-quality-report/pull/234) preserves one-shot missing-token iterators across streaming, in-memory and key profiling; [PR #233](https://github.com/rodrix91/csv-quality-report/pull/233) adds Unicode NFC-equivalent missing markers; [PR #232](https://github.com/rodrix91/csv-quality-report/pull/232) introduced case-insensitive markers |
| [ops-field-brief](https://github.com/rodrix91/ops-field-brief) | [313 tests, 100% line/branch coverage, and 17/17 exact-head PR CI jobs passed](https://github.com/rodrix91/ops-field-brief/actions/runs/40991061896) | [Merged PR #116](https://github.com/rodrix91/ops-field-brief/pull/116) bounds strict automatic delimiter sniffing on long CSV records; [PR #114](https://github.com/rodrix91/ops-field-brief/pull/114) rejects ambiguous delimiters; [PR #113](https://github.com/rodrix91/ops-field-brief/pull/113) verifies installed wheels on three OS |
| [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab) | [1,178 tests, 100% line/branch coverage and 15/15 exact-head PR CI jobs passed](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40997239456) | [Merged PR #113](https://github.com/rodrix91/inventory-policy-lab/pull/113) validates finite forecast residuals across reachable bootstrap intervals before sampling; [PR #112](https://github.com/rodrix91/inventory-policy-lab/pull/112) rejects corrupt bootstrap demand; [PR #111](https://github.com/rodrix91/inventory-policy-lab/pull/111) validates finite replay levels |

All three projects are **alpha-stage reference implementations**, not claims of
enterprise deployments or real customer outcomes. Reproducible synthetic examples
and documented caveats are available in the reviewer guide and case study.

The three projects are intentionally complementary: profile data quality, validate operational extracts, then model inventory decisions. All three publish `CITATION.cff` metadata for reproducible citation.

**[Explore a reproducible supply-chain case study](docs/portfolio-case-study.md)** — three independent synthetic demos, the business questions they answer, and their verified engineering evidence. The examples do not imply a deployed customer integration.

Across all three active projects, GitHub Actions dependencies are pinned by commit SHA. Current release workflows are configured to produce SHA-256 checksums and GitHub/Sigstore provenance attestations for new wheel and source-distribution releases; these guarantees are not retroactive to older releases. `ops-field-brief` has not yet published its first GitHub release (tracked in [issue #16](https://github.com/rodrix91/ops-field-brief/issues/16)).

## Explore my projects

### [csv-quality-report](https://github.com/rodrix91/csv-quality-report)
**Data quality and validation.** Profile CSV exports, check field types and missingness, validate business rules, reject ambiguous historical JSON baselines and fail pipelines when a documented quality gate is breached. Includes strict datetime validation and an opt-in GitHub Action.

[Source and quickstart](https://github.com/rodrix91/csv-quality-report) · [Verified CI](https://github.com/rodrix91/csv-quality-report/actions/runs/40998191268)

### [ops-field-brief](https://github.com/rodrix91/ops-field-brief)
**Operational data integrity.** Summarize required-field completeness, duplicate business keys, and counterparty concentration for business exports. Handles common Excel separators, gzip CSV and legacy line endings, with a reusable CI Action.

[Source and quickstart](https://github.com/rodrix91/ops-field-brief) · [Verified CI](https://github.com/rodrix91/ops-field-brief/actions/runs/40991061896)

### [inventory-policy-lab](https://github.com/rodrix91/inventory-policy-lab)
**Inventory analytics and decisions.** Explore demand classification, forecast backtests, reorder levels, safety stock, EOQ, and policy replay with explicit assumptions and out-of-sample evaluation. Uses reproducible synthetic examples; no customer deployments are claimed.

[Source and quickstart](https://github.com/rodrix91/inventory-policy-lab) · [Verified CI](https://github.com/rodrix91/inventory-policy-lab/actions/runs/40997239456)

For deeper technical decisions, limitations, formulas, regression evidence, and past milestones, read the **[complete engineering history](docs/engineering-history.md)**. For a fast hands-on evaluation, start with the [five-minute reviewer guide](docs/portfolio-review-guide.md) or its [Spanish version](docs/guia-portafolio-es.md).

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
- [datasharing](https://github.com/rodrix91/datasharing) (preserved third-party guide with an independent synthetic data handoff companion: [SHA-256 provenance, strict quoted-CSV validation and accurate source-line diagnostics](https://github.com/rodrix91/datasharing/pull/5); [14 tests and 3/3 Linux/macOS/Windows checks on `master`](https://github.com/rodrix91/datasharing/actions/runs/40612876621))

## Contact

[LinkedIn](https://www.linkedin.com/in/rodrigo-p-625862153)
