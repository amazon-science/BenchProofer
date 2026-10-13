import Velvet.Std
-- imports-end

/- Total-correctness semantics: the routine under spec is straight-line (a
   render call followed by bounded list surgery; no loops or recursion — it
   always returns), so the contract also demands termination. Under partial
   semantics a diverging body would vacuously satisfy every postcondition. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The syntax-highlighter's rendering of one inline code snippet, as a pure
   function on code points. It is an UNCHANGED callee: the routine under spec
   calls it and does not alter it. The only structural fact the spec relies on
   is `highlightInline_form`: the rendered text is a constant opening control
   sequence, then a newline, then the rendered body, then a newline, then a
   constant closing control sequence, then a final newline. We pin nothing about
   the body content (`renderedInline`) — the weakest sufficient contract is the
   surrounding frame (directive 7). Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom renderedInline : List Char → List Char
-- axioms-end

-- pure-start
/- The constant opening control sequence emitted by the highlighter's block
   formatter (length 37 code points). -/
def beginTok : List Char := "\\begin{Verbatim}[commandchars=\\\\\\{\\}]".toList

/- The constant closing control sequence emitted by the highlighter's block
   formatter (length 14 code points). -/
def endTok : List Char := "\\end{Verbatim}".toList

/- The inline-code macro opening (length 27 code points). -/
def codeOpen : List Char := "\\sphinxcode{\\sphinxupquote{".toList

/- The opening as the routine substitutes it: the inline-code macro opening
   immediately followed by a line-break-suppressing comment marker, so the
   line break that follows does not render as a leading space. -/
def openTok : List Char := codeOpen ++ ['%']

/- Drop trailing whitespace (the model of the standard right-strip). -/
def rstrip (s : List Char) : List Char := (s.reverse.dropWhile Char.isWhitespace).reverse

/- The desired wrapped markup for an inline snippet with rendered body `body`:
   the code-macro opening, a line-break-suppressing marker, a newline, the
   rendered body, a line-break-suppressing marker, a newline, and the closing
   braces. The two markers make the surrounding line breaks produce no spurious
   whitespace in the output. -/
def wrapped (body : List Char) : List Char :=
  codeOpen ++ ['%', '\n'] ++ body ++ ['%', '\n', '}', '}']

/- The non-deterministic choice of the highlighter's result is well-posed: for
   any target value `v`, the set of values equal to `v` is non-empty (`v`
   itself). This supplies the constructive existence witness so the `:|` choice
   elaborates. It does NOT weaken verification: under demonic choice the
   postcondition must still hold for every value the predicate allows, here
   exactly the framed rendering. -/
noncomputable instance findableEqList (v : List Char) (n : Lean.Name) :
    Findable (fun e : List Char => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

@[grind] lemma endTok_len : endTok.length = 14 := by unfold endTok; rfl

/- The arithmetic-and-slicing core: substituting the opening for the leading
   control sequence, right-stripping the single trailing newline, dropping the
   final closing control sequence together with the newline preceding it, then
   appending the line-break-suppressing marker and the closing braces, yields
   exactly `wrapped body`. Proven by structural rewriting of the concatenation;
   this is the single goal `loom_solve` leaves for the routine. -/
lemma compute (body : List Char) :
    List.take
      ((rstrip (openTok ++ List.drop beginTok.length
        (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))).length - 15)
      (rstrip (openTok ++ List.drop beginTok.length
        (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))) ++ ['%', '\n', '}', '}']
    = wrapped body := by
  have hdrop : List.drop beginTok.length
      (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'] := by
    have : beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']
        = beginTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']) := by
      simp [List.append_assoc]
    rw [this, List.drop_left]
  rw [hdrop]
  have hre : openTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'] := by
    simp [List.append_assoc]
  rw [hre]
  have hrs : rstrip ((openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok := by
    unfold rstrip endTok; simp [List.reverse_append]
  rw [hrs]
  have hre2 : (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok
      = (openTok ++ ['\n'] ++ body) ++ (['\n'] ++ endTok) := by
    simp [List.append_assoc]
  rw [hre2]
  have hlen : ((openTok ++ ['\n'] ++ body) ++ (['\n'] ++ endTok)).length - 15
      = (openTok ++ ['\n'] ++ body).length := by
    simp only [List.length_append, List.length_cons, List.length_nil, endTok_len]; omega
  rw [hlen, List.take_left]
  unfold wrapped openTok; simp [List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Wrap one highlighted inline code snippet for the document writer.

   The desired behavior: the snippet is rendered by the syntax highlighter and
   then wrapped in the inline-code macro. The result is exactly `wrapped` of the
   rendered body — the macro opening and the rendered body are each immediately
   followed by a line-break-suppressing marker, so the line breaks that the
   highlighter places around the body do not render as a spurious space at the
   start and end of the inline code (`out = wrapped (renderedInline snippet)`).

   `snippet` is the read-only input source text (not `mut`): the routine renders
   it and never alters it (directive 5). Both the snippet and the rendered text
   are modeled as `List Char` (per-code-point strings; mapping.md §2). -/
noncomputable section
method wrapInlineCode (snippet : List Char) return (out : List Char)
  ensures out = wrapped (renderedInline snippet)
  do
    -- impl-start
    -- Pre-image skeleton: the macro opening is substituted WITHOUT the
    -- line-break-suppressing marker, only the closing control sequence (not the
    -- newline preceding it) is dropped, and the trailer is the bare closing
    -- braces. The line breaks around the body therefore survive and the frozen
    -- spec `out = wrapped (renderedInline snippet)` is NOT met, so prove_correct
    -- MUST fail.
    let hlcode :| hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']
    let hlcode := codeOpen ++ hlcode.drop beginTok.length
    let stripped := rstrip hlcode
    let hlcode := stripped.take (stripped.length - 14)
    return hlcode ++ ['}', '}']
    -- impl-end
end

prove_correct wrapInlineCode by
  loom_solve
  rw [choice_1, compute (renderedInline snippet)]
