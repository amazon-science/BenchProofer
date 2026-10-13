#!/usr/bin/env python3
"""G-CONF for pydata__xarray-7229.

Differential-tests the R/I legs of `implementation_where` against the behaviour of
`patch.diff`, over >=1e5 fuzzed inputs, via the structural record model declared
in mapping.md. stdlib-only; exit 0 iff zero disagreements.

Model (mapping.md bijection):
  XObj  := {topAttrs: [[k,v]...], name: str|None, isContainer: bool,
            dataVars: [{name,attrs}...], coords: [{name,attrs}...],
            reserved: [[name, attrs]...]}
`reserved` is the object class's own attribute table, which Python consults
BEFORE the variable namespace on every `getattr(x, nm)`.
The opaque `select_combine` is an A-reference, identical on both legs; we model it
as a deterministic structural combine that -- like the real
apply_ufunc(..., keep_attrs=keep_attrs) -- takes the retention FLAG, and feed the
SAME combined result to both shadows, so the stand-in cancels. Under keep_attrs
False the real combine drops the merged bags (combine_attrs="drop"); under True it
overrides from the first argument ("override"), and the stand-in mirrors that
flag-dependence so the promotion branch's untouched data vars are exercised.

  * lean_shadow  — a faithful Python mirror of `implementation_where` (Solution.lean).
  * patch_shadow — a faithful Python mirror of the gold patch.diff post-combine
                   rebuild (computation.py:1879-1892).
They must agree on every fuzzed input.
"""
import json
import random
import sys

CONF_SEED = 7229
N = 120_000


def lookup_attrs(a, nm):
    """`getattr(getattr(a, nm, None), "attrs", {})` on the record model.

    Python resolves `getattr(obj, nm)` through the TYPE first: a class
    attribute/property/method of DataArray/Dataset answers and
    `Common.__getattr__` (which is what reaches the variable namespace) is never
    called. `reserved` carries exactly that per-class table -- the name paired
    with the `.attrs` of whatever the class-level answer is (`{}` for a method or
    a non-bag object, the object's OWN top-level bag for a whole-object view such
    as `.T`/`.real`/`.imag`/`.variable`). Only when the type does not answer does
    the lookup fall through to the variable namespace (`data_vars` then
    `coords`), and to `{}` when there is no such component either."""
    for nm_r, attrs_r in a["reserved"]:
        if nm_r == nm:
            return attrs_r
    for c in a["dataVars"] + a["coords"]:
        if c["name"] == nm:
            return c["attrs"]
    return []


def select_combine(cond, a, b, keep_attrs):
    """Deterministic structural stand-in for the unchanged apply_ufunc combine.
    Identical on both legs (A-reference). Takes the retention FLAG, as the real
    callee does (`keep_attrs=keep_attrs`), because the flag decides that routine's
    own attr merge: 'drop' (empty bags) when False, 'override' (a sentinel
    carrier bag) when True. Produces a result record whose component NAMES are
    what the rebuild reads."""
    is_container = a["isContainer"] or b["isContainer"]
    # union of component names from a and b (order: a then new-from-b), as the
    # real combine would surface; attrs per the flag-selected merge.
    def merge(an, bn):
        names = [c["name"] for c in an]
        for c in bn:
            if c["name"] not in names:
                names.append(c["name"])
        return [{"name": nm,
                 "attrs": ([["__combine__", nm]] if keep_attrs else [])}
                for nm in names]
    return {
        "topAttrs": ([["__combine__", "top"]] if keep_attrs else []),
        "name": a["name"] if not is_container else None,
        "isContainer": is_container,
        "dataVars": merge(a["dataVars"], b["dataVars"]),
        "coords": merge(a["coords"], b["coords"]),
        # the result's own class table; the rebuild never reads it (it reads
        # `x`'s), so the stand-in's choice here cancels on both legs.
        "reserved": [],
    }


def lean_shadow(cond, a, b, keep_attrs, produces):
    """Mirror of implementation_where (Solution.lean impl region).

    `produces` is the spec's fifth binder: the observation of THIS call that says
    whether it yields an object. The mirror threads it exactly as the impl does —
    the rebuild runs regardless and the outcome is gated at the end — so the
    differential below exercises BOTH arms."""
    result = json.loads(json.dumps(select_combine(cond, a, b, keep_attrs)))
    if keep_attrs:
        if b["isContainer"] and not a["isContainer"]:
            result["topAttrs"] = []
            nm = a["name"]
            if nm is not None:
                for c in result["dataVars"]:
                    if c["name"] == nm:
                        c["attrs"] = a["topAttrs"]
            for c in result["coords"]:
                c["attrs"] = lookup_attrs(a, c["name"])
        else:
            result["topAttrs"] = a["topAttrs"]
            for c in result["dataVars"]:
                c["attrs"] = lookup_attrs(a, c["name"])
            for c in result["coords"]:
                c["attrs"] = lookup_attrs(a, c["name"])
    if produces:
        return result
    return None


