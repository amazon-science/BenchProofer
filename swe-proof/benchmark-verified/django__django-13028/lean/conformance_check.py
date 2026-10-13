#!/usr/bin/env python3
"""G-CONF for django__django-13028.

Mechanically differential-tests the R/I shadow of `implementation_checkFilterable`
(Solution.lean) against the *patched* behavior of `Query.check_filterable`
(patch.diff) over >=1e5 fuzzed inputs.

Both legs are R/I (no A-tagged callees), so the whole impl is shadowed:

  * `reference_patched(obj)` reconstructs the patched Python control flow exactly
    — `hasattr(obj,'resolve_expression') and not getattr(obj,'filterable',True)`
    triggers rejection; then recurse over `get_source_expressions()`. It runs on
    real Python objects whose attributes are set per the fuzzed facets, so the
    `hasattr`/`getattr`-default semantics are exercised for real (including the
    attribute-absent default `True`).
  * `lean_shadow(e)` is the Lean `raises`/`raisesAny` fold transliterated.

mapping.md bijection:
  isQueryExpr  <-> presence of a `resolve_expression` attribute
  filterable   <-> `filterable` attribute (absent => default True)
  children     <-> `get_source_expressions()` (absent => leaf)

Pinned seed: 13028. Exit 0 iff zero disagreements over N samples.
"""
import json
import random
import sys

SEED = 13028
N = 100_000
MAX_DEPTH = 4
MAX_CHILDREN = 4


# ---- fuzzed-tree representation (the abstract Expr) -------------------------
def gen_expr(rng, depth):
    is_query = rng.random() < 0.5
    # model "filterable attribute absent" as a third state mapped to default True
    f_state = rng.choice(["true", "false", "absent"])
    if depth <= 0:
        n_children = 0
    else:
        n_children = rng.randint(0, MAX_CHILDREN)
    children = [gen_expr(rng, depth - 1) for _ in range(n_children)]
    # has_source: whether the object exposes get_source_expressions at all.
    # When it has children it must expose it; when it has none we still randomly
    # decide presence (a method returning [] vs. no method) — both must behave
    # identically (the [].any / hasattr-false cases coincide).
    has_source = True if children else (rng.random() < 0.5)
    return {
        "is_query": is_query,
        "f_state": f_state,
        "children": children,
        "has_source": has_source,
    }


# ---- Lean shadow: raises / raisesAny ----------------------------------------
def _filterable_bool(node):
    # absent attribute defaults to True (admissible)
    return False if node["f_state"] == "false" else True


def lean_shadow(node):
    q = node["is_query"]
    f = _filterable_bool(node)
    if q and (not f):
        return True
    return any(lean_shadow(c) for c in node["children"])


# ---- patched-Python reference: build a real object and run the patched code -
class _Obj:
    pass


def build_obj(node):
    o = _Obj()
    if node["is_query"]:
        o.resolve_expression = lambda *a, **k: None
    if node["f_state"] == "true":
        o.filterable = True
    elif node["f_state"] == "false":
        o.filterable = False
    # f_state == "absent": do not set the attribute at all
    if node["has_source"]:
        kids = [build_obj(c) for c in node["children"]]
        o.get_source_expressions = lambda kids=kids: kids
    return o


def reference_patched(expression):
    """Faithful transliteration of patched Query.check_filterable; returns True
    iff a NotSupportedError would be raised (transitively)."""
    if hasattr(expression, "resolve_expression") and not getattr(
        expression, "filterable", True
    ):
        return True
    if hasattr(expression, "get_source_expressions"):
        for expr in expression.get_source_expressions():
            if reference_patched(expr):
                return True
    return False


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    first = None
    for i in range(N):
        node = gen_expr(rng, MAX_DEPTH)
        got_shadow = lean_shadow(node)
        got_ref = reference_patched(build_obj(node))
        if got_shadow != got_ref:
            disagreements += 1
            if first is None:
                first = {"i": i, "shadow": got_shadow, "ref": got_ref}
    status = "pass" if disagreements == 0 else "fail"
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "django__django-13028",
        "status": status,
        "samples": N,
        "seed": SEED,
        "disagreements": disagreements,
        "first_disagreement": first,
    }))
    return 0 if disagreements == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
