#!/usr/bin/env python3
"""G-AX — executable soundness check for sympy__sympy-17318.

Runs the REAL unchanged callee `split_surds` (sympy/simplify/radsimp.py), in
the eval container at base_commit, against the contract the `fastSplit` domain
stub claims in Solution.lean:

    require allPosRat xs = true       -- domain: every addend's square is a
                                      --   positive rational
    ensures r = Outcome.matched       -- on that domain it always SUCCEEDS,
                                      --   returning a decomposition (never [])

Two obligations, both checked on boundary + fuzz `Add` expressions:

  (S1) SOUND on-domain: whenever `allPosRat(p)` holds, `split_surds(p)` does not
       raise and returns a 3-tuple (≡ Outcome.matched; never []). This is the
       `ensures` the proof consumes.

  (S2) DOMAIN is load-bearing (not too wide): there exist `allPosRat == False`
       sums on which the real `split_surds` RAISES `IndexError` — exactly the
       crash the patched guard avoids. If the domain restriction were vacuous,
       the stub would be unsound; this confirms it is necessary.

stdlib-only (plus sympy, which ships in the testbed image). Exit 0 iff sound.
"""
import sys
import random
import traceback

FUZZ_N = 4000
SEED = 17318


def _imports():
    from sympy import sqrt, S, I, Rational, Integer
    from sympy.simplify.sqrtdenest import _mexpand
    from sympy.simplify.radsimp import split_surds
    try:
        from sympy.core.compatibility import default_sort_key
    except Exception:
        from sympy import default_sort_key
    return sqrt, S, I, Rational, Integer, _mexpand, split_surds, default_sort_key


def all_pos_rat(p, _mexpand, default_sort_key):
    """The Solution.lean `allPosRat` predicate over the real expression: every
    sorted addend `x` has `(x**2).is_Rational and (x**2).is_positive`. Returns
    None if `p` is not an Add (then the modeled branch does not apply)."""
    p = _mexpand(p)
    if not p.is_Add:
        return None
    pargs = sorted(p.args, key=default_sort_key)
    for x in pargs:
        sq = x ** 2
        if not (bool(sq.is_Rational) and (sq.is_positive is True)):
            return False
    return True


def run():
    sqrt, S, I, Rational, Integer, _mexpand, split_surds, dsk = _imports()
    rnd = random.Random(SEED)

    # Term pools.
    pos_surd = [sqrt(2), sqrt(3), sqrt(5), sqrt(6), sqrt(7), sqrt(10), sqrt(15),
                3 * sqrt(3), sqrt(5) / 7, 2 * sqrt(11)]
    pos_rat = [S(1), S(2), S(3), Rational(1, 2), S(5), Integer(7)]
    nonpos = [I, 3 * I, 2 * I, -I, sqrt(-1), I * sqrt(2)]

    boundary = [
        sqrt(2) + sqrt(3),
        3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15),
        1 + sqrt(2) + sqrt(6),
        2 + sqrt(2) + sqrt(8),
        4 + I,
        3 + 3 * I,
        1 + 2 * I,
        3 - sqrt(2) * sqrt(4 + I) + 3 * I,
    ]

    s1_checked = 0      # on-domain successes asserted
    s2_witnessed = 0    # off-domain IndexError witnesses

    def check(expr):
        nonlocal s1_checked, s2_witnessed
        ap = all_pos_rat(expr, _mexpand, dsk)
        if ap is None:
            return  # not an Add — modeled branch does not apply
        p = _mexpand(expr)
        if ap is True:
            # (S1) must succeed with a 3-tuple decomposition (Outcome.matched).
            try:
                r = split_surds(p)
            except Exception as ex:
                raise AssertionError(
                    "S1 VIOLATED: split_surds raised %s on an allPosRat sum %r "
                    "(stub ensures matched / no-raise)" % (type(ex).__name__, expr)
                ) from ex
            if not (isinstance(r, tuple) and len(r) == 3):
                raise AssertionError(
                    "S1 VIOLATED: split_surds returned %r (not a 3-tuple "
                    "decomposition) on allPosRat sum %r" % (r, expr))
            s1_checked += 1
        else:
            # (S2) off-domain: a raise here witnesses the domain is load-bearing.
            try:
                split_surds(p)
            except IndexError:
                s2_witnessed += 1
            except Exception:
                pass  # other off-domain failures are not our witness, ignore

    for e in boundary:
        check(e)

    def rand_term():
        k = rnd.random()
        if k < 0.45:
            return rnd.choice(pos_surd)
        if k < 0.8:
            return rnd.choice(pos_rat)
        return rnd.choice(nonpos)

    for _ in range(FUZZ_N):
        n = rnd.randint(2, 5)
        terms = [rand_term() for _ in range(n)]
        try:
            expr = sum(terms[1:], terms[0])
        except Exception:
            continue
        try:
            check(expr)
        except AssertionError:
            raise
        except Exception:
            # building / sympifying degenerate sums may misbehave; skip those,
            # they are not observations of the callee's contract.
            continue

    if s1_checked < 20:
        raise AssertionError(
            "G-AX inconclusive: only %d on-domain (allPosRat) successes "
            "observed; need ≥20 to assert S1." % s1_checked)
    if s2_witnessed < 1:
        raise AssertionError(
            "G-AX inconclusive: never witnessed split_surds raising IndexError "
            "off-domain; the domain restriction may be vacuous (S2).")

    print("G-AX OK: split_surds domain stub sound — %d allPosRat sums all "
          "returned a 3-tuple decomposition (no raise, never []); %d off-domain "
          "sums witnessed the IndexError the guard avoids (boundary=%d, "
          "fuzz=%d, seed=%d)." % (s1_checked, s2_witnessed, len(boundary),
                                  FUZZ_N, SEED))


def main():
    try:
        run()
    except AssertionError as e:
        print("G-AX FAIL: %s" % e)
        return 1
    except Exception:
        print("G-AX ERROR:\n" + traceback.format_exc())
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
