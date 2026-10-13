# P2 adversarial audit — django__django-15973

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
@@ -131,8 +131,8 @@
     | none         => modelRefToPair targetRef scopeApp scopeName
   let mut deps : List (String × String) := [firstDep]
   match throughRef with
-  | some thr =>
-      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
+  | some _ =>
+      deps := deps ++ [modelRefToPair targetRef scopeApp scopeName]
   | none => pure ()
   return deps
 -- impl-end
@@ -145,5 +145,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,11 +129,7 @@
     match swappableSetting with
     | some setting => ("__setting__", setting)
     | none         => modelRefToPair targetRef scopeApp scopeName
-  let mut deps : List (String × String) := [firstDep]
-  match throughRef with
-  | some thr =>
-      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
-  | none => pure ()
+  let deps : List (String × String) := [firstDep]
   return deps
 -- impl-end
 
@@ -145,5 +141,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,12 +129,10 @@
     match swappableSetting with
     | some setting => ("__setting__", setting)
     | none         => modelRefToPair targetRef scopeApp scopeName
-  let mut deps : List (String × String) := [firstDep]
   match throughRef with
   | some thr =>
-      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
-  | none => pure ()
-  return deps
+      return [modelRefToPair thr scopeApp scopeName, firstDep]
+  | none => return [firstDep]
 -- impl-end
 
 -- proof-start
@@ -145,5 +143,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,10 +125,7 @@
     (targetRef : ModelRef) (throughRef : Option ModelRef)
     (swappableSetting : Option String) (scopeApp scopeName : String)
     : List (String × String) := Id.run do
-  let firstDep : String × String :=
-    match swappableSetting with
-    | some setting => ("__setting__", setting)
-    | none         => modelRefToPair targetRef scopeApp scopeName
+  let firstDep : String × String := modelRefToPair targetRef scopeApp scopeName
   let mut deps : List (String × String) := [firstDep]
   match throughRef with
   | some thr =>
@@ -145,5 +142,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,8 +131,8 @@
     | none         => modelRefToPair targetRef scopeApp scopeName
   let mut deps : List (String × String) := [firstDep]
   match throughRef with
-  | some thr =>
-      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
+  | some _ =>
+      deps := deps ++ [firstDep]
   | none => pure ()
   return deps
 -- impl-end
@@ -145,5 +145,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,7 +132,7 @@
   let mut deps : List (String × String) := [firstDep]
   match throughRef with
   | some thr =>
-      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
+      deps := deps ++ [modelRefToPair thr scopeName scopeApp]
   | none => pure ()
   return deps
 -- impl-end
@@ -145,5 +145,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,10 +130,10 @@
     | some setting => ("__setting__", setting)
     | none         => modelRefToPair targetRef scopeApp scopeName
   let mut deps : List (String × String) := [firstDep]
-  match throughRef with
-  | some thr =>
+  match swappableSetting, throughRef with
+  | none, some thr =>
       deps := deps ++ [modelRefToPair thr scopeApp scopeName]
-  | none => pure ()
+  | _, _ => pure ()
   return deps
 -- impl-end
 
