#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14373.

The bundle models ONE function: `DateFormat.Y` (the year-rendering method). Its
Lean implementation (`implementation_renderYear`) renders the year as its base-ten
numeral left-padded with '0' to a minimum width of 4:

    return padZeros(4, str(year))           # padZeros prepends max(0, 4-len) zeros

This script transliterates that R/I impl into Python (`shadow_render`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `DateFormat.Y` (`django/utils/dateformat.py`), together
with the `str(...)` wrapper that `Formatter.format` applies to every specifier's
return value:

    str('%04d' % self.data.year)

We do NOT instantiate a real `DateFormat` / datetime object: the modeled value is
a pure function of the integer year, and the post-patch method reads only
`self.data.year`. We reproduce the exact rendering the patched code performs
(`'%04d' % year`) and the formatter's `str(...)` wrapper (an identity on the
already-string result), per mapping.md.

The differential genuinely tests the Lean modeling: the shadow mirrors Lean's
`padZeros 4 (toString year)` (manual leading-zero padding to width 4), whereas the
oracle reproduces the patched `'%04d' % year`. They must agree for every input —
in particular for years < 1000, where the patch newly forces leading zeros
(pre-patch rendered the bare numeral, e.g. '1', '999').

stdlib-only; deterministic built-in fuzzer. Pinned seed: 14373 (also in mapping.md).
"""
import sys

SEED = 14373
N = 120_000


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# Post-patch `DateFormat.Y` returns `'%04d' % self.data.year`; `Formatter.format`
# then wraps it in `str(...)` (identity on a string).
def oracle_render(year):
    return str('%04d' % year)


# --- shadow of implementation_renderYear (the R/I leg) -----------------------
# Mirrors Solution.lean: `padZeros 4 (toString year)`.
def _pad_zeros(width, s):
    # natural subtraction clamps to 0 when len(s) >= width (Lean `width - s.length`)
    pad = width - len(s) if len(s) < width else 0
    return ("0" * pad) + s


def shadow_render(year):
    return _pad_zeros(4, str(year))


def disagree(year):
    got = oracle_render(year)
    want = shadow_render(year)
    if got != want:
        return (year, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Boundaries around the width-4 threshold + the datetime year domain."""
    cases = [1, 2, 9, 10, 42, 76, 99, 100, 476, 999, 1000, 1001,
             1999, 2021, 9999, 10000, 12345, 99999]
    # the full real datetime year range endpoints
    cases += [1, 9999]
    return cases


def main() -> int:
    checked = 0

    for year in _enumerate_edge():
        d = disagree(year)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        # mix: ~half within the real datetime domain (1..9999), ~half broader
        r = next(rnd)
        if r & 1:
            year = (next(rnd) % 9999) + 1          # 1..9999 (datetime domain)
        else:
            year = next(rnd) % 1_000_000           # 0..999999 (rendering superset)
        d = disagree(year)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
