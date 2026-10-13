# properties.py — PBT falsification battery for sympy__sympy-13551.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we edit
# ONLY the text inside the single `# impl-start` / `# impl-end` block, so the
# frozen spec (axioms / pure / pre-/post-conditions, the function signature) is
# byte-identical to model.py and `markers.same_spec` holds by construction.
#
# Defended surface (from model.py / mapping.md / refinement.md):
#   product_of_sum(base: List[int], comp: List[int]) -> int
#     Requires Acc(list_pred(base), 1/2), Acc(list_pred(comp), 1/2)  ← READ-ONLY
#     Requires len(base) == len(comp)
#     Requires Forall i in range: base[i] + comp[i] != 0   ← DOMAIN BOUNDARY
#       (a vanishing multiplicand makes the real reduction exp(Sum(log(p)))
#        evaluate to the undefined exp(zoo), not the integer 0, so zero-total
#        inputs are outside the modeled domain — mapping.md §2)
#     Ensures  Acc(list_pred(base), 1/2), Acc(list_pred(comp), 1/2), len ==
#     Ensures  Result() == prod_of_totals(ToSeq(base), ToSeq(comp))   ← LOAD-BEARING
#
#   prod_of_totals is a @Pure FRONT-RECURSIVE fold over the ACTUAL inputs:
#     prod_of_totals = ∏_i (base[i] + comp[i])  (product of the per-index totals)
#   It is GROUNDED in the args (fully unfolded function of base/comp), NOT an
#   opaque answer-key. So there is no "wrong echo": echoing prod_of_totals IS the
#   correct answer (it doubles as the cheapest honest positive control). The
#   ungrounded-oracle-echo class is therefore N/A here — see 'assessment'.
#
#   The wrong pre-patch behaviour the change repairs is
#     prod_one(base) + prod_one(comp)   (the total of the two per-part products),
#   which the spec must REJECT (G-DIFF: model_prepatch.py fails exactly this).
#   On the F2P shape base=[1,1], comp=[2,4]: correct (1+2)*(1+4)=15, wrong
#   (1*1)+(2*4)=9  → the 15/2 vs 9/2 of issue 13546.
#
# Both list inputs are read-only (Acc(...,1/2)) ⇒ a FRAME-MUTATION reject case is
# MANDATORY (an impl that writes to base/comp must fail for INSUFFICIENT
# PERMISSION). prod_of_totals is grounded ⇒ no wrong-echo, positive control
# instead. CONTROL-FLOW-EFFECT: N/A — the function neither raises nor has a side
# effect the value abstraction hides (pure integer reduction over read-only
# lists); see 'assessment'.
#
# The bundle has NO @ContractOnly consumed axiom (axioms region is empty;
# prod_of_totals is a deep A-reference validated out-of-band by axiom_check.py /
# G-AX). The axiom lane is therefore exercised as one A-reference soundness +
# one caller-domain containment probe that RUN THE REAL sympy callee in Docker.

from pathlib import Path

INSTANCE = "sympy__sympy-13551"
FLOAT_ENCODING = None  # meta.json float_encoding is null (exact integer arithmetic)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: anchor not found: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen gold impl BODY (the text strictly between # impl-start / # impl-end).
# Every variant is produced by _swap-ing this single unique block for a new body.
# Editing only here keeps the spec view (and thus same_spec) untouched.
# ---------------------------------------------------------------------------
_GOLD_BODY = """    result = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result"""


def _variant(body):
    """Replace ONLY the gold impl body; spec view is preserved verbatim."""
    return _swap(_BASE, _GOLD_BODY, body)


# ===========================================================================
# POSITIVE CONTROL 1 (soundness) — honest cheapest impl.
# prod_of_totals is grounded in the args, so directly returning it IS correct.
# A correct impl MUST verify; if it cannot, the postcondition is SPEC-TOO-STRONG.
# ===========================================================================
_POS_CHEAPEST = """    return prod_of_totals(ToSeq(base), ToSeq(comp))"""


