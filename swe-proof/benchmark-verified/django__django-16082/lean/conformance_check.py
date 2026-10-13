#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_resolveCombinedType against the post-patch repo behaviour.

The impl region is R/I plus one A-reference (`kindMatches` deep-models
`issubclass`, validated separately by G-AX). For the differential test we build
the R/I shadow op-for-op — scan the registered rows for the operator (same-kind
then mixed-kind, the patched set) and return the first whose two slots both
accept the operand kinds under `kindMatches` — and diff it against the REAL
post-patch `_resolve_combined_type` over every operator × operand-kind pair, then
over >=10^5 fuzzed inputs (operators × the four numeric field kinds for both
slots). Zero disagreements required.

stdlib-only (+ Django, the repo under test). exit 0 iff zero disagreements.
"""
import json
import random
import sys

SEED = 16082          # pinned in mapping.md
N = 120_000           # >= 10^5

# FieldKind names <-> Django classes filled at runtime.
KINDS = ["integerKind", "floatKind", "decimalKind", "autoKind"]
OPS = ["add", "sub", "mul", "div", "modOp", "powOp"]

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


def kind_matches(operand: str, slot: str) -> bool:
    if operand == "autoKind" and slot == "integerKind":
        return True
    return operand == slot


def combos_for(op: str):
    rows = []
    if op in SAME_KIND_OPS:
        rows += SAME_KIND_ROWS
    if op in MIXED_KIND_OPS:
        rows += MIXED_KIND_ROWS
    return rows


def shadow(op: str, lhs: str, rhs: str):
    """R/I shadow of implementation_resolveCombinedType -> kind name or None."""
    for (clhs, crhs, combined) in combos_for(op):
        if kind_matches(lhs, clhs) and kind_matches(rhs, crhs):
            return combined
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

    from django.db.models import fields as F
    from django.db.models.expressions import _resolve_combined_type, Combinable

    classes = {
        "integerKind": F.IntegerField,
        "floatKind": F.FloatField,
        "decimalKind": F.DecimalField,
        "autoKind": F.AutoField,
    }
    conns = {
        "add": Combinable.ADD,
        "sub": Combinable.SUB,
        "mul": Combinable.MUL,
        "div": Combinable.DIV,
        "modOp": Combinable.MOD,
        "powOp": Combinable.POW,
    }

    def real(op, lhs, rhs):
        res = _resolve_combined_type(conns[op], classes[lhs], classes[rhs])
        if res is None:
            return None
        for k, c in classes.items():
            if res is c:
                return k
        # result outside modeled kinds — treat as a distinct sentinel
        return f"OTHER:{res.__name__}"

    disagreements = 0
    examples = []

    def check(op, lhs, rhs):
        nonlocal disagreements
        s = shadow(op, lhs, rhs)
        r = real(op, lhs, rhs)
        if s != r:
            disagreements += 1
            if len(examples) < 20:
                examples.append({"op": op, "lhs": lhs, "rhs": rhs,
                                 "shadow": s, "real": r})

    # Exhaustive over operators × kind × kind (24*... small).
    for op in OPS:
        for lhs in KINDS:
            for rhs in KINDS:
                check(op, lhs, rhs)

    # Fuzz to >=10^5.
    rng = random.Random(SEED)
    for _ in range(N):
        check(rng.choice(OPS), rng.choice(KINDS), rng.choice(KINDS))

    ok = disagreements == 0
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "inputs": len(OPS) * len(KINDS) * len(KINDS) + N,
        "disagreements": disagreements,
        "examples": examples,
        "seed": SEED,
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
