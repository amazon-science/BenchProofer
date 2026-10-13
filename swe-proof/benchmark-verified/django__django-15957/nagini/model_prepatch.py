"""Twin-artifact model for django__django-15957.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A prefetch builds a related-object query by ANDing a membership predicate
  (the related objects belonging to the given parent instances) onto a query.
  The query may already have a slice taken on it (a start offset and an
  optional stop limit). The desired observable behaviour is:

    (1) The membership predicate is ALWAYS applied to produce the result, for
        every prefetch query — whether or not a slice was taken.

    (2) Taking a slice on a query and then applying a further predicate is not
        directly well-defined; doing it on a still-sliced query is an error.
        So a prefetch query that carries a slice must, by the time the
        membership predicate is applied, no longer be sliced: the result is a
        query that is NOT sliced.

    (3) The slice the caller asked for must not be lost when it is removed: the
        result still restricts each parent's related objects to exactly the
        same positions the original slice selected (the start offset, and the
        stop limit when one was given). Concretely the result records that
        restriction iff the query was originally sliced, and an upper
        restriction iff the original slice also had a finite stop limit.

The query is modelled as a minimal class carrying only the touched state: the
slice's start/stop marks, the predicates that have been applied to it, and two
opaque carrier fields (lower_bound/upper_bound) in which the result records the
position restriction described in (3). Field names and parent instances are
opaque to this behaviour and are carried as scalars.

The single step that is NOT a plain structural update is applying the
membership predicate. It is modelled as the callee `apply_membership`, which is
well-defined only on a query carrying no slice (its precondition); on success it
grants an unforgeable token (`membership_token`) recording that the predicate
was applied to a non-sliced query. The result of `bounded_prefetch` must carry
that token, so behaviour (1) cannot be satisfied by merely flagging the query —
it must actually route through a successful application on an unsliced query.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class PrefetchQuery:
    def __init__(self, offset_mark: int, limit_mark: Optional[int]) -> None:
        Requires(offset_mark >= 0)
        Requires(limit_mark is None or limit_mark >= 0)
        Ensures(Acc(self.offset_mark) and Acc(self.limit_mark))  # type: ignore
        Ensures(Acc(self.membership_applied))  # type: ignore
        Ensures(Acc(self.lower_bound) and Acc(self.upper_bound))  # type: ignore
        Ensures(self.offset_mark == offset_mark and self.limit_mark is limit_mark)  # type: ignore
        Ensures(self.membership_applied == False)  # type: ignore
        Ensures(self.lower_bound is None and self.upper_bound is None)  # type: ignore
        self.offset_mark = offset_mark          # slice start offset
        self.limit_mark = limit_mark            # slice stop limit (None = unbounded)
        self.membership_applied = False         # has the membership predicate been ANDed on?
        self.lower_bound = None                 # type: Optional[int]  # opaque lower position restriction
        self.upper_bound = None                 # type: Optional[int]  # opaque upper position restriction


# axioms-start
# Unforgeable capability token marking a query the membership predicate was
# applied to by a SUCCESSFUL (non-sliced) application step. It is abstract (no
# body), so nothing can fabricate it by hand; it can be obtained ONLY from the
# Ensures of apply_membership below, which grants it only when the query carried
# no slice at application time. The result of bounded_prefetch must carry this
# token, so a result the application step never produced on an unsliced query
# cannot satisfy the contract — applying the predicate to a still-sliced query
# is exactly the error the issue reports. Provenance + executable soundness
# check: mapping.md / axiom_check.py (G-AX).
@ContractOnly
@Predicate
def membership_token(query: PrefetchQuery) -> bool:
    pass


@ContractOnly
def apply_membership(query: PrefetchQuery) -> None:
    """Apply the membership predicate to the query. Applying a predicate is only
    well-defined while the query has NO slice taken on it: a query with a slice
    taken cannot accept a further predicate (the precondition models exactly
    that constraint). On a successful application it records that the predicate
    was applied AND grants the membership token on the query — the token nothing
    else can fabricate. Provenance + executable soundness check: mapping.md /
    axiom_check.py."""
    Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    Requires(Acc(query.membership_applied))
    Requires(not is_sliced(query))
    Requires(MustTerminate(2))
    Ensures(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    Ensures(Acc(query.membership_applied))
    Ensures(query.membership_applied == True)
    Ensures(membership_token(query))
# axioms-end


# pure-start
@Pure
def is_sliced(query: PrefetchQuery) -> bool:
    """The query has a slice taken on it: either a non-zero start offset or a
    finite stop limit is present."""
    Requires(Acc(query.offset_mark, 1 / 4) and Acc(query.limit_mark, 1 / 4))
    return query.offset_mark != 0 or query.limit_mark is not None
# pure-end


def bounded_prefetch(query: PrefetchQuery, member_code: int,
                     instance_count: int) -> PrefetchQuery:
    # pre-conditions-start
    Requires(Acc(query.offset_mark) and Acc(query.limit_mark))
    Requires(Acc(query.membership_applied))
    Requires(Acc(query.lower_bound) and Acc(query.upper_bound))
    Requires(query.offset_mark >= 0)
    Requires(query.limit_mark is None or query.limit_mark >= 0)
    # A freshly assembled prefetch query has no predicate applied yet.
    Requires(query.membership_applied == False)
    Requires(query.lower_bound is None and query.upper_bound is None)
    Requires(instance_count >= 0)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(query.offset_mark) and Acc(query.limit_mark))
    Ensures(Acc(query.membership_applied))
    Ensures(Acc(query.lower_bound) and Acc(query.upper_bound))
    Ensures(Result() is query)
    # (1) the membership predicate is always applied — and not merely flagged:
    #   the result must carry the unforgeable token that the application step
    #   grants ONLY when the query carried no slice at application time. Because
    #   the token cannot be fabricated, the result must have been produced by a
    #   successful application on an unsliced query (so a still-sliced query was
    #   first un-sliced), which is exactly the desired behaviour.
    Ensures(membership_token(query))
    Ensures(query.membership_applied == True)
    # (3) the position restriction preserves exactly the original slice.
    #   a lower restriction is recorded iff the query was originally sliced,
    #   and it carries the original start offset.
    Ensures(Old(is_sliced(query)) == (query.lower_bound is not None))
    Ensures(Implies(query.lower_bound is not None,
                    query.lower_bound == Old(query.offset_mark)))
    #   an upper restriction is recorded iff the query was originally sliced AND
    #   had a finite stop limit, and it carries that limit.
    Ensures((Old(is_sliced(query)) and Old(query.limit_mark) is not None)
            == (query.upper_bound is not None))
    Ensures(Implies(query.upper_bound is not None,
                    query.upper_bound == Old(query.limit_mark)))
    # (2) the resulting query is no longer sliced (so the predicate is applicable).
    Ensures(not is_sliced(query))
    Ensures(query.offset_mark == 0 and query.limit_mark is None)
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: the membership predicate is applied directly to the
    # query as given, without recording any position restriction and without
    # removing the slice. When the query has a slice taken on it this violates
    # apply_membership's precondition (a sliced query cannot accept a
    # predicate) and leaves the restrictions unset and the query still sliced —
    # so the spec's restriction-presence and not-sliced postconditions fail.
    apply_membership(query)
    return query
    # impl-end
