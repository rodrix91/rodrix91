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
- decimal commas (`10,5`) from Spanish, Portuguese and other comma-decimal locales
- spreadsheet exports in cp1252, Latin-1 or UTF-16 with `--encoding`, and very long text fields
- single-pass streaming: on a 1,000,000-row file, peak memory went from 873 MB to 234 MB with identical output
- quality gates for pipelines: `--max-missing` and `--max-duplicates` stop a bad extract with a dedicated exit code
- reads from pipes (`-`) and gzip-compressed files transparently, and can be used as a Python library
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
- design decisions recorded as ADRs, and a maintained CHANGELOG

> Status: prototype / alpha. The project is intentionally small and focused while I continue improving reliability, usability, documentation, and release readiness.

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

## Contact

[LinkedIn](https://www.linkedin.com/in/rodrigo-p-625862153)
