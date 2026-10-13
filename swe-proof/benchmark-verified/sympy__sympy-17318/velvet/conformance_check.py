#!/usr/bin/env python3
"""G-CONF — cross-language differential test for sympy__sympy-17318.

Builds the R/I shadow of `Solution.lean`'s `matchAddTerms` `do` block in Python
and diffs it against the behaviour of `patch.diff` (the post-patch real
`_sqrt_match` is_Add branch) over fuzzed `Add` inputs. Exit 0 iff zero
disagreements.

Bridge (mapping.md §2): a SymPy `Add` `p` ↔ `xs : List Addend` via the sorted
addends; the modeled result `Outcome` ↔ `len(_sqrt_match(p)) == 0` (`empty`)
vs `> 0` (`matched`).

R/I shadow of the `do` block (impl region of `matchAddTerms`):
    allPosRat(p)              -> matched   [A-leg: invoke the REAL split_surds,
                                            which must succeed on its domain;
                                            mapping.md §3 — left as the repo callee]
    else maxDepth(p) == 0     -> empty     [R/I: general regime, no decomposition]
    else                      -> matched   [R/I: general regime, decomposition]

The A-tagged leg (`fastSplit` ↔ `split_surds`) is NOT re-implemented: per the
worker spec, A-tagged callees are left as the real repo callee. Its
domain-soundness is the job of axiom_check.py (G-AX); here it only has to agree
that an on-domain call yields a non-empty result.

stdlib + sympy (ships in the testbed image). Run inside the eval container with
the gold patch applied. Seed pinned in mapping.md §5.
"""
import sys
import random
import traceback

N = 100000
SEED = 17318


def _imports():
    from sympy import sqrt, S, I, Rational, Integer
    from sympy.simplify.sqrtdenest import _sqrt_match, sqrt_depth, _mexpand
    from sympy.simplify.radsimp import split_surds
    try:
        from sympy.core.compatibility import default_sort_key
    except Exception:
        from sympy import default_sort_key
    return (sqrt, S, I, Rational, Integer, _sqrt_match, sqrt_depth, _mexpand,
            split_surds, default_sort_key)


def shadow_outcome(p, _mexpand, default_sort_key, sqrt_depth, split_surds):
    """R/I transliteration of matchAddTerms; returns 'matched' | 'empty'.
    Precondition: `_mexpand(p)` is an Add (caller guarantees)."""
    p = _mexpand(p)
    pargs = sorted(p.args, key=default_sort_key)
    all_pos_rat = all(
        (bool((x ** 2).is_Rational) and ((x ** 2).is_positive is True))
        for x in pargs)
    if all_pos_rat:
        # A-leg: the real unchanged callee. On its domain it must succeed; a
        # 3-tuple ⇒ _sqrt_match returns the 3-list ⇒ matched.
        split_surds(p)
        return "matched"
    nmax = max(sqrt_depth(x) for x in pargs)
    return "empty" if nmax == 0 else "matched"


def real_outcome(p, _sqrt_match):
    """Behaviour of patch.diff: post-patch _sqrt_match on an Add, abstracted to
    matched/empty by result length (mapping.md §2)."""
    r = _sqrt_match(p)
    return "empty" if len(r) == 0 else "matched"


def run():
    (sqrt, S, I, Rational, Integer, _sqrt_match, sqrt_depth, _mexpand,
     split_surds, dsk) = _imports()
    rnd = random.Random(SEED)

    pos_surd = [sqrt(2), sqrt(3), sqrt(5), sqrt(6), sqrt(7), sqrt(10), sqrt(15),
                sqrt(11), sqrt(13), 3 * sqrt(3), sqrt(5) / 7, 2 * sqrt(2)]
    pos_rat = [S(1), S(2), S(3), S(4), S(5), Rational(1, 2), Rational(3, 7),
               Integer(11)]
    nonpos = [I, 3 * I, 2 * I, -I, I * sqrt(2), I * sqrt(3), 5 * I]
    nested = [sqrt(1 + sqrt(5)), sqrt(2 + sqrt(3)), 2 * sqrt(1 + sqrt(2)),
              sqrt(3 + 2 * sqrt(2))]

    boundary = [
        4 + I, 3 + 3 * I, 1 + 2 * I, 5 + 7 * I,
        sqrt(2) + sqrt(3), 1 + sqrt(2) + sqrt(6),
        3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15),
        3 - sqrt(2) * sqrt(4 + I) + 3 * I,
        1 + sqrt(2) + sqrt(2) * sqrt(3) + 2 * sqrt(1 + sqrt(5)),
    ]

    disagreements = []
    checked = 0
    n_empty = 0
    n_matched = 0

    def one(expr):
        nonlocal checked, n_empty, n_matched
        try:
            me = _mexpand(expr)
        except Exception:
            return
        if not me.is_Add:
            return  # modeled branch is the is_Add case only
        try:
            sh = shadow_outcome(expr, _mexpand, dsk, sqrt_depth, split_surds)
        except Exception:
            # shadow's A-leg call raised: that is an off-domain call the shadow
            # should never make (allPosRat was True yet split_surds failed). Let
            # real_outcome decide; if real also raises we record below.
            sh = "RAISE"
        try:
            rl = real_outcome(me, _sqrt_match)
        except Exception as ex:
            rl = "RAISE:%s" % type(ex).__name__
        checked += 1
        if sh == "empty":
            n_empty += 1
        elif sh == "matched":
            n_matched += 1
        if sh != rl:
            if len(disagreements) < 25:
                disagreements.append((str(expr), sh, rl))

    for e in boundary:
        one(e)

    def rand_term():
        k = rnd.random()
        if k < 0.40:
            return rnd.choice(pos_surd)
        if k < 0.72:
            return rnd.choice(pos_rat)
        if k < 0.90:
            return rnd.choice(nonpos)
        return rnd.choice(nested)

    while checked < N:
        n = rnd.randint(2, 5)
        terms = [rand_term() for _ in range(n)]
        try:
            expr = sum(terms[1:], terms[0])
        except Exception:
            continue
        one(expr)

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) (showing ≤25):" % len(disagreements))
        for s, sh, rl in disagreements:
            print("  expr=%s  shadow=%s  real=%s" % (s, sh, rl))
        return 1

    print("G-CONF OK: R/I shadow of matchAddTerms agrees with patch.diff "
          "behaviour on %d Add inputs (seed=%d), 0 disagreements "
          "(empty=%d, matched=%d, incl %d boundary)."
          % (checked, SEED, n_empty, n_matched, len(boundary)))
    return 0


def main():
    try:
        return run()
    except Exception:
        print("G-CONF ERROR:\n" + traceback.format_exc())
        return 2


if __name__ == "__main__":
    sys.exit(main())
