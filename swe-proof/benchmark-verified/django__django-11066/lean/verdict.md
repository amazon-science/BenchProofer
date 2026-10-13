# P2 adversarial audit — django__django-11066

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,15 +117,9 @@
     (world : Alias → List ContentTypeRec)
     (db routerChoice : Alias)
     (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
-  -- Locate the record on the connection this operation is running against.
   if !hasKey (world db) appLabel oldModel then
     return world
-  -- The located record's model-name identity is updated and the change is
-  -- persisted to the connection the operation is running against.
-  let target := saveTarget routerChoice (some db)
-  -- The database receiving the write enforces the unique natural-key
-  -- constraint; a colliding rename is rejected and the surrounding
-  -- transaction rolls it back, so nothing is persisted anywhere.
+  let target := saveTarget routerChoice none
   if renameConflicts (world target) appLabel oldModel newModel then
     return world
   let mut updated := world
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,17 +117,9 @@
     (world : Alias → List ContentTypeRec)
     (db routerChoice : Alias)
     (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
-  -- Locate the record on the connection this operation is running against.
   if !hasKey (world db) appLabel oldModel then
     return world
-  -- The located record's model-name identity is updated and the change is
-  -- persisted to the connection the operation is running against.
   let target := saveTarget routerChoice (some db)
-  -- The database receiving the write enforces the unique natural-key
-  -- constraint; a colliding rename is rejected and the surrounding
-  -- transaction rolls it back, so nothing is persisted anywhere.
-  if renameConflicts (world target) appLabel oldModel newModel then
-    return world
   let mut updated := world
   updated := fun a =>
     if a = target then renameInStore (world target) appLabel oldModel newModel
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,21 +117,13 @@
     (world : Alias → List ContentTypeRec)
     (db routerChoice : Alias)
     (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
-  -- Locate the record on the connection this operation is running against.
   if !hasKey (world db) appLabel oldModel then
     return world
-  -- The located record's model-name identity is updated and the change is
-  -- persisted to the connection the operation is running against.
   let target := saveTarget routerChoice (some db)
-  -- The database receiving the write enforces the unique natural-key
-  -- constraint; a colliding rename is rejected and the surrounding
-  -- transaction rolls it back, so nothing is persisted anywhere.
   if renameConflicts (world target) appLabel oldModel newModel then
     return world
   let mut updated := world
-  updated := fun a =>
-    if a = target then renameInStore (world target) appLabel oldModel newModel
-    else world a
+  updated := fun a => renameInStore (world a) appLabel oldModel newModel
   return updated
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,21 +117,15 @@
     (world : Alias → List ContentTypeRec)
     (db routerChoice : Alias)
     (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
-  -- Locate the record on the connection this operation is running against.
   if !hasKey (world db) appLabel oldModel then
     return world
-  -- The located record's model-name identity is updated and the change is
-  -- persisted to the connection the operation is running against.
   let target := saveTarget routerChoice (some db)
-  -- The database receiving the write enforces the unique natural-key
-  -- constraint; a colliding rename is rejected and the surrounding
-  -- transaction rolls it back, so nothing is persisted anywhere.
   if renameConflicts (world target) appLabel oldModel newModel then
     return world
   let mut updated := world
   updated := fun a =>
-    if a = target then renameInStore (world target) appLabel oldModel newModel
-    else world a
+    if a = target then world a
+    else renameInStore (world a) appLabel oldModel newModel
   return updated
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,20 +117,14 @@
     (world : Alias → List ContentTypeRec)
     (db routerChoice : Alias)
     (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
-  -- Locate the record on the connection this operation is running against.
   if !hasKey (world db) appLabel oldModel then
     return world
-  -- The located record's model-name identity is updated and the change is
-  -- persisted to the connection the operation is running against.
   let target := saveTarget routerChoice (some db)
-  -- The database receiving the write enforces the unique natural-key
-  -- constraint; a colliding rename is rejected and the surrounding
-  -- transaction rolls it back, so nothing is persisted anywhere.
   if renameConflicts (world target) appLabel oldModel newModel then
     return world
   let mut updated := world
   updated := fun a =>
-    if a = target then renameInStore (world target) appLabel oldModel newModel
+    if a = target then renameInStore (world target) appLabel newModel oldModel
     else world a
   return updated
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,22 +117,7 @@
     (world : Alias → List ContentTypeRec)
     (db routerChoice : Alias)
     (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
-  -- Locate the record on the connection this operation is running against.
-  if !hasKey (world db) appLabel oldModel then
-    return world
-  -- The located record's model-name identity is updated and the change is
-  -- persisted to the connection the operation is running against.
-  let target := saveTarget routerChoice (some db)
-  -- The database receiving the write enforces the unique natural-key
-  -- constraint; a colliding rename is rejected and the surrounding
-  -- transaction rolls it back, so nothing is persisted anywhere.
-  if renameConflicts (world target) appLabel oldModel newModel then
-    return world
-  let mut updated := world
-  updated := fun a =>
-    if a = target then renameInStore (world target) appLabel oldModel newModel
-    else world a
-  return updated
+  return world
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Renaming a record's model-name identity inside a multi-database world.

The setting is a collection of independent databases, each identified by an
alias and each holding its own list of records. A record carries two observable
fields: the application label it belongs to and its model-name identity. A
single natural key `(appLabel, model)` locates a record within one database.

A rename operation runs against ONE designated database `db` (the connection the
operation is executing on). It:

  * locates, within `db`, the record whose natural key is `(appLabel, oldModel)`;
  * if no such record exists in `db`, leaves every database untouched;
  * otherwise updates that record's model-name identity from `oldModel` to
    `newModel`, and the update must be persisted to the SAME database the record
    was located in — i.e. to `db` itself.

Each database enforces uniqueness of the natural key `(appLabel, model)`. If
persisting the rename would collide with a record already carrying the
destination key `(appLabel, newModel)` (with `newModel` genuinely different
from `oldModel`), the write is rejected and rolled back: every database is
left untouched.

A persistence layer may, when not told otherwise, choose a destination database
on its own (here represented by `routerChoice`). The desired behavior is that
the rename always lands on `db`, regardless of any such free choice: the result
depends only on `db`, never on `routerChoice`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both the
-- destination-selection decision and the record update are modeled structurally
-- over the data (the alias, the optional explicit destination, and the records'
-- natural keys), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A database connection alias. Modeled as a `Nat` identity (an injective
encoding of the distinct alias strings; only equality is observed). -/
abbrev Alias := Nat

/-- One record, restricted to the touched fields:
* `appLabel` — the application label the record belongs to;
* `model` — the record's model-name identity. -/
structure ContentTypeRec where
  appLabel : Nat
  model : Nat
deriving DecidableEq

/-- Whether a record is the one located by the natural key `(appLabel, oldModel)`. -/
def matchesKey (appLabel oldModel : Nat) (r : ContentTypeRec) : Bool :=
  r.appLabel == appLabel && r.model == oldModel

/-- Whether a database's record list contains the natural key `(appLabel, oldModel)`. -/
def hasKey (store : List ContentTypeRec) (appLabel oldModel : Nat) : Bool :=
  store.any (matchesKey appLabel oldModel)

/-- Apply the rename inside one database's record list: the record(s) carrying
the natural key `(appLabel, oldModel)` get their model-name identity set to
`newModel`; every other record is left exactly as it was. (Natural keys are
unique, so at most one record is affected; see mapping.md.) -/
def renameInStore (store : List ContentTypeRec)
    (appLabel oldModel newModel : Nat) : List ContentTypeRec :=
  store.map (fun r => if matchesKey appLabel oldModel r then { r with model := newModel } else r)

/-- The database a persisted write lands on: an explicit destination (`some d`)
is used as given; absent an explicit destination (`none`), the free
`routerChoice` is used instead. -/
def saveTarget (routerChoice : Alias) (using? : Option Alias) : Alias :=
  match using? with
  | some d => d
  | none   => routerChoice

/-- Whether persisting the rename into `store` violates the unique
natural-key constraint: the rename targets a genuinely different model name
(`newModel ≠ oldModel`) while `store` already holds a record with the
destination key `(appLabel, newModel)`. Such a write is rejected and rolled
back, so nothing is persisted anywhere. -/
def renameConflicts (store : List ContentTypeRec)
    (appLabel oldModel newModel : Nat) : Bool :=
  newModel != oldModel && hasKey store appLabel newModel
-- pure-end

-- post-conditions-start
/-- The resulting world, pinned at every alias. When `db` contains the record
named by `(appLabel, oldModel)` and persisting the rename to `db` does NOT
collide with `db`'s unique natural-key constraint, the rename is applied to
`db`'s record list and to it ALONE — every other database is identical to its
input, and the outcome is independent of `routerChoice`. When the rename WOULD
collide (a record keyed `(appLabel, newModel)` already lives in `db` and
`newModel ≠ oldModel`), the write is rejected and rolled back: every database
is identical to its input. When `db` contains no `(appLabel, oldModel)` record,
every database is identical to its input. -/
def problem_spec_renameContentType
    (world : Alias → List ContentTypeRec)
    (db routerChoice : Alias)
    (appLabel oldModel newModel : Nat)
    (result : Alias → List ContentTypeRec) : Prop :=
  ∀ a,
    result a =
      if hasKey (world db) appLabel oldModel then
        if renameConflicts (world db) appLabel oldModel newModel then
          world a
        else if a = db then
          renameInStore (world db) appLabel oldModel newModel
        else
          world a
      else
        world a
-- post-conditions-end

-- impl-start
def implementation_renameContentType
    (world : Alias → List ContentTypeRec)
    (db routerChoice : Alias)
    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
  -- Locate the record on the connection this operation is running against.
  if !hasKey (world db) appLabel oldModel then
    return world
  -- The located record's model-name identity is updated and the change is
  -- persisted to the connection the operation is running against.
  let target := saveTarget routerChoice (some db)
  -- The database receiving the write enforces the unique natural-key
  -- constraint; a colliding rename is rejected and the surrounding
  -- transaction rolls it back, so nothing is persisted anywhere.
  if renameConflicts (world target) appLabel oldModel newModel then
    return world
  let mut updated := world
  updated := fun a =>
    if a = target then renameInStore (world target) appLabel oldModel newModel
    else world a
  return updated
-- impl-end

-- proof-start
theorem correct_renameContentType :
    ∀ (world : Alias → List ContentTypeRec) (db routerChoice : Alias)
      (appLabel oldModel newModel : Nat),
      problem_spec_renameContentType world db routerChoice appLabel oldModel newModel
        (implementation_renameContentType world db routerChoice appLabel oldModel newModel) := by
  intro world db routerChoice appLabel oldModel newModel a
  show implementation_renameContentType world db routerChoice appLabel oldModel newModel a = _
  by_cases h : hasKey (world db) appLabel oldModel
  · by_cases hc : renameConflicts (world db) appLabel oldModel newModel
    · simp only [implementation_renameContentType, saveTarget, Id.run, h, hc,
        Bool.not_true, Bool.false_eq_true, if_false, if_true]
      rfl
    · simp only [implementation_renameContentType, saveTarget, Id.run, h, hc,
        Bool.not_true, Bool.false_eq_true, if_false, if_true]
      rfl
  · simp only [implementation_renameContentType, saveTarget, Id.run, h,
      Bool.not_false, if_true, Bool.false_eq_true, if_false]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-11066 (lean). Spec problem_spec_renameContentType pins result a for ALL aliases a via total pointwise equality to a fully input-grounded expression; axioms region is EMPTY (no opaque/axiom decls — confirmed by grep), so there are NO A-legs to audit (refinement.md 'no consumed axiom / deep-model' claim is vacuously safe). routerChoice never appears on the spec RHS ⇒ result pinned router-independent. Maximally tight spec.

All 6 attacks pass same_spec=True (edited impl region ONLY, axioms/pure/pre/post byte-identical), verified via python swebench_unified.markers.same_spec. Positive control pos.lean = gold Solution.lean.

Results:
- pos.lean exit=0 (verifies, no sorry; empty axioms region ⇒ clean #print axioms).
- atk_1 (prepatch bug: saveTarget routerChoice none — write routes to routerChoice; byte-identical to Solution_prepatch.lean impl): exit=1, genuine `rfl` failure at L144/147.
- atk_2 (drops renameConflicts guard — persists even on unique-key collision): exit=1, `rfl` failure L142.
- atk_3 (renames in EVERY database, not just target — frame violation): exit=1, `rfl` failure L145.
- atk_4 (control-flow-effect swap: renames everywhere EXCEPT target, leaves target untouched): exit=1, `rfl` failure L147.
- atk_5 (boundary: old/new swapped, renameInStore ... newModel oldModel): exit=1, `rfl` failure L147.
- atk_6 (ungrounded/degenerate echo: always `return world` identity): exit=1, `rfl` failure L138.

Every wrong impl's carried gold proof fails to close with a genuine `rfl` mismatch (not a syntax/timeout artifact — error text 'Tactic `rfl` failed: The left-hand side' in each). Because NO behaviorally-wrong impl produced a CLOSING clean-axiom proof, the resolve/patch-materialization step (triggered only by a closing proof) was correctly not required — patches={}. verify⇒correct holds against all 6 distinct attack classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug, frame-widening). Refinement.md audit: all legs R/I, no A-legs, no kind-3; consistent with empty axioms region. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Renaming a record's model-name identity inside a multi-database world.

The setting is a collection of independent databases, each identified by an
alias and each holding its own list of records. A record carries two observable
fields: the application label it belongs to and its model-name identity. A
single natural key `(appLabel, model)` locates a record within one database.

A rename operation runs against ONE designated database `db` (the connection the
operation is executing on). It:

  * locates, within `db`, the record whose natural key is `(appLabel, oldModel)`;
  * if no such record exists in `db`, leaves every database untouched;
  * otherwise updates that record's model-name identity from `oldModel` to
    `newModel`, and the update must be persisted to the SAME database the record
    was located in — i.e. to `db` itself.

Each database enforces uniqueness of the natural key `(appLabel, model)`. If
persisting the rename would collide with a record already carrying the
destination key `(appLabel, newModel)` (with `newModel` genuinely different
from `oldModel`), the write is rejected and rolled back: every database is
left untouched.

A persistence layer may, when not told otherwise, choose a destination database
on its own (here represented by `routerChoice`). The desired behavior is that
the rename always lands on `db`, regardless of any such free choice: the result
depends only on `db`, never on `routerChoice`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both the
-- destination-selection decision and the record update are modeled structurally
-- over the data (the alias, the optional explicit destination, and the records'
-- natural keys), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A database connection alias. Modeled as a `Nat` identity (an injective
encoding of the distinct alias strings; only equality is observed). -/
abbrev Alias := Nat

/-- One record, restricted to the touched fields:
* `appLabel` — the application label the record belongs to;
* `model` — the record's model-name identity. -/
structure ContentTypeRec where
  appLabel : Nat
  model : Nat
deriving DecidableEq

/-- Whether a record is the one located by the natural key `(appLabel, oldModel)`. -/
def matchesKey (appLabel oldModel : Nat) (r : ContentTypeRec) : Bool :=
  r.appLabel == appLabel && r.model == oldModel

/-- Whether a database's record list contains the natural key `(appLabel, oldModel)`. -/
def hasKey (store : List ContentTypeRec) (appLabel oldModel : Nat) : Bool :=
  store.any (matchesKey appLabel oldModel)

/-- Apply the rename inside one database's record list: the record(s) carrying
the natural key `(appLabel, oldModel)` get their model-name identity set to
`newModel`; every other record is left exactly as it was. (Natural keys are
unique, so at most one record is affected; see mapping.md.) -/
def renameInStore (store : List ContentTypeRec)
    (appLabel oldModel newModel : Nat) : List ContentTypeRec :=
  store.map (fun r => if matchesKey appLabel oldModel r then { r with model := newModel } else r)

/-- The database a persisted write lands on: an explicit destination (`some d`)
is used as given; absent an explicit destination (`none`), the free
`routerChoice` is used instead. -/
def saveTarget (routerChoice : Alias) (using? : Option Alias) : Alias :=
  match using? with
  | some d => d
  | none   => routerChoice

/-- Whether persisting the rename into `store` violates the unique
natural-key constraint: the rename targets a genuinely different model name
(`newModel ≠ oldModel`) while `store` already holds a record with the
destination key `(appLabel, newModel)`. Such a write is rejected and rolled
back, so nothing is persisted anywhere. -/
def renameConflicts (store : List ContentTypeRec)
    (appLabel oldModel newModel : Nat) : Bool :=
  newModel != oldModel && hasKey store appLabel newModel
-- pure-end

-- post-conditions-start
/-- The resulting world, pinned at every alias. When `db` contains the record
named by `(appLabel, oldModel)` and persisting the rename to `db` does NOT
collide with `db`'s unique natural-key constraint, the rename is applied to
`db`'s record list and to it ALONE — every other database is identical to its
input, and the outcome is independent of `routerChoice`. When the rename WOULD
collide (a record keyed `(appLabel, newModel)` already lives in `db` and
`newModel ≠ oldModel`), the write is rejected and rolled back: every database
is identical to its input. When `db` contains no `(appLabel, oldModel)` record,
every database is identical to its input. -/
def problem_spec_renameContentType
    (world : Alias → List ContentTypeRec)
    (db routerChoice : Alias)
    (appLabel oldModel newModel : Nat)
    (result : Alias → List ContentTypeRec) : Prop :=
  ∀ a,
    result a =
      if hasKey (world db) appLabel oldModel then
        if renameConflicts (world db) appLabel oldModel newModel then
          world a
        else if a = db then
          renameInStore (world db) appLabel oldModel newModel
        else
          world a
      else
        world a
-- post-conditions-end

-- impl-start
def implementation_renameContentType
    (world : Alias → List ContentTypeRec)
    (db routerChoice : Alias)
    (appLabel oldModel newModel : Nat) : Alias → List ContentTypeRec := Id.run do
  -- Locate the record on the connection this operation is running against.
  if !hasKey (world db) appLabel oldModel then
    return world
  -- The located record's model-name identity is updated and the change is
  -- persisted to the connection the operation is running against.
  let target := saveTarget routerChoice (some db)
  -- The database receiving the write enforces the unique natural-key
  -- constraint; a colliding rename is rejected and the surrounding
  -- transaction rolls it back, so nothing is persisted anywhere.
  if renameConflicts (world target) appLabel oldModel newModel then
    return world
  let mut updated := world
  updated := fun a =>
    if a = target then renameInStore (world target) appLabel oldModel newModel
    else world a
  return updated
-- impl-end

-- proof-start
theorem correct_renameContentType :
    ∀ (world : Alias → List ContentTypeRec) (db routerChoice : Alias)
      (appLabel oldModel newModel : Nat),
      problem_spec_renameContentType world db routerChoice appLabel oldModel newModel
        (implementation_renameContentType world db routerChoice appLabel oldModel newModel) := by
  intro world db routerChoice appLabel oldModel newModel a
  show implementation_renameContentType world db routerChoice appLabel oldModel newModel a = _
  by_cases h : hasKey (world db) appLabel oldModel
  · by_cases hc : renameConflicts (world db) appLabel oldModel newModel
    · simp only [implementation_renameContentType, saveTarget, Id.run, h, hc,
        Bool.not_true, Bool.false_eq_true, if_false, if_true]
      rfl
    · simp only [implementation_renameContentType, saveTarget, Id.run, h, hc,
        Bool.not_true, Bool.false_eq_true, if_false, if_true]
      rfl
  · simp only [implementation_renameContentType, saveTarget, Id.run, h,
      Bool.not_false, if_true, Bool.false_eq_true, if_false]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-11066 (lean). Spec problem_spec_renameContentType pins result a for ALL aliases a via total pointwise equality to a fully input-grounded expression; axioms region is EMPTY (no opaque/axiom decls — confirmed by grep), so there are NO A-legs to audit (refinement.md 'no consumed axiom / deep-model' claim is vacuously safe). routerChoice never appears on the spec RHS ⇒ result pinned router-independent. Maximally tight spec.

All 6 attacks pass same_spec=True (edited impl region ONLY, axioms/pure/pre/post byte-identical), verified via python swebench_unified.markers.same_spec. Positive control pos.lean = gold Solution.lean.

Results:
- pos.lean exit=0 (verifies, no sorry; empty axioms region ⇒ clean #print axioms).
- atk_1 (prepatch bug: saveTarget routerChoice none — write routes to routerChoice; byte-identical to Solution_prepatch.lean impl): exit=1, genuine `rfl` failure at L144/147.
- atk_2 (drops renameConflicts guard — persists even on unique-key collision): exit=1, `rfl` failure L142.
- atk_3 (renames in EVERY database, not just target — frame violation): exit=1, `rfl` failure L145.
- atk_4 (control-flow-effect swap: renames everywhere EXCEPT target, leaves target untouched): exit=1, `rfl` failure L147.
- atk_5 (boundary: old/new swapped, renameInStore ... newModel oldModel): exit=1, `rfl` failure L147.
- atk_6 (ungrounded/degenerate echo: always `return world` identity): exit=1, `rfl` failure L138.

Every wrong impl's carried gold proof fails to close with a genuine `rfl` mismatch (not a syntax/timeout artifact — error text 'Tactic `rfl` failed: The left-hand side' in each). Because NO behaviorally-wrong impl produced a CLOSING clean-axiom proof, the resolve/patch-materialization step (triggered only by a closing proof) was correctly not required — patches={}. verify⇒correct holds against all 6 distinct attack classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug, frame-widening). Refinement.md audit: all legs R/I, no A-legs, no kind-3; consistent with empty axioms region. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function renameContentType <-> RenameContentType._rename (django/contrib/contenttypes/management/__init__.py) at base 4b45b6c8, post-patch (save(using=db)). Checked the spec (problem_spec_renameContentType) against the real callee over the whole modeled input domain (world: Alias->List ContentTypeRec, db, routerChoice, appLabel, oldModel, newModel):

- Read on db (db_manager(db).get_by_natural_key) <-> hasKey (world db) appLabel oldModel; DoesNotExist -> unchanged, matches hasKey=false => world a.
- save(using=db) directs the write to db regardless of the router; spec pins result INDEPENDENT of routerChoice (routerChoice never appears on the spec RHS), impl uses saveTarget routerChoice (some db)=db. Correct.
- IntegrityError under transaction.atomic(using=db) => rollback, nothing persisted <-> renameConflicts (world db) = (newModel!=oldModel && hasKey (world db) appLabel newModel) => world a. Conflict is checked against db's store (the store receiving the write), correct. new==old is correctly a no-conflict no-op; a destination key present only on a non-db database correctly does NOT conflict.
- Update: content_type.model=new_model; save. Natural key (app_label,model) is unique so at most one row matches; renameInStore's map-over-all-matches is equivalent.

Not-too-strong check: the only real behavior the spec omits is the early guard `if not router.allow_migrate_model(db, ContentType): return`. This is a documented scoping precondition (unchanged by the patch; F2P/P2P tests run with migration allowed) and, crucially, the modeled input signature has NO slot to express 'migration disallowed', so no diverging input exists within the modeled domain. Every input the spec accepts, it constrains to exactly the real post-patch callee's output.

Verification: scripts/lean_verify.sh Solution.lean -> exit 0 (only unused-variable warning for routerChoice, expected: routing is router-independent post-fix). #print axioms correct_renameContentType -> [propext, Quot.sound], NO sorryAx (proof is genuine, not fake). same_spec(Solution, Solution_prepatch, lean backend) -> True (spec region byte-identical; only the impl-region target = saveTarget ... (some db) vs none differs). conformance_check.py -> checked=120011 disagreements=0, status=pass (differential vs in-process replica of patched _rename routing, incl. routerChoice!=db with row on db, DoesNotExist, non-db collision, and unique-key collision edge cases). No divergence found; spec is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard_failures). Spec regions byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec=True). Semantic review of the spec view (imports/docstring/axioms/pure/post-conditions regions; impl+proof are elided by the projection): (1) No diff markers, no gold-patch line reproduced, no patched file path/module path (django/contrib/contenttypes/management/__init__.py absent). (2) No narration terms (bug/fix/patch/etc.). (3) The only distinctive patched symbol is 'rename', which is embedded in identifiers (renameContentType, renameInStore, renameConflicts) — but 'rename'/'RenameContentType._rename' is already public in the problem_statement, so no leak beyond it. (4) Most importantly, the gold edit itself is FULLY disclosed by the public problem_statement, which states verbatim that content_type.save(update_fields={'model'}) 'should be' content_type.save(using=db, update_fields={'model'}) and that the write must land on the database from schema_editor.connection.alias rather than the router's default. The spec's postcondition — the rename always lands on `db` and the result is independent of `routerChoice` — is precisely the publicly-stated desired behavior, i.e. a faithful behavioral specification, not a disclosure beyond problem_statement. Leakage judged against problem_statement only (not hints_text). No spec-view line reveals the gold discriminator beyond what the task already states publicly.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
