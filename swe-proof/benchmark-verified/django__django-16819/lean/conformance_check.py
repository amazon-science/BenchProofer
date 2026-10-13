#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16819.

The bundle models ONE decision: how an *add-index* migration operation reduces
against the operation that follows it (`AddIndex.reduce`, ADDED by the patch in
django/db/migrations/operations/models.py):

    def reduce(self, operation, app_label):
        if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
            return []
        return super().reduce(operation, app_label)

This script runs with the GOLD PATCH APPLIED in-container, so the REAL
`AddIndex.reduce` is the patched method. We differential-test:

  * ORACLE  = the real, patched `AddIndex.reduce(operation, app_label)`.
  * SHADOW  = the op-for-op transliteration of `implementation_reduceAddIndex`
              (Solution.lean): the added guard, with the else-branch left as the
              REAL `Operation.reduce` callee (the A-reference, per refinement.md —
              A legs keep the real repo callee in the shadow).

The modeled result is one of two outcomes (mapping.md bijection):
  * a `list` of operations  ↔ `ReduceResult.replace`
  * `False`                 ↔ `ReduceResult.cannot`
The annihilation outcome `[]` (empty list) is distinct from `False`. We compare
the oracle and shadow results structurally: kind (list vs False) must match, and
for the annihilation case the list must be empty.

Inputs fuzzed (mapping.md observation interface):
  * self.index.name        : the add-index's created index name
  * the following operation : a RemoveIndex(name) | another AddIndex | (rarely)
                              an operation with an elidable flag toggled
  * app_label
plus the elidable flags that the base `Operation.reduce` inspects.

stdlib-only (plus Django, present in the task image). Pinned seed: 16819.
"""
import random
import sys

SEED = 16819
N = 120_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
    django.setup()


def _result_key(res):
    """Normalize a reduce() result to a comparable key.
    False -> ('cannot',); a list -> ('replace', <len>, <repr of each op>)."""
    if res is False:
        return ("cannot",)
    if isinstance(res, list):
        # operations compare by their deconstruct() identity; for our pool the
        # length + each op's class/args suffices and matches Lean's structural eq.
        return ("replace", len(res), tuple(repr(o) for o in res))
    return ("other", repr(res))


def main() -> int:
    _setup_django()
    from django.db.migrations.operations.base import Operation
    from django.db.migrations.operations.models import AddIndex, RemoveIndex
    from django.db.models import Index

    def make_add(name, elidable=False):
        op = AddIndex("Pony", Index(fields=["weight", "pink"], name=name))
        op.elidable = elidable
        return op

    def make_remove(name, elidable=False):
        op = RemoveIndex("Pony", name)
        op.elidable = elidable
        return op

    def oracle(add, op, app):
        # The REAL patched AddIndex.reduce.
        return add.reduce(op, app)

    def shadow(add, op, app):
        # Transliteration of implementation_reduceAddIndex: the added guard,
        # else-branch = the REAL Operation.reduce (A-reference left as real callee).
        if isinstance(op, RemoveIndex) and add.index.name == op.name:
            return []
        return Operation.reduce(add, op, app)

    def disagree(add, op, app):
        g = _result_key(oracle(add, op, app))
        s = _result_key(shadow(add, op, app))
        if g != s:
            return (repr(add), repr(op), app, g, s)
        return None

    checked = 0

    # --- boundary / edge cases -------------------------------------------------
    edge = []
    # add-index names must be non-empty (AddIndex.__init__ rejects empty names).
    for nm in ["idx_pony_weight_pink", "a", "X" * 40]:
        edge.append((make_add(nm), make_remove(nm), "app"))            # F2P annihilation
        edge.append((make_add(nm), make_remove(nm + "_other"), "app")) # diff name -> base
        edge.append((make_add(nm), make_add(nm), "app"))               # following add -> base
        edge.append((make_add(nm, elidable=True), make_remove("z"), "app"))   # self elidable
        edge.append((make_add(nm), make_remove("z", elidable=True), "app"))   # op elidable
        edge.append((make_add(nm, elidable=True), make_remove(nm), "app"))    # elidable AND same-name (guard wins)
    for add, op, app in edge:
        d = disagree(add, op, app)
        if d:
            print(f"DISAGREE edge {d}")
            print("status=fail")
            return 1
        checked += 1

    # --- fuzz ------------------------------------------------------------------
    rng = random.Random(SEED)
    add_names = ["idx_pony_weight_pink", "a", "b", "idx", "Z" * 12]  # non-empty
    rm_names = ["idx_pony_weight_pink", "a", "b", "", "idx", "Z" * 12]
    apps = ["app", "migrations", ""]
    for _ in range(N):
        sn = rng.choice(add_names)
        add = make_add(sn, elidable=bool(rng.getrandbits(1)))
        # following op: mostly RemoveIndex (to exercise the guard both ways),
        # sometimes another AddIndex.
        if rng.random() < 0.75:
            op = make_remove(rng.choice(rm_names), elidable=bool(rng.getrandbits(1)))
        else:
            op = make_add(rng.choice(add_names), elidable=bool(rng.getrandbits(1)))
        app = rng.choice(apps)
        d = disagree(add, op, app)
        if d:
            print(f"DISAGREE fuzz {d}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
