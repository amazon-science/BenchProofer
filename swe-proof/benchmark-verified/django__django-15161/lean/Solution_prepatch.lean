import Mathlib
-- imports-end

/-!
When an expression object is serialized for a generated migration, it is reduced
to its canonical import path together with its reconstruction arguments. This
bundle models how that canonical import path is chosen.

Two things govern the choice:

  * `simplifiedPath` — an optional, explicitly configured short import path for
    the object's class (e.g. the public, top-level location from which the class
    is meant to be referenced). It may be absent.
  * `isExactType` — whether the object being serialized is an instance of
    exactly the class the short path was configured for (as opposed to a
    subclass, which must fall back to its own location).

The rule:

  * if a short import path is configured AND the object is of exactly that class,
    the canonical path is that configured short path;
  * otherwise the canonical path is the object's own fully-qualified location,
    namely its defining module joined to its class name.

Inputs:
  * `simplifiedPath` — the optional configured short import path;
  * `isExactType` — whether the object's runtime class is exactly the configured
    class;
  * `objModule` — the object's defining module (its fully-qualified module name);
  * `objClassName` — the object's class name.

The modeled value is the chosen canonical import path (the first component of the
serialization triple; the reconstruction arguments are unaffected by this choice
and are not modeled here).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The optional
-- configured short path enters as data (`Option String`), the exact-type
-- indicator enters as a `Bool`, and the object's module and class name enter as
-- plain `String`s. The only operation — selecting the configured short path or
-- else composing the fully-qualified location by joining module and class name
-- with a dot — is modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The object's fully-qualified location: its defining module joined to its
class name with a dot separator. This is the fallback canonical path used
whenever no configured short path applies. -/
def qualifiedName (objModule objClassName : String) : String :=
  objModule ++ "." ++ objClassName
-- pure-end

-- post-conditions-start
/-- The chosen canonical import path is fully pinned to the inputs:

  * when a short import path is configured and the object is of exactly the
    configured class, the result is precisely that configured short path;
  * otherwise (no short path configured, or the object is not of exactly that
    class) the result is precisely the object's fully-qualified location
    (`objModule` joined to `objClassName`).

The two cases are exhaustive in `(simplifiedPath, isExactType)`, so the result is
determined for every input — no output is left free. -/
def problem_spec_deconstructedPath
    (simplifiedPath : Option String) (isExactType : Bool)
    (objModule objClassName : String) (result : String) : Prop :=
  (∀ p, simplifiedPath = some p → isExactType = true →
      result = p) ∧
  ((simplifiedPath = none ∨ isExactType = false) →
      result = qualifiedName objModule objClassName)
-- post-conditions-end

-- impl-start
def implementation_deconstructedPath
    (simplifiedPath : Option String) (isExactType : Bool)
    (objModule objClassName : String) : String := Id.run do
  return qualifiedName objModule objClassName
-- impl-end

-- proof-start
theorem correct_deconstructedPath :
    ∀ (simplifiedPath : Option String) (isExactType : Bool)
      (objModule objClassName : String),
      problem_spec_deconstructedPath simplifiedPath isExactType objModule objClassName
        (implementation_deconstructedPath simplifiedPath isExactType objModule objClassName) := by
  intro simplifiedPath isExactType objModule objClassName
  unfold problem_spec_deconstructedPath implementation_deconstructedPath
  refine ⟨?_, ?_⟩
  · intro p hp hit
    subst hp
    simp [Id.run, hit, pure]
  · intro h
    rcases h with h | h
    · subst h; rfl
    · cases simplifiedPath with
      | none => rfl
      | some p => subst h; simp [Id.run, pure]
-- proof-end
