# P2 adversarial audit — pydata__xarray-3305

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a full functional equality on all three result fields — problem_spec_arrayQuantile pins result.dims=newDims ∧ result.data=qs ∧ result.attrs=(if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none), and problem_spec_collectionQuantile literally equates result to arrays.map(...). Any impl whose correct_* closes is forced to equal gold on every input. All 8 genuinely-wrong impls (atk_1-8) fail to close their proofs (exit 1, rfl/type-mismatch failures — genuine, not syntax errors); the only closing wrong-impl is atk_9, a gold-equivalent echo, whose faithful patch (=gold patch) RESOLVES.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,7 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
-  return { dims := newDims, data := qs, attrs := attrs }
+  return { dims := newDims, data := qs, attrs := none }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,9 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
+  let attrs := match keepAttrs with
+    | some b => if b then some selfAttrs else none
+    | none   => none
   return { dims := newDims, data := qs, attrs := attrs }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,7 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
+  let attrs := if keepAttrs.getD globalDefault then none else some selfAttrs
   return { dims := newDims, data := qs, attrs := attrs }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,7 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
+  let attrs := if globalDefault then some selfAttrs else none
   return { dims := newDims, data := qs, attrs := attrs }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,12 +88,8 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
-  return { dims := newDims, data := qs, attrs := attrs }
+  let attrs := if keepAttrs.getD globalDefault then some selfAttrs else none
+  return { dims := [], data := qs, attrs := attrs }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,11 +88,7 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
+  let attrs := if keepAttrs.getD globalDefault then some (selfAttrs ++ selfAttrs) else none
   return { dims := newDims, data := qs, attrs := attrs }
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -139,8 +139,7 @@
     (globalDefault : Bool) : List QResult := Id.run do
   let mut out : Array QResult := #[]
   for a in arrays do
-    -- forward the SAME keep request to each member array's reduction
-    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
+    let r := implementation_arrayQuantile a.dims a.qs a.attrs none globalDefault
     out := out.push r
   return out.toList
 -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -139,10 +139,9 @@
     (globalDefault : Bool) : List QResult := Id.run do
   let mut out : Array QResult := #[]
   for a in arrays do
-    -- forward the SAME keep request to each member array's reduction
     let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
     out := out.push r
-  return out.toList
+  return out.toList.reverse
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -88,12 +88,8 @@
 def implementation_arrayQuantile
     (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
     (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
-  -- default the keep request from the supplied default flag when unspecified
-  let mut keep := keepAttrs
-  if keep.isNone then
-    keep := some globalDefault
-  let attrs := if keep.getD globalDefault then some selfAttrs else none
-  return { dims := newDims, data := qs, attrs := attrs }
+  return { dims := newDims, data := qs,
+           attrs := if keepAttrs.getD globalDefault then some selfAttrs else none }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing a quantile reduction of a labelled numeric array, with optional
preservation of the array's metadata attributes.

A source array carries:
  * a set of metadata attributes (`selfAttrs`) — key/value string pairs;
  * the value data and the dimension labels that survive the reduction.

The quantile reduction itself (the remaining dimension labels `newDims` and the
computed quantile value array `qs`) is supplied as input — it is independent of
the metadata question.  The behavior modeled here is the metadata contract:

  * an `attrs`-keeping request is either explicit (`some true` / `some false`) or
    unspecified (`none`);
  * when unspecified, it falls back to a caller-supplied default flag;
  * the result keeps the source attributes exactly when the resolved request is
    true, and otherwise carries no attributes;
  * the result's dimension labels and value data are exactly the supplied
    reduction (unchanged by the metadata choice).

A collection-level reduction applies the same reduction to each member array,
forwarding the SAME keep request to every member, so each member's attributes
are kept or dropped according to that one shared request.

Stated as input→output relations; the implementations and their correctness
proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract. The quantile
-- reduction (the remaining dimension labels and the computed value array) and
-- the resolved global default flag are taken as modeled inputs (`newDims`, `qs`,
-- `globalDefault`); they are unchanged by this behavior and exercised end-to-end
-- by the differential check. There is therefore no `axiom <callee>_prop` for the
-- proofs to consume.

/-- A metadata attribute mapping, abstracted to the only property observed here:
identity (equality). Modeled as its list of key/value string pairs. -/
abbrev Attrs := List (String × String)

/-- The result of a quantile reduction:
* `dims`  — the dimension labels that remain after the reduction;
* `data`  — the computed quantile value array (modeled as integer values);
* `attrs` — the kept metadata attributes, or none when not kept. -/
structure QResult where
  dims : List String
  data : List Int
  attrs : Option Attrs
deriving DecidableEq, Repr

/-- A source array as seen by a collection-level reduction: its surviving
dimension labels, its computed quantile value array, and its metadata. -/
structure SrcArray where
  dims : List String
  qs : List Int
  attrs : Attrs
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Resolve an attribute-keeping request: an explicit choice when given,
otherwise the supplied default flag. -/
def resolveKeepAttrs (keepAttrs : Option Bool) (globalDefault : Bool) : Bool :=
  keepAttrs.getD globalDefault
-- pure-end

-- post-conditions-start
/-- The single-array quantile result as a function of the inputs:

* `dims` and `data` are exactly the supplied reduction (`newDims`, `qs`) — the
  metadata choice does not touch them;
* `attrs` is the source attributes when the resolved keep request is true, and
  none otherwise. -/
def problem_spec_arrayQuantile
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool)
    (result : QResult) : Prop :=
  result.dims = newDims ∧
  result.data = qs ∧
  result.attrs =
    (if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none)
-- post-conditions-end

-- impl-start
def implementation_arrayQuantile
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
  -- default the keep request from the supplied default flag when unspecified
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  let attrs := if keep.getD globalDefault then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }
-- impl-end

