#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13670 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The @Pure helpers `tens_digit` / `units_digit` copy over as
plain functions. No PSeq is used (the impl builds a plain 2-element list) and
there are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.utils.dateformat.DateFormat.y`, invoked on a `DateFormat` built over a
real `datetime.date` carrying the year under test (a date carries no timezone,
so no Django settings are required; the method reads only `self.data.year`).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2): the model's `year: int` is exactly
`self.data.year`; the repo method returns a `str`, the model a `List[int]` of
its Unicode code points, so the oracle output is lifted via `ord` per
character before comparison.

Input domain: Requires admits 1 <= year <= 9999 (datetime's documented year
range). That domain has only 9999 points, so it is covered EXHAUSTIVELY —
every admitted year is checked — and then topped up with 100000 pinned-seed
fuzz redraws over the same range to satisfy the >=1e5-input contract.
Pinned fuzz seed: 13670.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import datetime
import json
import random
import sys

SEED = 13670
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped ---------------------------

def tens_digit(v):
    """Code point of the tens digit of a value in 0..99."""
    return 48 + (v // 10)


def units_digit(v):
    """Code point of the units digit of a value in 0..99."""
    return 48 + (v % 10)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def abbreviated_year(year):
    v = year % 100
    result = [tens_digit(v), units_digit(v)]  # type: List[int]
    return result


# --- bridge + differential check ----------------------------------------------

def real_render(DateFormat, year):
    """Real repo method output for the given year, lifted to code points."""
    df = DateFormat(datetime.date(year, 1, 1))
    s = df.y()
    return [ord(ch) for ch in s]


def check_year(DateFormat, year):
    shadow = abbreviated_year(year)
    real = real_render(DateFormat, year)
    if shadow != real:
        return ("DISAGREEMENT\n  year=%d\n  shadow=%r\n  real=%r"
                % (year, shadow, real))
    return None


def main():
    from django.utils.dateformat import DateFormat  # REAL patched callee

    checked = 0

    # Exhaustive sweep of the entire admitted domain (boundaries included:
    # 1, 9, 10, 99, 100, 999, 1000, 9999 are all in range).
    for year in range(1, 10000):
        err = check_year(DateFormat, year)
        if err:
            print(err)
            return 1
        checked += 1

    # Pinned-seed fuzz top-up to reach >= 1e5 Requires-satisfying inputs.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_year(DateFormat, rng.randint(1, 9999))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real renderer on %d inputs "
          "(9999 exhaustive over the admitted domain + %d fuzz, seed %d)."
          % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
