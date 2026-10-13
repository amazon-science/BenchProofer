# properties.py — PBT falsification battery for sympy__sympy-15599.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery that edits ONLY
# inside the `# impl-start` / `# impl-end` block (so the frozen spec — axioms,
# pure helpers, pre/post-conditions, signature — is byte-identical and
# same_spec holds). The runner stamps each with verify(host, Nagini) + same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (the spec this battery attacks)
# ---------------------------------------------------------------------------
#   reduce_coefficients(is_int: List[int], value: List[int], m: int) -> List[int]
#   reduces a product's factor-value list modulo an integer divisor m (m >= 2),
#   factor by factor (the integer-coefficient rewrite the gold patch inserts in
#   Mod.eval.doit's Mul branch). `is_int` and `value` are READ-ONLY inputs:
#   Acc(list_pred(is_int), 1/2) / Acc(list_pred(value), 1/2), held verbatim in
#   the Ensures (frame-preserving).
#
#   The load-bearing postcondition is the per-factor pin
#       Ensures(Acc(list_pred(Result())))
#       Ensures(len(Result()) == len(value))
#       Ensures(Forall k: 0<=k<len(value) ->
#                 Result()[k] == reduced_factor(is_int[k], value[k], m))
#   where `reduced_factor` (the `# pure` region) is, for m >= 2,
#       is_int==1 and residue(value,m)!=0  -> residue(value,m)   (shrink coeff)
#       otherwise (opaque factor, or integer multiple of m) -> value (unchanged)
#   and `residue(value,m)` is the @ContractOnly least-non-negative-residue
#   primitive (== sympy Integer.__mod__, A-reference, G-AX-validated).
#
#   The DISCRIMINATING content (vs the pre-patch code, which had no rewrite
#   block): an integer factor c with c % m != 0 must become c % m, not stay c
#   (the issue's Mod(3*i,2)==Mod(i,2): coeff 3 -> 1; Mod(8*i,4)==0: coeff 8 ->
#   0). model_prepatch.py returns value[k] unchanged and FAILS exactly this pin.
#
# Oracle-grounding note (ungrounded-oracle-echo class — DOES NOT APPLY):
#   `reduced_factor` is a @Pure helper, but it is NOT an opaque answer-key
#   oracle. Its body is fully spelled out and reads ONLY the inputs (is_int[k],
#   value[k], m) via the @Pure residue; the postcondition unfolds it. An impl
#   that "echoes" reduced_factor (v = reduced_factor(is_int[k], value[k], m)) is
#   therefore the CORRECT gold answer, not a cheat — there is no wrong value to
#   echo, because reducing IS the work. The discriminating content lives entirely
#   inside reduced_factor's branching. So we instead supply (a) an honest
#   structurally-different positive control that echoes reduced_factor directly
#   (cheapest correct shape, must verify) and (b) the partial-domain rivals below,
#   each of which perturbs the per-factor value so Result()[k] != reduced_factor.
#
# Control-flow-effect note (DOES NOT APPLY):
#   reduce_coefficients has no raise / early-return / side-effect branch — it is
#   a single total value-producing forward loop with no exceptional path. The
#   whole content is the produced value list, already pinned per index by the
#   value abstraction. There is no capability-token discriminator to add; omitted
#   (see assessment).

from pathlib import Path

INSTANCE = "sympy__sympy-15599"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything between # impl-start and
# # impl-end, markers exclusive). Every variant is produced by _swap on _BASE
# touching ONLY text inside this block.
_GOLD_IMPL = """    n = len(value)
    result = []  # type: List[int]
    k = 0
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(is_int), 1 / 2))
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(m >= 2)
        Invariant(len(is_int) == len(value))
        Invariant(n == len(value))
        Invariant(0 <= k and k <= n)
        Invariant(len(result) == k)
        Invariant(Forall(int, lambda b: (
            Implies(0 <= b and b < k,
                    result[b] == reduced_factor(is_int[b], value[b], m)),
            [[result[b]]])))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        if is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]
        # v is exactly the per-factor reduction for factor k.
        Assert(v == reduced_factor(is_int[k], value[k], m))
        old_result = result
        result = result + [v]
        Assert(len(result) == k + 1)
        Assert(Forall(int, lambda b: (
            Implies(0 <= b and b < k, result[b] == old_result[b]),
            [[result[b]]])))
        Assert(result[k] == v)
        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
        k = k + 1
    return result
"""

# Sanity: the gold impl text must appear verbatim and uniquely in _BASE.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drift — re-sync _GOLD_IMPL"


