# mapping.md — pytest-dev__pytest-7571

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 422685d0bdc110547535036c1ff398b5e1c44145`, states the type
abstraction, and gives the provenance of each modelled callee (source + the
exact behaviour relied upon).

Repo file under change: `src/_pytest/logging.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `CaptureController` | `LogCaptureFixture` — `src/_pytest/logging.py:341` | the log-capturing controller object under change (minimal model: only the two touched facets) |
| `CaptureController.__init__(sink_level)` | `LogCaptureFixture.__init__` — `src/_pytest/logging.py:344` (body 346-348) | constructor; the patch adds the restore-point field here |
| `CaptureController.sink_level` (field) | `self.handler.level` — the capture handler's level; `self.handler` is `LogCaptureFixture.handler` property `src/_pytest/logging.py:360-365` → `LogCaptureHandler` (`:313`, a `logging.StreamHandler`) `.level` | the sink's current acceptance threshold |
| `CaptureController.saved_level` (field, `Optional[int]`) | `self._initial_handler_level` — added by the patch (`src/_pytest/logging.py:348` post-patch), `# type: Optional[int]` | the recorded restore point (`None` = nothing recorded) |
| `set_level(self, level)` | `LogCaptureFixture.set_level` — `src/_pytest/logging.py:422` (body 433-437) | the level-setting operation; the patch adds the "record the handler level" line |
| `teardown_restore(self)` | `LogCaptureFixture._finalize` — `src/_pytest/logging.py:350` (body 355-358) | end-of-test teardown; the patch adds the "restore the handler level" guard |
| `run_raise_then_teardown(level, ambient)` | (no single repo symbol) | end-to-end teardown observable: the composition `__init__ → set_level → _finalize` the F2P test exercises across two tests; pins the cross-test restore guarantee |

The pre-patch repo state (for the refinement audit, not referenced from the
consumer spec view): `LogCaptureFixture` had **no** `_initial_handler_level`
field; `set_level` did not record the handler level; `_finalize` restored only
the saved *logger* levels (the `_initial_logger_levels` dict, unchanged by this
fix), leaving the handler level stuck at the value the test raised it to. The
sibling context manager `LogCaptureFixture.at_level` (`:439-458`) ALREADY saved
and restored `self.handler.level` correctly (lines 452/458); the patch brings
`set_level`/`_finalize` to parity with it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.handler.level` (an `int`; `logging.Handler.level` set by `setLevel`) | `self.sink_level: int` | read `self.handler.level` ↔ read `self.sink_level`; `self.handler.setLevel(L)` ↔ `self.sink_level = L`. `setLevel` stores `_checkLevel(level)`; for the integer levels the tests use (`0, 41, 43`, the `logging` constants) `_checkLevel` is the identity, so the field write is exact (mapping §3.1). |
| `self._initial_handler_level` (`Optional[int]`, `None` sentinel) | `self.saved_level: Optional[int]` | `None` ↔ `None` ("nothing recorded"); a recorded `int` ↔ the same `int`. The `is not None` guard in `_finalize` ↔ `self.saved_level is not None`. |
| `self.handler` property (`self._item._store[caplog_handler_key]`) | (omitted) — the controller reads/writes the sink level directly as a field | the handler object identity is irrelevant to the tested behaviour; only its `level` integer matters, carried by `sink_level`. The patch does not change the handler accessor. |
| the logger-level dict (`self._initial_logger_levels`, `logger.setLevel`) | (omitted) | unchanged by this fix; `_finalize`'s logger-level restoration loop and `set_level`'s `setdefault` are pre-existing and correct, and are not part of the modelled changed behaviour. Omitting them keeps the model minimal and faithful to the *changed* facet (the handler level). |

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

This bundle consumes **no** `@ContractOnly` axiom: the record-then-restore
round trip is modelled **deeply** as pure object/state logic. Two real-callee
references are validated by `axiom_check.py` (G-AX):

### 3.1 `sink_level` field read/write ↔ `logging.Handler.level` / `setLevel` (A-reference)
**Callee:** CPython `logging.Handler.level` (a plain integer attribute) and
`logging.Handler.setLevel(level)`, which executes `self.level =
logging._checkLevel(level)` (`Lib/logging/__init__.py`). For an integer
argument `_checkLevel` returns it unchanged, so `handler.level` reads back
exactly what `setLevel` wrote. `LogCaptureHandler` (`src/_pytest/logging.py:313`)
is a `logging.StreamHandler` and inherits these unchanged. The model therefore
abstracts `self.handler.level` / `self.handler.setLevel(L)` as an integer field
read / write (`sink_level`). Docs:
https://docs.python.org/3/library/logging.html#logging.Handler.setLevel.
G-AX asserts `handler.level == L` after `setLevel(L)` over the boundary levels
(`0,10,20,30,40,41,42,43,50,…`) and 20000 fuzz levels.

### 3.2 `set_level`/`finalize` round trip ↔ real `LogCaptureFixture` (A-reference)
**Callee:** the post-patch `LogCaptureFixture.set_level` / `_finalize`
themselves, driven on a real `LogCaptureHandler`. `axiom_check.py` builds a real
`LogCaptureFixture` (wired to a real handler through a minimal item carrying a
`_pytest.store.Store`, exactly as `pytest_runtest_setup`
(`src/_pytest/logging.py:683-684`) wires it), then runs the exact F2P scenario
(`handler.level == 0` → `set_level(41)` → `handler.level == 41` → `_finalize()`
→ `handler.level == 0`) plus 2000 fuzzed `(ambient, level)` pairs, asserting
teardown restores the ambient level — i.e. `run_raise_then_teardown(level,
ambient) == ambient`. This validates the deep model against the real callee
end-to-end. (Runs in the official container where pytest 6.0 is installed; the
integer-attribute check §3.1 runs everywhere on stdlib `logging`.)

**Soundness check (G-AX):** `axiom_check.py` imports only the standard-library
`logging` (always) and `_pytest` (in-container). Exit 0 iff every observation
matches the model.

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl regions (shadow)
differentially against the real patched `LogCaptureFixture` on a real
`LogCaptureHandler` in-container, comparing the bridged state pair
`(sink_level, saved_level)` ↔ `(handler.level, _initial_handler_level)` after
every operation over >= 1e5 probes (boundary grid + fuzz lifecycles).
Pinned fuzz seed: **7571**.
