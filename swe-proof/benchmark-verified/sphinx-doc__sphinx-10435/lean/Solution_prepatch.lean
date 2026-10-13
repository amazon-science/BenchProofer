import Mathlib

-- imports-end

-- axioms-start
-- No unchanged callee is consumed as an axiom: the relevant post-processing
-- (a textual rewrite of the highlighter's output) is modeled deeply below.
-- axioms-end

-- pure-start
/-- Newline character used to join LaTeX body fragments. -/
def CR : Char := '\n'

/-- Whitespace predicate matching the characters stripped by default when
trailing whitespace is removed from a string. -/
def isTrailWs (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
  c == (Char.ofNat 0x0b) || c == (Char.ofNat 0x0c)

/-- Remove trailing whitespace from a character sequence. -/
def rstripWs (s : List Char) : List Char := (s.reverse.dropWhile isTrailWs).reverse

/-- Keep all but the last `n` characters of `s` (the value-level slice `s[:-n]`
for `n > 0`; yields the empty sequence when `n ≥ s.length`). -/
def dropLastN (n : Nat) (s : List Char) : List Char := s.take (s.length - n)

/-- Replace every non-overlapping, left-to-right occurrence of a non-empty
pattern `pat` by `rep`. -/
def replaceAll (pat rep : List Char) : List Char → List Char
  | [] => []
  | (c :: cs) =>
    if pat.isPrefixOf (c :: cs) ∧ 0 < pat.length then
      rep ++ replaceAll pat rep ((c :: cs).drop pat.length)
    else
      c :: replaceAll pat rep cs
  termination_by s => s.length
  decreasing_by
    · simp_wf; omega
    · simp_wf

/-- The Verbatim opening emitted by the syntax highlighter. -/
def verbOpen : List Char := r"\begin{Verbatim}[commandchars=\\\{\}]".toList

/-- The constant sequence the Verbatim opening is rewritten to. The trailing `%`
comments out the newline that immediately follows, so it produces no leading
inter-token space in the rendered output. -/
def upquoteOpen : List Char := r"\sphinxcode{\sphinxupquote{%".toList

/-- The trailing closing sequence appended after the highlighted body. The
leading `%` comments out the trailing newline, so no spurious space survives at
the end of the rendered output. -/
def closingTail : List Char := '%' :: CR :: "}}".toList
-- pure-end

-- post-conditions-start
/-- `result` is the exact character sequence emitted for an inline highlighted
code fragment, given the highlighter output `hlcode`.

The emission rewrites the highlighter's opening delimiter to the upquote opening
(whose trailing comment suppresses the following newline), then drops trailing
whitespace together with the 15-character closing-delimiter run that
precedes it (i.e. the newline plus the closing delimiter), and finally appends a
comment-terminated newline followed by the closing braces. Both the leading and
the trailing inter-token newline are thereby comment-suppressed, so the rendered
fragment carries no extra whitespace at either end. -/
def problem_spec_inlineCode (hlcode : List Char) (result : List Char) : Prop :=
  let rewritten := replaceAll verbOpen upquoteOpen hlcode
  let trimmed := dropLastN 15 (rstripWs rewritten)
  result = trimmed ++ closingTail
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the opening delimiter is rewritten WITHOUT the
-- trailing comment, only 14 characters are dropped from the trailer (the
-- closing delimiter itself, leaving the preceding newline in place), and the
-- closing braces are appended with no comment-terminated newline. The two
-- un-suppressed newlines render as spurious leading/trailing inter-token space.
def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do
  let mut hl := hlcode
  hl := replaceAll verbOpen (r"\sphinxcode{\sphinxupquote{".toList) hl
  -- get consistent trailer
  hl := dropLastN 14 (rstripWs hl)
  let mut body : List Char := []
  body := body ++ hl
  body := body ++ "}}".toList
  return body
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (the
-- missing `%` comment terminators and the 14-vs-15 trailer contradict the
-- `result = trimmed ++ closingTail` clause), so verification must fail.
theorem correct_inlineCode : ∀ hlcode : List Char,
    problem_spec_inlineCode hlcode (implementation_inlineCode hlcode) := by
  sorry
-- proof-end
