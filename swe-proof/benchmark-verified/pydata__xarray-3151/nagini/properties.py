# properties.py — PBT manifest for pydata__xarray-3151. NOT a Nagini module; a
# record of adversarially-reasoned falsification cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT.
#
# Defended surface (reasoned from model.py, refinement.md, the gold patch and
# the F2P test test_combine_leaving_bystander_dimensions):
#
#   guard_rejects(is_joined, is_monotonic) returns a bool: True iff the
#   post-concatenation monotonicity guard of combine_by_coords would raise.
#   The single load-bearing postcondition is
#       Ensures(Result() == any_joined_nonmonotonic(ToSeq(is_joined),
#                                                    ToSeq(is_monotonic)))
#   where any_joined_nonmonotonic is a @Pure front-recursive existential that is
#   FULLY GROUNDED in the two input carriers (no opaque oracle / answer-key):
#   it is True iff some dimension with is_joined==1 has is_monotonic==0.
#
#   Both inputs are READ-ONLY: Requires(Acc(list_pred(x), 1/2)). So the
#   frame-mutation attack is MANDATORY (directive 5).
#
#   The guard carries Requires(MustTerminate(2)) — a total-correctness
#   obligation. A rival that diverges before returning (infinite loop) would
#   satisfy every value Ensures vacuously; the obligation system rejects any
#   loop lacking a decreasing termination measure. The gold scan discharges it
#   with Invariant(MustTerminate(i)). A side effect: a same-measure SELF-call
#   of guard_rejects is an obligation leak (callee measure not smaller), so
#   the contract cannot be discharged by re-invoking the routine itself.
#
#   The discriminating sub-domain the gold patch fixes (and the F2P exercises)
#   is exactly a dimension with is_joined==0 AND is_monotonic==0: the non-
#   monotonic bystander y=['a','c','b']. Pre-patch (loop over concatenated.dims)
#   wrongly rejects it; the gold (loop over concat_dims) must NOT. That is the
#   partial-domain pressure point.
#
# Region-surgery discipline: every spec variant is built by _swap on the frozen
# model.py, editing ONLY text inside the # impl-start / # impl-end region (the
# nested invariants live inside that region too, so same_spec stays True even
# when an invariant is touched). The frozen spec view is never altered.
from pathlib import Path

INSTANCE = "pydata__xarray-3151"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact gold inner test (nested ifs) inside the impl region. Unique anchor.
_GOLD_INNER = (
    "        if is_joined[i - 1] == 1:\n"
    "            if is_monotonic[i - 1] == 0:\n"
    "                rejected = True\n"
)

# The gold loop body keeps a bank of framing asserts + invariants; we reuse the
# helper offsets to phrase variants that keep those proof obligations intact.


# === POSITIVE CONTROL (soundness) ==========================================
# Structurally different but CORRECT: collapse the two nested `if`s into a
# single conjunction. Same right-to-left walk, same invariants, same framing
# asserts (so the gold proof obligations are preserved — directive #2 / #3).
# Must VERIFY; else SPEC-TOO-STRONG.
_POS_FLAT = _swap(
    _BASE, _GOLD_INNER,
    "        if is_joined[i - 1] == 1 and is_monotonic[i - 1] == 0:\n"
    "            rejected = True\n",
)


# A second positive control: keep nested-if shape but reorder the i decrement
# vs the unchanged `i = i - 1` semantics by introducing a typed local for the
# head flags before the test (a local-variable reshape, not a loop-direction
# flip). Keeps every invariant/assert; must VERIFY.
_POS_LOCALS = _swap(
    _BASE, _GOLD_INNER,
    "        jhead = is_joined[i - 1]  # type: int\n"
    "        mhead = is_monotonic[i - 1]  # type: int\n"
    "        if jhead == 1:\n"
    "            if mhead == 0:\n"
    "                rejected = True\n",
)


