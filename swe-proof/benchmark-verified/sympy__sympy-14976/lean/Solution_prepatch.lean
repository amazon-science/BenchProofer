import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The only callee the
-- rendered string depends on is the module-name resolver, whose result for the
-- floating-point constructor is a constant module-qualified name; it is modeled
-- DEEPLY as the constant `mpfName` below (an A-reference validated by G-AX),
-- not axiomatized. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- The module-qualified name of the arbitrary-precision floating-point
constructor, as emitted by the printer's module-name resolver under its default
(fully-qualified) module setting: `mpmath.mpf`. -/
def mpfName : List Char := "mpmath.mpf".toList

/-- Decimal rendering of an integer, matching the textual form used when an
integer is substituted into a format string (sign-prefixed for negatives, no
leading sign for non-negatives). -/
def intText (n : Int) : List Char := (toString n).toList
-- pure-end

-- post-conditions-start
/-- A rational number with numerator `p` and denominator `q` is rendered for the
arbitrary-precision floating-point backend as the quotient of two backend
floating-point literals: the constructor applied to the numerator, a division
sign, then the constructor applied to the denominator — i.e.
`mpmath.mpf(<p>)/mpmath.mpf(<q>)`. Both operands carry the full-precision integer
text so neither is evaluated at reduced precision. -/
def problem_spec_mpfRational (p q : Int) (result : List Char) : Prop :=
  result =
    mpfName ++ "(".toList ++ intText p ++ ")/".toList ++
    mpfName ++ "(".toList ++ intText q ++ ")".toList
-- post-conditions-end

-- impl-start
/-- Pre-patch behavior: with no backend-specific rational renderer the value
falls back to the plain textual quotient `<p>/<q>`, dropping the backend
floating-point constructor entirely (so the operands are evaluated at reduced
precision). -/
def implementation_mpfRational (p q : Int) : List Char :=
  intText p ++ "/".toList ++ intText q
-- impl-end

-- proof-start
theorem correct_mpfRational : ∀ (p q : Int),
    problem_spec_mpfRational p q (implementation_mpfRational p q) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the fallback impl (G-DIFF)
-- proof-end
