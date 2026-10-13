import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee. The
   behaviour under spec is the segmentation of a keystroke string into its keys
   and the separators between them. It is computed entirely from the input
   sequence with concrete character operations and is modeled DEEPLY in the
   `pure` region below; nothing is borrowed from an oracle. The downstream
   rendering that wraps each produced key/separator segment is unchanged control
   flow reached identically for any segmentation, and is not modeled here — only
   the segmentation, whose behaviour the issue is about, is. See mapping.md §3
   and refinement.md §C. -/
-- axioms-end

-- pure-start
/- The three connector characters that may join two keys in a compound
   keystroke (`-`, `+`, `^`). Returns `true` exactly for these. -/
def isSep (c : Char) : Bool := c == '-' || c == '+' || c == '^'

/- The whitespace class the scanner recognizes between two keys: the full
   Unicode whitespace set of 29 code points (U+0009–U+000D, U+001C–U+0020,
   U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F,
   U+3000), so a non-ASCII space such as the no-break space U+00A0 between two
   keys joins them just as a plain space does. A MAXIMAL RUN of these
   characters counts as ONE separator, not one separator per character. -/
def isBlank (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n = 0x85 || n = 0xa0 || n = 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n = 0x2028 || n = 0x2029 ||
  n = 0x202f || n = 0x205f || n = 0x3000

/- Whether a character counts as a key character FLANKING a separator. Every
   character does except the line feed U+000A: the scanner's notion of "a
   character sits here" does not admit a line break, so a line feed neither
   closes a key to the left of a separator nor opens one to its right. -/
def isFlank (c : Char) : Bool := c != '\n'

/- Whether a flanking key character sits at the front of `s`; false at the end
   of the input, where nothing follows at all. -/
def headFlanks : List Char → Bool
  | []     => false
  | d :: _ => isFlank d

/- Whether the LAST character of `s` is a flanking key character; false for the
   empty list. Carries "a key character immediately precedes the cursor"
   forward across one scan step. -/
def lastFlank : List Char → Bool
  | []      => false
  | [c]     => isFlank c
  | _ :: cs => lastFlank cs

/- Length of the leading maximal run of whitespace. -/
def blankRun : List Char → Nat
  | []      => 0
  | c :: cs => if isBlank c then 1 + blankRun cs else 0

/- Trim a candidate separator of length `n` at the front of `rest` to the
   longest prefix that is still FOLLOWED by a flanking key character, or to 0 if
   no such prefix exists. This is what makes a separator require a key on its
   RIGHT: a candidate run reaching the end of the input, or followed only by a
   line feed, is shortened one character at a time until a key character
   follows it, and a one-character candidate with nothing usable after it is
   rejected outright, so its character stays part of the surrounding key. -/
def gapFit (rest : List Char) : Nat → Nat
  | 0     => 0
  | n + 1 => if headFlanks (rest.drop (n + 1)) then n + 1 else gapFit rest n

/- Length of the separator starting at the front of `rest`, or 0 when the front
   of `rest` is an ordinary key character. A separator is recognized only when a
   flanking key character immediately PRECEDES it (`leftOk`) and, after trimming
   by `gapFit`, a flanking key character FOLLOWS it. Two forms are recognized: a
   single connector character, and a maximal run of whitespace. Consequently a
   connector or a whitespace run at the very start of the input, at its very
   end, or standing alone as the whole input, is not a separator and belongs to
   the key around it. -/
def sepLen (leftOk : Bool) : List Char → Nat
  | []      => 0
  | c :: cs =>
      if leftOk = true then
        (if isSep c then gapFit (c :: cs) 1
         else if isBlank c then gapFit (c :: cs) (blankRun (c :: cs))
         else 0)
      else 0

/- One forward scan step: the separator run at the front if one is recognized
   there, otherwise a single key character. At least 1 on any nonempty input,
   which is what makes the scan progress. -/
def stepLen (leftOk : Bool) (rest : List Char) : Nat :=
  if sepLen leftOk rest = 0 then 1 else sepLen leftOk rest

/- A nonempty remainder always advances by at least one character: either a
   recognized separator run (`sepLen ≥ 1`) or one key character. -/
theorem stepLen_pos (leftOk : Bool) (rest : List Char) : 1 ≤ stepLen leftOk rest := by
  unfold stepLen; split <;> omega

/- One step off a nonempty remainder STRICTLY shortens it (`stepLen_pos`). This
   is the scan's progress, and it discharges the measure obligation that
   TOTAL-correctness semantics emits for the `while` below. -/
theorem stepLen_drop_lt {leftOk : Bool} {rest : List Char} (h : rest ≠ []) :
    (rest.drop (stepLen leftOk rest)).length < rest.length := by
  have h1 := stepLen_pos leftOk rest
  have hlen : 0 < rest.length := by
    cases rest with | nil => exact absurd rfl h | cons _ _ => simp
  simp only [List.length_drop]; omega

/- Segment a keystroke into its parts, scanning left to right while carrying the
   partial current key `cur` and `leftOk`, which records whether a flanking key
   character immediately precedes the cursor.

   * When a separator is recognized at the cursor (`sepLen ≠ 0`), the current
     key is closed and emitted, the separator run itself is emitted as its own
     segment, and a fresh key is started.
   * Otherwise the characters of the step extend the current key.

   `leftOk` for the next step is whether the last character just consumed is a
   flanking key character. The result lists, in order, the keys interleaved with
   the separators between them; a keystroke with no interior separator yields
   the single segment `[whole input]`, and the empty input yields `[[]]`.
   Front-recursive so a single unfold is available per scan step (the
   forward-scan pattern, plan §5.4). -/
def splitParts (leftOk : Bool) (cur : List Char) (rest : List Char) :
    List (List Char) :=
  if h : rest = [] then [cur]
  else
    if sepLen leftOk rest = 0
    then splitParts (lastFlank (rest.take (stepLen leftOk rest)))
           (cur ++ rest.take (stepLen leftOk rest)) (rest.drop (stepLen leftOk rest))
    else cur :: rest.take (stepLen leftOk rest) ::
           splitParts (lastFlank (rest.take (stepLen leftOk rest))) []
             (rest.drop (stepLen leftOk rest))
  termination_by rest.length
  decreasing_by all_goals exact stepLen_drop_lt (leftOk := leftOk) h

/- Reaching the end of the input emits the key built so far. -/
@[grind] theorem splitParts_nil (leftOk : Bool) (cur : List Char) :
    splitParts leftOk cur [] = [cur] := by
  unfold splitParts; simp

/- The single front-unfold one scan step needs. -/
@[grind] theorem splitParts_step (leftOk : Bool) (cur : List Char)
    (rest : List Char) (h : rest ≠ []) :
    splitParts leftOk cur rest =
      (if sepLen leftOk rest = 0
       then splitParts (lastFlank (rest.take (stepLen leftOk rest)))
              (cur ++ rest.take (stepLen leftOk rest)) (rest.drop (stepLen leftOk rest))
       else cur :: rest.take (stepLen leftOk rest) ::
              splitParts (lastFlank (rest.take (stepLen leftOk rest))) []
                (rest.drop (stepLen leftOk rest))) := by
  conv_lhs => unfold splitParts
  simp [h]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Segment a keystroke into its keys and the separators that join them. A
   separator is a single connector character (`-`, `+`, `^`) or a maximal run of
   whitespace, and is recognized only where a flanking key character sits
   immediately on both sides of it; a connector or whitespace run at the start
   of the input, at its end, or standing alone as the whole input is an ordinary
   key character. The output lists the keys interleaved with the separating
   runs, in order; an input with no interior separator is returned unchanged as
   a single segment.

   `text` is read-only (not `mut`); the scan only reads it and builds the result
   (directive 5). -/
method kbdSplit (text : List Char) return (out : List (List Char))
  ensures out = splitParts false [] text
  do
    -- impl-start
    -- Pre-image skeleton: a connector character splits whenever it occurs and
    -- whitespace is never a separator, regardless of whether keys flank
    -- anything (the simplistic separator test). The frozen spec recognizes a
    -- separator — a connector OR a maximal whitespace run — only where key
    -- characters flank it on both sides, so a leading/trailing/standalone
    -- connector and every whitespace-separated keystroke diverge, and
    -- prove_correct MUST fail (e.g. on the single-key input "-").
    let mut acc : List (List Char) := []
    let mut cur : List Char := []
    let mut i := 0
    while i < text.length
      invariant i ≤ text.length
      invariant splitParts false [] text = acc ++ splitParts true cur (text.drop i)
      done_with i = text.length
      decreasing text.length - i
    do
      let c := text[i]!
      if isSep c = true then
        acc := acc ++ [cur, [c]]
        cur := []
        i := i + 1
      else
        cur := cur ++ [c]
        i := i + 1
    return acc ++ [cur]
    -- impl-end

prove_correct kbdSplit by
  loom_solve
  all_goals try exact stepLen_drop_lt (by assumption)
