#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11848 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The impl is plain integer arithmetic — no
PSeq carrier, no @Pure helpers used by the impl, no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.utils.http.parse_http_date`, exercised on its two-digit-year branch.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Bridges (mapping.md section 2):
  * `two_digit_year` <-> the two-digit year field of an RFC850-format date
    string fed to the real parser. We drive the parser with
    'Sunday, 06-Nov-%02d 08:49:37 GMT' so the parsed two-digit value is
    exactly our input (identity on the integer, per the mapping).
  * `reference_year` <-> the value the wall-clock source returns inside the
    parser. The repo's own regression tests pin that source with
    unittest.mock; we use the identical patch target so the oracle sees our
    chosen reference year (identity on the integer value, per the mapping).
  * `Result()` <-> the full year embedded in the parser's return value. The
    parser returns epoch seconds; we recover the calendar year with pure
    datetime+timedelta arithmetic (no OS gmtime, so no platform range limits).

Input domain: Requires demands 0 <= two_digit_year < 100 and
reference_year >= 1000. The oracle additionally constructs a calendar datetime,
which caps representable years at 9999; since the expansion can land up to 50
years past the reference year, fuzzed reference years stay in 1000..9949 so
every oracle observation is representable. That is a restriction of the
harness, not of the shadow (the shadow is checked on the same points).

>= 1e5 Requires-satisfying inputs: exhaustive 0..99 over boundary reference
years + 7 repo-test-pinned cases + 1000 fuzz reference years x all 100
two-digit inputs = >100,000 comparisons. Pinned fuzz seed: 11848.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from datetime import datetime, timedelta
from unittest import mock

SEED = 11848
N_FUZZ_REFS = 1000  # x 100 two-digit years each = 100,000 fuzz comparisons

EPOCH = datetime(1970, 1, 1)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def expand_two_digit_year(two_digit_year, reference_year):
    base = reference_year - (reference_year % 100)
    if two_digit_year - (reference_year % 100) > 50:
        # More than fifty years ahead: roll back to the previous century.
        result = two_digit_year + base - 100
    else:
        result = two_digit_year + base
    return result


# --- oracle plumbing -----------------------------------------------------------

def oracle_year(parse_http_date, two_digit_year, reference_year):
    """Run the REAL patched parser on a two-digit-year date stamp with the
    wall-clock source pinned to `reference_year`; return the full year the
    parser resolved."""
    stamp = 'Sunday, 06-Nov-%02d 08:49:37 GMT' % two_digit_year
    with mock.patch('django.utils.http.datetime.datetime') as mocked:
        mocked.side_effect = datetime          # constructor stays real
        mocked.utcnow = mock.Mock(return_value=datetime(reference_year, 6, 15))
        parsed = parse_http_date(stamp)
    # epoch seconds -> calendar year, via pure arithmetic (works for any year
    # a datetime can represent, including pre-1970 negative epochs)
    return (EPOCH + timedelta(seconds=parsed)).year


def check_one(parse_http_date, two_digit_year, reference_year):
    shadow = expand_two_digit_year(two_digit_year, reference_year)
    real = oracle_year(parse_http_date, two_digit_year, reference_year)
    if shadow != real:
        return ("DISAGREEMENT\n  two_digit_year=%d reference_year=%d\n"
                "  shadow=%d\n  real=%d"
                % (two_digit_year, reference_year, shadow, real))
    return None


# --- input sets ------------------------------------------------------------------

def boundary_reference_years():
    return [
        1000,            # Requires lower bound
        1900, 1970, 1999, 2000,
        2019, 2020, 2026, 2048,  # repo-test-pinned + current era
        2049, 2050, 2051,        # mid-century threshold stress
        2069, 2099, 2100, 2101, 2150,
        1100, 1150, 1199,        # early-century stress
        2999, 9949,              # far future (oracle-representable cap)
    ]


# (utcnow_year, two_digit_year, expected_full_year) — the repo regression
# test's pinned observations, re-checked here against BOTH shadow and oracle.
PINNED = [
    (2019, 69, 2069),
    (2019, 70, 1970),
    (2019, 94, 1994),
    (2020, 70, 2070),
    (2020, 71, 1971),
    (2048, 0, 2000),
    (2048, 99, 1999),
]


def main():
    from django.utils.http import parse_http_date  # REAL patched callee

    checked = 0

    # exhaustive two-digit domain over boundary reference years
    for ref in boundary_reference_years():
        for tdy in range(100):
            err = check_one(parse_http_date, tdy, ref)
            if err:
                print(err)
                return 1
            checked += 1

    # pinned cases: shadow must also match the recorded expected value
    for ref, tdy, expected in PINNED:
        err = check_one(parse_http_date, tdy, ref)
        if err:
            print(err)
            return 1
        got = expand_two_digit_year(tdy, ref)
        if got != expected:
            print("DISAGREEMENT (pinned)\n  two_digit_year=%d reference_year=%d"
                  "\n  shadow=%d\n  expected=%d" % (tdy, ref, got, expected))
            return 1
        checked += 1

    # fuzz: random reference years, full two-digit domain each
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_REFS):
        ref = rng.randint(1000, 9949)
        for tdy in range(100):
            err = check_one(parse_http_date, tdy, ref)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real parser's two-digit-year expansion "
          "on %d inputs (boundary exhaustive + %d pinned + %d fuzz refs x 100, "
          "seed %d)." % (checked, len(PINNED), N_FUZZ_REFS, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