-- proof-start
/-- Closed form of the single-array implementation: the loop just resolves the
keep request, so the result is the supplied reduction with attributes kept iff
the resolved request is true.  Proved by case split on `keepAttrs`; each branch
is definitionally the spec's `if`. -/
theorem arrayQuantile_eq
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool) :
    implementation_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault =
      { dims := newDims, data := qs,
        attrs := if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none } := by
  cases keepAttrs <;> rfl

theorem correct_arrayQuantile :
    ∀ (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
      (keepAttrs : Option Bool) (globalDefault : Bool),
      problem_spec_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault
        (implementation_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault) := by
  intro newDims qs selfAttrs keepAttrs globalDefault
  unfold problem_spec_arrayQuantile
  rw [arrayQuantile_eq]
  exact ⟨rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- The collection-level quantile result: each member array is reduced with the
SAME keep request forwarded to every member.  So each member result has the
member's own surviving dims and value data, and keeps the member's attributes
exactly when the one shared resolved request is true. -/
def problem_spec_collectionQuantile
    (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool)
    (result : List QResult) : Prop :=
  result = arrays.map (fun a =>
    { dims := a.dims, data := a.qs,
      attrs := if resolveKeepAttrs keepAttrs globalDefault then some a.attrs else none })
-- post-conditions-end

-- impl-start
def implementation_collectionQuantile
    (arrays : List SrcArray) (keepAttrs : Option Bool)
    (globalDefault : Bool) : List QResult := Id.run do
  let mut out : Array QResult := #[]
  for a in arrays do
    -- forward the SAME keep request to each member array's reduction
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  return out.toList
-- impl-end

-- proof-start
/-- The accumulator loop (in its desugared `forIn` form, generalized over the
running accumulator) appends each member's single-array reduction.  Route B
induction on the list. -/
theorem collectionQuantile_forIn
    (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool)
    (init : Array QResult) :
    (forIn arrays init (fun a r => do
        pure PUnit.unit
        pure (ForInStep.yield
          (r.push (implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault))))
        : Id (Array QResult)).run.toList
    = init.toList ++ arrays.map (fun a =>
        { dims := a.dims, data := a.qs,
          attrs := if resolveKeepAttrs keepAttrs globalDefault then some a.attrs else none }) := by
  induction arrays generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih, arrayQuantile_eq, Array.toList_push]
    simp

