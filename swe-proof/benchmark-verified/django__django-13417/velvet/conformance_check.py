#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13417.

Refutes the R/I refinement leg (A1-A9: the modeled five-signal boolean decision
of `Solution.lean`'s `ordered` do block).

ORACLE CHOICE — why we transliterate the source line instead of running the
property:
  `QuerySet.ordered` reads five attributes off a live `QuerySet` / its `Query`
  (`isinstance(self, EmptyQuerySet)`, `self.query.extra_order_by`,
  `self.query.order_by`, `self.query.default_ordering`,
  `self.query.get_meta().ordering`, `self.query.group_by`) and returns a pure
  boolean combination of their TRUTH VALUES. The behavior under test is exactly
  that boolean decision; the attributes are consumed only for truthiness
  (mapping.md §2). So, per the worker prompt, the ORACLE is the gold-patched
  property body transliterated VERBATIM (each attribute fed as its bool()
  projection — the R-refinement), and the SHADOW is the modeled decision from
  Solution.lean's `ordered` / `isOrdered`.

  We differential-test SHADOW vs ORACLE over ALL 2**5 = 32 combinations of the
  five booleans (exhaustive — the input space is finite) plus a fuzzed stream
  for defense in depth. Exit 0 iff zero disagreements. stdlib only.

  No callee is abstracted: there is no library/utility call the patch leaves
  unchanged; every input is a truthy attribute read, R-refined to a bool. Hence
  no axiom and no axiom_check.py (G-AX vacuous).
"""
import itertools
import random
import sys

SEED = 13417
N_FUZZ = 200_000


def shadow(is_empty, has_raw_order, default_on, model_has_order, is_grouped):
    """`ordered` / `isOrdered` transliterated: the modeled five-signal decision.
    Mirrors `isEmpty || hasRawOrder || (defaultOn && modelHasOrder && !isGrouped)`
    exactly (equivalently the nested-if impl region of Solution.lean)."""
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False


def oracle(is_empty, has_raw_order, default_on, model_has_order, is_grouped):
    """The gold-patched `QuerySet.ordered` body transliterated verbatim from
    django/db/models/query.py (gold-patched), with each attribute read fed as
    its bool() projection (the R-refinement, mapping.md §2):

        if isinstance(self, EmptyQuerySet):            -> is_empty
            return True
        if self.query.extra_order_by or self.query.order_by:  -> has_raw_order
            return True
        elif (self.query.default_ordering               -> default_on
              and self.query.get_meta().ordering         -> model_has_order
              and not self.query.group_by):              -> not is_grouped
            return True
        else:
            return False
    """
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(itertools.product([False, True], repeat=5))  # exhaustive 32
    for _ in range(N_FUZZ):
        cases.append(tuple(rng.choice([False, True]) for _ in range(5)))

    for tup in cases:
        count += 1
        s = shadow(*tup)
        o = oracle(*tup)
        if s != o:
            disagreements.append((tup, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of `ordered` agrees with the gold-patched "
          "property body on %d five-bool inputs (all 32 combinations exhaustive "
          "+ fuzz, seed=%d), 0 disagreements. Each repo truthy attribute read is "
          "fed as its bool() projection (R-refinement); no callee abstracted."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
