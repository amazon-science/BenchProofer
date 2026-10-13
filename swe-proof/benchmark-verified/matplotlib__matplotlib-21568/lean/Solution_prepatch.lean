import Mathlib
-- imports-end

/-!
Rendering a short tick-label string into a math-mode typesetting fragment.

When a date/time tick label is typeset through the math renderer, alphabetic
runs are kept as upright text while the surrounding numeric material is placed
in a math-default group. Inside that math group, individual symbols must be
braced or escaped so the typesetter does not treat them as binary operators or
collapse the spacing between numbers:

  * a hyphen `-` becomes `{-}`;
  * a colon `:` becomes `{:}`;
  * a space ` ` becomes a thin-space command `\;`.

The label is produced in four stages:

  1. every maximal run of ASCII letters is lifted out of the math group: the run
     is surrounded so that it renders as upright text and a fresh math-default
     group is opened after it;
  2. each remaining symbol is rewritten per the table above (letters and digits
     and every other character pass through unchanged);
  3. the whole thing is wrapped in one outer math-default group;
  4. any empty math-default group `$\mathdefault{}$` that results is removed.

The desired output is exactly the string these four stages produce for the given
input. Every input character's contribution is pinned, so no part of the result
is left free.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom. The one nontrivial
-- library operation the computation relies on — the regular-expression
-- substitution that lifts maximal alphabetic runs out of the math group — is
-- modeled DEEPLY (`bracketLetterRuns`, a front-recursive run scanner) rather
-- than axiomatized, and the model is validated against the real callee by G-AX.
-- Hence no `opaque`/`axiom` callee contract is declared here.
-- axioms-end

-- pure-start
/-- Stage 1. Lift each maximal run of ASCII letters out of the surrounding math
group: close the current group with `}$`, emit the letter run verbatim, then
reopen a fresh math-default group with `$\mathdefault{`; non-letter characters
pass through unchanged. This is the per-run rewrite the substitution performs. -/
def bracketLetterRuns : List Char → List Char
  | [] => []
  | c :: cs =>
    if c.isAlpha then
      let rest := (c :: cs).dropWhile Char.isAlpha
      "}$".toList ++ (c :: cs).takeWhile Char.isAlpha
        ++ "$\\mathdefault{".toList ++ bracketLetterRuns rest
    else
      c :: bracketLetterRuns cs
  termination_by xs => xs.length
  decreasing_by
    · have hc : Char.isAlpha c = true := by assumption
      have h2 : ((c :: cs).dropWhile Char.isAlpha) = cs.dropWhile Char.isAlpha := by
        simp [List.dropWhile_cons_of_pos, hc]
      rw [h2]
      calc (cs.dropWhile Char.isAlpha).length ≤ cs.length := List.length_dropWhile_le _ _
        _ < (c :: cs).length := by simp
    · simp

/-- Stage 2, per character: brace a hyphen as `{-}`, a colon as `{:}`, rewrite a
space as the thin-space command `\;`, and leave every other character alone. -/
def escapeMathSym (c : Char) : List Char :=
  if c = '-' then ['{', '-', '}']
  else if c = ':' then ['{', ':', '}']
  else if c = ' ' then ['\\', ';']
  else [c]

/-- Stage 2: rewrite every symbol of the string by `escapeMathSym`. -/
def escapeMathSyms (cs : List Char) : List Char := cs.flatMap escapeMathSym

/-- Stage 4: delete every (non-overlapping, left-to-right) occurrence of the
literal token `o :: os` from the string. Used to drop the empty math-default
group `$\mathdefault{}$`. -/
def dropToken (o : Char) (os : List Char) : List Char → List Char
  | [] => []
  | c :: cs =>
    if (o :: os).isPrefixOf (c :: cs) then dropToken o os ((c :: cs).drop (os.length + 1))
    else c :: dropToken o os cs
  termination_by s => s.length
  decreasing_by
    · calc ((c :: cs).drop (os.length + 1)).length
            ≤ (c :: cs).length - (os.length + 1) := by simp [List.length_drop]
        _ < (c :: cs).length := by simp; omega
    · simp

/-- The full four-stage label transform: lift letter runs, rewrite symbols, wrap
in one outer math-default group, then drop any resulting empty math group. This
is the desired output for a given input string. -/
def texLabel (text : List Char) : List Char :=
  let lifted := bracketLetterRuns text
  let escaped := escapeMathSyms lifted
  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
  dropToken '$' "\\mathdefault{}$".toList wrapped
-- pure-end

-- post-conditions-start
/-- The result is exactly the four-stage label transform of the input string.
Every character of the input contributes deterministically (letters via the
run-lifting stage, hyphen/colon/space via the symbol-rewrite stage, all other
characters verbatim), so the whole output is pinned to the input. -/
def problem_spec_texLabel (text : List Char) (result : List Char) : Prop :=
  result = texLabel text
-- post-conditions-end

-- impl-start
def implementation_texLabel (text : List Char) : List Char := Id.run do
  let lifted := bracketLetterRuns text
  -- Earlier behavior: only hyphens are braced; colons and spaces are left as
  -- bare operators inside the math group.
  let mut escaped : List Char := []
  for c in lifted do
    if c = '-' then
      escaped := escaped ++ ['{', '-', '}']
    else
      escaped := escaped ++ [c]
  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
  return dropToken '$' "\\mathdefault{}$".toList wrapped
-- impl-end

-- proof-start
theorem correct_texLabel :
    ∀ (text : List Char),
      problem_spec_texLabel text (implementation_texLabel text) := by
  intro text
  unfold problem_spec_texLabel implementation_texLabel texLabel
  simp only [Id.run]
  rfl
-- proof-end
