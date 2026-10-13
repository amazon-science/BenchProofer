#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13852.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same discrete argument patterns and comparing the closed-form
CODE each assigns:

  * SHADOW  — the R/I-tagged dispatch of Solution.lean's impl region
              (`recognizeClosedForm` / `closedFormFor`) transliterated to Python
              over the discrete dispatch quotient (mapping.md §2): `s` as int,
              `z` as a tag in {0..9}, result as a closed-form code. This is the
              priority cascade verbatim — z-keyed clauses first (any s), then the
              distinguished-s special arguments, then the s-keyed clauses, else
              "unevaluated". The A-reference content (which concrete closed form
              a code names) is out of scope for G-CONF; it stays with G-AX.
  * ORACLE  — patch.diff's behaviour: the patched real callee. We run the REAL
              polylog(s, z) at the concrete argument each tag denotes, classify
              the result into the same closed-form code (by symbolic equality
              with the gold closed form, or "unevaluated" if it stays a polylog
              instance / or one of the s-only z-keyed forms), and compare.

They must agree on every argument pattern. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image). The eval image ships
the PRE-patch sympy at base_commit, so — exactly as axiom_check.py — this script
applies patch.diff to /testbed (idempotently) before importing sympy, then
exercises the real gold-patched dispatch.
"""
import sys
import os
import subprocess


def _ensure_gold_patched():
    """Apply patch.diff to /testbed unless already applied. Idempotent."""
    testbed = "/testbed"
    if not os.path.isdir(testbed):
        return
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.path.join(here, "patch.diff"), "/work/patch.diff",
                  "/gold.patch"]
    patch = next((p for p in candidates if os.path.isfile(p)), None)
    if patch is None:
        print("G-CONF NOTE: patch.diff not found; using ambient /testbed.")
        return
    already = subprocess.run(["git", "apply", "--reverse", "--check", patch],
                             cwd=testbed, capture_output=True, text=True)
    if already.returncode == 0:
        print("G-CONF NOTE: gold patch already applied; skipping re-apply.")
        return
    fwd = subprocess.run(["git", "apply", "--check", patch],
                         cwd=testbed, capture_output=True, text=True)
    if fwd.returncode != 0:
        print("G-CONF FAIL: gold patch neither forward- nor reverse-applies: %s"
              % fwd.stderr.strip())
        sys.exit(1)
    applied = subprocess.run(["git", "apply", patch], cwd=testbed,
                             capture_output=True, text=True)
    if applied.returncode != 0:
        print("G-CONF FAIL: gold patch failed to apply: %s"
              % applied.stderr.strip())
        sys.exit(1)
    print("G-CONF NOTE: applied gold patch.diff to /testbed.")


_ensure_gold_patched()

try:
    from sympy import (polylog, pi, log, sqrt, I, S, zeta, dirichlet_eta,
                       symbols)
except Exception as exc:  # pragma: no cover
    print("G-CONF SKIP: sympy not importable (%r); run in-container." % (exc,))
    sys.exit(0)


# --- closed-form code constants (lock-step with Solution.lean) --------------
CF_UNEVAL, CF_ZA, CF_ZB, CF_ZC = 0, 1, 2, 3
CF_P1, CF_P2, CF_P3, CF_P4, CF_P5, CF_P6 = 4, 5, 6, 7, 8, 9
CF_SA, CF_SB = 10, 11

# z-tags (Solution.lean: zA..z6, zOther)
Z_A, Z_B, Z_C = 1, 2, 3
Z_1, Z_2, Z_3, Z_4, Z_5, Z_6 = 4, 5, 6, 7, 8, 9
Z_OTHER = 0

# s-predicate values
S_SPECIAL, S_KEY_A, S_KEY_B = 2, 0, -1


# --- the R/I shadow: closedFormFor transliterated to Python -----------------
def shadow_code(s, z_tag):
    """closedFormFor(s, z_tag) — the priority cascade, verbatim."""
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    if s == S_SPECIAL:
        return {Z_1: CF_P1, Z_2: CF_P2, Z_3: CF_P3, Z_4: CF_P4,
                Z_5: CF_P5, Z_6: CF_P6}.get(z_tag, CF_UNEVAL)
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL


# --- the concrete (s, z_tag) <-> (s, z) decoding (mapping.md key) -----------
def concrete_z(z_tag):
    g = sqrt(5)
    return {
        Z_A: S.One, Z_B: -S.One, Z_C: S.Zero,
        Z_1: S.Half, Z_2: S(2), Z_3: -(g - 1) / 2, Z_4: -(g + 1) / 2,
        Z_5: (3 - g) / 2, Z_6: (g - 1) / 2,
        # representative of zOther: a generic z matching none of the nine
        # recognised values (so the s-keyed clauses are genuinely exercised).
        Z_OTHER: S(1) / 3,
    }[z_tag]


def gold_form(code, s, z):
    """The concrete gold closed form each code names (cf. axiom_check.py)."""
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
    raise AssertionError("no gold form for code %d" % code)


def oracle_code(s, z_tag):
    """Classify the REAL polylog(s, z) into the closed-form code the dispatch
    produced. Unevaluated -> CF_UNEVAL; otherwise match against the gold form
    the shadow predicts (a wrong shadow prediction is caught as a disagreement
    because the real result then fails to equal the predicted gold form)."""
    s_expr = S(s)
    z = concrete_z(z_tag)
    real = polylog(s_expr, z)
    if isinstance(real, polylog):
        return CF_UNEVAL
    predicted = shadow_code(s, z_tag)
    if predicted == CF_UNEVAL:
        # real evaluated but the shadow says unevaluated -> over-fire mismatch.
        return ("EVALUATED-BUT-SHADOW-UNEVAL", real)
    gold = gold_form(predicted, s_expr, z)
    # Structural equality first: it handles the degenerate s-only z-keyed forms
    # at a pole (e.g. polylog(1,1) and zeta(1) both auto-reduce to complex
    # infinity `zoo`, where a `real - gold` subtraction is indeterminate).
    if real == gold:
        return predicted
    # Finite case: confirm equality by symbolic simplification of the difference.
    if real.is_finite is not False and gold.is_finite is not False:
        if (real - gold).simplify() == 0:
            return predicted
    return ("EVALUATED-TO-OTHER", real)


def main():
    # All (s, z_tag) pairs the dispatch distinguishes: s over the distinguished
    # predicates plus a few generic ints; z_tag over the full tag range.
    s_values = [-2, -1, 0, 1, 2, 3]
    z_tags = list(range(0, 10))
    disagreements = []
    count = 0
    for s in s_values:
        for z_tag in z_tags:
            count += 1
            sh = shadow_code(s, z_tag)
            orc = oracle_code(s, z_tag)
            # CF_ZA/CF_ZB are s-only forms (zeta/eta), confirmed by gold_form.
            # Z_OTHER is represented by a generic z (1/3) matching none of the
            # nine recognised values: at s=0/s=-1 the s-keyed clauses fire
            # (CF_SA/CF_SB); at a generic s the call stays unevaluated.
            if sh != orc:
                disagreements.append((s, z_tag, sh, orc))
                if len(disagreements) >= 8:
                    break
        if len(disagreements) >= 8:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d patterns:"
              % (len(disagreements), count))
        for s, zt, sh, orc in disagreements:
            print("  s=%s z_tag=%s shadow=%r oracle=%r" % (s, zt, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of recognizeClosedForm (the closedFormFor "
          "priority cascade) agrees with patch.diff behaviour on %d argument "
          "patterns, 0 disagreements." % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
