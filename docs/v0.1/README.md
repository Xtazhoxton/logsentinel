# LogSentinel v0.1 — POC Specification

**Goal**: A CLI tool that reads a locally exported AWS CloudWatch JSON log file, parses it into structured entries, and displays them in a formatted terminal table with optional level and keyword filtering.

**Input**: Local `.json` file exported from AWS CloudWatch
**Output**: Formatted terminal table (Rich)
**Interface**: `logsentinel parse <file> [--level LEVEL] [--search KEYWORD]`

---

## Learning Outcomes

By the end of v0.1 you will know how to:

- Manage a Python project with Poetry (dependencies, virtual envs, scripts)
- Structure a Python package using the `src/` layout
- Use type hints, dataclasses, and enums from the standard library
- Parse JSON and work with files using `pathlib`
- Use regular expressions for pattern extraction
- Build a typed CLI with Typer
- Format terminal output with Rich tables
- Write unit and integration tests with pytest
- Measure and enforce code coverage
- Set up a CI pipeline with GitHub Actions

---

## AWS CloudWatch Log Format

CloudWatch logs exported to a JSON file look like this:

```json
{
  "logGroupName": "/aws/lambda/my-function",
  "logStreamName": "2024/01/15/[$LATEST]abc123",
  "logEvents": [
    {
      "id": "001",
      "timestamp": 1705312245123,
      "message": "START RequestId: req-001 Version: $LATEST"
    },
    {
      "id": "002",
      "timestamp": 1705312246000,
      "message": "[ERROR] 2024-01-15T10:31:00Z req-001 Database connection failed"
    }
  ]
}
```

Key things to understand:
- `timestamp` is Unix time in **milliseconds** (not seconds)
- Lambda log messages embed the level as `[LEVEL]` at the start
- Special Lambda messages (`START`, `END`, `REPORT`) have no level prefix
- `logGroupName` identifies the source (e.g. which Lambda function)

Official reference: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html

---

## Tasks

### EPIC-01: Project Foundation

---

#### T001 — Initialize Poetry Project
**Status**: [FAILED]
**Estimate**: 2 hours
**Branch**: `feature/T001-poetry-setup`

**What is Poetry?**
Poetry is Python's modern dependency and packaging manager. Think of it as npm + nvm combined: it manages dependencies and creates/manages a virtual environment automatically. The central file is `pyproject.toml` — it replaces `requirements.txt`, `setup.py`, and `setup.cfg`. Running `poetry add` is the equivalent of `npm install --save`.

TypeScript parallel: `package.json` → `pyproject.toml` / `node_modules/` → `.venv/` / `npm install` → `poetry install`

Resources:
- https://python-poetry.org/docs/#installation
- https://python-poetry.org/docs/basic-usage/
- https://python-poetry.org/docs/managing-dependencies/ (dependency groups section)

**What to do**
Initialize a new Poetry project named `logsentinel` targeting Python `^3.13`. Add `typer[all]` and `rich` as main dependencies. Add `pytest` and `pytest-cov` as a dev dependency group (not in main dependencies).

**Acceptance Criteria**
- [ ] `pyproject.toml` exists with `name = "logsentinel"`, `version = "0.1.0"`, `python = "^3.13"`
- [ ] `typer[all]` and `rich` are under `[tool.poetry.dependencies]`
- [ ] `pytest` and `pytest-cov` are under `[tool.poetry.group.dev.dependencies]`
- [ ] `poetry.lock` is committed
- [ ] `poetry run python --version` outputs Python 3.13.x
- [ ] `.gitignore` excludes `.venv/`, `__pycache__/`, `*.pyc`, `.coverage`, `dist/`
- [ ] `.venv/` is NOT committed

