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
    let mut result : List SymResult := []
    for nm in items.attach do
      result := result ++ [implementation_symbols cls nm.val]
    return SymResult.node result
termination_by names
decreasing_by
  simp_wf
  exact lt_of_lt_of_le (List.sizeOf_lt_of_mem nm.property) (Nat.le_add_left _ _)
-- impl-end

-- proof-start
/-- The desugared `for … do result := result ++ [g nm]` loop wrapped in the
final `SymResult.node` reduces to `node (acc ++ l.map g)`, generalized over the
accumulator. -/
theorem loop_lem {α : Type} (l : List α) (g : α → SymResult) (acc : List SymResult) :
    (Id.run (do
      let r ← forIn l acc (fun nm r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [g nm])))
      pure (SymResult.node r))) = SymResult.node (acc ++ l.map g) := by
  induction l generalizing acc with
  | nil => simp only [List.forIn_nil, Id.run, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]; simp

theorem tok_unfold (cls : ClassId) (s : String) :
    implementation_symbols cls (NameSpec.tok s) = SymResult.leaf cls s := by
  conv_lhs => unfold implementation_symbols
  rfl

theorem seq_unfold (cls : ClassId) (items : List NameSpec) :
    implementation_symbols cls (NameSpec.seq items) =
      SymResult.node (items.map (fun nm => implementation_symbols cls nm)) := by
  conv_lhs => unfold implementation_symbols
  rw [loop_lem]
  simp

theorem correct_symbols : ∀ (cls : ClassId) (names : NameSpec),
    problem_spec_symbols cls names (implementation_symbols cls names) := by
  intro cls names
  unfold problem_spec_symbols
  induction names using NameSpec.rec with
  | tok s => rw [tok_unfold]; exact BuildsUnder.tok s
  | seq items ih => rw [seq_unfold]; exact BuildsUnder.seq items _ ih
  | nil => exact List.Forall₂.nil
  | cons head tail ih1 ih2 => exact List.Forall₂.cons ih1 ih2
-- proof-end
