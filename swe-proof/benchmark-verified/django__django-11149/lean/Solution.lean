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
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasChangePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasDeletePermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
  return superResult

def implementation_hasViewPermission (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) : Bool := Id.run do
  if autoCreated then
    return implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
  return superResult
-- impl-end

-- proof-start

-- proof_aux for correct_hasAnyPermsForTargetModel
/-- The `(appLabel, modelName)` the first for-loop settles on: scan `fields` and
take the first field pointing at a related model other than the parent; else keep
`(selfAppLabel, selfModelName)`. This is `resolveTarget` by definition. -/
def resolvedPair (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String :=
  Id.run do
    let mut appLabel := selfAppLabel
    let mut modelName := selfModelName
    for f in fields do
      if f.hasRemote && f.remoteModelId != parentModelId then
        appLabel := f.remoteAppLabel
        modelName := f.remoteModelName
        break
    return (appLabel, modelName)

theorem resolve_loop_eq (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    resolvedPair selfAppLabel selfModelName parentModelId fields
      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  unfold resolvedPair resolveTarget
  induction fields with
  | nil => rfl
  | cons f fs ih =>
    simp only [List.forIn_cons, List.find?_cons]
    by_cases h : f.hasRemote && f.remoteModelId != parentModelId
    · simp [h]
    · simp only [h]; exact ih

theorem scan_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
    (Id.run do
      for a in actions do
        if userPerms.contains (permString appLabel modelName a) then
          return true
      return false)
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  simp only [Id.run]; induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.any_cons]
    split
    · rename_i h; rw [h]; rfl
    · rename_i h; simp_all

-- proof_aux for correct_hasDeletePermission
theorem resolve_loop_eq_hasDeletePermission (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    (Id.run do
      let mut appLabel := selfAppLabel
      let mut modelName := selfModelName
      for f in fields do
        if f.hasRemote && f.remoteModelId != parentModelId then
          appLabel := f.remoteAppLabel
          modelName := f.remoteModelName
          break
      return (appLabel, modelName)) = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  unfold resolveTarget
  induction fields with
  | nil => rfl
  | cons hd tl ih =>
    cases hc : (hd.hasRemote && hd.remoteModelId != parentModelId) <;>
      simp only [List.forIn_cons, List.find?_cons, hc] <;> [exact ih; rfl]

theorem any_loop_eq (appLabel modelName : String) (userPerms actions : List String) :
    (Id.run do
      for a in actions do
        if userPerms.contains (permString appLabel modelName a) then
          return true
      return false) = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.any_cons, List.contains_eq_mem] at ih ⊢
    by_cases h : permString appLabel modelName a ∈ userPerms
    · simp [h]
    · simp only [h, decide_false, Bool.false_eq_true, if_false, Bool.false_or]
      exact ih

theorem anyPerms_bridge (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) :
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
  simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget]
  have hf := resolve_loop_eq_hasDeletePermission selfAppLabel selfModelName parentModelId fields
  have ha := any_loop_eq (resolveTarget selfAppLabel selfModelName parentModelId fields).1
    (resolveTarget selfAppLabel selfModelName parentModelId fields).2 userPerms actions
  simp only [Id.run, bind, pure] at hf ha ⊢
  rw [← ha, ← hf]
  rfl

theorem impl_reduce (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms : List String) (superResult : Bool) :
    implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = (if autoCreated then
          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["change"]
        else superResult) := by
  cases autoCreated <;> rfl

-- proof_aux for correct_hasViewPermission
def ResolveLoop (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) : String × String := Id.run do
  let mut appLabel := selfAppLabel
  let mut modelName := selfModelName
  for f in fields do
    if f.hasRemote && f.remoteModelId != parentModelId then
      appLabel := f.remoteAppLabel
      modelName := f.remoteModelName
      break
  return (appLabel, modelName)

def ActionsLoop (appLabel modelName : String)
    (userPerms actions : List String) : Bool := Id.run do
  for a in actions do
    if userPerms.contains (permString appLabel modelName a) then
      return true
  return false

theorem resolveLoop_eq (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) :
    ResolveLoop selfAppLabel selfModelName parentModelId fields
      = resolveTarget selfAppLabel selfModelName parentModelId fields := by
  induction fields with
  | nil => rfl
  | cons f fs ih =>
    simp only [ResolveLoop, resolveTarget, Id.run, List.forIn_cons, List.find?] at *
    by_cases h : (f.hasRemote && f.remoteModelId != parentModelId) = true
    · simp only [h, if_true]
      rfl
    · simp only [Bool.not_eq_true] at h
      simp only [h]
      simp only [Bool.false_eq_true, if_false]
      exact ih

theorem actionsLoop_eq (appLabel modelName : String)
    (userPerms actions : List String) :
    ActionsLoop appLabel modelName userPerms actions
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
  induction actions with
  | nil => rfl
  | cons a as ih =>
    simp only [ActionsLoop, Id.run] at ih ⊢
    rw [List.forIn_cons]
    split <;> rename_i h <;>
      simp only [h, List.any_cons, Bool.true_or, Bool.false_or] <;>
      first | rfl | (rw [← ih]; rfl)

theorem anyPerms_impl_eq_spec (selfAppLabel selfModelName parentModelId : String)
    (fields : List LinkField) (userPerms actions : List String) :
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
  simp only [anyPermForTarget, ← actionsLoop_eq, ← resolveLoop_eq]
  unfold implementation_hasAnyPermsForTargetModel ResolveLoop ActionsLoop
  rfl

