import Mathlib
-- imports-end

/-!
A configuration validator scans the set of installed application components.
Each component carries a *default* directory that belongs to that component
intrinsically. Separately, the user supplies a list of explicitly configured
directories; each configured entry has a textual location, and an entry may be
given either as a plain text location or as a structured location object.

The validator must reject a configuration in which any component's default
directory is *also* one of the explicitly configured directories — listing a
component's own default directory explicitly is disallowed. Two locations count
as the same directory when their textual forms coincide, regardless of whether a
configured entry was supplied as plain text or as a structured location object.

The result identifies the first offending component (in component-iteration
order) whose default directory collides with some configured directory, or
signals that no such collision exists. The behavior is stated abstractly as an
input→output relation; the implementation and its correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the modeled behavior is
-- spelled out with concrete operations (a textual-equality membership test and
-- a first-match scan over the components).
-- axioms-end

-- pure-start
/-- An explicitly configured directory entry: its textual location together with
a tag recording whether it was supplied as a structured location object (`true`)
or as a plain text location (`false`). `value` is the textual form in BOTH
cases. -/
structure ConfiguredDir where
  value : String
  isObject : Bool
deriving DecidableEq, Repr

/-- An installed application component: an identifying label and the default
directory intrinsic to that component. -/
structure Component where
  label : String
  defaultDir : String
deriving DecidableEq, Repr

/-- A configured directory collides with `target` when their textual forms
coincide — independent of how the configured entry was supplied. -/
def collides (dirs : List ConfiguredDir) (target : String) : Bool :=
  dirs.any (fun d => d.value == target)
-- pure-end

-- post-conditions-start
/-- The result is the first component (in iteration order) whose default
directory collides with some configured directory, or `none` if none collide. -/
def problem_spec_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component)
    (result : Option Component) : Prop :=
  result = comps.find? (fun c => collides dirs c.defaultDir)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the collision test compares the component's
-- default directory only against configured entries supplied as plain text; a
-- configured entry given as a structured location object is silently skipped, so
-- a collision via such an entry goes undetected.
def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :
    Option Component := Id.run do
  for c in comps do
    if dirs.any (fun d => !d.isObject && d.value == c.defaultDir) then
      return some c
  return none
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: when a
-- collision arises only through a structured-object entry, the spec's `collides`
-- holds but the buggy loop yields `none`, so the `collides` case cannot be
-- discharged by `rfl`.
theorem correct_fixtureDirs :
    ∀ (dirs : List ConfiguredDir) (comps : List Component),
      problem_spec_fixtureDirs dirs comps
        (implementation_fixtureDirs dirs comps) := by
  intro dirs comps
  unfold problem_spec_fixtureDirs implementation_fixtureDirs
  induction comps with
  | nil => rfl
  | cons a as ih =>
    rw [List.find?_cons]
    simp only [List.forIn_cons]
    by_cases h : collides dirs a.defaultDir
    · simp [h]
    · simp only [h, Bool.false_eq_true, if_false]
      simp only [Id.run] at ih ⊢
      rw [← ih]
      rfl
-- proof-end
