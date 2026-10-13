# P2 adversarial audit — django__django-11433

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_offbyone_index.lean`, `atk_2_prepatch.lean`, `atk_3_partial_stop_early.lean`, `atk_4_append_reversed.lean`, `atk_5_eligible_only.lean`, `atk_6_const_true.lean`, `atk_7_negated_guard.lean`, `atk_8_extra_element.lean`, `atk_9_drop_noincoming.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verify⇏ correct gap to exhibit. The postcondition `out = applyPlan fields` under total-correctness semantics is an exact functional equality to a fully-spelled-out recursive decision function (`applies f = eligible && !(modelHasDefault && noIncomingValue && cleanedValueEmpty)`), with NO axioms and NO deep-model references (meta.json axioms=[], deep_model_references=[]). Any verifying impl must compute applyPlan field-by-field, so the resolve-run obligation (materialize a verifying wrong impl's faithful patch and check it does NOT resolve) is never triggered.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_offbyone_index.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
       done_with i = 0
       decreasing i
     do
-      let f := fields[i - 1]!
+      let f := fields[i]!
       result := applies f :: result
       i := i - 1
     return result
```

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,6 +75,13 @@
   ensures out = applyPlan fields
   do
     -- impl-start
+    -- Pre-image skeleton: the per-field decision leaves the model fallback in
+    -- place whenever the model declares a fallback AND the payload carried no
+    -- incoming value, WITHOUT the third guard on the cleaned value being empty.
+    -- The frozen spec requires `applyPlan` (which also demands the cleaned
+    -- value be empty before deferring to the fallback), so prove_correct MUST
+    -- fail: a field with a non-empty cleaned value but an omitted payload entry
+    -- is assigned by the spec yet left unassigned by this skeleton.
     let mut result : List Bool := []
     let mut i := fields.length
     while i > 0
@@ -84,7 +91,9 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := applies f :: result
+      let decision : Bool :=
+        f.eligible && !(f.modelHasDefault && f.noIncomingValue)
+      result := decision :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3_partial_stop_early.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
     -- impl-start
     let mut result : List Bool := []
     let mut i := fields.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ fields.length
       invariant result = applyPlan (fields.drop i)
       done_with i = 0
```

Attack 4 — `atk_4_append_reversed.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := applies f :: result
+      result := result ++ [applies f]
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5_eligible_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := applies f :: result
+      result := f.eligible :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6_const_true.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,8 +83,7 @@
       done_with i = 0
       decreasing i
     do
-      let f := fields[i - 1]!
-      result := applies f :: result
+      result := true :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7_negated_guard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,9 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := applies f :: result
+      let decision : Bool :=
+        f.eligible && (f.modelHasDefault && f.noIncomingValue && f.cleanedValueEmpty)
+      result := decision :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_8_extra_element.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
       let f := fields[i - 1]!
       result := applies f :: result
       i := i - 1
-    return result
+    return true :: result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the field at
```

Attack 9 — `atk_9_drop_noincoming.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,9 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := applies f :: result
+      let decision : Bool :=
+        f.eligible && !(f.modelHasDefault && f.cleanedValueEmpty)
+      result := decision :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. Whether the constructing loop hands
   a field's cleaned value to that field's write step is decided entirely by
   booleans observable at the field — whether the field is one the form may
   assign at all, whether the model declares a fallback for it, whether the
   submitted payload carried an incoming value for it, and whether the cleaned
   value is itself empty. All of that is modeled directly in the `pure` region
   below; nothing is axiomatized. The write step itself is an unchanged callee
   outside the modeled boundary. Cross-language soundness of those refinements
   is checked mechanically by G-CONF (conformance_check.py). -/
-- axioms-end

-- pure-start
/- One model field, as the value-assignment step observes it.
   * `eligible`          — the field is one the form may assign from cleaned
                           data at all: it accepts assignment, is not an
                           auto-generated key, has an entry in cleaned data, and
                           is permitted by the form's field selection. (The
                           gating conditions that are unaffected by the desired
                           change, bundled.)
   * `modelHasDefault`   — the model declares a fallback value for this field.
   * `noIncomingValue`   — the submitted payload carried no incoming value for
                           this field (so, absent any other reason, the model
                           fallback would stand).
   * `cleanedValueEmpty` — the cleaned value for this field is itself an empty
                           value. -/
structure Field where
  eligible          : Bool
  modelHasDefault   : Bool
  noIncomingValue   : Bool
  cleanedValueEmpty : Bool
deriving Inhabited, DecidableEq

/- Whether the constructing loop hands a single field's cleaned value to that
   field's write step, as opposed to skipping the field so the model's fallback
   stands. (What the write step then does with the handed value is the write
   step's own behavior, outside this decision.)

   An ineligible field is never handed off. An eligible field is handed its
   cleaned value UNLESS the model's fallback should stand in its place, which
   happens exactly when all three hold together: the model declares a fallback,
   the submitted payload carried no incoming value for the field, AND the
   cleaned value is itself empty. When the cleaned value is non-empty it is
   handed to the write step even though the payload omitted the field. -/
def applies (f : Field) : Bool :=
  f.eligible && !(f.modelHasDefault && f.noIncomingValue && f.cleanedValueEmpty)

/- The per-field assignment decisions across the whole field list.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def applyPlan : List Field → List Bool
  | []      => []
  | f :: fs => applies f :: applyPlan fs

@[grind] lemma applyPlan_nil : applyPlan [] = [] := rfl
@[grind] lemma applyPlan_cons (f : Field) (fs : List Field) :
    applyPlan (f :: fs) = applies f :: applyPlan fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method assignCleanedValues (fields : List Field) return (out : List Bool)
  ensures out = applyPlan fields
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = applyPlan (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := applies f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the field at
   `i-1` on the front, so `applyPlan` peels one `applies`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma applyPlan_drop_step (fields : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    applyPlan (fields.drop (i - 1)) = applies fields[i - 1]! :: applyPlan (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, applyPlan_cons]

prove_correct assignCleanedValues by
  loom_solve
  rw [applyPlan_drop_step fields i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec verified True for all 9 attacks + positive control via swebench_unified.markers.same_spec (velvet). Verifications run concurrently in batches of ≤4 via `bash scripts/lean_verify.sh <file>`.

### RESULTS (exit codes: 0=verifies, 1=error, 3=sorry):
- pos_control.lean (correct impl, structurally distinct forward/backward-fold as gold) => EXIT 0 (VERIFIES) ✓
- atk_2_prepatch.lean (prepatch bug: 2-conjunct guard missing cleanedValueEmpty) => EXIT 1. Genuine goal failure: `applies (fields[i-1]) ` residual at invariant_2 = the F2P discriminator. PREPATCH REPRODUCED.
- atk_1_offbyone_index (boundary: fields[i]! not [i-1]!) => EXIT 1, goal `applies fields[i]? = applies fields[i-1]?`.
- atk_3_partial_stop_early (partial-domain: while i>1 leaves first field undone) => EXIT 1, invariant/ensures unsolved.
- atk_4_append_reversed (control-flow-effect: result ++ [x] reverses order) => EXIT 1, goal `applyPlan ++ [x] = x :: applyPlan`.
- atk_5_eligible_only (ungrounded-oracle echo: drops whole guard, uses f.eligible) => EXIT 1, goal `eligible = applies f`.
- atk_6_const_true (constant true) => EXIT 1, goal `applies f = true`.
- atk_7_negated_guard (guard sign flipped, drop the !) => EXIT 1, unsolved applies goal.
- atk_8_extra_element (append extra true after loop => wrong length) => EXIT 1, ensures goal `true :: result = applyPlan fields`.
- atk_9_drop_noincoming (distinct partial guard: eligible && !(hasDefault && cleanedEmpty), drops noIncomingValue) => EXIT 1, unsolved applies goal.

All 9 rejections are genuine postcondition/invariant failures at the `applyPlan`/`ensures out = applyPlan fields` goal (each log shows the exact discriminating subgoal), not syntax artifacts.

A-LEG / AXIOM AUDIT: meta.json declares axioms=[], deep_model_references=[], additional_change_sites=[], conf_skip=False. Solution.lean axioms region is comment-only (nothing axiomatized); no `axiom`/`opaque`/`sorry`/`:|`(oracle)/`noncomputable`/`constant` anywhere in the spec region. This is a pure R/I bundle => there are NO A-legs and G-AX is vacuous; refinement.md §B correctly claims no kind-3 steps. Model↔patch correspondence is exact: `applies` = the post-patch 3-conjunct `if (has_default() and value_omitted_from_data(...) and cleaned_data.get in empty_values): continue` guard, negated and conjoined with eligibility (patch.diff verbatim; mapping.md §1-2, refinement.md A1-A7 all R/I). The added third conjunct (cleanedValueEmpty) is the sole behavioural change and is modeled identically, not axiomatized.

CONCLUSION: No verifying wrong impl exists, so no faithful refined patch needs a resolve run (step-2 obligation not triggered). Positive control verifies (non-vacuous), prepatch reproduced for the exact F2P discriminator. verify⇒correct holds for this frozen spec. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_offbyone_index.lean`, `atk_2_prepatch.lean`, `atk_3_partial_stop_early.lean`, `atk_4_append_reversed.lean`, `atk_5_eligible_only.lean`, `atk_6_const_true.lean`, `atk_7_negated_guard.lean`, `atk_8_extra_element.lean`, `atk_9_drop_noincoming.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verify⇏ correct gap to exhibit. The postcondition `out = applyPlan fields` under total-correctness semantics is an exact functional equality to a fully-spelled-out recursive decision function (`applies f = eligible && !(modelHasDefault && noIncomingValue && cleanedValueEmpty)`), with NO axioms and NO deep-model references (meta.json axioms=[], deep_model_references=[]). Any verifying impl must compute applyPlan field-by-field, so the resolve-run obligation (materialize a verifying wrong impl's faithful patch and check it does NOT resolve) is never triggered.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_offbyone_index.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial_stop_early.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_append_reversed.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_eligible_only.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_const_true.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_negated_guard.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_extra_element.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_drop_noincoming.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. Whether the constructing loop hands
   a field's cleaned value to that field's write step is decided entirely by
   booleans observable at the field — whether the field is one the form may
   assign at all, whether the model declares a fallback for it, whether the
   submitted payload carried an incoming value for it, and whether the cleaned
   value is itself empty. All of that is modeled directly in the `pure` region
   below; nothing is axiomatized. The write step itself is an unchanged callee
   outside the modeled boundary. Cross-language soundness of those refinements
   is checked mechanically by G-CONF (conformance_check.py). -/
-- axioms-end

-- pure-start
/- One model field, as the value-assignment step observes it.
   * `eligible`          — the field is one the form may assign from cleaned
                           data at all: it accepts assignment, is not an
                           auto-generated key, has an entry in cleaned data, and
                           is permitted by the form's field selection. (The
                           gating conditions that are unaffected by the desired
                           change, bundled.)
   * `modelHasDefault`   — the model declares a fallback value for this field.
   * `noIncomingValue`   — the submitted payload carried no incoming value for
                           this field (so, absent any other reason, the model
                           fallback would stand).
   * `cleanedValueEmpty` — the cleaned value for this field is itself an empty
                           value. -/
structure Field where
  eligible          : Bool
  modelHasDefault   : Bool
  noIncomingValue   : Bool
  cleanedValueEmpty : Bool
deriving Inhabited, DecidableEq

/- Whether the constructing loop hands a single field's cleaned value to that
   field's write step, as opposed to skipping the field so the model's fallback
   stands. (What the write step then does with the handed value is the write
   step's own behavior, outside this decision.)

   An ineligible field is never handed off. An eligible field is handed its
   cleaned value UNLESS the model's fallback should stand in its place, which
   happens exactly when all three hold together: the model declares a fallback,
   the submitted payload carried no incoming value for the field, AND the
   cleaned value is itself empty. When the cleaned value is non-empty it is
   handed to the write step even though the payload omitted the field. -/
def applies (f : Field) : Bool :=
  f.eligible && !(f.modelHasDefault && f.noIncomingValue && f.cleanedValueEmpty)

/- The per-field assignment decisions across the whole field list.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def applyPlan : List Field → List Bool
  | []      => []
  | f :: fs => applies f :: applyPlan fs

@[grind] lemma applyPlan_nil : applyPlan [] = [] := rfl
@[grind] lemma applyPlan_cons (f : Field) (fs : List Field) :
    applyPlan (f :: fs) = applies f :: applyPlan fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method assignCleanedValues (fields : List Field) return (out : List Bool)
  ensures out = applyPlan fields
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = applyPlan (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := applies f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the field at
   `i-1` on the front, so `applyPlan` peels one `applies`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma applyPlan_drop_step (fields : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    applyPlan (fields.drop (i - 1)) = applies fields[i - 1]! :: applyPlan (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, applyPlan_cons]

prove_correct assignCleanedValues by
  loom_solve
  rw [applyPlan_drop_step fields i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec verified True for all 9 attacks + positive control via swebench_unified.markers.same_spec (velvet). Verifications run concurrently in batches of ≤4 via `bash scripts/lean_verify.sh <file>`.

### RESULTS (exit codes: 0=verifies, 1=error, 3=sorry):
- pos_control.lean (correct impl, structurally distinct forward/backward-fold as gold) => EXIT 0 (VERIFIES) ✓
- atk_2_prepatch.lean (prepatch bug: 2-conjunct guard missing cleanedValueEmpty) => EXIT 1. Genuine goal failure: `applies (fields[i-1]) ` residual at invariant_2 = the F2P discriminator. PREPATCH REPRODUCED.
- atk_1_offbyone_index (boundary: fields[i]! not [i-1]!) => EXIT 1, goal `applies fields[i]? = applies fields[i-1]?`.
- atk_3_partial_stop_early (partial-domain: while i>1 leaves first field undone) => EXIT 1, invariant/ensures unsolved.
- atk_4_append_reversed (control-flow-effect: result ++ [x] reverses order) => EXIT 1, goal `applyPlan ++ [x] = x :: applyPlan`.
- atk_5_eligible_only (ungrounded-oracle echo: drops whole guard, uses f.eligible) => EXIT 1, goal `eligible = applies f`.
- atk_6_const_true (constant true) => EXIT 1, goal `applies f = true`.
- atk_7_negated_guard (guard sign flipped, drop the !) => EXIT 1, unsolved applies goal.
- atk_8_extra_element (append extra true after loop => wrong length) => EXIT 1, ensures goal `true :: result = applyPlan fields`.
- atk_9_drop_noincoming (distinct partial guard: eligible && !(hasDefault && cleanedEmpty), drops noIncomingValue) => EXIT 1, unsolved applies goal.

All 9 rejections are genuine postcondition/invariant failures at the `applyPlan`/`ensures out = applyPlan fields` goal (each log shows the exact discriminating subgoal), not syntax artifacts.

A-LEG / AXIOM AUDIT: meta.json declares axioms=[], deep_model_references=[], additional_change_sites=[], conf_skip=False. Solution.lean axioms region is comment-only (nothing axiomatized); no `axiom`/`opaque`/`sorry`/`:|`(oracle)/`noncomputable`/`constant` anywhere in the spec region. This is a pure R/I bundle => there are NO A-legs and G-AX is vacuous; refinement.md §B correctly claims no kind-3 steps. Model↔patch correspondence is exact: `applies` = the post-patch 3-conjunct `if (has_default() and value_omitted_from_data(...) and cleaned_data.get in empty_values): continue` guard, negated and conjoined with eligibility (patch.diff verbatim; mapping.md §1-2, refinement.md A1-A7 all R/I). The added third conjunct (cleanedValueEmpty) is the sole behavioural change and is modeled identically, not axiomatized.

CONCLUSION: No verifying wrong impl exists, so no faithful refined patch needs a resolve run (step-2 obligation not triggered). Positive control verifies (non-vacuous), prepatch reproduced for the exact F2P discriminator. verify⇒correct holds for this frozen spec. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift-from-repo) verified for velvet django__django-11433. Modeled function assignCleanedValues over `applies f = f.eligible && !(f.modelHasDefault && f.noIncomingValue && f.cleanedValueEmpty)` / applyPlan (front-recursive per-field decision list). Real callee: patched django.forms.models.construct_instance @ base_commit 21b1d23 (loop body models.py:40-59), observable = per-field hand-off to save_form_data vs continue.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — the elided spec view (axioms/pure/pre/post + `ensures out = applyPlan fields`) is byte-identical between gold and prepatch; the prepatch differs ONLY in the impl region (2-conjunct guard). No hidden spec weakening.
2. Solution.lean verifies (lean_verify exit 0). Solution_prepatch.lean FAILS at line 115 with the exact discriminating unsolved goal (eligible && (!hasDefault || !noIncoming)) = applies f — i.e. the spec genuinely requires the 3rd conjunct (cleanedValueEmpty), so the spec is NOT vacuous / not too weak, and it is not artificially strong beyond the real change.
3. Independently ran conformance_check.py against the REAL patched repo (Django 3.2a): 160011 per-field comparisons, seed 11433, 0 disagreements between the R/I shadow of applies/applyPlan and the real patched construct_instance hand-off decision. Coverage includes: default/no-default fields, payload present/omitted (value_omitted_from_data via form.data & form.files), empty vs non-empty cleaned values (EMPTY_VALUES = [None,'',[],(),{}]), fields/exclude filtering, and file-typed fields whose unchanged write step treats some handed tokens as 'no change' (boundary drawn at hand-off, correctly).

Drift hunting: I looked for an input where the free-boolean Field abstraction over-constrains or diverges from the real callee — eligibility is a conjunction of independent `continue` gates (order-independent, each field decided independently), and the changed guard is exactly the negated 3-conjunct. The `applies` boolean equals the real post-patch per-field hand-off for every combination of the four observables; nothing in the real code couples fields or introduces a fifth relevant observable at the modeled boundary. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Velvet bundle django__django-11433. Mechanical G-LEAK screen (leakage.screen over spec_view) passes with zero hard failures and no relaxation (RELAXED_LEAKAGE.md absent; not a relaxed bundle). Independent semantic review confirms no leak beyond the public problem_statement ('Allow cleaned_data to overwrite fields' default values' — mentions default value on the model, data payload omission, cleaned_data). Findings: (1) Spec region is BYTE-IDENTICAL with Solution_prepatch.lean (markers.same_spec = True); the discriminating behavior lives in the shared spec, and the two files differ only in the elided impl/proof — correct by design. (2) No patched repo symbol appears anywhere in the spec view: construct_instance, empty_values, value_omitted_from_data, has_default, save_form_data, models.py, forms/models, cleaned_data, django all absent. Only abstract carriers (Field, eligible, modelHasDefault, noIncomingValue, cleanedValueEmpty, applies, applyPlan, assignCleanedValues). (3) No diff markers, no patched file/module path, no bug/fix/patch narration. (4) The docstrings describe the target behavior in the same domain vocabulary the problem_statement already uses; the cleanedValueEmpty third-conjunct encodes WHAT a faithful spec must require (the correct post-change semantics), not WHERE/HOW to edit the repo — impl and proof are elided. A consumer sees an abstract per-field boolean decision spec, not a locator for the one-conjunct gold edit to django/forms/models.py. No spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
