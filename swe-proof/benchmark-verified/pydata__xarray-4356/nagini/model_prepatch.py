"""Twin-artifact model for pydata__xarray-4356.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A masked reduction over a SET of axes records, at every output position, how
  many of the reduced-over input elements were missing, and compares the number
  of present (non-missing) elements against a required minimum. The position is
  flagged as "too few present" exactly when

      (present elements at the position) < (the required minimum),

  where the number of elements that were reduced over at a position is the
  COUNT OF THE WHOLE REDUCED BLOCK -- the product of the input's sizes along
  every reduced axis -- not the size of a single axis. With several reduced
  axes the block spans the PRODUCT of their sizes; with a single reduced axis it
  is just that axis's size. So, writing `total` for that product and `missing`
  for the number of missing elements at the position, the position is flagged
  iff `total - missing < required_minimum`.

  This must hold for any non-empty group of reduced axes (one or many), each
  with a positive size.

Modelling: `sizes` is the input's sizes along the reduced axes (`List[int]`,
the per-reduced-axis-list selection of the input's shape; each > 0). `prod`
folds them to `total`; `missing` is the number of missing elements at the
position (0 <= missing <= total). `flag_too_few` returns whether the position
is flagged.

`prod` is spelled out DEEPLY (front-recursive fold), and the composition
"select the reduced-axes sizes, then take their product" is validated == the
real select-then-product callee by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom: the changed quantity -- the product of the
# reduced-axes sizes -- is modelled deeply by `prod` below and validated against
# the real select-then-product callee by axiom_check.py (G-AX, an A-reference).
# There is no unchanged opaque callee the proof depends on.)
# axioms-end


# pure-start
@Pure
def prod(xs: PSeq[int]) -> int:
    """Product fold over a sequence (empty product is 1). Front-recursive so a
    single unfold is available per loop step."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod(xs.drop(1))
# pure-end


def flag_too_few(sizes: List[int], missing: int,
                 required_minimum: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(sizes), 1 / 2))
    # at least one reduced axis
    Requires(len(sizes) >= 1)
    # the number of missing elements is between none and the whole block
    Requires(0 <= missing)
    Requires(missing <= prod(ToSeq(sizes)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(sizes), 1 / 2))
    # The position is flagged iff the present elements -- the product of the
    # reduced-axes sizes minus the missing ones -- are fewer than the minimum.
    Ensures(Result() ==
            (prod(ToSeq(sizes)) - missing - required_minimum < 0))
    # post-conditions-end
    # impl-start
    # PRE-PATCH BUG: counts the elements of only the FIRST reduced axis, i.e.
    # the single-axis size `mask.shape[axis]`, rather than the product over the
    # whole reduced block. For a single reduced axis this coincides with the
    # product; for several it undercounts, so present-element counts (and hence
    # the flag) are wrong.
    total = sizes[0]
    return (total - missing - required_minimum) < 0
    # impl-end


def lemma_prod_snoc(xs: PSeq[int]) -> None:
    """Lemma: the product of a non-empty sequence equals the product of its
    front (all but the last) times the last element:
        prod(xs) == prod(xs.take(len-1)) * xs[len-1].
    Proved by induction on the front-recursive fold."""
    Requires(len(xs) >= 1)
    Ensures(prod(xs) == prod(xs.take(len(xs) - 1)) * xs[len(xs) - 1])
    if len(xs) == 1:
        Assert(xs.take(0) == PSeq(0).take(0))
        Assert(xs.drop(1) == PSeq(0).take(0))
    else:
        lemma_prod_snoc(xs.drop(1))
        Assert(xs[len(xs) - 1] == xs.drop(1)[len(xs) - 2])
        Assert(xs.take(len(xs) - 1).drop(1) == xs.drop(1).take(len(xs) - 2))
        Assert(prod(xs) == xs[0] * prod(xs.drop(1)))
        Assert(prod(xs.take(len(xs) - 1)) ==
               xs.take(len(xs) - 1)[0] * prod(xs.take(len(xs) - 1).drop(1)))
        Assert(xs.take(len(xs) - 1)[0] == xs[0])
