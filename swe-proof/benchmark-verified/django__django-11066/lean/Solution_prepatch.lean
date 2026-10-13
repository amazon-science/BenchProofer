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
  -- persisted WITHOUT naming an explicit destination, so the free router choice
  -- is consulted to pick the database the write lands on.
  let target := saveTarget routerChoice none
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
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