theorem correct_collectionQuantile :
    ∀ (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool),
      problem_spec_collectionQuantile arrays keepAttrs globalDefault
        (implementation_collectionQuantile arrays keepAttrs globalDefault) := by
  intro arrays keepAttrs globalDefault
  unfold problem_spec_collectionQuantile implementation_collectionQuantile
  have h := collectionQuantile_forIn arrays keepAttrs globalDefault #[]
  simpa [Id.run] using h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

python env. same_spec=True confirmed for all 9 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical). Positive control (gold Solution.lean) verifies exit 0. Prepatch (Solution_prepatch.lean) reproduced buggy: exit 1, unsolved goals at 106/152.

### ATTACKS (each: /tmp path, cmd `bash scripts/lean_verify.sh <f>`, exit):
- atk_1 prepatch array bug (attrs always none): EXIT=1 (rfl failed L105) — does NOT close.
- atk_2 partial-domain (none-case forced to none): EXIT=1 — does NOT close.
- atk_3 boundary swap (some/none swapped): EXIT=1 (rfl failed L106) — does NOT close.
- atk_4 control-flow-effect (ignores keepAttrs, uses globalDefault only): EXIT=1 — does NOT close.
- atk_5 dims frame corruption (dims:=[]): EXIT=1 (rfl failed L106) — does NOT close.
- atk_6 attrs content corruption (selfAttrs++selfAttrs): EXIT=1 — does NOT close.
- atk_7 collection non-forwarding (prepatch bug, passes none): EXIT=1 (type mismatch L177) — does NOT close.
- atk_8 collection reorder (.reverse): EXIT=1 (type mismatch L177) — does NOT close.
- atk_9 ECHO gold-equivalent (attrs := if keepAttrs.getD globalDefault then some selfAttrs else none): EXIT=0, VERIFIES. #print axioms: correct_arrayQuantile depends on NO axioms; correct_collectionQuantile depends on [propext, Quot.sound] — clean, no sorryAx/custom.