# ===========================================================================
# POSITIVE CONTROL 2 (soundness) — structurally-different but CORRECT.
# Keeps the BACKWARD loop direction (do NOT flip to forward-append: that needs
# an f(a+b)==f(a)+f(b) lemma the verifier won't auto-discharge against a
# front-recursive fold — pilot bug #3). Reshape only: bind the per-index total
# to a local `t`, COMMUTE the multiplication (result * t instead of t * result),
# and KEEP every gold framing Assert that the loop invariant still needs.
# ===========================================================================
_POS_RESHAPE = """    result = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        t = base[i - 1] + comp[i - 1]
        result = result * t
        i = i - 1
    return result"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input and is non-vacuous on both the empty base case and a general step. We
# keep the gold impl verbatim and add entry Asserts that exercise the contract's
# own grounded oracle on the reachable shapes (empty product == 1; the recursive
# unfold is available). If the gold proof still goes through, the Requires
# accepts a legitimate input (else PRECOND-TOO-STRONG). The added Asserts live
# strictly inside the impl region.
# ===========================================================================
_ADMISS = """    # admissibility witnesses (impl-region only): the precondition is
    # non-vacuous — it admits the empty shape and a general non-empty shape.
    Assert(Implies(len(base) == 0,
                   prod_of_totals(ToSeq(base), ToSeq(comp)) == 1))
    Assert(len(base) == len(comp))
    Assert(0 <= len(base))
    result = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result"""


# ===========================================================================
# FRAME-MUTATION (uniqueness, reject) — MANDATORY: both inputs are read-only
# (Acc(...,1/2)). This rival tries to satisfy the postcondition by WRITING into
# the read-only input `base`. Even though it then recomputes the correct value
# via the gold loop, the write itself requires FULL permission on list_pred(base)
# which the precondition does not grant (only 1/2). It must be REJECTED for
# INSUFFICIENT PERMISSION — not because the value is wrong. We keep all gold
# invariants/asserts verbatim so the rejection is attributable solely to the
# write. (A byte-fuzzer never thinks to mutate the input — project #1 class.)
# ===========================================================================
_FRAME_MUT = """    # ATTACK: write into the read-only input `base` (only Acc(...,1/2) held).
    # This must be rejected for insufficient permission to list_pred(base).
    base[0] = base[0]
    result = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result"""


# ===========================================================================
# UNIQUENESS — sum-of-part-products (the EXACT pre-patch bug). This is the
# wrong "product of a sum == sum of the part-products" reduction the gold patch
# repairs (prod_one(base) + prod_one(comp)). It is value-correct on a measure-
# zero set (any input where ∏(b+c) happens to equal ∏b+∏c, e.g. all-zero or
# single-element lists) but DIVERGES on the F2P shape (15 vs 9). The spec must
# reject it: it cannot satisfy Result() == prod_of_totals(...). This is the same
# impl as model_prepatch.py (G-DIFF already confirms it fails the postcondition).
# ===========================================================================
_UNIQ_SUMPARTS = """    pb = 1
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= i and i <= len(base))
        Invariant(pb == prod_one(ToSeq(base).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        pb = base[i - 1] * pb
        i = i - 1
    pc = 1
    j = len(comp)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(0 <= j and j <= len(comp))
        Invariant(pc == prod_one(ToSeq(comp).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(comp).drop(j - 1)[0] == comp[j - 1])
        Assert(ToSeq(comp).drop(j - 1).drop(1) == ToSeq(comp).drop(j))
        pc = comp[j - 1] * pc
        j = j - 1
    result = pb + pc
    return result"""


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness, reject) — correct on the EMPTY input only.
# Returns the empty product (1) unconditionally. For len==0 this is the right
# answer (prod_of_totals over empty == 1), so it agrees with the spec on the
# empty sub-domain; but for every non-empty F2P/P2P input it is wrong (e.g.
# the F2P shape needs 15, not 1). The spec must reject it: Result()==1 cannot
# satisfy Result()==prod_of_totals(...) for non-empty inputs.
# ===========================================================================
_PARTIAL_EMPTY = """    one = 1
    return one"""


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness, reject) — drop the FIRST index (index 0).
# Computes ∏_{i>=1}(base[i]+comp[i]) by stopping the backward loop at i==1
# instead of i==0, i.e. it never multiplies in the per-index total at index 0.
# Correct only when the first total is 1 (a sub-domain); wrong on the F2P shape
# (drops the (1+2)=3 factor → 5 instead of 15). The spec must reject: the final
# `result` equals prod_of_totals(ToSeq(base).drop(1), ToSeq(comp).drop(1)),
# which ≠ prod_of_totals(ToSeq(base), ToSeq(comp)) in general.
# ===========================================================================
_PARTIAL_DROPFIRST = """    result = 1
    i = len(base)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(comp), 1 / 2))
        Invariant(len(base) == len(comp))
        Invariant(1 <= i and i <= len(base))
        Invariant(result == prod_of_totals(ToSeq(base).drop(i),
                                           ToSeq(comp).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(base).drop(i - 1)[0] == base[i - 1])
        Assert(ToSeq(comp).drop(i - 1)[0] == comp[i - 1])
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        Assert(ToSeq(comp).drop(i - 1).drop(1) == ToSeq(comp).drop(i))
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_CHEAPEST),
        "rationale": "prod_of_totals is GROUNDED in the args (a fully-unfolded "
                     "@Pure fold over base/comp), so returning it directly is "
                     "the correct value. An honest cheapest impl MUST verify; "
                     "if it cannot the postcondition is SPEC-TOO-STRONG. (This "
                     "also serves as the grounded-oracle positive control: there "
                     "is no WRONG echo because the oracle is a function of the "
                     "inputs, not an opaque answer-key.)",
    },
    {
        "id": "pos-reshape-commute",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_RESHAPE),
        "rationale": "structurally-different CORRECT impl: same backward loop "
                     "(NOT flipped — avoids the f(a+b) lemma gap of pilot bug "
                     "#3), but the per-index total is bound to a local `t` and "
                     "the multiplication is COMMUTED (result*t). All gold "
                     "framing Asserts are kept so the loop invariant still holds "
                     "for a proof reason. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-fshape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "the Requires (two read-only equal-length lists) is a "
                     "standard, easily-satisfiable precondition; entry Asserts "
                     "exercise the grounded oracle on the empty and general "
                     "shapes and the gold proof still discharges, so the "
                     "precondition admits a normal F2P-shaped input (else "
                     "PRECOND-TOO-STRONG).",
    },
    {
        "id": "frame-mutate-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUT),
        "refinement": "A faithful real patch that WRITES into the multiplicand "
                      "parts would mutate sympy's input Add term in place — the "
                      "gold patch reads `p`/`p.as_coeff_Add()` and never mutates "
                      "the term, so an in-place-mutating variant is not the gold "
                      "behaviour and would corrupt the shared expression; it "
                      "would not faithfully resolve test_issue_13546. The write "
                      "is a pure artifact of cheating the proof.",
        "rationale": "REJECTION SOURCE = permission system. base is held with "
                     "only Acc(list_pred(base), 1/2); `base[0] = base[0]` needs "
                     "FULL write permission to list_pred(base), which the "
                     "precondition does not grant. Must fail for insufficient "
                     "permission, NOT for a wrong value (the gold loop still "
                     "computes the correct result). This is the project's #1 "
                     "weakness class for read-only inputs.",
    },
    {
        "id": "uniq-sum-of-part-products",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_UNIQ_SUMPARTS),
        "refinement": "This is verbatim the PRE-PATCH sympy behaviour "
                      "`sum([_eval_product(part) for part in p.as_coeff_Add()])` "
                      "= prod_one(base) + prod_one(comp). The gold patch exists "
                      "precisely to replace it; a patch shaped like this is the "
                      "bug, not the fix — it produces 9/2 (not 15/2) on the F2P "
                      "input and FAILS test_issue_13546 (G-DIFF: model_prepatch "
                      "is exactly this impl and fails the postcondition).",
        "rationale": "REJECTION SOURCE = postcondition clause "
                     "Result()==prod_of_totals(ToSeq(base),ToSeq(comp)). The "
                     "loops establish result==prod_one(base)+prod_one(comp), "
                     "which differs from the product of the per-index totals on "
                     "the F2P shape (9 vs 15), so the Ensures cannot be proven.",
    },
    {
        "id": "partial-domain-empty-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_EMPTY),
        "refinement": "A real patch that returns the empty product (1) "
                      "regardless of the multiplicand would make every finite "
                      "Product of a non-polynomial Add evaluate to 1 — exactly "
                      "the nonsense the hints_text calls out (product of "
                      "k**(2/3)+1 collapsing to 1). It resolves nothing: F2P "
                      "needs 15/2, this gives 1/2 (1 over the q denominator).",
        "rationale": "REJECTION SOURCE = postcondition. Result()==1 satisfies "
                     "the Ensures only on the empty sub-domain (prod over [] is "
                     "1); for any non-empty input prod_of_totals(...) != 1 in "
                     "general (F2P: 15), so the Ensures is unprovable. Correct "
                     "on a strict sub-domain, wrong on the rest.",
    },
    {
        "id": "partial-domain-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_DROPFIRST),
        "refinement": "A real patch that skips the first index of the range "
                      "(k==a) computes ∏_{k=a+1}^{n} p instead of ∏_{k=a}^{n} p "
                      "— it drops one factor. On the F2P shape it omits the "
                      "(2+2**0)=3 factor at k=0, giving 5 not 15, so "
                      "test_issue_13546 fails. It is correct only when the first "
                      "total is 1 (a measure-zero sub-domain).",
        "rationale": "REJECTION SOURCE = postcondition + loop bound. Stopping "
                     "the backward loop at i==1 leaves "
                     "result==prod_of_totals(ToSeq(base).drop(1), "
                     "ToSeq(comp).drop(1)), which omits index 0's total and so "
                     "!= prod_of_totals(ToSeq(base),ToSeq(comp)) in general; the "
                     "Ensures cannot be discharged.",
    },
]


