# properties.py — PBT falsification battery for sympy__sympy-17630.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# byte-for-byte (region-surgery: only the text strictly INSIDE the single
# # impl-start / # impl-end region is swapped) and is checked by Nagini verify +
# markers.same_spec. AXIOM_TESTS is empty: this bundle has NO @ContractOnly
# axioms (axioms region intentionally empty; the matrix-domain constructors are
# A-reference deep models validated by axiom_check.py / G-AX, not consumed in the
# proof — there is no axiom obligation a Docker probe could falsify here).
#
# Defended surface (model.py `postprocess`):
#   postprocess(is_sum: bool, num_matrices: int, num_scalars: int,
#               has_explicit_matrix: bool) -> Combo
#   Requires: num_matrices >= 1; num_scalars >= 0; MustTerminate(2)
#             -- (T) a total-correctness obligation: the post-processor must
#                terminate and actually return its Combo; a diverging impl
#                satisfies the value postconditions only vacuously and is
#                rejected by Nagini's obligation system (the exact
#                spec-too-weak class the G-PANEL-1 auditor exploited with an
#                infinite `while True` loop before this obligation was added)
#   Ensures:  (E1) Result().matrix_arg_count == num_matrices
#             (E2) Implies(is_sum, Result().scalar_arg_present == False)
#                  -- the DISCRIMINATING fix clause (sum never carries a scalar
#                     coefficient argument; the additive identity is NOT injected)
#             (E3) Implies(not is_sum,
#                          scalar_arg_present
#                          == (num_scalars > 0 and not has_explicit_matrix))
# All four inputs are pass-by-value primitives (bool/int); the only object is the
# freshly-built Combo result. => NO read-only Acc(.,1/2) input, so the
# frame-mutation class is N/A (nothing to overwrite). The postcondition is
# GROUNDED entirely in the args (no @Pure answer-key / opaque oracle to echo), so
# the ungrounded-oracle-echo class is N/A — replaced by an honest positive
# control. The function is pure-functional (no raise / no side effect), so the
# control-flow-effect class is N/A. See 'assessment'. The strong, applicable
# classes are PARTIAL-DOMAIN (the spec pins three disjoint sub-domains:
# sum-no-scalar / sum-with-scalar / product subcases) and VALUE (matrix_arg_count
# pin), plus the soundness positive control and admissibility.
from pathlib import Path

INSTANCE = "sympy__sympy-17630"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim text strictly BETWEEN "    # impl-start\n" and "    # impl-end\n".
# Every variant is _BASE with this block replaced by an equivalent-shape body
# that touches ONLY the impl region (guarantees markers.same_spec == True).
_IMPL = (
    "    if num_scalars > 0:\n"
    "        if not is_sum:\n"
    "            # Product with a scalar coefficient: absorb it into an explicit\n"
    "            # matrix factor when one is present, leaving only matrix factors.\n"
    "            absorbed = has_explicit_matrix  # type: bool\n"
    "            if absorbed:\n"
    "                return Combo(num_matrices, False)\n"
    "            # No explicit matrix to absorb into: the scalar coefficient leads\n"
    "            # the matrix-domain product.\n"
    "            return Combo(num_matrices, True)\n"
    "        else:\n"
    "            # Sum with a genuine scalar term: the scalar is held apart; the\n"
    "            # matrix-domain sum is formed from the matrix terms alone.\n"
    "            return Combo(num_matrices, False)\n"
    "    # No genuine scalar term remains.\n"
    "    if is_sum:\n"
    "        # Build the matrix-domain sum from the matrix terms alone; do NOT\n"
    "        # collapse the empty scalar collection into the additive identity and\n"
    "        # inject it as an argument.\n"
    "        return Combo(num_matrices, False)\n"
    "    # Product with no scalar term: the matrix-domain product is the matrix\n"
    "    # factors alone (the empty scalar collection collapses to the multiplicative\n"
    "    # identity, which the product constructor drops — no scalar argument).\n"
    "    return Combo(num_matrices, False)\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: impl block not found verbatim")
    if src.count(old) != 1:
        raise AssertionError("not unique: impl block")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Return full model source with the impl region body replaced by new_impl.

    new_impl is the text that goes strictly between the # impl-start / # impl-end
    markers (so same_spec is preserved by construction)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl.
