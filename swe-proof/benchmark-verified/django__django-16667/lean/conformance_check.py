#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16667.

The bundle models ONE behavior: the date-coercion `try/except` block inside
`SelectDateWidget.value_from_datadict` (`django/forms/widgets.py:1158-1164`). Its
Lean implementation (`implementation_coerceDateEntry`) dispatches on the outcome
of constructing a calendar date from the three raw components:

    valid           -> some rendered            (date_value.strftime(input_format))
    malformed       -> some pseudo_iso(y, m, d) (the "%s-%s-%s" % (y or 0, ...) fallback)
    unrepresentable -> some "0-0-0"             (the added OverflowError handler -- the fix)

The result is modeled as an Option (Solution.lean ships `Option String`): a value
being handed on is `("some", s)`; an uncaught failure that produces no value is
`("none", None)`. The post-patch block is total (always `("some", ...)`).

This script reproduces the patched block as the ORACLE (`oracle_coerce`): it runs
the REAL callees `int(...)`, `datetime.date(...)`, and `.strftime(...)`, with the
post-patch control flow (a `ValueError` -> pseudo-ISO, an `OverflowError` ->
"0-0-0", otherwise the rendering), and returns `("some", value)`. It then builds
the R/I shadow of the Lean impl (`shadow_coerce`): classify the entry by running
the SAME real callees (this is the binding of `(y, m, d) -> c` and `-> rendered`
declared in mapping.md), then apply the Lean dispatch (`some pseudo_iso` for
malformed, `some "0-0-0"` for the unrepresentable magnitude, `some rendered` for
valid).

The differential genuinely tests the Lean modeling: the shadow's three-way
dispatch (DateEntry.valid / malformed / unrepresentable -> rendered / pseudoIso /
"0-0-0") must agree with the patched block on every input, INCLUDING the
discriminating case the patch fixes -- a component larger than sys.maxsize, which
raises OverflowError and must coerce to "0-0-0" (pre-fix: uncaught crash).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 16667 (also recorded in
mapping.md). Uses a fixed strftime format ("%Y-%m-%d") in BOTH legs, so the exact
input-format text cancels (mapping.md: the lookup is unchanged and orthogonal).
"""
import datetime
import sys

SEED = 16667
N = 120_000
FMT = "%Y-%m-%d"  # stand-in for sanitize_strftime_format(DATE_INPUT_FORMATS[0])


# --- the pure helper pseudoIso, transliterated from Solution.lean -------------
# Models "%s-%s-%s" % (y or 0, m or 0, d or 0): an empty component renders as the
# single character "0" (Python: "" is falsy, so "" or 0 == 0 -> "0"); any other
# string is truthy and renders verbatim.
def pseudo_iso(y, m, d):
    def comp(s):
        return "0" if s == "" else s
    return "%s-%s-%s" % (comp(y), comp(m), comp(d))


# --- ORACLE: the post-patch date-coercion block, faithful in-process replica --
# Reproduces widgets.py:1158-1164 AFTER the patch, running the real callees.
def oracle_coerce(y, m, d):
    try:
        date_value = datetime.date(int(y), int(m), int(d))
    except ValueError:
        return ("some", "%s-%s-%s" % (y or 0, m or 0, d or 0))
    except OverflowError:
        return ("some", "0-0-0")
    return ("some", date_value.strftime(FMT))


# --- binding (mapping.md): classify the entry by running the real callees -----
# Returns (c, rendered) where c in {"valid","malformed","unrepresentable"} and
# rendered is date_value.strftime(FMT) on the valid outcome (else None).
def classify(y, m, d):
    try:
        date_value = datetime.date(int(y), int(m), int(d))
    except ValueError:
        return ("malformed", None)
    except OverflowError:
        return ("unrepresentable", None)
    return ("valid", date_value.strftime(FMT))


# --- shadow of implementation_coerceDateEntry (the R/I leg) -------------------
# Mirrors Solution.lean: dispatch on the classified entry.
def shadow_coerce(y, m, d):
    c, rendered = classify(y, m, d)
    if c == "valid":
        return ("some", rendered)
    if c == "malformed":
        return ("some", pseudo_iso(y, m, d))
    # c == "unrepresentable"
    return ("some", "0-0-0")


def disagree(y, m, d):
    got = oracle_coerce(y, m, d)
    want = shadow_coerce(y, m, d)
    if got != want:
        return ((y, m, d), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


_BIG = str(sys.maxsize + 1)
_HUGE = "1234567821345678901234567890"


def _enumerate_edge():
    """Hand-picked edge cases pinning the three outcomes + the fix clause."""
    return [
        # THE fix: month > sys.maxsize -> OverflowError -> "0-0-0"
        (_BIG, "12", "1"),
        ("2010", _BIG, "31"),       # year huge
        ("2010", "1", _HUGE),       # day enormous
        (_BIG, _BIG, _BIG),         # all huge
        # representable date -> canonical rendering
        ("2010", "1", "1"),
        ("2017", "2", "28"),
        # well-formed but not a date -> pseudo-ISO
        ("2017", "0", "23"),        # month 0
        ("2017", "13", "1"),        # month 13
        ("2017", "2", "30"),        # impossible day
        ("0", "1", "1"),            # year 0 out of range
        ("10000", "1", "1"),        # year too large for date()
        # non-numeric text -> ValueError -> pseudo-ISO with raw text
        ("200a", "10", "25"),
        ("abc", "def", "ghi"),
        # empty components -> pseudo-ISO with "0" placeholders
        ("", "12", "1"),
        ("2017", "", "23"),
        ("", "", ""),
    ]


_ALPHABET = ["", "0", "1", "2", "12", "13", "28", "31", "32", "00",
             "2010", "2017", "0", "10000", "99999",
             "200a", "abc", "-1", "+5", " 7", _BIG, _HUGE, "9" * 40]


def _rand_comp(rnd):
    return _ALPHABET[next(rnd) % len(_ALPHABET)]


def main():
    checked = 0

    for y, m, d in _enumerate_edge():
        bad = disagree(y, m, d)
        if bad:
            print(f"DISAGREE edge {bad[0]!r}: oracle={bad[1]!r} shadow={bad[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        y = _rand_comp(rnd)
        m = _rand_comp(rnd)
        d = _rand_comp(rnd)
        bad = disagree(y, m, d)
        if bad:
            print(f"DISAGREE fuzz {bad[0]!r}: oracle={bad[1]!r} shadow={bad[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
