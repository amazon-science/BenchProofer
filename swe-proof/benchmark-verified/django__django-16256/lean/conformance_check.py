#!/usr/bin/env python3
"""G-CONF for django__django-16256.

The modeled behavior (Solution.lean `implementation_scopedOp`) is the R-refined
"merge scope bindings into caller kwargs, first-occurrence semantics" operation.
This is the ONLY behavior the gold fix changes: post-fix, each async related-
manager op routes through the manager's sync op, which assigns every scope
binding into the kwargs dict before the data op; pre-fix it did not.

We differential-test two Python realizations over >=1e5 fuzzed inputs:

  * SHADOW  — a faithful transliteration of the Lean `kwUpsert` fold over an
    association list (List (String x Int)), first-occurrence `lookup`.
  * REF     — the gold behavior expressed with a real Python insertion-ordered
    dict: start from caller kwargs, then `d[key] = val` for each scope binding.

Equality of the observable read model (for every key, SHADOW.lookup == REF.get)
witnesses that the R refinement (assoc-list update <-> Python dict assignment)
is sound. stdlib + hypothesis only; exit 0 iff zero disagreements.
"""
import sys

SEED = 16256  # pinned in mapping.md


# ---- SHADOW: transliteration of Lean kwUpsert / fold / lookup -------------
def kw_upsert(kvs, key, val):
    out = []
    replaced = False
    for (k, v) in kvs:
        if not replaced and k == key:
            out.append((key, val))
            replaced = True
        else:
            out.append((k, v))
    if not replaced:
        out.append((key, val))
    return out


def shadow_impl(bindings, kwargs):
    out = list(kwargs)
    for (k, v) in bindings:
        out = kw_upsert(out, k, v)
    return out


def assoc_lookup(kvs, key):
    for (k, v) in kvs:
        if k == key:
            return v
    return None


# ---- REF: gold behavior via a real Python dict ----------------------------
def ref_impl(bindings, kwargs):
    d = {}
    for (k, v) in kwargs:      # caller kwargs, insertion order (first wins on read)
        d.setdefault(k, v)
    for (k, v) in bindings:    # scope binding assignment d[k] = v (overrides)
        d[k] = v
    return d


def compare(bindings, kwargs):
    sh = shadow_impl(bindings, kwargs)
    rf = ref_impl(bindings, kwargs)
    keys = set(k for k, _ in bindings) | set(k for k, _ in kwargs)
    for key in keys:
        if assoc_lookup(sh, key) != rf.get(key):
            return False, key
    return True, None


def main():
    try:
        from hypothesis import given, settings, strategies as st, seed
    except Exception as e:  # pragma: no cover
        print(f"status=error hypothesis unavailable: {e}")
        return 2

    keys = st.text(alphabet="abcdefghij_", min_size=1, max_size=4)
    vals = st.integers(min_value=-20, max_value=20)
    kv = st.tuples(keys, vals)
    kwargs_st = st.lists(kv, max_size=8)
    # scope bindings have distinct keys (the Nodup precondition)
    bindings_st = st.lists(kv, max_size=4, unique_by=lambda t: t[0])

    failures = []

    @seed(SEED)
    @settings(max_examples=120000, deadline=None)
    @given(bindings_st, kwargs_st)
    def prop(bindings, kwargs):
        ok, key = compare(bindings, kwargs)
        if not ok:
            failures.append((bindings, kwargs, key))
            assert False, f"disagreement at key {key!r}: {bindings} {kwargs}"

    try:
        prop()
    except AssertionError as e:
        print(f"status=fail {e}")
        return 1
    print("status=pass 0 disagreements over fuzzed inputs (R bijection sound)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