> **[FAILED]** — Three criteria fail:
> 1. `typer[all]` and `rich` are not under `[tool.poetry.dependencies]`. You used Poetry 2.x format (`[project]` table), which uses different section names than the ones the criteria require. The criteria were written for Poetry 1.x. You need to either reconcile with your Poetry version's actual format, or understand the difference — look up what changed between Poetry 1.x and 2.x, specifically around the `[project]` vs `[tool.poetry]` tables and `[dependency-groups]` vs `[tool.poetry.group.dev.dependencies]`.
> 2. Same issue for `pytest`/`pytest-cov`: they are in `[dependency-groups]`, not `[tool.poetry.group.dev.dependencies]`.
> 3. `.gitignore` has a typo on line 2: `__pychache__` → should be `__pycache__`. As written, `__pycache__` directories are **not** being ignored. This will lead to compiled bytecode getting committed.

---

#### T002 — Set Up Project Structure
**Status**: [TODO]
**Estimate**: 1 hour
**Branch**: `feature/T002-project-structure`
**Blocked by**: T001

**What is a Python package?**
In Python, a directory becomes a package when it contains an `__init__.py` file — this is the equivalent of an `index.ts` barrel file. The `src/` layout places your package inside `src/` so that test runs always use the installed version of your package rather than the raw files in your directory.

TypeScript parallel: `src/logsentinel/__init__.py` ≈ `src/index.ts`

Resources:
- https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- https://python-poetry.org/docs/pyproject/#packages

**What to do**
Create the full directory structure below. Update `pyproject.toml` to declare the `src/` layout.

```
src/
└── logsentinel/
    ├── __init__.py        ← expose __version__ = "0.1.0"
    ├── models/
    │   └── __init__.py
    ├── parsers/
    │   └── __init__.py
    ├── filters/
    │   └── __init__.py
    ├── formatters/
    │   └── __init__.py
    ├── cli/
    │   └── __init__.py
    └── utils/
        └── __init__.py
tests/
├── __init__.py
├── unit/
│   └── __init__.py
├── integration/
│   └── __init__.py
└── fixtures/
    └── .gitkeep
```

**Acceptance Criteria**
- [ ] All directories and `__init__.py` files exist as shown
- [ ] `src/logsentinel/__init__.py` contains `__version__ = "0.1.0"`
- [ ] `pyproject.toml` has `packages = [{include = "logsentinel", from = "src"}]`
- [ ] `poetry run python -c "import logsentinel; print(logsentinel.__version__)"` outputs `0.1.0`
- [ ] `tests/fixtures/` is committed (use `.gitkeep` to track the empty directory)

---

### EPIC-02: Core Domain Model

---

#### T003 — LogEntry and LogLevel Models
**Status**: [TODO]
**Estimate**: 3 hours
**Branch**: `feature/T003-log-entry-model`
**Blocked by**: T002

**What are dataclasses and Enums?**
Python's `dataclasses` module auto-generates `__init__`, `__repr__`, and `__eq__` from annotated fields — similar to a TypeScript interface but with real runtime behavior. `frozen=True` makes instances immutable like `Object.freeze()`. The `field(compare=False)` option excludes a field from equality checks.

Python's `Enum` works similarly to TypeScript's `enum` but with more flexibility — members can have arbitrary values (integers, strings) and you can iterate over them.

TypeScript parallel: `@dataclass` ≈ TypeScript class with auto-generated constructor / `Enum` ≈ TypeScript `enum`

Resources:
- https://docs.python.org/3/library/dataclasses.html — pay attention to `frozen`, `field`, `compare`
- https://docs.python.org/3/library/enum.html
- https://docs.python.org/3/library/datetime.html — read the section on "aware" vs "naive" datetime objects

**Interface to implement**

```python
# src/logsentinel/models/log_entry.py

class LogLevel(Enum):
    # Members: DEBUG, INFO, WARNING, ERROR, CRITICAL, UNKNOWN
    # Each member has an integer value representing severity for ordering
    # UNKNOWN should not participate in severity ordering

@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime      # must always be timezone-aware (UTC)
    level: LogLevel
    message: str
    source: str              # log group name or filename
    raw: str                 # original unparsed string — excluded from equality
    request_id: str | None   # AWS RequestId if present — excluded from equality
    metadata: dict           # extra key-value pairs — excluded from equality

    def is_error(self) -> bool: ...
```

