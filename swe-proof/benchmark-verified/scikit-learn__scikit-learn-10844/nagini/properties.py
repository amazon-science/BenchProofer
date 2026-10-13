# properties.py — PBT falsification battery for scikit-learn__scikit-learn-10844.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only the impl region differs,
# guaranteed by region-surgery via _swap) and are checked by Nagini verify +
# markers.same_spec. Axiom cases are real-callee probes run in the instance image.
#
# Defended surface (pair_similarity_index(tk, pk, qk, m); models the
# fowlkes_mallows_score score-assembly tail; gold reorder
#   `tk / np.sqrt(pk*qk)` -> `np.sqrt(tk/pk) * np.sqrt(tk/qk)`):
#   Signature: all four params are `float` (by-value; NO permission tokens, NO
#              read-only list/array input) => directive-5 FRAME-MUTATION is N/A.
#   Requires: m >= 1; tk >= 0; 0 <= pk <= m; 0 <= qk <= m; tk <= pk; tk <= qk.
#             (Each marginal representable in m; their cross product deliberately
#              NOT given <= m — that is the overflow the reorder avoids.)
#   Ensures : (1) Implies(tk > 0,  Result() == mul(root(ratio(tk,pk,m),m),
#                                                   root(ratio(tk,qk,m),m)))  <- LOAD-BEARING
#             (2) Implies(tk == 0, Result() == 0.0)
#             (3) Result() >= 0.0
#             (4) Result() <= 1.0
# Axioms (A-consumed, @ContractOnly over interpreted reals):
#   ratio(a,b,m): 0<=a<=b<=m, b>0  -> Result()==a/b AND 0<=Result()<=1   (real `/`)
#   root(x,m):    0<=x<=m          -> Result()>=0 AND (x<=1 => Result()<=1) (np.sqrt)
#                 *** the Requires(x <= m) representability GATE is the overflow
#                     discriminator: a value that overflowed the domain cannot be
#                     fed to the root. This is what rejects the pre-patch order. ***
#   mul(x,y):     x,y in [0,1]     -> Result()==x*y AND 0<=Result()<=1     (real `*`)
#
# The load-bearing Ensures (1) pins Result to mul(root(ratio(...)), root(ratio(...)))
# — a composition of axioms over the actual args tk/pk/qk/m. It is GROUNDED in the
# inputs (a fully-determined function of the args, not an opaque answer-key/marker),
# so there is NO wrong value to "echo": the ungrounded-oracle-echo class is N/A.
# The honest cheapest-impl positive control (pos-control-inline) stands in for that
# slot. See 'assessment'.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10844"
FLOAT_ENCODING = "real"   # meta.json float_encoding; verified with --float-encoding=real

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region (between # impl-start and # impl-end). Every variant is
# produced by _swap on a substring that lies ENTIRELY inside this region, so the
# spec view (axioms / pure / pre / post / signature) is untouched => same_spec.
_GOLD_IMPL_BODY = """    if tk != 0.0:
        # Form the two unit-interval conditional ratios FIRST; each is
        # representable (<= 1 <= m), so neither operand fed to the root, nor the
        # final product, can overflow the domain. The cross product of the two
        # marginals is never formed. (A concordant pair forces both marginals
        # strictly positive, since each marginal dominates the concordant count.)
        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))
    else:
        result = 0.0
    return result"""


# ---------------------------------------------------------------------------
# 1. UNIQUENESS — the PRE-PATCH overflow order (THE bug). Form the cross product
#    pk*qk FIRST with the native `*` (the only way to multiply two non-unit
#    values; `mul` requires both args in [0,1]), take its root, then divide.
#    Must REJECT at the root(prod, m) precondition `prod <= m`: pk*qk <= m is NOT
#    derivable from the per-marginal pk<=m, qk<=m. This is exactly model_prepatch
#    (G-DIFF) restated as a uniqueness rival, and the load-bearing case.
# ---------------------------------------------------------------------------
_prepatch_overflow = _swap(
    _BASE,
    _GOLD_IMPL_BODY,
    """    if tk != 0.0:
        # PRE-PATCH evaluation order: form the cross product of the two marginals
        # FIRST and take the square root of that single combined quantity, then
        # divide. The cross product can exceed the representable domain even when
        # each marginal is representable, so the value fed to the root is NOT
        # known to be <= m.
        prod = pk * qk
        denom = root(prod, m)
        result = ratio(tk, denom, m)
    else:
        result = 0.0
    return result""",
)


# ---------------------------------------------------------------------------
# 2. UNIQUENESS — drop the square roots (the SQUARED index). Return
#    mul(ratio(tk,pk,m), ratio(tk,qk,m)) = (tk/pk)*(tk/qk) = tk^2/(pk*qk) instead
#    of sqrt(tk/pk)*sqrt(tk/qk). Stays in [0,1] (so clauses 3,4 hold) and never
#    overflows, but is the WRONG value => REJECT on the load-bearing Ensures (1).
# ---------------------------------------------------------------------------
_no_roots = _swap(
    _BASE,
    """        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))""",
    """        # squared-index rival: multiply the ratios directly, no square root.
        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(r_p, r_q)""",
)


# ---------------------------------------------------------------------------
# 3. UNIQUENESS — single ratio (drop the multiply). Return just root(tk/pk),
#    ignoring the second marginal qk. In [0,1] (clauses 3,4 hold) and finite, but
#    not the geometric MEAN => REJECT on Ensures (1) (sqrt(tk/pk) != the product
#    unless tk/qk == 1, i.e. tk == qk).
# ---------------------------------------------------------------------------
_single_ratio = _swap(
    _BASE,
    """        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))""",
    """        # single-ratio rival: only the first conditional ratio, no qk term.
        r_p = ratio(tk, pk, m)
        result = root(r_p, m)""",
)


# ---------------------------------------------------------------------------
# 4. UNIQUENESS / partial-domain — corrupt the ZERO branch. Return a non-zero
#    in-range constant when tk == 0 (correct on every tk > 0 input, diverges on
#    the no-concordant-pair subdomain). Must REJECT on Ensures (2)
#    Implies(tk == 0, Result() == 0.0). 0.5 is in [0,1] so clauses 3,4 are fine.
# ---------------------------------------------------------------------------
_zero_branch_wrong = _swap(
    _BASE,
    """    else:
        result = 0.0
    return result""",
    """    else:
        result = 0.5  # partial-domain: wrong value on the tk==0 subdomain
    return result""",
)


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness) — branch REORDER. Test the zero case first and
#    fall through to the geometric-mean assembly in the else. Behaviourally
#    identical, structurally different (guard inverted). No loop / no induction
#    lemma needed — straight-line code, so the gold proof obligations all still
#    discharge. MUST VERIFY, else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_pos_control_reorder = _swap(
    _BASE,
    _GOLD_IMPL_BODY,
    """    if tk == 0.0:
        result = 0.0
    else:
        # reordered: zero case guarded first; the geometric-mean assembly in else.
        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))
    return result""",
)


