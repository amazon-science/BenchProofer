import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The tiny strictly-positive floor `eps` is taken as a
--  plain positive input — the operation under spec does not change how that
--  floor value is produced; its strict positivity is captured by `require`.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A logarithmic intensity mapping is only defined for strictly positive
   magnitudes: the logarithm of zero or of a negative magnitude has no finite
   value. Before such a mapping is applied, its lower scale bound must therefore
   be sanitised to a strictly positive figure.

   The sanitised lower bound honours exactly one rule: any lower bound that is
   not strictly positive — whether it is zero or negative — is replaced by a
   constant tiny strictly-positive floor; a lower bound that is already strictly
   positive is left untouched.

   The tiny floor is read-only (not `mut`) and is always strictly positive (it
   is a constant smallest-representable positive figure for the working precision);
   the incoming lower bound is read-only too. The operation derives a single
   bound and mutates nothing (directive 5). Both inputs and the result are
   modeled as exact rationals (`Rat`): the discriminating behaviour is the
   sign/zero boundary of the lower bound, an order-only property that is
   precision-independent, so an exact ordered carrier is faithful. -/
method logNormVmin (sVmin : Rat) (eps : Rat) return (out : Rat)
  require eps > 0
  ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)
  do
    -- impl-start
    if sVmin ≤ 0 then
      return eps
    else
      return sVmin
    -- impl-end

prove_correct logNormVmin by
  loom_solve
