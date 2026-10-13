import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The function being simplified, as an opaque deterministic map over expression
   handles (an UNCHANGED elementary callee — it is consulted, not redefined).
   Determinism is all the proof relies on: the value computed from the periodic
   part is the same value later inspected. Declared `opaque` (not `axiom`) so it
   is computable inside the executable `do` block. Provenance: mapping.md.
   Because it is a free function with no asserted `ensures`, there is nothing to
   validate against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque primaryEval : Int → Int

/- The reciprocal-family sibling function, likewise an opaque deterministic
   UNCHANGED callee over expression handles. `opaque` for do-block codegen.
   Provenance: mapping.md. -/
opaque siblingEval : Int → Int

/- A second, DISTINCT opaque elementary map over handles — a different function
   in the same trigonometric family. Used only to exhibit that the branch must
   not be governed by an unrelated quantity (the pre-image inspects this one).
   Provenance: mapping.md. -/
opaque cofamilyEval : Int → Int

/- The distinguished "directed-infinity" sentinel expression handle (an
   UNCHANGED module constant / singleton). Provenance: mapping.md. -/
opaque directedInfinity : Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An automatic simplifier for a hyperbolic-cotangent-like function handles the
   case where its argument decomposes into a remainder part `x` and a multiple
   of a distinguished imaginary period `m`. When that periodic part is present,
   the simplifier evaluates the SAME function on the periodic part and inspects
   the resulting expression:

     * if evaluating the function on the periodic part yields the
       directed-infinity sentinel, the simplified result is the function applied
       to the remainder part;
     * otherwise (the evaluation yields the finite/zero alternative), the
       simplified result is the reciprocal-family sibling function applied to
       the remainder part.

   The behavior pinned here: the branch that chooses between these two results
   is governed by the value obtained by evaluating the function on the PERIODIC
   PART — the quantity just computed from `m` — and by no other quantity. The
   result is the remainder-part evaluation of the same function exactly when
   that computed value is the directed-infinity sentinel, and the sibling on the
   remainder part otherwise.

   `x` and `m` are read-only opaque expression handles (not `mut`); the routine
   computes a single handle and mutates nothing (directive 5). The elementary
   functions consulted are opaque deterministic callees over handles; the
   sentinel is an opaque distinguished handle. -/
method cothEvalPeriodic (x : Int) (m : Int) return (out : Int)
  ensures out = (if primaryEval m = directedInfinity then primaryEval x else siblingEval x)
  do
    -- impl-start
    -- Evaluate the same function on the periodic part, then branch on THAT
    -- just-computed value: the function on the remainder when it is the
    -- directed-infinity sentinel, the sibling on the remainder otherwise.
    let computed := primaryEval m
    if computed = directedInfinity then
      return primaryEval x
    else
      return siblingEval x
    -- impl-end

prove_correct cothEvalPeriodic by
  loom_solve
