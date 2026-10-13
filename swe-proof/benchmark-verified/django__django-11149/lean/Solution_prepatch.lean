import Mathlib
-- imports-end

/-!
Authorization for the implicit intermediary model of a many-to-many
relationship in an administrative interface.

An object editor may display the rows of an auto-created link model (the hidden
table that records which pairs of two related models are associated). Such a
link model has no permissions of its own, so the authority to act on its rows is
derived from permissions held on the *target* model — the related model that the
link points at (the one that is NOT the containing/parent model).

Two ingredients are involved.

* **Locating the target model.** The link model exposes a list of fields. The
  target model is identified by the first field that refers to a related model
  other than the parent model; its application label and model name are taken
  from that related model. If no such field exists, the link model's own labels
  are used.

* **Permission strings.** Permission to perform an action `a` on a model is
  expressed as the string `"<app_label>.<a>_<model_name>"`. A user holds a set
  of such permission strings; the user is authorized for action `a` exactly when
  that string is among the held permissions.

The authority required of each editor action, when operating on an auto-created
link model, is:

* **add**, **change**, **delete** — require the *change* permission on the target
  model;
* **view** — requires the *view* permission OR the *change* permission on the
  target model (the latter subsuming the former).

When the model is NOT an auto-created link model, each action defers to the
ordinary authorization decision supplied for that action (a caller-supplied input
here).

The behavior is stated abstractly as an input→output relation; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The user's effective set
-- of granted permission strings is supplied as the `userPerms` input (a
-- membership test against it stands in for the authorization lookup), the
-- per-action permission-string format is spelled out concretely below, and the
-- target-model resolution over the field list is modeled deeply.
-- axioms-end

-- pure-start
/-- One field of the link model, as far as target resolution is concerned.

* `hasRemote`        — whether the field refers to a related model at all;
* `remoteModelId`    — an identity tag for the related model it refers to (used
                        to tell it apart from the parent model);
* `remoteAppLabel`   — the application label of that related model;
* `remoteModelName`  — the model name of that related model. -/
structure LinkField where
  hasRemote : Bool
  remoteModelId : String
  remoteAppLabel : String
  remoteModelName : String
deriving Repr, DecidableEq

/-- The permission string for performing action `action` on the model named
`modelName` in application `appLabel`: `"<appLabel>.<action>_<modelName>"`. -/
def permString (appLabel modelName action : String) : String :=
  appLabel ++ "." ++ action ++ "_" ++ modelName

/-- Resolve the `(appLabel, modelName)` of the target model. It is taken from the
first field that refers to a related model whose identity differs from the parent
model; absent such a field, the link model's own `(selfAppLabel, selfModelName)`
is used. -/
def resolveTarget (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String :=
  match fields.find? (fun f => f.hasRemote && f.remoteModelId != parentModelId) with
  | some f => (f.remoteAppLabel, f.remoteModelName)
  | none => (selfAppLabel, selfModelName)

/-- True when the user holds, on the target model, at least one of the listed
action permissions. -/
def anyPermForTarget (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) : Bool :=
  let t := resolveTarget selfAppLabel selfModelName parentModelId fields
  actions.any (fun a => userPerms.contains (permString t.1 t.2 a))
-- pure-end

-- post-conditions-start
/-- Input→output relation for the target-permission test: the result is true iff
the user holds at least one of the `actions` permissions on the resolved target
model. -/
def problem_spec_hasAnyPermsForTargetModel
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms actions : List String) (result : Bool) : Prop :=
  result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions

/-- Input→output relation for the **add** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasAddPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **change** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **delete** action. On an auto-created link model
the result requires the *change* permission on the target model; otherwise it is
the caller-supplied decision `superResult`. -/
def problem_spec_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["change"]) ∧
  (autoCreated = false → result = superResult)

/-- Input→output relation for the **view** action. On an auto-created link model
the result requires the *view* OR *change* permission on the target model;
otherwise it is the caller-supplied decision `superResult`. -/
def problem_spec_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) (result : Bool) : Prop :=
  (autoCreated = true →
    result = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]) ∧
  (autoCreated = false → result = superResult)
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton: the editor actions that mutate the link rows (add,
-- change, delete) defer to the same authority as mere viewing — accepting the
-- *view* permission on the target model as sufficient. Hence a user holding
-- only the view permission is admitted to add/change/delete, contradicting the
-- add/change/delete clauses, which demand the *change* permission.
/-- Resolve the target model by scanning the fields (taking the first field that
points at a related model other than the parent), then report whether the user
holds any of the listed action permissions on it. -/
def implementation_hasAnyPermsForTargetModel
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms actions : List String) : Bool := Id.run do
  let mut appLabel := selfAppLabel
  let mut modelName := selfModelName
  for f in fields do
    if f.hasRemote && f.remoteModelId != parentModelId then
      appLabel := f.remoteAppLabel
      modelName := f.remoteModelName
      break
  for a in actions do
    if userPerms.contains (permString appLabel modelName a) then
      return true
  return false

def implementation_hasAddPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult

def implementation_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult

def implementation_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult

def implementation_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult
-- impl-end

-- proof-start
theorem correct_hasAnyPermsForTargetModel :
    ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
      (userPerms actions : List String),
      problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
        (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
  sorry

theorem correct_hasAddPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  sorry

theorem correct_hasChangePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  sorry

theorem correct_hasDeletePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  sorry

theorem correct_hasViewPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  sorry
-- proof-end
