import Mathlib
-- imports-end

/-!
Reducing the concrete-integer factors of a product against a divisor.

A product is modelled as a list of factors, each of which is either a concrete
integer coefficient or a symbolic atom (a non-numeric factor, identified
opaquely). Given an integer divisor `q`, the desired normalisation rewrites the
product so that every concrete-integer factor is taken modulo `q`, EXCEPT when
that residue is zero, in which case the factor is left untouched; symbolic
factors are always preserved exactly.

The remainder convention is Python's: the residue carries the sign of the
divisor (floored division). When the divisor equals one the product is returned
unchanged (every integer is congruent to zero modulo one, so reducing would
erase information rather than simplify). The normalisation is total: for a
zero divisor the floored remainder of `n` is `n` itself, so every factor is
kept unchanged (a zero divisor never reaches this normalisation in practice —
it is rejected upstream — and the total extension is the identity).

Every factor of the result is pinned to its input factor, so no part of the
output is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-factor
-- residue is modeled DEEPLY via exact integer arithmetic (floored remainder),
-- and the symbolic factors are carried through structurally, so no
-- `opaque`/`axiom` callee contract is needed. The R/I refinement of the residue
-- arithmetic is differential-tested by G-CONF.
-- axioms-end

-- pure-start
/-- A single factor of a product: either a concrete integer coefficient, or a
symbolic atom identified by an opaque tag. -/
inductive Factor where
  | coeff (n : Int)
  | sym (id : Nat)
deriving DecidableEq, Repr

/-- The Python-convention (floored) remainder `a mod b`: the residue carries the
sign of `b`. Defined via `Int.fdiv` so `intMod (-7) 2 = 1` and `intMod 7 (-2) = -1`. -/
def intMod (a b : Int) : Int := a - b * (Int.fdiv a b)

/-- Reduce one factor against the divisor `q`: a concrete coefficient `n` becomes
its residue `intMod n q` unless that residue is zero (then `n` is kept); a
symbolic factor is preserved. -/
def reduceFactor (q : Int) (f : Factor) : Factor :=
  match f with
  | Factor.coeff n => if intMod n q ≠ 0 then Factor.coeff (intMod n q) else Factor.coeff n
  | Factor.sym s => Factor.sym s

/-- Front-recursive fold applying `reduceFactor q` to every factor of a product. -/
def reduceFactors (q : Int) : List Factor → List Factor
  | [] => []
  | f :: fs => reduceFactor q f :: reduceFactors q fs
-- pure-end

-- post-conditions-start
/-- The normalised product: when the divisor is one the factor list is returned
unchanged; otherwise every concrete-integer factor is reduced against `q`
(non-zero residues only) while symbolic factors are preserved. The result is
pinned factor-for-factor to the input. -/
def problem_spec_modFactors (q : Int) (factors result : List Factor) : Prop :=
  result = (if q = 1 then factors else reduceFactors q factors)
-- post-conditions-end

-- impl-start
def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
  -- PRE-PATCH (buggy): the product's factors are returned unchanged; concrete
  -- integer coefficients are never reduced against the divisor.
  return factors
-- impl-end

-- proof-start
theorem correct_modFactors :
    ∀ (q : Int) (factors : List Factor),
      problem_spec_modFactors q factors (implementation_modFactors q factors) := by
  sorry
-- proof-end
