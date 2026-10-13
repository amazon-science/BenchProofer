#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8459 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the recorded ordered mapping:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (via the mapping.md
              bijection: ordered params ↔ `List Param`, `dict` ↔ assoc list,
              `param.empty`/`sig.empty` ↔ `none`, `autodoc_type_aliases` ↔
              `aliases`). The renderer callee (`inspect.signature(obj,
              type_aliases=·)` + `typing.stringify`) is the free input
              `renderType`; it is NOT substituted here — it is left as the REAL
              callee applied to the configured `aliases`, exactly as in the
              oracle. G-CONF therefore isolates the loop STRUCTURE: ordered
              iteration, skip-unannotated parameters, the constant `'return'`
              key, the return entry recorded last.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sphinx.ext.autodoc.typehints.record_typehints` (which calls
              `inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)`)
              run directly at base_commit with the gold patch applied.

They must agree on the recorded `(name, type_string)` sequence for every fuzzed
`(callable, alias-map)` pair. Exit 0 iff zero disagreements; any disagreement is
a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sphinx only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import types
from collections import OrderedDict

from sphinx.ext.autodoc.typehints import record_typehints  # patched callee
from sphinx.util import inspect as sphinx_inspect
from sphinx.util import typing as sphinx_typing

SEED = 8459
N_FUZZ = 100_000

# Annotation tokens (used as forward-ref strings under `from __future__ import
# annotations`). A mix of builtins, typing constructs, and alias-like names.
_ANNOTS = ["int", "str", "float", "bool", "bytes",
           "List[int]", "Dict[str, Any]", "Optional[int]",
           "JSONObject", "myint", "Alias0", "Alias1", "MyType"]
# Candidate alias targets the configured map may bind names to.
_TARGETS = ["int", "str", "types.JSONObject", "myint", "mod.MyType",
            "Dict[str, Any]", "builtins.int"]
_PARAM_NAMES = ["a", "b", "c", "d", "e", "data", "x", "y", "value", "n"]


def make_callable(rng):
    """Build a function with a random parameter/return annotation pattern.

    Uses `from __future__ import annotations` so every annotation is a string
    (forward ref); resolution via `type_aliases` is exercised by both sides
    identically. Returns (obj, source) — source is cached by the caller."""
    nparams = rng.randint(0, 5)
    names = rng.sample(_PARAM_NAMES, nparams) if nparams else []
    parts = []
    for nm in names:
        if rng.random() < 0.7:                      # 70% annotated
            parts.append("%s: '%s'" % (nm, rng.choice(_ANNOTS)))
        else:                                       # 30% bare (no annotation)
            parts.append(nm)
    ret = ""
    if rng.random() < 0.6:                          # 60% have a return annot
        ret = " -> '%s'" % rng.choice(_ANNOTS)
    return "from __future__ import annotations\ndef _f(%s)%s:\n    pass\n" % (
        ", ".join(parts), ret)


def random_aliases(rng):
    """A configured autodoc_type_aliases map (possibly empty)."""
    k = rng.randint(0, 4)
    keys = rng.sample(_ANNOTS, min(k, len(_ANNOTS)))
    return {key: rng.choice(_TARGETS) for key in keys}


def build_obj(source):
    ns = {}
    exec(compile(source, "<fuzz>", "exec"), ns, ns)
    return ns["_f"]


def shadow_record(obj, aliases):
    """R/I shadow of recordParamTypes: the loop structure of Solution.lean's
    impl region, with the renderer left as the REAL callee applied to the
    configured `aliases` (the free input `renderType aliases`). The `try/except
    (TypeError, ValueError)` mirrors record_typehints exactly, so the only thing
    being differentially tested is the loop STRUCTURE, not the (shared) renderer
    or its exceptions."""
    out = []
    try:
        sig = sphinx_inspect.signature(obj, type_aliases=aliases)  # real renderer
        for param in sig.parameters.values():
            if param.annotation is not param.empty:
                out.append((param.name, sphinx_typing.stringify(param.annotation)))
        if sig.return_annotation is not sig.empty:
            out.append(("return", sphinx_typing.stringify(sig.return_annotation)))
    except (TypeError, ValueError):
        pass
    return out


def oracle_record(obj, aliases, name="target.fn"):
    """patch.diff's behaviour: the patched record_typehints, run against a
    minimal app carrying the configured alias map."""
    app = types.SimpleNamespace(
        config=types.SimpleNamespace(autodoc_type_aliases=aliases),
        env=types.SimpleNamespace(temp_data={}),
    )
    record_typehints(app, "function", name, obj, {}, "", "")
    recorded = app.env.temp_data.get("annotations", {}).get(name, OrderedDict())
    return list(recorded.items())


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    cache = {}
    for _ in range(N_FUZZ):
        count += 1
        source = make_callable(rng)
        aliases = random_aliases(rng)
        obj = cache.get(source)
        if obj is None:
            obj = build_obj(source)
            cache[source] = obj
        try:
            shadow = shadow_record(obj, aliases)
            oracle = oracle_record(obj, aliases)
        except Exception as exc:                    # both sides share the
            # renderer; an exception in the oracle is swallowed by
            # record_typehints (except TypeError/ValueError -> pass), so a
            # raised exception here is a shadow-only divergence worth recording.
            disagreements.append((source, aliases, "EXC:%r" % exc, None))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((source, aliases, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for src, al, sh, orc in disagreements:
            print("  src=%r aliases=%r shadow=%r oracle=%r"
                  % (src, al, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of recordParamTypes agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