# Branch order is flipped (handle the no-scalar cases first, then the
# scalar cases; split is_sum out into its own top-level dispatch) and a fresh
# local layout is used. No loops / no fold => no induction lemma needed, so the
# gold proof obligations (the three Ensures on Result()) are discharged exactly
# as before. MUST verify, else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = (
    "    # Structurally-different but behaviourally-identical dispatch: branch\n"
    "    # on is_sum first, then on the scalar presence, with a fresh local.\n"
    "    if is_sum:\n"
    "        # (E2) A SUM never carries a scalar coefficient argument, with or\n"
    "        # without a genuine scalar term.\n"
    "        return Combo(num_matrices, False)\n"
    "    # PRODUCT below.\n"
    "    scalar_leads = num_scalars > 0 and not has_explicit_matrix  # type: bool\n"
    "    return Combo(num_matrices, scalar_leads)\n"
)

# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY — the precondition must admit an F2P-shaped input. The exact
# discriminating F2P witness is a SUM of matrix terms with NO genuine scalar
# (is_sum=True, num_matrices>=1, num_scalars=0): Add(ZeroMatrix, ZeroMatrix) and
# block_collapse(b*b*b). A CONTRACT-FREE module-level caller (injected into the
# impl region after the real logic's return, so spec_signature is untouched)
# calls postprocess on that literal argument tuple, forcing the verifier to
# discharge Requires(num_matrices>=1 and num_scalars>=0) AND to take the fresh
# MustTerminate(2) termination obligation at the call site (a contract-free
# caller holds no obligations, so the call succeeds only if the precondition —
# including the obligation — is establishable for a normal input); if not,
# PRECOND-TOO-STRONG. (An in-impl self-call would instead leak the caller's own
# MustTerminate(2) obligation — the callee's measure is not smaller — so the
# probe lives in a separate caller, exactly as a real consumer would call it.)
# The probe result is also asserted to carry no scalar argument (E2).
# ---------------------------------------------------------------------------
_ADMISS = (
    "    # Real logic (unchanged behaviour).\n"
    "    if is_sum:\n"
    "        return Combo(num_matrices, False)\n"
    "    scalar_leads = num_scalars > 0 and not has_explicit_matrix  # type: bool\n"
    "    return Combo(num_matrices, scalar_leads)\n"
    "\n"
    "\n"
    "def _admiss_caller() -> None:\n"
    "    # Admissibility: a contract-free caller invokes postprocess on the\n"
    "    # discriminating F2P-shaped input (a SUM of >=1 matrix term, no genuine\n"
    "    # scalar). The Requires (incl. the MustTerminate(2) termination\n"
    "    # obligation, freshly takeable in a context that holds none) must be\n"
    "    # establishable for it, else PRECOND-TOO-STRONG.\n"
    "    probe = postprocess(True, 2, 0, False)  # type: Combo\n"
    "    Assert(probe.scalar_arg_present == False)\n"
    "    Assert(probe.matrix_arg_count == 2)\n"
)

# ---------------------------------------------------------------------------
# 3a. PARTIAL-DOMAIN (the pre-patch bug, the F2P-discriminating sub-domain):
# correct everywhere EXCEPT is_sum=True & num_scalars==0, where it injects the
# collapsed additive identity as a scalar argument (scalar_arg_present=True).
# This is exactly model_prepatch.py's failing branch. Violates (E2). MUST reject.
# ---------------------------------------------------------------------------
_REJ_PREPATCH = (
    "    if is_sum:\n"
    "        if num_scalars > 0:\n"
    "            # Sum with a genuine scalar: scalar held apart (correct).\n"
    "            return Combo(num_matrices, False)\n"
    "        # SUM, no genuine scalar: PRE-PATCH BUG -- collapse the empty scalar\n"
    "        # collection into the additive identity Zero() and inject it as a\n"
    "        # top-level argument of the rebuilt MatAdd (scalar contamination).\n"
    "        return Combo(num_matrices, True)\n"
    "    # PRODUCT (unchanged, correct).\n"
    "    scalar_leads = num_scalars > 0 and not has_explicit_matrix  # type: bool\n"
    "    return Combo(num_matrices, scalar_leads)\n"
)

