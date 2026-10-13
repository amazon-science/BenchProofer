import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The conversion that renders a sparse multivariate datum (a map from monomials
   to ground coefficients) into a symbolic expression over a GIVEN ordered list
   of generator names. An UNCHANGED helper the operation delegates to: modeled as
   an uninterpreted function because the operation never inspects the expression
   it produces — its only responsibility is to decide WHICH list of generator
   names to hand over, so no contract is owed about the rendered value
   (directive 7). The datum, each generator name, and the produced expression are
   opaque handles (`Int`); the bijection to the repository value space is in
   mapping.md (G-AX / G-CONF use it). Provenance + executable soundness check:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque exprFromDict : Int → List Int → Int
-- axioms-end

-- pure-start
/- The only failure the desired behavior distinguishes: a caller-supplied list of
   generator names whose length does not match the number of generators the datum
   lives over. -/
inductive AsExprErr where
  | wrongNumberOfSymbols
  deriving DecidableEq

/- The intended outcome of rendering the datum `d` over an optional caller list of
   generator names `symbols`, given the datum's own ordered generator names
   `ringSymbols` (whose length is the number of generators):

     * if the caller supplies NO names, render over the datum's own names;
     * otherwise, if the supplied list has exactly one name per generator, render
       over the SUPPLIED names (they are honored, not discarded);
     * otherwise the request is rejected.

   Honoring a correctly-sized caller list is the behavior the public problem
   statement requires. -/
def asExprSpec (d : Int) (ringSymbols : List Int) (symbols : List Int) :
    Except AsExprErr Int :=
  if symbols.isEmpty then
    Except.ok (exprFromDict d ringSymbols)
  else
    if symbols.length = ringSymbols.length then
      Except.ok (exprFromDict d symbols)
    else
      Except.error AsExprErr.wrongNumberOfSymbols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a sparse multivariate datum as a symbolic expression, letting the caller
   choose the generator names.

   `d` is the datum (a map from monomials to ground coefficients) and `ringSymbols`
   are the datum's own ordered generator names — both read-only, so neither is
   `mut`. `symbols` is the caller's optional list of names. Desired behavior: when
   the caller supplies a list whose length equals the number of generators
   (`ringSymbols.length`), the expression must be rendered over the caller's names;
   when the caller supplies nothing, the datum's own names are used; when the
   caller supplies a list of any other length, the request is rejected. The
   expression itself is produced by the unchanged rendering helper from the datum
   and the chosen names; the operation's only responsibility is to pick that list
   of names correctly (mapping.md §2). -/
method asExpr (d : Int) (ringSymbols : List Int) (symbols : List Int)
    return (out : Except AsExprErr Int)
  ensures out = asExprSpec d ringSymbols symbols
  do
    -- impl-start
    -- Choose the list of generator names to render over, then hand the datum and
    -- that list to the unchanged renderer. The caller's own names are honored
    -- when one per generator is supplied; the datum's names are used when the
    -- caller supplies none; any other caller length is rejected.
    let mut chosen : List Int := symbols
    if symbols.isEmpty then
      chosen := ringSymbols
    else
      if symbols.length = ringSymbols.length then
        chosen := symbols
      else
        return Except.error AsExprErr.wrongNumberOfSymbols
    return Except.ok (exprFromDict d chosen)
    -- impl-end

prove_correct asExpr by
  loom_solve <;> simp_all [asExprSpec]
