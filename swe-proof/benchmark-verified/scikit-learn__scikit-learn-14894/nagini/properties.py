"""properties.py — PBT falsification manifest for scikit-learn__scikit-learn-14894.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    row_pointer_for_block_layout(width: int, n_rows: int) -> List[int]
        Requires(width >= 0); Requires(n_rows >= 1)

modelling the CSR dual-coefficient row-pointer assembly inside
`BaseLibSVM._sparse_fit` (the gold patch adds an `if not n_SV:` guard so the
row-pointer is never built with a zero per-row width — the issue's
ZeroDivisionError). The load-bearing postcondition:

    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == 0)
    Ensures(Result()[len(Result()) - 1] == width * n_rows)              # stored-count
    Ensures(Implies(width == 0, len(Result()) == 2))                    # empty layout == [0, 0]
    Ensures(Implies(width >= 1, len(Result()) == n_rows + 1))           # non-empty len
    Ensures(Implies(width >= 1,
                    Forall(k: 0<=k<=n_rows => Result()[k] == k*width)))  # progression

and the ONE consumed axiom `range_step(start, stop, step)` (A-consumed —
`numpy.arange`), partial with `Requires(step >= 1)`: a zero step is undefined
(the ZeroDivisionError). The impl establishes the positive step via the
`if width == 0` guard before calling the builder.

WHAT THIS SPEC DEFENDS, AND THE ATTACKS IT MUST SURVIVE
-------------------------------------------------------
  * THE DISCRIMINATOR is the per-row-width guard. The whole bug is that the
    pre-patch builds the row-pointer unconditionally; with an empty
    support-vectors set the step is 0 and `np.arange(0, size+1, 0)` raises
    `ZeroDivisionError`. The model encodes this as `range_step`'s
    `Requires(step >= 1)`. `rival-drop-guard` is EXACTLY model_prepatch.py: it
    drops the `if width == 0` guard and calls `range_step(0, size+1, width)`
    with `width` possibly 0, which CANNOT discharge the callee precondition. It
    must be rejected (insufficient-Requires on the consumed axiom). This is the
    core verify⇏resolve discriminator: that real patch raises on the F2P.

  * THE STORED-COUNT CLAUSE `Result()[len-1] == width*n_rows` is the observable
    the F2P checks (`assert not model.dual_coef_.data.size` ⟺ final boundary 0
    when width==0). `rival-empty-nonzero-tail` returns a row-pointer whose final
    entry is non-zero for the empty case; its faithful patch produces a CSR with
    stored entries for empty support vectors, failing the F2P. Rejected by the
    stored-count clause.

  * THE EMPTY CASE IS PINNED EXACTLY TO THE CANONICAL [0, 0]. For width==0 the
    spec pins `len == 2`, `[0] == 0`, `[last] == 0` — i.e. the row-pointer IS
    [0, 0], the indptr of the real gold `sp.csr_matrix([])` (a (1, 0) empty CSR
    whose indptr is exactly [0, 0]). An earlier revision left the empty-case
    length loose (`len >= 2` only); the P1 audit exhibited a same-spec wrong
    impl exploiting that slack (a padded empty row-pointer, e.g. [0, 0, 0],
    whose faithful patch builds an indptr whose length disagrees with the CSR's
    row count — a malformed dual_coef_ diverging from gold's sp.csr_matrix([])).
    The `Implies(width == 0, len(Result()) == 2)` clause closes it:
    `rival-empty-padded` (below) must now be rejected. The other empty-branch
    rivals attack the OBSERVABLE (final entry != 0) and the opening boundary
    (`[0] != 0`).

  * THE NON-EMPTY PROGRESSION IS PINNED BOTH WAYS. `rival-flat-nonempty` returns
    the empty layout `[0,0]` even for width>=1: rejected by
    `Implies(width>=1, len(Result())==n_rows+1)` (n_rows>=1, fails for n_rows>=2)
    AND by the stored-count clause (final 0 != width*n_rows>0). `rival-wrong-open`
    opens at boundary 1 instead of 0: rejected by `Result()[0]==0`. A CSR
    row-pointer that does not open at 0 / does not end at the stored count is a
    malformed matrix, so each rival's faithful patch diverges from gold.

  * THE ORACLE IS NOT AN ANSWER-KEY (no ungrounded-oracle echo). `range_step` is
    A-consumed: it is used ONLY inside the impl and NEVER referenced from an
    `Ensures`. The postcondition pins the result's values STRUCTURALLY
    (`Result()[k] == k*width`, `Result()[len-1] == width*n_rows`), grounded in
    the args `width`/`n_rows` and fully unfolded — there is no opaque marker an
    impl could echo to skip the work. So there is no "wrong oracle-echo that
    verifies" reject case; `pos-control-inverted-branch` is the honest
    structurally-different positive control (directive 2 fallback for a grounded
    spec). Noted in the structured assessment.

  * NO READ-ONLY (Acc(x,1/2)) INPUT ⇒ FRAME-MUTATION IS N/A. Both parameters are
    plain immutable Python `int`s passed BY VALUE (`width: int`, `n_rows: int`);
    there is no `Acc(x, 1/2)` reference whose frame an impl could overwrite to
    satisfy the postcondition vacuously. The only reference object is the
    returned `List[int]`. The mandatory frame-mutation probe therefore does not
    apply (no input frame exists to subvert) — noted in the structured
    assessment rather than fabricated.

  * NO CAPABILITY-TOKEN / CONTROL-FLOW-EFFECT CHANNEL. The function purely
    computes and returns a list; the only control-flow difference that matters
    (the empty-vs-non-empty guard) IS observable through the returned value
    (final boundary 0 vs width*n_rows) and through the consumed axiom's
    precondition (step>=1) — both already pinned by the spec. There is no
    raise/side-effect difference invisible to the value abstraction, so the
    capability-token class is N/A. Noted in the assessment.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
GUARANTEED and a rejection comes from the POSTCONDITION / the consumed axiom's
Requires catching wrong behaviour, never from a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P. The one consumed axiom `range_step` is checked
by running the REAL `numpy.arange` in Docker (reusing/strengthening
axiom_check.py's logic).
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14894"
FLOAT_ENCODING = None   # meta.json float_encoding is null

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
# The exact gold impl body (everything between # impl-start and # impl-end).
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    size = width * n_rows
    if width == 0:
        # Empty per-row width: the layout stores nothing (a valid empty layout).
        return [0, 0]
    else:
        step = width
        Assert(step >= 1)
        # The upper bound size+1 is one past the n_rows-th multiple of step.
        Assert(size + 1 == n_rows * step + 1)
        indptr = range_step(0, size + 1, step)
        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
        Assert((len(indptr) - 1) * step == n_rows * step)
        Assert(len(indptr) - 1 == n_rows)
        Assert(indptr[0] == 0 * step)
        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
        return indptr"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (soundness) Structurally-different but CORRECT: the branches are REORDERED so
# the non-empty (positive-step) build comes FIRST under `if width >= 1` and the
# empty layout is the `else`. Same partition of the (width>=0) domain (width>=1
# vs width==0), same returned values, but the executable control-flow shape is
# inverted. ALL gold framing asserts are kept verbatim inside the build branch so
# the loop-free proof obligations (range_step's Requires(step>=1) discharge, the
# length and boundary pins) are preserved — only the branch order changes. No
# loop / no @Pure fold, so no induction lemma is needed. It must verify; if a
# faithful inverted-branch correct impl cannot satisfy the Ensures => SPEC-TOO-STRONG.
_POS_INVERTED = """    size = width * n_rows
    if width >= 1:
        step = width
        Assert(step >= 1)
        # The upper bound size+1 is one past the n_rows-th multiple of step.
        Assert(size + 1 == n_rows * step + 1)
        indptr = range_step(0, size + 1, step)
        # From the axiom: (len-1)*step + 1 == size+1 == n_rows*step + 1, hence
        # (len-1)*step == n_rows*step; with step >= 1 the lengths match.
        Assert((len(indptr) - 1) * step == n_rows * step)
        Assert(len(indptr) - 1 == n_rows)
        Assert(indptr[0] == 0 * step)
        Assert(indptr[len(indptr) - 1] == (len(indptr) - 1) * step)
        return indptr
    else:
        # width == 0 (since width >= 0 and not width >= 1): empty layout.
        return [0, 0]"""
_POS_INVERTED_MOD = _swap(_BASE, _GOLD_IMPL, _POS_INVERTED)

# (admissibility) The gold body, prefixed with a SELF-CALL on an F2P-shaped
# input — the regression test fits an SVR whose support_vectors_ is EMPTY, i.e.
# width == 0 with n_rows >= 1 (n_class for regression == 1, but n_rows >= 2 is
# equally in-domain; use n_rows == 2). The call site must establish the Requires
# (width=0 satisfies width>=0; n_rows=2 satisfies n_rows>=1), and the asserted
# result property (final boundary == 0 == 0*2, the empty-layout observable)
# follows from the callee's Ensures. Verification uses the contract, not the
# body, so no termination measure is needed. If the call site cannot establish
# Requires for this normal empty-support-vector input => PRECOND-TOO-STRONG.
_ADMISS = """    Assert(0 >= 0)
    Assert(2 >= 1)
