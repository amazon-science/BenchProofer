# P2 adversarial audit — django__django-15561

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_requiresColumnChange pins `result` to a TOTAL boolean equality over both inputs: result = ((quoteIdentifier old.column != quoteIdentifier new.column) || decide((old.path,old.args,popAttrs old.kwargs) != (new.path,new.args,popAttrs new.kwargs))). Any closing impl is therefore pointwise-equal to gold and resolves identically. The prepatch bug (omit "choices" from the popped set) does NOT close (atk_1, exit 1): on a choices-only change the spec pops choices from both -> equal triples, equal columns -> demands result=false, but that impl retains the differing choices kwarg -> true. No closing-but-non-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,14 +89,13 @@
 def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
   let mut oldKwargs := old.kwargs
   let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
+  for attr in otherNonColumnAttrs do
     oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
+  for attr in otherNonColumnAttrs do
     newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
   return (quoteIdentifier old.column != quoteIdentifier new.column) ||
          decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,17 +86,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
-  let mut oldKwargs := old.kwargs
-  let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
-    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
-    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
-  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
-         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
+def implementation_requiresColumnChange (old new : FieldDesc) : Bool :=
+  decide ((old.path, old.args, popAttrs old.kwargs) ≠ (new.path, new.args, popAttrs new.kwargs))
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,17 +86,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
-  let mut oldKwargs := old.kwargs
-  let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
-    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
-    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
-  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
-         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
+def implementation_requiresColumnChange (old new : FieldDesc) : Bool :=
+  (quoteIdentifier old.column != quoteIdentifier new.column) ||
+  decide ((old.path, old.args, popAttrs old.kwargs) ≠ (new.path, new.args, new.kwargs))
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,17 +86,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
-  let mut oldKwargs := old.kwargs
-  let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
-    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
-    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
-  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
-         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
+def implementation_requiresColumnChange (old new : FieldDesc) : Bool :=
+  (quoteIdentifier old.column != quoteIdentifier new.column) &&
+  decide ((old.path, old.args, popAttrs old.kwargs) ≠ (new.path, new.args, popAttrs new.kwargs))
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,17 +86,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
-  let mut oldKwargs := old.kwargs
-  let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
-    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
-    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
-  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
-         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
+def implementation_requiresColumnChange (old new : FieldDesc) : Bool := true
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,17 +86,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
-  let mut oldKwargs := old.kwargs
-  let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
-    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
-    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
-  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
-         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
+def implementation_requiresColumnChange (old new : FieldDesc) : Bool :=
+  let drop := "max_length" :: ignoredAttrs
+  let popX := fun (kw : List (String × String)) => kw.filter (fun kv => !drop.contains kv.1)
+  (quoteIdentifier old.column != quoteIdentifier new.column) ||
+  decide ((old.path, old.args, popX old.kwargs) ≠ (new.path, new.args, popX new.kwargs))
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -86,17 +86,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
-  let mut oldKwargs := old.kwargs
-  let mut newKwargs := new.kwargs
-  for attr in ignoredAttrs do
-    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
-  for attr in ignoredAttrs do
-    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
-  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
-         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
+def implementation_requiresColumnChange (old new : FieldDesc) : Bool :=
+  (quoteIdentifier old.column != quoteIdentifier new.column) ||
+  decide ((old.path, old.args, popAttrs old.kwargs) ≠ (new.path, new.args, popAttrs new.kwargs))
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresColumnChange :
@@ -104,22 +97,5 @@
       problem_spec_requiresColumnChange old new
         (implementation_requiresColumnChange old new) := by
   intro old new
