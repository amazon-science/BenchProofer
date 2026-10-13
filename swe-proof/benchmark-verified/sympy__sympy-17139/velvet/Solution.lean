import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee.

   The only unchanged sub-steps this step routes through are modeled WITHOUT a
   contract, as strictly-weaker free values: whether the input is a power of the
   shape this rewrite targets (`matchesPow`) and the value the downstream rewrite
   would produce for an in-range real exponent (`transformed`). The desired
   behaviour holds for EVERY value of them, so neither is owed an axiom
   (directive 7). The single behaviour this bundle pins — a power whose exponent
   is not a real number is returned unchanged — is decided structurally from the
   exponent's imaginary part (`expIsReal`, `pure` region). There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque algebraic expression. Only its identity (equality) is observed: the
   rewrite either returns its input expression unchanged or replaces it with the
   downstream result, and the desired behaviour constrains only WHICH of those
   two it is (mapping.md §2). -/
structure Expr where
  tag : Nat
  deriving DecidableEq

/- An exponent, carried as a number with a real and an imaginary component. The
   only property the desired behaviour consults is whether the exponent is a real
   number, i.e. has no imaginary component. -/
structure Cexp where
  re : Int
  im : Int
  deriving DecidableEq

/- An exponent is real exactly when its imaginary component is zero. Ordering
   comparisons against a number are only meaningful for a real number; a number
   with a nonzero imaginary component is not comparable. -/
def expIsReal (e : Cexp) : Bool := e.im == 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- One rewrite step on a candidate power expression. `rv` is the input
   expression; `exp` is its exponent; `matchesPow` says whether the input is a
   power of the kind this rewrite targets (its base is the trigonometric function
   being rewritten); `transformed` is the value the downstream rewrite produces
   for a real, in-range exponent. All are read-only.

   Desired behaviour: an expression that is not a targeted power is returned
   unchanged; a targeted power whose exponent is NOT a real number is also
   returned unchanged (its exponent cannot be compared by magnitude, so no
   rewrite is attempted); only a targeted power with a real exponent proceeds to
   the downstream rewrite. The middle clause is the behaviour at issue: a
   non-real (e.g. purely or partly imaginary) exponent must leave the expression
   untouched rather than being subjected to an ordering comparison. -/
method powerRewriteStep (rv : Expr) (exp : Cexp) (matchesPow : Bool)
    (transformed : Expr) return (out : Expr)
  ensures out = (if matchesPow then (if expIsReal exp then transformed else rv) else rv)
  ensures (matchesPow ∧ ¬ expIsReal exp) → out = rv
  ensures (matchesPow ∧ expIsReal exp) → out = transformed
  ensures ¬ matchesPow → out = rv
  do
    -- impl-start
    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.
    if !matchesPow then
      return rv
    else
      -- Guard 2: a non-real exponent is not comparable by magnitude, so the
      -- expression is returned unchanged rather than rewritten.
      if !expIsReal exp then
        return rv
      else
        -- Real, targeted power: proceed to the downstream rewrite.
        return transformed
    -- impl-end

prove_correct powerRewriteStep by
  loom_solve
