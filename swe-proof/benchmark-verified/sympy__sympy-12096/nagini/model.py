"""Twin-artifact model for sympy__sympy-12096.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic application carries a numeric implementation `imp` (a deterministic
  unary map on numbers) and is wrapped in zero or more layers around a numeric
  leaf -- each layer being one more surrounding application of the same kind.
  The whole nested object is reduced to a number INSIDE-OUT: the innermost
  numeric leaf is taken first, then `imp` is applied once per surrounding layer,
  the result of each inner layer becoming the (already-numeric) input to the
  next.

  The number of layers is carried by `layers` (its length is the nesting count;
  the element values are irrelevant). Within the domain where the reduced value
  is exactly representable (a non-negative leaf whose inside-out reduction stays
  below the exact-representation bound), the reduction must succeed -- yield a
  PRESENT number -- for EVERY number of layers, including a composition (two or
  more layers) whose argument is itself an application: that inner application
  is reduced to its number before the outer `imp` is applied to it. A naive
  reduction that feeds an un-reduced inner application into `imp` can only
  produce a number when there is at most one layer, and leaves any deeper
  composition unevaluated (absent / None).

  Zero layers (a bare numeric leaf) reduce to the leaf value.

A concrete representative numeric implementation is used (`imp(x) = x * x`, the
squaring map of the worked example): the discriminating behaviour -- whether a
deep composition reduces to a number at all -- is independent of which concrete
implementation is chosen, so the reduction is modelled deeply as the
front-recursive fold `eval_seq` over that map and the layer sequence. The fold's
agreement with the real recursive evaluation is checked out-of-band by
axiom_check.py (G-AX). Numbers are modelled as `int`; the layer sequence is a
`List[int]` carried into the specification as a `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No opaque callee is consumed: the numeric implementation and the inside-out
#  reduction are modelled directly below as the pure functions `imp` and
#  `eval_seq`. Their agreement with the real recursive evaluation is an
#  A-reference validated by axiom_check.py / G-AX, not a consumed value axiom.)
# axioms-end


# pure-start
@Pure
def imp(x: int) -> int:
    """A concrete representative of the numeric implementation applied at each
    layer (the squaring map of the worked example). Deterministic and total."""
    return x * x


@Pure
def eval_seq(leaf: int, layers: PSeq[int]) -> int:
    """Inside-out reduction: apply `imp` once per layer to the numeric `leaf`.
    Only the number of layers matters (element values are ignored).
    Front-recursive over the head so a single unfold is available per loop
    step. An empty layer sequence is the bare leaf."""
    if len(layers) == 0:
        return leaf
    return imp(eval_seq(leaf, layers.drop(1)))
# pure-end


def eval_implemented(leaf: int, layers: List[int]) -> Optional[int]:
    # pre-conditions-start
    # `layers` is read-only; its length is the nesting count.
    Requires(Acc(list_pred(layers), 1 / 2))
    # Domain of the contract: the leaf is non-negative and the inside-out
    # reduction stays inside the exact representable window (< 1e14). Outside
    # this window the result is only an approximation, so the exact-value
    # postcondition below is asserted only where it holds.
    Requires(leaf >= 0)
    Requires(eval_seq(leaf, ToSeq(layers)) < 100000000000000)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(layers), 1 / 2))
    # The nested object reduces, for every number of layers, to a PRESENT
    # number equal to the inside-out reduction: `imp` applied once per layer to
    # the leaf. In particular a composition (two or more layers) is reduced --
    # never left absent.
    Ensures(Result() is not None)
    Ensures(Result() == eval_seq(leaf, ToSeq(layers)))
    # post-conditions-end
    # impl-start
    acc = leaf
    i = len(layers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(layers), 1 / 2))
        Invariant(0 <= i and i <= len(layers))
        # `acc` is the inside-out reduction of the innermost `len - i` layers.
        Invariant(acc == eval_seq(leaf, ToSeq(layers).drop(i)))
        # invariants-end
        # The fold unfolds at the head of drop(i-1) (non-empty since i > 0):
        # supply the head/tail split so a single unfold relates step i-1 to i.
        Assert(ToSeq(layers).drop(i - 1).drop(1) == ToSeq(layers).drop(i))
        acc = imp(acc)
        i = i - 1
    return acc
    # impl-end
