#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13794.

The bundle models the binary concatenation `a + b` of two operands, each of which
is either an ordinary concrete text value or an on-demand ("deferred"/lazy) value
that forces to an underlying text (mapping.md). The gold patch adds the two
binary-concatenation operators to the on-demand proxy so the concatenation works
in every operand combination instead of raising.

ORACLE — a faithful in-process replica of the POST-PATCH Python dispatch, built
directly on the real `django.utils.functional.lazy` proxy when importable, with a
behavior-identical pure fallback otherwise. The proxy's gold operators are:

    def __add__(self, other):  return self.__cast() + other
    def __radd__(self, other): return other + self.__cast()

so `proxy + x == cast() + x`, `x + proxy == x + cast()`, and `proxy + proxy`
forces both. Standing up the proxy is light, so we exercise the REAL operators
when available; the fallback replicates the same three code paths.

SHADOW — an op-for-op transliteration of the Solution.lean impl region (the R/I
legs, per refinement.md): force each deferred operand to its carried text and
append left-to-right.

Diffs ORACLE vs SHADOW over >=10^5 fuzzed operand pairs covering all four
concrete/deferred combinations (both the forward `__add__` and reflected
`__radd__` operators, plus the all-concrete baseline). stdlib-only.
Pinned seed: 13794 (also in mapping.md).
"""
import random
import sys

SEED = 13794
N = 120_000

# --- try to drive the REAL post-patch proxy operators -------------------------
_real_lazy = None
try:
    from django.utils.functional import lazy as _real_lazy  # type: ignore
    # Ensure the proxy actually has the gold operators (post-patch tree); if a
    # pre-patch tree is mounted, fall back to the faithful replica below.
    _probe = _real_lazy(lambda: "x", str)()
    if not hasattr(type(_probe), "__add__") or (_probe + "y") != "xy":
        _real_lazy = None
except Exception:
    _real_lazy = None


def _mk_deferred(s):
    """A deferred (lazy) str operand whose forced value is `s`."""
    if _real_lazy is not None:
        return _real_lazy(lambda s=s: s, str)()
    return _Deferred(s)


class _Deferred:
    """Behavior-identical pure replica of the post-patch proxy for `str`."""
    __slots__ = ("_s",)

    def __init__(self, s):
        self._s = s

    def _cast(self):
        return self._s

    def __add__(self, other):          # gold __add__
        return self._cast() + other
    def __radd__(self, other):         # gold __radd__
        return other + self._cast()


def oracle_concat(a, b):
    """Real Python `a + b` over (concrete str | deferred) operands, post-patch."""
    return a + b


# --- SHADOW of the Solution.lean impl region (the R/I legs) -------------------
# Operands are represented as ("concrete", s) or ("deferred", s).
def force(op):
    return op[1]


def shadow_concat(a_op, b_op):
    # mirrors implementation_lazyConcat: force each operand, append left-to-right.
    kind_a = a_op[0]
    if kind_a == "deferred":
        return a_op[1] + force(b_op)
    else:  # concrete
        if b_op[0] == "deferred":
            return a_op[1] + b_op[1]
        else:
            return a_op[1] + b_op[1]


def to_python(op):
    """Materialize an operand tuple as the real/replica Python value."""
    if op[0] == "deferred":
        return _mk_deferred(op[1])
    return op[1]


def disagree(a_op, b_op):
    o = oracle_concat(to_python(a_op), to_python(b_op))
    s = shadow_concat(a_op, b_op)
    if o != s:
        return (a_op, b_op, o, s)
    return None


_POOL = ["", "string", "lazy", "Hello", "world", "café", "λ", "naïve",
         "a", "  ", "你好", "x" * 17, "multi\nline", "tab\there"]


def _rand_operand(rng):
    kind = rng.choice(["concrete", "deferred"])
    s = rng.choice(_POOL) if rng.random() < 0.7 else "".join(
        rng.choice("abcXYZ 09_") for _ in range(rng.randint(0, 12)))
    return (kind, s)


def _edge_cases():
    cases = []
    # F2P add08: concrete + deferred -> "stringlazy"
    cases.append((("concrete", "string"), ("deferred", "lazy")))
    # F2P add09: deferred + deferred -> "stringlazy"
    cases.append((("deferred", "string"), ("deferred", "lazy")))
    # deferred + concrete (forward __add__)
    cases.append((("deferred", "string"), ("concrete", "lazy")))
    # all-concrete baseline (PASS_TO_PASS test_add*)
    cases.append((("concrete", "foo"), ("concrete", "bar")))
    # empties in every slot
    for ka in ("concrete", "deferred"):
        for kb in ("concrete", "deferred"):
            cases.append(((ka, ""), (kb, "")))
            cases.append(((ka, "x"), (kb, "")))
            cases.append(((ka, ""), (kb, "y")))
    return cases


def main() -> int:
    checked = 0
    for a_op, b_op in _edge_cases():
        d = disagree(a_op, b_op)
        if d:
            print(f"DISAGREE edge: a={d[0]} b={d[1]} oracle={d[2]!r} shadow={d[3]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        a_op = _rand_operand(rng)
        b_op = _rand_operand(rng)
        d = disagree(a_op, b_op)
        if d:
            print(f"DISAGREE fuzz: a={d[0]} b={d[1]} oracle={d[2]!r} shadow={d[3]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0 real_proxy={_real_lazy is not None}")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
