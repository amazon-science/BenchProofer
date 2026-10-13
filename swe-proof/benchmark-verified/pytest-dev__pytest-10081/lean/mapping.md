# mapping.md — pytest-dev__pytest-10081

## Modeled function

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_deferTeardown` / `problem_spec_deferTeardown` / `correct_deferTeardown` | `TestCaseFunction.runtest` (the `--pdb` teardown-deferral guard) | `src/_pytest/unittest.py:316-322` @ `da9a2b584eb7a6c7e924b2621ed0ddaeca0a7bea` |

## What is modeled

The patch changes one boolean decision inside `runtest`, taken on the `else`
(non-async) branch:

```python
# pre-patch
if self.config.getoption("usepdb") and not _is_skipped(self.obj):
    self._explicit_tearDown = self._testcase.tearDown
    setattr(self._testcase, "tearDown", lambda *args: None)

# post-patch
assert isinstance(self.parent, UnitTestCase)
skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)
if self.config.getoption("usepdb") and not skipped:
    self._explicit_tearDown = self._testcase.tearDown
    setattr(self._testcase, "tearDown", lambda *args: None)
```

The body of the `if` (capture `tearDown` and stub it out so it can be replayed
after the pdb prompt) is the act of "specially deferring teardown". The modeled
result `deferTeardown : Bool` is whether that `if` is taken.

## Lean ↔ Python type / value bijection (used by G-CONF, G-AX)

| Python observable | Lean datum | bijection |
|---|---|---|
| `self.config.getoption("usepdb")` (truthiness) | `pdbEnabled : Bool` | `True ↔ true`, `False ↔ false` |
| `_is_skipped(self.obj)` — test method has `__unittest_skip__` attr truthy | `testItselfSkipped : Bool` | `True ↔ true`, `False ↔ false` |
| `_is_skipped(self.parent.obj)` — containing class has `__unittest_skip__` attr truthy | `classSkipped : Bool` | `True ↔ true`, `False ↔ false` |
| the `if` guard is taken (teardown captured + stubbed) | `result : Bool` | taken ↔ `true` |

`_is_skipped(obj)` is defined in the same module
(`src/_pytest/unittest.py:412-414`) as
`bool(getattr(obj, "__unittest_skip__", False))` — a pure boolean predicate over
the object's marker attribute. Both `self.obj` (the test method) and
`self.parent.obj` (the test class) are passed through the SAME predicate. Its
two-way boolean outcome is the observable that enters the model directly as
`testItselfSkipped` / `classSkipped`; it is an UNCHANGED dependency, not modeled
internally.

## Callee provenance + flag deps

- `_is_skipped` — UNCHANGED by the patch; its boolean result is an input
  observable, not an axiom (no `opaque`/`axiom` consumed). No flag dependency:
  `__unittest_skip__` is set by `@unittest.skip` / `@pytest.mark.skip`
  decorators on the method or the class respectively.
- `self.config.getoption("usepdb")` — UNCHANGED; truthiness enters as
  `pdbEnabled`.
- `self.parent` / `UnitTestCase` — the patch adds an `assert isinstance(...)`
  guard; structurally `self.parent.obj` is the containing class object whose
  skip marker is the new observable. The assertion does not alter behavior on
  any valid run (a `TestCaseFunction`'s parent is always a `UnitTestCase`).

## G-CONF fuzz seed

Pinned seed: **10081** (also recorded in meta.json `verifier_pins.conf_seed`).
