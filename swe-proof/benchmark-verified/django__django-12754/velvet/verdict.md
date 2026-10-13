# P2 adversarial audit — django__django-12754

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so there is no verifying-wrong-impl whose faithful refined patch could be materialized/resolved. The frozen spec pins the output completely.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -130,10 +130,9 @@
       invariant 0 ≤ i ∧ i ≤ derivedFields.length
       invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := derivedFields[i - 1]!
-      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
+      let _n := derivedFields[i - 1]!
+      result := [] ++ result
       i := i - 1
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -130,10 +130,9 @@
       invariant 0 ≤ i ∧ i ≤ derivedFields.length
       invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := derivedFields[i - 1]!
-      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
+      result := (if isMoved oldBaseFields newBaseFields n then [] else [n]) ++ result
       i := i - 1
     return result
     -- impl-end
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -124,18 +124,7 @@
   ensures ∀ n, n ∈ out → n ∈ derivedFields ∧ isMoved oldBaseFields newBaseFields n = true
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := derivedFields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ derivedFields.length
-      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := derivedFields[i - 1]!
-      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
-      i := i - 1
-    return result
+    return derivedFields
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -124,18 +124,7 @@
   ensures ∀ n, n ∈ out → n ∈ derivedFields ∧ isMoved oldBaseFields newBaseFields n = true
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := derivedFields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ derivedFields.length
-      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := derivedFields[i - 1]!
-      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
-      i := i - 1
-    return result
+    return derivedFields.filter (fun n => isMoved oldBaseFields newBaseFields n)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -125,16 +125,14 @@
   do
     -- impl-start
     let mut result : List Int := []
-    let mut i := derivedFields.length
-    while i > 0
+    let mut i := 0
+    while i < derivedFields.length
       invariant 0 ≤ i ∧ i ≤ derivedFields.length
-      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = derivedFields.length
     do
-      let n := derivedFields[i - 1]!
-      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
-      i := i - 1
+      let n := derivedFields[i]!
+      result := result ++ (if isMoved oldBaseFields newBaseFields n then [n] else [])
+      i := i + 1
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -130,9 +130,8 @@
       invariant 0 ≤ i ∧ i ≤ derivedFields.length
       invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := derivedFields[i - 1]!
+      let n := derivedFields[i]!
       result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
       i := i - 1
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -125,12 +125,11 @@
   do
     -- impl-start
     let mut result : List Int := []
-    let mut i := derivedFields.length
+    let mut i := derivedFields.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ derivedFields.length
       invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := derivedFields[i - 1]!
       result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
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
 -- (No axiomatized callees. The behaviour modeled here is a closed set computation
@@ -124,18 +124,7 @@
   ensures ∀ n, n ∈ out → n ∈ derivedFields ∧ isMoved oldBaseFields newBaseFields n = true
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := derivedFields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ derivedFields.length
-      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := derivedFields[i - 1]!
-      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
-      i := i - 1
-    return result
+    return derivedFields
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -156,5 +145,3 @@
 
 prove_correct movedBaseFields by
   loom_solve
-  rw [movedFold_drop_step oldBaseFields newBaseFields derivedFields i (by omega) (by omega)]
-  rw [‹result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)›]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed set computation
--  over three field-name collections: the base entity's fields before, the base
--  entity's fields after, and the newly created derived entity's own fields. No
--  unchanged library callee is consulted, so no callee contract is assumed. Every
--  step is an R/I refinement, validated against the real construction by
--  conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- Whether a single derived-entity field name `n` is one that must be sequenced.

   A name qualifies exactly when the base entity is present BOTH before and after
   the change AND the name was a field of the base before but is no longer a field
   of the base after — i.e. it was removed from the base. The presence of the base
   on both sides is carried as `Option (List Int)`: `none` means the base entity
   is absent from that side (so nothing qualifies); `some fields` carries the
   base's field-name set on that side. The decision is by PRESENCE on both sides,
   not by whether either field set is non-empty. -/
def isMoved (oldBase newBase : Option (List Int)) (n : Int) : Bool :=
  match oldBase, newBase with
  | some ob, some nb => decide (n ∈ ob) && decide (n ∉ nb)
  | _, _             => false

@[grind] lemma isMoved_none_left (newBase : Option (List Int)) (n : Int) :
    isMoved none newBase n = false := rfl
@[grind] lemma isMoved_none_right (oldBase : Option (List Int)) (n : Int) :
    isMoved oldBase none n = false := by
  cases oldBase <;> rfl

