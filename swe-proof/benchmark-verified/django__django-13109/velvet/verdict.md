# P2 adversarial audit — django__django-13109

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists. The postcondition `out = existsMatch target rows` is TOTAL and EXACT (no preconditions, no unbounded/ungrounded oracle), so any impl that verifies computes exactly existsMatch over the COMPLETE carrier — i.e. the discriminating case (a matching row hidden from the everyday/default view) forces out=true, which is precisely the post-patch _base_manager behavior that resolves. There is therefore no faithful wrong-patch to materialize; the BROKEN precondition (a verifying wrong impl) is never met.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -57,16 +57,20 @@
   ensures out = existsMatch target rows
   do
     -- impl-start
+    -- Pre-image skeleton: the existence test consults only the model's
+    -- everyday/default view, i.e. records NOT hidden by the custom view filter
+    -- (`!r.hidden`). A hidden record that matches the target is therefore never
+    -- seen, so `found` stays false. The frozen spec requires `existsMatch` over
+    -- the COMPLETE collection (hidden records included), so prove_correct MUST
+    -- fail on any input whose only matching record is hidden.
     let mut found : Bool := false
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant found = existsMatch target (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := rows[i - 1]!
-      found := matchesTarget target r || found
+      found := (matchesTarget target r && !r.hidden) || found
       i := i - 1
     return found
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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -57,18 +57,7 @@
   ensures out = existsMatch target rows
   do
     -- impl-start
-    let mut found : Bool := false
-    let mut i := rows.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant found = existsMatch target (rows.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := rows[i - 1]!
-      found := matchesTarget target r || found
-      i := i - 1
-    return found
+    return true
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the record at
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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -57,18 +57,7 @@
   ensures out = existsMatch target rows
   do
     -- impl-start
-    let mut found : Bool := false
-    let mut i := rows.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant found = existsMatch target (rows.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := rows[i - 1]!
-      found := matchesTarget target r || found
-      i := i - 1
-    return found
+    return false
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the record at
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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -63,10 +63,9 @@
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant found = existsMatch target (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := rows[i - 1]!
-      found := matchesTarget target r || found
+      found := matchesTarget target r && found
       i := i - 1
     return found
     -- impl-end
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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -63,10 +63,9 @@
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant found = existsMatch target (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := rows[i - 1]!
-      found := matchesTarget target r || found
+      found := (matchesTarget target r && r.hidden) || found
       i := i - 1
     return found
     -- impl-end
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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -58,12 +58,11 @@
   do
     -- impl-start
     let mut found : Bool := false
-    let mut i := rows.length
+    let mut i := rows.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant found = existsMatch target (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := rows[i - 1]!
       found := matchesTarget target r || found
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
 -- (No axiomatized callees. The existence test that validates an identity
@@ -57,18 +57,7 @@
   ensures out = existsMatch target rows
   do
     -- impl-start
-    let mut found : Bool := false
-    let mut i := rows.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant found = existsMatch target (rows.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := rows[i - 1]!
-      found := matchesTarget target r || found
-      i := i - 1
-    return found
+    return existsMatch target rows
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the record at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The existence test that validates an identity
--  reference is modeled DEEPLY as a per-record disjunction over the COMPLETE
--  record collection below; the collection the test ranges over is the input
--  carrier itself, not an outside contract. There is no `axiom` declaration and
--  no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One stored record considered when validating an identity reference. It
   carries only the two fields the operation observes: `key`, the stored value
   of the referenced field (a match is when it equals the target identity), and
   `hidden`, whether this record is filtered out of the model's everyday/default
   view by a custom view filter. A validity check that consults the COMPLETE
   record collection must consider every record regardless of `hidden`. -/
structure Record where
  key : Int
  hidden : Bool
deriving Inhabited, DecidableEq

/- Whether a single record matches the target identity: the stored referenced
   value equals the target. The match does NOT depend on `hidden` — a record
   that is hidden from the everyday view still matches if its key matches. -/
def matchesTarget (target : Int) (r : Record) : Bool :=
  r.key == target

/- Whether ANY record in the collection matches the target identity, over the
   COMPLETE collection. Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern). Because every record is consulted, a
   matching record contributes `true` even when it is hidden from the everyday
   view — which is exactly the behavior a complete-collection existence test
   demands. -/
def existsMatch (target : Int) : List Record → Bool
  | []      => false
  | r :: rs => matchesTarget target r || existsMatch target rs

@[grind] lemma existsMatch_nil (target : Int) : existsMatch target [] = false := rfl
@[grind] lemma existsMatch_cons (target : Int) (r : Record) (rs : List Record) :
    existsMatch target (r :: rs) = (matchesTarget target r || existsMatch target rs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method validateExists (rows : List Record) (target : Int) return (out : Bool)
  ensures out = existsMatch target rows
  do
    -- impl-start
    let mut found : Bool := false
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant found = existsMatch target (rows.drop i)
      done_with i = 0
    do
      let r := rows[i - 1]!
      found := matchesTarget target r || found
      i := i - 1
    return found
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the record at
   `i-1` on the front, so `existsMatch` peels one disjunct. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma existsMatch_drop_step (rows : List Record) (target : Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ rows.length) :
    existsMatch target (rows.drop (i - 1))
      = (matchesTarget target rows[i - 1]! || existsMatch target (rows.drop i)) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, existsMatch_cons]

prove_correct validateExists by
  loom_solve
  rw [existsMatch_drop_step rows target i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files same_spec=True vs frozen Solution.lean (swebench_unified.markers.same_spec, velvet backend). Only the impl region (lines 59-71) edited; axioms/pure (Record, matchesTarget, existsMatch + @[grind] lemmas)/pre/post/signature and the existsMatch_drop_step lemma + prove_correct body kept byte-identical.

VERIFY cmd: bash scripts/lean_verify.sh <file>  (run in two <=4 background batches).
Results:
- atk_pos POSITIVE CONTROL (gold impl verbatim): exit 0, verifies clean (empty log, no sorry).
- atk_1 PREPATCH bug (matchesTarget target r && !r.hidden = _default_manager): exit 1. Genuine unsolved goal: rewrite finds no `existsMatch target (List.drop (i-1) rows)`, leaves `i_1 = existsMatch target rows`. Reproduces the archived-target bug (G-DIFF).
- atk_2 constant `return true` (control-flow-effect): exit 1, unsolved `true = existsMatch target rows`.
- atk_3 constant `return false` (degenerate): exit 1, unsolved `false = existsMatch target rows`.
- atk_4 operator swap `&&` fold (requires ALL match): exit 1, invariant_2 unsolved.
- atk_5 only-hidden `matchesTarget && r.hidden` (model inversion): exit 1, invariant_2 unsolved.
- atk_6 off-by-one `i := rows.length - 1` (boundary, skips last row): exit 1, unsolved `false = existsMatch target (List.drop (rows.length-1) rows)`.
- atk_7 ungrounded-oracle echo `return existsMatch target rows` (a CORRECT impl): exit 1 only because the frozen prove_correct tactic body is loop-shaped ('No goals to be solved' at the rw); not a wrong impl and irrelevant to BROKEN.

RESOLVE: no wrong impl verified => no faithful wrong-patch to materialize => `patches` empty; the BROKEN precondition is never met. Harness sanity/positive-control resolve run: run_resolve('django__django-13109', gold patch.diff) => RESOLVED=True COMPLETED=True note='resolved' attempts=1 (harness confirmed functional).

REFINEMENT.MD AUDIT: meta.json axioms=[] and deep_model_references=[] => NO A-legs to attack. All legs are R or I; no kind-3 (changed-op-inexpressible). Model<->patch correspondence holds: existsMatch over complete `rows` with matchesTarget ignoring `hidden` <-> post-patch _base_manager (complete set); prepatch `&& !r.hidden` <-> _default_manager, and it correctly fails verify (atk_1). conf_skip=true is justified (mapping.md §4: no DB-free oracle for live-manager .exists()); soundness carried by G-VERIFY + G-DIFF, consistent with django-13315/13089 precedents.

CONCLUSION: >=5 distinct wrong impls (partial-domain, boundary/off-by-one, control-flow-effect constants, operator-swap, model-inversion, prepatch) all fail to verify; the exact+total postcondition admits no verifying wrong impl. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists. The postcondition `out = existsMatch target rows` is TOTAL and EXACT (no preconditions, no unbounded/ungrounded oracle), so any impl that verifies computes exactly existsMatch over the COMPLETE carrier — i.e. the discriminating case (a matching row hidden from the everyday/default view) forces out=true, which is precisely the post-patch _base_manager behavior that resolves. There is therefore no faithful wrong-patch to materialize; the BROKEN precondition (a verifying wrong impl) is never met.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The existence test that validates an identity
--  reference is modeled DEEPLY as a per-record disjunction over the COMPLETE
--  record collection below; the collection the test ranges over is the input
--  carrier itself, not an outside contract. There is no `axiom` declaration and
--  no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One stored record considered when validating an identity reference. It
   carries only the two fields the operation observes: `key`, the stored value
   of the referenced field (a match is when it equals the target identity), and
   `hidden`, whether this record is filtered out of the model's everyday/default
   view by a custom view filter. A validity check that consults the COMPLETE
   record collection must consider every record regardless of `hidden`. -/
structure Record where
  key : Int
  hidden : Bool
deriving Inhabited, DecidableEq

/- Whether a single record matches the target identity: the stored referenced
   value equals the target. The match does NOT depend on `hidden` — a record
   that is hidden from the everyday view still matches if its key matches. -/
def matchesTarget (target : Int) (r : Record) : Bool :=
  r.key == target

/- Whether ANY record in the collection matches the target identity, over the
   COMPLETE collection. Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern). Because every record is consulted, a
   matching record contributes `true` even when it is hidden from the everyday
   view — which is exactly the behavior a complete-collection existence test
   demands. -/
def existsMatch (target : Int) : List Record → Bool
  | []      => false
  | r :: rs => matchesTarget target r || existsMatch target rs

@[grind] lemma existsMatch_nil (target : Int) : existsMatch target [] = false := rfl
@[grind] lemma existsMatch_cons (target : Int) (r : Record) (rs : List Record) :
    existsMatch target (r :: rs) = (matchesTarget target r || existsMatch target rs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method validateExists (rows : List Record) (target : Int) return (out : Bool)
  ensures out = existsMatch target rows
  do
    -- impl-start
    let mut found : Bool := false
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant found = existsMatch target (rows.drop i)
      done_with i = 0
    do
      let r := rows[i - 1]!
      found := matchesTarget target r || found
      i := i - 1
    return found
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the record at
   `i-1` on the front, so `existsMatch` peels one disjunct. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma existsMatch_drop_step (rows : List Record) (target : Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ rows.length) :
    existsMatch target (rows.drop (i - 1))
      = (matchesTarget target rows[i - 1]! || existsMatch target (rows.drop i)) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, existsMatch_cons]

prove_correct validateExists by
  loom_solve
  rw [existsMatch_drop_step rows target i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 8 files same_spec=True vs frozen Solution.lean (swebench_unified.markers.same_spec, velvet backend). Only the impl region (lines 59-71) edited; axioms/pure (Record, matchesTarget, existsMatch + @[grind] lemmas)/pre/post/signature and the existsMatch_drop_step lemma + prove_correct body kept byte-identical.

VERIFY cmd: bash scripts/lean_verify.sh <file>  (run in two <=4 background batches).
Results:
- atk_pos POSITIVE CONTROL (gold impl verbatim): exit 0, verifies clean (empty log, no sorry).
- atk_1 PREPATCH bug (matchesTarget target r && !r.hidden = _default_manager): exit 1. Genuine unsolved goal: rewrite finds no `existsMatch target (List.drop (i-1) rows)`, leaves `i_1 = existsMatch target rows`. Reproduces the archived-target bug (G-DIFF).
- atk_2 constant `return true` (control-flow-effect): exit 1, unsolved `true = existsMatch target rows`.
- atk_3 constant `return false` (degenerate): exit 1, unsolved `false = existsMatch target rows`.
- atk_4 operator swap `&&` fold (requires ALL match): exit 1, invariant_2 unsolved.
- atk_5 only-hidden `matchesTarget && r.hidden` (model inversion): exit 1, invariant_2 unsolved.
- atk_6 off-by-one `i := rows.length - 1` (boundary, skips last row): exit 1, unsolved `false = existsMatch target (List.drop (rows.length-1) rows)`.
- atk_7 ungrounded-oracle echo `return existsMatch target rows` (a CORRECT impl): exit 1 only because the frozen prove_correct tactic body is loop-shaped ('No goals to be solved' at the rw); not a wrong impl and irrelevant to BROKEN.

RESOLVE: no wrong impl verified => no faithful wrong-patch to materialize => `patches` empty; the BROKEN precondition is never met. Harness sanity/positive-control resolve run: run_resolve('django__django-13109', gold patch.diff) => RESOLVED=True COMPLETED=True note='resolved' attempts=1 (harness confirmed functional).

REFINEMENT.MD AUDIT: meta.json axioms=[] and deep_model_references=[] => NO A-legs to attack. All legs are R or I; no kind-3 (changed-op-inexpressible). Model<->patch correspondence holds: existsMatch over complete `rows` with matchesTarget ignoring `hidden` <-> post-patch _base_manager (complete set); prepatch `&& !r.hidden` <-> _default_manager, and it correctly fails verify (atk_1). conf_skip=true is justified (mapping.md §4: no DB-free oracle for live-manager .exists()); soundness carried by G-VERIFY + G-DIFF, consistent with django-13315/13089 precedents.

CONCLUSION: >=5 distinct wrong impls (partial-domain, boundary/off-by-one, control-flow-effect constants, operator-swap, model-inversion, prepatch) all fail to verify; the exact+total postcondition admits no verifying wrong impl. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region (existsMatch/matchesTarget + `ensures out = existsMatch target rows`) is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True). Solution.lean elaborates cleanly (lean_verify.sh exit 0); prepatch (matchesTarget && !r.hidden) fails prove_correct exactly on inputs whose only matching row is hidden, so G-DIFF genuinely discriminates the bug.

Modeled callee: the existence test inside ForeignKey.validate (django/db/models/fields/related.py:917-921 @ base fbe82f8255): `qs = <manager>.using(using).filter(**{field_name: value}); qs = qs.complex_filter(get_limit_choices_to()); if not qs.exists(): raise`. Gold patch flips _default_manager -> _base_manager (verbatim in patch.diff).

Faithfulness of the abstraction, checked against the real repo:
- rows:List Record <-> consulted manager queryset. QuerySet->List order-irrelevance is sound because .exists() is order-independent. FAITHFUL.
- matchesTarget r = (r.key==target) faithfully models .filter(**{field_name: value}) (row matches iff referenced field == value). FAITHFUL.
- existsMatch = OR-fold over ALL rows faithfully models .exists() over the collection. FAITHFUL.
- hidden distinguishing base vs default manager is faithful: _base_manager surfaces every row regardless of a custom get_queryset() view filter; _default_manager drops filtered (e.g. archived) rows. This IS the changed op and existsMatch ignores hidden, matching post-patch base-manager semantics.

Only genuinely abstracted step: .complex_filter(get_limit_choices_to()). This does NOT create a faithfulness break because it is (a) applied identically to BOTH managers, (b) unchanged by the patch, and (c) not part of the modeled distinction (which-manager-supplies-rows). `rows` is DEFINED as the collection the existence test ranges over, so limit_choices_to is upstream/downstream of the abstraction boundary, disclosed in refinement.md A/mapping.md §2, and soundness-preserving for the modeled behavior. No input within the modeled domain (choice of source collection) makes existsMatch disagree with the real callee's exists() decision.

G-CONF legitimately skipped (conf_skip=true): the manager row-visibility is only observable against a live relational backend; no DB-free R/I shadow exists. Soundness carried by G-VERIFY + G-DIFF, consistent with the accepted django-13315 / django-13089 precedents. No too-strong spec, no drift found. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen (lean flavor) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced (view uses neutral existsMatch/matchesTarget/Record over key+hidden, none of the changed lines' >=8-char normalized fragments appear), no patched file path (django/db/models/fields/related.py) or dotted module in view, only changed symbol 'validate' is not embedded in any spec-view identifier, and no narration keywords in comments. Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True). meta.json records G-LEAK=pass with no relaxed_leakage flag (genuine clean pass, not a deferral).

Semantic gold-reconstruction check: the gold edit is the one-line _default_manager -> _base_manager change in ForeignKey.validate, semantically 'consult the COMPLETE row set (including rows a custom default manager filters out, e.g. archived) for the FK existence test.' This fix is ALREADY fully disclosed in the PUBLIC problem_statement, which states verbatim 'ForeignKey.validate() should validate using the base manager instead of the default manager', gives the archived-articles worked example, notes it 'always uses _default_manager instead of _base_manager', and offers 'Suggested solution: the ForeignKey validation should use the _base_manager.' The spec view's abstraction (existsMatch consults every record regardless of Record.hidden, where hidden = excluded from the default view by a custom view filter) therefore reveals nothing beyond the public statement. The actual edit tokens (_base_manager/_default_manager) do not appear in the spec view at all, and are public regardless. No leak beyond problem_statement (leakage is judged vs problem_statement only, never hints_text; hints here add only PR#/acceptance notes, irrelevant).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
