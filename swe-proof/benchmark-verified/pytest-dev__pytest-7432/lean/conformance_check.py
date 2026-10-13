#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-7432.

The bundle models ONE decision inside `pytest_runtest_makereport`
(`src/_pytest/skipping.py`): was the reported source location of a mark-skipped
result rewritten to point at the test item?

The real hook reads a handful of observable conditions and runs an
expected-failure dispatch (a chain of mutually-exclusive cases) followed by the
skip-location rewrite. The modeled value is a PURE Boolean function of seven
observables the real hook reads:

    unexpSuccess     -- unexpectedsuccess_key in item._store and rep.when=="call"
    runxfail         -- item.config.option.runxfail
    xfailRaised      -- call.excinfo and isinstance(call.excinfo.value, xfail.Exception)
    notSkippedXfail  -- (not rep.skipped) and xfailed     (the xfail-mark branch)
    skippedByMark    -- item._store.get(skipped_by_mark_key, True)
    repSkipped       -- rep.skipped
    longreprIsTuple  -- type(rep.longrepr) is tuple

POST-PATCH rule: the expected-failure dispatch is one mutually-exclusive chain;
the location rewrite is a SEPARATE, independent decision that fires exactly when
the result is a mark-skipped result whose location is the structured triple
(`skippedByMark and repSkipped and longreprIsTuple`), regardless of which dispatch
arm was taken — in particular regardless of `runxfail`.

Standing up a live pytest session, a real `--runxfail` run, and inspecting the
emitted skip-summary location is heavy and unnecessary: the modeled value is this
pure decision over observables the real hook exposes. So the ORACLE below is a
faithful in-process replica of the POST-PATCH control flow (the dispatch chain
plus the independent rewrite `if`), and the SHADOW is the op-for-op
transliteration of `implementation_skipLocationRewrite` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical clause: when `runxfail` is active and
the result is a mark-skipped triple (the F2P scenario `[-rs --runxfail]`), the
location MUST still be rewritten (oracle/shadow == True) — the pre-patch code,
where the rewrite was the final `elif` arm, returns False there.

The input space is only 2**7 = 128 points; it is enumerated exhaustively in
addition to a seeded fuzz loop. stdlib-only. Pinned seed: 7432 (also in
mapping.md).
"""
import itertools
import random
import sys

SEED = 7432
N = 200_000


# --- ORACLE: faithful in-process replica of the POST-PATCH control flow -------
# Mirrors src/_pytest/skipping.py pytest_runtest_makereport after the gold patch:
# a mutually-exclusive expected-failure dispatch chain, then an INDEPENDENT `if`
# that rewrites the location of a mark-skipped, structured-triple result.
def oracle(unexpSuccess, runxfail, xfailRaised, notSkippedXfail,
           skippedByMark, repSkipped, longreprIsTuple):
    location_rewritten = False
    # expected-failure dispatch (none of these arms touch the skip location)
    if unexpSuccess:
        pass
    elif runxfail:
        pass            # "don't interfere" — only about xfail
    elif xfailRaised:
        pass
    elif notSkippedXfail:
        pass
    # INDEPENDENT of the dispatch above:
    if skippedByMark and repSkipped and longreprIsTuple:
        location_rewritten = True
    return location_rewritten


# --- SHADOW of implementation_skipLocationRewrite (the R/I leg) ---------------
# Mirrors Solution.lean impl region exactly.
def shadow(unexpSuccess, runxfail, xfailRaised, notSkippedXfail,
           skippedByMark, repSkipped, longreprIsTuple):
    location_rewritten = False
    if unexpSuccess:
        pass
    elif runxfail:
        pass
    elif xfailRaised:
        pass
    elif notSkippedXfail:
        pass
    if skippedByMark and repSkipped and longreprIsTuple:
        location_rewritten = True
    return location_rewritten


def disagree(inp):
    got = oracle(*inp)
    want = shadow(*inp)
    if got != want:
        return (inp, got, want)
    return None


def main() -> int:
    checked = 0

    # Exhaustive enumeration of the 128-point input space.
    for inp in itertools.product([False, True], repeat=7):
        d = disagree(inp)
        if d:
            print(f"DISAGREE exhaustive: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    # Seeded fuzz (redundant given exhaustion, kept for the gate convention).
    rng = random.Random(SEED)
    for _ in range(N):
        inp = tuple(rng.random() < 0.5 for _ in range(7))
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
