"""Twin-artifact model for sphinx-doc__sphinx-7757.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A function signature is described by an ordered list of *positional*
  parameters, the leading prefix of which are positional-only and the rest
  positional-or-keyword. Separately, a list of supplied default expressions is
  given; by the parser's contract these defaults bind to the *trailing*
  positional parameters (right-aligned across the WHOLE positional list,
  positional-only and ordinary alike), so if there are `n` positional
  parameters and `m` supplied defaults then exactly the last `m` parameters
  carry a default and the first `n - m` carry none.

  The desired result associates each positional parameter with its default:
  parameter at index `p` (0-based over the whole positional list) has NO
  default when `p < n - m`, and otherwise carries the supplied default at
  offset `p - (n - m)`, rendered to its source form. This must hold uniformly
  whether the parameter is positional-only or positional-or-keyword — the
  positional-only prefix is NOT exempt from receiving its share of the
  trailing defaults.

Parameters carry an integer "kind" tag and a default slot. Defaults are
modelled as `List[int]` of value codes; the sentinel `EMPTY` (-1) marks "no
default". The per-element rendering of a supplied default expression to its
source string is an unchanged callee, modelled by the deterministic pure map
`render` (validated == the real renderer by axiom_check.py / G-AX); it never
changes WHICH positions receive a default, which is the property the
specification pins.

The specification is a TOTAL-correctness one: resolving the defaults is
required to terminate on every input its precondition admits, so the
postconditions below are claimed of every run and not only of the runs that
happen to reach a return. That is a property of the real behaviour, not a
convenience: the desired resolution walks each of the finitely many positional
parameters exactly once, consulting a finite list of supplied defaults, and
consults nothing that could grow while it is being read, so no admissible input
gives it an unbounded amount of work to do. `Requires(MustTerminate(...))` on
the resolver states that obligation, and the loop measure inside the
implementation region discharges it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def renderable(value_code: int) -> bool:
    """Holds of exactly those supplied-default value codes the unchanged
    per-default renderer accepts. The renderer is a PARTIAL map: it is defined
    only on the subset of default expressions it supports and is undefined
    (does not return a source string) on the rest. This predicate names that
    domain of definedness; `render` is only ever applied to codes that satisfy
    it, so the contract never claims the renderer returns on inputs it does not
    handle. Validated == the real renderer's domain out-of-band (mapping.md /
    axiom_check.py, G-AX)."""


@Pure
@ContractOnly
def render(value_code: int) -> int:
    """Render one supplied default expression to its source form. The unchanged
    per-default callee (AST node -> source string); abstracted as a
    deterministic map on the value codes it is *defined* on (`renderable`). It
    is applied pointwise to the defaults that survive alignment and therefore
    cannot move a default from one position to another. Determinism (referential
    transparency) over its domain is all the proof needs; the concrete map is
    validated equal to the real renderer out-of-band (mapping.md /
    axiom_check.py, G-AX). On a renderable input the result is always a
    non-sentinel code (a rendered source string is never the 'no default'
    marker, which is a unique sentinel object distinct from any source string).
    The `renderable` precondition restricts the contract to the renderer's
    domain of definedness so it never asserts a return value on inputs the real
    renderer does not handle.
    """
    Requires(renderable(value_code))
    Ensures(Result() != EMPTY())
# axioms-end


# pure-start
@Pure
def EMPTY() -> int:
    """Sentinel value code meaning 'this parameter carries no default'."""
    return -1


@Pure
def first_default_pos(n: int, m: int) -> int:
    """Index of the first positional parameter that carries a default: the
    supplied defaults right-align across all `n` positional parameters, so the
    leading `n - m` carry none."""
    Requires(0 <= m and m <= n)
    Ensures(Result() == n - m)
    return n - m


@Pure
def resolved_default(p: int, n: int, m: int, provided: PSeq[int]) -> int:
    """The default associated with positional parameter at index `p`:
    `EMPTY` when `p` is before the trailing default block, otherwise the
    rendered supplied default at offset `p - (n - m)`."""
    Requires(0 <= m and m <= n)
    Requires(0 <= p and p < n)
    Requires(len(provided) == m)
    # every supplied default is one the renderer is defined on (its domain)
    Requires(Forall(int, lambda j: (
        Implies(0 <= j and j < m, renderable(provided[j])),
        [[provided[j]]])))
    Ensures(Implies(p < n - m, Result() == EMPTY()))
    Ensures(Implies(p >= n - m, Result() == render(provided[p - (n - m)])))
    Ensures(Implies(p >= n - m, Result() != EMPTY()))
    if p < first_default_pos(n, m):
        return EMPTY()
    return render(provided[p - first_default_pos(n, m)])


# pure-end


def resolve_positional_defaults(positionals: int, posonly: int,
                                provided: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(0 <= posonly and posonly <= positionals)
    Requires(Acc(list_pred(provided), 1 / 2))
    Requires(len(provided) <= positionals)
    # every supplied default is one the per-default renderer is defined on
    # (its domain); the renderer is partial and is only invoked on these
    Requires(Forall(int, lambda j: (
        Implies(0 <= j and j < len(provided), renderable(ToSeq(provided)[j])),
        [[ToSeq(provided)[j]]])))
    # TERMINATION is part of what is specified, not an artefact of the proof.
    # Without this obligation Nagini proves only PARTIAL correctness and every
    # postcondition below is claimed only of runs that reach the return, so an
    # implementation that never reaches one -- a self-delegation, an unbounded
    # loop -- satisfies the whole contract while performing none of the work.
    # Resolving the defaults must ANSWER, on every input admitted above: the
    # desired behaviour visits each of the `positionals` parameters once and
    # reads a `provided` list whose length is settled before the first step,
    # so the work is bounded by the input and no admissible input makes it
    # unbounded. The level is a bookkeeping bound, not a domain restriction:
    # it constrains no input value, it obliges the callee to answer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(provided), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the (read-only) supplied defaults are unchanged, hence still renderable
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(provided), renderable(ToSeq(provided)[j])),
        [[ToSeq(provided)[j]]])))
    # the supplied defaults never outnumber the positional parameters
    Ensures(0 <= len(provided) and len(provided) <= positionals)
    # one resolved default per positional parameter
    Ensures(len(Result()) == positionals)
    # every parameter (positional-only prefix included) gets its aligned default
    Ensures(Forall(int, lambda p: (
        Implies(0 <= p and p < positionals,
                ToSeq(Result())[p] == resolved_default(
                    p, positionals, len(provided), ToSeq(provided))),
        [[ToSeq(Result())[p]]])))
    # the positional-only prefix is not exempt: any positional-only parameter
    # within the trailing default block carries a (non-empty) default
    Ensures(Forall(int, lambda p: (
        Implies(0 <= p and p < posonly
                and p >= positionals - len(provided),
                ToSeq(Result())[p] != EMPTY()),
        [[ToSeq(Result())[p]]])))
    # post-conditions-end
    # impl-start
    m = len(provided)
    pad = positionals - m
    result = []  # type: List[int]
    p = 0
    while p < positionals:
        # invariants-start
        Invariant(Acc(list_pred(provided), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(provided) == m and positionals - m == pad)
        Invariant(0 <= pad and pad <= positionals)
        Invariant(0 <= p and p <= positionals)
        Invariant(len(result) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < m, renderable(ToSeq(provided)[j])),
            [[ToSeq(provided)[j]]])))
        Invariant(Forall(int, lambda q: (
            Implies(0 <= q and q < p,
                    ToSeq(result)[q] == resolved_default(
                        q, positionals, m, ToSeq(provided))),
            [[ToSeq(result)[q]]])))
        # decreasing measure discharging the method's MustTerminate obligation:
        # the number of positional parameters still to be resolved, +1 so the
        # last iteration still carries a positive level.
        Invariant(MustTerminate(positionals - p + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        if p < pad:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]
        # the new sequence extends the old by one element at index p
        Assert(len(ToSeq(result)) == p + 1)
        Assert(Forall(int, lambda q: (
            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
            [[ToSeq(result)[q]], [old_seq[q]]])))
        Assert(ToSeq(result)[p] == resolved_default(
            p, positionals, m, ToSeq(provided)))
        p = p + 1
    return result
    # impl-end
