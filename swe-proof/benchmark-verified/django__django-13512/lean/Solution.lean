import Mathlib
-- imports-end

/-!
Serializing a text value to its JSON string-literal form.

A text value is a sequence of Unicode characters. Its JSON string literal is the
characters between a pair of `"` delimiters, where each character is rendered as
follows:

  * the quotation mark `"` and the backslash `\` are written as the two-character
    escapes `\"` and `\\`;
  * the control characters backspace, tab, line feed, form feed and carriage
    return are written as the short escapes `\b`, `\t`, `\n`, `\f`, `\r`;
  * any other control character below code point U+0020 is written as a
    six-character escape `\u00XX` (lowercase hexadecimal);
  * every remaining character — INCLUDING every non-ASCII character (accented
    letters, CJK text, emoji, …) — is written out literally as itself.

In particular a non-ASCII character is emitted verbatim in the output; it is NOT
expanded into a `\uXXXX` escape sequence. So the text `中` serializes to the
three-code-point literal `"中"`, and the text `a` serializes to `"a"`.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-character JSON
-- string escaping rule is spelled out directly (`escapeChar` below) from the
-- public description of the desired serialization; there is no opaque repo
-- callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- Lowercase hexadecimal digit for `n < 16`. -/
def hexDigit (n : Nat) : Char :=
  if n < 10 then Char.ofNat (n + 0x30) else Char.ofNat (n - 10 + 0x61)

/-- The JSON string-literal rendering of a single character (the body, i.e. with
no surrounding delimiters). `"` and `\` get two-character escapes; the five named
control characters get their short escapes; any other character below U+0020 gets
a `\u00XX` escape; every other character — every printable and every non-ASCII
character — is emitted literally as itself. -/
def escapeChar (c : Char) : List Char :=
  let n := c.toNat
  if n = 0x22 then ['\\', '"']
  else if n = 0x5c then ['\\', '\\']
  else if n = 0x08 then ['\\', 'b']
  else if n = 0x09 then ['\\', 't']
  else if n = 0x0a then ['\\', 'n']
  else if n = 0x0c then ['\\', 'f']
  else if n = 0x0d then ['\\', 'r']
  else if n < 0x20 then ['\\', 'u', '0', '0', hexDigit (n / 16), hexDigit (n % 16)]
  else [c]

/-- Front-recursive escaping of a whole character sequence (the literal body,
without the surrounding `"` delimiters). -/
def escapeBody : List Char → List Char
  | [] => []
  | c :: cs => escapeChar c ++ escapeBody cs
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the input text: it is the per-character
escaped body (`escapeBody`) wrapped in a pair of `"` delimiters. No output
component is left free — every character of the result is determined by the
corresponding input character via `escapeChar`, and the two delimiters are constant.
Because `escapeChar` emits every non-control, non-`"`, non-`\` character (in
particular every non-ASCII character) literally, the result contains those
characters verbatim rather than as `\uXXXX` escapes. -/
def problem_spec_jsonEncodeString (s : List Char) (result : List Char) : Prop :=
  result = ('"' :: escapeBody s) ++ ['"']
-- post-conditions-end

-- impl-start
def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in s do
    acc := acc ++ escapeChar c
  return ('"' :: acc) ++ ['"']
-- impl-end

-- proof-start
/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
`forIn` accumulation appends the per-character escaping `escapeBody`. -/
theorem forIn_escape_eq : ∀ (s init : List Char),
    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
      = init ++ escapeBody s := by
  intro s
  induction s with
  | nil => intro init; simp [escapeBody]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih (init ++ escapeChar a)]
    simp [escapeBody, List.append_assoc]

theorem correct_jsonEncodeString :
    ∀ (s : List Char),
      problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
  intro s
  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
  simp only [Id.run, bind]
  rw [forIn_escape_eq s []]
  simp only [List.nil_append]
  rfl
-- proof-end