**Acceptance Criteria**
- [ ] `LogLevel` is an `Enum` with `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `UNKNOWN`
- [ ] `LogLevel` members have integer values reflecting severity (`DEBUG` lowest, `CRITICAL` highest)
- [ ] `LogEntry` is a frozen dataclass
- [ ] `raw`, `request_id`, and `metadata` are excluded from `__eq__` comparisons
- [ ] `is_error()` returns `True` only for `ERROR` and `CRITICAL`
- [ ] `timestamp` is always a timezone-aware `datetime` — the model should make it impossible to create a `LogEntry` with a naive datetime (raise `ValueError`)
- [ ] Tests are in `tests/unit/test_log_entry.py`
- [ ] Tests cover: valid creation, equality ignores `raw`/`request_id`/`metadata`, `is_error()` for all 6 levels, naive datetime raises `ValueError`

---

### EPIC-03: Parser

---

#### T004 — AWS CloudWatch JSON Parser
**Status**: [TODO]
**Estimate**: 4 hours
**Branch**: `feature/T004-cloudwatch-parser`
**Blocked by**: T003

**File I/O and pathlib**
Python's `pathlib.Path` is the modern way to handle file paths — more readable than the old `os.path`. Always use a context manager (`with open(...) as f:`) to open files; it ensures the file is closed even if an error occurs. This is equivalent to wrapping `fs.readFileSync` in a try/finally in Node.

For timestamps: CloudWatch stores them as Unix **milliseconds**. `datetime.fromtimestamp()` works with seconds — divide by 1000. Always pass `tz=timezone.utc` to get a timezone-aware datetime.

Resources:
- https://docs.python.org/3/library/pathlib.html
- https://docs.python.org/3/library/json.html
- https://docs.python.org/3/library/re.html — you will need regex to extract `[LEVEL]` and `RequestId`

**Fixture to create**
Create `tests/fixtures/cloudwatch_sample.json` with this content (commit it):

```json
{
  "logGroupName": "/aws/lambda/my-function",
  "logStreamName": "2024/01/15/[$LATEST]abc123",
  "logEvents": [
    {"id": "001", "timestamp": 1705312245123, "message": "START RequestId: req-001 Version: $LATEST"},
    {"id": "002", "timestamp": 1705312246000, "message": "[ERROR] 2024-01-15T10:31:00Z req-001 Database connection failed"},
    {"id": "003", "timestamp": 1705312247000, "message": "[INFO] 2024-01-15T10:31:01Z req-001 Retrying connection..."},
    {"id": "004", "timestamp": 1705312248000, "message": "END RequestId: req-001"},
    {"id": "005", "timestamp": 1705312248500, "message": "REPORT RequestId: req-001 Duration: 3400.00 ms Billed Duration: 3400 ms Memory Size: 128 MB Max Memory Used: 89 MB"}
  ]
}
```

**Interface to implement**

```python
# src/logsentinel/parsers/cloudwatch.py

class CloudWatchParser:
    def parse_file(self, path: Path) -> list[LogEntry]: ...
    def parse_string(self, content: str) -> list[LogEntry]: ...
    def _parse_event(self, event: dict, source: str) -> LogEntry: ...
    def _extract_level(self, message: str) -> LogLevel: ...
    def _extract_request_id(self, message: str) -> str | None: ...