/- The field names of the derived entity that must be sequenced, in derived-field
   order: keep each derived field name that was removed from the base. This is the
   per-element expansion of the derived entity's field list. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
def movedFold (oldBase newBase : Option (List Int)) : List Int → List Int
  | []      => []
  | n :: ns => (if isMoved oldBase newBase n then [n] else [])
                 ++ movedFold oldBase newBase ns

@[grind] lemma movedFold_nil (oldBase newBase : Option (List Int)) :
    movedFold oldBase newBase [] = [] := rfl
@[grind] lemma movedFold_cons (oldBase newBase : Option (List Int))
    (n : Int) (ns : List Int) :
    movedFold oldBase newBase (n :: ns) =
      (if isMoved oldBase newBase n then [n] else []) ++ movedFold oldBase newBase ns := rfl

/- If the base entity is absent before the change, nothing qualifies. -/
@[grind] lemma movedFold_none_left (newBase : Option (List Int)) (ns : List Int) :
    movedFold none newBase ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [movedFold_cons, isMoved_none_left]; simpa using ih

/- If the base entity is absent after the change, nothing qualifies. -/
@[grind] lemma movedFold_none_right (oldBase : Option (List Int)) (ns : List Int) :
    movedFold oldBase none ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [movedFold_cons, isMoved_none_right]; simpa using ih

/- A sequenced name is always one of the derived entity's own fields (nothing is
   invented) and genuinely qualifies. Proven by induction; `@[grind]` so the
   corresponding postcondition discharges automatically. -/
@[grind] lemma movedFold_mem (oldBase newBase : Option (List Int)) (ns : List Int) :
    ∀ n, n ∈ movedFold oldBase newBase ns → n ∈ ns ∧ isMoved oldBase newBase n = true := by
  induction ns with
  | nil => intro n h; simp [movedFold] at h
  | cons c cs ih =>
      intro n h
      rw [movedFold_cons] at h
      by_cases hk : isMoved oldBase newBase c = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hnc | htail
        · subst hnc; exact ⟨List.mem_cons_self, hk⟩
        · obtain ⟨hmem, hkeep⟩ := ih n htail
          exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
      · rw [if_neg hk] at h
        rw [List.nil_append] at h
        obtain ⟨hmem, hkeep⟩ := ih n h
        exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a new derived entity is created that inherits from an existing base
   entity, some of the derived entity's own fields may be fields that were just
   removed from the base entity (moved down onto the subclass in the same step).
   Creating the derived entity must be sequenced AFTER those base fields are
   removed; otherwise the two definitions of the same field name collide.

   This routine determines exactly which of the derived entity's field names need
   that ordering: a field name qualifies iff the base entity exists both before
   and after the change and the name was a field of the base before but not after
   (it was removed from the base) — restricted to the derived entity's own fields.

   The base entity's field-name sets are read as optionals: `none` when the base
   entity is absent from that side of the change (then nothing qualifies),
   `some names` otherwise. Field names are modeled as distinct integer identifiers
   (`List Int`, mapping.md §2). The result is the list of qualifying derived-field
   names, in derived-field order.

   `oldBaseFields`, `newBaseFields` and `derivedFields` are read-only (none
   `mut`): the routine only reads them and builds a fresh result, mutating no
   input (directive 5). -/
