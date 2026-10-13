#!/usr/bin/env python3
"""G-CONF for django__django-12193.

Differential test: the R/A-reference shadow of `implementation_buildInputContext`
(translated from Solution.lean) vs the real patched behaviour of
`CheckboxInput.get_context` (post-patch: `attrs = {**(attrs or {}), 'checked':
True}`, then `build_attrs(self.attrs, attrs) = {**self.attrs, **(attrs or {})}`).

We compare BOTH observable components over >=1e5 fuzzed inputs:
  * contextAttrs  — the merged attribute mapping exposed by the context;
  * callerAttrs   — the caller's own dict, observed AFTER the call (must be
                    identical object-content to what was passed in).

stdlib-only; exit 0 iff zero disagreements.
"""
import random
import sys

CONF_SEED = 20240627
N = 120_000
KEYS = ["checked", "id", "class", "name", "disabled", "type"]


# ---- Lean-model shadow (assoc list with Bool payload; mirrors Solution.lean) ----
def dict_set(d, k, v):
    if any(p[0] == k for p in d):
        return [(k, v) if p[0] == k else p for p in d]
    return d + [(k, v)]


def merge_dict(base, extra):
    acc = list(base)
    for (k, v) in extra:
        acc = dict_set(acc, k, v)
    return acc


def shadow(base, check_test, attrs):
    """Returns (contextAttrs, callerAttrs) per implementation_buildInputContext."""
    cur = list(attrs) if attrs is not None else []
    if check_test:
        cur = dict_set(cur, "checked", True)
    context_attrs = merge_dict(base, cur)
    caller_attrs = None if attrs is None else list(attrs)
    return context_attrs, caller_attrs


# ---- Real patched behaviour (faithful transcription of patched get_context) ----
def real(base, check_test, attrs):
    """attrs is the caller's dict (or None). We observe it after the call."""
    self_attrs = dict(base)
    caller_obj = None if attrs is None else dict(attrs)  # the caller's object

    # post-patch get_context body, operating on the caller's object:
    a = caller_obj
    if check_test:
        a = {**(a or {}), "checked": True}  # FRESH dict; caller_obj untouched
    # super().get_context -> build_attrs(self.attrs, a)
    context_attrs = {**self_attrs, **(a or {})}

    # caller observes caller_obj after the call
    return context_attrs, caller_obj


def norm_map(assoc):
    """Lean assoc list -> dict (Bool payloads only)."""
    return {k: v for (k, v) in assoc}


def main():
    rng = random.Random(CONF_SEED)
    disagreements = 0
    for _ in range(N):
        # random base (widget's own attrs) and caller attrs, Bool payloads only
        base = []
        for k in rng.sample(KEYS, rng.randint(0, len(KEYS))):
            base.append((k, bool(rng.getrandbits(1))))
        if rng.random() < 0.25:
            attrs = None
        else:
            attrs = []
            for k in rng.sample(KEYS, rng.randint(0, len(KEYS))):
                attrs.append((k, bool(rng.getrandbits(1))))
        check_test = bool(rng.getrandbits(1))

        sc, sk = shadow(base, check_test, attrs)
        rc, rk = real(base, check_test, attrs)

        # compare contextAttrs as maps (order-insensitive content)
        if norm_map(sc) != (rc or {}):
            disagreements += 1
            if disagreements <= 5:
                print(f"CTX mismatch base={base} ct={check_test} attrs={attrs}: "
                      f"shadow={norm_map(sc)} real={rc}", file=sys.stderr)
        # compare callerAttrs
        sk_map = None if sk is None else norm_map(sk)
        if sk_map != rk:
            disagreements += 1
            if disagreements <= 5:
                print(f"CALLER mismatch base={base} ct={check_test} attrs={attrs}: "
                      f"shadow={sk_map} real={rk}", file=sys.stderr)

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements over {N} inputs")
        return 1
    print(f"G-CONF PASS: 0 disagreements over {N} fuzzed inputs (seed={CONF_SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
