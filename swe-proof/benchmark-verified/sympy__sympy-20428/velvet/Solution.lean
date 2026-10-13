import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two zero-tests an element can be subjected to —
--  the mathematical/identical zero test and the bare comparison against the
--  literal zero — are UNCHANGED machinery; they are abstracted to the two
--  boolean observations of `SymExpr` below and exercised structurally by
--  G-CONF (conformance_check.py), and their relationship is validated against
--  the real element by G-AX (axiom_check.py). Nothing is borrowed from an
--  oracle, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- A field element of the symbolic-expression domain, reduced to the two
   observations a zero-test can depend on:

     * `identicallyZero` — whether the element is mathematically (identically)
       zero: it denotes the value zero, however its representation is written;
     * `literalZero`     — whether the element's representation is the bare
       literal zero (a far coarser test: it can be `false` for an element that
       nonetheless denotes zero).

   A representation that is the literal zero always denotes zero, so
   `literalZero` implies `identicallyZero`; the converse fails — an element can
   denote zero without being written as the literal zero. -/
structure SymExpr where
  identicallyZero : Bool
  literalZero     : Bool
  deriving DecidableEq, Inhabited, Repr

/- The intended truth value of a symbolic field element: it counts as nonzero
   exactly when it is NOT identically zero. An element that denotes zero — even
   one whose representation is not the literal zero — counts as zero. -/
def nonzeroSpec (e : SymExpr) : Bool := !e.identicallyZero
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a symbolic field element is nonzero.

   Desired behavior: an element counts as nonzero exactly when it is not
   identically (mathematically) zero. It is NOT enough to compare the element's
   representation against the literal zero — a representation can differ from the
   literal zero and yet still denote the value zero, and such an element must be
   reported as zero, not nonzero. (Reporting a zero-denoting element as nonzero
   is what lets a stale zero survive where downstream machinery assumes a genuine
   zero has been discarded, the failure the public problem statement reports.)

   `e` is read-only (it is not `mut`): the decision reads the element and mutates
   nothing it is handed (directive 5). The element is modeled by its two relevant
   observations — whether it is identically zero and whether its representation is
   the bare literal zero (mapping.md §2); the former is the one that decides the
   outcome. A literal-zero representation always denotes zero, so the input
   satisfies `literalZero → identicallyZero`. -/
method symbolicNonzero (e : SymExpr) return (out : Bool)
  require e.literalZero → e.identicallyZero
  ensures out = nonzeroSpec e
  do
    -- impl-start
    -- Report nonzero iff the element is not identically zero — the mathematical
    -- zero test, not a comparison of the representation against the literal zero.
    return !e.identicallyZero
    -- impl-end

prove_correct symbolicNonzero by
  loom_solve
  simp_all [nonzeroSpec]