def patch_shadow(cond, x, y, keep_attrs, produces):
    """Mirror of the gold patch.diff post-combine rebuild (computation.py:1879-1892).

    `produces` mirrors whether the real call completes with an object: when it is
    false the real `where` raises out of the rebuild and yields no value, which
    this shadow reports as `None`.

    Maps the record model: x.attrs<->topAttrs, data_vars<->dataVars,
    coords<->coords, x.name<->name, isinstance(_,Dataset)<->isContainer,
    getattr(getattr(x,v,None),"attrs",{})<->lookup_attrs(x,v), whose first
    stage is x's own class table (`reserved`)."""
    result = json.loads(json.dumps(select_combine(cond, x, y, keep_attrs)))
    if keep_attrs:
        if y["isContainer"] and not x["isContainer"]:
            result["topAttrs"] = []
            data_var_names = [c["name"] for c in result["dataVars"]]
            if x["name"] is not None and x["name"] in data_var_names:
                for c in result["dataVars"]:
                    if c["name"] == x["name"]:
                        c["attrs"] = x["topAttrs"]  # getattr(x,"attrs",{})
        else:
            result["topAttrs"] = x["topAttrs"]
            for c in result["dataVars"]:
                c["attrs"] = lookup_attrs(x, c["name"])  # getattr(getattr(x,v),"attrs",{})
        for c in result["coords"]:
            c["attrs"] = lookup_attrs(x, c["name"])  # always rebuild coord attrs from x
    if produces:
        return result
    return None


def rand_attrs(rng):
    return [[f"k{rng.randint(0,3)}", f"v{rng.randint(0,5)}"]
            for _ in range(rng.randint(0, 3))]


def rand_components(rng, pool):
    n = rng.randint(0, 3)
    chosen = rng.sample(pool, min(n, len(pool))) if pool else []
    return [{"name": nm, "attrs": rand_attrs(rng)} for nm in chosen]


# Component names, deliberately MIXING names a real class does not reserve
# ("time", "lat", "lon") with names it does: "T"/"real" resolve to a
# whole-object view and so carry the object's own top-level bag, while
# "dims"/"values"/"mean" resolve to a method or non-bag object and carry {}.
# Both reserved outcomes and the unreserved fall-through are therefore fuzzed.
NAME_POOL = ["a", "b", "x", "time", "lat", "lon",
             "T", "real", "dims", "values", "mean"]
# Names whose class-level answer is a view of the whole object: the bag is the
# object's OWN top-level bag. The rest of the reserved table yields {}.
VIEW_NAMES = ["T", "real"]
BAGLESS_NAMES = ["dims", "values", "mean"]


def rand_reserved(rng, top_attrs):
    """The object's class table: reserved name -> the bag its answer carries."""
    out = []
    for nm in VIEW_NAMES:
        if rng.random() < 0.8:
            out.append([nm, top_attrs])
    for nm in BAGLESS_NAMES:
        if rng.random() < 0.8:
            out.append([nm, []])
    return out


def rand_obj(rng):
    is_container = rng.random() < 0.5
    top = rand_attrs(rng)
    return {
        "topAttrs": top,
        "name": rng.choice([None] + NAME_POOL),
        "isContainer": is_container,
        "dataVars": rand_components(rng, NAME_POOL) if is_container else [],
        "coords": rand_components(rng, NAME_POOL),
        "reserved": rand_reserved(rng, top),
    }


def main():
    rng = random.Random(CONF_SEED)
    disagreements = 0
    first = None
    for i in range(N):
        cond = rand_obj(rng)
        a = rand_obj(rng)
        b = rand_obj(rng)
        keep = rng.random() < 0.5
        produces = rng.random() < 0.5
        lhs = lean_shadow(cond, a, b, keep, produces)
        rhs = patch_shadow(cond, a, b, keep, produces)
        if lhs != rhs:
            disagreements += 1
            if first is None:
                first = {"i": i, "a": a, "b": b, "keep": keep,
                         "produces": produces, "lean": lhs, "patch": rhs}
    status = "pass" if disagreements == 0 else "fail"
    print(json.dumps({
        "gate": "G-CONF",
        "status": status,
        "inputs": N,
        "seed": CONF_SEED,
        "disagreements": disagreements,
        "first_disagreement": first,
    }))
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
