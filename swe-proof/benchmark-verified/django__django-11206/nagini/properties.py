"""properties.py — PBT falsification manifest for django__django-11206.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    format_small(coeff: int, exponent: int, decimal_pos: int) -> Optional[List[int]]

modelling the gold patch's "below-the-visible-window magnitude collapses to a
padded zero" guard (django/utils/numberformat.format). Its load-bearing
postcondition is, with the @Pure deep models `below_cutoff` / `zero_render`:

    P1  Implies(not below_cutoff(coeff, exponent, decimal_pos), Result() is None)
    P2  Implies(below_cutoff(coeff, exponent, decimal_pos),     Result() is not None)
    P3  Implies(Result() is not None, Acc(list_pred(Result())))          # fresh, full perm
    P4  Implies(below_cutoff(coeff, exponent, decimal_pos),
                opt_seq(Result()) == zero_render(decimal_pos))           # the value pin

What the spec defends, and the attacks it must survive:

  * GROUNDED ORACLE, no echo. `below_cutoff` and `zero_render` are @Pure deep
    models fully unfolded by Viper over the integer args (NOT @ContractOnly
    opaque answer-keys), and there is no executable materialization of a @Pure
    PSeq into a list_pred list. So you cannot `return <materialize
    zero_render(...)>` to echo a wrong answer; the only way to satisfy P4 is to
    build the code-point list element-by-element (the real work). Therefore the
    UNGROUNDED-ORACLE-ECHO class is N/A; in its place we keep an HONEST
    cheapest-impl positive control (`pos-control-grounded-guard`) that uses the
    grounded oracle directly as the smallness guard and must verify.

  * NO READ-ONLY INPUT. All three parameters are `int` (passed by value); the
    only `Acc` is on the freshly built Result (`Acc(list_pred(Result()))`, full
    write perm). There is no `Acc(x,1/2)` half-permission input to overwrite, so
    the FRAME-MUTATION class is N/A (justified in the agent's assessment). A
    `coeff[i]=…`-style write has nothing to target.

  * NO HIDDEN CONTROL-FLOW EFFECT. The only behavioural fork is "produce a
    rendering" vs "return None" (fall through to the ordinary path), and that
    fork is fully visible to the value abstraction via P1/P2 (Result() is /
    is not None). There is no raise / mutation / side-effect the value
    abstraction cannot see, so the CONTROL-FLOW-EFFECT capability-token class is
    N/A; the return-shape rivals (`rival-over-collapse`, `rival-never-collapse`)
    already exercise the None/not-None fork against P1/P2.

  * The real attack surface is PARTIAL-DOMAIN on the smallness decision and the
    zero rendering: the strict-vs-non-strict cutoff edge, the max(decimal_pos,1)
    threshold floor (the rjust-quirk), the exact-zero magnitude, the dp==0
    no-separator rendering, and the pad length. Every uniqueness rival below is
    one of those, each with the refinement argument that its faithful real patch
    would FAIL the F2P/P2P (verify ⇏ resolve break, not an artifact).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the nested invariants region
lives there too), so `markers.same_spec` is guaranteed and a rejection comes from
the POSTCONDITION catching wrong behaviour, never from a tampered spec. The
uniqueness rivals deliberately DROP the impl's own `Assert(is_small ==
below_cutoff(...))` / render-pin asserts so the rejection is forced by the
POSTCONDITION (P1/P2/P4) itself, not by the impl's self-check.

Axiom lane: this bundle consumes NO @ContractOnly axiom (meta.axioms == []); the
smallness decision and zero rendering are A-reference deep models validated ==
the real arithmetic by axiom_check.py (G-AX). The AXIOM_TESTS below re-run that
A-reference soundness in Docker against the Python stdlib `decimal` (the very
module the gold patch uses — `Decimal('0.'+'1'.rjust(dp,'0'))`), fuzzing the
strict edge / boundaries to try to make the real callee disagree with the deep
model. Probes import only stdlib, read no files.
"""
from pathlib import Path

INSTANCE = "django__django-11206"
FLOAT_ENCODING = None  # meta.float_encoding is null (exact integer arithmetic)

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The smallness-decision block + its guarding self-assert (impl region).
_IS_SMALL_BLOCK = """    is_small = False  # type: bool
    if coeff == 0:
        is_small = True
    elif shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))"""

# The threshold-floor computation (the rjust-quirk: max(decimal_pos,1)).
_FLOOR_BLOCK = """    p = decimal_pos
    if p < 1:
        p = 1
    shifted = exponent + p"""

