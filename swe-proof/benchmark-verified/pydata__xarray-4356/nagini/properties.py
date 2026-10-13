# properties.py — PBT manifest for pydata__xarray-4356.
#
# NOT a Nagini module; a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS, writes each
# `module` to a temp file, runs Nagini verify + markers.same_spec against the
# frozen model.py, and stamps RESULT. Region-surgery (we replace ONLY text
# strictly inside # impl-start / # impl-end, which the spec_view elides whole —
# nested # invariants too) guarantees same_spec stays True for every spec case.
#
# DEFENDED SURFACE (reasoned from this task's own spec, NOT corrupted):
#   flag_too_few(sizes: List[int], missing: int, required_minimum: int) -> bool
#   Models the per-position null_mask element of xarray.core.nanops._maybe_null_out's
#   multi-/single-axis reduction branch. The gold fix replaces the single-axis
#   element count `mask.shape[axis]` with the whole-block count
#   `np.take(mask.shape, axis).prod()` (and deletes the early raise that forbade a
#   tuple/list axis). The position is flagged "too few present" iff the present
#   elements (block total minus missing) are below min_count.
#
#   PRECONDITION:
#     (R0) Acc(list_pred(sizes), 1/2)        <-- HALF permission: sizes READ-ONLY
#     (R1) len(sizes) >= 1                    at least one reduced axis
#     (R2) 0 <= missing
#     (R3) missing <= prod(ToSeq(sizes))      at most the whole block is missing
#
#   POSTCONDITION (load-bearing):
#     (P0) Acc(list_pred(sizes), 1/2)         sizes returned read-only (frame)
#     (P1) Result() == (prod(ToSeq(sizes)) - missing - required_minimum < 0)
#          <-- THE discriminator. `prod` is the @Pure front-recursive product fold
#              over ALL the reduced-axes sizes (the whole block), not the first axis.
#
#   READ-ONLY INPUT: `sizes` carries only Acc(list_pred(sizes), 1/2) in Requires
#   AND in Ensures — a half-permission, FRAMED, read-only list. The frame-mutation
#   probe is therefore MANDATORY: an impl that WRITES to sizes (sizes[i] = ...) to
#   satisfy P1 must fail for INSUFFICIENT PERMISSION (you cannot write with 1/2).
#   has_readonly_input = True; frame_mutation_included = True.
#
#   UNGROUNDED-ORACLE ECHO: N/A. P1 is pinned to prod(ToSeq(sizes)) — a @Pure fold
#   FULLY GROUNDED in the read-only input `sizes` and entirely unfolded by the
#   gold loop+snoc lemma. There is no opaque @ContractOnly answer-key / exact
#   marker to echo: an impl that "materialises the oracle" is computing the
#   correct grounded product, i.e. it is CORRECT. So instead of a wrong echo we
#   ship grounded positive controls (directive-2 fallback) + the honest cheapest
#   impl as the admissibility/soundness witnesses.
#
#   CONTROL-FLOW-EFFECT: N/A. flag_too_few returns a pure bool value; there is no
#   raise / return-vs-side-effect difference modeled. The gold's deleted
#   `raise ValueError` for a tuple/list axis is NOT a separate observable in the
#   value abstraction — the model admits the multi-axis case directly via
#   len(sizes) >= 2, and meta.json records the raise's removal is observable ONLY
#   through the corrected multi-axis count (which P1 already pins). No capability
#   token is needed; omitted (justified in assessment).
#
#   THE REAL BUG (model_prepatch.py): `total = sizes[0]` — count only the FIRST
#   reduced axis (the single-axis `mask.shape[axis]`). Coincides with the product
#   when len(sizes)==1, UNDERCOUNTS for >=2 axes with a non-unit later size. That
#   is the partial-domain attack and the prepatch revert; its faithful real patch
#   is the UNPATCHED nanops.py, which on the 3-dim F2P (dim=["x","y","z"],
#   min_count=3) either raises (tuple axis) or computes the wrong null_mask.
#
#   AXIOM LANE: NO consumed @ContractOnly axiom (axioms region empty). `prod` over
#   the selected sizes is an A-REFERENCE deep model of np.take(mask.shape,axis).prod()
#   validated by axiom_check.py (G-AX). Per PBT_PLAN §2.4 / §4, A-reference deep
#   models are checked the same way: soundness (deep model == real callee on every
#   caller-reachable input) + containment (every callee-input the model can reach
#   lies in the callee's domain). Both probes below.
from pathlib import Path

