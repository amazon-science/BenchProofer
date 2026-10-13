#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13569.

The bundle models ONE function: `Random.get_group_by_cols`
(`django/db/models/functions/math.py`). Its Lean implementation
(`randomGroupingColumns`) returns the list of grouping columns that a
non-deterministic ordering term contributes to an aggregated result set. Post-fix
this is the empty list for every receiver and alias:

    return []

This script transliterates that R/I impl into Python (`shadow_cols`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `Random.get_group_by_cols`:

    def get_group_by_cols(self, alias=None):
        return []

We do NOT stand up a Django expression/compiler stack (heavy, and the modeled
value is a constant list). Instead we feed both sides the SAME observable inputs
the real method consumes (mapping.md): the random term (modeled by its emitted SQL
function name) and the optional `alias`. The oracle reproduces the patched
constant-`[]` return; the shadow reaches the same result via the Lean impl. They
must agree for every input — for any function name and any alias (present or
absent).

The downstream consumer `SQLCompiler.get_group_by` extends the GROUP BY with this
list per non-ref order_by term; an empty contribution is exactly the property the
FAIL_TO_PASS test `test_aggregation_random_ordering` depends on (random ordering
adds no grouping column).

stdlib-only; pinned seed 13569 (also recorded in mapping.md).
"""
import sys

SEED = 13569
N = 120_000

FUNCTIONS = ["RANDOM", "RAND", "DBMS_RANDOM.VALUE", "", "RANDOM()", "X", "rand"]
ALIASES = [None, "", "a", "col1", "alias", "RANDOM"]


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# `Random.get_group_by_cols(self, alias=None)` returns [] unconditionally.
def oracle_cols(function, alias):
    return []


# --- shadow of randomGroupingColumns (the R/I leg) ---------------------------
# Mirrors Solution.lean: return []  (constant empty grouping-column list).
def shadow_cols(function, alias):
    return []


def disagree(args):
    got = oracle_cols(*args)
    want = shadow_cols(*args)
    if got != want:
        return (args, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked cases exercising the function/alias inputs."""
    cases = []
    cases.append(("RANDOM", None))
    cases.append(("RAND", None))
    cases.append(("DBMS_RANDOM.VALUE", None))
    cases.append(("RANDOM", "rc"))
    cases.append(("", ""))
    cases.append(("RANDOM", "RANDOM"))
    return cases


def main() -> int:
    checked = 0

    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        function = FUNCTIONS[next(rnd) % len(FUNCTIONS)]
        alias = ALIASES[next(rnd) % len(ALIASES)]
        d = disagree((function, alias))
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
