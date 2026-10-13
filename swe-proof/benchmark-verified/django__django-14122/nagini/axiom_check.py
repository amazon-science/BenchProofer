#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14122.

This bundle consumes NO @ContractOnly axiom (the `axioms` region of model.py is
empty). The only kind-A obligation is the **A-reference** deep model: the whole
grouping-key assembly is modeled DEEPLY (`assemble_grouping_key` + the `order_contrib`
fold, model.py), and we must validate that deep model against the REAL patched
repo logic it abstracts.

The real callee is `SQLCompiler.get_group_by(select, order_by)`
(django/db/models/sql/compiler.py). At the abstraction this bundle uses each
contributing source is reduced to its grouping-column tokens:

  * the selected-column source (the `for expr, _, _ in select:` loop +
    `having_group_by`) is appended unconditionally;
  * the result-ordering source (the `for expr, (sql, params, is_ref) in
    order_by:` loop) extends the expression list with
    `expr.get_group_by_cols()` for each entry whose `is_ref` is falsy, and is
    *skipped entirely* when `self._meta_ordering` is set (the patched guard
    `if not self._meta_ordering:`).

`self._meta_ordering` is set ONLY when the ordering was taken from the model's
default `Meta.ordering` and NOT explicitly requested (get_order_by,
compiler.py:286-288). So `ordering_was_requested == (not bool(_meta_ordering))`,
and the patched guard `if not self._meta_ordering:` is exactly "fold the
ordering source into the grouping key iff the ordering was requested".

