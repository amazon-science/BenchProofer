# P2 adversarial audit — django__django-11820

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None. No same-spec wrong impl produced a closing clean-axiom proof, so verify⇒correct held for every attack. Machine-checked semantic distinctness of the two prepatch bugs from the pinned reference `pathValid` (disproof.lean, exit 0, `by decide`): (atk_1, drop pk-alias) on graph {model0: getField only 'name'; primaryKey a non-relation field} and path ["pk"] — pathValid=true (pk resolves to primaryKey) vs impl1=false (getField "pk"=none, no field yet ⇒ invalid). (atk_2, drop non-relation termination) path ["name","name"] — pathValid=false (after resolving non-relation 'name' the walk ends, second 'name' hits none-branch, nameFld accepts no transform ⇒ invalid) vs impl2=true (keeps cur, re-resolves). Because the postcondition pins result = pathValid exactly (total, precondition-free, ∀-quantified), each wrong impl makes correct_lookupPathValid a FALSE proposition, unprovable without sorry/axioms.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,21 +102,17 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
   for part in parts do
     match cur with
     | some c =>
-        let resolved := if part == "pk" then some (models c).primaryKey
-                        else (models c).getField part
+        let resolved := (models c).getField part
         match resolved with
         | some f =>
             fld := some f
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,13 +102,10 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
@@ -122,8 +119,6 @@
             fld := some f
             if f.isRelation then
               cur := some f.target
-            else
-              cur := none
         | none =>
             match fld with
             | some pf => if !(pf.acceptsTransform part) then invalid := true
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,13 +102,10 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
@@ -126,11 +123,11 @@
               cur := none
         | none =>
             match fld with
-            | some pf => if !(pf.acceptsTransform part) then invalid := true
+            | some pf => if (pf.acceptsTransform part) then invalid := true
             | none => invalid := true
     | none =>
         match fld with
-        | some pf => if !(pf.acceptsTransform part) then invalid := true
+        | some pf => if (pf.acceptsTransform part) then invalid := true
         | none => invalid := true
   return !invalid
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,13 +102,10 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
@@ -124,14 +121,8 @@
               cur := some f.target
             else
               cur := none
-        | none =>
-            match fld with
-            | some pf => if !(pf.acceptsTransform part) then invalid := true
-            | none => invalid := true
-    | none =>
-        match fld with
-        | some pf => if !(pf.acceptsTransform part) then invalid := true
-        | none => invalid := true
+        | none => pure ()
+    | none => pure ()
   return !invalid
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,13 +102,10 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
@@ -127,11 +124,11 @@
         | none =>
             match fld with
             | some pf => if !(pf.acceptsTransform part) then invalid := true
-            | none => invalid := true
+            | none => pure ()
     | none =>
         match fld with
         | some pf => if !(pf.acceptsTransform part) then invalid := true
-        | none => invalid := true
+        | none => pure ()
   return !invalid
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,13 +102,10 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
@@ -121,7 +118,7 @@
         | some f =>
             fld := some f
             if f.isRelation then
