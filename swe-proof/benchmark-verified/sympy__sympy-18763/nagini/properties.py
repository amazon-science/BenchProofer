# properties.py — PBT manifest for sympy__sympy-18763. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# parses SPEC_TESTS / AXIOM_TESTS, executes each, and stamps RESULT.
#
# Instance surface (read model.py / refinement.md / mapping.md):
#   format_restriction(body: List[int], cond: List[int]) -> List[int]
#   assembles a constant LaTeX "restriction" layout around two ALREADY-RENDERED,
#   read-only fragments. The gold change inserts a matched scaling delimiter pair
#   \left( ... \right) directly around the body fragment.
#
#   Read-only inputs:  body, cond  both at Acc(list_pred(.), 1/2)  -> FRAME probes
#   Load-bearing post: ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond))
#                      where `assembled` is a @Pure GROUNDED function of the inputs
#                      (concatenation of constant code-point literals + body + cond),
#                      NOT an opaque answer-key oracle -> there is no "wrong echo"
#                      that verifies (see ungrounded-oracle note in `assessment`).
#   Structural posts:  len(Result()) == ...   and the take/drop clauses that pin the
#                      \left( open-delim immediately before, \right) close-delim
#                      immediately after the body copy (A4/A6, the discriminating ops).
#   Axioms: NONE (no @ContractOnly, no A-reference deep models) -> AXIOM_TESTS = [].
#
# Region-surgery discipline: every SPEC_TESTS module is built by _swap on _BASE,
# editing ONLY text that lies inside the # impl-start / # impl-end region (which
# includes the nested # invariants-start / # invariants-end blocks). The frozen
# spec (axioms/pure/pre-conditions/post-conditions + signature) is never touched,
# so markers.same_spec(base, module) is True for every case.
from pathlib import Path

INSTANCE = "sympy__sympy-18763"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact gold impl region (verbatim from model.py impl-start..impl-end body).
# Reused as the anchor for surgical swaps so we never disturb the spec.
# ---------------------------------------------------------------------------

# The body-copy loop, verbatim.
_BODY_LOOP = """    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body).take(i))
        # invariants-end
        result.append(body[i])
        i = i + 1"""

# The open-delim concatenation line (the load-bearing A4 op), verbatim.
_OPEN_DELIM_LINE = """    # open-delim (matched pair, before the body)
    result = result + [92, 108, 101, 102, 116, 40]"""

# The close-delim concatenation line (the load-bearing A6 op), verbatim.
_CLOSE_DELIM_LINE = """    # close-delim (matched pair, after the body)
    result = result + [92, 114, 105, 103, 104, 116, 41]"""


# ===========================================================================
# 1. POSITIVE CONTROL (soundness, expect=verify)
#    Structurally-different but CORRECT impl. We keep the gold two-loop proof
#    skeleton (the invariants the verifier relies on) intact, and change only
#    the EXECUTABLE shape: each constant code-point segment is first bound to a
#    typed local, then concatenated. This is a local-variable reshape (directive
#    3 / pilot-bug-3 safe: NO loop-direction flip, NO forward-append against a
#    front-recursive fold), so the gold loop invariants stay valid and the
#    verifier discharges the same obligations. If a faithful correct impl in a
#    different shape CANNOT verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS = _swap(
    _BASE,
    """    result = []  # type: List[int]
    # open-layout
    result = result + [92, 108, 101, 102, 116, 46, 32]
    # open-delim (matched pair, before the body)
    result = result + [92, 108, 101, 102, 116, 40]""",
    """    result = []  # type: List[int]
    # open-layout + open-delim, bound to locals first (executable reshape)
    seg_open_layout = [92, 108, 101, 102, 116, 46, 32]  # type: List[int]
    seg_open_delim = [92, 108, 101, 102, 116, 40]  # type: List[int]
    result = result + seg_open_layout
    result = result + seg_open_delim""",
)

# ===========================================================================
# 2. FRAME-MUTATION (uniqueness / frame, expect=reject)  -- MANDATORY (body is
#    a read-only Acc(list_pred(body), 1/2) input). A rival that WRITES to `body`
#    must be rejected for INSUFFICIENT PERMISSION (you can only mutate a list you
#    hold full Acc to; the contract grants only 1/2). The gold postcondition /
#    invariants are kept verbatim so the rejection is attributable solely to the
#    write. We mutate body then restore it, so the *value* abstraction would be
#    unchanged -- only the permission system can catch this.
# ===========================================================================
_FRAME_BODY = _swap(
    _BASE,
    _BODY_LOOP,
    """    if len(body) > 0:
        save = body[0]
        body[0] = save  # WRITE to a read-only (Acc 1/2) input -> must be rejected
""" + _BODY_LOOP,
)

# 2b. FRAME-MUTATION on the OTHER read-only input `cond`.
_FRAME_COND = _swap(
    _BASE,
    """    j = 0
    while j < len(cond):""",
    """    if len(cond) > 0:
        savec = cond[0]
        cond[0] = savec  # WRITE to a read-only (Acc 1/2) input -> must be rejected
    j = 0
    while j < len(cond):""",
)

