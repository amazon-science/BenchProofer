import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The recoverable failure shape of the shared-factor computation: a polynomial
   error, raised when that computation is asked to work on operands outside the
   domain it supports. This is the only failure the desired behavior
   distinguishes; it is named in the public problem statement. -/
inductive PolyErr where
  | polynomialError
  deriving DecidableEq

/- The shared-factor computation over two operands (an UNCHANGED helper the
   region under specification consults; it is invoked, never redefined). It does
   NOT always succeed: on operands it cannot handle it fails with a polynomial
   error, which is reified here as the error leg of `Except`; otherwise it yields
   a factor. Declared `opaque` (not `axiom`) so it is computable inside the
   executable `do` block, and given NO `ensures` — the desired behavior assumes
   nothing about WHICH factor it returns, only how a success vs a failure is
   handled. Provenance + executable soundness check (that the real helper indeed
   fails with exactly this error on the problem's operands, so the recovery
   branch is reachable): mapping.md §3 / axiom_check.py (G-AX). -/
opaque commonFactor : Int → Int → Except PolyErr Int

/- The per-operand reduction applied only once a non-trivial shared factor has
   been found (an UNCHANGED helper on the success path; opaque, no asserted
   contract). It maps an operand and the factor to the reduced operand.
   Provenance: mapping.md §3. -/
opaque reduceTerm : Int → Int → Int
-- axioms-end

-- pure-start
/- The intended result of the shared-factor-extraction step, as the triple
   (factor, first operand, second operand):

     * if the shared-factor computation FAILS with a polynomial error, the step
       recovers locally — the factor is the trivial factor `1` and BOTH operands
       are returned unchanged. The failure is never propagated out;
     * if it succeeds with the trivial factor `1`, the operands are likewise left
       unchanged (no reduction is warranted);
     * if it succeeds with a non-trivial factor, each operand is reduced by that
       factor.

   The behavior pinned here is total: for every outcome of the (partial) shared-
   factor computation the step yields a well-defined triple and never fails. -/
def extractSpec (p : Int) (q : Int) : Int × Int × Int :=
  match commonFactor p q with
  | Except.error _ => (1, p, q)
  | Except.ok g =>
      if g = 1 then (g, p, q)
      else (g, reduceTerm p g, reduceTerm q g)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reduce a pair of operands by extracting a shared factor before further
   processing.

   Desired behavior: the step consults a shared-factor computation over the two
   operands. That computation does not always succeed — on operands outside its
   supported domain it fails with a polynomial error. When it fails, the step
   must RECOVER locally: take the shared factor to be the trivial factor `1`,
   leave both operands exactly as they were, and continue — the failure must NOT
   be propagated out (a propagated polynomial error is the defect the public
   problem statement reports). When it succeeds, the result is the usual one: the
   operands are left unchanged for a trivial factor, and reduced by the factor
   otherwise. In every case the step yields a result — a (factor, first operand,
   second operand) triple — and never itself fails.

   `p` and `q` are the read-only operands (not `mut`): the step computes a new
   triple and mutates neither input (directive 5). Operands and the factor are
   modeled as opaque handles (`Int`); the only distinguished handle is the
   trivial factor `1` (mapping.md §2). -/
method extractCommonFactor (p : Int) (q : Int)
    return (out : Except PolyErr (Int × Int × Int))
  ensures out = Except.ok (extractSpec p q)
  do
    -- impl-start
    -- Attempt the shared-factor computation and branch on its OUTCOME rather
    -- than letting a failure escape: a polynomial-error failure is recovered
    -- with the trivial factor `1` and the operands unchanged; a success either
    -- leaves the operands unchanged (trivial factor) or reduces each by the
    -- factor found. The whole step always returns a value.
    let result : Int × Int × Int :=
      match commonFactor p q with
      | Except.error _ => (1, p, q)
      | Except.ok g =>
          if g = 1 then (g, p, q)
          else (g, reduceTerm p g, reduceTerm q g)
    return Except.ok result
    -- impl-end

prove_correct extractCommonFactor by
  loom_solve
  simp_all [extractSpec]