# ---------------------------------------------------------------------------
# 3b. PARTIAL-DOMAIN (sum-WITH-genuine-scalar sub-domain): correct everywhere
# EXCEPT is_sum=True & num_scalars>0, where it leaves the genuine scalar among
# the matrix-domain sum's arguments (scalar_arg_present=True). Violates (E2) on a
# DIFFERENT sub-domain than 3a (this branch is is_sum & num_scalars>0). MUST
# reject.
# ---------------------------------------------------------------------------
_REJ_SUM_WITH_SCALAR = (
    "    if is_sum:\n"
    "        if num_scalars > 0:\n"
    "            # WRONG: leave the genuine scalar among the matrix-domain sum's\n"
    "            # arguments instead of holding it apart -> contaminates MatAdd.\n"
    "            return Combo(num_matrices, True)\n"
    "        return Combo(num_matrices, False)\n"
    "    scalar_leads = num_scalars > 0 and not has_explicit_matrix  # type: bool\n"
    "    return Combo(num_matrices, scalar_leads)\n"
)

# ---------------------------------------------------------------------------
# 3c. PARTIAL-DOMAIN (product, explicit-matrix-absorb sub-domain): correct
# everywhere EXCEPT is_sum=False & num_scalars>0 & has_explicit_matrix, where it
# FAILS to absorb the scalar into the explicit matrix factor and instead leaves a
# spurious scalar argument (scalar_arg_present=True). Violates (E3). MUST reject.
# ---------------------------------------------------------------------------
_REJ_PRODUCT_NO_ABSORB = (
    "    if is_sum:\n"
    "        return Combo(num_matrices, False)\n"
    "    # PRODUCT: scalar should be absorbed when an explicit matrix is present.\n"
    "    if num_scalars > 0:\n"
    "        # WRONG: ignore has_explicit_matrix and always keep a scalar arg.\n"
    "        return Combo(num_matrices, True)\n"
    "    return Combo(num_matrices, False)\n"
)

# ---------------------------------------------------------------------------
# 3d. PARTIAL-DOMAIN (product, no-scalar sub-domain): correct everywhere EXCEPT
# is_sum=False & num_scalars==0, where it claims a scalar coefficient argument is
# present (scalar_arg_present=True) although the multiplicative identity is
# dropped. Violates (E3: rhs == False there). MUST reject.
# ---------------------------------------------------------------------------
_REJ_PRODUCT_PHANTOM_SCALAR = (
    "    if is_sum:\n"
    "        return Combo(num_matrices, False)\n"
    "    if num_scalars > 0:\n"
    "        absorbed = has_explicit_matrix  # type: bool\n"
    "        if absorbed:\n"
    "            return Combo(num_matrices, False)\n"
    "        return Combo(num_matrices, True)\n"
    "    # WRONG: product with no scalar term still claims a scalar argument; the\n"
    "    # multiplicative identity is in fact dropped by the matrix product.\n"
    "    return Combo(num_matrices, True)\n"
)

# ---------------------------------------------------------------------------
# 1' VALUE / matrix-count attack (the matrix_arg_count facet, E1): an impl that
# satisfies BOTH scalar-arg clauses exactly but mis-states the matrix-term count
# (drops one matrix term, num_matrices - 1, in the discriminating SUM-no-scalar
# branch). Invisible to E2/E3 (the scalar facet is correct) but violates E1.
# A byte-fuzzer flipping the scalar bool would never find this. MUST reject.
# (num_matrices-1 can be 0, still satisfies Combo's Requires matrix_arg_count>=0.)
# ---------------------------------------------------------------------------
_REJ_WRONG_COUNT = (
    "    if is_sum:\n"
    "        # WRONG matrix count in the discriminating SUM-no-scalar domain:\n"
    "        # drop one matrix term while keeping scalar_arg_present correct.\n"
    "        if num_scalars > 0:\n"
    "            return Combo(num_matrices, False)\n"
    "        return Combo(num_matrices - 1, False)\n"
    "    scalar_leads = num_scalars > 0 and not has_explicit_matrix  # type: bool\n"
    "    return Combo(num_matrices, scalar_leads)\n"
)

# ---------------------------------------------------------------------------
# 3e. SUPPORTING near-miss (whole-sum always-scalar): cheap corruption that
# claims every SUM carries a scalar argument. Subsumes 3a+3b on the sum domain;
# kept as a cheap supporting case but it still carries a real refinement (any
# matrix-term sum becomes scalar-contaminated -> the reported crash). MUST reject.
# ---------------------------------------------------------------------------
_REJ_SUM_ALWAYS_SCALAR = (
    "    if is_sum:\n"
    "        # WRONG: every SUM carries a scalar argument (violates E2 on the\n"
    "        # whole is_sum domain).\n"
    "        return Combo(num_matrices, True)\n"
    "    scalar_leads = num_scalars > 0 and not has_explicit_matrix  # type: bool\n"
    "    return Combo(num_matrices, scalar_leads)\n"
)