MANDATORY RESOLVE for the closing clean-axiom impl (atk_9): materialized faithful patch = gold patch (atk_9 is behaviorally identical to gold: keepAttrs.getD globalDefault equals gold's default-then-getD). Ran run_resolve('pydata__xarray-3305', patch, timeout=1800, retries=2) via official harness → RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note='resolved'. (First attempt hit a transient docker list_images ImageNotFound race from concurrent audit containers; retry succeeded and was executed, not speculated.) So the one impl with a closing clean-axiom proof RESOLVES — verify⇒correct holds.

REFINEMENT.MD AUDIT: 6 legs, all tagged R (type refinement). Zero A-consumed, zero A-reference, zero kind-3 (changed-inexpressible) — the entire fix (keep-attrs defaulting op1, attr selection op2, result construction op3, per-variable loop op4, flag-forwarding op5, collection output op6) is modeled deeply over Attrs/QResult. Consistent with axiom_check.py (G-AX status=skip, no axiom <callee>_prop declared) and Solution.lean axioms region (no axiom). The A-leg correspondence concern is vacuous (all-R bundle); no false real-callee correspondence possible. dims/data frame-pinned to modeled inputs newDims/qs (unchanged nanpercentile+dim-removal reduction), correctly not axiomatized.

CONCLUSION: The spec is a full functional equality with no wiggle room (no ∃, no inequality, no unconstrained field). Every closing impl is forced to gold observables. Attempted 8 distinct genuinely-wrong impls across partial-domain/boundary/control-flow-effect/frame/content/ordering families + the prepatch bug; none closes. Only the gold echo closes and it resolves. No verify⇏correct gap exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a full functional equality on all three result fields — problem_spec_arrayQuantile pins result.dims=newDims ∧ result.data=qs ∧ result.attrs=(if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none), and problem_spec_collectionQuantile literally equates result to arrays.map(...). Any impl whose correct_* closes is forced to equal gold on every input. All 8 genuinely-wrong impls (atk_1-8) fail to close their proofs (exit 1, rfl/type-mismatch failures — genuine, not syntax errors); the only closing wrong-impl is atk_9, a gold-equivalent echo, whose faithful patch (=gold patch) RESOLVES.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing a quantile reduction of a labelled numeric array, with optional
preservation of the array's metadata attributes.

A source array carries:
  * a set of metadata attributes (`selfAttrs`) — key/value string pairs;
  * the value data and the dimension labels that survive the reduction.

The quantile reduction itself (the remaining dimension labels `newDims` and the
computed quantile value array `qs`) is supplied as input — it is independent of
the metadata question.  The behavior modeled here is the metadata contract:

  * an `attrs`-keeping request is either explicit (`some true` / `some false`) or
    unspecified (`none`);
  * when unspecified, it falls back to a caller-supplied default flag;
  * the result keeps the source attributes exactly when the resolved request is
    true, and otherwise carries no attributes;
  * the result's dimension labels and value data are exactly the supplied
    reduction (unchanged by the metadata choice).

A collection-level reduction applies the same reduction to each member array,
forwarding the SAME keep request to every member, so each member's attributes
are kept or dropped according to that one shared request.

Stated as input→output relations; the implementations and their correctness
proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract. The quantile
-- reduction (the remaining dimension labels and the computed value array) and
-- the resolved global default flag are taken as modeled inputs (`newDims`, `qs`,
-- `globalDefault`); they are unchanged by this behavior and exercised end-to-end
-- by the differential check. There is therefore no `axiom <callee>_prop` for the
-- proofs to consume.

/-- A metadata attribute mapping, abstracted to the only property observed here:
identity (equality). Modeled as its list of key/value string pairs. -/
abbrev Attrs := List (String × String)

/-- The result of a quantile reduction:
* `dims`  — the dimension labels that remain after the reduction;
* `data`  — the computed quantile value array (modeled as integer values);
* `attrs` — the kept metadata attributes, or none when not kept. -/
structure QResult where
  dims : List String
  data : List Int
  attrs : Option Attrs
deriving DecidableEq, Repr

/-- A source array as seen by a collection-level reduction: its surviving
dimension labels, its computed quantile value array, and its metadata. -/
structure SrcArray where
  dims : List String
  qs : List Int
  attrs : Attrs
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Resolve an attribute-keeping request: an explicit choice when given,
otherwise the supplied default flag. -/
def resolveKeepAttrs (keepAttrs : Option Bool) (globalDefault : Bool) : Bool :=
  keepAttrs.getD globalDefault
-- pure-end

-- post-conditions-start
/-- The single-array quantile result as a function of the inputs:

* `dims` and `data` are exactly the supplied reduction (`newDims`, `qs`) — the
  metadata choice does not touch them;
* `attrs` is the source attributes when the resolved keep request is true, and
  none otherwise. -/
def problem_spec_arrayQuantile
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool)
    (result : QResult) : Prop :=
  result.dims = newDims ∧
  result.data = qs ∧
  result.attrs =
    (if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none)
-- post-conditions-end

-- impl-start
def implementation_arrayQuantile
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
  -- default the keep request from the supplied default flag when unspecified
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  let attrs := if keep.getD globalDefault then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }
-- impl-end

-- proof-start
/-- Closed form of the single-array implementation: the loop just resolves the
keep request, so the result is the supplied reduction with attributes kept iff
the resolved request is true.  Proved by case split on `keepAttrs`; each branch
is definitionally the spec's `if`. -/
theorem arrayQuantile_eq
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool) :
    implementation_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault =
      { dims := newDims, data := qs,
        attrs := if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none } := by
  cases keepAttrs <;> rfl

