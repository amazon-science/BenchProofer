# properties.py — PBT falsification battery for astropy__astropy-13977.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants built by region-surgery (edits ONLY inside the
# # impl-start / # impl-end region, so the frozen spec — axioms/pure/pre/post —
# is byte-identical and same_spec holds). Each is checked by Nagini verify +
# markers.same_spec.
#
# Defended surface (from model.py + refinement.md + instance.json F2P):
#   dispatch_ufunc(io_kinds: List[int], recoverable_failure: bool) -> int
#     * io_kinds is READ-ONLY: Requires AND Ensures Acc(list_pred(io_kinds),1/2).
#       => FRAME-MUTATION is mandatory (a rival that writes io_kinds must be
#          rejected for insufficient permission).
#     * tri-state postcondition pins the outcome EXACTLY:
#         not recoverable_failure                       -> Result()==0  (A3)
#         recoverable_failure & all_recognised(...)      -> Result()==2  (A5)
#         recoverable_failure & has_custom_handler(...)  -> Result()==1  (A6)
#       all three clauses are present, so the spec is tri-state-complete; a wrong
#       rival must violate one of them.
#     * the oracle all_recognised/has_custom_handler is GROUNDED: a @Pure fold
#       fully unfolded over the input io_kinds (a function of the args), NOT an
#       opaque answer-key. There is no wrong echo to build => no ungrounded-oracle
#       case (see 'assessment'); instead a cheapest-honest positive control is
#       given. There is no raise/side-effect channel invisible to the value
#       abstraction (the three exits ARE the value), so no control-flow-effect
#       case.
#
# The discriminating F2P behaviour (astropy/units/tests/test_quantity_ufuncs.py
# TestUfuncReturnsNotImplemented::TestBinaryUfuncs::test_full[...]): a recoverable
# failure WITH a custom-handler operand (DuckQuantity3) present must yield
# NotImplemented (code 1), not surface the error (code 2). The mirror clause
# (all-recognised failure surfaces the error, code 2) is exercised by the
# empty/all-recognised operand collections.
from pathlib import Path