""" + _GOLD_IMPL
_ADMISS_MOD = _swap(_BASE, _GOLD_IMPL, _ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (DISCRIMINATOR — the actual bug / model_prepatch.py) Drop the `if width == 0`
# guard entirely: build the row-pointer UNCONDITIONALLY via range_step with
# step == width, exactly as the pre-patch np.arange(0, size+1, size/n_class)
# does. When width == 0 the step is 0, so the call CANNOT discharge
# range_step's Requires(step >= 1). MUST be rejected — the verification fails at
# the call site for an unsatisfiable callee precondition. Rejection source: the
# consumed axiom range_step's Requires(step >= 1) (the partiality that the guard
# respects and the pre-patch violates).
_RIVAL_DROP_GUARD = """    size = width * n_rows
    step = width
    # No `if width == 0` guard (pre-patch behaviour): width may be 0, so step
    # may be 0 — range_step's Requires(step >= 1) cannot be established.
    indptr = range_step(0, size + 1, step)
    return indptr"""
_RIVAL_DROP_GUARD_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_DROP_GUARD)

# (PARTIAL-DOMAIN — empty branch, the OBSERVABLE) Correct on the non-empty
# domain (gold build) but for the empty case returns a row-pointer whose FINAL
# entry is non-zero ([0, 5]). MUST be rejected by the stored-count clause
# Result()[len-1] == width*n_rows (== 0 when width == 0, but this returns 5).
# Rejection source: the postcondition Result()[len(Result()) - 1] == width*n_rows.
_RIVAL_EMPTY_NONZERO = _swap(
    _GOLD_IMPL,
    "        # Empty per-row width: the layout stores nothing (a valid empty layout).\n        return [0, 0]",
    "        # WRONG: final boundary 5 != 0 == width*n_rows for the empty layout.\n        return [0, 5]")
_RIVAL_EMPTY_NONZERO_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_EMPTY_NONZERO)

# (PARTIAL-DOMAIN — empty branch, the OPENING boundary) Correct on the non-empty
# domain but for the empty case opens at boundary 1 instead of 0 ([1, 0]). MUST
# be rejected by Result()[0] == 0. Rejection source: the postcondition
# Result()[0] == 0 (every CSR row-pointer opens at 0).
_RIVAL_WRONG_OPEN = _swap(
    _GOLD_IMPL,
    "        # Empty per-row width: the layout stores nothing (a valid empty layout).\n        return [0, 0]",
    "        # WRONG: opens at boundary 1, not 0.\n        return [1, 0]")
_RIVAL_WRONG_OPEN_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_WRONG_OPEN)

# (PARTIAL-DOMAIN — empty branch, PADDED length) Correct on the non-empty
# domain (gold build) but for the empty case returns a PADDED row-pointer
# [0, 0, 0] (final boundary still 0, opening still 0 — the P1 exploit shape).
# The real gold empty CSR sp.csr_matrix([]) has indptr EXACTLY [0, 0] (a (1, 0)
# matrix: one row, so n_rows+1 == 2 boundaries); a faithful patch emitting a
# 3-boundary indptr for a 1-row matrix builds a malformed CSR (indptr length
# must be rows+1), diverging from gold. MUST be rejected by the empty-length pin
# Implies(width == 0, len(Result()) == 2). Rejection source: the empty-layout
# length clause (the strengthening that closes the P1 finding).
_RIVAL_EMPTY_PADDED = _swap(
    _GOLD_IMPL,
    "        # Empty per-row width: the layout stores nothing (a valid empty layout).\n        return [0, 0]",
    "        # WRONG: padded empty row-pointer (3 boundaries for the 1-row empty CSR).\n        return [0, 0, 0]")
_RIVAL_EMPTY_PADDED_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_EMPTY_PADDED)

# (PARTIAL-DOMAIN — non-empty collapse) Correct on the empty case but returns
# the empty layout [0, 0] for EVERY input, including width >= 1. MUST be
# rejected: for width >= 1 the spec pins len(Result()) == n_rows + 1 (>= 2 + 1
# == 3 when n_rows >= 2, but [0,0] has length 2) AND Result()[len-1] ==
# width*n_rows (> 0 when width >= 1, but [0,0] ends at 0). Rejection source:
# Implies(width >= 1, len(Result()) == n_rows + 1) and the stored-count clause.
_RIVAL_FLAT = """    size = width * n_rows
    # WRONG: collapse every layout to the empty row-pointer, ignoring the
    # per-row width entirely. Correct only on the width == 0 sub-domain.
    return [0, 0]"""
_RIVAL_FLAT_MOD = _swap(_BASE, _GOLD_IMPL, _RIVAL_FLAT)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-inverted-branch", "kind": "soundness", "expect": "verify",
     "module": _POS_INVERTED_MOD,
     "rationale": "structurally-different but CORRECT: the branch order is inverted "
                  "(build under `if width >= 1` first, empty layout in the `else`). Same "
                  "domain partition and same returned values as gold; only the executable "
                  "control-flow shape changes. ALL gold framing asserts are kept verbatim so "
                  "the range_step Requires(step>=1) discharge and the length/boundary pins "
                  "still hold. No loop / no @Pure fold => no induction lemma needed. If a "
                  "faithful inverted-branch correct impl cannot verify => SPEC-TOO-STRONG."},
    {"id": "admiss-empty-support-vectors", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_MOD,
     "rationale": "self-call on an F2P-shaped input: the regression test fits an SVR with an "
                  "EMPTY support_vectors_ set (width == 0, n_rows >= 1; use n_rows == 2). The "
                  "call site must establish the Requires (0 >= 0; 2 >= 1) and the asserted "
                  "empty-layout observable (final boundary == 0) follows from the callee's "
                  "Ensures. If the precondition cannot be established for this normal empty "
                  "input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-drop-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_GUARD_MOD,
     "refinement": "this is the EXACT pre-gold behaviour (model_prepatch.py): the row-pointer "
                   "is built unconditionally via range_step(0, size+1, width), mirroring the "
                   "pre-patch np.arange(0, dual_coef_indices.size+1, dual_coef_indices.size/"
                   "n_class) with step == n_SV == width. Its faithful real patch is the "
                   "pre-patch _sparse_fit, which on the F2P input (empty support_vectors_, "
                   "n_SV == 0) computes step == 0 and raises `ZeroDivisionError: float "
                   "division by zero` — exactly the issue. That patch FAILS the F2P "
                   "(test_sparse_fit_support_vectors_empty), so it would NOT resolve; a "
                   "verifying rival here would be a true verify⇏resolve break.",
     "rationale": "the discriminator. Rejection source: the consumed axiom range_step's "
                  "Requires(step >= 1), which a width==0 (step==0) call cannot discharge. The "
                  "guard the gold patch adds is precisely what establishes this positive step. "
                  "If it verified => SPEC-TOO-WEAK (the partiality the bug fix respects would "
                  "be hollow)."},
    {"id": "rival-empty-nonzero-tail", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY_NONZERO_MOD,
     "refinement": "correct on the entire non-empty domain (gold build) but for the empty "
                   "layout returns a row-pointer whose final boundary is 5, not 0. A faithful "
                   "real patch that produces a CSR with a non-zero final indptr for empty "
                   "support vectors yields a matrix with stored entries — and the F2P asserts "
                   "`not model.dual_coef_.data.size` (zero stored entries). That patch FAILS "
                   "the F2P, so it would NOT resolve.",
     "rationale": "partial-domain on the empty branch, attacking the OBSERVABLE (not the "
                  "deliberately-loose inner length). Rejection source: the stored-count clause "
                  "Result()[len(Result()) - 1] == width*n_rows (== 0 when width == 0). If it "
                  "verified => SPEC-TOO-WEAK (the stored-count observable would be hollow on "
                  "the empty case the bug is about)."},
    {"id": "rival-wrong-open", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_OPEN_MOD,
     "refinement": "correct on the non-empty domain but for the empty layout opens at boundary "
                   "1 instead of 0 ([1, 0]). A CSR row-pointer MUST open at 0 (the start of "
                   "the flat storage); a faithful patch producing indptr[0] != 0 builds a "
                   "malformed CSR matrix whose first row is ill-defined, diverging from the "
                   "gold sp.csr_matrix([]) empty layout. It is not behaviourally equal to gold.",
     "rationale": "partial-domain on the empty branch's opening boundary. Rejection source: "
                  "the postcondition Result()[0] == 0. If it verified, the opening-boundary "
                  "invariant would be hollow."},
    {"id": "rival-empty-padded", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY_PADDED_MOD,
     "refinement": "correct on the entire non-empty domain (gold build) but for the empty "
                   "layout returns the padded row-pointer [0, 0, 0] — the exploit shape the "
                   "P1 audit used against the earlier loose (len >= 2 only) empty case. The "
                   "gold empty CSR sp.csr_matrix([]) is a (1, 0) matrix whose indptr is "
                   "EXACTLY [0, 0]; a faithful patch that hands scipy a 3-boundary indptr "
                   "for a 1-row matrix constructs a malformed CSR (indptr length must be "
                   "rows+1), so its dual_coef_ diverges from gold's — not behaviourally "
                   "equal to the gold patch.",
     "rationale": "partial-domain on the empty branch's LENGTH. Rejection source: the "
                  "empty-layout pin Implies(width == 0, len(Result()) == 2). If it verified "
                  "=> SPEC-TOO-WEAK (the exact P1 finding would still be open)."},
    {"id": "rival-flat-nonempty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FLAT_MOD,
     "refinement": "collapses EVERY layout to the empty row-pointer [0, 0], ignoring the "
                   "per-row width; correct only on the width == 0 sub-domain. A faithful real "
                   "patch that always emits an empty CSR would, for a non-empty model (n_SV "
                   ">= 1, n_class >= 2), produce zero stored entries where gold produces "
                   "n_SV*n_class — failing the P2P fit/predict tests that exercise non-trivial "
                   "support vectors (e.g. test_libsvm_iris, test_svr). That patch would NOT "
                   "resolve.",
     "rationale": "partial-domain: pins only the empty sub-domain, diverging on every "
                  "non-empty layout. Rejection source: Implies(width >= 1, len(Result()) == "
                  "n_rows + 1) (fails for n_rows >= 2 where [0,0] has length 2) AND the "
                  "stored-count clause Result()[len-1] == width*n_rows (> 0 != 0). If it "
                  "verified => SPEC-TOO-WEAK (the non-empty progression would be hollow)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real numpy callee numpy.arange)
# ===========================================================================

# (1) axiom-soundness for range_step. range_step is A-consumed: it models
# numpy.arange(start, stop, step). The proof CONSUMES its Ensures (the boundary
# values result[k]==k*step, the length >= 2, and the final-boundary identity
# (len-1)*step+1==stop). The obligation: running the REAL numpy.arange on every
# input IN the axiom's Requires domain (start==0, step>=1, stop==count*step+1,
# count>=1) — the exact (step==width, count==n_rows) family the construction
# calls it with — must satisfy all three Ensures. We ALSO fuzz the EXCLUDED
# step==0 input (the n_SV==0 case the issue triggers) to confirm it genuinely
# RAISES, so the Requires(step>=1) partiality is sound (not over-restrictive
# narration). This reuses + strengthens axiom_check.py's logic; it imports only
# numpy (the module the patch calls) + the stdlib. The axiom describes the
# unchanged callee, so apply_gold is irrelevant; set True for parity with the
# post-gold runtime configuration.
_AX_RANGE_STEP_SOUND = r'''
import random
import sys

import numpy as np


def check_range_step(start, stop, step, count):
    """Assert numpy.arange(start, stop, step) meets the range_step Ensures on an
    input in the axiom's Requires domain."""
    assert step >= 1 and start == 0 and count >= 1 and stop == count * step + 1

    result = list(np.arange(start, stop, step))   # the REAL callee

    # Ensures: len(result) >= 2
    if len(result) < 2:
        print("AXIOM-UNSOUND range_step: arange(%r,%r,%r) len=%d < 2"
              % (start, stop, step, len(result)))
        sys.exit(1)

    # Ensures: result[k] == k*step for every enumerated boundary
    for k, v in enumerate(result):
        if int(v) != k * step:
            print("AXIOM-UNSOUND range_step: arange(%r,%r,%r)[%d] = %r != %d*%d"
                  % (start, stop, step, k, v, k, step))
            sys.exit(1)

    # Ensures: (len-1)*step + 1 == stop  (final boundary is greatest multiple of
    # step strictly below stop; no integer division needed)
    if (len(result) - 1) * step + 1 != stop:
        print("AXIOM-UNSOUND range_step: arange(%r,%r,%r) len=%d violates "
              "(len-1)*step+1 == stop" % (start, stop, step, len(result)))
        sys.exit(1)

    # The final boundary equals the number of stored entries == count*step.
    if int(result[-1]) != count * step:
        print("AXIOM-UNSOUND range_step: arange(%r,%r,%r) last=%r != %d"
              % (start, stop, step, result[-1], count * step))
        sys.exit(1)


