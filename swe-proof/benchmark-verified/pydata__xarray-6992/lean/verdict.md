# P2 adversarial audit — pydata__xarray-6992

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,14 +86,12 @@
   let mut dropIndexes : List String := []
   let mut dropVariables : List String := []
   for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
     dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
     if drop then
       dropVariables := dropVariables ++ [name]
   let indexNames := removeAll c.indexNames dropIndexes
   let varNames := removeAll c.varNames dropVariables
-  let coordNames := removeAll c.coordNames dropVariables
+  let coordNames := c.coordNames
   return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,13 +86,11 @@
   let mut dropIndexes : List String := []
   let mut dropVariables : List String := []
   for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
     dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
     if drop then
       dropVariables := dropVariables ++ [name]
   let indexNames := removeAll c.indexNames dropIndexes
-  let varNames := removeAll c.varNames dropVariables
+  let varNames := c.varNames
   let coordNames := removeAll c.coordNames dropVariables
   return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,12 +86,10 @@
   let mut dropIndexes : List String := []
   let mut dropVariables : List String := []
   for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
     dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
     if drop then
       dropVariables := dropVariables ++ [name]
-  let indexNames := removeAll c.indexNames dropIndexes
+  let indexNames := c.indexNames
   let varNames := removeAll c.varNames dropVariables
   let coordNames := removeAll c.coordNames dropVariables
   return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,10 +86,8 @@
   let mut dropIndexes : List String := []
   let mut dropVariables : List String := []
   for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
     dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
-    if drop then
+    if !drop then
       dropVariables := dropVariables ++ [name]
   let indexNames := removeAll c.indexNames dropIndexes
   let varNames := removeAll c.varNames dropVariables
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,14 +86,12 @@
   let mut dropIndexes : List String := []
   let mut dropVariables : List String := []
   for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
     dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
     if drop then
       dropVariables := dropVariables ++ [name]
   let indexNames := removeAll c.indexNames dropIndexes
   let varNames := removeAll c.varNames dropVariables
-  let coordNames := removeAll c.coordNames dropVariables
+  let coordNames := removeAll c.coordNames resetNames
   return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,14 +83,8 @@
 def implementation_resetIndexCoords
     (c : ContainerNames) (resetNames : List String) (drop : Bool) :
     ContainerNames := Id.run do
-  let mut dropIndexes : List String := []
-  let mut dropVariables : List String := []
-  for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
-    dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
-    if drop then
-      dropVariables := dropVariables ++ [name]
+  let dropIndexes : List String := resetNames.take 1
+  let dropVariables : List String := if drop then resetNames.take 1 else []
   let indexNames := removeAll c.indexNames dropIndexes
   let varNames := removeAll c.varNames dropVariables
   let coordNames := removeAll c.coordNames dropVariables
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,15 +86,13 @@
   let mut dropIndexes : List String := []
   let mut dropVariables : List String := []
   for name in resetNames do
-    -- the coordinate names sharing this plain dimension index: just `name`
     dropIndexes := dropIndexes ++ [name]
-    -- discard-or-convert the underlying coordinate
     if drop then
       dropVariables := dropVariables ++ [name]
   let indexNames := removeAll c.indexNames dropIndexes
   let varNames := removeAll c.varNames dropVariables
   let coordNames := removeAll c.coordNames dropVariables
-  return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
+  return { varNames := coordNames, coordNames := varNames, indexNames := indexNames }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Releasing a dimension index from a labelled multi-dimensional container.

A container tracks three name collections over the same underlying axes:

  * `varNames`   — the stored data/coordinate variables, by name;
  * `coordNames` — the subset of those names that are coordinates;
  * `indexNames` — the names that currently carry a fast lookup index.

A core invariant ties them together: every coordinate name must also be a stored
variable name (`coordNames ⊆ varNames`). When a dimension index is released, the
container must preserve that invariant.

This models releasing one or more *plain dimension indexes* — each a lookup index
whose only associated coordinate is the dimension's own name. Releasing such a
name always removes its lookup index. A boolean `drop` then decides the fate of
the underlying coordinate:

  * when `drop` is true, the coordinate is discarded — its name leaves BOTH the
    stored variables and the coordinate set together, so the invariant is kept;
  * when `drop` is false, the coordinate is retained as an ordinary stored
    variable — its name stays in both collections unchanged.

