# mapping.md — pytest-dev__pytest-7571

## Symbol binding (file:line @ base_commit 422685d0bdc110547535036c1ff398b5e1c44145)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_captureLevel` / `problem_spec_captureLevel` / `correct_captureLevel` | the capture-handler level lifecycle of `LogCaptureFixture`: `__init__` (initial state) + each `set_level` call + `_finalize` (teardown) | `src/_pytest/logging.py:344-358, 422-437` |
| `runCaptureLevels` (pure helper) | the per-`set_level` state update: each call records the handler level it sees, then raises the handler to the requested level | `set_level` body, `logging.py:432-437` |
| `restoredCaptureLevel` (pure helper) | the capture-handler level observable after `_finalize` runs | `_finalize` body, `logging.py:350-358` |

## What the code does (base_commit)

`LogCaptureFixture` owns a capture handler with a numeric level (the minimum
record severity it keeps; `0` = NOTSET on a fresh handler). A test may call
`set_level(level, logger=None)` one or more times to raise the capturing
threshold. At the end of the test, `caplog`'s generator finalizer calls
`_finalize`, which is meant to undo the level changes `set_level` made.

```python
def __init__(self, item):
    self._item = item
    self._initial_logger_levels = {}        # dict of log name -> log level

def _finalize(self):
    # restore log levels
    for logger_name, level in self._initial_logger_levels.items():
        logging.getLogger(logger_name).setLevel(level)

def set_level(self, level, logger=None):
    logger_obj = logging.getLogger(logger)
    self._initial_logger_levels.setdefault(logger, logger_obj.level)
    logger_obj.setLevel(level)
    self.handler.setLevel(level)            # <-- raises the CAPTURE HANDLER too
```

`set_level` adjusts **two** things: the named logger's level (saved with
`setdefault` and restored in `_finalize`) **and** the capture handler's level
(`self.handler.setLevel(level)`). But `__init__`/`_finalize` only ever track and
restore the *logger* levels — the capture handler's level is adjusted yet never
recorded nor undone, so after a test that called `set_level` the handler keeps
the raised threshold, and it carries into the next test (the issue: a test
calling `set_level(42)` leaves the next test's `caplog.handler.level == 42`
instead of `0`).

## The fix (gold patch)

* `__init__` gains `self._initial_handler_level = None`.
* `set_level` adds `self._initial_handler_level = self.handler.level` (read of
  the handler level *immediately before* this call's `setLevel`). This is a plain
  assignment (last-write-wins), in contrast to the `setdefault` (first-write-wins)
  used for the logger levels.
* `_finalize` adds `if self._initial_handler_level is not None:
  self.handler.setLevel(self._initial_handler_level)`.

So after teardown the capture handler is reset to the level it held immediately
before the **last** `set_level` call (its initial level if `set_level` was called
at most once), instead of being left at the last-requested level.

## Lean modeling

The observable across the lifecycle is the capture handler's numeric level after
teardown, a function of:

* `initialLevel : Int` — the handler level at fixture creation
  (`self.handler.level` before any `set_level`; `0` for a fresh handler);
* `levels : List Int` — the sequence of levels passed to `set_level`, in call
  order. (Python accepts `int`/`str`; a `str` is normalized to its `int` by
  `logging`, so the modeled element type is the resolved integer level.)

`runCaptureLevels initialLevel levels` folds the call sequence, threading the
pair `(handlerLevel, savedLevel)`: each step records the *current* handler level
into `savedLevel` and then raises the handler to the requested level — exactly
the two assignments the post-fix `set_level` performs (`_initial_handler_level =
self.handler.level; self.handler.setLevel(level)`). `restoredCaptureLevel`
applies teardown: if a level was recorded (`some s`) the handler is reset to it,
else (`none`, no `set_level` ever called) it is left as is.

* `none` ↔ `_initial_handler_level is None` (teardown is a no-op for the handler).
* `some s` ↔ `_initial_handler_level == s` (teardown re-applies `s`).

The `_initial_logger_levels` dict and the named-logger restoration are **not**
modeled: they are unchanged by the patch, are independent of the capture-handler
level (the only behavior the issue concerns and the F2P test observes), and
introduce no coupling to it.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.handler.level` initial | `initialLevel : Int` | identity (resolved int level) |
| ordered `set_level(level)` calls | `levels : List Int` | identity, in call order |
| `self.handler.level` after `_finalize` | `result : Int` | identity (the observable) |
| `self._initial_handler_level` (`None`/`int`) | `Option Int` (`none`/`some`) | `None ↔ none`; `int ↔ some` |
| `self.handler.setLevel(x)` | set state component to `x` | identity |
| reads `self.handler.level` before set | reads the `handlerLevel` component | identity |

## Callee provenance + flag dependencies

* **No consumed callee axiom; no A-reference.** The lifecycle (the record-then-set
  per call, and the teardown re-application) is the behavior the patch changes,
  so it is modeled DEEPLY over the observable inputs (SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op). The `axioms` region is empty and
  **G-AX skips**.
* `logging.getLogger(...).setLevel(...)` and the `_initial_logger_levels`
  bookkeeping are unchanged and independent of the modeled observable, so they
  are not modeled.
* No flag dependence: `set_level`'s capture-handler adjustment is unconditional.

## G-CONF fuzz seed

Pinned seed: **7571** (see `conformance_check.py` `SEED`). Corpus: randomized
`(initialLevel, levels)` with `levels` of length 0..6 over standard logging
levels (0, 10, 20, 30, 40, 41, 42, 43, 50) plus arbitrary ints, ≥1e5 inputs. The
R/I shadow of `implementation_captureLevel` is diffed against a faithful
in-process replica of the POST-PATCH lifecycle (`__init__` → each `set_level` →
`_finalize`). Hand-picked edge cases pin: the F2P single-call scenario
(`initialLevel=0`, `levels=[41]` → restored `0`, the leak fixed); no-call
(`levels=[]` → `0`); and the multi-call case (`levels=[41,43]` → `41`, the level
before the last adjustment).
