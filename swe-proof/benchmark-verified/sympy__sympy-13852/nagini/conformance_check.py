#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13852 (nagini).

SHADOW: the impl regions of model.py's `recognize_closed_form` and
`series_expansion_at_one`, copied VERBATIM below with the contract calls
(Requires/Ensures/MustTerminate) stripped, plus the @Pure helper maps
`closed_form_for` / `expansion_code` copied over as plain functions and the
integer code/tag constants. No PSeq usage, no @ContractOnly callees; the
carriers are plain ints, so no container shim is needed.

ORACLE: the REAL patched repo functions the model models per mapping.md --
the auto-evaluation dispatch `polylog.eval` (observed through construction of
`polylog(s, z)`) and the s == 1 branch of `polylog._eval_expand_func`
(observed through `expand_func(polylog(1, z))`). The gate applies patch.diff
to /testbed before this script runs and sets PYTHONPATH=/testbed, so plain
`import sympy` resolves the patched code; this script does NOT apply any
patch itself.

TYPE BRIDGE (mapping.md "Type abstraction"):
  * `s` is a plain int on both sides: the dispatch branches only on discrete
    equality predicates over s, which integer s realises exactly.
  * `z_tag` in {0..9} is the finite quotient of the SymPy argument z by the
    nine equality tests the dispatch performs. The bridge decodes each tag to
    the concrete SymPy value defining its class; the residual class Z_OTHER
    (tag 0) is decoded to SEVERAL representatives (rationals, integers, a
    surd, a symbol, a complex rational), all matching none of the nine
    equalities -- the dispatch is constant on each class, so any
    representative is faithful.
  * a closed-form CODE decodes to the concrete closed-form expression it
    names (same code values as axiom_check.py); CF_UNEVAL decodes to "the
    call stays a bare polylog instance". Comparison is SymPy structural
    equality with a simplify(diff) == 0 fallback.
  * EXP_PLAIN decodes to the elementary logarithm in (1 - z) with no
    polar/branch factor; the real observable is expand_func of the s == 1
    call, checked both for equality to that form and for absence of any
    exp_polar factor.

The real callee is pure, so verdicts are cached per distinct decoded case;
the >= 1e5 logical inputs replay the cached verdicts (the model's input
domain is a finite quotient, so distinct-case coverage is exhaustive by
construction: every (s-branch-class, tag, representative) combination is in
the boundary sweep).

