#!/usr/bin/env python
"""G-AX for astropy__astropy-14365.

Runs INSIDE the instance image with the gold patch applied (PYTHONPATH=/testbed),
so `astropy.io.ascii.qdp` here is the FIXED code.

The bundle consumes no `axiom <callee>_prop` (both `correct_*` close without a
callee property — `correct_classify` by `rfl`, `correct_readRow` by the loop
fold). The impl ops are A-references whose MODELING ASSUMPTIONS this check
validates against the real patched callees:

  A-reference 1 — `matchCategory true` (Triple 1 = the patched `_line_type`
  recognizer with case-insensitive matching). The modeled property the desired
  behavior rests on is CASE-INVARIANCE: classification does not depend on the
  letter-case of the line. Concretely:
    (a) `_line_type(line)` == `_line_type(any ASCII case-variant of line)`;
    (b) the lower-case header / new-block / data lines the issue reports
        (`read serr 1 2`, `no no no`, `1 nan no`) classify as command / new /
        data — i.e. are ACCEPTED, not raised as "Unrecognized QDP line".

  A-reference 2 — `parseNumber` + the masked-sentinel test (Triple 2 = the patched
  value loop `v.upper() == "NO"`). The modeled property: a token is read as a
  masked value exactly when it equals `NO` up to ASCII letter-case; otherwise it
  is the number `int(v) or float(v)`. Validated by reading one-row data files.

stdlib + astropy only. Exit 0 iff every observation holds on boundary + fuzz.

NOTE ON PATCH APPLICATION: the A-reference properties this check validates are
properties of the *patched* callees (case-invariance of `_line_type`, the
case-insensitive sentinel test) — they do NOT hold of the pre-fix code (that is
the bug the issue reports). The G-AX harness mounts this bundle at /work but does
not itself git-apply the gold patch to /testbed (unlike G-CONF). So this check
applies the mounted gold patch (`/work/patch.diff`) to /testbed itself, before
importing astropy, so it observes the FIXED callees. If /testbed already carries
the fix (idempotent re-run / pre-patched testbed), the apply is a no-op.
"""
import os
import random
import subprocess
import sys


def _ensure_patched():
    """Git-apply the bundle's gold patch to /testbed if it is not already
    applied, so the imported astropy is the FIXED code this check validates.

    The harness runs the frozen instance image, so /testbed is either exactly
    the unpatched base_commit or exactly the gold-patched tree. Both directions
    are checked so an unexpected/drifted tree errors loudly instead of silently
    validating against the wrong source."""
    patch = "/work/patch.diff"
    testbed = "/testbed"
    if not (os.path.isfile(patch) and os.path.isdir(testbed)):
        return  # not in the harness layout; assume caller arranged the fix

    def _check(*extra):
        return subprocess.run(["git", "apply", "--check", *extra, patch],
                              cwd=testbed, capture_output=True).returncode == 0

    forward = _check()               # patch applies cleanly => tree is unpatched
    reverse = _check("--reverse")    # reverse applies cleanly => tree is patched
    if forward and not reverse:
        subprocess.run(["git", "apply", patch], cwd=testbed, check=True,
                       capture_output=True)
    elif reverse and not forward:
        return                       # already gold-patched: no-op
    else:
        raise SystemExit(
            f"G-AX ERROR: unexpected /testbed state (forward={forward}, "
            f"reverse={reverse}); cannot establish gold-patched reference")


_ensure_patched()

import numpy as np
from astropy.io.ascii.qdp import _line_type, _get_tables_from_qdp_file

SEED = 20240629
N_FUZZ = 20_000


def ascii_case_variant(rng, s):
    return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in s)


# Building blocks for plausible QDP lines.
CMD_TOKENS = ["READ", "SERR", "TERR", "read", "serr", "terr"]
DATA_TOKENS = ["1", "0.5", "-2.5", "1e3", ".04", "-3", "NO", "no", "No",
               "nan", "NAN", "+7", "2.0"]
