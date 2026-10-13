# P2 adversarial audit — scikit-learn__scikit-learn-26323

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1s.lean`, `atk_2s.lean`, `atk_3s.lean`, `atk_4s.lean`, `atk_5s.lean`, `atk_6s.lean` |

**Non-vacuity.** The positive control `pos_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,23 +72,10 @@
   let mut outTransformers : List Transformer := []
   for trans in transformers do
     outTransformers := outTransformers ++ [setOutput transform trans]
-  -- The real patch guards the remainder call with
-  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
-  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
-  -- coincidence that subsumes the contained loop's sentinel filter,
-  -- refinement.md op 2), so the propagation is applied directly.
-  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
-  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
-  -- one re-adding the real patch's redundant sentinel guard) verifies too;
-  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
-  -- genuine weakness witness must compute a DIFFERENT function.
-  let outRemainder := setOutput transform remainder
+  let outRemainder := remainder
   return (outTransformers, outRemainder)
 -- impl-end
-
 -- proof-start
-/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
-initial accumulator, generalized over that accumulator (Route B helper). -/
 theorem loop_helper_setOutput
     (transform : String) (xs : List Transformer) (init : List Transformer) :
     Id.run (forIn xs init (fun trans r =>
@@ -110,7 +97,10 @@
   simp only [Id.run]
   have h := loop_helper_setOutput transform transformers []
   simp only [Id.run] at h
-  rw [h]
-  simp only [List.nil_append]
-  exact ⟨rfl, rfl⟩
+  simp only [h, List.nil_append]
+  constructor <;>
+    (try cases transformers) <;>
+    (try cases remainder) <;>
+    simp_all [setOutput, loop_helper_setOutput] <;>
+    (try rfl) <;> (try decide)
 -- proof-end
```

Attack 2 — `atk_2s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,24 +71,11 @@
     List Transformer × Transformer := Id.run do
   let mut outTransformers : List Transformer := []
   for trans in transformers do
-    outTransformers := outTransformers ++ [setOutput transform trans]
-  -- The real patch guards the remainder call with
-  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
-  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
-  -- coincidence that subsumes the contained loop's sentinel filter,
-  -- refinement.md op 2), so the propagation is applied directly.
-  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
-  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
-  -- one re-adding the real patch's redundant sentinel guard) verifies too;
-  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
-  -- genuine weakness witness must compute a DIFFERENT function.
+    outTransformers := outTransformers ++ [trans]
   let outRemainder := setOutput transform remainder
   return (outTransformers, outRemainder)
 -- impl-end
-
 -- proof-start
-/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
-initial accumulator, generalized over that accumulator (Route B helper). -/
 theorem loop_helper_setOutput
     (transform : String) (xs : List Transformer) (init : List Transformer) :
     Id.run (forIn xs init (fun trans r =>
@@ -110,7 +97,10 @@
   simp only [Id.run]
   have h := loop_helper_setOutput transform transformers []
   simp only [Id.run] at h
-  rw [h]
-  simp only [List.nil_append]
-  exact ⟨rfl, rfl⟩
+  simp only [h, List.nil_append]
+  constructor <;>
+    (try cases transformers) <;>
+    (try cases remainder) <;>
+    simp_all [setOutput, loop_helper_setOutput] <;>
+    (try rfl) <;> (try decide)
 -- proof-end
```

Attack 3 — `atk_3s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,24 +71,11 @@
     List Transformer × Transformer := Id.run do
   let mut outTransformers : List Transformer := []
   for trans in transformers do
-    outTransformers := outTransformers ++ [setOutput transform trans]
-  -- The real patch guards the remainder call with
-  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
-  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
-  -- coincidence that subsumes the contained loop's sentinel filter,
-  -- refinement.md op 2), so the propagation is applied directly.
-  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
-  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
-  -- one re-adding the real patch's redundant sentinel guard) verifies too;
-  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
-  -- genuine weakness witness must compute a DIFFERENT function.
+    outTransformers := [setOutput transform trans] ++ outTransformers
   let outRemainder := setOutput transform remainder
   return (outTransformers, outRemainder)
 -- impl-end
-
 -- proof-start
-/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
-initial accumulator, generalized over that accumulator (Route B helper). -/
 theorem loop_helper_setOutput
     (transform : String) (xs : List Transformer) (init : List Transformer) :
     Id.run (forIn xs init (fun trans r =>
@@ -110,7 +97,10 @@
   simp only [Id.run]
   have h := loop_helper_setOutput transform transformers []
   simp only [Id.run] at h
-  rw [h]
-  simp only [List.nil_append]
-  exact ⟨rfl, rfl⟩
+  simp only [h, List.nil_append]
+  constructor <;>
+    (try cases transformers) <;>
+    (try cases remainder) <;>
+    simp_all [setOutput, loop_helper_setOutput] <;>
+    (try rfl) <;> (try decide)
 -- proof-end
```

Attack 4 — `atk_4s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,23 +72,12 @@
   let mut outTransformers : List Transformer := []
   for trans in transformers do
     outTransformers := outTransformers ++ [setOutput transform trans]
-  -- The real patch guards the remainder call with
-  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
-  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
-  -- coincidence that subsumes the contained loop's sentinel filter,
-  -- refinement.md op 2), so the propagation is applied directly.
-  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
-  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
-  -- one re-adding the real patch's redundant sentinel guard) verifies too;
-  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
-  -- genuine weakness witness must compute a DIFFERENT function.
-  let outRemainder := setOutput transform remainder
+  let outRemainder := match transformers with
+    | [] => remainder
+    | _ => setOutput transform remainder
   return (outTransformers, outRemainder)
 -- impl-end
-
 -- proof-start
-/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
-initial accumulator, generalized over that accumulator (Route B helper). -/
 theorem loop_helper_setOutput
     (transform : String) (xs : List Transformer) (init : List Transformer) :
     Id.run (forIn xs init (fun trans r =>
@@ -110,7 +99,10 @@
   simp only [Id.run]
   have h := loop_helper_setOutput transform transformers []
   simp only [Id.run] at h
-  rw [h]
-  simp only [List.nil_append]
-  exact ⟨rfl, rfl⟩
+  simp only [h, List.nil_append]
+  constructor <;>
+    (try cases transformers) <;>
+    (try cases remainder) <;>
+    simp_all [setOutput, loop_helper_setOutput] <;>
+    (try rfl) <;> (try decide)
 -- proof-end
```

Attack 5 — `atk_5s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,23 +72,10 @@
   let mut outTransformers : List Transformer := []
   for trans in transformers do
     outTransformers := outTransformers ++ [setOutput transform trans]
-  -- The real patch guards the remainder call with
-  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
-  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
-  -- coincidence that subsumes the contained loop's sentinel filter,
-  -- refinement.md op 2), so the propagation is applied directly.
-  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
-  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
-  -- one re-adding the real patch's redundant sentinel guard) verifies too;
-  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
-  -- genuine weakness witness must compute a DIFFERENT function.
-  let outRemainder := setOutput transform remainder
+  let outRemainder := setOutput "pandas" remainder
   return (outTransformers, outRemainder)
 -- impl-end
-
 -- proof-start
-/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
-initial accumulator, generalized over that accumulator (Route B helper). -/
 theorem loop_helper_setOutput
     (transform : String) (xs : List Transformer) (init : List Transformer) :
     Id.run (forIn xs init (fun trans r =>
@@ -110,7 +97,10 @@
   simp only [Id.run]
   have h := loop_helper_setOutput transform transformers []
   simp only [Id.run] at h
-  rw [h]
-  simp only [List.nil_append]
-  exact ⟨rfl, rfl⟩
+  simp only [h, List.nil_append]
+  constructor <;>
+    (try cases transformers) <;>
+    (try cases remainder) <;>
+    simp_all [setOutput, loop_helper_setOutput] <;>
+    (try rfl) <;> (try decide)
 -- proof-end
```

Attack 6 — `atk_6s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,25 +70,12 @@
     (transformers : List Transformer) (remainder : Transformer) (transform : String) :
     List Transformer × Transformer := Id.run do
   let mut outTransformers : List Transformer := []
-  for trans in transformers do
+  for trans in transformers.tail do
     outTransformers := outTransformers ++ [setOutput transform trans]
-  -- The real patch guards the remainder call with
-  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
-  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
-  -- coincidence that subsumes the contained loop's sentinel filter,
-  -- refinement.md op 2), so the propagation is applied directly.
-  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
-  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
-  -- one re-adding the real patch's redundant sentinel guard) verifies too;
-  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
-  -- genuine weakness witness must compute a DIFFERENT function.
   let outRemainder := setOutput transform remainder
   return (outTransformers, outRemainder)
 -- impl-end
-
 -- proof-start
-/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
-initial accumulator, generalized over that accumulator (Route B helper). -/
 theorem loop_helper_setOutput
     (transform : String) (xs : List Transformer) (init : List Transformer) :
     Id.run (forIn xs init (fun trans r =>
@@ -110,7 +97,10 @@
   simp only [Id.run]
   have h := loop_helper_setOutput transform transformers []
   simp only [Id.run] at h
-  rw [h]
-  simp only [List.nil_append]
-  exact ⟨rfl, rfl⟩
+  simp only [h, List.nil_append]
+  constructor <;>
+    (try cases transformers) <;>
+    (try cases remainder) <;>
+    simp_all [setOutput, loop_helper_setOutput] <;>
+    (try rfl) <;> (try decide)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_correct.lean`

```lean
import Mathlib
-- imports-end

/-!
Propagating an output-container choice through a composite transformer.

A composite transformer holds an ordered collection of contained
sub-transformers together with a fall-back transformer that handles the columns
not claimed by any of them. Each entry is either an actual estimator (which
carries its own output-container configuration) or one of the two reserved
sentinels meaning "pass the columns through unchanged" or "drop the columns".

Configuring the output container of the composite propagates the chosen
container to every contained estimator, and likewise to the fall-back
transformer whenever that fall-back is itself an estimator (i.e. not one of the
two reserved sentinels). A sentinel carries no configuration and is left as is.

So the result is: every contained sub-transformer with its output container set
to the chosen value (sentinels untouched), paired with the fall-back transformer
with its output container set to the chosen value (again, untouched if it is a
sentinel).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Applying the
-- output-container choice to one transformer is modeled DEEPLY (the pure helper
-- `setOutput` below: an estimator records the new container, a sentinel is left
-- unchanged), so there is no `opaque`/`axiom` callee contract. The composite's
-- own container choice and the membership/fitted bookkeeping that produces the
-- contained collection are orthogonal to the modeled behavior and enter through
-- the grounded inputs.
-- axioms-end

-- pure-start
/-- A contained transformer entry: either an actual estimator carrying an
identity `id` and its current output-container configuration `output`, or one of
the two reserved sentinels (`passthrough` / `drop`) that carry no configuration.
(Faithful refinement of a Python transformer slot, which is either an estimator
object or one of the two reserved strings.) -/
inductive Transformer where
  | passthrough
  | drop
  | est (id : Nat) (output : String)
deriving DecidableEq, Repr

/-- Apply an output-container choice to one transformer: an estimator records the
new container value; a sentinel carries no configuration and is returned
unchanged. -/
def setOutput (transform : String) (t : Transformer) : Transformer :=
  match t with
  | .est id _ => .est id transform
  | other => other
-- pure-end

-- post-conditions-start
/-- The result pins both components to their inputs under the chosen container
`transform`: the first component is the contained collection with the container
applied to each entry (sentinels unchanged), and the second component is the
fall-back transformer with the container applied (again unchanged if it is a
sentinel). -/
def problem_spec_setOutput
    (transformers : List Transformer) (remainder : Transformer) (transform : String)
    (result : List Transformer × Transformer) : Prop :=
  result.1 = transformers.map (setOutput transform) ∧
  result.2 = setOutput transform remainder
-- post-conditions-end

-- impl-start
def implementation_setOutput
    (transformers : List Transformer) (remainder : Transformer) (transform : String) :
    List Transformer × Transformer := Id.run do
  let mut outTransformers : List Transformer := []
  for trans in transformers do
    outTransformers := outTransformers ++ [setOutput transform trans]
  -- The real patch guards the remainder call with
  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
  -- coincidence that subsumes the contained loop's sentinel filter,
  -- refinement.md op 2), so the propagation is applied directly.
  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
  -- one re-adding the real patch's redundant sentinel guard) verifies too;
  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
  -- genuine weakness witness must compute a DIFFERENT function.
  let outRemainder := setOutput transform remainder
  return (outTransformers, outRemainder)
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
initial accumulator, generalized over that accumulator (Route B helper). -/
theorem loop_helper_setOutput
    (transform : String) (xs : List Transformer) (init : List Transformer) :
    Id.run (forIn xs init (fun trans r =>
      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [setOutput transform trans]))))) =
      init ++ xs.map (setOutput transform) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_setOutput :
    ∀ (transformers : List Transformer) (remainder : Transformer) (transform : String),
      problem_spec_setOutput transformers remainder transform
        (implementation_setOutput transformers remainder transform) := by
  intro transformers remainder transform
  unfold implementation_setOutput problem_spec_setOutput
  simp only [Id.run]
  have h := loop_helper_setOutput transform transformers []
  simp only [Id.run] at h
  rw [h]
  simp only [List.nil_append]
  exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY FUNCTIONAL — no same-spec wrong impl can verify. problem_spec_setOutput pins BOTH output components by equations: result.1 = transformers.map (setOutput transform) AND result.2 = setOutput transform remainder. This uniquely determines the result, so any verifying implementation_setOutput must compute exactly this function; there is no room for a spec-too-weak witness.

ATTACKS (6 distinct wrong impls, all same_spec=True vs Solution.lean, verified concurrently ≤4 at a time). Command per file: `bash scripts/lean_verify.sh <path>`.
  atk_1s: prepatch bug — remainder returned unconfigured (outRemainder := remainder). exit=1, error: unsolved goals (line 94). == the actual pre-patch bug (Solution_prepatch.lean), reproduced.
  atk_2s: no propagation to contained transformers (identity on contained loop). exit=1, error: simp made no progress.
  atk_3s: reversed contained order (prepend instead of append). exit=1, error: simp made no progress.
  atk_4s: partial-domain — remainder configured only when transformers nonempty (match transformers | [] => remainder | _ => setOutput). exit=1, error: unsolved goals (line 96).
  atk_5s: ungrounded-oracle echo — hardcoded container 'pandas' on remainder (setOutput "pandas" remainder). exit=1, error: unsolved goals (line 94).
  atk_6s: control-flow effect — drops head contained transformer (for trans in transformers.tail). exit=1, error: simp made no progress.

NONE VERIFIES → protocol step 2 (materialize faithful patch + run_resolve for verifying wrong impls) is VACUOUS; no verifying wrong impl exists, so `patches` is empty. verify⇏correct is NOT exhibited.

PROOF-HARNESS CONFOUND CONTROLLED: an initial weak `first|...|decide` harness failed even on a CORRECT guarded same-spec variant (pos_variant.lean, exit=1) — a false-negative risk. I therefore rebuilt all 6 attacks (the *s files) with a STRONGER harness (loop_helper rewrite + constructor <;> cases transformers <;> cases remainder <;> simp_all[setOutput] <;> rfl/decide) and PROVED that harness closes a correct guarded variant: pos_variant2.lean (remainder handled via explicit match on passthrough/drop/est — same_spec=True) verifies exit=0. The 6 attacks STILL fail (exit=1, genuine 'unsolved goals'/'simp made no progress', NOT sorry/timeout) under that same capable harness. So the failures are due to spec strength, not tactic weakness.

POSITIVE CONTROL: pos_correct.lean = shipped Solution.lean impl+proof verbatim, exit=0. #print axioms correct_setOutput (via pos_axioms.lean) → 'depends on axioms: [propext, Quot.sound]' — clean, no sorryAx / no custom axioms.

A-LEG / MODEL-CORRESPONDENCE AUDIT (my focus): axioms region is EMPTY. `_safe_set_output` (the per-slot container propagation the patch invokes on remainder) is modeled DEEPLY by pure helper `setOutput` (est id _ ↦ est id transform; sentinel ↦ unchanged), which per SPEC_GUIDE §3 is NOT axiomatized. Hence there are NO A-consumed and NO A-reference legs to break, and no opaque/axiom callee contract to over-strengthen. refinement.md legs: op1=I (init accumulator), op2=R (contained loop; membership filter subsumed by setOutput no-op on sentinel), op3=R (the fix — remainder propagation; `if remainder not in {passthrough,drop}` guard subsumed by setOutput no-op on sentinel, extensionally equal, G-CONF-diffed), op4=I (return self). No kind-3 legs. The deep-model↔callee correspondence (setOutput ≡ _safe_set_output on the modeled domain of transformable estimators + guard subsumption) is faithful and independently machine-checked by conformance_check.py over 120k+ inputs incl. F2P config. mapping.md bijection is consistent.

VERDICT: SOUND. 6 same-spec wrong impls (incl. prepatch bug, partial-domain, boundary/order, control-flow-effect, ungrounded-oracle echo) all fail to verify under a harness proven able to close correct same-spec variants; positive control verifies with clean axioms; A-legs are empty/deep-model and correspond to the real callee. No verify⇏correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1s.lean`, `atk_2s.lean`, `atk_3s.lean`, `atk_4s.lean`, `atk_5s.lean`, `atk_6s.lean` |

**Non-vacuity.** The positive control `pos_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1s.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2s.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3s.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4s.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5s.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6s.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_correct.lean`

```lean
import Mathlib
-- imports-end

/-!
Propagating an output-container choice through a composite transformer.

A composite transformer holds an ordered collection of contained
sub-transformers together with a fall-back transformer that handles the columns
not claimed by any of them. Each entry is either an actual estimator (which
carries its own output-container configuration) or one of the two reserved
sentinels meaning "pass the columns through unchanged" or "drop the columns".

Configuring the output container of the composite propagates the chosen
container to every contained estimator, and likewise to the fall-back
transformer whenever that fall-back is itself an estimator (i.e. not one of the
two reserved sentinels). A sentinel carries no configuration and is left as is.

So the result is: every contained sub-transformer with its output container set
to the chosen value (sentinels untouched), paired with the fall-back transformer
with its output container set to the chosen value (again, untouched if it is a
sentinel).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Applying the
-- output-container choice to one transformer is modeled DEEPLY (the pure helper
-- `setOutput` below: an estimator records the new container, a sentinel is left
-- unchanged), so there is no `opaque`/`axiom` callee contract. The composite's
-- own container choice and the membership/fitted bookkeeping that produces the
-- contained collection are orthogonal to the modeled behavior and enter through
-- the grounded inputs.
-- axioms-end

-- pure-start
/-- A contained transformer entry: either an actual estimator carrying an
identity `id` and its current output-container configuration `output`, or one of
the two reserved sentinels (`passthrough` / `drop`) that carry no configuration.
(Faithful refinement of a Python transformer slot, which is either an estimator
object or one of the two reserved strings.) -/
inductive Transformer where
  | passthrough
  | drop
  | est (id : Nat) (output : String)
deriving DecidableEq, Repr

/-- Apply an output-container choice to one transformer: an estimator records the
new container value; a sentinel carries no configuration and is returned
unchanged. -/
def setOutput (transform : String) (t : Transformer) : Transformer :=
  match t with
  | .est id _ => .est id transform
  | other => other
-- pure-end

-- post-conditions-start
/-- The result pins both components to their inputs under the chosen container
`transform`: the first component is the contained collection with the container
applied to each entry (sentinels unchanged), and the second component is the
fall-back transformer with the container applied (again unchanged if it is a
sentinel). -/
def problem_spec_setOutput
    (transformers : List Transformer) (remainder : Transformer) (transform : String)
    (result : List Transformer × Transformer) : Prop :=
  result.1 = transformers.map (setOutput transform) ∧
  result.2 = setOutput transform remainder
-- post-conditions-end

-- impl-start
def implementation_setOutput
    (transformers : List Transformer) (remainder : Transformer) (transform : String) :
    List Transformer × Transformer := Id.run do
  let mut outTransformers : List Transformer := []
  for trans in transformers do
    outTransformers := outTransformers ++ [setOutput transform trans]
  -- The real patch guards the remainder call with
  -- `if self.remainder not in {"passthrough", "drop"}`; in this model that
  -- guard is subsumed by `setOutput` being a no-op on a sentinel (the same
  -- coincidence that subsumes the contained loop's sentinel filter,
  -- refinement.md op 2), so the propagation is applied directly.
  -- Auditor note: the spec is FUNCTIONAL — both components are equations, so
  -- it pins `result` uniquely. Any impl extensionally equal to this one (e.g.
  -- one re-adding the real patch's redundant sentinel guard) verifies too;
  -- such a variant is a POSITIVE CONTROL, not a spec-too-weak witness. A
  -- genuine weakness witness must compute a DIFFERENT function.
  let outRemainder := setOutput transform remainder
  return (outTransformers, outRemainder)
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop accumulates the container-applied entries onto the
initial accumulator, generalized over that accumulator (Route B helper). -/
theorem loop_helper_setOutput
    (transform : String) (xs : List Transformer) (init : List Transformer) :
    Id.run (forIn xs init (fun trans r =>
      (do pure PUnit.unit; pure (ForInStep.yield (r ++ [setOutput transform trans]))))) =
      init ++ xs.map (setOutput transform) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    simp only [ih, List.map_cons, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_setOutput :
    ∀ (transformers : List Transformer) (remainder : Transformer) (transform : String),
      problem_spec_setOutput transformers remainder transform
        (implementation_setOutput transformers remainder transform) := by
  intro transformers remainder transform
  unfold implementation_setOutput problem_spec_setOutput
  simp only [Id.run]
  have h := loop_helper_setOutput transform transformers []
  simp only [Id.run] at h
  rw [h]
  simp only [List.nil_append]
  exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY FUNCTIONAL — no same-spec wrong impl can verify. problem_spec_setOutput pins BOTH output components by equations: result.1 = transformers.map (setOutput transform) AND result.2 = setOutput transform remainder. This uniquely determines the result, so any verifying implementation_setOutput must compute exactly this function; there is no room for a spec-too-weak witness.

ATTACKS (6 distinct wrong impls, all same_spec=True vs Solution.lean, verified concurrently ≤4 at a time). Command per file: `bash scripts/lean_verify.sh <path>`.
  atk_1s: prepatch bug — remainder returned unconfigured (outRemainder := remainder). exit=1, error: unsolved goals (line 94). == the actual pre-patch bug (Solution_prepatch.lean), reproduced.
  atk_2s: no propagation to contained transformers (identity on contained loop). exit=1, error: simp made no progress.
  atk_3s: reversed contained order (prepend instead of append). exit=1, error: simp made no progress.
  atk_4s: partial-domain — remainder configured only when transformers nonempty (match transformers | [] => remainder | _ => setOutput). exit=1, error: unsolved goals (line 96).
  atk_5s: ungrounded-oracle echo — hardcoded container 'pandas' on remainder (setOutput "pandas" remainder). exit=1, error: unsolved goals (line 94).
  atk_6s: control-flow effect — drops head contained transformer (for trans in transformers.tail). exit=1, error: simp made no progress.

NONE VERIFIES → protocol step 2 (materialize faithful patch + run_resolve for verifying wrong impls) is VACUOUS; no verifying wrong impl exists, so `patches` is empty. verify⇏correct is NOT exhibited.

PROOF-HARNESS CONFOUND CONTROLLED: an initial weak `first|...|decide` harness failed even on a CORRECT guarded same-spec variant (pos_variant.lean, exit=1) — a false-negative risk. I therefore rebuilt all 6 attacks (the *s files) with a STRONGER harness (loop_helper rewrite + constructor <;> cases transformers <;> cases remainder <;> simp_all[setOutput] <;> rfl/decide) and PROVED that harness closes a correct guarded variant: pos_variant2.lean (remainder handled via explicit match on passthrough/drop/est — same_spec=True) verifies exit=0. The 6 attacks STILL fail (exit=1, genuine 'unsolved goals'/'simp made no progress', NOT sorry/timeout) under that same capable harness. So the failures are due to spec strength, not tactic weakness.

POSITIVE CONTROL: pos_correct.lean = shipped Solution.lean impl+proof verbatim, exit=0. #print axioms correct_setOutput (via pos_axioms.lean) → 'depends on axioms: [propext, Quot.sound]' — clean, no sorryAx / no custom axioms.

A-LEG / MODEL-CORRESPONDENCE AUDIT (my focus): axioms region is EMPTY. `_safe_set_output` (the per-slot container propagation the patch invokes on remainder) is modeled DEEPLY by pure helper `setOutput` (est id _ ↦ est id transform; sentinel ↦ unchanged), which per SPEC_GUIDE §3 is NOT axiomatized. Hence there are NO A-consumed and NO A-reference legs to break, and no opaque/axiom callee contract to over-strengthen. refinement.md legs: op1=I (init accumulator), op2=R (contained loop; membership filter subsumed by setOutput no-op on sentinel), op3=R (the fix — remainder propagation; `if remainder not in {passthrough,drop}` guard subsumed by setOutput no-op on sentinel, extensionally equal, G-CONF-diffed), op4=I (return self). No kind-3 legs. The deep-model↔callee correspondence (setOutput ≡ _safe_set_output on the modeled domain of transformable estimators + guard subsumption) is faithful and independently machine-checked by conformance_check.py over 120k+ inputs incl. F2P config. mapping.md bijection is consistent.

VERDICT: SOUND. 6 same-spec wrong impls (incl. prepatch bug, partial-domain, boundary/order, control-flow-effect, ungrounded-oracle echo) all fail to verify under a harness proven able to close correct same-spec variants; positive control verifies with clean axioms; A-legs are empty/deep-model and correspond to the real callee. No verify⇏correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on scikit-learn__scikit-learn-26323 (lean). Spec models the output-container propagation in ColumnTransformer.set_output (post-patch, sklearn/compose/_column_transformer.py:296-306 + _safe_set_output in utils/_set_output.py:244). Post-conditions pin BOTH components: result.1 = transformers.map (setOutput transform) and result.2 = setOutput transform remainder, where setOutput sets an estimator's container to `transform` and is a no-op on the reserved sentinels.

Verification performed:
- Lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry/admit).
- #print axioms correct_setOutput => [propext, Quot.sound]: no sorryAx, proof is genuine.
- swebench_unified.markers.same_spec(bundle, reference, LeanBackend.language) = True; spec region byte-identical to the accepted gold reference. Spec view confirms axioms region is empty (deeply-modeled changed op, G-AX skips).
- conformance_check.py (G-CONF differential, seed 26323, 120,007 inputs incl. edge cases) => status=pass, 0 disagreements between the impl shadow and a POST-PATCH oracle.

Attempted divergence witnesses vs the real callee, all resolved as non-defects:
1. Sentinel handling: real code skips {"passthrough","drop"} for both the contained loop and (the fix) the remainder; setOutput's no-op-on-sentinel exactly subsumes both guards. Matches on every mixed list.
2. remainder guard (the actual patch): `if self.remainder not in {passthrough,drop}: _safe_set_output(...)` — equals setOutput transform remainder for all four slot kinds (est => configured; sentinel => unchanged). Matches.
3. transform=None early-return in the mixin: the model uses transform:String, which cannot express the Python None object; this is a documented type/domain boundary (mapping.md 'flag dependencies'), not a false claim — a literal string is recorded identically by both sides.
4. non-transforming estimator early-return in _safe_set_output: scoped out of the modeled domain (mapping.md); such slots never appear in a fitted ColumnTransformer's transformers. Legitimate boundary.
5. Aliasing / duplicate ids / remainder identical to a contained slot: element-wise setting is idempotent and order-preserving; final state matches the real callee.

On the declared modeled domain (transforming estimator slots + container strings + the two sentinels) the deep model setOutput agrees with _safe_set_output on every input. No input was found where the spec is stronger than / drifts from the real repo behavior. The spec is also non-trivial: it is functional (pins result uniquely) and the discriminating clause result.2 = setOutput transform remainder is exactly the post-patch fix that the F2P test_remainder_set_output observes (prepatch impl leaves remainder unconfigured and fails this clause). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (consumer-visible) = header docstring + axioms note + pure region (Transformer type, setOutput helper) + post-conditions (problem_spec_setOutput). The impl and proof regions — which DO contain leaky prose ('The real patch guards the remainder call with `if self.remainder not in {"passthrough","drop"}`', 'the added lines (the fix)', 'the real patch's redundant sentinel guard') — are ELIDED by markers.spec_view and never reach the consumer. Verified same_spec(post, prepatch)=True: the spec view is byte-identical across the edit, so it cannot reconstruct which side is gold. Mechanical leakage.screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no narration term). Only changed symbol is `set_output`, which is ALREADY public in the problem_statement ('`ColumnTransformer.set_output` ignores the `remainder`'); the Lean identifiers setOutput/problem_spec_setOutput don't lexically embed it anyway. Semantic check: the discriminating clause `result.2 = setOutput transform remainder` (remainder estimator receives the container) is exactly the behavior the public problem_statement already spells out ('it sets the output to its sub-transformers but it ignores the transformer defined in remainder', with expected-vs-actual output). The sentinel (passthrough/drop) structure is general sklearn domain modeling that also governs the pre-existing contained loop, not edit-specific localization. Spec reveals nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
