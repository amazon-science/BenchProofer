"""Twin-artifact model for pytest-dev__pytest-7324.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual match expression turns a bare identifier (an arbitrary run of word
  characters, possibly spelling a reserved word such as the three special
  constant names) into a name node of a tiny boolean program, which is later
  evaluated by looking the name up through a user-supplied membership predicate.

  Two behavioural properties are specified:

  (1) The name emitted for an identifier always begins with a single
      designated non-word sentinel code point. Because its first code point is
      that sentinel rather
      than a letter, the emitted name is always a legal program name and can
      never coincide with one of the three reserved constant spellings ("True",
      "False", "None") whose first code point is a letter — those spellings are
      legal *expression identifiers* yet illegal as bare program names, and the
      sentinel keeps them legal.

  (2) The membership lookup consults the predicate on the ORIGINAL identifier:
      from a sentinel-led name it recovers the identifier by removing exactly
      the one leading sentinel code point. Hence the predicate is always asked
      about the identifier the user actually wrote. Recovery is the exact
      inverse of (1), so the round trip is the identity on every identifier,
      including the three reserved spellings.

Strings/identifiers are modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing); specifications are carried over `PSeq[int]` via `ToSeq`.
The user membership predicate is an unchanged callee, axiomatized (`match`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def match(name: PSeq[int]) -> bool:
    """The unchanged user-supplied membership predicate consulted at lookup
    time (an arbitrary total function from an identifier to a boolean). The
    proof only relies on it being a deterministic function of its argument, so
    that asking it about the recovered identifier is well defined. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    pass
# axioms-end


# pure-start
@Pure
def sentinel() -> int:
    """The single designated sentinel code point every emitted name begins
    with. It is a non-word code point, so no identifier body can begin with it, and it is
    distinct from the first code point of each reserved constant spelling
    (84/70/78 — "True"/"False"/"None"), so a sentinel-led name is never a bare
    reserved spelling."""
    return 36


@Pure
def strip_sentinel(name: PSeq[int]) -> PSeq[int]:
    """Recover the original identifier from a sentinel-prefixed name by
    removing exactly the one leading sentinel code point."""
    Requires(len(name) >= 1)
    return name.drop(1)
# pure-end


def encode_ident(ident: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    # The emitted name must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value pins only vacuously
    # by never returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) the emitted name is the identifier led by the one sentinel code point.
    Ensures(ToSeq(Result()) == PSeq(sentinel()) + ToSeq(ident))
    # the emitted name is non-empty and its first code point is the sentinel —
    # never a letter, so it equals none of the three reserved constant spellings
    # (whose first code points are 84/70/78).
    Ensures(len(Result()) >= 1 and ToSeq(Result())[0] == sentinel())
    Ensures(ToSeq(Result())[0] != 84)   # not "True"  (T)
    Ensures(ToSeq(Result())[0] != 70)   # not "False" (F)
    Ensures(ToSeq(Result())[0] != 78)   # not "None"  (N)
    # (2) round trip: removing the leading sentinel from the emitted name
    # recovers the original identifier exactly.
    Ensures(strip_sentinel(ToSeq(Result())) == ToSeq(ident))
    # post-conditions-end
    # impl-start
    result = [sentinel()]  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(ident))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(ident) - i.
        Invariant(MustTerminate(len(ident) - i))
        Invariant(ToSeq(result) == PSeq(sentinel()) + ToSeq(ident).take(i))
        # invariants-end
        result = result + [ident[i]]
        i = i + 1
    return result
    # impl-end


def lookup_key(key: List[int]) -> bool:
    # pre-conditions-start
    # the lookup is reached only with a sentinel-prefixed name (the only names
    # the program ever contains), so the key is non-empty and begins with it.
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(len(ToSeq(key)) >= 1 and ToSeq(key)[0] == sentinel())
    # The lookup answer must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value pin only vacuously
    # by never returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 2))
    # the key still begins with the sentinel in the post-state (it is read-only).
    Ensures(len(ToSeq(key)) >= 1 and ToSeq(key)[0] == sentinel())
    # the predicate is consulted on the recovered identifier (the key with its
    # single leading sentinel removed), not on the raw prefixed name.
    Ensures(Result() == match(strip_sentinel(ToSeq(key))))
    # post-conditions-end
    # impl-start
    # Pre-image of site (2): the predicate is consulted on the raw key, with the
    # leading sentinel still attached (the sentinel is not removed before lookup).
    return match(ToSeq(key))
    # impl-end
