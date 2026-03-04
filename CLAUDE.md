# CLAUDE.md — logsentinel-cli

For project-level guidance (role, architecture, task workflow, roadmap), see `../CLAUDE.md`.

---

## This Repository

CLI tool and infrastructure deploy command for LogSentinel.

**GitHub**: https://github.com/Xtazhoxton/logsentinel
**Branch convention**: `feature/T{id}-short-description`

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.13 | Language |
| Poetry | Dependency management + virtual env |
| Typer | CLI framework (type-hint driven, built on Click) |
| Rich | Terminal output (tables, colors) |
| pytest + pytest-cov | Testing + coverage |
| ruff | Linting + formatting (replaces flake8 + black + isort) |
| mypy | Static type checking |
| moto | AWS service mocking for unit tests |

## Package Structure

```
logsentinel-cli/
├── src/
│   └── logsentinel/
│       ├── models/       — data structures only (LogEntry, LogLevel)
│       ├── parsers/      — raw input → list[LogEntry]
│       ├── filters/      — list[LogEntry] → filtered list
│       ├── formatters/   — list[LogEntry] → output
│       ├── cli/          — argument wiring only
│       ├── api/          — API handlers (Lambda functions, v0.3+)
│       ├── infra/        — CloudFormation stack + deploy logic
│       └── utils/        — pure shared helpers
└── tests/
    ├── unit/             — mirrors src/ structure
    ├── integration/      — full CLI command tests
    └── fixtures/         — static sample log files
```

## Testing Rules

- Every module has a corresponding test file
- Every CLI command has at least one integration test
- No test touches the filesystem directly — use `tmp_path` or `tests/fixtures/`
- Coverage must stay ≥ 80%

## Common Commands

```bash
poetry run logsentinel --help
poetry run pytest
poetry run pytest --cov=logsentinel --cov-report=term-missing
poetry run ruff check src/
poetry run mypy src/
```
