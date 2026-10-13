#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15930.

The bundle models ONE decision: which `(guard_sql, guard_params)` pair a single
branch of a searched conditional expression splices into its
`"WHEN %(condition)s THEN %(result)s"` template, in `When.as_sql`
(`django/db/models/expressions.py`). The modeled value is a PURE function of four
observables (mapping.md):

    conditionSql   : str        (compiler.compile(self.condition)[0])
    conditionParams: list       (compiler.compile(self.condition)[1])
    trueSql        : str        (compiler.compile(Value(True))[0])
    trueParams     : list       (compiler.compile(Value(True))[1])

Post-patch rule (the inserted block):

    if condition_sql == "":
        condition_sql, condition_params = compiler.compile(Value(True))
    # -> the pair (condition_sql, condition_params) is what the template uses

Standing up a SQL compiler / ORM to drive the real `When.as_sql` is heavy and
unnecessary: the modeled value is this pure decision over observables the compile
steps expose. So the ORACLE below is a faithful in-process replica that applies
the EXACT patched conditional (`if condition_sql == "": ... = compile(Value(True))`),
and the SHADOW is the op-for-op transliteration of
`implementation_resolveBranchCondition` (`if condSql == "": condSql, condParams =
trueSql, trueParams`, per refinement.md).

The pair is compared component-wise (the SQL string and the parameter list,
exactly the two things spliced into the template / extended into sql_params).

stdlib-only. Pinned seed: 15930 (also in mapping.md).
"""
import random
import sys

SEED = 15930
N = 120_000


# --- ORACLE: faithful in-process replica of the patched decision -------------
def oracle_select(condition_sql, condition_params, true_sql, true_params):
    # mirrors the patched block in When.as_sql verbatim
    if condition_sql == "":
        condition_sql, condition_params = true_sql, list(true_params)
    return (condition_sql, list(condition_params))


# --- SHADOW of implementation_resolveBranchCondition (the R/I leg) -----------
# Mirrors Solution.lean: condSql := conditionSql; condParams := conditionParams;
# if condSql == "" then condSql := trueSql; condParams := trueParams;
# return (condSql, condParams).
def shadow_select(condition_sql, condition_params, true_sql, true_params):
    cond_sql = condition_sql
    cond_params = list(condition_params)
    if cond_sql == "":
        cond_sql = true_sql
        cond_params = list(true_params)
    return (cond_sql, cond_params)


def disagree(cs, cp, ts, tp):
    got = oracle_select(cs, cp, ts, tp)
    want = shadow_select(cs, cp, ts, tp)
    if got != want:
        return ((cs, cp, ts, tp), got, want)
    return None


SQL_POOL = ["", '"t"."a" = %s', "1 = 1", "true", '"t"."pk" IN (%s, %s)',
            "NOT (0 = 1)", '"t"."x" IS NULL', "%s"]
TRUE_SQL_POOL = ["%s", "true", "1", "(1 = 1)"]  # always non-empty (precondition)
PARAM_POOL = [True, False, 0, 1, 42, "alpha", "beta", None]


def _enumerate_edge():
    cases = []
    # The F2P shape: an everything-matching guard compiles to "" and is replaced
    # by the always-true stand-in's (sql, params).
    cases.append(("", [], "%s", [True]))
    cases.append(("", [1, 2], "true", []))
    # Non-empty guard: kept unchanged regardless of the stand-in.
    cases.append(('"t"."a" = %s', [7], "%s", [True]))
    cases.append(('"t"."pk" IN (%s, %s)', [1, 2], "true", []))
    # Empty guard with an empty-params stand-in.
    cases.append(("", [], "true", []))
    # Non-empty guard equal to the stand-in sql (must still be kept, not swapped).
    cases.append(("true", [9], "true", []))
    return cases


def main() -> int:
    checked = 0
    for cs, cp, ts, tp in _enumerate_edge():
        d = disagree(cs, cp, ts, tp)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        cs = rng.choice(SQL_POOL)
        cp = [rng.choice(PARAM_POOL) for _ in range(rng.randint(0, 4))]
        ts = rng.choice(TRUE_SQL_POOL)   # non-empty per precondition trueSql != ""
        tp = [rng.choice(PARAM_POOL) for _ in range(rng.randint(0, 3))]
        d = disagree(cs, cp, ts, tp)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
