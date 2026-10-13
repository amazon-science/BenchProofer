# refinement.md — pytest-dev__pytest-7490

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveDynamicXfail` `do` block, over the pure model `refresh`/`finalXfail`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep/
parametric model validated == the real callee by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The modeled function — `pytest_runtest_call` (`src/_pytest/skipping.py:248`)

Relevant gold hunk:
```
-    if not item.config.option.runxfail:
-        if xfailed and not xfailed.run:
-            xfail("[NOTRUN] " + xfailed.reason)
+    if xfailed and not item.config.option.runxfail and not xfailed.run:
+        xfail("[NOTRUN] " + xfailed.reason)

     yield

+    # The test run may have added an xfail mark dynamically.
+    xfailed = item._store.get(xfailed_key, None)
+    if xfailed is None:
+        item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)
```
The behaviourally-observable change is the **post-`yield` block**: re-read the
stored determination and, if none is established, evaluate the markers again
(now possibly including one added during the body) and store the result. The
`runxfail` guard rewrite is a pure boolean-form refactor (same truth value),
test-neutral, and orthogonal to which determination is stored.

| # | Solution.lean impl op (`resolveDynamicXfail`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `entry : Option Xfail` parameter | `xfailed = item._store.get(xfailed_key, None)` (pre-yield read) | R | the stored `Optional[Xfail]` ↔ `Option Xfail` (mapping.md §2). G-CONF seeds `xfailed_key` with `entry`. |
| 2 | `evalBefore`, `evalAfter : Option Xfail` parameters | the two `evaluate_xfail_marks(item)` results (pre- and post-`yield`) | A-reference | the UNCHANGED callee is modeled **parametrically** by its `Option Xfail` results; G-AX validates the real callee is a pure function of the marker set reflecting markers present at call time (mapping.md §3.1). No consumed axiom: the spec is quantified over all results. |
| 3 | pre-body settle: `xfailed := match xfailed with some x => some x \| none => evalBefore` | pre-yield `if xfailed is None: ... = evaluate_xfail_marks(item)` | I | identical "evaluate only if not already known" guard; `refresh entry evalBefore`. G-CONF transliterates it. |
| 4 | the gap between the two `match` steps | `yield` (the test body runs; it may add a marker dynamically) | R | the body's only modeled effect is that the post-body marker evaluation (`evalAfter`) may now differ from `evalBefore` (mapping.md §2). |
| 5 | post-body settle: `xfailed := match xfailed with some x => some x \| none => evalAfter` | the new post-yield block (`xfailed = ...get(...)`; `if xfailed is None: ... = evaluate_xfail_marks(item)`) | I | identical guard applied a second time; `refresh _ evalAfter`. **This is the fix the patch introduces**; G-CONF transliterates it. |
| 6 | `return xfailed` (`= finalXfail entry evalBefore evalAfter`) | the value left under `xfailed_key` when the hook completes | R | the stored `Optional[Xfail]` reporting (`pytest_runtest_makereport`, unchanged) consults. mapping.md §1. |

Discriminating content of the change — the case `entry = none`, `evalBefore =
none`, `evalAfter = some _` (a determination that only becomes available while the
body runs). The spec pins `stored = finalXfail entry evalBefore evalAfter`, which
equals `evalAfter` here; the pre-patch settles only once (step 3) and never
reconsiders, yielding `none`. `Solution_prepatch.lean` reproduces that and
**fails** the `ensures` exactly on this clause (G-DIFF; the unsolved goal is the
`entry/evalBefore → evalAfter` discrepancy).

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
second settle of the stored determination after the body finishes — is modeled
**concretely** (step 5, an I op over `refresh`), not hidden behind an axiom. The
only abstracted callee, `evaluate_xfail_marks` (step 2), is **unchanged** by the
patch and modeled parametrically (its results are inputs), validated by G-AX.

## verify(Solution) ⇒ resolved

`resolveDynamicXfail` verifies only if its result equals `finalXfail entry
evalBefore evalAfter` — i.e. the determination established at any of the three
moments is retained, including one that first becomes available after the body
(steps 5–6). By R (`Optional[Xfail] ↔ Option Xfail`; the unchanged reporting
hook reads exactly the stored value) the verified resolution equals the gold
patch's stored determination on the tested inputs; by G-AX the parametric model
of `evaluate_xfail_marks` matches the real callee (A-reference); by G-CONF the
R/I transliteration agrees with the REAL patched `pytest_runtest_call` over ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and an audited callee — and the gold patch
resolves (G-RESOLVE). The two F2P tests (`test_dynamic_xfail_set_during_runtest_
failed`, `..._passed_strict`) add an xfail marker inside the test body — exactly
the `entry=none, evalBefore=none, evalAfter=some _` clause the spec pins and the
prepatch drops.
