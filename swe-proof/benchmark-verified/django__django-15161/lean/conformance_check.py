#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15161.

The bundle models ONE decision: the canonical import path produced as the first
component of an expression object's `deconstruct()` 3-tuple, as governed by the
`deconstruct` closure installed by the `deconstructible` class decorator
(`django/utils/deconstruct.py`). The modeled value is a PURE function of four
observables (mapping.md):

    simplified_path : str | None   (the `path` kwarg of @deconstructible)
    is_exact_type   : bool         (type(obj) is klass)
    obj_module      : str          (obj.__class__.__module__)
    obj_class_name  : str          (obj.__class__.__name__)

Patched rule (the closure):

    return (
        path if path and type(obj) is klass
        else f'{obj.__class__.__module__}.{name}',
        ...,
    )

Standing up the full migrations writer / Django app registry to drive a real
`deconstruct()` is heavy and unnecessary: the modeled value is this pure decision
over observables. So the ORACLE below is a faithful in-process replica that uses
the EXACT patched expression, and the SHADOW is the op-for-op transliteration of
`implementation_deconstructedPath` (per refinement.md).

stdlib-only. Pinned seed: 15161 (also in mapping.md).
"""
import random
import sys

SEED = 15161
N = 150_000


# --- ORACLE: faithful in-process replica of the patched closure --------------
def oracle_path(simplified_path, is_exact_type, obj_module, obj_class_name):
    # `path if path and type(obj) is klass else f'{module}.{name}'`
    # `path` truthy <=> a non-None, non-empty configured short path.
    if simplified_path and is_exact_type:
        return simplified_path
    return f'{obj_module}.{obj_class_name}'


# --- SHADOW of implementation_deconstructedPath (the R leg) ------------------
# Mirrors Solution.lean: match simplifiedPath with
#   | some p => if isExactType then p else qualifiedName module name
#   | none   => qualifiedName module name
# qualifiedName m n = m ++ "." ++ n.
def _qualified_name(obj_module, obj_class_name):
    return obj_module + "." + obj_class_name


def shadow_path(simplified_path, is_exact_type, obj_module, obj_class_name):
    if simplified_path is not None:          # `some p`
        if is_exact_type:
            return simplified_path
        return _qualified_name(obj_module, obj_class_name)
    return _qualified_name(obj_module, obj_class_name)


def disagree(sp, ie, m, n):
    got = oracle_path(sp, ie, m, n)
    want = shadow_path(sp, ie, m, n)
    if got != want:
        return ((sp, ie, m, n), got, want)
    return None


# The six patched classes and their configured short paths (gold patch.diff),
# plus their real fully-qualified location at base_commit.
REAL_CASES = [
    ("django.db.models.Func", "django.db.models.expressions", "Func"),
    ("django.db.models.Value", "django.db.models.expressions", "Value"),
    ("django.db.models.ExpressionWrapper",
     "django.db.models.expressions", "ExpressionWrapper"),
    ("django.db.models.When", "django.db.models.expressions", "When"),
    ("django.db.models.Case", "django.db.models.expressions", "Case"),
    ("django.db.models.OrderBy", "django.db.models.expressions", "OrderBy"),
]

MODULES = ["django.db.models.expressions", "django.db.models", "myapp.models",
           "", "a.b.c"]
NAMES = ["Func", "Value", "OrderBy", "Sub", "X", "", "MyExpr"]
# `path` is always either absent (None) or a non-empty dotted path string.
# Per the bijection (mapping.md), a falsy Python `path` (None or "") maps to Lean
# `none`; a truthy (non-empty) `path` maps to `some p`. We therefore fuzz `some`
# only over NON-EMPTY strings and represent the falsy case as None — feeding
# `some ""` would not correspond to any real configured path.
PATHS = [None, "django.db.models.Value", "django.db.models.Func",
         "django.db.models.expressions.Value", "x.Y"]


def _enumerate_edge():
    cases = []
    # The real F2P shape: direct instance of a patched class, exact type True ->
    # must select the short path; subclass (exact type False) -> fully-qualified.
    for short, mod, name in REAL_CASES:
        cases.append((short, True, mod, name))    # direct instance: short path
        cases.append((short, False, mod, name))   # subclass: fully-qualified
        cases.append((None, True, mod, name))     # bare decorator (prepatch)
        cases.append((None, False, mod, name))
        # short path that happens to equal the qualified name (no-op case)
        cases.append((mod + "." + name, True, mod, name))
    return cases


def main() -> int:
    checked = 0
    for sp, ie, m, n in _enumerate_edge():
        d = disagree(sp, ie, m, n)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        sp = rng.choice(PATHS)
        ie = rng.choice([True, False])
        m = rng.choice(MODULES)
        n = rng.choice(NAMES)
        d = disagree(sp, ie, m, n)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
