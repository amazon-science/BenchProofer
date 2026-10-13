# P2 adversarial audit — django__django-15732

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_selectUniqueToDrop is total and FUNCTIONAL: for every input tuple (candidates, isUnique, allowsMultiple, defaultName) it uniquely pins result via names = narrowedNames(...): if names.length = 1 then result must = Except.ok names.headI, else result must = Except.error (). No extensionally-wrong impl can satisfy it, so no same-spec wrong impl can carry a closing proof. All 7 attacks failed to close.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,9 +50,8 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
-  let mut names := candidates
-  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
-    names := [defaultName]
+  -- ATTACK 1: prepatch bug — never narrows
+  let names := candidates
   if names.length != 1 then
     return Except.error ()
   return Except.ok names.headI
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,8 +50,9 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
+  -- ATTACK 2: partial-domain — drops the allowsMultiple guard
   let mut names := candidates
-  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
+  if isUnique && !names.isEmpty && names.contains defaultName then
     names := [defaultName]
   if names.length != 1 then
     return Except.error ()
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,10 +50,11 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
+  -- ATTACK 3: boundary — checks length == 0 instead of != 1
   let mut names := candidates
   if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
     names := [defaultName]
-  if names.length != 1 then
+  if names.length == 0 then
     return Except.error ()
   return Except.ok names.headI
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,13 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
+  -- ATTACK 4: control-flow-effect — returns pre-narrow head element
   let mut names := candidates
   if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
     names := [defaultName]
   if names.length != 1 then
     return Except.error ()
-  return Except.ok names.headI
+  return Except.ok candidates.headI
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,8 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
-  let mut names := candidates
-  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
-    names := [defaultName]
-  if names.length != 1 then
-    return Except.error ()
-  return Except.ok names.headI
+  -- ATTACK 5: ungrounded-oracle echo — always returns ok defaultName
+  return Except.ok defaultName
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,8 +50,9 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
+  -- ATTACK 6: narrowing guard uses || instead of && (too eager)
   let mut names := candidates
-  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
+  if isUnique || !names.isEmpty || allowsMultiple || names.contains defaultName then
     names := [defaultName]
   if names.length != 1 then
     return Except.error ()
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,8 @@
 def implementation_selectUniqueToDrop (candidates : List String)
     (isUnique allowsMultiple : Bool) (defaultName : String) :
     Except Unit String := Id.run do
-  let mut names := candidates
-  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
-    names := [defaultName]
-  if names.length != 1 then
-    return Except.error ()
-  return Except.ok names.headI
+  -- ATTACK 7: always error
+  return Except.error ()
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decision being modeled
-- consumes only DATA produced by surrounding helpers: the set of candidate
-- constraint identifiers discovered for the target columns, the canonical
-- identifier that the schema generator assigns to a composite-uniqueness
-- constraint, and two capability flags. Those values are taken as free inputs
-- (the spec is universally quantified over them), so the result is correct for
-- every possible value a real helper could return — strictly stronger than any
-- axiom. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The candidate identifiers, after narrowing.

When the operation removes a uniqueness constraint, the backend permits several
uniqueness constraints to coexist over the same columns, and the canonical
identifier the schema generator would assign is among the candidates, the
candidate set is reduced to exactly that canonical identifier. Otherwise the
candidate set is left untouched. -/
def narrowedNames (candidates : List String) (isUnique allowsMultiple : Bool)
    (defaultName : String) : List String :=
  if isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧
      defaultName ∈ candidates then
    [defaultName]
  else
    candidates
-- pure-end

-- post-conditions-start
/-- Selecting the single constraint identifier to drop.

`result` is `Except.error ()` exactly when the (possibly narrowed) candidate set
does not contain exactly one identifier — the operation cannot decide and signals
an error. Otherwise `result` is `Except.ok n`, where `n` is that single
identifier. The candidates are narrowed first (see `narrowedNames`), so that a
duplicate uniqueness constraint coexisting over the same columns no longer forces
an error when the canonical identifier can be singled out. -/
def problem_spec_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String)
    (result : Except Unit String) : Prop :=
  let names := narrowedNames candidates isUnique allowsMultiple defaultName
  (names.length = 1 → result = Except.ok names.headI) ∧
  (names.length ≠ 1 → result = Except.error ())
-- post-conditions-end

-- impl-start
def implementation_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String) :
    Except Unit String := Id.run do
  let mut names := candidates
  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
    names := [defaultName]
  if names.length != 1 then
    return Except.error ()
  return Except.ok names.headI
-- impl-end

