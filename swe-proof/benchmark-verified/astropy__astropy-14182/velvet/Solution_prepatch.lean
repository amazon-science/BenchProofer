import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions are changed functions whose
--  new behaviour is a direct arithmetic/positional expression of an already
--  available count — the number of header rows requested for the rendering.
--  The surrounding rendering and parsing machinery that supplies and consumes
--  those values is unchanged; the count itself is an input, an R-refinement
--  (mapping.md §2), not a callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
-- (No pure helpers required: each result is a single closed-form expression of
--  the inputs — a positional pick from the rendered lines, and a small offset
--  added to the header-row count.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Frame a constant-width simple-table rendering with its column-extent ruler line.

   A simple-table rendering is a list of text lines: first the `headerRowCount`
   header lines (one per requested header row), then the column-extent ruler
   line, then the data lines. The framing copies that single ruler line to both
   the very top and the very bottom of the rendering, leaving the rendering
   otherwise untouched.

   The ruler line is therefore the line at position `headerRowCount` — it sits
   immediately after the header rows, so its position tracks how many header
   rows were requested rather than being a predetermined constant. The
   rendering must contain that line (`headerRowCount` is a valid position).

   The rendering `lines` is consulted but not `mut`; a fresh framed list is
   built and the original is not mutated (directive 5). -/
method surroundWithRuler (lines : List (List Char)) (headerRowCount : Nat)
    return (out : List (List Char))
  require headerRowCount < lines.length
  ensures out = [lines[headerRowCount]!] ++ lines ++ [lines[headerRowCount]!]
  do
    -- impl-start
    -- Pre-image skeleton: the ruler position is hard-wired to the second line
    -- (index 1), assuming exactly one header row, instead of tracking the
    -- requested header-row count. The frozen spec frames with the line at
    -- `headerRowCount`, so prove_correct MUST fail whenever headerRowCount ≠ 1.
    let ruler := lines[1]!
    let out := [ruler] ++ lines ++ [ruler]
    return out
    -- impl-end

prove_correct surroundWithRuler by
  loom_solve

/- The position of the first data line within a simple-table rendering being
   parsed back into a table.

   Above the data sit: one opening ruler line, then the `headerRowCount` header
   lines, then a second ruler line closing the header block — so the first data
   line is offset from the start by two ruler lines plus however many header
   rows were requested. The offset must therefore track the header-row count
   rather than assuming a single header row.

   `headerRowCount` is consulted but not `mut`; nothing is mutated (directive 5). -/
method dataStartOffset (headerRowCount : Nat) return (out : Nat)
  ensures out = 2 + headerRowCount
  do
    -- impl-start
    -- This behaviour is the correct (post-image) skeleton; this prepatch
    -- isolates the framing-position regression in `surroundWithRuler` above.
    let out := 2 + headerRowCount
    return out
    -- impl-end

prove_correct dataStartOffset by
  loom_solve
