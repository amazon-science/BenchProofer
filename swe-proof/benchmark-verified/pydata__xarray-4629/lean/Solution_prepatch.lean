import Mathlib
-- imports-end

/-!
Combining the attribute mappings of several source objects under the
"override" policy: the combined attributes are taken from the FIRST source.

Each source object carries an *identity* (which object it is) and *contents*
(its key→value attribute mapping). Two distinct objects have distinct
identities; the contents are an association of keys to values.

Under the "override" policy the desired behavior is:

  * with no sources, there is nothing to combine (no result);
  * with at least one source, the combined attributes have the SAME contents
    as the first source, but live in a result object that is INDEPENDENT of
    every source — its identity differs from each source's identity, so the
    sources are never shared into the result. Changing the result later can
    therefore not be reflected back into any source.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Producing a fresh independent copy of
-- the first source's attributes — a new object whose contents equal the first
-- source's and whose identity differs from every source's — is reproduced
-- structurally (a fresh identity + a verbatim content copy), so no
-- `opaque`/`axiom` callee contract is needed. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The contents of an attribute object: an association of keys to values.
String keys/values are abstracted to `Int` by an injective encoding; only
equality of contents is observed. -/
abbrev AttrDict := List (Int × Int)

/-- A source object: its identity paired with its contents. Distinct objects
have distinct identities; only equality/distinctness of identities is observed. -/
abbrev AttrObj := Nat × AttrDict
-- pure-end

-- post-conditions-start
/-- The "override" combination, pinned at every component:

* with no sources the result is absent;
* with at least one source `first`, the result is present, its contents are
  exactly `first`'s contents (the data is carried over unchanged), and its
  identity is fresh — distinct from the identity of every source — so the
  result aliases none of the sources. -/
def problem_spec_mergeAttrsOverride
    (attrs : List AttrObj) (result : Option AttrObj) : Prop :=
  match attrs with
  | [] => result = none
  | first :: _ =>
    ∃ id, result = some (id, first.2) ∧ id ∉ attrs.map Prod.fst
-- post-conditions-end

-- impl-start
def implementation_mergeAttrsOverride
    (attrs : List AttrObj) : Option AttrObj := Id.run do
  -- Pre-patch (buggy): with no sources there is nothing to combine.
  if attrs.isEmpty then
    return none
  -- Override returns the first source object ITSELF, rather than an independent
  -- copy: the result shares the first source's identity, so a later change to
  -- the result is reflected back into that source.
  let first := attrs.head!
  return some first
-- impl-end

-- proof-start
theorem correct_mergeAttrsOverride :
    ∀ (attrs : List AttrObj),
    problem_spec_mergeAttrsOverride attrs
      (implementation_mergeAttrsOverride attrs) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
