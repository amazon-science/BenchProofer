#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16667 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`dateText`,
              `pseudoTriple`, `orZero`, `allZeroTriple`) transliterated to Python
              over the *real* repo types (`str`), via the mapping.md bijection
              (`List Char` <-> `str`). The construct-and-format callee
              (`datetime.date(int(y),int(m),int(d))` + `strftime`) is the
              A-reference: it is left as the REAL callee here, NOT re-implemented
              (G-CONF isolates the R/I legs; the callee's faithfulness is G-AX's
              job). So the shadow IS the post-patch routing of the real callee's
              outcome:  rendered -> strftime text;  ValueError -> pseudo-ISO
              triple;  OverflowError -> "0-0-0".
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `SelectDateWidget.value_from_datadict` (the real correctness
              oracle, G-RESOLVE), called with all three components present.

They must agree on every all-present input (the branch `dateComponentsText`
models). Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image; django installed and
patched). stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import os
import random
import sys

SEED = 16667
N_FUZZ = 100_000


def _configure_django():
    """Minimal settings so get_format / sanitize_strftime_format work."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=True,
            USE_L10N=True,
            USE_TZ=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


# --- the R/I shadow: Solution.lean dateText / pseudoTriple, transliterated ----

def _or_zero(x):
    """orZero (pure region): empty component shows as '0', else verbatim."""
    return "0" if x == "" else x


def _pseudo_triple(y, m, d):
    """pseudoTriple (pure region): the three components, empties as '0',
    joined by '-'.  == the gold '%s-%s-%s' % (y or 0, m or 0, d or 0) for the
    str inputs in scope (each of y,m,d is a str; or-0 fires only on '')."""
    return "%s-%s-%s" % (_or_zero(y), _or_zero(m), _or_zero(d))


_ALL_ZERO_TRIPLE = "0-0-0"   # allZeroTriple (pure region)


def shadow_value(y, m, d, input_format):
    """dateComponentsText transliterated: route the REAL construct-and-format
    callee's outcome (A-reference, run real) per dateText (I).

    The unchanged framing of value_from_datadict (refinement.md §B) is reproduced
    so the shadow matches the FULL real method, not just the inner branch:
    the all-three-empty short-circuit returns None before the all-present branch.
    The fuzzer always supplies all three components as strings (never None), so
    the `y is not None and m is not None and d is not None` guard always holds and
    the trailing `return data.get(name)` is unreachable here."""
    import datetime
    if y == m == d == "":
        return None
    try:
        date_value = datetime.date(int(y), int(m), int(d))
    except OverflowError:
        return _ALL_ZERO_TRIPLE                 # .unrepresentable -> allZeroTriple
    except ValueError:
        return _pseudo_triple(y, m, d)          # .notCalendar    -> pseudoTriple
    return date_value.strftime(input_format)    # .rendered s      -> s


# --- the oracle: patch.diff's real SelectDateWidget.value_from_datadict -------

def make_oracle():
    from django.forms import SelectDateWidget
    w = SelectDateWidget()
    name = "mydate"
    yf, mf, df = w.year_field % name, w.month_field % name, w.day_field % name

    def oracle(y, m, d):
        data = {yf: y, mf: m, df: d}
        return w.value_from_datadict(data, {}, name)

    return oracle


def make_input_format():
    """Reproduce the input_format the widget computes, so the shadow's
    `rendered` payload matches the oracle's strftime exactly."""
    from django.utils import formats
    from django.utils.formats import get_format
    fmt = get_format("DATE_INPUT_FORMATS")[0]
    return formats.sanitize_strftime_format(fmt)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield (str(sys.maxsize + 1), "12", "1")        # F2P selectdatewidget overflow
    yield (str(sys.maxsize + 1), "31", "2010")     # F2P datefield overflow
    yield ("1234567821345678", "1", "1")           # problem-statement overflow
    yield ("2010", "1", "1")                        # ordinary valid date
    yield ("2010", "12", "31")
    yield ("0", "0", "0")
    yield ("", "", "")
    yield ("", "1", "1")
    yield ("2010", "", "1")
    yield ("2010", "1", "")
    yield ("abc", "1", "1")
    yield ("2010", "13", "1")
    yield ("2010", "2", "30")
    yield ("9999", "12", "31")
    yield ("10000", "1", "1")
    # long-range edges on each position
    for edge in [2 ** 31 - 1, 2 ** 31, -(2 ** 31), -(2 ** 31) - 1,
                 sys.maxsize, sys.maxsize + 1]:
        yield (str(edge), "6", "15")
        yield ("2010", str(edge), "15")
        yield ("2010", "6", str(edge))
    # overflow-vs-parse precedence
    yield ("abc", str(sys.maxsize + 1), "1")
    yield (str(sys.maxsize + 1), "abc", "1")

    digit_pool = "0123456789"
    junk_pool = "0123456789-+ .eExXabc"

    def num():
        k = rng.randint(1, 22)
        s = "".join(rng.choice(digit_pool) for _ in range(k))
        return ("-" + s) if rng.random() < 0.3 else s

    def junk():
        k = rng.randint(0, 12)
        return "".join(rng.choice(junk_pool) for _ in range(k))

    for _ in range(n):
        if rng.random() < 0.6:
            yield (num(), num(), num())
        else:
            yield (junk(), junk(), junk())


def main():
    _configure_django()
    oracle = make_oracle()
    input_format = make_input_format()

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (y, m, d) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_value(y, m, d, input_format)
        orc = oracle(y, m, d)
        if shadow != orc:
            disagreements.append(((y, m, d), shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for triple, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (triple, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of dateComponentsText agrees with patch.diff "
          "(patched value_from_datadict) on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
