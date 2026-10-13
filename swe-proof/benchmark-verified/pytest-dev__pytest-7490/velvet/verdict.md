# P2 adversarial audit — pytest-dev__pytest-7490

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
entry=none, evalBefore=none, evalAfter=some x (dynamic-add clause): finalXfail=some x, but prepatch/partial impls yield none. This is the discriminating clause the fix introduces and the F2P tests (test_dynamic_xfail_set_during_runtest_failed, ..._passed_strict) exercise.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -73,16 +73,9 @@
   do
     -- impl-start
     let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
     xfailed := match xfailed with
       | some x => some x
       | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
     return xfailed
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -72,18 +72,7 @@
   ensures stored = finalXfail entry evalBefore evalAfter
   do
     -- impl-start
-    let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
-    return xfailed
+    return entry
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -73,13 +73,6 @@
   do
     -- impl-start
     let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
     xfailed := match xfailed with
       | some x => some x
       | none   => evalAfter
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -72,18 +72,7 @@
   ensures stored = finalXfail entry evalBefore evalAfter
   do
     -- impl-start
-    let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
-    return xfailed
+    return finalXfail entry evalAfter evalBefore
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -72,18 +72,7 @@
   ensures stored = finalXfail entry evalBefore evalAfter
   do
     -- impl-start
-    let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
-    return xfailed
+    return evalAfter
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -72,18 +72,7 @@
   ensures stored = finalXfail entry evalBefore evalAfter
   do
     -- impl-start
-    let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
-    return xfailed
+    return none
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -73,17 +73,13 @@
   do
     -- impl-start
     let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
     xfailed := match xfailed with
       | some x => some x
       | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
     xfailed := match xfailed with
       | some x => some x
       | none   => evalAfter
-    return xfailed
+    return evalBefore
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -72,18 +72,7 @@
   ensures stored = finalXfail entry evalBefore evalAfter
   do
     -- impl-start
-    let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
-    return xfailed
+    return refresh entry evalAfter
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The marker-evaluation callee that produces an xfail
@@ -72,18 +72,7 @@
   ensures stored = finalXfail entry evalBefore evalAfter
   do
     -- impl-start
-    let mut xfailed : Option Xfail := entry
-    -- Before the body is entered: settle the determination if not already known.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalBefore
-    -- The body runs here; it may establish a determination dynamically.
-    -- After the body has finished: settle again against the markers now present,
-    -- so a determination established while the body ran is observed.
-    xfailed := match xfailed with
-      | some x => some x
-      | none   => evalAfter
-    return xfailed
+    return refresh (refresh evalAfter evalBefore) entry
     -- impl-end
 
 prove_correct resolveDynamicXfail by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The marker-evaluation callee that produces an xfail
   determination from the item's current markers is taken as a given primitive
   and modeled parametrically: its result is the abstract `Option Xfail`
   value (`none` = no xfail determination, `some _` = an xfail determination),
   so the spec holds for every possible result of that callee. Its relevant
   behaviour (deterministic in the marker set; yields `some _` exactly when an
   xfail marker is present) is validated against the real callee by G-AX
   (axiom_check.py). There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable content of an xfail determination: the reason to report, and
   the two flags downstream reporting consults. These are the only fields the
   desired behaviour carries through; everything else about the determination is
   orthogonal (mapping.md §2). The determination is passed through UNCHANGED, so
   its content is pinned by exact equality, not merely by presence. -/
structure Xfail where
  reason : String
  run    : Bool
  strict : Bool
  deriving DecidableEq

/- One determination step: keep an already-made determination; otherwise adopt a
   freshly-evaluated one. Mirrors the "evaluate only if not already known" guard
   the reporting machinery relies on (a determination, once made, is stable). -/
def refresh (current fresh : Option Xfail) : Option Xfail :=
  match current with
  | some x => some x
  | none   => fresh

