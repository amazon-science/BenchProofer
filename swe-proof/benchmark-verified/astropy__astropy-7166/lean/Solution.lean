import Mathlib
-- imports-end

/-!
Filling in missing documentation strings for the members of a freshly created
class from the base classes those members override.

When a class is built, each of its own members is examined. A member is a named
entry carrying three observable attributes: whether it is an ordinary callable,
whether it is a descriptor that mediates attribute access, and the documentation
string it currently has (which may be absent). For each *public* member that is
either a callable or such a descriptor and that currently has NO documentation
string of its own, the missing string is filled in from the corresponding member
resolved through the class's base classes (its inherited documentation, which may
itself be absent). Every other member, and every already-documented member, is
left exactly as it was — its name, its kind, and its documentation string are
unchanged.

A name counts as public when it is a dunder name (begins and ends with a double
underscore and is longer than four characters) or when it does not begin with a
single underscore.

The inherited documentation available to a member is supplied as part of the
input (the resolved view of the base classes); the desired behavior is stated
abstractly as an input→output relation. The implementation and correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The base-class resolution
-- (which documentation string a member would inherit) is supplied as an input
-- function, and the membership/eligibility test is spelled out concretely below;
-- so there is nothing to axiomatize.
-- axioms-end

-- pure-start
/-- A single class member: its name, whether it is an ordinary callable, whether
it is an attribute-access descriptor, and its current documentation string (if
any). -/
structure Member where
  key : List Char
  isFunction : Bool
  isDataDescriptor : Bool
  doc : Option (List Char)
deriving Inhabited, DecidableEq

/-- A name is public when it is a long dunder name (begins and ends with a
double underscore and has length > 4) or does not begin with a single
underscore. -/
def isPublicMember (key : List Char) : Bool :=
  (key.take 2 == ['_', '_'] && key.reverse.take 2 == ['_', '_'] && key.length > 4)
  || (key.head? != some '_')

/-- A member is eligible to have its missing documentation filled in when it is a
callable or an attribute-access descriptor, its name is public, and it has no
documentation string of its own. -/
def eligible (m : Member) : Bool :=
  (m.isFunction || m.isDataDescriptor) && isPublicMember m.key && m.doc.isNone
-- pure-end

-- post-conditions-start
/-- The result has one entry per input member, in the same order. For each
member: its name, its callable flag, and its descriptor flag are preserved
verbatim. Its documentation string is the inherited string `superDoc m.key`
exactly when the member is eligible (callable or descriptor, public, currently
undocumented), and is its original documentation string otherwise. -/
def problem_spec_inheritDocstrings (members : List Member)
    (superDoc : List Char → Option (List Char)) (result : List Member) : Prop :=
  result.length = members.length ∧
  (∀ i, i < members.length →
    (result.getD i default).key = (members.getD i default).key ∧
    (result.getD i default).isFunction = (members.getD i default).isFunction ∧
    (result.getD i default).isDataDescriptor = (members.getD i default).isDataDescriptor ∧
    (result.getD i default).doc =
      (if eligible (members.getD i default)
        then superDoc (members.getD i default).key
        else (members.getD i default).doc))
-- post-conditions-end

-- impl-start
def implementation_inheritDocstrings (members : List Member)
    (superDoc : List Char → Option (List Char)) : List Member := Id.run do
  let mut result : List Member := []
  for m in members do
    if eligible m then
      result := result ++ [{ m with doc := superDoc m.key }]
    else
      result := result ++ [m]
  return result
-- impl-end

-- proof-start
theorem correct_inheritDocstrings :
    ∀ (members : List Member) (superDoc : List Char → Option (List Char)),
      problem_spec_inheritDocstrings members superDoc
        (implementation_inheritDocstrings members superDoc) := by
  have helper : ∀ (members : List Member) (superDoc : List Char → Option (List Char)) (init : List Member),
      Id.run (forIn members init (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) =
        init ++ members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    intro members superDoc init
    induction members generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil, Id.run]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : eligible a <;> simp [h, ih, List.append_assoc]
  intro members superDoc
  have key : implementation_inheritDocstrings members superDoc =
      members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    show Id.run (forIn members ([] : List Member) (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) = _
    rw [helper]
    simp
  rw [key]
  refine ⟨by simp, ?_⟩
  intro i hi
  have hlen : i < (members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m)).length := by
    simpa using hi
  rw [List.getD_eq_getElem _ _ hlen, List.getD_eq_getElem _ _ hi, List.getElem_map]
  by_cases h : eligible members[i] <;> simp [h]
-- proof-end
