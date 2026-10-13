#!/usr/bin/env python3
"""G-CONF for django__django-15268.

Mechanical differential test of the R/I legs of `implementation_canOptimizeAcross`
against the REAL patched behaviour of
`AlterTogetherOptionOperation.can_reduce_through`.

The Lean impl is:
    base || (isAlterTogether op.ty && op.ty != kindTag selfKind)
where `base = !(affectsModel op selfName)` is the A-reference leg — left as the
REAL repo callee `operation.references_model(self.name, app_label)`.

We build that shadow in Python (rows 1-5 of refinement.md), then diff it against
the real `can_reduce_through` over >=1e5 fuzzed inputs. Exit 0 iff zero
disagreements. stdlib-only (+ the in-container django under test).

mapping.md type bijection:
  selfKind unique/index  <-> type(self) is AlterUniqueTogether/AlterIndexTogether
  op.ty alterUnique/alterIndex/other
                         <-> isinstance exact-type of operation
  affectsModel op name   <-> operation.references_model(name, app_label)  (Bool)
"""
import random
import sys

SEED = 15268          # pinned (mapping.md)
N = 120_000           # >= 1e5 fuzzed inputs


def main() -> int:
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(INSTALLED_APPS=[], DATABASES={})
        django.setup()
        from django.db.migrations.operations.models import (
            AlterUniqueTogether, AlterIndexTogether, AlterTogetherOptionOperation,
            DeleteModel, CreateModel,
        )
        from django.db.migrations.operations.base import Operation
    except Exception as e:  # pragma: no cover - environment guard
        print(f"G-CONF: cannot import django operations: {e}", file=sys.stderr)
        return 2

    rng = random.Random(SEED)
    names = ["book", "Book", "author", "MyModel", "mymodel", "tag", "x", ""]
    app_label = "otherapp"

    def make_self(kind, name):
        if kind == "unique":
            return AlterUniqueTogether(name=name, unique_together=set())
        return AlterIndexTogether(name=name, index_together=set())

    def make_op(ty, name):
        if ty == "alterUnique":
            return AlterUniqueTogether(name=name, unique_together=set())
        if ty == "alterIndex":
            return AlterIndexTogether(name=name, index_together=set())
        # "other": a non-alter-together operation that still references models.
        return DeleteModel(name=name)

    def shadow(self_op, operation):
        # row 1 (A-reference): real, unchanged callee
        base = not operation.references_model(self_op.name, app_label)
        # rows 2-3 (R): exact-type tags
        is_alter_together = isinstance(operation, AlterTogetherOptionOperation)
        diff_kind = type(operation) is not type(self_op)
        # rows 4-5 (I): boolean and / or
        return bool(base or (is_alter_together and diff_kind))

    mismatches = 0
    examples = []
    for _ in range(N):
        self_kind = rng.choice(["unique", "index"])
        self_name = rng.choice(names)
        op_ty = rng.choice(["alterUnique", "alterIndex", "other"])
        op_name = rng.choice(names)

        self_op = make_self(self_kind, self_name)
        operation = make_op(op_ty, op_name)

        got = shadow(self_op, operation)
        real = bool(self_op.can_reduce_through(operation, app_label))
        if got != real:
            mismatches += 1
            if len(examples) < 10:
                examples.append((self_kind, self_name, op_ty, op_name, got, real))

    if mismatches:
        print(f"G-CONF: {mismatches}/{N} disagreements", file=sys.stderr)
        for ex in examples:
            print(f"  selfKind={ex[0]} selfName={ex[1]!r} opTy={ex[2]} "
                  f"opName={ex[3]!r} shadow={ex[4]} real={ex[5]}", file=sys.stderr)
        return 1
    print(f"G-CONF: {N} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
