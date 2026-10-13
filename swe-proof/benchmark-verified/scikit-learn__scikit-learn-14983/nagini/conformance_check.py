#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14983
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helper `resolved_value` copies
over as a plain function. The model works over ints and a plain dict, so no
PSeq shim is needed. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL repo function the model models per mapping.md —
`sklearn.model_selection._split._build_repr(self)`, whose per-parameter value
resolution is the modeled operation. The gate applies the diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the module importable.
This script never applies any diff itself.

DRIVING THE ORACLE: `_build_repr` inspects the object's constructor signature
to choose which parameter names to report, resolves a value for each name,
and renders `ClassName(name=value, ...)`. So each check builds a real object
(from a small set of synthetic classes whose `__init__` signatures carry 1..6
parameter names, plus the real repository classes), calls the REAL
`_build_repr`, parses the reported `name=value` pairs back out (values are
kept to ints / an absent marker so the rendering is exactly `repr(int)` or
the absent word), and compares each parameter's reported value against the
shadow resolver run on the bridged inputs.

TYPE BRIDGE (mapping.md section 2): for one object `obj` and parameter name
`key` —
  getattr(obj, key, None)                -> attr (Python None -> NONE sentinel)
  hasattr(obj, 'cvargs')                 -> has_store: bool
  {k: v for k, v in obj.cvargs.items()
       if v is not None}                 -> store (concrete entries only,
                                            satisfying the model Requires
                                            `store[key] != none`)
  the parameter name (a str here; the model uses int keys, but the resolution
  is key-agnostic, so the renaming is an exact bijection) -> key
  reported value (None == absent)        -> shadow result (NONE == absent)
An entry holding None in the secondary mapping resolves the same as a missing
entry in the real code, which is exactly what dropping it from `store` gives
the shadow — the bridge is total on all generated objects.

>= 1e5 Requires-satisfying inputs: structured boundary cases (every branch of
the resolution: direct attribute present / absent / explicitly None, store
carried or not, key recorded or not, plus the real repository classes) and
randomized fuzz objects, iterated until at least 100000 per-key checks ran.
Pinned fuzz seed: 149830.

Exit 0 iff zero disagreements; on disagreement prints the object, the key,
and both outcomes, then exits 1. stdlib only (plain random; no hypothesis).
"""
import json
import random
import re
import sys

SEED = 149830
MIN_CHECKS = 100_000

# A sentinel int standing for Python None in the model's int domain. All
# concrete values generated below stay far away from it.
NONE = -999999


# --- @Pure helper from model.py, contracts stripped ---------------------------

def resolved_value(attr, none, has_store, store, key):
    if attr != none:
        return attr
    if has_store and (key in store):
        return store[key]
    return none


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reported_param_value(attr, none, has_store, store, key):
    value = attr  # type: int
    if value == none and has_store:
        if key in store:
            value = store[key]
        else:
            value = none
    return value


# --- synthetic classes whose signatures drive the real function ---------------

_CLASS_CACHE = {}


def make_class(n_params):
    """A class whose __init__ signature carries parameter names p0..p{n-1}
    (the real function reports exactly the named constructor parameters).
    Attributes and the optional secondary mapping are set per instance."""
    cls = _CLASS_CACHE.get(n_params)
    if cls is not None:
        return cls
    names = ["p%d" % i for i in range(n_params)]
    src = "def __init__(self, %s):\n    pass\n" % ", ".join(names)
    ns = {}
    exec(src, ns)
    cls = type("Synth%d" % n_params, (object,), {"__init__": ns["__init__"]})
    _CLASS_CACHE[n_params] = cls
    return cls


def build_obj(n_params, attrs, cvargs):
    """Instantiate a synthetic object: `attrs` maps parameter names to values
    (a name may be absent, or explicitly None); `cvargs` is the secondary
    mapping (None => the object carries no such mapping at all)."""
    cls = make_class(n_params)
    obj = cls.__new__(cls)  # attribute state is set explicitly below
    for k, v in attrs.items():
        setattr(obj, k, v)
    if cvargs is not None:
        obj.cvargs = dict(cvargs)
    return obj


# --- bridge + comparison -------------------------------------------------------

_PAIR_RE = re.compile(r"(\w+)=(-?\d+|None)")


def parse_reported(repr_str, class_name):
    """Parse the `name=value` pairs out of the real function's rendering.
    All generated values are ints (rendered as their repr) or absent
    (rendered as the absent word), so this recovers the reported mapping
    exactly, including across wrapped lines."""
    assert repr_str.startswith(class_name + "(") and repr_str.endswith(")"), \
        "unexpected rendering shape: %r" % repr_str
    body = repr_str[len(class_name) + 1:-1]
    out = {}
    for m in _PAIR_RE.finditer(body):
        out[m.group(1)] = None if m.group(2) == "None" else int(m.group(2))
    return out


def shadow_inputs(obj, key):
    """Map (object, parameter name) to the shadow's arguments per the bridge."""
    raw_attr = getattr(obj, key, None)
    attr = NONE if raw_attr is None else raw_attr
    has_store = hasattr(obj, "cvargs")
    store = {}
    if has_store:
        for k, v in obj.cvargs.items():
            if v is not None:
                store[k] = v
    return attr, NONE, has_store, store, key


