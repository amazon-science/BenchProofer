"""Twin-artifact model for pylint-dev__pylint-8898.

Behaviour under specification (stated as the desired property, not as an edit):

  A configuration value carrying several regular expressions is given as one
  text string. The result is the ordered list of the individual expressions
  obtained by treating the comma as the separator between expressions, with one
  exception: a comma that occurs inside a `{...}` group of an expression (such
  as the comma in `(foo{1,3})`) belongs to that expression and does NOT separate
  it. Each resulting expression is whitespace-trimmed, and any expression that
  ends up containing no characters is dropped; order is preserved.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` (one expression) and
`PSeq[PSeq[int]]` (the list of expressions) via `ToSeq`. The pure functions
`seg_of` and `finalize_seq` are the formal carrier of the contract above,
modelled DEEPLY as front-recursive folds; the per-segment whitespace trim
(`strip_seq`, an unchanged library operation) is an uninterpreted deterministic
function the specification applies identically on both sides, validated against
the real trim by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def strip_seq(s: PSeq[int]) -> PSeq[int]:
    """Whitespace trim of a single segment (the unchanged community/library
    trim the surrounding code applies to every segment). Modelled as an
    uninterpreted DETERMINISTIC function of its argument: the specification
    applies the same `strip_seq` on both sides of every equality, so no
    behavioural property is asserted about it here and it cannot over-claim.
    Its determinism (a pure function of the segment) is checked against the
    real trim by axiom_check.py (G-AX); provenance in mapping.md.
    """
    pass
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty expression (no code points)."""
    return PSeq(0).take(0)


@Pure
def empty_segs() -> PSeq[PSeq[int]]:
    """The empty list of expressions."""
    return PSeq(empty_seq()).take(0)


@Pure
def cons(head: PSeq[int], rest: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Prepend one segment to a list of segments. Factored into a helper to
    avoid a nested-sequence-literal translator limitation on
    `PSeq(<sequence expression>) + rest`."""
    return PSeq(head) + rest


@Pure
def seg_of(s: PSeq[int], opn: bool) -> PSeq[PSeq[int]]:
    """The raw (untrimmed) segmentation of `s` given that a brace region is
    currently open iff `opn`. Front-recursive (one unfold per code point), so a
    single forward scan discharges the value equality. Always at least one
    segment (a trailing separator yields a trailing empty segment)."""
    Ensures(len(Result()) >= 1)
    if len(s) == 0:
        return PSeq(empty_seq())
    c = s[0]
    # `{` (123) opens a region; `}` (125) closes an open region; else unchanged.
    no = (c == 123) or (opn and not (c == 125))
    rest = seg_of(s.drop(1), no)
    # comma (44) outside any open brace region ends the current segment.
    if c == 44 and not opn:
        return cons(empty_seq(), rest)
    return cons(PSeq(c) + rest[0], rest.drop(1))


@Pure
def merge2(R: PSeq[PSeq[int]], cur: PSeq[int], S: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Stitch the already-closed segments `R`, the in-progress segment `cur`,
    and the segmentation `S` of the remaining suffix into one segmentation: the
    last open segment `cur` continues into the first segment of `S`."""
    Requires(len(S) >= 1)
    return R + cons(cur + S[0], S.drop(1))


@Pure
def finalize_seq(raw: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Discard every raw segment that received no character (length 0) and
    whitespace-trim the rest. Front-recursive (one unfold per segment)."""
    if len(raw) == 0:
        return empty_segs()
    if len(raw[0]) == 0:
        return finalize_seq(raw.drop(1))
    return cons(strip_seq(raw[0]), finalize_seq(raw.drop(1)))
# pure-end


def comma_split(text: List[int]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the trimmed, non-empty segments of the brace-aware
    # comma segmentation: a comma inside an open `{...}` region never splits.
    Ensures(ToSeq(Result()) == finalize_seq(seg_of(ToSeq(text), False)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
