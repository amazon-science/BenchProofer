"""Twin-artifact model for sphinx-doc__sphinx-8548.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the documented members of a class are gathered with inheritance enabled,
  the comment-derived documentation of a data attribute must be found for the
  attribute no matter WHICH class along the class's method-resolution order
  (MRO) the attribute's documentation was recorded under -- not only the
  documentation recorded directly under the class itself.

  A documentation record is keyed by a pair (owner, attribute-name), where
  `owner` identifies the class whose source the documentation comment was read
  from. The resolution for a queried attribute name is:

    * the name resolves to a documentation body exactly when some record names
      it whose `owner` is one of the classes on the MRO (the class itself OR
      any of its base classes) -- so an attribute documented only on a base
      class still resolves;

    * when several records name the attribute under different MRO classes, the
      record whose `owner` sits EARLIEST on the MRO wins (the class itself
      overrides its bases); among records of that same owner, the first-recorded
      one wins;

    * if no MRO class owns a matching record, the name resolves to the absent
      marker.

  Resolution is a bounded scan of the finite MRO against the finite record
  table: the operation MUST terminate and return its answer (a total-
  correctness obligation, carried as MustTerminate in the precondition).

  The discriminating guarantee: an attribute documented ONLY on a base class
  resolves (to that base class's documentation), and an attribute documented on
  both the class and a base class resolves to the class's own documentation. A
  resolution that matches records only against the class's own `owner` does NOT
  satisfy this -- it leaves every base-only attribute absent.

Identifiers (class owners, attribute names, documentation bodies) are modelled
as integer codes; the MRO and the record table are `List[int]` carriers, with
the specification carried by `PSeq[int]` via `ToSeq`. No callee is axiomatized:
the membership/precedence resolution is the changed decision logic and is
modelled deeply (pure `resolve_from` / `lookup_owner_doc`), paired with a
verified nested-loop implementation that mirrors it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The operation that changed -- the rule deciding which
# documentation record resolves a given attribute name (own-owner match vs.
# any-MRO-owner match, with earliest-MRO-owner precedence) -- is the decision
# logic under specification, so it is modelled DEEPLY here (the pure
# `resolve_from` / `lookup_owner_doc` spec and the verified nested loop), never
# hidden behind an axiom.
# axioms-end


# pure-start
ABSENT = -1  # "no documentation record resolves this name"


@Pure
def lookup_owner_doc(owner: int, nm: int, ens: PSeq[int], enm: PSeq[int],
                     edoc: PSeq[int], j: int) -> int:
    """Documentation body of the first record (scanning entries `j, j+1, ...`
    to the end) whose owner is `owner` and whose attribute-name is `nm`;
    `ABSENT` if none. Front-recursive over the entry suffix start `j` so one
    unfold is available per inner-loop step."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    Requires(0 <= j and j <= len(ens))
    if j == len(ens):
        return ABSENT
    if ens[j] == owner and enm[j] == nm:
        return edoc[j]
    return lookup_owner_doc(owner, nm, ens, enm, edoc, j + 1)


@Pure
def resolve_from(nm: int, mro: PSeq[int], ens: PSeq[int], enm: PSeq[int],
                 edoc: PSeq[int], c: int) -> int:
    """Documentation body resolving attribute name `nm`, considering MRO
    classes `mro[c], mro[c+1], ...` to the end: take the first MRO class (from
    `c`) that owns a record named `nm`, and within it that record's doc body;
    `ABSENT` if no such MRO class owns one. Front-recursive over the MRO start
    `c`, so the earliest MRO class wins."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    Requires(0 <= c and c <= len(mro))
    if c == len(mro):
        return ABSENT
    if lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0) != ABSENT:
        return lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0)
    return resolve_from(nm, mro, ens, enm, edoc, c + 1)


@Pure
def resolved_doc(nm: int, mro: PSeq[int], ens: PSeq[int], enm: PSeq[int],
                 edoc: PSeq[int]) -> int:
    """The documentation body resolving attribute name `nm` under the full MRO,
    or `ABSENT` if `nm` is documented on no MRO class."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    return resolve_from(nm, mro, ens, enm, edoc, 0)
# pure-end


def resolve_attribute_doc(nm: int, mro: List[int], ens: List[int],
                          enm: List[int], edoc: List[int]) -> int:
    """Resolve the documentation body of attribute name `nm` under the MRO-aware
    lookup. `mro` is the method-resolution order as owner codes (the class first,
    then its bases). `ens`/`enm`/`edoc` are the parallel record table: record `j`
    has owner `ens[j]`, attribute-name `enm[j]`, documentation body `edoc[j]`.
    Returns the resolving documentation body -- the body recorded under the
    earliest MRO class that owns a matching record (and the first such record for
    that class) -- or `ABSENT` if no MRO class owns a record naming `nm`.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(mro), 1 / 2))
    Requires(Acc(list_pred(ens), 1 / 2))
    Requires(Acc(list_pred(enm), 1 / 2))
    Requires(Acc(list_pred(edoc), 1 / 2))
    Requires(len(ens) == len(enm))
    Requires(len(enm) == len(edoc))
    # TERMINATION: resolving one name against the finite MRO and the finite
    # record table is a bounded scan and must actually ANSWER. Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. `while True: pass` or bare
    # self-recursion before the return) satisfies every Ensures vacuously;
    # the real collection loop always returns its members.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mro), 1 / 2))
    Ensures(Acc(list_pred(ens), 1 / 2))
    Ensures(Acc(list_pred(enm), 1 / 2))
    Ensures(Acc(list_pred(edoc), 1 / 2))
    Ensures(len(ToSeq(ens)) == len(ToSeq(enm)))
    Ensures(len(ToSeq(enm)) == len(ToSeq(edoc)))
    # The resolved documentation body is exactly the earliest-MRO-owner,
    # first-record resolution of the name. This pins both the membership
    # (base-class owners count) and the override precedence.
    Ensures(Result() == resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                     ToSeq(edoc)))
    # post-conditions-end
    # impl-start
    c = 0
    while c < len(mro):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= c and c <= len(mro))
        # every MRO class before `c` owned no record for `nm`
        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), 0) ==
                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), c))
        # The loop consumes the termination obligation: len(mro) - c is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(len(mro) - c))
        # invariants-end
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                ToSeq(edoc), c) == found)
            return found
        c = c + 1
    return ABSENT
    # impl-end