def check_zero_step_raises(stop):
    """The axiom EXCLUDES step == 0 (Requires step >= 1). Confirm the REAL callee
    is genuinely undefined there (must raise, not return a progression) so the
    exclusion is sound, not over-claiming. This is the n_SV==0 case the issue
    reports (the ZeroDivisionError on the float step)."""
    try:
        _ = np.arange(0, stop, 0)
    except Exception:
        return  # raises (ZeroDivisionError / ValueError): undefined, as claimed
    print("AXIOM-UNSOUND range_step: np.arange(0,%r,0) did NOT raise — the "
          "step>=1 Requires would be over-restrictive" % (stop,))
    sys.exit(1)


# --- boundary cases over the construction's real (width, n_rows) family ---
# step == width (>=1), count == n_rows (>=1): stop == n_rows*width + 1.
boundary = []
for width in [1, 2, 3, 4, 5, 7, 16, 100]:
    for n_rows in [1, 2, 3, 4, 10, 50]:
        boundary.append((0, n_rows * width + 1, width, n_rows))
boundary += [
    (0, 1 * 1 + 1, 1, 1),        # smallest non-trivial: [0, 1]
    (0, 1 * 9999 + 1, 9999, 1),  # single huge row
]
for (start, stop, step, count) in boundary:
    check_range_step(start, stop, step, count)

