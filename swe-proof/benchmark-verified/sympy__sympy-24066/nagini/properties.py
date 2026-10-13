# properties.py — PBT falsification battery for sympy__sympy-24066.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (region-surgery: only the text strictly INSIDE the single # impl-start /
# # impl-end region is swapped). Because markers.same_spec compares the
# spec_view — which ELIDES the entire impl span (markers + nested invariants
# inclusive) — editing anything between # impl-start and # impl-end (including
# the loop invariants) preserves same_spec by construction; the frozen
# axioms / pure / pre-conditions / post-conditions regions are never touched.
#
# ---------------------------------------------------------------------------
# Defended surface (model.py `collect_argument_dimensions`):
#   collect_argument_dimensions(arg_dims: List[int]) -> List[int]
#   Requires:
#     (R0) Acc(list_pred(arg_dims), 1/2)                 # READ-ONLY input (half perm)
#     (R1) Forall k in [0,len): resolvable(arg_dims[k])  # element-wise domain
#     (R2) all_resolvable(ToSeq(arg_dims))               # fold-shaped domain
#   Ensures:
#     (E0) Acc(list_pred(arg_dims), 1/2)                 # input still read-only-held
#     (E1) Acc(list_pred(Result()))                      # result fully owned
#     (E2) all_resolvable(ToSeq(arg_dims))               # domain carried to post
#     (E3) len(Result()) == len(arg_dims)                # length pinned
#     (E4) ToSeq(Result()) == canon_seq(ToSeq(arg_dims)) # LOAD-BEARING value pin
#   where canon_seq is the front-recursive @Pure fold of canon_dim, and
#   canon_dim(c) = CANON_ONE() (==1) if is_dimensionless(c) else c.
#
# The fix (gold patch) canonicalises each *dimensionless* argument dimension to
# the canonical Dimension(1) (== CANON_ONE()); a non-dimensionless one is kept
# verbatim. Pre-patch every argument dimension flowed out unchanged. The
# load-bearing clause is (E4): on a dimensionless-but-non-canonical code c
# (is_dimensionless(c) True, c != CANON_ONE()) the gold must report CANON_ONE(),
# not c. model_prepatch.py (unconditional `result = [c] + result`) violates (E4)
# exactly there — the F2P test_issue_24062 witness time/(capacitance*impedance).
#
# ---------------------------------------------------------------------------
# WHICH WEAKNESS CLASSES APPLY (others justified-N/A in 'assessment'):
#
#  * FRAME-MUTATION: APPLIES and is MANDATORY. arg_dims is held at HALF
#    permission (R0/E0). A rival that WRITES into arg_dims to fabricate the
#    canonicalised codes in place must be REJECTED for insufficient permission.
#    Two framings: (a) write-then-read-back to satisfy (E4) vacuously; (b) a
#    pure-mutation no-op write. Both must reject. A byte fuzzer never tries this.
#
#  * PARTIAL-DOMAIN: the STRONG class here. The fix differs from the bug only on
#    the dimensionless-but-non-canonical sub-domain. Rivals: (i) the prepatch
#    verbatim impl (no canonicalisation — bug); (ii) inverted branch
#    (canonicalise the NON-dimensionless code, leave dimensionless verbatim);
#    (iii) first-element-only / last-element-only divergence; (iv) drop the head
#    canonicalisation only.
#
#  * UNGROUNDED-ORACLE ECHO: N/A as a *wrong* echo. The postcondition oracle
#    (canon_seq / canon_dim) is GROUNDED — a pure function of the input arg_dims,
#    fully unfolded (front-recursive), bottoming out in the opaque-but-pure
#    is_dimensionless. There is no answer-key the impl could echo to a WRONG
#    result and still verify: `return canon_seq(arg_dims)` materialised is the
#    correct answer, not a cheat. So instead of a wrong-echo reject we ship an
#    honest cheapest-impl positive control (the materialise-the-grounded-fold
#    impl) that MUST verify, plus the structurally-different positive control.
#
#  * CONTROL-FLOW-EFFECT: N/A. collect_argument_dimensions has no raise / no
#    return-vs-raise distinction modeled (the real callee's raise surface is
#    fenced OUT of the modeled domain by resolvable / all_resolvable, an axiom-
#    lane obligation, not a value-abstraction gap), and no second observable
#    output channel. The List[int] result + the read-only-preservation of
#    arg_dims capture every modeled observable; there is no capability-token
#    rival to build at the spec lane. (The partiality / raise surface IS attacked
#    — in the AXIOM lane, the soundness probe below.)
#
#  * POSITIVE CONTROL (soundness) + ADMISSIBILITY: included. CAUTION (directive
#    3): canon_seq is FRONT-recursive, so a FORWARD-append positive control would
#    need an f(a+b)==f(a)+f(b) lemma the verifier cannot auto-discharge. The
#    positive controls therefore KEEP the gold BACKWARD loop (front-recursive-
#    matching) and reshape only the per-element branch / locals, preserving every
#    gold invariant + framing assert (directive 2).
#
# ---------------------------------------------------------------------------
# AXIOM_TESTS: PRESENT. Two @ContractOnly axioms (resolvable, is_dimensionless,
# both A-consumed) + the canon_dim/canon_seq A-reference deep model. The probes
# re-run the REAL callees in the instance image (apply_gold where the obligation
# is post-patch) and:
#   - axiom-soundness (is_dimensionless): real DimensionSystem.is_dimensionless
#     returns a bool on every resolvable regime AND raises TypeError on the
#     non-resolvable witnesses resolvable() fences out (raise-surface fuzz).
#   - axiom-containment (resolvable): the model only ever feeds is_dimensionless
#     codes it has proven resolvable (R1/R2 + the impl's per-element resolvable
#     Assert); the probe confirms every caller-reachable regime (the three the
#     branch distinguishes, incl. the F2P non-canonical dimensionless) lies IN
#     the dimensionless test's domain (does not raise) — and the gold Function
#     branch end-to-end canonicalises as canon_dim claims (A-reference).
# The probes embed axiom_check.py's logic (it is NOT mounted in-container; the
# runner mounts only the probe). Read it on the host at load time and inline it.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-24066"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim text strictly BETWEEN "    # impl-start\n" and "    # impl-end\n"
# in model.py (the full impl region, INCLUDING the nested invariants block).
# Every variant is _BASE with this block replaced -> markers.same_spec == True
# by construction (the frozen axioms/pure/pre/post regions are never edited).
_IMPL = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(arg_dims), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(arg_dims))\n"
    "        # Every argument dimension code has a dimensionless verdict (the modeled\n"
    "        # domain), so each per-element test and the canonicalisation fold below\n"
    "        # are well-defined. Kept in both views: element-wise (per-element test)\n"
    "        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),\n"
    "                                                  resolvable(arg_dims[k])))))\n"
    "        Invariant(all_resolvable(ToSeq(arg_dims)))\n"
    "        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))\n"
    "        Invariant(len(result) == len(arg_dims) - i)\n"
    "        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))\n"
    "        # invariants-end\n"
    "        c = arg_dims[i - 1]\n"
    "        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))\n"
    "        # c is resolvable (element-wise view), so the per-element test below is\n"
    "        # defined; and the suffix one longer is all-resolvable (fold view), which\n"
    "        # is canon_seq's domain for the next iteration.\n"
    "        Assert(resolvable(c))\n"
    "        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))\n"
    "        if is_dimensionless(c):\n"
    "            result = [CANON_ONE()] + result\n"
    "        else:\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
    "    # At exit i == 0: the processed suffix is the whole sequence, whose domain\n"
    "    # and canonicalisation are exactly those of arg_dims.\n"
    "    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))\n"
    "    Assert(all_resolvable(ToSeq(arg_dims)))\n"
    "    return result\n"
)

