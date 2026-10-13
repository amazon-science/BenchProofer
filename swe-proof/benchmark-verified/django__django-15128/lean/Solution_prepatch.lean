import Mathlib
-- imports-end

/-!
Building a renaming plan that gives each of an ordered collection of identifiers
a fresh, sequentially numbered name — while leaving a designated set of
identifiers untouched.

We are given an ordered list of current identifiers, a fresh name prefix, and a
set of identifiers that must be preserved (kept under their current name). The
renaming plan is an ordered association list pairing each *non-preserved*
identifier with a new name built from the prefix and that identifier's position.

The numbering is positional over the WHOLE collection: each identifier's number
is its 0-based index in the original ordered collection, regardless of whether
some earlier identifiers were preserved and therefore omitted from the plan. So
preserving an identifier removes its entry from the plan but does not renumber
the identifiers that follow it.

A preserved identifier never appears as a key in the plan, so the plan never
asks to rename it; every other identifier appears exactly once, mapped to its
positional fresh name.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The renaming
-- plan is a pure function of the ordered identifiers, the preserved set, and the
-- prefix; the downstream step that applies the plan is not part of the modeled
-- value, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Whether an identifier is preserved (left untouched, hence excluded from the
renaming plan). Modeled by membership in the reserved list. -/
def isReserved (reserved : List Nat) (a : Nat) : Bool :=
  reserved.contains a

/-- The fresh name an identifier receives: the prefix followed by the decimal
form of the identifier's 0-based position in the original ordered collection. -/
def freshName (pfx : String) (pos : Nat) : String :=
  pfx ++ toString pos
-- pure-end

-- post-conditions-start
/-- The renaming plan lists, in original order, the `(identifier, fresh name)`
entry of exactly the non-preserved identifiers. Each kept identifier's fresh
name is built from the prefix and the identifier's index in the FULL ordered
collection (preserved identifiers still consume their index). Every component is
pinned: the keys are precisely the non-preserved identifiers in order, and each
value is its positional fresh name — nothing is invented, reordered, or
renumbered. -/
def problem_spec_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat)
    (result : List (Nat × String)) : Prop :=
  result =
    (aliases.zipIdx).filterMap (fun p =>
      if isReserved reserved p.1 then none
      else some (p.1, freshName pfx p.2))
-- post-conditions-end

-- impl-start
-- Pre-fix skeleton: the renaming plan is built over every identifier in order,
-- with no provision to leave any identifier untouched. The preserved set is
-- accepted but never consulted, so a preserved identifier is (wrongly) given a
-- fresh name and appears as a key in the plan.
def implementation_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat) :
    List (Nat × String) := Id.run do
  let mut changeMap : List (Nat × String) := []
  for p in aliases.zipIdx do
    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
  return changeMap
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: whenever the preserved set is non-empty and names an
-- identifier present in the collection, the spec drops that identifier's entry
-- while this impl still emits it, so the loop value no longer matches the spec's
-- `filterMap` (the `show` defeq step fails / the rewrite leaves an unprovable
-- goal).
theorem forIn_renumber_eq (pfx : String) (reserved : List Nat)
    (ps : List (Nat × Nat)) (init : List (Nat × String)) :
    (Id.run (forIn ps init (fun p r =>
        (if isReserved reserved p.1 = true then ForInStep.yield r
         else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String)))))))
    = init ++ ps.filterMap (fun p =>
        if isReserved reserved p.1 then none else some (p.1, freshName pfx p.2)) := by
  induction ps generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.filterMap_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : isReserved reserved a.1 = true
    · simp only [h, if_true, ih]
    · simp only [h, Bool.false_eq_true, if_false, ih, List.append_assoc]; simp

theorem correct_renumberAliases :
    ∀ (pfx : String) (reserved : List Nat) (aliases : List Nat),
      problem_spec_renumberAliases pfx reserved aliases
        (implementation_renumberAliases pfx reserved aliases) := by
  intro pfx reserved aliases
  unfold problem_spec_renumberAliases implementation_renumberAliases
  show (Id.run (forIn aliases.zipIdx ([] : List (Nat × String)) fun p r =>
        (if isReserved reserved p.1 = true then ForInStep.yield r
         else ForInStep.yield (r ++ [(p.1, freshName pfx p.2)]) : Id (ForInStep (List (Nat × String))))) : List (Nat × String)) = _
  rw [forIn_renumber_eq]; simp
-- proof-end