method movedBaseFields (oldBaseFields : Option (List Int))
    (newBaseFields : Option (List Int)) (derivedFields : List Int)
    return (out : List Int)
  ensures out = movedFold oldBaseFields newBaseFields derivedFields
  ensures oldBaseFields = none → out = []
  ensures newBaseFields = none → out = []
  ensures ∀ n, n ∈ out → n ∈ derivedFields ∧ isMoved oldBaseFields newBaseFields n = true
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := derivedFields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ derivedFields.length
      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
      done_with i = 0
    do
      let n := derivedFields[i - 1]!
      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `movedFold` peels one keep-decision. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma movedFold_drop_step (oldBase newBase : Option (List Int)) (xs : List Int)
    (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    movedFold oldBase newBase (xs.drop (i - 1)) =
      (if isMoved oldBase newBase xs[i - 1]! then [xs[i - 1]!] else [])
        ++ movedFold oldBase newBase (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, movedFold_cons]

prove_correct movedBaseFields by
  loom_solve
  rw [movedFold_drop_step oldBaseFields newBaseFields derivedFields i (by omega) (by omega)]
  rw [‹result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL & RESULTS (all, verified with `bash scripts/lean_verify.sh <f>` from project root; same_spec confirmed True for every attack via swebench_unified.markers.same_spec + get_backend('velvet'); verifications run concurrently in two batches of 4).

WHY THE SPEC IS AIRTIGHT: method movedBaseFields carries FOUR ensures clauses, the first being an EXACT functional list-equality `out = movedFold oldBaseFields newBaseFields derivedFields`. This fully determines the return value (value AND order) for every input; the other three (none-left ⇒ [], none-right ⇒ [], membership+isMoved soundness) are redundant reinforcements. Any impl that verifies must equal movedFold exactly, so a behaviorally-wrong impl cannot pass. There are NO axioms and NO deep-model references (mapping.md §3, refinement.md §B/§C: G-AX=skip), so there is no ungrounded-oracle A-leg to exploit — the sole trust point is refinement fidelity (this + G-CONF), and the changed set-computation is modeled DEEPLY/concretely (isMoved/movedFold), not hidden behind a function-under-change axiom.

### ATTACKS (8 distinct same-spec wrong impls; impl region edited only, axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug, control-flow-effect): loop emits [] per element → returns []. lean_verify EXIT=1. Fails invariant_2 `result = movedFold ...(drop i)`. This is the recorded prepatch reproduction.
- atk_2 (negated oracle): keeps the fields NOT moved. EXIT=1, fails invariant_2.
- atk_3 (ungrounded echo): `return derivedFields` with the original loop-based proof left in place. EXIT=1 (stale proof `i` + unsolved goals).
- atk_4 (filter over-broad / ungrounded): `return derivedFields.filter isMoved` — behaviorally equivalent but keeps the loop proof. EXIT=1 (proof mismatch).
- atk_5 (order/control-flow): front-to-back loop appending on the right → reversed result. EXIT=1, rewrite of movedFold_drop_step fails (pattern absent) — exact-order equality broken.
- atk_6 (boundary/off-by-one): reads derivedFields[i] instead of [i-1]. EXIT=1, fails invariant_2.
- atk_7 (partial-domain): starts i at length-1, skipping the last derived field. EXIT=1, fails invariant_2.
- atk_8 (clean ungrounded, honest proof): `return derivedFields` with prove_correct reduced to bare loom_solve so the ONLY failure is the spec. EXIT=1 — leaves ensures_1 (∀n∈out, isMoved n=true), ensures_2 (newBase=none⇒[]), ensures_3 (oldBase=none⇒[]) unsolvable. Direct spec-level rejection.

POSITIVE CONTROL: pos.lean = exact gold impl (backward while-loop). lean_verify EXIT=0 (verifies, no sorry). (An honest filter-based correct alternative, pos2.lean, required a top-level helper lemma that alters the spec view, giving same_spec=False — correctly NOT counted as a same-spec impl; not needed.)

RESOLVE STEP: N/A. Protocol step 2 requires materializing+running a faithful patch ONLY for a wrong impl that VERIFIES. Zero same-spec wrong impls verify, so there is nothing to resolve; patches={} is correct and complete. No run_resolve run was needed and none is missing.

REFINEMENT AUDIT (refinement.md): legs A1=R, A2=R, A3=R (Option/List Int ↔ ModelState.fields bijections, mapping.md §2), A4=I (both-present guard ↔ Option×Option match), A5=I (element-wise set.difference∩intersection ↔ isMoved), A6=R+I (result names ↔ appended removal deps; base_app/base_name/False are R-identity constants). All legs are R or I — NO kind-3 inexpressible-changed-op, NO consumed axiom, NO A-reference. Model↔patch correspondence holds: movedFold = (old\new)∩derived over the derived carrier, exactly the gold hunk at autodetector.py:571-577. G-CONF (seed 12754) validates the R/I transliteration against the real patched callee. Verdict: SOUND (≥5 distinct attacks run, none breaks the spec).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so there is no verifying-wrong-impl whose faithful refined patch could be materialized/resolved. The frozen spec pins the output completely.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed set computation
--  over three field-name collections: the base entity's fields before, the base
--  entity's fields after, and the newly created derived entity's own fields. No
--  unchanged library callee is consulted, so no callee contract is assumed. Every
--  step is an R/I refinement, validated against the real construction by
--  conformance_check.py (G-CONF). See refinement.md §C.)
-- axioms-end

-- pure-start
/- Whether a single derived-entity field name `n` is one that must be sequenced.

   A name qualifies exactly when the base entity is present BOTH before and after
   the change AND the name was a field of the base before but is no longer a field
   of the base after — i.e. it was removed from the base. The presence of the base
   on both sides is carried as `Option (List Int)`: `none` means the base entity
   is absent from that side (so nothing qualifies); `some fields` carries the
   base's field-name set on that side. The decision is by PRESENCE on both sides,
   not by whether either field set is non-empty. -/
def isMoved (oldBase newBase : Option (List Int)) (n : Int) : Bool :=
  match oldBase, newBase with
  | some ob, some nb => decide (n ∈ ob) && decide (n ∉ nb)
  | _, _             => false

@[grind] lemma isMoved_none_left (newBase : Option (List Int)) (n : Int) :
    isMoved none newBase n = false := rfl
@[grind] lemma isMoved_none_right (oldBase : Option (List Int)) (n : Int) :
    isMoved oldBase none n = false := by
  cases oldBase <;> rfl

/- The field names of the derived entity that must be sequenced, in derived-field
   order: keep each derived field name that was removed from the base. This is the
   per-element expansion of the derived entity's field list. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern, plan §5.4). -/
def movedFold (oldBase newBase : Option (List Int)) : List Int → List Int
  | []      => []
  | n :: ns => (if isMoved oldBase newBase n then [n] else [])
                 ++ movedFold oldBase newBase ns

@[grind] lemma movedFold_nil (oldBase newBase : Option (List Int)) :
    movedFold oldBase newBase [] = [] := rfl
@[grind] lemma movedFold_cons (oldBase newBase : Option (List Int))
    (n : Int) (ns : List Int) :
    movedFold oldBase newBase (n :: ns) =
      (if isMoved oldBase newBase n then [n] else []) ++ movedFold oldBase newBase ns := rfl

/- If the base entity is absent before the change, nothing qualifies. -/
@[grind] lemma movedFold_none_left (newBase : Option (List Int)) (ns : List Int) :
    movedFold none newBase ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [movedFold_cons, isMoved_none_left]; simpa using ih

/- If the base entity is absent after the change, nothing qualifies. -/
@[grind] lemma movedFold_none_right (oldBase : Option (List Int)) (ns : List Int) :
    movedFold oldBase none ns = [] := by
  induction ns with
  | nil => rfl
  | cons n ns ih => rw [movedFold_cons, isMoved_none_right]; simpa using ih

/- A sequenced name is always one of the derived entity's own fields (nothing is
   invented) and genuinely qualifies. Proven by induction; `@[grind]` so the
   corresponding postcondition discharges automatically. -/