INSTANCE = "astropy__astropy-13977"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (all strictly INSIDE the # impl-start / # impl-end region).
# ---------------------------------------------------------------------------

# The leading success guard.
_SUCCESS_GUARD = (
    "    if not recoverable_failure:\n"
    "        # The protected evaluation completed; yield the ordinary result.\n"
    "        return 0\n"
)

# The final tri-state decision (after the loop).
_FINAL_DECISION = (
    "    if every_recognised:\n"
    "        # Every operand is a recognised built-in kind: surface the error.\n"
    "        return 2\n"
    "    # Some operand supplies a custom handler: abstain so it can be tried.\n"
    "    return 1\n"
)

# The per-operand write into the running flag (read-only; no write to io_kinds).
_FLAG_UPDATE = (
    "        if io_kinds[i - 1] != 0:\n"
    "            every_recognised = False\n"
)

# The loop header (back-to-front scan).
_LOOP_HEADER = "    i = len(io_kinds)\n    while i > 0:\n"


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness) ------------------------------------
    # Structurally-different but CORRECT: the final tri-state branch is
    # REORDERED (test `not every_recognised` first, abstain code 1; else
    # surface code 2). The backward loop, all three Invariants, and BOTH
    # framing Asserts are kept BYTE-IDENTICAL, so the gold proof obligations
    # the loop discharges (every_recognised == all_recognised(drop(i))) are
    # untouched — only the executable branch order changes. Must verify; if a
    # faithful correct reshape cannot => SPEC-TOO-STRONG.
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _FINAL_DECISION,
            "    if not every_recognised:\n"
            "        # Some operand supplies a custom handler: abstain so it can be tried.\n"
            "        return 1\n"
            "    # Every operand is a recognised built-in kind: surface the error.\n"
            "    return 2\n",
        ),
        "rationale": "a correct impl that only reorders the final decision "
                     "branch (same local every_recognised, loop+invariants+"
                     "asserts verbatim) must verify, else SPEC-TOO-STRONG.",
    },

    # --- ADMISSIBILITY ----------------------------------------------------
    # Assert, on the reachable operand index, the well-formedness fact the
    # precondition Forall promises (io_kinds[i-1] in {0,1}). It must discharge
    # for an F2P-shaped input; if the precondition were contradictory or its
    # trigger unusable in practice this would fail => PRECOND-TOO-STRONG.
    #
    # A Requires-Forall is known at method ENTRY but is not automatically a loop
    # invariant; inside the back-to-front loop the verifier only sees the
    # Invariants, so the well-formedness fact must be carried forward as a
    # proof-only loop invariant before it can be instantiated at k = i-1. That
    # invariant lives INSIDE the impl region (nested between invariants-start /
    # invariants-end, which spec_view elides), so same_spec with model.py is
    # preserved — this is a proof-engineering step, not a spec change. The
    # invariant is itself maintained directly from the precondition (io_kinds is
    # never written, held at Acc(...,1/2)), proving the precondition IS usable
    # on every reachable index. Gold loop/asserts otherwise verbatim.
    {
        "id": "admiss-wellformed-flag",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE,
                "        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))\n",
                "        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))\n"
                "        Invariant(Forall(int, lambda k:\n"
                "            (Implies(0 <= k and k < len(io_kinds),\n"
                "                     io_kinds[k] == 0 or io_kinds[k] == 1),\n"
                "             [[io_kinds[k]]])))\n",
            ),
            _FLAG_UPDATE,
            "        Assert(io_kinds[i - 1] == 0 or io_kinds[i - 1] == 1)\n"
            "        if io_kinds[i - 1] != 0:\n"
            "            every_recognised = False\n",
        ),
        "rationale": "the precondition's per-operand well-formedness "
                     "(io_kinds[k] in {0,1}) must be usable on a reachable "
                     "index for a normal input, else PRECOND-TOO-STRONG. "
                     "Carrying it as a loop invariant (an in-region, "
                     "same_spec-preserving proof step) lets it discharge.",
    },

    # --- FRAME-MUTATION (MANDATORY: io_kinds is Acc(...,1/2) read-only) ----
    # The rival WRITES to the read-only operand list (io_kinds[i-1] = 0) before
    # reading it. Functionally it would still compute the gold decision (it sets
    # the same value back for recognised operands and clobbers customs to 0),
    # but the half-permission Requires/Ensures forbids ANY write => the verifier
    # must reject for INSUFFICIENT PERMISSION on list_pred. The gold invariants
    # and decision are otherwise verbatim so the rejection is attributable to the
    # write, not to a logic change.
    {
        "id": "frame-mutation-write-io_kinds",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FLAG_UPDATE,
            "        if io_kinds[i - 1] != 0:\n"
            "            every_recognised = False\n"
            "            io_kinds[i - 1] = 0\n",
        ),
        "refinement": "the real dispatcher only READS the operand kinds "
                      "(getattr(type(io),'__array_ufunc__',None) membership); a "
                      "faithful patch that mutated the inputs+outputs operand "
                      "tuple in the except handler would corrupt the operands "
                      "before the reflected handler runs (and the operand tuple "
                      "is immutable), so it could not produce the values the F2P "
                      "test_full[...] cases assert — it would not resolve.",
        "rationale": "io_kinds is held at Acc(list_pred(io_kinds),1/2) "
                     "(Requires AND Ensures). A write needs full permission; the "
                     "permission system rejects it. Mechanical fuzzers never "
                     "mutate the input — this is the #1 weakness class.",
    },

    # --- PARTIAL-DOMAIN: skip the FIRST operand (index 0) ------------------
    # Loop stops at i>1 instead of i>0, so the operand at index 0 is never
    # inspected. A custom handler sitting at index 0 with all others recognised
    # is missed => every_recognised stays True => returns 2 (surface) where gold
    # abstains (1). Violates the load-bearing F2P clause
    #   Implies(recoverable_failure and has_custom_handler(...), Result()==1).
    # (The invariant is relaxed to i>=1 so the variant is well-formed and the
    # rejection comes from the POSTCONDITION, not a loop-invariant proof gap.)
    {
        "id": "partial-domain-skip-first-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(
                _BASE,
                "    i = len(io_kinds)\n    while i > 0:\n",
                "    i = len(io_kinds)\n    while i > 1:\n",
            ),
            "        Invariant(0 <= i and i <= len(io_kinds))\n",
            "        Invariant(1 <= i and i <= len(io_kinds))\n",
        ),
        "refinement": "this is the gold's pre-patch failure mode localized to "
                      "one operand: a real handler that never classified the "
                      "first operand (e.g. inputs_and_outputs[1:]) would, when "
                      "the custom DuckQuantity3 is the FIRST operand (the F2P "
                      "test_full[duck_quantity-quantity-...] orderings), re-raise "
                      "the TypeError/ValueError instead of returning "
                      "NotImplemented — the reflected handler never runs, so the "
                      "test asserts the wrong value and it does NOT resolve.",
        "rationale": "violates Ensures(Implies(recoverable_failure and "
                     "has_custom_handler(ToSeq(io_kinds)), Result()==1)) when "
                     "the only custom operand is at index 0.",
    },

    # --- PARTIAL-DOMAIN: always abstain on failure (drops the all-recognised
    #     -> surface clause; first-fails on the empty / all-recognised case) ---
    # Returns 1 unconditionally on a recoverable failure. Correct whenever a
    # custom handler is present, but on an ALL-recognised failure (e.g. the
    # `empty` operand list, where all_recognised([]) is True, or two plain
    # ndarrays) gold surfaces the error (code 2) — this abstains (1). Violates
    #   Implies(recoverable_failure and all_recognised(...), Result()==2).
    {
        "id": "partial-domain-always-abstain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    # Recoverable failure: inspect the operands (back-to-front) for any custom\n"
            "    # handler. `every_recognised` tracks all_recognised over the suffix drop(i).\n"
            "    every_recognised = True\n"
            "    i = len(io_kinds)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(io_kinds), 1 / 2))\n"
            "        Invariant(0 <= i and i <= len(io_kinds))\n"
            "        Invariant(every_recognised == all_recognised(ToSeq(io_kinds).drop(i)))\n"
            "        Invariant(MustTerminate(i + 1))\n"
            "        # invariants-end\n"
            "        # drop(i-1) front-decomposes as io_kinds[i-1] :: drop(i); one unfold of\n"
            "        # all_recognised then matches the running conjunction.\n"
            "        Assert(ToSeq(io_kinds).drop(i - 1)[0] == io_kinds[i - 1])\n"
            "        Assert(ToSeq(io_kinds).drop(i - 1).drop(1) == ToSeq(io_kinds).drop(i))\n"
            "        if io_kinds[i - 1] != 0:\n"
            "            every_recognised = False\n"
            "        i = i - 1\n"
            "    if every_recognised:\n"
            "        # Every operand is a recognised built-in kind: surface the error.\n"
            "        return 2\n"
            "    # Some operand supplies a custom handler: abstain so it can be tried.\n"
            "    return 1\n",
            # Always abstain on failure: never surface the error.
            "    # Always abstain on a recoverable failure (drops the surface path).\n"
            "    return 1\n",
        ),
        "refinement": "a real handler that returned NotImplemented for EVERY "
                      "caught TypeError/ValueError (never `raise e`) would "
                      "swallow genuine unit errors when all operands are "
                      "recognised built-ins (the `empty`/all-Quantity F2P "
                      "orderings expect the error surfaced, code 2): numpy, "
                      "seeing NotImplemented from both sides, raises a generic "
                      "TypeError rather than the original — the test asserts the "
                      "specific surfaced value/behaviour and it does NOT resolve.",
        "rationale": "violates Ensures(Implies(recoverable_failure and "
                     "all_recognised(ToSeq(io_kinds)), Result()==2)); first "
                     "fails on the all-recognised (incl. empty) failure case.",
    },

    # --- UNIQUENESS: flip the SUCCESS outcome -----------------------------
    # On a successful protected evaluation return code 1 (abstain) instead of 0.
    # Violates Implies(not recoverable_failure, Result()==0) directly — the
    # ordinary-result path is pinned. Cheap supporting case, but with a real
    # refinement: a patch that returned NotImplemented on SUCCESS would break
    # every non-failing ufunc call.
    {
        "id": "uniqueness-success-returns-abstain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    if not recoverable_failure:\n"
            "        # The protected evaluation completed; yield the ordinary result.\n"
            "        return 0\n",
            "    if not recoverable_failure:\n"
            "        # WRONG: abstain even though the evaluation succeeded.\n"
            "        return 1\n",
        ),
        "refinement": "a real patch returning NotImplemented when the protected "
                      "body SUCCEEDED would abstain on every ordinary "
                      "ufunc(quantity, quantity) call (the 322 P2P cases), "
                      "yielding the reflected/other operand's result or a "
                      "TypeError instead of the computed Quantity — it would "
                      "not resolve (massive P2P regression).",
        "rationale": "violates Ensures(Implies(not recoverable_failure, "
                     "Result()==0)); the success path is pinned to code 0.",
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# This bundle ships NO @ContractOnly axiom (meta.axioms == []). The one
# genuinely-new operation (the per-operand __array_ufunc__-membership
# classification + the abstain-vs-surface dispatch) is modelled DEEPLY in the
# pure region (all_recognised / has_custom_handler) and validated == the real
# numpy classification by axiom_check.py (G-AX). There is therefore no
# axiom-soundness or axiom-containment obligation to probe here.
AXIOM_TESTS = []