# ===========================================================================
# AXIOM LANE — there is NO @ContractOnly consumed axiom (meta.axioms == []).
# prod_of_totals is a deep A-REFERENCE: the model's spelled-out @Pure fold that
# must equal the real fixed sympy callee exp(Sum(log(p),(k,a,n))) on every
# caller-reachable input. We exercise it as:
#   (1) ax-ref-soundness  — run the REAL callee Product(p,(k,0,n-1)).doit() /
#       exp(Sum(log(p))) under the branch config that actually fires (non-poly
#       Add, symbolic limits — flag_dependency / provenance from meta) and assert
#       it equals prod_of_totals on fuzzed inputs INCLUDING the F2P shape; and
#       that the pre-patch sum-of-part-products differs (the discriminator). If
#       the real callee disagrees ⇒ AXIOM-UNSOUND.
#   (2) ax-ref-containment — assert every callee-input the MODEL can reach lies
#       inside the A-reference's domain (len(base)==len(comp)>=0, integer-valued
#       NONZERO per-index totals base[i]+comp[i] — the Requires excludes zero
#       totals, on which the real callee is undefined exp(zoo)); a reachable
#       input outside that domain ⇒ AXIOM-TOO-WEAK-FOR-CALLER.
# Both probes CALL the real sympy routine (never scrape source), open files with
# encoding="utf-8", and embed the HOST-side axiom_check oracle source so the
# runner's single mounted probe script is self-contained (pilot bugs #4,#5,#6).
# ===========================================================================