/- The determination the reporting machinery must observe. Starting from the
   determination known on entry, it is refreshed once against the markers present
   when the body is entered, and AGAIN against the markers present once the body
   has finished — so a determination that only becomes available while the body
   runs (e.g. a marker added dynamically during the run) is still observed and
   not lost. Pinned by the method `ensures`. -/
def finalXfail (entry evalBefore evalAfter : Option Xfail) : Option Xfail :=
  refresh (refresh entry evalBefore) evalAfter

@[grind] lemma refresh_some (x : Xfail) (f : Option Xfail) :
    refresh (some x) f = some x := rfl
@[grind] lemma refresh_none (f : Option Xfail) :
    refresh none f = f := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the xfail determination across a single test body's execution.
   `entry` is the determination known before the body is scheduled; `evalBefore`
   is the determination from the markers present as the body is entered;
   `evalAfter` is the determination from the markers present once the body has
   finished (which may now include a marker added dynamically while the body
   ran). The determination handed to reporting must reflect the markers present
   AFTER the body finished whenever none was established earlier — otherwise a
   dynamically-added xfail determination is silently dropped. -/
method resolveDynamicXfail
    (entry : Option Xfail) (evalBefore : Option Xfail) (evalAfter : Option Xfail)
    return (stored : Option Xfail)
  ensures stored = finalXfail entry evalBefore evalAfter
  do
    -- impl-start
    return refresh (refresh entry evalBefore) evalAfter
    -- impl-end

prove_correct resolveDynamicXfail by
  loom_solve
  simp [finalXfail, refresh]
```

Prepatch bug re-encoded as an attack: `True`.

Spec = single total functional equation `stored = finalXfail entry evalBefore evalAfter` (= refresh (refresh entry evalBefore) evalAfter) over universally-quantified Option Xfail inputs. No axiom, no opaque/answer-key symbol in impl region; evalBefore/evalAfter are plain params => ungrounded-oracle echo structurally impossible. 9 same-spec wrong impls (partial-domain: atk_3/atk_5; boundary/constant: atk_6; ignore-all: atk_2; arg-swap/reorder: atk_4/atk_9; drop-middle: atk_8; control-flow-effect/discard: atk_1 prepatch-bug, atk_7) all verified with `bash scripts/lean_verify.sh <f>`, all EXIT=1 rejected on ensures_1 (residue = the nested-refresh/finalXfail normal form; atk_2 residue: entry = match(match entry|none=>evalBefore)|none=>evalAfter; atk_5 residue: evalAfter = same).

Positive control atk_ctrl (correct, structurally distinct nested refresh) EXIT=0, clean, no sorry => non-vacuous. same_spec=True verified for ALL 10 files via markers.same_spec/get_backend('velvet'). RESOLVE STEP VACUOUS: zero verifying wrong impls, so no faithful refined patch exists to materialize/run through run_resolve; verify=>correct not falsified. Refinement audit: every leg R/A-reference/I, no kind-3; the changed op (post-yield second settle, step 5) modeled concretely as refresh _ evalAfter (not axiom-hidden); only abstracted callee evaluate_xfail_marks unchanged, modeled parametrically as inputs (A-reference, G-AX). prepatch (Solution_prepatch.lean) reproduces the bug and fails ensures on exactly the entry=none/evalBefore=none/evalAfter=some clause. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
entry=none, evalBefore=none, evalAfter=some x (dynamic-add clause): finalXfail=some x, but prepatch/partial impls yield none. This is the discriminating clause the fix introduces and the F2P tests (test_dynamic_xfail_set_during_runtest_failed, ..._passed_strict) exercise.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The marker-evaluation callee that produces an xfail
   determination from the item's current markers is taken as a given primitive
   and modeled parametrically: its result is the abstract `Option Xfail`
   value (`none` = no xfail determination, `some _` = an xfail determination),
   so the spec holds for every possible result of that callee. Its relevant
   behaviour (deterministic in the marker set; yields `some _` exactly when an
   xfail marker is present) is validated against the real callee by G-AX
   (axiom_check.py). There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable content of an xfail determination: the reason to report, and
   the two flags downstream reporting consults. These are the only fields the
   desired behaviour carries through; everything else about the determination is
   orthogonal (mapping.md §2). The determination is passed through UNCHANGED, so
   its content is pinned by exact equality, not merely by presence. -/
structure Xfail where
  reason : String
  run    : Bool
  strict : Bool
  deriving DecidableEq

/- One determination step: keep an already-made determination; otherwise adopt a
   freshly-evaluated one. Mirrors the "evaluate only if not already known" guard
   the reporting machinery relies on (a determination, once made, is stable). -/
def refresh (current fresh : Option Xfail) : Option Xfail :=
  match current with
  | some x => some x
  | none   => fresh

/- The determination the reporting machinery must observe. Starting from the
   determination known on entry, it is refreshed once against the markers present
   when the body is entered, and AGAIN against the markers present once the body
   has finished — so a determination that only becomes available while the body
   runs (e.g. a marker added dynamically during the run) is still observed and
   not lost. Pinned by the method `ensures`. -/
def finalXfail (entry evalBefore evalAfter : Option Xfail) : Option Xfail :=
  refresh (refresh entry evalBefore) evalAfter

@[grind] lemma refresh_some (x : Xfail) (f : Option Xfail) :
    refresh (some x) f = some x := rfl
@[grind] lemma refresh_none (f : Option Xfail) :
    refresh none f = f := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the xfail determination across a single test body's execution.
   `entry` is the determination known before the body is scheduled; `evalBefore`
   is the determination from the markers present as the body is entered;
   `evalAfter` is the determination from the markers present once the body has
   finished (which may now include a marker added dynamically while the body
   ran). The determination handed to reporting must reflect the markers present
   AFTER the body finished whenever none was established earlier — otherwise a
   dynamically-added xfail determination is silently dropped. -/
method resolveDynamicXfail
    (entry : Option Xfail) (evalBefore : Option Xfail) (evalAfter : Option Xfail)
    return (stored : Option Xfail)
  ensures stored = finalXfail entry evalBefore evalAfter
  do
    -- impl-start
    return refresh (refresh entry evalBefore) evalAfter
    -- impl-end

prove_correct resolveDynamicXfail by
  loom_solve
  simp [finalXfail, refresh]
```

