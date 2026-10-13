import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The two shapes a failure of the univariate-relation solver can take when it is
   asked for the explicit solution set of a relation in one real variable.

     * `cannotSolve` — the solver reports that it is unable to produce an explicit
       solution set for this relation (the failure the desired behavior is allowed
       to turn into an explicit unevaluated condition set over the reals).
     * `other` — any other failure; it is NOT intercepted and always propagates
       out unchanged.

   The distinction is exactly the set of failure shapes the desired behavior
   distinguishes; provenance + executable soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
inductive SolveErr where
  | cannotSolve
  | other
  deriving DecidableEq

/- The univariate-relation solver the routine consults (an UNCHANGED helper that
   is invoked, never redefined). It does NOT always succeed: for some relations it
   returns an explicit solution set (an opaque handle `h`, carried verbatim — the
   routine never inspects its content); for others it fails, and the failure may be
   `cannotSolve` or `other`. Declared `opaque` (computable inside the `do` block)
   and given NO `ensures` — the desired behavior assumes nothing about WHICH set it
   returns, only how a success vs each failure shape is handled. Provenance +
   executable soundness check (that the real solver indeed signals `cannotSolve`
   on relations it cannot solve and returns a set on solvable ones):
   mapping.md §3.1 / axiom_check.py (G-AX). -/
opaque solveUnivariate : Int → Except SolveErr Int
-- axioms-end

-- pure-start
/- The result set of the routine.

     * `solverSet h` — the explicit solution set the solver produced, carried
       through verbatim as an opaque handle `h` (its content is never inspected).
     * `conditionOverReals rel` — the explicit unevaluated set
       `{x ∈ ℝ | rel holds}` determined ENTIRELY by the relation `rel` itself
       (a function of the input, not of any solver output). This is the set the
       desired behavior must return when the solver cannot solve the relation. -/
inductive SetVal where
  | solverSet (h : Int)
  | conditionOverReals (rel : Int)
  deriving DecidableEq

/- The intended result of producing the solution set of a relation in one real
   variable, as `Except SolveErr SetVal` (`error` = a failure propagates out,
   `ok` = a set is returned):

     * if the solver SUCCEEDS, its explicit solution set is returned verbatim;
     * if the solver reports it CANNOT SOLVE the relation, the routine does not
       fail: it returns the explicit unevaluated condition set over the reals
       built from the relation itself, `conditionOverReals rel`;
     * if the solver fails in any OTHER way, that failure propagates out
       unchanged — it is never intercepted.

   Only the `cannotSolve` failure is turned into an explicit condition set; every
   other case preserves the solver's behavior exactly. -/
def asSetSpec (rel : Int) : Except SolveErr SetVal :=
  match solveUnivariate rel with
  | Except.ok h => Except.ok (SetVal.solverSet h)
  | Except.error SolveErr.cannotSolve =>
      Except.ok (SetVal.conditionOverReals rel)
  | Except.error SolveErr.other => Except.error SolveErr.other
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the solution set of a relation in a single real variable.

   Desired behavior: the routine consults a univariate-relation solver. That
   solver does not always succeed — for some relations it cannot produce an
   explicit solution set and reports so. When the solver reports it cannot solve
   the relation, the routine must NOT let that failure escape; instead it returns
   the explicit unevaluated set of reals satisfying the relation,
   `conditionOverReals rel` — the obvious set determined by the relation itself
   (the missing behavior the public problem statement reports). When the solver
   succeeds, its explicit solution set is returned verbatim. Any other kind of
   solver failure propagates out unchanged.

   `rel` is the read-only relation (not `mut`): the routine computes a set and
   mutates no input (directive 5). It is modeled as an opaque handle (`Int`); the
   only observations are the solver's outcome (`solveUnivariate rel`) and the
   condition set built from the relation (`conditionOverReals rel`)
   (mapping.md §2). -/
method relationAsSet (rel : Int)
    return (out : Except SolveErr SetVal)
  ensures out = asSetSpec rel
  do
    -- impl-start
    -- Pre-image skeleton: the solver's result is returned DIRECTLY, with no
    -- interception — a produced solution set is returned, but ANY failure
    -- (whether cannot-solve or other) escapes unchanged. The frozen spec requires
    -- that a cannot-solve failure instead yield the explicit condition set over
    -- the reals, so prove_correct MUST fail on that case.
    let result : Except SolveErr SetVal :=
      match solveUnivariate rel with
      | Except.ok h => Except.ok (SetVal.solverSet h)
      | Except.error e => Except.error e
    return result
    -- impl-end

prove_correct relationAsSet by
  loom_solve
  simp_all [asSetSpec]
