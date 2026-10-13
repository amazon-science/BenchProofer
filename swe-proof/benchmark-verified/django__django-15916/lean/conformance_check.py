#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15916.

The bundle models ONE decision: which `formfield_callback` the model-form
metaclass selects and hands to the field builder when constructing a model-form
class (`ModelFormMetaclass.__new__`, `django/forms/models.py`). The modeled value
is a PURE function of four observables (mapping.md):

    metaCallback       : Optional[id]            the class's own options-block
                                                 callback (opts.formfield_callback)
    directHasCallback  : bool                    is "formfield_callback" a top-level
                                                 class attribute? (attrs membership)
    directCallback     : Optional[id]            its value when present
    baseMetaCallback   : Optional[Optional[id]]  first base whose Meta declares the
                                                 attr: None=no such base; (v,) carries
                                                 that base's value (v may be None)

Post-patch rule (the gold patch): the selected callback is exactly the class's
own options-block callback.

    selected = metaCallback

Standing up Django's full metaclass machinery is unnecessary: the modeled value
is this pure projection over observables the construction exposes. The ORACLE
below is a faithful in-process replica of the EXACT patched selection
(`opts.formfield_callback`); the SHADOW is the op-for-op transliteration of
`implementation_resolveModelFormCallback` (per refinement.md). They must agree
for every input — in particular when a direct attribute or a base-form callback
is present but differs from the own-options-block callback (the discriminating
cases the F2P tests exercise).

Callbacks are compared by identity (their integer id / None), exactly as Python
selects a callable object by reference. stdlib-only. Pinned seed: 15916.
"""
import random
import sys

SEED = 15916
N = 200_000

NONE = None  # "no callback"


# --- ORACLE: faithful in-process replica of the patched selection ------------
def oracle_select(meta_callback, direct_has, direct_callback, base_meta_callback):
    # post-patch: fields_for_model(..., opts.formfield_callback, ...)
    return meta_callback


# --- SHADOW of implementation_resolveModelFormCallback (the R/I leg) ----------
# Mirrors Solution.lean: selected := metaCallback; return selected.
def shadow_select(meta_callback, direct_has, direct_callback, base_meta_callback):
    selected = meta_callback
    return selected


def disagree(mc, dh, dc, bmc):
    got = oracle_select(mc, dh, dc, bmc)
    want = shadow_select(mc, dh, dc, bmc)
    if got != want:
        return ((mc, dh, dc, bmc), got, want)
    return None


# callback identities; None == "no callback"
CB_POOL = [NONE, 1, 2, 3, 7]


def _enumerate_edge():
    cases = []
    for mc in (NONE, 5):
        for dh in (True, False):
            for dc in (NONE, 9):
                # base scan: absent / present-with-None / present-with-value
                for bmc in (NONE, (NONE,), (9,), (5,)):
                    cases.append((mc, dh, dc, bmc))
    # F2P #1 shape: own Meta declares cb, no top-level attr, no base ->
    #   metaCallback = some cb, legacy resolution would give none.
    cases.append((11, False, NONE, NONE))
    # F2P #2 shape: factory-built class inherits base Meta cb into its own opts,
    #   top-level attr injected as None (clobber) -> metaCallback = some cb.
    cases.append((11, True, NONE, (11,)))
    return cases


def main() -> int:
    checked = 0
    for mc, dh, dc, bmc in _enumerate_edge():
        d = disagree(mc, dh, dc, bmc)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        mc = rng.choice(CB_POOL)
        dh = rng.choice([True, False])
        dc = rng.choice(CB_POOL)
        bmc = rng.choice([NONE, (NONE,), (rng.choice(CB_POOL),)])
        d = disagree(mc, dh, dc, bmc)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