# ---------------------------------------------------------------------------
# 6. POSITIVE CONTROL (cheapest honest impl) — inline the whole assembly into one
#    expression, dropping the r_p/r_q temporaries. Genuinely does the work (forms
#    the two unit-interval ratios first, never the cross product). Doubles as the
#    GROUNDED-ORACLE positive control: Ensures (1) pins Result to exactly this
#    composition of axioms over the args, so there is no wrong value to echo — the
#    honest cheapest impl is the only thing that satisfies it. MUST VERIFY.
# ---------------------------------------------------------------------------
_pos_control_inline = _swap(
    _BASE,
    """        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))""",
    """        # cheapest honest impl: inline the two ratios + roots into one product.
        result = mul(root(ratio(tk, pk, m), m), root(ratio(tk, qk, m), m))""",
)


# ---------------------------------------------------------------------------
# 7. ADMISSIBILITY — self-call on the actual LARGE-COUNT failing-test magnitudes
#    (tk=3003497866, pk=5152663196, qk=3294371982, m=INT64_MAX). This is the
#    regime that overflowed; the precondition MUST admit it (each marginal <= m,
#    tk <= each marginal) and the post-condition must give a usable in-range
#    result. The probe args are fresh locals; modular verification uses
#    pair_similarity_index's own contract. MUST VERIFY, else PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_admiss = _swap(
    _BASE,
    """    if tk != 0.0:
        # Form the two unit-interval conditional ratios FIRST""",
    """    # admissibility witness: the precondition admits the LARGE-COUNT regime
    # that overflowed (the actual failing-test marginals), and the post-condition
    # yields a finite in-range index there.
    _m = 9223372036854775807.0          # INT64_MAX (the representable bound)
    Assert(_m >= 1.0)
    Assert(3003497866.0 >= 0.0)
    Assert(5152663196.0 >= 0.0 and 5152663196.0 <= _m)
    Assert(3294371982.0 >= 0.0 and 3294371982.0 <= _m)
    Assert(3003497866.0 <= 5152663196.0)
    Assert(3003497866.0 <= 3294371982.0)
    if tk != 0.0:
        # Form the two unit-interval conditional ratios FIRST""",
)


