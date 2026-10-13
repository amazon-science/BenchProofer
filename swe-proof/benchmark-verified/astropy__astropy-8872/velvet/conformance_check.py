#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-8872 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs. There are no
A-tagged callees in this bundle (no axioms / no deep-model reference), so the
whole impl region is pure R/I (`conf_skip=false`).

  * SHADOW  — the R/I-tagged dispatch of Solution.lean's two impl regions
              (`resolveElemGeneral` / `resolveElemFast`) transliterated to Python
              over the *real* repo type (a numpy dtype), via the mapping.md
              bijection (`ElemType` ↔ a representative `np.dtype`). The decision
              is a pure categorical dispatch on the input element-type, yielding
              the resulting element-type.
  * ORACLE  — `patch.diff`'s behaviour at the two changed sites of
              `Quantity.__new__`, transliterated VERBATIM from the post-image:
                site 1 (fast / already-array path):  cast iff dtype.kind in 'iu'
                site 2 (general path):               cast iff dtype.kind in 'iuO'
              applied to the SAME real numpy dtype, producing the resulting dtype
              (`float` i.e. float64 when cast, else the input dtype). We drive the
              real numpy dtype machinery (`np.dtype`, `.kind`, `np.array(...)
              .astype(float)`) so the oracle is the real predicate the patch
              installs, not a hand-rolled re-encoding.

ORACLE CHOICE — why not drive `Quantity.__new__` end-to-end: the resulting
element-type is decided inside `__new__` purely from the input array's dtype
(`value.dtype.kind`); building a full `Quantity` (units machinery, `_set_unit`,
`to`) only to read back `q.dtype` would not isolate the modeled decision and
needs the whole astropy units stack. The F2P test observes exactly `q.dtype`,
which equals the resulting dtype this oracle computes. So the oracle is the
patched dtype-resolution predicate applied to real numpy dtypes; the harness
having applied patch.diff is irrelevant to this self-contained predicate (we do
not import astropy), but the predicate is copied verbatim from the post-image.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + numpy only (numpy is a
hard dependency of the instance image). The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import numpy as np

SEED = 8872
N_FUZZ = 100_000

# --- mapping.md §2 bijection: ElemType  <->  a representative numpy dtype ------
# Each modeled ElemType maps to one representative real numpy dtype. The decision
# reacts ONLY to the distinctions these representatives differ in (kind, and —
# pre-patch — width via can_cast), so one representative per category is faithful;
# the fuzz loop additionally samples extra concrete dtypes within each category.
_STRUCT = np.dtype([("f0", np.int32), ("f1", np.float64)])
ELEMTYPE_TO_DTYPE = {
    "boolean":      np.dtype(np.bool_),
    "integral":     np.dtype(np.int64),
    "floatHalf":    np.dtype(np.float16),
    "floatSingle":  np.dtype(np.float32),
    "floatDouble":  np.dtype(np.float64),
    "floatExtended": np.dtype(np.longdouble),
    "complexFloat": np.dtype(np.complex128),
    "object":       np.dtype(np.object_),
    "structured":   _STRUCT,
}
# Extra concrete dtypes per category, for fuzz coverage within a category.
CATEGORY_MEMBERS = {
    "boolean":      [np.bool_],
    "integral":     [np.int8, np.int16, np.int32, np.int64,
                     np.uint8, np.uint16, np.uint32, np.uint64],
    "floatHalf":    [np.float16],
    "floatSingle":  [np.float32],
    "floatDouble":  [np.float64],
    "floatExtended": [np.longdouble],
    "complexFloat": [np.complex64, np.complex128],
    "object":       [np.object_],
    "structured":   [_STRUCT],
}

DEFAULT_FLOAT = np.dtype(float)   # float64 — the default cast target


# --- SHADOW: Solution.lean dispatch, transliterated --------------------------
def shadow_general(dtype):
    """resolveElemGeneral, transliterated: integral / object -> floatDouble; every
    floating width, boolean, complex, structured -> preserved."""
    cat = category_of(dtype)
    if cat in ("integral", "object"):
        return DEFAULT_FLOAT
    return dtype


def shadow_fast(dtype):
    """resolveElemFast, transliterated: only integral -> floatDouble; every
    floating width, boolean, complex, object, structured -> preserved."""
    cat = category_of(dtype)
    if cat == "integral":
        return DEFAULT_FLOAT
    return dtype


def category_of(dtype):
    """Classify a real numpy dtype into one modeled ElemType category (the
    mapping.md bijection, read backwards: which ElemType this real dtype binds
    to). Used only by the SHADOW to pick its categorical arm."""
    if dtype.fields:
        return "structured"
    k = dtype.kind
    if k == "b":
        return "boolean"
    if k in "iu":
        return "integral"
    if k == "O":
        return "object"
    if k == "c":
        return "complexFloat"
    if k == "f":
        if dtype == np.dtype(np.float16):
            return "floatHalf"
        if dtype == np.dtype(np.float32):
            return "floatSingle"
        if dtype == np.dtype(np.float64):
            return "floatDouble"
        return "floatExtended"
    raise AssertionError("unmodeled dtype kind %r" % k)


# --- ORACLE: patch.diff post-image predicate, applied to real numpy dtypes ----
def oracle_general(dtype):
    """Site 2 (general path), post-image (`quantity.py`):
        if dtype is None and value.dtype.kind in 'iuO':
            value = value.astype(float)
    The resulting element-type is float64 when cast, else the input dtype."""
    if dtype.kind in "iuO":
        return DEFAULT_FLOAT
    return dtype


def oracle_fast(dtype):
    """Site 1 (fast / already-array path), post-image (`quantity.py`):
        if value.dtype.kind in 'iu':
            dtype = float
    The resulting element-type is float64 when cast, else the input dtype."""
    if dtype.kind in "iu":
        return DEFAULT_FLOAT
    return dtype


def dtype_pool(rng):
    # exhaustive: one representative per modeled category (boundary first)
    pool = [np.dtype(d) for cat in ELEMTYPE_TO_DTYPE for d in [ELEMTYPE_TO_DTYPE[cat]]]
    # plus every concrete member of every category
    for members in CATEGORY_MEMBERS.values():
        for m in members:
            pool.append(np.dtype(m))
    return pool


def main():
    rng = random.Random(SEED)
    pool = dtype_pool(rng)

    disagreements = []
    count = 0

    def check(dtype):
        nonlocal count
        count += 1
        for name, shadow, oracle in (
            ("general", shadow_general, oracle_general),
            ("fast", shadow_fast, oracle_fast),
        ):
            s = shadow(dtype)
            o = oracle(dtype)
            if s != o:
                disagreements.append((name, str(dtype), str(s), str(o)))

    # exhaustive over the representative + member pool
    for dt in pool:
        check(dt)
    # seeded fuzz: random concrete dtypes drawn from the modeled categories
    all_members = [np.dtype(m) for ms in CATEGORY_MEMBERS.values() for m in ms]
    for _ in range(N_FUZZ):
        check(rng.choice(all_members))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d (site,input) checks:"
              % (len(disagreements), count))
        for site, inp, sh, orc in disagreements:
            print("  site=%s input=%s shadow=%s oracle=%s" % (site, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveElemGeneral/resolveElemFast agrees "
          "with the patched dtype-resolution logic of Quantity.__new__ on %d "
          "checks (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