Prepatch bug re-encoded as an attack: `True`.

Spec = single total functional equation `stored = finalXfail entry evalBefore evalAfter` (= refresh (refresh entry evalBefore) evalAfter) over universally-quantified Option Xfail inputs. No axiom, no opaque/answer-key symbol in impl region; evalBefore/evalAfter are plain params => ungrounded-oracle echo structurally impossible. 9 same-spec wrong impls (partial-domain: atk_3/atk_5; boundary/constant: atk_6; ignore-all: atk_2; arg-swap/reorder: atk_4/atk_9; drop-middle: atk_8; control-flow-effect/discard: atk_1 prepatch-bug, atk_7) all verified with `bash scripts/lean_verify.sh <f>`, all EXIT=1 rejected on ensures_1 (residue = the nested-refresh/finalXfail normal form; atk_2 residue: entry = match(match entry|none=>evalBefore)|none=>evalAfter; atk_5 residue: evalAfter = same).

Positive control atk_ctrl (correct, structurally distinct nested refresh) EXIT=0, clean, no sorry => non-vacuous. same_spec=True verified for ALL 10 files via markers.same_spec/get_backend('velvet'). RESOLVE STEP VACUOUS: zero verifying wrong impls, so no faithful refined patch exists to materialize/run through run_resolve; verify=>correct not falsified. Refinement audit: every leg R/A-reference/I, no kind-3; the changed op (post-yield second settle, step 5) modeled concretely as refresh _ evalAfter (not axiom-hidden); only abstracted callee evaluate_xfail_marks unchanged, modeled parametrically as inputs (A-reference, G-AX). prepatch (Solution_prepatch.lean) reproduces the bug and fails ensures on exactly the entry=none/evalBefore=none/evalAfter=some clause. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: patched pytest_runtest_call (src/_pytest/skipping.py:248), whose observable effect is the value left under xfailed_key by hook completion (mapping.md §1; makereport is unchanged and reads exactly that value). Spec: `stored = finalXfail entry evalBefore evalAfter` where finalXfail = refresh(refresh entry evalBefore) evalAfter and refresh keeps the first `some`, else adopts the fresh value.

