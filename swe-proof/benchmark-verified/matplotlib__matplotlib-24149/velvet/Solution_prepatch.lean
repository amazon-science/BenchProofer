import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two element-extraction routines this step relies
--  on are modeled DEEPLY as the pure functions below — `firstFinite` and
--  `firstElement` — and are validated against the real routines by axiom_check.py
--  (G-AX, A-reference). Nothing is left as an opaque assumed contract.)
-- axioms-end

-- pure-start
/- The failure that the element-extraction step can report: a request for the
   first finite element of a sequence that happens to contain none. Modeled as
   an error leg so the post-state can distinguish "produced a value" from
   "raised". -/
inductive ExtractErr where
  | noFiniteFound
  deriving Inhabited, DecidableEq

/- Whether a scalar real value is finite — i.e. neither not-a-number nor an
   infinity. (Bijection to the real scalar-finiteness predicate: mapping.md §2.) -/
def isFiniteVal (x : Float) : Bool := x.isFinite

/- The first finite element of a sequence, if one exists. Scans front-to-back
   and returns the first element satisfying the finiteness predicate, or `none`
   when every element is non-finite. Deep model of the "first finite" extractor
   (A-reference; mapping.md §3). -/
def firstFinite (xs : List Float) : Option Float := xs.find? isFiniteVal

/- The first element of a sequence, taken unconditionally (finite or not). Deep
   model of the "first element" extractor (A-reference; mapping.md §3). The
   default is immaterial under the precondition that the sequence is non-empty. -/
def firstElement (xs : List Float) : Float := xs.headD 0
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Pick the representative scalar of a non-empty sequence for use as a reference
   point.

   The sequence is consulted read-only. The desired behavior is total: a
   representative is always produced for a non-empty sequence, never an error.
   Specifically, the representative is the first finite element of the sequence
   when one exists, and the first element of the sequence (taken unconditionally)
   when no element is finite. Pinning the result to
   `(firstFinite xs).getD (firstElement xs)` pins both legs at once — the
   finite-element value on the common path, and the unconditional first-element
   fallback on the all-non-finite path — and rules out the error outcome on every
   non-empty input. -/
method selectReference (xs : List Float) return (out : Except ExtractErr Float)
  require xs ≠ []
  ensures out = Except.ok ((firstFinite xs).getD (firstElement xs))
  do
    -- impl-start
    -- Take the first finite element. No fallback is attempted: when no element
    -- is finite the extraction has nothing to return and the failure is
    -- propagated outward as an error rather than recovered.
    let found := firstFinite xs
    let result := match found with
      | some v => Except.ok v
      | none   => Except.error ExtractErr.noFiniteFound
    return result
    -- impl-end

prove_correct selectReference by
  loom_solve
