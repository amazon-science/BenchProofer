import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No module-level consumed `axiom`. The one community callee modeled here is a
   structural-decomposition routine, captured below as the `fastSplit` method
   stub (its contract is the WEAKEST one the dispatch needs): it is only defined
   for sums whose terms each have a positive-rational square, and on that domain
   it always succeeds in producing a decomposition. Provenance + executable
   soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- A single addend of a sum, abstracted by exactly the three observations the
   decomposition decision depends on:
     * `sqRat`  — its square is a rational number;
     * `sqPos`  — its square is a positive number;
     * `depth`  — its nesting depth of square roots (0 for a plain atom). -/
structure Addend where
  sqRat : Bool
  sqPos : Bool
  depth : Nat
deriving DecidableEq, Inhabited

/- The possible outcomes of matching a sum against the shape `a + b·√r`:
   either a decomposition is produced (`matched`) or the sum has none
   (`empty`). These mirror the function's `[a, b, r]` vs `[]` results. -/
inductive Outcome where
  | empty
  | matched
deriving DecidableEq, Inhabited

/- The domain of the fast structural split: every term of the sum must have a
   positive-rational square. Only within this domain is the gcd-based split a
   well-defined total operation. -/
def allPosRat (xs : List Addend) : Bool :=
  xs.all (fun a => a.sqRat && a.sqPos)

/- The maximal square-root nesting depth among the terms of the sum (0 when the
   sum contains no nested radical at all). -/
def maxDepth (xs : List Addend) : Nat :=
  xs.foldl (fun m a => Nat.max m a.depth) 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The fast structural split of a sum into the `a + b·√r` shape via the common
   gcd of the (squared) surds. It is a PARTIAL operation: it is only defined for
   sums all of whose terms have a positive-rational square (`allPosRat`); on that
   domain it always yields a decomposition. Calling it outside that domain is not
   permitted — the precondition pins the domain so no caller may invoke it on a
   sum outside it. Models an unchanged community routine (mapping.md §3,
   G-AX-checked); read-only input (directive 5). -/
method fastSplit (xs : List Addend) return (r : Outcome)
  require allPosRat xs = true
  ensures r = Outcome.matched
  do
    -- impl-start
    return Outcome.matched
    -- impl-end

prove_correct fastSplit by
  loom_solve

/- Match a sum of terms against the shape `a + b·√r`, returning whether a
   decomposition exists. The decision proceeds in two regimes:

   * When every term of the sum has a positive-rational square, the sum lies in
     the domain of the fast structural split (`fastSplit`), which always produces
     a decomposition.
   * Otherwise the sum is routed to the general depth-based procedure: it yields
     no decomposition exactly when the sum contains no nested radical (its
     maximal root-nesting depth is 0); when some term is itself a radical it
     produces a decomposition.

   The fast split is invoked ONLY within its domain; the general regime is total.
   `xs` is read-only (directive 5). -/
method matchAddTerms (xs : List Addend) return (out : Outcome)
  ensures allPosRat xs = true → out = Outcome.matched
  ensures allPosRat xs = false → maxDepth xs = 0 → out = Outcome.empty
  ensures allPosRat xs = false → maxDepth xs ≠ 0 → out = Outcome.matched
  do
    -- impl-start
    -- Pre-patch dispatch: routes to the fast split whenever every term's square
    -- is merely rational, ignoring whether those squares are positive. A sum
    -- with a rational-but-non-positive square (e.g. an imaginary-unit term)
    -- thus reaches `fastSplit` outside its domain — the precondition cannot be
    -- discharged, exactly the out-of-domain invocation the issue exhibits.
    let r ← if xs.all (fun a => a.sqRat) then
        fastSplit xs
      else
        if maxDepth xs = 0 then
          pure Outcome.empty
        else
          pure Outcome.matched
    return r
    -- impl-end

prove_correct matchAddTerms by
  loom_solve
