#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-12585.

The bundle models ONE function: `clone(estimator, safe=True)`
(`sklearn/base.py`). Its Lean implementation (`implementation_duplicate`)
duplicates a structured value: collections element-wise; a value whose
configuration interface is unusable (exposes none, OR is a class/blueprint) is
routed to the no-config branch (unchanged when unsafe, failure when safe); a
realized configuration-exposing instance is rebuilt from a duplicated config.

ORACLE = the REAL post-patch `clone`. The harness git-applies the gold patch to
`/testbed` before running this script, so `from sklearn.base import clone` is the
PATCHED function (`elif not hasattr(...) or isinstance(estimator, type)`). We feed
it real Python objects.

SHADOW = `shadow_duplicate`, a line-for-line transliteration of
`implementation_duplicate` (the R/I leg), operating on independently-built copies
of the SAME real objects.

We build real objects from randomly generated specs (the mapping.md bijection),
run BOTH legs, and compare a canonical `observe(...)` rendering plus error/no-error
behavior. The differential exercises the fixed guard
(`isinstance(estimator, type)` ↔ `isBlueprint`), the `safe=False` recursion into
config entries, and the no-config identity copy. The discriminating case — a class
object, at top level and nested as a parameter — is covered by hand-picked edges
AND the fuzzer.

Value shapes (mapping.md bijection):
  * int                      -> a leaf (no get_params, not a type)
  * Estimator(**params)      -> config-exposing instance (isBlueprint=false)
  * Estimator (the class)    -> blueprint advertising config (isBlueprint=true,
                                exposesConfig=true) — the unbound-get_params case
  * NonEstClass (the class)  -> blueprint, no config (isBlueprint=true,
                                exposesConfig=false)
  * list / tuple             -> a group (collection), duplicated element-wise

set/frozenset are omitted: behaviorally identical under `clone` (kind is only the
reconstruction type) but their unordered iteration would make the differential
nondeterministic (documented limitation, mapping.md).

