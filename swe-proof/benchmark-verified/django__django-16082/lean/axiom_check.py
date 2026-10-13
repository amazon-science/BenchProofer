#!/usr/bin/env python3
"""G-AX — validate the one A-reference deep model against the real callee.

The modeled function `_resolve_combined_type` accepts an operand class `C` for a
combinator slot class `S` exactly when `issubclass(C, S)`. We deep-model that test
as `kindMatches operand slot` over the finite numeric-kind lattice (refinement.md
row #4): `autoKind` matches an `integerKind` slot, otherwise match iff equal.

This script runs the REAL `issubclass` over every (operand, slot) pair of the
modeled numeric field classes and asserts it agrees with `kindMatches`, for the
operand kinds AND the slot kinds that actually appear in the registered numeric
rows.

It also validates the deep-modeled row set (`combosFor`) against the REAL
registered rows — but ONLY for the parts the patch does NOT change, because G-AX
runs against the repo AT base_commit (no gold patch applied). Concretely
(SPEC_GUIDE §0.7 — never validate the changed op against the pre-change callee):

  * For every operator the patch leaves UNCHANGED (add, sub, mul, div, powOp),
    the base registered rows must equal `combosFor(op)` exactly.
  * The patch's only edit is adding mixed-kind promotion rows to the remainder
    operator. For that operator we validate the UNCHANGED portion — its base
    registered rows must equal the same-kind rows the deep model attributes to it
    (`sameKindRows`) — AND we confirm the mixed-kind rows are genuinely ABSENT at
    base (i.e. the bug the patch fixes is real). The post-patch mixed-kind MOD
    rows are validated separately by G-CONF against the patched repo; asserting
    them here (against base) would be validating the changed op against the
    pre-change callee, which §0.7 forbids.

stdlib-only (+ Django, which is the repo under test). exit 0 iff sound.
"""
import json
import sys


# FieldKind <-> real Django field class
def field_classes():
    from django.db.models import fields as F
    return {
        "integerKind": F.IntegerField,
        "floatKind": F.FloatField,
        "decimalKind": F.DecimalField,
        "autoKind": F.AutoField,
    }


# The Lean `kindMatches operand slot`.
def kind_matches(operand: str, slot: str) -> bool:
    if operand == "autoKind" and slot == "integerKind":
        return True
    return operand == slot


# combosFor (registration order): same-kind rows then mixed-kind rows.
SAME_KIND_ROWS = [
    ("integerKind", "integerKind", "integerKind"),
    ("floatKind", "floatKind", "floatKind"),
    ("decimalKind", "decimalKind", "decimalKind"),
]
MIXED_KIND_ROWS = [
    ("integerKind", "decimalKind", "decimalKind"),
    ("decimalKind", "integerKind", "decimalKind"),
    ("integerKind", "floatKind", "floatKind"),
    ("floatKind", "integerKind", "floatKind"),
]
SAME_KIND_OPS = {"add", "sub", "mul", "div", "modOp", "powOp"}
MIXED_KIND_OPS = {"add", "sub", "mul", "div", "modOp"}

# The single operator whose registered rows the patch CHANGES (adds the
# mixed-kind promotion rows to the remainder operator). Its post-patch row set is
# validated by G-CONF against the patched repo, NOT here against base_commit.
CHANGED_OP = "modOp"


def combos_for(op: str):
    rows = []
    if op in SAME_KIND_OPS:
        rows += SAME_KIND_ROWS
    if op in MIXED_KIND_OPS:
        rows += MIXED_KIND_ROWS
    return rows


def base_expected_rows(op: str):
    """The rows the deep model attributes to `op` that are UNCHANGED by the patch,
    i.e. what must already be registered at base_commit. For the changed operator
    that is only the same-kind portion; for every other operator it is the full
    `combos_for(op)`."""
    if op == CHANGED_OP:
        return list(SAME_KIND_ROWS)
    return combos_for(op)


# ArithOp <-> Combinable connector string
def op_connectors():
    from django.db.models.expressions import Combinable
    return {
        "add": Combinable.ADD,
        "sub": Combinable.SUB,
        "mul": Combinable.MUL,
        "div": Combinable.DIV,
        "modOp": Combinable.MOD,
        "powOp": Combinable.POW,
    }


def class_to_kind(cls, classes):
    for k, c in classes.items():
        if c is cls:
            return k
    return None


def main() -> int:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={},
        )
    django.setup()

    from django.db.models.expressions import _connector_combinators

    classes = field_classes()
    kinds = list(classes.keys())

    failures = []
    checks = 0

    # (1) kindMatches == issubclass over every (operand, slot) pair of modeled kinds.
    for operand in kinds:
        for slot in kinds:
            real = issubclass(classes[operand], classes[slot])
            model = kind_matches(operand, slot)
            checks += 1
            if real != model:
                failures.append(
                    f"kindMatches({operand},{slot})={model} != issubclass={real}"
                )

    # (2) The registered rows for each modeled operator, restricted to modeled
    #     numeric kinds, equal the UNCHANGED-by-the-patch expectation at base
    #     (registration order preserved). For unchanged operators that is the full
    #     combos_for(op); for the changed operator (remainder) it is only the
    #     same-kind portion — its added mixed-kind rows are a G-CONF concern.
    conns = op_connectors()
    for op, conn in conns.items():
        real_rows = []
        for (lhs, rhs, res) in _connector_combinators.get(conn, ()):
            lk, rk, rsk = (
                class_to_kind(lhs, classes),
                class_to_kind(rhs, classes),
                class_to_kind(res, classes),
            )
            # keep only rows entirely within the modeled numeric kinds
            if lk and rk and rsk:
                real_rows.append((lk, rk, rsk))
        expected = base_expected_rows(op)
        checks += 1
        if real_rows != expected:
            failures.append(
                f"base rows for {op}={real_rows} != unchanged-expected={expected}"
            )

    # (3) Confirm the bug the patch fixes is genuinely present at base_commit:
    #     the changed operator must have NO mixed-kind promotion row registered
    #     yet. (This asserts absence at base — it does not validate the changed
    #     op's post-patch behavior, which G-CONF owns.)
    changed_conn = conns[CHANGED_OP]
    base_changed_rows = []
    for (lhs, rhs, res) in _connector_combinators.get(changed_conn, ()):
        lk, rk, rsk = (
            class_to_kind(lhs, classes),
            class_to_kind(rhs, classes),
            class_to_kind(res, classes),
        )
        if lk and rk and rsk:
            base_changed_rows.append((lk, rk, rsk))
    checks += 1
    leaked = [row for row in base_changed_rows if row in MIXED_KIND_ROWS]
    if leaked:
        failures.append(
            f"{CHANGED_OP} already has mixed-kind rows at base={leaked}; "
            "the modeled bug is not present pre-patch"
        )

    ok = not failures
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "checks": checks,
        "failures": failures[:20],
        "note": "kindMatches deep-models issubclass (validated over all pairs); "
                "combosFor deep-models the registered rows, validated at base for "
                "unchanged ops and the unchanged (same-kind) portion of the changed "
                "op. The added mixed-kind MOD promotion is validated by G-CONF vs "
                "the patched repo, never here vs base (SPEC_GUIDE §0.7).",
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