This script re-expresses the PATCHED get_group_by algorithm at the token level
(`reference_group_by`) and asserts the model's deep reference
(`model_assemble_grouping_key`) equals it on boundary + randomized fuzz inputs,
including the discriminating `ordering_was_requested` flag and the per-entry
back-reference skip. Imports stdlib only (no repo import needed: the modeled
operation is pure list/flag control flow, transcribed from the patched source
with its provenance cited above and in mapping.md). Exit 0 iff sound.
"""
import random
import sys


# --- model.py deep-model reference (kept in lock-step with order_contrib) -----

def model_order_contrib(cols, refs):
    """Reference of model.py `order_contrib`: tokens of NON-back-reference
    entries, in order. refs[k] != 0 marks entry k a back-reference (skipped)."""
    assert len(cols) == len(refs)
    out = []
    for c, r in zip(cols, refs):
        if r == 0:
            out.append(c)
    return out


def model_assemble_grouping_key(select_cols, order_cols, order_is_backref, trailing_cols,
                         ordering_was_requested):
    """Reference of model.py `assemble_grouping_key` (its two postcondition clauses)."""
    if ordering_was_requested:
        return (list(select_cols)
                + model_order_contrib(order_cols, order_is_backref)
                + list(trailing_cols))
    return list(select_cols) + list(trailing_cols)


# --- the REAL patched get_group_by algorithm, transcribed at token level ------

def reference_group_by(select_cols, order_cols, order_is_backref, trailing_cols,
                       meta_ordering):
    """Token-level transcription of the PATCHED
    SQLCompiler.get_group_by (compiler.py:120-135 post-patch):

        expressions = []                      # plus the unconditional select loop
        for expr, _, _ in select:             #  -> select_cols
            expressions.extend(expr.get_group_by_cols())
        if not self._meta_ordering:           # the PATCHED guard
            for expr, (sql, params, is_ref) in order_by:
                if not is_ref:                #  -> skip back-references
                    expressions.extend(expr.get_group_by_cols())
        for expr in having_group_by:          # the unconditional trailing source
            expressions.append(expr)          #  -> trailing_cols
    """
    expressions = []
    # select source (unconditional)
    for c in select_cols:
        expressions.append(c)
    # result-ordering source: skipped entirely when meta_ordering is truthy
    if not meta_ordering:
        for c, is_ref in zip(order_cols, order_is_backref):
            if not is_ref:                    # skip references (is_ref truthy)
                expressions.append(c)
    # trailing (having) source (unconditional)
    for c in trailing_cols:
        expressions.append(c)
    return expressions


def reference_group_by_prepatch(select_cols, order_cols, order_is_backref,
                                trailing_cols, meta_ordering):
    """The PRE-PATCH algorithm (compiler.py:128-132 pre-patch): the ordering
    source is folded UNCONDITIONALLY (no `if not self._meta_ordering:` guard).
    Used only to confirm the discriminating witness actually differs."""
    expressions = []
    for c in select_cols:
        expressions.append(c)
    for c, is_ref in zip(order_cols, order_is_backref):   # NO meta_ordering guard
        if not is_ref:
            expressions.append(c)
    for c in trailing_cols:
        expressions.append(c)
    return expressions


# --- the checks ---------------------------------------------------------------

def check_one(select_cols, order_cols, order_is_backref, trailing_cols,
              ordering_was_requested):
    """Assert the model deep reference == the real patched algorithm.

    Model flag `ordering_was_requested` corresponds to repo `_meta_ordering`
    via `meta_ordering = not ordering_was_requested` (compiler.py:286-288)."""
    meta_ordering = not ordering_was_requested
    observed = reference_group_by(select_cols, order_cols, order_is_backref,
                                  trailing_cols, meta_ordering)
    expected = model_assemble_grouping_key(select_cols, order_cols, order_is_backref,
                                    trailing_cols, ordering_was_requested)
    assert observed == expected, (
        "deep model unsound: select=%r order=%r refs=%r trailing=%r "
        "requested=%r -> patched get_group_by gave %r, model gives %r"
        % (select_cols, order_cols, order_is_backref, trailing_cols,
           ordering_was_requested, observed, expected))


def main():
    rng = random.Random(14122)

    # --- boundary cases -------------------------------------------------------
    boundary = [
        # (select, order_cols, order_is_backref, trailing, requested)
        ([], [], [], [], True),
        ([], [], [], [], False),
        ([1], [], [], [], True),
        ([1], [2], [0], [], True),     # one order col, not a ref, requested
        ([1], [2], [0], [], False),    # default ordering -> order col dropped
        ([1], [2], [1], [], True),     # the single order entry is a back-ref
        ([1], [2], [1], [], False),
        ([1, 2], [3, 4], [0, 0], [5], True),
        ([1, 2], [3, 4], [0, 0], [5], False),   # the F2P-shaped case
        ([10], [10], [0], [], False),  # order col duplicates a select col
        ([10], [10], [0], [], True),
        ([1], [2, 3, 4], [0, 1, 0], [9], True),  # mixed refs
        ([1], [2, 3, 4], [0, 1, 0], [9], False),
        # the discriminating F2P scenario: values('author').annotate(Count) with
        # Article Meta.ordering = ['-pub_date'] -> ordering NOT requested ->
        # pub_date must NOT join the grouping key (author).
        ([100], [200], [0], [], False),
    ]
    for case in boundary:
        check_one(*case)

    # --- the F2P discriminating witness: default ordering must differ from the
    #     pre-patch behaviour, and the model must match the PATCHED behaviour ---
    sel, oc, refs, tr = [100], [200], [0], []
    patched = reference_group_by(sel, oc, refs, tr, meta_ordering=True)
    prepatch = reference_group_by_prepatch(sel, oc, refs, tr, meta_ordering=True)
    assert patched == [100], "patched dropped order col? %r" % patched
    assert prepatch == [100, 200], "prepatch should keep order col: %r" % prepatch
    assert patched != prepatch, "F2P witness does not discriminate the fix"
    assert model_assemble_grouping_key(sel, oc, refs, tr, False) == patched

    # --- randomized fuzz ------------------------------------------------------
    for _ in range(50000):
        ns = rng.randint(0, 5)
        no = rng.randint(0, 5)
        nt = rng.randint(0, 3)
        select_cols = [rng.randint(1, 9) for _ in range(ns)]
        order_cols = [rng.randint(1, 9) for _ in range(no)]
        order_is_backref = [rng.choice([0, 0, 1]) for _ in range(no)]
        trailing_cols = [rng.randint(1, 9) for _ in range(nt)]
        requested = rng.choice([True, False])
        check_one(select_cols, order_cols, order_is_backref, trailing_cols, requested)

    print("G-AX OK: assemble_grouping_key/order_contrib deep model == patched "
          "get_group_by token algorithm on %d boundary + 50000 fuzz inputs; "
          "F2P default-ordering witness drops the ordering token (patched) "
          "vs keeps it (pre-patch)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
