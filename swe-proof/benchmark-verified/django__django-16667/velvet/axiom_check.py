#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16667.

Solution.lean models the construct-and-format step
`datetime.date(int(y),int(m),int(d))` then (on success) `.strftime(...)` as a
FREE INPUT `outcome : ConstructOutcome` with three mutually-exclusive shapes:

    rendered s     -- a valid calendar date, formatted to the str s
    notCalendar    -- the components name no valid calendar date (ValueError)
    unrepresentable -- a parsed component is out of C-long range (OverflowError)

This callee is UNCHANGED by the patch (only the handling of its OverflowError
outcome changes), so there is no consumed axiom and no pinned output value — the
model is the weakest possible (a free input; directive 7). What G-AX MUST still
establish is that this three-way partition is an A-reference faithful to the
real callee:

  (1) TOTAL/well-defined: the real `datetime.date(int(y),int(m),int(d))` always
      lands in EXACTLY ONE of the three shapes — it never produces a fourth
      outcome the routing fails to handle (no exception type other than
      ValueError / OverflowError, and the success/exception cases are disjoint).

  (2) FAITHFUL: the shape the real callee produces matches the documented
      predicate (mapping.md §3.1):
        - OverflowError  <=> every component parses as int AND some parsed value
                             is outside the signed C-long range [-2**31, 2**31-1];
        - ValueError     <=> not OverflowError AND (a component fails int() OR
                             the in-range (y,m,d) is not a valid calendar date);
        - constructed    <=> otherwise.

If the partition were not total, the `match outcome with ...` in Solution.lean
would be missing a case the real world can hit, and `verify => correct` would be
unsound. This check refutes that over boundary + fuzz inputs.

