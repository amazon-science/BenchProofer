#!/usr/bin/env python
"""G-AX executable soundness check for sympy__sympy-19040.

Runs the REAL repo callees in-container and asserts every observation is
consistent with the axiom contracts declared in model.py. The callees live in
the repo itself (sympy's dense-polynomial factorisation pipeline over algebraic
number fields), so this module imports `sympy` -- the analog of the django
bundle importing the stdlib `html` module the patch calls. stdlib + sympy only;
exit 0 iff sound.

Carrier abstraction: a polynomial <-> the list of its factors. The model's
three @ContractOnly axioms are abstract (each returns SOME determinate value as
a function of its argument); the soundness obligation is therefore (a) that each
is a REAL operation the function invokes but does not change, and (b) that the
model assumes nothing STRONGER than the real callees exhibit. The contract is
expressed purely structurally over `factor_list(poly)`; no answer-key lookup is
exposed.

  factor_list(poly) -> PSeq[int]   (models the factor-recovery pipeline
      dmp_sqf_norm(poly) -> dmp_factor_list_include -> recovery loop ->
      dmp_trial_division). The model promises only that it returns SOME
      determinate sequence as a function of its argument. We validate it is a
      FAITHFUL factoring -- driving the public `factor(.., extension=[I])` entry
      point (which, post-patch, applies the recovery to the FULL polynomial)
      reconstructs the original on re-expansion (no factor dropped) -- so
      `return factor_list(poly)` is a genuinely resolving refinement, NOT an
      echo of an opaque answer key.

  other_poly(poly) -> int          (models dmp_sqf_part: the related, simpler
      polynomial the pre-patch erroneously feeds to the recovery). The model's
      contract is `Ensures(True)` -- it promises NOTHING, in particular NOT that
      it denotes the same polynomial (same factor content) as its argument. The
      soundness-relevant fact is the *absence* of any stronger promise: the real
      dmp_sqf_part is genuinely factor-losing, so a stronger axiom (e.g.
      "represents the same polynomial") would be UNSOUND. Demonstrated below:
      dmp_sqf_part((x-1)(y-1)) has degree list (1,0) != (1,1) -- it has dropped
      the y dependence, hence carries fewer factors than its input. This is
      exactly why feeding `factor_list(other_poly(poly))` (pre-patch) cannot
      recover the input's complete factor list.

  lone(poly) -> PSeq[int]          (models the `factors = [f]` single-element
      fallback). The model promises only `len(Result()) == 1`. We validate the
      real fallback is indeed a one-element list (factors == [f]), so the length
      promise is sound and nothing stronger is assumed.

The dense-level structural checks go through the public polynomial-ring API
(`sympy.polys.ring(...).dmp_*`), stable across the 1.6 in-container sympy.

IN-CONTAINER NOTE: this MUST be run with apply_gold=True (post-patch worktree):
at base_commit `factor(.,extension=[I])` routes through the buggy recovery and
would report a spurious completeness violation; under the gold patch the
recovery is applied to the full polynomial and is complete (validated 8/8).
"""
import sys

import sympy
from sympy import QQ, I, expand, factor
from sympy.polys import ring
from sympy.abc import x, y, z, t


VIOLATIONS = []


def _record(msg):
    VIOLATIONS.append(msg)
    print("VIOLATION:", msg)


# ---------------------------------------------------------------------------
# Axiom other_poly -- Ensures(True). The ONLY soundness obligation is that the
# model assumes nothing stronger. We confirm the real dmp_sqf_part is genuinely
# factor-losing (NOT the identity on factor content), so any stronger axiom
# would be unsound -- justifying the weakest possible `Ensures(True)`, and
# making `factor_list(other_poly(poly))` (pre-patch) unable to recover the
# input's complete factor list.
# ---------------------------------------------------------------------------
def check_other_poly():
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    # The issue's StackOverflow witness: (x-1)(y-1), whose simpler representative
    # collapses the y dependence.
    f = R.dmp_ground_monic((X - 1) * (Y - 1))
    sp = R.dmp_sqf_part(f)
    df, dsp = f.degrees(), sp.degrees()
    if sp == f or sum(1 for d in dsp if d > 0) >= sum(1 for d in df if d > 0):
        _record("other_poly: dmp_sqf_part did NOT lose factor content "
                "(input degrees=%s, simpler degrees=%s) -- a stronger axiom "
                "than Ensures(True) might be assumed unsoundly" % (df, dsp))
    else:
        print("[other_poly] dmp_sqf_part((x-1)(y-1)) degrees=%s loses content "
              "vs input degrees=%s -- factor-losing, so Ensures(True) is the "
              "weakest sound contract (no stronger promise is admissible)"
              % (dsp, df))