-              cur := some f.target
+              cur := some c
             else
               cur := none
         | none =>
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,21 +102,18 @@
   result = pathValid models startModel parts
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_lookupPathValid
     (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
-  -- Walk the path one segment at a time from the start model, remembering the
-  -- last resolved field; a non-relation field ends the walk, the "pk" alias
-  -- resolves to the primary-key field, and an unresolved segment is tolerated
-  -- only if the last field accepts it as a transform.
   let mut cur : Option Nat := some startModel
   let mut fld : Option FieldInfo := none
   let mut invalid : Bool := false
   for part in parts do
     match cur with
     | some c =>
-        let resolved := if part == "pk" then some (models c).primaryKey
-                        else (models c).getField part
+        let resolved := if part == "pk" then (models c).getField part
+                        else some (models c).primaryKey
         match resolved with
         | some f =>
             fld := some f
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a dotted field-lookup path is valid for a model in a model
graph.

A model graph is a collection of models indexed by natural numbers. Each model
exposes, by name, the fields declared on it; a field is either a *relation*
(it points at another model in the graph) or a plain value field. Every model
also has a distinguished *primary-key* field, reachable through the alias
`"pk"` (the alias is NOT one of the by-name declared fields — it is resolved
separately).

A lookup path is a list of name segments (the pieces of an `"a__b__c"` string).
Validity is decided by walking the path one segment at a time, starting at a
given model, while remembering the last field that was resolved:

  * To resolve a segment against the *current model*: the segment `"pk"`
    resolves to that model's primary-key field; any other segment resolves to
    the by-name field of that name, if one exists.
  * A resolved field that is a relation moves the walk onto the model it points
    at; a resolved field that is NOT a relation ends the walk — there is no
    current model for the remaining segments.
  * If a segment cannot be resolved (no current model, or the name is not a
    declared field of the current model), the path is acceptable at that
    segment ONLY when the most recently resolved field accepts the segment as a
    registered transform/lookup; otherwise the whole path is invalid. If no
    field has been resolved yet, the path is invalid.

The path is valid exactly when no segment makes it invalid.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The model graph is
-- supplied as data: each model's by-name field resolution, its primary-key
-- field, and per-field relation target / transform admissibility are carried by
-- `ModelInfo` / `FieldInfo` values. The behavior under spec is solely WHICH
-- paths are valid given that data, so the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
/-- A field declared on a model. `isRelation` says whether following it moves
the walk onto another model (`target`, an index into the model graph). For a
non-relation field these are irrelevant. `acceptsTransform name` says whether the
field accepts `name` as a registered transform/lookup (so a segment that is not
a declared field may still be acceptable). -/
structure FieldInfo where
  isRelation : Bool
  target : Nat
  acceptsTransform : String → Bool

/-- A model in the graph. `getField name` is the by-name field of that name, if
declared (`none` otherwise); the `"pk"` alias is NOT covered by `getField` and
is resolved through `primaryKey`. -/
structure ModelInfo where
  getField : String → Option FieldInfo
  primaryKey : FieldInfo

/-- Walk state: the current model (`none` once the walk has ended), the most
recently resolved field (`none` until one is resolved), and whether the path has
already been found invalid. -/
abbrev WalkState := Option Nat × Option FieldInfo × Bool

/-- Process one path segment. `fld` is the last resolved field; on a resolution
failure the segment is tolerated only when that field accepts it as a transform. -/
def stepPath (models : Nat → ModelInfo) (st : WalkState) (part : String) : WalkState :=
  let (cur, fld, invalid) := st
  match cur with
  | some c =>
      let resolved := if part == "pk" then some (models c).primaryKey
                      else (models c).getField part
      match resolved with
      | some f =>
          (if f.isRelation then some f.target else none, some f, invalid)
      | none =>
          let bad := match fld with
                     | some pf => !pf.acceptsTransform part
                     | none => true
          (cur, fld, invalid || bad)
  | none =>
      let bad := match fld with
                 | some pf => !pf.acceptsTransform part
                 | none => true
      (none, fld, invalid || bad)

/-- Validity of a whole path: fold the segments through `stepPath` from the
start model and report that no segment invalidated the path. -/
def pathValid (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool :=
  let (_, _, invalid) := parts.foldl (stepPath models) (some startModel, none, false)
  !invalid
-- pure-end

-- post-conditions-start
/-- The decision is fully pinned to the model graph, the start model, and the
path segments: the result is `true` exactly when walking the path leaves it
valid (no segment invalidates it). No output is left free. -/
def problem_spec_lookupPathValid
    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String)
    (result : Bool) : Prop :=
  result = pathValid models startModel parts
-- post-conditions-end

-- impl-start
def implementation_lookupPathValid
    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
  -- Walk the path one segment at a time from the start model, remembering the
  -- last resolved field; a non-relation field ends the walk, the "pk" alias
  -- resolves to the primary-key field, and an unresolved segment is tolerated
  -- only if the last field accepts it as a transform.
  let mut cur : Option Nat := some startModel
  let mut fld : Option FieldInfo := none
  let mut invalid : Bool := false
  for part in parts do
    match cur with
    | some c =>
        let resolved := if part == "pk" then some (models c).primaryKey
                        else (models c).getField part
        match resolved with
        | some f =>
            fld := some f
            if f.isRelation then
              cur := some f.target
            else
              cur := none
        | none =>
            match fld with
            | some pf => if !(pf.acceptsTransform part) then invalid := true
            | none => invalid := true
    | none =>
        match fld with
        | some pf => if !(pf.acceptsTransform part) then invalid := true
        | none => invalid := true
  return !invalid
-- impl-end


-- proof-start
/-- The pure `WalkState → String → WalkState` transformer obtained by reading
the `for`-loop body of `implementation_lookupPathValid` as a single state update
on the tuple `(cur, fld, invalid)`. Extensionally the same recursion as
`stepPath`; the difference is only the surface `if _ then true else invalid`
vs. `invalid || bad` shape, discharged by `loopBody_eq_stepPath`. -/
def loopBody (models : Nat → ModelInfo) (st : WalkState) (part : String) : WalkState :=
  let (cur, fld, invalid) := st
  match cur with
  | some c =>
      let resolved := if part == "pk" then some (models c).primaryKey
                      else (models c).getField part
      match resolved with
      | some f =>
          (if f.isRelation then some f.target else none, some f, invalid)
      | none =>
          match fld with
          | some pf => (cur, fld, if !(pf.acceptsTransform part) then true else invalid)
          | none => (cur, fld, true)
  | none =>
      match fld with
      | some pf => (cur, fld, if !(pf.acceptsTransform part) then true else invalid)
      | none => (cur, fld, true)

/-- The `for`-loop of `implementation_lookupPathValid` run from an ARBITRARY
initial walk-state `st` (rather than the fixed `(some startModel, none, false)`).
Abstracting the start state is exactly what lets the fold-equivalence be proved
by a straightforward induction on `parts`; the fixed-start impl is the `st =
(some startModel, none, false)` instance (`impl_eq_implLoop`). -/
def implLoop (models : Nat → ModelInfo) (parts : List String) (st : WalkState) : Bool := Id.run do
  let mut cur : Option Nat := st.1
  let mut fld : Option FieldInfo := st.2.1
  let mut invalid : Bool := st.2.2
  for part in parts do
    match cur with
    | some c =>
        let resolved := if part == "pk" then some (models c).primaryKey
                        else (models c).getField part
        match resolved with
        | some f =>
            fld := some f
            if f.isRelation then cur := some f.target else cur := none
        | none =>
            match fld with
            | some pf => if !(pf.acceptsTransform part) then invalid := true
            | none => invalid := true
    | none =>
        match fld with
        | some pf => if !(pf.acceptsTransform part) then invalid := true
        | none => invalid := true
  return !invalid

/-- `implementation_lookupPathValid` is `implLoop` at the fixed start state.
Holds by `rfl` (the `for`-loop bodies are syntactically identical). -/
theorem impl_eq_implLoop (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) :
    implementation_lookupPathValid models startModel parts
      = implLoop models parts (some startModel, none, false) := by rfl

/-- One unfolding of `implLoop`: running the loop on `p :: ps` from `st` equals
running it on `ps` from `loopBody models st p`. This is the single-step bridge
between the imperative `for` body and the pure `loopBody`; prove it by casing on
`st` and reducing the (single) `forIn` step. -/
theorem implLoop_cons (models : Nat → ModelInfo) (p : String) (ps : List String) (st : WalkState) :
    implLoop models (p :: ps) st = implLoop models ps (loopBody models st p) := by
  obtain ⟨cur, fld, invalid⟩ := st
  simp only [implLoop, loopBody, List.forIn_cons]
  repeat' split
  all_goals rfl

/-- `implLoop` computes exactly the negated `invalid` flag of the `loopBody`
fold. Prove by induction on `parts` (generalizing `st`): `nil` is `rfl`, `cons`
is `implLoop_cons` + `List.foldl_cons` + the IH. -/
theorem implLoop_eq_foldl (models : Nat → ModelInfo) (parts : List String) (st : WalkState) :
    implLoop models parts st = !((parts.foldl (loopBody models) st).2.2) := by
  induction parts generalizing st with
  | nil => rfl
  | cons p ps ih =>
      rw [implLoop_cons, List.foldl_cons, ih]

theorem impl_as_foldl (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) :
    implementation_lookupPathValid models startModel parts
      = !((parts.foldl (loopBody models) (some startModel, none, false)).2.2) := by
  rw [impl_eq_implLoop, implLoop_eq_foldl]

theorem loopBody_eq_stepPath (models : Nat → ModelInfo) (st : WalkState) (part : String) :
    loopBody models st part = stepPath models st part := by
  obtain ⟨cur, fld, invalid⟩ := st
  simp only [loopBody, stepPath]
  cases cur <;> cases fld <;> split <;> simp_all [Bool.or_comm]

theorem correct_lookupPathValid :
    ∀ (models : Nat → ModelInfo) (startModel : Nat) (parts : List String),
      problem_spec_lookupPathValid models startModel parts
        (implementation_lookupPathValid models startModel parts) := by
  intro models startModel parts
  unfold problem_spec_lookupPathValid
  rw [impl_as_foldl models startModel parts]
  have hfun : loopBody models = stepPath models := by
    funext st part
    exact loopBody_eq_stepPath models st part
  rw [hfun]
  simp only [pathValid]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: reference-implementation postcondition `problem_spec_lookupPathValid ... result := result = pathValid models startModel parts`. Total function, no preconditions, no dead inputs, universally quantified over (models, startModel, parts). This is the tightest possible spec: any verifying impl must be extensionally equal to `pathValid` on ALL inputs. spec_view elides BOTH impl and proof regions, so an attacker may supply any proof, but a wrong impl yields a false theorem — Lean soundness forbids a clean closing proof.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec on lean backend (impl region is the only edit; axioms/pure/pre/post byte-identical).

### ATTACKS (all edited impl region only; each carries the full gold proof body as a best-effort closing attempt):
- atk_1 (PREPATCH BUG #1, matches Solution_prepatch.lean): drops the pk-alias branch, always uses getField. command: `bash scripts/lean_verify.sh atk_1.lean` -> exit 1 (rfl fails at proof; theorem is false, counterexample above).
- atk_2 (PREPATCH BUG #2, matches Solution_prepatch_2.lean): drops the `else cur := none` non-relation termination. exit 1.
- atk_3 (control-flow-effect): negates transform tolerance (`if pf.acceptsTransform part then invalid`). exit 1.
- atk_4 (partial-domain/trivial): tolerates every unresolved segment (both none-branches -> pure ()), ~constant-accepting. exit 1.
- atk_5 (boundary): drops the `fld = none ⇒ invalid` rule (leading unresolved segment tolerated). exit 1.
- atk_6 (control-flow-effect): relation advances to `some c` (self) instead of `f.target` (ungrounded target). exit 1.
- atk_7 (boundary/echo): swaps pk vs getField resolution ('pk' via getField, others via primaryKey). exit 1.

All 7 exit 1 on `rfl` at the proof step; positive control atk_pos exits 0. Two of them additionally machine-disproven semantically (disproof.lean).

POSITIVE CONTROL: atk_pos = exact gold Solution.lean. `lean_verify.sh atk_pos.lean` -> exit 0 (no sorry, no error). `#print axioms correct_lookupPathValid` -> `[propext, Quot.sound]` (clean standard Mathlib axioms, NO sorryAx).

RESOLVE RUNS: none required. Step-2 resolve is triggered only for a wrong impl whose proof CLOSES with clean axioms; zero attacks closed, so no faithful patch was materialized/run. verify⇒correct is not falsified.

REFINEMENT AUDIT: refinement.md has 14 legs, all R / A-reference / I; no kind-3 (changed-inexpressible) op. No A-consumed axiom (consistent with proof axioms = propext/Quot.sound only; axiom_check.py is a legitimate skip stub). Three A-reference legs (#7 opts.get_field, #9 get_path_info target, #12 get_transform) bind to the real Django callees; conformance_check.py (G-CONF, seed 11820) differential-tests the Python shadow of the walk vs the REAL patched Model._check_ordering E015 decision over 120k fuzzed model-graph/path inputs (register_lookup(CharField, Lower) for the transform branch). The two gold-fixed behaviors (pk alias op#6, non-relation termination op#10) are correctly modeled concretely as I, not A. Correspondence holds.

CONCLUSION: SOUND. The reference-impl spec is exactly as strong as the intended behavior; the two real prepatch bugs and 5 further distinct wrong impls are all rejected (proof cannot close), while the gold impl verifies with clean axioms.

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
None. No same-spec wrong impl produced a closing clean-axiom proof, so verify⇒correct held for every attack. Machine-checked semantic distinctness of the two prepatch bugs from the pinned reference `pathValid` (disproof.lean, exit 0, `by decide`): (atk_1, drop pk-alias) on graph {model0: getField only 'name'; primaryKey a non-relation field} and path ["pk"] — pathValid=true (pk resolves to primaryKey) vs impl1=false (getField "pk"=none, no field yet ⇒ invalid). (atk_2, drop non-relation termination) path ["name","name"] — pathValid=false (after resolving non-relation 'name' the walk ends, second 'name' hits none-branch, nameFld accepts no transform ⇒ invalid) vs impl2=true (keeps cur, re-resolves). Because the postcondition pins result = pathValid exactly (total, precondition-free, ∀-quantified), each wrong impl makes correct_lookupPathValid a FALSE proposition, unprovable without sorry/axioms.
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
import Mathlib
-- imports-end

/-!
Deciding whether a dotted field-lookup path is valid for a model in a model
graph.

A model graph is a collection of models indexed by natural numbers. Each model
exposes, by name, the fields declared on it; a field is either a *relation*
(it points at another model in the graph) or a plain value field. Every model
also has a distinguished *primary-key* field, reachable through the alias
`"pk"` (the alias is NOT one of the by-name declared fields — it is resolved
separately).

A lookup path is a list of name segments (the pieces of an `"a__b__c"` string).
Validity is decided by walking the path one segment at a time, starting at a
given model, while remembering the last field that was resolved:

  * To resolve a segment against the *current model*: the segment `"pk"`
    resolves to that model's primary-key field; any other segment resolves to
    the by-name field of that name, if one exists.
  * A resolved field that is a relation moves the walk onto the model it points
    at; a resolved field that is NOT a relation ends the walk — there is no
    current model for the remaining segments.
  * If a segment cannot be resolved (no current model, or the name is not a
    declared field of the current model), the path is acceptable at that
    segment ONLY when the most recently resolved field accepts the segment as a
    registered transform/lookup; otherwise the whole path is invalid. If no
    field has been resolved yet, the path is invalid.

The path is valid exactly when no segment makes it invalid.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The model graph is
-- supplied as data: each model's by-name field resolution, its primary-key
-- field, and per-field relation target / transform admissibility are carried by
-- `ModelInfo` / `FieldInfo` values. The behavior under spec is solely WHICH
-- paths are valid given that data, so the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
/-- A field declared on a model. `isRelation` says whether following it moves
the walk onto another model (`target`, an index into the model graph). For a
non-relation field these are irrelevant. `acceptsTransform name` says whether the
field accepts `name` as a registered transform/lookup (so a segment that is not
a declared field may still be acceptable). -/
structure FieldInfo where
  isRelation : Bool
  target : Nat
  acceptsTransform : String → Bool

/-- A model in the graph. `getField name` is the by-name field of that name, if
declared (`none` otherwise); the `"pk"` alias is NOT covered by `getField` and
is resolved through `primaryKey`. -/
structure ModelInfo where
  getField : String → Option FieldInfo
  primaryKey : FieldInfo

/-- Walk state: the current model (`none` once the walk has ended), the most
recently resolved field (`none` until one is resolved), and whether the path has
already been found invalid. -/
abbrev WalkState := Option Nat × Option FieldInfo × Bool

/-- Process one path segment. `fld` is the last resolved field; on a resolution
failure the segment is tolerated only when that field accepts it as a transform. -/
def stepPath (models : Nat → ModelInfo) (st : WalkState) (part : String) : WalkState :=
  let (cur, fld, invalid) := st
  match cur with
  | some c =>
      let resolved := if part == "pk" then some (models c).primaryKey
                      else (models c).getField part
      match resolved with
      | some f =>
          (if f.isRelation then some f.target else none, some f, invalid)
      | none =>
          let bad := match fld with
                     | some pf => !pf.acceptsTransform part
                     | none => true
          (cur, fld, invalid || bad)
  | none =>
      let bad := match fld with
                 | some pf => !pf.acceptsTransform part
                 | none => true
      (none, fld, invalid || bad)

/-- Validity of a whole path: fold the segments through `stepPath` from the
start model and report that no segment invalidated the path. -/
def pathValid (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool :=
  let (_, _, invalid) := parts.foldl (stepPath models) (some startModel, none, false)
  !invalid
-- pure-end

-- post-conditions-start
/-- The decision is fully pinned to the model graph, the start model, and the
path segments: the result is `true` exactly when walking the path leaves it
valid (no segment invalidates it). No output is left free. -/
def problem_spec_lookupPathValid
    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String)
    (result : Bool) : Prop :=
  result = pathValid models startModel parts
-- post-conditions-end

-- impl-start
def implementation_lookupPathValid
    (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) : Bool := Id.run do
  -- Walk the path one segment at a time from the start model, remembering the
  -- last resolved field; a non-relation field ends the walk, the "pk" alias
  -- resolves to the primary-key field, and an unresolved segment is tolerated
  -- only if the last field accepts it as a transform.
  let mut cur : Option Nat := some startModel
  let mut fld : Option FieldInfo := none
  let mut invalid : Bool := false
  for part in parts do
    match cur with
    | some c =>
        let resolved := if part == "pk" then some (models c).primaryKey
                        else (models c).getField part
        match resolved with
        | some f =>
            fld := some f
            if f.isRelation then
              cur := some f.target
            else
              cur := none
        | none =>
            match fld with
            | some pf => if !(pf.acceptsTransform part) then invalid := true
            | none => invalid := true
    | none =>
        match fld with
        | some pf => if !(pf.acceptsTransform part) then invalid := true
        | none => invalid := true
  return !invalid
-- impl-end


-- proof-start
/-- The pure `WalkState → String → WalkState` transformer obtained by reading
the `for`-loop body of `implementation_lookupPathValid` as a single state update
on the tuple `(cur, fld, invalid)`. Extensionally the same recursion as
`stepPath`; the difference is only the surface `if _ then true else invalid`
vs. `invalid || bad` shape, discharged by `loopBody_eq_stepPath`. -/
def loopBody (models : Nat → ModelInfo) (st : WalkState) (part : String) : WalkState :=
  let (cur, fld, invalid) := st
  match cur with
  | some c =>
      let resolved := if part == "pk" then some (models c).primaryKey
                      else (models c).getField part
      match resolved with
      | some f =>
          (if f.isRelation then some f.target else none, some f, invalid)
      | none =>
          match fld with
          | some pf => (cur, fld, if !(pf.acceptsTransform part) then true else invalid)
          | none => (cur, fld, true)
  | none =>
      match fld with
      | some pf => (cur, fld, if !(pf.acceptsTransform part) then true else invalid)
      | none => (cur, fld, true)

/-- The `for`-loop of `implementation_lookupPathValid` run from an ARBITRARY
initial walk-state `st` (rather than the fixed `(some startModel, none, false)`).
Abstracting the start state is exactly what lets the fold-equivalence be proved
by a straightforward induction on `parts`; the fixed-start impl is the `st =
(some startModel, none, false)` instance (`impl_eq_implLoop`). -/
def implLoop (models : Nat → ModelInfo) (parts : List String) (st : WalkState) : Bool := Id.run do
  let mut cur : Option Nat := st.1
  let mut fld : Option FieldInfo := st.2.1
  let mut invalid : Bool := st.2.2
  for part in parts do
    match cur with
    | some c =>
        let resolved := if part == "pk" then some (models c).primaryKey
                        else (models c).getField part
        match resolved with
        | some f =>
            fld := some f
            if f.isRelation then cur := some f.target else cur := none
        | none =>
            match fld with
            | some pf => if !(pf.acceptsTransform part) then invalid := true
            | none => invalid := true
    | none =>
        match fld with
        | some pf => if !(pf.acceptsTransform part) then invalid := true
        | none => invalid := true
  return !invalid

/-- `implementation_lookupPathValid` is `implLoop` at the fixed start state.
Holds by `rfl` (the `for`-loop bodies are syntactically identical). -/
theorem impl_eq_implLoop (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) :
    implementation_lookupPathValid models startModel parts
      = implLoop models parts (some startModel, none, false) := by rfl

/-- One unfolding of `implLoop`: running the loop on `p :: ps` from `st` equals
running it on `ps` from `loopBody models st p`. This is the single-step bridge
between the imperative `for` body and the pure `loopBody`; prove it by casing on
`st` and reducing the (single) `forIn` step. -/
theorem implLoop_cons (models : Nat → ModelInfo) (p : String) (ps : List String) (st : WalkState) :
    implLoop models (p :: ps) st = implLoop models ps (loopBody models st p) := by
  obtain ⟨cur, fld, invalid⟩ := st
  simp only [implLoop, loopBody, List.forIn_cons]
  repeat' split
  all_goals rfl

/-- `implLoop` computes exactly the negated `invalid` flag of the `loopBody`
fold. Prove by induction on `parts` (generalizing `st`): `nil` is `rfl`, `cons`
is `implLoop_cons` + `List.foldl_cons` + the IH. -/
theorem implLoop_eq_foldl (models : Nat → ModelInfo) (parts : List String) (st : WalkState) :
    implLoop models parts st = !((parts.foldl (loopBody models) st).2.2) := by
  induction parts generalizing st with
  | nil => rfl
  | cons p ps ih =>
      rw [implLoop_cons, List.foldl_cons, ih]

theorem impl_as_foldl (models : Nat → ModelInfo) (startModel : Nat) (parts : List String) :
    implementation_lookupPathValid models startModel parts
      = !((parts.foldl (loopBody models) (some startModel, none, false)).2.2) := by
  rw [impl_eq_implLoop, implLoop_eq_foldl]

theorem loopBody_eq_stepPath (models : Nat → ModelInfo) (st : WalkState) (part : String) :
    loopBody models st part = stepPath models st part := by
  obtain ⟨cur, fld, invalid⟩ := st
  simp only [loopBody, stepPath]
  cases cur <;> cases fld <;> split <;> simp_all [Bool.or_comm]

theorem correct_lookupPathValid :
    ∀ (models : Nat → ModelInfo) (startModel : Nat) (parts : List String),
      problem_spec_lookupPathValid models startModel parts
        (implementation_lookupPathValid models startModel parts) := by
  intro models startModel parts
  unfold problem_spec_lookupPathValid
  rw [impl_as_foldl models startModel parts]
  have hfun : loopBody models = stepPath models := by
    funext st part
    exact loopBody_eq_stepPath models st part
  rw [hfun]
  simp only [pathValid]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: reference-implementation postcondition `problem_spec_lookupPathValid ... result := result = pathValid models startModel parts`. Total function, no preconditions, no dead inputs, universally quantified over (models, startModel, parts). This is the tightest possible spec: any verifying impl must be extensionally equal to `pathValid` on ALL inputs. spec_view elides BOTH impl and proof regions, so an attacker may supply any proof, but a wrong impl yields a false theorem — Lean soundness forbids a clean closing proof.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec on lean backend (impl region is the only edit; axioms/pure/pre/post byte-identical).

### ATTACKS (all edited impl region only; each carries the full gold proof body as a best-effort closing attempt):
- atk_1 (PREPATCH BUG #1, matches Solution_prepatch.lean): drops the pk-alias branch, always uses getField. command: `bash scripts/lean_verify.sh atk_1.lean` -> exit 1 (rfl fails at proof; theorem is false, counterexample above).
- atk_2 (PREPATCH BUG #2, matches Solution_prepatch_2.lean): drops the `else cur := none` non-relation termination. exit 1.
- atk_3 (control-flow-effect): negates transform tolerance (`if pf.acceptsTransform part then invalid`). exit 1.
- atk_4 (partial-domain/trivial): tolerates every unresolved segment (both none-branches -> pure ()), ~constant-accepting. exit 1.
- atk_5 (boundary): drops the `fld = none ⇒ invalid` rule (leading unresolved segment tolerated). exit 1.
- atk_6 (control-flow-effect): relation advances to `some c` (self) instead of `f.target` (ungrounded target). exit 1.
- atk_7 (boundary/echo): swaps pk vs getField resolution ('pk' via getField, others via primaryKey). exit 1.

All 7 exit 1 on `rfl` at the proof step; positive control atk_pos exits 0. Two of them additionally machine-disproven semantically (disproof.lean).

POSITIVE CONTROL: atk_pos = exact gold Solution.lean. `lean_verify.sh atk_pos.lean` -> exit 0 (no sorry, no error). `#print axioms correct_lookupPathValid` -> `[propext, Quot.sound]` (clean standard Mathlib axioms, NO sorryAx).

RESOLVE RUNS: none required. Step-2 resolve is triggered only for a wrong impl whose proof CLOSES with clean axioms; zero attacks closed, so no faithful patch was materialized/run. verify⇒correct is not falsified.

REFINEMENT AUDIT: refinement.md has 14 legs, all R / A-reference / I; no kind-3 (changed-inexpressible) op. No A-consumed axiom (consistent with proof axioms = propext/Quot.sound only; axiom_check.py is a legitimate skip stub). Three A-reference legs (#7 opts.get_field, #9 get_path_info target, #12 get_transform) bind to the real Django callees; conformance_check.py (G-CONF, seed 11820) differential-tests the Python shadow of the walk vs the REAL patched Model._check_ordering E015 decision over 120k fuzzed model-graph/path inputs (register_lookup(CharField, Lower) for the transform branch). The two gold-fixed behaviors (pk alias op#6, non-relation termination op#10) are correctly modeled concretely as I, not A. Correspondence holds.

CONCLUSION: SOUND. The reference-impl spec is exactly as strong as the intended behavior; the two real prepatch bugs and 5 further distinct wrong impls are all rejected (proof cannot close), while the gold impl verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No spec drift found; the modeled function agrees with the real callee.

Evidence:
- Lean verifies (lean_verify.sh exit 0) and #print axioms correct_lookupPathValid = [propext, Quot.sound] only — no sorryAx, proof is real.
- Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean) and (Solution_prepatch_2.lean) both True under LeanBackend.language tables.
- patch.diff matches the applied gold at base_commit c2678e49: the pk-alias branch (if part=='pk': fld=_cls._meta.pk) and the non-relation termination (else: _cls=None).
- Semantic branch-by-branch trace: pk-alias always resolves at a valid model; relation advances (cur:=some target), non-relation ends walk (cur:=none); unresolved segment tolerated iff last field accepts it as a transform, invalid if no field resolved yet; on resolution failure _cls/cur is left UNCHANGED in both Python and Lean; cur=None + part=='pk' is treated identically to any name (Python: _cls._meta raises AttributeError before the pk check; Lean: none-branch checks acceptsTransform). All match, including Python short-circuit `fld is None or fld.get_transform(part) is None`.
- Ran the conformance shadow (op-for-op transliteration of implementation_lookupPathValid) against the REAL patched _check_ordering over 120000 fuzzed (start-model, lookup-path) inputs on a rich model graph (FKs, self-FK, value fields, pk alias, registered Lower transform, bogus names, 'pk' as a transform-name-when-cur=None case): 0 disagreements, status=pass.

Boundary note (not a defect): FieldInfo.target is a total Nat so a relation always advances; the fuzzer's finite 3-model graph never has a relation leave the graph, and this is a modeling boundary of the parameterized graph data (A-reference), not a strengthening of the spec. The spec is if-and-only-if pinned to pathValid (result = pathValid ...), i.e. not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lean backend. Mechanical G-LEAK screen (leakage.screen over spec_view) passes: no hard failures, no warnings. Spec view (impl + proof regions elided to placeholders) contains NO diff markers, NO patched file path (base.py), NO patched repo symbols (_check_ordering, get_field, _meta, _cls, get_transform, get_path_info, FieldDoesNotExist, E015), NO fix-narration tokens (bug/fix/buggy/patch/regression/440505). Impl comment 'buggy'/proof 'G-DIFF/UNCLOSABLE' narration is confined to elided impl/proof regions. same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True — spec regions are byte-identical across patched and both buggy variants, so the spec view is invariant to the gold edit and was not tailored to leak it. The spec docstring/stepPath DO specify correct semantics (pk-alias -> primaryKey; non-relation field ends the walk), but (a) that is the required function of a specification, not leakage; (b) pk-alias behavior is already public in problem_statement (option__pk); (c) both behaviors are expressed abstractly over a generic model-graph vocabulary (ModelInfo/FieldInfo/WalkState) with no repo-localizing anchor, gold-diff line, or edit narration. No line reveals the gold edit's localization or content beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
