"""Twin-artifact model for django__django-15930.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single conditional branch is rendered into a textual clause of the constant
  shape ``<lead> <predicate> <sep> <consequent>``: a leading keyword, then the
  predicate fragment, then a separating keyword, then the consequent fragment.
  Alongside the text, the branch carries an ordered list of bound parameters:
  the predicate's parameters followed by the consequent's parameters, in that
  order.

  The predicate fragment is produced upstream and handed in. A predicate that
  matches every row is produced upstream as the EMPTY fragment (carrying no
  parameters). Splicing an empty fragment between the two keywords would yield
  a malformed clause whose predicate slot is blank. The required behaviour is
  therefore: whenever the supplied predicate fragment is empty, the rendered
  clause must instead use a constant, NON-EMPTY always-true predicate (together
  with that always-true predicate's own parameters); a non-empty supplied
  fragment is used verbatim. As a consequence the predicate slot of the
  rendered clause is never blank, for any supplied predicate.

Modelling choices (Nagini fragment):
  * Text fragments (the rendered clause, the predicate fragment, the consequent
    fragment, the constant keywords, the always-true predicate) are modelled as
    ``List[int]`` / ``PSeq[int]`` of code points; Nagini bans ``str`` indexing.
    Only fragment identity and emptiness matter to the behaviour, so the code
    points are faithful carriers (mapping.md §2).
  * The bound-parameter lists are ``List[int]`` of opaque parameter-identity
    tokens; only their order and the concatenation order matter.
  * The constant leading keyword, separating keyword and always-true predicate are
    modelled as concrete constant sequences. The always-true predicate is the
    constant the behaviour splices in for an empty supplied predicate; its only
    relied-on property is that it is NON-EMPTY (and that it contributes its own
    parameter list), so it is spelled out as a constant rather than treated as
    an opaque callee.

The whole behaviour is modelled deeply (the empty-predicate substitution and
the clause assembly are spelled out); there is no axiomatised callee. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms. The empty-predicate substitution and the clause assembly are the
# behaviour under specification and are modelled deeply (the `lead()`,
# `sep()`, `true_predicate()`, `true_params()` constants and the impl region).
# The only operations the behaviour composes are an emptiness test and
# sequence construction/concatenation, ordinary operations with their real
# Python semantics; there is no unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def lead() -> PSeq[int]:
    """The constant leading keyword spliced before the predicate: 'WHEN '."""
    return PSeq(87, 72, 69, 78, 32)


@Pure
def sep() -> PSeq[int]:
    """The constant separating keyword spliced between predicate and consequent:
    ' THEN '."""
    return PSeq(32, 84, 72, 69, 78, 32)


@Pure
def true_predicate() -> PSeq[int]:
    """The constant, NON-EMPTY always-true predicate fragment spliced in when the
    supplied predicate fragment is empty. Modelled here as the constant 'TRUE';
    the behaviour relies only on its being non-empty."""
    return PSeq(84, 82, 85, 69)


@Pure
def true_params() -> PSeq[int]:
    """The bound parameters carried by the always-true predicate: a single
    opaque parameter token (the always-true predicate binds its truth value as
    one parameter). Spliced in alongside `true_predicate()` when the supplied
    predicate fragment is empty."""
    return PSeq(1)


@Pure
def clause_text(pred: PSeq[int], cons: PSeq[int]) -> PSeq[int]:
    """The rendered clause text for a (predicate, consequent) pair:
    `lead()` then the predicate slot then `sep()` then the consequent.
    The predicate slot is the supplied predicate when non-empty, otherwise the
    constant always-true predicate -- so it is never empty."""
    if len(pred) == 0:
        return lead() + true_predicate() + sep() + cons
    return lead() + pred + sep() + cons


@Pure
def clause_params(pred: PSeq[int], pred_params: PSeq[int],
                  cons_params: PSeq[int]) -> PSeq[int]:
    """The rendered clause's bound parameters: the predicate's parameters
    followed by the consequent's parameters. For an empty supplied predicate
    its parameters are replaced by the always-true predicate's parameters
    (`true_params()`)."""
    if len(pred) == 0:
        return true_params() + cons_params
    return pred_params + cons_params
# pure-end


def render_branch(pred: List[int],
                  pred_params: List[int],
                  cons: List[int],
                  cons_params: List[int]) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All four inputs are read-only upstream products (never mutated): the
    # supplied predicate fragment, its parameters, the consequent fragment and
    # its parameters. Fractional permission, required AND ensured.
    Requires(Acc(list_pred(pred), 1 / 2))
    Requires(Acc(list_pred(pred_params), 1 / 2))
    Requires(Acc(list_pred(cons), 1 / 2))
    Requires(Acc(list_pred(cons_params), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pred), 1 / 2))
    Ensures(Acc(list_pred(pred_params), 1 / 2))
    Ensures(Acc(list_pred(cons), 1 / 2))
    Ensures(Acc(list_pred(cons_params), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The rendered clause text is the constant-shape splice, with the empty
    # supplied predicate replaced by the always-true predicate.
    Ensures(ToSeq(Result()[0]) == clause_text(ToSeq(pred), ToSeq(cons)))
    # The rendered clause's bound parameters, with the empty predicate's
    # parameters replaced by the always-true predicate's parameters.
    Ensures(ToSeq(Result()[1]) ==
            clause_params(ToSeq(pred), ToSeq(pred_params), ToSeq(cons_params)))
    # The discriminating guarantee: the predicate slot of the rendered clause
    # is never blank. Concretely, the rendered text strictly extends the constant
    # 'lead + sep + consequent' framing by at least one predicate code point,
    # for EVERY supplied predicate (including the empty one).
    Ensures(len(Result()[0]) > len(lead()) + len(sep()) + len(cons))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the supplied predicate fragment is used as the
    # predicate slot verbatim, with NO substitution when it is empty. For a
    # supplied predicate that matches every row (the empty fragment) this leaves
    # the predicate slot blank.
    cond_text = []  # type: List[int]
    cond_params = []  # type: List[int]
    k = 0
    while k < len(pred):
        # invariants-start
        Invariant(Acc(list_pred(cond_text)))
        Invariant(Acc(list_pred(pred), 1 / 2))
        Invariant(0 <= k and k <= len(pred))
        Invariant(ToSeq(cond_text) == ToSeq(pred).take(k))
        Invariant(MustTerminate(len(pred) - k + 1))
        # invariants-end
        cond_text = cond_text + [pred[k]]
        k = k + 1
    Assert(ToSeq(pred).take(len(pred)) == ToSeq(pred))
    Assert(ToSeq(cond_text) == ToSeq(pred))
    k = 0
    while k < len(pred_params):
        # invariants-start
        Invariant(Acc(list_pred(cond_params)))
        Invariant(Acc(list_pred(cond_text)))
        Invariant(Acc(list_pred(pred), 1 / 2))
        Invariant(Acc(list_pred(pred_params), 1 / 2))
        Invariant(ToSeq(cond_text) == ToSeq(pred))
        Invariant(0 <= k and k <= len(pred_params))
        Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
        Invariant(MustTerminate(len(pred_params) - k + 1))
        # invariants-end
        cond_params = cond_params + [pred_params[k]]
        k = k + 1
    Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
    Assert(ToSeq(cond_text) == ToSeq(pred))
    Assert(ToSeq(cond_params) == ToSeq(pred_params))
    # Assemble lead + predicate-slot + sep + consequent.
    text = []  # type: List[int]
    i = 0
    while i < len(lead()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(0 <= i and i <= len(lead()))
        Invariant(ToSeq(text) == lead().take(i))
        Invariant(MustTerminate(len(lead()) - i + 1))
        # invariants-end
        text = text + [lead()[i]]
        i = i + 1
    i = 0
    while i < len(cond_text):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(cond_text))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text).take(i))
        Invariant(MustTerminate(len(cond_text) - i + 1))
        # invariants-end
        text = text + [cond_text[i]]
        i = i + 1
    i = 0
    while i < len(sep()):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(0 <= i and i <= len(sep()))
        Invariant(ToSeq(text) == lead() + ToSeq(cond_text) + sep().take(i))
        Invariant(MustTerminate(len(sep()) - i + 1))
        # invariants-end
        text = text + [sep()[i]]
        i = i + 1
    i = 0
    while i < len(cons):
        # invariants-start
        Invariant(Acc(list_pred(text)))
        Invariant(Acc(list_pred(cond_text), 1 / 2))
        Invariant(Acc(list_pred(cons), 1 / 2))
        Invariant(0 <= i and i <= len(cons))
        Invariant(ToSeq(text) ==
                  lead() + ToSeq(cond_text) + sep() + ToSeq(cons).take(i))
        Invariant(MustTerminate(len(cons) - i + 1))
        # invariants-end
        text = text + [cons[i]]
        i = i + 1
    # Combined parameters: predicate-slot parameters then consequent parameters.
    params = []  # type: List[int]
    i = 0
    while i < len(cond_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(0 <= i and i <= len(cond_params))
        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
        Invariant(MustTerminate(len(cond_params) - i + 1))
        # invariants-end
        params = params + [cond_params[i]]
        i = i + 1
    i = 0
    while i < len(cons_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cons_params))
        Invariant(ToSeq(params) ==
                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
        Invariant(MustTerminate(len(cons_params) - i + 1))
        # invariants-end
        params = params + [cons_params[i]]
        i = i + 1
    return text, params
    # impl-end