# The dp==0 rendering branch (no separator, just '0').
_DP0_BLOCK = """    if decimal_pos == 0:
        result = [48]  # type: List[int]
        Assert(ToSeq(result) == zero_render(decimal_pos))
        return result"""

# The dp>=1 final assembly (prefix '0' '.' onto the run of zeros) + pins.
_ASSEMBLE_BLOCK = """    result = [48, 46] + frac
    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
    Assert(ToSeq(result) == zero_render(decimal_pos))
    return result"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5/2) HONEST cheapest-impl / grounded-guard positive control. Instead of the
# gold's spelled-out branch computation of `is_small`, use the GROUNDED @Pure
# oracle directly as the guard: `is_small = below_cutoff(...)`. This is the
# cheapest impl of the smallness decision and is CORRECT, so it must verify. It
# also demonstrates the spec is NOT echo-vulnerable: `below_cutoff` is grounded
# in the args (fully unfolded), there is no WRONG value it could echo — using it
# directly simply re-derives the gold decision. The render path is unchanged, so
# all gold render obligations still hold. If this fails => SPEC-TOO-STRONG
# (over-fit to the inline branch form of the decision).
_POS_GROUNDED = _swap(
    _BASE, _IS_SMALL_BLOCK,
    "    is_small = below_cutoff(coeff, exponent, decimal_pos)  # type: bool",
)

# (5) Structurally-DIFFERENT but CORRECT: the is_small decision rewritten as TWO
# separate `if`s (nonzero-small first, then the coeff==0 case) instead of the
# if/elif chain. Semantically identical (coeff==0 forces is_small True either
# way; coeff>0 hits only the first if), different executable shape. The guarding
# `Assert(is_small == below_cutoff(...))` is KEPT (it must still hold), and the
# render path is untouched, so the gold proof obligations are all preserved
# (avoids the pilot's drop-a-framing-assert trap). If this fails to verify the
# postcondition is over-fit to one branch structure => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _IS_SMALL_BLOCK,
    """    is_small = False  # type: bool
    if shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    if coeff == 0:
        is_small = True
    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))""",
)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped in-domain input — the flipped
# F2P row `1.234e-300` at decimal_pos=3 has magnitude 1234 * 10**-303, i.e.
# coeff=1234, exponent=-303, decimal_pos=3 (all >= 0 where required). The call
# must establish the precondition `coeff >= 0 and decimal_pos >= 0` for a normal
# input. If it cannot => PRECOND-TOO-STRONG. (The result is unused; the callee's
# own contract discharges its obligations.)
_ADMISS = _swap(
    _BASE,
    "    p = decimal_pos\n    if p < 1:\n        p = 1\n",
    "    _probe = format_small(1234, -303, 3)\n"
    "    p = decimal_pos\n    if p < 1:\n        p = 1\n",
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (3a) PARTIAL-DOMAIN / strict-edge: NON-STRICT cutoff. Collapses a magnitude
# EXACTLY at the threshold (coeff*10**shifted == 1, i.e. shifted==0 and coeff==1)
# in addition to the strictly-below ones. Everything strictly below or strictly
# above is handled exactly as gold; only the exact-cutoff edge flips. The
# guarding assert is DROPPED so the rejection is forced by P1.
_RIVAL_NONSTRICT = _swap(
    _BASE, _IS_SMALL_BLOCK,
    """    is_small = False  # type: bool
    if coeff == 0:
        is_small = True
    elif shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    elif shifted == 0 and coeff == 1:
        is_small = True""",
)

# (3b) PARTIAL-DOMAIN: NO threshold floor. Drops `if p < 1: p = 1`, so at
# decimal_pos==0 the cutoff becomes 10**-0 == 1 instead of the real
# 10**-1 == 0.1 (the rjust-quirk). Values in [0.1, 1) at dp==0 (e.g. 0.5,
# coeff=5 exponent=-1) are wrongly collapsed. Guarding assert dropped (P1 forces
# the rejection).
_RIVAL_NOFLOOR = _swap(
    _swap(_BASE, _FLOOR_BLOCK, "    p = decimal_pos\n    shifted = exponent + p"),
    "    is_small = False  # type: bool\n"
    "    if coeff == 0:\n"
    "        is_small = True\n"
    "    elif shifted < 0 and coeff < pow10(-shifted):\n"
    "        is_small = True\n"
    "    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))",
    "    is_small = False  # type: bool\n"
    "    if coeff == 0:\n"
    "        is_small = True\n"
    "    elif shifted < 0 and coeff < pow10(-shifted):\n"
    "        is_small = True",
)

# (1-inverse) OVER-COLLAPSE: always treat the value as small (is_small = True).
# A huge magnitude (the F2P `1` + `0`*300 at dp=3 -> must stay `1.000e+300`) is
# wrongly collapsed to `0.000`. Rejected by P1 (not below_cutoff but Result is
# not None). p/shifted/pow10 become dead but still type-check.
_RIVAL_OVERCOLLAPSE = _swap(
    _BASE, _IS_SMALL_BLOCK, "    is_small = True  # type: bool",
)

# (prepatch-faithful) UNDER-COLLAPSE: never treat the value as small
# (is_small stays False), so the routine always returns None. This is exactly
# model_prepatch.py's behaviour (the documented G-DIFF delta): a below-window
# value falls through to the ordinary path (which pre-patch rendered in
# exponential form). Rejected by P2 (below_cutoff but Result is None). The
# render code below is unreachable (path condition infeasible) so it verifies
# vacuously — the violation is solely the missing collapse.
_RIVAL_NEVERCOLLAPSE = _swap(
    _BASE, _IS_SMALL_BLOCK, "    is_small = False  # type: bool",
)

# (3c) PARTIAL-DOMAIN on the dp==0 rendering: emit `'0.'` (a stray trailing
# separator, [48,46]) instead of `'0'` ([48]). All dp>=1 renderings are correct;
# only the dp==0 collapse is wrong. The dp==0 render-pin assert is dropped so the
# rejection is forced by P4. Rejected because
# opt_seq([48,46]) == PSeq(48,46) != PSeq(48) == zero_render(0).
_RIVAL_DP0_SEP = _swap(
    _BASE, _DP0_BLOCK,
    """    if decimal_pos == 0:
        result = [48, 46]  # type: List[int]
        return result""",
)

# (3d) PARTIAL-DOMAIN on the dp>=1 rendering: an EXTRA leading zero — emit
# `'00.' + zeros` ([48,48,46]+frac) instead of `'0.' + zeros`. The smallness
# decision and dp==0 path are correct; only the dp>=1 leading digit is doubled.
# The final render-pin asserts are dropped so P4 forces the rejection
# (opt_seq has a spurious extra 48 at the front; != zero_render).
_RIVAL_EXTRA_ZERO = _swap(
    _BASE, _ASSEMBLE_BLOCK,
    """    result = [48, 48, 46] + frac
    return result""",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-grounded-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_GROUNDED,
     "rationale": "the cheapest CORRECT impl of the smallness decision uses the GROUNDED "
                  "@Pure oracle directly (is_small = below_cutoff(...)); it must verify "
                  "(else SPEC-TOO-STRONG, over-fit to the inline branch form). Also the "
                  "echo-class positive control: below_cutoff is grounded in the args so "
                  "there is no WRONG value it could echo — using it simply re-derives the "
                  "gold decision."},
    {"id": "pos-control-reorder-decision", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "a structurally-different but CORRECT decision (two separate `if`s, "
                  "nonzero-small then coeff==0, instead of if/elif) must verify. The "
                  "guarding assert and the whole render path are kept verbatim, so all gold "
                  "proof obligations hold; if it fails => SPEC-TOO-STRONG (over-fit to one "
                  "branch structure)."},
    {"id": "admiss-f2p-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the flipped F2P input 1.234e-300 @ dp=3 "
                  "(coeff=1234, exponent=-303, decimal_pos=3) must establish the "
                  "precondition coeff>=0 and decimal_pos>=0; if not => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-non-strict-cutoff", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONSTRICT,
     "refinement": "collapses a magnitude EXACTLY equal to the cutoff (e.g. 1e-8 @ dp=8, "
                   "coeff=1 exponent=-8 shifted=0). A faithful real patch using non-strict "
                   "`abs(number) <= cutoff` would render 1e-8 @ dp=8 as '0.00000000' instead "
                   "of the expected '0.00000001' (the F2P/P2P decimal row + axiom_check's "
                   "documented strict edge '== cutoff: NOT below'), so it would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN / strict-edge. Rejection source: P1 "
                  "Implies(not below_cutoff, Result() is None) — below_cutoff(1,-8,8) is "
                  "False (shifted>=0) so the routine must return None, but the rival returns "
                  "a rendering. The guarding self-assert is dropped so P1 (the spec) forces "
                  "the rejection. If it verified => SPEC-TOO-WEAK (non-strict cutoff admitted)."},
    {"id": "rival-no-threshold-floor", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOFLOOR,
     "refinement": "drops the max(decimal_pos,1) floor, so at decimal_pos==0 the cutoff "
                   "becomes 10**-0 == 1 instead of the real Decimal('0.'+'1'.rjust(0,'0')) "
                   "== 0.1. A value like 0.5 @ dp=0 (coeff=5 exponent=-1) is wrongly "
                   "collapsed to '0'. A real patch computing cutoff as 10**-decimal_pos "
                   "(without the rjust quirk) would collapse every value in [0.1, 1) at "
                   "dp=0 and so FAIL the dp=0 P2P/F2P cases, NOT resolving.",
     "rationale": "PARTIAL-DOMAIN at dp==0. Rejection source: P1 — below_cutoff(5,-1,0) is "
                  "False (threshold_exp(0)=1, shifted=0>=0) so Result() must be None, but "
                  "the floorless rival (shifted=-1) renders. Self-assert dropped so P1 "
                  "forces it. If it verified => SPEC-TOO-WEAK (threshold floor unpinned)."},
    {"id": "rival-over-collapse", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVERCOLLAPSE,
     "refinement": "is_small := True unconditionally. The F2P huge value `1`+`0`*300 @ dp=3 "
                   "(which must render '1.000e+300') is wrongly collapsed to '0.000'. A real "
                   "patch that always replaced number with Decimal('0') under decimal_pos is "
                   "not None would fail that F2P row (and every non-tiny P2P), NOT resolving.",
     "rationale": "return-shape fork against the spec. Rejection source: P1 — for any "
                  "not-below input below_cutoff is False so Result() must be None, but the "
                  "rival always renders. If it verified => SPEC-TOO-WEAK (no smallness gate)."},
    {"id": "rival-never-collapse", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NEVERCOLLAPSE,
     "refinement": "is_small stays False so the routine always returns None — exactly "
                   "model_prepatch.py (the G-DIFF delta). The below-window 1.234e-300 @ dp=3 "
                   "falls through to the ordinary path that pre-patch rendered as the "
                   "exponential '1.234e-300' rather than '0.000' — precisely the bug, so the "
                   "F2P test_decimal_numbers row stays failing: it would NOT resolve.",
     "rationale": "the documented failing prepatch. Rejection source: P2 "
                  "Implies(below_cutoff, Result() is not None) — below_cutoff(1234,-303,3) "
                  "is True so a rendering is required, but the rival returns None. If it "
                  "verified => SPEC-TOO-WEAK (the collapse is not actually demanded)."},
    {"id": "rival-dp0-stray-separator", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DP0_SEP,
     "refinement": "emits '0.' ([48,46]) at decimal_pos==0 instead of '0' ([48]). The real "
                   "dp=0 rendering of Decimal('0') is '0' (the separator is joined only when "
                   "the fractional part is non-empty, axiom_check witness dp=0 -> '0'); a "
                   "patch producing '0.' would fail any dp=0 P2P/F2P case, NOT resolving.",
     "rationale": "PARTIAL-DOMAIN on the dp==0 rendering. Rejection source: P4 — "
                  "opt_seq([48,46]) == PSeq(48,46) != PSeq(48) == zero_render(0). The dp==0 "
                  "render-pin assert is dropped so P4 forces the rejection. If it verified "
                  "=> SPEC-TOO-WEAK (dp==0 separator unpinned)."},
    {"id": "rival-extra-leading-zero", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_ZERO,
     "refinement": "emits '00.'+zeros ([48,48,46]+frac) at decimal_pos>=1 instead of "
                   "'0.'+zeros. A real patch doubling the leading integer zero would render "
                   "e.g. 1e-199 @ dp=2 as '00.00' instead of '0.00', failing every collapse "
                   "F2P/P2P row, NOT resolving.",
     "rationale": "PARTIAL-DOMAIN on the dp>=1 rendering. Rejection source: P4 — "
                  "opt_seq([48,48,46]+frac) has a spurious leading 48 and != "
                  "zero_render(decimal_pos). The final render-pin asserts are dropped so P4 "
                  "forces the rejection. If it verified => SPEC-TOO-WEAK (leading digit "
                  "unpinned)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real stdlib `decimal` callee — the A-reference deep models)
# ===========================================================================
#
# No @ContractOnly axiom is consumed (meta.axioms == []). `below_cutoff` and
# `zero_render` are A-reference deep models validated == the real arithmetic by
# axiom_check.py / G-AX. These probes re-run that A-reference soundness against
# the Python stdlib `decimal` module (the exact module + cutoff expression the
# gold patch uses) and fuzz the strict edge / floor / boundaries to try to make
# the real callee disagree with the deep model. Stdlib only; no file reads.

# (A-reference 1) below_cutoff deep model == real abs(number) < cutoff, where
# cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0')) reproduced VERBATIM from
# the gold patch. Boundary witnesses + exact-threshold edge (strict) + heavy
# fuzz straddling the cutoff. Any disagreement => A-REFERENCE-UNSOUND.
_AX_BELOW_CUTOFF_SOUND = r'''
import decimal, random, sys
from decimal import Decimal
decimal.getcontext().prec = 400

def m_threshold_exp(dp):
    return dp if dp >= 1 else 1

def below_cutoff_model(coeff, exponent, dp):
    # the model.py cross-multiplied integer test
    assert coeff >= 0 and dp >= 0
    if coeff == 0:
        return True
    shifted = exponent + m_threshold_exp(dp)
    if shifted >= 0:
        return False
    return coeff < 10 ** (-shifted)

def coeff_exponent(number):
    _, digits, exponent = abs(number).as_tuple()
    coeff = 0
    for d in digits:
        coeff = coeff * 10 + d
    return coeff, exponent

def real_below(number, dp):
    cutoff = Decimal('0.' + '1'.rjust(dp, '0'))   # VERBATIM gold cutoff
    return abs(number) < cutoff

def check(number, dp):
    coeff, exponent = coeff_exponent(number)
    m = below_cutoff_model(coeff, exponent, dp)
    r = real_below(number, dp)
    if m != r:
        print("A-REFERENCE-UNSOUND below_cutoff on number=%s dp=%d: model=%r real=%r "
              "(coeff=%d exponent=%d)" % (number, dp, m, r, coeff, exponent))
        sys.exit(1)

# documented boundary + problem-statement witnesses + the F2P/P2P magnitudes
boundary = [
    ('1e-199', 2), ('1e-200', 2),                  # problem statement (the bug)
    ('1e-7', 8), ('1e-8', 8), ('1e-9', 8),         # the strict edge at 1e-8 == cutoff
    ('1e-10', 8), ('1e-11', 8), ('0.00000001', 8),  # == cutoff: NOT below
    ('0.' + '0' * 299 + '1234', 3),                 # 1.234e-300 -> below at dp=3 (F2P)
    ('1' + '0' * 300, 3),                           # huge -> not below (F2P)
    ('0.5', 0), ('0.1', 0), ('0.09', 0), ('0.10', 0),  # dp=0 floor: cutoff is 0.1
    ('0', 0), ('0', 5), ('0.0', 4),                 # exact zero magnitude
    ('1234.5678', 2), ('-1234.33', 1), ('-9e-50', 4),
]
for v, dp in boundary:
    check(Decimal(v), dp)

# exact-threshold edge across dp 0..30: the cutoff value itself (strict: NOT
# below), a tenth of it (below), ten times it (not below), and 0.
for dp in range(0, 30):
    e = dp if dp >= 1 else 1
    at = Decimal(1).scaleb(-e)
    check(at, dp); check(at.scaleb(-1), dp); check(at.scaleb(1), dp)
    check(-at, dp); check(Decimal(0), dp)

# heavy randomized fuzz straddling the cutoff over a wide magnitude window
rng = random.Random(11206)
for _ in range(200000):
    dp = rng.randint(0, 20)
    coeff = rng.randint(1, 9999)
    exp = rng.randint(-(dp + 8), 4)
    sign = rng.choice(['', '-'])
    check(Decimal('%s%dE%d' % (sign, coeff, exp)), dp)

print("A-reference OK: below_cutoff == real abs(number) < "
      "Decimal('0.'+'1'.rjust(dp,'0')) on boundary + exact-edge (dp 0..29) + 200000 fuzz")
sys.exit(0)
'''

# (A-reference 2) zero_render deep model == real fixed-point rendering of
# Decimal('0') at decimal_pos places with the '.' separator, reproduced verbatim
# from the post-patch numberformat.format render tail. dp 0..40. Any mismatch
# => A-REFERENCE-UNSOUND (the rendering deep model is wrong).
_AX_ZERO_RENDER_SOUND = r'''
import sys
from decimal import Decimal

def zero_render_model(dp):
    if dp == 0:
        return [ord('0')]
    return [ord('0'), ord('.')] + [ord('0')] * dp

def real_zero_render(dp):
    number = Decimal('0')
    str_number = '{:f}'.format(number)          # '0'
    assert str_number == '0'
    if '.' in str_number:
        int_part, dec_part = str_number.split('.')
    else:
        int_part, dec_part = str_number, ''
    if dp is not None:
        dec_part = dec_part + ('0' * (dp - len(dec_part)))
    dec_part = dec_part and '.' + dec_part        # decimal_sep = '.'
    return [ord(ch) for ch in (int_part + dec_part)]

bad = []
for dp in range(0, 41):
    m = zero_render_model(dp)
    r = real_zero_render(dp)
    if m != r:
        bad.append((dp, m, r))
if bad:
    print("A-REFERENCE-UNSOUND zero_render:", bad[:8]); sys.exit(1)
print("A-reference OK: zero_render == real Decimal('0') fixed-point rendering "
      "('.' sep) for decimal_pos 0..40")
sys.exit(0)
'''

# (containment) The model can pass below_cutoff exactly the inputs in its
# Requires domain: coeff >= 0, decimal_pos >= 0, exponent unconstrained. The real
# callee (abs(number) < cutoff over Decimal) is total over that whole domain — a
# Decimal of every (coeff>=0, exponent, dp>=0) decomposition is constructible and
# the comparison is defined, so every caller-reachable input lies in the real
# callee's domain. This probe confirms that: it builds the Decimal magnitude
# coeff*10**exponent for a wide grid of reachable (coeff, exponent, dp) and
# asserts the real comparison is well-defined AND agrees with the deep model on
# every one (containment + soundness tie-in). A reachable input the real callee
# could not evaluate, or disagrees on, => AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import decimal, sys
from decimal import Decimal
decimal.getcontext().prec = 400

def m_threshold_exp(dp):
    return dp if dp >= 1 else 1

def below_cutoff_model(coeff, exponent, dp):
    if coeff == 0:
        return True
    shifted = exponent + m_threshold_exp(dp)
    if shifted >= 0:
        return False
    return coeff < 10 ** (-shifted)

def real_below_from_decomp(coeff, exponent, dp):
    # reconstruct the Decimal magnitude the caller's (coeff, exponent) denotes
    number = Decimal(coeff).scaleb(exponent)
    cutoff = Decimal('0.' + '1'.rjust(dp, '0'))
    return abs(number) < cutoff

bad = []
for dp in (0, 1, 2, 3, 8, 20):
    for coeff in (0, 1, 5, 9, 10, 99, 1234, 9999):
        for exponent in range(-(dp + 10), 6):     # spans below/at/above the cutoff
            m = below_cutoff_model(coeff, exponent, dp)
            r = real_below_from_decomp(coeff, exponent, dp)
            if m != r:
                bad.append((coeff, exponent, dp, m, r))
if bad:
    print("AXIOM-TOO-WEAK-FOR-CALLER / unsound on reachable decomposition:", bad[:8])
    sys.exit(1)
print("containment OK: every reachable (coeff>=0, exponent, decimal_pos>=0) is in the "
      "real callee's domain and below_cutoff agrees with abs(number)<cutoff on the grid")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-below-cutoff-sound", "axiom": "below_cutoff", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_BELOW_CUTOFF_SOUND,
     "rationale": "the A-reference deep model below_cutoff must equal the REAL "
                  "abs(number) < Decimal('0.'+'1'.rjust(dp,'0')) (gold cutoff verbatim) over "
                  "the documented boundary + the strict exact-cutoff edge + 200000 fuzz; any "
                  "disagreement => A-REFERENCE-UNSOUND (the smallness deep model is wrong)."},
    {"id": "ax-zero-render-sound", "axiom": "zero_render", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_ZERO_RENDER_SOUND,
     "rationale": "the A-reference deep model zero_render must equal the REAL fixed-point "
                  "rendering of Decimal('0') at decimal_pos places with the '.' separator "
                  "(render tail reproduced verbatim) for dp 0..40; any mismatch => "
                  "A-REFERENCE-UNSOUND (the zero rendering deep model is wrong)."},
    {"id": "ax-below-cutoff-containment", "axiom": "below_cutoff", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every input the model can pass below_cutoff (its Requires domain "
                  "coeff>=0, decimal_pos>=0, any exponent) lies in the real callee's domain "
                  "(the Decimal comparison is total there) and the deep model agrees on the "
                  "reachable grid; a reachable input the real callee could not evaluate or "
                  "disagrees on => AXIOM-TOO-WEAK-FOR-CALLER."},
]