# === FRAME-MUTATION (uniqueness; MANDATORY — read-only inputs) =============
# A rival that WRITES to the read-only input is_joined to satisfy the
# postcondition vacuously. With only Acc(list_pred(is_joined), 1/2) the write
# must fail for INSUFFICIENT PERMISSION (you cannot mutate at 1/2). Gold
# invariants/asserts kept verbatim so the rejection is attributable to the
# write, not a proof regression. expect="reject".
_FRAME_MUT = _swap(
    _BASE, _GOLD_INNER,
    "        if is_joined[i - 1] == 1:\n"
    "            if is_monotonic[i - 1] == 0:\n"
    "                rejected = True\n"
    "        is_joined[i - 1] = is_joined[i - 1]\n",
)


# === PARTIAL-DOMAIN: the pre-patch bug (bystander cheat) ====================
# Reject on ANY non-monotonic dimension, regardless of is_joined — i.e. drop
# the is_joined guard. This is literally the pre-patch loop over all coordinate
# dimensions. On a bystander dim (is_joined==0, is_monotonic==0) it sets
# rejected=True where the spec (and gold) demand False. Must NOT verify; if it
# verifies the spec failed to defend the carried-through case => SPEC-TOO-WEAK.
_PARTIAL_BYSTANDER = _swap(
    _BASE, _GOLD_INNER,
    "        if is_monotonic[i - 1] == 0:\n"
    "            rejected = True\n",
)


# === PARTIAL-DOMAIN: ignore the head (last) dimension =======================
# Correct on every dimension EXCEPT it never inspects position 0 (the first
# dimension of the list / the last one the right-to-left walk would reach):
# loop stops at i > 1 instead of i > 0. On a 1-dimension input that is a joined
# non-monotonic dim (is_joined=[1], is_monotonic=[0]) it returns False where the
# spec demands True. Must NOT verify => else SPEC-TOO-WEAK on the boundary dim.
_PARTIAL_HEAD = _swap(
    _BASE,
    "    while i > 0:\n",
    "    while i > 1:\n",
)


# === SUPPORTING near-miss: constant False ===================================
# Cheapest wrong impl: never reject. Wrong on any joined non-monotonic dim
# (is_joined=[1], is_monotonic=[0] -> spec True). A supporting mechanical case;
# still carries a real refinement (it would never raise the ValueError the gold
# patch must still raise for a genuinely non-monotonic JOINED dimension).
# Written as a DELETION of the rejection branch rather than as `if False:`:
# Nagini's front end rejects a statement it can prove unreachable (`dead.code`),
# and a rival that fails to translate proves nothing about the spec (43c6680f6).
# A constant-false guard is not control flow, so this is the same rival.
_CONST_FALSE = _swap(
    _BASE, _GOLD_INNER,
    "        # Never reject: the rejection branch is absent entirely, so\n"
    "        # `rejected` keeps its initial False for every dimension.\n",
)


