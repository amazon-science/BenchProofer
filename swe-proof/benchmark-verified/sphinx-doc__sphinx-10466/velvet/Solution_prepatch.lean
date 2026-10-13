import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms.) The single operation under specification — publishing
-- the recorded positions of a message — is modeled DEEPLY below: the per-entry
-- projection, the per-code-point order, the deduplication, and the ascending
-- sort are all spelled out. The two unchanged primitives the model leans on (a
-- set-based deduplication and a total-order sort of a sequence) are validated as
-- A-references against the real standard-library primitives by axiom_check.py
-- (G-AX); see mapping.md.
-- axioms-end

-- pure-start
/- A recorded position pairs a source name (carried as its code-point sequence)
   with a line index. -/
abbrev Pos := List Char × Int

/- An entry recorded for a message carries a source name, a line index, and an
   opaque identity tag (also a code-point sequence). -/
abbrev Entry := List Char × Int × List Char

/- The position of an entry is its (source, line) pair: the identity tag is
   dropped. Two entries that agree on source and line denote the same position
   regardless of their tags. -/
def toPos (e : Entry) : Pos := (e.1, e.2.1)

/- Strict lexicographic order on code-point sequences, by code point. -/
def lcharLt : List Char → List Char → Bool
  | [],      []     => false
  | [],      _ :: _ => true
  | _ :: _,  []     => false
  | a :: u,  b :: v =>
      if a.val < b.val then true
      else if b.val < a.val then false
      else lcharLt u v

/- Total order on positions: order by source first (code-point lexicographic),
   then by line index. This is the value comparison of (source, line) pairs. -/
def posLe (x y : Pos) : Bool :=
  if lcharLt x.1 y.1 then true
  else if lcharLt y.1 x.1 then false
  else decide (x.2 ≤ y.2)

/- The published positions of a message: the DISTINCT (source, line) pairs among
   its entries, listed in ascending order. Deduplication collapses entries that
   share a position (differing only in their identity tag); the sort puts the
   survivors in a canonical ascending order. -/
def orderedPositions (entries : List Entry) : List Pos :=
  ((entries.map toPos).dedup).mergeSort posLe
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method publishPositions (entries : List Entry) return (out : List Pos)
  ensures out = orderedPositions entries
  ensures out.Nodup
  do
    -- impl-start
    -- Pre-image skeleton: the positions are published exactly as recorded — the
    -- raw per-entry projection, in insertion order, with no collapsing of
    -- coincident positions. The frozen spec requires the canonical distinct
    -- ascending list (orderedPositions), so prove_correct MUST fail.
    let result := entries.map toPos
    return result
    -- impl-end

prove_correct publishPositions by
  loom_solve
  · exact (List.mergeSort_perm ((entries.map toPos).dedup) posLe).nodup_iff.mpr
      (List.nodup_dedup _)
  · rfl
