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
- Design a domain model that anticipates future requirements (`correlation_id` for v0.2 grouping)
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
**Status**: [DONE]
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
**Status**: [DONE]
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
**Status**: [DONE]
**Estimate**: 3 hours
**Branch**: `feature/T003-log-entry-model`
**Blocked by**: T002

**What are dataclasses and Enums?**
Python's `dataclasses` module auto-generates `__init__`, `__repr__`, and `__eq__` from annotated fields — similar to a TypeScript interface but with real runtime behavior. `frozen=True` makes instances immutable like `Object.freeze()`. The `field(compare=False)` option excludes a field from equality checks.

Python's `Enum` works similarly to TypeScript's `enum` but with more flexibility — members can have arbitrary values (integers, strings) and you can iterate over them.

TypeScript parallel: `@dataclass` ≈ TypeScript class with auto-generated constructor / `Enum` ≈ TypeScript `enum`

Resources:
- https://docs.python.org/3/library/dataclasses.html — pay attention to `frozen`, `field`, `compare`, `default_factory`, `__post_init__`
- https://docs.python.org/3/library/enum.html — read the sections on `IntEnum` and member values
- https://docs.python.org/3/library/datetime.html — read the section on "aware" vs "naive" datetime objects, and `tzinfo`

**Why `correlation_id` now?**
`correlation_id` is the key that will allow v0.2 to group `LogEntry` objects into `Trace` objects — a full workflow execution. For AWS Step Functions, this will be the `executionId`. For Lambda, it could be the `requestId` or an X-Ray trace ID.

We introduce the field in v0.1 even though grouping is a v0.2 feature, because adding it later means migrating the data model and all existing tests. It costs almost nothing now. It costs a lot later.

**Interface to implement**

```python
# src/logsentinel/models/log_entry.py

class LogLevel(Enum):
    # Members: DEBUG, INFO, WARNING, ERROR, CRITICAL, UNKNOWN
    # Each member has an integer value representing severity for ordering
    # UNKNOWN should not participate in severity ordering

@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime           # must always be timezone-aware (UTC)
    level: LogLevel
    message: str
    source: str                   # log group name or filename
    correlation_id: str | None    # groups entries belonging to the same workflow execution — excluded from equality
    raw: str                      # original unparsed string — excluded from equality
    request_id: str | None        # AWS RequestId if present — excluded from equality
    metadata: dict                # extra key-value pairs — excluded from equality

    def is_error(self) -> bool: ...
```

**Subtasks**

**S1 — Choose the right Enum base class**
Open the `enum` module docs and read the difference between `Enum` and `IntEnum`. The key question: does `LogLevel.ERROR > LogLevel.INFO` need to work as a comparison? It will in T007. If you use plain `Enum`, that comparison raises a `TypeError`. If you use `IntEnum`, members are also integers and support `<`, `>`, `>=`. Decide which to use, then define `LogLevel` with the 5 severity levels (`DEBUG` to `CRITICAL`) assigned ascending integer values. Add `UNKNOWN` last — pick a value that will NOT accidentally place it in the severity chain (hint: think about what `UNKNOWN >= DEBUG` should return in a severity filter context — it should never match a severity check, so its value needs to be clearly outside the 1–50 range or handled specially).

> Pitfall: There is no single "correct" integer for UNKNOWN — what matters is that your choice is consistent with how T007 will use it. Think ahead: T007 will filter `entries where level >= min_level`. If `UNKNOWN = 0`, it falls below `DEBUG` and would be excluded when filtering with `min_level=INFO`. That is wrong — `UNKNOWN` entries should always pass through. You will need a special case in T007 regardless of what value you pick.

**S2 — Import what you need**
At the top of `src/logsentinel/models/log_entry.py`, you need three imports:
- `Enum` (or `IntEnum`) from `enum`
- `dataclass` and `field` from `dataclasses`
- `datetime` and `timezone` from `datetime`

Each import is on its own line. In Python, `from module import Name` is the equivalent of `import { Name } from 'module'` in TypeScript.

**S3 — Define the LogEntry fields**
Define `LogEntry` with `@dataclass(frozen=True)`. Add the 8 fields listed in the interface above. For fields that should be excluded from `==` comparisons, look up the `compare` parameter of `field()` in the dataclasses docs. For `metadata`, you cannot use `metadata: dict = {}` as a default — mutable default values are forbidden in dataclasses. Look up `field(default_factory=...)` to understand how to provide a mutable default.

> Pitfall: `correlation_id: str | None` means the field is optional and can hold `None`. In Python 3.10+, this union syntax (`X | Y`) works directly. But you still need to decide: should `correlation_id` have a default value of `None`? If yes, it must come after all fields without defaults (Python enforces this). Fields with defaults must appear after fields without defaults.

