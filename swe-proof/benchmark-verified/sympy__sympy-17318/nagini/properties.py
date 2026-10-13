# properties.py — PBT manifest for sympy__sympy-17318.
#
# NOT a Nagini module; an adversarial falsification battery the runner
# (swebench_nagini.pbt) parses. Each SPEC_TESTS case is a full model.py variant
# built by region-surgery: ONLY the text inside the single # impl-start /
# # impl-end block is swapped, so the frozen spec (axioms + pure + pre/post
# conditions + Exsures) is provably untouched (markers.same_spec == True).
#
# Defended surface of match_additive(codes) (read fully before reading cases):
#   * codes is READ-ONLY: Requires/Ensures Acc(list_pred(codes), 1/2). A mutating
#     impl must fail for INSUFFICIENT PERMISSION (frame-mutation, MANDATORY).
#   * The fast-path postcondition is GROUNDED in the modeled computation:
#       Implies(all_fast_facet and num_surds>=1,
#               Result() == split_by_radicand_gcd(ToSeq(codes), num_surds(...)))
#     split_by_radicand_gcd is @Pure @ContractOnly with Ensures(Result() != 1)
#     and its EXACT value deliberately UNPINNED (opaque). So there is no constant
#     a wrong impl can echo: the clause is dischargeable ONLY by actually calling
#     the helper. (This is the 2nd-pass fix of the re-audit's residual hole where
#     a prior Result()==2 could be faked with `return 2` — meta.json G-EQ.) The
#     ungrounded-oracle ECHO class therefore has no WRONG-yet-verifying echo; we
#     still include the literal-echo as a REJECT case (it must reject) plus an
#     honest cheapest correct positive control.
#   * The depth path is pinned: Implies(not all_fast_facet, Result()==1).
#   * The empty match is pinned by Exsures(NoMatch, ... and not all_fast_facet
#     and not any_has_depth) — a raise/return-marker divergence is observable.
#
# Gold impl region (the unique anchor every variant swaps):
#     if all_fast_facet(ToSeq(codes)):
#         k = num_surds(ToSeq(codes))
#         return split_by_radicand_gcd(ToSeq(codes), k)
#     if not any_has_depth(ToSeq(codes)):
#         raise NoMatch()
#     return 1
from pathlib import Path

INSTANCE = "sympy__sympy-17318"
FLOAT_ENCODING = None  # meta.json float_encoding is null; carrier is PSeq[int]

_BASE = (Path(__file__).parent / "model.py").read_text()