@[grind] lemma movedFold_mem (oldBase newBase : Option (List Int)) (ns : List Int) :
    ∀ n, n ∈ movedFold oldBase newBase ns → n ∈ ns ∧ isMoved oldBase newBase n = true := by
  induction ns with
  | nil => intro n h; simp [movedFold] at h
  | cons c cs ih =>
      intro n h
      rw [movedFold_cons] at h
      by_cases hk : isMoved oldBase newBase c = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hnc | htail
        · subst hnc; exact ⟨List.mem_cons_self, hk⟩
        · obtain ⟨hmem, hkeep⟩ := ih n htail
          exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
      · rw [if_neg hk] at h
        rw [List.nil_append] at h
        obtain ⟨hmem, hkeep⟩ := ih n h
        exact ⟨List.mem_cons_of_mem _ hmem, hkeep⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a new derived entity is created that inherits from an existing base
   entity, some of the derived entity's own fields may be fields that were just
   removed from the base entity (moved down onto the subclass in the same step).
   Creating the derived entity must be sequenced AFTER those base fields are
   removed; otherwise the two definitions of the same field name collide.

   This routine determines exactly which of the derived entity's field names need
   that ordering: a field name qualifies iff the base entity exists both before
   and after the change and the name was a field of the base before but not after
   (it was removed from the base) — restricted to the derived entity's own fields.

   The base entity's field-name sets are read as optionals: `none` when the base
   entity is absent from that side of the change (then nothing qualifies),
   `some names` otherwise. Field names are modeled as distinct integer identifiers
   (`List Int`, mapping.md §2). The result is the list of qualifying derived-field
   names, in derived-field order.

   `oldBaseFields`, `newBaseFields` and `derivedFields` are read-only (none
   `mut`): the routine only reads them and builds a fresh result, mutating no
   input (directive 5). -/
