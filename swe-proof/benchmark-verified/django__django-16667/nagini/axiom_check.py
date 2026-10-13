#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16667.

Executes the REAL platform calendar-date constructor (`datetime.date`, the
stdlib callee the widget invokes inside its guarded region) on representative
component triples of every construction outcome and asserts that each
observation matches the `construct_date` axiom encoded in model.py:

    kind 0 — the constructor ACCEPTS the components and returns normally;
    kind 1 — the constructor rejects them as not a real calendar date
             (`ValueError`, the out-of-range failure);
    kind 2 — the constructor rejects them because a component's magnitude
             exceeds the platform's native date representation
             (`OverflowError`, the capacity-overflow failure).

The axiom's contract (model.py axioms region) is:
    Requires(kind in {0,1,2})
    Ensures(kind == 0)                              # returns normally iff kind 0
    Exsures(DateOutOfRange,        kind == 1)       # ValueError
    Exsures(DateCapacityOverflow,  kind == 2)       # OverflowError

So soundness requires, for the REAL `datetime.date(int(y), int(m), int(d))`:
    - kind-0 components construct without raising;
    - kind-1 components raise EXACTLY ValueError;
    - kind-2 components raise EXACTLY OverflowError;
    - NO component triple escapes with any OTHER exception class — i.e.
      {OverflowError, ValueError} is EXHAUSTIVE for integer arguments, so the
      widget's two-handler `try` (`except ValueError` + the patch's
      `except OverflowError`) covers every failure. This exhaustiveness is the
      property the gold patch relies on.

It also confirms the patch sentinel "0-0-0" is the code-point list
[48,45,48,45,48] (model.py `zero_zero_zero`), and that the unchanged renderings
the model pins (`success_text` via strftime; `out_of_range_text` via the
"%s-%s-%s" fallback) are NON-EMPTY (so the absent value, modelled as the empty
list, is distinct from every text-producing branch).