theorem correct_arrayQuantile :
    ∀ (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
      (keepAttrs : Option Bool) (globalDefault : Bool),
      problem_spec_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault
        (implementation_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault) := by
  intro newDims qs selfAttrs keepAttrs globalDefault
  unfold problem_spec_arrayQuantile
  rw [arrayQuantile_eq]
  exact ⟨rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- The collection-level quantile result: each member array is reduced with the
SAME keep request forwarded to every member.  So each member result has the
member's own surviving dims and value data, and keeps the member's attributes
exactly when the one shared resolved request is true. -/
def problem_spec_collectionQuantile
    (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool)
    (result : List QResult) : Prop :=
  result = arrays.map (fun a =>
    { dims := a.dims, data := a.qs,
      attrs := if resolveKeepAttrs keepAttrs globalDefault then some a.attrs else none })
-- post-conditions-end

-- impl-start
def implementation_collectionQuantile
    (arrays : List SrcArray) (keepAttrs : Option Bool)
    (globalDefault : Bool) : List QResult := Id.run do
  let mut out : Array QResult := #[]
  for a in arrays do
    -- forward the SAME keep request to each member array's reduction
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  return out.toList
-- impl-end

-- proof-start
/-- The accumulator loop (in its desugared `forIn` form, generalized over the
running accumulator) appends each member's single-array reduction.  Route B
induction on the list. -/
theorem collectionQuantile_forIn
    (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool)
    (init : Array QResult) :
    (forIn arrays init (fun a r => do
        pure PUnit.unit
        pure (ForInStep.yield
          (r.push (implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault))))
        : Id (Array QResult)).run.toList
    = init.toList ++ arrays.map (fun a =>
        { dims := a.dims, data := a.qs,
          attrs := if resolveKeepAttrs keepAttrs globalDefault then some a.attrs else none }) := by
  induction arrays generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih, arrayQuantile_eq, Array.toList_push]
    simp

theorem correct_collectionQuantile :
    ∀ (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool),
      problem_spec_collectionQuantile arrays keepAttrs globalDefault
        (implementation_collectionQuantile arrays keepAttrs globalDefault) := by
  intro arrays keepAttrs globalDefault
  unfold problem_spec_collectionQuantile implementation_collectionQuantile
  have h := collectionQuantile_forIn arrays keepAttrs globalDefault #[]
  simpa [Id.run] using h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

python env. same_spec=True confirmed for all 9 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical). Positive control (gold Solution.lean) verifies exit 0. Prepatch (Solution_prepatch.lean) reproduced buggy: exit 1, unsolved goals at 106/152.

### ATTACKS (each: /tmp path, cmd `bash scripts/lean_verify.sh <f>`, exit):
- atk_1 prepatch array bug (attrs always none): EXIT=1 (rfl failed L105) — does NOT close.
- atk_2 partial-domain (none-case forced to none): EXIT=1 — does NOT close.
- atk_3 boundary swap (some/none swapped): EXIT=1 (rfl failed L106) — does NOT close.
- atk_4 control-flow-effect (ignores keepAttrs, uses globalDefault only): EXIT=1 — does NOT close.
- atk_5 dims frame corruption (dims:=[]): EXIT=1 (rfl failed L106) — does NOT close.
- atk_6 attrs content corruption (selfAttrs++selfAttrs): EXIT=1 — does NOT close.
- atk_7 collection non-forwarding (prepatch bug, passes none): EXIT=1 (type mismatch L177) — does NOT close.
- atk_8 collection reorder (.reverse): EXIT=1 (type mismatch L177) — does NOT close.
- atk_9 ECHO gold-equivalent (attrs := if keepAttrs.getD globalDefault then some selfAttrs else none): EXIT=0, VERIFIES. #print axioms: correct_arrayQuantile depends on NO axioms; correct_collectionQuantile depends on [propext, Quot.sound] — clean, no sorryAx/custom.