# The exact per-factor value-computation block (the only thing the partial-domain
# rivals perturb). The framing/lemma asserts AROUND it are kept verbatim in every
# rival so a rejection is attributable to the VALUE being wrong (Result()[k] !=
# reduced_factor(...)), never to a deleted proof obligation.
_GOLD_BRANCH = """        if is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]"""


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
#    Reshape: instead of the inlined if/else that recomputes residue, call the
#    pure `reduced_factor` per-factor oracle directly (v = reduced_factor(...)).
#    This is a legitimate, faithful impl (reduced_factor IS the gold per-factor
#    rewrite, validated == the real callee by G-AX) and is the cheapest correct
#    shape. It keeps the FORWARD append, the prefix-preservation invariant, and
#    EVERY gold framing assert verbatim, so the gold proof obligations still
#    discharge (Assert(v == reduced_factor(...)) becomes trivially v == v).
#    MUST verify — else SPEC-TOO-STRONG.
_POS_IMPL = _swap(
    _GOLD_IMPL,
    _GOLD_BRANCH,
    "        v = reduced_factor(is_int[k], value[k], m)",
)


# ===========================================================================
# 2. POSITIVE CONTROL #2 (soundness) — a DIFFERENT structural reshape that keeps
#    the explicit branch but INVERTS the guard / reorders the cases: handle the
#    "keep value" case first (NOT an integer coefficient to shrink), then the
#    shrink case. The two branches still partition the per-factor domain
#    identically, so v is the same value for every k; all gold asserts kept
#    verbatim. MUST verify — else SPEC-TOO-STRONG (rejecting a faithful guard
#    inversion). NB: residue() is @Pure/@ContractOnly so re-evaluating it in a
#    different order is sound (determinism only).
_POS2_IMPL = _swap(
    _GOLD_IMPL,
    _GOLD_BRANCH,
    """        if is_int[k] != 1 or residue(value[k], m) == 0:
            v = value[k]
        else:
            v = residue(value[k], m)""",
)


# ===========================================================================
# 3. ADMISSIBILITY — the precondition must ACCEPT a normal F2P-shaped input.
#    The Requires is permission (Acc(list_pred,1/2) on is_int and value) + m >= 2
#    + len(is_int) == len(value). The issue's witness Mod(3*i, 2) is the product
#    of a concrete integer coefficient 3 (is_int=1, value=3) and an opaque factor
#    i (is_int=0): is_int=[1,0], value=[3,*], m=2 — squarely in-domain. We keep
#    the full gold impl and add, at the TOP of impl, derivable assertions that the
#    Requires facts hold (a 1/4 read share is obtainable from the 1/2 held; m>=2
#    and the equal-length fact are establishable). If this fails to verify =>
#    PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    Assert(Acc(list_pred(is_int), 1 / 4))
    Assert(Acc(list_pred(value), 1 / 4))
    Assert(m >= 2)
    Assert(len(is_int) == len(value))