**S4 — Add timezone validation with `__post_init__`**
A frozen dataclass cannot set new values in `__init__`, but it CAN run a `__post_init__` method to validate the inputs after they are set. If the datetime is "naive" (no timezone info), `timestamp.tzinfo` will be `None`. Raise a `ValueError` with a descriptive message if that is the case.

> Pitfall: You cannot assign to `self.timestamp` inside `__post_init__` on a frozen dataclass — Python will raise a `FrozenInstanceError`. You can only read fields and raise exceptions.

**S5 — Implement `is_error()`**
A simple method. Check if `self.level` is one of the two error levels and return `True` or `False` accordingly. In Python, `self.level in (LogLevel.ERROR, LogLevel.CRITICAL)` is the idiomatic way to check membership in a set of values.

**S6 — Expose the model from the module**
Open `src/logsentinel/models/__init__.py` and import `LogEntry` and `LogLevel` so they can be imported as `from logsentinel.models import LogEntry, LogLevel` rather than the full path.

**S7 — Write the tests**
Create `tests/unit/test_log_entry.py`. Import `pytest` and your classes. Each test function must start with `test_`. Things to test:
- **Valid creation**: build a `LogEntry` with a UTC-aware datetime and check you can access its fields
- **Equality ignores excluded fields**: create two entries identical except for `correlation_id` and `raw` — they must be `==`
- **Equality uses included fields**: create two entries that differ in `message` — they must not be `==`
- **`is_error()` for all 6 levels**: parametrize or write 6 individual tests
- **Naive datetime raises ValueError**: use `pytest.raises(ValueError)` — look up how to use it as a context manager

For a UTC-aware datetime, use `datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)`.

**Acceptance Criteria**
- [ ] `LogLevel` is an `Enum` with `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `UNKNOWN`
- [ ] `LogLevel` members have integer values reflecting severity (`DEBUG` lowest, `CRITICAL` highest)
- [ ] `LogEntry` is a frozen dataclass
- [ ] `correlation_id`, `raw`, `request_id`, and `metadata` are excluded from `__eq__` comparisons
- [ ] `is_error()` returns `True` only for `ERROR` and `CRITICAL`
- [ ] `timestamp` is always a timezone-aware `datetime` — the model should make it impossible to create a `LogEntry` with a naive datetime (raise `ValueError`)
- [ ] Tests are in `tests/unit/test_log_entry.py`
- [ ] Tests cover: valid creation, equality ignores `correlation_id`/`raw`/`request_id`/`metadata`, `is_error()` for all 6 levels, naive datetime raises `ValueError`

> **[DONE]** — All 8 criteria pass. A few things to be aware of going forward:
> 1. `UNKNOWN = 60` — this puts UNKNOWN above CRITICAL in integer ordering. The good news: it means UNKNOWN entries automatically pass any severity filter in T007 without needing a special case. The spec says a special case *will* be needed regardless of choice — your value proves that wrong, which is fine. Just be aware in T007 that the "always include UNKNOWN" logic is already handled implicitly.
> 2. `is_error()` has no `-> bool` return type annotation. When mypy runs in T009 with `strict = true`, it will flag this. Good habit: annotate all method return types now.
> 3. `from tests.conftest import sample_entry` in the test file is redundant — pytest discovers fixtures from `conftest.py` automatically. Remove this import.

---

### EPIC-03: Parser

---

#### T004 — AWS CloudWatch JSON Parser
**Status**: [REVIEW]
**Estimate**: 4 hours
**Branch**: `feature/T004-cloudwatch-parser`
**Blocked by**: T003

**File I/O and pathlib**
Python's `pathlib.Path` is the modern way to handle file paths — more readable than the old `os.path`. Always use a context manager (`with open(...) as f:`) to open files; it ensures the file is closed even if an error occurs. This is equivalent to wrapping `fs.readFileSync` in a try/finally in Node.

For timestamps: CloudWatch stores them as Unix **milliseconds**. `datetime.fromtimestamp()` works with seconds — divide by 1000. Always pass `tz=timezone.utc` to get a timezone-aware datetime.

TypeScript parallel: `Protocol` ≈ TypeScript `interface` / `pathlib.Path` ≈ Node's `path` module / `json.loads()` ≈ `JSON.parse()`

Resources:
- https://docs.python.org/3/library/pathlib.html — `Path.exists()`, `Path.read_text()`
- https://docs.python.org/3/library/json.html — `json.loads()`, `json.load()`
- https://docs.python.org/3/library/re.html — `re.match()`, `re.search()`, capturing groups `(...)`, `match.group(1)`
- https://docs.python.org/3/library/typing.html#typing.Protocol

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

**Why a Parser Protocol?**
Python's `typing.Protocol` enables structural subtyping — duck typing with type safety. If a class implements the right methods with the right signatures, it satisfies the protocol without any explicit declaration. This is the direct equivalent of a TypeScript `interface`.

Without a protocol, `CloudWatchParser` is a standalone class. The CLI would depend on it directly, and adding a new format in v0.2 would require modifying the CLI. With a `Parser` protocol, the CLI depends only on the *contract* (`Parser`), not on the *implementation* (`CloudWatchParser`) — adding a new format is extension, not modification.

TypeScript parallel: `Parser` protocol ≈ TypeScript `interface Parser { parseFile(...): LogEntry[]; parseString(...): LogEntry[]; }`

**Interface to implement**

```python
# src/logsentinel/parsers/base.py
class Parser(Protocol):
    def parse_file(self, path: Path) -> list[LogEntry]: ...
    def parse_string(self, content: str) -> list[LogEntry]: ...
