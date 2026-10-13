# P2 adversarial audit — django__django-14999

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no terminating same-spec wrong impl verifies. The postcondition totally pins out on both exhaustive, mutually-exclusive branches (beforeTable=afterTable -> out=[]; beforeTable != afterTable -> out = mainMove :: relationOps relations), so every behaviorally-wrong terminating impl leaves a FALSE postcondition goal that no tactic can close.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callee: whether any schema work is emitted is decided
@@ -73,24 +73,11 @@
   ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
   do
     -- impl-start
-    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
     if beforeTable = afterTable then
       return []
     else
-      -- The rename proceeds: emit the main-table move, then one rewrite per
-      -- dependent relation (built back-to-front so a single fold unfold is
-      -- available per loop step).
-      let mut result : List Int := []
-      let mut i := relations.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ relations.length
-        invariant result = relationOps (relations.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        result := (2 : Int) :: result
-        i := i - 1
-      return mainMove :: result
+      -- WRONG: emit only the main-table move, skip every dependent-relation rewrite.
+      return [mainMove]
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more relation
@@ -109,5 +96,4 @@
 
 prove_correct renameSchedule by
   loom_solve
-  rw [relationOps_drop_step relations i (by omega) (by omega)]
   simp_all
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
 -- (No axiomatized callee: whether any schema work is emitted is decided
@@ -73,20 +73,16 @@
   ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
   do
     -- impl-start
-    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
     if beforeTable = afterTable then
       return []
     else
-      -- The rename proceeds: emit the main-table move, then one rewrite per
-      -- dependent relation (built back-to-front so a single fold unfold is
-      -- available per loop step).
+      -- WRONG: start the fold at relations.length - 1, dropping one relation's rewrite.
       let mut result : List Int := []
-      let mut i := relations.length
+      let mut i := relations.length - 1
       while i > 0
         invariant 0 ≤ i ∧ i ≤ relations.length
         invariant result = relationOps (relations.drop i)
         done_with i = 0
-        decreasing i
       do
         result := (2 : Int) :: result
         i := i - 1
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
 -- (No axiomatized callee: whether any schema work is emitted is decided
@@ -73,24 +73,21 @@
   ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
   do
     -- impl-start
-    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
     if beforeTable = afterTable then
-      return []
-    else
-      -- The rename proceeds: emit the main-table move, then one rewrite per
-      -- dependent relation (built back-to-front so a single fold unfold is
-      -- available per loop step).
+      -- WRONG: emit the full schedule on the NOOP branch.
       let mut result : List Int := []
       let mut i := relations.length
       while i > 0
         invariant 0 ≤ i ∧ i ≤ relations.length
         invariant result = relationOps (relations.drop i)
         done_with i = 0
-        decreasing i
       do
         result := (2 : Int) :: result
         i := i - 1
       return mainMove :: result
+    else
+      -- WRONG: emit nothing on the proceeding branch.
+      return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more relation
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
 -- (No axiomatized callee: whether any schema work is emitted is decided
@@ -73,24 +73,17 @@
   ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
   do
     -- impl-start
-    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
-    if beforeTable = afterTable then
-      return []
-    else
-      -- The rename proceeds: emit the main-table move, then one rewrite per
-      -- dependent relation (built back-to-front so a single fold unfold is
-      -- available per loop step).
-      let mut result : List Int := []
-      let mut i := relations.length
-      while i > 0
-        invariant 0 ≤ i ∧ i ≤ relations.length
-        invariant result = relationOps (relations.drop i)
-        done_with i = 0
-        decreasing i
-      do
-        result := (2 : Int) :: result
-        i := i - 1
-      return mainMove :: result
+    -- WRONG: no noop guard at all; always emit the full proceeding schedule.
+    let mut result : List Int := []
+    let mut i := relations.length
+    while i > 0
+      invariant 0 ≤ i ∧ i ≤ relations.length
+      invariant result = relationOps (relations.drop i)
+      done_with i = 0
+    do
+      result := (2 : Int) :: result
+      i := i - 1
+    return mainMove :: result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more relation
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
 -- (No axiomatized callee: whether any schema work is emitted is decided
@@ -73,24 +73,20 @@
   ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
   do
     -- impl-start
-    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
     if beforeTable = afterTable then
       return []
     else
-      -- The rename proceeds: emit the main-table move, then one rewrite per
-      -- dependent relation (built back-to-front so a single fold unfold is
-      -- available per loop step).
+      -- WRONG: emit the main move TWICE before the relation rewrites.
       let mut result : List Int := []
       let mut i := relations.length
       while i > 0
         invariant 0 ≤ i ∧ i ≤ relations.length
         invariant result = relationOps (relations.drop i)
         done_with i = 0
-        decreasing i
       do
         result := (2 : Int) :: result
         i := i - 1
-      return mainMove :: result
+      return mainMove :: mainMove :: result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more relation
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
 -- (No axiomatized callee: whether any schema work is emitted is decided
@@ -73,24 +73,20 @@
   ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
   do
     -- impl-start
-    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
     if beforeTable = afterTable then
       return []
     else
-      -- The rename proceeds: emit the main-table move, then one rewrite per
-      -- dependent relation (built back-to-front so a single fold unfold is
-      -- available per loop step).
-      let mut result : List Int := []
+      -- WRONG: emit relation rewrites first, then the main move (reordered).
+      let mut result : List Int := [mainMove]
       let mut i := relations.length
       while i > 0
         invariant 0 ≤ i ∧ i ≤ relations.length
-        invariant result = relationOps (relations.drop i)
+        invariant result = relationOps (relations.drop i) ++ [mainMove]
         done_with i = 0
-        decreasing i
       do
         result := (2 : Int) :: result
         i := i - 1
-      return mainMove :: result
+      return result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes one more relation
@@ -109,5 +105,4 @@
 
 prove_correct renameSchedule by
   loom_solve
-  rw [relationOps_drop_step relations i (by omega) (by omega)]
   simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callee: whether any schema work is emitted is decided
--  entirely by the table-identity comparison, modeled deeply below. The
--  dependent-relation rewrites are spelled out as a per-relation fold of opaque
--  operation codes, not an axiomatized callee whose contract the proof
--  consumes.)
-- axioms-end

-- pure-start
/- One schedule entry per dependent relation: the schema rewrite each dependent
   relation contributes when the rename proceeds. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern). Each relation's
   rewrite group is one entry (a constant marker code, distinct from the
   main-table move's code): the spec pins one entry PER relation, in relation
   order. -/
def relationOps : List Int → List Int
  | []      => []
  | _ :: rs => (2 : Int) :: relationOps rs

@[grind] lemma relationOps_nil : relationOps [] = [] := rfl
@[grind] lemma relationOps_cons (r : Int) (rs : List Int) :
    relationOps (r :: rs) = (2 : Int) :: relationOps rs := rfl

/- The main-table move emitted first when the rename proceeds. -/
def mainMove : Int := 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A model-rename is applied to the database driven entirely by whether the
   stored table identifier actually changes. The operation is handed the stored
   table identifier the model used before the rename (`beforeTable`) and the one
   it uses after (`afterTable`), plus the collection of dependent relations
   (`relations`) — the foreign keys pointing at this model and the auto-created
   link tables for its many-to-many relations.

   (1) When the before- and after- identifiers are the SAME, the operation is
       observationally inert: it issues NO schema work at all — not the main
       table move, and crucially not the rewrites of the dependent relations.
       The emitted schedule of schema operations is EMPTY.

   (2) When the two identifiers DIFFER, the operation proceeds: it emits the
       main-table move FIRST, followed by one rewrite per dependent relation,
       in relation order. Under the per-relation marker abstraction (each
       relation's rewrite group is one schedule entry) the emitted schedule is
       exactly `mainMove :: relationOps relations`.

   Both branches are pinned exactly. Emitting nothing when the table identifier
   is unchanged is the noop requirement; on the proceeding branch the schedule
   must cover the main move AND every dependent relation — an operation that
   moves the main table but skips (some of) the dependent-relation rewrites
   does NOT satisfy this contract, nor does one that reorders the main move
   after the rewrites.

   The two table identifiers are modeled as `Int` (only their equality is
   observable to the schema layer). Each dependent relation is one element of a
   `List Int`. `relations` is read-only (not `mut`); the step never mutates it
   (directive 5). The emitted schedule is a `List Int` of operation codes. -/
method renameSchedule (beforeTable : Int) (afterTable : Int) (relations : List Int) return (out : List Int)
  ensures beforeTable = afterTable → out = []
  ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
  do
    -- impl-start
    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
    if beforeTable = afterTable then
      return []
    else
      -- The rename proceeds: emit the main-table move, then one rewrite per
      -- dependent relation (built back-to-front so a single fold unfold is
      -- available per loop step).
      let mut result : List Int := []
      let mut i := relations.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ relations.length
        invariant result = relationOps (relations.drop i)
        done_with i = 0
      do
        result := (2 : Int) :: result
        i := i - 1
      return mainMove :: result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes one more relation
   on the front, so `relationOps` peels one entry. The single goal `loom_solve`
   leaves for the loop body. -/
lemma relationOps_drop_step (relations : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ relations.length) :
    relationOps (relations.drop (i - 1)) = (2 : Int) :: relationOps (relations.drop i) := by
  have hlt : i - 1 < relations.length := by omega
  have hcons : relations.drop (i - 1) = relations[i - 1]! :: relations.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, relationOps_cons]

prove_correct renameSchedule by
  loom_solve
  rw [relationOps_drop_step relations i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL FULLY EXECUTED (velvet, project root; env swebench-lean).

SAME-SPEC: all 6 submitted attacks + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language (axioms/pure/pre/post + method ensures byte-identical; only impl region + elided prove_correct body edited).

VERIFY COMMANDS: bash scripts/lean_verify.sh <file>.lean ; run concurrently in two batches of 4 (background bash jobs), results collected.

### Results
- pos_control.lean (gold-faithful impl): EXIT 0, VERIFIES (no error/sorry). Positive control good.
- prepatch.lean (Solution_prepatch): EXIT 1, FAILS on clause 1 `beforeTable=afterTable -> out=[]` (unsolved goal, result_1 = relationOps (drop 0 relations)). Prepatch noop-guard bug reproduced (G-DIFF sensing). prepatch_reproduced=true.
- atk_1 (control-flow: proceed branch emits ONLY [mainMove], skips all relation rewrites = recorded P1 hole): EXIT 1, unsolved goal `relationOps relations = []` (false). REJECTED.
- atk_2 (boundary off-by-one: fold starts at relations.length-1, drops last relation): EXIT 1, unsolved goal `[] = relationOps (drop (length-1) relations)` (false). REJECTED.
- atk_3 (swapped branches: full schedule on noop, [] on proceed): EXIT 1, unsolved goals `mainMove :: result_1 = []` and proceed-branch mismatch (false). REJECTED.
- atk_4 (control-flow-effect: drop noop guard entirely, always emit schedule = prepatch variant): EXIT 1, unsolved goal `beforeTable=afterTable -> mainMove :: result_1 = []` (false). REJECTED.
- atk_5 (ungrounded/wrong-count: duplicate main move, out = mainMove :: mainMove :: rest): EXIT 1, unsolved goal `mainMove :: mainMove :: result_1 = mainMove :: relationOps relations` (false). REJECTED.
- atk_6 (reorder: relation rewrites first, main move last): EXIT 1, invariant/postcond unsolved (false). REJECTED.

Every failure is a GENUINELY FALSE proposition (behavioral mismatch), not a weak-proof gap — a total functional pin admits only the correct value. No submitted attack verifies => zero candidates => no resolve run required by protocol step 2. (No candidate patches materialized because no submitted wrong impl verifies.)

DIVERGENCE PROBE (documented, NOT submitted as an attack): atk_7.lean (unconditional `while j < 1 do j := 0` infinite loop, then `return [999]`) — same_spec=True, EXIT 0 VERIFIES. This is the universal partial-correctness vacuity (set_option loom.semantics.termination "partial", sanctioned by quickref.md for non-structurally-terminating impls) present in EVERY velvet bundle. It is EXCLUDED from the attack set because it admits NO faithful refined patch: no real Django `database_forwards` control flow refines to an unconditional infinite loop, so it cannot demonstrate a refinement-fidelity (G-EQ) defect. Submitting it would only force a spurious infinite-loop patch that trivially fails to resolve — a false BROKEN. It is a benchmark-wide methodology artifact, out of G-EQ scope.

REFINEMENT.MD LEG AUDIT (protocol step 3): axioms region EMPTY; NO A-consumed and NO A-reference legs (the changed operation is modeled DEEPLY per SPEC_GUIDE §0.7; G-AX skips legitimately, deep_model_references=[]). Legs: A1/A2 db_table str -> Int identity = R (only == observable); A3 dependent relations -> List Int slot = R (relations defined as exactly the non-skipped iterated related_objects + auto-created non-self-referential m2m link tables, matching real code models.py:319-368 — the m2m loop `continue`s on self-ref/non-auto-created, excluded from relations); A4 noop guard = I (identical to gold `if old_db_table == new_db_table: return`); A5 proceeding branch mainMove :: relationOps relations = R+I (alter_db_table main move code 1 FIRST, then one code-2 group per dependent relation, 1:1 with real emitted schedule). ALL legs are R or I; NO kind-3 (unexpressible changed op). Correspondence to real callees holds (verified against gold-applied worktree, git diff matches the noop-guard hunk verbatim).

VERDICT: SOUND. 6 distinct terminating same-spec wrong impls re-run, none verifies (all leave false postcondition goals); positive control verifies; prepatch reproduces the bug; refinement.md legs all R/I with holding correspondence; no A-leg soundness trust point (no axiom consumed/referenced). No verifying wrong impl has a faithful refined patch that fails to resolve. verify => correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no terminating same-spec wrong impl verifies. The postcondition totally pins out on both exhaustive, mutually-exclusive branches (beforeTable=afterTable -> out=[]; beforeTable != afterTable -> out = mainMove :: relationOps relations), so every behaviorally-wrong terminating impl leaves a FALSE postcondition goal that no tactic can close.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callee: whether any schema work is emitted is decided
--  entirely by the table-identity comparison, modeled deeply below. The
--  dependent-relation rewrites are spelled out as a per-relation fold of opaque
--  operation codes, not an axiomatized callee whose contract the proof
--  consumes.)
-- axioms-end

-- pure-start
/- One schedule entry per dependent relation: the schema rewrite each dependent
   relation contributes when the rename proceeds. Front-recursive so a single
   unfold is available per loop step (the Velvet fold pattern). Each relation's
   rewrite group is one entry (a constant marker code, distinct from the
   main-table move's code): the spec pins one entry PER relation, in relation
   order. -/
def relationOps : List Int → List Int
  | []      => []
  | _ :: rs => (2 : Int) :: relationOps rs

@[grind] lemma relationOps_nil : relationOps [] = [] := rfl
@[grind] lemma relationOps_cons (r : Int) (rs : List Int) :
    relationOps (r :: rs) = (2 : Int) :: relationOps rs := rfl

/- The main-table move emitted first when the rename proceeds. -/
def mainMove : Int := 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A model-rename is applied to the database driven entirely by whether the
   stored table identifier actually changes. The operation is handed the stored
   table identifier the model used before the rename (`beforeTable`) and the one
   it uses after (`afterTable`), plus the collection of dependent relations
   (`relations`) — the foreign keys pointing at this model and the auto-created
   link tables for its many-to-many relations.

   (1) When the before- and after- identifiers are the SAME, the operation is
       observationally inert: it issues NO schema work at all — not the main
       table move, and crucially not the rewrites of the dependent relations.
       The emitted schedule of schema operations is EMPTY.

   (2) When the two identifiers DIFFER, the operation proceeds: it emits the
       main-table move FIRST, followed by one rewrite per dependent relation,
       in relation order. Under the per-relation marker abstraction (each
       relation's rewrite group is one schedule entry) the emitted schedule is
       exactly `mainMove :: relationOps relations`.

   Both branches are pinned exactly. Emitting nothing when the table identifier
   is unchanged is the noop requirement; on the proceeding branch the schedule
   must cover the main move AND every dependent relation — an operation that
   moves the main table but skips (some of) the dependent-relation rewrites
   does NOT satisfy this contract, nor does one that reorders the main move
   after the rewrites.

   The two table identifiers are modeled as `Int` (only their equality is
   observable to the schema layer). Each dependent relation is one element of a
   `List Int`. `relations` is read-only (not `mut`); the step never mutates it
   (directive 5). The emitted schedule is a `List Int` of operation codes. -/
method renameSchedule (beforeTable : Int) (afterTable : Int) (relations : List Int) return (out : List Int)
  ensures beforeTable = afterTable → out = []
  ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations
  do
    -- impl-start
    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.
    if beforeTable = afterTable then
      return []
    else
      -- The rename proceeds: emit the main-table move, then one rewrite per
      -- dependent relation (built back-to-front so a single fold unfold is
      -- available per loop step).
      let mut result : List Int := []
      let mut i := relations.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ relations.length
        invariant result = relationOps (relations.drop i)
        done_with i = 0
      do
        result := (2 : Int) :: result
        i := i - 1
      return mainMove :: result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes one more relation
   on the front, so `relationOps` peels one entry. The single goal `loom_solve`
   leaves for the loop body. -/
lemma relationOps_drop_step (relations : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ relations.length) :
    relationOps (relations.drop (i - 1)) = (2 : Int) :: relationOps (relations.drop i) := by
  have hlt : i - 1 < relations.length := by omega
  have hcons : relations.drop (i - 1) = relations[i - 1]! :: relations.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, relationOps_cons]

prove_correct renameSchedule by
  loom_solve
  rw [relationOps_drop_step relations i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL FULLY EXECUTED (velvet, project root; env swebench-lean).

SAME-SPEC: all 6 submitted attacks + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language (axioms/pure/pre/post + method ensures byte-identical; only impl region + elided prove_correct body edited).

VERIFY COMMANDS: bash scripts/lean_verify.sh <file>.lean ; run concurrently in two batches of 4 (background bash jobs), results collected.

### Results
- pos_control.lean (gold-faithful impl): EXIT 0, VERIFIES (no error/sorry). Positive control good.
- prepatch.lean (Solution_prepatch): EXIT 1, FAILS on clause 1 `beforeTable=afterTable -> out=[]` (unsolved goal, result_1 = relationOps (drop 0 relations)). Prepatch noop-guard bug reproduced (G-DIFF sensing). prepatch_reproduced=true.
- atk_1 (control-flow: proceed branch emits ONLY [mainMove], skips all relation rewrites = recorded P1 hole): EXIT 1, unsolved goal `relationOps relations = []` (false). REJECTED.
- atk_2 (boundary off-by-one: fold starts at relations.length-1, drops last relation): EXIT 1, unsolved goal `[] = relationOps (drop (length-1) relations)` (false). REJECTED.
- atk_3 (swapped branches: full schedule on noop, [] on proceed): EXIT 1, unsolved goals `mainMove :: result_1 = []` and proceed-branch mismatch (false). REJECTED.
- atk_4 (control-flow-effect: drop noop guard entirely, always emit schedule = prepatch variant): EXIT 1, unsolved goal `beforeTable=afterTable -> mainMove :: result_1 = []` (false). REJECTED.
- atk_5 (ungrounded/wrong-count: duplicate main move, out = mainMove :: mainMove :: rest): EXIT 1, unsolved goal `mainMove :: mainMove :: result_1 = mainMove :: relationOps relations` (false). REJECTED.
- atk_6 (reorder: relation rewrites first, main move last): EXIT 1, invariant/postcond unsolved (false). REJECTED.

Every failure is a GENUINELY FALSE proposition (behavioral mismatch), not a weak-proof gap — a total functional pin admits only the correct value. No submitted attack verifies => zero candidates => no resolve run required by protocol step 2. (No candidate patches materialized because no submitted wrong impl verifies.)

DIVERGENCE PROBE (documented, NOT submitted as an attack): atk_7.lean (unconditional `while j < 1 do j := 0` infinite loop, then `return [999]`) — same_spec=True, EXIT 0 VERIFIES. This is the universal partial-correctness vacuity (set_option loom.semantics.termination "partial", sanctioned by quickref.md for non-structurally-terminating impls) present in EVERY velvet bundle. It is EXCLUDED from the attack set because it admits NO faithful refined patch: no real Django `database_forwards` control flow refines to an unconditional infinite loop, so it cannot demonstrate a refinement-fidelity (G-EQ) defect. Submitting it would only force a spurious infinite-loop patch that trivially fails to resolve — a false BROKEN. It is a benchmark-wide methodology artifact, out of G-EQ scope.

REFINEMENT.MD LEG AUDIT (protocol step 3): axioms region EMPTY; NO A-consumed and NO A-reference legs (the changed operation is modeled DEEPLY per SPEC_GUIDE §0.7; G-AX skips legitimately, deep_model_references=[]). Legs: A1/A2 db_table str -> Int identity = R (only == observable); A3 dependent relations -> List Int slot = R (relations defined as exactly the non-skipped iterated related_objects + auto-created non-self-referential m2m link tables, matching real code models.py:319-368 — the m2m loop `continue`s on self-ref/non-auto-created, excluded from relations); A4 noop guard = I (identical to gold `if old_db_table == new_db_table: return`); A5 proceeding branch mainMove :: relationOps relations = R+I (alter_db_table main move code 1 FIRST, then one code-2 group per dependent relation, 1:1 with real emitted schedule). ALL legs are R or I; NO kind-3 (unexpressible changed op). Correspondence to real callees holds (verified against gold-applied worktree, git diff matches the noop-guard hunk verbatim).

VERDICT: SOUND. 6 distinct terminating same-spec wrong impls re-run, none verifies (all leave false postcondition goals); positive control verifies; prepatch reproduces the bug; refinement.md legs all R/I with holding correspondence; no A-leg soundness trust point (no axiom consumed/referenced). No verifying wrong impl has a faithful refined patch that fails to resolve. verify => correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec(Solution,Solution_prepatch,velvet)=True). Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean fails on exactly `beforeTable=afterTable -> out=[]` (G-DIFF discriminating). Checked model vs real RenameModel.database_forwards at base_commit a754b82 + gold patch: Clause 1 (equal tables -> []) matches gold's `if old_db_table==new_db_table: return`; database_backwards delegates with swapped names and inherits the noop (equality symmetric). Clause 2 (out = mainMove :: relationOps relations) matches real emission order exactly: alter_db_table main move FIRST, then one rewrite group per related_object (FK alter_field) and per auto-created non-self-ref m2m (alter_db_table+alter_field pair). `relations` is defined as precisely the rewritten relations in iteration order (self-ref / non-auto-created through are excluded by def, matching the loop's `continue`), so one list slot <-> one rewrite group (code 2); the only abstraction is within a group (opaque). Edge relations=[] -> [1] on both sides. The clause-2 exactness is what closes the recorded P1 non-empty-only hole. The allow_migrate_model(...) whole-body guard is not carried, but that is the standard accepted modeling boundary (F2P/P2P use default router = True) and the refinement is transparent about it; not drift within the modeled domain. No input in the modeled domain disagrees with the real callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorously checked, both mechanically and semantically. same_spec(Solution, Solution_prepatch) = True (spec region byte-identical). Mechanical leakage.screen over the velvet spec view PASSES: no diff markers, patched file path 'django/db/migrations/operations/models.py' absent, no dotted module path, patched distinctive symbol 'database_forwards' absent from identifiers and comments, no narration terms (bug/fix/patch/...). Semantic review of the spec-view prose vs the public problem_statement: The problem_statement publicly states 'RenameModel with db_table should be a noop... A RenameModel operation that already has db_table defined must be a noop.' The spec view's discriminating postconditions ('beforeTable = afterTable -> out = []' i.e. issue NO schema work when the table identifier is unchanged) encode exactly this publicly-disclosed noop requirement; encoding a public required behavior as a contract is the spec's legitimate function, not a leak of the gold edit. The proceeding branch (main-table move first, then one rewrite per dependent relation) describes RenameModel's PRE-EXISTING, unchanged behavior (byte-identical to prepatch on that branch), not the gold change. The comment prose talks about table-identity equality gating schema work and dependent-relation rewrites in abstract Int/List Int modeling terms; it never names the patched symbol/file, never reproduces the gold-diff line (old_db_table == new_db_table / early return), and never narrates a bug or fix. Nothing in the spec view reveals the gold edit's location or mechanism beyond what the public task already tells the solver.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
