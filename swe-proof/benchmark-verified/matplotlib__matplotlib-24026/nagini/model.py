"""Twin-artifact model for matplotlib__matplotlib-24026.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stacked area drawing routine paints N stacked layers. When the caller
  supplies an explicit, non-empty sequence of colours, the colour of layer i
  is the supplied colour at position (i mod K), where K is the number of
  supplied colours -- i.e. the supplied colours are cycled, repeating from the
  beginning once exhausted, and need not match the layer count.

  Crucially, supplying explicit colours is a read-only request: it MUST NOT
  alter the drawing context's own colour-cycle state. That shared state is the
  same one consulted by other drawing routines, so the context's colour-cycle
  snapshot is observed to be identical before and after the call.

The colour-cycle state of the drawing context is modelled as a small object
holding an opaque snapshot (`cycle`). Colours are modelled as `List[int]`
opaque tokens (only identity, order and count matter). The per-layer colour
assignment is modelled DEEPLY as integer indexing with a modulus; there is no
axiomatized callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callee: the only library operation -- cycling a finite colour
#  sequence -- is modelled deeply as `colors[i % len(colors)]`, fully expressible
#  in Nagini. This deep model is validated externally against the real cyclic
#  colour source, which repeats the supplied colours from the beginning.)
# axioms-end


# pure-start
@Pure
def cyc(colors: PSeq[int], i: int) -> int:
    """The colour painted on layer `i`: the supplied colour at the cyclic
    position `i mod K` (K = number of supplied colours), i.e. the supplied
    colours repeating from the beginning. A direct modular index, carrying its
    own well-definedness (non-empty sequence, non-negative layer index)."""
    Requires(len(colors) >= 1)
    Requires(i >= 0)
    return colors[i % len(colors)]


@Pure
def cyc_prefix(colors: PSeq[int], m: int) -> PSeq[int]:
    """The first `m` per-layer colours: the cyclic reading of `colors`, layer 0
    first. Front-recursive (one auto-unfold per loop step): the colours up to
    layer m-1 followed by layer m-1's colour."""
    Requires(len(colors) >= 1)
    Requires(m >= 0)
    if m == 0:
        return colors.take(0)
    return cyc_prefix(colors, m - 1) + PSeq(cyc(colors, m - 1))


@Pure
def cyc_prefix_unfold(colors: PSeq[int], m: int) -> bool:
    """Lemma: at length m >= 1 the cyclic reading is the length-(m-1) reading
    followed by layer (m-1)'s colour (one front-recursive unfold)."""
    Requires(len(colors) >= 1)
    Requires(m >= 1)
    Ensures(Result())
    Ensures(cyc_prefix(colors, m)
            == cyc_prefix(colors, m - 1) + PSeq(cyc(colors, m - 1)))
    return True


@Pure
def cyc_prefix_len(colors: PSeq[int], m: int) -> bool:
    """Lemma: the cyclic reading of length m has length m (proof by structural
    recursion over m)."""
    Requires(len(colors) >= 1)
    Requires(m >= 0)
    Ensures(Result())
    Ensures(len(cyc_prefix(colors, m)) == m)
    if m == 0:
        return True
    return cyc_prefix_len(colors, m - 1)


@Pure
def cyc_prefix_elem(colors: PSeq[int], m: int, j: int) -> bool:
    """Lemma: element j of the length-m cyclic reading is the colour at cyclic
    position j (proof by structural recursion over m)."""
    Requires(len(colors) >= 1)
    Requires(m >= 0)
    Requires(0 <= j and j < m)
    Ensures(Result())
    Ensures(cyc_prefix_len(colors, m))
    Ensures(cyc_prefix(colors, m)[j] == cyc(colors, j))
    if j == m - 1:
        return cyc_prefix_len(colors, m - 1)
    return cyc_prefix_elem(colors, m - 1, j)
# pure-end


class Axes:
    """The drawing context, carrying only the field this change concerns: an
    opaque snapshot of its colour-cycle state (`cycle`). The behaviour under
    test is whether the routine leaves this snapshot untouched."""

    def __init__(self, cycle: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.cycle))
        Ensures(self.cycle == cycle)
        # post-conditions-end
        # impl-start
        self.cycle = cycle  # type: PSeq[int]
        # impl-end


def assign_layer_facecolors(axes: Axes, colors: List[int],
                            n: int) -> List[int]:
    # pre-conditions-start
    # A stacked plot always paints at least the first layer; the caller supplies
    # a non-empty colour sequence (the explicit-colours branch).
    Requires(n >= 1)
    Requires(Acc(list_pred(colors), 1 / 2))
    Requires(len(colors) >= 1)
    # The colour-cycle snapshot is read-only: held at half permission, so a
    # conforming implementation may observe but never mutate it.
    Requires(Acc(axes.cycle, 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(colors), 1 / 2))
    Ensures(len(colors) >= 1)
    Ensures(Acc(axes.cycle, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The drawing context's colour-cycle snapshot is unchanged by the call.
    Ensures(axes.cycle == Old(axes.cycle))
    # The whole per-layer colour list is the cyclic reading of the supplied
    # colours: layer i is the supplied colour at cyclic position (i mod K).
    Ensures(ToSeq(Result()) == cyc_prefix(ToSeq(colors), n))
    # One facecolour per layer.
    Ensures(len(Result()) == n)
    # Layer i is painted with the supplied colour at position (i mod K): the
    # supplied colours are cycled, repeating from the beginning.
    Ensures(Forall(int, lambda i:
                   (Implies(0 <= i and i < n,
                            Result()[i] == cyc(ToSeq(colors), i)),
                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(colors), 1 / 2))
        Invariant(len(colors) >= 1)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(result) == cyc_prefix(ToSeq(colors), i))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = cyc(ToSeq(colors), i)
        result.append(c)
        # ToSeq(result) is now the old prefix followed by layer i's colour,
        # which is exactly cyc_prefix at length i+1 (one front-recursive unfold).
        Assert(ToSeq(result) == cyc_prefix(ToSeq(colors), i)
               + PSeq(cyc(ToSeq(colors), i)))
        Assert(cyc_prefix_unfold(ToSeq(colors), i + 1))
        i = i + 1
        # One more layer is painted per step: the length of what has been
        # painted tracks the layer counter exactly.
        Assert(cyc_prefix_len(ToSeq(colors), i))
        Assert(len(ToSeq(result)) == i)
    # The loop ran to the last layer, so the counter reached the layer count.
    Assert(i == n)
    # The cumulative-sequence postcondition holds directly from the invariant.
    # Discharge the length and element-wise postconditions via the lemmas.
    Assert(cyc_prefix_len(ToSeq(colors), n))
    Assert(Forall(int, lambda j:
                  (Implies(0 <= j and j < n,
                           cyc_prefix_elem(ToSeq(colors), n, j)),
                   [[cyc(ToSeq(colors), j)]])))
    return result
    # impl-end
