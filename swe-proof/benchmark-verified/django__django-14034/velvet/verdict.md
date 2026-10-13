# P2 adversarial audit — django__django-14034

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
       done_with i = 0
       decreasing i
     do
-      let s := subs[i - 1]!
+      let s := subs[i]!
       result := subRequired outerRequired requireAll s :: result
       i := i - 1
     return result
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,17 +65,7 @@
   ensures out = requiredPlan outerRequired requireAll subs
   do
     -- impl-start
-    let mut result : List Bool := []
-    let mut i := subs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ subs.length
-      invariant result = requiredPlan outerRequired requireAll (subs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := subs[i - 1]!
-      result := subRequired outerRequired requireAll s :: result
-      i := i - 1
+    let result : List Bool := []
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
       decreasing i
     do
       let s := subs[i - 1]!
-      result := subRequired outerRequired requireAll s :: result
+      result := subRequired requireAll outerRequired s :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,8 @@
       done_with i = 0
       decreasing i
     do
-      let s := subs[i - 1]!
-      result := subRequired outerRequired requireAll s :: result
+      let _s := subs[i - 1]!
+      result := (outerRequired && requireAll) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
       decreasing i
     do
       let s := subs[i - 1]!
-      result := subRequired outerRequired requireAll s :: result
+      result := (!subRequired outerRequired requireAll s) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,8 @@
       done_with i = 0
       decreasing i
     do
-      let s := subs[i - 1]!
-      result := subRequired outerRequired requireAll s :: result
+      let _s := subs[i - 1]!
+      result := true :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,18 +65,7 @@
   ensures out = requiredPlan outerRequired requireAll subs
   do
     -- impl-start
-    let mut result : List Bool := []
-    let mut i := subs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ subs.length
-      invariant result = requiredPlan outerRequired requireAll (subs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := subs[i - 1]!
-      result := subRequired outerRequired requireAll s :: result
-      i := i - 1
-    return result
+    return requiredPlan outerRequired requireAll subs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the sub-field at
@@ -95,5 +84,3 @@
 
 prove_correct requiredFlags by
   loom_solve
-  rw [requiredPlan_drop_step outerRequired requireAll subs i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real attribute-assembly step is a bounded loop over
   the zipped (sub-field, sub-widget) pairs and always terminates, so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating loop discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. Whether a sub-widget renders the
   required marker is decided entirely by two booleans observable at the
   sub-widget — whether it opts into the marker on its own, and whether its
   sub-field is itself required — together with the two field-level flags. All
   of that is modeled directly in the `pure` region below; nothing is
   axiomatized. -/
-- axioms-end

-- pure-start
/- One sub-field of a MultiValueField, as the rendering step observes it.
   * `required`      — whether this sub-field is itself a required field.
   * `marksRequired` — whether this sub-field's own sub-widget opts into the
                       required marker (a visible text-style widget does; a
                       hidden one does not). -/
structure SubField where
  required      : Bool
  marksRequired : Bool
deriving Inhabited, DecidableEq

/- Whether a single sub-widget should carry the required marker.

   `outerRequired` is the overall gate: the MultiValueField as a whole is
   required and the form asks for the required marker. When that gate is open,
   two regimes apply:
     * all sub-fields jointly required (`requireAll`): every sub-widget carries
       the marker;
     * otherwise (`require_all_fields` is false): a sub-widget carries the
       marker exactly when it opts in on its own AND its sub-field is required.
   When the gate is closed, no sub-widget carries the marker. -/
def subRequired (outerRequired requireAll : Bool) (s : SubField) : Bool :=
  outerRequired && (requireAll || (s.marksRequired && s.required))

/- The per-sub-widget required markers across the whole sub-field list.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def requiredPlan (outerRequired requireAll : Bool) : List SubField → List Bool
  | []      => []
  | s :: ss => subRequired outerRequired requireAll s :: requiredPlan outerRequired requireAll ss

@[grind] lemma requiredPlan_nil (oR rA : Bool) : requiredPlan oR rA [] = [] := rfl
@[grind] lemma requiredPlan_cons (oR rA : Bool) (s : SubField) (ss : List SubField) :
    requiredPlan oR rA (s :: ss) = subRequired oR rA s :: requiredPlan oR rA ss := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method requiredFlags (outerRequired : Bool) (requireAll : Bool) (subs : List SubField) return (out : List Bool)
  ensures out = requiredPlan outerRequired requireAll subs
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := subs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ subs.length
      invariant result = requiredPlan outerRequired requireAll (subs.drop i)
      done_with i = 0
      decreasing i
    do
      let s := subs[i - 1]!
      result := subRequired outerRequired requireAll s :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the sub-field at
   `i-1` on the front, so `requiredPlan` peels one `subRequired`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma requiredPlan_drop_step (oR rA : Bool) (subs : List SubField) (i : Nat)
    (hi : 0 < i) (hle : i ≤ subs.length) :
    requiredPlan oR rA (subs.drop (i - 1)) = subRequired oR rA subs[i - 1]! :: requiredPlan oR rA (subs.drop i) := by
  have hlt : i - 1 < subs.length := by omega
  have hcons : subs.drop (i - 1) = subs[i - 1]! :: subs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, requiredPlan_cons]

prove_correct requiredFlags by
  loom_solve
  rw [requiredPlan_drop_step outerRequired requireAll subs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (velvet, django__django-14034). Spec is a TIGHT equational postcondition: `ensures out = requiredPlan outerRequired requireAll subs`, NO preconditions, output fully pinned. same_spec=True for all 7 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical).

BASELINE: positive_control.lean VERIFIES (exit 0); prepatch.lean REPRODUCED as failing (exit 1) — its uniform `v := outerRequired` leaves goal `outerRequired = subRequired outerRequired requireAll (subs[i-1]?.getD default)` unsolved (over-marks a non-required subfield).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`, run concurrently in 2 batches of <=4):
- atk_1 (control-flow/off-by-one, subs[i]! vs subs[i-1]!): FAIL exit 1, goal `subRequired oR rA subs[i]? = subRequired oR rA subs[i-1]?`.
- atk_2 (boundary, return [] skipping loop): FAIL exit 1, goal `[] = requiredPlan oR rA subs` (+ unknown id `i`).
- atk_3 (swapped flags subRequired requireAll outerRequired): FAIL exit 1, goal `subRequired rA oR .. = subRequired oR rA ..`.
- atk_4 (control-flow-effect, drop per-subfield term -> oR && rA): FAIL exit 1, goal `(oR && rA) = subRequired oR rA ..`.
- atk_5 (ungrounded/inverted oracle, !subRequired): FAIL exit 1, goal reduces to `False`.
- atk_6 (partial-domain/over-mark, uniform true under gate): FAIL exit 1, goal `subRequired oR rA .. = true`.
- atk_7 (ungrounded-oracle ECHO, `return requiredPlan outerRequired requireAll subs`, proof `loom_solve`): VERIFIES exit 0. This is behaviorally IDENTICAL to gold (returns the postcondition RHS verbatim). Per protocol its faithful refined patch = the gold patch verbatim; materialized as faithful_patch.diff and RUN through the official harness: `run_resolve('django__django-14034', patch, timeout=1800)` under SBU_BENCHMARK=swe_bench_verified -> RESOLVED=True, completed=True (real Docker report, ~4 min). So the only verifying wrong-shaped attack RESOLVES; verify does NOT diverge from correct here.

6/6 genuinely-wrong impls (partial-domain, boundary, control-flow-effect, swapped-flag, inverted-oracle, over-mark) are all REJECTED by verify — the equational postcondition forces exact equality with requiredPlan on every input. The 7th (echo) verifies AND resolves.

REFINEMENT.md AUDIT: legs A1 (R+A-reference), A2 (R), A3 (R), A4 (A-reference+I), A5 (I) — no kind-3, no consumed axioms (axioms region empty). A-reference callees confirmed against the real repo at base_commit db1fc5cd3c: Widget.use_required_attribute = `return not self.is_hidden` (text->True/hidden->False == marksRequired); MultiValueField.__init__ forces subfield.required=False when require_all_fields=True (model robust: requireAll disjunct short-circuits); composed outer gate = widget.use_required_attribute(initial) and field.required and form.use_required_attribute; per-subwidget assignment `subwidget.use_required_attribute(self.initial) and subfield.required` matches subRequired's not-require-all branch. Correspondence holds. G-AX passed (6 boundary + 4000 fuzz); G-CONF passed (100007 inputs, seed 14034, 0 disagreements).

Verdict SOUND: >=6 distinct wrong impls attacked, none verifies; the sole verifying same-spec attack (echo) materializes to a patch that RESOLVES under the official harness. verify => correct is upheld for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real attribute-assembly step is a bounded loop over
   the zipped (sub-field, sub-widget) pairs and always terminates, so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating loop discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. Whether a sub-widget renders the
   required marker is decided entirely by two booleans observable at the
   sub-widget — whether it opts into the marker on its own, and whether its
   sub-field is itself required — together with the two field-level flags. All
   of that is modeled directly in the `pure` region below; nothing is
   axiomatized. -/
-- axioms-end

-- pure-start
/- One sub-field of a MultiValueField, as the rendering step observes it.
   * `required`      — whether this sub-field is itself a required field.
   * `marksRequired` — whether this sub-field's own sub-widget opts into the
                       required marker (a visible text-style widget does; a
                       hidden one does not). -/
structure SubField where
  required      : Bool
  marksRequired : Bool
deriving Inhabited, DecidableEq

/- Whether a single sub-widget should carry the required marker.

   `outerRequired` is the overall gate: the MultiValueField as a whole is
   required and the form asks for the required marker. When that gate is open,
   two regimes apply:
     * all sub-fields jointly required (`requireAll`): every sub-widget carries
       the marker;
     * otherwise (`require_all_fields` is false): a sub-widget carries the
       marker exactly when it opts in on its own AND its sub-field is required.
   When the gate is closed, no sub-widget carries the marker. -/
def subRequired (outerRequired requireAll : Bool) (s : SubField) : Bool :=
  outerRequired && (requireAll || (s.marksRequired && s.required))

/- The per-sub-widget required markers across the whole sub-field list.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def requiredPlan (outerRequired requireAll : Bool) : List SubField → List Bool
  | []      => []
  | s :: ss => subRequired outerRequired requireAll s :: requiredPlan outerRequired requireAll ss

@[grind] lemma requiredPlan_nil (oR rA : Bool) : requiredPlan oR rA [] = [] := rfl
@[grind] lemma requiredPlan_cons (oR rA : Bool) (s : SubField) (ss : List SubField) :
    requiredPlan oR rA (s :: ss) = subRequired oR rA s :: requiredPlan oR rA ss := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method requiredFlags (outerRequired : Bool) (requireAll : Bool) (subs : List SubField) return (out : List Bool)
  ensures out = requiredPlan outerRequired requireAll subs
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := subs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ subs.length
      invariant result = requiredPlan outerRequired requireAll (subs.drop i)
      done_with i = 0
      decreasing i
    do
      let s := subs[i - 1]!
      result := subRequired outerRequired requireAll s :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the sub-field at
   `i-1` on the front, so `requiredPlan` peels one `subRequired`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma requiredPlan_drop_step (oR rA : Bool) (subs : List SubField) (i : Nat)
    (hi : 0 < i) (hle : i ≤ subs.length) :
    requiredPlan oR rA (subs.drop (i - 1)) = subRequired oR rA subs[i - 1]! :: requiredPlan oR rA (subs.drop i) := by
  have hlt : i - 1 < subs.length := by omega
  have hcons : subs.drop (i - 1) = subs[i - 1]! :: subs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, requiredPlan_cons]

prove_correct requiredFlags by
  loom_solve
  rw [requiredPlan_drop_step outerRequired requireAll subs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (velvet, django__django-14034). Spec is a TIGHT equational postcondition: `ensures out = requiredPlan outerRequired requireAll subs`, NO preconditions, output fully pinned. same_spec=True for all 7 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical).

BASELINE: positive_control.lean VERIFIES (exit 0); prepatch.lean REPRODUCED as failing (exit 1) — its uniform `v := outerRequired` leaves goal `outerRequired = subRequired outerRequired requireAll (subs[i-1]?.getD default)` unsolved (over-marks a non-required subfield).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`, run concurrently in 2 batches of <=4):
- atk_1 (control-flow/off-by-one, subs[i]! vs subs[i-1]!): FAIL exit 1, goal `subRequired oR rA subs[i]? = subRequired oR rA subs[i-1]?`.
- atk_2 (boundary, return [] skipping loop): FAIL exit 1, goal `[] = requiredPlan oR rA subs` (+ unknown id `i`).
- atk_3 (swapped flags subRequired requireAll outerRequired): FAIL exit 1, goal `subRequired rA oR .. = subRequired oR rA ..`.
- atk_4 (control-flow-effect, drop per-subfield term -> oR && rA): FAIL exit 1, goal `(oR && rA) = subRequired oR rA ..`.
- atk_5 (ungrounded/inverted oracle, !subRequired): FAIL exit 1, goal reduces to `False`.
- atk_6 (partial-domain/over-mark, uniform true under gate): FAIL exit 1, goal `subRequired oR rA .. = true`.
- atk_7 (ungrounded-oracle ECHO, `return requiredPlan outerRequired requireAll subs`, proof `loom_solve`): VERIFIES exit 0. This is behaviorally IDENTICAL to gold (returns the postcondition RHS verbatim). Per protocol its faithful refined patch = the gold patch verbatim; materialized as faithful_patch.diff and RUN through the official harness: `run_resolve('django__django-14034', patch, timeout=1800)` under SBU_BENCHMARK=swe_bench_verified -> RESOLVED=True, completed=True (real Docker report, ~4 min). So the only verifying wrong-shaped attack RESOLVES; verify does NOT diverge from correct here.

6/6 genuinely-wrong impls (partial-domain, boundary, control-flow-effect, swapped-flag, inverted-oracle, over-mark) are all REJECTED by verify — the equational postcondition forces exact equality with requiredPlan on every input. The 7th (echo) verifies AND resolves.

REFINEMENT.md AUDIT: legs A1 (R+A-reference), A2 (R), A3 (R), A4 (A-reference+I), A5 (I) — no kind-3, no consumed axioms (axioms region empty). A-reference callees confirmed against the real repo at base_commit db1fc5cd3c: Widget.use_required_attribute = `return not self.is_hidden` (text->True/hidden->False == marksRequired); MultiValueField.__init__ forces subfield.required=False when require_all_fields=True (model robust: requireAll disjunct short-circuits); composed outer gate = widget.use_required_attribute(initial) and field.required and form.use_required_attribute; per-subwidget assignment `subwidget.use_required_attribute(self.initial) and subfield.required` matches subRequired's not-require-all branch. Correspondence holds. G-AX passed (6 boundary + 4000 fuzz); G-CONF passed (100007 inputs, seed 14034, 0 disagreements).

Verdict SOUND: >=6 distinct wrong impls attacked, none verifies; the sole verifying same-spec attack (echo) materializes to a patch that RESOLVES under the official harness. verify => correct is upheld for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-14034 velvet bundle. Modeled function: BoundField.build_widget_attrs (django/forms/boundfield.py:232), modeled as requiredFlags with spec `out = requiredPlan outerRequired requireAll subs` where subRequired oR rA s = oR && (rA || (s.marksRequired && s.required)).

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean)=True — frozen spec regions (axioms/pure/pre/post + method signature/ensures) are byte-identical across patch and prepatch. Diffs vs the pre-migration velvet reference are confined to NON-spec lines only (set_option loom.semantics.termination partial->total, open PartialCorrectness->TotalCorrectness, added `decreasing i`), which the spec_view/same_spec projection excludes. Solution.lean elaborates clean under lean_verify.sh (exit 0, total correctness) so the spec is non-vacuous.

