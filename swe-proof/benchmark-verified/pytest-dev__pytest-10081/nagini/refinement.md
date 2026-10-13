# refinement.md — pytest-dev__pytest-10081

The operation-by-operation correspondence between `model.py`'s implementation
(the `postpone_teardown` impl region and the deep `marked_skipped` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The teardown-postponement guard — `TestCaseFunction.runtest` (`src/_pytest/unittest.py:319`)

Gold hunk:
```
-            if self.config.getoption("usepdb") and not _is_skipped(self.obj):
+            # We need to consider if the test itself is skipped, or the whole class.
+            assert isinstance(self.parent, UnitTestCase)
+            skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)
+            if self.config.getoption("usepdb") and not skipped:
                 self._explicit_tearDown = self._testcase.tearDown
                 setattr(self._testcase, "tearDown", lambda *args: None)
```

| # | model.py impl op (`postpone_teardown`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `usepdb: bool` | `self.config.getoption("usepdb")` | R | the `--pdb` option observed as a bool (mapping.md §2). |
| A2 | `marked_skipped(item.obj_skip)` | `_is_skipped(self.obj)` | A-reference | the unchanged probe is modelled **deeply**: `marked_skipped(flag) == flag` and `obj_skip` records `_is_skipped(self.obj)` exactly (probe returns `bool(getattr(obj, "__unittest_skip__", False))`). No consumed axiom; G-AX (axiom_check.py) validates `marked_skipped == _is_skipped` against the real callee on the real `@unittest.skip` decorator (mapping.md §3.1). |
| A3 | `marked_skipped(item.class_skip)` | `_is_skipped(self.parent.obj)` | A-reference | the **newly added** second call to the same unchanged probe, on the enclosing class. `class_skip` records `_is_skipped(self.parent.obj)` exactly; same deep model + G-AX check as A2. |
| A4 | `skipped = marked_skipped(item.obj_skip) or marked_skipped(item.class_skip)` | `skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)` | I | identical boolean `or` of the two probe results. |
| A5 | `if usepdb and not skipped: return True` else `return False` | `if self.config.getoption("usepdb") and not skipped:` then run the postponement body | I + R | identical boolean guard `usepdb and not skipped`. `Result()==True` ⇔ the guard is true ⇔ the body runs (sets `self._explicit_tearDown = self._testcase.tearDown` and replaces `tearDown` with a no-op so the instance teardown is deferred); `Result()==False` ⇔ the body is skipped and unittest's own skip handling governs teardown (mapping.md §2). |
| A6 | (omitted) | `assert isinstance(self.parent, UnitTestCase)` | I | a static type assertion with no observable effect for the modeled inputs (`self.parent` is always a `UnitTestCase`, created by `UnitTestCase.collect`); does not affect the guard's truth value (mapping.md §2). |

The discriminating content of the change — also considering the *enclosing
class's* skip marker, not only the test callable's — lives in step A3 (the added
`marked_skipped(item.class_skip)` disjunct). The pre-patch guard considered only the
callable (`not _is_skipped(self.obj)`); `model_prepatch.py` reproduces that
(`skipped = marked_skipped(item.obj_skip)` only) and **fails** the postcondition
`Result() == (usepdb and not (marked_skipped(item.obj_skip) or
marked_skipped(item.class_skip)))` on the case `class_skip=True, obj_skip=False,
usepdb=True` — exactly the spec sensing the change (G-DIFF). That is the
behaviour the F2P test `test_pdb_teardown_skipped_for_classes[@unittest.skip]`
observes: the class-skipped test's `tearDown` must NOT run under `--pdb`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation involved in the
change — combining the two skip probes with `or` — is modelled **deeply** (the
`or` over the two boolean facets, step A4), not hidden behind an axiom. The skip
probe `_is_skipped` is **unchanged** by the patch and fully expressible, so it
is an **A-reference** deep model (`marked_skipped`), validated == the real callee by
G-AX, NOT a consumed axiom. There is **no `@ContractOnly` axiom** in this bundle
(no opaque unchanged callee the proof must trust). The `meta.json` axioms array
is empty by design.

## C. verify(model) ⇒ resolved

`postpone_teardown` verifies only if its result equals
`under_debugger and not (marked_skipped(obj_skip) or marked_skipped(class_skip))`
(steps A4–A5), i.e. only if the enclosing class's skip marker suppresses
postponement just as the callable's does. By R (`usepdb` bool, `Result()` ⇔
guard truth ⇔ body runs)
and the A-reference validations (deep `marked_skipped` == real `_is_skipped` on both
sites), the verified guard equals the gold guard
`usepdb and not (_is_skipped(self.obj) or _is_skipped(self.parent.obj))` on the
tested inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited probe — and the gold
patch resolves (G-RESOLVE). The single trust point is the A-reference of PLAN
§1.1: the deep model `marked_skipped` equals the real `_is_skipped` (G-AX); there is
no consumed axiom to trust.