-- proof-start
theorem correct_selectUniqueToDrop :
    ∀ (candidates : List String) (isUnique allowsMultiple : Bool)
      (defaultName : String),
      problem_spec_selectUniqueToDrop candidates isUnique allowsMultiple defaultName
        (implementation_selectUniqueToDrop candidates isUnique allowsMultiple defaultName) := by
  intro candidates isUnique allowsMultiple defaultName
  have hcond : (isUnique && !candidates.isEmpty && allowsMultiple && candidates.contains defaultName) = true ↔
      (isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates) := by
    simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff,
      List.contains_eq_mem, ne_eq, and_assoc, decide_eq_true_eq]
  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop narrowedNames
  simp only [Id.run]
  by_cases h : isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates
  · rw [if_pos h, if_pos (hcond.mpr h)]
    refine ⟨fun _ => rfl, fun hlen => ?_⟩
    simp at hlen
  · rw [if_neg h, if_neg (fun hh => h (hcond.mp hh))]
    by_cases hlen : candidates.length = 1
    · rw [if_neg (by simp [hlen])]
      exact ⟨fun _ => rfl, fun hne => absurd hlen hne⟩
    · rw [if_pos (by simp [hlen])]
      exact ⟨fun he => absurd he hlen, fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec confirmed True for pos_control and all 7 attacks (swebench_unified.markers.same_spec, lean backend) — edits confined to the impl region; axioms/pure/post byte-identical. Note _lean_spec_view collapses BOTH impl AND proof regions to placeholders, so attacks may keep the gold proof unchanged; failure to close is the signal.

### ATTACKS (each: cp Solution.lean, replace ONLY impl-start..impl-end, keep gold proof):
- atk_1.lean: PREPATCH bug (never narrows). cmd: bash scripts/lean_verify.sh atk_1.lean -> EXIT=1 (rewrite pattern mismatch at proof; genuine failure, no sorry). Reproduces prepatch: on candidates len!=1 that narrows to len 1, spec demands ok defaultName, impl errors.
- atk_2.lean: PARTIAL-DOMAIN (drops allowsMultiple guard). EXIT=1.
- atk_3.lean: BOUNDARY (checks length==0 instead of !=1). EXIT=1.
- atk_4.lean: CONTROL-FLOW-EFFECT (returns pre-narrow candidates.headI instead of names.headI). EXIT=1.
- atk_5.lean: UNGROUNDED-ORACLE ECHO (always return Except.ok defaultName). EXIT=1.
- atk_6.lean: guard uses || instead of && (too-eager narrowing). EXIT=1.
- atk_7.lean: always Except.error (). EXIT=1.
All ran via scripts/lean_verify.sh (concurrent, <=4 at a time, 2 batches). All 7 EXIT=1 with genuine 'rewrite failed / Did not find an occurrence of the pattern' errors; grep found NO "declaration uses 'sorry'" in any attack output.

POSITIVE CONTROL: pos_control.lean = byte copy of gold Solution.lean. cmd: bash scripts/lean_verify.sh pos_control.lean -> EXIT=0. Axioms: pos_axiom.lean (pos_control + '#print axioms correct_selectUniqueToDrop') -> EXIT=0, "'correct_selectUniqueToDrop' depends on axioms: [propext, Quot.sound]" — clean (no sorry, no _prop axioms, no sorryAx).

RESOLVE STEP: NOT triggered — no wrong impl produced a closing clean-axiom proof, so there is nothing to materialize/run through run_resolve. verify=>correct holds for every attempted attack.

REFINEMENT.MD AUDIT (A-leg focus): axioms region is EMPTY. Legs: row1 candidate list (I), row2 narrowing block (I, line-for-line four-way guard + reduction), row3 defaultName canonical identifier (R: rendered name <-> String, free input), row4 wrong-number guard (I), row5 single-selection headI (I). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible). G-AX is a genuine skip: no UNCHANGED callee property is consumed and no deep model is validated against a real callee; _constraint_names / _unique_constraint_name / _delete_constraint_sql outputs are all universally-quantified FREE inputs (strictly stronger than axiomatizing them). Correspondence to patch.diff post-block (schema.py:571-588) verified against mapping.md and the diff. A-legs vacuously hold (no axioms). Sound.

CONCLUSION: spec is total+functional -> extensionally sound; 5+ (=7) distinct wrong impls (prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, boolean-op flip, always-error) all fail to verify; positive control verifies with clean axioms. verify<=>correct upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_selectUniqueToDrop is total and FUNCTIONAL: for every input tuple (candidates, isUnique, allowsMultiple, defaultName) it uniquely pins result via names = narrowedNames(...): if names.length = 1 then result must = Except.ok names.headI, else result must = Except.error (). No extensionally-wrong impl can satisfy it, so no same-spec wrong impl can carry a closing proof. All 7 attacks failed to close.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decision being modeled
-- consumes only DATA produced by surrounding helpers: the set of candidate
-- constraint identifiers discovered for the target columns, the canonical
-- identifier that the schema generator assigns to a composite-uniqueness
-- constraint, and two capability flags. Those values are taken as free inputs
-- (the spec is universally quantified over them), so the result is correct for
-- every possible value a real helper could return — strictly stronger than any
-- axiom. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The candidate identifiers, after narrowing.