# the exact gold impl block (between # impl-start / # impl-end); unique in _BASE.
_GOLD_IMPL = (
    "    if all_fast_facet(ToSeq(codes)):\n"
    "        k = num_surds(ToSeq(codes))\n"
    "        return split_by_radicand_gcd(ToSeq(codes), k)\n"
    "    if not any_has_depth(ToSeq(codes)):\n"
    "        raise NoMatch()\n"
    "    return 1\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: anchor not found: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body: str) -> str:
    """Build a full model.py variant by replacing ONLY the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl.
#    Inverts the conditional nesting: handles the non-fast path FIRST (the depth
#    branch), and the fast path in the trailing else. Keeps every gold proof
#    obligation it still needs: the fast path genuinely invokes the helper with
#    k == num_surds (so the grounded postcondition is discharged by the helper's
#    own opaque output, NOT a literal), the depth fallback returns 1, and the
#    empty match raises NoMatch on (not all_fast_facet and not any_has_depth).
#    No loop / fold-direction change (would need an f(a+b) lemma, AVOID #3); a
#    pure branch-reorder keeps the gold proof valid. MUST verify, else
#    SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = (
    "    if not all_fast_facet(ToSeq(codes)):\n"
    "        if any_has_depth(ToSeq(codes)):\n"
    "            return 1\n"
    "        raise NoMatch()\n"
    "    k = num_surds(ToSeq(codes))\n"
    "    return split_by_radicand_gcd(ToSeq(codes), k)\n"
)

# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY — the precondition must admit a normal F2P/P2P-shaped input
#    on BOTH branches. Keeps the gold impl and adds Asserts that the precondition
#    is consistent with reaching the fast path AND with reaching the fallback
#    (the guard and its negation are both establishable, the frame fact is
#    usable). If the Requires were contradictory / over-constrained on a normal
#    input, these would fail => PRECOND-TOO-STRONG. Asserts only restate facts
#    already implied by the contract, so a tight spec verifies.
# ---------------------------------------------------------------------------
_ADMISS = (
    "    # admissibility: the precondition admits inputs on both branches and the\n"
    "    # frame fact is usable (the guard is reachable, its negation is reachable).\n"
    "    Assert(Implies(all_fast_facet(ToSeq(codes)), num_surds(ToSeq(codes)) >= 1))\n"
    "    Assert(len(codes) >= 2)\n"
    "    if all_fast_facet(ToSeq(codes)):\n"
    "        k = num_surds(ToSeq(codes))\n"
    "        return split_by_radicand_gcd(ToSeq(codes), k)\n"
    "    if not any_has_depth(ToSeq(codes)):\n"
    "        raise NoMatch()\n"
    "    return 1\n"
)

# ---------------------------------------------------------------------------
# 3. FRAME-MUTATION (uniqueness, reject) — MANDATORY (codes is Acc(...,1/2)).
#    A rival that WRITES to the read-only input to satisfy the postcondition
#    vacuously. It must fail for INSUFFICIENT PERMISSION: only 1/2 of
#    list_pred(codes) is held, and list assignment requires the FULL predicate.
#    Gold invariants/contracts are kept verbatim so the rejection is attributable
#    to the write, not a proof gap. refinement: a real patch that mutated the
#    sorted addend list `pargs` before classifying would corrupt _sqrt_match's
#    own analysis (the helper splits the wrong sum), failing the F2P / P2P.
# ---------------------------------------------------------------------------
_FRAME_MUT = (
    "    codes[0] = 1  # illegal: writes a read-only (Acc 1/2) input\n"
    "    if all_fast_facet(ToSeq(codes)):\n"
    "        k = num_surds(ToSeq(codes))\n"
    "        return split_by_radicand_gcd(ToSeq(codes), k)\n"
    "    if not any_has_depth(ToSeq(codes)):\n"
    "        raise NoMatch()\n"
    "    return 1\n"
)

# ---------------------------------------------------------------------------
# 4. LITERAL ECHO on the fast path (uniqueness, reject) — the ungrounded-oracle
#    probe, recast: return a literal (!= 1) on the guard-passing case WITHOUT
#    invoking the helper. The grounded postcondition pins Result() ==
#    split_by_radicand_gcd(...), an OPAQUE value, so the literal cannot be proved
#    equal to it => reject. If it verified, the spec would be the pre-2nd-pass
#    hole (a fabricatable marker) => SPEC-TOO-WEAK.
#    refinement: a real patch that returned a hardcoded triple on the fast path
#    instead of split_surds(p)'s gcd-split would give the WRONG (a,b,r) for every
#    real fast-path sum (test_sqrtdenest2/3 fast-path splits), failing the P2P.
# ---------------------------------------------------------------------------
_ECHO_LIT = (
    "    if all_fast_facet(ToSeq(codes)):\n"
    "        return 2  # literal, never calls the opaque helper\n"
    "    if not any_has_depth(ToSeq(codes)):\n"
    "        raise NoMatch()\n"
    "    return 1\n"
)

# ---------------------------------------------------------------------------
# 5. DEPTH-MARKER ON THE FAST PATH (uniqueness, reject) — route a fast-path input
#    through the depth analysis (always return 1). On the fast path the grounded
#    postcondition requires Result() == split_by_radicand_gcd(...), and the axiom
#    pins that helper output != 1, so Result()==1 is provably wrong => reject.
#    refinement: this is the marker-collapse the batch02 panel's DEFECT-1 caught;
#    a real patch routing an all-positive-rational sum through the depth fallback
#    (instead of split_surds) yields a depth-match triple, not the gcd split, so
#    test_sqrtdenest2/3 (which exercise the fast split) fail.
# ---------------------------------------------------------------------------
_DEPTH_ON_FAST = (
    "    if not any_has_depth(ToSeq(codes)):\n"
    "        if not all_fast_facet(ToSeq(codes)):\n"
    "            raise NoMatch()\n"
    "    return 1  # always the depth marker — never the helper, even on fast path\n"
)

# ---------------------------------------------------------------------------
# 6. WRONG k INTO THE HELPER (uniqueness, reject) — calls the helper with
#    k = num_surds + 1, violating its Requires(k == num_surds). The axiom's
#    precondition fails to verify => reject.
#    refinement: split_surds counts its own surds; a patch that lied about the
#    surd count would not change what the real callee does, but the MODEL proof
#    breaks — and a faithful patch building the wrong gcd grouping would split
#    the wrong radicands, failing the fast-path P2P.
# ---------------------------------------------------------------------------
_WRONG_K = (
    "    if all_fast_facet(ToSeq(codes)):\n"
    "        k = num_surds(ToSeq(codes)) + 1\n"
    "        return split_by_radicand_gcd(ToSeq(codes), k)\n"
    "    if not any_has_depth(ToSeq(codes)):\n"
    "        raise NoMatch()\n"
    "    return 1\n"
)

# ---------------------------------------------------------------------------
# 7. PARTIAL-DOMAIN / CONTROL-FLOW (uniqueness, reject) — correct on the fast
#    path and on the nested fallback, but NEVER raises NoMatch: it returns the
#    depth marker 1 on the shallow non-eligible sub-domain (e.g. codes [0,2]).
#    That domain is pinned by Exsures(NoMatch, ... and not all_fast_facet and not
#    any_has_depth): returning 1 there leaves the NoMatch obligation undischarged
#    AND violates Ensures(all_fast_facet or any_has_depth) (both are false), so
#    it must reject.
#    refinement: this is exactly the FAIL_TO_PASS — _sqrt_match(4 + I) (codes
#    [0,2]) must return the EMPTY match []. An impl returning a non-empty match
#    marker there returns a spurious (a,b,r) and fails test_issue_12420.
# ---------------------------------------------------------------------------
_PARTIAL = (
    "    if all_fast_facet(ToSeq(codes)):\n"
    "        k = num_surds(ToSeq(codes))\n"
    "        return split_by_radicand_gcd(ToSeq(codes), k)\n"
    "    return 1  # never raises NoMatch — wrong on the shallow non-eligible domain\n"
)

# ---------------------------------------------------------------------------
# 8. WEAK-GUARD FAST PATH (uniqueness, reject) — SUPPORTING near-miss mirroring
#    the prepatch bug at the spec level: take the fast path under a LOOSER guard
#    (any_has_depth instead of all_fast_facet), so the helper is invoked on an
#    input that may carry a NON-eligible addend (e.g. codes [2,3]: any_has_depth
#    true, all_fast_facet false). The helper call then fails its
#    Requires(all_fast_facet) precondition => reject. This is the exact shape of
#    the bug the gold patch fixes (the guard was too loose); model_prepatch.py
#    reproduces it and fails the same split_by_radicand_gcd precondition (G-DIFF).
#    refinement: the loosened guard hands split_surds a sum with non-eligible
#    addends — the very over-admission whose imaginary special case (4 + I) hits
#    _split_gcd with an empty surds tuple -> IndexError, the pre-patch crash the
#    FAIL_TO_PASS asserts is gone.
# ---------------------------------------------------------------------------
_WEAK_GUARD = (
    "    if any_has_depth(ToSeq(codes)):\n"
    "        k = num_surds(ToSeq(codes))\n"
    "        return split_by_radicand_gcd(ToSeq(codes), k)\n"
    "    raise NoMatch()\n"
)


SPEC_TESTS = [
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _impl(_POS),
     "rationale": "structurally-different correct impl (inverted branch nesting, "
                  "fallback-first) that genuinely invokes the helper on the fast "
                  "path; must verify or the spec is SPEC-TOO-STRONG."},
    {"id": "admiss-both-branches", "kind": "admissibility", "expect": "verify",
     "module": _impl(_ADMISS),
     "rationale": "the precondition admits an F2P/P2P-shaped input on BOTH "
                  "branches (frame fact usable, guard and its negation reachable); "
                  "if these Asserts failed the Requires would be PRECOND-TOO-STRONG."},

    {"id": "frame-mutation", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_FRAME_MUT),
     "refinement": "a faithful patch that mutated the sorted addend list before "
                   "classifying would split the wrong sum in split_surds, "
                   "corrupting every fast-path match and failing test_sqrtdenest2/3.",
     "rationale": "codes is read-only (Acc(list_pred(codes),1/2)); writing codes[0] "
                  "needs the full predicate => INSUFFICIENT PERMISSION. The #1 "
                  "weakness class; gold contracts kept verbatim so the rejection "
                  "is attributable to the write, not a proof gap."},
    {"id": "echo-literal-fastpath", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_ECHO_LIT),
     "refinement": "returning a hardcoded triple on the fast path instead of "
                   "split_surds(p)'s gcd-split gives the wrong (a,b,r) for every "
                   "real fast-path sum, failing the P2P fast-path splits.",
     "rationale": "the grounded fast-path postcondition Result() == "
                  "split_by_radicand_gcd(ToSeq(codes), num_surds(...)) pins the "
                  "result to the helper's OPAQUE output; a literal (2) cannot be "
                  "proved equal to it. If it verified => SPEC-TOO-WEAK (the "
                  "pre-2nd-pass fabricatable-marker hole)."},
    {"id": "depth-marker-on-fastpath", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_DEPTH_ON_FAST),
     "refinement": "routing an all-positive-rational sum through the depth "
                   "fallback yields a depth-match triple, not the gcd split, so "
                   "the fast-path P2P (test_sqrtdenest2/3) fail.",
     "rationale": "on the fast path the grounded postcondition needs Result() == "
                  "split_by_radicand_gcd(...), and the axiom pins that output != 1, "
                  "so Result()==1 is provably wrong (marker-collapse, DEFECT-1)."},
    {"id": "wrong-k-into-helper", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_WRONG_K),
     "refinement": "a faithful patch lying about the surd count would build the "
                   "wrong gcd grouping and split the wrong radicands, failing the "
                   "fast-path P2P.",
     "rationale": "split_by_radicand_gcd Requires(k == num_surds(codes)); calling "
                  "it with num_surds+1 fails that precondition => reject."},
    {"id": "partial-domain-no-nomatch", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_PARTIAL),
     "refinement": "this is the FAIL_TO_PASS itself: _sqrt_match(4 + I) (codes "
                   "[0,2]) must return the EMPTY match []; returning a non-empty "
                   "match marker there fails test_issue_12420.",
     "rationale": "on the shallow non-eligible domain (not all_fast_facet and not "
                  "any_has_depth) Exsures(NoMatch, ...) requires a raise; returning 1 "
                  "leaves NoMatch undischarged AND violates Ensures(all_fast_facet "
                  "or any_has_depth) (both false) => reject."},
    {"id": "weak-guard-fastpath", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_WEAK_GUARD),
     "refinement": "this admits 4 + I (codes [0,2]) to split_surds, which the real "
                   "callee hits with an empty surds tuple -> IndexError — the "
                   "pre-patch crash the FAIL_TO_PASS asserts is gone.",
     "rationale": "supporting near-miss = the prepatch bug at spec level: taking "
                  "the fast path under the looser guard `any_has_depth` calls the "
                  "helper on a possibly non-eligible input (e.g. codes [2,3]) "
                  "without establishing its Requires(all_fast_facet) => reject "
                  "(same precondition model_prepatch.py fails, G-DIFF)."},
]


# ---------------------------------------------------------------------------
# AXIOM lane — the one A-consumed axiom split_by_radicand_gcd ↔ the unchanged
# real callee sympy.simplify.radsimp.split_surds. Both probes EXECUTE the real
# callee (AVOID #4: never scrape source) and reuse axiom_check.py's classifier.
# The runner mounts ONLY the probe at /work, so the classifier is embedded as a
# string at load time (AVOID #6) and all file reads use encoding="utf-8"
# (AVOID #5). apply_gold=True: the axiom describes the post-gold (and unchanged)
# callee behaviour under the post-patch guard.
# ---------------------------------------------------------------------------

# shared classifier, copied verbatim from axiom_check.py's helpers (the G-AX
# soundness ground truth) so the two probes agree on the code abstraction.
_CLASSIFIER = r'''
import sys
try:
    from sympy import sqrt, S, I, Add, Rational, Integer
    from sympy.core.function import _mexpand
    from sympy.simplify.radsimp import split_surds
    from sympy.simplify.sqrtdenest import _sqrt_match, sqrt_depth
except Exception as e:
    print("PBT SKIP: sympy not importable (%r); run in the patched container." % (e,))
    sys.exit(0)

def addend_code(x):
    sq = x ** 2
    pos_rat = bool(sq.is_Rational) and bool(sq.is_positive)
    rat = bool(sq.is_Rational)
    depth = sqrt_depth(x) >= 1
    if pos_rat and not depth:
        return 0
    if pos_rat and depth:
        return 1
    if rat and not pos_rat and not depth:
        return 2
    return 3 if depth else 2

def codes_of(p):
    p = _mexpand(p)
    if not p.is_Add:
        return None
    return [addend_code(x) for x in p.args]

def is_surd_addend(x):
    c, m = x.as_coeff_Mul()
    return bool(m.is_Pow)

def num_surds_real(p):
    p = _mexpand(p)
    return sum(1 for x in p.args if is_surd_addend(x))

def splits_ok(p):
    try:
        split_surds(p)
        return True
    except IndexError:
        return False

FAIL = []
def check(cond, msg):
    if not cond:
        FAIL.append(msg)

# the all-positive-rational fast-path sums (axiom Requires domain) and the
# shallow imaginary sums the OLD rational-only guard admitted (out of domain).
FAST = [
    3 + sqrt(2),
    1 + sqrt(2) + sqrt(3),
    2 + 3 * sqrt(5),
    sqrt(2) + sqrt(3) + sqrt(6),
    3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15),
    Rational(1, 2) + sqrt(7),
    4 + sqrt(2) + sqrt(8) + sqrt(18),
    1 + sqrt(2) + sqrt(2) * sqrt(3),
]
IMAG = [4 + I, 3 + 2 * I, I + Rational(5, 3), 7 + I]
'''

_AX_SOUNDNESS = _CLASSIFIER + r'''
# axiom-soundness: under the caller's actual runtime config (post-gold sympy),
# the real split_surds RETURNS NORMALLY on every input IN the axiom's Requires
# domain (all_fast_facet AND num_surds>=1), matching Ensures(Result() != 1) =
# "a match is produced" (an opaque outcome; the value is unpinned and not
# asserted here). The frame fact num_surds>=1 must hold so the precondition is
# not vacuous. The boundary/sentinel probe: the SHALLOW IMAGINARY sums (a
# code-2 addend) are OUTSIDE the domain and the real callee RAISES IndexError
# there — confirming the positive requirement is load-bearing, so the axiom
# precondition cannot be vacuously satisfied on those inputs (no false "holds").
for p in FAST:
    codes = codes_of(p)
    if codes is None:
        continue
    all_pos = all(c in (0, 1) for c in codes)
    ns = num_surds_real(p)
    if all_pos and ns >= 1:
        check(splits_ok(p),
              "AXIOM-UNSOUND: split_surds raised on in-domain sum (%d surd(s)): %r"
              % (ns, p))
        check(ns >= 1,
              "frame fact broken: all-pos-rational sum has no surd: %r" % p)

for p in IMAG:
    codes = codes_of(p)
    if codes is None:
        continue
    check(any(c == 2 for c in codes),
          "expected a code-2 (rational non-positive) addend in %r, got %r" % (p, codes))
    check(not all(c in (0, 1) for c in codes),
          "imaginary sum %r misclassified as all fast-eligible" % p)
    all_rat = all(bool((x ** 2).is_Rational) for x in _mexpand(p).args)
    check(all_rat, "expected the OLD rational-only guard to admit %r" % p)
    check(not splits_ok(p),
          "split_surds did NOT raise on out-of-domain %r — the positive guard "
          "would be unnecessary, the axiom precondition would be vacuous" % p)

# end-to-end: the FAIL_TO_PASS and the fast-path matches behave as modeled.
check(_sqrt_match(4 + I) == [],
      "_sqrt_match(4 + I) must be [] (empty match), got %r" % (_sqrt_match(4 + I),))
for p in IMAG:
    check(_sqrt_match(p) == [],
          "_sqrt_match(%r) must be [] (shallow non-positive square), got %r"
          % (p, _sqrt_match(p)))
for p in [1 + sqrt(2) + sqrt(3), sqrt(2) + sqrt(3) + sqrt(6),
          3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15)]:
    m = _sqrt_match(p)
    check(isinstance(m, list) and len(m) == 3,
          "_sqrt_match(%r) expected a 3-element match, got %r" % (p, m))

if FAIL:
    print("AXIOM-SOUNDNESS FAIL (%d):" % len(FAIL))
    for f in FAIL:
        print("  -", f)
    sys.exit(1)
print("axiom-soundness OK: split_surds returns normally on every in-domain "
      "(all fast-eligible, >=1 surd) sum and RAISES on every out-of-domain "
      "shallow imaginary sum; frame fact holds; _sqrt_match([]) end-to-end.")
sys.exit(0)
'''

_AX_CONTAINMENT = _CLASSIFIER + r'''
# axiom-containment: enumerate EXACTLY the callee-inputs the MODEL can reach and
# assert each lies in the axiom's Requires domain. The model invokes
# split_by_radicand_gcd(ToSeq(codes), num_surds(ToSeq(codes))) ONLY inside
# `if all_fast_facet(ToSeq(codes))`, and the precondition frame fact gives
# num_surds(codes) >= 1 whenever all_fast_facet. So the reachable inputs are
# precisely { codes : all_fast_facet(codes) } with k == num_surds(codes) >= 1 —
# which is EXACTLY the axiom's Requires(all_fast_facet AND k==num_surds AND k>=1).
# Containment holds iff every real fast-path-shaped Add the caller can reach has
# num_surds >= 1 (so k >= 1 is established, not assumed). We confirm this on the
# real Add: every all-fast-eligible genuine multi-term sum has >= 1 surd, so the
# caller NEVER passes k == 0 (the only way to escape the axiom domain). Covering
# the imaginary sums (which the caller CANNOT reach via the post-patch guard) is
# not required — and indeed those are out-of-domain, which is sound, not a defect.
seen_fast = 0
for p in FAST:
    codes = codes_of(p)
    if codes is None:
        continue
    if all(c in (0, 1) for c in codes):  # caller-reachable fast-path input
        seen_fast += 1
        ns = num_surds_real(p)
        # the axiom Requires k >= 1; the caller passes k = num_surds, so this is
        # the containment obligation: a reachable input with num_surds == 0 would
        # be OUTSIDE the axiom domain => AXIOM-TOO-WEAK-FOR-CALLER.
        check(ns >= 1,
              "AXIOM-TOO-WEAK-FOR-CALLER: caller-reachable fast-path sum %r has "
              "num_surds == 0 (outside the axiom's k>=1 domain)" % p)
        check(all(0 <= c <= 3 for c in codes),
              "code out of the model's declared 0..3 range for %r: %r" % (p, codes))

check(seen_fast >= 1,
      "no caller-reachable fast-path sum exercised — containment check vacuous")

# negative containment evidence: the imaginary sums are NOT caller-reachable
# (the post-patch guard all_fast_facet is false on them), so the model never
# hands them to the helper — covering them is unnecessary (float-vs-int rule).
for p in IMAG:
    codes = codes_of(p)
    if codes is None:
        continue
    check(not all(c in (0, 1) for c in codes),
          "imaginary sum %r would be caller-reachable but is out-of-domain" % p)

if FAIL:
    print("AXIOM-CONTAINMENT FAIL (%d):" % len(FAIL))
    for f in FAIL:
        print("  -", f)
    sys.exit(1)
print("axiom-containment OK: every caller-reachable fast-path input "
      "(all fast-eligible) has num_surds >= 1, so k >= 1 is established and each "
      "reachable callee-input lies inside the axiom's Requires domain; the "
      "out-of-domain imaginary sums are not caller-reachable.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {"id": "ax-soundness-split-surds", "axiom": "split_by_radicand_gcd",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUNDNESS,
     "rationale": "the real split_surds must return normally on every in-domain "
                  "(all fast-eligible, >=1 surd) sum (Ensures(Result()!=1) = a "
                  "match is produced) and RAISE on the out-of-domain shallow "
                  "imaginary sums (so the precondition is load-bearing, not "
                  "vacuous). A violation => AXIOM-UNSOUND."},
    {"id": "ax-containment-split-surds", "axiom": "split_by_radicand_gcd",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "the model reaches the helper only under all_fast_facet, where "
                  "the frame fact gives num_surds>=1; every caller-reachable "
                  "fast-path Add has >=1 surd so k>=1 is established. A reachable "
                  "input with num_surds==0 => AXIOM-TOO-WEAK-FOR-CALLER."},
]
