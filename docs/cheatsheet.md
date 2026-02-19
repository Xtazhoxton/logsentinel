# TypeScript → Python Cheat Sheet

A growing reference of Python concepts mapped to their TypeScript equivalents.
Updated as new concepts are introduced throughout the project.

---

## Project & Dependencies

| TypeScript | Python | Notes |
|------------|--------|-------|
| `package.json` | `pyproject.toml` | Single source of truth for project metadata and deps |
| `package-lock.json` | `poetry.lock` | Always commit this |
| `node_modules/` | `.venv/` | Never commit this |
| `npm install` | `poetry install` | Installs all deps from lockfile |
| `npm install <pkg>` | `poetry add <pkg>` | Adds to main dependencies |
| `npm install -D <pkg>` | `poetry add --group dev <pkg>` | Adds to dev group |
| `npx <cmd>` / `./node_modules/.bin/<cmd>` | `poetry run <cmd>` | Runs a command in the project's virtual env |
| `npm run <script>` | `poetry run <script>` | Runs a defined script |

---

## Module System

| TypeScript | Python | Notes |
|------------|--------|-------|
| `src/index.ts` | `src/logsentinel/__init__.py` | Package entry point |
| `export { foo }` | expose at `__init__.py` level | Or import directly from the submodule |
| `import { foo } from './bar'` | `from .bar import foo` | Relative import |
| `import * as bar from './bar'` | `import logsentinel.bar as bar` | Namespace import |
| Directory as module (needs `index.ts`) | Directory as package (needs `__init__.py`) | Same concept, different file |

---

## Type System

| TypeScript | Python | Notes |
|------------|--------|-------|
| `string` | `str` | |
| `number` | `int` / `float` | Python distinguishes integers from floats |
| `boolean` | `bool` | `True` / `False` (capital) |
| `string \| null` | `str \| None` | Python 3.10+ union syntax |
| `string \| undefined` | `str \| None` | Python has no `undefined`; use `None` |
| `string[]` | `list[str]` | |
| `Record<string, string>` | `dict[str, str]` | |
| `[string, number]` | `tuple[str, int]` | Fixed-length typed tuple |
| `any` | `Any` (from `typing`) | Avoid — same as in TS |
| `interface Foo { bar: string }` | `@dataclass class Foo: bar: str` | With runtime behavior |
| `type Foo = ...` | `TypeAlias` (3.10+) or just assign | `Foo = str \| int` |
| `enum Direction { Up, Down }` | `class Direction(Enum): UP = 1` | Python Enum members have values |
| `readonly foo: string` | `@dataclass(frozen=True)` | Makes the whole instance immutable |
| `Object.freeze(obj)` | `@dataclass(frozen=True)` | Enforced at runtime in Python |

---

## Functions

| TypeScript | Python | Notes |
|------------|--------|-------|
| `function foo(x: string): void` | `def foo(x: str) -> None:` | |
| `const foo = (x: string) => x` | `foo = lambda x: x` | Lambdas are single-expression only |
| `foo?: string` (optional param) | `foo: str \| None = None` | Default to None for optional params |
| `...args: string[]` | `*args: str` | Variadic positional args |
| `{ key: value }` destructuring | No direct equivalent | Use positional or keyword unpacking |

---

## Classes

| TypeScript | Python | Notes |
|------------|--------|-------|
| `class Foo { constructor(x: string) {} }` | `@dataclass class Foo: x: str` | Dataclass auto-generates `__init__` |
| `private foo` | `_foo` (convention only) | Python has no true private — underscore is a signal |
| `protected foo` | `_foo` | Same convention |
| `this.foo` | `self.foo` | `self` must be the first param of every method |
| `implements Interface` | No direct equivalent | Use `Protocol` from `typing` for structural typing |
| `extends Base` | `class Foo(Base):` | |

---

## Error Handling

| TypeScript | Python | Notes |
|------------|--------|-------|
| `throw new Error("msg")` | `raise ValueError("msg")` | Many built-in exception types exist |
| `try / catch / finally` | `try / except / finally` | `except` not `catch` |
| `catch (e: Error)` | `except ValueError as e:` | Catch specific exception types |
| `new TypeError(...)` | `TypeError(...)` | No `new` keyword for exceptions |

---

## Testing

| TypeScript (Jest/Vitest) | Python (pytest) | Notes |
|--------------------------|-----------------|-------|
| `describe('suite', () => {})` | No required grouping; use classes or just functions | |
| `test('name', () => {})` | `def test_name():` | Function name must start with `test_` |
| `expect(x).toBe(y)` | `assert x == y` | Plain `assert` in pytest |
| `expect(x).toEqual(y)` | `assert x == y` | Same — `==` is deep equality for dicts/lists |
| `expect(fn).toThrow()` | `with pytest.raises(ValueError):` | |
| `beforeEach` | `@pytest.fixture` | Fixtures are injected by name into test functions |
| `jest.mock(...)` | `unittest.mock.patch` or `pytest-mock` | |