-  unfold problem_spec_requiresColumnChange implementation_requiresColumnChange
-  simp only [Id.run, bind, pure]
-  have key : ∀ (attrs : List String) (kw : List (String × String)),
-      (forIn (m := Id) attrs kw (fun attr r => ForInStep.yield (List.filter (fun kv => kv.1 != attr) r)))
-      = kw.filter (fun kv => !attrs.contains kv.1) := by
-    intro attrs kw
-    induction attrs generalizing kw with
-    | nil => simp; rfl
-    | cons a rest ih =>
-      simp only [List.forIn_cons]
-      show forIn rest (List.filter (fun kv => kv.1 != a) kw) _ = _
-      rw [ih, List.filter_filter]
-      congr 1
-      funext kv
-      simp only [List.contains_cons, Bool.not_or, bne]
-      rw [Bool.and_comm]
-  simp only [key, popAttrs, isIgnored]
-
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether altering one model field into another requires a column-level
schema change.

A field is described, for this decision, by:

  * the database column it occupies,
  * a class path and a list of positional construction arguments, and
  * a list of keyword construction arguments (attribute name → value),

obtained by deconstructing the field. Changing a field into another requires a
column-level schema change exactly when either

  * the (backend-quoted) column name changes, or
  * the two field descriptions still differ after dropping the keyword
    arguments that correspond to attributes which do not affect the column
    definition.

The second clause is the point of interest: certain field attributes are purely
presentational or validation-level and have no bearing on the stored column. A
change touching only such attributes must NOT require a column change — in
particular, a change that only adjusts a field's set of permitted `choices`. The
keyword arguments naming any column-irrelevant attribute are removed from both
descriptions before they are compared.
-/

-- axioms-start
/-- A backend identifier-quoting function (quotes a column name for use in SQL).
Unchanged by the behavior under specification and applied identically on both
sides of the column-name comparison, so no property of it is consumed. -/
opaque quoteIdentifier : String → String

/-- The other attribute names — apart from `choices`, treated below — whose
keyword arguments are already understood not to affect the column definition.
This is a stable set the behavior under specification does not itself revise; it
is modeled abstractly because only its membership is ever queried. -/
opaque otherNonColumnAttrs : List String
-- axioms-end

-- pure-start
/-- A field, observed through the components the alteration decision reads: the
database column it occupies, plus its deconstruction into a class path, a list of
positional arguments, and a list of keyword arguments (attribute name → value).
The deconstruction's leading name slot is never read by the decision and is not
modeled. -/
structure FieldDesc where
  /-- the database column the field occupies -/
  column : String
  /-- the field class import path produced by deconstruction -/
  path : String
  /-- positional construction arguments (canonical reprs) -/
  args : List String
  /-- keyword construction arguments: attribute name → canonical repr of value -/
  kwargs : List (String × String)
deriving DecidableEq, Repr

/-- Attribute names whose keyword arguments do not affect the column definition,
and so are dropped from both field descriptions before they are compared. The
permitted-`choices` attribute is among them, alongside the other stable
column-irrelevant attributes. -/
def ignoredAttrs : List String := "choices" :: otherNonColumnAttrs

/-- An attribute name is ignored when it is among `ignoredAttrs`. -/
def isIgnored (name : String) : Bool := ignoredAttrs.contains name

/-- Drop from `kwargs` every keyword argument whose attribute name is ignored. -/
def popAttrs (kwargs : List (String × String)) : List (String × String) :=
  kwargs.filter (fun kv => !isIgnored kv.1)
-- pure-end

-- post-conditions-start
/-- `result` is `true` exactly when altering `old` into `new` requires a
column-level schema change: either the quoted column name differs, or the field
descriptions still differ after dropping the column-irrelevant keyword arguments
from BOTH descriptions (directive 5 frame: `result` is pinned to the inputs in
full; directive 8: grounded in `quoteIdentifier`/`path`/`args`/`kwargs`, no
oracle). -/
def problem_spec_requiresColumnChange (old new : FieldDesc) (result : Bool) : Prop :=
  result =
    ((quoteIdentifier old.column != quoteIdentifier new.column) ||
     decide ((old.path, old.args, popAttrs old.kwargs) ≠
             (new.path, new.args, popAttrs new.kwargs)))