# The frozen invariants + framing asserts that any backward-loop variant must
# KEEP to discharge the gold proof (directive 2). Reused by every variant that
# keeps the loop so we never accidentally drop a proof obligation.
_INV_AND_FRAME = (
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(arg_dims), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(arg_dims))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),\n"
    "                                                  resolvable(arg_dims[k])))))\n"
    "        Invariant(all_resolvable(ToSeq(arg_dims)))\n"
    "        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))\n"
    "        Invariant(len(result) == len(arg_dims) - i)\n"
    "        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))\n"
    "        # invariants-end\n"
    "        c = arg_dims[i - 1]\n"
    "        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))\n"
    "        Assert(resolvable(c))\n"
    "        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))\n"
)

_EXIT_FRAME = (
    "    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))\n"
    "    Assert(all_resolvable(ToSeq(arg_dims)))\n"
    "    return result\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Full model source with the whole impl region body replaced by new_impl
    (text strictly between # impl-start / # impl-end). same_spec preserved by
    construction (spec_view elides the entire impl span)."""
    return _swap(_BASE, _IMPL, new_impl)


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impl.
# Keeps the gold BACKWARD loop (matches the front-recursive canon_seq fold so no
# induction lemma is needed) and EVERY gold invariant + framing assert, but
# reshapes the per-element step: (a) the branch is INVERTED (test `not
# is_dimensionless(c)` first), and (b) the chosen code is bound to a typed local
# `nc` before the prepend, instead of two literal prepends. The verdict on every
# element is identical to gold (CANON_ONE for dimensionless, c otherwise), so
# (E4) holds. MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================
_POS = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # Inverted branch + local-binding reshape (same verdict per element).\n"
    "        # Declare the typed local once (a second `# type:` on the other branch\n"
    "        # is a mypy re-declaration error, not a spec rejection).\n"
    "        nc = c  # type: int\n"
    "        if not is_dimensionless(c):\n"
    "            nc = c\n"
    "        else:\n"
    "            nc = CANON_ONE()\n"
    "        result = [nc] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 5b. POSITIVE CONTROL (soundness, cheapest honest impl) — materialise the
# GROUNDED oracle. canon_seq is a pure function of the input, so the cheapest
# correct impl walks arg_dims backward and prepends canon_dim(c) directly (the
# per-element grounded oracle) rather than inlining the is_dimensionless branch.
# This is NOT an ungrounded-oracle cheat: canon_dim(c) IS the correct per-element
# answer (a function of c), and canon_seq(ToSeq(arg_dims)) IS the correct result.
# Keeps every gold invariant/frame; MUST verify (the grounded oracle is honest).
# ===========================================================================
_POS_ORACLE = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # Grounded per-element oracle: canon_dim(c) is a pure function of c\n"
    "        # (CANON_ONE() iff is_dimensionless(c) else c). Honest, not an echo.\n"
    "        cd = canon_dim(c)  # type: int\n"
    "        result = [cd] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 6. ADMISSIBILITY — the precondition must admit the discriminating F2P-shaped
# input. The F2P test_issue_24062 collects an applied Function exp(expr) with a
# SINGLE argument whose dimension is the non-canonical dimensionless
# time/(capacitance*impedance) -> a length-1 arg_dims with a resolvable code.
# To stay same_spec-safe we add NO new module-level symbol (that would alter the
# spec_view / signature). Instead we use the FIRST argument of arg_dims itself
# (guaranteed resolvable by R1) as the singleton seed: the precondition admits a
# length>=1 input, and the call on [arg_dims[0]] re-establishes R0 (half-perm
# read-only) / R1 (element-wise resolvable) / R2 (all_resolvable) for a real,
# in-domain singleton. If the precondition rejected this normal input,
# PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS2 = (
    "    # Admissibility: from a normal NON-EMPTY input, form the singleton\n"
    "    # [arg_dims[0]] (arg_dims[0] is resolvable by R1) and self-invoke. The\n"
    "    # call site must discharge the Requires (R0 half-perm, R1 element-wise\n"
    "    # resolvable, R2 all_resolvable) for this real in-domain input, else\n"
    "    # PRECOND-TOO-STRONG. We hold arg_dims read-only throughout.\n"
    "    if len(arg_dims) > 0:\n"
    "        Assert(resolvable(arg_dims[0]))\n"
    "        seed = arg_dims[0]  # type: int\n"
    "        single = [seed]  # type: List[int]\n"
    "        Assert(len(single) == 1)\n"
    "        Assert(single[0] == seed)\n"
    "        Assert(resolvable(single[0]))\n"
    "        # all_resolvable([seed]) unfolds to resolvable(seed) and all_resolvable([]).\n"
    "        Assert(all_resolvable(ToSeq(single).drop(1)))\n"
    "        Assert(all_resolvable(ToSeq(single)))\n"
    "        out = collect_argument_dimensions(single)  # type: List[int]\n"
    "        Assert(len(out) == 1)\n"
    "        Assert(ToSeq(out) == canon_seq(ToSeq(single)))\n"
    "    # Real logic (unchanged gold body).\n"
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        if is_dimensionless(c):\n"
    "            result = [CANON_ONE()] + result\n"
    "        else:\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 1a. FRAME-MUTATION (MANDATORY) — write into the read-only input to fabricate
# the canonicalised codes IN PLACE, then return arg_dims. arg_dims is held at
# HALF permission (R0); a write `arg_dims[i-1] = CANON_ONE()` requires FULL
# permission. MUST reject for INSUFFICIENT PERMISSION (not for a value reason).
# A byte fuzzer never tries to mutate the input. The gold invariants are kept
# verbatim so the rejection is attributable to the write, not a proof gap.
# ===========================================================================
_REJ_FRAME_WRITE = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # FRAME MUTATION: overwrite the read-only input in place. arg_dims is\n"
    "        # held at HALF permission (R0) -> this write is rejected for\n"
    "        # insufficient permission. (If it verified, the read-only contract is\n"
    "        # vacuous.)\n"
    "        if is_dimensionless(c):\n"
    "            arg_dims[i - 1] = CANON_ONE()\n"
    "        result = [arg_dims[i - 1]] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 1b. FRAME-MUTATION (supporting) — a pure no-op write to the read-only input
# (write a cell back to its own value). Even a value-preserving write needs FULL
# permission, so it MUST reject for insufficient permission. Confirms the
# half-permission frame condition is enforced for ANY store, not just a
# value-changing one.
# ===========================================================================
_REJ_FRAME_NOOP = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # FRAME MUTATION (no-op): write the cell back to its own value. Still\n"
    "        # needs FULL permission; arg_dims is half-held -> must reject.\n"
    "        arg_dims[i - 1] = c\n"
    "        if is_dimensionless(c):\n"
    "            result = [CANON_ONE()] + result\n"
    "        else:\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 3a. PARTIAL-DOMAIN — THE PREPATCH BUG. No canonicalisation: every argument
# dimension is reported verbatim (`result = [c] + result` unconditionally) =
# model_prepatch.py. Correct on the genuinely-dimensional sub-domain and on
# already-canonical codes, but WRONG on a dimensionless-but-non-canonical code
# (reports c instead of CANON_ONE()). MUST reject (violates E4).
# ===========================================================================
_REJ_PREPATCH = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # PRE-PATCH: report every argument dimension verbatim (no canonicalise).\n"
    "        result = [c] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 3b. PARTIAL-DOMAIN — INVERTED canonicalisation. Canonicalise the
# NON-dimensionless codes (report CANON_ONE() for them) and leave the
# dimensionless ones verbatim. Wrong on BOTH regimes whenever they differ from
# the gold verdict; in particular on a dimensionless-but-non-canonical code it
# returns c (gold: CANON_ONE()) and on a genuine dimension it returns CANON_ONE()
# (gold: c). MUST reject (violates E4 on both sub-domains).
# ===========================================================================
_REJ_INVERTED = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # INVERTED: canonicalise the NON-dimensionless codes, keep the\n"
    "        # dimensionless ones verbatim -- the exact opposite of the gold rule.\n"
    "        if is_dimensionless(c):\n"
    "            result = [c] + result\n"
    "        else:\n"
    "            result = [CANON_ONE()] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 3c. PARTIAL-DOMAIN — FIRST-ELEMENT-ONLY divergence. Canonicalise correctly for
# every element EXCEPT the first (index 0), which is always reported verbatim.
# (i==1 is the last loop iteration in the backward loop = the head of arg_dims.)
# Wrong only when arg_dims[0] is a dimensionless-but-non-canonical code. A test
# whose applied function's FIRST argument is never such a code would miss it.
# MUST reject (violates E4 on the head element).
# ===========================================================================
_REJ_FIRST_VERBATIM = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # FIRST-ELEMENT bug: skip the canonicalisation for index 0 (the head,\n"
    "        # reached at i == 1 in the backward loop).\n"
    "        if i > 1 and is_dimensionless(c):\n"
    "            result = [CANON_ONE()] + result\n"
    "        else:\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)

# ===========================================================================
# 3d. PARTIAL-DOMAIN — LAST-ELEMENT-ONLY divergence. Canonicalise correctly for
# every element EXCEPT the last (index len-1), reported verbatim. (i == len is
# the FIRST loop iteration in the backward loop = the tail of arg_dims.) Wrong
# only when arg_dims[len-1] is a dimensionless-but-non-canonical code. Disjoint
# from 3c. MUST reject (violates E4 on the tail element).
# ===========================================================================
_REJ_LAST_VERBATIM = (
    "    result = []  # type: List[int]\n"
    "    i = len(arg_dims)\n"
    "    while i > 0:\n"
    + _INV_AND_FRAME +
    "        # LAST-ELEMENT bug: skip the canonicalisation for index len-1 (the\n"
    "        # tail, reached at i == len(arg_dims) on the first backward iteration).\n"
    "        if i < len(arg_dims) and is_dimensionless(c):\n"
    "            result = [CANON_ONE()] + result\n"
    "        else:\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
    + _EXIT_FRAME
)


SPEC_TESTS = [
    {
        "id": "pos-control-inverted-branch-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS),
        "rationale": "Structurally-different but behaviourally-identical impl: the "
                     "per-element branch is inverted (`not is_dimensionless(c)` "
                     "first) and the chosen code is bound to a typed local before a "
                     "single prepend, instead of two literal prepends. Keeps the gold "
                     "BACKWARD loop (matches the front-recursive canon_seq fold, so no "
                     "induction lemma is needed) and EVERY gold invariant + framing "
                     "assert (directive 2). Every element yields the same verdict as "
                     "gold, so (E4) holds. MUST verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_ORACLE),
        "rationale": "Cheapest HONEST impl: prepend canon_dim(c) (the grounded "
                     "per-element oracle, a pure function of c) directly instead of "
                     "inlining the is_dimensionless branch. This is the positive "
                     "control standing in for the ungrounded-oracle slot: because the "
                     "oracle is GROUNDED in the input (canon_seq is a pure function of "
                     "arg_dims, fully unfolded), materialising it is the CORRECT answer, "
                     "not a cheat. MUST verify (else the spec rejects its own grounded "
                     "model => SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-f2p-singleton",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS2),
        "rationale": "Self-call on the F2P-shaped singleton [arg_dims[0]] (a real "
                     "in-domain code, resolvable by R1) forces the Requires (R0 "
                     "half-perm read-only, R1 element-wise resolvable, R2 "
                     "all_resolvable) to be discharged at the call site for a normal "
                     "single-argument input -- the exact shape of the F2P "
                     "test_issue_24062 (an applied Function exp(expr) with one "
                     "dimensionless argument). The probe asserts the result equals "
                     "canon_seq of the singleton. If the precondition rejected this "
                     "normal input, PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-write-inplace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_FRAME_WRITE),
        "refinement": "The faithful real patch corresponding to this rival mutates "
                      "the recursively-collected fds dimension components in place "
                      "(`d[1] = Dimension(1)`), then re-reads them. SWE-bench's "
                      "_collect_factor_and_dimension returns NEW tuples and the caller "
                      "(the Add/Mul branches and the test) re-collects from the "
                      "original expression tree; an in-place mutation of the argument "
                      "dimension objects would corrupt the SHARED Dimension instances "
                      "used elsewhere in the same collection (Dimensions are interned), "
                      "so the P2P unit-arithmetic tests (test_factor_and_dimension, "
                      "test_issue_20288) that re-collect the same units would observe "
                      "the corrupted dimension and FAIL -> not resolved. So a verifying "
                      "in-place-mutation rival is a true verify-not-resolve break.",
        "rationale": "REJECTS at the PERMISSION SYSTEM: arg_dims is held at HALF "
                     "permission (Requires/Ensures Acc(list_pred(arg_dims), 1/2)); the "
                     "store `arg_dims[i-1] = CANON_ONE()` needs FULL permission and "
                     "fails with insufficient permission. This is the #1 weakness "
                     "class -- if it verified, the read-only contract would be vacuous.",
    },
    {
        "id": "frame-mutation-noop-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_FRAME_NOOP),
        "refinement": "Even a value-preserving write (`arg_dims[i-1] = c`) is a STORE "
                      "into the read-only input. The faithful real patch would assign "
                      "into the caller-owned fds list the modeled branch only reads; "
                      "the gold patch builds a FRESH `dims` list and never mutates "
                      "`fds`, so a patch that wrote back into `fds` (even identically) "
                      "diverges from the gold control flow and is not the gold object. "
                      "Supporting case: confirms the half-perm frame condition is "
                      "enforced for ANY store, not only a value-changing one.",
        "rationale": "REJECTS at the PERMISSION SYSTEM (insufficient permission for "
                     "the store), independent of the value written. Demonstrates the "
                     "frame condition is about ownership, not value.",
    },
    {
        "id": "uniq-prepatch-no-canonicalise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_PREPATCH),
        "refinement": "This IS model_prepatch.py / the pre-patch Function branch: "
                      "`return (expr.func(...), *(d[1] for d in fds))` reports every "
                      "argument dimension VERBATIM (no Dimension(1) substitution). The "
                      "faithful real patch (revert the canonicalisation) makes "
                      "exp(time/(capacitance*impedance)) report the non-canonical "
                      "dimension, so 1 + exp(expr) hits the Add branch's `if dim != "
                      "addend_dim` with a structurally-unequal dimension and raises "
                      "ValueError -> the F2P test_issue_24062 FAILS -> not resolved.",
        "rationale": "Violates Ensures (E4) ToSeq(Result()) == canon_seq(...) on the "
                     "dimensionless-but-non-canonical sub-domain (reports c, gold "
                     "reports CANON_ONE()). This is exactly the spec sensing the "
                     "change (= the G-DIFF prepatch failure).",
    },
    {
        "id": "uniq-inverted-canonicalise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_INVERTED),
        "refinement": "Canonicalises the NON-dimensionless codes and keeps the "
                      "dimensionless ones verbatim -- the exact opposite rule. The "
                      "faithful real patch (`Dimension(1) if NOT is_dimensionless(d[1]) "
                      "else d[1]`) would (a) leave the F2P dimensionless argument "
                      "non-canonical so test_issue_24062 still raises, AND (b) collapse "
                      "every genuine dimension (length, mass, ...) to Dimension(1), "
                      "corrupting every dimensional-arithmetic P2P test "
                      "(test_factor_and_dimension etc.) -> not resolved.",
        "rationale": "Violates Ensures (E4) on BOTH regimes: a dimensionless code "
                     "yields c (gold CANON_ONE()) and a genuine code yields CANON_ONE() "
                     "(gold c). A maximally-wrong rival the value pin must reject.",
    },
    {
        "id": "uniq-first-element-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_FIRST_VERBATIM),
        "refinement": "Canonicalises every argument EXCEPT the first (the head of "
                      "expr.args), reported verbatim. The faithful real patch "
                      "(`dims = [d[1] if k==0 else (Dimension(1) if is_dimensionless... "
                      ")] `) would, on an applied multi-argument Function whose FIRST "
                      "argument is dimensionless-but-non-canonical, leak the "
                      "non-canonical dimension out of the first slot; the downstream "
                      "structural-equality comparison then rejects it -> a F2P-like "
                      "Add over such an expression FAILS -> not resolved. A test whose "
                      "first argument is never that regime would not catch it.",
        "rationale": "Violates Ensures (E4) on the head element (index 0, reached at "
                     "i==1) only. Partial-domain rival targeting the boundary the bulk "
                     "clauses leave implicit.",
    },
    {
        "id": "uniq-last-element-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_LAST_VERBATIM),
        "refinement": "Canonicalises every argument EXCEPT the last (index len-1), "
                      "reported verbatim -- disjoint from the first-element rival. On "
                      "an applied Function whose LAST argument is "
                      "dimensionless-but-non-canonical (the single-argument F2P case is "
                      "EXACTLY this: len==1 -> index 0 is also the last), the faithful "
                      "real patch leaks the non-canonical dimension -> the F2P "
                      "test_issue_24062 (single dimensionless argument) FAILS -> not "
                      "resolved.",
        "rationale": "Violates Ensures (E4) on the tail element (index len-1, reached "
                     "at i==len on the first backward iteration) only. Note: for the "
                     "length-1 F2P input the head and tail coincide, so this rival also "
                     "breaks the actual F2P witness -- the strongest partial-domain "
                     "attack.",
    },
]


# ===========================================================================
# AXIOM LANE. axiom_check.py is NOT mounted in-container (the runner mounts only
# the probe at /work), so its logic is read on the HOST at manifest-load time and
# inlined into each probe string. The probes import only sympy + stdlib, open any
# file with encoding="utf-8" (none needed here), CALL the real callees (never
# regex-scrape source), and sys.exit(0) iff the obligation holds.
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# Probe 1 — is_dimensionless axiom SOUNDNESS (A-consumed). Re-run the real
# DimensionSystem.is_dimensionless: it must return a bool on every resolvable
# regime (canonical / non-canonical dimensionless / genuine) AND raise TypeError
# on the non-resolvable witnesses resolvable() fences out (raise-surface fuzz).
# This is exactly axiom_check.py's A-consumed half, which is config-independent
# (the callee is unchanged by the patch, so it holds on base or gold). We run the
# WHOLE axiom_check.main(); apply_gold=True so the A-reference half (gold Function
# branch == canon_dim) is also exercised.
_PROBE_IS_DIMENSIONLESS = (
    "# embedded axiom_check.py (host-read at load time; not mounted in-container)\n"
    + _AXIOM_CHECK_SRC
)

# Probe 2 — resolvable axiom CONTAINMENT (A-consumed) + canon_dim A-reference.
# Enumerate EXACTLY the codes the MODEL can feed to is_dimensionless: every
# argument dimension, which the caller's Requires (R1/R2) + the impl's per-element
# `Assert(resolvable(c))` prove resolvable. Concretely the model reaches the three
# regimes the branch distinguishes (canonical, non-canonical dimensionless,
# genuine). The probe confirms each lies IN the dimensionless test's domain (the
# real callee returns a verdict, does not raise) -> resolvable covers every
# caller-reachable input. It then runs the gold Function branch end-to-end on the
# F2P scenario and asserts canon_dim's claim holds (A-reference).
_PROBE_RESOLVABLE_CONTAINMENT = (
    "import sys\n"
    "def _main():\n"
    "    from sympy import exp\n"
    "    from sympy.core.numbers import E\n"
    "    from sympy import S\n"
    "    from sympy.physics.units import (impedance, capacitance, time, ohm, farad,\n"
    "                                     second, length, mass)\n"
    "    from sympy.physics.units.quantities import Quantity\n"
    "    from sympy.physics.units.dimensions import Dimension\n"
    "    from sympy.physics.units.systems.si import SI\n"
    "    dimsys = SI.get_dimension_system()\n"
    "    is_dimensionless = dimsys.is_dimensionless\n"
    "    # The non-canonical dimensionless code from the F2P issue.\n"
    "    R = Quantity('R_ctn'); C = Quantity('C_ctn'); T = Quantity('T_ctn')\n"
    "    SI.set_quantity_dimension(R, impedance)\n"
    "    SI.set_quantity_dimension(C, capacitance)\n"
    "    SI.set_quantity_dimension(T, time)\n"
    "    R.set_global_relative_scale_factor(1, ohm)\n"
    "    C.set_global_relative_scale_factor(1, farad)\n"
    "    T.set_global_relative_scale_factor(1, second)\n"
    "    inner = T / (R * C)\n"
    "    inner_dim = SI._collect_factor_and_dimension(inner)[1]\n"
    "    # EXACTLY the codes the model can feed is_dimensionless (every argument\n"
    "    # dimension; the three regimes the branch distinguishes). CONTAINMENT:\n"
    "    # each must be IN the dimensionless test's domain (no raise).\n"
    "    reachable = [Dimension(1), inner_dim, length, mass,\n"
    "                 length / length, impedance, capacitance, time]\n"
    "    for d in reachable:\n"
    "        try:\n"
    "            v = is_dimensionless(d)\n"
    "        except Exception as e:\n"
    "            sys.stderr.write('CONTAINMENT VIOLATION: caller-reachable %r is '\n"
    "                             'OUTSIDE the dimensionless test domain (raised %s); '\n"
    "                             'resolvable would be too weak for the caller\\n'\n"
    "                             % (d, type(e).__name__))\n"
    "            return 1\n"
    "        if not isinstance(v, bool):\n"
    "            sys.stderr.write('is_dimensionless(%r) returned non-bool %r\\n'\n"
    "                             % (d, type(v)))\n"
    "            return 1\n"
    "    # The F2P non-canonical code is dimensionless yet != Dimension(1) -- the\n"
    "    # whole point; confirm so the containment isn't vacuous.\n"
    "    if not (is_dimensionless(inner_dim) is True and inner_dim != Dimension(1)):\n"
    "        sys.stderr.write('F2P code must be dimensionless yet non-canonical\\n')\n"
    "        return 1\n"
    "    # A-reference end-to-end (gold tree): exp(inner) reports CANON Dimension(1)\n"
    "    # and 1 + exp(inner) collects to (1 + E, Dimension(1)).\n"
    "    fdim = SI._collect_factor_and_dimension(exp(inner))[1]\n"
    "    if not (is_dimensionless(fdim) and fdim == Dimension(1)):\n"
    "        sys.stderr.write('gold Function branch did not canonicalise '\n"
    "                         'exp(dimensionless) to Dimension(1); got %r\\n' % (fdim,))\n"
    "        return 1\n"
    "    factor, dim = SI._collect_factor_and_dimension(S(1) + exp(inner))\n"
    "    if not (dim == Dimension(1) and factor == 1 + E):\n"
    "        sys.stderr.write('gold end-to-end F2P != (1 + E, Dimension(1)); '\n"
    "                         'got (%r, %r)\\n' % (factor, dim))\n"
    "        return 1\n"
    "    print('CONTAINMENT OK: every caller-reachable argument dimension is in '\n"
    "          'the dimensionless test domain (resolvable covers the caller); '\n"
    "          'canon_dim A-reference matches the gold Function branch + F2P.')\n"
    "    return 0\n"
    "sys.exit(_main())\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-is_dimensionless",
        "axiom": "is_dimensionless",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_IS_DIMENSIONLESS,
        "rationale": "Runs the REAL DimensionSystem.is_dimensionless (the unchanged "
                     "community callee the axiom models) in-container: it must be a "
                     "bool on every resolvable regime (canonical Dimension(1), "
                     "non-canonical dimensionless time/(capacitance*impedance), genuine "
                     "length/mass) AND raise TypeError on the non-resolvable witnesses "
                     "the model's resolvable() fences out (Dimension(length+mass), "
                     "Dimension(length-mass), Dimension(sin(length)), "
                     "Dimension(exp(length))). If the real callee returned a verdict "
                     "off the resolvable domain, the axiom would over-claim totality => "
                     "AXIOM-UNSOUND. This is axiom_check.py's directive-7 raise-surface "
                     "fuzz, embedded verbatim (apply_gold=True also exercises the "
                     "canon_dim A-reference end-to-end).",
    },
    {
        "id": "ax-cover-resolvable",
        "axiom": "resolvable",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_RESOLVABLE_CONTAINMENT,
        "rationale": "CONTAINMENT: the model only ever feeds is_dimensionless codes it "
                     "has proven resolvable (caller R1/R2 + the impl's per-element "
                     "Assert(resolvable(c))). The probe enumerates the codes the model "
                     "can actually reach -- every argument dimension, instantiated to "
                     "the three regimes the branch distinguishes incl. the F2P "
                     "non-canonical dimensionless -- and confirms each lies IN the "
                     "dimensionless test's domain (the real callee returns a verdict, "
                     "does not raise). A caller-reachable code OUTSIDE that domain would "
                     "be AXIOM-TOO-WEAK-FOR-CALLER. Covering MORE than the caller "
                     "reaches (the raising witnesses) is SOUND, not a defect; the probe "
                     "only checks containment of the reachable set, then validates the "
                     "canon_dim A-reference end-to-end on the gold tree.",
    },
]
