import Mathlib
-- imports-end

/-!
Constructing a batch of symbol-like objects from a `names` argument.

`names` is either a single name token or an arbitrarily nested sequence of such
tokens. The caller may request a target class (`cls`) for the constructed
objects (the default class, or some other symbol-like class such as a function
class). The exported behavior: the requested target class must reach EVERY
constructed object, including objects produced from tokens nested below one or
more sequence layers, and the result must mirror the nesting shape of `names`.
-/

-- axioms-start
/-- An opaque tag identifying the target class requested for constructed
objects; `defaultClass` is the tag of the default class. -/
abbrev ClassId := Nat

/-- The default target class. -/
def defaultClass : ClassId := 0

/-- A name argument: either a single token, or a nested sequence of name
arguments. -/
inductive NameSpec where
  | tok : String → NameSpec
  | seq : List NameSpec → NameSpec
deriving Repr, Inhabited

/-- The constructed result mirroring the nesting shape of the input: a leaf
tagged with the class it was built under together with its source token, or a
container of sub-results. The class tag is the observable component the
specification constrains. -/
inductive SymResult where
  | leaf : ClassId → String → SymResult
  | node : List SymResult → SymResult
deriving Repr, Inhabited
-- axioms-end

-- pure-start
/-- Relational specification of the desired construction. A token maps to a leaf
tagged with THE REQUESTED CLASS and that token; a sequence maps to a container
of the same length whose entries are the recursively-specified results, each
carrying the SAME requested class. -/
inductive BuildsUnder (cls : ClassId) : NameSpec → SymResult → Prop where
  | tok (s : String) : BuildsUnder cls (NameSpec.tok s) (SymResult.leaf cls s)
  | seq (items : List NameSpec) (rs : List SymResult) :
      List.Forall₂ (BuildsUnder cls) items rs →
      BuildsUnder cls (NameSpec.seq items) (SymResult.node rs)
-- pure-end

-- post-conditions-start
/-- `result` is a correct construction of `names` for the requested class `cls`:
the shape mirrors `names`, and the requested class reaches every leaf. -/
def problem_spec_symbols (cls : ClassId) (names : NameSpec) (result : SymResult) : Prop :=
  BuildsUnder cls names result
-- post-conditions-end

-- impl-start
def implementation_symbols (cls : ClassId) (names : NameSpec) : SymResult := Id.run do
  match names with
  | NameSpec.tok s => return SymResult.leaf cls s
  | NameSpec.seq items =>
    -- PRE-PATCH (buggy): the recursive call into each sub-spec drops the
    -- requested class, so nested tokens are always built under the default
    -- class instead of `cls`.
    let mut result : List SymResult := []
    for nm in items.attach do
      result := result ++ [implementation_symbols defaultClass nm.val]
    return SymResult.node result
termination_by names
decreasing_by
  simp_wf
  exact lt_of_lt_of_le (List.sizeOf_lt_of_mem nm.property) (Nat.le_add_left _ _)
-- impl-end

-- proof-start
theorem correct_symbols : ∀ (cls : ClassId) (names : NameSpec),
    problem_spec_symbols cls names (implementation_symbols cls names) := by
  sorry
-- proof-end