-- post-conditions-end

-- impl-start
def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
  let mut oldKwargs := old.kwargs
  let mut newKwargs := new.kwargs
  for attr in ignoredAttrs do
    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
  for attr in ignoredAttrs do
    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
-- impl-end


-- proof-start
theorem correct_requiresColumnChange :
    ∀ (old new : FieldDesc),
      problem_spec_requiresColumnChange old new
        (implementation_requiresColumnChange old new) := by
  intro old new
  unfold problem_spec_requiresColumnChange implementation_requiresColumnChange
  simp only [Id.run, bind, pure]
  have key : ∀ (attrs : List String) (kw : List (String × String)),
      (forIn (m := Id) attrs kw (fun attr r => ForInStep.yield (List.filter (fun kv => kv.1 != attr) r)))
      = kw.filter (fun kv => !attrs.contains kv.1) := by
    intro attrs kw
    induction attrs generalizing kw with
    | nil => simp; rfl
    | cons a rest ih =>
      simp only [List.forIn_cons]
      show forIn rest (List.filter (fun kv => kv.1 != a) kw) _ = _
      rw [ih, List.filter_filter]
      congr 1
      funext kv
      simp only [List.contains_cons, Bool.not_or, bne]
      rw [Bool.and_comm]
  simp only [key, popAttrs, isIgnored]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (7 attacks, all same_spec=True; verified concurrently, <=4 background jobs). Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`.

### Results
- atk_1 (prepatch bug: pop only otherNonColumnAttrs, omit "choices"): exit=1 (unsolved goals) -> does NOT close. Prepatch reproduced.
- atk_2 (partial-domain: drop quoteIdentifier column clause): exit=1 -> does NOT close.
- atk_3 (boundary/asymmetric: pop ignored attrs from old only, not new): exit=1 -> does NOT close.
- atk_4 (control-flow-effect: || replaced with &&): exit=1 -> does NOT close.
- atk_5 (ungrounded-oracle echo: const `true`, ignore inputs): exit=1 -> does NOT close.
- atk_6 (extra-ignored: also drop column-relevant "max_length" from both): exit=1 (unsolved goals) -> does NOT close.
- atk_7 (behaviorally-identical echo of gold: direct popAttrs form, proof `rfl`): exit=0 CLOSES. `#print axioms` -> 'does not depend on any axioms' (CLEAN, no sorryAx). Per protocol step 2, materialized its faithful refined patch (== gold patch, since behaviorally identical) and RAN run_resolve: ResolveResult(resolved=True, completed=True, note='resolved', attempts=1). FAIL_TO_PASS test_alter_field_choices_noop PASS; all PASS_TO_PASS pass. A resolving echo is NOT a break.
- positive_control pos_gold (committed Solution.lean): exit=0, `#print axioms` -> [propext, Quot.sound] (clean, standard Mathlib). Gold patch resolves (same run as atk_7).

Only the behaviorally-identical echo closes; every genuinely-divergent impl fails to verify. No closing-but-non-resolving impl found.