# --- randomized fuzz over the Requires-satisfying domain ---
rng = random.Random(14894)
for _ in range(20000):
    step = rng.randint(1, 500)      # n_SV >= 1
    count = rng.randint(1, 500)     # n_class >= 1
    stop = count * step + 1
    check_range_step(0, stop, step, count)

# --- the EXCLUDED zero-step (n_SV == 0): real callee must be undefined ---
for stop in [1, 2, 5, 17, 101, 1000]:
    check_zero_step_raises(stop)

print("G-PBT ax-range-step-sound OK: range_step axiom sound vs real numpy.arange "
      "on %d boundary + 20000 fuzz inputs; step==0 confirmed undefined on 6 "
      "witnesses." % (len(boundary),))
sys.exit(0)
'''

# (2) axiom-containment for range_step. Enumerate EXACTLY the (start, stop, step)
# the MODEL can reach, derived from the impl control flow: range_step is called
# ONLY in the `else` (width >= 1) branch, as range_step(0, size+1, step) with
# size == width*n_rows and step == width. Under the model's Requires
# (width >= 0, n_rows >= 1) restricted to the reachable branch (width >= 1):
#     start == 0           (literal)
#     step  == width       (>= 1, since the guard establishes width >= 1)
#     stop  == size + 1 == width*n_rows + 1 == count*step + 1 with count == n_rows >= 1
# Every such triple lies INSIDE range_step's Requires domain (step >= 1,
# start == 0, Exists count >= 1 with stop == count*step + 1). The containment
# obligation: assert that for the full reachable (width, n_rows) family, the
# triple satisfies the axiom's Requires. We additionally confirm the guarded
# branch NEVER reaches step == 0 (the only Requires-violating step), i.e. the
# model cannot feed range_step a callee-input outside its domain. A reachable
# triple outside the Requires domain => AXIOM-TOO-WEAK-FOR-CALLER. (Covering more
# than the caller reaches would be sound.) No real callee is strictly needed for
# a pure-arithmetic containment, but we run in-container for parity and exercise
# the real numpy.arange acceptance on the reachable family.
_AX_RANGE_STEP_CONTAINMENT = r'''
import sys

