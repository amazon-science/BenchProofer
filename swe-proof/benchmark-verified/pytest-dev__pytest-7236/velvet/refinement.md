# refinement.md — pytest-dev__pytest-7236

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `markedSkipped` and `teardownPostponed` `do` blocks) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. This bundle has **no axiom** and
**no `axiom_check.py`** (G-AX = skip): the only callee the changed deferral
calls is `_is_skipped`, itself a changed function modeled as a sub-method
(callee-under-spec), not an unchanged callee.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The deferral site — `TestCaseFunction.runtest` (`unittest.py:220`)

Gold hunk:
```
- if self.config.getoption("usepdb"):
+ if self.config.getoption("usepdb") and not _is_skipped(self.obj):
      self._explicit_tearDown = self._testcase.tearDown
      setattr(self._testcase, "tearDown", lambda *args: None)
```
This guard sits in the `else` branch of `if is_async_function(self.obj):`, so it
is reached only for non-async tests. Entering the branch DEFERS teardown
(`postpone = true`); not entering it leaves the no-op `tearDown` stub absent and
the real `tearDown` runs in-line — except for a skipped test, whose method body
(and therefore `tearDown`/`setUp` via the autouse fixture) never executes.

| # | Solution.lean impl op (`teardownPostponed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `asyncTest : Bool` | `is_async_function(self.obj)` (the enclosing `if`) | R | `bool` ↔ `Bool` (mapping.md §2). The async branch bypasses the guard, modeled by the `!asyncTest` conjunct. |
| A2 | param `debuggerActive : Bool` | `self.config.getoption("usepdb")` | R | the `--pdb` option boolean ↔ `Bool` (mapping.md §2). |
| A3 | `let skipped ← markedSkipped skipMarked` | `_is_skipped(self.obj)` | I | the new helper call; transliterated as the identity on the skip-mark boolean (markedSkipped's spec). callee-under-spec, discharged via `markedSkipped_correct`. |
| A4 | `!asyncTest && debuggerActive && !skipped` returned as `postpone` | the full guard `usepdb and not _is_skipped(self.obj)`, within the non-async `else` | I + R | boolean conjunction of A1–A3; `postpone = true` ↔ deferral branch taken (mapping.md §2). The `not _is_skipped(...)` ⇔ `!skipped` is the single behavioural change. |

Discriminating content of the change — a skip-marked test under the debugger
must NOT have teardown deferred — lives in the `!skipMarked` conjunct of
`postpone`. The pre-patch guard had no such conjunct;
`Solution_prepatch.lean` reproduces that (`postpone = !asyncTest &&
debuggerActive`) and **fails** the frozen `ensures` exactly when `skipMarked`
holds (G-DIFF), which is the F2P case (`@unittest.skip` test under `--pdb`).

## B. The skip-mark query — `_is_skipped` (new helper)

Gold hunk: adds `def _is_skipped(obj): return bool(getattr(obj,
"__unittest_skip__", False))`.

| # | Solution.lean construct (`markedSkipped`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `skipMarked : Bool` | `bool(getattr(obj, "__unittest_skip__", False))` | R | the truthiness of the skip-mark attribute ↔ `Bool` (mapping.md §2). |
| B2 | `return skipMarked` | `return bool(...)` | I | `_is_skipped` returns exactly its argument's skip-mark boolean; the model's identity spec is that surfacing. |

No separate failing prepatch for `markedSkipped`: it is a newly-added pure
surfacing of an existing read; its content has no independently-observable
pre-patch behaviour (the spec must stay byte-identical, G-DIFF). Its role is to
feed the deferral exclusion (site A), which the site-A prepatch already
exercises.

## C. The two refactor hunks — `collect` / `_make_xunit_fixture` (not modeled)

Gold hunks 1–2 replace `getattr(cls, "__unittest_skip__", False)` and
`getattr(self, "__unittest_skip__", None)` by `_is_skipped(cls)` /
`_is_skipped(self)`. These are **behaviour-preserving refactors**:
`_is_skipped(x)` is `bool(getattr(x, "__unittest_skip__", False))`, and both
former expressions were already used in a boolean context (`if not skipped`,
`if getattr(...):`), where `getattr(self, ..., None)` and `bool(getattr(self,
..., False))` are truthiness-identical. They route the same read through the new
helper and change nothing the F2P/P2P tests observe — confirmed by P2P tests
`test_unittest_skip_issue148`, `test_unittest_skip_issue1169` continuing to
pass. They are therefore not independently modeled (no kind-3 op; nothing
changed behaviourally).

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, I (no A). The one operation that genuinely *changed* — adding
the skip exclusion to the teardown-deferral guard — is modeled **deeply** (the
closed boolean expression of `teardownPostponed`, step A4), not hidden behind an
axiom. The helper it calls is itself modeled (callee-under-spec, site B).

## E. verify(Solution) ⇒ resolved

`teardownPostponed` verifies only if `postpone` equals `!asyncTest &&
debuggerActive && !skipMarked` (A4) — i.e. teardown is deferred under the
debugger only for a non-async, non-skipped test. By R (`bool ↔ Bool`,
mapping.md §2) the verified decision equals the patched guard
`usepdb and not _is_skipped(self.obj)` within the non-async `else`. For a
skip-marked test under `--pdb` the decision is `false`, so teardown is NOT
deferred and the skipped test's real `tearDown` never runs — exactly the F2P
assertion `tracked == []` and `* 1 skipped in *`. By G-CONF the R/I
transliteration agrees with the patched source expression on the full boolean
cube + fuzz. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point (no axiom).