The desired behaviour is stated abstractly as an input→output relation over the
three name collections; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- The set of coordinate names sharing one dimension index is, for a plain
-- dimension index, exactly the singleton of that index's own name; this is
-- modeled DEEPLY as the literal singleton (a deep-model reference, not a
-- consumed callee contract). Converting a retained coordinate to an ordinary
-- stored variable changes only its internal kind, never its name, so it is the
-- identity on the name-collection abstraction. No separate property of an
-- unchanged callee is consumed by the proof, so there is no `opaque`/`axiom`
-- callee declaration here.
-- axioms-end

-- pure-start
/-- A labelled container observed through the only features that determine the
result of releasing a dimension index: the names of its stored variables, the
names that are coordinates, and the names that carry a lookup index. -/
structure ContainerNames where
  /-- names of all stored variables -/
  varNames : List String
  /-- names that are coordinates (must be a sub-collection of `varNames`) -/
  coordNames : List String
  /-- names that currently carry a lookup index -/
  indexNames : List String
deriving Repr, DecidableEq

/-- Drop from `xs` every name occurring in `ys`, preserving the order of the
names that remain. -/
def removeAll (xs ys : List String) : List String :=
  xs.filter (fun k => ¬ ys.contains k)
-- pure-end

-- post-conditions-start
/-- Releasing the plain dimension indexes named in `resetNames` (with flag
`drop`). The names whose coordinates are discarded are exactly `resetNames` when
`drop` is true and none otherwise. The result is pinned in full (directive 5
frame; directive 8 grounded in the input collections):

  * every released name loses its lookup index;
  * a discarded coordinate's name leaves the stored variables AND the coordinate
    set together — so the invariant `coordNames ⊆ varNames` is preserved;
  * when nothing is discarded, the stored variables and coordinate set are
    unchanged. -/
def problem_spec_resetIndexCoords
    (c : ContainerNames) (resetNames : List String) (drop : Bool)
    (result : ContainerNames) : Prop :=
  let dropVariables := if drop then resetNames else ([] : List String)
  result.indexNames = removeAll c.indexNames resetNames ∧
  result.varNames   = removeAll c.varNames dropVariables ∧
  result.coordNames = removeAll c.coordNames dropVariables
-- post-conditions-end

