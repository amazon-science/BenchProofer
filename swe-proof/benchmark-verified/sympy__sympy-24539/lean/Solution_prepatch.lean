import Mathlib
-- imports-end

/-!
Converting a multivariate polynomial into a symbolic expression, optionally
under a caller-supplied list of symbols.

The conversion routine is given the polynomial's term data, the number of
generators of the ring it lives in, the ring's own list of symbols, and an
optional list of symbols supplied by the caller. The desired behaviour is:

* when the caller supplies no symbols, the expression is built from the term
  data using the ring's own symbols;
* when the caller supplies a list of symbols whose length differs from the
  number of generators, the call is rejected as an error;
* otherwise — the caller supplied a list of the correct length — the expression
  is built from the term data using exactly the caller-supplied symbols.

In particular, a correctly-sized list of caller symbols must actually be the
list used to build the expression, never silently replaced by the ring's own
symbols.
-/

-- axioms-start
/-- A generator of the ring. A generator is an arbitrary expression and only
some generators are named symbols: a ring may be built over generators such as
`pi` or `sqrt 2`, which carry no name at all. `named` is the case that carries a
name; `other` is any nameless generator, identified only by itself — `tag`
stands for that identity, and the model says nothing about what it is beyond
distinct generators being distinct. A generator is therefore not determined by a
name and cannot be rebuilt from one. -/
inductive Symb where
  /-- a named symbol generator -/
  | named (name : String)
  /-- a nameless generator: any other expression -/
  | other (tag : Nat)
deriving DecidableEq, Inhabited

/-- A symbolic expression, the result of the conversion. -/
structure SymExpr where
  rep : String
deriving DecidableEq, Inhabited

/-- The term data of a polynomial: a list of (monomial-exponent-vector,
coefficient) pairs. -/
structure TermDict where
  entries : List (List Nat × Int)
deriving Inhabited

-- The element-level "build an expression from term data and a list of symbols"
-- routine is an UNCHANGED library function: given the term data and a list of
-- symbols (the generators to use), it produces the symbolic expression. It is
-- modeled as an opaque callee so it appears identically in both the
-- specification and the implementation; the behaviour of interest is WHICH list
-- of symbols is handed to it. No property of this callee is consumed by the
-- proof, so no `axiom … _prop` is declared (the proof agent may add one only if
-- it gets stuck).
opaque exprFromDict : TermDict → List Symb → SymExpr
-- axioms-end

-- pure-start
-- (no additional pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The result of converting the polynomial to an expression, fully pinned to
the inputs:

  * with no caller symbols, the expression is built from the term data using the
    ring's own symbols;
  * with caller symbols whose count differs from the number of generators, the
    result is an error;
  * with caller symbols of the correct count, the expression is built from the
    term data using exactly those caller symbols.

The three cases partition every input, so the result is determined in all
cases. -/
def problem_spec_asExpr
    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb)
    (result : Except Unit SymExpr) : Prop :=
  (symbols.isEmpty → result = .ok (exprFromDict d ringSymbols)) ∧
  (¬ symbols.isEmpty → symbols.length = ngens →
      result = .ok (exprFromDict d symbols)) ∧
  (¬ symbols.isEmpty → symbols.length ≠ ngens → result = .error ())
-- post-conditions-end

-- impl-start
def implementation_asExpr
    (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :
    Except Unit SymExpr := Id.run do
  let mut gens := symbols
  if ¬ symbols.isEmpty ∧ symbols.length ≠ ngens then
    return .error ()
  else
    gens := ringSymbols
  return .ok (exprFromDict d gens)
-- impl-end

-- proof-start
-- Carried gold proof body: it closes against the correct (post-patch) impl, but
-- the pre-patch impl above always overwrites the generators with the ring's own
-- symbols, ignoring a correctly-sized caller list, so clause 2 of the spec is
-- unprovable here (G-DIFF).
theorem correct_asExpr :
    ∀ (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb),
      problem_spec_asExpr d ngens ringSymbols symbols
        (implementation_asExpr d ngens ringSymbols symbols) := by
  intro d ngens ringSymbols symbols
  unfold problem_spec_asExpr implementation_asExpr
  simp only [Id.run, bind, pure]
  refine ⟨?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2; simp [h1, h2]
  · intro h1 h2; simp [h1, h2]
-- proof-end
