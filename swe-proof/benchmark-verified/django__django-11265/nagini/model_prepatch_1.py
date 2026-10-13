"""Twin-artifact model for django__django-11265.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) When an exclusion over an N-to-many relation is rewritten into a nested
      subquery, that subquery must inherit the outer query's registry of
      declared relation aliases. The alias the exclusion refers to is declared
      on the outer query; for the subquery's own lookup resolution to find it,
      the inner registry must contain exactly the same declared aliases as the
      outer one. In particular every alias declared on the outer query — the
      referenced one included — is resolvable inside the subquery.

  (2) The set of filter conditions in effect on the subquery is determined by
      its leading join. The leading join's own filter condition is retained
      exactly when that join is left-outer OR carries a relation-specific
      filter; when the leading join is an inner join without a relation-specific
      filter, its condition is not part of the result. Downstream conditions are
      always in effect.

Relation-alias registries and join filter-condition sets are modelled as
``List[int]`` of opaque tokens (Nagini bans ``str``/dict indexing); the
specification is carried over ``PSeq[int]`` via ``ToSeq``. The two join kinds
are abstract ``int`` tokens. The two behaviours are two separate contracted
functions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms: both modelled behaviours are pure data-flow /
#  control-flow over abstract relation-alias tokens, join-kind tokens, and
#  filter-condition tokens, spelled out in full. There is no unchanged opaque
#  callee whose contract the proof consumes, and no deep model standing in for
#  an external callee. Hence no axiom_check.py.)
# axioms-end


# pure-start
@Pure
def LOUTER() -> int:
    """Abstract token for the left-outer join kind."""
    return 1


@Pure
def INNER() -> int:
    """Abstract token for the inner join kind."""
    return 0


@Pure
def may_trim_leading_join(join_type: int, is_filtered_relation: bool) -> bool:
    """The leading join of the subquery may be collapsed only when it is an
    inner join (not left-outer) AND it does not carry a relation-specific
    filter. A left-outer join, or any join carrying a filter, must be kept."""
    return join_type != LOUTER() and not is_filtered_relation
# pure-end


def propagate_relation_registry(outer_relations: List[int],
                                referenced_alias: int) -> List[int]:
    # pre-conditions-start
    # ``outer_relations`` is the outer query's registry of declared relation
    # aliases (read-only here: fractional permission, directive 5).
    Requires(Acc(list_pred(outer_relations), 1 / 2))
    # The exclusion refers to an alias that is declared on the outer query.
    Requires(referenced_alias in ToSeq(outer_relations))
    Requires(MustTerminate(len(outer_relations) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The read-only input is returned at the same fractional permission.
    Ensures(Acc(list_pred(outer_relations), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The subquery's registry is exactly the outer query's registry: same
    # declared aliases, in the same order. Pinned by value, so an impl that
    # leaves the inner registry empty or drops/adds any alias is rejected.
    Ensures(ToSeq(Result()) == ToSeq(outer_relations))
    # Consequently the referenced alias is resolvable inside the subquery: it is
    # a member of the inherited registry. An empty inner registry fails here.
    Ensures(referenced_alias in ToSeq(Result()))
    # Every alias declared on the outer query is resolvable inside the subquery.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(outer_relations),
                                           outer_relations[k] in ToSeq(Result())))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (site 1): the freshly-created inner query keeps its empty
    # registry (Query.__init__ sets ``_filtered_relations = {}``); the outer
    # registry is NOT propagated. The referenced alias is therefore absent from
    # the inner registry, so the postcondition pins this as unresolvable.
    result = []  # type: List[int]
    return result
    # impl-end


def subquery_retained_filters(join_type: int, is_filtered_relation: bool,
                              leading_filter: int,
                              other_filters: List[int]) -> List[int]:
    # pre-conditions-start
    # ``leading_filter`` is the filter-condition token of the subquery's leading
    # join; ``other_filters`` are the downstream conditions (always retained,
    # read-only here: fractional permission, directive 5).
    Requires(Acc(list_pred(other_filters), 1 / 2))
    Requires(MustTerminate(len(other_filters) + 6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(other_filters), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The retained-conditions set is pinned by value on both branches. When the
    # leading join's condition is not retained, the result is exactly the
    # downstream conditions; otherwise the leading condition precedes them. The
    # downstream conditions are always in effect.
    Ensures(Implies(may_trim_leading_join(join_type, is_filtered_relation),
                    ToSeq(Result()) == ToSeq(other_filters)))
    Ensures(Implies(not may_trim_leading_join(join_type, is_filtered_relation),
                    ToSeq(Result()) == PSeq(leading_filter) + ToSeq(other_filters)))
    # When the leading join carries a relation-specific filter, its condition is
    # part of the retained set.
    Ensures(Implies(is_filtered_relation,
                    ToSeq(Result()) == PSeq(leading_filter) + ToSeq(other_filters)))
    # When the leading join is left-outer, its condition is part of the retained
    # set.
    Ensures(Implies(join_type == LOUTER(),
                    ToSeq(Result()) == PSeq(leading_filter) + ToSeq(other_filters)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if not may_trim_leading_join(join_type, is_filtered_relation):
        result = result + [leading_filter]
    prefix = ToSeq(result)
    i = 0
    while i < len(other_filters):
        # invariants-start
        Invariant(Acc(list_pred(other_filters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(other_filters))
        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))
        Invariant(MustTerminate(len(other_filters) - i + 1))
        # invariants-end
        result = result + [other_filters[i]]
        i = i + 1
    Assert(ToSeq(other_filters).take(len(other_filters)) == ToSeq(other_filters))
    return result
    # impl-end