-- impl-start
def implementation_resetIndexCoords
    (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    ContainerNames := Id.run do
  let mut dropIndexes : List String := []
  let mut dropVariables : List String := []
  for name in resetNames do
    -- the coordinate names sharing this plain dimension index: just `name`
    dropIndexes := dropIndexes ++ [name]
    -- discard-or-convert the underlying coordinate
    if drop then
      dropVariables := dropVariables ++ [name]
  let indexNames := removeAll c.indexNames dropIndexes
  let varNames := removeAll c.varNames dropVariables
  let coordNames := removeAll c.coordNames dropVariables
  return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
-- impl-end

-- proof-start
-- @decl:loopState-start
/-- The pair state threaded through the `for` loop, in the program's declaration
order: `dropIndexes` first, `dropVariables` second. -/
def loopState : Type := List String × List String
-- @decl:loopState-end

-- @decl:loopBody-start
/-- The per-iteration transition of the loop body: append the current `name` to
`dropIndexes`, and (only when `drop`) also to `dropVariables`. -/
def loopBody (drop : Bool) (name : String) (s : List String × List String) :
    ForInStep (List String × List String) :=
  ForInStep.yield (s.1 ++ [name], if drop then s.2 ++ [name] else s.2)
-- @decl:loopBody-end

-- @ns:loop_closed_form-start
-- @decl:loop_closed_form-start
/-- Closed form of the loop's tuple accumulator: folding `loopBody` over
`resetNames` from `(di, dv)` yields `(di ++ resetNames, dv ++ (if drop then
resetNames else []))`. Stated over the FULL tuple (declaration order) so it
unifies with the desugared `forIn`. -/
theorem loop_closed_form (drop : Bool) (resetNames di dv : List String) :
    (forIn resetNames (di, dv) (fun name s => loopBody drop name s) :
        Id (List String × List String))
      = (di ++ resetNames, dv ++ (if drop then resetNames else ([] : List String))) := by
  induction resetNames generalizing di dv with
  | nil => rw [List.forIn_nil]; simp [pure]
  | cons name rest ih =>
    rw [List.forIn_cons]
    show (forIn rest (di ++ [name], if drop then dv ++ [name] else dv)
            (fun name s => loopBody drop name s) : Id _) = _
    rw [ih]
    cases drop with
    | true => simp [List.append_assoc]
    | false => simp [List.append_assoc]
-- @decl:loop_closed_form-end
-- @ns:loop_closed_form-end

-- @ns:reduce_impl-start
-- @decl:reduce_impl-start
/-- Evaluate the implementation to the explicit record built from the closed-form
accumulators. -/
theorem reduce_impl (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    implementation_resetIndexCoords c resetNames drop
      = { varNames := removeAll c.varNames (if drop then resetNames else ([] : List String)),
          coordNames := removeAll c.coordNames (if drop then resetNames else ([] : List String)),
          indexNames := removeAll c.indexNames resetNames } := by
  unfold implementation_resetIndexCoords
  simp only [Id.run, bind, pure]
  have key : ∀ (l di dv : List String),
      (forIn l (⟨di, dv⟩ : MProd (List String) (List String))
        (fun name r => if drop = true then ForInStep.yield ⟨r.1 ++ [name], r.2 ++ [name]⟩
          else ForInStep.yield ⟨r.1 ++ [name], r.2⟩) : Id (MProd (List String) (List String)))
      = ⟨di ++ l, dv ++ (if drop then l else ([] : List String))⟩ := by
    intro l
    induction l with
    | nil => intro di dv; cases drop <;>
        simp only [List.forIn_nil, List.append_nil, if_true, if_false, Bool.false_eq_true] <;> rfl
    | cons a t ih =>
        intro di dv
        rw [List.forIn_cons]
        cases drop <;>
          · show forIn t _ _ = _
            rw [ih]
            simp [List.append_assoc]
  rw [key]
  simp
-- @decl:reduce_impl-end
-- @ns:reduce_impl-end

-- @ns:match_spec-start
-- @decl:match_spec-start
/-- The concrete record produced by `reduce_impl` satisfies the specification:
all three postcondition conjuncts hold. -/
theorem match_spec (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    problem_spec_resetIndexCoords c resetNames drop
      { varNames := removeAll c.varNames (if drop then resetNames else ([] : List String)),
        coordNames := removeAll c.coordNames (if drop then resetNames else ([] : List String)),
        indexNames := removeAll c.indexNames resetNames } := by
  refine ⟨rfl, rfl, rfl⟩
-- @decl:match_spec-end
-- @ns:match_spec-end


theorem correct_resetIndexCoords :
    ∀ (c : ContainerNames) (resetNames : List String) (drop : Bool),
    problem_spec_resetIndexCoords c resetNames drop
      (implementation_resetIndexCoords c resetNames drop) := by
  intro c resetNames drop
  rw [reduce_impl]
  exact match_spec c resetNames drop
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. verifier `bash scripts/lean_verify.sh <file>`.

SPEC SHAPE: problem_spec_resetIndexCoords is FULLY FUNCTIONAL — it pins ALL THREE output collections to exact input-determined functions: indexNames'=removeAll c.indexNames resetNames, varNames'=removeAll c.varNames (drop?resetNames:[]), coordNames'=removeAll c.coordNames (drop?resetNames:[]). removeAll = order-preserving List.filter. The correct output is UNIQUE for every input, so any impl that closes correct_resetIndexCoords must be extensionally equal to the spec function; two verifying impls therefore have behaviorally identical refined patches. verify=>correct holds by construction — there is no room for a verify-but-wrong gap.

POSITIVE CONTROL: pos_control.lean (byte-identical bundle Solution.lean) -> lean_verify exit 0; `#print axioms correct_resetIndexCoords` = [propext, Quot.sound] (clean, no sorryAx).

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec, LeanBackend; only impl region edited, axioms/pure/pre/post byte-identical):
- atk_1 PREPATCH BUG (coordNames := c.coordNames, unsubtracted — the reported invariant violation): lean_verify exit 1, error 'unsolved goals' at the reduce_impl step (144:63). Prepatch bug reproduced: this wrong impl does NOT verify.
- atk_2 varNames unsubtracted (varNames := c.varNames): exit 1, unsolved goals.
- atk_3 indexNames unsubtracted (indexNames := c.indexNames): exit 1, unsolved goals.
- atk_4 control-flow effect (dropVariables built under !drop): exit 1, rewrite failed (163:6).
- atk_5 ungrounded-oracle echo (coordNames subtracted by resetNames ignoring drop): exit 1, unsolved goals.
- atk_6 partial-domain (only resetNames.take 1 processed): exit 1, rewrite failed (159:6).
- atk_7 structural swap (varNames/coordNames outputs swapped): exit 1, unsolved goals.

All 7 exits collected via concurrent background jobs (<=4 at a time). Every failure is genuine (unsolved goals / rewrite pattern-not-found), NONE is a sorry, NONE a timeout.

PROTOCOL STEP 2: the set of wrong impls whose proof CLOSES with clean axioms is EMPTY (no attack verified), so there is no faithful refined patch to materialize/run_resolve. Nothing to resolve; nothing breaks the spec.

REFINEMENT.MD LEG AUDIT: op1=I, op2=A-reference (get_all_coords(name)=={name} modeled deeply as literal [name]; ships NO opaque/axiom — confirmed by clean [propext,Quot.sound] axioms; correspondence validated by axiom_check.py 38,551 plain-index trials per verdict.md), ops3-6=R (mechanically covered by conformance_check.py, 120,004 trials, 0 disagreements). No A-consumed leg, no kind-3 leg. A-reference correspondence to the real callee holds.

VERDICT: SOUND — >=5 distinct same-spec wrong impls (7) all attempted; none produced a closing clean-axiom proof, hence no verify-but-non-resolving patch exists. The fully-functional spec admits only the correct behavior.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

/-!
Releasing a dimension index from a labelled multi-dimensional container.

A container tracks three name collections over the same underlying axes:

  * `varNames`   — the stored data/coordinate variables, by name;
  * `coordNames` — the subset of those names that are coordinates;
  * `indexNames` — the names that currently carry a fast lookup index.

A core invariant ties them together: every coordinate name must also be a stored
variable name (`coordNames ⊆ varNames`). When a dimension index is released, the
container must preserve that invariant.

This models releasing one or more *plain dimension indexes* — each a lookup index
whose only associated coordinate is the dimension's own name. Releasing such a
name always removes its lookup index. A boolean `drop` then decides the fate of
the underlying coordinate:

  * when `drop` is true, the coordinate is discarded — its name leaves BOTH the
    stored variables and the coordinate set together, so the invariant is kept;
  * when `drop` is false, the coordinate is retained as an ordinary stored
    variable — its name stays in both collections unchanged.

The desired behaviour is stated abstractly as an input→output relation over the
three name collections; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- The set of coordinate names sharing one dimension index is, for a plain
-- dimension index, exactly the singleton of that index's own name; this is
-- modeled DEEPLY as the literal singleton (a deep-model reference, not a
-- consumed callee contract). Converting a retained coordinate to an ordinary
-- stored variable changes only its internal kind, never its name, so it is the
-- identity on the name-collection abstraction. No separate property of an
-- unchanged callee is consumed by the proof, so there is no `opaque`/`axiom`
-- callee declaration here.
-- axioms-end

-- pure-start
/-- A labelled container observed through the only features that determine the
result of releasing a dimension index: the names of its stored variables, the
names that are coordinates, and the names that carry a lookup index. -/
structure ContainerNames where
  /-- names of all stored variables -/
  varNames : List String
  /-- names that are coordinates (must be a sub-collection of `varNames`) -/
  coordNames : List String
  /-- names that currently carry a lookup index -/
  indexNames : List String
deriving Repr, DecidableEq

/-- Drop from `xs` every name occurring in `ys`, preserving the order of the
names that remain. -/
def removeAll (xs ys : List String) : List String :=
  xs.filter (fun k => ¬ ys.contains k)
-- pure-end

-- post-conditions-start
/-- Releasing the plain dimension indexes named in `resetNames` (with flag
`drop`). The names whose coordinates are discarded are exactly `resetNames` when
`drop` is true and none otherwise. The result is pinned in full (directive 5
frame; directive 8 grounded in the input collections):

  * every released name loses its lookup index;
  * a discarded coordinate's name leaves the stored variables AND the coordinate
    set together — so the invariant `coordNames ⊆ varNames` is preserved;
  * when nothing is discarded, the stored variables and coordinate set are
    unchanged. -/
def problem_spec_resetIndexCoords
    (c : ContainerNames) (resetNames : List String) (drop : Bool)
    (result : ContainerNames) : Prop :=
  let dropVariables := if drop then resetNames else ([] : List String)
  result.indexNames = removeAll c.indexNames resetNames ∧
  result.varNames   = removeAll c.varNames dropVariables ∧
  result.coordNames = removeAll c.coordNames dropVariables
-- post-conditions-end

-- impl-start
def implementation_resetIndexCoords
    (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    ContainerNames := Id.run do
  let mut dropIndexes : List String := []
  let mut dropVariables : List String := []
  for name in resetNames do
    -- the coordinate names sharing this plain dimension index: just `name`
    dropIndexes := dropIndexes ++ [name]
    -- discard-or-convert the underlying coordinate
    if drop then
      dropVariables := dropVariables ++ [name]
  let indexNames := removeAll c.indexNames dropIndexes
  let varNames := removeAll c.varNames dropVariables
  let coordNames := removeAll c.coordNames dropVariables
  return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
-- impl-end

-- proof-start
-- @decl:loopState-start
/-- The pair state threaded through the `for` loop, in the program's declaration
order: `dropIndexes` first, `dropVariables` second. -/
def loopState : Type := List String × List String
-- @decl:loopState-end

-- @decl:loopBody-start
/-- The per-iteration transition of the loop body: append the current `name` to
`dropIndexes`, and (only when `drop`) also to `dropVariables`. -/
def loopBody (drop : Bool) (name : String) (s : List String × List String) :
    ForInStep (List String × List String) :=
  ForInStep.yield (s.1 ++ [name], if drop then s.2 ++ [name] else s.2)
-- @decl:loopBody-end

-- @ns:loop_closed_form-start
-- @decl:loop_closed_form-start
/-- Closed form of the loop's tuple accumulator: folding `loopBody` over
`resetNames` from `(di, dv)` yields `(di ++ resetNames, dv ++ (if drop then
resetNames else []))`. Stated over the FULL tuple (declaration order) so it
unifies with the desugared `forIn`. -/
theorem loop_closed_form (drop : Bool) (resetNames di dv : List String) :
    (forIn resetNames (di, dv) (fun name s => loopBody drop name s) :
        Id (List String × List String))
      = (di ++ resetNames, dv ++ (if drop then resetNames else ([] : List String))) := by
  induction resetNames generalizing di dv with
  | nil => rw [List.forIn_nil]; simp [pure]
  | cons name rest ih =>
    rw [List.forIn_cons]
    show (forIn rest (di ++ [name], if drop then dv ++ [name] else dv)
            (fun name s => loopBody drop name s) : Id _) = _
    rw [ih]
    cases drop with
    | true => simp [List.append_assoc]
    | false => simp [List.append_assoc]
-- @decl:loop_closed_form-end
-- @ns:loop_closed_form-end

-- @ns:reduce_impl-start
-- @decl:reduce_impl-start
/-- Evaluate the implementation to the explicit record built from the closed-form
accumulators. -/
theorem reduce_impl (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    implementation_resetIndexCoords c resetNames drop
      = { varNames := removeAll c.varNames (if drop then resetNames else ([] : List String)),
          coordNames := removeAll c.coordNames (if drop then resetNames else ([] : List String)),
          indexNames := removeAll c.indexNames resetNames } := by
  unfold implementation_resetIndexCoords
  simp only [Id.run, bind, pure]
  have key : ∀ (l di dv : List String),
      (forIn l (⟨di, dv⟩ : MProd (List String) (List String))
        (fun name r => if drop = true then ForInStep.yield ⟨r.1 ++ [name], r.2 ++ [name]⟩
          else ForInStep.yield ⟨r.1 ++ [name], r.2⟩) : Id (MProd (List String) (List String)))
      = ⟨di ++ l, dv ++ (if drop then l else ([] : List String))⟩ := by
    intro l
    induction l with
    | nil => intro di dv; cases drop <;>
        simp only [List.forIn_nil, List.append_nil, if_true, if_false, Bool.false_eq_true] <;> rfl
    | cons a t ih =>
        intro di dv
        rw [List.forIn_cons]
        cases drop <;>
          · show forIn t _ _ = _
            rw [ih]
            simp [List.append_assoc]
  rw [key]
  simp
-- @decl:reduce_impl-end
-- @ns:reduce_impl-end

-- @ns:match_spec-start
-- @decl:match_spec-start
/-- The concrete record produced by `reduce_impl` satisfies the specification:
all three postcondition conjuncts hold. -/
theorem match_spec (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    problem_spec_resetIndexCoords c resetNames drop
      { varNames := removeAll c.varNames (if drop then resetNames else ([] : List String)),
        coordNames := removeAll c.coordNames (if drop then resetNames else ([] : List String)),
        indexNames := removeAll c.indexNames resetNames } := by
  refine ⟨rfl, rfl, rfl⟩
-- @decl:match_spec-end
-- @ns:match_spec-end


theorem correct_resetIndexCoords :
    ∀ (c : ContainerNames) (resetNames : List String) (drop : Bool),
    problem_spec_resetIndexCoords c resetNames drop
      (implementation_resetIndexCoords c resetNames drop) := by
  intro c resetNames drop
  rw [reduce_impl]
  exact match_spec c resetNames drop
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. verifier `bash scripts/lean_verify.sh <file>`.

SPEC SHAPE: problem_spec_resetIndexCoords is FULLY FUNCTIONAL — it pins ALL THREE output collections to exact input-determined functions: indexNames'=removeAll c.indexNames resetNames, varNames'=removeAll c.varNames (drop?resetNames:[]), coordNames'=removeAll c.coordNames (drop?resetNames:[]). removeAll = order-preserving List.filter. The correct output is UNIQUE for every input, so any impl that closes correct_resetIndexCoords must be extensionally equal to the spec function; two verifying impls therefore have behaviorally identical refined patches. verify=>correct holds by construction — there is no room for a verify-but-wrong gap.

POSITIVE CONTROL: pos_control.lean (byte-identical bundle Solution.lean) -> lean_verify exit 0; `#print axioms correct_resetIndexCoords` = [propext, Quot.sound] (clean, no sorryAx).

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec, LeanBackend; only impl region edited, axioms/pure/pre/post byte-identical):
- atk_1 PREPATCH BUG (coordNames := c.coordNames, unsubtracted — the reported invariant violation): lean_verify exit 1, error 'unsolved goals' at the reduce_impl step (144:63). Prepatch bug reproduced: this wrong impl does NOT verify.
- atk_2 varNames unsubtracted (varNames := c.varNames): exit 1, unsolved goals.
- atk_3 indexNames unsubtracted (indexNames := c.indexNames): exit 1, unsolved goals.
- atk_4 control-flow effect (dropVariables built under !drop): exit 1, rewrite failed (163:6).
- atk_5 ungrounded-oracle echo (coordNames subtracted by resetNames ignoring drop): exit 1, unsolved goals.
- atk_6 partial-domain (only resetNames.take 1 processed): exit 1, rewrite failed (159:6).
- atk_7 structural swap (varNames/coordNames outputs swapped): exit 1, unsolved goals.

All 7 exits collected via concurrent background jobs (<=4 at a time). Every failure is genuine (unsolved goals / rewrite pattern-not-found), NONE is a sorry, NONE a timeout.

PROTOCOL STEP 2: the set of wrong impls whose proof CLOSES with clean axioms is EMPTY (no attack verified), so there is no faithful refined patch to materialize/run_resolve. Nothing to resolve; nothing breaks the spec.

REFINEMENT.MD LEG AUDIT: op1=I, op2=A-reference (get_all_coords(name)=={name} modeled deeply as literal [name]; ships NO opaque/axiom — confirmed by clean [propext,Quot.sound] axioms; correspondence validated by axiom_check.py 38,551 plain-index trials per verdict.md), ops3-6=R (mechanically covered by conformance_check.py, 120,004 trials, 0 disagreements). No A-consumed leg, no kind-3 leg. A-reference correspondence to the real callee holds.

VERDICT: SOUND — >=5 distinct same-spec wrong impls (7) all attempted; none produced a closing clean-axiom proof, hence no verify-but-non-resolving patch exists. The fully-functional spec admits only the correct behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-6992 lean bundle. Modeled function: NAME bookkeeping of Dataset.reset_index restricted to the declared domain of PLAIN single dimension indexes (get_all_coords(name)=={name}, non-PandasMultiIndex). 

### Verification performed
- Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry/admit).
- #print axioms correct_resetIndexCoords => [propext, Quot.sound] only. No sorryAx; proof is genuine, not fake.
- Spec region byte-identical with Solution_prepatch.lean per swebench_unified.markers.same_spec (lean backend) = True. Only the impl coordNames line differs pre/post (bug re-injection), spec unchanged.
- meta.json: patch_equals_gold=True, opaque_callees=[], axioms=[]; the one deep_model_reference (get_all_coords(name)=literal singleton) is validated by G-AX. All gates pass (G-PBT skip only).

FAITHFULNESS ANALYSIS vs REAL GOLD CALLEE (base_commit 45c0a114): The /tmp worktrees are at commit 1757dff (2019 xarray) and installed xarray is 0.15.1 — both far older than the modeled base_commit — so I analyzed against the gold patch text directly (the post-patch reset_index: drop_or_convert; drop_indexes|=get_all_coords(name); coord_names = self._coord_names - drop_variables; variables filtered by drop_variables then updated with new_variables which reuse same names via to_base_variable). In the plain-single-index domain this reduces exactly to: indexNames'=indexNames\resetNames, varNames'=varNames\dropVars, coordNames'=coordNames\dropVars where dropVars=resetNames if drop else {} — precisely the Lean problem_spec's removeAll clauses.

DIFFERENTIAL: transliterated the gold reset_index bookkeeping and ran 200,000 randomized in-domain inputs (varying dim coords, extra data vars, non-index coords, multi-target resets, both drop values) against the Lean spec semantics => 0 divergences. Also checked spec-too-strong edge cases: duplicate resetNames (idempotent both sides via set/seen), reset name absent from coordNames (no-op both), reset name absent from varNames (excluded by domain: a live dimension index coordinate is guaranteed present in _variables and _coord_names). No in-domain input where the modeled function disagrees with the real callee was found.

The domain restriction is honestly declared in mapping.md/refinement.md/meta.modeled_domain and mechanically enforced by conformance_check.py domain_ok (get_all_coords=={name} + reject PandasMultiIndex). The multi-index level-manipulation branch is legitimately out of scope. No drift, no spec-too-strong defect. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier or comment naming a patched repo symbol {reset_index, set_index, drop_or_convert, keep_levels}, no bug/fix narration). same_spec(Solution.lean, Solution_prepatch.lean)=True and impl+proof regions are elided in the spec view, so the discriminating logic is hidden. The spec view is fully abstracted to a name-collection domain (ContainerNames.varNames/coordNames/indexNames, removeAll, resetNames, drop) with no Python, dataset.py path, or gold mechanism (the old `set(new_variables) | self._coord_names` collapse) exposed. The postcondition `coordNames = removeAll c.coordNames dropVariables` and the `coordNames ⊆ varNames` invariant merely state the desired correct behavior, which is already implied by the PUBLIC problem_statement (DataVariables assumes _variables ⊇ _coord_names; the bug yields more _coord_names than _variables; MVCE reset_index('z', drop=True); ValueError __len__() should return >= 0). Nothing in the spec view leaks the gold edit beyond that public statement, and reconstruction is not made easier. hints_text is empty, so it is not a factor.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