# === VACUOUS NON-TERMINATION (uniqueness) ===================================
# An impl that never returns: it spins forever in a loop that maintains only
# the (trivially preserved) permission invariants, so every value
# postcondition is satisfiable only vacuously — no execution reaches a return.
# This is the exact spec-too-weak class the G-PANEL-1 auditor exploited before
# the MustTerminate obligation was added (atk4_oracle_echo: a same-spec impl
# with an unreachable return verified against the value-only spec). Under
# Requires(MustTerminate(2)) the loop carries no termination measure, so
# Nagini's obligation system MUST reject it ("might not take all unsatisfied
# obligations"). The reject must come from the obligation system, not a
# postcondition mismatch.
_NONTERM = _swap(
    _BASE,
    "    rejected = False  # type: bool\n"
    "    i = len(is_joined)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(is_joined), 1 / 2))\n"
    "        Invariant(Acc(list_pred(is_monotonic), 1 / 2))\n"
    "        Invariant(len(is_joined) == len(is_monotonic))\n"
    "        Invariant(0 <= i and i <= len(is_joined))\n"
    "        Invariant(len(ToSeq(is_joined)) == len(is_joined))\n"
    "        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))\n"
    "        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))\n"
    "        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),\n"
    "                                                      ToSeq(is_monotonic).drop(i)))\n"
    "        # the scan consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure i, discharging\n"
    "        # MustTerminate(2) from the precondition.\n"
    "        Invariant(MustTerminate(i))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])\n"
    "        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])\n"
    "        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))\n"
    "        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))\n"
    "        if is_joined[i - 1] == 1:\n"
    "            if is_monotonic[i - 1] == 0:\n"
    "                rejected = True\n"
    "        i = i - 1\n"
    "    return rejected\n",
    # spin forever: the loop condition is always re-satisfied by the
    # non-advancing body, so the return below it is never reached at runtime
    # (but stays statically reachable, avoiding a dead-code type error). The
    # invariant bank is relaxed to what the spinning body maintains; the
    # reject must come from the obligation system, not a value clause.
    "    rejected = False  # type: bool\n"
    "    x = 0\n"
    "    while x == 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(is_joined), 1 / 2))\n"
    "        Invariant(Acc(list_pred(is_monotonic), 1 / 2))\n"
    "        # invariants-end\n"
    "        x = 0\n"
    "    return rejected\n",
)


# === SUPPORTING near-miss: constant True ====================================
# Always reject. Wrong on any all-clean input (is_joined=[1], is_monotonic=[1]
# -> spec False), and on the empty input (-> spec False). Supporting case.
_CONST_TRUE = _swap(
    _BASE,
    "    rejected = False  # type: bool\n",
    "    rejected = True  # type: bool\n",
)


# === ADMISSIBILITY ==========================================================
# Inside guard_rejects's OWN impl region (so same_spec is preserved — no new
# top-level symbol is added to the spec view) we build a fresh F2P-shaped
# literal input — the issue's case x joined+monotonic, y bystander+
# non-monotonic -> is_joined=[1,0], is_monotonic=[1,0] — and (a) ASSERT every
# value clause of the precondition on it (lengths equal, all flags 0/1): if any
# such Assert failed the Requires would be rejecting the F2P-shaped input
# (PRECOND-TOO-STRONG); and (b) ASSERT the grounded postcondition oracle yields
# the F2P answer False on it (no JOINED dim is non-monotonic — the bystander's
# non-monotonicity must not reject). The remainder of the impl (the normal
# right-to-left walk) is kept verbatim so the function still satisfies its
# postcondition.
#
# (The probe is deliberately CALL-FREE: guard_rejects carries a
# Requires(MustTerminate(2)) total-correctness obligation, so a same-measure
# self-call is an obligation leak by design — the vacuity fix intentionally
# forbids discharging the contract by re-invoking the routine itself. The
# call-free probe still checks exactly what the admissibility case is for:
# the precondition ADMITS the F2P-shaped input and the spec PINS the F2P
# answer on it.)
#
# PROOF NOTE (proof-gap fix, not a spec change): any_joined_nonmonotonic is a
# front-recursive @Pure fold, and Nagini does NOT auto-evaluate a recursive
# @Pure to its concrete value: to discharge the final Assert we walk the
# recursion one drop() per step (base case drop(2) empty -> drop(1) head (0,0)
# not-joined -> full head (1,1) joined-but-monotonic), each level giving the
# unfold for the next. These asserts live wholly inside the impl region
# (same_spec preserved) and only TEACH the verifier the value of the grounded
# existential; they do not alter the spec.
_ADMISS = _swap(
    _BASE,
    "    rejected = False  # type: bool\n",
    "    probe_joined = [1, 0]  # type: List[int]\n"
    "    probe_mono = [1, 0]  # type: List[int]\n"
    "    # (a) the precondition's value clauses hold for the F2P-shaped input\n"
    "    # (else the Requires would be rejecting it: PRECOND-TOO-STRONG).\n"
    "    Assert(len(probe_joined) == len(probe_mono))\n"
    "    Assert(probe_joined[0] == 1 and probe_joined[1] == 0)\n"
    "    Assert(probe_mono[0] == 1 and probe_mono[1] == 0)\n"
    "    # (b) the issue's non-monotonic-bystander input must NOT be rejected.\n"
    "    # Walk the front-recursive existential one drop() per step so the\n"
    "    # verifier evaluates any_joined_nonmonotonic([1,0],[1,0]) == False.\n"
    "    pj = ToSeq(probe_joined)  # type: PSeq[int]\n"
    "    pm = ToSeq(probe_mono)  # type: PSeq[int]\n"
    "    Assert(pj == PSeq(1, 0))\n"
    "    Assert(pm == PSeq(1, 0))\n"
    "    Assert(not any_joined_nonmonotonic(pj.drop(2), pm.drop(2)))\n"
    "    Assert(not any_joined_nonmonotonic(pj.drop(1), pm.drop(1)))\n"
    "    Assert(not any_joined_nonmonotonic(pj, pm))\n"
    "    rejected = False  # type: bool\n",
)


