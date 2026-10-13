import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The normalization performed here is modeled DEEPLY
--  in the `pure` region as a closed, computable function of its input text:
--  split into lines, find the common leading indentation shared by the lines
--  AFTER the first, remove that indentation from those lines while stripping the
--  first line, then drop surrounding blank lines and rejoin. The standard-library
--  routine this models (an unchanged callee the routine delegates to) is an
--  A-reference: the deep model `cleanDocModel` is validated equal to the real
--  library routine by axiom_check.py / G-AX. Nothing is consumed as an axiom —
--  see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Number of leading space characters of a line. -/
def leadingSpaces : List Char → Nat
  | []      => 0
  | c :: cs => if c = ' ' then leadingSpaces cs + 1 else 0

/- Drop the leading space characters of a line. -/
def stripLeadingSpaces : List Char → List Char
  | []      => []
  | c :: cs => if c = ' ' then stripLeadingSpaces cs else c :: cs

/- A line "has content" iff it contains at least one non-space character, i.e.
   stripping its leading spaces leaves something. -/
def hasContent (l : List Char) : Bool := !(stripLeadingSpaces l).isEmpty

/- Split a character sequence into lines on the newline separator. Always
   returns at least one line (an empty sequence is a single empty line). -/
def splitLines : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
      let rest := splitLines cs
      if c = '\n' then [] :: rest
      else
        match rest with
        | []      => [[c]]
        | r :: rs => (c :: r) :: rs

/- The common leading indentation shared by the content lines of a list: the
   minimum number of leading spaces over the lines that have content, or `none`
   when there is no such line. -/
def commonIndent : List (List Char) → Option Nat
  | []      => none
  | l :: ls =>
      let rest := commonIndent ls
      if hasContent l then
        match rest with
        | none   => some (leadingSpaces l)
        | some m => some (Nat.min (leadingSpaces l) m)
      else rest

/- Remove the common indentation: always strip the leading spaces of the first
   line; remove `margin` leading characters from every subsequent line when a
   common indentation exists (otherwise leave the subsequent lines untouched). -/
def dedentLines (margin : Option Nat) : List (List Char) → List (List Char)
  | []            => []
  | first :: tail =>
      let f := stripLeadingSpaces first
      let t := match margin with
        | none   => tail
        | some m => tail.map (fun l => l.drop m)
      f :: t

/- Drop trailing blank (empty) lines. -/
def dropTrailingBlank (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (fun l => l.isEmpty)).reverse

/- Drop leading blank (empty) lines. -/
def dropLeadingBlank (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (fun l => l.isEmpty)

/- Rejoin lines with the newline separator. -/
def joinNL : List (List Char) → List Char
  | []      => []
  | [l]     => l
  | l :: ls => l ++ '\n' :: joinNL ls

/- The deep model of the standard normalization (A-reference, validated equal to
   the real library routine by axiom_check.py / G-AX): split into lines, compute
   the common indentation of the lines AFTER the first, strip that indentation
   while stripping the first line, then drop surrounding blank lines and rejoin.
   The common indentation is taken over the lines after the first so that a
   first line that begins at column zero does not force the shared indentation to
   zero — the behaviour the issue requires. -/
def cleanDocModel (text : List Char) : List Char :=
  let lines := splitLines text
  let margin := commonIndent (lines.drop 1)
  let dedented := dedentLines margin lines
  joinNL (dropLeadingBlank (dropTrailingBlank dedented))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Uniformly normalize the indentation of a multi-line block of text. The first
   line is stripped of its leading whitespace; the indentation common to all the
   remaining non-blank lines is removed from those lines; surrounding blank lines
   are dropped. Crucially the common indentation is measured from the lines AFTER
   the first, so a block whose text begins on the very first line is dedented
   correctly rather than left indented.

   The input `text` is read-only (not `mut`): the routine derives a fresh
   normalized sequence and returns it, mutating nothing (directive 5). -/
method normalizeIndentation (text : List Char) return (out : List Char)
  ensures out = cleanDocModel text
  do
    -- impl-start
    -- Pre-image skeleton: the common indentation is measured over ALL lines
    -- (including the first) instead of the lines after the first. When the first
    -- line begins at column zero this forces the shared indentation to zero, so
    -- the subsequent lines are never dedented. The frozen spec requires
    -- cleanDocModel (margin taken over the lines AFTER the first), so
    -- prove_correct MUST fail.
    let lines := splitLines text
    let margin := commonIndent lines
    let dedented := dedentLines margin lines
    let trimmed := dropLeadingBlank (dropTrailingBlank dedented)
    return joinNL trimmed
    -- impl-end

prove_correct normalizeIndentation by
  loom_solve
  unfold cleanDocModel
  rfl
