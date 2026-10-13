#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-14248.

The bundle models ONE routine: the additive-term recombination performed by
`_print_MatAdd` (the algorithm is byte-identical in `sympy/printing/str.py` and
`sympy/printing/latex.py`). It consumes a list of ALREADY-RENDERED summand
strings and joins them into one displayed sum, turning each leading-minus summand
into a genuine subtraction instead of `+ (-...)`, and eliding the very first
connective.

    post-patch:  for each term, push ("-", t[1:]) if t startswith "-" else
                 ("+", t); pop the first connective; "" if it was "+"; then
                 sign + " ".join(rest).

Pre-patch the routine was simply " + ".join(terms), so a leading-minus summand
printed as the addition of a negated term. This routine has NO callee — the
per-summand renderer that produces the input strings is upstream and out of
scope — so this differential test isolates exactly the R/I legs of the impl.

ORACLE = faithful in-process replica of the POST-PATCH `_print_MatAdd`.
SHADOW = op-for-op transliteration of `implementation_renderSum`
(Solution.lean impl region), per refinement.md.

stdlib-only. Pinned seed: 14248 (also in mapping.md).
"""
import random
import sys

SEED = 14248
N = 120_000


# --- ORACLE: faithful replica of POST-PATCH _print_MatAdd ---------------------
def oracle(terms):
    l = []
    for t in terms:
        if t.startswith('-'):
            sign = "-"
            t = t[1:]
        else:
            sign = "+"
        l.extend([sign, t])
    sign = l.pop(0)
    if sign == '+':
        sign = ""
    return sign + ' '.join(l)


# --- SHADOW of implementation_renderSum (the R/I legs) ------------------------
# Mirrors Solution.lean impl region exactly: build the working list, take the
# head connective (headD "+") and the tail, elide a leading "+", then join.
def shadow(terms):
    l = []
    for t in terms:
        if t.startswith('-'):
            l = l + ["-", t[1:]]
        else:
            l = l + ["+", t]
    first_sign = l[0] if l else "+"          # headD "+"
    rest = l[1:]                             # tail
    first_sign = "" if first_sign == "+" else first_sign
    return first_sign + " ".join(rest)


def disagree(terms):
    got = oracle(terms)
    want = shadow(terms)
    if got != want:
        return (terms, got, want)
    return None


# Building blocks for synthetic rendered-summand strings. Includes leading-minus
# terms, parenthesized groups, products, and multi-char bodies.
TOKENS = [
    "A", "B", "C", "A*B", "B*C", "A*B*C", "-A", "-B", "-A*B", "-B*C",
    "-A*B*C", "(A + B)", "-(A + B)", "A B", "-A B", "x_1", "-x_1", "2*A",
    "-2*A", "(-1)*B",
]


def _edge_cases():
    cases = []
    # F2P anchors (post-patch behavior).
    cases.append(["-B", "-A*B", "A"])          # str(A - A*B - B) -> "-B - A*B + A"
    cases.append(["-(A + B)", "A*B"])          # str(A*B - (A+B)) -> "-(A + B) + A*B"
    cases.append(["-B", "A"])                  # (-B + A)[0,0]
    cases.append(["A"])                        # single positive
    cases.append(["-A"])                       # single negative
    cases.append(["A", "B"])                   # plain sum
    cases.append(["-A", "-B"])                 # all negative
    cases.append(["-A*B", "-A*B*C", "-B"])     # latex -A*B - A*B*C - B style
    return cases


def _rand_case(rng):
    n = rng.randint(1, 6)
    return [rng.choice(TOKENS) for _ in range(n)]


def main() -> int:
    checked = 0
    for terms in _edge_cases():
        d = disagree(terms)
        if d:
            print(f"DISAGREE edge: terms={d[0]} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        terms = _rand_case(rng)
        d = disagree(terms)
        if d:
            print(f"DISAGREE fuzz: terms={d[0]} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