stdlib + sklearn (the system under test). Pinned seed: 12585 (also in mapping.md).
"""
import copy
import sys

SEED = 12585
N = 120_000
MAX_DEPTH = 4

try:
    from sklearn.base import clone as real_clone
except Exception as e:  # pragma: no cover
    print(f"cannot import sklearn.base.clone: {e}")
    print("status=fail")
    sys.exit(1)


# --- real value classes mirroring the PyVal bijection ------------------------
class Estimator:
    """A configuration-exposing value. As an INSTANCE: get_params is bound and
    callable (isBlueprint=false). As the CLASS object: get_params is present but
    UNBOUND (isBlueprint=true, exposesConfig=true) — calling it raises TypeError,
    exactly the bug the patch fixes."""
    def __init__(self, **params):
        self._params = dict(params)
        for k, v in params.items():
            setattr(self, k, v)

    def get_params(self, deep=False):
        return dict(self._params)


class NonEstClass:
    """A plain class with no get_params: a type that exposes no config interface
    (isBlueprint=true, exposesConfig=false)."""
    pass


ESTIMATOR_CLASS = Estimator
NONEST_CLASS = NonEstClass


def make_leaf(n):
    return n   # a plain int: not a collection, no get_params, not a type


# --- canonical observation (value-comparable across both legs) ---------------
def observe(obj):
    if isinstance(obj, list):
        return ("list", [observe(e) for e in obj])
    if isinstance(obj, tuple):
        return ("tuple", tuple(observe(e) for e in obj))
    if isinstance(obj, type):
        return ("type", obj.__name__, id(obj))   # class identity (returned as-is)
    if hasattr(obj, "get_params"):
        cfg = obj.get_params(deep=False)
        return ("est", type(obj).__name__,
                tuple(sorted((k, observe(v)) for k, v in cfg.items())))
    return ("leaf", obj)


# --- ERROR sentinel ----------------------------------------------------------
class _Err:
    pass
ERROR = _Err()


# --- SHADOW: transliteration of implementation_duplicate ---------------------
def is_group(obj):
    return isinstance(obj, (list, tuple))


def shadow_duplicate(obj, safe):
    if is_group(obj):
        out = []
        for e in obj:
            r = shadow_duplicate(e, safe)
            if r is ERROR:
                return ERROR
            out.append(r)
        return out if isinstance(obj, list) else tuple(out)
    # node
    exposes_config = hasattr(obj, "get_params")
    is_blueprint = isinstance(obj, type)
    if (not exposes_config) or is_blueprint:          # configUnusable
        if safe:
            return ERROR
        else:
            return copy.deepcopy(obj)
    else:
        if is_blueprint:                              # dead under the fixed guard
            return ERROR
        cfg = obj.get_params(deep=False)
        new_cfg = {}
        for k, v in cfg.items():
            r = shadow_duplicate(v, False)
            if r is ERROR:
                return ERROR
            new_cfg[k] = r
        return obj.__class__(**new_cfg)


# --- run both legs -----------------------------------------------------------
def run_oracle(obj, safe):
    try:
        return ("ok", observe(real_clone(obj, safe=safe)))
    except TypeError:
        return ("err",)


def run_shadow(obj, safe):
    r = shadow_duplicate(obj, safe)
    if r is ERROR:
        return ("err",)
    return ("ok", observe(r))


def disagree(builder, safe):
    o1 = builder()
    o2 = builder()
    got = run_oracle(o1, safe)
    want = run_shadow(o2, safe)
    if got != want:
        return (str(observe(builder())), safe, got, want)
    return None


# --- deterministic generation ------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def gen_builder(rnd, depth):
    """Return a thunk building a fresh real object tree (each leg gets its own)."""
    choice = next(rnd) % 8
    if depth <= 0 or choice == 0:
        n = next(rnd) % 100
        return lambda: make_leaf(n)
    if choice == 1:
        return lambda: ESTIMATOR_CLASS          # blueprint advertising config
    if choice == 2:
        return lambda: NONEST_CLASS             # blueprint, no config
    if choice in (3, 4):
        nparams = next(rnd) % 4
        sub = [(next(rnd) % 1000, gen_builder(rnd, depth - 1)) for _ in range(nparams)]
        return lambda sub=sub: Estimator(**{f"p{k}": b() for k, b in sub})
    if choice in (5, 6):
        nelem = next(rnd) % 4
        subs = [gen_builder(rnd, depth - 1) for _ in range(nelem)]
        return lambda subs=subs: [b() for b in subs]
    nelem = next(rnd) % 4
    subs = [gen_builder(rnd, depth - 1) for _ in range(nelem)]
    return lambda subs=subs: tuple(b() for b in subs)


# --- hand-picked edges -------------------------------------------------------
def edge_builders():
    return [
        (lambda: make_leaf(7), True),
        (lambda: make_leaf(7), False),
        (lambda: Estimator(a=make_leaf(1)), True),
        # THE F2P case: estimator instance whose param IS an estimator CLASS
        (lambda: Estimator(empty=ESTIMATOR_CLASS), True),
        (lambda: Estimator(empty=ESTIMATOR_CLASS), False),
        (lambda: ESTIMATOR_CLASS, True),
        (lambda: ESTIMATOR_CLASS, False),
        (lambda: NONEST_CLASS, True),
        (lambda: NONEST_CLASS, False),
        (lambda: [Estimator(empty=ESTIMATOR_CLASS), make_leaf(3)], True),
        (lambda: Estimator(inner=Estimator(empty=ESTIMATOR_CLASS)), True),
        (lambda: (ESTIMATOR_CLASS, NONEST_CLASS), True),
        (lambda: Estimator(c=ESTIMATOR_CLASS, e=Estimator(x=make_leaf(9))), True),
        (lambda: [make_leaf(1), make_leaf(2)], True),
        (lambda: Estimator(), True),
    ]


def main() -> int:
    checked = 0

    for builder, safe in edge_builders():
        d = disagree(builder, safe)
        if d:
            print(f"DISAGREE edge spec={d[0]!r} safe={d[1]}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        builder = gen_builder(rnd, MAX_DEPTH)
        safe = bool(next(rnd) % 2)
        d = disagree(builder, safe)
        if d:
            print(f"DISAGREE fuzz spec={d[0]!r} safe={d[1]}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