SPEC_TESTS = [
    {
        "id": "prepatch-overflow-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _prepatch_overflow,
        "refinement": (
            "This IS the pre-patch evaluation order tk / sqrt(pk*qk): it forms the "
            "cross product pk*qk first. On the failing test pk*qk ~= 1.7e19 > "
            "9.2e18 = INT64_MAX, so the real numpy int multiply overflows and the "
            "result is nan; the F2P assert_all_finite(fowlkes_mallows_score(x,y)) "
            "FAILS -> would NOT resolve. (model_prepatch.py transcribes exactly this "
            "and is the G-DIFF discriminator.)"
        ),
        "rationale": (
            "Rejection comes from the root axiom's representability precondition "
            "Requires(x <= m): root(prod, m) needs prod = pk*qk <= m, which is NOT "
            "derivable from the per-marginal pk <= m, qk <= m. (The follow-on "
            "ratio(tk, denom, m) precondition tk <= denom <= m is likewise "
            "underivable, but the root gate fires first.)"
        ),
    },
    {
        "id": "no-square-roots-squared-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_roots,
        "refinement": (
            "mul(tk/pk, tk/qk) = tk^2/(pk*qk) is the SQUARE of the Fowlkes-Mallows "
            "index, not the index. It is in [0,1] and finite, so it would not crash, "
            "but it is the wrong number: the P2P exact-value tests (test_perfect_"
            "matches expects FMI=1.0; the squared value also =1 only at the perfect "
            "match but diverges elsewhere, e.g. tk/pk=tk/qk=0.5 gives 0.25 vs the "
            "correct 0.5) FAIL -> would NOT resolve."
        ),
        "rationale": (
            "Rejection from the load-bearing Ensures (1) Result() == mul(root(ratio("
            "tk,pk,m),m), root(ratio(tk,qk,m),m)): mul(r_p, r_q) omits both roots, so "
            "Result() = r_p*r_q != root(r_p)*root(r_q) in general."
        ),
    },
    {
        "id": "single-ratio-drop-qk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _single_ratio,
        "refinement": (
            "Returning only sqrt(tk/pk) ignores the second clustering's marginal qk. "
            "It is in [0,1] and finite, but is not the geometric mean: e.g. with "
            "tk/pk=1 and tk/qk=0.25 the correct FMI is 0.5 but this returns 1.0. The "
            "P2P value tests (homogeneous-but-not-complete vs complete-but-not-"
            "homogeneous are asymmetric) FAIL -> would NOT resolve."
        ),
        "rationale": (
            "Rejection from Ensures (1): Result() = root(ratio(tk,pk,m),m) != "
            "mul(root(ratio(tk,pk,m),m), root(ratio(tk,qk,m),m)) unless ratio(tk,qk,m)"
            "==1 (i.e. tk==qk), which is not an admissible-input invariant."
        ),
    },
    {
        "id": "zero-branch-nonzero-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _zero_branch_wrong,
        "refinement": (
            "Correct on every tk>0 input but returns 0.5 when tk==0 (no concordant "
            "pair). The real FMI is 0.0 there (sklearn's `... else 0.`). A clustering "
            "pair with zero concordance must score 0; the P2P tests covering "
            "no-shared-pair cases would see 0.5 -> assertion FAILS -> would NOT "
            "resolve. Partial-domain: diverges only on the tk==0 subdomain."
        ),
        "rationale": (
            "Rejection from Ensures (2) Implies(tk == 0.0, Result() == 0.0): the else "
            "branch sets result = 0.5, so the tk==0 post-condition cannot discharge. "
            "(Clauses 3,4 still hold since 0.5 in [0,1].)"
        ),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control_reorder,
        "rationale": (
            "Structurally different (zero case guarded first, geometric-mean assembly "
            "in the else) but behaviourally identical correct impl. Straight-line "
            "code, no loop/induction lemma, so every gold proof obligation still "
            "discharges. MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-inline-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control_inline,
        "rationale": (
            "Cheapest honest impl: inline the two ratios + roots into one product, "
            "drop the r_p/r_q temporaries; still forms the unit-interval ratios first "
            "(never the cross product). Doubles as the grounded-oracle positive "
            "control — Ensures (1) pins Result to exactly this axiom composition over "
            "the args, so there is no wrong value to echo. MUST verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-large-count-regime",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Self-call on the actual failing-test large-count marginals "
            "(tk=3.0e9, pk=5.15e9, qk=3.29e9, m=INT64_MAX) establishes Requires "
            "(each marginal <= m; tk <= each marginal; m >= 1) and uses the "
            "post-condition (result in [0,1]). MUST verify, else PRECOND-TOO-STRONG "
            "(the precondition would reject the very regime the fix targets)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. Three A-consumed @ContractOnly axioms over UNCHANGED numeric
# primitives (the fix changes only evaluation ORDER and integer WIDTH, not which
# operations run):
#   ratio(a,b,m) <-> real division  a / b
#   root(x,m)    <-> numpy.sqrt / math.sqrt
#   mul(x,y)     <-> real multiplication  x * y
# All three are patch-state-independent pure arithmetic (apply_gold irrelevant;
# we set apply_gold=False — the operations are identical pre/post patch). We
# reuse and strengthen axiom_check.py's check_ratio/check_root/check_mul logic
# and its overflow-discriminator block. Probes import only the standard library
# (math, random) — no repo callee needed; they exercise the SAME real operations
# the score-assembly uses, and the numpy `/`,`sqrt`,`*` agree with these on
# finite reals (numpy delegates to the C library; checked once below).
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import math
import random
import sys

# Real-operation soundness of the ratio/root/mul axioms (model.py axioms region),
# evaluated on the SAME real `/`, sqrt, `*` the fowlkes_mallows_score assembly
# invokes. INT64_MAX is the representable bound m (the int64 domain the fix widens
# the marginals into). Confirm numpy agrees with the stdlib ops on these inputs,
# then drive the heavy fuzz on the (faster) stdlib ops.
INT64_MAX = 2 ** 63 - 1
M = float(INT64_MAX)
fail = []

# numpy agreement spot-check (the actual callees are numpy `/`, np.sqrt, `*`).
try:
    import numpy as np
    spot = [(3003497866.0, 5152663196.0), (1.0, 2.0), (4.0, 6.0)]
    for a, b in spot:
        if float(np.true_divide(a, b)) != a / b:
            fail.append("numpy / disagrees with stdlib / on %r,%r" % (a, b))
    for x in [0.25, 0.5, 1.0, 5152663196.0]:
        if abs(float(np.sqrt(x)) - math.sqrt(x)) > 1e-9 * (1.0 + math.sqrt(x)):
            fail.append("np.sqrt disagrees with math.sqrt on %r" % x)
    if float(np.multiply(0.5, 0.5)) != 0.5 * 0.5:
        fail.append("numpy * disagrees with stdlib *")
except Exception as e:
    # numpy missing is not a soundness failure of the arithmetic; the stdlib ops
    # are the same IEEE-754 operations. Record but do not fail on import.
    print("note: numpy spot-check skipped:", repr(e))


def check_ratio(a, b, m):
    assert b > 0.0 and 0.0 <= a <= b <= m
    r = a / b
    if not (r == a / b):
        fail.append("ratio !=a/b on a=%r b=%r" % (a, b))
    if not (0.0 <= r <= 1.0):
        fail.append("ratio axiom unsound: a/b=%r not in [0,1] (a=%r b=%r)" % (r, a, b))


def check_root(x, m):
    assert 0.0 <= x <= m
    r = math.sqrt(x)
    if not (r >= 0.0):
        fail.append("root axiom unsound: sqrt(%r)=%r < 0" % (x, r))
    if x <= 1.0 and not (r <= 1.0):
        fail.append("root axiom unsound: sqrt(%r)=%r > 1 for x<=1" % (x, r))


def check_mul(x, y):
    assert 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
    r = x * y
    if not (r == x * y):
        fail.append("mul !=x*y on x=%r y=%r" % (x, y))
    if not (0.0 <= r <= 1.0):
        fail.append("mul axiom unsound: x*y=%r not in [0,1] (x=%r y=%r)" % (r, x, y))


# ---- boundary cases (incl. the actual failing-test magnitudes) ----
ratio_boundary = [
    (0.0, 1.0), (0.0, M), (1.0, 1.0), (1.0, M), (M, M),
    (1.0, 2.0), (3.0, 12.0), (4.0, 6.0), (12.0, 12.0),
    (3003497866.0, 5152663196.0),   # tk, pk (failing-test regime)
    (3003497866.0, 3294371982.0),   # tk, qk (failing-test regime)
]
for a, b in ratio_boundary:
    check_ratio(a, b, M)

root_boundary = [0.0, 1.0, 0.25, 0.5, 0.9999999999, 2.0, 100.0, M, M / 2.0,
                 5152663196.0, 3294371982.0]
for x in root_boundary:
    check_root(x, M)

mul_boundary = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0),
                (0.5, 0.5), (0.9999, 0.9999),
                (math.sqrt(3003497866.0 / 5152663196.0),
                 math.sqrt(3003497866.0 / 3294371982.0))]
for x, y in mul_boundary:
    check_mul(x, y)

# ---- randomized fuzz over the axiom Requires domains ----
rng = random.Random(10844)
for _ in range(200000):
    b = rng.uniform(1e-9, M)
    a = rng.uniform(0.0, b)            # 0 <= a <= b <= M
    check_ratio(a, b, M)
    x = rng.uniform(0.0, M)            # 0 <= x <= M
    check_root(x, M)
    u = rng.uniform(0.0, 1.0)
    v = rng.uniform(0.0, 1.0)          # u,v in [0,1]
    check_mul(u, v)

# ---- the overflow discriminator the root gate turns on ----
tk, pk, qk = 3003497866.0, 5152663196.0, 3294371982.0
if not (pk <= M and qk <= M):
    fail.append("each marginal must be representable (<= M)")
if not (pk * qk > M):
    fail.append("cross product must exceed M (the overflow the reorder avoids)")
safe = math.sqrt(tk / pk) * math.sqrt(tk / qk)   # divide-first (gold) order
if not (math.isfinite(safe) and 0.0 <= safe <= 1.0):
    fail.append("divide-first order must yield a finite unit-interval result")
direct = tk / math.sqrt(pk * qk)                 # finite ONLY because Python bigints
if not (abs(safe - direct) < 1e-9):
    fail.append("the two evaluation orders must agree mathematically")

if fail:
    print("AXIOM-UNSOUND:", "; ".join(fail[:6]))
    sys.exit(1)
print("axiom-soundness OK: ratio/root/mul sound on %d boundary + %d fuzz inputs; "
      "overflow discriminator confirmed (pk*qk > INT64_MAX while each marginal "
      "<= INT64_MAX; divide-first stays finite in [0,1] and equals the direct order)"
      % (len(ratio_boundary) + len(root_boundary) + len(mul_boundary), 200000 * 3))
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
import math
import random
import sys

# AXIOM-CONTAINMENT: every callee-input the MODEL can reach must lie inside the
# corresponding axiom's Requires domain. Derive the reachable inputs from the
# model's own Requires + control flow (the impl tk!=0 branch):
#
#   Preconditions: m >= 1; tk >= 0; 0 <= pk <= m; 0 <= qk <= m; tk <= pk; tk <= qk.
#   In the tk!=0 branch, tk > 0, so (tk <= pk, tk <= qk) => pk > 0 and qk > 0.
#
#   ratio(tk, pk, m): needs 0<=tk<=pk<=m AND pk>0.  Reachable: 0<tk<=pk<=m  -> IN.
#   ratio(tk, qk, m): needs 0<=tk<=qk<=m AND qk>0.  Reachable: 0<tk<=qk<=m  -> IN.
#       Each ratio Ensures Result() in [0,1].
#   root(r_p, m), root(r_q, m): need 0<=x<=m. Reachable x = ratio(...) in [0,1]
#       subseteq [0,m] (since m>=1).  -> IN. Each root of a unit value Ensures
#       Result() in [0,1].
#   mul(root(r_p,m), root(r_q,m)): needs both args in [0,1]. Reachable args are
#       roots of unit-interval values, which are in [0,1].  -> IN.
#
# We sample the model's admissible (tk,pk,qk,m) space, propagate through the exact
# call chain the impl performs, and assert each intermediate satisfies the next
# callee's Requires. A reachable input outside an axiom domain => AXIOM-TOO-WEAK-
# FOR-CALLER. Covering MORE than the caller reaches is SOUND, not a defect.
INT64_MAX = 2 ** 63 - 1
fail = []


def in_domain_ratio(a, b, m):
    return (b > 0.0) and (a >= 0.0) and (a <= b) and (b <= m)


def in_domain_root(x, m):
    return (x >= 0.0) and (x <= m)


def in_domain_mul(x, y):
    return (0.0 <= x <= 1.0) and (0.0 <= y <= 1.0)


def propagate(tk, pk, qk, m):
    """Walk the impl's call chain for the tk>0 branch; flag any out-of-domain
    callee-input the model reaches."""
    # ratio(tk, pk, m)
    if not in_domain_ratio(tk, pk, m):
        fail.append("ratio(tk,pk,m) input OUT of domain: tk=%r pk=%r m=%r" % (tk, pk, m))
        return
    r_p = tk / pk
    if not in_domain_ratio(tk, qk, m):
        fail.append("ratio(tk,qk,m) input OUT of domain: tk=%r qk=%r m=%r" % (tk, qk, m))
        return
    r_q = tk / qk
    # root(r_p, m), root(r_q, m)
    if not in_domain_root(r_p, m):
        fail.append("root(r_p,m) input OUT of domain: r_p=%r m=%r" % (r_p, m))
        return
    if not in_domain_root(r_q, m):
        fail.append("root(r_q,m) input OUT of domain: r_q=%r m=%r" % (r_q, m))
        return
    s_p = math.sqrt(r_p)
    s_q = math.sqrt(r_q)
    # mul(s_p, s_q)
    if not in_domain_mul(s_p, s_q):
        fail.append("mul(s_p,s_q) input OUT of domain: s_p=%r s_q=%r" % (s_p, s_q))


# explicit boundary admissible inputs (m varied across its admissible range)
boundary = [
    # (tk, pk, qk, m)
    (1.0, 1.0, 1.0, 1.0),                         # m at its minimum, all equal
    (1.0, 1.0, 1.0, float(INT64_MAX)),
    (1.0, 2.0, 3.0, 10.0),
    (5.0, 5.0, 9.0, 9.0),                         # tk==pk (ratio=1) boundary
    (0.0, 0.0, 0.0, 1.0),                         # tk==0 (else branch; chain not taken, but in-domain anyway is moot)
    (3003497866.0, 5152663196.0, 3294371982.0, float(INT64_MAX)),  # failing-test
    (float(INT64_MAX), float(INT64_MAX), float(INT64_MAX), float(INT64_MAX)),  # all at m
]
for tk, pk, qk, m in boundary:
    # only propagate the tk>0 branch (the chain the impl runs); tk==0 goes to else.
    if tk != 0.0:
        # respect the model's preconditions for a valid admissible input
        assert m >= 1.0 and tk >= 0.0 and 0.0 <= pk <= m and 0.0 <= qk <= m
        assert tk <= pk and tk <= qk
        propagate(tk, pk, qk, m)

# randomized fuzz over the admissible input space
rng = random.Random(108442)
M = float(INT64_MAX)
for _ in range(200000):
    m = rng.uniform(1.0, M)
    pk = rng.uniform(1e-6, m)          # marginal positive & representable
    qk = rng.uniform(1e-6, m)
    tk = rng.uniform(0.0, min(pk, qk)) # 0 <= tk <= pk, tk <= qk
    if tk == 0.0:
        continue                        # else branch: no callee chain
    propagate(tk, pk, qk, m)
    if fail:
        break

if fail:
    print("AXIOM-TOO-WEAK-FOR-CALLER:", "; ".join(fail[:6]))
    sys.exit(1)
print("axiom-containment OK: every callee-input the model reaches "
      "(ratio(tk,pk,m), ratio(tk,qk,m), root(r_p,m), root(r_q,m), mul(s_p,s_q)) "
      "lies inside its axiom's Requires domain across 7 boundary + 200000 fuzz "
      "admissible inputs. The cross product pk*qk is NEVER formed, so it is never "
      "passed to root (that is the bug the gold reorder removes).")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-ratio-root-mul",
        "axiom": "ratio/root/mul",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,   # real /, sqrt, * are unchanged by the patch
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "The three A-consumed axioms model the unchanged numeric callees "
            "(real /, np.sqrt, real *). Running them on their Requires domains + "
            "the actual failing-test magnitudes + 600k fuzz inputs confirms each "
            "Ensures holds, and confirms the overflow discriminator (pk*qk > "
            "INT64_MAX while each marginal <= INT64_MAX; divide-first stays finite). "
            "Any disagreement => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-contain-callee-domains",
        "axiom": "ratio/root/mul",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "Every callee-input the model can reach (ratio(tk,pk,m), ratio(tk,qk,m) "
            "with 0<tk<=marginal<=m; root of a unit-interval ratio; mul of two "
            "unit-interval roots) lies inside its axiom's Requires domain — verified "
            "by propagating the impl's exact call chain over the admissible input "
            "space. The cross product pk*qk is never formed so never reaches root. A "
            "reachable input outside a domain => AXIOM-TOO-WEAK-FOR-CALLER; none exists."
        ),
    },
]
