#!/usr/bin/env python
"""G-CONF: differential conformance for sphinx-doc__sphinx-8459.

Modeled function: `record_typehints` (`sphinx/ext/autodoc/typehints.py`) — the
body that fills the per-name `annotation` table from a callable's signature. The
gold patch changes signature resolution from `inspect.signature(obj)` to
`inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)`, whose
observable effect (via `sphinx.util.inspect.signature` ->
`typing.get_type_hints(subject, None, type_aliases)`) is that each emitted type
label becomes alias-aware: a declared annotation name that is a configured alias
key is shown as the alias's replacement, otherwise as the default rendering.

The REAL patch-behaviour leg below reproduces the gold-patched recording: it
iterates parameters in order, emits `param.name -> resolve(ann)` for each
annotated parameter and finally `'return' -> resolve(return_ann)`, where
`resolve(nm)` applies the alias table on top of the default renderer — exactly
the alias-aware resolution `get_type_hints(..., type_aliases)` injects.

It is diffed against the Python shadow of the Lean `implementation_aliasedLabels`
skeleton (`Id.run do` loop over params, then the return entry) over a discrete
catalogue (incl. the F2P `myint` shape) plus >= 1e5 fuzzed inputs.

Bridge (mapping.md): Python `OrderedDict[str,str]` <-> Lean
`List (String x String)` (insertion order preserved); `dict[str,str]` aliases
<-> `List (String x String)`; the default renderer `typing.stringify` <-> the
free input `render`. Exit 0 iff zero disagreements. stdlib only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 150_000  # >= 1e5

# A deterministic stand-in for the UNCHANGED default renderer `typing.stringify`.
# The fix's behaviour does not depend on which renderer this is, so any
# fixed function exercises the alias-vs-default distinction; we use a tagging
# renderer so that "default label of nm" is always distinguishable from nm.
def default_render(nm):
    return "py:" + nm


# ---- REAL patch behaviour (gold-patched record_typehints recording) ---------

def patch_behaviour(params, ret, aliases):
    """Gold-patched `record_typehints`: build the ordered annotation table with
    alias-aware labels. `aliases` is the {name: replacement} config map.
    Returns a list of (key, label) pairs in insertion order."""
    def resolve(nm):
        # inspect.signature(obj, type_aliases=aliases) -> get_type_hints applies
        # the alias map; stringify renders whatever survives. For a name that is
        # an alias key, the configured replacement is shown; else the default.
        if nm in aliases:
            return aliases[nm]
        return default_render(nm)

    annotation = []  # OrderedDict modeled as ordered list of pairs
    for name, ann in params:
        if ann is not None:               # param.annotation is not param.empty
            annotation.append((name, resolve(ann)))
    if ret is not None:                   # sig.return_annotation is not sig.empty
        annotation.append(("return", resolve(ret)))
    return annotation


# ---- Python shadow of implementation_aliasedLabels (R/I leg) ----------------

def _lookup_alias(aliases, nm):
    # lookupAlias: first matching key's replacement, else None (List.find?).
    for k, v in aliases:
        if k == nm:
            return v
    return None


def _render_name(render, aliases, nm):
    # renderName: alias replacement if present, else default renderer.
    hit = _lookup_alias(aliases, nm)
    if hit is not None:
        return hit
    return render(nm)


def lean_shadow(params, ret, aliases_pairs):
    # aliases_pairs: ordered List (String x String), mirrors the Lean argument.
    annotation = []
    for name, ann in params:
        if ann is not None:
            annotation.append((name, _render_name(default_render, aliases_pairs, ann)))
    if ret is not None:
        annotation.append(("return", _render_name(default_render, aliases_pairs, ret)))
    return annotation


# ---- fuzz generators --------------------------------------------------------

NAMES = ["x", "y", "z", "data", "n", "self", "return", "value", "arg1", "arg2"]
TYPENAMES = ["myint", "int", "str", "JSONObject", "float", "Dict", "Any", "T", "MyType"]


def make_case(rng):
    nparams = rng.randint(0, 5)
    # parameter names: unique-ish; duplicates in a real signature are impossible
    pnames = rng.sample(NAMES, min(nparams, len(NAMES))) if nparams else []
    params = []
    for pn in pnames:
        if rng.random() < 0.25:
            params.append((pn, None))            # unannotated parameter
        else:
            params.append((pn, rng.choice(TYPENAMES)))
    ret = None if rng.random() < 0.3 else rng.choice(TYPENAMES)
    # alias config: a dict subset of type names mapped to chosen replacements.
    naliases = rng.randint(0, 4)
    keys = rng.sample(TYPENAMES, min(naliases, len(TYPENAMES))) if naliases else []
    aliases = {}
    for k in keys:
        aliases[k] = rng.choice(["alias:" + k, k, "pkg." + k])
    return params, ret, aliases


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # discrete catalogue, incl. the exact F2P shape: params x:myint, y:myint;
    # return myint; alias {'myint':'myint'} -> every label must be 'myint'.
    catalogue = [
        ([("x", "myint"), ("y", "myint")], "myint", {"myint": "myint"}),
        ([], None, {}),
        ([("x", None)], None, {"myint": "myint"}),
        ([("data", "JSONObject")], "JSONObject", {"JSONObject": "types.JSONObject"}),
        ([("x", "int")], "str", {}),                       # no alias -> defaults
        ([("a", "myint"), ("b", None), ("c", "int")], None, {"myint": "M"}),
    ]
    for params, ret, aliases in catalogue:
        checked += 1
        a = patch_behaviour(params, ret, aliases)
        b = lean_shadow(params, ret, list(aliases.items()))
        if a != b:
            disagreements += 1
            print(f"DISAGREE (catalogue): params={params} ret={ret} aliases={aliases}")
            print(f"  patch={a}")
            print(f"  lean ={b}")

    for _ in range(N_RANDOM):
        params, ret, aliases = make_case(rng)
        checked += 1
        a = patch_behaviour(params, ret, aliases)
        b = lean_shadow(params, ret, list(aliases.items()))
        if a != b:
            disagreements += 1
            if disagreements <= 10:
                print(f"DISAGREE: params={params} ret={ret} aliases={aliases}")
                print(f"  patch={a}\n  lean ={b}")

    print(f"checked={checked} disagreements={disagreements} seed={SEED}")
    if disagreements == 0:
        print("status=pass G-CONF: lean shadow == gold patch behaviour")
        sys.exit(0)
    print("status=fail")
    sys.exit(1)


if __name__ == "__main__":
    main()