# Embed the host bundle's validated oracle (axiom_check.py) into each probe so
# the in-container probe is self-contained (the runner mounts ONLY the probe).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


_PROBE_SOUNDNESS = '''\
import random, sys
# real sympy callee (the repo under test inside the instance image)
from sympy import Symbol, Product, Sum, exp, log, zoo, Integer, sympify


def prod_of_totals(base, comp):
    # deep-model reference (lock-step with model.py): product of per-index totals
    assert len(base) == len(comp)
    out = 1
    for bi, ci in zip(base, comp):
        out *= (bi + ci)
    return out


def prod_one(xs):
    out = 1
    for x in xs:
        out *= x
    return out


def has_zero_total(d, c, N):
    # the domain boundary model.py's Requires excludes (zero per-index total)
    return any(d + c * (2 ** i) == 0 for i in range(N))


def real_doit_symbolic(p_fn):
    k = Symbol("k"); n = Symbol("n")
    return Product(p_fn(k), (k, 0, n - 1)).doit(), n


def check(part_const, part_exp_coeff, N, label):
    assert part_const != 0  # d=0 makes p a pure power, not an Add
    assert not has_zero_total(part_const, part_exp_coeff, N)  # Requires domain
    k = Symbol("k")
    p_fn = lambda kk: part_const + part_exp_coeff * 2 ** kk
    doit_expr, n = real_doit_symbolic(p_fn)
    # (a) the patched is_Add / q.is_Number branch must actually have fired
    assert doit_expr.has(exp) and doit_expr.has(Sum) and doit_expr.has(log), (
        "patched is_Add branch did not fire for %s: doit=%s" % (label, doit_expr))
    real_val = doit_expr.subs(n, N).doit()
    base = [part_const for _ in range(N)]
    comp = [part_exp_coeff * (2 ** i) for i in range(N)]
    model_val = prod_of_totals(base, comp)
    real_exp = exp(Sum(log(p_fn(k)), (k, 0, N - 1))).doit()
    assert Integer(model_val) == sympify(real_val), (
        "A-reference UNSOUND (%s,N=%d): deep model=%s real Product.doit=%s"
        % (label, N, model_val, real_val))
    assert Integer(model_val) == sympify(real_exp), (
        "A-reference UNSOUND (%s,N=%d): deep model=%s real exp(Sum(log))=%s"
        % (label, N, model_val, real_exp))
    return model_val, prod_one(base) + prod_one(comp)


def main():
    cases = [
        ("F2P 1+2*2^k", 1, 2), ("F2P 1+3*2^k", 1, 3), ("F2P 1+5*2^k", 1, 5),
        ("2+1*2^k", 2, 1), ("3+4*2^k", 3, 4), ("1+1*2^k", 1, 1), ("7+2*2^k", 7, 2),
        ("-3+1*2^k", -3, 1), ("-9+2*2^k", -9, 2), ("-5+3*2^k", -5, 3),
    ]
    checked = 0; disc = 0
    for label, d, c in cases:
        for N in range(1, 7):
            if has_zero_total(d, c, N):
                continue  # outside the modeled domain (Requires)
            mv, bv = check(d, c, N, label); checked += 1
            if N >= 2 and mv != bv: disc += 1
    # fuzz spans NEGATIVE and positive constant parts; d == 0 excluded (pure
    # power, branch cannot fire); zero-total draws excluded (Requires domain).
    rng = random.Random(13551)
    for _ in range(300):
        d = rng.randint(-9, 9); c = rng.randint(1, 9); N = rng.randint(1, 6)
        if d == 0 or has_zero_total(d, c, N):
            continue
        mv, bv = check(d, c, N, "fuzz"); checked += 1
        if N >= 2 and mv != bv: disc += 1
    assert disc > 0, "no discriminating witness — the bug would be invisible"
    # explicit F2P-of-the-issue cross-check: base=[1,1], comp=[2,4] -> 15, bug 9
    assert prod_of_totals([1, 1], [2, 4]) == 15
    assert prod_one([1, 1]) + prod_one([2, 4]) == 9
    # domain-boundary confirmation: on a zero-total input (excluded by the
    # Requires) the real callee is the undefined exp(zoo), NOT the integer 0 —
    # exactly why model.py's precondition excludes such inputs.
    k = Symbol("k"); n = Symbol("n"); nb = 0
    for d, c, N in ((-1, 1, 1), (-1, 1, 4), (-2, 1, 4), (-4, 1, 3)):
        assert has_zero_total(d, c, N)
        p = d + c * 2 ** k
        direct = exp(Sum(log(p), (k, 0, N - 1))).doit()
        assert direct.has(zoo), (d, c, N, direct)
        routed = Product(p, (k, 0, n - 1)).doit().subs(n, N).doit()
        assert routed.has(zoo), (d, c, N, routed)
        nb += 1
    print("ax-ref-soundness OK: deep model prod_of_totals == real "
          "exp(Sum(log(p)))/Product.doit on %d in-domain inputs (incl. "
          "negative totals; patched is_Add branch fired); pre-patch "
          "sum-of-part-products differs on %d of them; F2P 15 vs 9 confirmed; "
          "%d zero-total boundary inputs confirmed undefined exp(zoo), "
          "matching the Requires exclusion." % (checked, disc, nb))
    return 0


sys.exit(main())
'''


