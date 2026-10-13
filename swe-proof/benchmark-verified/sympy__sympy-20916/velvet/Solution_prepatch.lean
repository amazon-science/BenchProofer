import Velvet.Std
-- imports-end

/- Total correctness: the real trailing-digit step is a straight-line anchored
   regex match plus a tuple unpack — it always terminates — so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge `out = peelDigits name` vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Two per-code-point character classes, taken as opaque recognizers because
   they classify the FULL code-point space, not just the ASCII subset Lean's
   built-in `Char.isAlpha`/`isDigit` cover:

   * `isLetterU c` — `c` is a letter code point (any script, not only A–Z/a–z).
   * `isDigitU  c` — `c` is a decimal-digit code point (any script).

   They are mutually exclusive and neither holds of the underscore. Provenance
   and executable soundness (each is validated against the real per-code-point
   classifier by axiom_check.py, as an A-reference) are in mapping.md §3. These
   are NOT contracts about the function under change; they are the unchanged
   character-classification primitives the peel step consults. -/
axiom isLetterU : Char → Bool
axiom isDigitU : Char → Bool
axiom letter_not_digit : ∀ c : Char, isLetterU c = true → isDigitU c = false
axiom underscore_not_letter : isLetterU '_' = false
axiom underscore_not_digit : isDigitU '_' = false
-- axioms-end

-- pure-start
/- The maximal leading run of letter code points of `cs`. -/
noncomputable def letterPrefix (cs : List Char) : List Char := cs.takeWhile isLetterU

/- What remains after the maximal leading letter run. -/
noncomputable def afterLetters (cs : List Char) : List Char := cs.dropWhile isLetterU

/- Drop ONE final newline (U+000A) if `cs` ends with it; otherwise `cs`
   unchanged. The trailing-digit recognizer tolerates exactly one final
   newline at the very end of the name: it is ignored by the acceptance test
   and omitted from the returned digit block (mapping.md §3.3). -/
def stripFinalNewline (cs : List Char) : List Char :=
  if cs.getLast? = some '\n' then cs.dropLast else cs

/- Peel a trailing decimal block off a parsed name, treating it as a subscript
   exactly when the name — after setting aside at most one final newline
   character — is a non-empty run of letter code points followed by a non-empty
   run made up ENTIRELY of decimal-digit code points (and nothing else). On a
   match the result is `(letters, some digits)` (the set-aside newline, if any,
   is dropped); otherwise the name is returned whole as `(name, none)`.

   This is the deep model of the trailing-digit recognizer. The acceptance
   condition is `letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU` with
   `digits = stripFinalNewline rest`, i.e. the input is precisely
   `letters ++ digits` or `letters ++ digits ++ ['\n']` with `letters` a
   maximal letter run and `digits` all digits — which is the structural reading
   of "a letter block immediately followed by a digit block spanning the whole
   name, up to one trailing newline". mapping.md §3. -/
noncomputable def peelDigits (name : List Char) : List Char × Option (List Char) :=
  let letters := letterPrefix name
  let rest := afterLetters name
  let digits := stripFinalNewline rest
  if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
  else (name, none)

@[grind] lemma peelDigits_def (name : List Char) :
    peelDigits name =
      (let letters := letterPrefix name
       let rest := afterLetters name
       let digits := stripFinalNewline rest
       if letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU then (letters, some digits)
       else (name, none)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Given an already-parsed symbol base `name`, decide whether it ends in a block
   of digits that should be split off and treated as a trailing subscript.

   When `name` — ignoring at most one final newline character — consists of a
   (non-empty) block of alphabetic code points immediately followed by a
   (non-empty) block of decimal-digit code points — in ANY script,
   Greek/Latin/etc. treated alike — the digit block is split off: the result is
   the alphabetic block paired with `some <digits>` (the tolerated final
   newline, if present, is dropped). Otherwise the name is left intact and
   paired with `none`.

   `name` is read-only: the routine only reads it and returns derived values. -/
noncomputable section
method splitTrailingDigits (name : List Char)
    return (out : List Char × Option (List Char))
  ensures out = peelDigits name
  do
    -- impl-start
    -- Pre-patch skeleton: the leading letter block and trailing digit block are
    -- recognized only over the ASCII letter/digit subset (`Char.isAlpha` /
    -- `Char.isDigit`). A name whose leading letters or trailing digits lie
    -- outside ASCII is therefore left intact rather than split. (The `$`
    -- anchor's one-trailing-newline tolerance is the same pre- and post-patch,
    -- so the skeleton strips it too.)
    let letters := name.takeWhile Char.isAlpha
    let rest := name.dropWhile Char.isAlpha
    let digits := stripFinalNewline rest
    let out : List Char × Option (List Char) :=
      if letters ≠ [] ∧ digits ≠ [] ∧ digits.all Char.isDigit then (letters, some digits)
      else (name, none)
    return out
    -- impl-end
end

prove_correct splitTrailingDigits by
  loom_solve
