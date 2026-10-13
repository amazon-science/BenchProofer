"""Twin-artifact model for scikit-learn__scikit-learn-13496.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An incremental-ensemble estimator holds a roster of already-fitted members
  (each identified by a stable identity) and is asked to (re)fit so the roster
  reaches a requested total size. A construction-time option decides whether a
  subsequent fit REUSES the members already present:

    * When the caller opts in to reuse AND members are already present, the
      existing members are kept exactly as they are — same members, in the same
      order, at the same positions — and the roster is merely EXTENDED with
      freshly-built members until it reaches the requested total size. In
      particular the first existing member is the very same member afterwards
      (its identity is preserved, not rebuilt), and the final size is the
      requested total.

    * Otherwise (the caller does not opt in, or there is nothing yet to reuse)
      the roster is rebuilt from scratch: every member of the result is a
      freshly-built one, so no previously-present member survives, and the
      final size is again the requested total.

  The option the caller supplies at construction is the one that governs this
  reuse decision at fit time: it must be carried through faithfully, not
  silently forced off. The behaviour pinned here is exactly that a caller who
  opts in to reuse, fits, then enlarges the requested total and fits again,
  ends with the requested number of members and with its original first member
  still in place.

The roster is modelled as a `List[int]` of member identities. A freshly-built
member is modelled by the sentinel identity `FRESH_MEMBER` (-1); an
already-present member carries a non-negative identity, so a preserved member
is structurally distinguishable from a freshly-built one. The reuse option is a
plain `bool`. Nagini bans `str`/object identity, so identities are ints and the
specification is carried over `PSeq[int]` via `ToSeq`; `fresh_run(n)` is the
pure run of `n` freshly-built members.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the reuse decision and the roster update are modelled deeply;
#  there is no unchanged opaque callee the proof must consume.)
# axioms-end


# pure-start
@Pure
def FRESH_MEMBER() -> int:
    """Identity of a freshly-built member. Distinct from every already-present
    member identity (which the precondition pins to be non-negative)."""
    return -1


@Pure
def effective_reuse(requested_reuse: bool, have_members: bool) -> bool:
    """The reuse decision actually taken at fit time, given the option the
    caller supplied at construction (`requested_reuse`) and whether any members
    are already present (`have_members`). The construction-time option is
    carried through faithfully: reuse happens exactly when the caller opted in
    AND members are already present."""
    return requested_reuse and have_members


@Pure
def fresh_run(n: int) -> PSeq[int]:
    """A run of `n` freshly-built members (`n <= 0` gives the empty run). Front-
    recursive so one unfold is available per step; every element is the
    freshly-built sentinel, so a rebuilt roster retains no already-present
    (non-negative) member."""
    Ensures(Implies(n <= 0, len(Result()) == 0))
    Ensures(Implies(n >= 0, len(Result()) == n))
    if n <= 0:
        return PSeq(0).take(0)
    return PSeq(FRESH_MEMBER()) + fresh_run(n - 1)


@Pure
def lemma_fresh_snoc(n: int) -> bool:
    """Appending one more freshly-built member at the BACK of a fresh run of
    length `n` yields the fresh run of length `n + 1`. (The building loops grow
    the run by back-append; `fresh_run` is front-recursive, so this bridges the
    two.) Proven by front-induction; exposed to callers as an equation."""
    Requires(n >= 0)
    Ensures(Result())
    Ensures(fresh_run(n) + PSeq(FRESH_MEMBER()) == fresh_run(n + 1))
    if n == 0:
        return True
    return lemma_fresh_snoc(n - 1)
# pure-end


def reuse_and_extend(existing: List[int], target_count: int) -> List[int]:
    # pre-conditions-start
    # Read-only roster of already-present members: fractional permission.
    Requires(Acc(list_pred(existing), 1 / 2))
    Requires(len(existing) <= target_count)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(existing), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The roster reaches exactly the requested total size, the existing members
    # are preserved verbatim as the prefix (same identities, same order, same
    # positions), and the remainder are freshly-built members.
    Ensures(len(Result()) == target_count)
    Ensures(ToSeq(Result()) ==
            ToSeq(existing) + fresh_run(target_count - len(existing)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < len(existing):
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(existing))
        Invariant(len(existing) <= target_count)
        Invariant(len(result) == j)
        Invariant(ToSeq(result) == ToSeq(existing).take(j))
        Invariant(MustTerminate(len(existing) - j + 1))
        # invariants-end
        result.append(existing[j])
        j = j + 1
    Assert(ToSeq(existing).take(len(existing)) == ToSeq(existing))
    Assert(ToSeq(result) == ToSeq(existing))
    while len(result) < target_count:
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(existing) <= len(result) and
                  len(result) <= target_count)
        Invariant(ToSeq(result) ==
                  ToSeq(existing) + fresh_run(len(result) - len(existing)))
        Invariant(MustTerminate(target_count - len(result) + 1))
        # invariants-end
        Assert(lemma_fresh_snoc(len(result) - len(existing)))
        result.append(FRESH_MEMBER())
    return result
    # impl-end


def rebuild_all(target_count: int) -> List[int]:
    # pre-conditions-start
    Requires(target_count >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # Every member of the result is freshly built, so no previously-present
    # member survives; the roster reaches exactly the requested total size.
    Ensures(len(Result()) == target_count)
    Ensures(ToSeq(Result()) == fresh_run(target_count))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    while len(result) < target_count:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= len(result) and len(result) <= target_count)
        Invariant(ToSeq(result) == fresh_run(len(result)))
        Invariant(MustTerminate(target_count - len(result) + 1))
        # invariants-end
        Assert(lemma_fresh_snoc(len(result)))
        result.append(FRESH_MEMBER())
    return result
    # impl-end


def refit_to_size(existing: List[int], target_count: int,
                  requested_reuse: bool) -> List[int]:
    # pre-conditions-start
    # Read-only roster of already-present members: fractional permission.
    Requires(Acc(list_pred(existing), 1 / 2))
    # The requested total is at least the number of members already present
    # (one cannot ask for fewer members than are already kept on reuse).
    Requires(len(existing) <= target_count)
    # Already-present member identities are non-negative, hence distinct from a
    # freshly-built member's sentinel identity FRESH_MEMBER (-1).
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(existing), existing[k] >= 0),
                     [[existing[k]]])))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input returned at the same fractional permission, so no caller
    # can satisfy a postcondition vacuously by overwriting it.
    Ensures(Acc(list_pred(existing), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The roster always reaches exactly the requested total size.
    Ensures(len(Result()) == target_count)
    # Reuse case: the existing members are preserved verbatim as the prefix and
    # the roster is merely extended with freshly-built members. The first
    # existing member therefore survives unchanged.
    Ensures(Implies(effective_reuse(requested_reuse, len(existing) > 0),
                    ToSeq(Result()) ==
                    ToSeq(existing) + fresh_run(target_count - len(existing))))
    # Rebuild case: every member of the result is freshly built, so no
    # previously-present member survives.
    Ensures(Implies(not effective_reuse(requested_reuse, len(existing) > 0),
                    ToSeq(Result()) == fresh_run(target_count)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the caller's reuse option is NOT carried through to
    # the fit-time decision — the stored option keeps its inherited default of
    # "off" — so the roster is rebuilt from scratch on every fit regardless of
    # what the caller requested. (This drops the requested_reuse parameter.)
    return rebuild_all(target_count)
    # impl-end
