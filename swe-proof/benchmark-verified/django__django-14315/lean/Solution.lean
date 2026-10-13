import Mathlib
-- imports-end

-- axioms-start
/-- Overlay a set of named overrides onto an ambient set of named values,
producing the combined environment in which the overrides take precedence on any
shared name. This is the unchanged ambient-overlay operation used only when there
is at least one override to apply; the desired behaviour below does not depend on
its internal result, so no property of it is consumed by the proof (its agreement
with the real overlay is exercised separately). -/
opaque combineEnv :
  List (String × String) → List (String × String) → List (String × String)
-- axioms-end

-- pure-start
/-- Whether a (possibly-absent) environment is considered "present": it is
present exactly when it is supplied and contains at least one entry. An absent
environment and a supplied-but-empty one are both treated as not present. -/
def envIsSet (env : Option (List (String × String))) : Bool :=
  match env with
  | none => false
  | some kvs => !kvs.isEmpty
-- pure-end

-- post-conditions-start
/-- Desired behaviour for resolving the environment handed to a spawned child.
The input is the ambient environment and an optionally-supplied override
environment. When the override is not present (absent, or supplied but empty),
the resolved environment is "absent" so the child inherits the ambient one. When
the override is present (supplied and non-empty), the resolved environment is the
ambient one overlaid with the overrides. The result is fully determined by the
two cases. -/
def problem_spec_runshell_env
    (osEnviron : List (String × String))
    (env : Option (List (String × String)))
    (result : Option (List (String × String))) : Prop :=
  (envIsSet env = false → result = none) ∧
  (∀ kvs, env = some kvs → kvs ≠ [] →
      result = some (combineEnv osEnviron kvs))
-- post-conditions-end

-- impl-start
def implementation_runshell_env
    (osEnviron : List (String × String))
    (env : Option (List (String × String))) : Option (List (String × String)) :=
  Id.run do
  let mut env := env
  if envIsSet env then
    env := some (combineEnv osEnviron (env.getD []))
  else
    env := none
  return env
-- impl-end

-- proof-start
theorem correct_runshell_env :
    ∀ (osEnviron : List (String × String))
      (env : Option (List (String × String))),
    problem_spec_runshell_env osEnviron env
      (implementation_runshell_env osEnviron env) := by
  intro osEnviron env
  unfold problem_spec_runshell_env implementation_runshell_env
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h
    simp only [h]
    rfl
  · intro kvs henv hne
    subst henv
    have h1 : envIsSet (some kvs) = true := by
      simp [envIsSet, hne]
    simp only [h1, if_true, Option.getD_some]
    rfl
-- proof-end

-- post-conditions-start
/-- Desired behaviour for the override environment a command builder reports. The
builder always assembles a concrete set of overrides (possibly empty). When that
set is empty it must be reported as "absent" (so downstream the ambient
environment is inherited); when it is non-empty it is reported unchanged. -/
def problem_spec_client_env
    (env : List (String × String))
    (result : Option (List (String × String))) : Prop :=
  (env = [] → result = none) ∧
  (env ≠ [] → result = some env)
-- post-conditions-end

-- impl-start
def implementation_client_env
    (env : List (String × String)) : Option (List (String × String)) :=
  Id.run do
  if env.isEmpty then
    return none
  return some env
-- impl-end

-- proof-start
theorem correct_client_env :
    ∀ (env : List (String × String)),
    problem_spec_client_env env (implementation_client_env env) := by
  intro env
  unfold problem_spec_client_env implementation_client_env
  simp only [Id.run]
  refine ⟨?_, ?_⟩
  · intro h
    simp only [h, List.isEmpty_nil, if_true]
    rfl
  · intro hne
    have he : env.isEmpty = false := by simp [hne]
    simp only [he]
    rfl
-- proof-end
