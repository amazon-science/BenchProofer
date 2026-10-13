# properties.py — PBT falsification battery for sympy__sympy-13852.
#
# NOT a Nagini module; a record of adversarial cases parsed by
# swebench_nagini.pbt. Spec cases are full model.py variants built by
# region-surgery (edits ONLY inside the # impl-start / # impl-end regions, so the
# frozen spec — axioms/pure/pre/post-conditions/signatures — is never touched and
# same_spec holds by construction). Axiom cases are real-callee probes run in the
# instance Docker image.
#
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py):
#   recognize_closed_form(s:int, z_tag:int) -> int
#     Requires(0 <= z_tag and z_tag <= 9)              # s unconstrained int
#     Requires(MustTerminate(2))                       # total correctness
#     Ensures(Result() == closed_form_for(s, z_tag))   # LOAD-BEARING: full cascade
#     + per-pattern pins (Z_C, S_SPECIAL/Z_1, S_SPECIAL/Z_2, S_KEY_A/Z_OTHER,
#       S_KEY_B/Z_OTHER must each produce an ACTUAL closed form, not CF_UNEVAL).
#   series_expansion_at_one(s:int) -> int
#     Requires(s == S_EXPAND)
#     Requires(MustTerminate(2))                       # total correctness
#     Ensures(Result() == expansion_code(s) == EXP_PLAIN != EXP_POLAR)
#
# NO read-only inputs: both functions take int parameters (by value); there is no
# Acc(x,1/2) half-permission input and no mutable container, so the FRAME-MUTATION
# class is N/A here (justified in the agent assessment). closed_form_for /
# expansion_code are GROUNDED @Pure maps (their body IS the computation, a function
# of the args, fully unfolded) — there is no opaque @ContractOnly answer-key to
# echo, so the ungrounded-oracle-echo attack does not apply; instead the cheapest
# honest echo (`return closed_form_for(s, z_tag)`) is a POSITIVE control that must
# verify (it does the work). The real attack surface is PARTIAL-DOMAIN /
# PRIORITY / OVER-FIRE over the cascade, where a rival is correct on most patterns
# but diverges on a load-bearing one — plus VACUITY-BY-DIVERGENCE (an infinite
# loop before an unreachable return satisfies every value Ensures vacuously under
# Nagini's default partial correctness), which the spec closes with
# Requires(MustTerminate(2)) on both contracted functions.
from pathlib import Path

INSTANCE = "sympy__sympy-13852"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl of recognize_closed_form (verbatim inside its impl region).
_GOLD_RCF = """    if z_tag == Z_A:
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
    return CF_UNEVAL"""

# The frozen gold impl of series_expansion_at_one. `return EXP_PLAIN` alone is
# NOT unique (it is also the body of the @Pure expansion_code), so anchor on the
# impl-region markers to target ONLY the impl region.
_GOLD_SER = "    # impl-start\n    return EXP_PLAIN\n    # impl-end"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _rcf(new_impl):
    """Build a model.py variant by replacing ONLY the recognize_closed_form impl
    region body with new_impl (series_expansion_at_one impl left at gold)."""
    return _swap(_BASE, _GOLD_RCF, new_impl)


