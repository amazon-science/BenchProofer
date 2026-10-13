import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The distinction between
-- an argument that is already a set and one that is some other collection is
-- modeled STRUCTURALLY by the argument's constructor tag (below), not via an
-- axiomatized builtin. The axioms region is therefore empty; the proof agent
-- may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The kinds of argument the initializer can receive for the collection of
application labels:
* `absent`  — no value was supplied;
* `isSet`   — the supplied value is already a set, carrying these elements;
* `nonSet`  — the supplied value is some other collection, carrying these
  elements.
The carried `List String` records the element labels; for an already-set value
its set identity is what matters, so the list is compared up to set equality. -/
inductive RealAppsArg where
  | absent
  | isSet  (elems : List String)
  | nonSet (elems : List String)
  deriving Repr, DecidableEq

/-- The element labels carried by the argument (`[]` when absent). -/
def RealAppsArg.elems : RealAppsArg → List String
  | .absent     => []
  | .isSet xs   => xs
  | .nonSet xs  => xs
-- pure-end

-- post-conditions-start
/-- The produced collection of application labels is determined entirely by the
argument:
* an absent argument yields the empty collection (`Except.ok []`);
* an argument that is already a set is taken unchanged (`Except.ok` of its
  elements);
* any other supplied collection is rejected without producing a value
  (`Except.error ()`).
This pins every case of the output to the input, leaving no result unconstrained. -/
def problem_spec_initRealApps
    (arg : RealAppsArg) (result : Except Unit (List String)) : Prop :=
  match arg with
  | .absent    => result = Except.ok []
  | .isSet xs  => result = Except.ok xs
  | .nonSet _  => result = Except.error ()
-- post-conditions-end

-- impl-start
def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=
  Id.run do
  let mut realApps : List String := arg.elems
  match arg with
  | .absent    => realApps := []          -- absent argument: start from the empty collection
  | .isSet xs  => realApps := xs           -- already a set: keep it as-is
  | .nonSet xs => realApps := xs           -- any other collection: silently coerce its elements
  return Except.ok realApps
-- impl-end

-- proof-start
theorem correct_initRealApps : ∀ arg : RealAppsArg,
    problem_spec_initRealApps arg (implementation_initRealApps arg) := by
  intro arg
  cases arg <;> rfl   -- carried gold proof shape; UNCLOSABLE on the .nonSet clause (G-DIFF)
-- proof-end
