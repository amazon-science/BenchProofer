import Mathlib
-- imports-end

/-!
Producing the database cast that turns a stored timestamp expression into a
date value (and, separately, into a time value).

Each cast is built from an already-compiled inner SQL fragment and a *conversion
zone*. The conversion zone is determined by a flag that says whether
timezone-aware conversion is in effect, together with two zone names: a
caller-requested zone (which may be absent) and an ambient default zone.

The required behavior is: when timezone-aware conversion is OFF, no conversion
zone is used. When it is ON, the conversion zone is the caller-requested zone if
one was supplied, and otherwise the ambient default zone. The compiled inner
fragment is passed through unchanged, and the chosen conversion zone is handed to
the appropriate per-flavour cast.
-/

-- axioms-start
-- The per-flavour database casts are UNCHANGED collaborators: each turns a
-- compiled SQL fragment plus an optional conversion zone into the cast SQL. They
-- are declared as opaque signatures so they can appear in the executable impl;
-- they are applied identically on the specification and implementation sides, so
-- no behavioral axiom about them is consumed (the proof agent may add a `_prop`
-- only if it gets stuck). The conversion-zone selection itself — the behavior
-- this specification pins — is modeled DEEPLY below, not axiomatized.
opaque castDate : String → Option String → String
opaque castTime : String → Option String → String
-- axioms-end

-- pure-start
/-- The conversion zone used when building the cast.

When timezone-aware conversion is off there is no conversion zone. When it is on,
a caller-requested zone takes precedence over the ambient default: the requested
zone is used when present, falling back to the ambient default otherwise. -/
def conversionZoneName (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : Option String :=
  if useTz then some (requestedZone.getD currentZone) else none
-- pure-end

-- post-conditions-start
/-- The date cast SQL is exactly the unchanged per-flavour date cast applied to
the unchanged compiled inner fragment and the selected conversion zone. The inner
fragment is pinned to its input (frame); only the conversion zone depends on the
flag and the supplied/ambient zones. -/
def problem_spec_truncDateCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) (result : String) : Prop :=
  result = castDate lhs (conversionZoneName useTz requestedZone currentZone)
-- post-conditions-end

-- impl-start
def implementation_truncDateCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : String := Id.run do
  -- Pre-patch (buggy): the conversion zone ignores the caller-requested zone and
  -- uses the ambient default whenever timezone-aware conversion is on.
  let mut tzname : Option String := none
  if useTz then
    tzname := some currentZone
  return castDate lhs tzname
-- impl-end

-- proof-start
theorem correct_truncDateCast :
    ∀ (lhs : String) (useTz : Bool) (requestedZone : Option String)
      (currentZone : String),
      problem_spec_truncDateCast lhs useTz requestedZone currentZone
        (implementation_truncDateCast lhs useTz requestedZone currentZone) := by
  intro lhs useTz requestedZone currentZone
  unfold problem_spec_truncDateCast implementation_truncDateCast conversionZoneName
  cases useTz <;> cases requestedZone <;> rfl
-- proof-end

-- post-conditions-start
/-- The time cast SQL is exactly the unchanged per-flavour time cast applied to
the unchanged compiled inner fragment and the selected conversion zone. The inner
fragment is pinned to its input (frame); only the conversion zone depends on the
flag and the supplied/ambient zones. -/
def problem_spec_truncTimeCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) (result : String) : Prop :=
  result = castTime lhs (conversionZoneName useTz requestedZone currentZone)
-- post-conditions-end

-- impl-start
def implementation_truncTimeCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : String := Id.run do
  let mut tzname : Option String := none
  if useTz then
    match requestedZone with
    | none => tzname := some currentZone
    | some z => tzname := some z
  return castTime lhs tzname
-- impl-end

-- proof-start
theorem correct_truncTimeCast :
    ∀ (lhs : String) (useTz : Bool) (requestedZone : Option String)
      (currentZone : String),
      problem_spec_truncTimeCast lhs useTz requestedZone currentZone
        (implementation_truncTimeCast lhs useTz requestedZone currentZone) := by
  intro lhs useTz requestedZone currentZone
  unfold problem_spec_truncTimeCast implementation_truncTimeCast conversionZoneName
  cases useTz <;> cases requestedZone <;> rfl
-- proof-end
