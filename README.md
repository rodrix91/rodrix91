# Rodrigo Pantoja Navajas

I build practical Python tools focused on **data quality, automation, reproducibility, and clear technical communication**.

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
- quality gates for pipelines: `--max-missing`, `--max-duplicates`, required types and value ranges (`--range Peso=0:`) stop a bad extract with a dedicated exit code
- reads from pipes (`-`) and gzip-compressed files transparently, and can be used as a Python library
- flags mixed currencies or units in a column (pesos and dollars, kg and lb) instead of silently averaging them
- available as a GitHub Action: the report goes to the job summary and a failed check fails the job
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

> Status: prototype / alpha. The project is intentionally small and focused while I continue improving reliability, usability, documentation, and release readiness.

### [ops-field-brief](https://github.com/rodrix91/ops-field-brief)

A small standard-library Python CLI that reports fill rate, repeated business keys, and top groups for one operational CSV. It complements csv-quality-report when the question is operational completeness rather than full profiling.

See [docs/related.md](https://github.com/rodrix91/csv-quality-report/blob/main/docs/related.md) in the flagship repository for how the two tools fit together.

Status: 0.1.0. Local unit tests passed before publish. Not a production pipeline.

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

## Archived coursework

These repositories preserve early coursework and are not current product work:

- [datasciencecoursera](https://github.com/rodrix91/datasciencecoursera) (2020 Coursera R archive)
- [ProgrammingAssignment2](https://github.com/rodrix91/ProgrammingAssignment2) (R Programming assignment fork)
- [datasharing](https://github.com/rodrix91/datasharing) (data-sharing guide fork)

## Contact

[LinkedIn](https://www.linkedin.com/in/rodrigo-p-625862153)