FAITHFULNESS TEST (real repo): built patched base-commit repo (db1fc5cd + gold patch.diff) and ran an EXHAUSTIVE differential comparison of the modeled requiredPlan/subRequired against the real patched repo's actually-rendered per-sub-widget `required` attribute. Enumerated ALL 340 configurations: sub-field lists of length 0..3, each sub-field in {required T/F} x {text/hidden sub-widget}, cross outer in {T,F} x require_all in {T,F}. Result: 0 divergences.

WHY EXHAUSTIVE IS SUFFICIENT: the observable change is pointwise per sub-widget — each element's rendered flag depends only on its own (required, marksRequired) plus the two global booleans (outerRequired, requireAll); no cross-element coupling. Length 0..3 therefore exhausts every per-element behavior class; longer lists are independent repetitions. All three regimes verified against reality: (a) gate closed (outerRequired=false) => all false, matching patch setting nothing; (b) require_all=True / else branch => uniform outerRequired even for HIDDEN sub-widgets (real code sets attrs['required']=True on the outer MultiWidget final_attrs, which propagates to every subwidget via get_context, so hidden subwidgets DO render required — model's requireAll disjunct captures this correctly); (c) require_all_fields=false over MultiWidget => marksRequired && required per subwidget, matching `subwidget.use_required_attribute(self.initial) and subfield.required`.

