#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11095.

The bundle models ONE function: `ModelAdmin.get_inline_instances`, which builds
the ordered list of inline editor instances to show on an admin page
(`django/contrib/admin/options.py`). The modeled value is a PURE function of the
following observables (mapping.md):

    hasRequest   : bool             (bool(request) — a request is in context)
    selfInlines  : list[Inline]     (self.inlines — the static attribute)
    hookInlines  : list[Inline]     (self.get_inlines(request, obj) — hook output)

where each Inline carries:
    id              : int           (class identity)
    hasViewOrChange : bool          (inline.has_view_or_change_permission)
    hasAdd          : bool          (inline.has_add_permission)
    hasDelete       : bool          (inline.has_delete_permission)

and each produced InlineInstance carries (id, maxNumZeroed).

Post-patch rule (the loop iterates the HOOK output):

    instances = []
    for c in hookInlines:
        inst = (c.id, max_num_zeroed=False)
        if hasRequest:
            if not (c.hasViewOrChange or c.hasAdd or c.hasDelete):
                continue
            if not c.hasAdd:
                inst = (c.id, max_num_zeroed=True)
        instances.append(inst)
    return instances

Standing up the full admin/ORM stack to drive the real `get_inline_instances`
is heavy and unnecessary: the modeled value is this pure decision over the
observables the real method consumes. The ORACLE below is a faithful in-process
replica of the EXACT patched control flow (iterating the hook output, the
verbatim permission filter and max_num zeroing); the SHADOW is the op-for-op
transliteration of `implementation_getInlineInstances` (refinement.md). They
compare as ordered lists of (id, maxNumZeroed) tuples — order is observable
(`inline_instances` is a list returned in iteration order).

The fuzzer deliberately varies hookInlines INDEPENDENTLY of selfInlines (the
override case the patch enables), including the F2P shapes: hook returns [] while
self.inlines is non-empty, and hook returns a slice differing from self.inlines.

stdlib-only. Pinned seed: 11095 (also in mapping.md).
"""
import random
import sys

SEED = 11095
N = 120_000


# --- ORACLE: faithful in-process replica of the patched method ---------------
# Inline := (id, hasViewOrChange, hasAdd, hasDelete); produced := (id, maxNumZeroed)
def oracle_get_inline_instances(has_request, self_inlines, hook_inlines):
    instances = []
    for c in hook_inlines:                       # post-patch: self.get_inlines(...)
        cid, hvc, hadd, hdel = c
        max_num_zeroed = False
        if has_request:
            if not (hvc or hadd or hdel):
                continue
            if not hadd:
                max_num_zeroed = True
        instances.append((cid, max_num_zeroed))
    return instances


# --- SHADOW of implementation_getInlineInstances (the R/I leg) ---------------
# Mirrors Solution.lean op-for-op: iterate hookInlines, keepInline filter under
# hasRequest, maxNumZeroed = hasRequest and not hasAdd, append in order.
def shadow_get_inline_instances(has_request, self_inlines, hook_inlines):
    instances = []
    for c in hook_inlines:
        cid, hvc, hadd, hdel = c
        inst = (cid, False)
        if has_request:
            if not (hvc or hadd or hdel):
                continue
            if not hadd:
                inst = (cid, True)
        instances.append(inst)
    return instances


def disagree(hr, si, hi):
    got = oracle_get_inline_instances(hr, si, hi)
    want = shadow_get_inline_instances(hr, si, hi)
    if got != want:
        return ((hr, si, hi), got, want)
    return None


def _enumerate_edge():
    cases = []
    full = (1, True, True, True)        # all permissions
    noadd = (2, True, False, True)      # may view/delete but not add -> zeroed
    none = (3, False, False, False)     # no permissions -> dropped under request
    for hr in (True, False):
        cases.append((hr, [], []))                       # nothing selected
        cases.append((hr, [full, noadd], []))            # F2P: hook returns []
        cases.append((hr, [full, noadd], [full]))        # F2P: hook = slice [:1]
        cases.append((hr, [full, noadd], [noadd]))       # F2P: hook = slice [1:2]
        cases.append((hr, [], [full, noadd, none]))      # hook differs from self
        cases.append((hr, [full], [none, noadd, full]))  # filtering + zeroing mix
    return cases


def _rand_inline(rng):
    return (rng.randint(0, 9),
            rng.choice([True, False]),
            rng.choice([True, False]),
            rng.choice([True, False]))


def main() -> int:
    checked = 0
    for hr, si, hi in _enumerate_edge():
        d = disagree(hr, si, hi)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        hr = rng.choice([True, False])
        si = [_rand_inline(rng) for _ in range(rng.randint(0, 5))]
        hi = [_rand_inline(rng) for _ in range(rng.randint(0, 5))]
        d = disagree(hr, si, hi)
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