SPEC_TESTS = [
    {
        "id": "pos-flatten-inner-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLAT,
        "rationale": "structurally-different CORRECT impl (two nested ifs "
                     "collapsed into one conjunction; same right-to-left walk, "
                     "same invariants + framing asserts). Must verify against "
                     "Result()==any_joined_nonmonotonic; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-head-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCALS,
        "rationale": "local-variable reshape: bind the head flags to typed "
                     "locals before testing them. Keeps the gold proof "
                     "obligations; a faithful correct impl must verify.",
    },
    {
        "id": "admiss-f2p-bystander",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "a call-free probe builds the F2P-shaped input "
                     "(is_joined=[1,0], is_monotonic=[1,0]: the non-monotonic "
                     "bystander), asserts every value clause of the Requires "
                     "on it (the precondition must ADMIT it), and asserts the "
                     "grounded postcondition oracle yields the F2P answer "
                     "False on it (the bystander's non-monotonicity must not "
                     "reject). any_joined_nonmonotonic is a recursive @Pure "
                     "fold, so the concrete value False is taught to the "
                     "verifier by walking the drop() recursion (a proof "
                     "unfold, in-region, same_spec); else "
                     "PRECOND/SPEC-TOO-STRONG. (Call-free because the "
                     "MustTerminate obligation forbids a same-measure "
                     "self-call by design.)",
    },
    {
        "id": "vacuous-nonterminating-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NONTERM,
        "refinement": "a real patch whose guard spins forever instead of "
                      "answering would hang combine_by_coords: the F2P test "
                      "test_combine_leaving_bystander_dimensions never gets a "
                      "result and times out — it does NOT resolve. This is "
                      "the audit's P1 witness class (atk4_oracle_echo: a "
                      "same-spec impl whose return is unreachable verified "
                      "under the value-only contract).",
        "rationale": "MUST reject via the OBLIGATION system: the guard's "
                     "Requires(MustTerminate(2)) forces every loop on the "
                     "path to the return to carry a decreasing termination "
                     "measure; the while-True loop has none, so Nagini "
                     "reports an obligation leak. Under the pre-fix contract "
                     "(no MustTerminate) this rival VERIFIED — every Ensures "
                     "held vacuously on a path with no normal exit.",
    },
    {
        "id": "frame-mutate-readonly-is_joined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": "A faithful real patch that wrote to the read-only "
                      "metadata (e.g. overwriting concatenated's per-dimension "
                      "is_joined/coordinate to make the guard pass) would "
                      "corrupt the combined Dataset that combine_by_coords "
                      "returns; the F2P asserts assert_identical(expected, "
                      "actual), so the mutated result would NOT resolve.",
        "rationale": "is_joined is Requires(Acc(list_pred(is_joined),1/2)) — "
                     "read-only. The write `is_joined[i-1]=...` needs full "
                     "permission and must fail for INSUFFICIENT PERMISSION "
                     "(permission system), not a postcondition mismatch.",
    },
    {
        "id": "weak-drop-is_joined-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_BYSTANDER,
        "refinement": "This is exactly the PRE-PATCH bug: inspecting every "
                      "coordinate dimension instead of only concat_dims. On the "
                      "F2P input the non-monotonic bystander y=['a','c','b'] "
                      "(is_joined=0,is_monotonic=0) makes combine_by_coords "
                      "raise the spurious ValueError, so "
                      "test_combine_leaving_bystander_dimensions FAILS "
                      "(assert_identical never reached) — would NOT resolve.",
        "rationale": "fails the loop invariant rejected == "
                     "any_joined_nonmonotonic(ToSeq(is_joined).drop(i), ...): a "
                     "bystander dim sets rejected=True where the grounded "
                     "existential is False (postcondition clause).",
    },
    {
        "id": "weak-skip-head-dimension",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_HEAD,
        "refinement": "Never inspecting position 0 means a length-1 input that "
                      "is a genuinely non-monotonic JOINED dimension "
                      "(is_joined=[1], is_monotonic=[0]) is accepted, so "
                      "combine_by_coords would FAIL to raise where it must "
                      "(the gold patch still raises on a real non-monotonic "
                      "joined dim) — diverges from gold, would NOT resolve.",
        "rationale": "the loop exits at i>1, leaving the i==1 step unprocessed; "
                     "the final-iteration invariant rejected == "
                     "any_joined_nonmonotonic(ToSeq(is_joined).drop(1)) cannot "
                     "be strengthened to drop(0) at exit, so the postcondition "
                     "rejected == any_joined_nonmonotonic(...) fails.",
    },
    {
        "id": "weak-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _CONST_FALSE,
        "refinement": "Never rejecting (supporting near-miss) drops the "
                      "ValueError the gold patch still raises for a real "
                      "non-monotonic joined dimension; a faithful patch that "
                      "removed the raise would not match gold behaviour and "
                      "would not resolve the broader guard contract.",
        "rationale": (
            "always leaves rejected=False, so the scan's own invariant "
            "`rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i), "
            "ToSeq(is_monotonic).drop(i))` (model.py:142-143) stops being preserved "
            "at the first joined non-monotonic dimension. Measured verbatim: `Loop "
            "invariant might not be preserved` on that assertion. At loop exit i==0 "
            "and drop(0) is the whole sequence, so that invariant IS the "
            "postcondition Result() == any_joined_nonmonotonic(...): the refutation "
            "is the postcondition's, reported one step earlier because the invariant "
            "restates it per prefix. Smallest witness is_joined=[1], is_monotonic=[0] "
            "(spec True, impl False). If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _CONST_TRUE,
        "refinement": "Always rejecting is the over-strict opposite of the bug: "
                      "it would raise ValueError even on the all-monotonic / "
                      "empty case, so combine_by_coords would reject valid "
                      "inputs and FAIL P2P/F2P (the expected Dataset is never "
                      "returned) — would NOT resolve.",
        "rationale": "postcondition fails on the empty input (spec False) and "
                     "on is_joined=[1], is_monotonic=[1] (spec False).",
    },
]


# No @ContractOnly axioms are consumed by this bundle (axioms region is empty;
# meta.json axioms == []). The only deep model, any_joined_nonmonotonic, is an
# A-reference validated by axiom_check.py / G-AX (already pass). The PBT axiom
# lane (which runs probes against a CONSUMED axiom's real callee) therefore has
# nothing to attack here; the A-reference equivalence is covered by the existing
# G-AX gate. See 'assessment' for the explicit justification.
AXIOM_TESTS = []