import numpy as np


def requires_holds(start, stop, step):
    """range_step's Requires: step >= 1, start == 0, and there exists count >= 1
    with stop == count*step + 1."""
    if not (step >= 1 and start == 0):
        return False
    # stop == count*step + 1  =>  count == (stop - 1) / step must be a positive int
    num = stop - 1
    if step <= 0 or num <= 0 or num % step != 0:
        return False
    count = num // step
    return count >= 1


# Enumerate the (width, n_rows) the model can reach in the range_step-calling
# branch (width >= 1, n_rows >= 1). The triple the impl forms is
# (0, width*n_rows + 1, width).
bad = []
checked = 0
for width in range(1, 200):          # width >= 1 (the guarded branch)
    for n_rows in range(1, 200):     # n_rows >= 1 (the Requires)
        start, step = 0, width
        size = width * n_rows
        stop = size + 1              # == n_rows*width + 1 == count*step + 1
        checked += 1
        if not requires_holds(start, stop, step):
            bad.append((width, n_rows, start, stop, step))
            continue
        # sanity: the real callee accepts it and the count it encodes is n_rows
        count = (stop - 1) // step
        if count != n_rows:
            bad.append(("count-mismatch", width, n_rows, count))
            continue
        # the real callee must not raise on a reachable triple
        try:
            _ = np.arange(start, stop, step)
        except Exception as e:        # pragma: no cover
            bad.append(("real-callee-raised", width, n_rows, repr(e)))