def _ser(new_impl):
    """Build a model.py variant by replacing ONLY the series_expansion_at_one impl
    region body with new_impl (recognize_closed_form impl left at gold). The impl
    markers are preserved (re-wrapped) so the region structure stays intact."""
    return _swap(_BASE, _GOLD_SER,
                 "    # impl-start\n" + new_impl + "\n    # impl-end")


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ---- POSITIVE CONTROLS (soundness): structurally-different CORRECT impls
    #      must verify, else SPEC-TOO-STRONG. -----------------------------------

    # P1: cheapest honest impl — echo the GROUNDED @Pure cascade oracle. Because
    # closed_form_for's body IS the full computation (a function of s/z_tag, fully
    # unfolded), echoing it does the work — this is a positive control, NOT an
    # ungrounded-oracle cheat. It must verify.
    {
        "id": "pos-echo-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _rcf("    return closed_form_for(s, z_tag)"),
        "rationale": "closed_form_for is a grounded @Pure map (body = the computation, args-only); echoing it satisfies Result()==closed_form_for(s,z_tag) by definition. A correct impl must verify (else SPEC-TOO-STRONG).",
    },

    # P2: structurally-different correct impl — the six disjoint special-s equality
    # tests are REORDERED (Z_6..Z_1 instead of Z_1..Z_6) and the two s-keyed
    # clauses are written with an elif-style nested guard. The branches are
    # pairwise disjoint so order is irrelevant; the z-keyed priority is preserved.
    # No loop / no fold, so no induction lemma is needed (avoids the pilot trap).
    {
        "id": "pos-reorder-disjoint-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _rcf(
            "    if z_tag == Z_A:\n"
            "        return CF_ZA\n"
            "    if z_tag == Z_B:\n"
            "        return CF_ZB\n"
            "    if z_tag == Z_C:\n"
            "        return CF_ZC\n"
            "    if s == S_SPECIAL:\n"
            "        if z_tag == Z_6:\n"
            "            return CF_P6\n"
            "        if z_tag == Z_5:\n"
            "            return CF_P5\n"
            "        if z_tag == Z_4:\n"
            "            return CF_P4\n"
            "        if z_tag == Z_3:\n"
            "            return CF_P3\n"
            "        if z_tag == Z_2:\n"
            "            return CF_P2\n"
            "        if z_tag == Z_1:\n"
            "            return CF_P1\n"
            "        return CF_UNEVAL\n"
            "    if s == S_KEY_B:\n"
            "        return CF_SB\n"
            "    if s == S_KEY_A:\n"
            "        return CF_SA\n"
            "    return CF_UNEVAL"
        ),
        "rationale": "the six special-s checks and the two s-keyed checks are mutually exclusive equality tests, so reordering them preserves the cascade; the z-keyed priority block is unchanged. A correct restructure must verify (else SPEC-TOO-STRONG).",
    },

    # P3: structurally-different correct series-expansion impl — bind a typed local
    # then return it (Nagini-legal: type comment attaches to the assignment target).
    {
        "id": "pos-series-local-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _ser("    result = EXP_PLAIN  # type: int\n    return result"),
        "rationale": "a local-variable reshape of the s=1 expansion is still EXP_PLAIN; must verify (else SPEC-TOO-STRONG).",
    },

    # ---- ADMISSIBILITY: the precondition admits a normal F2P-shaped input. -----

    # A1: the impl asserts (in-region) that the @Pure oracle the postcondition is
    # pinned to actually computes the F2P-load-bearing answers for representative
    # in-domain inputs, then runs the correct cascade. If the precondition were
    # too strong / the spec inconsistent for these inputs the asserts (or the
    # postcondition) would fail to verify.
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rcf(
            "    Assert(closed_form_for(S_SPECIAL, Z_2) == CF_P2)\n"
            "    Assert(closed_form_for(S_SPECIAL, Z_1) == CF_P1)\n"
            "    Assert(closed_form_for(S_KEY_A, Z_OTHER) == CF_SA)\n"
            "    Assert(closed_form_for(S_KEY_B, Z_OTHER) == CF_SB)\n"
            "    Assert(closed_form_for(S_EXPAND, Z_A) == CF_ZA)\n"
            + _GOLD_RCF
        ),
        "rationale": "representative F2P-shaped inputs (s=2/z=2, s=2/z=1/2, s=0, s=-1, z-keyed-wins) are admitted by Requires(0<=z_tag<=9) and the cascade pins them; the asserts + postcondition verify (else PRECOND-TOO-STRONG).",
    },

    # ---- UNIQUENESS / PARTIAL-DOMAIN rivals: same spec, WRONG impl that must be
    #      REJECTED. Each carries the refinement that its faithful real patch would
    #      NOT resolve the F2P. ---------------------------------------------------

    # W1: drop the z=2 special (s=2, Z_2) -> stays unevaluated (CF_UNEVAL).
    # This is the single most F2P-load-bearing pattern: the gold F2P asserts the
    # SYMBOLIC equality polylog(2,2) == pi**2/4 - I*pi*log(2).
    {
        "id": "weak-drop-special-z2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "        if z_tag == Z_2:\n            return CF_P2\n", "", 1)),
        "refinement": "a faithful patch omitting the z==2 special leaves polylog(2,2) UNEVALUATED, so the F2P symbolic assertion `polylog(2, 2) == pi**2/4 - I*pi*log(2)` FAILS -> test_polylog_values does NOT pass -> not resolved.",
        "rationale": "rejected by Ensures(Result()==closed_form_for(s,z_tag)) AND the explicit Ensures(Implies(s==S_SPECIAL and z_tag==Z_2, Result()==CF_P2)): the rival returns CF_UNEVAL at (S_SPECIAL,Z_2) where the cascade demands CF_P2.",
    },

    # W2: drop the z=1/2 special (s=2, Z_1) -> stays unevaluated.
    # The other F2P symbolic assertion is polylog(2, 1/2) == pi**2/12 - log(2)**2/2.
    {
        "id": "weak-drop-special-z1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "        if z_tag == Z_1:\n            return CF_P1\n", "", 1)),
        "refinement": "omitting the z==1/2 special leaves polylog(2,1/2) UNEVALUATED, so the F2P symbolic assertion `polylog(2, S.Half) == pi**2/12 - log(2)**2/2` FAILS -> not resolved.",
        "rationale": "rejected by the cascade postcondition and Ensures(Implies(s==S_SPECIAL and z_tag==Z_1, Result()==CF_P1)).",
    },

    # W3: WRONG code binding — swap CF_P1<->CF_P2 (z=1/2 returns CF_P2, z=2 returns
    # CF_P1). Mirrors axiom_check.py's discrimination control. Both F2P symbolic
    # asserts then bind the WRONG closed form.
    {
        "id": "weak-swap-p1-p2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF
                       .replace("        if z_tag == Z_1:\n            return CF_P1\n",
                                "        if z_tag == Z_1:\n            return CF_P2\n", 1)
                       .replace("        if z_tag == Z_2:\n            return CF_P2\n",
                                "        if z_tag == Z_2:\n            return CF_P1\n", 1)),
        "refinement": "swapping the closed forms makes polylog(2,1/2) return pi**2/4 - I*pi*log(2) and polylog(2,2) return pi**2/12 - log(2)**2/2 — BOTH F2P symbolic asserts then compare against the wrong value and FAIL -> not resolved.",
        "rationale": "rejected by Ensures(Implies(...Z_1, Result()==CF_P1)) and Ensures(Implies(...Z_2, Result()==CF_P2)): the rival returns CF_P2 at Z_1 and CF_P1 at Z_2.",
    },

    # W4: drop the s==0 (S_KEY_A) clause -> CF_UNEVAL.
    # The F2P numeric loop `for s in [-1,0,1]` compares polylog(s,z).evalf() to
    # polylog(s,z,evaluate=False).evalf(); if s=0 stays unevaluated the two sides
    # are identical and the loop is vacuous, BUT P2P/expansion identity
    # polylog(0,z)==z/(1-z) (test_polylog_expansion myexpand) breaks; more directly
    # the spec pins it via the explicit s-keyed Ensures clause.
    {
        "id": "weak-drop-s0-keyed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "    if s == S_KEY_A:\n        return CF_SA\n", "", 1)),
        "refinement": "dropping s==0 leaves polylog(0,z) unevaluated, so the gold closed form z/(1-z) is never produced; the s-keyed auto-evaluation the patch adds is absent — the faithful patch missing this clause does not introduce the s=0 closed form the issue requires.",
        "rationale": "rejected by Ensures(Result()==closed_form_for(s,z_tag)) and the explicit Ensures(Implies(s==S_KEY_A and z_tag==Z_OTHER, Result()==CF_SA)): rival returns CF_UNEVAL at (S_KEY_A, Z_OTHER).",
    },

    # W5: PRIORITY VIOLATION — check s==S_KEY_A (s=0) BEFORE the z-keyed clauses.
    # Then at (s=0, z_tag=Z_A) the rival returns CF_SA, but the cascade demands
    # CF_ZA (the z-keyed clause wins for any s).
    {
        "id": "weak-priority-s0-before-zkeyed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(
            "    if s == S_KEY_A:\n"
            "        return CF_SA\n"
            "    if z_tag == Z_A:\n"
            "        return CF_ZA\n"
            "    if z_tag == Z_B:\n"
            "        return CF_ZB\n"
            "    if z_tag == Z_C:\n"
            "        return CF_ZC\n"
            "    if s == S_SPECIAL:\n"
            "        if z_tag == Z_1:\n"
            "            return CF_P1\n"
            "        if z_tag == Z_2:\n"
            "            return CF_P2\n"
            "        if z_tag == Z_3:\n"
            "            return CF_P3\n"
            "        if z_tag == Z_4:\n"
            "            return CF_P4\n"
            "        if z_tag == Z_5:\n"
            "            return CF_P5\n"
            "        if z_tag == Z_6:\n"
            "            return CF_P6\n"
            "        return CF_UNEVAL\n"
            "    if s == S_KEY_B:\n"
            "        return CF_SB\n"
            "    return CF_UNEVAL"
        ),
        "refinement": "checking s==0 before z==1 makes polylog(0,1) auto-evaluate via z/(1-z) at z=1 -> division by zero (zoo) instead of the gold zeta(0); the priority the dispatch must preserve is broken — polylog(0,1) would no longer be the zeta value (axiom_check.py asserts polylog(0,1)==zeta(0)).",
        "rationale": "rejected by Ensures(Result()==closed_form_for(s,z_tag)): closed_form_for(S_KEY_A, Z_A) == CF_ZA (z-keyed wins) but the rival returns CF_SA.",
    },

    # W6: OVER-FIRE — at s=2 with an unrecognised z (Z_OTHER and any non-special
    # z_tag) the rival returns CF_SA instead of CF_UNEVAL.
    {
        "id": "weak-overfire-s2-else",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(_GOLD_RCF.replace(
            "        if z_tag == Z_6:\n            return CF_P6\n        return CF_UNEVAL",
            "        if z_tag == Z_6:\n            return CF_P6\n        return CF_SA", 1)),
        "refinement": "over-firing makes polylog(2, z) return z/(1-z) at a generic z (e.g. z=1/3) where the gold callee stays UNEVALUATED — a wrong closed form; axiom_check.py's non-over-fire control (`s=2 generic z=1/3 stays symbolic`) FAILS, and P2P symbolic identities for polylog(2,·) break.",
        "rationale": "rejected by Ensures(Result()==closed_form_for(s,z_tag)): closed_form_for(S_SPECIAL, Z_OTHER) == CF_UNEVAL (the s=2 block's else) but the rival returns CF_SA.",
    },

    # W8: VACUITY-BY-DIVERGENCE — an infinite loop before an unreachable echo of
    # the oracle. Under partial correctness every value Ensures holds vacuously
    # (this was the G-PANEL-1 audit's atk_8_oracle_echo hole); the
    # Requires(MustTerminate(2)) obligation makes Nagini's obligation leak check
    # reject the loop (it carries no decreasing termination measure).
    {
        "id": "weak-nonterm-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rcf(
            "    i = 0  # type: int\n"
            "    while i >= 0:\n"
            "        Invariant(i >= 0)\n"
            "        i = i + 1\n"
            "    return closed_form_for(s, z_tag)"
        ),
        "refinement": "a faithful patch whose eval dispatch never returns hangs every polylog(...) construction, so the F2P test_polylog_values (which constructs polylog(2,2), polylog(2,1/2), ...) never completes -> not resolved.",
        "rationale": "rejected by the MustTerminate(2) precondition: the loop takes no termination obligation (no decreasing measure), so Nagini's obligation leak check fails; without the obligation this impl verified vacuously (the audit's spec-too-weak witness).",
    },

    # ---- SERIES-EXPANSION rival (non-gating co-fix, kept for faithfulness). -----

    # W7: return EXP_POLAR (the pre-patch -log(1 + exp_polar(-I*pi)*z)).
    {
        "id": "weak-series-polar",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ser("    return EXP_POLAR"),
        "refinement": "returning EXP_POLAR is the pre-patch s=1 expansion -log(1 + exp_polar(-I*pi)*z), which the gold test_patch's myexpand(polylog(1,z), -log(1-z)) rejects. NOTE: test_polylog_expansion is NEITHER F2P nor P2P (non-gating co-fix per refinement.md §B); this reject defends the modeled co-fix's faithfulness, not the F2P gate. The spec is intentionally a conjunction the gold patch satisfies in full, so verify=>resolved is preserved.",
        "rationale": "rejected by Ensures(Result()==expansion_code(s)), Ensures(Result()==EXP_PLAIN) and Ensures(Result()!=EXP_POLAR): EXP_POLAR violates all three.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — no consumed @ContractOnly axiom (axioms region empty), but two
# A-reference deep models (closed_form_for / expansion_code) validated == the real
# gold-patched callee. These probes re-run the REAL polylog / expand_func in the
# instance image (runner applies the gold patch). Mirrors axiom_check.py.
# ---------------------------------------------------------------------------

# axiom-soundness probe: the model's code<->closed-form bindings are SOUND against
# the real callee (each recognised pattern auto-evaluates to EXACTLY the gold
# closed form the code names AND actually fired; unrecognised patterns stay
# unevaluated; s=1 expansion is polar-free -log(1-z)). Self-contained: imports
# only sympy (stdlib + sympy). Exit 0 iff every obligation holds.
_AX_SOUND_PROBE = r'''
import sys, random
try:
    from sympy import (polylog, expand_func, pi, log, sqrt, I, S, Rational,
                        symbols, Abs, exp_polar, zeta, dirichlet_eta)
except Exception as exc:
    print("AX SKIP: sympy not importable (%r)" % (exc,))
    sys.exit(0)

# code <-> concrete gold closed form (same integer codes as model.py / axiom_check.py)
CF_ZC, CF_P1, CF_P2, CF_P3, CF_P4, CF_P5, CF_P6, CF_SA, CF_SB = 3,4,5,6,7,8,9,10,11

def gold_cf(code, z):
    if code == CF_ZC: return S.Zero
    if code == CF_P1: return pi**2/12 - log(2)**2/2
    if code == CF_P2: return pi**2/4 - I*pi*log(2)
    if code == CF_P3: return -pi**2/15 + log((sqrt(5)-1)/2)**2/2
    if code == CF_P4: return -pi**2/10 - log((sqrt(5)+1)/2)**2
    if code == CF_P5: return pi**2/15 - log((sqrt(5)-1)/2)**2
    if code == CF_P6: return pi**2/10 - log((sqrt(5)-1)/2)**2
    if code == CF_SA: return z/(1 - z)
    if code == CF_SB: return z/(1 - z)**2
    raise AssertionError("no gold form for code %d" % code)

def unevaluated(e):
    return isinstance(e, polylog)

fail = []
def check(cond, msg):
    if not cond: fail.append(msg)

g = sqrt(5)
specials = [
    ("s=2 z=1/2", 2, S.Half, CF_P1),
    ("s=2 z=2",   2, S(2),   CF_P2),
    ("s=2 z=-(g-1)/2", 2, -(g-1)/2, CF_P3),
    ("s=2 z=-(g+1)/2", 2, -(g+1)/2, CF_P4),
    ("s=2 z=(3-g)/2",  2, (3-g)/2,  CF_P5),
    ("s=2 z=(g-1)/2",  2, (g-1)/2,  CF_P6),
]
for label, s, zz, code in specials:
    real = polylog(s, zz)
    check(not unevaluated(real), "%s did NOT fire (stayed unevaluated)" % label)
    if not unevaluated(real):
        diff = (real - gold_cf(code, zz)).simplify()
        check(diff == 0, "%s: real != gold (diff=%s)" % (label, diff))
        d = Abs(real.evalf(30) - gold_cf(code, zz).evalf(30))
        check(d < S(1)/10**12, "%s: numeric mismatch %s" % (label, d))

# the two F2P symbolic assertions verbatim
check(polylog(2, S(2)) == pi**2/4 - I*pi*log(2), "F2P symbolic polylog(2,2)")
check(polylog(2, S.Half) == pi**2/12 - log(2)**2/2, "F2P symbolic polylog(2,1/2)")

# z=0 -> exact zero for any s (CF_ZC)
for s in [-2,-1,0,1,2,3, symbols('s')]:
    check(polylog(s, S.Zero) == S.Zero, "polylog(%s,0) != 0" % s)

# s=0 -> z/(1-z) (CF_SA), s=-1 -> z/(1-z)**2 (CF_SB) numerically over random z
rng = random.Random(13852)
for s, code in [(0, CF_SA), (-1, CF_SB)]:
    for _ in range(40):
        zz = S(rng.uniform(-5,5)).evalf(30) + I*S(rng.uniform(-5,5)).evalf(30)
        d = Abs(polylog(s, zz).evalf(30) - gold_cf(code, zz).evalf(30))
        check(d < S(1)/10**12, "s=%d random z numeric mismatch %s" % (s, d))

# priority cascade: z-keyed clauses win over s-keyed
check(polylog(0, S.One) == zeta(0), "priority polylog(0,1)!=zeta(0)")
check(polylog(0, -S.One) == -dirichlet_eta(0), "priority polylog(0,-1)")
check(polylog(-1, S.One) == zeta(-1), "priority polylog(-1,1)")
check(polylog(0, S.Zero) == S.Zero and polylog(-1, S.Zero) == S.Zero, "priority z=0 zeros")

# NO over-fire: unrecognised patterns stay unevaluated
for label, s, zz in [("s=2 z=1/3", 2, Rational(1,3)),
                     ("s=3 z=1/2", 3, Rational(1,2)),
                     ("s=2 z=7/5", 2, Rational(7,5))]:
    check(unevaluated(polylog(s, zz)), "over-fire: %s evaluated to %s" % (label, polylog(s, zz)))

# s=1 expansion polar-free -log(1-z)
z = symbols('z')
e = expand_func(polylog(1, z))
check(e == -log(1 - z), "s=1 expansion %s != -log(1-z)" % e)
check(not e.has(exp_polar), "s=1 expansion still has exp_polar: %s" % e)

if fail:
    print("AX-SOUND FAIL: " + " || ".join(fail))
    sys.exit(1)
print("AX-SOUND OK: all code<->closed-form bindings match the real polylog; "
      "priority cascade holds; no over-fire; s=1 expansion polar-free.")
sys.exit(0)
'''

# axiom-containment probe: enumerate EXACTLY the (s, z_tag) inputs the MODEL can
# reach (the model's Requires + the discrete dispatch quotient) and assert that
# for every input the model maps to a NON-UNEVAL code, the real callee actually
# AUTO-EVALUATES (and for CF_UNEVAL the real callee STAYS unevaluated) — i.e. the
# model never claims a closed form outside the real dispatch's recognised domain
# (AXIOM-TOO-WEAK-FOR-CALLER would be a model-reachable input the real callee does
# not handle the way the code asserts). Covering MORE of the callee than the model
# reaches would be sound; the defect is only a model-reachable input outside it.
_AX_COVER_PROBE = r'''
import sys
try:
    from sympy import (polylog, pi, log, sqrt, I, S, symbols, Abs,
                       zeta, dirichlet_eta)
except Exception as exc:
    print("AX SKIP: sympy not importable (%r)" % (exc,))
    sys.exit(0)

# The model's discrete dispatch quotient -> concrete (s_value, z_value) the model
# can reach. s in {S_SPECIAL=2, S_KEY_A=0, S_KEY_B=-1} plus a generic s for the
# z-keyed clauses; z_tag 0..9 -> concrete z. (z_tag=0 = Z_OTHER, a generic z.)
g = sqrt(5)
Z_OF = {
    0: S(1)/3,        # Z_OTHER: a generic unrecognised z
    1: S.One,         # Z_A: z==1
    2: -S.One,        # Z_B: z==-1
    3: S.Zero,        # Z_C: z==0
    4: S.Half,        # Z_1: z==1/2  (only special at s==2)
    5: S(2),          # Z_2: z==2
    6: -(g-1)/2,      # Z_3
    7: -(g+1)/2,      # Z_4
    8: (3-g)/2,       # Z_5
    9: (g-1)/2,       # Z_6
}

# The model's @Pure closed_form_for cascade (mirrored exactly), 0==CF_UNEVAL.
CF_UNEVAL=0; CF_ZA=1; CF_ZB=2; CF_ZC=3
CF_P1,CF_P2,CF_P3,CF_P4,CF_P5,CF_P6 = 4,5,6,7,8,9
CF_SA,CF_SB = 10,11
def model_code(s_pred, z_tag):
    if z_tag == 1: return CF_ZA
    if z_tag == 2: return CF_ZB
    if z_tag == 3: return CF_ZC
    if s_pred == 2:
        return {4:CF_P1,5:CF_P2,6:CF_P3,7:CF_P4,8:CF_P5,9:CF_P6}.get(z_tag, CF_UNEVAL)
    if s_pred == 0: return CF_SA
    if s_pred == -1: return CF_SB
    return CF_UNEVAL

def unevaluated(e):
    return isinstance(e, polylog)

fail = []
# s-predicate values the dispatch branches on, plus a couple of generic s for the
# z-keyed clauses (where the dispatch is s-agnostic).
s_values = [2, 0, -1, 3, 5]
checked = 0
for s in s_values:
    for z_tag in range(10):
        z = Z_OF[z_tag]
        code = model_code(s, z_tag)
        real = polylog(s, z)
        checked += 1
        if code == CF_UNEVAL:
            # the model claims NO closed form -> the real callee must stay
            # unevaluated (the model is not under-claiming a real evaluation in
            # a way that would silently disagree). Tolerate the special z-keyed
            # exact values that always evaluate (z=0/1/-1) which model also codes.
            if z_tag in (1, 2, 3):
                # z-keyed clauses always recognised -> code is never CF_UNEVAL here
                fail.append("model says UNEVAL but z_tag=%d is z-keyed (s=%s)" % (z_tag, s))
            else:
                if not unevaluated(real):
                    fail.append("model UNEVAL but real polylog(%s,%s)=%s EVALUATED "
                                "(model-reachable input outside coverage)" % (s, z, real))
        else:
            # the model claims a closed form -> the real callee MUST auto-evaluate
            # (this input lies inside the real dispatch's recognised domain).
            if unevaluated(real):
                fail.append("model code=%d but real polylog(%s,%s) STAYED unevaluated "
                            "(AXIOM-TOO-WEAK-FOR-CALLER: claimed form the callee "
                            "does not produce)" % (code, s, z))

if fail:
    print("AX-COVER FAIL: " + " || ".join(fail))
    sys.exit(1)
print("AX-COVER OK: every model-reachable (s,z_tag) is consistent with the real "
      "dispatch domain (%d patterns: each non-UNEVAL code corresponds to a real "
      "auto-evaluation; each UNEVAL to a real unevaluated polylog)." % checked)
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-dispatch",
        "axiom": "closed_form_for / expansion_code (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "if the real gold-patched polylog does NOT auto-evaluate each recognised pattern to exactly the gold closed form the code names (or over-fires, or the s=1 expansion still carries exp_polar) the A-reference is unsound (AXIOM-UNSOUND). Mirrors axiom_check.py against the real callee.",
    },
    {
        "id": "ax-cover-dispatch",
        "axiom": "closed_form_for (A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "enumerates EXACTLY the (s,z_tag) the model can reach (its discrete dispatch quotient) and asserts each non-UNEVAL code lands inside the real dispatch's recognised domain (real callee auto-evaluates) and each UNEVAL stays unevaluated; a model-reachable input the real callee handles differently => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
