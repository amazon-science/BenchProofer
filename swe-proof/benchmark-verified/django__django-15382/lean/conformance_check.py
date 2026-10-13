#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15382.

The bundle models ONE dispatch: `Exists.as_sql`
(django/db/models/expressions.py:1212-1224) deciding how to render a
(possibly-negated) existence test, given the outcome of the unchanged inner
renderer `super().as_sql(...)`. The outcome is either a successful `(sql, params)`
pair or an `EmptyResultSet` signal (raised when the subquery is statically empty).

Inputs (mapping.md bijection):
  * negated : bool                 <- self.negated
  * inner   : ('ok', sql, params) | ('empty',) | ('other',)
              ('ok', ...) <- super().as_sql returns (sql, params)
              ('empty',)  <- super().as_sql raises EmptyResultSet
              ('other',)  <- super().as_sql raises any OTHER exception

ORACLE — the POST-PATCH `Exists.as_sql` dispatch, reproduced directly from the
patched source control flow:
    try: sql, params = super().as_sql(...)        # -> inner
    except EmptyResultSet:
        if self.negated: return '', ()
        raise                                      # -> EmptyResultSet propagates
    if self.negated: sql = 'NOT {}'.format(sql)
    return sql, params
Note the `except` catches ONLY EmptyResultSet: any other exception is never
special-cased and propagates unchanged regardless of `negated` (the `('other',)`
input).

SHADOW — `implementation_compileExistenceCheck` (Solution.lean) transliterated:
  match inner: error emptyResult -> (ok ('',[]) if negated else error emptyResult)
               error other       -> error other
               ok                -> ok (('NOT '+sql if negated else sql), params)

The discriminating configuration the patch fixes — `negated=True` AND inner is the
empty-result signal — must render as the empty fragment `('', [])` (ok), NOT
propagate the signal. We diff oracle vs shadow over hand-picked edges + a
deterministic built-in fuzzer; exit 0 iff zero disagreements.

stdlib-only. Pinned seed: 15382 (also recorded in mapping.md).
"""
import sys

SEED = 15382
N = 200_000

# Sentinels for propagated failures (the exception re-raised unchanged).
RAISE_EMPTY = ("raise", "empty")
RAISE_OTHER = ("raise", "other")


# --- ORACLE: post-patch Exists.as_sql dispatch -------------------------------
def oracle(negated, inner):
    # inner: ('ok', sql, params) | ('empty',) | ('other',)
    if inner[0] == "empty":
        # except EmptyResultSet:
        if negated:
            return ("ok", "", [])      # return '', ()
        return RAISE_EMPTY              # raise  (EmptyResultSet propagates)
    if inner[0] == "other":
        # not caught by `except EmptyResultSet` -> propagates, negated irrelevant
        return RAISE_OTHER
    _, sql, params = inner
    if negated:
        sql = "NOT {}".format(sql)      # 'NOT {}'.format(sql)
    return ("ok", sql, params)          # return sql, params


# --- SHADOW of implementation_compileExistenceCheck (R/I leg) ----------------
def shadow(negated, inner):
    if inner[0] == "empty":
        if negated:
            return ("ok", "", [])       # .ok ("", [])
        return RAISE_EMPTY               # .error .emptyResult  (propagated)
    if inner[0] == "other":
        return RAISE_OTHER               # .error .other  (propagated, any negated)
    _, sql, params = inner
    if negated:
        sql = "NOT " + sql               # "NOT " ++ sql
    return ("ok", sql, params)           # .ok (sql, params)


def disagree(negated, inner):
    o = oracle(negated, inner)
    s = shadow(negated, inner)
    if o != s:
        return ((negated, inner), o, s)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _edges():
    return [
        # THE fix: negated test over a statically-empty subquery -> empty fragment.
        (True, ("empty",)),
        # non-negated empty -> propagate the empty-result signal.
        (False, ("empty",)),
        # any OTHER failure is never special-cased: propagates for both flags.
        (True, ("other",)),
        (False, ("other",)),
        # negated success -> NOT-prefixed, params unchanged.
        (True, ("ok", "EXISTS(SELECT 1)", ["p0"])),
        # non-negated success -> unchanged.
        (False, ("ok", "EXISTS(SELECT 1)", ["p0"])),
        # success with empty fragment / no params (boundary).
        (True, ("ok", "", [])),
        (False, ("ok", "", [])),
        # success with multiple params (passed through verbatim).
        (True, ("ok", "EXISTS(SELECT 1 WHERE x=%s AND y=%s)", ["a", "b"])),
        (False, ("ok", "EXISTS(SELECT 1 WHERE x=%s)", ["a"])),
    ]


_FRAGS = ["", "EXISTS(SELECT 1)", "EXISTS(SELECT 1 WHERE c=%s)",
          "NOT EXISTS(x)", "EXISTS((SELECT 1))"]


def _rand_case(rnd):
    negated = bool(next(rnd) % 2)
    r = next(rnd) % 4
    if r == 0:
        return negated, ("empty",)
    if r == 1:
        return negated, ("other",)
    sql = _FRAGS[next(rnd) % len(_FRAGS)]
    k = next(rnd) % 4
    params = ["p%d" % (next(rnd) % 1000) for _ in range(k)]
    return negated, ("ok", sql, params)


def main() -> int:
    checked = 0

    for negated, inner in _edges():
        d = disagree(negated, inner)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        negated, inner = _rand_case(rnd)
        d = disagree(negated, inner)
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