NEW_TOKENS = ["NO", "no", "No", "nO"]


def gen_line(rng):
    kind = rng.random()
    if kind < 0.3:                       # command-ish
        n = rng.randint(2, 5)
        return " ".join(rng.choice(CMD_TOKENS) for _ in range(n))
    elif kind < 0.5:                     # new-block-ish (NO NO ...)
        n = rng.randint(2, 5)
        return " ".join(rng.choice(NEW_TOKENS) for _ in range(n))
    else:                                # data-ish
        n = rng.randint(1, 6)
        return " ".join(rng.choice(DATA_TOKENS) for _ in range(n))


def check_case_invariance(rng):
    """A-reference 1(a): _line_type is invariant under ASCII letter-case."""
    fails = 0
    for _ in range(N_FUZZ):
        line = gen_line(rng)

        def cls(s):
            try:
                return ("ok", _line_type(s))
            except ValueError:
                return ("raise", None)

        base = cls(line)
        var = cls(ascii_case_variant(rng, line))
        if base != var:
            fails += 1
            if fails <= 10:
                print(f"CASE-VARIANCE: {line!r} -> {base}  vs variant -> {var}")
    return fails


def check_issue_lines():
    """A-reference 1(b): the lower-case lines the issue reports are ACCEPTED and
    classify the same as their upper-case forms."""
    pairs = [
        ("READ SERR 1 2", "read serr 1 2"),
        ("READ TERR 1", "read terr 1"),
        ("NO NO NO", "no no no"),
        ("1 NO 2", "1 no 2"),
        ("1 NAN 2", "1 nan 2"),
    ]
    fails = 0
    for up, lo in pairs:
        try:
            cu = _line_type(up)
        except ValueError:
            cu = "RAISE"
        try:
            cl = _line_type(lo)
        except ValueError:
            cl = "RAISE"
        if cu == "RAISE" or cl != cu:
            fails += 1
            print(f"ISSUE-LINE: {up!r}->{cu}  {lo!r}->{cl}  (expected equal, accepted)")
    return fails


def check_sentinel(rng):
    """A-reference 2: a token reads as masked iff it equals NO up to ASCII case;
    otherwise it is the parsed number."""
    fails = 0
    tokens_pool = ["NO", "no", "No", "nO", "1", "-3", "0.5", "2.0", "+7", "42"]
    for _ in range(N_FUZZ):
        ncol = rng.randint(1, 5)
        toks = [rng.choice(tokens_pool) for _ in range(ncol)]
        line = " ".join(toks)
        try:
            tables = _get_tables_from_qdp_file([line])
        except Exception:
            continue
        if len(tables) != 1:
            continue
        t = tables[0]
        if len(t) != 1 or len(t.colnames) != ncol:
            continue
        row = t[0]
        for v, cell in zip(toks, row):
            masked = bool(np.ma.is_masked(cell))
            want_masked = (v.upper() == "NO")
            if masked != want_masked:
                fails += 1
                if fails <= 10:
                    print(f"SENTINEL: token {v!r} masked={masked} want={want_masked}")
            elif not masked:
                want = int(v) if _is_int(v) else float(v)
                if float(cell) != float(want):
                    fails += 1
                    if fails <= 10:
                        print(f"PARSE: token {v!r} -> {cell} want {want}")
    return fails


def _is_int(tok):
    try:
        int(tok)
        return True
    except ValueError:
        return False


def main():
    rng = random.Random(SEED)
    total = 0
    total += check_case_invariance(rng)
    total += check_issue_lines()
    total += check_sentinel(rng)
    if total == 0:
        print(f"G-AX OK: A-reference properties hold on boundary + fuzz "
              f"(seed={SEED}, N={N_FUZZ})")
        sys.exit(0)
    print(f"G-AX FAIL: {total} violation(s)")
    sys.exit(1)


if __name__ == "__main__":
    main()
