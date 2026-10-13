import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The three line-list transformations composed here are
--  modeled DEEPLY in the `pure` region as closed, computable functions of their
--  inputs: removing a chosen amount of leading indentation from each line of a
--  body, adding one caller-supplied line before the body, and adding one
--  caller-supplied line after it. Each is an unchanged library routine the
--  assembly delegates to, modeled as an A-reference: `removeIndent`, `addPrefix`
--  and `addSuffix` are validated equal to the real library routines by
--  axiom_check.py / G-AX. Nothing is consumed as an axiom — see refinement.md §C
--  and mapping.md §3.)
-- axioms-end

-- pure-start
/- Remove `n` leading characters from a single line. A line that is emptied by
   the removal but originally carried a trailing newline keeps that newline (so
   a blank separator line is preserved rather than collapsed away). -/
def removeIndentLine (n : Nat) (line : List Char) : List Char :=
  let dropped := line.drop n
  if dropped.isEmpty && (line.getLast? == some '\n') then ['\n'] else dropped

/- Remove `n` leading characters from every line of the body. When no indentation
   amount is supplied the body is left untouched. -/
def removeIndent (n : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match n with
  | none   => lines
  | some k => lines.map (removeIndentLine k)

/- Add one caller-supplied line (terminated by a newline) before the body. An
   empty text adds nothing. -/
def addPrefix (prefixText : List Char) (lines : List (List Char)) : List (List Char) :=
  if prefixText.isEmpty then lines else (prefixText ++ ['\n']) :: lines

/- Add one caller-supplied line (terminated by a newline) after the body. An
   empty text adds nothing. -/
def addSuffix (suffixText : List Char) (lines : List (List Char)) : List (List Char) :=
  if suffixText.isEmpty then lines else lines ++ [suffixText ++ ['\n']]

/- Concatenate the lines back into a single character sequence. Each line by now
   carries its own terminating newline, so joining is plain concatenation.
   Front-recursive so a single unfold is available (the Velvet fold pattern). -/
def joinLines : List (List Char) → List Char
  | []      => []
  | l :: ls => l ++ joinLines ls

@[grind] lemma joinLines_nil : joinLines [] = [] := rfl
@[grind] lemma joinLines_cons (l : List Char) (ls : List (List Char)) :
    joinLines (l :: ls) = l ++ joinLines ls := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble an included block of text. The body has a chosen amount of leading
   indentation removed from each of its lines; then a caller-supplied line is
   added before the body and another after it. Crucially, the indentation
   removal applies ONLY to the body — the lines added before and after are
   exempt, so their own leading whitespace is preserved exactly as supplied.
   The result is the assembled lines concatenated into one character sequence.

   All four inputs are inspected only (none `mut`): the routine derives a fresh
   assembled sequence and returns it, mutating nothing (directive 5). `indent`
   is `none` when no indentation amount is supplied; `prefixText`/`suffixText`
   are empty when nothing is to be added. -/
method assembleBlock (body : List (List Char)) (prefixText : List Char)
    (suffixText : List Char) (indent : Option Nat) return (out : List Char)
  ensures out = joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))
  do
    -- impl-start
    -- Indentation removal runs FIRST, on the body alone; only afterwards are the
    -- before/after lines added, so they escape the removal.
    let trimmed  := removeIndent indent body
    let withHead := addPrefix prefixText trimmed
    let withTail := addSuffix suffixText withHead
    return joinLines withTail
    -- impl-end

prove_correct assembleBlock by
  loom_solve