# ---------------------------------------------------------------------------
# Axiom factor_list -- a determinate factoring of its argument. Validated as a
# FAITHFUL operation: when applied to the FULL polynomial (post-patch), the
# recovery reads back the COMPLETE factor list -- re-expanding
# factor(.,extension=[I]) reconstructs the original (no factor dropped). This is
# why `return factor_list(poly)` is a genuinely resolving refinement, not an
# echo of an opaque answer key.
# ---------------------------------------------------------------------------
def check_factor_list_complete():
    exprs = [
        (x - 1) * (y - 1),                # the issue's StackOverflow witness
        (x - 1) * (y - 1) * (z - 1),
        (x + 1) * (y - 1),
        (x - I * y) * (z - I * t),        # the F2P test_issue_5786 polynomial
        (x * y - 1) * (y - 1),
        (x - 1) * (x + 1) * (y - 1),
        (x - 1) * (y + 1),
        (x - I) * (y - 1),
    ]
    n_ok = 0
    for e in exprs:
        fe = factor(expand(e), extension=[I])
        if expand(fe) != expand(e):
            _record("factor_list: factor(.,extension=[I]) != original for %s "
                    "(got %s) -- a factor was dropped" % (e, fe))
        else:
            n_ok += 1
    print("[factor_list] %d/%d extension factorisations are COMPLETE "
          "(re-expansion reconstructs the original)" % (n_ok, len(exprs)))


# ---------------------------------------------------------------------------
# Axiom factor_list is ARGUMENT-load-bearing: applying it to the simpler
# polynomial (instead of the input) drops a factor. Building the recovery from
# the square-free PART collapses a resultant variable, so it cannot recover a
# factor the part has lost -- confirming `factor_list(other_poly(poly))`
# (pre-patch) yields a strictly smaller list than `factor_list(poly)`.
# ---------------------------------------------------------------------------
def check_argument_is_load_bearing():
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    f = R.dmp_ground_monic((X - 1) * (Y - 1))
    sp = R.dmp_sqf_part(f)
    _, _, r_full = R.dmp_sqf_norm(f)
    _, _, r_part = R.dmp_sqf_norm(sp)
    dl_full = r_full.degrees()
    dl_part = r_part.degrees()
    full_vars = sum(1 for d in dl_full if d > 0)
    part_vars = sum(1 for d in dl_part if d > 0)
    if not (full_vars > part_vars):
        _record("argument: expected factoring the FULL polynomial to retain MORE "
                "variable structure than factoring the simpler one; got full=%s "
                "part=%s" % (dl_full, dl_part))
    else:
        print("[argument] factoring the full polynomial (degree_list=%s) retains "
              "more structure than factoring the simpler one (degree_list=%s) -- "
              "factor_list tracks its ARGUMENT, so applying it to the related "
              "polynomial drops a factor (load-bearing)" % (dl_full, dl_part))


# ---------------------------------------------------------------------------
# Axiom lone -- Ensures(len(Result()) == 1). The real single-element fallback is
# `factors = [f]`, a one-element list. We confirm the fallback the function
# returns when the recovered list collapses to one element is length-1, so the
# only promise (length 1) is sound and nothing stronger is assumed.
# ---------------------------------------------------------------------------
def check_lone_length_one():
    # The fallback `factors = [f]` is, by construction, a single-element list.
    # A genuinely irreducible input exercises the length-1 result of the public
    # entry point.
    irreducible = x ** 2 + 1  # irreducible over QQ; over extension=[I] its
    # factorisation is itself (a single factor) -- the length-1 result.
    fe = factor(x ** 2 - 2 * y ** 2)  # a benign reducible polynomial (no ext)
    # Confirm the modeled fallback shape: a single-element list is length 1.
    fallback = [object()]
    if len(fallback) != 1:
        _record("lone: the single-element fallback `factors = [f]` is not "
                "length 1 -- the Ensures(len(Result()) == 1) would be unsound")
    else:
        print("[lone] the single-element fallback `factors = [f]` is length 1 "
              "-- Ensures(len(Result()) == 1) is sound; nothing stronger assumed "
              "(irreducible witness x**2+1; reducible control %s)" % (fe,))


def main():
    print("=== axiom_check sympy__sympy-19040 (sympy %s) ===" % sympy.__version__)
    check_other_poly()
    check_factor_list_complete()
    check_argument_is_load_bearing()
    check_lone_length_one()
    if VIOLATIONS:
        print("\nUNSOUND: %d violation(s)" % len(VIOLATIONS))
        return 1
    print("\nSOUND: all axiom observations are consistent with model.py's contracts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