```

**Acceptance Criteria**
- [ ] `parse_file` returns a `list[LogEntry]` from the fixture file
- [ ] `parse_string` and `parse_file` return identical results for the same content
- [ ] Timestamps are UTC-aware `datetime` objects (correctly converted from milliseconds)
- [ ] `[ERROR]`, `[INFO]`, `[WARNING]`, `[DEBUG]`, `[CRITICAL]` are mapped to the correct `LogLevel`
- [ ] `START`, `END`, `REPORT` messages receive `LogLevel.UNKNOWN`
- [ ] `request_id` is extracted when `RequestId: <value>` appears in the message
- [ ] `source` is populated from `logGroupName`
- [ ] `parse_file` raises `FileNotFoundError` if the path does not exist
- [ ] `parse_file` raises `ValueError` with a descriptive message if `logEvents` key is missing
- [ ] `tests/fixtures/cloudwatch_sample.json` is committed
- [ ] Tests in `tests/unit/test_cloudwatch_parser.py` cover all criteria above, including edge cases: empty `logEvents` array, missing `logGroupName`

---

### EPIC-04: CLI Interface

---

#### T005 — CLI Skeleton with Typer
**Status**: [TODO]
**Estimate**: 3 hours
**Branch**: `feature/T005-cli-skeleton`
**Blocked by**: T002

**What is Typer?**
Typer builds CLIs from Python type hints — no need to declare argument types separately. It is built on top of Click (the de facto Python CLI standard) but feels more natural if you are used to TypeScript's type system. The `[all]` extra includes Rich integration for better help text and error formatting.

TypeScript parallel: Typer ≈ a typed `commander.js` where the types drive the argument parser automatically.

Resources:
- https://typer.tiangolo.com/tutorial/ — read "First Steps" through "Commands"
- https://typer.tiangolo.com/tutorial/options/
- Entry points in pyproject.toml: https://python-poetry.org/docs/pyproject/#scripts

**Command structure to implement** (no business logic yet — `parse` can print a placeholder)

```
logsentinel --help
logsentinel version
logsentinel parse <file> [--format cloudwatch] [--level LEVEL] [--search KEYWORD]
```

**Acceptance Criteria**
- [ ] `pyproject.toml` has `[tool.poetry.scripts]` with `logsentinel = "logsentinel.cli:app"`
- [ ] `poetry run logsentinel --help` shows app name, description, and available commands
- [ ] `poetry run logsentinel version` prints exactly `LogSentinel v0.1.0`
- [ ] `poetry run logsentinel parse --help` documents `file`, `--format`, `--level`, `--search`
- [ ] `--format` defaults to `cloudwatch`; an unrecognized format exits with code 1 and an error message
- [ ] `--level` accepts only `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (case-insensitive); invalid value exits with code 1
- [ ] `--search` is optional, accepts any string
- [ ] Passing a non-existent file exits with code 1 and a clear error message
- [ ] Tests use Typer's `CliRunner` (`from typer.testing import CliRunner`) and cover: version output, invalid file path, invalid format, invalid level value

---

#### T006 — Wire Parse Command to Parser and Formatter
**Status**: [TODO]
**Estimate**: 3 hours
**Branch**: `feature/T006-parse-command`
**Blocked by**: T004, T005

**What is Rich?**
Rich is a Python library for terminal formatting — tables, colors, progress bars, syntax highlighting. You already installed it via `typer[all]`. Think of it as `chalk` + `cli-table3` for Python but significantly more powerful.

Resources:
- https://rich.readthedocs.io/en/stable/tables.html
- https://rich.readthedocs.io/en/stable/style.html

**Interface to implement**

```python
# src/logsentinel/formatters/table.py

class TableFormatter:
    def format(self, entries: list[LogEntry]) -> Table: ...   # rich.table.Table
    def _level_style(self, level: LogLevel) -> str: ...       # returns a Rich style string
```

**Acceptance Criteria**
- [ ] `poetry run logsentinel parse tests/fixtures/cloudwatch_sample.json` renders a Rich table with all 5 entries
- [ ] Table columns: `Timestamp` (ISO 8601), `Level`, `Source`, `Message` (truncated at 80 chars with `…`)
- [ ] `ERROR`/`CRITICAL` rows styled red, `WARNING` yellow, `INFO` green, `DEBUG` blue, `UNKNOWN` dim
- [ ] An empty log file (0 events) prints `No log entries found.` instead of an empty table
- [ ] `TableFormatter` is unit tested with mock `LogEntry` objects
- [ ] Integration test in `tests/integration/test_parse_command.py` runs the CLI on the fixture and asserts exit code 0

---

### EPIC-05: Filtering & Search

---