@@ -145,5 +145,5 @@
         (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
   intro targetRef throughRef swappableSetting scopeApp scopeName
   unfold problem_spec_relationDependencies implementation_relationDependencies
-  cases throughRef <;> rfl
+  cases throughRef <;> simp_all <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the migration dependencies of a relational field.

A relational field on a model induces, for the migration that creates it, a list
of ordered dependencies: each dependency names the `(app_label, object_name)` of
another model that must be created first. Two kinds of dependency arise:

  * the dependency on the field's target model — the model the relation points
    at (or, for a field tied to a swappable setting, a dependency keyed by that
    setting instead);
  * when the relation routes through an explicit intermediary ("through") model,
    an additional dependency on that intermediary model.

Every model the field refers to is given as a *reference*: either a string of
the form `"app_label.ObjectName"` (or a bare `"ObjectName"`, or the recursive
marker), or a concrete model whose own metadata already carries its app label
and object name. Resolving a reference to its `(app_label, object_name)` pair is
done **within the scope of the field's owning model** — the owning model's app
label and name supply the scope for unscoped or recursive references.

The contract below pins, for every input, the exact list of resolved
dependency pairs: the target dependency, followed — only when an intermediary
model is specified — by the dependency for that intermediary model, each pair
resolved from the reference that actually denotes the model that dependency is
about, in the owning model's scope.

The object-name case normalization the resolver applies to textual references
is left ABSTRACT (`lower`, an opaque function bound to the surrounding
platform's string lower-casing): its exact character mapping (a full Unicode
case fold) is orthogonal to the dependency-construction rule modeled here, and
leaving it opaque keeps the contract faithful on every input — including
non-ASCII object names — instead of committing to an approximation of the
fold. Concrete model references, the scope strings, and the swappable setting
are passed through verbatim (no case folding is applied to them).
-/

-- axioms-start
-- The reference→`(app_label, object_name)` resolution used here is an UNCHANGED
-- helper of the surrounding code. It is modeled DEEPLY (spelled out in the
-- `pure` region as `modelRefToPair`) rather than axiomatized, so the contract is
-- grounded in the inputs and not in an opaque oracle — EXCEPT for one
-- building block, the string case normalization, declared opaque below.

/-- Lower-case a string: the object-name case normalization the resolver
applies to textual references. This is the platform's full string
lower-casing (a Unicode case fold, e.g. `"Ä"` → `"ä"`, not merely an ASCII
letter shift). It is an UNCHANGED per-string building block of the resolver;
its exact character mapping is orthogonal to the dependency-construction rule
modeled here, so it is left abstract (`opaque`) rather than approximated. Its
binding to the real normalization is validated executably by G-AX as part of
the `resolve_relation` A-reference (no `axiom` about it is consumed: the proof
never inspects its behavior). -/
opaque lower : String → String
-- axioms-end

-- pure-start
/-- A reference to a model: either a textual reference (an `"app.Object"` string,
a bare `"Object"`, or the recursive self-marker `"self"`), or a concrete model
that already carries its own `(app_label, object_name)` metadata. -/
inductive ModelRef where
  | str (s : String)
  | concrete (appLabel objectName : String)
  deriving DecidableEq, Repr

/-- Split a string on its FIRST `.` only, mirroring `split(".", 1)`: `none` when
the string contains no `.`, else the prefix before the first `.` paired with the
remainder after it. -/
def splitFirstDot (s : String) : Option (String × String) :=
  match s.splitOn "." with
  | []      => none
  | [_]     => none
  | a :: rest => some (a, ".".intercalate rest)

/-- Resolve a model reference to its `(app_label, object_name)` pair within the
scope given by `scopeApp`/`scopeName` (the owning model's app label and name):

  * a concrete model yields its own metadata pair unchanged;
  * the recursive marker `"self"` yields the enclosing scope;
  * an `"app.Object"` textual reference splits on its first `.`, keeping the app
    label verbatim and lower-casing the object name;
  * a bare `"Object"` reference is scoped to the owning model's app label, with a
    lower-cased object name. -/
def modelRefToPair (m : ModelRef) (scopeApp scopeName : String) : String × String :=
  match m with
  | .concrete a n => (a, n)
  | .str s =>
      if s = "self" then (scopeApp, scopeName)
      else
        match splitFirstDot s with
        | some (a, n) => (a, lower n)
        | none        => (scopeApp, lower s)
-- pure-end

-- post-conditions-start
/-- The resolved dependency list is fully pinned to the inputs:

  * its first entry is the target dependency — `("__setting__", setting)` when the
    field is tied to a swappable `setting`, otherwise the target model reference
    resolved in the owning model's scope;
  * when an intermediary model reference `thr` is supplied, the list has exactly
    one further entry: that intermediary reference resolved in the owning model's
    scope. When no intermediary model is supplied the list stops after the target
    dependency.

No output entry is left unconstrained: both the presence/absence of the second
entry and the value of every entry are determined by the inputs. -/
def problem_spec_relationDependencies
    (targetRef : ModelRef) (throughRef : Option ModelRef)
    (swappableSetting : Option String) (scopeApp scopeName : String)
    (result : List (String × String)) : Prop :=
  let firstDep : String × String :=
    match swappableSetting with
    | some setting => ("__setting__", setting)
    | none         => modelRefToPair targetRef scopeApp scopeName
  match throughRef with
  | none     => result = [firstDep]
  | some thr => result = [firstDep, modelRefToPair thr scopeApp scopeName]
-- post-conditions-end

-- impl-start
def implementation_relationDependencies
    (targetRef : ModelRef) (throughRef : Option ModelRef)
    (swappableSetting : Option String) (scopeApp scopeName : String)
    : List (String × String) := Id.run do
  let firstDep : String × String :=
    match swappableSetting with
    | some setting => ("__setting__", setting)
    | none         => modelRefToPair targetRef scopeApp scopeName
  let mut deps : List (String × String) := [firstDep]
  match throughRef with
  | some thr =>
      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
  | none => pure ()
  return deps
-- impl-end

-- proof-start
theorem correct_relationDependencies :
    ∀ (targetRef : ModelRef) (throughRef : Option ModelRef)
      (swappableSetting : Option String) (scopeApp scopeName : String),
      problem_spec_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName
        (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
  intro targetRef throughRef swappableSetting scopeApp scopeName
  unfold problem_spec_relationDependencies implementation_relationDependencies
  cases throughRef <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_relationDependencies is a FULLY-PINNED universal functional equality: for every input the postcondition forces result = [firstDep] (no through) or result = [firstDep, modelRefToPair thr scopeApp scopeName] (through), where firstDep is ('__setting__', setting) when swappable else modelRefToPair targetRef scopeApp scopeName. Any verifying same-spec impl must compute exactly this function, so no wrong impl can close its proof. Confirmed empirically.

Protocol executed (all same_spec=True via markers.same_spec on lean backend; only the impl region edited, axioms/pure/pre/post byte-identical).

Positive control (gold impl, cp of Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. `#print axioms correct_relationDependencies` (pos_axioms.lean) -> 'depends on axioms: [propext]' (CLEAN: no sorryAx, no shipped axiom; opaque lower NOT consumed).

7 DISTINCT same-spec wrong impls, each with the gold proof skeleton hardened to `cases throughRef <;> simp_all <;> rfl`; all FAILED to verify (exit=1, unprovable residual goal):
- atk_1 PREPATCH BUG (through dep resolves targetRef instead of thr): exit=1, residual `modelRefToPair targetRef scopeApp scopeName = modelRefToPair val✝ scopeApp scopeName` (unprovable — the F2P case test_create_with_through_model_separate_apps). prepatch_reproduced=true.
- atk_2 partial-domain (drops through dep, always single): exit=1, residual `⊢ False`.
- atk_3 boundary (reversed dep order): exit=1, list mismatch.
- atk_4 control-flow-effect (ignores swappableSetting for firstDep): exit=1, mismatch.
- atk_5 ungrounded-oracle echo (through dep = echo of firstDep): exit=1, mismatch.
- atk_6 boundary (swaps scopeApp/scopeName args to modelRefToPair for through): exit=1, residual `modelRefToPair val✝ scopeName scopeApp = modelRefToPair val✝ scopeApp scopeName`.
- atk_7 control-flow (skips through dep when swappable set): exit=1, list mismatch.

All verifications run concurrently as background jobs (<=4 at a time). Commands: `bash scripts/lean_verify.sh atk_N.lean` from project root.

Since ZERO wrong impls close with clean axioms, there is NO patch to materialize/resolve — verify=>correct cannot be broken here (patches={}).

refinement.md audit: all legs are R / A-reference / I. NO A-consumed row, NO kind-3 (ungrounded axiom) leg. The single A-reference resolve_relation is DEEP-modeled as modelRefToPair (not axiomatized) and executably validated == the real repo callee by axiom_check.py/G-AX on 50k+ inputs incl. concrete/self/dotted/bare boundary cases. `opaque lower` abstracts Python str.lower's full Unicode case fold (orthogonal to the dependency-construction rule); the proof never unfolds it, hence axioms=[propext]. deep_model_references=['resolve_relation'] matches. Model<->patch correspondence holds: the fix (through dep resolves field.remote_field.through, not remote_field_model) is exactly discriminated by the through-branch clause, and atk_1 confirms the prepatch bug fails the spec.

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
Computing the migration dependencies of a relational field.

A relational field on a model induces, for the migration that creates it, a list
of ordered dependencies: each dependency names the `(app_label, object_name)` of
another model that must be created first. Two kinds of dependency arise:

  * the dependency on the field's target model — the model the relation points
    at (or, for a field tied to a swappable setting, a dependency keyed by that
    setting instead);
  * when the relation routes through an explicit intermediary ("through") model,
    an additional dependency on that intermediary model.

Every model the field refers to is given as a *reference*: either a string of
the form `"app_label.ObjectName"` (or a bare `"ObjectName"`, or the recursive
marker), or a concrete model whose own metadata already carries its app label
and object name. Resolving a reference to its `(app_label, object_name)` pair is
done **within the scope of the field's owning model** — the owning model's app
label and name supply the scope for unscoped or recursive references.

The contract below pins, for every input, the exact list of resolved
dependency pairs: the target dependency, followed — only when an intermediary
model is specified — by the dependency for that intermediary model, each pair
resolved from the reference that actually denotes the model that dependency is
about, in the owning model's scope.

The object-name case normalization the resolver applies to textual references
is left ABSTRACT (`lower`, an opaque function bound to the surrounding
platform's string lower-casing): its exact character mapping (a full Unicode
case fold) is orthogonal to the dependency-construction rule modeled here, and
leaving it opaque keeps the contract faithful on every input — including
non-ASCII object names — instead of committing to an approximation of the
fold. Concrete model references, the scope strings, and the swappable setting
are passed through verbatim (no case folding is applied to them).
-/

-- axioms-start
-- The reference→`(app_label, object_name)` resolution used here is an UNCHANGED
-- helper of the surrounding code. It is modeled DEEPLY (spelled out in the
-- `pure` region as `modelRefToPair`) rather than axiomatized, so the contract is
-- grounded in the inputs and not in an opaque oracle — EXCEPT for one
-- building block, the string case normalization, declared opaque below.

/-- Lower-case a string: the object-name case normalization the resolver
applies to textual references. This is the platform's full string
lower-casing (a Unicode case fold, e.g. `"Ä"` → `"ä"`, not merely an ASCII
letter shift). It is an UNCHANGED per-string building block of the resolver;
its exact character mapping is orthogonal to the dependency-construction rule
modeled here, so it is left abstract (`opaque`) rather than approximated. Its
binding to the real normalization is validated executably by G-AX as part of
the `resolve_relation` A-reference (no `axiom` about it is consumed: the proof
never inspects its behavior). -/
opaque lower : String → String
-- axioms-end

-- pure-start
/-- A reference to a model: either a textual reference (an `"app.Object"` string,
a bare `"Object"`, or the recursive self-marker `"self"`), or a concrete model
that already carries its own `(app_label, object_name)` metadata. -/
inductive ModelRef where
  | str (s : String)
  | concrete (appLabel objectName : String)
  deriving DecidableEq, Repr

/-- Split a string on its FIRST `.` only, mirroring `split(".", 1)`: `none` when
the string contains no `.`, else the prefix before the first `.` paired with the
remainder after it. -/
def splitFirstDot (s : String) : Option (String × String) :=
  match s.splitOn "." with
  | []      => none
  | [_]     => none
  | a :: rest => some (a, ".".intercalate rest)

/-- Resolve a model reference to its `(app_label, object_name)` pair within the
scope given by `scopeApp`/`scopeName` (the owning model's app label and name):

  * a concrete model yields its own metadata pair unchanged;
  * the recursive marker `"self"` yields the enclosing scope;
  * an `"app.Object"` textual reference splits on its first `.`, keeping the app
    label verbatim and lower-casing the object name;
  * a bare `"Object"` reference is scoped to the owning model's app label, with a
    lower-cased object name. -/
def modelRefToPair (m : ModelRef) (scopeApp scopeName : String) : String × String :=
  match m with
  | .concrete a n => (a, n)
  | .str s =>
      if s = "self" then (scopeApp, scopeName)
      else
        match splitFirstDot s with
        | some (a, n) => (a, lower n)
        | none        => (scopeApp, lower s)
-- pure-end

-- post-conditions-start
/-- The resolved dependency list is fully pinned to the inputs:

  * its first entry is the target dependency — `("__setting__", setting)` when the
    field is tied to a swappable `setting`, otherwise the target model reference
    resolved in the owning model's scope;
  * when an intermediary model reference `thr` is supplied, the list has exactly
    one further entry: that intermediary reference resolved in the owning model's
    scope. When no intermediary model is supplied the list stops after the target
    dependency.

No output entry is left unconstrained: both the presence/absence of the second
entry and the value of every entry are determined by the inputs. -/
def problem_spec_relationDependencies
    (targetRef : ModelRef) (throughRef : Option ModelRef)
    (swappableSetting : Option String) (scopeApp scopeName : String)
    (result : List (String × String)) : Prop :=
  let firstDep : String × String :=
    match swappableSetting with
    | some setting => ("__setting__", setting)
    | none         => modelRefToPair targetRef scopeApp scopeName
  match throughRef with
  | none     => result = [firstDep]
  | some thr => result = [firstDep, modelRefToPair thr scopeApp scopeName]
-- post-conditions-end

-- impl-start
def implementation_relationDependencies
    (targetRef : ModelRef) (throughRef : Option ModelRef)
    (swappableSetting : Option String) (scopeApp scopeName : String)
    : List (String × String) := Id.run do
  let firstDep : String × String :=
    match swappableSetting with
    | some setting => ("__setting__", setting)
    | none         => modelRefToPair targetRef scopeApp scopeName
  let mut deps : List (String × String) := [firstDep]
  match throughRef with
  | some thr =>
      deps := deps ++ [modelRefToPair thr scopeApp scopeName]
  | none => pure ()
  return deps
-- impl-end

-- proof-start
theorem correct_relationDependencies :
    ∀ (targetRef : ModelRef) (throughRef : Option ModelRef)
      (swappableSetting : Option String) (scopeApp scopeName : String),
      problem_spec_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName
        (implementation_relationDependencies targetRef throughRef swappableSetting scopeApp scopeName) := by
  intro targetRef throughRef swappableSetting scopeApp scopeName
  unfold problem_spec_relationDependencies implementation_relationDependencies
  cases throughRef <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_relationDependencies is a FULLY-PINNED universal functional equality: for every input the postcondition forces result = [firstDep] (no through) or result = [firstDep, modelRefToPair thr scopeApp scopeName] (through), where firstDep is ('__setting__', setting) when swappable else modelRefToPair targetRef scopeApp scopeName. Any verifying same-spec impl must compute exactly this function, so no wrong impl can close its proof. Confirmed empirically.

Protocol executed (all same_spec=True via markers.same_spec on lean backend; only the impl region edited, axioms/pure/pre/post byte-identical).

Positive control (gold impl, cp of Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. `#print axioms correct_relationDependencies` (pos_axioms.lean) -> 'depends on axioms: [propext]' (CLEAN: no sorryAx, no shipped axiom; opaque lower NOT consumed).

7 DISTINCT same-spec wrong impls, each with the gold proof skeleton hardened to `cases throughRef <;> simp_all <;> rfl`; all FAILED to verify (exit=1, unprovable residual goal):
- atk_1 PREPATCH BUG (through dep resolves targetRef instead of thr): exit=1, residual `modelRefToPair targetRef scopeApp scopeName = modelRefToPair val✝ scopeApp scopeName` (unprovable — the F2P case test_create_with_through_model_separate_apps). prepatch_reproduced=true.
- atk_2 partial-domain (drops through dep, always single): exit=1, residual `⊢ False`.
- atk_3 boundary (reversed dep order): exit=1, list mismatch.
- atk_4 control-flow-effect (ignores swappableSetting for firstDep): exit=1, mismatch.
- atk_5 ungrounded-oracle echo (through dep = echo of firstDep): exit=1, mismatch.
- atk_6 boundary (swaps scopeApp/scopeName args to modelRefToPair for through): exit=1, residual `modelRefToPair val✝ scopeName scopeApp = modelRefToPair val✝ scopeApp scopeName`.
- atk_7 control-flow (skips through dep when swappable set): exit=1, list mismatch.

All verifications run concurrently as background jobs (<=4 at a time). Commands: `bash scripts/lean_verify.sh atk_N.lean` from project root.

Since ZERO wrong impls close with clean axioms, there is NO patch to materialize/resolve — verify=>correct cannot be broken here (patches={}).

refinement.md audit: all legs are R / A-reference / I. NO A-consumed row, NO kind-3 (ungrounded axiom) leg. The single A-reference resolve_relation is DEEP-modeled as modelRefToPair (not axiomatized) and executably validated == the real repo callee by axiom_check.py/G-AX on 50k+ inputs incl. concrete/self/dotted/bare boundary cases. `opaque lower` abstracts Python str.lower's full Unicode case fold (orthogonal to the dependency-construction rule); the proof never unfolds it, hence axioms=[propext]. deep_model_references=['resolve_relation'] matches. Model<->patch correspondence holds: the fix (through dep resolves field.remote_field.through, not remote_field_model) is exactly discriminated by the through-branch clause, and atk_1 confirms the prepatch bug fails the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of django__django-15973 lean bundle. Modeled fn: _get_dependencies_for_foreign_key (autodetector.py:1397-1431 @ base 2480554dc4), callee resolve_relation (utils.py:27-51), both read at base_commit git show.

Preconditions verified:
- same_spec(Solution, Solution_prepatch, lean) = True (spec region byte-identical).
- lean_verify.sh exit 0; #print axioms correct_relationDependencies = [propext] only (no sorryAx; opaque lower adds no axiom). Genuine proof.
- conformance_check.py: 150007 inputs, 0 disagreements, status=pass.

Branch-by-branch model vs real callee — NO divergence found:
- modelRefToPair .concrete a n -> (a,n) matches model._meta.(app_label, model_name) (verbatim, no fold).
- "self" -> (scopeApp, scopeName): RECURSIVE_RELATIONSHIP_CONSTANT confirmed = "self" (related.py:40). Matches.
- "app.Obj" -> (a, lower n): splitFirstDot (splitOn "." then re-intercalate remainder) is provably equal to Python split(".",1) on all shapes (a.b.c, trailing/leading dot, no dot); obj lowered, app verbatim. Matches.
- bare "Obj" -> (scopeApp, lower s) matches (app_label, model.lower()).
- firstDep: swappable some setting -> ("__setting__", setting) matches `if swappable_setting is not None`; Option boundary aligns with `is not None` (empty string still 'some'). none -> resolve target. Matches.
- through: gated by some thr, resolved from thr (the fix, field.remote_field.through) in owning scope. Matches post-patch line 1424. (None,True) tail is an input-independent literal at both append sites -> correctly projected out (frame note).
- TypeError branches (recursive relation w/ None app_label/model_name) unreachable at this call site (owning model always named) -> correctly unmodeled; F2P inputs never reach them.
- opaque lower: NOT a too-strong commitment. Left uninterpreted and bound to real str.lower by G-AX; the correctness proof never unfolds it, and Lean's Char.toLower (ASCII-only) cannot reproduce Python's Unicode fold, so abstraction is the faithful choice on non-ASCII names. Under the intended binding the model equals the real callee on every input.

No input exists where the modeled function disagrees with the real repo callee. Spec is faithful and (from functional uniqueness in verdict.md) exactly determines the gold output. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical pre/post-patch (same_spec=True); mechanical G-LEAK screen passes (no diff markers, no patched file/module path, no reproduced gold-diff line, no narration). No relaxation flag (relaxed_leakage=None). Gold edit is a one-liner: `remote_field_model` -> `field.remote_field.through` in _get_dependencies_for_foreign_key. Leakage assessment beyond the public problem_statement: (1) Modeled symbol is the NEUTRAL `relationDependencies` — no echo of the patched symbol `_get_dependencies_for_foreign_key`; patched file `autodetector.py` never appears in the view. (2) The only repo symbol named in view comments is `resolve_relation`, which is the UNCHANGED callee (deep-modeled as modelRefToPair) — it localizes no edit. (3) The post-condition pins the CORRECT behavior (through dep = `modelRefToPair thr …`, i.e. resolve the intermediary reference in the owning model's scope). Encoding correct behavior is the legitimate function of a functional spec — it is NOT edit-disclosure: the view never narrates the prior/buggy behavior (never says the through dep was previously resolved from the target reference), contains no bug/fix narration, and reveals no diff/localization. (4) The problem_statement itself already discloses the crux (a through model in ANOTHER app raises `field.remote_field.through._meta` AttributeError), so the spec's semantic content (through reference resolved in scope, honoring its own app) does not exceed what is public. No spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