# ---------------------------------------------------------------------------
# 7. VACUOUS NON-TERMINATION (uniqueness) — an impl that never returns. It
# spins forever (while i stays >= 0 with i increasing), so every value
# postcondition (E1/E2/E3) is satisfiable only vacuously: no execution reaches
# a return. This is the exact spec-too-weak class the G-PANEL-1 auditor
# exploited before the MustTerminate obligation was added (atk_5: an infinite
# `while True: pass` inserted into the real _postprocessor after the
# `if not matrices` early return, verifying against the value-only spec while
# hanging the whole sympy test suite). Under Requires(MustTerminate(2)) the
# loop takes no termination obligation and has no decreasing measure, so
# Nagini's obligation system MUST reject it ("Obligation leak check failed").
# The invariant is only what the spinning loop maintains — the reject must
# come from the obligation system, not a broken proof of a correct impl.
# ---------------------------------------------------------------------------
_REJ_NONTERM = (
    "    # WRONG: diverge before returning; all value postconditions hold only\n"
    "    # vacuously. Must be rejected by the MustTerminate(2) obligation.\n"
    "    i = 0  # type: int\n"
    "    while 0 <= i:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i)\n"
    "        # invariants-end\n"
    "        i = i + 1\n"
    "    return Combo(num_matrices, False)\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS),
        "rationale": "A structurally-different but behaviourally-identical impl "
                     "(is_sum dispatched first, fresh local for the product "
                     "branch, no loops/folds so no induction lemma needed) must "
                     "verify; satisfies E1/E2/E3 on every input. If it cannot, "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-sum-no-scalar",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "A contract-free caller (_admiss_caller, injected into the "
                     "impl region) calls postprocess on the discriminating "
                     "F2P-shaped input postprocess(is_sum=True, num_matrices=2, "
                     "num_scalars=0, has_explicit_matrix=False), forcing "
                     "Requires(num_matrices>=1 and num_scalars>=0) AND the fresh "
                     "MustTerminate(2) obligation to be discharged at the call "
                     "site; the probe asserts E2 (no scalar arg) and E1 "
                     "(count==2). If the precondition rejected this normal "
                     "input, PRECOND-TOO-STRONG.",
    },
    {
        "id": "uniq-prepatch-sum-inject-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_PREPATCH),
        "refinement": "This is exactly model_prepatch.py / the pre-patch final "
                      "return: for a SUM with no genuine scalar term it collapses "
                      "the empty scalar collection into Add.identity == Zero() and "
                      "injects it into MatAdd(Zero, *matrices). The faithful real "
                      "patch (this branch) makes Add(ZeroMatrix, ZeroMatrix) a "
                      "scalar Zero, so test_zero_matrix_add FAILS and "
                      "block_collapse(b*b*b) raises 'Zero' object has no attribute "
                      "'cols' -> test_issue_17624 FAILS. Both F2P unresolved.",
        "rationale": "Violates Ensures (E2) Implies(is_sum, scalar_arg_present == "
                     "False) on the sub-domain is_sum & num_scalars==0. The "
                     "rejection comes from the post-condition's discriminating "
                     "clause (the inserted fix).",
    },
    {
        "id": "uniq-sum-with-scalar-contaminates",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_SUM_WITH_SCALAR),
        "refinement": "For a SUM that DOES carry a genuine scalar term, the gold "
                      "patch holds the scalar apart "
                      "(cls._from_args(nonmatrices + [MatAdd(*matrices)])): the "
                      "matrix-domain MatAdd is still formed from the matrix terms "
                      "alone, no scalar among its args. This rival keeps the scalar "
                      "among the matrix-domain sum's arguments, building a "
                      "different (scalar-contaminated) MatAdd node -> diverges from "
                      "the gold result on every scalar-bearing matrix sum, so the "
                      "matadd tests (test_matadd_of_matrices et al.) would not "
                      "match the gold canonical form.",
        "rationale": "Violates Ensures (E2) on the DISJOINT sub-domain is_sum & "
                     "num_scalars>0 (the sum-with-scalar branch), distinct from "
                     "the prepatch case.",
    },
    {
        "id": "uniq-product-no-absorb",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_PRODUCT_NO_ABSORB),
        "refinement": "For a PRODUCT with a scalar coefficient AND an explicit "
                      "matrix factor, the gold absorb loop folds the scalar into "
                      "the explicit matrix and clears nonmatrices, so no scalar "
                      "argument remains (scalar_arg_present==False). This rival "
                      "never absorbs and always leaves a scalar argument, building "
                      "a MatMul(scalar, *matrices) where the gold builds the absorbed "
                      "matrix product -> different result on every "
                      "scalar*explicit-matrix product (the test_bc_matmul / explicit "
                      "matrix product paths diverge from gold).",
        "rationale": "Violates Ensures (E3) Implies(not is_sum, scalar_arg_present "
                     "== (num_scalars>0 and not has_explicit_matrix)) on the "
                     "sub-domain is_sum=False & num_scalars>0 & has_explicit_matrix "
                     "(rhs is False, rival returns True).",
    },
    {
        "id": "uniq-product-phantom-scalar",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_PRODUCT_PHANTOM_SCALAR),
        "refinement": "For a PRODUCT with NO genuine scalar term the gold drops the "
                      "trivial multiplicative identity (Mul.identity == One()), so "
                      "no scalar argument is present. This rival claims a scalar "
                      "argument is present -> builds MatMul(One(), *matrices) (or "
                      "equivalently asserts a coefficient) where the gold builds the "
                      "bare matrix product, diverging on every scalar-free matrix "
                      "product (test_bc_matmul matrix-only paths).",
        "rationale": "Violates Ensures (E3) on the sub-domain is_sum=False & "
                     "num_scalars==0 (rhs is False, rival returns True).",
    },
    {
        "id": "uniq-wrong-matrix-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_WRONG_COUNT),
        "refinement": "The scalar-arg facet is left CORRECT on every input, so a "
                      "scalar-bit fuzzer cannot detect this; but it drops one "
                      "matrix term (num_matrices-1) in the discriminating "
                      "SUM-no-scalar branch. The gold splats exactly *matrices into "
                      "MatAdd, preserving every matrix term; dropping one builds a "
                      "MatAdd over the wrong number of blocks -> block_collapse "
                      "produces a structurally wrong (or dimension-mismatched) "
                      "result, so test_issue_17624 / the block tests would not match "
                      "the gold BlockMatrix.",
        "rationale": "Violates Ensures (E1) Result().matrix_arg_count == "
                     "num_matrices in the is_sum & num_scalars==0 branch. Targets "
                     "the matrix-count facet that E2/E3 do not constrain.",
    },
    {
        "id": "uniq-sum-always-scalar-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_SUM_ALWAYS_SCALAR),
        "refinement": "Cheap supporting near-miss: every SUM is claimed to carry a "
                      "scalar coefficient argument. Faithful real patch would make "
                      "every matrix-term sum scalar-contaminated (the reported "
                      "'Zero'-has-no-'cols' crash class), so both F2P "
                      "(test_zero_matrix_add, test_issue_17624) stay unresolved.",
        "rationale": "Violates Ensures (E2) on the entire is_sum domain; subsumes "
                     "the two sum sub-domain attacks. Kept as a cheap supporting "
                     "case, not a substitute for the reasoned sub-domain rivals.",
    },
    {
        "id": "uniq-nonterm-vacuous",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_NONTERM),
        "refinement": "The faithful real-repo form of this rival is the audited "
                      "atk_5: insert `while True: pass` into _postprocessor after "
                      "the `if not matrices` early return, so every Add/Mul over "
                      ">=1 matrix term hangs. The SWE-bench harness times out "
                      "(900s) with both F2P (test_zero_matrix_add, "
                      "test_issue_17624) unresolved — it does NOT resolve, yet a "
                      "value-only spec verified it. MUST reject.",
        "rationale": "Diverges before returning, so E1/E2/E3 hold only "
                     "vacuously. Rejected exclusively by the "
                     "Requires(MustTerminate(2)) total-correctness obligation "
                     "('Obligation leak check failed'): the spinning loop takes "
                     "no termination obligation and has no decreasing measure. "
                     "Closes the G-PANEL-1 spec-too-weak finding.",
    },
]

# No @ContractOnly axioms in this bundle (meta.axioms == []; axioms region empty).
# The matrix-domain constructors are A-reference deep models validated by
# axiom_check.py / G-AX in-container, not consumed obligations the proof relies
# on, so there is no axiom-soundness / axiom-containment obligation a Docker probe
# could falsify here.
AXIOM_TESTS = []
