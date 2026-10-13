#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-14351.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Exercises the REAL patched callee
`django.db.models.lookups.In.get_group_by_cols` and diffs its observable
behaviour against the Python shadow of the Lean
`implementation_membershipGroupColumns` skeleton over a discrete catalogue plus
>=1e5 randomized cases.

What is observed (mapping.md): for a membership ("IN") lookup, `get_group_by_cols`
returns the collected grouping-key column list AND may mutate its right-hand-side
subquery's *selection state*. The fix is observable in BOTH: the returned list
embeds the rhs, and the rhs's `has_select_fields` / `select` flip when an
implicitly-selected subquery is normalized to its identity (`pk`) column.

The collaborators (`lhs`, `rhs`) are lightweight stand-ins that faithfully model
the real `Query` semantics the method depends on (A-reference, cited in
mapping.md):
  * `lhs.get_group_by_cols()`            -> the lhs grouping columns, collected verbatim
  * `rhs.get_group_by_cols()`            -> patch-invariant grouping contribution
  * `rhs.has_select_fields`              -> bool(select or masks)  (query.py:243-245)
  * `rhs.clear_select_clause()`          -> select=()             (query.py:1861)
  * `rhs.add_fields(['pk'])`             -> set_select([pk])       (query.py:1893)
The METHOD UNDER TEST (its branch + the two mutations it performs) is the REAL
unmodified `In.get_group_by_cols`. Exit 0 iff zero disagreements.
stdlib only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5

PK = -1  # sentinel column id standing for the identity ('pk') column


# ---- faithful Query-state collaborator (A-reference per query.py) -----------

class FakeQuery:
    """Models the touched state of a nested-query rhs. `clear_select_clause` and
    `add_fields` reproduce query.py semantics exactly."""
    def __init__(self, explicitly_selected, selected, default_columns, group_keys):
        self._explicitly_selected = explicitly_selected
        self.select = tuple(selected)
        self.annotation_select_mask = None
        self.extra_select_mask = None
        self.default_columns = list(default_columns)
        self.group_keys = list(group_keys)

    @property
    def has_select_fields(self):
        # query.py:243-245
        return bool(self.select or self.annotation_select_mask or self.extra_select_mask)

    def clear_select_clause(self):
        # query.py:1861 (only the parts that affect has_select_fields / select)
        self.select = ()
        self.annotation_select_mask = None
        self.extra_select_mask = None

    def add_fields(self, field_names):
        # query.py:1893 -> set_select([pk]); we only ever receive ['pk']
        assert list(field_names) == ['pk']
        self.select = (PK,)

    def get_group_by_cols(self, alias=None):
        return list(self.group_keys)


class FakeLhs:
    def __init__(self, cols):
        self.cols = list(cols)

    def get_group_by_cols(self, alias=None):
        return list(self.cols)


class PlainRhs:
    """A non-subquery rhs: it has NO get_group_by_cols, so hasattr() is False."""
    def __init__(self, cols):
        self.cols = list(cols)


def observe_state(rhs):
    """Snapshot the rhs subquery selection state as a comparable tuple, or None
    for a non-subquery rhs."""
    if not hasattr(rhs, 'get_group_by_cols'):
        return None
    return (bool(rhs.has_select_fields), tuple(rhs.select))


# ---- real callee observation ------------------------------------------------

def real(lhs_cols, rhs_spec):
    """Run the REAL patched In.get_group_by_cols against faithful collaborators.
    Returns (cols, rhs_state)."""
    from django.db.models.lookups import In
    lk = object.__new__(In)               # skip __init__ (get_prep_lookup)
    lk.lhs = FakeLhs(lhs_cols)
    if rhs_spec is None:
        lk.rhs = PlainRhs([])
    else:
        es, selected, defaults, gk = rhs_spec
        lk.rhs = FakeQuery(es, selected, defaults, gk)
    cols = lk.get_group_by_cols()
    return list(cols), observe_state(lk.rhs)


# ---- Python shadow of implementation_membershipGroupColumns -----------------

def shadow(lhs_cols, rhs_spec):
    """Transliteration of implementation_membershipGroupColumns. Returns
    (cols, rhs_state) in the SAME observable form as real()."""
    cols = list(lhs_cols)
    if rhs_spec is None:
        return cols, None
    explicitly_selected, selected, defaults, group_keys = rhs_spec
    sel = tuple(selected)
    if not explicitly_selected:
        # discard implicit selection, then select only the identity column
        sel = ()
        sel = (PK,)
    cols = cols + list(group_keys)
    # observable state mirrors has_select_fields = bool(select)
    rhs_state = (bool(sel), sel)
    return cols, rhs_state


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def rand_cols(n):
        return [rng.randint(0, 50) for _ in range(n)]

    cases = []  # each: (lhs_cols, rhs_spec)  rhs_spec=None | (es, selected, defaults, group_keys)

    # discrete catalogue ------------------------------------------------------
    cases.append(([1, 2], None))                                   # plain value rhs
    cases.append(([], None))
    # implicitly-selected subquery (the bug scenario): es=False, no select
    cases.append(([7], (False, [], [10, 11, 12, 13], [99])))
    cases.append(([], (False, [], [1, 2, 3, 4, 5, 6], [42])))
    # explicitly-selected subquery: es=True, must be left untouched
    cases.append(([7], (True, [3], [10, 11, 12], [99])))
    cases.append(([1, 2], (True, [5, 6], [9], [8])))
    # implicitly selected but empty group keys
    cases.append(([4], (False, [], [], [])))

    # randomized --------------------------------------------------------------
    for _ in range(N_RANDOM):
        kind = rng.randint(0, 2)
        lhs = rand_cols(rng.randint(0, 4))
        if kind == 0:
            cases.append((lhs, None))
        else:
            es = (kind == 2)
            selected = rand_cols(rng.randint(1, 3)) if es else []
            defaults = rand_cols(rng.randint(0, 6))
            gk = rand_cols(rng.randint(0, 3))
            cases.append((lhs, (es, selected, defaults, gk)))

    for lhs_cols, rhs_spec in cases:
        got = real(lhs_cols, rhs_spec)
        exp = shadow(lhs_cols, rhs_spec)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH lhs={lhs_cols} rhs={rhs_spec}: real={got!r} shadow={exp!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
