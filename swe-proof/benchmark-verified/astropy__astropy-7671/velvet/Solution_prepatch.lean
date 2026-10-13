import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The failure that the order comparison of two requirement labels can report.
   The comparison consumes two label component-sequences and, where they remain
   well-ordered, yields a Boolean verdict; on a pair it cannot order it reports
   this failure instead of a verdict. -/
inductive CmpErr where
  | incomparable
  deriving DecidableEq

/- The order comparison of two requirement labels (an UNCHANGED callee; the
   weakest sufficient contract is no constraint at all, so it is left fully
   opaque — directive 7). Given the reference label, a candidate label, and a
   flag selecting non-strict (`true`) versus strict (`false`) ordering, it
   yields either a verdict or the incomparable failure. Crucially it is a
   PARTIAL operation: on certain candidate labels it fails rather than
   returning a verdict — which is exactly why the candidate must be reduced to
   its orderable leading portion before it is consulted. Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom labelGE : List Char → List Char → Bool → Except CmpErr Bool
-- axioms-end

-- pure-start
/- Whether a code point is one of the ten decimal digits. -/
def isDigit (c : Char) : Bool :=
  '0' ≤ c ∧ c ≤ '9'

/- The length of the maximal run of leading decimal digits. -/
def digitRun : List Char → Nat
  | []      => 0
  | c :: cs => if isDigit c then 1 + digitRun cs else 0

/- The length of one orderable numeric segment at the front: a lone zero, or a
   nonzero-led maximal digit run; `0` when the front is not such a segment. A
   leading zero stands alone (never absorbs following digits), matching the
   canonical numeric-segment grammar. -/
def segLen : List Char → Nat
  | []      => 0
  | c :: cs =>
    if c = '0' then 1
    else if isDigit c then 1 + digitRun cs
    else 0

/- The length of a maximal sequence of `.`-separated numeric segments following
   an initial segment. Structurally recursive on a fuel bound (the remaining
   input length) so it is total; each step consumes a `.` plus one segment. -/
def dottedTail : Nat → List Char → Nat
  | 0,        _  => 0
  | _,        [] => 0
  | fuel + 1, c :: cs =>
    if c = '.' then
      let s := segLen cs
      if s = 0 then 0
      else 1 + s + dottedTail fuel (cs.drop s)
    else 0

/- The length of an optional leading epoch: a nonzero-led digit run followed by
   `!`, accepted only when a numeric segment still follows the `!`; otherwise
   `0`. -/
def epochLen : List Char → Nat
  | []      => 0
  | c :: cs =>
    if isDigit c ∧ c ≠ '0' then
      let r := 1 + digitRun cs              -- the nonzero-led digit run length
      let after := (c :: cs).drop r
      match after with
      | '!' :: rest => if segLen rest = 0 then 0 else r + 1
      | _           => 0
    else 0

/- The orderable leading portion of a requirement label: an optional epoch, a
   mandatory leading numeric segment, then a maximal run of dotted numeric
   segments. When no leading numeric segment is present the label is returned
   unchanged (there is nothing orderable to isolate). This is the canonical
   numeric-prefix of the public version grammar. -/
def cleanLabel (version : List Char) : List Char :=
  let e := epochLen version
  let afterEpoch := version.drop e
  let r := segLen afterEpoch
  if r = 0 then version
  else
    let afterRel := afterEpoch.drop r
    let d := dottedTail afterRel.length afterRel
    version.take (e + r + d)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether an available requirement label meets a required one.

   The available label `have_` and the ordering mode `inclusive` are read-only
   inputs (not `mut`); the required label `version` is consulted only through
   the orderable leading portion isolated from it.

   Desired behaviour: the required label may carry trailing annotation beyond
   its orderable numeric portion. Comparing that raw label against the available
   one can fail outright (the order comparison is partial). So the decision must
   first reduce the required label to its orderable leading portion
   (`cleanLabel version`) and only then ask the order comparison for a verdict.
   The result is exactly the verdict the order comparison returns for the
   available label against that reduced required label, under the selected mode —
   never the verdict for the raw required label.

   Modeled domain: the required label ranges over the ASCII plane (the public
   version grammar is ASCII, as is every graded input). Outside it the digit
   classification of the real leading-portion extractor is standard-library
   specific and is not claimed (mapping.md §2.1). -/
noncomputable section
method meetsRequirement (have_ : List Char) (version : List Char) (inclusive : Bool)
    return (out : Except CmpErr Bool)
  require ∀ c ∈ version, c.toNat < 128
  ensures out = labelGE have_ (cleanLabel version) inclusive
  do
    -- impl-start
    -- Pre-image skeleton: the required label is handed to the order comparison
    -- RAW, with no reduction to its orderable leading portion. The frozen spec
    -- requires the verdict against `cleanLabel version`, so whenever the label
    -- carries trailing annotation the two diverge and prove_correct MUST fail.
    let result := labelGE have_ version inclusive
    return result
    -- impl-end
end

prove_correct meetsRequirement by
  loom_solve