REFINEMENT.MD AUDIT: legs 1(R FieldDesc<->Field via deconstruct, name slot dropped), 2/3(I the fixed pop-loop; ignoredAttrs="choices"::otherNonColumnAttrs matches post-patch non_db_attrs, verified vs base-commit 6991880109 source where prepatch non_database_attrs OMITS "choices" and patch prepends it), 4(A-reference quoteIdentifier<->quote_name applied identically both sides of != in spec AND impl -> cancels, no property consumed; meta axioms:[] and #print axioms confirm no quoteIdentifier_prop), 5(I structural tuple !=), 6(R Bool ||). NO kind-3 legs. deep_model_references=['quoteIdentifier'] matches; otherNonColumnAttrs is opaque/universally-quantified so proof holds for all values (tightens spec). A-reference correspondence holds.

HARNESS NOTE: run_resolve required docker group; first attempt failed completed=False (session shell lacked docker group in active creds); re-ran under `docker` -> completed=True, resolved=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_requiresColumnChange pins `result` to a TOTAL boolean equality over both inputs: result = ((quoteIdentifier old.column != quoteIdentifier new.column) || decide((old.path,old.args,popAttrs old.kwargs) != (new.path,new.args,popAttrs new.kwargs))). Any closing impl is therefore pointwise-equal to gold and resolves identically. The prepatch bug (omit "choices" from the popped set) does NOT close (atk_1, exit 1): on a choices-only change the spec pops choices from both -> equal triples, equal columns -> demands result=false, but that impl retains the differing choices kwarg -> true. No closing-but-non-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether altering one model field into another requires a column-level
schema change.

A field is described, for this decision, by:

  * the database column it occupies,
  * a class path and a list of positional construction arguments, and
  * a list of keyword construction arguments (attribute name → value),

obtained by deconstructing the field. Changing a field into another requires a
column-level schema change exactly when either

  * the (backend-quoted) column name changes, or
  * the two field descriptions still differ after dropping the keyword
    arguments that correspond to attributes which do not affect the column
    definition.

The second clause is the point of interest: certain field attributes are purely
presentational or validation-level and have no bearing on the stored column. A
change touching only such attributes must NOT require a column change — in
particular, a change that only adjusts a field's set of permitted `choices`. The
keyword arguments naming any column-irrelevant attribute are removed from both
descriptions before they are compared.
-/

-- axioms-start
/-- A backend identifier-quoting function (quotes a column name for use in SQL).
Unchanged by the behavior under specification and applied identically on both
sides of the column-name comparison, so no property of it is consumed. -/
opaque quoteIdentifier : String → String

/-- The other attribute names — apart from `choices`, treated below — whose
keyword arguments are already understood not to affect the column definition.
This is a stable set the behavior under specification does not itself revise; it
is modeled abstractly because only its membership is ever queried. -/
opaque otherNonColumnAttrs : List String
-- axioms-end

-- pure-start
/-- A field, observed through the components the alteration decision reads: the
database column it occupies, plus its deconstruction into a class path, a list of
positional arguments, and a list of keyword arguments (attribute name → value).
The deconstruction's leading name slot is never read by the decision and is not
modeled. -/
structure FieldDesc where
  /-- the database column the field occupies -/
  column : String
  /-- the field class import path produced by deconstruction -/
  path : String
  /-- positional construction arguments (canonical reprs) -/
  args : List String
  /-- keyword construction arguments: attribute name → canonical repr of value -/
  kwargs : List (String × String)
deriving DecidableEq, Repr

/-- Attribute names whose keyword arguments do not affect the column definition,
and so are dropped from both field descriptions before they are compared. The
permitted-`choices` attribute is among them, alongside the other stable
column-irrelevant attributes. -/
def ignoredAttrs : List String := "choices" :: otherNonColumnAttrs

/-- An attribute name is ignored when it is among `ignoredAttrs`. -/
def isIgnored (name : String) : Bool := ignoredAttrs.contains name

/-- Drop from `kwargs` every keyword argument whose attribute name is ignored. -/
def popAttrs (kwargs : List (String × String)) : List (String × String) :=
  kwargs.filter (fun kv => !isIgnored kv.1)
-- pure-end

-- post-conditions-start
/-- `result` is `true` exactly when altering `old` into `new` requires a
column-level schema change: either the quoted column name differs, or the field
descriptions still differ after dropping the column-irrelevant keyword arguments
from BOTH descriptions (directive 5 frame: `result` is pinned to the inputs in
full; directive 8: grounded in `quoteIdentifier`/`path`/`args`/`kwargs`, no
oracle). -/
def problem_spec_requiresColumnChange (old new : FieldDesc) (result : Bool) : Prop :=
  result =
    ((quoteIdentifier old.column != quoteIdentifier new.column) ||
     decide ((old.path, old.args, popAttrs old.kwargs) ≠
             (new.path, new.args, popAttrs new.kwargs)))
-- post-conditions-end

-- impl-start
def implementation_requiresColumnChange (old new : FieldDesc) : Bool := Id.run do
  let mut oldKwargs := old.kwargs
  let mut newKwargs := new.kwargs
  for attr in ignoredAttrs do
    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)
  for attr in ignoredAttrs do
    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)
  return (quoteIdentifier old.column != quoteIdentifier new.column) ||
         decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))
