# refinement.md — pytest-dev__pytest-10081

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`shouldDeferCleanup` `do` block plus the deep model `shouldDefer`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + narrative by G-EQ. This bundle has **no A legs** (no axioms,
no `:|` stubs), so the entire correspondence is R/I and is covered end-to-end by
G-CONF against the real `_is_skipped` callee.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change

Gold hunk (`src/_pytest/unittest.py`, inside `TestCaseFunction.runtest`):
```python
-            if self.config.getoption("usepdb") and not _is_skipped(self.obj):
+            # We need to consider if the test itself is skipped, or the whole class.
+            assert isinstance(self.parent, UnitTestCase)
+            skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)
+            if self.config.getoption("usepdb") and not skipped:
                 self._explicit_tearDown = self._testcase.tearDown
                 setattr(self._testcase, "tearDown", lambda *args: None)
```

The guarded block postpones the test's post-run cleanup so an active interactive
debugger can inspect instance state. Pre-patch the guard's notion of "skipped"
consulted ONLY the test method (`_is_skipped(self.obj)`); a test whose enclosing
class was decorated `@unittest.skip` (so the method itself is not marked, but the
class is) was treated as not-skipped, its cleanup was postponed, and the
postponed cleanup was then forced to run — raising inside `tearDown` for a test
that should never have run (the issue's `NameError`). The patch broadens
"skipped" to `_is_skipped(self.obj) or _is_skipped(self.parent.obj)` so a
class-level skip also suppresses the postponement.

## shouldDeferCleanup — the postponement decision (`unittest.py:319` patched)

| # | Solution.lean impl op (`shouldDeferCleanup`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `debuggerActive : Bool` | `self.config.getoption("usepdb")` truthiness | R | `bool ↔ Bool` identity; result of the unchanged `config.getoption` callee (mapping.md §2, §3). |
| 2 | parameter `unitSkipped : Bool` | `_is_skipped(self.obj)` | R | `bool ↔ Bool` identity; result of the unchanged `_is_skipped` callee on the test method object (mapping.md §3). |
| 3 | parameter `groupSkipped : Bool` | `_is_skipped(self.parent.obj)` | R | `bool ↔ Bool` identity; result of the unchanged `_is_skipped` callee on the enclosing class object — the new call site the patch adds (mapping.md §3). |
| 4 | `let skipped : Bool := unitSkipped \|\| groupSkipped` | `skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)` | I | boolean `or` transliterated; `\|\| ↔ or` (mapping.md §2). |
| 5 | `if debuggerActive && !skipped then return true else return false` | `if self.config.getoption("usepdb") and not skipped:` (postpone) | I | the unchanged guard, transliterated; `&& / not ↔ and / not`. `out = true` ↔ entering the postpone block (set `_explicit_tearDown`, replace cleanup with no-op); `out = false` ↔ not postponing (mapping.md §2). |

The `assert isinstance(self.parent, UnitTestCase)` line the patch adds is a type
assertion with no observable behaviour (the parent of a `TestCaseFunction` is
always a `UnitTestCase`) — it has no impl op and is R-identity (mapping.md §3).
The body the guard controls (`self._explicit_tearDown = ...; setattr(...)`) is
unchanged and is the R-identity consequence of `out = true`; it is not modeled
op-by-op because the only thing the patch changes is the boolean guard.

## Discriminating content + prepatch

The single behavioural change is step 4/3: the decision now consults
`groupSkipped`. The discriminating input is
`(debuggerActive, unitSkipped, groupSkipped) = (true, false, true)` — debugger
active, test method not itself skipped, but the enclosing class skipped:
- patched: `skipped = false || true = true` ⇒ guard `true && !true = false` ⇒
  `out = false` — cleanup NOT postponed (the skipped test's `tearDown` is left to
  the framework, which never runs it; F2P
  `test_pdb_teardown_skipped_for_classes[@unittest.skip]` passes);
- pre-patch: `skipped = false` (group ignored) ⇒ `true && !false = true` ⇒
  `out = true` — cleanup postponed and then forced, running `tearDown` for a
  skipped test (the issue's failure).

`Solution_prepatch.lean` restores `skipped := unitSkipped` (the enclosing group's
marker ignored). `prove_correct` **fails** exactly on the `.true.false.true`
case (the spec demands `out = false`, the buggy skeleton produces `out = true`) —
the single independently-fixed behaviour (G-DIFF). The frozen spec is
byte-identical across both files.

## No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one thing that genuinely changed — widening the
"skipped" predicate to also consult the enclosing group — is concrete boolean
logic modeled directly (step 4, an `I` op). The two callees whose results are
consumed (`config.getoption`, `_is_skipped`) are **unchanged** and modeled as
R-identity `Bool` inputs, not axioms: their results are taken at face value and
G-CONF routes the inputs through the *real* `_is_skipped` over objects with
varied marker encodings, refuting the R legs. There is **no consumed axiom and
no `:|` stub**, so G-AX is not applicable and G-CONF carries the full R/I burden.

## verify(Solution) ⇒ resolved

`shouldDeferCleanup` verifies only if it postpones exactly when the debugger is
active AND neither the unit nor its enclosing group is skipped. By R
(`bool ↔ Bool`, `||/&&/not ↔ or/and/not`, `_is_skipped`/`getoption` results as
inputs) the verified method equals the patched guard on every input; by G-CONF
the R/I transliteration agrees with `patch.diff`'s behaviour on 100 008 inputs
(full 2³ boundary + fuzz over real marker encodings) and disagrees with the
unpatched repo on the class-skip discriminator. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The single trust point (no axioms) is refinement
fidelity, mechanized by G-CONF and audited by G-EQ.