# ===========================================================================
# 3. PARTIAL-DOMAIN (uniqueness, expect=reject). A rival CORRECT on every
#    non-empty body but diverging on the body-empty sub-domain: when body is
#    empty it ALSO drops the close-delim, producing \left( with no \right). The
#    F2P test `latex(3*Subs(-x+y,(x,),(1,)))` has a non-empty body so this rival
#    is correct THERE, but a faithful real patch that emits "\left(" without the
#    matched "\right)" for an empty inner expression breaks the matched-pair
#    invariant the whole change exists to guarantee -- it would NOT render the
#    bracketed group correctly and would diverge from the gold template on an
#    empty-body Subs. expect=reject: the unconditional `assembled` equality and
#    the close-delim take/drop clause must catch the missing \right) at len 0.
# ===========================================================================
_PARTIAL_EMPTY = _swap(
    _BASE,
    _CLOSE_DELIM_LINE,
    """    # close-delim (matched pair, after the body) -- DROPPED when body is empty
    if len(body) > 0:
        result = result + [92, 114, 105, 103, 104, 116, 41]""",
)

# 3b. PARTIAL-DOMAIN off-by-one: copy all body elements EXCEPT the last. Correct
#     on length-0/1? no -- diverges whenever len(body) >= 1, but we phrase it as a
#     loop bound `i < len(body) - 1` which still satisfies the per-iteration
#     invariant up to the bound; the FINAL `assembled` equality (full body) and
#     the length clause must reject it. A faithful patch that drops the last
#     character of the rendered inner expression renders garbage LaTeX and fails
#     the F2P string-equality assertion.
_PARTIAL_LASTCHAR = _swap(
    _BASE,
    """    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body).take(i))
        # invariants-end
        result.append(body[i])
        i = i + 1""",
    """    i = 0
    while i < len(body) - 1:
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(cond), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == open_layout() + open_delim()
                  + ToSeq(body).take(i))
        # invariants-end
        result.append(body[i])
        i = i + 1""",
)

# ===========================================================================
# 4. DROP-DELIM (uniqueness, expect=reject) -- the EXACT pre-patch bug surfaced
#    as a same-spec rival. Omit BOTH the open-delim (A4) and close-delim (A6)
#    around the body: the body fragment is dropped straight into the layout with
#    no matched \left( ... \right) pair. This is literally what model_prepatch.py
#    does and what the gold patch FIXES; its faithful real patch is the pre-patch
#    template, which the F2P `test_latex_subs` rejects (renders
#    `\left. x y \right|...` instead of `\left. \left(x y\right) \right|...`).
#    expect=reject: must fail the `assembled` equality + the open-delim take clause.
#    To keep the body loop's invariant well-formed once open_delim is gone we also
#    drop open_delim from the loop invariant (still inside the impl/invariants
#    region, so same_spec holds); the post-condition still demands open_delim.
# ===========================================================================
_DROP_DELIM = _swap(
    _swap(
        _BASE,
        _OPEN_DELIM_LINE + "\n",
        "",  # delete the open-delim concatenation entirely
    ),
    """    # close-delim (matched pair, after the body)
    result = result + [92, 114, 105, 103, 104, 116, 41]
""",
    "",  # delete the close-delim concatenation entirely
)
# the body loop invariant still references open_delim() but the impl no longer
# emits it, so the FIRST loop iteration's invariant `ToSeq(result) == open_layout()
# + open_delim() + ToSeq(body).take(i)` is already false at entry (result lacks
# open_delim) -> the rival cannot establish the loop invariant and fails to verify.
# That failure is in the impl/proof, the spec is untouched (same_spec holds).

# ===========================================================================
# 5. WRONG-CONSTANT (uniqueness, expect=reject, supporting). Swap one code point
#    of close_delim in the impl (41 ')' -> 40 '(') so the body's enclosing pair is
#    `\left(...\right(`, an unmatched delimiter. A faithful real patch emitting
#    `\right(` produces invalid LaTeX and fails the F2P string compare.
#    expect=reject: the close_delim take/drop clause and `assembled` equality pin
#    the exact byte 41.
# ===========================================================================
_WRONG_CLOSE = _swap(
    _BASE,
    """    # close-delim (matched pair, after the body)
    result = result + [92, 114, 105, 103, 104, 116, 41]""",
    """    # close-delim with a corrupted final byte (41 ')' -> 40 '(') => unmatched
    result = result + [92, 114, 105, 103, 104, 116, 40]""",
)

