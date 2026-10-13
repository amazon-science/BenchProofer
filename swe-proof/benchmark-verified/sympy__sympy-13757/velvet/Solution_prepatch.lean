import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The value the product takes when it IS carried out is
--  built by combination machinery this behaviour does NOT change; its result is
--  supplied to the operation as a free input (`productValue`), so the
--  postcondition holds for EVERY such product value — strictly weaker than any
--  concrete multiplier, hence no contract is owed (directive 7). Whether the two
--  factors combine into a single value is likewise a property of that unchanged
--  combination machinery; it is observed directly as an input, not via any
--  callee. There is no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The two observable shapes the result of forming the product of an ordinary
   expression and a polynomial can take:

   - `carriedOut`  — the product is actually performed: the two factors are
                     combined into a single evaluated value.
   - `formalProduct` — the product is left standing as an unevaluated formal
                     product of the two factors, i.e. nothing is computed. -/
inductive ProductForm where
  | carriedOut
  | formalProduct
  deriving DecidableEq, Inhabited

/- The observable result of forming the product of an ordinary expression and a
   polynomial, reduced to the two observations the desired behaviour
   distinguishes:

   - `form`  — whether the product was carried out (evaluated into a single
               value) or left as a formal, unevaluated product (mapping.md §2).
   - `value` — the value the product carries when it IS carried out: the
               evaluated product of the two factors. The combination that
               produces it is machinery the desired behaviour does NOT change,
               so it is supplied to the operation as a free input. -/
structure ProductResult where
  form : ProductForm
  value : List Int
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Form the product of an ordinary expression (on the left) and a polynomial (on
   the right).

   Desired behaviour (reported symptom: such a product "does not evaluate" when
   the expression is the left operand): when the polynomial is the right operand,
   the product must be treated the same way it already is when the polynomial is
   the left operand — namely, whenever the two factors do combine into a single
   value, that product is CARRIED OUT (actually evaluated into one value) instead
   of being left as a formal, unevaluated product of the two factors.

   Not every pair of factors combines into a single value: some left expressions
   simply do not merge with the polynomial, and for those the product is
   genuinely left formal. Whether the two factors combine into a single value is
   a property of the surrounding (unchanged) combination machinery, observed here
   directly as the input `factorsCombineIntoPolynomial`; only its truth value
   matters (mapping.md §2). The operation must:

   - carry the product out (a single evaluated value) exactly when the two
     factors combine, and
   - leave it as a formal, unevaluated product otherwise.

   The value the carried-out product takes is the evaluated product of the two
   factors, which the surrounding (unchanged) machinery supplies; this step does
   not recompute it. That supplied value is read-only (not `mut`) and must
   survive into the result unchanged (directive 5): the operation decides the
   SHAPE of the result and preserves the supplied product value. -/
method formExpressionTimesPolynomial
    (productValue : List Int) (factorsCombineIntoPolynomial : Bool)
    return (out : ProductResult)
  ensures out.form = (if factorsCombineIntoPolynomial
                      then ProductForm.carriedOut
                      else ProductForm.formalProduct)
  ensures factorsCombineIntoPolynomial = true → out.value = productValue
  do
    -- impl-start
    -- Pre-image skeleton (the bug): the product of an ordinary LEFT expression
    -- and a right-hand polynomial is NOT handled the way the polynomial-on-the-
    -- left product is — the left-operand product is never carried out, it is
    -- always left as a formal, unevaluated product of the two factors, EVEN when
    -- the two factors do combine into a single value. The frozen spec requires
    -- the product be carried out whenever the factors combine
    -- (`factorsCombineIntoPolynomial = true`), so prove_correct MUST fail on
    -- `out.form = carriedOut` for that case.
    let form := ProductForm.formalProduct
    return { form := form, value := productValue }
    -- impl-end

prove_correct formExpressionTimesPolynomial by
  loom_solve
