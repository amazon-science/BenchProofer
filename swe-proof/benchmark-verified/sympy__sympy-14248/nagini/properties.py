"""properties.py — PBT falsification battery for sympy__sympy-14248.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT.

Defended surface (read tasks/sympy__sympy-14248/model.py + refinement.md):

  Three modeled functions, all sharing the same skeleton (a BACKWARD loop
  i=len(xs); while i>1 that PREPENDS each rendered piece, matching a
  front-recursive @Pure fold via the invariant ToSeq(result)==fold(xs, i)):

    render_sum(terms)        — pinned by  ToSeq(Result()) == matadd(ToSeq(terms))
                               (spaced binary-minus join: a leading-'-' term →
                                ' - ' + stripped body; first term: '+' blanked,
                                a leading-'-' first term keeps its '-').
    render_sum_space(terms, negs)
                             — pinned by  ToSeq(Result()) == matadd_space(ToSeq(terms), ToSeq(negs))
                               (single-space join, term KEPT in full: a
                                STRUCTURALLY-negative non-leading term (negs[k],
                                the S(item.args[0]).is_negative fact, an input
                                alongside the rendered term) → ' ' + the FULL
                                term; else ' + ' + term; first term emitted in
                                full. The decision is negs[k], NOT a test on
                                the rendered text).
    render_product(factors,neg)
                             — pinned by  ToSeq(Result()) == matmul(ToSeq(factors),neg)
                               (factors joined by '*', a single leading '-' iff neg).

  EVERY input is READ-ONLY: Requires/Ensures(Acc(list_pred(xs), 1/2)). So the
  #1 weakness class — frame mutation — applies to all three and is mandatory.

  The load-bearing postcondition clause in each case is a DEEPLY-UNFOLDED fold
  (matadd / matadd_space / matmul) that is fully a function of the args (the
  child renders are inputs). There is NO opaque @Pure answer-key / exact marker
  to echo: matadd(ToSeq(terms)) is not an oracle, it is the spelled-out result.
  So the ungrounded-oracle-echo class does NOT apply (a "return materialize(
  oracle)" reduces to the gold computation itself). See 'assessment'. Instead we
  carry honest positive controls plus partial-domain and cross-algorithm rivals,
  which is where THIS spec is actually attackable.

Same-spec is guaranteed by region-surgery: every variant is built by _swap on
the frozen model.py text editing ONLY lines that live strictly inside an
# impl-start/# impl-end block; the spec view (axioms/pure/pre/post/invariants/
signatures) is never touched.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14248"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- unique impl-region anchors (each occurs exactly once in model.py) -------
# Termination note (all three sites): the loops count DOWN -- i = len(xs) then
# `while i > 1` with `i = i - 1` -- so the measure of remaining iterations is `i`
# itself: it drops by exactly one per pass and the guard keeps it > 1 on entry,
# so it is still >= 1 (positive) at the last pass. Every anchor below carries
# that Invariant(MustTerminate(i)) line because model.py now does, and a variant
# spliced from an anchor that omitted it would raise AssertionError: drift.
# render_sum impl
_SUM_PIECE = "        piece = list(contrib(t))  # type: List[int]"
_SUM_HEAD = "    head = list(lead(t0))  # type: List[int]"
_SUM_RESULT0 = ("    # impl-start\n"
                "    result = []  # type: List[int]\n"
                "    i = len(terms)\n"
                "    while i > 1:\n"
                "        # invariants-start\n"
                "        Invariant(Acc(list_pred(terms), 1 / 2))\n"
                "        Invariant(Acc(list_pred(result)))\n"
                "        Invariant(1 <= i and i <= len(terms))\n"
                "        Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))\n"
                "        Invariant(MustTerminate(i))\n")
# render_sum_space impl
_SPACE_PIECE = "        piece = list(contrib_space(t, n))  # type: List[int]"
_SPACE_RESULT0 = ("    # impl-start\n"
                  "    result = []  # type: List[int]\n"
                  "    i = len(terms)\n"
                  "    while i > 1:\n"
                  "        # invariants-start\n"
                  "        Invariant(Acc(list_pred(terms), 1 / 2))\n"
                  "        Invariant(Acc(list_pred(negs), 1 / 2))\n"
                  "        Invariant(Acc(list_pred(result)))\n"
                  "        Invariant(1 <= i and i <= len(terms))\n"
                  "        Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))\n"
                  "        Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))\n"
                  "        Invariant(MustTerminate(i))\n")
# render_product impl
_PROD_PIECE = "        piece = list(star() + t)  # type: List[int]"
_PROD_NEG = "    if neg:\n        result = [45] + result\n    return result"
_PROD_RESULT0 = ("    # impl-start\n"
                 "    result = []  # type: List[int]\n"
                 "    i = len(factors)\n"
                 "    while i > 1:\n"
                 "        # invariants-start\n"
                 "        Invariant(Acc(list_pred(factors), 1 / 2))\n"
                 "        Invariant(Acc(list_pred(result)))\n"
                 "        Invariant(1 <= i and i <= len(factors))\n"
                 "        Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))\n"
                 "        Invariant(MustTerminate(i))\n")


# =========================== POSITIVE CONTROLS ===============================
# Structurally-different but CORRECT impls that MUST verify (else SPEC-TOO-STRONG).
# We keep the gold BACKWARD-fold proof (same invariant, same per-step prepend,
# same Assert framing) and only reshape the executable surface — hoisting the
# head computation BEFORE the loop into a local, and routing the per-step
# prepend through an explicit temporary. This avoids a forward-append-vs-
# front-recursive-fold lemma gap (PBT_PLAN §3/§5a) entirely: the proof is
# byte-for-byte the same obligations, only statement ordering / locals differ.
# Termination: both reshapes keep the gold's descending counter untouched
# (i = len(xs); while i > 1; i = i - 1), so each carries the gold's own measure
# `i`. Hoisting the head out of the loop and routing the prepend through a temp
# add no iteration and change nothing the measure counts.

_POS_SUM = """    # impl-start
    head = list(lead(terms[0]))  # type: List[int]
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(head)))
        Invariant(len(ToSeq(terms)) == len(terms))
        Invariant(1 <= i and i <= len(terms))
        Invariant(ToSeq(head) == lead(ToSeq(terms)[0]))
        Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
        Invariant(MustTerminate(i))
        # invariants-end
        t = terms[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        piece = list(contrib(t))  # type: List[int]
        tmp = piece + result  # type: List[int]
        result = tmp
        i = i - 1
    result = head + result
    return result
    # impl-end"""

_POS_PRODUCT = """    # impl-start
    result = []  # type: List[int]
    i = len(factors)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(factors))
        Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
        Invariant(MustTerminate(i))
        # invariants-end
        t = factors[i - 1]
        Assert(ToSeq(factors)[i - 1] == t)
        star_t = list(star() + t)  # type: List[int]
        result = star_t + result
        i = i - 1
    head = list(factors[0])  # type: List[int]
    if neg:
        body_full = head + result  # type: List[int]
        signed = [45] + body_full  # type: List[int]
        result = signed
    else:
        result = head + result
    return result
    # impl-end"""


# =============================== ADMISSIBILITY ===============================
# The precondition (Acc(list_pred(terms), 1/2) & len(terms) >= 1) must admit a
# normal F2P-shaped input and let a normal (non-raising) return be reached. We
# prove admissibility INSIDE render_sum's impl region (so same_spec is preserved
# — appending a new function would add its signature to the spec view): at entry
# we read the half-permission input (ToSeq(terms), terms[0]), assert the minimal
# in-domain shape len(terms) >= 1 holds, and the gold body then returns normally.
# If these could not be discharged for a legitimate input => PRECOND-TOO-STRONG.
# The boundary input the F2P first exercises is a 1-element list (the body's
# while i>1 loop runs zero times, the leading-term path alone), so we pin that
# minimal shape is admissible.
# Termination: the gold body verbatim, so the gold measure `i`. Note the boundary
# input this case pins (a 1-element list) runs the loop ZERO times -- the measure
# is never even evaluated there, which is fine: MustTerminate bounds remaining
# iterations only for the passes that happen.

_ADMISS_SUM = """    # impl-start
    # admissibility: the half-permission input is readable and the minimal
    # in-domain shape (a single leading term) is admitted; a normal return
    # is reachable from the gold body below.
    Assert(len(terms) >= 1)
    Assert(ToSeq(terms)[0] == terms[0])
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
        Invariant(MustTerminate(i))
        # invariants-end
        t = terms[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        piece = list(contrib(t))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(lead(t0))  # type: List[int]
    result = head + result
    return result
    # impl-end"""


# ============================ FRAME-MUTATION (reject) ========================
# MANDATORY: every input is read-only (Acc(list_pred(xs), 1/2)). A rival that
# WRITES to the read-only input to (vacuously) satisfy the postcondition must be
# rejected for INSUFFICIENT PERMISSION. We keep the entire gold impl verbatim and
# only PREPEND a write to the input, so the rejection is attributable to the
# write, not to any downstream proof obligation.

_FRAME_SUM = _SUM_RESULT0.replace(
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n"
    "    terms[0] = terms[0]  # frame-mutation: write to a 1/2-perm input\n",
    1,
)
_FRAME_SPACE = _SPACE_RESULT0.replace(
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n"
    "    terms[0] = terms[0]  # frame-mutation: write to a 1/2-perm input\n",
    1,
)
_FRAME_PRODUCT = _PROD_RESULT0.replace(
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n"
    "    factors[0] = factors[0]  # frame-mutation: write to a 1/2-perm input\n",
    1,
)


SPEC_TESTS = [
    # ----------------------------- soundness ------------------------------
    {
        "id": "pos-sum-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _SUM_RESULT0 + (
            "        # invariants-end\n"
            "        t = terms[i - 1]\n"
            "        Assert(ToSeq(terms)[i - 1] == t)\n"
            "        piece = list(contrib(t))  # type: List[int]\n"
            "        result = piece + result\n"
            "        i = i - 1\n"
            "    t0 = terms[0]\n"
            "    head = list(lead(t0))  # type: List[int]\n"
            "    result = head + result\n"
            "    return result\n"
            "    # impl-end"), _POS_SUM),
        "rationale": "render_sum: same backward fold proof (same invariant, same "
                     "Assert framing, same per-step prepend), only statement order "
                     "and locals reshaped (head hoisted, prepend via a temp). A "
                     "structurally-different CORRECT impl MUST verify; if not => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-product-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _PROD_RESULT0 + (
            "        # invariants-end\n"
            "        t = factors[i - 1]\n"
            "        Assert(ToSeq(factors)[i - 1] == t)\n"
            "        piece = list(star() + t)  # type: List[int]\n"
            "        result = piece + result\n"
            "        i = i - 1\n"
            "    t0 = factors[0]\n"
            "    head = list(t0)  # type: List[int]\n"
            "    result = head + result\n"
            "    if neg:\n"
            "        result = [45] + result\n"
            "    return result\n"
            "    # impl-end"), _POS_PRODUCT),
        "rationale": "render_product: same backward '*'-fold proof; the leading-sign "
                     "branch is restructured into an explicit if/else over named "
                     "temporaries that still computes [45]+head+result iff neg. Must "
                     "verify (else SPEC-TOO-STRONG on the product postcondition).",
    },
    # --------------------------- admissibility ----------------------------
    {
        "id": "admiss-sum-readable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _SUM_RESULT0 + (
            "        # invariants-end\n"
            "        t = terms[i - 1]\n"
            "        Assert(ToSeq(terms)[i - 1] == t)\n"
            "        piece = list(contrib(t))  # type: List[int]\n"
            "        result = piece + result\n"
            "        i = i - 1\n"
            "    t0 = terms[0]\n"
            "    head = list(lead(t0))  # type: List[int]\n"
            "    result = head + result\n"
            "    return result\n"
            "    # impl-end"), _ADMISS_SUM),
        "rationale": "render_sum precondition (Acc(list_pred(terms),1/2) & len>=1) must "
                     "admit a normal input. Inside the impl we read the half-permission "
                     "input (ToSeq(terms), terms[0]) and assert the minimal in-domain "
                     "shape len(terms)>=1, then the gold body returns normally. All "
                     "discharge for a legitimate input; if not => PRECOND-TOO-STRONG. "
                     "Edits live strictly inside the impl region, so same_spec holds.",
    },
    # -------------------------- frame-mutation (reject) -------------------
    {
        "id": "frame-sum-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SUM_RESULT0, _FRAME_SUM),
        "refinement": "Writing terms[0] back to itself is observationally a no-op in "
                      "Python, but the rival's POINT is that a mutating real patch "
                      "(e.g. reusing the children list to overwrite an element with a "
                      "re-signed copy) would corrupt the caller's parenthesized-args "
                      "list that StrPrinter._print_MatAdd shares — _print recurses over "
                      "the SAME expr.args, so a faithful mutating patch changes sibling "
                      "renders and FAILS test_MatrixSymbol_printing. The model forbids it "
                      "for free.",
        "rationale": "render_sum input terms is Acc(list_pred(terms), 1/2) (read-only); "
                      "an assignment terms[0]=... needs FULL permission, so it is "
                      "rejected for INSUFFICIENT PERMISSION by the permission system. If "
                      "it verified, the half-permission frame guarantee would be "
                      "vacuous => SPEC-TOO-WEAK.",
    },
    {
        "id": "frame-sum-space-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SPACE_RESULT0, _FRAME_SPACE),
        "refinement": "Same as frame-sum-write but for the pretty single-space site: a "
                      "mutating patch that overwrites the per-item picture list would "
                      "clobber shared prettyForm children and break "
                      "test_MatrixSymbol_printing's pretty assertions. The read-only "
                      "frame forbids it.",
        "rationale": "render_sum_space input terms is 1/2-permission; terms[0]=... "
                      "requires full permission => rejected for insufficient permission "
                      "(else the frame guarantee is vacuous, SPEC-TOO-WEAK).",
    },
    {
        "id": "frame-product-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PROD_RESULT0, _FRAME_PRODUCT),
        "refinement": "A mutating _print_MatMul that overwrote the rendered-factor list "
                      "(e.g. to fold the sign into the first factor in place) would alter "
                      "the shared args rendering and FAIL str(-A*B*C)=='-A*B*C'. The "
                      "half-permission frame on factors forbids the write.",
        "rationale": "render_product input factors is Acc(list_pred(factors), 1/2); "
                      "factors[0]=... needs full permission => rejected for insufficient "
                      "permission (else SPEC-TOO-WEAK).",
    },
    # ------------------------- partial-domain (reject) --------------------
    {
        "id": "weak-sum-plusjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _SUM_PIECE,
                  "        piece = list(sep_plus() + t)  # type: List[int]"),
            _SUM_HEAD, "    head = list(t0)  # type: List[int]"),
        "refinement": "This is the PRE-PATCH ' + '.join(terms) with a bare first term and "
                      "no leading-minus handling (model_prepatch.py). On the F2P witness "
                      "str(A - A*B - B), terms=['-B','-A*B','A'], gold renders "
                      "'-B - A*B + A' but this renders '-B + -A*B + A' (and a leading-'-' "
                      "first term would not be normalised) => FAILS "
                      "test_MatrixSymbol_printing. Faithful real patch does NOT resolve.",
        "rationale": "It is correct only on the sub-domain where NO non-leading term "
                      "begins with '-' (and the first term is non-negative); it diverges "
                      "exactly on the sign-bearing inputs the F2P exercises. Rejected by "
                      "the invariant ToSeq(result)==add_tail(ToSeq(terms),i): contrib(t) "
                      "for a leading-'-' t is ' - '+body(t), not ' + '+t.",
    },
    {
        "id": "weak-sum-head-strip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SUM_HEAD, "    head = list(body(t0))  # type: List[int]"),
        "refinement": "Keeps the correct ' - ' tail discipline but renders the FIRST "
                      "term as body(t0) — stripping a leading minus from term 0. On "
                      "str(A - A*B - B), terms=['-B','-A*B','A'], gold='-B - A*B + A' but "
                      "this drops the leading '-' on '-B', giving 'B - A*B + A' => FAILS "
                      "test_MatrixSymbol_printing. A patch that blanked the first sign "
                      "unconditionally would not resolve.",
        "rationale": "Partial-domain: correct on every input whose first term is "
                      "non-negative, wrong exactly when term 0 begins with '-'. Rejected "
                      "by Ensures ToSeq(Result())==matadd: matadd's lead(terms[0]) is "
                      "PSeq(45)+body(t) for a negative leading term (keeps the '-'), not "
                      "body(t).",
    },
    {
        "id": "weak-space-as-str-discipline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SPACE_PIECE,
                        "        piece = list(contrib(t))  # type: List[int]"),
        "refinement": "This is the G-EQ counterexample (refinement.md A2/D): it renders "
                      "the pretty MatAdd site with the STR discipline (' - ' + stripped "
                      "body for a negative non-leading term) instead of the single-space, "
                      "minus-kept discipline. On the F2P witness "
                      "pretty(A*B*C - A*B - B*C), terms=['-A*B','-B*C','A*B*C'], the "
                      "required value is '-A*B -B*C + A*B*C' but this yields "
                      "'-A*B - B*C + A*B*C' (extra space, minus stripped) => FAILS "
                      "test_MatrixSymbol_printing's pretty assertion. Faithful patch "
                      "(porting str's algorithm to pretty) does NOT resolve.",
        "rationale": "render_sum_space is pinned to matadd_space (single space, term "
                      "kept in full, decided by the STRUCTURAL fact negs[k]), NOT matadd. "
                      "The invariant ToSeq(result)==add_tail_space(...) uses "
                      "contrib_space (sep_space()+t when negs[k], full term kept); "
                      "substituting contrib (sep_minus()+body(t), decided on the rendered "
                      "text) violates it. This is the cross-algorithm rival the whole §A2 "
                      "deep model exists to reject.",
    },
    {
        "id": "weak-space-text-negativity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SPACE_PIECE,
                        "        piece = list(contrib_space(t, is_neg(t)))  # type: List[int]"),
        "refinement": "This is the panel's P1 attack (audit atk_7): it decides the pretty "
                      "join with the RENDERED-TEXT leading-minus test is_neg(t) instead of "
                      "the structural fact S(item.args[0]).is_negative that the gold "
                      "tests. The two diverge on admissible inputs: for item y*B with "
                      "Symbol('y', negative=True), S(item.args[0]).is_negative is True "
                      "but the rendered picture 'y\\u22c5B' has no leading '-', so the "
                      "gold emits '-A y\\u22c5B' (single space) while this rival emits "
                      "'-A + y\\u22c5B'. A real patch that ported the text test would NOT "
                      "reproduce the gold behaviour on such sums.",
        "rationale": "The spec now carries the structural negativity fact as the input "
                      "negs (mapping.md §2.2): contrib_space(t, n) keys on n, and the "
                      "invariant ToSeq(result)==add_tail_space(ToSeq(terms), ToSeq(negs), "
                      "i) pins each step to negs[i]. Substituting is_neg(t) for n fails "
                      "whenever negs[k] != is_neg(terms[k]) (both directions are "
                      "admissible), so the invariant is not preserved and the rival is "
                      "rejected. If it verified, the spec would again conflate the "
                      "structural test with the rendered text => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-product-drop-neg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PROD_NEG, "    return result"),
        "refinement": "This is the PRE-PATCH '*'.join(...) with NO leading sign "
                      "(model_prepatch_2.py): it drops the `neg` minus entirely. On "
                      "str(-A*B*C) / pretty(-A*B*C) the gold renders '-A*B*C' but this "
                      "renders 'A*B*C', and latex(-A) -> 'A' instead of '-A' => FAILS "
                      "test_MatrixSymbol_printing. The faithful pre-patch real patch does "
                      "NOT resolve.",
        "rationale": "Partial-domain: correct exactly on neg==False, wrong on every "
                      "negative-leading-coefficient product. Rejected by Ensures "
                      "ToSeq(Result())==matmul(ToSeq(factors),neg): matmul prepends "
                      "PSeq(45) iff neg, which the dropped branch no longer produces.",
    },
    {
        "id": "weak-product-always-neg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PROD_NEG, "    result = [45] + result\n    return result"),
        "refinement": "Unconditionally prepends '-' to EVERY product. On a positive "
                      "product str(A*B) the gold renders 'A*B' but this renders '-A*B' => "
                      "FAILS the non-negative MatMul cases. A patch that always emitted a "
                      "leading sign does not resolve.",
        "rationale": "Partial-domain (the complement of weak-product-drop-neg): correct "
                      "only on neg==True. Rejected by Ensures ToSeq(Result())==matmul(...,"
                      "neg): for neg==False matmul is joinstar(factors) with NO leading "
                      "minus.",
    },
]


# No @ContractOnly axioms and no A-reference deep models (meta.json axioms==[],
# deep_model_references==[]; G-AX vacuous). Both rendering behaviours are pure
# string-assembly logic modelled deeply with the child renders as inputs, so
# there is no real callee to probe.
AXIOM_TESTS = []  # type: list