```

```python
# src/logsentinel/parsers/cloudwatch.py

class CloudWatchParser:
    def parse_file(self, path: Path) -> list[LogEntry]: ...
    def parse_string(self, content: str) -> list[LogEntry]: ...
    def _parse_event(self, event: dict, source: str) -> LogEntry: ...
    def _extract_level(self, message: str) -> LogLevel: ...
    def _extract_request_id(self, message: str) -> str | None: ...
```

**Subtasks**

**S1 — Create the fixture file**
Copy the JSON above into `tests/fixtures/cloudwatch_sample.json`. This is real test data — you will reference this file in multiple tests later. Commit it.

**S2 — Create the Parser protocol**
Create `src/logsentinel/parsers/base.py`. Import `Protocol` from `typing`, `Path` from `pathlib`, and `LogEntry` from your models module. A `Protocol` class is defined exactly like a normal class — the only difference is that it inherits from `Protocol`. Method bodies should be `...` (the Ellipsis literal), not `pass` — this is the convention for protocol stubs.

> Pitfall: A `Protocol` class must explicitly inherit from `Protocol` — `class Parser(Protocol):`. If you write `class Parser:` it becomes a regular class and the structural subtyping won't work.

**S3 — Create the CloudWatchParser skeleton**
Create `src/logsentinel/parsers/cloudwatch.py`. Define the class with all 5 method stubs (body `...`). Write the imports you will need: `re`, `json`, `Path`, `datetime`, `timezone`, `LogEntry`, `LogLevel`. Do not implement any logic yet — just get the file to import cleanly.

**S4 — Implement `_extract_level`**
This method takes a raw message string and returns a `LogLevel`. The pattern to detect is `[LEVEL]` at the very start of the string — for example `[ERROR] 2024-01-15...`.

Steps:
1. Use `re.match()` (not `re.search()` — read the docs to understand the difference) with the pattern `r"^\[(\w+)\]"`
2. If there is a match, extract the captured group with `match.group(1)` — this gives you the string `"ERROR"`
3. Try to look up the `LogLevel` member by name: `LogLevel["ERROR"]`. This raises `KeyError` if the string is not a valid member name. Catch that with a `try/except KeyError` and return `LogLevel.UNKNOWN`
4. If there is no match at all, return `LogLevel.UNKNOWN`

> Pitfall: `re.match()` vs `re.search()`: `match` only checks at the beginning of the string. `search` scans the entire string. Use `match` here because the level prefix must be at position 0.

**S5 — Implement `_extract_request_id`**
Similar approach. The pattern to find is `RequestId: <value>` anywhere in the message. The value ends at the next whitespace character.

Steps:
1. Use `re.search()` (not `match` — the RequestId can appear anywhere in the message)
2. Pattern: `r"RequestId:\s+(\S+)"` — `\s+` matches one or more whitespace characters, `(\S+)` captures one or more non-whitespace characters
3. Return `match.group(1)` if found, `None` otherwise

**S6 — Implement `_parse_event`**
This method takes a single event dict (one element from `logEvents`) and the `source` string. It must return a `LogEntry`.

Steps:
1. Get the raw message string from `event["message"]`
2. Convert the timestamp: `event["timestamp"]` is milliseconds — divide by 1000 and pass to `datetime.fromtimestamp(..., tz=timezone.utc)`
3. Call `_extract_level(message)` and `_extract_request_id(message)`
4. Construct and return a `LogEntry` — set `source` to the passed-in source string, `raw` to the original message, `correlation_id` to `None` for now (will be populated in v0.2), `metadata` to an empty dict

**S7 — Implement `parse_string`**
This method takes a JSON string and returns a list of `LogEntry` objects.

Steps:
1. Parse the JSON string with `json.loads(content)`
2. Check that `"logEvents"` key exists in the parsed dict — if not, raise `ValueError` with a descriptive message like `"Missing 'logEvents' key in CloudWatch JSON"`
3. Get the source from `data.get("logGroupName", "unknown")` — use `.get()` with a default value so it never raises `KeyError`
4. Iterate over `data["logEvents"]` and call `_parse_event` for each one
5. Return the list

**S8 — Implement `parse_file`**
This method takes a `Path` and returns a list of `LogEntry` objects.

Steps:
1. Check if the path exists: `if not path.exists(): raise FileNotFoundError(...)`
2. Read the file content: `path.read_text(encoding="utf-8")`
3. Call and return `parse_string(content)`

> Pitfall: Do not use `open()` directly — `Path.read_text()` is cleaner and equivalent. Both work, but `read_text()` is idiomatic with `pathlib`.

**S9 — Write the tests**
Create `tests/unit/test_cloudwatch_parser.py`. Tests to write:
- `parse_file` with the fixture returns 5 entries
- `parse_string` with the same file content returns the same 5 entries (read the fixture file and pass it as a string)
- The `START` event (id 001) has `level == LogLevel.UNKNOWN`
- The `[ERROR]` event (id 002) has `level == LogLevel.ERROR`
- The `[ERROR]` event has `request_id == None` — applicative logs don't include a `RequestId:` prefix, only Lambda system messages (`START`, `END`, `REPORT`) do
- The `END` event (id 004) has `request_id == "req-001"`
- All timestamps are UTC-aware (check `entry.timestamp.tzinfo is not None`)
- `parse_file` raises `FileNotFoundError` on a non-existent path
- `parse_string` raises `ValueError` when `logEvents` key is absent
- `parse_string` returns an empty list for `{"logGroupName": "x", "logEvents": []}`

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
- [ ] `Parser` protocol exists in `src/logsentinel/parsers/base.py`
- [ ] `mypy` confirms `CloudWatchParser` satisfies the `Parser` protocol (no explicit `implements` needed — structural subtyping)

> **[FAILED]** — Three criteria fail. Note: the task was never moved to `[REVIEW]` — remember to do that before asking for a review.
>
> 1. **Criterion 4 — Level mapping tests incomplete.** Only `LogLevel.ERROR` is explicitly asserted. `[INFO]`, `[WARNING]`, `[DEBUG]`, and `[CRITICAL]` are never tested. The fixture has an `[INFO]` event (id 003) but there is no assertion on its level. Add tests for `_extract_level` directly, or add fixture events that cover all five levels.
> 2. **Criterion 7 — `source` field never verified.** The implementation is correct, but no test ever asserts `entry.source == "/aws/lambda/my-function"`. A criterion that requires testing must be tested.
> 3. **Criterion 11 — Missing `logGroupName` edge case not tested.** The spec explicitly lists this alongside the empty `logEvents` test. Write a test that passes JSON without `logGroupName` and asserts the entries have `source == "unknown"`.
>
> Additionally: the timestamp UTC check `assert [entry.timestamp.tzinfo is not None for entry in parsed_file]` is a logic bug — a non-empty list is always truthy, so this assertion never fails regardless of the values inside. Replace with `assert all(entry.timestamp.tzinfo is not None for entry in parsed_file)`.

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
- https://typer.tiangolo.com/tutorial/options/ — options vs arguments
- https://typer.tiangolo.com/tutorial/testing/ — CliRunner for testing
- Entry points in pyproject.toml: https://python-poetry.org/docs/pyproject/#scripts

**Command structure to implement** (no business logic yet — `parse` can print a placeholder)

```
logsentinel --help
logsentinel version
logsentinel parse <file> [--format cloudwatch] [--level LEVEL] [--search KEYWORD]
```

**Subtasks**

**S1 — Register the CLI entry point**
In `pyproject.toml`, add a `[tool.poetry.scripts]` section with one line: `logsentinel = "logsentinel.cli:app"`. This tells Poetry to create a `logsentinel` executable that maps to the `app` object inside `src/logsentinel/cli/__init__.py`. After editing `pyproject.toml`, run `poetry install` to register the new entry point — without this step, `poetry run logsentinel` will not find the command.

**S2 — Create the Typer app**
In `src/logsentinel/cli/__init__.py`:
1. Import `typer`
2. Create the app: `app = typer.Typer(name="logsentinel", help="...", add_completion=False)`. Pick a short description for `help`. `add_completion=False` disables shell autocomplete installation noise.

**S3 — Add the `version` command**
Create a function `def version()` and decorate it with `@app.command()`. Inside, use `typer.echo()` to print the version. Import `__version__` from `logsentinel` (the top-level `__init__.py`). The output must be exactly `LogSentinel v0.1.0`.

> Pitfall: `typer.echo()` is preferred over `print()` in Typer commands — it works correctly with the test runner and supports color/formatting options.

**S4 — Create a `Format` enum for `--format`**
Before defining the `parse` command, define a small `Enum` for supported formats. For now it has one member: `cloudwatch = "cloudwatch"`. Typer uses enum types to validate option values automatically — if the user passes `--format unknown`, Typer will reject it with an error and a usage message.

> Note: Use `str, Enum` as the base classes: `class Format(str, Enum)`. This is required for Typer to correctly handle the enum as a string option. Read the Typer docs on "Enum" options.

**S5 — Add the `parse` command**
Create a function `def parse(...)` decorated with `@app.command()`. Define these parameters:
- `file: Path = typer.Argument(...)` — a required positional argument. Add `exists=True` to the `typer.Argument()` call so Typer automatically checks if the file exists and exits with code 1 if not. Look up the `exists` parameter in Typer docs.
- `format: Format = typer.Option(Format.cloudwatch, "--format")` — optional, defaults to `cloudwatch`
- `level: Optional[str] = typer.Option(None, "--level")` — optional string for now (T006 will make this typed)
- `search: Optional[str] = typer.Option(None, "--search")`

The body can just print a placeholder: `typer.echo(f"Parsing {file} with format {format.value}...")`.

For `Optional`, import it from `typing` or use `str | None` syntax.

**S6 — Add manual level validation**
Since `--level` is a plain string for now, validate it manually inside `parse`. Define an allowed set: `{"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}`. If the provided level (uppercased) is not in this set, print an error with `typer.echo("Error: ...", err=True)` and call `raise typer.Exit(code=1)`.

> Pitfall: `typer.Exit` is not an exception you catch — it is raised to signal the process exit code. `err=True` in `typer.echo()` prints to stderr instead of stdout, which is correct for error messages.

**S7 — Write the tests**
Create `tests/unit/test_cli.py`. Import `CliRunner` from `typer.testing` and your `app`.

```python
from typer.testing import CliRunner
runner = CliRunner()
```

Use `runner.invoke(app, ["version"])` to run commands. The result has `.exit_code` and `.output`. Tests to write:
- `version` command outputs `LogSentinel v0.1.0` and exits 0
- `parse` with a non-existent file exits with code != 0
- `parse` with `--format invalid_format` exits with code != 0
- `parse` with `--level INVALID` exits 1 and the output contains an error message

> Note: When using `exists=True` in `typer.Argument`, Typer handles the missing file check internally — you do not need to test that the file actually runs. Just verify the exit code is non-zero.

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

TypeScript parallel: Rich ≈ `chalk` + `cli-table3` combined.

Resources:
- https://rich.readthedocs.io/en/stable/tables.html — `Table`, `add_column`, `add_row`
- https://rich.readthedocs.io/en/stable/style.html — style strings (`"red"`, `"bold yellow"`, `"dim"`)
- https://rich.readthedocs.io/en/stable/console.html — `Console`, `console.print()`

**Interface to implement**

```python
# src/logsentinel/formatters/table.py

class TableFormatter:
    def format(self, entries: list[LogEntry]) -> Table: ...   # rich.table.Table
    def _level_style(self, level: LogLevel) -> str: ...       # returns a Rich style string
```

**Subtasks**

**S1 — Implement `_level_style`**
Create `src/logsentinel/formatters/table.py`. Import `LogLevel` from your models and `Table` from `rich.table`. Define `TableFormatter` with `_level_style` first — it is the simplest method. It takes a `LogLevel` and returns a Rich style string. Map: `ERROR`/`CRITICAL` → `"red"`, `WARNING` → `"yellow"`, `INFO` → `"green"`, `DEBUG` → `"blue"`, `UNKNOWN` → `"dim"`. Use a dict or a series of `if/elif`.

**S2 — Implement `format()`**
This method creates a Rich `Table`, adds 4 columns, iterates over entries, and returns the table.

Steps:
1. Create the table: `table = Table(show_header=True, header_style="bold")`
2. Add columns: `table.add_column("Timestamp")`, `table.add_column("Level")`, etc. Look up the `style` parameter on `add_column` for header styling.
3. Iterate over entries. For each entry:
   - Format the timestamp: `entry.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")` — this gives ISO 8601 format
   - Truncate the message: if `len(entry.message) > 80`, take `entry.message[:79] + "…"`, otherwise use the full message
   - Get the row style: `self._level_style(entry.level)`
   - Add the row: `table.add_row(timestamp_str, entry.level.name, entry.source, message_str, style=row_style)`
4. Return the table

**S3 — Handle the empty case**
The `format()` method returns a `Table`. But what if entries is empty? You have two options: return a `Table` with no rows, or handle it in the caller. The acceptance criterion says to print `"No log entries found."` — so handle this in the CLI, not in `TableFormatter`. In the `parse` command, check `if not entries:` after parsing and print the message using a `Console`.

**S4 — Wire the `parse` command**
Now in the CLI `parse` function, replace the placeholder with real logic:
1. Create a `CloudWatchParser()` and call `parse_file(file)` — wrap in a `try/except` to handle `FileNotFoundError` and `ValueError` gracefully (print error, exit 1)
2. Check if entries is empty → print message and exit 0
3. Apply filters if provided (skip for now — T007/T008 will add this)
4. Create a `TableFormatter()`, call `format(entries)`, and print the table using `Console().print(table)`

> Pitfall: Import `Console` from `rich.console` and `Table` from `rich.table`. These are separate submodules.

**S5 — Write the tests**
For `TableFormatter`:
- Build a small list of `LogEntry` objects manually (you know how to construct them from T003)
- Call `formatter.format(entries)` and assert the result is a `Table` instance
- Check that `_level_style(LogLevel.ERROR)` returns `"red"` etc.

For the integration test, create `tests/integration/test_parse_command.py`:
- Use `CliRunner` to invoke `parse tests/fixtures/cloudwatch_sample.json`
- Assert `exit_code == 0`
- Assert the output contains `"Timestamp"` (the column header)

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

TypeScript parallel: `LevelFilter.apply()` ≈ `entries.filter(e => e.level >= minLevel)`

Resources:
- https://docs.python.org/3/library/functions.html#filter — or use a list comprehension: `[e for e in entries if condition]`

**Interface to implement**

```python
# src/logsentinel/filters/level.py

class LevelFilter:
    def __init__(self, min_level: LogLevel): ...
    def apply(self, entries: list[LogEntry]) -> list[LogEntry]: ...
```

**Subtasks**

**S1 — Understand severity comparison**
If you used `IntEnum` for `LogLevel`, you can compare members directly: `LogLevel.ERROR >= LogLevel.WARNING` returns `True` because `40 >= 30`. This is the key mechanic of this filter. Take a moment to verify this works in a Python REPL: `poetry run python -c "from logsentinel.models import LogLevel; print(LogLevel.ERROR >= LogLevel.WARNING)"`.

If the result surprises you, revisit your `LogLevel` definition from T003 — the comparison behavior depends on the base class you chose.

**S2 — Implement `LevelFilter`**
Create `src/logsentinel/filters/level.py`. The `__init__` stores `min_level`. The `apply` method returns a filtered list. The logic for each entry: include it if `entry.level == LogLevel.UNKNOWN` **OR** `entry.level >= min_level`.

Use a list comprehension: `[e for e in entries if <condition>]`. This is the Pythonic way to build a filtered list — equivalent to `entries.filter(...)` in JavaScript.

> Pitfall: The `UNKNOWN` special case must use `or`, not `and`. Read the condition aloud: "include this entry if it is UNKNOWN OR if its level is at least the minimum".

**S3 — Expose from the module**
Add `LevelFilter` to `src/logsentinel/filters/__init__.py`.

**S4 — Wire to CLI**
In the `parse` command, add level filtering. At this point you should also convert `--level` from a plain string to a `LogLevel` enum lookup. Inside `parse`, after parsing entries and before formatting:

```python
if level is not None:
    # convert the string to LogLevel, apply filter
```

Raise a `typer.BadParameter` or print an error and exit 1 if the string is not a valid level name.

**S5 — Write the tests**
Create `tests/unit/test_level_filter.py`. For each test, build a list of entries covering all 6 levels and check what comes out. Tests:
- `min_level=DEBUG` → all entries pass including UNKNOWN
- `min_level=WARNING` → only WARNING, ERROR, CRITICAL, and UNKNOWN pass; DEBUG and INFO are excluded
- `min_level=CRITICAL` → only CRITICAL and UNKNOWN pass
- Empty list input → returns empty list
- List of only UNKNOWN entries → all pass regardless of min_level

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

TypeScript parallel: `SearchFilter.apply()` ≈ `entries.filter(e => e.message.toLowerCase().includes(keyword.toLowerCase()))`

Resources:
- https://docs.python.org/3/library/stdtypes.html#str.casefold — better than `lower()` for Unicode
- https://docs.python.org/3/library/stdtypes.html#str — `in` operator: `"foo" in "foobar"` returns `True`

**Interface to implement**

```python
# src/logsentinel/filters/search.py

class SearchFilter:
    def __init__(self, keyword: str, case_sensitive: bool = False): ...
    def apply(self, entries: list[LogEntry]) -> list[LogEntry]: ...
```

**Subtasks**

**S1 — Implement `SearchFilter`**
Create `src/logsentinel/filters/search.py`. The `__init__` stores `keyword` and `case_sensitive`. In `apply`:

1. If `keyword` is empty (`not keyword` or `keyword == ""`), return all entries unchanged — this is the short-circuit case.
2. For each entry, check if the keyword appears in `entry.message`. For case-insensitive search, use `keyword.casefold() in entry.message.casefold()`. For case-sensitive, use `keyword in entry.message`.
3. Also check `entry.metadata` values: iterate over `entry.metadata.values()`, and for each value that is a string, apply the same check. If any metadata value matches, include the entry.
4. Return a list comprehension of matching entries.

> Pitfall: `entry.metadata` is a `dict`. Its `.values()` returns the values, not keys. Not all values will necessarily be strings if you ever store non-string data in metadata — use `isinstance(v, str)` before calling string methods on them.

**S2 — Expose from the module**
Add `SearchFilter` to `src/logsentinel/filters/__init__.py`.

**S3 — Wire to CLI**
In `parse`, after the level filter, apply the search filter if `--search` was provided:

```python
if search is not None:
    # apply SearchFilter
```

Both filters can be active simultaneously. Level filter runs first, search filter second.

**S4 — Write the tests**
Create `tests/unit/test_search_filter.py`. Tests:
- Case-insensitive match: keyword `"error"` matches entry with message `"[ERROR] something"`
- Case-sensitive non-match: `keyword="error"`, `case_sensitive=True` does NOT match `"[ERROR] something"` (uppercase)
- Case-sensitive match: `keyword="ERROR"`, `case_sensitive=True` DOES match
- Empty keyword returns all entries unchanged
- Keyword found in metadata value but not in message — entry is included
- Keyword found in neither message nor metadata — entry is excluded

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

#### T009 — Code Quality: Tests, Linting, and CI
**Status**: [TODO]
**Estimate**: 3 hours
**Branch**: `feature/T009-ci`
**Blocked by**: T008

**What is pytest configuration and CI?**
`pytest` discovers and runs tests automatically. Its configuration goes in `pyproject.toml` under `[tool.pytest.ini_options]` — no separate `pytest.ini` needed. `pytest-cov` measures which lines of code are exercised by tests. GitHub Actions is a CI/CD platform that runs your tests automatically on every push, catching regressions before they reach the main branch.

**What are ruff and mypy?**
`ruff` is a linter and formatter in one tool, written in Rust — extremely fast. It replaces three separate tools: `flake8` (linting), `isort` (import sorting), and `black` (formatting). TypeScript parallel: ruff ≈ ESLint + Prettier combined.

`mypy` is a static type checker. It reads your type hints and catches type errors before runtime — the same safety net TypeScript's compiler gives you. TypeScript parallel: mypy ≈ `tsc --noEmit`.

Why set these up from the start: adding linting and type checking retroactively to an existing codebase is painful and demoralizing. Start with a high bar and maintain it from commit one.

Resources:
- https://docs.pytest.org/en/stable/reference/customize.html — `ini_options`, `addopts`, `pythonpath`
- https://pytest-cov.readthedocs.io/en/latest/config.html — coverage flags
- https://docs.astral.sh/ruff/configuration/ — `pyproject.toml` config
- https://mypy.readthedocs.io/en/stable/config_file.html — `pyproject.toml` config
- https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python

**Subtasks**

**S1 — Configure pytest in `pyproject.toml`**
Add a `[tool.pytest.ini_options]` section. You need three keys:
- `testpaths = ["tests"]` — tells pytest where to look for tests
- `pythonpath = ["src"]` — adds `src/` to the Python path so `import logsentinel` works inside test files
- `addopts = "--cov=src/logsentinel --cov-report=term-missing"` — automatically measures coverage on every test run

After adding this, run `poetry run pytest` and verify it discovers and runs all your tests. Fix any `ModuleNotFoundError` issues — they are usually caused by missing `__init__.py` files or incorrect `pythonpath`.

> Pitfall: `pythonpath` in `pytest.ini_options` is what makes `import logsentinel` work in tests. Without it, Python looks for the package in the current directory, not inside `src/`. This setting was introduced in pytest 7 — verify your pytest version supports it.

**S2 — Add ruff and mypy as dev dependencies**
Run `poetry add --group dev ruff mypy`. Then `poetry install`. After installing, verify the tools are accessible: `poetry run ruff --version` and `poetry run mypy --version`.

**S3 — Configure ruff**
Add to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

- `E` — pycodestyle error rules (style errors)
- `F` — Pyflakes rules (undefined names, unused imports)
- `I` — isort rules (import ordering)

Run `poetry run ruff check src/`. Read every error carefully and fix it. Common issues: unused imports, wrong import order, lines that are too long.

> Pitfall: If ruff reports `I001` (import sort order), run `poetry run ruff check --fix src/` to auto-fix import ordering. For other errors, fix them manually.

**S4 — Configure mypy**
Add to `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.13"
strict = true
```

Run `poetry run mypy src/`. Mypy strict mode is demanding — it will report missing return type annotations, possibly-untyped function parameters, and more. Fix each error:
- Missing return type: add `-> ReturnType` to function signatures
- Missing parameter type: add type annotation to the parameter
- `dict` without type params: use `dict[str, str]` instead of bare `dict`

> Pitfall: Strict mode enables many checks including `--disallow-untyped-defs`, `--warn-return-any`, and `--no-implicit-optional`. If mypy reports errors you do not understand, search the specific error code (e.g. `mypy error [no-untyped-def]`) in the mypy docs.

**S5 — Create the GitHub Actions workflow**
Create the directory `.github/workflows/` and the file `ci.yml` inside it.

The workflow should:
1. Trigger on `push` to any branch
2. Run on `ubuntu-latest`
3. Steps: checkout the repo → set up Python 3.13 → install Poetry → run `poetry install` → run `ruff check src/` → run `mypy src/` → run `poetry run pytest`

Look at the GitHub Actions Python guide linked above for the exact YAML structure. Key things:
- Use `actions/checkout@v4` and `actions/setup-python@v5`
- Poetry is not installed by default on GitHub runners — you need to install it. The recommended way is `pip install poetry` or the official Poetry installer action. The simplest approach: add a step `run: pip install poetry` before `poetry install`.

**S6 — Verify CI passes**
Push your branch and navigate to the "Actions" tab on GitHub. If the workflow fails, read the error output step by step. Common CI-specific failures:
- Package not found: the `pythonpath` pytest config was not set
- Poetry not found: the install step is missing or in the wrong order
- mypy or ruff errors that were not caught locally (check your local Python version matches)

Fix all failures until the green checkmark appears on your branch.

**Acceptance Criteria**
- [ ] `[tool.pytest.ini_options]` is in `pyproject.toml` — no separate `pytest.ini`
- [ ] `testpaths`, `addopts` (with coverage flags), and `pythonpath = ["src"]` are configured
- [ ] `poetry run pytest` runs the full test suite and shows a coverage summary
- [ ] Total coverage is ≥ 80%
- [ ] `ruff` and `mypy` added as dev dependencies
- [ ] `[tool.ruff]` configured in `pyproject.toml` — target Python version and selected rule sets
- [ ] `[tool.mypy]` configured in `pyproject.toml` — strict mode enabled
- [ ] `poetry run ruff check src/` exits 0
- [ ] `poetry run mypy src/` exits 0
- [ ] `.github/workflows/ci.yml` triggers on push to any branch
- [ ] CI workflow: checkout → Python 3.13 → install Poetry → `poetry install` → ruff → mypy → `poetry run pytest`
- [ ] CI passes on the `main` branch

---

## Task Summary

| ID | Title | Status   | Estimate |
|----|-------|----------|----------|
| T001 | Initialize Poetry Project | [DONE]   | 2h |
| T002 | Set Up Project Structure | [DONE]   | 1h |
| T003 | LogEntry and LogLevel Models | [DONE]   | 3h |
| T004 | AWS CloudWatch JSON Parser | [FAILED] | 4h |
| T005 | CLI Skeleton with Typer | [TODO]   | 3h |
| T006 | Wire Parse Command to Parser and Formatter | [TODO]   | 3h |
| T007 | Log Level Filter | [TODO]   | 2h |
| T008 | Keyword Search Filter | [TODO]   | 2h |
| T009 | Code Quality: Tests, Linting, and CI | [TODO]   | 3h |

**Total estimate**: ~23 hours (~3 days full-time)
