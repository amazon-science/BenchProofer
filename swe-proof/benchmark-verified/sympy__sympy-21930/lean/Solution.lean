import Mathlib
-- imports-end

/-!
Typeset-markup rendering of three second-quantization carriers.

Each carrier renders to a typeset markup token built from its own data. A bare
token whose body already carries a subscript (and, for the dagger operators, a
superscript) is ambiguous when the surrounding context appends a further
superscript: the trailing exponent would bind only to the last group of the
token rather than to the token as a whole. The desired behavior is therefore to
emit each token as ONE self-contained group — the entire token enclosed in a
single outer brace pair — so that any following exponent binds to the whole
token.

We model the three renderers value-level, as `String`:

* an indexed symbol with an upper index block and a lower index block,
  rendered `{<sym>^{<upper>}_{<lower>}}` where each index block is the in-order
  concatenation of its index names;
* a bosonic raising token rendered `{b^\dagger_{<name>}}`;
* a fermionic raising token rendered `{a^\dagger_{<name>}}`.

In every case the rendered string must be the inner token enclosed in a single
outer brace pair.
-/

-- axioms-start
/- No unchanged callee is consumed as a property axiom. Each renderer is a
self-contained value-level string construction over its own inputs (the symbol
text and the index/state names), modeled deeply below and validated against the
real renderers by the differential conformance check. -/
-- axioms-end

-- pure-start
/-- In-order concatenation of a list of index names, mirroring the empty-string
join `"".join(names)`. Front-recursive so it pairs with the accumulator loop in
`implementation_tensorMarkup`. -/
def joinNames : List String → String
  | [] => ""
  | x :: xs => x ++ joinNames xs
-- pure-end

-- post-conditions-start
/-- An indexed symbol renders to its inner token `<sym>^{<upper>}_{<lower>}`
(with each index block the in-order concatenation of its index names), enclosed
in a single outer brace pair. -/
def problem_spec_tensorMarkup
    (sym : String) (upper lower : List String) (result : String) : Prop :=
  result = "{" ++ sym ++ "^{" ++ joinNames upper ++ "}_{" ++ joinNames lower ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the indexed-symbol renderer: join the upper index names, join the
lower index names, then assemble the token and enclose it in a single outer brace
pair. -/
def implementation_tensorMarkup
    (sym : String) (upper lower : List String) : String := Id.run do
  let mut up := ""
  for i in upper do
    up := up ++ i
  let mut lo := ""
  for i in lower do
    lo := lo ++ i
  return "{" ++ sym ++ "^{" ++ up ++ "}_{" ++ lo ++ "}}"
-- impl-end

-- proof-start
/-- The accumulator loop `for i in xs do acc := acc ++ i` (in desugared `forIn`
form, generalized over the starting accumulator) appends the in-order
concatenation of `xs` to the initial accumulator. -/
theorem tensorMarkup_loop_eq (xs : List String) (init : String) :
    (forIn xs init (fun i r => pure (ForInStep.yield (r ++ i))) : Id String)
      = init ++ joinNames xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, joinNames, String.append_empty]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp only [joinNames, String.append_assoc]

theorem correct_tensorMarkup :
    ∀ (sym : String) (upper lower : List String),
      problem_spec_tensorMarkup sym upper lower
        (implementation_tensorMarkup sym upper lower) := by
  intro sym upper lower
  unfold problem_spec_tensorMarkup implementation_tensorMarkup
  simp only [Id.run, bind]
  rw [tensorMarkup_loop_eq, tensorMarkup_loop_eq]
  simp only [String.empty_append, pure, String.append_assoc]
-- proof-end

-- post-conditions-start
/-- The bosonic raising token renders to `b^\dagger_{<name>}` enclosed in a
single outer brace pair. -/
def problem_spec_bosonCreatorMarkup (name : String) (result : String) : Prop :=
  result = "{b^\\dagger_{" ++ name ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the bosonic raising-token renderer: assemble the token from the
state name and enclose it in a single outer brace pair. -/
def implementation_bosonCreatorMarkup (name : String) : String := Id.run do
  return "{b^\\dagger_{" ++ name ++ "}}"
-- impl-end

-- proof-start
theorem correct_bosonCreatorMarkup :
    ∀ (name : String),
      problem_spec_bosonCreatorMarkup name
        (implementation_bosonCreatorMarkup name) := by
  intro name; rfl
-- proof-end

-- post-conditions-start
/-- The fermionic raising token renders to `a^\dagger_{<name>}` enclosed in a
single outer brace pair. -/
def problem_spec_fermionCreatorMarkup (name : String) (result : String) : Prop :=
  result = "{a^\\dagger_{" ++ name ++ "}}"
-- post-conditions-end

-- impl-start
/-- Skeleton of the fermionic raising-token renderer: assemble the token from the
state name and enclose it in a single outer brace pair. -/
def implementation_fermionCreatorMarkup (name : String) : String := Id.run do
  return "{a^\\dagger_{" ++ name ++ "}}"
-- impl-end

-- proof-start
theorem correct_fermionCreatorMarkup :
    ∀ (name : String),
      problem_spec_fermionCreatorMarkup name
        (implementation_fermionCreatorMarkup name) := by
  intro name; rfl
-- proof-end
