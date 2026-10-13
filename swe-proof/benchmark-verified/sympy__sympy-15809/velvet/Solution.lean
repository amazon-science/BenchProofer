import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The standard argument-normalisation pipeline a lattice extremum constructor
   runs over its raw arguments before deciding a result: it sympifies, flattens
   nested same-kind extrema, drops the absorbing/identity elements, and removes
   locally-dominated members, yielding the normalised argument multiset. It is an
   UNCHANGED helper the constructor merely invokes (never redefined), so it is
   modeled `opaque` (computable inside the `do` block) and carries NO general
   `ensures` — the desired behaviour assumes nothing about which members survive
   for a non-empty input.

   The one fact the desired behaviour relies on is `processArgs_nil`: normalising
   an EMPTY argument list yields an EMPTY multiset (the pipeline introduces no
   members out of nothing). This is the WEAKEST contract sufficient for the
   empty-input result and is the only consumed axiom (A-consumed). Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
opaque processArgs : List Int → List Int

axiom processArgs_nil : processArgs [] = []
-- axioms-end

-- pure-start
/- The failure the constructor is asked about: being called with no arguments at
   all. (The public problem statement reports exactly this case — that empty
   calls currently fail.) -/
inductive MinMaxErr where
  | noArguments
  deriving DecidableEq

/- The result of constructing a lattice extremum:

     * `identityResult idv` — the lattice identity element `idv` is returned
       (the value that is the extremum of the EMPTY collection: the top element
       for a minimum, the bottom element for a maximum);
     * `single a` — exactly one member survives normalisation, returned verbatim;
     * `combined members` — two or more members survive; the extremum object over
       that normalised multiset is built. -/
inductive MinMaxResult where
  | identityResult (idv : Int)
  | single (a : Int)
  | combined (members : List Int)
  deriving DecidableEq

/- The intended outcome of constructing a lattice extremum from a raw argument
   list and the lattice identity element `idv`, as `Except MinMaxErr MinMaxResult`:

   the raw arguments are normalised (the unchanged `processArgs` pipeline), then
   the result is decided ENTIRELY by how many members survive —
     * none survive  ⇒ the identity element `idv` is returned (the extremum of the
       empty collection); in particular a call with no arguments at all yields the
       identity element rather than failing;
     * one survives  ⇒ that member is returned verbatim;
     * two or more    ⇒ the extremum object over the survivors is built.

   No input is rejected for being empty: the empty collection has a well-defined
   extremum, namely the identity element. -/
def minMaxResult (idv : Int) (rawArgs : List Int) : Except MinMaxErr MinMaxResult :=
  match processArgs rawArgs with
  | []           => Except.ok (MinMaxResult.identityResult idv)
  | [a]          => Except.ok (MinMaxResult.single a)
  | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct a lattice extremum (a minimum or a maximum) from a raw argument list
   and the lattice identity element `idv` (the top element for a minimum, the
   bottom element for a maximum — the extremum of the empty collection).

   Desired behaviour: the constructor normalises its raw arguments through the
   unchanged argument-normalisation pipeline and then decides the result purely by
   how many members survive — none ⇒ the identity element, one ⇒ that member,
   two or more ⇒ the extremum object. Crucially it must NOT reject an empty
   argument list: the empty collection has a well-defined extremum, the identity
   element, so a call with no arguments returns `idv` instead of failing.

   `idv` and `rawArgs` are read-only (not `mut`): the constructor computes a
   result and mutates no input (directive 5). Arguments are modeled as opaque
   handles (`Int`); the only observations are the normalisation outcome
   (`processArgs rawArgs`) and the supplied identity element (mapping.md §2). -/
method constructMinMax (idv : Int) (rawArgs : List Int)
    return (out : Except MinMaxErr MinMaxResult)
  ensures out = minMaxResult idv rawArgs
  ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv)
  do
    -- impl-start
    -- Normalise the raw arguments (unchanged pipeline) and decide the result by
    -- how many members survive. There is NO rejection of an empty argument list:
    -- the empty collection's extremum is the identity element, reached through
    -- the empty-normalisation branch below.
    let result : Except MinMaxErr MinMaxResult :=
      match processArgs rawArgs with
      | []           => Except.ok (MinMaxResult.identityResult idv)
      | [a]          => Except.ok (MinMaxResult.single a)
      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))
    return result
    -- impl-end

prove_correct constructMinMax by
  loom_solve <;> simp_all [minMaxResult, processArgs_nil]
