# mapping.md — pytest-dev__pytest-7236

## Symbol binding (file:line @ base_commit c98bc4cd3d687fe9b392d8eecd905627191d4f06)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_deferTeardown` / `problem_spec_deferTeardown` / `correct_deferTeardown` | the teardown-postponement decision inside `TestCaseFunction.runtest` | `src/_pytest/unittest.py:207-232` (the changed condition at line 223 @ base_commit) |
| `teardownDeferralRule` | the post-patch guard `self.config.getoption("usepdb") and not _is_skipped(self.obj)`, taken inside the synchronous (`else`) branch of the `is_async_function(self.obj)` test | `src/_pytest/unittest.py:213-224` |

## What `runtest` does (post-patch, the modeled decision)

```python
def runtest(self):
    ...
    if is_async_function(self.obj):
        self._testcase(self)                       # async path: no postponement
    else:
        ...
        if self.config.getoption("usepdb") and not _is_skipped(self.obj):
            self._explicit_tearDown = self._testcase.tearDown
            setattr(self._testcase, "tearDown", lambda *args: None)   # postpone
        ...
```

The modeled value is the Boolean "was teardown postponement arranged for this
test case" — i.e. whether the `if` body (storing the bound `tearDown` aside and
installing a no-op) executed.

## Lean ↔ Python type bijection (G-CONF + G-AX use this)

| Lean | Python observable | source |
|---|---|---|
| `isAsync : Bool` | `is_async_function(self.obj)` | `_pytest.compat.is_async_function`; selects the `if`/`else` branch in `runtest` |
| `usePdb : Bool` | `self.config.getoption("usepdb")` truthiness | the `--pdb` option |
| `skipped : Bool` | `_is_skipped(self.obj)` == `bool(getattr(self.obj, "__unittest_skip__", False))` | post-patch helper added at end of `unittest.py` |
| `result : Bool` | the postponement was arranged (`self._explicit_tearDown` was set and `tearDown` replaced by the no-op) | the `if` body in `runtest` |

`result = True` iff `not isAsync and usePdb and not skipped`.

## Callee provenance + flag deps

The new `_is_skipped(obj)` helper introduced by the patch is the per-object
truthiness of the `__unittest_skip__` attribute:
`bool(getattr(obj, "__unittest_skip__", False))`. It is NOT axiomatized — its
result is the modeled Boolean observable `skipped`. The two other patch sites
(`collect`'s `skipped = _is_skipped(cls)` and the xunit-fixture's
`if _is_skipped(self):`) replace `getattr(..., "__unittest_skip__", <falsey>)`
with `_is_skipped(...)`; since both old call sites only consumed the value in a
Boolean context, those two edits are truthiness-preserving refactors with no
observable behavior change (no separate F2P test exercises them differently).
The only behavior change observable by the F2P test is the added
`and not _is_skipped(self.obj)` guard in `runtest`, which is the modeled
decision.

Flag dependency: the postponement branch is reached only on the synchronous
(`is_async_function(self.obj) == False`) path; `usePdb` is the `--pdb` option.
Both are fuzzed in conformance_check.py.

## G-CONF fuzz seed

Pinned seed: **7236** (also pinned in meta.json `verifier_pins.conf_seed`). The
input space (3 Booleans = 8 points) is enumerated exhaustively in addition to the
seeded fuzz loop.
