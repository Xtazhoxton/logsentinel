# LogSentinel

> Stop searching through logs. Start reading what happened.

LogSentinel transforms raw, fragmented log streams into **readable execution narratives**. It groups events that belong to the same workflow, reconstructs what happened step by step, and surfaces failures without requiring you to know what to search for.

Built for event-driven architectures (AWS Step Functions, Lambda, EventBridge) where a single user action generates dozens of correlated log entries spread across multiple log groups. Built progressively in Python as a learning project, from CLI tool to ML-powered platform.

---

## Project Phases

| Phase | Version | Status | What it solves |
|-------|---------|--------|----------------|
| POC | v0.1 | 🔵 In progress | Parse CloudWatch logs locally, filter by level/keyword, display in a readable table. Lay the domain model foundation (`LogEntry` with `correlation_id`). |
| Correlation | v0.2 | ⬜ Planned | Group log entries into `Trace` objects by workflow execution. Reconstruct Step Functions timelines. View an entire workflow as a single readable narrative. |
| Intelligence | v0.3 | ⬜ Planned | Extract log templates automatically (Drain algorithm). Detect statistical anomalies. Alert on patterns that precede failures — no external ML services, no LLMs. |
| Platform | v1.0 | ⬜ Planned | REST API (FastAPI), real-time log ingestion, persistent storage. LogSentinel becomes a service, not just a CLI. |
| Web UI | v2.0 | ⬜ Planned | Dashboard, visual workflow timelines, incident history. |
| ML | v3.0 | ⬜ Planned | Automatic format detection for unknown log sources. Sequence anomaly detection (what execution path is abnormal?). Root cause suggestions. All built with Python ML libraries, no external APIs. |

**Future input sources** (not yet scoped — revisit at the start of each phase): stdin/pipe, S3 buckets, live CloudWatch Logs API streaming, remote SSH.

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
| Linting + formatting | [ruff](https://docs.astral.sh/ruff/) | Fast linter + formatter (replaces flake8 + black + isort) |
| Type checking | [mypy](https://mypy.readthedocs.io/) | Static type checker, enforces type hints at development time |

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

### Core Domain Concepts

| Concept | Description | Introduced |
|---------|-------------|-----------|
| `LogEntry` | A single log event. Has a `correlation_id` field from the start to support grouping. | v0.1 |
| `Trace` | A group of `LogEntry` objects belonging to the same workflow execution (same Step Functions `executionId`, same request, etc.). The primary unit of analysis. | v0.2 |
| `LogPattern` | A template extracted from a family of similar messages, e.g. `"Connection to {IP} failed after {N} retries"`. Enables anomaly detection at the pattern level. | v0.3 |
| `Anomaly` | A `LogEntry` or `Trace` that deviates statistically from known patterns. | v0.3 |

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

**Parser protocol**: `parsers/base.py` defines a `Parser` protocol (structural interface) that all parsers implement. The CLI depends on `Parser`, not on `CloudWatchParser` — adding a new format means adding a new file, not modifying existing code.

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
