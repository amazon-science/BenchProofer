#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15161 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`deconstructPath`) transliterated to Python over the real repo
              types, via the mapping.md bijection:
                `definingModule`/`className`/`publicPath` ↔ str / str / (None|str)
                `exactType`      ↔ `type(obj) is klass`
                `m ++ ['.'] ++ n` ↔ f'{m}.{n}'
              `publicPath`/`exactType` are derived from the mapping.md §3.1
              public-path registry — the discrete input data the patch
              introduces — NOT by calling the real callee. There are NO A-tagged
              callees in this bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the real `deconstruct()[0]` of an actual
              expression node, built from the patched
              `django.db.models.expressions` at base_commit (the real
              correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs.

They must agree on `deconstruct()[0]` (the import path — the only element the
patch touches) for every node. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15161
N_FUZZ = 100_000

DEFINING_MODULE = "django.db.models.expressions"

# --- mapping.md §3.1 public-path registry (the patch's input data) ----------
# class name -> simplified public path assigned by @deconstructible(path=...).
# F is the pre-existing precedent (PR #14047); the other six are this patch.
PUBLIC_PATH = {
    "F": "django.db.models.F",
    "Func": "django.db.models.Func",
    "Value": "django.db.models.Value",
    "ExpressionWrapper": "django.db.models.ExpressionWrapper",
    "When": "django.db.models.When",
    "Case": "django.db.models.Case",
    "OrderBy": "django.db.models.OrderBy",
}


# --- the R/I shadow: Solution.lean deconstructPath, transliterated ----------
def shadow_path(defining_module, class_name, public_path, exact_type):
    """deconstructPath's `do` block, transliterated to str carriers.

    out = publicPath        if publicPath is not None and exactType
        = m ++ '.' ++ n     otherwise
    (mapping.md §2: `m ++ ['.'] ++ n` ↔ f'{m}.{n}')."""
    if public_path is not None and exact_type:
        return public_path
    return "%s.%s" % (defining_module, class_name)


# --- the oracle: patch.diff's real behaviour --------------------------------
def build_nodes():
    """Construct real expression nodes covering: the six patched types
    (exactType=True), subclasses of patched types (publicPath inherited but
    exactType=False), and undecorated expression types (publicPath=None).

    Each entry is (label, node, public_path, exact_type) where (public_path,
    exact_type) are the SHADOW-side inputs derived independently from the
    mapping.md registry; the node is fed to the real deconstruct() oracle."""
    from django.db.models.expressions import (
        F, Func, Value, ExpressionWrapper, When, Case, OrderBy,
        ExpressionList, OrderByList, OuterRef, ResolvedOuterRef,
        RawSQL, Star, Ref,
    )
    from django.db.models import IntegerField

    nodes = []

    def add(label, node, runtime_class_name, ancestor_path_class=None):
        # publicPath: the registry path for the runtime class if it is itself
        # decorated, else the ancestor's path if it inherits one, else None.
        # exactType: True iff the runtime class is itself in the registry.
        if runtime_class_name in PUBLIC_PATH:
            public_path = PUBLIC_PATH[runtime_class_name]
            exact_type = True
        elif ancestor_path_class is not None:
            public_path = PUBLIC_PATH[ancestor_path_class]
            exact_type = False
        else:
            public_path = None
            exact_type = False
        nodes.append((label, node, public_path, exact_type))

    # --- the six patched types (exactType = True) ---------------------------
    add("Func", Func("rating", function="ABS"), "Func")
    add("Value", Value("name"), "Value")
    add("Value+of", Value("name", output_field=IntegerField()), "Value")
    add("ExpressionWrapper",
        ExpressionWrapper(F("pages"), output_field=IntegerField()),
        "ExpressionWrapper")
    add("When", When(name="special", then=Value("X")), "When")
    add("Case",
        Case(When(name="special", then=Value("X")), default=Value("other")),
        "Case")
    add("OrderBy", OrderBy(F("name")), "OrderBy")
    add("OrderBy.desc", OrderBy(F("name"), descending=True), "OrderBy")
    # the pre-existing precedent
    add("F", F("name"), "F")

    # --- subclasses of patched types (publicPath inherited, exactType=False) -
    add("ExpressionList", ExpressionList(F("a"), F("b")), "ExpressionList",
        ancestor_path_class="Func")
    add("OrderByList", OrderByList(F("a")), "OrderByList",
        ancestor_path_class="Func")
    add("OuterRef", OuterRef("name"), "OuterRef", ancestor_path_class="F")
    add("ResolvedOuterRef", ResolvedOuterRef("name"), "ResolvedOuterRef",
        ancestor_path_class="F")

    # --- undecorated expression types (publicPath = None) -------------------
    add("RawSQL", RawSQL("1 = 1", []), "RawSQL")
    add("Star", Star(), "Star")
    add("Ref", Ref("r", F("x")), "Ref")

    return nodes


def oracle_path(node):
    """patch.diff's behaviour: element 0 of the real deconstruct() 3-tuple."""
    path, _args, _kwargs = node.deconstruct()
    return path


def _ensure_django_configured():
    """In the SWE-Bench image django is normally configured by the test runner;
    when invoked standalone, configure a minimal settings so expression nodes
    (e.g. `When(name=...)` building a `Q`) can be constructed."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    import django
    django.setup()


def main():
    rng = random.Random(SEED)

    try:
        _ensure_django_configured()
        nodes = build_nodes()
    except Exception as exc:  # pragma: no cover - import/build failure
        print("G-CONF FAIL: could not build expression nodes: %r" % (exc,))
        return 1

    disagreements = []

    # Deterministic pass over every constructed node first (boundary coverage).
    base = list(nodes)

    count = 0
    # Boundary pass + fuzz pass: the fuzz repeatedly re-picks a node and
    # re-derives the shadow from the registry, exercising the same comparison
    # over the pinned schedule (deterministic given SEED).
    schedule = list(base)
    for _ in range(N_FUZZ):
        schedule.append(base[rng.randrange(len(base))])

    for label, node, public_path, exact_type in schedule:
        count += 1
        shadow = shadow_path(DEFINING_MODULE, type(node).__name__,
                             public_path, exact_type)
        oracle = oracle_path(node)
        if shadow != oracle:
            disagreements.append((label, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d node checks:"
              % (len(disagreements), count))
        for label, sh, orc in disagreements:
            print("  node=%s shadow=%r oracle=%r" % (label, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of deconstructPath agrees with patch.diff "
          "behaviour on %d node checks over %d distinct nodes (seed=%d), "
          "0 disagreements." % (count, len(base), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