No diverging input found. The spec is not too strong and does not drift from real callee behavior. Corroborating recorded gates: G-CONF pass (100007 inputs, 0 disagreements, seed 14034); G-AX pass (outer-gate + use_required_attribute A-references + boolean->markup rendering faithful over 4000+ fuzz); G-DIFF pass (prepatch fails on a non-required subfield).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen passes (velvet/lean flavor): no diff markers, no reproduced gold-patch line, no patched file path (django/forms/boundfield.py), no patched module path, no spec-view identifier or comment embedding the sole distinctive patched symbol build_widget_attrs, and no bug/fix narration. same_spec(Solution.lean, Solution_prepatch.lean)=True — frozen spec region is byte-identical, differing only in impl/proof. Domain terms in the spec view (MultiValueField, MultiWidget, require_all_fields) are all already public in problem_statement. Terms absent from problem_statement (use_required_attribute, build_widget_attrs, boundfield) do NOT appear in the spec view; use_required_attribute is expressed abstractly as `marksRequired` (behavior, not the callee/edit). The subRequired formula encodes the desired post-condition (per-sub-field required marking) in abstract Lean booleans/lists — which any valid spec must — and the discriminating behavior it captures is exactly what the public problem_statement already demands (sub-fields should respect their own required attribute). No spec-view line reveals the gold edit's location or specifics beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