def check_object(build_repr, obj, param_names):
    """Run the REAL function once on obj; diff each parameter's reported value
    against the shadow. Returns (n_checked, error_or_None)."""
    rendered = build_repr(obj)
    reported = parse_reported(rendered, obj.__class__.__name__)
    n = 0
    for key in param_names:
        if key not in reported:
            return n, ("MISSING KEY\n  obj attrs=%r cvargs=%r key=%r\n"
                       "  rendered=%r" % (
                           {k: v for k, v in vars(obj).items()
                            if k != "cvargs"},
                           getattr(obj, "cvargs", "<no store>"), key,
                           rendered))
        args = shadow_inputs(obj, key)
        # model Requires hold by construction: store holds concrete values only
        assert all(v != NONE for v in args[3].values())
        shadow_out = reported_param_value(*args)
        assert shadow_out == resolved_value(*args)  # pure helper agreement
        shadow_as_real = None if shadow_out == NONE else shadow_out
        real_out = reported[key]
        if shadow_as_real != real_out:
            return n, ("DISAGREEMENT\n  obj attrs=%r cvargs=%r key=%r\n"
                       "  bridged (attr, none, has_store, store, key)=%r\n"
                       "  shadow=%r  real=%r  (rendered=%r)" % (
                           {k: v for k, v in vars(obj).items()
                            if k != "cvargs"},
                           getattr(obj, "cvargs", "<no store>"), key, args,
                           shadow_as_real, real_out, rendered))
        n += 1
    return n, None


# --- input generation -----------------------------------------------------------

def boundary_objects():
    """Every branch of the resolution, as (n_params, attrs, cvargs)."""
    return [
        # direct attribute present -> wins
        (1, {"p0": 2}, None),
        (1, {"p0": 0}, None),
        # attribute absent, no secondary mapping -> absent
        (2, {"p0": 5}, None),
        # attribute absent, mapping carried and records the key -> its value
        (1, {}, {"p0": 2}),
        # attribute absent, mapping carried but key not recorded -> absent
        (2, {"p0": 1}, {"other": 9}),
        # attribute present AND mapping records the key -> attribute wins
        (1, {"p0": 11}, {"p0": 2}),
        # attribute explicitly None, mapping records the key -> mapping value
        (1, {"p0": None}, {"p0": 4}),
        # attribute explicitly None, no mapping -> absent
        (1, {"p0": None}, None),
        # attribute explicitly None, mapping carried, key not recorded -> absent
        (1, {"p0": None}, {"q": 7}),
        # mapping entry holding None resolves like a missing entry
        (1, {}, {"p0": None}),
        (1, {"p0": None}, {"p0": None}),
        # empty carried mapping
        (2, {"p0": 3}, {}),
        # negative and zero values round-trip through the rendering
        (3, {"p0": -7, "p1": 0}, {"p2": -1}),
        # mixed: several keys exercising different branches at once
        (4, {"p0": 1, "p2": None}, {"p1": 6, "p2": 8, "extra": 5}),
    ]


def fuzz_object(rng):
    n_params = rng.randint(1, 6)
    names = ["p%d" % i for i in range(n_params)]
    attrs = {}
    for k in names:
        r = rng.random()
        if r < 0.34:
            attrs[k] = rng.randint(-50, 50)
        elif r < 0.5:
            attrs[k] = None
        # else: attribute absent
    cvargs = None
    if rng.random() < 0.6:
        cvargs = {}
        for k in names + ["extra%d" % rng.randint(0, 2)]:
            r = rng.random()
            if r < 0.5:
                cvargs[k] = rng.randint(-50, 50)
            elif r < 0.6:
                cvargs[k] = None  # resolves like a missing entry
    return n_params, attrs, cvargs


def main():
    # REAL repo symbols (the function the model models, per mapping.md):
    from sklearn.model_selection._split import _build_repr
    from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold

    checked = 0
    n_boundary = 0

    # --- boundary: synthetic objects covering every branch -----------------
    for n_params, attrs, cvargs in boundary_objects():
        obj = build_obj(n_params, attrs, cvargs)
        names = ["p%d" % i for i in range(n_params)]
        n, err = check_object(_build_repr, obj, names)
        checked += n
        n_boundary += n
        if err:
            print(err)
            return 1

    # --- boundary: the real repository classes -----------------------------
    for cls in (RepeatedKFold, RepeatedStratifiedKFold):
        for kw in ({"n_splits": 2, "n_repeats": 6},
                   {"n_splits": 5, "n_repeats": 10},
                   {"n_splits": 3, "n_repeats": 4, "random_state": 7}):
            obj = cls(**kw)
            n, err = check_object(
                _build_repr, obj, ["n_splits", "n_repeats", "random_state"])
            checked += n
            n_boundary += n
            if err:
                print(err)
                return 1

    # --- fuzz: randomized objects until >= 1e5 per-key checks --------------
    rng = random.Random(SEED)
    n_fuzz = 0
    while checked < MIN_CHECKS:
        n_params, attrs, cvargs = fuzz_object(rng)
        obj = build_obj(n_params, attrs, cvargs)
        names = ["p%d" % i for i in range(n_params)]
        n, err = check_object(_build_repr, obj, names)
        checked += n
        n_fuzz += n
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real per-parameter resolution of the "
          "reported representation on %d per-key checks (%d boundary + %d "
          "fuzz, seed %d)." % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