Verified against the real repo at base_commit 7f7a36478 and the gold patch (dataset instance.patch, byte-verified). Stored-value dataflow of the PATCHED hook:
- entry := item._store.get(xfailed_key, None)  (pre-yield read)
- mid := if entry is None then evaluate_xfail_marks(item) [=evalBefore] and store it, else entry  ==> mid = refresh(entry, evalBefore)
- (guarded xfail raise) fires iff mid is some x with run=False
- yield (body runs; a dynamically-added marker does NOT mutate the store)
- post-yield: re-read store (= mid), then if None set to evaluate_xfail_marks(item) [=evalAfter]  ==> final = refresh(mid, evalAfter) = refresh(refresh(entry,evalBefore),evalAfter) = finalXfail. MATCHES spec exactly.

Checked the only branch that could diverge — the run=False xfail("[NOTRUN]") raise, which aborts before the post-yield block. It fires only when mid = some x; but then refresh(some x, evalAfter) = some x = mid, so finalXfail collapses to precisely the value already stored. No divergence (this branch is also excluded from the fuzz domain per mapping.md §2.1 as run=True is fixed, but it is sound regardless).

Field projection (dropping Xfail.raises) is safe: refresh always returns one of its two input Option Xfail values verbatim (never merges fields), so it cannot conflate two distinct Xfail objects — the stored object is exactly one of entry/evalBefore/evalAfter, so equality on (reason,run,strict) plus the omitted raises is preserved by identity of the selected object.

Parametric callee evaluate_xfail_marks is UNCHANGED by the patch; modeled by quantifying evalBefore/evalAfter over all Option Xfail (no consumed axiom), so the spec is sound for any real callee output; G-AX (axiom_check.py) validates purity + marker-presence properties against the real callee (real code at :200 confirms: returns None with no xfail marker, Xfail(reason,run,strict,raises) once present). same_spec(Solution, Solution_prepatch, velvet) = True; Solution.lean verifies EXIT=0.

The spec is neither too strong nor drifting: it exactly reproduces the real stored determination for every (entry,evalBefore,evalAfter) triple, including the fix's discriminating case entry=none, evalBefore=none, evalAfter=some _ (dynamic add), where both spec and real repo yield evalAfter. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet _lean_spec_view: impl region + prove_correct body elided) screened clean by leakage.screen (hard_failures=[]). same_spec(Solution, Solution_prepatch)=True: the two differ only in the elided impl region, so the projected spec is patch-neutral. Independent review of the spec view content — structure Xfail{reason,run,strict}; refresh/finalXfail pure model with `finalXfail entry evalBefore evalAfter = refresh (refresh entry evalBefore) evalAfter`; ensures stored = finalXfail entry evalBefore evalAfter; and doc comments about a determination being refreshed against markers present when the body is entered and AGAIN after it finishes so a dynamically-added marker is not lost. This is a faithful behavioral characterization of the PUBLIC problem_statement (issue title: 'Dynamically adding xfail marker in test no longer ignores failure'; body: request.node.add_marker(mark) added inside the test body must be treated like a static xfail again). No gold-patch discriminators appear: no xfailed_key, _store, evaluate_xfail_marks, pytest_runtest_call, yield, '[NOTRUN]', no changed-function name (uses invented resolveDynamicXfail), no file/line refs. The three-moment (entry/before/after) abstraction is the natural spec derivable from the publicly-described dynamic-marker scenario, not an echo of the patch's code shape. Repo-internal binding details live in mapping.md/refinement.md, which are audit docs outside the G-LEAK-projected spec view. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.