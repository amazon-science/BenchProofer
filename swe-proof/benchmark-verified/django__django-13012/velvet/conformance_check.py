#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13012 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `refinement.md`: the deep
behaviour model of `Solution.lean`'s `groupingColumns` — a transparent wrapping
expression contributes EXACTLY the columns the wrapped inner expression
contributes for the SAME requested grouping context (`out = innerCols`) —
transliterated to Python, differential-tested against `patch.diff`'s behaviour
driven through the REAL patched code at base_commit+gold.

ORACLE — the gold-patched wrapping expression itself: for a wrapping expression
`w` around inner expression `e` and a requested grouping context `alias`, the
observed `w.get_group_by_cols(alias=alias)` (the column list the harness/SQL
compiler consumes for the GROUP BY clause).

SHADOW — `Solution.lean`'s `groupingColumns`, transliterated. The single free
observation `innerCols` is derived exactly as the gold delegation derives it
(mapping.md §2): the inner expression's own grouping columns for the SAME
context, `e.get_group_by_cols(alias=alias)`. The model returns `innerCols`.

Comparison is by OBJECT IDENTITY of the contributed columns (mapping.md §2:
`GroupCol` abstracts an expression's identity; `get_group_by_cols` returns the
actual expression objects, and downstream GROUP BY de-duplication is identity /
equality based). Exit 0 iff zero disagreements over >=10^5 inputs.

stdlib + Django only; the fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=True,
    )
import django                                              # noqa: E402
django.setup()

from django.db.models import (                             # noqa: E402
    Value, IntegerField, FloatField, F, Sum, Count, Avg, Max, Min,
)
from django.db.models.expressions import (                 # noqa: E402
    ExpressionWrapper, RawSQL, Random, Col,
)
from django.db.models.functions import (                   # noqa: E402
    Lower, Upper, Coalesce, Length, Concat,
)

SEED = 13012


def _cols_identity(cols):
    """Canonical identity signature of a list of contributed grouping columns.
    GROUP BY de-duplicates on object identity / equality, so identity is the
    observable that matters (mapping.md §2)."""
    return tuple(id(c) for c in cols)


# ---- ORACLE: the real gold-patched wrapping expression ----------------------
def oracle_observe(inner, alias):
    w = ExpressionWrapper(inner, output_field=IntegerField())
    return _cols_identity(w.get_group_by_cols(alias=alias))


# ---- SHADOW: Solution.lean groupingColumns, transliterated ------------------
def shadow_observe(inner, alias):
    # free observation innerCols, derived exactly as the gold delegation does:
    # the wrapped inner expression's grouping columns for the SAME context.
    inner_cols = inner.get_group_by_cols(alias=alias)
    # groupingColumns: out = innerCols
    out = inner_cols
    return _cols_identity(out)


# ---- inputs: the F2P matrix + a broad fuzz over inner-expression kinds -------
def make_inner(rng):
    kind = rng.randint(0, 12)
    if kind == 0:
        return Value(rng.randint(-10, 10))                 # constant (F2P: empty)
    if kind == 1:
        return Value(rng.choice(["f", "g", "x", ""]))      # string constant
    if kind == 2:
        return Lower(Value(rng.choice(["f", "g"])))        # F2P: non-empty
    if kind == 3:
        return Upper(Value("h"))
    if kind == 4:
        return RawSQL("1", [])                             # contributes [self]
    if kind == 5:
        return Coalesce(Value(1), Value(rng.randint(0, 5)))
    if kind == 6:
        return Sum(Value(1))                               # aggregate -> []
    if kind == 7:
        return Count(Value(1))
    if kind == 8:
        return Avg(Value(2))
    if kind == 9:
        return Max(Value(3))
    if kind == 10:
        return Min(Value(4))
    if kind == 11:
        return Length(Value("abc"))
    return Concat(Value("a"), Value("b"))


def boundary_inners():
    return [
        Value(3),                                          # F2P test_empty_group_by
        Lower(Value("f")),                                 # F2P test_non_empty_group_by
        Value("const"), Value(0), Value(-1),
        Upper(Value("g")), RawSQL("1", []),
        Coalesce(Value(1), Value(2)),
        Sum(Value(1)), Count(Value(1)), Avg(Value(1)),
        Length(Value("xyz")), Concat(Value("p"), Value("q")),
    ]


def main():
    rng = random.Random(SEED)
    aliases = [None, "a1", "col_alias", "agg", ""]
    disagreements = []
    count = 0

    # boundary inners x every alias context
    pairs = [(inner, a) for inner in boundary_inners() for a in aliases]
    # fuzz
    for _ in range(100000):
        pairs.append((make_inner(rng), rng.choice(aliases)))

    for inner, alias in pairs:
        count += 1
        try:
            oracle = oracle_observe(inner, alias)
        except Exception as e:                             # noqa: BLE001
            disagreements.append((repr(inner), "ORACLE-CRASH:" + repr(e), None))
            if len(disagreements) >= 8:
                break
            continue
        try:
            shadow = shadow_observe(inner, alias)
        except Exception as e:                             # noqa: BLE001
            disagreements.append((repr(inner), "SHADOW-CRASH:" + repr(e), None))
            if len(disagreements) >= 8:
                break
            continue
        if oracle != shadow:
            disagreements.append((repr(inner) + " alias=" + repr(alias),
                                  shadow, oracle))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  input=%s shadow=%s oracle=%s" % (v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of groupingColumns (transparent wrapping "
          "expression contributes exactly the wrapped expression's grouping "
          "columns) agrees with patch.diff behaviour through the real patched "
          "ExpressionWrapper.get_group_by_cols on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
