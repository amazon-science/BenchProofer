"""Twin-artifact model for django__django-11734.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ``exclude(...)`` (equivalently a negated ``~Q(...)``) over an N-to-many
  relation is realised by building a fresh, nested inner subquery and matching
  the outer rows against it. The right-hand side of the original condition may
  be one of three things:

    * a plain literal value (no query reference at all),
    * a local field reference, which means "the field of the row in the query
      that the condition was written against", or
    * an ``OuterRef``, which means "a field of a query one level further out
      than the query the condition was written against".

  When such a right-hand side is carried into the freshly generated inner
  subquery, the query level it ultimately refers to MUST be preserved. The
  inner subquery sits one nesting level deeper than the query the condition was
  written against, so any reference moved into it has to be re-anchored by
  exactly one extra outward hop to keep pointing at the same query as before:

    * a local field reference (level 0, the original query) becomes an
      ``OuterRef`` so that, resolved from inside the inner subquery, it again
      denotes the original query;
    * an ``OuterRef`` (level -1, one out from the original query) must be
      wrapped in a further ``OuterRef`` so that, resolved from inside the inner
      subquery, it still denotes that same outer-of-the-original query rather
      than collapsing onto the original query;
    * a plain value carries no reference and is left untouched.

  Separately, when the value supplied to a relational comparison is prepared,
  only a genuine concrete value is normalised through the relation's value
  coercion. Anything that is itself a query expression (i.e. carries the
  ability to be resolved against a query, such as an ``OuterRef`` or a field
  reference) must be passed through untouched, because it has no concrete value
  to coerce and will be resolved later against the appropriate query level.

The two decisions are pure integer/boolean logic over a small tagged domain
(no library callee is consumed): a reference's "kind" and its effective
resolution level are modelled as ints, so no axiom is required.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No library callee is axiomatized: both modelled behaviours are pure,
# fully expressible integer/boolean decisions.)
# axioms-end


# pure-start
# Right-hand-side kinds (a small tagged domain).
#   KIND_VALUE   -- a plain concrete value, no query reference.
#   KIND_LOCAL   -- a local field reference (resolves against the query it is
#                   added to).
#   KIND_OUTER   -- an OuterRef (resolves one level further out than the query
#                   it is added to).
@Pure
def kind_value() -> int:
    return 0


@Pure
def kind_local() -> int:
    return 1


@Pure
def kind_outer() -> int:
    return 2


@Pure
def is_query_expression(kind: int) -> bool:
    """A right-hand side is a query expression (can be resolved against a
    query) exactly when it is a local reference or an OuterRef; a plain value
    is not."""
    return kind == kind_local() or kind == kind_outer()


@Pure
def target_level(kind: int) -> int:
    """The query level a right-hand side ultimately denotes, measured relative
    to the query the original condition was written against (that query is
    level 0). A local reference denotes that query itself (0); an OuterRef
    denotes one level further out (-1). A plain value denotes no level; we use
    the sentinel level 0 for it since it is never re-anchored."""
    if kind == kind_outer():
        return -1
    return 0


@Pure
def resolved_level_in_inner(kind: int) -> int:
    """If a right-hand side of the given kind were carried UNCHANGED into the
    freshly generated inner subquery and then resolved, this is the query level
    it would denote, again relative to the original query (level 0).

    The inner subquery is one nesting level deeper (level +1). A local
    reference resolved there denotes the inner subquery itself (level +1). An
    OuterRef resolved there denotes one level out from the inner subquery,
    i.e. the original query (level 0). A plain value denotes no level (0)."""
    if kind == kind_local():
        return 1
    if kind == kind_outer():
        return 0
    return 0
# pure-end


def rebind_into_inner_subquery(rhs_kind: int) -> int:
    """Re-anchoring applied to the original condition's right-hand side when it
    is carried into the freshly generated inner subquery. Returns the number of
    additional outward (``OuterRef``) wrapping hops to apply.

    Behaviour required: after the re-anchoring, resolving the right-hand side
    from inside the inner subquery must denote the SAME query level it denoted
    before (``target_level``)."""
    # pre-conditions-start
    Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
             or rhs_kind == kind_outer())
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() >= 0)
    # A plain value carries no reference: it is left untouched (no hops).
    Ensures(Implies(rhs_kind == kind_value(), Result() == 0))
    # A query-expression right-hand side is re-anchored so that, resolved from
    # inside the inner subquery, it denotes the same level as before.
    # Each added outward hop shifts the denoted level one step further out (-1).
    Ensures(Implies(is_query_expression(rhs_kind),
                    resolved_level_in_inner(rhs_kind) - Result() == target_level(rhs_kind)))
    # post-conditions-end
    # impl-start
    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        # level +1 in inner must become level 0 -> one outward hop.
        return 1
    # OuterRef carried into the inner subquery unchanged: no extra outward hop.
    return 0
    # impl-end


def normalize_only_concrete_value(rhs_kind: int) -> bool:
    """Decision for preparing the value of a relational comparison: returns
    whether the right-hand side is normalised through the relation's value
    coercion. Only a genuine concrete value is normalised; any query expression
    is passed through untouched."""
    # pre-conditions-start
    Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
             or rhs_kind == kind_outer())
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # Normalise iff the right-hand side is NOT a query expression.
    Ensures(Result() == (not is_query_expression(rhs_kind)))
    # Concretely: a plain value is normalised; a local reference and an
    # OuterRef are both passed through.
    Ensures(Result() == (rhs_kind == kind_value()))
    # post-conditions-end
    # impl-start
    return not is_query_expression(rhs_kind)
    # impl-end