INSTANCE = "pydata__xarray-4356"
# meta.json float_encoding is null: the fix is integer-only (shape sizes are
# ints), precision-independent — no float encoding.
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact frozen impl-region BODY of model.py (strictly INSIDE the markers,
# the marker comment lines excluded). We only ever replace this block, so the
# spec regions (axioms/pure/pre/post-conditions + signatures) are untouched and
# markers.same_spec stays True. The nested # invariants region lives inside the
# impl span, so it is elided by spec_view too and may be edited freely.
_IMPL = """    # total = product over the reduced axes of their sizes  (select then product)
    total = 1
    k = 0
    while k < len(sizes):
        # invariants-start
        Invariant(Acc(list_pred(sizes), 1 / 2))
        Invariant(0 <= k and k <= len(sizes))
        # the running product is the product over the sizes processed so far
        Invariant(total == prod(ToSeq(sizes).take(k)))
        # invariants-end
        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
        total = total * sizes[k]
        k = k + 1
    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
    Assert(total == prod(ToSeq(sizes)))
    return (total - missing - required_minimum) < 0"""

# The gold forward product loop + snoc lemma + framing asserts, VERBATIM. Every
# positive control / admissibility / partial-domain rival reuses this block so it
# keeps exactly the proof obligations the gold proof discharges (directive-2:
# never drop a framing assert / lemma) — only the requested executable shape
# around it changes.
_GOLD_LOOP = """    total = 1
    k = 0
    while k < len(sizes):
        # invariants-start
        Invariant(Acc(list_pred(sizes), 1 / 2))
        Invariant(0 <= k and k <= len(sizes))
        # the running product is the product over the sizes processed so far
        Invariant(total == prod(ToSeq(sizes).take(k)))
        # invariants-end
        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))
        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)
        lemma_prod_snoc(ToSeq(sizes).take(k + 1))
        total = total * sizes[k]
        k = k + 1
    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))
    Assert(total == prod(ToSeq(sizes)))"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(body: str) -> str:
    """Build a full model.py variant by replacing ONLY the impl-region body."""
    return _swap(_BASE, _IMPL, body)


SPEC_TESTS = [
    # -------------------------------------------------------------------------
    # 5. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
    # Keeps the gold forward product loop + snoc lemma + framing asserts VERBATIM
    # (no induction lemma is added/removed; directive-3: do NOT flip to a
    # front-append against the front-recursive fold). What changes is purely
    # value-preserving and local:
    #   * the two pre-loop assignments are reordered (k first, then total),
    #   * the decision is computed into a typed bool local then returned,
    #   * the subtraction operands are reassociated (total - required_minimum -
    #     missing == total - missing - required_minimum over ints).
    # MUST verify — else SPEC-TOO-STRONG.
    # -------------------------------------------------------------------------
    {
        "id": "pos-control-reorder-local-bool",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Same gold product fold, pre-loop assignments reordered.\n"
            "    k = 0\n"
            + _GOLD_LOOP.replace("    total = 1\n    k = 0\n", "    total = 1\n", 1)
            + "\n"
            "    # value-preserving reshape: reassociate the integer subtraction and\n"
            "    # bind the decision to a typed local before returning.\n"
            "    flagged = (total - required_minimum - missing) < 0  # type: bool\n"
            "    return flagged"
        ),
        "rationale": "a structurally-different but CORRECT impl (reordered pre-loop "
                     "assignments, decision bound to a typed bool local, subtraction "
                     "reassociated) keeps the gold loop/lemma/asserts verbatim and must "
                     "satisfy P1. If it cannot verify, the postcondition is too strong "
                     "(SPEC-TOO-STRONG). No new induction lemma — only value-preserving "
                     "local reshapes around the gold forward fold.",
    },
    # -------------------------------------------------------------------------
    # 2 (fallback). GROUNDED POSITIVE CONTROL / honest cheapest impl. Because P1's
    # oracle prod(ToSeq(sizes)) is fully grounded in the read-only input (no
    # answer-key to echo), the honest impl that computes that product IS correct
    # and must verify. This variant accumulates the product into a differently-
    # named local using a multiply-into-self form (total *= sizes[k] spelled as
    # total = sizes[k] * total — commuted) while keeping the gold loop scaffold,
    # lemma, and the two closing framing asserts verbatim. MUST verify.
    # -------------------------------------------------------------------------
    {
        "id": "pos-control-commuted-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    total = 1\n"
            "    k = 0\n"
            "    while k < len(sizes):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(sizes), 1 / 2))\n"
            "        Invariant(0 <= k and k <= len(sizes))\n"
            "        # the running product is the product over the sizes processed so far\n"
            "        Invariant(total == prod(ToSeq(sizes).take(k)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(sizes).take(k + 1).take(k) == ToSeq(sizes).take(k))\n"
            "        Assert(len(ToSeq(sizes).take(k + 1)) == k + 1)\n"
            "        lemma_prod_snoc(ToSeq(sizes).take(k + 1))\n"
            "        # commuted multiply-into-accumulator (a*b == b*a over ints)\n"
            "        total = sizes[k] * total\n"
            "        k = k + 1\n"
            "    Assert(ToSeq(sizes).take(k) == ToSeq(sizes))\n"
            "    Assert(total == prod(ToSeq(sizes)))\n"
            "    return (total - missing - required_minimum) < 0"
        ),
        "rationale": "P1's oracle prod(ToSeq(sizes)) is grounded (a @Pure fold of the "
                     "read-only input, fully unfolded by the gold loop), so the honest "
                     "cheapest impl that computes the block product is CORRECT and must "
                     "verify (directive-2 fallback; no ungrounded answer-key to echo). "
                     "Only the multiply is commuted (a*b==b*a); the lemma and framing "
                     "asserts are verbatim, so any failure is SPEC-TOO-STRONG not a "
                     "proof gap.",
    },
    # -------------------------------------------------------------------------
    # 6. ADMISSIBILITY — a recursive self-call on the F2P-shaped input forces
    # Nagini to discharge the Requires (R0-R3) at a real call site. The F2P test
    # (test_min_count_nd) reduces a 3-dim array over dim=["x","y","z"] with
    # min_count=3, so the model sees len(sizes)==3 reduced axes; sizes=[4,3,2] is
    # a representative such block (prod==24), missing==5 in [0,24], required_min==3.
    # If the precondition could not admit this legitimate F2P-shaped input the call
    # site would fail => PRECOND-TOO-STRONG. The gold body follows verbatim.
    # -------------------------------------------------------------------------
    {
        "id": "admiss-f2p-three-axes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # ADMISSIBILITY: build the F2P-shaped reduced-axes sizes (3 axes,\n"
            "    # the dim=['x','y','z'] reduction) and call flag_too_few on it; the\n"
            "    # Requires R0-R3 must admit it (else PRECOND-TOO-STRONG).\n"
            "    witness = [4, 3, 2]  # type: List[int]\n"
            "    Assert(len(witness) >= 1)\n"
            "    # prod([4,3,2]) == 24, needed to discharge R3 (missing<=prod) at the\n"
            "    # call site. `prod` is the FRONT-RECURSIVE fold prod(xs) == xs[0] *\n"
            "    # prod(xs.drop(1)); Nagini does not auto-evaluate it on the concrete\n"
            "    # sequence, so unfold it explicitly tail-to-front to the empty tail.\n"
            "    # This is a pure in-region PROOF AID (no spec change) — it only lets\n"
            "    # Nagini see the literal product value the precondition already admits.\n"
            "    w = ToSeq(witness)  # type: PSeq[int]\n"
            "    Assert(prod(w.drop(1).drop(1).drop(1)) == 1)  # empty tail, prod == 1\n"
            "    Assert(prod(w.drop(1).drop(1)) == 2)          # [2]\n"
            "    Assert(prod(w.drop(1)) == 6)                  # [3, 2]\n"
            "    Assert(prod(ToSeq(witness)) == 24)            # [4, 3, 2]\n"
            "    # missing==5 lies in [0, prod]; min_count==3 (the F2P value).\n"
            "    _ = flag_too_few(witness, 5, 3)\n"
            "    # --- gold body verbatim below ---\n"
            + _IMPL
        ),
        "rationale": "the precondition (R0 Acc(sizes,1/2); R1 len>=1; R2 0<=missing; "
                     "R3 missing<=prod(sizes)) must admit the F2P-shaped 3-axis input "
                     "(sizes=[4,3,2], missing=5, min_count=3 — the dim=['x','y','z'], "
                     "min_count=3 reduction). The self-call discharges the Requires at "
                     "a real call site; if it cannot, PRECOND-TOO-STRONG. Gold body is "
                     "verbatim so the postcondition obligation is unchanged.",
    },
    # -------------------------------------------------------------------------
    # 1. FRAME-MUTATION (MANDATORY — `sizes` is Acc(list_pred(sizes), 1/2),
    # read-only). A rival that WRITES to sizes to "satisfy" P1 must fail for
    # INSUFFICIENT PERMISSION. We do the honest gold computation AND additionally
    # write sizes[0] = sizes[0] (a value-preserving self-store): the value is
    # identical, so P1 is still semantically true, but the WRITE itself requires
    # full permission which the half-permission frame denies. The rejection is
    # therefore attributable purely to the write, not to a value mismatch. Keeps
    # the gold loop/lemma/asserts verbatim. expect=reject (insufficient permission).
    # -------------------------------------------------------------------------
    {
        "id": "frame-mutation-self-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_LOOP
            + "\n"
            "    # FRAME VIOLATION: write into the read-only (half-permission) input.\n"
            "    # The stored value is identical (value-preserving), so P1 still holds\n"
            "    # semantically; the rejection is for the WRITE needing full permission.\n"
            "    sizes[0] = sizes[0]\n"
            "    return (total - missing - required_minimum) < 0"
        ),
        "refinement": "a faithful real patch that MUTATES the input (e.g. assigns into "
                     "mask.shape or the shape array it reduces over) corrupts the array "
                     "the caller reuses for mask.sum(axis) / the result fill; the F2P "
                     "test_min_count_nd asserts the multi-dim reduction equals the "
                     "dim=... reduction (assert_allclose), which an in-place shape write "
                     "would break. Does NOT resolve.",
        "rationale": "rejection comes from the PERMISSION SYSTEM: sizes is held at "
                     "Acc(list_pred(sizes), 1/2) (R0/P0), and a list store sizes[0]=... "
                     "requires FULL permission. Nagini rejects for insufficient "
                     "permission even though the value is preserved. A verify here would "
                     "mean the read-only frame is unenforced (the #1 weakness class).",
    },
    # -------------------------------------------------------------------------
    # 3. PARTIAL-DOMAIN / THE REAL PREPATCH BUG — count only the FIRST reduced
    # axis (total = sizes[0], the single-axis mask.shape[axis]). Correct when
    # len(sizes)==1 (prod==sizes[0]); UNDERCOUNTS for >=2 axes with a non-unit
    # later size. This is model_prepatch.py verbatim. expect=reject (violates P1
    # on the multi-axis sub-domain). The single most important uniqueness attack.
    # -------------------------------------------------------------------------
    {
        "id": "reject-prepatch-first-axis-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PREPATCH BUG (model_prepatch.py): single-axis count only.\n"
            "    total = sizes[0]\n"
            "    return (total - missing - required_minimum) < 0"
        ),
        "refinement": "this IS the pre-patch op mask.shape[axis] (single-axis size). Its "
                     "faithful real patch is the UNPATCHED nanops.py, which on the F2P "
                     "(da.sum(dim=['x','y','z'], min_count=3) over a 3-dim array) either "
                     "RAISES ValueError (the old tuple-axis guard) or, with the guard "
                     "gone, counts only shape[x] instead of shape[x]*shape[y]*shape[z], "
                     "so null_mask flags the wrong positions and the result diverges "
                     "from the dim=... reduction the F2P asserts equal. Does NOT resolve.",
        "rationale": "violates P1 (Result()==(prod(ToSeq(sizes))-missing-min<0)) on every "
                     "input where prod(sizes) != sizes[0] (>=2 axes, a later size>1). A "
                     "verify here is SPEC-TOO-WEAK — the discriminating product-over-block "
                     "count would be unenforced (exactly what G-DIFF senses).",
    },
    # -------------------------------------------------------------------------
    # 3'. PARTIAL-DOMAIN (subtler) — product of the FIRST TWO axes only
    # (total = sizes[0]*sizes[1] for len>=2, else sizes[0]). Correct for
    # len(sizes) in {1,2}; UNDERCOUNTS for len>=3 with a non-unit third+ size —
    # exactly the F2P shape (dim=["x","y","z"], 3 axes). expect=reject. Probes that
    # P1 pins the WHOLE block product, not just a leading prefix of axes.
    # -------------------------------------------------------------------------
    {
        "id": "reject-first-two-axes-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG: product of only the first two reduced axes (drops axis 3+).\n"
            "    if len(sizes) >= 2:\n"
            "        total = sizes[0] * sizes[1]\n"
            "    else:\n"
            "        total = sizes[0]\n"
            "    return (total - missing - required_minimum) < 0"
        ),
        "refinement": "a faithful real patch that took np.take(shape, axis[:2]).prod() "
                     "(only the first two reduced axes) would, on the 3-dim F2P "
                     "(dim=['x','y','z']), compute shape[x]*shape[y] instead of "
                     "shape[x]*shape[y]*shape[z] — undercounting the block by the factor "
                     "shape[z]>1, so null_mask flags positions the full-block reduction "
                     "does not, and the result != the dim=... reduction. Does NOT resolve.",
        "rationale": "violates P1 on the len(sizes)>=3 sub-domain (where prod over all "
                     "axes != sizes[0]*sizes[1]). A verify here is SPEC-TOO-WEAK: P1 "
                     "would only pin a prefix of the reduced axes, not the whole block. "
                     "This is correct for the single- and two-axis P2P cases yet wrong "
                     "for the three-axis F2P — a true partial-domain miss.",
    },
    # -------------------------------------------------------------------------
    # 3''. OFF-BY-ONE COMPARISON (cheap supporting near-miss with a real
    # refinement) — uses <= 0 instead of < 0 in the decision. Right block product,
    # but the boundary present==min_count (total-missing==required_minimum) is the
    # boundary the F2P min_count=3 exercises: < 0 means "flag iff present < min",
    # <= 0 means "flag iff present <= min", flipping the exactly-min_count
    # position. expect=reject. Confirms P1 pins the strict < 0 boundary.
    # -------------------------------------------------------------------------
    {
        "id": "reject-off-by-one-le-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_LOOP
            + "\n"
            "    # WRONG boundary: <= 0 flags the exactly-min_count position too.\n"
            "    return (total - missing - required_minimum) <= 0"
        ),
        "refinement": "the gold expression is (block - missing - min_count) < 0, i.e. "
                     "flag iff present < min_count. Using <= 0 additionally flags the "
                     "position where present == min_count exactly (e.g. block 24, "
                     "missing 21, min_count 3 -> present 3). The F2P uses min_count=3 and "
                     "a real patch with <= would null out positions that have EXACTLY "
                     "min_count present values — which the dim=... reference reduction "
                     "keeps — so assert_allclose FAILS. Does NOT resolve.",
        "rationale": "violates P1 (Result()==(...<0)) at the present==required_minimum "
                     "boundary: P1 demands strict < 0, this returns <= 0. A verify here "
                     "is SPEC-TOO-WEAK — the strict boundary would be unenforced. (Cheap "
                     "supporting near-miss carrying a real refinement.)",
    },
]


# axiom_check.py source, read on the HOST at manifest-load time and embedded into
# the soundness probe. The runner mounts ONLY the probe script at /work, so
# model.py / axiom_check.py are NOT in-container (directive 6) — we inline the
# audited G-AX oracle. It imports only numpy (the same library the gold patch
# calls), CALLS the real np.take(...).prod() callee (never scrapes source,
# directive 4), and exits 0 iff every obligation holds.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


AXIOM_TESTS = [
    # -------------------------------------------------------------------------
    # A-REFERENCE SOUNDNESS — there is NO consumed @ContractOnly axiom; `prod`
    # over the selected reduced-axes sizes is the deep model (A-reference) of the
    # one changed quantity np.take(mask.shape, axis).prod(). Per PBT_PLAN §2.4,
    # the deep model must equal the real callee on every caller-reachable input.
    # This reuses axiom_check.py VERBATIM (the bundle's audited G-AX oracle): it
    # runs the real np.take(shape,axis).prod() on 13 boundary + 4000 fuzz
    # shape/axis cases and asserts prod(select(shape,axis)) == np.take(..).prod(),
    # PLUS the full null_mask decision against the gold numpy expression on real
    # boolean masks over 7 multi-axis configurations. A single mismatch is
    # AXIOM-UNSOUND (here: deep-model-unsound). Exit 0 iff sound.
    #
    # apply_gold=True: the null_mask sub-check evaluates the gold-fixed expression
    # np.take(mask.shape,axis).prod(); the deep-model identity sub-check is
    # patch-independent (pure numpy), so applying the gold patch is harmless and
    # keeps the image in the post-fix state meta records for G-AX.
    # -------------------------------------------------------------------------
    {
        "id": "ax-sound-prod-take-deepmodel",
        "axiom": "prod (A-reference: np.take(mask.shape, axis).prod())",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the A-reference deep model prod(select(shape,axis)) must equal the "
                     "real np.take(shape,axis).prod() on every caller-reachable shape/axis "
                     "AND the model's null_mask decision must match the gold numpy "
                     "expression on real masks. axiom_check.py executes the real callee "
                     "over 13 boundary + 4000 fuzz cases + 7 real-mask configs; a single "
                     "disagreement is AXIOM-UNSOUND (deep model unsound). It CALLS the "
                     "real numpy routine (never scrapes source) and imports only numpy. "
                     "Exit 0 iff sound.",
    },
    # -------------------------------------------------------------------------
    # A-REFERENCE CONTAINMENT — every callee-input the MODEL can reach must lie in
    # the real callee's Requires domain. The model passes np.take(shape, axis) a
    # shape with len(sizes)>=1 positive integer sizes (R1) and a reduced-axes
    # index list `axis` that is a non-empty subset of range(ndim) — exactly what
    # _maybe_null_out passes (np.take(mask.shape, axis) for axis = the reduced
    # dims). np.take over a flat shape array accepts ANY integer index sequence in
    # [-ndim, ndim); the model only ever produces a valid in-range non-empty axis
    # subset, so every caller-reachable (shape, axis) is in the callee's domain.
    # Coverage broader than reached (np.take accepts more) is SOUND (float-vs-int
    # rule). A reachable input the callee rejected would be
    # AXIOM-TOO-WEAK-FOR-CALLER — the probe ENUMERATES the exact caller-reachable
    # (shape, axis) shapes (F2P 3-axis + boundary + fuzz) and asserts np.take(...)
    # .prod() accepts each and equals the deep model (containment witnessed by
    # acceptance + agreement). Self-contained: imports only numpy, embeds the deep
    # model. apply_gold=True (the callee is the gold-fixed expression).
    # -------------------------------------------------------------------------
    {
        "id": "ax-contain-prod-take-domain",
        "axiom": "prod (A-reference: np.take(mask.shape, axis).prod())",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys, itertools, random\n"
            "try:\n"
            "    import numpy as np\n"
            "except Exception as e:\n"
            "    print('cannot import numpy:', e); sys.exit(1)\n"
            "\n"
            "def prod_model(xs):\n"
            "    out = 1\n"
            "    for v in xs:\n"
            "        out *= v\n"
            "    return out\n"
            "\n"
            "def select_model(shape, axis):\n"
            "    return [shape[ax] for ax in axis]\n"
            "\n"
            "# The model passes np.take(mask.shape, axis) ONLY a shape of len>=1\n"
            "# positive int sizes (R1, each>0) and a NON-EMPTY reduced-axes index\n"
            "# subset of range(ndim). Enumerate exactly those caller-reachable\n"
            "# (shape, axis) shapes — the 3-axis F2P (dim=['x','y','z']) + boundary +\n"
            "# fuzz — and assert the real np.take(shape,axis).prod() ACCEPTS each (it\n"
            "# is in the callee's Requires domain) and EQUALS prod(select(shape,axis))\n"
            "# (containment witnessed by acceptance + agreement).\n"
            "reached = [\n"
            "    ((4, 3, 2), [0, 1, 2]),   # the F2P 3-axis reduction (dim=x,y,z)\n"
            "    ((5,), [0]),              # single axis (P2P)\n"
            "    ((2, 3), [0, 1]),         # two axes\n"
            "    ((2, 3), [0]),            # partial axis subset\n"
            "    ((2, 3), [1]),\n"
            "    ((1, 1, 1), [0, 1, 2]),   # unit sizes (empty-ish block, prod 1)\n"
            "    ((10, 1, 1), [0]),\n"
            "    ((3, 3, 3, 3), [0, 1, 2, 3]),\n"
            "]\n"
            "rng = random.Random(4356)\n"
            "for _ in range(400):\n"
            "    ndim = rng.randint(1, 5)\n"
            "    shape = tuple(rng.randint(1, 6) for _ in range(ndim))\n"
            "    k = rng.randint(1, ndim)\n"
            "    axis = sorted(rng.sample(range(ndim), k))\n"
            "    reached.append((shape, axis))\n"
            "ok = True\n"
            "for shape, axis in reached:\n"
            "    assert len(axis) >= 1, 'model only ever passes a non-empty axis subset'\n"
            "    assert all(s >= 1 for s in shape), 'R1: each reduced-axis size > 0'\n"
            "    assert all(0 <= a < len(shape) for a in axis), 'axis indices in range'\n"
            "    try:\n"
            "        real = int(np.take(np.array(shape), axis).prod())\n"
            "    except Exception as e:\n"
            "        print('FAIL: caller-reachable (shape=%r, axis=%r) OUTSIDE the '\n"
            "              'np.take domain: %s' % (shape, axis, e))\n"
            "        ok = False\n"
            "        continue\n"
            "    model = prod_model(select_model(shape, axis))\n"
            "    if real != model:\n"
            "        print('FAIL: containment/agreement mismatch shape=%r axis=%r '\n"
            "              'real=%r model=%r' % (shape, axis, real, model))\n"
            "        ok = False\n"
            "if not ok:\n"
            "    sys.exit(1)\n"
            "print('AX-CONTAIN OK: every caller-reachable (shape, non-empty axis subset) '\n"
            "      '(F2P 3-axis + boundary + 400 fuzz) lies in the np.take(shape,axis).prod() '\n"
            "      'Requires domain and equals prod(select(shape,axis)); coverage is '\n"
            "      'broader-than-reached (np.take accepts more index shapes) - SOUND.')\n"
            "sys.exit(0)\n"
        ),
        "rationale": "containment, not whole-domain coverage: the model only ever passes "
                     "np.take(mask.shape, axis) a len>=1 positive-int shape and a "
                     "non-empty in-range reduced-axes subset (R1 + the reduction's axis "
                     "list). Every such caller-reachable input lies in the real "
                     "np.take(...).prod() domain and agrees with the deep model. A "
                     "reachable input the callee rejected would be AXIOM-TOO-WEAK-FOR-"
                     "CALLER; none exists. Broader callee coverage (other index shapes) "
                     "is sound (float-vs-int rule).",
    },
]
