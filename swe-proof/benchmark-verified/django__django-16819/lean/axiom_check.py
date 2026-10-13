#!/usr/bin/env python3
"""G-AX for django__django-16819 — validates the lone A-reference `baseReduce`.

The bundle consumes NO callee *axiom* (`meta.json axioms = []`): the proof of
`correct_reduceAddIndex` closes by a case split + `rfl` and uses no property of
`baseReduce`. `baseReduce` is an **A-reference**: it models `super().reduce` ==
the UNCHANGED generic `Operation.reduce` (django/db/migrations/operations/base.py),
which the added `AddIndex.reduce` delegates to in its else-branch.

This check validates that A-reference against the REAL callee on the BASE source
(no patch applied — `AddIndex` has no `reduce` override yet, so `AddIndex.reduce`
*is* the inherited `Operation.reduce`). We confirm two soundness facts the model
relies on:

  (1) The fallback the patched else-branch defers to is exactly the unchanged
      `Operation.reduce(self, operation, app_label)` — i.e. modeling it as an
      opaque reference invoked on the same two operations is faithful.
  (2) `Operation.reduce` is TOTAL (never raises) and returns only one of the
      modeled outcomes — a `list` (`ReduceResult.replace`) or `False`
      (`ReduceResult.cannot`) — so the opaque (value-unconstrained) reference is
      sound: the proof may consume no property of it.

stdlib-only (plus Django, present in the task image). Boundary + fuzz.
Pinned seed: 16819.
"""
import json
import random
import sys

SEED = 16819


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
    django.setup()


def main() -> int:
    try:
        _setup_django()
        from django.db.migrations.operations.base import Operation
        from django.db.migrations.operations.models import AddIndex, RemoveIndex
        from django.db.models import Index
    except Exception as e:  # pragma: no cover
        print(json.dumps({"status": "fail", "instance": "django__django-16819",
                          "reason": f"setup failed: {e!r}"}))
        return 1

    rng = random.Random(SEED)
    checked = 0

    def make_add(name):
        return AddIndex("Pony", Index(fields=["weight", "pink"], name=name))

    def make_remove(name):
        return RemoveIndex("Pony", name)

    # A pool of "following operations" the reduction may be asked about. On base
    # source these are the only operations whose reduce-interaction we model.
    def make_other_ops(idx_name):
        return [
            make_remove(idx_name),              # same-name remove (guard branch)
            make_remove(idx_name + "_x"),        # different-name remove (else branch)
            make_add(idx_name),                  # an add-index (else branch)
            make_remove("other"),                # unrelated remove (else branch)
        ]

    # add-index names must be non-empty (AddIndex.__init__ rejects empty names);
    # remove-index targets may be any string, including "".
    names = ["idx_pony_weight_pink", "a", "idx", "Z" * 30]
    app_labels = ["app", "migrations", ""]

    try:
        for nm in names:
            add = make_add(nm)
            for op in make_other_ops(nm):
                for app in app_labels:
                    # (1)+(2): the real base reducer is total and the inherited
                    # AddIndex.reduce on base source IS Operation.reduce.
                    base_res = Operation.reduce(add, op, app)
                    inherited_res = add.reduce(op, app)  # base source: no override
                    if base_res != inherited_res:
                        print(json.dumps({
                            "status": "fail", "instance": "django__django-16819",
                            "reason": f"inherited AddIndex.reduce != Operation.reduce "
                                      f"for op={op!r}: {inherited_res!r} vs {base_res!r}"}))
                        return 1
                    # outcome shape must be a list or False (the two modeled cases)
                    if not (base_res is False or isinstance(base_res, list)):
                        print(json.dumps({
                            "status": "fail", "instance": "django__django-16819",
                            "reason": f"unexpected reduce outcome shape: {base_res!r}"}))
                        return 1
                    checked += 1

        # Fuzz the only attribute the base reducer actually inspects: elidability.
        for _ in range(50_000):
            nm = rng.choice(names)
            add = make_add(nm)
            op = make_remove(rng.choice([nm, nm + "_x", "other"]))
            app = rng.choice(app_labels)
            add.elidable = bool(rng.getrandbits(1))
            op.elidable = bool(rng.getrandbits(1))
            res = Operation.reduce(add, op, app)
            # documented contract of the unchanged base reducer (base.py:128-138)
            if add.elidable:
                expected = [op]
            elif op.elidable:
                expected = [add]
            else:
                expected = False
            if res != expected:
                print(json.dumps({
                    "status": "fail", "instance": "django__django-16819",
                    "reason": f"Operation.reduce contract violated: "
                              f"self.elidable={add.elidable} op.elidable={op.elidable} "
                              f"-> {res!r}, expected {expected!r}"}))
                return 1
            checked += 1
    except Exception as e:
        print(json.dumps({"status": "fail", "instance": "django__django-16819",
                          "reason": f"callee raised (model assumes total): {e!r}"}))
        return 1

    print(json.dumps({
        "status": "pass", "instance": "django__django-16819",
        "checked": checked,
        "reason": "A-reference baseReduce validated == real Operation.reduce "
                  "(total, list/False outcomes; inherited AddIndex.reduce on base "
                  "source IS Operation.reduce)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
