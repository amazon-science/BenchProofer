# P2 adversarial audit — sympy__sympy-21596

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,18 @@
 -- impl-start
 def implementation_realParams
     (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
   let mut sols1 : Set ℚ := ∅
   for f in vanish do
     sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
-  let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
+  let mut base_set := base \ sols1
   let mut sols2 : Set ℚ := ∅
   for d in poles do
     sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
   base_set := base_set \ sols2
   return base_set
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +93,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,18 @@
 -- impl-start
 def implementation_realParams
     (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
   let mut sols1 : Set ℚ := ∅
   for f in vanish do
     sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
   let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
   let mut sols2 : Set ℚ := ∅
   for d in poles do
     sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
-  base_set := base_set \ sols2
+  base_set := base_set ∩ sols2
   return base_set
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +93,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,14 @@
 -- impl-start
 def implementation_realParams
     (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
   let mut sols1 : Set ℚ := ∅
   for f in vanish do
     sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
-  let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
-  let mut sols2 : Set ℚ := ∅
-  for d in poles do
-    sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
-  base_set := base_set \ sols2
+  let base_set := base ∩ sols1
   return base_set
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +89,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,26 +60,10 @@
 
 -- impl-start
 def implementation_realParams
-    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
-  let mut sols1 : Set ℚ := ∅
-  for f in vanish do
-    sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
-  let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
-  let mut sols2 : Set ℚ := ∅
-  for d in poles do
-    sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
-  base_set := base_set \ sols2
-  return base_set
+    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := ∅
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +84,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,18 @@
 -- impl-start
 def implementation_realParams
     (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
   let mut sols1 : Set ℚ := ∅
-  for f in vanish do
+  for f in poles do
     sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
   let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
   let mut sols2 : Set ℚ := ∅
-  for d in poles do
+  for d in vanish do
     sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
   base_set := base_set \ sols2
   return base_set
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +93,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,14 @@
 -- impl-start
 def implementation_realParams
     (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
   let mut sols1 : Set ℚ := ∅
   for f in vanish do
     sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
-  let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
-  let mut sols2 : Set ℚ := ∅
-  for d in poles do
-    sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
-  base_set := base_set \ sols2
+  let base_set := (base ∩ sols1) \ sols1
   return base_set
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +89,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,26 +60,10 @@
 
 -- impl-start
 def implementation_realParams
-    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
-  -- union of the imaginary-part factors' zero sets
-  let mut sols1 : Set ℚ := ∅
-  for f in vanish do
-    sols1 := sols1 ∪ {x | f x = 0}
-  -- keep the base parameters that make the value real
-  let mut base_set := base ∩ sols1
-  -- union of the denominator factors' zero sets
-  let mut sols2 : Set ℚ := ∅
-  for d in poles do
-    sols2 := sols2 ∪ {x | d x = 0}
-  -- drop the parameters that make the value undefined
-  base_set := base_set \ sols2
-  return base_set
+    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := base
 -- impl-end
 
 -- proof-start
-/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
-front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
-so the Route-B induction goes through. -/
 theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
     (forIn (m := Id) xs init (fun f r =>
         pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
@@ -100,5 +84,8 @@
   simp only [Id.run, bind]
   rw [fold_zeroUnion, fold_zeroUnion]
   simp only [Set.empty_union]
-  rfl
+  first
+  | rfl
+  | (simp only [Set.inter_comm, Set.diff_eq]; rfl)
+  | ext x; simp [Set.mem_inter_iff, Set.mem_diff, Set.mem_setOf_eq]; tauto
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the real members of a parametrized family of complex values.

A family of complex values is indexed by a *parameter* drawn from a base set of
parameters (for example, the integers). Each value is built from the parameter by
a single rule; the value is *real* exactly when its imaginary part vanishes, and it
is *defined* only when none of the rule's denominators vanish.

The imaginary part of the value, as a function of the parameter, factors into a
list of simpler factors; the imaginary part vanishes precisely when at least one
factor vanishes. Likewise the value is undefined precisely when at least one
denominator factor vanishes.

The set of parameters that yield a real, defined value is therefore obtained from
the base set of parameters by *keeping* those parameters at which some
imaginary-part factor vanishes (an intersection with the union of the factors'
zero sets), and then *removing* those parameters at which some denominator factor
vanishes (a difference against the union of the denominators' zero sets).

This pins the exact set of surviving parameters as a function of the base set and
the two factor lists; nothing in the result is left free. The family-building rule
itself is the unchanged, monotone outer wrapper applied to this parameter set and
is modeled away (refinement.md).
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The quantity modeled — the
-- set of surviving parameters — is built directly from the base parameter set and
-- the two lists of factor functions by ordinary set operations (union over a
-- factor list, then one intersection and one difference). The per-factor
-- zero-set construction is modeled deeply by `zeroUnion` below (refinement.md
-- tags it R, an A-reference modeled in-spec), so no `opaque`/`axiom` callee
-- contract is required. The family-building rule applied to the parameter set is
-- an unchanged, monotone outer wrapper that is modeled away, so it needs no
-- contract either.
-- axioms-end

-- pure-start
/-- The union of the zero sets of a list of factor functions: the set of points
at which *at least one* factor vanishes. Front-recursive so a `for`-accumulator
loop matches it by Route-B induction. -/
def zeroUnion : List (ℚ → ℚ) → Set ℚ
  | []      => ∅
  | f :: fs => {x | f x = 0} ∪ zeroUnion fs
-- pure-end

-- post-conditions-start
/-- The result is exactly the set of parameters drawn from `base` that survive:
keep those at which some `vanish` factor is zero (intersection with the union of
their zero sets), then drop those at which some `poles` factor is zero (difference
against the union of their zero sets). The single output set is fully pinned to
the three inputs. -/
def problem_spec_realParams
    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) (result : Set ℚ) : Prop :=
  result = (base ∩ zeroUnion vanish) \ zeroUnion poles
-- post-conditions-end

-- impl-start
def implementation_realParams
    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
  -- union of the imaginary-part factors' zero sets
  let mut sols1 : Set ℚ := ∅
  for f in vanish do
    sols1 := sols1 ∪ {x | f x = 0}
  -- keep the base parameters that make the value real
  let mut base_set := base ∩ sols1
  -- union of the denominator factors' zero sets
  let mut sols2 : Set ℚ := ∅
  for d in poles do
    sols2 := sols2 ∪ {x | d x = 0}
  -- drop the parameters that make the value undefined
  base_set := base_set \ sols2
  return base_set
-- impl-end

-- proof-start
/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
so the Route-B induction goes through. -/
theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
    (forIn (m := Id) xs init (fun f r =>
        pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, zeroUnion, Set.union_empty]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp only [zeroUnion, Set.union_assoc]

theorem correct_realParams :
    ∀ (base : Set ℚ) (vanish poles : List (ℚ → ℚ)),
      problem_spec_realParams base vanish poles
        (implementation_realParams base vanish poles) := by
  intro base vanish poles
  unfold problem_spec_realParams implementation_realParams
  simp only [Id.run, bind]
  rw [fold_zeroUnion, fold_zeroUnion]
  simp only [Set.empty_union]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinning extensional set equality. post-conditions: `problem_spec_realParams base vanish poles result := result = (base ∩ zeroUnion vanish) \ zeroUnion poles`. Because `result` is pinned to a single closed set-expression of the three inputs, ANY impl whose correct_realParams closes must be provably equal to that exact set on all inputs — a genuinely wrong impl cannot close. axioms region is a comment only; axioms=[] and deep_model_references=[] in meta; no A-consumed legs.

SAME_SPEC: all 8 attack files + pos.lean report same_spec=True against Solution.lean (axioms/pure/pre/post byte-identical; only impl region — and for atk_8 the proof — edited).

### ATTACKS (each `bash scripts/lean_verify.sh <file>` from root):
- atk_1 = PREPATCH bug (`base \ sols1` difference instead of `∩`): EXIT 1 (does NOT close). This is also the recorded prepatch counterexample; Solution_prepatch.lean itself verifies to EXIT 1 → prepatch bug reproduced.
- atk_2 = intersect poles (`∩ sols2`) instead of subtract: EXIT 1.
- atk_3 = drop pole loop entirely (`base ∩ sols1`): EXIT 1.
- atk_4 = constant ∅ (partial/boundary): EXIT 1.
- atk_5 = swap vanish/poles roles: EXIT 1.
- atk_6 = `(base ∩ sols1) \ sols1` (control-flow-effect, reuse vanish set as poles): EXIT 1.
- atk_7 = identity `return base` (ungrounded/echo of domain): EXIT 1.
All 7 same-spec WRONG impls FAIL to close (EXIT 1), so NONE is a `verified ∧ ¬correct` candidate → no faithful patch needs to be materialized/resolved (patches={} is correct; there is nothing to resolve-test).

### CLOSING PROOFS (only mathematically-correct impls close, as required):
- pos.lean = gold impl: EXIT 0. `#print axioms correct_realParams` → [propext, Quot.sound] (clean, no sorryAx/custom axiom).
- atk_8.lean = ECHO of the spec RHS `(base ∩ zeroUnion vanish) \ zeroUnion poles` (rfl proof): EXIT 0; `#print axioms` → [propext] (clean). This echo is the CORRECT set, not a weakness; its faithful patch is the gold patch which resolves — under the fixed G-PANEL-1/eq derivation a resolving same-spec candidate is not a break. Not listed under `attacks` because it is not a wrong impl.

REFINEMENT.MD A-LEG AUDIT: 5 legs, tags R (rows1,3,5)/A-reference(rows1,3)/I(rows2,4) — NO kind-3 (changed-inexpressible) leg; the 'No changed-inexpressible op' claim holds. The A-reference legs assert `zeroUnion fs` models `_solution_union(fs,sym) = Union(*[zero set of each factor])`. `zeroUnion` is an in-spec front-recursive union of `{x | f x = 0}` and consumes NO axiom (axiom_check.py is a legitimate skip stub; nothing is axiomatized). Correspondence is faithful: FiniteSet(root) vs ConditionSet(Eq(f,0)) are two representations of the same per-factor zero set; the modeled quantity (surviving parameter set after `&=` intersect then `-=` difference) is exactly the patch's observable effect, and `imageset(lam,·)` is a monotone unchanged outer wrapper legitimately wrapped away. No ungrounded oracle to echo-exploit.

CONCLUSION: ≥7 distinct same-spec wrong impls attempted and all fail to verify; the only impls that verify (gold + spec-echo) are correct with clean axioms; prepatch reproduced; refinement A-legs sound. No verify⇏correct gap found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting the real members of a parametrized family of complex values.

A family of complex values is indexed by a *parameter* drawn from a base set of
parameters (for example, the integers). Each value is built from the parameter by
a single rule; the value is *real* exactly when its imaginary part vanishes, and it
is *defined* only when none of the rule's denominators vanish.

The imaginary part of the value, as a function of the parameter, factors into a
list of simpler factors; the imaginary part vanishes precisely when at least one
factor vanishes. Likewise the value is undefined precisely when at least one
denominator factor vanishes.

The set of parameters that yield a real, defined value is therefore obtained from
the base set of parameters by *keeping* those parameters at which some
imaginary-part factor vanishes (an intersection with the union of the factors'
zero sets), and then *removing* those parameters at which some denominator factor
vanishes (a difference against the union of the denominators' zero sets).

This pins the exact set of surviving parameters as a function of the base set and
the two factor lists; nothing in the result is left free. The family-building rule
itself is the unchanged, monotone outer wrapper applied to this parameter set and
is modeled away (refinement.md).
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The quantity modeled — the
-- set of surviving parameters — is built directly from the base parameter set and
-- the two lists of factor functions by ordinary set operations (union over a
-- factor list, then one intersection and one difference). The per-factor
-- zero-set construction is modeled deeply by `zeroUnion` below (refinement.md
-- tags it R, an A-reference modeled in-spec), so no `opaque`/`axiom` callee
-- contract is required. The family-building rule applied to the parameter set is
-- an unchanged, monotone outer wrapper that is modeled away, so it needs no
-- contract either.
-- axioms-end

-- pure-start
/-- The union of the zero sets of a list of factor functions: the set of points
at which *at least one* factor vanishes. Front-recursive so a `for`-accumulator
loop matches it by Route-B induction. -/
def zeroUnion : List (ℚ → ℚ) → Set ℚ
  | []      => ∅
  | f :: fs => {x | f x = 0} ∪ zeroUnion fs
-- pure-end

-- post-conditions-start
/-- The result is exactly the set of parameters drawn from `base` that survive:
keep those at which some `vanish` factor is zero (intersection with the union of
their zero sets), then drop those at which some `poles` factor is zero (difference
against the union of their zero sets). The single output set is fully pinned to
the three inputs. -/
def problem_spec_realParams
    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) (result : Set ℚ) : Prop :=
  result = (base ∩ zeroUnion vanish) \ zeroUnion poles
-- post-conditions-end

-- impl-start
def implementation_realParams
    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
  -- union of the imaginary-part factors' zero sets
  let mut sols1 : Set ℚ := ∅
  for f in vanish do
    sols1 := sols1 ∪ {x | f x = 0}
  -- keep the base parameters that make the value real
  let mut base_set := base ∩ sols1
  -- union of the denominator factors' zero sets
  let mut sols2 : Set ℚ := ∅
  for d in poles do
    sols2 := sols2 ∪ {x | d x = 0}
  -- drop the parameters that make the value undefined
  base_set := base_set \ sols2
  return base_set
-- impl-end

-- proof-start
/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
so the Route-B induction goes through. -/
theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
    (forIn (m := Id) xs init (fun f r =>
        pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, zeroUnion, Set.union_empty]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp only [zeroUnion, Set.union_assoc]

theorem correct_realParams :
    ∀ (base : Set ℚ) (vanish poles : List (ℚ → ℚ)),
      problem_spec_realParams base vanish poles
        (implementation_realParams base vanish poles) := by
  intro base vanish poles
  unfold problem_spec_realParams implementation_realParams
  simp only [Id.run, bind]
  rw [fold_zeroUnion, fold_zeroUnion]
  simp only [Set.empty_union]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinning extensional set equality. post-conditions: `problem_spec_realParams base vanish poles result := result = (base ∩ zeroUnion vanish) \ zeroUnion poles`. Because `result` is pinned to a single closed set-expression of the three inputs, ANY impl whose correct_realParams closes must be provably equal to that exact set on all inputs — a genuinely wrong impl cannot close. axioms region is a comment only; axioms=[] and deep_model_references=[] in meta; no A-consumed legs.

SAME_SPEC: all 8 attack files + pos.lean report same_spec=True against Solution.lean (axioms/pure/pre/post byte-identical; only impl region — and for atk_8 the proof — edited).

### ATTACKS (each `bash scripts/lean_verify.sh <file>` from root):
- atk_1 = PREPATCH bug (`base \ sols1` difference instead of `∩`): EXIT 1 (does NOT close). This is also the recorded prepatch counterexample; Solution_prepatch.lean itself verifies to EXIT 1 → prepatch bug reproduced.
- atk_2 = intersect poles (`∩ sols2`) instead of subtract: EXIT 1.
- atk_3 = drop pole loop entirely (`base ∩ sols1`): EXIT 1.
- atk_4 = constant ∅ (partial/boundary): EXIT 1.
- atk_5 = swap vanish/poles roles: EXIT 1.
- atk_6 = `(base ∩ sols1) \ sols1` (control-flow-effect, reuse vanish set as poles): EXIT 1.
- atk_7 = identity `return base` (ungrounded/echo of domain): EXIT 1.
All 7 same-spec WRONG impls FAIL to close (EXIT 1), so NONE is a `verified ∧ ¬correct` candidate → no faithful patch needs to be materialized/resolved (patches={} is correct; there is nothing to resolve-test).

### CLOSING PROOFS (only mathematically-correct impls close, as required):
- pos.lean = gold impl: EXIT 0. `#print axioms correct_realParams` → [propext, Quot.sound] (clean, no sorryAx/custom axiom).
- atk_8.lean = ECHO of the spec RHS `(base ∩ zeroUnion vanish) \ zeroUnion poles` (rfl proof): EXIT 0; `#print axioms` → [propext] (clean). This echo is the CORRECT set, not a weakness; its faithful patch is the gold patch which resolves — under the fixed G-PANEL-1/eq derivation a resolving same-spec candidate is not a break. Not listed under `attacks` because it is not a wrong impl.

REFINEMENT.MD A-LEG AUDIT: 5 legs, tags R (rows1,3,5)/A-reference(rows1,3)/I(rows2,4) — NO kind-3 (changed-inexpressible) leg; the 'No changed-inexpressible op' claim holds. The A-reference legs assert `zeroUnion fs` models `_solution_union(fs,sym) = Union(*[zero set of each factor])`. `zeroUnion` is an in-spec front-recursive union of `{x | f x = 0}` and consumes NO axiom (axiom_check.py is a legitimate skip stub; nothing is axiomatized). Correspondence is faithful: FiniteSet(root) vs ConditionSet(Eq(f,0)) are two representations of the same per-factor zero set; the modeled quantity (surviving parameter set after `&=` intersect then `-=` difference) is exactly the patch's observable effect, and `imageset(lam,·)` is a monotone unchanged outer wrapper legitimately wrapped away. No ungrounded oracle to echo-exploit.

CONCLUSION: ≥7 distinct same-spec wrong impls attempted and all fail to verify; the only impls that verify (gold + spec-echo) are correct with clean axioms; prepatch reproduced; refinement A-legs sound. No verify⇏correct gap found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift). No diverging input found. Checks:

1) COMPILES + CLEAN AXIOMS: scripts/lean_verify.sh exits 0; `#print axioms correct_realParams` = [propext, Quot.sound] only, no sorryAx — the correctness proof is real.

2) same_spec (swebench_unified.markers, LeanBackend) = True: the spec view (axioms/pure/post-conditions) is byte-identical between Solution.lean and Solution_prepatch.lean; only impl/proof differ. Prepatch impl reproduces the gold bug (`base \ zeroUnion vanish`, a DIFFERENCE) while spec demands `base ∩ zeroUnion vanish` (INTERSECT) — exactly the `-=`→`&=` fix in patch.diff.

3) CONFORMANCE: conformance_check.py passes — checked=120005, disagreements=0, prepatch_discriminated=True.

4) SPEC vs REAL REPO (post-patch worktree). Modeled quantity = surviving parameter set base_set after the `other == S.Reals` branch of intersection_sets(ImageSet,Set). Gold: base_set &= _solution_union(Mul.make_args(numer(im)),n) then base_set -= _solution_union(denoms(f),n). _solution_union unions per-factor zero sets (FiniteSet(root) if solve_linear succeeds, else ConditionSet(Eq(f,0))) = zeroUnion. So the callee computes (base ∩ zeroUnion vanish) \ zeroUnion poles = problem_spec_realParams. Confirmed on real sympy:
   - n+(n-1)(n+1)I over ℤ → params {-1,1}, 2∉ (matches problem_statement)
   - 3*(n-1)I → {1} (constant multiplicative factor contributes empty zero set — harmless, matches zeroUnion of a nonvanishing constant = ∅)
   - (n+(n-1)I)/(n-2): numer(im)=n-1 → keep {1}; denom (n-2) → pole {2}; param {1} (imageset wraps to {-1}, the wrapped-away outer step)
   - (n+(n-1)I)/(n-1): root==pole → kept then removed → ∅
   - n²-2 (irrational roots) → ConditionSet with no rational solutions = ∅ over ℚ, matching Set ℚ type refinement

Order of operations (intersect then difference) matches; difference is applied unconditionally in both. The ℚ type refinement preserves membership over the integer/rational base domain. The `imageset(lam,·)` outer step is legitimately wrapped away (unchanged, monotone image map — equal param sets ⟺ equal image sets up to the unchanged lambda). The spec is neither too strong nor too weak relative to the modeled callee. No divergence exhibited.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leak screen (leakage.screen) PASSES: 0 hard_failures. same_spec(prepatch, postpatch)=True — spec region byte-identical, so the spec was not tuned to the gold. Spec view fully abstracts the fix: no gold-patch identifiers appear (_solution_union, solve_linear, numer, denoms, Mul.make_args, FiniteSet, ConditionSet, Union, imageset, S.Reals); variables renamed to base/vanish/poles/zeroUnion. Semantic check of the gold discriminator (the buggy `base_set -= FiniteSet(xis)` becoming `base_set &= _solution_union(...)`, encoded in the spec as `base ∩ zeroUnion vanish`): this is DERIVABLE from the public problem_statement, which states the required correct output `S1.intersect(Reals) == {-1, 1}` for `S1 = imageset(Lambda(n, n+(n-1)(n+1)I), ℤ)`. The reals are exactly the roots of the imaginary-part factors `(n-1)(n+1)`, so 'keep the parameters where the imaginary part vanishes' (intersection) is precisely what the stated corrected answer {-1,1} forces — a solver with the problem_statement reaches the intersection semantics. The pole-difference term `\ zeroUnion poles` is standard mathematical domain knowledge (a value is defined only where denominators are nonzero) and is NOT the discriminating gold edit — both prepatch and postpatch subtract poles. The spec is an abstract behavioral restatement of the publicly-stated correct behavior, exposing no implementation structure, hidden-test fixtures, or phrasing beyond problem_statement. NO leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
