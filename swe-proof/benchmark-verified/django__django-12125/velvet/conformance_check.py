#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12125 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of the type-reference dispatch
modeled in Solution.lean (`typeReference` / `renderRef`). There are NO axioms in
this bundle: every op is closed string/Option construction over facts read off
the input type value, so the whole impl region is R/I-tagged (conf_skip=false).

  * SHADOW  — Solution.lean's `renderRef` transliterated to Python over the real
              repo types, via the mapping.md §2 bijection:
                  isSentinelBase <-> self.value is models.Model
                  isNoneType     <-> self.value is type(None)
                  isBuiltin      <-> self.value.__module__ == builtins.__name__
                  module         <-> self.value.__module__
                  qualified      <-> self.value.__qualname__
                  bare           <-> self.value.__name__
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.

  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `django.db.migrations.serializer.TypeSerializer.serialize`, applied
              at base_commit (the harness applies patch.diff before this runs).
              We feed it genuine `type` objects with controlled
              __module__/__qualname__/__name__ (built via `type(...)` and real
              nested-class definitions), plus the genuine `models.Model`,
              `type(None)`, and a builtin (`int`), and compare the returned
              `(string, imports)` tuple.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container (the prebuilt
SWE-Bench instance image), stdlib + django only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import builtins
import random
import sys

SEED = 12125
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean `renderRef` transliterated ----------------------

def shadow_render(is_sentinel_base, is_none_type, is_builtin,
                  module, qualified, bare):
    """renderRef: priority dispatch over the facts read off the type value.
    Returns (expr, imports_set) to match the repo's (string, set) tuple."""
    if is_sentinel_base:
        return ("models.Model", set())
    if is_none_type:
        return ("type(None)", set())
    if is_builtin:
        return (bare, set())
    return ("%s.%s" % (module, qualified), {"import %s" % module})


# ---- ORACLE: real patched TypeSerializer.serialize -------------------------

def oracle_serialize(type_obj):
    """patch.diff's behaviour: the real patched TypeSerializer over a genuine
    type object. Returns (string, imports_set)."""
    from django.db.migrations.serializer import serializer_factory
    string, imports = serializer_factory(type_obj).serialize()
    return (string, set(imports))


def facts_of(type_obj):
    """Read the mapping.md §2 facts off a genuine type object, exactly the way
    the modeled function does."""
    from django.db import models
    is_sentinel_base = type_obj is models.Model
    is_none_type = type_obj is type(None)
    has_module = hasattr(type_obj, "__module__")
    module = type_obj.__module__ if has_module else None
    is_builtin = has_module and module == builtins.__name__
    qualified = getattr(type_obj, "__qualname__", None)
    bare = getattr(type_obj, "__name__", None)
    return (is_sentinel_base, is_none_type, is_builtin, module, qualified, bare)


# ---- input space: genuine type objects -------------------------------------

def build_types(rng):
    """Construct genuine `type` objects exercising every branch, including
    nested classes (where __qualname__ != __name__ — the patched case)."""
    from django.db import models

    types_under_test = []

    # special cases
    types_under_test.append(models.Model)          # isSentinelBase
    types_under_test.append(type(None))            # isNoneType
    # builtins (module == 'builtins')
    types_under_test += [int, str, float, list, dict, bool, bytes]

    # a genuine top-level class (qualname == name)
    class TopLevel:
        pass
    types_under_test.append(TopLevel)

    # genuine nested classes (qualname includes the enclosing scope; this is the
    # F2P case where the patch matters: name='Inner', qualname='Outer.Inner').
    class Outer:
        class Inner:
            pass
        class Middle:
            class Deep:
                pass
    types_under_test.append(Outer)
    types_under_test.append(Outer.Inner)
    types_under_test.append(Outer.Middle)
    types_under_test.append(Outer.Middle.Deep)

    # synthesize many types with controlled module/qualname/name via type():
    # type(name, bases, ns) sets __name__ == __qualname__ == name and
    # __module__ to the caller's module; override __qualname__/__module__ to
    # simulate nested + cross-module placements the serializer must handle.
    mod_pool = ["app.models", "migrations.test_writer", "some.deep.pkg",
                "builtins", "a", "x.y.z.w"]
    name_pool = ["Inner", "State", "Foo", "Bar", "Choices", "NestedEnum", "T"]
    encl_pool = ["", "Outer", "WriterTests", "A.B", "Thing", "Outer.Middle"]
    for _ in range(N_FUZZ):
        nm = rng.choice(name_pool)
        encl = rng.choice(encl_pool)
        mod = rng.choice(mod_pool)
        t = type(nm, (), {})
        t.__module__ = mod
        t.__qualname__ = ("%s.%s" % (encl, nm)) if encl else nm
        # __name__ stays nm (the bare component) — set explicitly for clarity
        t.__name__ = nm
        types_under_test.append(t)

    return types_under_test


def main():
    rng = random.Random(SEED)
    try:
        types_under_test = build_types(rng)
    except Exception as e:  # pragma: no cover
        print("G-CONF ERROR: could not build type objects: %r" % e)
        return 2

    disagreements = []
    count = 0
    for t in types_under_test:
        count += 1
        try:
            oracle = oracle_serialize(t)
        except Exception as e:
            disagreements.append((t, "<oracle raised %r>" % e, None))
            if len(disagreements) >= 8:
                break
            continue
        shadow = shadow_render(*facts_of(t))
        if shadow != oracle:
            disagreements.append((getattr(t, "__qualname__", t), shadow, oracle))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d type objects "
              "(seed=%d):" % (len(disagreements), count, SEED))
        for who, sh, orc in disagreements:
            print("  type=%r shadow=%r oracle=%r" % (who, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of typeReference agrees with patch.diff "
          "behaviour on %d genuine type objects (seed=%d), 0 disagreements "
          "(general values named by module + FULL qualified location)."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