Imports nothing repo-specific: `datetime` is the Python standard library — the
exact module the widget's `datetime.date(int(y), int(m), int(d))` call uses.
Exit 0 iff every obligation holds.
"""
import datetime
import random
import sys

# signed C-long range that datetime.date()'s C argument conversion accepts;
# a parsed component outside this raises OverflowError before calendar checks.
LONG_MIN = -(2 ** 31)
LONG_MAX = 2 ** 31 - 1


def real_outcome(y, m, d):
    """Run the REAL widget callee and report which of the three shapes it lands
    in. Any OTHER exception type is a partition violation (returned as 'OTHER')."""
    try:
        date_value = datetime.date(int(y), int(m), int(d))
    except OverflowError:
        return "unrepresentable"
    except ValueError:
        return "notCalendar"
    except Exception as e:  # pragma: no cover - the violation we are hunting
        return "OTHER:%s" % type(e).__name__
    # success path: strftime must also succeed for the `rendered` payload to
    # exist; if strftime itself raised we would have a fourth outcome.
    try:
        date_value.strftime("%Y-%m-%d")
    except Exception as e:  # pragma: no cover
        return "OTHER-strftime:%s" % type(e).__name__
    return "rendered"


def predicted_outcome(y, m, d):
    """The documented partition predicate (mapping.md §3.1), computed WITHOUT
    catching datetime's exceptions — a pure decision procedure. G-AX asserts
    real_outcome == predicted_outcome on every input, so the model's three-way
    split is proven total and faithful, not merely 'never observed otherwise'."""
    parsed = []
    for comp in (y, m, d):
        try:
            parsed.append(int(comp))
        except ValueError:
            return "notCalendar"        # int() rejects -> ValueError, parse-first
    if any(v < LONG_MIN or v > LONG_MAX for v in parsed):
        return "unrepresentable"        # out-of-long -> OverflowError
    # all in range: valid calendar date or not
    yy, mm, dd = parsed
    if 1 <= yy <= 9999 and 1 <= mm <= 12 and 1 <= dd <= _days_in_month(yy, mm):
        return "rendered"
    return "notCalendar"


def _days_in_month(year, month):
    import calendar
    return calendar.monthrange(year, month)[1]


def check_triple(y, m, d):
    real = real_outcome(y, m, d)
    assert not real.startswith("OTHER"), (
        "PARTITION NOT TOTAL on (%r,%r,%r): real callee produced %s — a fourth "
        "outcome ConstructOutcome does not model." % (y, m, d, real))
    pred = predicted_outcome(y, m, d)
    assert real == pred, (
        "PARTITION UNFAITHFUL on (%r,%r,%r): real callee -> %s, model predicts "
        "%s" % (y, m, d, real, pred))


def main():
    boundary = []
    # the F2P / problem-statement triggers
    boundary += [
        (str(sys.maxsize + 1), "12", "1"),      # F2P selectdatewidget overflow
        (str(sys.maxsize + 1), "31", "2010"),   # F2P datefield month overflow
        ("1234567821345678", "1", "1"),         # problem-statement year overflow
        ("2010", "1", "1"),                     # ordinary valid date
        ("0", "0", "0"),                        # the "0-0-0" components
    ]
    # signed C-long edges on each of the three positions
    for edge in [LONG_MAX, LONG_MAX + 1, LONG_MIN, LONG_MIN - 1,
                 sys.maxsize, sys.maxsize + 1, -sys.maxsize - 2,
                 2 ** 63, -(2 ** 63) - 1]:
        boundary += [
            (str(edge), "6", "15"),
            ("2010", str(edge), "15"),
            ("2010", "6", str(edge)),
        ]
    # calendar edges (all in long-range; exercise the ValueError vs constructed split)
    boundary += [
        ("0", "1", "1"), ("1", "1", "1"), ("9999", "12", "31"),
        ("10000", "1", "1"), ("2010", "13", "1"), ("2010", "0", "1"),
        ("2010", "2", "29"), ("2011", "2", "29"), ("2012", "2", "29"),
        ("2010", "2", "30"), ("2010", "4", "31"), ("2010", "1", "0"),
        ("-1", "1", "1"),
    ]
    # parse-failure / non-numeric / empty (ValueError before any overflow)
    boundary += [
        ("", "1", "1"), ("2010", "", "1"), ("2010", "1", ""),
        ("", "", ""), ("abc", "1", "1"), ("2010", "xy", "1"),
        ("1.5", "1", "1"), ("0x10", "1", "1"), ("  5 ", "6", "15"),
        # parse-first vs overflow precedence: non-numeric beside an overflow value
        ("abc", str(sys.maxsize + 1), "1"),
        (str(sys.maxsize + 1), "abc", "1"),
        (str(sys.maxsize + 1), "13", "1"),   # overflow takes priority over bad month
        (str(sys.maxsize + 1), "2", "30"),   # overflow takes priority over bad day
    ]
    for t in boundary:
        check_triple(*t)

    # randomized fuzz: mix of digit strings (incl. very large), signs, junk
    rng = random.Random(16667)
    digit_pool = "0123456789"
    junk_pool = "0123456789-+ .eExXabc"

    def gen_numeric():
        k = rng.randint(1, 22)
        s = "".join(rng.choice(digit_pool) for _ in range(k))
        if rng.random() < 0.3:
            s = "-" + s
        return s

    def gen_junk():
        k = rng.randint(0, 12)
        return "".join(rng.choice(junk_pool) for _ in range(k))

    N = 200_000
    for _ in range(N):
        if rng.random() < 0.6:
            t = (gen_numeric(), gen_numeric(), gen_numeric())
        else:
            t = (gen_junk(), gen_junk(), gen_junk())
        check_triple(*t)

    print("G-AX OK: ConstructOutcome 3-way partition (rendered/notCalendar/"
          "unrepresentable) is TOTAL and FAITHFUL to the real "
          "datetime.date(int(y),int(m),int(d)) callee on %d boundary + %d fuzz "
          "triples; 0 fourth-outcome violations, 0 predicate mismatches."
          % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