_PROBE_CONTAINMENT = '''\
import sys
from sympy import Symbol, Product, Sum, exp, log

# The A-reference prod_of_totals(base, comp) requires:
#   len(base) == len(comp)  and the per-index total base[i]+comp[i] is a value
#   the real callee exp(Sum(log(p),(k,a,n))) accepts (an integer-valued
#   multiplicand evaluated over a finite index range). The MODEL can only reach
#   inputs with len(base)==len(comp)>=0 and every per-index total NONZERO (its
#   Requires — a zero total makes the real callee the undefined exp(zoo), so
#   such inputs are outside the modeled domain) with integer per-index totals
#   (base[i],comp[i] are int). We confirm every such reachable input lies
#   inside the callee's domain — i.e. the real callee EVALUATES (the is_Add /
#   q.is_Number branch fires and produces a finite value) for the shapes the
#   model can produce, including the empty range and the F2P shape. All probe
#   shapes below have nonzero per-index totals.

k = Symbol("k"); n = Symbol("n")
checked = 0
# (1) empty range (len 0): model's empty product is 1; callee over an empty
#     range must also evaluate (vacuous product == 1).
for N in range(0, 7):
    # F2P-shape multiplicand: constant part + exponential part (non-poly Add)
    p_fn = lambda kk: 1 + 2 ** kk
    if N == 0:
        # empty range a..n with n = a-1: Product(p,(k,0,-1)) — must be defined
        val = Product(p_fn(k), (k, 0, -1)).doit()
        assert val == 1, "callee not defined on empty range: %s" % val
    else:
        sym = Product(p_fn(k), (k, 0, n - 1)).doit()
        assert sym.has(exp) and sym.has(Sum) and sym.has(log), (
            "callee branch did not fire for reachable len=%d" % N)
        val = sym.subs(n, N).doit()
        assert val.is_number, "callee produced non-numeric for len=%d: %s" % (N, val)
    checked += 1

# (2) integer-valued per-index totals across a spread of magnitudes/signs the
#     model's int lists can hold — the callee must accept each (no domain gap).
for d in (-3, 0, 1, 7):
    for c in (1, 2, 5):
        p_fn = lambda kk: d + c * 2 ** kk
        sym = Product(p_fn(k), (k, 0, n - 1)).doit()
        # the branch fires for the non-poly exponential Add; value is finite at N
        v = sym.subs(n, 3).doit()
        assert v.is_number, "callee non-numeric for (d=%d,c=%d): %s" % (d, c, v)
        checked += 1

# Covering MORE than the caller reaches (e.g. non-integer or infinite ranges)
# would be SOUND, not a defect; we only assert containment of the REACHABLE set.
print("ax-ref-containment OK: every caller-reachable input "
      "(len(base)==len(comp)>=0, integer per-index totals) lies in the "
      "A-reference callee domain; %d shapes evaluated." % checked)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-ref-soundness",
        "axiom": "prod_of_totals",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "A-reference soundness: runs the REAL sympy callee "
                     "Product(p,(k,0,n-1)).doit() / exp(Sum(log(p))) under the "
                     "branch config that fires (non-polynomial Add + symbolic "
                     "limits — provenance/flag_dependency from meta) on the F2P "
                     "shape + 300 fuzz inputs and asserts it equals the deep "
                     "model prod_of_totals on each; also that the pre-patch "
                     "sum-of-part-products differs (the discriminator F2P "
                     "observes, 15 vs 9). Any disagreement ⇒ AXIOM-UNSOUND. "
                     "Mirrors the bundle's axiom_check.py (G-AX) logic.",
    },
    {
        "id": "ax-ref-containment",
        "axiom": "prod_of_totals",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "Caller-domain containment: every input the MODEL can reach "
                     "(len(base)==len(comp)>=0 per its Requires; integer "
                     "per-index totals base[i]+comp[i]) lies inside the "
                     "A-reference callee's domain — the real callee evaluates "
                     "(branch fires, finite value) on the empty range and on a "
                     "spread of integer multiplicands. A reachable input OUTSIDE "
                     "the covered domain ⇒ AXIOM-TOO-WEAK-FOR-CALLER. (Covering "
                     "more than the caller reaches would be sound, not a defect.)",
    },
]
