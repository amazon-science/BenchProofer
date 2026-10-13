#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14373 (nagini).

SHADOW: the impl region of model.py (`render_year`), copied verbatim below
with the contract calls (Requires/Ensures/Assert) stripped. The @Pure helpers
`digit` / `thousands` / `hundreds` / `tens` / `units` copy over as plain
functions. `four_field` and the PSeq carrier appear only inside contracts
(Ensures/Assert), so they have no runtime role here. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.utils.dateformat.DateFormat.Y`, the `Y` format-specifier handler. The
gate applies patch.diff to /testbed before this script runs; PYTHONPATH=
/testbed makes the patched module importable. `Y` reads only the wrapped
value's `year` attribute, so the oracle is exercised through a
`datetime.date` carrier (constructing the formatter from a plain date keeps
the check independent of timezone configuration; settings are configured
minimally and defensively regardless).

Type bridge (mapping.md section 2):
  * model input `year: int`, `1 <= year <= 9999` — exactly the CPython
    `datetime` year domain — concretizes to `date(year, month, day)` whose
    `.year` is that integer (month/day are irrelevant to the mapped symbol
    and are varied freely during fuzzing);
  * the model result, a List[int] of ASCII code points, compares against the
    oracle's `str` result via `[ord(ch) for ch in s]` (result[k] <-> ord(s[k]),
    len <-> len).

Input domain: every Requires-satisfying year 1..9999 is checked exhaustively
(so coverage of the modeled domain is total), plus the explicit boundary
years, plus 100000 fuzz draws with randomized month/day to confirm the
oracle's independence from the non-year components. Total > 1e5 inputs.
Pinned fuzz seed: 14373.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import datetime
import json
import random
import sys

SEED = 14373
N_FUZZ = 100_000


# --- pure helpers from model.py, decorators/contracts stripped ---------------

def digit(d):
    return 48 + d


def thousands(year):
    return year // 1000


def hundreds(year):
    return (year // 100) % 10


def tens(year):
    return (year // 10) % 10


def units(year):
    return year % 10


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def render_year(year):
    result = []  # type: list
    result.append(digit(thousands(year)))
    result.append(digit(hundreds(year)))
    result.append(digit(tens(year)))
    result.append(digit(units(year)))
    return result


# --- oracle plumbing ----------------------------------------------------------

def check_year(DateFormat, year, month=1, day=1):
    """Run shadow and oracle on one year; return an error string on
    disagreement, else None."""
    shadow = render_year(year)
    real = DateFormat(datetime.date(year, month, day)).Y()
    real_points = [ord(ch) for ch in str(real)]
    if real_points != shadow:
        return ("DISAGREEMENT\n  year=%d (month=%d day=%d)\n"
                "  shadow=%r (%r)\n  real=%r (%r)"
                % (year, month, day, shadow,
                   ''.join(chr(c) for c in shadow), real_points, real))
    return None


BOUNDARY_YEARS = [1, 4, 9, 10, 42, 99, 100, 476, 500, 999,
                  1000, 1001, 1999, 2021, 9000, 9998, 9999]


def main():
    # Defensive minimal settings: the mapped symbol itself does not touch
    # settings for date inputs, but the formatter module lives inside a
    # settings-aware package.
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=False)
    from django.utils.dateformat import DateFormat  # REAL patched callee

    checked = 0
    for year in BOUNDARY_YEARS:
        err = check_year(DateFormat, year)
        if err:
            print(err)
            return 1
        checked += 1

    # Exhaustive sweep of the entire Requires domain.
    for year in range(1, 10000):
        err = check_year(DateFormat, year)
        if err:
            print(err)
            return 1
        checked += 1

    # Fuzz: random years with randomized month/day carriers.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        year = rng.randint(1, 9999)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        err = check_year(DateFormat, year, month, day)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real formatter on %d inputs "
          "(%d boundary + 9999 exhaustive + %d fuzz, seed %d)."
          % (checked, len(BOUNDARY_YEARS), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
