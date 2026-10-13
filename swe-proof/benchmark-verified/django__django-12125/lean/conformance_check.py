#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12125.

The bundle models ONE function: `TypeSerializer.serialize`
(`django/db/migrations/serializer.py`). Its Lean implementation
(`implementation_serializeType`) turns a class descriptor into its
`(reference, imports)` source pair:

    if is_model_base: return ("models.Model", [])
    if is_none_type:  return ("type(None)", [])
    if has_module:
        if module == "builtins": return (short_name, [])
        else:                    return (module + "." + full_name, ["import " + module])
    return None

This script transliterates that R/I impl into Python (`shadow_serialize`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `TypeSerializer.serialize`:

    special_cases = [(models.Model, "models.Model", []), (type(None), "type(None)", [])]
    for case, string, imports in special_cases:
        if case is self.value: return string, set(imports)
    if hasattr(self.value, "__module__"):
        module = self.value.__module__
        if module == builtins.__name__: return self.value.__name__, set()
        else: return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}
        #                                ^^^^^^^^^^^^^  the fix: __qualname__, not __name__

We do NOT stand up Django/the migration writer (heavy, and the modeled value is a
pure transformation of a class descriptor's attributes). Instead we reproduce the
patched serializer with a light stand-in descriptor: a tuple of the six observed
attributes (mapping.md). The descriptor's `__name__` (`short_name`) is the
unqualified leaf name and its `__qualname__` (`full_name`) is the fully-qualified
in-module path; for a top-level class they coincide, for a nested class
`full_name` carries the enclosing path. The post-patch oracle emits
`module.__qualname__`, so it agrees with the shadow's `module + "." + full_name`.

The differential genuinely tests the Lean modeling: the discriminating regime is
a non-builtins class whose `full_name != short_name` (a nested class) — pre-fix
the serializer dropped the enclosing path; post-fix `__qualname__` keeps it. Both
legs see the full descriptor and must agree everywhere.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 12125 (also recorded in
mapping.md).
"""
import sys

SEED = 12125
N = 120_000

BUILTINS = "builtins"


# --- ORACLE: the post-patch serialize, faithful in-process replica -----------
# `v` is a descriptor tuple:
#   (is_model_base, is_none_type, has_module, module, short_name, full_name)
# short_name <-> __name__, full_name <-> __qualname__ (post-patch uses qualname).
def oracle_serialize(v):
    is_model_base, is_none_type, has_module, module, short_name, full_name = v
    # special_cases, in order
    if is_model_base:
        return ("models.Model", set())
    if is_none_type:
        return ("type(None)", set())
    if has_module:
        if module == BUILTINS:
            return (short_name, set())
        else:
            return ("%s.%s" % (module, full_name), {"import %s" % module})
    return None


# --- shadow of implementation_serializeType (the R/I leg) --------------------
# Mirrors Solution.lean exactly. Imports modeled as a list; normalized to a set
# for comparison since at most one import is produced (mapping.md bijection).
def shadow_serialize(v):
    is_model_base, is_none_type, has_module, module, short_name, full_name = v
    if is_model_base:
        return ("models.Model", [])
    if is_none_type:
        return ("type(None)", [])
    if has_module:
        if module == BUILTINS:
            return (short_name, [])
        else:
            return (module + "." + full_name, ["import " + module])
    return None


def _norm(res):
    """Normalize a (string, imports) | None result to compare across legs."""
    if res is None:
        return None
    s, imports = res
    return (s, set(imports))


def disagree(v):
    got = _norm(oracle_serialize(v))
    want = _norm(shadow_serialize(v))
    if got != want:
        return (v, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning the discriminating qualname clause."""
    return [
        # THE fix: non-builtins nested class, full_name strictly longer than short_name
        (False, False, True, "migrations.test_writer", "NestedEnum", "WriterTests.NestedEnum"),
        (False, False, True, "migrations.test_writer", "NestedChoices", "WriterTests.NestedChoices"),
        (False, False, True, "test1.models", "Inner", "Outer.Inner"),
        # deeply nested (two enclosing scopes)
        (False, False, True, "a.b", "Leaf", "Top.Mid.Leaf"),
        # top-level class: full_name == short_name -> both impls agree
        (False, False, True, "migrations.test_writer", "Money", "Money"),
        (False, False, True, "decimal", "Decimal", "Decimal"),
        # builtins namespace -> leaf name, no import
        (False, False, True, BUILTINS, "int", "int"),
        (False, False, True, BUILTINS, "str", "str"),
        # special case 1: base model class (wins even if other flags set)
        (True, False, True, "django.db.models", "Model", "Model"),
        (True, True, True, "django.db.models", "Model", "Model"),  # priority: model base first
        # special case 2: null type
        (False, True, True, "builtins", "NoneType", "NoneType"),
        # no module -> implicit None
        (False, False, False, "", "Anon", "Anon"),
    ]


def _rand_token(rnd):
    n = 1 + (next(rnd) % 6)
    return "".join(chr(ord('a') + (next(rnd) % 26)) for _ in range(n))


def _rand_descriptor(rnd):
    is_model_base = (next(rnd) % 10) == 0
    is_none_type = (next(rnd) % 10) == 0
    has_module = (next(rnd) % 8) != 0  # mostly True, sometimes False (None branch)
    # module: sometimes the builtins namespace, otherwise a dotted module name
    if (next(rnd) % 4) == 0:
        module = BUILTINS
    else:
        module = _rand_token(rnd) + "." + _rand_token(rnd)
    short_name = _rand_token(rnd).capitalize()
    # full_name: half top-level (== short_name), half nested (enclosing prefix)
    if (next(rnd) % 2) == 0:
        full_name = short_name
    else:
        depth = 1 + (next(rnd) % 2)
        prefix = ".".join(_rand_token(rnd).capitalize() for _ in range(depth))
        full_name = prefix + "." + short_name
    return (is_model_base, is_none_type, has_module, module, short_name, full_name)


def main() -> int:
    checked = 0

    for v in _enumerate_edge():
        d = disagree(v)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        v = _rand_descriptor(rnd)
        d = disagree(v)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
