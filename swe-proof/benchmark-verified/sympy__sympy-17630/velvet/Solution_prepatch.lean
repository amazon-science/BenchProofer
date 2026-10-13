import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The distinguished combining operator that denotes additive composition (an
   UNCHANGED module-level constant / class object — it is consulted, not
   redefined). The operator in effect is compared against it to decide which
   recombination rule applies. Declared `opaque` (not `axiom`) so it is
   computable inside the executable `do` block. Provenance: mapping.md. As a
   free constant with no asserted `ensures`, there is nothing to validate
   against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque additiveOp : Int

/- Compose a non-empty homogeneous collection of matrix-valued terms under the
   ADDITIVE operator, yielding a single matrix-valued term. An opaque
   deterministic UNCHANGED callee over expression handles; determinism is all
   the proof relies on (a given argument denotes one and the same result).
   `opaque` for do-block codegen. Provenance: mapping.md. -/
opaque additiveCombine : Int → Int

/- Compose a non-empty homogeneous collection of matrix-valued terms under the
   MULTIPLICATIVE operator, yielding a single matrix-valued term. A second,
   DISTINCT opaque deterministic UNCHANGED callee over handles (a different
   composition than `additiveCombine`). `opaque` for do-block codegen.
   Provenance: mapping.md. -/
opaque multiplicativeCombine : Int → Int

/- Build the argument bundle that places a leading scalar-valued term in front
   of a collection of matrix-valued terms (a deterministic UNCHANGED bundle
   constructor over handles). Provenance: mapping.md. -/
opaque withLeadingScalar : Int → Int → Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A construction-finalization step that recombines a single algebraic node
   after its child terms have been partitioned. This case handles a node whose
   children are a NON-EMPTY collection of matrix-valued terms with NO
   scalar-valued terms left to compose among them. The node was produced under
   one of two combining operators — additive or multiplicative — and the
   recombination rule differs by operator:

     * under the ADDITIVE operator, the result is the additive composition of
       exactly the matrix-valued terms;
     * under the MULTIPLICATIVE operator, the result is the multiplicative
       composition of those matrix-valued terms with a leading scalar-valued
       term placed in front of them.

   The behavior pinned here: the recombination is governed by WHICH combining
   operator is in effect, and for the additive operator the matrix-valued terms
   are composed ON THEIR OWN — no leading scalar-valued term is placed in front
   of them. The matrix-valued terms denote a matrix-valued result; placing a
   scalar-valued term in front of them under the additive operator would
   otherwise be free to collapse the result to a scalar-valued term, which is
   not matrix-valued.

   `op` (the combining operator in effect), `leadingScalar` (the scalar-valued
   term the multiplicative case places in front), and `matrixTerms` (the
   partitioned collection of matrix-valued terms) are read-only opaque
   expression handles (not `mut`); the routine computes a single handle and
   mutates nothing (directive 5). The composers, the leading-scalar
   constructor, and the additive-operator constant are opaque deterministic
   UNCHANGED callees/constants over handles. -/
method recombineMatrixNode (op : Int) (leadingScalar : Int) (matrixTerms : Int)
    return (out : Int)
  ensures out =
    (if op = additiveOp
     then additiveCombine matrixTerms
     else multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms))
  do
    -- impl-start
    -- Pre-image: the leading scalar-valued term is placed in front of the
    -- matrix-valued terms UNCONDITIONALLY — under BOTH operators, including the
    -- additive operator. The combiner is still selected by the operator, but
    -- the additive case wrongly carries the leading scalar, so it diverges from
    -- the spec's additive composition of the matrix-valued terms alone.
    if op = additiveOp then
      return additiveCombine (withLeadingScalar leadingScalar matrixTerms)
    else
      return multiplicativeCombine (withLeadingScalar leadingScalar matrixTerms)
    -- impl-end

prove_correct recombineMatrixNode by
  loom_solve
