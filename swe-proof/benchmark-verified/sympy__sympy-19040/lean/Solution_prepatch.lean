import Mathlib
-- imports-end

/-!
Twin-artifact bundle: factorization of a MULTIVARIATE polynomial over an
algebraic number field. The procedure makes the polynomial monic, discards the
trivial (degenerate-degree) case, then builds a square-free norm over the ground
domain, factors that norm, lifts each ground factor back over the extension and
recovers multiplicities by trial division.

Desired behaviour pinned here: the square-free norm — and therefore the ground
factor list that the recovered factors come from — is taken of the FULL monic
polynomial, so every irreducible component of the input is represented (including
components that do not involve the principal variable). The trivial-degree case
returns the leading coefficient with no factors; otherwise the leading
coefficient is returned unchanged together with the recovered factor list.
-/

-- axioms-start
-- The polynomial-algebra operations the procedure calls are UNCHANGED by the
-- modeled behaviour; they are declared here as opaque signatures (identity
-- carriers) so they can appear in the executable skeleton. None of them is the
-- operation whose data flow this bundle pins. The construction agent ships NO
-- `_prop` axiom (the obligation is a structural unfolding plus one list-shape
-- induction); the proof agent may add `_prop` axioms only if it gets stuck.

/-- A polynomial over the algebraic extension field. Opaque identity carrier. -/
structure ExPoly where val : Nat deriving Inhabited, DecidableEq
/-- A polynomial over the ground domain. Opaque identity carrier. -/
structure GrPoly where val : Nat deriving Inhabited, DecidableEq
/-- A coefficient (element of the extension field). Opaque identity carrier. -/
structure ExCoeff where val : Nat deriving Inhabited, DecidableEq

/-- Leading coefficient over the ground. -/
opaque groundLC : ExPoly → ExCoeff
/-- Make the polynomial monic over the ground. -/
opaque groundMonic : ExPoly → ExPoly
/-- Per-variable degree list. -/
opaque degreeList : ExPoly → List Int
/-- Square-free part w.r.t. the principal variable. -/
opaque sqfPart : ExPoly → ExPoly
/-- Square-free norm: returns a shift count `s`, an extension polynomial `g`, and
the norm `r` over the ground domain. -/
opaque sqfNorm : ExPoly → (Nat × ExPoly × GrPoly)
/-- Factor a ground polynomial into ground factors (multiplicity attached). -/
opaque factorListInclude : GrPoly → List (GrPoly × Nat)
/-- The shift polynomial built from the shift count, used to compose recovered
factors back into the original variable. -/
opaque raiseShift : Nat → ExPoly
/-- One recovery step: convert a ground factor into the extension, refine the
running gcd carrier, and compose with the shift. Returns the recovered factor and
the updated gcd carrier. -/
opaque recoverOne : ExPoly → ExPoly → GrPoly → (ExPoly × ExPoly)
/-- Recover multiplicities of the given factors w.r.t. a polynomial by trial
division. -/
opaque trialDivision : ExPoly → List ExPoly → List (ExPoly × Nat)
-- axioms-end

-- pure-start
/-- The trivial-degree test: every per-variable degree is non-positive. -/
def degreesNonpos (ds : List Int) : Bool := ds.all (· ≤ 0)

/-- Front-recursive recovery fold over the ground factor list, threading the gcd
carrier. With a single ground factor the recovered list is just the square-free
part; otherwise each ground factor is lifted by one recovery step. -/
def recoverLoop (H : ExPoly) : ExPoly → List (GrPoly × Nat) → List ExPoly
  | _, [] => []
  | g, entry :: rest =>
      let (h, g') := recoverOne H g entry.1
      h :: recoverLoop H g' rest

/-- The recovered factor list: the single-factor short-circuit, else the loop. -/
def recoverFactors (H g : ExPoly) (factors0 : List (GrPoly × Nat)) (fSqf : ExPoly) :
    List ExPoly :=
  if factors0.length = 1 then [fSqf] else recoverLoop H g factors0
-- pure-end

-- post-conditions-start
/-- The factorization result. The leading coefficient component equals the
input's ground leading coefficient. When all per-variable degrees of the monic
polynomial are non-positive the factor component is empty. Otherwise the factor
component is obtained by trial division of the monic polynomial against the
factors recovered from the square-free norm OF THE MONIC POLYNOMIAL — its shift,
gcd carrier and ground factor list — falling back to the square-free part when
the norm factors into a single ground factor. -/
def problem_spec_extFactor (f : ExPoly) (result : ExCoeff × List (ExPoly × Nat)) : Prop :=
  let lc := groundLC f
  let mono := groundMonic f
  result.1 = lc ∧
  (degreesNonpos (degreeList mono) = true → result.2 = []) ∧
  (degreesNonpos (degreeList mono) = false →
    result.2 = trialDivision mono
      (recoverFactors (raiseShift (sqfNorm mono).1) (sqfNorm mono).2.1
        (factorListInclude (sqfNorm mono).2.2) (sqfPart mono)))
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) skeleton: the square-free norm is taken of the square-free
PART of the monic polynomial rather than the full monic polynomial. The
square-free part w.r.t. the principal variable omits components that do not
involve the principal variable, so the ground factor list it yields — and hence
the recovered factors after trial division — leaves those components out. On the
issue's input the norm of the part factors into a single ground factor, so the
result is the single square-free part and the missing component is dropped. -/
def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
  let lc := groundLC f
  let mono := groundMonic f
  if degreesNonpos (degreeList mono) then
    return (lc, [])
  let fSqf := sqfPart mono
  let (s, g, r) := sqfNorm fSqf
  let factors0 := factorListInclude r
  let mut factors : List ExPoly := []
  if factors0.length = 1 then
    factors := [fSqf]
  else
    let H := raiseShift s
    let mut gCur := g
    for entry in factors0 do
      let (h, g') := recoverOne H gCur entry.1
      gCur := g'
      factors := factors ++ [h]
  return (lc, trialDivision mono factors)
-- impl-end

-- proof-start
theorem correct_extFactor : ∀ f : ExPoly,
    problem_spec_extFactor f (implementation_extFactor f) := by
  sorry   -- carries the gold proof; UNCLOSABLE against the buggy impl (G-DIFF):
          -- the spec's discriminating clause pins the factor component to trial
          -- division against factors recovered from `sqfNorm mono` (the full
          -- monic), while the buggy impl recovers from `sqfNorm (sqfPart mono)`;
          -- since `sqfNorm` is opaque these are not provably equal, so the
          -- third conjunct cannot be discharged.
-- proof-end
