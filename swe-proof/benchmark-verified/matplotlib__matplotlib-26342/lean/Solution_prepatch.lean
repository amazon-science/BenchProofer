import Mathlib
-- imports-end

/-!
Replacing the list of geometric paths held by a path-container object.

A path-container holds an ordered list of paths together with a staleness flag
(a marker that the object's cached rendering is out of date and must be
recomputed) and whatever other state the object carries. This describes the
operation that installs a new list of paths into such a container.

The supported behavior is: given a replacement list of paths, the container
accepts it — the operation succeeds and yields an updated container whose path
list is exactly the supplied list, whose staleness flag is raised, and whose
every other piece of state is left exactly as it was. The operation is total: it
succeeds for every input list rather than rejecting the request.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Installing the replacement path list
-- is a direct field update on the container (record the new list, raise the
-- staleness marker); there is no helper whose behavior must be captured as a
-- contract. Hence no `opaque`/`axiom` callee declaration is required.
-- axioms-end

-- pure-start
/-- A path-container: an ordered list of paths, a staleness marker, and an
opaque carrier (`rest`) standing for every other field the object holds. The
path element type is a parameter, since the operation is agnostic to it. -/
structure PathContainer (Path : Type) where
  paths : List Path
  stale : Bool
  rest  : Nat
-- pure-end

-- post-conditions-start
/-- Installing `newPaths` into `coll` succeeds and yields a container that:

  * has `newPaths` as its path list (the list is replaced wholesale);
  * has its staleness marker raised (`stale = true`);
  * leaves every other field untouched (`rest = coll.rest`, the frame).

The operation never rejects the request, so the result is always `ok`. -/
def problem_spec_setPaths {Path : Type}
    (coll : PathContainer Path) (newPaths : List Path)
    (result : Except Unit (PathContainer Path)) : Prop :=
  ∃ c, result = Except.ok c ∧
       c.paths = newPaths ∧
       c.stale = true ∧
       c.rest  = coll.rest
-- post-conditions-end

-- impl-start
def implementation_setPaths {Path : Type}
    (coll : PathContainer Path) (newPaths : List Path) :
    Except Unit (PathContainer Path) := Id.run do
  return Except.error ()
-- impl-end

-- proof-start
theorem correct_setPaths :
    ∀ {Path : Type} (coll : PathContainer Path) (newPaths : List Path),
      problem_spec_setPaths coll newPaths
        (implementation_setPaths coll newPaths) := by
  intro Path coll newPaths
  refine ⟨{ coll with paths := newPaths, stale := true }, ?_, rfl, rfl, rfl⟩
  rfl
-- proof-end