# ===========================================================================
# 6. ADMISSIBILITY (expect=verify). A positive-control caller proves the
#    precondition admits a normal, F2P-shaped input. The F2P case is
#    latex(3*Subs(-x+y,(x,),(1,))) where the inner expression renders to
#    "- x + y" (body) and the condition to "x=1" (cond) -- both ordinary non-empty
#    code-point lists. We add (inside the impl region) a self-call on freshly
#    constructed lists carrying those exact code points; if the Requires cannot be
#    established for this legitimate input => PRECOND-TOO-STRONG. The original
#    body still runs afterwards so the function's own postcondition is unaffected.
# ===========================================================================
_ADMISS_HEAD = """    # admissibility self-call on an F2P-shaped input ("- x + y" / "x=1")
    demo_body = [45, 32, 120, 32, 43, 32, 121]  # type: List[int]
    demo_cond = [120, 61, 49]  # type: List[int]
    Assert(len(demo_body) == 7)
    Assert(len(demo_cond) == 3)
    _demo = format_restriction(demo_body, demo_cond)
    Assert(len(_demo) == len(open_layout()) + len(open_delim())
           + len(demo_body) + len(close_delim()) + len(mid_layout())
           + len(demo_cond) + len(tail()))
"""
_ADMISS = _swap(
    _BASE,
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n" + _ADMISS_HEAD,
)


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "structurally-different CORRECT impl (constant segments bound "
                     "to typed locals first, gold two-loop proof + invariants kept "
                     "verbatim). Must verify; else SPEC-TOO-STRONG. Local-variable "
                     "reshape only (no loop flip / no fold lemma) so no proof gap.",
    },
    {
        "id": "frame-mutate-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_BODY,
        "refinement": "A real patch that writes into the already-rendered body "
                      "fragment is impossible/incorrect: latex_expr is an immutable "
                      "Python str the printer must not mutate; any such impl is not "
                      "the gold one-line template change and would not be accepted.",
        "rationale": "body is Acc(list_pred(body),1/2) read-only; the write "
                     "body[0]=save needs FULL permission. Rejection comes from the "
                     "permission system (insufficient permission), NOT from a value "
                     "clause -- value is restored so only framing catches it.",
    },
    {
        "id": "frame-mutate-cond",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_COND,
        "refinement": "Same as frame-mutate-body for the latex_subs fragment: the "
                      "condition string is immutable; a patch mutating it is not the "
                      "gold template change.",
        "rationale": "cond is Acc(list_pred(cond),1/2) read-only; cond[0]=savec needs "
                     "full permission -> rejected for insufficient permission.",
    },
    {
        "id": "partial-domain-empty-body-drops-close",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_EMPTY,
        "refinement": "A faithful patch that emits \\left( but conditionally skips "
                      "\\right) when the inner expression is empty produces an "
                      "unmatched scaling delimiter -- invalid LaTeX and divergent from "
                      "the gold unconditional template. It is correct on the non-empty "
                      "F2P body but wrong on an empty-body Subs, so it does not "
                      "faithfully implement the matched-pair change.",
        "rationale": "the UNCONDITIONAL postconditions ToSeq(Result())==assembled(...) "
                     "and the close_delim take/drop clause demand \\right) for ALL "
                     "bodies incl. len 0; dropping it on empty body must be rejected.",
    },
    {
        "id": "partial-domain-drop-last-body-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_LASTCHAR,
        "refinement": "Copying all but the last code point of the rendered inner "
                      "expression renders truncated LaTeX (e.g. '- x + ' instead of "
                      "'- x + y'); the F2P string-equality assertion fails. Such a "
                      "patch is not the gold verbatim-substitution behaviour.",
        "rationale": "the body loop stops at len(body)-1; the final `assembled` "
                     "equality (full ToSeq(body)) and the len(Result()) clause are "
                     "violated whenever len(body)>=1, so it must be rejected.",
    },
    {
        "id": "drop-delim-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_DELIM,
        "refinement": "This IS the pre-patch behaviour (body dropped into the layout "
                      "with no \\left( ... \\right) pair). The gold patch exists to add "
                      "that pair; the F2P test_latex_subs rejects the un-bracketed "
                      "rendering. model_prepatch.py reproduces it and fails on the same "
                      "`assembled` postcondition (meta G-DIFF).",
        "rationale": "removing open_delim/close_delim makes ToSeq(Result())!=assembled "
                     "and breaks the open-delim take clause + the body loop invariant; "
                     "spec untouched (same_spec) so the failure is the impl missing the "
                     "discriminating ops A4/A6.",
    },
    {
        "id": "wrong-close-delim-byte",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_CLOSE,
        "refinement": "Emitting \\right( (final byte 40 '(') instead of \\right) "
                      "produces an unmatched delimiter -- invalid LaTeX; the F2P string "
                      "compare fails. A supporting near-miss that still carries a real "
                      "refinement (the close delimiter must match the open one).",
        "rationale": "close_delim() is pinned to the exact byte 41 by the `assembled` "
                     "equality and the close_delim take/drop clause; byte 40 must be "
                     "rejected.",
    },
    {
        "id": "admissibility-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a self-call on the F2P-shaped input ('- x + y' / 'x=1') must "
                     "establish Requires(Acc(list_pred(body),1/2)) & "
                     "Requires(Acc(list_pred(cond),1/2)) for freshly built lists; if "
                     "the precondition rejected this legitimate input => "
                     "PRECOND-TOO-STRONG.",
    },
]

# No @ContractOnly axioms and no A-reference deep models (meta.axioms == [],
# deep_model_references == []). The changed op is a pure constant string-template
# assembly of two opaque already-rendered fragments; there is no real callee to
# axiomatize (mapping.md §3). Axiom lane is vacuous.
AXIOM_TESTS = []
