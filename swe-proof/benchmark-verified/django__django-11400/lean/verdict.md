# P2 adversarial audit — django__django-11400

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl admits a closing clean-axiom proof, so no faithful patch needed to be materialized/resolved (protocol step 2 vacuously satisfied).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,8 +68,7 @@
 def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
     (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
   let mut qs := objs
-  if ordering ≠ [] then
-    qs := applyOrdering ordering objs
+  qs := applyOrdering ordering objs
   return (if includeBlank then blank else []) ++ qs.map toChoice
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,8 +84,7 @@
 -- impl-start
 def implementation_restrictedChoices (adminOrdering : Option (List String))
     (objs : List Obj) : List (Int × String) := Id.run do
-  let ordering := configuredOrdering adminOrdering
-  return implementation_orderedChoices false [] ordering objs
+  return implementation_orderedChoices false [] [] objs
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,7 +68,7 @@
 def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
     (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
   let mut qs := objs
-  if ordering ≠ [] then
+  if ordering = [] then
     qs := applyOrdering ordering objs
   return (if includeBlank then blank else []) ++ qs.map toChoice
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   let mut qs := objs
   if ordering ≠ [] then
     qs := applyOrdering ordering objs
-  return (if includeBlank then blank else []) ++ qs.map toChoice
+  return [] ++ qs.map toChoice
 -- impl-end
 
 -- post-conditions-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,7 +67,7 @@
 -- impl-start
 def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
     (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
-  let mut qs := objs
+  let mut qs := objs.reverse
   if ordering ≠ [] then
     qs := applyOrdering ordering objs
   return (if includeBlank then blank else []) ++ qs.map toChoice
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,9 +67,7 @@
 -- impl-start
 def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
     (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
-  let mut qs := objs
-  if ordering ≠ [] then
-    qs := applyOrdering ordering objs
+  let qs := objs
   return (if includeBlank then blank else []) ++ qs.map toChoice
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   let mut qs := objs
   if ordering ≠ [] then
     qs := applyOrdering ordering objs
-  return (if includeBlank then blank else []) ++ qs.map toChoice
+  return (if includeBlank then blank else []) ++ (qs.map toChoice).reverse
 -- impl-end
 
 -- post-conditions-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
 def implementation_restrictedChoices (adminOrdering : Option (List String))
     (objs : List Obj) : List (Int × String) := Id.run do
   let ordering := configuredOrdering adminOrdering
-  return implementation_orderedChoices false [] ordering objs
+  return (applyOrdering ordering objs).map toChoice
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Presenting the selectable values of a related collection as an ordered list of
(key, label) choices.

A related collection of records is materialized in a default presentation order
(the order intrinsic to the collection). A caller may additionally supply an
explicit ordering directive — a list of sort keys. The desired behavior:

  * when the directive is EMPTY, the collection's own default presentation order
    is preserved unchanged;
  * when the directive is NON-EMPTY, the collection is re-sequenced according to
    the directive before the choices are produced.

Each surviving record contributes one `(key, label)` choice, in the resulting
order; an optional leading "blank" choice may be prepended.

A second behavior concerns a restricted variant of this listing, where the set
of records has already been narrowed: the same ordering directive that a
configuration provides for the collection must be honored here too, rather than
discarded.

Behavior is stated abstractly as input→output relations; the implementations and
correctness proofs are supplied separately.
-/

-- axioms-start
/-- A record in a related collection: an identity key, plus an opaque label used
as its display text. (Only the touched fields are modeled; the bijection to the
real object is in mapping.md.) -/
structure Obj where
  pk : Int
  label : String
deriving Inhabited

/-- Re-sequencing a record list under an explicit ordering directive (a list of
sort keys). This is an ambient, behavior-preserving primitive: it is only ever
consulted, never redefined, so its result for a given directive and record list
is taken as given. It is applied ONLY for a non-empty directive; the spec never
asserts what it returns for the empty directive, pinning the empty-directive
result to the default presentation order instead. -/
opaque applyOrdering : List String → List Obj → List Obj
-- axioms-end

-- pure-start
/-- The (key, label) choice contributed by one record. -/
def toChoice (o : Obj) : Int × String := (o.pk, o.label)

/-- The ordering directive in force for a restricted listing: the configuration's
ordering when one is provided, otherwise none (the empty directive). -/
def configuredOrdering (adminOrdering : Option (List String)) : List String :=
  adminOrdering.getD []
-- pure-end

-- post-conditions-start
/-- The ordered choice list: an optional leading blank choice, followed by one
choice per record. The records appear in their default presentation order when
the ordering directive is empty, and re-sequenced under the directive otherwise. -/
def problem_spec_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
    (ordering : List String) (objs : List Obj) (result : List (Int × String)) : Prop :=
  result = (if includeBlank then blank else [])
    ++ (if ordering = [] then objs else applyOrdering ordering objs).map toChoice
-- post-conditions-end

-- impl-start
def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
    (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
-- impl-end

-- post-conditions-start
/-- The restricted listing presents the (already narrowed) record set with no
leading blank choice, honoring the configuration's ordering directive. -/
def problem_spec_restrictedChoices (adminOrdering : Option (List String))
    (objs : List Obj) (result : List (Int × String)) : Prop :=
  problem_spec_orderedChoices false [] (configuredOrdering adminOrdering) objs result
-- post-conditions-end

-- impl-start
def implementation_restrictedChoices (adminOrdering : Option (List String))
    (objs : List Obj) : List (Int × String) := Id.run do
  let ordering := configuredOrdering adminOrdering
  return implementation_orderedChoices false [] ordering objs
-- impl-end

-- proof-start
theorem correct_orderedChoices :
    ∀ (includeBlank : Bool) (blank : List (Int × String))
      (ordering : List String) (objs : List Obj),
      problem_spec_orderedChoices includeBlank blank ordering objs
        (implementation_orderedChoices includeBlank blank ordering objs) := by
  intro includeBlank blank ordering objs
  unfold problem_spec_orderedChoices implementation_orderedChoices
  by_cases h : ordering = [] <;>
    simp only [h, Id.run, ne_eq, not_true_eq_false, not_false_eq_true,
      if_true, if_false] <;> rfl
-- proof-end

-- proof-start
theorem correct_restrictedChoices :
    ∀ (adminOrdering : Option (List String)) (objs : List Obj),
      problem_spec_restrictedChoices adminOrdering objs
        (implementation_restrictedChoices adminOrdering objs) := by
  intro adminOrdering objs
  unfold problem_spec_restrictedChoices implementation_restrictedChoices
  simp only [Id.run]
  exact correct_orderedChoices false [] (configuredOrdering adminOrdering) objs
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: spec_view for the lean backend elides BOTH impl and proof regions, so same_spec depends only on imports/docstring/axioms/pure/post-conditions. All attacks edit ONLY impl (and the carried closing-proof attempt), leaving axioms/pure/post byte-identical. same_spec(gold, atk_N) == True confirmed for all 8 attacks + pos_control (python swebench_unified.markers.same_spec, lean backend).

SPEC SHAPE: both postconditions are STRICT functional equalities: problem_spec_orderedChoices pins result = (if includeBlank then blank else []) ++ (if ordering = [] then objs else applyOrdering ordering objs).map toChoice; restricted layers on it via configuredOrdering. Because opaque applyOrdering has NO asserted property and the empty-directive branch is pinned to objs (NOT applyOrdering [] objs), any impl deviating in control flow, blank handling, order, or oracle routing is FORCED to leave an unprovable residual goal.

POSITIVE CONTROL: cmd `bash scripts/lean_verify.sh <pos_control.lean>` -> EXIT 0 (verifies, no sorry). `#print axioms correct_orderedChoices` / `correct_restrictedChoices` (via pos_axcheck.lean) -> both depend on axioms: [propext, Quot.sound] ONLY. CLEAN — no applyOrdering axiom, no sorryAx. Confirms opaque applyOrdering contributes no axiom.

### ATTACKS (all cmd `bash scripts/lean_verify.sh <atk_N.lean>`):
- atk_1 (prepatch_1 bug: applyOrdering applied UNCONDITIONALLY in orderedChoices): EXIT 1, error atk_1.lean:100 `rfl` failed (residual applyOrdering [] objs = objs, unprovable — opaque). Reproduces the real prepatch bug.
- atk_2 (prepatch_2 bug: restrictedChoices always uses [] directive, discarding configuredOrdering): EXIT 1, type mismatch atk_2.lean:111. Reproduces prepatch bug.
- atk_3 (inverted guard: apply ordering iff ordering = []): EXIT 1, `rfl` failed atk_3.lean:101.
- atk_4 (blank always dropped: return [] ++ ...): EXIT 1, `rfl` failed atk_4.lean:101.
- atk_5 (control-flow-effect: objs reversed in empty-directive branch): EXIT 1, `rfl` failed atk_5.lean:101.
- atk_6 (ungrounded-oracle: ordering never applied, always objs): EXIT 1, `rfl` failed atk_6.lean:99.
- atk_7 (boundary: final choice list reversed): EXIT 1, `rfl` failed atk_7.lean:101.
- atk_8 (restrictedChoices routes empty directive through applyOrdering unconditionally): EXIT 1, type mismatch atk_8.lean:112.
All 8 fail with GENUINE proof errors (rfl-failed / type-mismatch), none via sorry. NONE closes with clean axioms => protocol step 2 has no verifying attack to materialize/resolve; no resolve run was required or possible. prepatch_1 and prepatch_2 bugs both re-encoded and both fail (prepatch_reproduced=true).

REFINEMENT.MD AUDIT: No axiom is declared or consumed. Sole opaque `applyOrdering` (QuerySet.order_by) is I-tagged: proofs only ECHO it in the non-empty branch, assert no property — corroborated by clean #print axioms (no applyOrdering axiom). Every leg is R or I; NO kind-3, no A-consumed/A-reference leg exists, so no callee-axiom correspondence obligation. G-AX is a legitimate skip stub. The R/I legs are differential-tested by G-CONF (conformance_check.py present, uses REAL order_by / get_choices / RelatedOnlyFieldListFilter over full discrete matrix + 120k random draws, seed 20240629). Model-to-patch correspondence (mapping.md) is coherent: empty-directive => default order (objs), non-empty => applyOrdering, restricted layer forwards configuredOrdering — matches the gold guard fix.

VERDICT: SOUND. 8 distinct same-spec wrong impls (incl. both prepatch bugs) run through lean_verify concurrently (<=4 batches); all fail to close. Positive control verifies with clean axioms. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl admits a closing clean-axiom proof, so no faithful patch needed to be materialized/resolved (protocol step 2 vacuously satisfied).
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Presenting the selectable values of a related collection as an ordered list of
(key, label) choices.

A related collection of records is materialized in a default presentation order
(the order intrinsic to the collection). A caller may additionally supply an
explicit ordering directive — a list of sort keys. The desired behavior:

  * when the directive is EMPTY, the collection's own default presentation order
    is preserved unchanged;
  * when the directive is NON-EMPTY, the collection is re-sequenced according to
    the directive before the choices are produced.

Each surviving record contributes one `(key, label)` choice, in the resulting
order; an optional leading "blank" choice may be prepended.

A second behavior concerns a restricted variant of this listing, where the set
of records has already been narrowed: the same ordering directive that a
configuration provides for the collection must be honored here too, rather than
discarded.

Behavior is stated abstractly as input→output relations; the implementations and
correctness proofs are supplied separately.
-/

-- axioms-start
/-- A record in a related collection: an identity key, plus an opaque label used
as its display text. (Only the touched fields are modeled; the bijection to the
real object is in mapping.md.) -/
structure Obj where
  pk : Int
  label : String
deriving Inhabited

/-- Re-sequencing a record list under an explicit ordering directive (a list of
sort keys). This is an ambient, behavior-preserving primitive: it is only ever
consulted, never redefined, so its result for a given directive and record list
is taken as given. It is applied ONLY for a non-empty directive; the spec never
asserts what it returns for the empty directive, pinning the empty-directive
result to the default presentation order instead. -/
opaque applyOrdering : List String → List Obj → List Obj
-- axioms-end

-- pure-start
/-- The (key, label) choice contributed by one record. -/
def toChoice (o : Obj) : Int × String := (o.pk, o.label)

/-- The ordering directive in force for a restricted listing: the configuration's
ordering when one is provided, otherwise none (the empty directive). -/
def configuredOrdering (adminOrdering : Option (List String)) : List String :=
  adminOrdering.getD []
-- pure-end

-- post-conditions-start
/-- The ordered choice list: an optional leading blank choice, followed by one
choice per record. The records appear in their default presentation order when
the ordering directive is empty, and re-sequenced under the directive otherwise. -/
def problem_spec_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
    (ordering : List String) (objs : List Obj) (result : List (Int × String)) : Prop :=
  result = (if includeBlank then blank else [])
    ++ (if ordering = [] then objs else applyOrdering ordering objs).map toChoice
-- post-conditions-end

-- impl-start
def implementation_orderedChoices (includeBlank : Bool) (blank : List (Int × String))
    (ordering : List String) (objs : List Obj) : List (Int × String) := Id.run do
  let mut qs := objs
  if ordering ≠ [] then
    qs := applyOrdering ordering objs
  return (if includeBlank then blank else []) ++ qs.map toChoice
-- impl-end

-- post-conditions-start
/-- The restricted listing presents the (already narrowed) record set with no
leading blank choice, honoring the configuration's ordering directive. -/
def problem_spec_restrictedChoices (adminOrdering : Option (List String))
    (objs : List Obj) (result : List (Int × String)) : Prop :=
  problem_spec_orderedChoices false [] (configuredOrdering adminOrdering) objs result
-- post-conditions-end

-- impl-start
def implementation_restrictedChoices (adminOrdering : Option (List String))
    (objs : List Obj) : List (Int × String) := Id.run do
  let ordering := configuredOrdering adminOrdering
  return implementation_orderedChoices false [] ordering objs
-- impl-end

-- proof-start
theorem correct_orderedChoices :
    ∀ (includeBlank : Bool) (blank : List (Int × String))
      (ordering : List String) (objs : List Obj),
      problem_spec_orderedChoices includeBlank blank ordering objs
        (implementation_orderedChoices includeBlank blank ordering objs) := by
  intro includeBlank blank ordering objs
  unfold problem_spec_orderedChoices implementation_orderedChoices
  by_cases h : ordering = [] <;>
    simp only [h, Id.run, ne_eq, not_true_eq_false, not_false_eq_true,
      if_true, if_false] <;> rfl
-- proof-end

-- proof-start
theorem correct_restrictedChoices :
    ∀ (adminOrdering : Option (List String)) (objs : List Obj),
      problem_spec_restrictedChoices adminOrdering objs
        (implementation_restrictedChoices adminOrdering objs) := by
  intro adminOrdering objs
  unfold problem_spec_restrictedChoices implementation_restrictedChoices
  simp only [Id.run]
  exact correct_orderedChoices false [] (configuredOrdering adminOrdering) objs
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: spec_view for the lean backend elides BOTH impl and proof regions, so same_spec depends only on imports/docstring/axioms/pure/post-conditions. All attacks edit ONLY impl (and the carried closing-proof attempt), leaving axioms/pure/post byte-identical. same_spec(gold, atk_N) == True confirmed for all 8 attacks + pos_control (python swebench_unified.markers.same_spec, lean backend).

SPEC SHAPE: both postconditions are STRICT functional equalities: problem_spec_orderedChoices pins result = (if includeBlank then blank else []) ++ (if ordering = [] then objs else applyOrdering ordering objs).map toChoice; restricted layers on it via configuredOrdering. Because opaque applyOrdering has NO asserted property and the empty-directive branch is pinned to objs (NOT applyOrdering [] objs), any impl deviating in control flow, blank handling, order, or oracle routing is FORCED to leave an unprovable residual goal.

POSITIVE CONTROL: cmd `bash scripts/lean_verify.sh <pos_control.lean>` -> EXIT 0 (verifies, no sorry). `#print axioms correct_orderedChoices` / `correct_restrictedChoices` (via pos_axcheck.lean) -> both depend on axioms: [propext, Quot.sound] ONLY. CLEAN — no applyOrdering axiom, no sorryAx. Confirms opaque applyOrdering contributes no axiom.

### ATTACKS (all cmd `bash scripts/lean_verify.sh <atk_N.lean>`):
- atk_1 (prepatch_1 bug: applyOrdering applied UNCONDITIONALLY in orderedChoices): EXIT 1, error atk_1.lean:100 `rfl` failed (residual applyOrdering [] objs = objs, unprovable — opaque). Reproduces the real prepatch bug.
- atk_2 (prepatch_2 bug: restrictedChoices always uses [] directive, discarding configuredOrdering): EXIT 1, type mismatch atk_2.lean:111. Reproduces prepatch bug.
- atk_3 (inverted guard: apply ordering iff ordering = []): EXIT 1, `rfl` failed atk_3.lean:101.
- atk_4 (blank always dropped: return [] ++ ...): EXIT 1, `rfl` failed atk_4.lean:101.
- atk_5 (control-flow-effect: objs reversed in empty-directive branch): EXIT 1, `rfl` failed atk_5.lean:101.
- atk_6 (ungrounded-oracle: ordering never applied, always objs): EXIT 1, `rfl` failed atk_6.lean:99.
- atk_7 (boundary: final choice list reversed): EXIT 1, `rfl` failed atk_7.lean:101.
- atk_8 (restrictedChoices routes empty directive through applyOrdering unconditionally): EXIT 1, type mismatch atk_8.lean:112.
All 8 fail with GENUINE proof errors (rfl-failed / type-mismatch), none via sorry. NONE closes with clean axioms => protocol step 2 has no verifying attack to materialize/resolve; no resolve run was required or possible. prepatch_1 and prepatch_2 bugs both re-encoded and both fail (prepatch_reproduced=true).

REFINEMENT.MD AUDIT: No axiom is declared or consumed. Sole opaque `applyOrdering` (QuerySet.order_by) is I-tagged: proofs only ECHO it in the non-empty branch, assert no property — corroborated by clean #print axioms (no applyOrdering axiom). Every leg is R or I; NO kind-3, no A-consumed/A-reference leg exists, so no callee-axiom correspondence obligation. G-AX is a legitimate skip stub. The R/I legs are differential-tested by G-CONF (conformance_check.py present, uses REAL order_by / get_choices / RelatedOnlyFieldListFilter over full discrete matrix + 120k random draws, seed 20240629). Model-to-patch correspondence (mapping.md) is coherent: empty-directive => default order (objs), non-empty => applyOrdering, restricted layer forwards configuredOrdering — matches the gold guard fix.

VERDICT: SOUND. 8 distinct same-spec wrong impls (incl. both prepatch bugs) run through lean_verify concurrently (<=4 batches); all fail to close. Positive control verifies with clean axioms. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks pass: lean_verify.sh Solution.lean exit 0 (compiles, no sorry); #print axioms on both correct_orderedChoices and correct_restrictedChoices = [propext, Quot.sound] only (no sorryAx; opaque applyOrdering never leaks into axiom set); patch_equals_gold=True; region hashes present. Faithfulness traced against real repo @ base 1f8382d34d: (1) QuerySet.order_by (query.py:1073) with empty args -> clear_ordering(force_empty=False) then add_ordering() which sets default_ordering=False (sql/query.py:1858-1884), clearing Meta.ordering — exactly the bug mechanism the spec captures by making the empty-directive result the default-order carrier `objs` and NEVER routing through applyOrdering []; (2) Field.get_choices (fields/__init__.py:809-831) and ForeignObjectRel.get_choices (reverse_related.py:117-127) both call .order_by(*ordering) unconditionally pre-patch, gold guards on `if ordering:` <-> spec `if ordering != []` under tuple()->List String bijection; (3) RelatedOnlyFieldListFilter.field_choices (filters.py:419-422) omits ordering kwarg pre-patch, gold forwards field_admin_ordering(...) <-> configuredOrdering adminOrdering = adminOrdering.getD [] with Option bijection none->[] / some xs->xs. The non-empty-directive branch leaves applyOrdering fully opaque (asserts nothing about the sorted result) so it cannot over-constrain the real order_by; toChoice abstracts (choice_func(x)/x.pk, str(x)) via opaque carriers so no key/label input diverges; complex_filter/limit_choices_to restriction is an input carrier (objs), not a modeled op, adding no strength. Searched for a spec-too-strong diverging input across the blank prefix (exact Boolean bijection), empty-directive branch (matches default-order preservation), and non-empty branch (opaque) — none exists. Spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures) and same_spec holds across both prepatch variants. Semantic review of the spec view (impl+proof regions elided): the docstring and the two problem_spec_* definitions state the required behavior purely abstractly — empty ordering directive preserves the collection's default presentation order (spec: `if ordering = [] then objs else applyOrdering ordering objs`), and the restricted listing must honor the configured ordering (`configuredOrdering adminOrdering`) rather than discard it. This is exactly the behavior already disclosed by the public problem_statement, which names both bugs: RelatedFieldListFilter losing Model._meta.ordering when the ordering tuple is empty, and RelatedOnlyFieldListFilter omitting the ordering kwarg to field.get_choices. The spec view uses only abstract symbols (Obj, applyOrdering, configuredOrdering, orderedChoices, restrictedChoices) and does NOT quote gold-patch specifics (field_admin_ordering, get_choices, order_by, complex_filter, _default_manager, the `if ordering:` guard) — those appear only in mapping.md/refinement.md, which are auditor documents, not the consumer spec view. No spec-view line reconstructs the gold edit's structure beyond the public problem_statement. No hints_text content was relied upon. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