# Confirm the guard makes step == 0 UNREACHABLE: in the calling branch width>=1,
# so step == width is never 0 — the model never feeds the one Requires-violating
# input. (The width == 0 case returns [0,0] without calling range_step.)
reachable_zero_step = any(w == 0 for w in range(1, 200))  # range starts at 1 => False
if reachable_zero_step:
    print("AXIOM-TOO-WEAK-FOR-CALLER: model can reach step == 0 (outside range_step "
          "Requires(step >= 1))")
    sys.exit(1)

if bad:
    print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches range_step inputs OUTSIDE its "
          "Requires domain (or count mismatch / real callee raised):", bad[:20])
    sys.exit(1)

print("G-PBT ax-range-step-containment OK: every range_step input the model can "
      "reach (start==0, step==width>=1, stop==width*n_rows+1==count*step+1 with "
      "count==n_rows>=1) lies inside the axiom's Requires domain; step==0 is "
      "unreachable (guarded). Checked %d reachable (width,n_rows) pairs; real "
      "numpy.arange accepted all." % (checked,))
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-range-step-sound", "axiom": "range_step", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_RANGE_STEP_SOUND,
     "rationale": "range_step (A-consumed) models numpy.arange; the proof consumes its "
                  "Ensures (boundary values, len>=2, final-boundary identity). Running the "
                  "REAL numpy.arange on every input in the axiom's Requires domain "
                  "(start==0, step>=1, stop==count*step+1) — the exact (step==width, "
                  "count==n_rows) family the construction calls — must satisfy all three "
                  "Ensures; the EXCLUDED step==0 (the n_SV==0 issue case) must genuinely "
                  "raise. Any Ensures violation, or a step==0 that does NOT raise, => "
                  "AXIOM-UNSOUND."},
    {"id": "ax-range-step-containment", "axiom": "range_step", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_RANGE_STEP_CONTAINMENT,
     "rationale": "range_step is called ONLY in the guarded (width>=1) branch as "
                  "range_step(0, width*n_rows+1, width); enumerate that reachable family and "
                  "assert each triple satisfies range_step's Requires (step==width>=1, "
                  "start==0, stop==count*step+1 with count==n_rows>=1). step==0 is unreachable "
                  "(the width==0 case returns [0,0] without calling range_step). A reachable "
                  "triple outside the Requires domain => AXIOM-TOO-WEAK-FOR-CALLER; the axiom "
                  "covering more would be sound (containment rule)."},
]
