import Velvet.Std
-- imports-end

/- Total correctness: the real construction is a straight-line build of a
   fixed-shape expression object (a bounded tree of constructor applications)
   and always terminates, so a diverging implementation must NOT satisfy this
   spec. Partial correctness would let a non-terminating body discharge the
   postcondition vacuously — an implementation that never produces the
   closed-form object at all. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The desired behaviour is the construction of a specific
   closed-form expression object for the cumulative distribution of a
   bounded-support, two-parameter continuous distribution; that object is
   modeled DEEPLY as a transparent expression value in the `pure` region
   (`arcsinExprCdf`), parameterised by the symbolic operands. No module-level
   `axiom` is used or required. The carrier↔library-object correspondence is a
   pure constructor bijection, validated end-to-end against the real library by
   the conformance check (G-CONF). -/
-- axioms-end

-- pure-start
/- A finite expression carrier: the fragment of symbolic terms that this
   distribution's closed-form cumulative function is built from. It is an
   honest data carrier — each node is a concrete constructor referring to its
   sub-operands, with NO opaque "answer" node. The desired output is produced
   by applying these constructors to the actual symbolic operands, so a builder
   that did not compute it cannot echo an answer key: it would have to emit a
   different tree.

   Constructors model exactly the library term-builders the closed form uses:
   the rational unit/zero and small integer literals, the circle constant, the
   field operations (`div`/`mul`/`sub`), the inverse-sine and square-root
   functions, the two order relations (strict `lt` and non-strict `le`), the
   always-true guard `top`, and a three-clause case split `piecewise3`. The
   `integralFallback` node models the SEPARATE, generic value produced when no
   closed form is supplied and the cumulative function is instead obtained by
   the default definite-integration route (used only by the pre-change
   skeleton). -/
inductive Expr where
  | zero
  | one
  | natLit (n : Nat)
  | pi
  | div (a b : Expr)
  | mul (a b : Expr)
  | sub (a b : Expr)
  | asin (e : Expr)
  | sqrt (e : Expr)
  | lt (a b : Expr)
  | le (a b : Expr)
  | top
  | piecewise3 (v1 c1 v2 c2 v3 c3 : Expr)
  | integralFallback (lo hi : Expr)
  deriving DecidableEq, Inhabited

/- The closed-form cumulative distribution of the two-parameter,
   bounded-support distribution whose density is supported on the open interval
   between its two endpoints, as a function of its lower endpoint `a`, its upper
   endpoint `b`, and the evaluation point `x`. It is a three-clause case split:

     • below the lower endpoint  (`x < a`)            → `0`
     • on the support up to `b`  (`x ≤ b`)            → `2·asin(√((x-a)/(b-a)))/π`
     • otherwise                                       → `1`

   This is the per-operand expansion of the desired result object: every node is
   built from `a`, `b`, `x`, the rational constants, and `π` — the result is
   forced to be *produced by* these operands, never an opaque constant. -/
def arcsinExprCdf (a b x : Expr) : Expr :=
  Expr.piecewise3
    Expr.zero (Expr.lt x a)
    (Expr.div
      (Expr.mul (Expr.natLit 2)
        (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
      Expr.pi) (Expr.le x b)
    Expr.one Expr.top

@[grind] lemma arcsinExprCdf_def (a b x : Expr) :
    arcsinExprCdf a b x =
      Expr.piecewise3
        Expr.zero (Expr.lt x a)
        (Expr.div
          (Expr.mul (Expr.natLit 2)
            (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
          Expr.pi) (Expr.le x b)
        Expr.one Expr.top := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the closed-form cumulative distribution value for the two-parameter,
   bounded-support continuous distribution from its lower endpoint `a`, upper
   endpoint `b`, and evaluation point `x`.

   Desired behaviour: the cumulative distribution must be returned as the exact
   closed-form case split below — `0` below the lower endpoint, the inverse-sine
   expression on the support, `1` above the upper endpoint — rather than left as
   a generic definite-integral object (which is what is produced when no closed
   form is available and is, for this distribution, not a usable result). The
   output object is pinned operand-by-operand so that only the intended
   expression — not a numerically-equal but differently-shaped one — satisfies
   the contract. -/
method arcsinCdfBuild (a : Expr) (b : Expr) (x : Expr) return (out : Expr)
  ensures out = arcsinExprCdf a b x
  do
    -- impl-start
    -- Build the three-clause closed form directly from the operands `a`, `b`,
    -- `x`. The middle clause is the inverse-sine expression on the support.
    let onSupport : Expr :=
      Expr.div
        (Expr.mul (Expr.natLit 2)
          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
        Expr.pi
    return Expr.piecewise3
      Expr.zero (Expr.lt x a)
      onSupport (Expr.le x b)
      Expr.one Expr.top
    -- impl-end

prove_correct arcsinCdfBuild by
  loom_solve
