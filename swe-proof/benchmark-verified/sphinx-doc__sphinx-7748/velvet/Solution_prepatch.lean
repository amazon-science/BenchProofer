import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no consumed axioms: the per-line classification is supplied as input data —
--  see the `LineInfo` carrier below — and validated against the real callees by
--  the executable soundness check; the collection logic is modeled deeply.)
-- axioms-end

-- pure-start
/- The payload extracted from one signature-bearing line: the argument text and
   the return-annotation text. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Inhabited, Repr

/- The decision data about a single docstring line, as observed by a standard
   signature recognizer:
   * `blank`  — the line is empty (a paragraph break);
   * `isSig`  — the line, with any trailing continuation marker removed, parses
                as a signature whose name is one of the documented object's
                accepted names;
   * `cont`   — the line carries a trailing continuation marker, indicating a
                further signature follows;
   * `sig`    — the parsed `(args, retann)` payload (meaningful only when `isSig`).
   The recognizer itself is unchanged and is supplied as this input carrier. -/
structure LineInfo where
  blank : Bool
  isSig : Bool
  cont : Bool
  sig : Sig
deriving Inhabited

/- The signatures collected from one docstring, in reading order. Scanning the
   lines front to back: a blank line ends the scan; a signature line is
   collected, and collection carries on past it only when that line bears a
   trailing join marker (otherwise that signature is the last one); a line that
   is neither blank nor a signature is skipped. Front-recursive so a single
   unfold is available per loop step (the fold pattern, plan §5.4). -/
def collectSigs : List LineInfo → List Sig
  | [] => []
  | l :: ls =>
    if l.blank then []
    else if l.isSig then
      (if l.cont then l.sig :: collectSigs ls else [l.sig])
    else collectSigs ls

@[grind] lemma collectSigs_nil : collectSigs [] = [] := rfl
@[grind] lemma collectSigs_cons (l : LineInfo) (ls : List LineInfo) :
    collectSigs (l :: ls) =
      (if l.blank then []
       else if l.isSig then (if l.cont then l.sig :: collectSigs ls else [l.sig])
       else collectSigs ls) := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (lines : List LineInfo) (i : Nat) (hi : i < lines.length) :
    lines.drop i = lines[i]! :: lines.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The fold step: `collectSigs (lines.drop i)` peels the classification of line
   `i`. This is the single per-line goal the loop body leaves. -/
@[grind] lemma collectSigs_drop_step (lines : List LineInfo) (i : Nat)
    (hi : i < lines.length) :
    collectSigs (lines.drop i) =
      (if (lines[i]!).blank then []
       else if (lines[i]!).isSig then
              (if (lines[i]!).cont then (lines[i]!).sig :: collectSigs (lines.drop (i + 1))
               else [(lines[i]!).sig])
            else collectSigs (lines.drop (i + 1))) := by
  rw [drop_cons_eq lines i hi, collectSigs_cons]

/- Past the end there is nothing left to collect. -/
@[grind] lemma collectSigs_drop_ge (lines : List LineInfo) (i : Nat)
    (h : lines.length ≤ i) : collectSigs (lines.drop i) = [] := by
  rw [List.drop_eq_nil_of_le h]; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method collectSignatures (lines : List LineInfo) return (out : List Sig)
  ensures out = collectSigs lines
  do
    -- impl-start
    -- Pre-image skeleton: the original scan inspects only the FIRST line and
    -- stops at the first signature it finds, never honoring a continuation
    -- marker. So at most one signature is ever produced. The frozen spec
    -- requires the full reading-order collection (which continues past a
    -- continuation-marked signature), so prove_correct MUST fail.
    let mut out : List Sig := []
    let mut i := 0
    let mut stopped := false
    while i < lines.length ∧ stopped = false
      invariant 0 ≤ i ∧ i ≤ lines.length
      invariant out ++ (if stopped then [] else collectSigs (lines.drop i)) = collectSigs lines
      done_with stopped = true ∨ i = lines.length
      decreasing (lines.length - i) + (if stopped then 0 else 1)
    do
      let l := lines[i]!
      if l.blank then
        stopped := true
      else
        if l.isSig then
          out := out ++ [l.sig]
          stopped := true
        else
          i := i + 1
    return out
    -- impl-end

prove_correct collectSignatures by
  loom_solve
