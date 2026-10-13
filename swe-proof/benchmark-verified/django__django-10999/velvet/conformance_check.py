#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10999 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the
              `parseDurationSeconds` `do` block: the left-to-right fold of
              `step` and the final `decode`) transliterated to Python over the
              real repo type (`str`), via the mapping.md §2 bijection
              (`List Char` <-> `str`, `Char.ofNat (ord ch)` <-> ch; the result
              `Option Int` of seconds <-> `round(td.total_seconds())`).
              The impl region contains NO A-tagged callee (the changed op is
              modeled deeply and concretely), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.utils.dateparse.parse_duration` applied at base_commit
              (the real correctness oracle, G-RESOLVE). The harness applies
              patch.diff before this runs.

They must agree on every Requires-satisfying input (non-empty string over the
modeled `{0-9, :, -}` alphabet). Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container, stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import itertools
import random
import sys

SEED = 10999
N_FUZZ = 100_000
ALPHABET = "0123456789:-"


# --- the R/I shadow: Solution.lean step/decode/parseDuration, transliterated -
def shadow_parse(s):
    """parseDuration (s.toList) : Option Int, the R/I fold of the impl region."""
    sign = 1
    acc = 0
    cur = 0
    groups = 1
    curlen = 0
    valid = True
    seen = False
    for ch in s:                                   # text.foldl step initPS
        if not valid:
            pass
        elif ch == '-':
            if seen:
                valid = False
            else:
                sign = -1
            seen = True
        elif ch == ':':
            if curlen == 0:
                valid = False
            elif groups == 3:
                valid = False
            else:
                acc = acc * 60 + cur
                cur = 0
                groups += 1
                curlen = 0
            seen = True
        elif '0' <= ch <= '9':
            cur = cur * 10 + (ord(ch) - 48)
            curlen += 1
            seen = True
        else:
            valid = False
            seen = True
    if not valid:                                  # decode
        return None
    if curlen == 0:
        return None
    return sign * (acc * 60 + cur)


_OUT_OF_DOMAIN = object()


def oracle_parse(s):
    """patch.diff's behaviour: the patched parse_duration, bridged to
    Option Int (seconds) per mapping.md §2. Returns the sentinel
    `_OUT_OF_DOMAIN` for magnitudes too large for Python's `timedelta`
    (|days| <= 999999999) — a callee limit, not a spec one: the Lean carrier
    `Int` is unbounded, so such inputs are outside the finitely representable
    modeled domain."""
    from django.utils.dateparse import parse_duration
    try:
        td = parse_duration(s)
    except OverflowError:
        return _OUT_OF_DOMAIN
    if td is None:
        return None
    secs = td.total_seconds()
    r = round(secs)
    # Inside the modeled domain results are integral; guard the bridge.
    if abs(secs - r) >= 1e-9:
        raise AssertionError("non-integral seconds %r outside modeled domain "
                             "for %r" % (secs, s))
    return r


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4) — the discriminating F2P rows
    for s in ["-15:30", "-1:15:30", "-00:01:01", "-01:01", "-01:-01",
              "30", "-30", "0", "1:30", "10:20:30", "-10:20:30",
              ":", "-", "1:", ":1", "1:2:3:4", "-1:2:3:4"]:
        yield s
    # exhaustive over the alphabet up to length 5
    for L in range(1, 6):
        for tup in itertools.product(ALPHABET, repeat=L):
            yield "".join(tup)
    # randomized fuzz (per-group magnitude kept representable)
    for _ in range(n):
        k = rng.randint(1, 8)
        yield "".join(rng.choice(ALPHABET) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        if s == "":            # require text != []
            continue
        oracle = oracle_parse(s)
        if oracle is _OUT_OF_DOMAIN:    # callee overflow, outside modeled domain
            skipped += 1
            continue
        count += 1
        shadow = shadow_parse(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of parseDurationSeconds agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements; %d skipped "
          "out-of-domain (timedelta overflow)." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