When the operation removes a uniqueness constraint, the backend permits several
uniqueness constraints to coexist over the same columns, and the canonical
identifier the schema generator would assign is among the candidates, the
candidate set is reduced to exactly that canonical identifier. Otherwise the
candidate set is left untouched. -/
def narrowedNames (candidates : List String) (isUnique allowsMultiple : Bool)
    (defaultName : String) : List String :=
  if isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧
      defaultName ∈ candidates then
    [defaultName]
  else
    candidates
-- pure-end

-- post-conditions-start
/-- Selecting the single constraint identifier to drop.

`result` is `Except.error ()` exactly when the (possibly narrowed) candidate set
does not contain exactly one identifier — the operation cannot decide and signals
an error. Otherwise `result` is `Except.ok n`, where `n` is that single
identifier. The candidates are narrowed first (see `narrowedNames`), so that a
duplicate uniqueness constraint coexisting over the same columns no longer forces
an error when the canonical identifier can be singled out. -/
def problem_spec_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String)
    (result : Except Unit String) : Prop :=
  let names := narrowedNames candidates isUnique allowsMultiple defaultName
  (names.length = 1 → result = Except.ok names.headI) ∧
  (names.length ≠ 1 → result = Except.error ())
-- post-conditions-end

-- impl-start
def implementation_selectUniqueToDrop (candidates : List String)
    (isUnique allowsMultiple : Bool) (defaultName : String) :
    Except Unit String := Id.run do
  let mut names := candidates
  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then
    names := [defaultName]
  if names.length != 1 then
    return Except.error ()
  return Except.ok names.headI
-- impl-end

-- proof-start
theorem correct_selectUniqueToDrop :
    ∀ (candidates : List String) (isUnique allowsMultiple : Bool)
      (defaultName : String),
      problem_spec_selectUniqueToDrop candidates isUnique allowsMultiple defaultName
        (implementation_selectUniqueToDrop candidates isUnique allowsMultiple defaultName) := by
  intro candidates isUnique allowsMultiple defaultName
  have hcond : (isUnique && !candidates.isEmpty && allowsMultiple && candidates.contains defaultName) = true ↔
      (isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates) := by
    simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff,
      List.contains_eq_mem, ne_eq, and_assoc, decide_eq_true_eq]
  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop narrowedNames
  simp only [Id.run]
  by_cases h : isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates
  · rw [if_pos h, if_pos (hcond.mpr h)]
    refine ⟨fun _ => rfl, fun hlen => ?_⟩
    simp at hlen
  · rw [if_neg h, if_neg (fun hh => h (hcond.mp hh))]
    by_cases hlen : candidates.length = 1
    · rw [if_neg (by simp [hlen])]
      exact ⟨fun _ => rfl, fun hne => absurd hlen hne⟩
    · rw [if_pos (by simp [hlen])]
      exact ⟨fun he => absurd he hlen, fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec confirmed True for pos_control and all 7 attacks (swebench_unified.markers.same_spec, lean backend) — edits confined to the impl region; axioms/pure/post byte-identical. Note _lean_spec_view collapses BOTH impl AND proof regions to placeholders, so attacks may keep the gold proof unchanged; failure to close is the signal.

### ATTACKS (each: cp Solution.lean, replace ONLY impl-start..impl-end, keep gold proof):
- atk_1.lean: PREPATCH bug (never narrows). cmd: bash scripts/lean_verify.sh atk_1.lean -> EXIT=1 (rewrite pattern mismatch at proof; genuine failure, no sorry). Reproduces prepatch: on candidates len!=1 that narrows to len 1, spec demands ok defaultName, impl errors.
- atk_2.lean: PARTIAL-DOMAIN (drops allowsMultiple guard). EXIT=1.
- atk_3.lean: BOUNDARY (checks length==0 instead of !=1). EXIT=1.
- atk_4.lean: CONTROL-FLOW-EFFECT (returns pre-narrow candidates.headI instead of names.headI). EXIT=1.
- atk_5.lean: UNGROUNDED-ORACLE ECHO (always return Except.ok defaultName). EXIT=1.
- atk_6.lean: guard uses || instead of && (too-eager narrowing). EXIT=1.
- atk_7.lean: always Except.error (). EXIT=1.
All ran via scripts/lean_verify.sh (concurrent, <=4 at a time, 2 batches). All 7 EXIT=1 with genuine 'rewrite failed / Did not find an occurrence of the pattern' errors; grep found NO "declaration uses 'sorry'" in any attack output.

