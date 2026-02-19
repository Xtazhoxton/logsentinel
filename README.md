# LogSentinel

> A log analysis and monitoring tool — built progressively in Python.

LogSentinel reads, parses, filters, and displays logs from various sources. Built phase by phase, starting from a simple CLI tool and evolving toward a full-stack application with machine learning capabilities.

---

## Project Phases

| Phase | Version | Status | Description |
|-------|---------|--------|-------------|
| POC | v0.1 | 🔵 In progress | CLI tool — parse AWS CloudWatch JSON logs from a local file |
| CLI Extended | v0.2 | ⬜ Planned | Multiple log formats, live file tailing, CSV/JSON export |
| API Backend | v1.0 | ⬜ Planned | REST API with FastAPI, persistent storage, query endpoints |
| Web UI | v2.0 | ⬜ Planned | Django-based web interface |
| ML Parsing | v3.0 | ⬜ Planned | Automatic log format detection and ML-powered field extraction |

**Future input sources to evaluate** (not yet scoped — revisit at the start of each phase): stdin/pipe, remote SSH, S3 buckets, live CloudWatch Logs API streaming.

---

## Documentation

- [v0.1 POC — Specification & Tasks](docs/v0.1/README.md)
- [TypeScript → Python Cheat Sheet](docs/cheatsheet.md)

---

## Tech Stack

| Layer | Library | Why |
|-------|---------|-----|
| Dependency management | [Poetry](https://python-poetry.org/) | Modern replacement for pip + virtualenv |
| CLI framework | [Typer](https://typer.tiangolo.com/) | Type-hint-driven CLI, built on Click |
| Terminal output | [Rich](https://rich.readthedocs.io/) | Tables, colors, formatted output |
| Testing | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) | Standard Python testing + coverage |

---

## Setup

### Prerequisites

- Python 3.13+ → https://www.python.org/downloads/
- Poetry → see below
- Git → https://git-scm.com/

### What is Poetry and why use it?

Poetry is Python's modern dependency and packaging manager. It solves two problems at once: it manages your project's dependencies (like npm) and automatically creates and manages a virtual environment per project (like nvm). The single source of truth is `pyproject.toml`, which replaces `requirements.txt`, `setup.py`, and `setup.cfg`.

Key concepts to understand before installing:

- **`pyproject.toml`** — the single config file for the whole project (equivalent to `package.json`)
- **`poetry.lock`** — auto-generated lockfile, always commit this (equivalent to `package-lock.json`)
- **Virtual environment** — Poetry creates one per project automatically; prefix commands with `poetry run` instead of activating it manually
- **Dependency groups** — separates production deps from dev deps (test tools, linters)

Resources:
- What is Poetry: https://python-poetry.org/docs/
- Installation: https://python-poetry.org/docs/#installation
- Basic usage (init, add, run): https://python-poetry.org/docs/basic-usage/
- Managing dependency groups: https://python-poetry.org/docs/managing-dependencies/

### Running the project

```bash
poetry run logsentinel --help
poetry run logsentinel parse path/to/logfile.json
poetry run pytest
```

---

## Architecture

### Package Structure

The project uses a **`src/` layout** — the main package lives in `src/logsentinel/`, not at the root. This prevents test runs from accidentally importing local source instead of the installed package.

```
logsentinel/
├── src/
│   └── logsentinel/
│       ├── models/       — data structures only
│       ├── parsers/      — raw input → list[LogEntry]
│       ├── filters/      — list[LogEntry] → filtered list[LogEntry]
│       ├── formatters/   — list[LogEntry] → output (table, JSON, etc.)
│       ├── cli/          — argument wiring only
│       └── utils/        — pure shared helpers
└── tests/
    ├── unit/             — mirrors src/ structure
    ├── integration/      — full CLI command tests
    └── fixtures/         — static sample log files
```

### Module Responsibilities

| Module | Responsibility | Must NOT contain |
|--------|---------------|-----------------|
| `models/` | Data structures (`LogEntry`, `LogLevel`) | Parsing logic, I/O, CLI |
| `parsers/` | Convert raw input → `list[LogEntry]` | CLI logic, formatting |
| `filters/` | Filter `list[LogEntry]` | Parsing, formatting, CLI |
| `formatters/` | Render `list[LogEntry]` to output | Parsing, filtering, I/O |
| `cli/` | Wire CLI args → parser → filters → formatter | Business logic |
| `utils/` | Pure shared helpers (no side effects) | State, I/O, CLI |

**Dependency direction**: `cli` → `parsers`, `filters`, `formatters` → `models`. Nothing in `models/` imports from elsewhere in the package.

**Adding a new log format**: add a new file in `parsers/` — never modify existing parsers.

### Testing Rules

- Every module has a corresponding test file: `src/logsentinel/parsers/cloudwatch.py` → `tests/unit/test_cloudwatch_parser.py`
- Every CLI command has at least one integration test in `tests/integration/`
- No test touches the filesystem directly — use pytest's `tmp_path` fixture or `tests/fixtures/` for static files
- Coverage must stay ≥ 80%

---

## README Rules

As the project grows, documentation is split across multiple files:

- **`README.md`** (this file) — project overview, roadmap, setup, architecture. Always up to date.
- **`docs/v{X.Y}/README.md`** — version-specific spec and task list. Created at the start of a version, updated throughout, finalized when the version is complete.
- **`docs/cheatsheet.md`** — TypeScript → Python concept map. Grows over time.

Rules:
1. No duplicate content between files — root README links to version READMEs, never copies them.
2. Root README roadmap table is updated when a version changes status.
3. Version READMEs contain the live task list for that version — statuses are updated directly in that file.
