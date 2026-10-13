# mapping.md — pytest-dev__pytest-10081

Binds every `model.py` symbol to its repository counterpart at
`base_commit = da9a2b584eb7a6c7e924b2621ed0ddaeca0a7bea`, states the type
abstraction, and gives the provenance of the one deeply-modelled probe.

Repo file under change: `src/_pytest/unittest.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `postpone_teardown(item, under_debugger)` | the teardown-postponement decision inside `TestCaseFunction.runtest` — `src/_pytest/unittest.py:319-321` | the modeled changed code: the predicate guarding whether instance teardown is deferred under `--pdb` |
| `TestItem.obj_skip` | `_is_skipped(self.obj)` where `self.obj` is the test callable — `src/_pytest/unittest.py:319` (pre-patch), `:318` (post-patch) | bool facet: does the test callable carry the skip marker |
| `TestItem.class_skip` | `_is_skipped(self.parent.obj)` where `self.parent` is the `UnitTestCase` and `.obj` the enclosing class — added at `src/_pytest/unittest.py:318-319` post-patch | bool facet: does the enclosing test-case class carry the skip marker |
| `marked_skipped(flag)` *(deep model — A-reference)* | `_is_skipped(obj)` — `src/_pytest/unittest.py:412-414`: `return bool(getattr(obj, "__unittest_skip__", False))` | unchanged probe the changed code calls; modelled deeply as the read of the boolean `__unittest_skip__` skip flag |
| `under_debugger` | `self.config.getoption("usepdb")` — `src/_pytest/unittest.py:319` | bool input: the `--pdb` option |
| `Result()` (the bool returned) | the truth of the guard `... and not skipped`, i.e. whether the branch body runs and sets `self._explicit_tearDown = self._testcase.tearDown` + replaces `tearDown` with a no-op (`src/_pytest/unittest.py:320-321`) | observable: was the instance teardown postponed |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view):
`if self.config.getoption("usepdb") and not _is_skipped(self.obj):`
(`src/_pytest/unittest.py:319`) — guarded only by the test callable's skip
marker. Post-patch:
```
assert isinstance(self.parent, UnitTestCase)
skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)
if self.config.getoption("usepdb") and not skipped:
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.obj` (an unbound test method object that may carry `__unittest_skip__`) | `TestItem.obj_skip: bool` | `obj_skip == bool(getattr(self.obj, "__unittest_skip__", False))` = `_is_skipped(self.obj)` |
| `self.parent.obj` (the enclosing `unittest.TestCase` subclass, may carry `__unittest_skip__` from `@unittest.skip` on the class) | `TestItem.class_skip: bool` | `class_skip == bool(getattr(self.parent.obj, "__unittest_skip__", False))` = `_is_skipped(self.parent.obj)` |
| `self.config.getoption("usepdb")` | `under_debugger: bool` | identity (the option is observed as a boolean) |
| running the branch body (postpone teardown) | `Result() == True` | the guard `usepdb and not skipped` is exactly the truth value `postpone_teardown` returns |
| `_is_skipped(obj)` -> `bool` | `marked_skipped(flag) -> bool` | `_is_skipped(obj)` reads `__unittest_skip__` on `obj`; `marked_skipped` reads the corresponding boolean facet. The probe returns `bool(getattr(..., False))`, so its value is exactly the boolean skip flag — modelled as the identity on that flag (deep, not axiomatized). |

`assert isinstance(self.parent, UnitTestCase)` (added by the patch) is a static
type assertion that does not change runtime behaviour for the modeled inputs;
the `self.parent` is always a `UnitTestCase` for a `TestCaseFunction` (it is the
collector that creates the item — `UnitTestCase.collect` at
`src/_pytest/unittest.py:80-85` yields `TestCaseFunction.from_parent(self, ...)`).
It carries no observable effect beyond enabling the `self.parent.obj` access and
is omitted from the model (mapping is total on the `class_skip` facet).

## 3. Deeply-modelled probe (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `marked_skipped` deep model ↔ `_is_skipped` (A-reference)
**Callee:** `_pytest.unittest._is_skipped(obj)` —
`src/_pytest/unittest.py:412-414`:
```python
def _is_skipped(obj) -> bool:
    """Return True if the given object has been marked with @unittest.skip."""
    return bool(getattr(obj, "__unittest_skip__", False))
```
This probe is **unchanged** by the patch (the patch only adds a *second* call to
it, on `self.parent.obj`). It is fully expressible, so it is modelled **deeply**
as `marked_skipped(flag) == flag` — the boolean facet `obj_skip` / `class_skip`
records exactly `_is_skipped(self.obj)` / `_is_skipped(self.parent.obj)`. There
is **no consumed `@ContractOnly` axiom**; the proof depends on no opaque callee.

`@unittest.skip` sets `__unittest_skip__ = True` on the decorated object (the
class or the function), per CPython `Lib/unittest/case.py`'s `skip()` decorator.
A class decorated with `@unittest.skip` therefore has
`_is_skipped(self.parent.obj) == True`, while its individual (non-decorated) test
methods have `_is_skipped(self.obj) == False` — exactly the discriminating case
(`class_skip=True, obj_skip=False`) the F2P test exercises.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`_pytest.unittest._is_skipped`, applies the real `@unittest.skip` decorator to
classes and methods (alone, combined, neither), and asserts:
(a) the deep model `marked_skipped(flag) == _is_skipped(obj)` where `flag` is the
recorded facet, on every boundary combination; and (b) the full modeled
decision `postpone_teardown` reproduces the post-patch repo guard
`usepdb and not (_is_skipped(self.obj) or _is_skipped(self.parent.obj))` and that
the pre-patch guard `usepdb and not _is_skipped(self.obj)` differs precisely on
the class-skipped case. Exit 0 iff sound. It imports only stdlib `unittest` plus
the real `_pytest.unittest` module the patch edits (run in-container).