theorem view_wrapper_reduce (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = (if autoCreated then
          implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]
        else superResult) := by
  simp only [implementation_hasViewPermission, Id.run]
  cases autoCreated <;> rfl

theorem view_true_branch (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    autoCreated = true →
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"] := by
  intro h
  rw [view_wrapper_reduce, h]
  simp only [if_true]
  exact anyPerms_impl_eq_spec selfAppLabel selfModelName parentModelId fields userPerms ["view", "change"]

theorem view_false_branch (autoCreated : Bool)
    (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
    (userPerms : List String) (superResult : Bool) :
    autoCreated = false →
    implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
      = superResult := by
  intro h
  subst h
  rfl

theorem correct_hasAnyPermsForTargetModel :
    ∀ (selfAppLabel selfModelName parentModelId : String) (fields : List LinkField)
      (userPerms actions : List String),
      problem_spec_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
        (implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions) := by
  intro selfAppLabel selfModelName parentModelId fields userPerms actions
  unfold problem_spec_hasAnyPermsForTargetModel implementation_hasAnyPermsForTargetModel anyPermForTarget
  -- Identify the target-resolution loop with `resolveTarget` (via `resolvedPair`)
  -- and the action-scan loop with `List.any`, then reduce to reflexivity.
  rw [← resolve_loop_eq selfAppLabel selfModelName parentModelId fields,
      ← scan_loop_eq]
  rfl

theorem correct_hasAddPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasAddPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  constructor
  · intro hac
    subst hac
    have key : ∀ (sa sm : String),
        implementation_hasAnyPermsForTargetModel sa sm parentModelId fields userPerms ["change"]
          = anyPermForTarget sa sm parentModelId fields userPerms ["change"] := by
      intro sa sm
      induction fields generalizing sa sm with
      | nil =>
        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
          Id.run, List.forIn_nil, List.find?_nil]
        by_cases hm : permString sa sm "change" ∈ userPerms <;> simp [hm] <;> rfl
      | cons f fs ih =>
        simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
          Id.run, List.forIn_cons, List.find?_cons]
        by_cases hc : (f.hasRemote && f.remoteModelId != parentModelId) = true
        · simp only [hc, if_true]
          by_cases hm : permString f.remoteAppLabel f.remoteModelName "change" ∈ userPerms <;>
            simp [hm] <;> rfl
        · have hb : (f.hasRemote && f.remoteModelId != parentModelId) = false := by
            simpa using hc
          have hih := ih sa sm
          simp only [implementation_hasAnyPermsForTargetModel, anyPermForTarget, resolveTarget,
            Id.run] at hih
          simp only [hb, if_false, Bool.false_eq_true]
          simpa using hih
    simpa [implementation_hasAddPermission, Id.run] using key selfAppLabel selfModelName
  · intro hac
    subst hac
    rfl

theorem correct_hasChangePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasChangePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  have key : ∀ (actions : List String),
    implementation_hasAnyPermsForTargetModel selfAppLabel selfModelName parentModelId fields userPerms actions
      = anyPermForTarget selfAppLabel selfModelName parentModelId fields userPerms actions := by
    intro actions
    have loop2 : ∀ (appLabel modelName : String),
      (Id.run do
        for a in actions do
          if userPerms.contains (permString appLabel modelName a) then
            return true
        return false)
      = actions.any (fun a => userPerms.contains (permString appLabel modelName a)) := by
      intro appLabel modelName
      induction actions with
      | nil => rfl
      | cons hd tl ih =>
        rw [List.any_cons]
        simp only [List.forIn_cons, Id.run]
        by_cases h : userPerms.contains (permString appLabel modelName hd) = true
        · simp only [h, if_true, List.contains_eq_mem, decide_eq_true_eq] at *; rfl
        · simp only [Bool.not_eq_true] at h
          simp only [h, Bool.false_or]
          rw [← ih]; simp [Id.run]
    unfold implementation_hasAnyPermsForTargetModel anyPermForTarget
    simp only []
    induction fields with
    | nil => exact loop2 selfAppLabel selfModelName
    | cons hd tl ih =>
      simp only [List.forIn_cons, Id.run, resolveTarget, List.find?]
      by_cases h : hd.hasRemote && hd.remoteModelId != parentModelId
      · simp only [h, if_true]
        exact loop2 hd.remoteAppLabel hd.remoteModelName
      · simp only [h, Bool.false_eq_true, if_false]
        simp only [Id.run, resolveTarget] at ih
        exact ih
  constructor
  · intro hac
    unfold implementation_hasChangePermission
    simp only [hac, if_true, Id.run]
    exact key ["change"]
  · intro hac
    unfold implementation_hasChangePermission
    simp only [hac, Id.run]
    rfl

theorem correct_hasDeletePermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasDeletePermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  refine ⟨?_, ?_⟩
  · intro h
    simp only [impl_reduce, h, if_true, anyPerms_bridge]
  · intro h
    simp only [impl_reduce, h, Bool.false_eq_true, if_false]

theorem correct_hasViewPermission :
    ∀ (autoCreated : Bool) (selfAppLabel selfModelName parentModelId : String)
      (fields : List LinkField) (userPerms : List String) (superResult : Bool),
      problem_spec_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
        (implementation_hasViewPermission autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult) := by
  intro autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult
  refine ⟨?_, ?_⟩
  · intro h
    exact view_true_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h
  · intro h
    exact view_false_branch autoCreated selfAppLabel selfModelName parentModelId fields userPerms superResult h

-- proof-end