Input domain (the model's Requires): recognize_closed_form needs
0 <= z_tag <= 9 (s any int); series_expansion_at_one needs s == S_EXPAND.
Boundary sweep: s in {-60..60 extremes and all branch values} x all tags x
all Z_OTHER representatives; fuzz draws (s, tag, rep) uniformly from
s in [-60, 60]. Larger |s| is avoided only because the z == 1 clause's
closed form grows combinatorially there (an orthogonal cost, not a dispatch
branch: the dispatch has no further s-dependence beyond its equality tests).

>= 1e5 Requires-satisfying inputs: full boundary sweep + 100000 fuzz triples
for the dispatch, + the expansion checks. Pinned fuzz seed: 13852.

Exit 0 iff zero disagreements; on disagreement prints the decoded input and
both outputs, then exits 1. stdlib + sympy (the library under test) only.
"""
from __future__ import print_function

import json
import random
import sys

SEED = 13852
N_FUZZ = 100000


# ---------------------------------------------------------------------------
# Constants from model.py (verbatim values).
# ---------------------------------------------------------------------------
CF_UNEVAL = 0
CF_ZA = 1
CF_ZB = 2
CF_ZC = 3
CF_P1 = 4
CF_P2 = 5
CF_P3 = 6
CF_P4 = 7
CF_P5 = 8
CF_P6 = 9
CF_SA = 10
CF_SB = 11

Z_A = 1
Z_B = 2
Z_C = 3
Z_1 = 4
Z_2 = 5
Z_3 = 6
Z_4 = 7
Z_5 = 8
Z_6 = 9
Z_OTHER = 0

S_SPECIAL = 2
S_KEY_A = 0
S_KEY_B = -1
S_EXPAND = 1

EXP_PLAIN = 1
EXP_POLAR = 2


# ---------------------------------------------------------------------------
# @Pure helpers from model.py, decorators + contracts stripped (verbatim).
# ---------------------------------------------------------------------------

def closed_form_for(s, z_tag):
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL


def expansion_code(s):
    return EXP_PLAIN


# ---------------------------------------------------------------------------
# The impl regions of model.py, verbatim (contract calls stripped).
# ---------------------------------------------------------------------------

def recognize_closed_form(s, z_tag):
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL


def series_expansion_at_one(s):
    return EXP_PLAIN


# ---------------------------------------------------------------------------
# Bridge + oracle.
# ---------------------------------------------------------------------------

def main():
    try:
        from sympy import (polylog, expand_func, exp_polar, pi, log, sqrt, I,
                           S, Rational, Symbol, zeta, dirichlet_eta, simplify)
    except Exception as exc:
        print("G-CONF ERROR: sympy not importable (%r); run in-container "
              "with PYTHONPATH=/testbed." % (exc,))
        return 1

    g = sqrt(5)
    w = Symbol('w')

    # tag -> concrete z representative(s) of its equivalence class.
    # Tags 1..9 are singleton classes (the defining value); Z_OTHER is the
    # residual class, decoded to several representatives that match none of
    # the nine equalities.
    tag_reps = {
        Z_A: [S.One],
        Z_B: [-S.One],
        Z_C: [S.Zero],
        Z_1: [S.Half],
        Z_2: [S(2)],
        Z_3: [-(g - 1) / 2],
        Z_4: [-(g + 1) / 2],
        Z_5: [(3 - g) / 2],
        Z_6: [(g - 1) / 2],
        Z_OTHER: [Rational(1, 3), Rational(7, 5), S(3), S(-2),
                  Rational(-3, 7), sqrt(2), w, 3 + 2 * I],
    }

    def expected_expr(code, s, z):
        """The concrete closed-form expression a (non-UNEVAL) code names,
        instantiated at (s, z). Same code<->form binding as axiom_check.py."""
        if code == CF_ZA:
            return zeta(s)
        if code == CF_ZB:
            return -dirichlet_eta(s)
        if code == CF_ZC:
            return S.Zero
        if code == CF_P1:
            return pi**2 / 12 - log(2)**2 / 2
        if code == CF_P2:
            return pi**2 / 4 - I * pi * log(2)
        if code == CF_P3:
            return -pi**2 / 15 + log((sqrt(5) - 1) / 2)**2 / 2
        if code == CF_P4:
            return -pi**2 / 10 - log((sqrt(5) + 1) / 2)**2
        if code == CF_P5:
            return pi**2 / 15 - log((sqrt(5) - 1) / 2)**2
        if code == CF_P6:
            return pi**2 / 10 - log((sqrt(5) - 1) / 2)**2
        if code == CF_SA:
            return z / (1 - z)
        if code == CF_SB:
            return z / (1 - z)**2
        raise AssertionError("no expression for code %d" % code)

    def sym_eq(a, b):
        if a == b:
            return True
        try:
            return simplify(a - b) == 0
        except Exception:
            return False

    # Verdict cache: the real callee is pure, so each distinct decoded case
    # is checked against the oracle exactly once.
    cache = {}

    def check_dispatch(s, z_tag, rep_idx):
        """Diff the shadow against the real auto-evaluation at one decoded
        case. Returns an error string on disagreement, else None."""
        key = (s, z_tag, rep_idx)
        if key in cache:
            return cache[key]
        z = tag_reps[z_tag][rep_idx]
        shadow_code = recognize_closed_form(s, z_tag)
        real = polylog(s, z)
        err = None
        if shadow_code == CF_UNEVAL:
            if not isinstance(real, polylog):
                err = ("DISAGREEMENT (dispatch)\n"
                       "  s=%r z_tag=%r z=%s\n"
                       "  shadow=CF_UNEVAL (stays unevaluated)\n"
                       "  real=polylog(%r, %s) evaluated to %s"
                       % (s, z_tag, z, s, z, real))
        else:
            if isinstance(real, polylog):
                err = ("DISAGREEMENT (dispatch)\n"
                       "  s=%r z_tag=%r z=%s\n"
                       "  shadow=code %d (closed form %s)\n"
                       "  real=polylog(%r, %s) stayed unevaluated"
                       % (s, z_tag, z, shadow_code,
                          expected_expr(shadow_code, s, z), s, z))
            else:
                want = expected_expr(shadow_code, s, z)
                if not sym_eq(real, want):
                    err = ("DISAGREEMENT (dispatch)\n"
                           "  s=%r z_tag=%r z=%s\n"
                           "  shadow=code %d -> %s\n"
                           "  real=%s" % (s, z_tag, z, shadow_code, want, real))
        cache[key] = err
        return err

    def check_expansion(z):
        """Diff the shadow expansion code against the real series expansion
        at the distinguished s (the only Requires-satisfying s)."""
        s = S_EXPAND
        shadow_code = series_expansion_at_one(s)
        # sanity: the shadow must agree with its own pure map
        if shadow_code != expansion_code(s):
            return ("DISAGREEMENT (expansion, internal)\n  s=%r\n"
                    "  shadow=%r pure-map=%r" % (s, shadow_code,
                                                 expansion_code(s)))
        real = expand_func(polylog(s, z))
        has_polar = bool(real.has(exp_polar))
        plain = -log(1 - z)
        if shadow_code == EXP_PLAIN:
            ok = (not has_polar) and sym_eq(real, plain)
        else:
            ok = has_polar
        if not ok:
            return ("DISAGREEMENT (expansion)\n  s=%r z=%s\n"
                    "  shadow=code %d (EXP_PLAIN=-log(1-z), polar-free)\n"
                    "  real=%s (has exp_polar: %r)"
                    % (s, z, shadow_code, real, has_polar))
        return None

    checked = 0
    disagreements = []

    # ---- boundary sweep: every s branch class x every tag x every rep ----
    boundary_s = [-60, -13, -3, -2, -1, 0, 1, 2, 3, 4, 7, 25, 60]
    for s in boundary_s:
        for tag in range(0, 10):
            for rep_idx in range(len(tag_reps[tag])):
                err = check_dispatch(s, tag, rep_idx)
                checked += 1
                if err:
                    print(err)
                    return 1

    # ---- expansion at the distinguished s, several z representatives ----
    from sympy import Rational as R
    for z in [w, R(1, 3), R(1, 2), S(2), S(-2), R(-3, 7), 3 + 2 * I]:
        err = check_expansion(z)
        checked += 1
        if err:
            print(err)
            return 1

    # ---- fuzz: >= 1e5 Requires-satisfying inputs, pinned seed ----
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        s = rng.randint(-60, 60)
        tag = rng.randint(0, 9)
        rep_idx = rng.randrange(len(tag_reps[tag]))
        err = check_dispatch(s, tag, rep_idx)
        checked += 1
        if err:
            print(err)
            return 1

    distinct = len(cache)
    print("G-CONF OK: shadow dispatch == real auto-evaluation and shadow "
          "expansion code == real series expansion on %d inputs "
          "(%d distinct decoded dispatch cases, seed %d, 0 disagreements)."
          % (checked, distinct, SEED))
    print(json.dumps({"checked": checked, "distinct_cases": distinct,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
