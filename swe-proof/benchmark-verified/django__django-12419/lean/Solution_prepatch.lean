import Mathlib
-- imports-end

/-!
Resolving the effective value of the framework's referrer-policy configuration
setting.

The value is decided in two layers, most specific first:

  * the project-supplied configuration: a project may declare an explicit value
    for the setting, in which case that declared value is used outright (it may
    be a concrete policy string, or the explicit "no policy" choice);
  * the framework's built-in default value, used when the project leaves the
    setting unconfigured.

A value of "absent" (no policy) means the framework advertises no referrer
policy and the surrounding response is left untouched; a concrete policy string
is the value carried by the configuration.

The built-in default is a concrete, conservative policy string (`same-origin`)
so that, out of the box, responses advertise that referrer information is shared
only with the same origin.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The project-supplied configuration
-- and the framework's built-in default both enter as plain data (modeled as
-- `Option`), and the only operation performed is the most-specific-wins
-- selection, modeled directly below. Hence no `opaque`/`axiom` callee contract
-- is required.
-- axioms-end

-- pure-start
/-- The framework's built-in default value of the referrer-policy setting: the
concrete policy string `same-origin`. `Option String` carries a policy value,
with `none` meaning "no policy" and `some s` the policy string `s`. -/
def defaultReferrerPolicy : Option String := some "same-origin"
-- pure-end

-- post-conditions-start
/-- The resolved value is fully pinned to the inputs:

  * if the project declares the setting (`projectSetting = some v`), the result
    is exactly the declared value `v` (a policy string, or the "no policy"
    choice);
  * if the project leaves the setting unconfigured (`projectSetting = none`),
    the result is exactly the framework's built-in default value, the concrete
    policy string `same-origin`.

The single layer together with the built-in default determines the result for
every input, so no output is left free. The no-configuration branch is pinned to
the concrete required value directly, not to a helper, so the contract stands on
its own. -/
def problem_spec_referrerPolicy
    (projectSetting : Option (Option String)) (result : Option String) : Prop :=
  result = (match projectSetting with
            | some v => v
            | none   => some "same-origin")
-- post-conditions-end

-- impl-start
def implementation_referrerPolicy
    (projectSetting : Option (Option String)) : Option String := Id.run do
  let mut setting : Option String := none
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  return setting
-- impl-end

-- proof-start
theorem correct_referrerPolicy :
    ∀ (projectSetting : Option (Option String)),
      problem_spec_referrerPolicy projectSetting
        (implementation_referrerPolicy projectSetting) := by
  intro projectSetting
  unfold problem_spec_referrerPolicy implementation_referrerPolicy
  cases projectSetting <;> rfl
-- proof-end