POSITIVE CONTROL: pos_control.lean = byte copy of gold Solution.lean. cmd: bash scripts/lean_verify.sh pos_control.lean -> EXIT=0. Axioms: pos_axiom.lean (pos_control + '#print axioms correct_selectUniqueToDrop') -> EXIT=0, "'correct_selectUniqueToDrop' depends on axioms: [propext, Quot.sound]" — clean (no sorry, no _prop axioms, no sorryAx).

RESOLVE STEP: NOT triggered — no wrong impl produced a closing clean-axiom proof, so there is nothing to materialize/run through run_resolve. verify=>correct holds for every attempted attack.

REFINEMENT.MD AUDIT (A-leg focus): axioms region is EMPTY. Legs: row1 candidate list (I), row2 narrowing block (I, line-for-line four-way guard + reduction), row3 defaultName canonical identifier (R: rendered name <-> String, free input), row4 wrong-number guard (I), row5 single-selection headI (I). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible). G-AX is a genuine skip: no UNCHANGED callee property is consumed and no deep model is validated against a real callee; _constraint_names / _unique_constraint_name / _delete_constraint_sql outputs are all universally-quantified FREE inputs (strictly stronger than axiomatizing them). Correspondence to patch.diff post-block (schema.py:571-588) verified against mapping.md and the diff. A-legs vacuously hold (no axioms). Sound.

CONCLUSION: spec is total+functional -> extensionally sound; 5+ (=7) distinct wrong impls (prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, boolean-op flip, always-error) all fail to verify; positive control verifies with clean axioms. verify<=>correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift audit of django__django-15732 lean bundle. Modeled function = constraint-selection decision in BaseDatabaseSchemaEditor._delete_composed_index (post-patch). Spec narrowedNames fires iff isUnique ∧ candidates≠[] ∧ allowsMultiple ∧ defaultName∈candidates -> [defaultName], matching the patch's 4-way guard incl. inner `default_name in constraint_names` check; post-condition maps length=1 -> Except.ok headI and length≠1 -> Except.error () matching the real `len(constraint_names)!=1 -> raise ValueError` / drop constraint_names[0]. Verified: (1) scripts/lean_verify.sh exit 0 (compiles, no sorry); (2) #print axioms correct_selectUniqueToDrop = [propext, Quot.sound] only — no sorryAx, proof genuine; (3) markers.same_spec(Solution, Solution_prepatch, lean)=True — spec region byte-identical; (4) real repo at base_commit (859a87d) confirmed prepatch omits narrowing block, patch.diff introduces exactly the modeled narrowing. Traced edge cases (duplicate names, already-length-1, narrow-2->1 which is the actual bug fix, all-flags-false): modeled decision agrees with the real callee on each given identical free inputs. The free-input abstraction is universally quantified over candidates/defaultName/flags, so it is if anything strictly-stronger-safe, not too strong. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (spec view clean, no failures); meta G-LEAK=pass, relaxed_leakage=None; same_spec(Solution, prepatch)=True. Semantic review confirms no leakage beyond the public problem_statement:

1. Diff markers: none present in the spec view.
2. Patched file path: 'django/db/backends/base/schema.py' does not appear.
3. Patched repo symbols: the distinctive gold-patch def/class names (alter_unique_together, _delete_composed_index, _unique_constraint_name, _create_unique_sql, create_unique_name) are ABSENT — the Lean spec uses generic modeling names (selectUniqueToDrop, narrowedNames, candidates, defaultName, isUnique, allowsMultiple). None of these embeds a patched symbol, and none of those symbols is in the problem_statement anyway.
4. Narration: no bug/fix/previously/broken/wrong wording in comments; the docstrings describe target behavior abstractly ('the candidate set is reduced to exactly that canonical identifier ... no longer forces an error').
5. Verbatim gold lines: none of the gold-patch changed lines is reproduced in the normalized view.

The spec's narrowing condition (isUnique ∧ candidates≠[] ∧ allowsMultiple ∧ defaultName∈candidates → [defaultName]) is a faithful, abstract behavioral specification — exactly what the solver must implement and prove — not edit-localization leakage. The public problem_statement already describes the failure mode (two coexisting UNIQUE constraints on a column cause 'wrong number of constraints'), so encoding the corrected selection semantics in generic Lean terms does not reveal the gold edit beyond what the task legitimately requires. Nothing reconstructs the gold patch's file, symbols, diff, or defect narration.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
