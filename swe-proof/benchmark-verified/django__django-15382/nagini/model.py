"""Twin-artifact model for django__django-15382.

Behaviour under specification (an abstract behavioural contract over the result,
NOT an edit or a diagnosis):

  A negatable existence predicate over an inner sub-selection is rendered to a
  fragment of result text. Rendering the inner sub-selection is delegated to a
  shared (unchanged) sub-selection renderer, which has two outcomes: for a
  SATISFIABLE inner selection it yields a non-empty inner fragment; for an
  UNSATISFIABLE one it signals the "matches-nothing" condition.

  The predicate also carries a negation flag. The result of rendering the
  predicate, by case, is:

    * inner selection satisfiable, not negated  -> the inner fragment;
    * inner selection satisfiable, negated      -> the inner fragment with the
                                                    negation marker prepended;
    * inner selection unsatisfiable, negated     -> a result that, in the
                                                    surrounding condition, holds
                                                    for every row (the negation
                                                    of "exists no row of an empty
                                                    selection");
    * inner selection unsatisfiable, not negated -> the matches-nothing condition
                                                    (an existence test over an
                                                    empty selection never holds).

  The behaviour the surrounding condition observes is whether the predicate
  reduces to "matches every row" or to the matches-nothing condition, and (on the
  satisfiable cases) whether the rendered inner fragment carries the negation
  marker. On the satisfiable cases the result is exactly the inner fragment as
  produced by the shared renderer, with the negation marker prepended iff the
  predicate is negated.

Result text is modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
shared sub-selection renderer is an axiomatized callee that either returns a
non-empty fragment or signals the matches-nothing condition according to whether
the inner selection is satisfiable; its satisfiable-case content is named by a
``@Pure`` companion so the result content can be pinned to what the renderer
actually produces.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class EmptyResultSet(Exception):
    """The "matches-nothing" signal. User-defined stand-in (a builtin exception
    in an ``Exsures`` crashes the Nagini translator; mapping.md §2). It is the
    signal the shared sub-selection renderer raises for an unsatisfiable inner
    selection, and the signal the predicate renderer propagates on the
    non-negated unsatisfiable case.
    """
    pass


# axioms-start
@Pure
@ContractOnly
def inner_fragment(satisfiable: int) -> PSeq[int]:
    """The CONTENT of the fragment the shared sub-selection renderer produces for
    a satisfiable inner selection (the @Pure companion of ``render_inner``).
    Naming the content as a pure function of the input lets the predicate
    renderer's postcondition pin the satisfiable result to what the renderer
    actually produces (directive 8: ground the result in the modeled renderer's
    output, never an echoable constant). Weakest properties the proof needs:
    non-empty, and it does not itself begin with the negation marker (so the
    marker is observable only when the predicate renderer prepends it)."""
    Requires(satisfiable == 1)
    Ensures(len(Result()) > 0)
    Ensures(Result().take(len(not_prefix())) != not_prefix())


@ContractOnly
def render_inner(satisfiable: int) -> List[int]:
    """The shared, UNCHANGED sub-selection renderer (the predicate's super-class
    rendering of its inner selection). Weakest contract the proof needs: it
    signals the matches-nothing condition exactly when the inner selection is
    unsatisfiable (``satisfiable == 0``); otherwise it returns, with full
    ownership, the fragment whose content is ``inner_fragment(satisfiable)``. It
    is the callee the predicate renderer invokes and does NOT change. Provenance +
    executable soundness: mapping.md / axiom_check.py (A-consumed)."""
    Requires(satisfiable == 0 or satisfiable == 1)
    Requires(MustTerminate(2))
    Ensures(satisfiable == 1)
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == inner_fragment(satisfiable))
    Exsures(EmptyResultSet, satisfiable == 0)
# axioms-end


# pure-start
@Pure
def not_prefix() -> PSeq[int]:
    # 'NOT ' — the negation marker prepended to a rendered predicate fragment.
    return PSeq(78, 79, 84, 32)
# pure-end


def render_exists(satisfiable: int, negated: int) -> List[int]:
    # pre-conditions-start
    Requires(satisfiable == 0 or satisfiable == 1)
    Requires(negated == 0 or negated == 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The matches-nothing signal is observable ONLY on the non-negated
    # unsatisfiable case; every other case returns normally. In particular the
    # negated unsatisfiable case returns normally rather than propagating the
    # signal, and its result is the EMPTY fragment: an empty fragment contributes
    # no restriction, so the surrounding condition holds for every row (the
    # negation of "exists no row of an empty selection"). Pinning the empty
    # fragment is what makes that row-set observable behaviour discriminating —
    # a non-empty fragment on this case would impose a spurious restriction and
    # change the observed rows.
    Ensures(not (satisfiable == 0 and negated == 0))
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(satisfiable == 0 and negated == 1, len(Result()) == 0))
    # Satisfiable cases: the result is exactly the inner fragment the shared
    # renderer produced, with the negation marker prepended iff negated. Pinned to
    # the renderer's actual output content (directive 8: grounded, not echoable):
    Ensures(Implies(satisfiable == 1 and negated == 0,
                    ToSeq(Result()) == inner_fragment(satisfiable)))
    Ensures(Implies(satisfiable == 1 and negated == 1,
                    ToSeq(Result()) == not_prefix() + inner_fragment(satisfiable)))
    # Non-negated unsatisfiable: the matches-nothing signal is propagated.
    Exsures(EmptyResultSet, satisfiable == 0 and negated == 0)
    # post-conditions-end
    # impl-start
    try:
        sql = render_inner(satisfiable)  # type: List[int]
    except EmptyResultSet as exc:
        # Inner selection is unsatisfiable. A negated existence predicate over an
        # empty selection is universally true -> return normally (here, the empty
        # always-true fragment). A non-negated one can never hold -> re-propagate.
        if negated == 1:
            empty = []  # type: List[int]
            return empty
        raise exc
    if negated == 1:
        sql = [78, 79, 84, 32] + sql
        Assert(ToSeq(sql) == not_prefix() + inner_fragment(satisfiable))
    return sql
    # impl-end