""" + _GOLD_IMPL


# ===========================================================================
# 4. FRAME-MUTATION (MANDATORY — read-only inputs). A rival that WRITES to the
#    read-only input `value` before the loop. With only Acc(list_pred(value),
#    1/2) the assignment value[0] = 0 needs FULL permission and MUST be rejected
#    for insufficient permission. Every gold invariant / branch / assert is kept
#    verbatim so the rejection is attributable to the WRITE, not to a proof gap.
#    expect=reject.
#    Refinement: the repo block reads each factor `i` from `non_mod_l` and appends
#    a fresh value (`i % q` or `i`) to a NEW list `_`; it never mutates the source
#    factors. A faithful patch cannot write into the input factor list. One that
#    zeroed value[0] before reducing would, on the issue's Mod(3*i, 2) (factor 0 =
#    coeff 3), read coeff 0 instead of 3 -> reduced_factor(1,0,2)=0 (since
#    residue(0,2)=0, kept as value=0) instead of reduced_factor(1,3,2)=1; the
#    product becomes Mod(0, 2)=0 rather than Mod(i, 2). F2P test_Mod's
#    Mod(3*i,2)==Mod(i,2) FAILS. So a verifying mutator is a true
#    verify-not-resolve break.
_FRAME_IMPL = _swap(
    _GOLD_IMPL,
    "    n = len(value)\n    result = []",
    "    if len(value) > 0:\n        value[0] = 0\n    n = len(value)\n    result = []",
)


# ===========================================================================
# 5. FRAME-MUTATION #2 (the is_int tag input). Writes to the OTHER read-only
#    input is_int[0] before the loop (also Acc(list_pred(is_int),1/2)). MUST be
#    rejected for insufficient permission. Gold invariants/branch/asserts kept
#    verbatim. expect=reject.
#    Refinement: `is_int` abstracts each factor's `i.is_Integer` flag, an
#    immutable property of the source factor; the gold block reads it (the
#    `i.is_Integer` guard) and never alters it. A patch that forced is_int[0]=0
#    would treat the integer coefficient 3 in Mod(3*i,2) as opaque, keep it
#    unchanged (reduced_factor(0,3,2)=3) instead of reducing to 1, so Mod(3*i,2)
#    would NOT collapse to Mod(i,2); F2P test_Mod FAILS. A verifying mutator is a
#    true verify-not-resolve break.
_FRAME2_IMPL = _swap(
    _GOLD_IMPL,
    "    n = len(value)\n    result = []",
    "    if len(is_int) > 0:\n        is_int[0] = 0\n    n = len(value)\n    result = []",
)


# ===========================================================================
# 6. PARTIAL-DOMAIN (the LITERAL pre-patch bug) — never reduce: v = value[k]
#    always. Identical in spirit to model_prepatch.py (no rewrite block). Only the
#    branch is replaced by the pass-through; framing asserts kept verbatim, so it
#    fails ONLY on Assert(v == reduced_factor(...)) / the loop invariant (whenever
#    an integer factor has residue != 0 and value not already in [0,m)).
#    expect=reject.
#    Refinement: this is the exact regression. On the issue's Mod(3*i, 2), the
#    coefficient 3 stays 3 instead of becoming 1, so Mod(3*i,2) does NOT equal
#    Mod(i,2); on Mod(8*i, 4) the coeff 8 stays 8 instead of becoming 0, so the
#    product is not 0. F2P test_Mod FAILS. The canonical verify-not-resolve rival
#    (G-DIFF's discriminator).
_PASSTHRU_BRANCH = "        v = value[k]"
_PASSTHRU_IMPL = _swap(_GOLD_IMPL, _GOLD_BRANCH, _PASSTHRU_BRANCH)


# ===========================================================================
# 7. PARTIAL-DOMAIN (drop the is_int guard) — reduce EVERY factor to its residue
#    when residue != 0, even opaque (is_int==0) ones: drops the `is_int[k]==1`
#    conjunct. Correct on integer factors; WRONG on any opaque factor whose
#    placeholder value has residue != 0 (reduced_factor keeps it = value, this
#    returns residue(value,m)). Framing asserts kept verbatim; fails on Assert(v
#    == reduced_factor(...)). expect=reject.
#    Refinement: the gold block reduces only factors with `i.is_Integer`; an
#    opaque symbolic factor (i, x, i*x in the issue) is appended UNCHANGED. A
#    patch that applied `i % q` to a non-Integer factor would corrupt the
#    symbolic part of the product — e.g. on Mod(3*i, 2) the opaque i factor would
#    be rewritten rather than preserved, so the product is not Mod(i, 2). F2P
#    test_Mod (and P2P (3*i*x)%(2*i*y)==i*Mod(3*x,2*y), which relies on opaque
#    factors surviving) FAIL. A patch dropping the is_Integer guard would not
#    resolve.
_NOINTGUARD_BRANCH = """        if residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]"""
_NOINTGUARD_IMPL = _swap(_GOLD_IMPL, _GOLD_BRANCH, _NOINTGUARD_BRANCH)


# ===========================================================================
# 8. PARTIAL-DOMAIN (drop the residue!=0 guard) — for an integer factor, always
#    return residue(value[k], m), even when the residue is 0 (i.e. the factor is
#    a multiple of m). reduced_factor keeps such a factor = value (e.g.
#    reduced_factor(1,8,4)=8 since residue(8,4)=0), but this returns
#    residue(8,4)=0. WRONG on every integer multiple of m whose value is itself
#    >= m (value != residue). Framing asserts kept verbatim; fails on Assert(v ==
#    reduced_factor(...)). expect=reject.
#    Refinement: the gold guard `(i % q is not S.Zero)` keeps a multiple-of-q
#    integer factor UNCHANGED (it appends `i`, not `i%q`). A patch dropping that
#    guard would rewrite e.g. an 8-coefficient against q=4 to 0 in the factor
#    list (8 -> 8%4 == 0), collapsing a nonzero coefficient to 0 and changing the
#    product (turning Mul(8, ...) into Mul(0, ...)); for products where the
#    coefficient must be preserved this diverges from gold. The guard is part of
#    the inserted block; a patch without it would not be the gold rewrite and is
#    not what G-RESOLVE accepts. (Cheap supporting case: the divergence is on the
#    is-Zero sub-domain, value != residue.)
_NORESGUARD_BRANCH = """        if is_int[k] == 1:
            v = residue(value[k], m)
        else:
            v = value[k]"""
_NORESGUARD_IMPL = _swap(_GOLD_IMPL, _GOLD_BRANCH, _NORESGUARD_BRANCH)


# ===========================================================================
# 9. PARTIAL-DOMAIN (single-position miss at k==0) — correct EVERYWHERE except
#    the first factor (k==0), which is forced to a fixed 0 instead of its reduced
#    value. A near-miss that pins the entire domain but one position; framing
#    asserts kept verbatim; fails on Assert(v == reduced_factor(...)) at k==0.
#    expect=reject.
#    Refinement: a patch that special-cased the first factor to 0 would, on the
#    issue's Mod(3*i, 2) where factor 0 is the coeff 3, set its reduced value to 0
#    instead of 1, so Mod(3*i,2) collapses to Mod(0,2)=0 rather than Mod(i,2). F2P
#    test_Mod FAILS. A real first-element bug would not resolve.
_FIRSTPOS_BRANCH = """        if k == 0:
            v = 0
        elif is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]"""
_FIRSTPOS_IMPL = _swap(_GOLD_IMPL, _GOLD_BRANCH, _FIRSTPOS_BRANCH)


# ===========================================================================
# 10. PARTIAL-DOMAIN (single-position miss at k==n-1) — correct EVERYWHERE except
#    the last factor (k==n-1), which is forced to 0. Symmetric near-miss pinning
#    every index but the last; framing asserts kept verbatim; fails on Assert(v ==
#    reduced_factor(...)) at k==n-1. expect=reject.
#    Refinement: a patch special-casing the final factor to 0 would, on a product
#    Mod(i * 3, 2) where the coeff 3 is the last factor, set it to 0 instead of 1,
#    so the product collapses to 0 rather than Mod(i, 2). F2P test_Mod (depending
#    on factor order) FAILS; more generally a one-position special-case is not the
#    gold per-factor loop and would not resolve.
_LASTPOS_BRANCH = """        if k == n - 1:
            v = 0
        elif is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]"""
_LASTPOS_IMPL = _swap(_GOLD_IMPL, _GOLD_BRANCH, _LASTPOS_BRANCH)


SPEC_TESTS = [
    {
        "id": "pos-control-echo-reduced-factor",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: drops the inlined if/else "
            "that recomputes residue and binds v = reduced_factor(is_int[k], "
            "value[k], m) directly (the cheapest faithful shape; reduced_factor "
            "IS the gold per-factor rewrite, G-AX-validated == the real callee). "
            "Keeps the forward append, the prefix-preservation invariant, and "
            "every gold framing assert verbatim, so the gold proof obligations "
            "still discharge. Must verify; if it cannot, the postcondition is "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-guard-inversion",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS2_IMPL),
        "rationale": (
            "structurally-different but CORRECT impl: same per-factor logic, but "
            "the guard is INVERTED / the cases reordered (handle the keep-value "
            "case first, then the shrink case). The two branches still partition "
            "the per-factor domain identically so v is unchanged for every k; all "
            "gold asserts kept verbatim. residue is @Pure so re-ordering its "
            "evaluation is sound. Must verify; if it cannot, SPEC-TOO-STRONG "
            "(rejecting a faithful guard inversion)."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": (
            "the precondition is permission (Acc(list_pred,1/2) on is_int and "
            "value) + m>=2 + len(is_int)==len(value); the issue's witness "
            "Mod(3*i,2) is is_int=[1,0], value=[3,*], m=2 — in-domain. Added "
            "top-of-impl assertions confirm a 1/4 read share is derivable from "
            "the 1/2 held and the m>=2 / equal-length facts hold. Must verify; if "
            "it cannot, PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutate-readonly-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_IMPL),
        "refinement": (
            "the gold block reads each factor i from non_mod_l and appends a "
            "fresh value to a NEW list _; it never mutates the source factors. A "
            "faithful patch cannot write into the input factor list. One that "
            "zeroed value[0] (the coeff 3 in Mod(3*i,2)) would reduce coeff 0 "
            "instead of 3 -> 0 instead of 1, so Mod(3*i,2) collapses to Mod(0,2) "
            "rather than Mod(i,2); F2P test_Mod FAILS. A verifying mutator is a "
            "true verify-not-resolve break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: value holds only "
            "Acc(list_pred(value),1/2); the write value[0]=0 needs full "
            "permission and is rejected for insufficient permission. Every gold "
            "invariant/branch/assert is kept verbatim so the failure is "
            "attributable to the write, not a proof gap. If it verifies, the "
            "frame on `value` is unguarded (FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "frame-mutate-readonly-is-int",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME2_IMPL),
        "refinement": (
            "is_int abstracts each factor's i.is_Integer flag, an immutable "
            "property of the source factor; the gold block reads it and never "
            "alters it. A patch forcing is_int[0]=0 would treat the integer "
            "coefficient 3 in Mod(3*i,2) as opaque, keeping it unchanged "
            "(reduced_factor(0,3,2)=3) instead of reducing to 1, so Mod(3*i,2) "
            "would not collapse to Mod(i,2); F2P test_Mod FAILS. A verifying "
            "mutator is a true verify-not-resolve break."
        ),
        "rationale": (
            "REJECT must come from the PERMISSION SYSTEM: is_int holds only "
            "Acc(list_pred(is_int),1/2); the write is_int[0]=0 needs full "
            "permission and is rejected for insufficient permission. Every gold "
            "invariant/branch/assert is kept verbatim so the failure is "
            "attributable to the write. If it verifies, the frame on `is_int` is "
            "unguarded (FRAME-MUTATION SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-prepatch-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PASSTHRU_IMPL),
        "refinement": (
            "the LITERAL pre-patch behaviour (== model_prepatch.py: no rewrite "
            "block): every factor value passes through unchanged (v = value[k]). "
            "On the issue's Mod(3*i,2) the coeff 3 stays 3 instead of becoming 1, "
            "and on Mod(8*i,4) the coeff 8 stays 8 instead of becoming 0; "
            "Mod(3*i,2) != Mod(i,2) and Mod(8*i,4) != 0. F2P test_Mod FAILS. The "
            "canonical verify-not-resolve rival (G-DIFF's discriminator)."
        ),
        "rationale": (
            "REJECT comes from the postcondition pin Result()[k] == "
            "reduced_factor(is_int[k],value[k],m): on any integer factor with "
            "residue != 0 and value not already in [0,m) (e.g. is_int=1, value=3, "
            "m=2: reduced_factor=1) the pass-through value[k]=3 != 1, so Assert(v "
            "== reduced_factor(...)) / the loop invariant fails. If it verifies, "
            "the spec does not pin the coefficient reduction (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-drop-is-int-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NOINTGUARD_IMPL),
        "refinement": (
            "drops the i.is_Integer guard: reduces EVERY factor (even opaque "
            "ones) to its residue when residue != 0. The gold block reduces only "
            "factors with i.is_Integer and appends opaque symbolic factors (i, x, "
            "i*x in the issue) UNCHANGED. A patch applying i%q to a non-Integer "
            "factor would corrupt the symbolic part of the product, so e.g. "
            "Mod(3*i,2) would not preserve i. F2P test_Mod and P2P "
            "(3*i*x)%(2*i*y)==i*Mod(3*x,2*y) (which need opaque factors to "
            "survive) FAIL. A patch dropping the is_Integer guard would not "
            "resolve."
        ),
        "rationale": (
            "REJECT comes from Result()[k] == reduced_factor(...): on an opaque "
            "factor (is_int==0) whose placeholder value has residue != 0, "
            "reduced_factor returns value but this returns residue(value,m) != "
            "value, so Assert(v == reduced_factor(...)) fails. If it verifies, "
            "the spec does not pin that opaque factors are preserved "
            "(SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-drop-residue-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NORESGUARD_IMPL),
        "refinement": (
            "drops the (i % q is not S.Zero) guard: for an integer factor always "
            "returns residue(value,m), even when the factor is a multiple of m. "
            "The gold guard keeps a multiple-of-q integer factor UNCHANGED "
            "(appends i, not i%q). A patch without it rewrites e.g. an 8-coeff "
            "against q=4 to 0 in the factor list (8 -> 8%4 == 0) instead of "
            "keeping 8, collapsing a nonzero coefficient; this is not the gold "
            "rewrite (the inserted block carries that exact guard) and diverges "
            "wherever value != residue, so it would not be what G-RESOLVE accepts."
        ),
        "rationale": (
            "REJECT comes from Result()[k] == reduced_factor(...): on an integer "
            "factor that is a multiple of m with value >= m (residue == 0, value "
            "!= 0, e.g. is_int=1, value=8, m=4: reduced_factor keeps 8) this "
            "returns residue(8,4)=0 != 8, so Assert(v == reduced_factor(...)) "
            "fails. If it verifies, the spec does not pin the keep-multiples-of-m "
            "case (SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-first-factor-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FIRSTPOS_IMPL),
        "refinement": (
            "correct EVERYWHERE except the first factor (k==0), forced to 0. On "
            "the issue's Mod(3*i,2) where factor 0 is the coeff 3, this sets its "
            "reduced value to 0 instead of 1, so Mod(3*i,2) collapses to Mod(0,2) "
            "rather than Mod(i,2); F2P test_Mod FAILS. A real first-element "
            "special-case bug would not resolve."
        ),
        "rationale": (
            "REJECT comes from Result()[k] == reduced_factor(...) at k==0: the "
            "forced 0 != reduced_factor(is_int[0],value[0],m) whenever the first "
            "factor's reduced value is nonzero, so Assert(v == reduced_factor) "
            "fails at that position. If it verifies, the postcondition leaves the "
            "first factor unpinned (partial-domain SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "partial-domain-last-factor-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _LASTPOS_IMPL),
        "refinement": (
            "correct EVERYWHERE except the last factor (k==n-1), forced to 0. On "
            "a product Mod(i*3, 2) where the coeff 3 is the trailing factor, this "
            "sets it to 0 instead of 1, so the product collapses to 0 rather than "
            "Mod(i, 2). A one-position special-case is not the gold per-factor "
            "loop; F2P test_Mod (factor-order dependent) FAILS and the rival "
            "would not resolve."
        ),
        "rationale": (
            "REJECT comes from Result()[k] == reduced_factor(...) at k==n-1: the "
            "forced 0 != reduced_factor(is_int[n-1],value[n-1],m) whenever the "
            "last factor's reduced value is nonzero, so Assert(v == "
            "reduced_factor) fails at that position. If it verifies, the "
            "postcondition leaves the last factor unpinned (partial-domain "
            "SPEC-TOO-WEAK)."
        ),
    },
]


# ===========================================================================
# AXIOM lane — the bundle has ONE @ContractOnly axiom (residue, A-reference) and
# ONE A-reference deep model (reduced_factor). axiom_check.py already validates
# both IN-container against the real callee (sympy Integer.__mod__ / the real
# per-factor rewrite). We mirror its obligations as independent PBT probes,
# strengthening the boundary/fuzz coverage and the caller-reachable containment.
#
#   ax-residue-soundness (axiom-soundness): the real sympy Integer.__mod__ (i % q)
#     — the callee the gold block invokes — satisfies residue's three Ensures
#     (range 0<=r<m, congruence (value-r)%m==0, in-range idempotence) AND equals
#     the model's residue encoding, on boundary + sentinel + fuzz (value, m) pairs
#     in the axiom's Requires domain m >= 2. If the real callee violates any
#     Ensures -> AXIOM-UNSOUND. The bundle's runtime config is the default
#     global_evaluate[0] (no flag dependency) and divisors are integers; we fuzz
#     negatives / zero / multiples / boundaries of `value`.
#
#   ax-residue-containment (axiom-containment): every (value, m) pair the MODEL
#     can feed to residue lies in residue's Requires domain (m >= 2). The model
#     calls residue(value[k], m) only under Requires(m >= 2) (the caller's own
#     precondition) and reduced_factor calls residue(value, m) under its own
#     Requires(m >= 2); `value` is an arbitrary int (no constraint). So the only
#     scoping obligation is m >= 2, which holds by the caller's Requires. We
#     confirm the callee accepts EVERY such input (any int value, any m >= 2)
#     value-preservingly — a caller-reachable input outside the domain would be
#     AXIOM-TOO-WEAK-FOR-CALLER. (The callee actually accepts a wider domain than
#     the model reaches — covering more is SOUND, not a defect.)
#
#   ax-reduced-factor-fidelity (axiom-soundness on the A-reference deep model):
#     reduced_factor EQUALS the real patched per-factor rewrite (the inserted
#     block: integer factor i with i%q != 0 -> i%q, else unchanged) cell by cell
#     over integer constants across the residue boundary + opaque symbols + fuzz,
#     AND the pre-patch behaviour (no reduction, factor stays) is DETECTABLY wrong
#     wherever an integer coefficient has residue != 0. This is the discriminating
#     obligation: if reduced_factor disagreed with the real patched rewrite, the
#     A-reference would be UNSOUND.
#
# All probes import only sympy (the package under change) + stdlib, open nothing
# on disk, exit 0 iff the obligation holds. (The runner mounts ONLY the probe
# script in the instance image; these probes are self-contained and do NOT read
# axiom_check.py / model.py from disk — they re-encode the obligation inline.)

_RESIDUE_SOUNDNESS_PROBE = r'''
import random, sys
from sympy import Integer


def residue_model(value, m):
    # model.py reference encoding (least non-negative residue == Integer.__mod__)
    return value % m


def check_residue(value, m):
    observed = int(Integer(value) % Integer(m))     # REAL callee i % q
    # Ensures #1: range 0 <= r < m
    if not (0 <= observed < m):
        print("AXIOM-UNSOUND: %d %% %d -> %d not in [0,%d)" % (value, m, observed, m))
        sys.exit(1)
    # Ensures #2: congruence (value - r) divisible by m
    if (value - observed) % m != 0:
        print("AXIOM-UNSOUND: %d - (%d %% %d) not divisible by %d" % (value, value, m, m))
        sys.exit(1)
    # Ensures #3: in-range idempotence
    if 0 <= value < m and observed != value:
        print("AXIOM-UNSOUND: %d %% %d -> %d but value already in [0,%d)" % (value, m, observed, m))
        sys.exit(1)
    # model encoding agrees with the real callee
    if observed != residue_model(value, m):
        print("AXIOM-UNSOUND: residue model %d disagrees with sympy %d for %d %% %d"
              % (residue_model(value, m), observed, value, m))
        sys.exit(1)


# boundary moduli + sentinel/boundary values (negatives, zero, in-range,
# multiples, just-below/just-above the modulus)
boundary_m = [2, 3, 4, 5, 6, 7, 8, 12, 100]
boundary_v = [-100, -8, -5, -3, -2, -1, 0, 1, 2, 3, 4, 7, 8, 9, 99, 100, 1000, -1000]
for m in boundary_m:
    for v in boundary_v:
        check_residue(v, m)
    # explicit multiples-of-m and boundary residues
    for kk in range(-3, 4):
        check_residue(kk * m, m)
        check_residue(kk * m + 1, m)
        check_residue(kk * m - 1, m)
rng = random.Random(15599)
for _ in range(50000):
    m = rng.randint(2, 50)
    v = rng.randint(-100000, 100000)
    check_residue(v, m)
print("AXIOM-SOUND: residue (== sympy Integer %%) satisfies range+congruence+"
      "idempotence and == model on %d boundary + 50000 fuzz (value,m) pairs"
      % (len(boundary_m) * len(boundary_v)))
sys.exit(0)
'''


_RESIDUE_CONTAINMENT_PROBE = r'''
import random, sys
from sympy import Integer


# Containment: residue's Requires domain is m >= 2 (value is an unconstrained
# int). The model calls residue only under Requires(m >= 2) — the caller
# reduce_coefficients's precondition and reduced_factor's own Requires — with an
# arbitrary integer `value`. So every caller-reachable (value, m) has m >= 2 and
# value an int, all inside the axiom domain. We confirm the real callee ACCEPTS
# every such input (any int value, any m >= 2) without error and returns an int
# in range. A caller-reachable input the callee could NOT handle in-domain would
# be AXIOM-TOO-WEAK-FOR-CALLER. (The callee actually accepts m == 1 and other
# inputs the model never reaches; covering more than the caller reaches is SOUND.)
def reachable_ok(value, m):
    # m >= 2 is the caller's Requires; value is any int. The callee must accept.
    try:
        r = int(Integer(value) % Integer(m))
    except Exception as e:                    # noqa: BLE001
        print("AXIOM-TOO-WEAK-FOR-CALLER: callee rejected reachable (value=%d, m=%d): %r"
              % (value, m, e))
        sys.exit(1)
    if not (0 <= r < m):
        print("AXIOM-TOO-WEAK-FOR-CALLER: callee out-of-range on reachable (value=%d, m=%d) -> %d"
              % (value, m, r))
        sys.exit(1)


# the modeled domain: m >= 2 (caller Requires), value an arbitrary int including
# the F2P coefficients (3 against m=2, 8 against m=4) and sentinels
for m in [2, 3, 4, 5, 8, 12, 100]:
    for v in [-100000, -8, -1, 0, 1, 3, 8, 100000]:
        reachable_ok(v, m)
reachable_ok(3, 2)     # the issue's Mod(3*i, 2): coeff 3, modulus 2
reachable_ok(8, 4)     # the issue's Mod(8*i, 4): coeff 8, modulus 4
rng = random.Random(155990)
for _ in range(20000):
    m = rng.randint(2, 1000)               # m >= 2, the caller's Requires
    v = rng.randint(-1000000, 1000000)
    reachable_ok(v, m)
print("AXIOM-COVERED: every model-reachable residue argument (m >= 2, value any "
      "int) is accepted in-domain by the real callee over the F2P coefficients + "
      "boundary + 20000 fuzz pairs (callee domain is wider — sound)")
sys.exit(0)
'''


_REDUCED_FACTOR_FIDELITY_PROBE = r'''
import random, sys
from sympy import Integer, S, Symbol


def residue_model(value, m):
    return value % m


def reduced_factor_model(is_int, value, m):
    # model.py pure region encoding
    if is_int == 1 and residue_model(value, m) != 0:
        return residue_model(value, m)
    return value


def real_reduce_factor(factor, q):
    # the exact gold per-factor rewrite (sympy/core/mod.py inserted block):
    #   if factor.is_Integer and (factor % q is not S.Zero): factor % q
    #   else: factor
    if factor.is_Integer and (factor % q is not S.Zero):
        return factor % q
    return factor


def prepatch_factor(factor, q):
    # pre-patch behaviour: NO reduction block — factor passes through unchanged.
    return factor


def check_integer_factor(value, q_int, discriminated):
    q = Integer(q_int)
    obj = Integer(value)
    real = real_reduce_factor(obj, q)
    model_val = reduced_factor_model(1, value, q_int)
    if int(real) != model_val:
        print("AXIOM-UNSOUND: reduced_factor != real rewrite on integer %d mod %d: real %d / model %d"
              % (value, q_int, int(real), model_val))
        sys.exit(1)
    # discrimination: the pre-patch (no-reduction) value differs from gold
    # wherever an integer coeff has nonzero residue and value not already reduced
    pre = prepatch_factor(obj, q)
    if int(pre) != int(real):
        discriminated[0] = True


def check_opaque_factor(obj, q_int):
    q = Integer(q_int)
    real = real_reduce_factor(obj, q)
    if real != obj:
        print("AXIOM-UNSOUND: opaque factor %r changed to %r mod %d" % (obj, real, q_int))
        sys.exit(1)
    # model keeps opaque (is_int==0) factor's placeholder value unchanged
    model_val = reduced_factor_model(0, 12345, q_int)
    if model_val != 12345:
        print("AXIOM-UNSOUND: reduced_factor model altered opaque factor value -> %d" % model_val)
        sys.exit(1)


discriminated = [False]
i = Symbol('i', integer=True, positive=True)
x = Symbol('x')
y = Symbol('y')
opaque = [i, x, y, i * x]

for q_int in [2, 3, 4, 5, 8, 12]:
    for v in [-10, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 8, 9, 16, 99]:
        check_integer_factor(v, q_int, discriminated)
    for obj in opaque:
        check_opaque_factor(obj, q_int)

# the issue's exact discriminators
check_integer_factor(3, 2, discriminated)   # Mod(3*i,2): 3 -> 1 (pre-patch keeps 3)
check_integer_factor(8, 4, discriminated)   # Mod(8*i,4): 8 -> 0 (pre-patch keeps 8)

rng = random.Random(1559900)
for _ in range(20000):
    q_int = rng.randint(2, 30)
    v = rng.randint(-5000, 5000)
    check_integer_factor(v, q_int, discriminated)

if not discriminated[0]:
    print("AXIOM check anomaly: pre-patch never differed from gold — discrimination not witnessed")
    sys.exit(1)
print("AXIOM-SOUND: reduced_factor == real patched per-factor rewrite over "
      "boundary integers + opaque symbols + 20000 fuzz factors; pre-patch "
      "no-reduction detectably wrong on nonzero-residue integer coefficients")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-residue-soundness",
        "axiom": "residue",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _RESIDUE_SOUNDNESS_PROBE,
        "rationale": (
            "residue (A-reference) models the UNCHANGED numeric primitive sympy "
            "Integer.__mod__ (i % q). Runs the REAL callee over boundary + "
            "sentinel + 50000 fuzz (value, m) pairs in the axiom's Requires "
            "domain m >= 2 and asserts the three Ensures (range, congruence, "
            "in-range idempotence) AND == the model encoding. If the real callee "
            "violates any Ensures -> AXIOM-UNSOUND. apply_gold=False: the callee "
            "is unchanged by the patch (it exists at base_commit), so the "
            "soundness check runs against the real sympy as G-AX does."
        ),
    },
    {
        "id": "ax-residue-containment",
        "axiom": "residue",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _RESIDUE_CONTAINMENT_PROBE,
        "rationale": (
            "residue's Requires domain is m >= 2 (value unconstrained int). The "
            "model calls residue only under Requires(m >= 2) — the caller's and "
            "reduced_factor's own preconditions — with an arbitrary int value, so "
            "every caller-reachable input is in domain. Confirms the real callee "
            "accepts every such input (any int value, any m >= 2) and returns an "
            "in-range int. A caller-reachable input outside the domain would be "
            "AXIOM-TOO-WEAK-FOR-CALLER; the callee actually accepts a wider domain "
            "(covering more is sound)."
        ),
    },
    {
        "id": "ax-reduced-factor-fidelity",
        "axiom": "reduced_factor",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _REDUCED_FACTOR_FIDELITY_PROBE,
        "rationale": (
            "reduced_factor is the A-reference deep model of the patched "
            "per-factor rewrite (integer factor i with i%q != 0 -> i%q, else "
            "unchanged). Runs the REAL rewrite on real sympy factors (integer "
            "constants across the residue boundary + opaque symbols i,x,y,i*x + "
            "20000 fuzz) and asserts reduced_factor == it, AND that the pre-patch "
            "no-reduction behaviour is detectably wrong on nonzero-residue integer "
            "coefficients. If reduced_factor disagreed with the real rewrite, the "
            "A-reference would be UNSOUND. apply_gold=False: the rewrite is "
            "re-expressed inline from the real callees (is_Integer, % ), which "
            "exist at base_commit — matching axiom_check.py's base-commit flow."
        ),
    },
]