Imports nothing repo-specific: `datetime`/`sys` are the Python standard library
— the same callee the widget invokes. Exit 0 iff every obligation holds.
"""
import datetime
import random
import sys


def real_kind(y, m, d):
    """Run the REAL datetime.date(int(y), int(m), int(d)) and report which
    construction outcome it exhibits: 0 (accepted), 1 (ValueError), 2
    (OverflowError), or None for an undeclared/escaping exception (UNSOUND)."""
    try:
        datetime.date(int(y), int(m), int(d))
        return 0
    except OverflowError:
        return 2
    except ValueError:
        return 1
    except Exception:  # noqa: BLE001 — any other class would be unsound
        return None


def check(y, m, d, expected_kind):
    observed = real_kind(y, m, d)
    assert observed is not None, (
        "construct_date axiom UNSOUND on (%r,%r,%r): datetime.date raised an "
        "exception class outside {OverflowError, ValueError}; the widget's "
        "two-handler try does not cover it" % (y, m, d))
    assert observed == expected_kind, (
        "construct_date axiom UNSOUND on (%r,%r,%r): expected outcome kind %d, "
        "real datetime.date exhibited kind %d"
        % (y, m, d, expected_kind, observed))


def main():
    big = sys.maxsize + 1            # the exact F2P overflow trigger
    bigger = 10 ** 30
    neg_big = -(2 ** 70)

    # ---- kind 0: constructor ACCEPTS (valid, representable calendar date) -----
    accepted = [
        (2000, 12, 1), (2010, 1, 1), (1, 1, 1), (9999, 12, 31),
        (2016, 2, 29),                     # leap day
        (2017, 2, 28), (2020, 11, 30), ("2000", "12", "1"),
        ("0002010", "01", "09"),           # leading-zero text still parses
    ]
    for (y, m, d) in accepted:
        check(y, m, d, 0)

    # ---- kind 1: out-of-range / not a real calendar date -> ValueError --------
    out_of_range = [
        (2010, 13, 1), (2010, 0, 1), (2010, 2, 31), (2010, 1, 0),
        (2010, 4, 31), (2015, 2, 29),      # non-leap Feb 29
        (0, 1, 1), (10000, 1, 1), (-1, 1, 1),
        (2010, -1, 1), (2010, 1, -5),
    ]
    for (y, m, d) in out_of_range:
        check(y, m, d, 1)

    # int() of blank / non-numeric text also raises ValueError (it shares the
    # widget's `except ValueError` branch) — confirm it is kind 1, never an
    # escape.
    for bad in ["", "abc", "  ", "1.5", "0x10", "2010a"]:
        check(bad, "12", "1", 1)

    # ---- kind 2: capacity-overflow (magnitude exceeds C long) -> OverflowError -
    overflow = [
        (big, 12, 1),                      # the exact F2P input
        (big, 0, 0), (big, 13, 40),        # overflow takes precedence over range
        (bigger, 1, 1), (neg_big, 2, 31),
        (1, big, 1), (1, 1, big),          # an overflowing month / day too
        (str(big), "12", "1"),             # as submitted text
        (str(bigger), "1", "1"),
    ]
    for (y, m, d) in overflow:
        check(y, m, d, 2)

    # ---- precedence witness: a too-large year with an ALSO-invalid month/day --
    # must be OverflowError (the C conversion runs first), so the F2P-style input
    # routes to the patch's overflow handler, never to the ValueError fallback.
    assert real_kind(big, 13, 40) == 2, "overflow must precede range ValueError"
    assert real_kind(big, 0, 0) == 2, "overflow must precede range ValueError"

    # ---- randomized fuzz: confirm exhaustiveness over a wide mix --------------
    rng = random.Random(16667)
    counts = {0: 0, 1: 0, 2: 0}
    for _ in range(200000):
        # bias towards boundaries: small ints, near-C-long, and far-overflow
        def comp():
            r = rng.randint(0, 3)
            if r == 0:
                return rng.randint(-3, 13000)
            if r == 1:
                return sys.maxsize + rng.randint(-4, 6)
            if r == 2:
                return rng.choice([10 ** 25, -(10 ** 25), 2 ** 64, -(2 ** 64)])
            return rng.randint(-50, 60)
        y, m, d = comp(), comp(), comp()
        k = real_kind(y, m, d)
        assert k is not None, (
            "construct_date axiom UNSOUND on (%r,%r,%r): datetime.date raised "
            "outside {OverflowError, ValueError}" % (y, m, d))
        counts[k] += 1
    assert counts[1] > 0 and counts[2] > 0 and counts[0] > 0, (
        "fuzz failed to exercise all three outcomes: %r" % (counts,))

    # ---- the patch sentinel "0-0-0" decodes to the model code points ----------
    assert [ord(c) for c in "0-0-0"] == [48, 45, 48, 45, 48], (
        "zero_zero_zero sentinel mismatch")

    # ---- the unchanged renderings the model pins are NON-EMPTY ----------------
    # success_text  <-  date_value.strftime(input_format)
    for (y, m, d) in accepted:
        dv = datetime.date(int(y), int(m), int(d))
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y", "%b %d %Y"):
            rendered = dv.strftime(fmt)
            assert len(rendered) > 0, (
                "success_text axiom UNSOUND: strftime produced empty text for "
                "%r with format %r" % (dv, fmt))
    # out_of_range_text  <-  "%s-%s-%s" % (y or 0, m or 0, d or 0)
    for (y, m, d) in [("", "13", "1"), ("2010", "", "31"), ("2010", "2", ""),
                      ("2010", "13", "40"), ("abc", "x", "y")]:
        fallback = "%s-%s-%s" % (y or 0, m or 0, d or 0)
        assert len(fallback) > 0, (
            "out_of_range_text axiom UNSOUND: pseudo-ISO fallback empty for "
            "(%r,%r,%r)" % (y, m, d))

    print("G-AX OK: construct_date axiom sound against real datetime.date on "
          "%d accepted + %d out-of-range + 6 bad-text + %d overflow boundary "
          "inputs and 200000 fuzz triples (outcomes %r); every rejection is "
          "EXACTLY one of {OverflowError, ValueError} and overflow precedes "
          "range. Sentinel '0-0-0' == [48,45,48,45,48]; strftime / pseudo-ISO "
          "renderings non-empty."
          % (len(accepted), len(out_of_range), len(overflow), counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
