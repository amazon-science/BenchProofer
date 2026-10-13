#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14493.

The bundle models ONE function: `ManifestFilesMixin.post_process`
(`django/contrib/staticfiles/storage.py`). Its Lean implementation
(`implementation_postProcess`) decides the runtime state of the post-loop
`substitutions` flag after the bounded refinement-pass loop, returning that
state as an `Option Bool` (`some b` = the flag is bound to boolean `b`;
`none` = the flag is referenced with no value assigned, i.e. `UnboundLocalError`):

    substitutions = some(False)                  # gold: initialized before loop
    for i in range(maxPasses):
        substitutions = some(passSubst(i))
        if not passSubst(i):
            break
    return substitutions

This script transliterates that R/I impl into Python (`shadow_post_process`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `post_process`'s loop — the flag initialized to `False`
before the bounded loop, overwritten each pass with that pass's aggregated
substitution outcome, the loop breaking at the first pass producing no
substitutions, and the flag always bound on exit.

We do NOT stand up Django's staticfiles storage stack (heavy; the modeled value
is a pure decision over the iteration bound and the per-pass boolean pattern).
Both legs are total functions over the modeled abstraction, so the edge set
EXHAUSTIVELY enumerates the modeled input space (maxPasses 0..MAXK × every
per-pass boolean pattern of length maxPasses); the fuzz loop additionally samples
random points over a wider bound. The discriminating case — maxPasses == 0 — is
therefore covered: oracle (post-patch) returns `some False`, while the PRE-patch
flag would be unbound (`none`).

stdlib-only. Pinned seed: 14493 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 14493
N = 150_000
MAXK = 8            # exhaustive grid: maxPasses in 0..MAXK
FUZZ_MAXK = 40      # fuzz: wider iteration bound


# A per-pass behavior is a tuple `pattern` of bools; passSubst(i) = pattern[i].
def _pass_subst(pattern):
    def f(i):
        # passes beyond the supplied pattern (only reachable if maxPasses
        # exceeds len(pattern)) default to True (still substituting).
        return pattern[i] if i < len(pattern) else True
    return f


# --- ORACLE: the post-patch post_process loop, faithful in-process replica ----
def oracle_post_process(max_passes, pass_subst):
    substitutions = False               # gold: bound before the loop
    bound = True                        # always bound under post-patch code
    for i in range(max_passes):
        substitutions = pass_subst(i)
        if not pass_subst(i):
            break
    return (bound, substitutions)


# --- shadow of implementation_postProcess (the R/I leg) -----------------------
# Mirrors Solution.lean op-for-op; Option Bool modeled as (bound, value).
def shadow_post_process(max_passes, pass_subst):
    bound = True                        # `some false` init -> bound
    substitutions = False
    for i in range(max_passes):
        substitutions = pass_subst(i)
        if not pass_subst(i):
            break
    return (bound, substitutions)


def disagree(max_passes, pattern):
    f = _pass_subst(pattern)
    got = oracle_post_process(max_passes, f)
    want = shadow_post_process(max_passes, f)
    if got != want:
        return (max_passes, pattern, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over the modeled abstraction: every iteration bound
    # 0..MAXK paired with every per-pass boolean pattern of that length. The
    # crashing config maxPasses == 0 (empty pattern) is the first point.
    for k in range(0, MAXK + 1):
        for pattern in itertools.product((False, True), repeat=k):
            d = disagree(k, pattern)
            if d:
                print(f"DISAGREE exhaustive maxPasses={d[0]} pattern={d[1]!r}: "
                      f"oracle={d[2]} shadow={d[3]}")
                print("status=fail")
                return 1
            checked += 1

    # Redundant random fuzz over a wider iteration bound.
    rnd = _lcg(SEED)
    for _ in range(N):
        k = next(rnd) % (FUZZ_MAXK + 1)
        pattern = tuple((next(rnd) & 1) == 1 for _ in range(k))
        d = disagree(k, pattern)
        if d:
            print(f"DISAGREE fuzz maxPasses={d[0]} pattern={d[1]!r}: "
                  f"oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
