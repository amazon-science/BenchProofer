#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13417.

This bundle consumes NO `@ContractOnly` axiom: the modeled function
`QuerySet.ordered` reads only attributes and returns a boolean combination of
their truth values (mapping.md / refinement.md). There is therefore no
unchanged library callee to over-approximate, and the `axioms` region of
model.py is empty.

What this script DOES validate (the only soundness obligation here, the
refinement fidelity of the truthy-to-bool type abstraction): the model's pure
decision `is_ordered(is_empty, has_raw_order, default_on, model_has_order,
is_grouped)` (model.py pure region) equals the REAL post-patch
`QuerySet.ordered` property body, exhaustively over all 2**5 = 32 boolean
input combinations. The property body is reproduced here from the gold patch
(`django/db/models/query.py`, `ordered`), driven by lightweight stand-ins for
`self`, `self.query`, and `self.query.get_meta()` whose truthy attributes are
exactly the five booleans the model abstracts. We feed both truthy and falsy
*concrete* values for each signal (e.g. group_by as None/(): falsy and
True/(col,): truthy) so the bool() refinement is exercised on real values, not
just on bools.

stdlib-only (no repo imports). Exit 0 iff every observation matches the model.
"""
import itertools
import sys


# --- model.py reference encoding (kept in lock-step with the pure region) ----

def is_ordered(is_empty, has_raw_order, default_on, model_has_order,
               is_grouped):
    """Reference implementation of model.py's pure `is_ordered`."""
    return bool(
        is_empty
        or has_raw_order
        or (default_on and model_has_order and not is_grouped)
    )


# --- real post-patch property body (verbatim logic from the gold patch) ------

class _EmptyQuerySet:
    pass


class _Meta:
    def __init__(self, ordering):
        self.ordering = ordering


class _Query:
    def __init__(self, extra_order_by, order_by, default_ordering,
                 meta_ordering, group_by):
        self.extra_order_by = extra_order_by
        self.order_by = order_by
        self.default_ordering = default_ordering
        self._meta = _Meta(meta_ordering)
        self.group_by = group_by

    def get_meta(self):
        return self._meta


class _QuerySet:
    def __init__(self, is_empty, query):
        self._is_empty = is_empty
        self.query = query

    def _isinstance_empty(self):
        # the model treats EmptyQuerySet-ness as a bool signal; here a flag
        return self._is_empty

    @property
    def ordered(self):
        # Body reproduced verbatim from the gold-patched
        # django/db/models/query.py:QuerySet.ordered
        if self._isinstance_empty():
            return True
        if self.query.extra_order_by or self.query.order_by:
            return True
        elif (
            self.query.default_ordering and
            self.query.get_meta().ordering and
            not self.query.group_by
        ):
            return True
        else:
            return False


# Concrete truthy/falsy witnesses for each signal, so the bool() refinement is
# exercised on the actual repo value shapes, not just on Python bools.
_FALSY = {
    "extra_order_by": (),       # empty tuple
    "order_by": (),
    "default_ordering": False,
    "meta_ordering": [],        # empty Meta.ordering
    "group_by": None,           # Query.group_by init value
}
_TRUTHY = {
    "extra_order_by": ("-id",),
    "order_by": ("name",),
    "default_ordering": True,
    "meta_ordering": ["name"],  # a declared default ordering
    "group_by": True,           # also test ("col",) below
}


def main():
    checked = 0
    # Exhaustive over the five abstracted truth values (2**5 = 32).
    for is_empty, raw_extra, raw_order, default_on, model_has_order, grouped \
            in itertools.product([False, True], repeat=6):
        # has_raw_order abstracts (extra_order_by OR order_by); enumerate the
        # underlying two attributes (raw_extra, raw_order) to confirm the
        # disjunction refinement, then also the abstracted single bool.
        has_raw_order = bool(raw_extra or raw_order)

        # Build concrete repo-shaped values for each signal.
        extra_val = _TRUTHY["extra_order_by"] if raw_extra else _FALSY["extra_order_by"]
        order_val = _TRUTHY["order_by"] if raw_order else _FALSY["order_by"]
        default_val = _TRUTHY["default_ordering"] if default_on else _FALSY["default_ordering"]
        meta_val = _TRUTHY["meta_ordering"] if model_has_order else _FALSY["meta_ordering"]
        # exercise both truthy group_by shapes (True and a non-empty tuple)
        for group_val in ([_TRUTHY["group_by"], ("col1",)] if grouped
                          else [_FALSY["group_by"], ()]):
            qs = _QuerySet(is_empty,
                           _Query(extra_val, order_val, default_val,
                                  meta_val, group_val))
            observed = qs.ordered                       # real property body
            expected = is_ordered(is_empty, has_raw_order, default_on,
                                  model_has_order, grouped)  # model decision
            assert observed == expected, (
                "is_ordered model unsound: inputs "
                "is_empty=%r extra=%r order=%r default_on=%r "
                "model_has_order=%r group_by=%r -> real ordered=%r, "
                "model=%r" % (is_empty, extra_val, order_val, default_on,
                              meta_val, group_val, observed, expected))
            checked += 1

    print("G-AX OK (no axioms in this bundle): is_ordered model == real "
          "QuerySet.ordered property body over %d concrete input "
          "combinations (exhaustive truthy/falsy on all 5 signals)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
