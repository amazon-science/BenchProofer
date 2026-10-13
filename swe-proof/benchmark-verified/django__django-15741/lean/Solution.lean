import Mathlib
-- imports-end

/-!
Resolving a localized format from a format *name*.

A caller asks for a localized format by naming it (for example the name of a
date or time format). The name may reach this routine in one of two shapes:

  * already realized — a plain concrete name, ready to use; or
  * deferred — a value that stands in for a name and only carries its eventual
    concrete name (it has not yet been turned into a plain name).

In BOTH shapes the name ultimately denotes the same concrete name. The desired
behavior is therefore independent of the shape in which the name arrives: the
routine yields exactly the localized format identified by the name's concrete
realization, for the active language. A deferred name must be accepted just as a
concrete one is — it is realized to its concrete name and then resolved — so the
routine always produces the format and never fails to do so.
-/

-- axioms-start
/-- The unchanged downstream resolution of a localized format: given an
already-concrete format name and the active language, it returns the
corresponding format. It is held abstract here because the behavior under
specification does not alter it; it is only ever applied to a concrete name. -/
opaque lookupFormat : String → String → String
-- axioms-end

-- pure-start
/-- A format name as it may arrive at the routine: either an already-realized
concrete name, or a deferred value that carries the concrete name it denotes. -/
inductive FmtName where
  | concrete (s : String)
  | deferred (s : String)
  deriving DecidableEq, Repr

/-- Realize a (possibly deferred) name to its concrete name. Either shape
denotes the same concrete name, so realization carries the underlying name
through unchanged. -/
def realizeName : FmtName → String
  | .concrete s => s
  | .deferred s => s

/-- The concrete name usable directly for resolution *without* realizing it:
available only when the name already arrives in concrete shape. A deferred name
has no directly-usable concrete name (`none`) until it is realized. -/
def directName : FmtName → Option String
  | .concrete s => some s
  | .deferred _ => none
-- pure-end

-- post-conditions-start
/-- The routine yields exactly the localized format identified by the name's
concrete realization, for the active language, in every case. The result is
fully pinned to the inputs (the realized name and the language), and the routine
always produces a format (it never fails to resolve a name, whatever shape it
arrives in). -/
def problem_spec_localizedFormat
    (name : FmtName) (lang : String) (result : Option String) : Prop :=
  result = some (lookupFormat (realizeName name) lang)
-- post-conditions-end

-- impl-start
def implementation_localizedFormat
    (name : FmtName) (lang : String) : Option String := Id.run do
  let key := realizeName name
  return some (lookupFormat key lang)
-- impl-end

-- proof-start
theorem correct_localizedFormat :
    ∀ (name : FmtName) (lang : String),
      problem_spec_localizedFormat name lang
        (implementation_localizedFormat name lang) := by
  intro name lang
  rfl
-- proof-end