method movedBaseFields (oldBaseFields : Option (List Int))
    (newBaseFields : Option (List Int)) (derivedFields : List Int)
    return (out : List Int)
  ensures out = movedFold oldBaseFields newBaseFields derivedFields
  ensures oldBaseFields = none → out = []
  ensures newBaseFields = none → out = []
  ensures ∀ n, n ∈ out → n ∈ derivedFields ∧ isMoved oldBaseFields newBaseFields n = true
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := derivedFields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ derivedFields.length
      invariant result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)
      done_with i = 0
    do
      let n := derivedFields[i - 1]!
      result := (if isMoved oldBaseFields newBaseFields n then [n] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `movedFold` peels one keep-decision. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma movedFold_drop_step (oldBase newBase : Option (List Int)) (xs : List Int)
    (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    movedFold oldBase newBase (xs.drop (i - 1)) =
      (if isMoved oldBase newBase xs[i - 1]! then [xs[i - 1]!] else [])
        ++ movedFold oldBase newBase (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, movedFold_cons]

prove_correct movedBaseFields by
  loom_solve
  rw [movedFold_drop_step oldBaseFields newBaseFields derivedFields i (by omega) (by omega)]
  rw [‹result = movedFold oldBaseFields newBaseFields (derivedFields.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT PROTOCOL & RESULTS (all, verified with `bash scripts/lean_verify.sh <f>` from project root; same_spec confirmed True for every attack via swebench_unified.markers.same_spec + get_backend('velvet'); verifications run concurrently in two batches of 4).

WHY THE SPEC IS AIRTIGHT: method movedBaseFields carries FOUR ensures clauses, the first being an EXACT functional list-equality `out = movedFold oldBaseFields newBaseFields derivedFields`. This fully determines the return value (value AND order) for every input; the other three (none-left ⇒ [], none-right ⇒ [], membership+isMoved soundness) are redundant reinforcements. Any impl that verifies must equal movedFold exactly, so a behaviorally-wrong impl cannot pass. There are NO axioms and NO deep-model references (mapping.md §3, refinement.md §B/§C: G-AX=skip), so there is no ungrounded-oracle A-leg to exploit — the sole trust point is refinement fidelity (this + G-CONF), and the changed set-computation is modeled DEEPLY/concretely (isMoved/movedFold), not hidden behind a function-under-change axiom.

### ATTACKS (8 distinct same-spec wrong impls; impl region edited only, axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug, control-flow-effect): loop emits [] per element → returns []. lean_verify EXIT=1. Fails invariant_2 `result = movedFold ...(drop i)`. This is the recorded prepatch reproduction.
- atk_2 (negated oracle): keeps the fields NOT moved. EXIT=1, fails invariant_2.
- atk_3 (ungrounded echo): `return derivedFields` with the original loop-based proof left in place. EXIT=1 (stale proof `i` + unsolved goals).
- atk_4 (filter over-broad / ungrounded): `return derivedFields.filter isMoved` — behaviorally equivalent but keeps the loop proof. EXIT=1 (proof mismatch).
- atk_5 (order/control-flow): front-to-back loop appending on the right → reversed result. EXIT=1, rewrite of movedFold_drop_step fails (pattern absent) — exact-order equality broken.
- atk_6 (boundary/off-by-one): reads derivedFields[i] instead of [i-1]. EXIT=1, fails invariant_2.
- atk_7 (partial-domain): starts i at length-1, skipping the last derived field. EXIT=1, fails invariant_2.
- atk_8 (clean ungrounded, honest proof): `return derivedFields` with prove_correct reduced to bare loom_solve so the ONLY failure is the spec. EXIT=1 — leaves ensures_1 (∀n∈out, isMoved n=true), ensures_2 (newBase=none⇒[]), ensures_3 (oldBase=none⇒[]) unsolvable. Direct spec-level rejection.

POSITIVE CONTROL: pos.lean = exact gold impl (backward while-loop). lean_verify EXIT=0 (verifies, no sorry). (An honest filter-based correct alternative, pos2.lean, required a top-level helper lemma that alters the spec view, giving same_spec=False — correctly NOT counted as a same-spec impl; not needed.)

RESOLVE STEP: N/A. Protocol step 2 requires materializing+running a faithful patch ONLY for a wrong impl that VERIFIES. Zero same-spec wrong impls verify, so there is nothing to resolve; patches={} is correct and complete. No run_resolve run was needed and none is missing.

REFINEMENT AUDIT (refinement.md): legs A1=R, A2=R, A3=R (Option/List Int ↔ ModelState.fields bijections, mapping.md §2), A4=I (both-present guard ↔ Option×Option match), A5=I (element-wise set.difference∩intersection ↔ isMoved), A6=R+I (result names ↔ appended removal deps; base_app/base_name/False are R-identity constants). All legs are R or I — NO kind-3 inexpressible-changed-op, NO consumed axiom, NO A-reference. Model↔patch correspondence holds: movedFold = (old\new)∩derived over the derived carrier, exactly the gold hunk at autodetector.py:571-577. G-CONF (seed 12754) validates the R/I transliteration against the real patched callee. Verdict: SOUND (≥5 distinct attacks run, none breaks the spec).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of movedBaseFields (models the added block in MigrationAutodetector.generate_created_models, autodetector.py:563-578) against the real repo at base_commit 18759b2209.

Gold patch (commit 114da2d045): under `if old_base_model_state and new_base_model_state:` it computes `removed_base_fields = set(old_base.fields).difference(new_base.fields).intersection(model_state.fields)` and appends each as a (base_app, base_name, field, False) removal dependency.

Type facts confirmed at base_commit:
- state.py:362 `self.fields = dict(fields)` -> `set(ModelState.fields)` iterates the DICT KEYS = field NAMES. This matches the model's `List Int` of field-name identifiers (mapping.md §2). Correct: the set ops are over names, not (name, Field) tuples.
- ModelState defines no __bool__/__len__, so `if old and new` is precisely `both present (not None)` truthiness, exactly modeled by isMoved's `some ob, some nb => ... | _,_ => false` (Option x Option match). movedFold_none_left/right prove the none legs.

Model semantics: isMoved(old,new,n) = present-both-sides AND (n in old) AND (n not in new); movedFold keeps qualifying derived fields; observable compared as a SET (patch wraps in set()). This is exactly set(old).difference(new).intersection(derived) restricted to the both-present guard.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec regions byte-identical under velvet backend markers).
2. Solution.lean verifies: lean_verify.sh exit 0. Postcondition is the STRONGEST form `out = movedFold oldBaseFields newBaseFields derivedFields` (exact list equality) plus none-guards and membership soundness — not weak/vacuous, so the spec is not too weak either.
3. Differential (pure-Python) of moved_fold vs the exact gold set-op over 200,000 randomized inputs spanning the FULL domain — including None on either side, duplicate names, empty/non-empty sets, AND the derived∩new≠∅ region that conformance_check.py deliberately excludes as invalid-Django. ZERO divergences.

The conformance fuzzer's domain restriction (derived ∩ base_after = ∅, the real MTI field-clash constraint) is a valid-input restriction on the differential test, not a spec weakening: movedFold is total over all List Int and agrees with the gold set-op even on inputs outside that restriction. No input distinguishes the modeled function from the real callee. Spec is neither too strong (forbids no real repo behavior) nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) => True: spec region byte-identical; impl and prove_correct bodies correctly elided in the generated spec view. (2) Lexical screen over the spec view: none of the patch-specific tokens (title/Book/Readable/migration/django/dependency/CreateModel/RemoveField/from_state/to_state/generate_created_models/check_dependency/app_label/difference/intersection) appear anywhere. Spec uses only generic vocabulary (base entity, derived entity, field names as List Int / Option (List Int)). (3) Leakage vs PUBLIC problem_statement only (hints_text excluded): the problem_statement already discloses the exact observable behavior -- moving a field from base onto subclass in the same step, the field-name clash, and 'Reversing the order of the migration operations makes it pass. The auto-detector should be able to use this order.' The spec's prose ('Creating the derived entity must be sequenced AFTER those base fields are removed; otherwise the two definitions of the same field name collide') is a faithful abstraction of that publicly-stated behavior, and the isMoved/movedFold qualifying condition (on base before, gone after, on derived) is exactly the publicly described scenario. (4) ALL implementation mechanics (dependency tuple (base_app_label, base_name, field_name, False), generate_created_models, check_dependency, from_state/to_state, set.difference(...).intersection(...)) appear ONLY in hints_text (out of scope) and are absent from the spec view. No spec-view line reconstructs the gold edit beyond what the public problem_statement already reveals. Recorded G-LEAK=pass and recorded G-PANEL-3=NO-LEAKAGE are consistent with this finding. Bundle is not relaxed (band=set-computation, no RELAXED_LEAKAGE.md); strict standard applied.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