MANDATORY RESOLVE for the closing clean-axiom impl (atk_9): materialized faithful patch = gold patch (atk_9 is behaviorally identical to gold: keepAttrs.getD globalDefault equals gold's default-then-getD). Ran run_resolve('pydata__xarray-3305', patch, timeout=1800, retries=2) via official harness → RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note='resolved'. (First attempt hit a transient docker list_images ImageNotFound race from concurrent audit containers; retry succeeded and was executed, not speculated.) So the one impl with a closing clean-axiom proof RESOLVES — verify⇒correct holds.

REFINEMENT.MD AUDIT: 6 legs, all tagged R (type refinement). Zero A-consumed, zero A-reference, zero kind-3 (changed-inexpressible) — the entire fix (keep-attrs defaulting op1, attr selection op2, result construction op3, per-variable loop op4, flag-forwarding op5, collection output op6) is modeled deeply over Attrs/QResult. Consistent with axiom_check.py (G-AX status=skip, no axiom <callee>_prop declared) and Solution.lean axioms region (no axiom). The A-leg correspondence concern is vacuous (all-R bundle); no false real-callee correspondence possible. dims/data frame-pinned to modeled inputs newDims/qs (unchanged nanpercentile+dim-removal reduction), correctly not axiomatized.

CONCLUSION: The spec is a full functional equality with no wiggle room (no ∃, no inequality, no unconstrained field). Every closing impl is forced to gold observables. Attempted 8 distinct genuinely-wrong impls across partial-domain/boundary/control-flow-effect/frame/content/ordering families + the prepatch bug; none closes. Only the gold echo closes and it resolves. No verify⇏correct gap exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) Spec regions byte-identical pre/post patch: same_spec(Solution, Solution_prepatch, lean_backend)=True. (2) Solution.lean compiles clean (lean_verify exit 0); #print axioms shows only propext/Quot.sound (collection) and none (array) — no sorryAx, proofs genuine. (3) Model matches real callee exactly: resolveKeepAttrs = keepAttrs.getD globalDefault ↔ 'if keep_attrs is None: keep_attrs=_get_keep_attrs(default=False)'; result.attrs = (if resolved then some selfAttrs else none) ↔ 'attrs = self._attrs if keep_attrs else None; return Variable(new_dims, qs, attrs)'; dims/data frame-pinned to modeled inputs newDims/qs (reduction unchanged by patch). Collection forwards the SAME keepAttrs to every member ↔ Dataset.quantile forwarding keep_attrs=keep_attrs to each var.quantile. Dataset-level own-attrs handling correctly scoped OUT (not the F2P observable, which is per-variable attrs). (4) Empirical: ran conformance_check.py against real installed xarray 0.15.1 (has the fix) — 112282 checks, 0 disagreements across keep_attrs∈{None,True,False} × global option∈{default,True,False} × empty/non-empty attrs × scalar/array q. Edge cases probed (global-option override, keep=False overriding global True) all consistent. The modeled function agrees with the real callee on every input in the fuzzed matrix; the spec is neither too strong nor drifting. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Role: leakage / gold-reconstruction (G-PANEL-3), judged against the SOLVER-VISIBLE problem_statement ONLY (hints_text excluded per rubric).

Setup checks: spec region byte-identity confirmed (swebench_unified.markers.same_spec True; markers exit 0 per verdict.md). Mechanical G-LEAK screen over the computed spec_view: PASSED, 0 hard failures (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier embedding a patched repo symbol, no fix/bug narration). meta.relaxed_leakage is None / not a relaxed bundle, so no RELAXED_LEAKAGE deferral applies — judged on the merits.

Public problem_statement already discloses the full fix intent: title 'DataArray.quantile does not honor keep_attrs' plus MCVE `da.quantile(.9, dim='x', keep_attrs=True)` whose expected output preserves {'units':'K'}. The spec is a faithful, direct formalization of that publicly stated contract:
  - result.attrs = source attrs iff the resolved keep request is true, else none (exactly the bug report's expectation);
  - keep request is optional (some true/false/none) with fallback to a caller-supplied default flag (globalDefault) — the natural modeling of an optional keep_attrs, disclosing behavior not edit location;
  - collection-level op forwards the SAME keep request to each member — derivable from 'quantile should honor keep_attrs' at the aggregate level, not an extra disclosure.

No leak beyond problem_statement: spec-view identifiers are abstract (keepAttrs, globalDefault, selfAttrs, resolveKeepAttrs, QResult, SrcArray) and none echoes internal repo symbols (Variable.quantile, Dataset.quantile, _get_keep_attrs, _attrs, nanpercentile). The only patched-symbol token that appears (quantile) is itself in the public problem_statement. No file paths (variable.py/dataset.py), line numbers, or patch structure surface in the spec view. Nothing from hints_text (which names Variable.quantile) is echoed.

Conclusion: the spec view does not reconstruct or reveal the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