#### T007 — Log Level Filter
**Status**: [TODO]
**Estimate**: 2 hours
**Branch**: `feature/T007-level-filter`
**Blocked by**: T006

**Interface to implement**

```python
# src/logsentinel/filters/level.py

class LevelFilter:
    def __init__(self, min_level: LogLevel): ...
    def apply(self, entries: list[LogEntry]) -> list[LogEntry]: ...
```

**Acceptance Criteria**
- [ ] `LevelFilter(LogLevel.WARNING).apply(entries)` returns `WARNING`, `ERROR`, and `CRITICAL` entries
- [ ] Severity order enforced: `DEBUG < INFO < WARNING < ERROR < CRITICAL`
- [ ] `UNKNOWN` entries are **always** included regardless of the min level
- [ ] Passing `--level WARNING` to the CLI activates this filter
- [ ] Unit tests cover all 5 levels as min_level, empty list input, and list of only `UNKNOWN` entries

---

#### T008 — Keyword Search Filter
**Status**: [TODO]
**Estimate**: 2 hours
**Branch**: `feature/T008-keyword-filter`
**Blocked by**: T006

**Interface to implement**

```python
# src/logsentinel/filters/search.py

class SearchFilter:
    def __init__(self, keyword: str, case_sensitive: bool = False): ...
    def apply(self, entries: list[LogEntry]) -> list[LogEntry]: ...
```

**Acceptance Criteria**
- [ ] Searches in both `message` and string values inside `metadata`
- [ ] Case-insensitive by default; `case_sensitive=True` enforces exact case
- [ ] Empty keyword string returns all entries unchanged
- [ ] `--search` CLI option activates this filter
- [ ] When both `--level` and `--search` are active, level filter runs first
- [ ] Unit tests cover: case-insensitive match, case-sensitive non-match, empty keyword, keyword in metadata, no match

---

### EPIC-06: Quality

---

#### T009 — Pytest Configuration and GitHub Actions CI
**Status**: [TODO]
**Estimate**: 2 hours
**Branch**: `feature/T009-ci`
**Blocked by**: T008

**What is pytest configuration and CI?**
`pytest` discovers and runs tests automatically. Its configuration goes in `pyproject.toml` under `[tool.pytest.ini_options]` — no separate `pytest.ini` needed. `pytest-cov` measures which lines of code are exercised by tests. GitHub Actions is a CI/CD platform that runs your tests automatically on every push, catching regressions before they reach the main branch.

Resources:
- https://docs.pytest.org/en/stable/reference/customize.html
- https://pytest-cov.readthedocs.io/en/latest/config.html
- https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python

**Acceptance Criteria**
- [ ] `[tool.pytest.ini_options]` is in `pyproject.toml` — no separate `pytest.ini`
- [ ] `testpaths`, `addopts` (with coverage flags), and `pythonpath = ["src"]` are configured
- [ ] `poetry run pytest` runs the full test suite and shows a coverage summary
- [ ] Total coverage is ≥ 80%
- [ ] `.github/workflows/ci.yml` triggers on push to any branch
- [ ] CI workflow: checkout → Python 3.13 → install Poetry → `poetry install` → `poetry run pytest`
- [ ] CI passes on the `main` branch

---

## Task Summary

| ID | Title | Status | Estimate |
|----|-------|--------|----------|
| T001 | Initialize Poetry Project | [FAILED] | 2h |
| T002 | Set Up Project Structure | [TODO] | 1h |
| T003 | LogEntry and LogLevel Models | [TODO] | 3h |
| T004 | AWS CloudWatch JSON Parser | [TODO] | 4h |
| T005 | CLI Skeleton with Typer | [TODO] | 3h |
| T006 | Wire Parse Command to Parser and Formatter | [TODO] | 3h |
| T007 | Log Level Filter | [TODO] | 2h |
| T008 | Keyword Search Filter | [TODO] | 2h |
| T009 | Pytest Configuration and GitHub Actions CI | [TODO] | 2h |

**Total estimate**: ~22 hours (~3 days full-time)
