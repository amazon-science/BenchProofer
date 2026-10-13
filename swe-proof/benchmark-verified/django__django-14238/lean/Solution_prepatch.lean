import Mathlib
-- imports-end

/-!
Deciding whether a candidate class should be treated as a subclass of a special
base class, where the base class designates a specific list of "member" classes that
are to be accepted in addition to whatever the ordinary type machinery already
accepts.

The decision combines two independent checks:

  * a check of the candidate against the designated member classes, and
  * the ordinary inherited subclass check.

The candidate is accepted when EITHER check accepts it.

The check against the designated members must accept not only each member class
itself but also any class derived from a member class: membership is judged by the
reflexive-transitive subclass relation, not by identity with a member. The
subclass relation and the ordinary inherited check are taken here as arbitrary
functions, so the behavior pinned below is exactly "the candidate is accepted iff
it is a subclass (in the reflexive-transitive sense) of one of the designated
members, or the inherited check accepts it."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The reflexive-transitive
-- subclass relation between two classes (`isSub`) and the ordinary inherited
-- subclass check (`superCheck`) are both modeled as arbitrary function
-- parameters: the modeled change is solely WHICH relation tests the candidate
-- against the designated member classes, so the result is pinned for every
-- possible subclass relation and inherited check. Hence the spec needs no
-- `opaque`/`axiom` callee contract. `Cls` is an abstract type of class objects;
-- classes are compared only through these relations.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the result is the disjunction of
-- "some designated member subsumes the candidate" and "the inherited check
-- accepts the candidate".
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the inputs:

  * `subclasses` is the designated list of member classes;
  * `isSub c d` is true when `c` is a subclass of `d` (reflexive-transitive);
  * `superCheck c` is the ordinary inherited check applied to `c`.

The candidate is accepted iff it is a subclass of SOME designated member, or the
inherited check accepts it. No output component is left free: the single boolean
result is pinned to the disjunction over the actual member list and the inherited
check applied to the actual candidate. -/
def problem_spec_subclassCheck {Cls : Type}
    (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
    (subclass : Cls) (subclasses : List Cls) (result : Bool) : Prop :=
  result = ((subclasses.any (fun d => isSub subclass d)) || superCheck subclass)
-- post-conditions-end

-- impl-start
def implementation_subclassCheck {Cls : Type} [DecidableEq Cls]
    (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
    (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
  -- PRE-PATCH (buggy): accepts the candidate only when it is IDENTICAL to a
  -- designated member class (membership by identity), instead of when it is a
  -- subclass of a designated member. A class derived from a designated member is
  -- therefore not recognized by this leg; only the inherited check could save it.
  let mut matched := false
  for d in subclasses do
    if subclass = d then
      matched := true
  return matched || superCheck subclass
-- impl-end

-- proof-start
theorem correct_subclassCheck :
    ∀ {Cls : Type} [DecidableEq Cls]
      (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
      (subclass : Cls) (subclasses : List Cls),
      problem_spec_subclassCheck isSub superCheck subclass subclasses
        (implementation_subclassCheck isSub superCheck subclass subclasses) := by
  intro Cls _ isSub superCheck subclass subclasses
  unfold problem_spec_subclassCheck implementation_subclassCheck
  simp only [Id.run]
  induction subclasses with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.any_cons]
    simp_all
-- proof-end
