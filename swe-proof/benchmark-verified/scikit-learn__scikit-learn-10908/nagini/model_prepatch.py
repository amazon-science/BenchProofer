"""Twin-artifact model for scikit-learn__scikit-learn-10908.

Behaviour under specification (a self-standing behavioural contract):

  A text-vectoriser object exposes a query that returns the ordered list of
  feature names. The object can reach a usable state in two ways:

    * it has already been fitted from data (its learned name-to-index mapping is
      materialised on the object); or
    * a name list was supplied to the object at construction time. In this case
      the materialised mapping has not yet been built, but a usable supplied
      list is enough to build it on demand.

  A supplied name list is usable as a source for the mapping exactly when it is
  non-empty and lists no name twice; the materialise step rejects any other
  list, since it could not assign every name its own index.

  The desired behaviour of the feature-name query:

    * If the materialised mapping is not yet present but a name list WAS supplied
      at construction, the query first materialises the mapping from that
      supplied list — exactly as a transform query already does — recording that
      the object's vocabulary was supplied at construction, and then returns the
      feature names. If that supplied list is not usable, the materialise step's
      own rejection surfaces and the object is left untouched.
    * If the materialised mapping is already present, the query returns its
      feature names directly, leaving that mapping as it found it.
    * The query reports an unfitted-object failure ONLY when the object is
      genuinely unusable: no materialised mapping AND no construction-supplied
      list. A construction-supplied list must never trigger that failure.

  The query is an observation, not a reconfiguration: the only mapping it ever
  writes is one it materialises on an object that had none. It never alters a
  mapping that is already present, and it never alters the construction-supplied
  list, nor whether a list was supplied at construction.

  The returned feature names are the mapping's terms in ascending index order.
  When the mapping is materialised from a construction-supplied list, term i of
  that list is assigned index i, so the returned names equal the supplied list
  in its original order; and the object then records that its vocabulary was
  supplied at construction.

  A mapping has TWO observable halves, and the query answers for both: WHICH
  names it holds (reported in ascending index order) and WHICH index each of
  those names carries. The second half is what makes the first meaningful — a
  name's index is the column it addresses everywhere else — and a materialised
  mapping numbers its names BY THEIR PLACE in that reported order: the name
  reported at place k is the one the mapping sends to index k. So:

    * a mapping materialised from a construction-supplied list numbers term i of
      that list i (place = index, as above); and
    * a mapping that was already present is still numbered by place when the
      query is done. The query may not RENUMBER the mapping it reports on, not
      even while leaving the reported names themselves exactly where they were:
      re-indexing the very names it is reporting would move every one of them to
      a place other than the one it is reported at.

Feature names (opaque term identifiers) are modelled as `List[int]`; a
materialised mapping is carried as the parallel pair `names` (its terms in
ascending index order) and `idx` (the index each of those terms carries, in that
same order), so a renumbering is a state change the model can express and the
contract can forbid. A materialised mapping is a name-to-index correspondence, so
its index-ordered names are themselves usable in the above sense — non-empty and
repetition-free — and it is numbered by place; only such states denote a real
object. The materialise-from-supplied-list primitive is the unchanged routine a
transform query already uses; its effect (build the mapping, record the supplied-
at-construction vocabulary) and its usable-list domain are modelled deeply as a
contracted helper and validated == the real routine out-of-band (axiom_check.py /
G-AX). Both failures are user-defined exception classes (a builtin exception in
an `Exsures` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NotFittedError(Exception):
    """The unfitted-object failure surfaced when the object is genuinely
    unusable (no materialised mapping and no construction-supplied list).
    User-defined stand-in (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass


class UnusableTermsError(Exception):
    """The rejection the materialise step reports for a construction-supplied
    name list it cannot turn into a mapping (empty, or a name listed twice).
    User-defined stand-in, as above (mapping.md §2)."""
    pass


class Vectoriser:
    """The vectoriser object, carrying only the fields the feature-name query
    observes. `fitted` records whether the materialised name-to-index mapping is
    present; `has_param` records whether a name list was supplied at
    construction; `param` is that supplied list (its terms in order, meaningful
    only when `has_param`); `supplied` records whether the object reports that
    its vocabulary was supplied at construction; `names` is the materialised
    mapping viewed as its terms in ascending index order, and `idx` is the index
    each of those terms carries, listed in that same order — the two together are
    the mapping, so `idx` is what makes a renumbering of it observable."""

    def __init__(self, fitted: bool, has_param: bool, supplied: bool,
                 param: List[int], names: List[int], idx: List[int]) -> None:
        Requires(Acc(list_pred(param)) and Acc(list_pred(names)))
        Requires(Acc(list_pred(idx)))
        # Constructing a vectoriser is a bounded step (six field writes); its
        # level (1) sits strictly below every obligated method above it.
        Requires(MustTerminate(1))
        Ensures(Acc(self.fitted) and self.fitted == fitted)  # type: ignore
        Ensures(Acc(self.has_param) and self.has_param == has_param)  # type: ignore
        Ensures(Acc(self.supplied) and self.supplied == supplied)  # type: ignore
        Ensures(Acc(self.param) and self.param is param)  # type: ignore
        Ensures(Acc(self.names) and self.names is names)  # type: ignore
        Ensures(Acc(self.idx) and self.idx is idx)  # type: ignore
        Ensures(Acc(list_pred(self.param)) and Acc(list_pred(self.names)))  # type: ignore
        Ensures(Acc(list_pred(self.idx)))  # type: ignore
        self.fitted = fitted
        self.has_param = has_param
        self.supplied = supplied
        self.param = param
        self.names = names
        self.idx = idx


# axioms-start
# (No consumed @ContractOnly axiom. The one unchanged callee the query
#  invokes — the materialise-from-supplied-list routine — is modelled DEEPLY as
#  the contracted helper `materialise_from_param` below, an A-reference validated
#  == the real routine by axiom_check.py / G-AX, not consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def usable_terms(xs: List[int]) -> bool:
    """A term list can serve as a name-to-index mapping exactly when it is
    non-empty and no term is listed twice — only then does every term get its
    own index. Both the construction-supplied list (which an arbitrary caller
    may hand over in any shape) and the materialised mapping's index-ordered
    names satisfy this of a usable object."""
    Requires(Acc(list_pred(xs), 1 / 4))
    return len(xs) > 0 and Forall(int, lambda i: (Forall(int, lambda j: (
        Implies(0 <= i and i < j and j < len(xs), xs[i] != xs[j]),
        [[xs[i], xs[j]]])), []))


@Pure
def places(n: int) -> PSeq[int]:
    """The first n places, in order: 0, 1, ..., n-1. (Recursion on n, which
    strictly decreases towards the n <= 0 base case, so this is a total
    function; it is spec-only vocabulary for saying WHICH index a name at a
    given place carries.)"""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n <= 0:
        return PSeq(0).take(0)
    return places(n - 1) + PSeq(n - 1)


@Pure
def numbered_by_place(idx: List[int], names: List[int]) -> bool:
    """A materialised mapping is numbered BY PLACE: every one of its names
    carries an index (the two lists run in parallel), and the name at place k
    carries index k — i.e. the indices, read in the order the names are
    reported, are exactly 0, 1, ..., len(names)-1. This is the half of the
    mapping the reported name order alone cannot show — it is what distinguishes
    the mapping that sends the k-th reported name to k from any other mapping
    holding those same names in that same ascending order."""
    Requires(Acc(list_pred(idx), 1 / 4) and Acc(list_pred(names), 1 / 4))
    return len(idx) == len(names) and ToSeq(idx) == places(len(names))
# pure-end


def materialise_from_param(self: Vectoriser) -> None:
    """The unchanged materialise-from-supplied-list primitive (the routine a
    transform query already uses). Precondition: a USABLE name list was supplied
    at construction. Effect: build the materialised mapping from that list —
    term i of the list gets index i, so the index-ordered names equal the
    supplied list and the mapping it builds is numbered by place — and record
    that the object's vocabulary was supplied at construction. Its effect and its
    usable-list domain are modelled deeply here and validated == the real routine
    by axiom_check.py (G-AX)."""
    # pre-conditions-start
    Requires(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Requires(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Requires(Acc(list_pred(self.param), 1 / 2))
    Requires(self.has_param)
    # The routine builds a mapping, so it is only defined on a list that CAN be
    # one: an empty list or a repeated term is rejected instead (the caller
    # screens for this before invoking the step).
    Requires(usable_terms(self.param))
    # The materialise step must COMPLETE: without this the postconditions below
    # are claimed only of runs that reach the return, and an implementation that
    # spins forever would satisfy them vacuously. Level 2 leaves room for the
    # list allocation it performs (level 1 leaks `list.__init__`'s obligation).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Ensures(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Ensures(Acc(list_pred(self.param), 1 / 2) and Acc(list_pred(self.names)))
    Ensures(Acc(list_pred(self.idx)))
    Ensures(self.has_param)
    # The step READS the supplied list to build the mapping; the object still
    # carries that same supplied list, unchanged, afterwards.
    Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
    # The mapping is now materialised, the object records a supplied-at-
    # construction vocabulary, and the index-ordered feature names equal the
    # supplied list in its order.
    Ensures(self.fitted)
    Ensures(self.supplied)
    Ensures(ToSeq(self.names) == ToSeq(self.param))
    # Term i of the supplied list is given index i, so the mapping this step
    # builds is numbered by place: taken with the clause above, the name at
    # place k of the supplied list is the one the new mapping sends to k.
    Ensures(numbered_by_place(self.idx, self.names))
    # post-conditions-end
    # impl-start
    new_names = []  # type: List[int]
    new_idx = []  # type: List[int]
    k = 0
    while k < len(self.param):
        # invariants-start
        Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(new_names)) and Acc(list_pred(new_idx)))
        # The supplied list is only read, so it still holds its entry value.
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # (`not isinstance(k, bool)` is a proof hint, not an obligation: the
        # counter is a plain int, which the verifier needs spelled out because
        # `bool` is a subtype of `int`.)
        Invariant(0 <= k and k <= len(self.param) and not isinstance(k, bool))
        Invariant(ToSeq(new_names) == ToSeq(self.param).take(k))
        # The two halves are built together: place t of the part built so far
        # carries index t, i.e. the indices assigned so far are the places
        # 0 .. k-1 in order.
        Invariant(len(new_idx) == k)
        Invariant(ToSeq(new_idx) == places(k))
        # At most len(self.param) - k + 1 passes remain: the supplied list is
        # held (read-only) by the invariant above so its length cannot change,
        # and k rises by exactly one per pass, so the bound strictly decreases;
        # the loop guard k < len(self.param) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.param) - k + 1))
        # invariants-end
        Assert(ToSeq(self.param).take(k + 1).drop(k)[0] == self.param[k])
        new_names.append(self.param[k])
        new_idx.append(k)
        k = k + 1
    Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
    Assert(len(new_names) == k and len(new_idx) == k)
    Assert(places(len(new_names)) == places(k))
    self.names = new_names
    self.idx = new_idx
    self.fitted = True
    self.supplied = True
    # impl-end


def get_feature_names(self: Vectoriser) -> List[int]:
    # pre-conditions-start
    Requires(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Requires(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Requires(Acc(list_pred(self.param), 1 / 2))
    Requires(Acc(list_pred(self.names)))
    Requires(Acc(list_pred(self.idx)))
    # A materialised mapping is a name-to-index correspondence, so on an already
    # fitted object its index-ordered names are themselves a usable term list
    # (non-empty, no repetition). This is the representation invariant of the
    # materialised mapping, not a restriction on the caller's supplied list:
    # `param` below is left entirely unconstrained.
    Requires(Implies(self.fitted, usable_terms(self.names)))
    # The other half of that same representation invariant: a materialised
    # mapping is numbered by place. Every way a mapping comes into being numbers
    # it that way — materialising a supplied list of n names uses places 0..n-1,
    # and so does learning one from data — so this is what an already-materialised
    # mapping IS, not a case being ducked. It is stated here because the exit
    # clause below claims the same of the mapping the query leaves behind, and
    # that claim would be unfaithful of a mapping that arrived numbered some other
    # way: this query reports a mapping, it does not repair one.
    Requires(Implies(self.fitted, numbered_by_place(self.idx, self.names)))
    # The query must COMPLETE (total correctness): without this obligation every
    # Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 3 is strictly above materialise_from_param's 2 (the callee
    # it invokes) and leaves room for the list allocation it performs.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied))
    Ensures(Acc(self.param) and Acc(self.names) and Acc(self.idx))
    Ensures(Acc(list_pred(self.param), 1 / 2))
    Ensures(Acc(list_pred(self.names)))
    Ensures(Acc(list_pred(self.idx)))
    Ensures(Acc(list_pred(Result())))
    # The object ends usable: a materialised mapping is present.
    Ensures(self.fitted)
    # The returned feature names are the object's materialised mapping in index
    # order.
    Ensures(ToSeq(Result()) == ToSeq(self.names))
    # ... and that mapping is numbered by place, so the two clauses together say
    # WHICH index every returned name carries: the name at place k of the returned
    # list is the one the mapping the object now holds sends to index k. A query
    # that reported these very names while the mapping sent them to any other
    # indices would satisfy the clause above and violate this one.
    Ensures(numbered_by_place(self.idx, self.names))
    # This query reports names; it does not reconfigure the object it is asked
    # about. Whether a name list was supplied at construction, and that supplied
    # list itself, therefore hold their entry values when the query is done. This
    # is true on every exit, the two failures included (restated there below).
    Ensures(self.has_param == Old(self.has_param))
    Ensures(ToSeq(self.param) == Old(ToSeq(self.param)))
    # When the object was NOT already fitted, a USABLE construction-supplied list
    # is what made it usable: such a list must have been supplied, it is now
    # materialised AND recorded as supplied-at-construction, and the returned
    # names equal that supplied list in order. (This is exactly the case the
    # unfitted-object failure must NOT be raised on. Requiring the supplied list
    # to have been usable is what forbids returning it when it was not: that
    # case has to exit through the rejection below instead.)
    Ensures(Implies(not Old(self.fitted),
                    Old(self.has_param) and Old(usable_terms(self.param))
                    and self.supplied
                    and ToSeq(Result()) == ToSeq(self.param)))
    # When the materialised mapping was ALREADY present, the query only reads
    # it: the mapping the object carries afterwards, and its record of whether
    # its vocabulary was supplied at construction, are the ones it came in with,
    # and the names reported are that same already-present mapping in index
    # order. Nothing about an already-usable object is re-derived, and no
    # feature name it already had can go missing or change place, and no name it
    # already had is re-indexed: BOTH halves of the mapping — its names in index
    # order and the index each of them carries — come back out as they went in.
    Ensures(Implies(Old(self.fitted),
                    ToSeq(self.names) == Old(ToSeq(self.names))
                    and ToSeq(self.idx) == Old(ToSeq(self.idx))
                    and self.supplied == Old(self.supplied)
                    and ToSeq(Result()) == Old(ToSeq(self.names))))
    # The unfitted-object failure is raised ONLY when the object is genuinely
    # unusable: not already fitted AND no construction-supplied list. (The
    # access predicates are restored so the caller may inspect the object.)
    # `has_param` (whether a list was supplied at construction) is a read-only
    # input to this query; the discriminating clauses read its pre-state
    # (`Old(self.has_param)`) so an impl cannot vacate them by overwriting it.
    # On this genuinely-unusable path the on-demand materialise step runs and,
    # finding no list to build from, records that the object's vocabulary was
    # NOT supplied at construction (`not self.supplied`) before the failure
    # surfaces — a load-bearing side effect the query must reproduce, so an impl
    # that merely fails without recording it does NOT satisfy this clause. That
    # record is also the ONLY thing this exit changes: with no list to build
    # from, no mapping is materialised (the object is still not fitted, and both
    # halves of the mapping view it came in with — its names and their indices —
    # are untouched) and the construction inputs keep their entry values.
    Exsures(NotFittedError,
            Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied)
            and Acc(self.param) and Acc(self.names) and Acc(self.idx)
            and Acc(list_pred(self.param), 1 / 2)
            and Acc(list_pred(self.names))
            and Acc(list_pred(self.idx))
            and not Old(self.fitted) and not Old(self.has_param)
            and not self.supplied
            and not self.fitted
            and ToSeq(self.names) == Old(ToSeq(self.names))
            and ToSeq(self.idx) == Old(ToSeq(self.idx))
            and self.has_param == Old(self.has_param)
            and ToSeq(self.param) == Old(ToSeq(self.param)))
    # The materialise step's own rejection is reported ONLY when there was a
    # mapping to build and it could not be built: not already fitted, a list WAS
    # supplied at construction, and that list was not usable (empty, or a term
    # listed twice). On this path the step builds nothing and records nothing, so
    # the object is left exactly as it was — no mapping is materialised and the
    # supplied-at-construction flag keeps its entry value, as do both halves of
    # the mapping view and the construction-supplied list.
    Exsures(UnusableTermsError,
            Acc(self.fitted) and Acc(self.has_param) and Acc(self.supplied)
            and Acc(self.param) and Acc(self.names) and Acc(self.idx)
            and Acc(list_pred(self.param), 1 / 2)
            and Acc(list_pred(self.names))
            and Acc(list_pred(self.idx))
            and not Old(self.fitted) and Old(self.has_param)
            and not Old(usable_terms(self.param))
            and not self.fitted and self.supplied == Old(self.supplied)
            and ToSeq(self.names) == Old(ToSeq(self.names))
            and ToSeq(self.idx) == Old(ToSeq(self.idx))
            and self.has_param == Old(self.has_param)
            and ToSeq(self.param) == Old(ToSeq(self.param)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the query goes straight to the unusable check. It does
    # NOT first materialise the mapping from a construction-supplied list, so it
    # reports the unfitted-object failure whenever the materialised mapping is
    # absent — even when a name list WAS supplied at construction.
    if not self.fitted:
        raise NotFittedError()
    result = []  # type: List[int]
    j = 0
    while j < len(self.names):
        # invariants-start
        Invariant(Acc(self.names) and Acc(list_pred(self.names)))
        Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
        Invariant(Acc(self.param) and Acc(self.has_param) and Acc(self.supplied))
        Invariant(Acc(self.fitted) and self.fitted)
        Invariant(Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # The construction inputs are only read, so they still hold their entry
        # values on every pass.
        Invariant(self.has_param == Old(self.has_param))
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # The mapping being reported is numbered by place throughout: the copy
        # below reads it, it does not re-index it.
        Invariant(numbered_by_place(self.idx, self.names))
        # Whenever the object was not already fitted, a usable construction-
        # supplied list is what materialised it: the object records a supplied-
        # at-construction vocabulary, and the materialised names equal that list.
        # These facts are stable across the loop below.
        Invariant(Implies(not Old(self.fitted),
                          Old(self.has_param) and Old(usable_terms(self.param))
                          and self.supplied
                          and ToSeq(self.names) == ToSeq(self.param)))
        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
        # re-indexed the mapping, so both of its halves and the supplied-at-
        # construction record are still the ones the object came in with.
        Invariant(Implies(Old(self.fitted),
                          ToSeq(self.names) == Old(ToSeq(self.names))
                          and ToSeq(self.idx) == Old(ToSeq(self.idx))
                          and self.supplied == Old(self.supplied)))
        Invariant(0 <= j and j <= len(self.names))
        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
        # At most len(self.names) - j + 1 passes remain: the materialised mapping
        # is held by the invariant above so its length cannot change, and j rises
        # by exactly one per pass, so the bound strictly decreases; the loop guard
        # j < len(self.names) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.names) - j + 1))
        # invariants-end
        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
        result.append(self.names[j])
        j = j + 1
    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
    return result
    # impl-end