-- impl-end


-- proof-start
theorem correct_requiresColumnChange :
    ∀ (old new : FieldDesc),
      problem_spec_requiresColumnChange old new
        (implementation_requiresColumnChange old new) := by
  intro old new
  unfold problem_spec_requiresColumnChange implementation_requiresColumnChange
  simp only [Id.run, bind, pure]
  have key : ∀ (attrs : List String) (kw : List (String × String)),
      (forIn (m := Id) attrs kw (fun attr r => ForInStep.yield (List.filter (fun kv => kv.1 != attr) r)))
      = kw.filter (fun kv => !attrs.contains kv.1) := by
    intro attrs kw
    induction attrs generalizing kw with
    | nil => simp; rfl
    | cons a rest ih =>
      simp only [List.forIn_cons]
      show forIn rest (List.filter (fun kv => kv.1 != a) kw) _ = _
      rw [ih, List.filter_filter]
      congr 1
      funext kv
      simp only [List.contains_cons, Bool.not_or, bne]
      rw [Bool.and_comm]
  simp only [key, popAttrs, isIgnored]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (7 attacks, all same_spec=True; verified concurrently, <=4 background jobs). Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`.

### Results
- atk_1 (prepatch bug: pop only otherNonColumnAttrs, omit "choices"): exit=1 (unsolved goals) -> does NOT close. Prepatch reproduced.
- atk_2 (partial-domain: drop quoteIdentifier column clause): exit=1 -> does NOT close.
- atk_3 (boundary/asymmetric: pop ignored attrs from old only, not new): exit=1 -> does NOT close.
- atk_4 (control-flow-effect: || replaced with &&): exit=1 -> does NOT close.
- atk_5 (ungrounded-oracle echo: const `true`, ignore inputs): exit=1 -> does NOT close.
- atk_6 (extra-ignored: also drop column-relevant "max_length" from both): exit=1 (unsolved goals) -> does NOT close.
- atk_7 (behaviorally-identical echo of gold: direct popAttrs form, proof `rfl`): exit=0 CLOSES. `#print axioms` -> 'does not depend on any axioms' (CLEAN, no sorryAx). Per protocol step 2, materialized its faithful refined patch (== gold patch, since behaviorally identical) and RAN run_resolve: ResolveResult(resolved=True, completed=True, note='resolved', attempts=1). FAIL_TO_PASS test_alter_field_choices_noop PASS; all PASS_TO_PASS pass. A resolving echo is NOT a break.
- positive_control pos_gold (committed Solution.lean): exit=0, `#print axioms` -> [propext, Quot.sound] (clean, standard Mathlib). Gold patch resolves (same run as atk_7).

Only the behaviorally-identical echo closes; every genuinely-divergent impl fails to verify. No closing-but-non-resolving impl found.

