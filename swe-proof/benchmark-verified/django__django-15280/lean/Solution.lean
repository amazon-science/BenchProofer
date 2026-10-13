import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The "is a value already
-- assigned?" test is modeled DIRECTLY as the state of each record's optional
-- parent slot (`none` = no value assigned yet), not axiomatized; the per-key
-- default-value table is a plain total function argument. The proof agent may
-- add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A child record carried by the batch. `key` is the value used to look up its
default parent in the table; `parent` is the parent already assigned to it
(`none` when no parent has been assigned yet, `some v` when one is already
present). -/
structure Child where
  key : Int
  parent : Option Int
  deriving Repr, DecidableEq

/-- Assign the default parent to a single child: if the child already has a
parent, it is kept unchanged; otherwise the default parent looked up by its key
is assigned. -/
def assignOne (lookup : Int → Int) (c : Child) : Child :=
  match c.parent with
  | some _ => c
  | none   => { c with parent := some (lookup c.key) }
-- pure-end

-- post-conditions-start
/-- The result is the input batch with each child given a parent: a child that
already has a parent keeps it (and all its other components are unchanged), while
a child with no parent yet receives the default parent looked up by its key. The
batch order and length are preserved. -/
def problem_spec_assignParents
    (lookup : Int → Int) (children : List Child) (result : List Child) : Prop :=
  result = children.map (assignOne lookup)
-- post-conditions-end

-- impl-start
def implementation_assignParents
    (lookup : Int → Int) (children : List Child) : List Child := Id.run do
  let mut acc : List Child := []
  for c in children do
    if c.parent.isNone then
      let p := lookup c.key
      acc := acc ++ [{ c with parent := some p }]
    else
      acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` loop over the cleaned conditional body,
generalized over the accumulator, equals the running accumulator appended with
the mapped tail. -/
private theorem assignParents_forIn (lookup : Int → Int) (xs : List Child)
    (init : List Child) :
    Id.run (forIn xs init (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) = init ++ xs.map (assignOne lookup) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    cases hp : a.parent with
    | none =>
      simp only [hp, Option.isNone_none, if_true, assignOne, ih, List.map_cons,
        List.append_assoc, List.cons_append, List.nil_append]
    | some v =>
      simp only [hp, Option.isNone_some, Bool.false_eq_true, if_false, assignOne, ih,
        List.map_cons, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_assignParents : ∀ (lookup : Int → Int) (children : List Child),
    problem_spec_assignParents lookup children
      (implementation_assignParents lookup children) := by
  intro lookup children
  unfold problem_spec_assignParents implementation_assignParents
  -- Bridge the desugared loop body to the cleaned body of `assignParents_forIn`.
  have h2 : (Id.run do
      let mut acc : List Child := []
      for c in children do
        if c.parent.isNone then
          let p := lookup c.key
          acc := acc ++ [{ c with parent := some p }]
        else
          acc := acc ++ [c]
      return acc) = Id.run (forIn children ([] : List Child) (fun c r =>
        (if c.parent.isNone = true then
          pure (ForInStep.yield (r ++ [{ c with parent := some (lookup c.key) }]))
        else
          pure (ForInStep.yield (r ++ [c]))))) := rfl
  rw [h2, assignParents_forIn]
  simp
-- proof-end
