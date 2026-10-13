"""Twin-artifact model for pytest-dev__pytest-5787.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A failure representation that is sent across a process boundary is reduced to
  a transport form built only from primitive entries (the "serialize" step) and
  later reconstructed from that transport form (the "deserialize" step). Such a
  representation is a CHAIN of one or more links; each link records a distinct
  stage of the failure (an originating cause, then the intermediate stages, and
  finally the outermost failure that surfaced), in that order. A single,
  unchained failure is just the degenerate chain of length one.

  The required guarantee is that the transport form preserves the WHOLE chain,
  not only its outermost link, and that reconstruction is its exact inverse:

    (1) serialize(chain) carries every link, in order — its length and each
        link are those of the input chain (no link is dropped, none reordered);
    (2) deserialize(transport) reproduces every link of the transport form, in
        order — so deserialize(serialize(chain)) == chain for chains of ANY
        length, in particular length >= 2 (a genuinely multi-stage failure),
        not merely length one.

  Each link is an opaque token here; what is under specification is that the
  COUNT and ORDER of links survive the round trip — a chain of several stages
  must not collapse to a single stage.

Each link is modelled as an `int` token and a chain as a `List[int]` of those
tokens (Nagini bans `str` indexing, and the per-link content is an unchanged
structural copy, irrelevant to the count/order property under test). The pure
sequence theory `PSeq[int]` carries the specification. The per-link structural
copy that both steps perform on a link's contents is the unchanged behaviour,
modelled deeply as the identity on the token and validated == the real per-link
(de)serializer out-of-band by axiom_check.py (G-AX); it is not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axiom. The per-link structural copy each step
# applies to one link's contents is the unchanged callee behaviour; it is
# modelled DEEPLY as the identity on the link token (`copy_link` below) and
# validated == the real per-link (de)serializer by axiom_check.py / G-AX as an
# A-reference. The proof never depends on a @ContractOnly contract.)
# axioms-end


# pure-start
@Pure
def copy_link(link: int) -> int:
    """The structural copy applied to a single link's contents. It is the
    unchanged behaviour and is content-preserving: the round trip on one link
    is the identity on its token."""
    return link
# pure-end


def serialize_chain(chain: List[int]) -> List[int]:
    # pre-conditions-start
    # `chain` is a read-only input (fractional permission): serialization reads
    # the links and emits a fresh transport list; it does not mutate the chain.
    Requires(Acc(list_pred(chain), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Requires(len(chain) >= 1)
    Ensures(Acc(list_pred(chain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The transport form carries the WHOLE chain, in order: same length and
    # every link preserved (each via the content-preserving structural copy).
    Ensures(len(Result()) == len(chain))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(chain),
            ToSeq(Result())[k] == copy_link(ToSeq(chain)[k])),
            [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
                  [[ToSeq(out)[k]]])))
        Invariant(MustTerminate(len(chain) - i + 1))
        # invariants-end
        old = out  # type: List[int]
        out = out + [chain[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == chain[i])
        i = i + 1
    return out
    # impl-end


def deserialize_chain(transport: List[int]) -> List[int]:
    # pre-conditions-start
    # `transport` is a read-only input (fractional permission): reconstruction
    # reads the transport links and emits a fresh chain; it does not mutate it.
    Requires(Acc(list_pred(transport), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Requires(len(transport) >= 1)
    Ensures(Acc(list_pred(transport), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Reconstruction reproduces EVERY transport link, in order: same length and
    # every link preserved (each via the content-preserving structural copy).
    Ensures(len(Result()) == len(transport))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(transport),
            ToSeq(Result())[k] == copy_link(ToSeq(transport)[k])),
            [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    # Pre-fix reconstruction: a single link is always rebuilt from the
    # outermost entry of the transport form, ignoring any earlier links — so a
    # multi-stage transport form is reconstructed as one stage only.
    out = []  # type: List[int]
    out = out + [transport[len(transport) - 1]]
    return out
    # impl-end