REFINEMENT.MD AUDIT: legs 1(R FieldDesc<->Field via deconstruct, name slot dropped), 2/3(I the fixed pop-loop; ignoredAttrs="choices"::otherNonColumnAttrs matches post-patch non_db_attrs, verified vs base-commit 6991880109 source where prepatch non_database_attrs OMITS "choices" and patch prepends it), 4(A-reference quoteIdentifier<->quote_name applied identically both sides of != in spec AND impl -> cancels, no property consumed; meta axioms:[] and #print axioms confirm no quoteIdentifier_prop), 5(I structural tuple !=), 6(R Bool ||). NO kind-3 legs. deep_model_references=['quoteIdentifier'] matches; otherNonColumnAttrs is opaque/universally-quantified so proof holds for all values (tightens spec). A-reference correspondence holds.

HARNESS NOTE: run_resolve required docker group; first attempt failed completed=False (session shell lacked docker group in active creds); re-ran under `docker` -> completed=True, resolved=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of the modeled function BaseDatabaseSchemaEditor._field_should_be_altered (django/db/backends/base/schema.py) for django__django-15561.

Mechanical checks (all clean):
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_requiresColumnChange` -> [propext, Quot.sound]; NO sorryAx, no consumed custom axiom. quoteIdentifier / otherNonColumnAttrs are `opaque` (not axioms) and do not appear.
- swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) -> True (spec region byte-identical between patched and prepatch).
- Real base-commit (dj15561_src @ 6991880109) confirms pre-patch `non_database_attrs` = 11 attrs WITHOUT `choices`; gold patch adds `choices` to Field.non_db_attrs -> matches `ignoredAttrs = "choices" :: otherNonColumnAttrs`.

Real-callee differential (the decisive faithfulness test): I applied the actual gold patch to a base-commit Django checkout (added Field.non_db_attrs incl. `choices`; rewrote the pop loops to iterate old/new_field.non_db_attrs) and ran the REAL post-patch _field_should_be_altered against the spec's fully-determined result computed as the list-based model (popAttrs filtering IGNORED = choices + others, order-sensitive list eq over deconstruct order):
  * 14 hand-picked cases incl. the F2P choices-only noop, db_column add==name, type change, null/blank/help_text/verbose_name/validators diffs -> ALL agree.
  * 4000 random mixed CharField/IntegerField pairs -> 0 mismatches.
  * 6000 same-class CharField kwarg-subset fuzz -> 0 mismatches.
  * Verified deconstruct() yields deterministic per-class key order for every kwarg subset, validating the documented list-vs-dict ordering modeling assumption (list-eq coincides with dict content-eq on the modeled same-class domain; cross-class changes make `path` differ so kwarg order is irrelevant).

The spec's `result` agrees with the real repo callee on every input tested, including the discriminating choices-only change (result=false). otherNonColumnAttrs is opaque/universally quantified, so the theorem holds for the concrete real 11-attr set -> the spec is never weaker than real code (strictly faithful). quoteIdentifier is the unchanged callee quote_name applied identically on both sides (A-reference, cancels; no property consumed). The only unmodeled behavior is a third-party subclass overriding non_db_attrs, which is a documented elidable corner exercised by no F2P/PASS test. No diverging input found. Spec is not too strong and does not drift from real behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms + pure + post-conditions) reveals only that a change touching ONLY a field's `choices` must be a no-op and that `choices` is among the column-irrelevant attributes dropped before comparison (`ignoredAttrs := "choices" :: otherNonColumnAttrs`). This is exactly the content of the PUBLIC problem_statement ('AlterField operation should be noop when adding/changing choices on SQLite'). Nothing goes beyond it: the rest of the gold patch's `non_database_attrs` tuple (blank, db_column, editable, error_messages, help_text, limit_choices_to, on_delete, related_name, related_query_name, validators, verbose_name) is modeled OPAQUELY as `otherNonColumnAttrs` and never enumerated; the code-level names (`non_database_attrs`/`Field.non_db_attrs`), ticket numbers, commit hashes, and SQLite-backend specifics — which live in hints_text/patch — do NOT appear in the spec view. The docstring uses abstract phrasing ('column-irrelevant', 'presentational or validation-level'), not gold-patch or hint phrasing. Construction was deliberate about this (notes: modeling the list opaquely 'keeps the spec view leak-clean'). Therefore the spec view does not disclose the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
