"""PBT falsification battery for pydata__xarray-7229.

Adversarially reasoned from the FROZEN spec of `rebuild_attrs` in model.py — the
model of `xarray.core.computation.where(cond, x, y, keep_attrs=True)`'s
post-patch level-by-level attribute rebuild.

Defended surface (the load-bearing postcondition clauses of `rebuild_attrs`):
  P-coord   : len(Result().coord_attrs) == len(x_coord_attrs) AND
              Forall k. Result().coord_attrs[k] == x_coord_attrs[k]      (EVERY case)
  P-top-ord : Implies(not top_unmatched, Result().attrs == x_attrs)
  P-top-pro : Implies(top_unmatched,     Result().attrs == 0)
  P-var-ord : Implies(not top_unmatched, Forall k. Result().var_attrs[k] == x_var_attrs[k])
  P-var-pro : Implies(top_unmatched and 0<=named_slot,
                      Result().var_attrs[named_slot] == x_attrs)
  P-frame   : x_coord_attrs / x_var_attrs are READ-ONLY (Acc(...,1/2) required AND
              ensured, ToSeq == Old) — the function may not write them.

Read-only inputs are present (x_coord_attrs, x_var_attrs at Acc(...,1/2)) so a
FRAME-MUTATION reject case is MANDATORY.

There is NO @Pure answer-key oracle and NO @ContractOnly axiom: every
postcondition is grounded directly in the input carriers (x_attrs,
x_coord_attrs[k], x_var_attrs[k]) — so the ungrounded-oracle-echo class does not
apply; see 'assessment'. There are no consumed axioms, so AXIOM_TESTS = [] (the
A-reference deep model is validated out-of-band by axiom_check.py / G-AX, which
runs the real callee — not duplicated here as a Docker probe lane).

Region surgery: every variant is built by `_swap` on a UNIQUE substring that
lies ENTIRELY inside the `rebuild_attrs` impl region (between # impl-start and
# impl-end). The frozen spec (axioms/pure/pre/post-conditions, invariants,
signatures, the WhereResult class) is never touched, so same_spec holds for
every spec case.

Obligation measures: `rebuild_attrs` requires MustTerminate(6), and Nagini
admits a call only at a STRICTLY LOWER measure than the caller's. So the
admissibility probes are appended as separate functions at MustTerminate(8)
rather than as in-body self-calls; a same-measure self-call is rejected for an
OBLIGATION LEAK (a call-graph property) rather than for the precondition, which
would misattribute PRECOND-TOO-STRONG to a domain that admits the input.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7229"
FLOAT_ENCODING = None  # meta.json: float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each is a unique fragment INSIDE the rebuild_attrs impl region.
# ---------------------------------------------------------------------------

# The coord-loop body (the per-coordinate fill that establishes P-coord).
_COORD_FILL = "        out_coords.append(x_coord_attrs[i])\n        i = i + 1"

# The matched-top-case var-loop body.
_VAR_ORD_FILL = "            out_vars.append(x_var_attrs[j])\n            j = j + 1"

# The matching-slot write in the top-unmatched case.
_PROMO_WRITE = (
    "            if j == named_slot:\n"
    "                out_vars.append(x_attrs)\n"
    "            else:\n"
    "                out_vars.append(0)")

# The top-level placement at the tail of the impl.
_TOP_PLACE = (
    "    if top_unmatched:\n"
    "        top = 0\n"
    "    else:\n"
    "        top = x_attrs\n"
    "    return WhereResult(top, out_coords, out_vars)")

# The very first executable line of the impl (a stable injection anchor).
_IMPL_HEAD = "    coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]"


# ===========================================================================
# POSITIVE CONTROL (soundness / verify) — a structurally-different but CORRECT
# impl that MUST verify (else SPEC-TOO-STRONG). We hoist the top-level mapping
# computation to the FRONT of the impl (before the loops) and reuse it at the
# return — a pure control-flow reorder + local-variable reshape. The loops and
# all their invariants are byte-identical, so no new lemma is needed (pilot
# pitfalls #2/#3 avoided: no framing assert is dropped, no loop direction
# flipped). The value produced is identical to the gold (top = 0 on top_unmatched,
# x_attrs otherwise), so every postcondition still holds.
# ===========================================================================
_POS_REORDER = _swap(
    _swap(_BASE, _IMPL_HEAD,
          "    # positive control: hoist the top-level placement (correct, reordered)\n"
          "    if top_unmatched:\n"
          "        top = 0\n"
          "    else:\n"
          "        top = x_attrs\n"
          "    coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]"),
    _TOP_PLACE,
    "    return WhereResult(top, out_coords, out_vars)")


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG).
#
# The witness is a probe FUNCTION appended at the tail of the impl region (which
# the spec view elides, so same_spec still holds and no separate spec-visible
# `def` is introduced). It must be a separate function rather than an in-body
# self-call, and the reason is the whole substance of this case's repair:
#
#   `rebuild_attrs` carries `Requires(MustTerminate(6))`. Nagini's obligation
#   discipline lets a caller invoke a callee only at a STRICTLY LOWER measure, so
#   an in-body self-call at the SAME measure is rejected with
#     "Obligation leak check failed. Callee rebuild_attrs might not take all
#      unsatisfied obligations from the caller."
#   — a property of the CALL GRAPH, not of the precondition's domain. The earlier
#   in-body form of this case therefore failed for a reason that had nothing to
#   do with admissibility, and G-PBT recorded the misattributed verdict
#   PRECOND-TOO-STRONG for a precondition that in fact admits the input fine.
#   Measured directly: the in-body form emits exactly the leak error above, while
#   the probe-function form below verifies.
#
# The probe sits at `MustTerminate(8)`, strictly above the callee's 6, so the
# call is legal and any failure is attributable to the PRECONDITION alone.
#
# Fault-injected control (so this is a live detector, not a rubber stamp):
# adding a domain-narrowing `Requires(len(x_coord_attrs) == 0)` to rebuild_attrs
# makes BOTH probes below fail with
#   "The precondition of method rebuild_attrs might not hold."
# i.e. a genuine PRECOND-TOO-STRONG, distinct from the leak error above.
#
# Two cases are probed because the precondition has a case-dependent
# conjunct (`Implies(top_unmatched, -1 <= named_slot < len(x_var_attrs))`), which is
# VACUOUS in the matched-top case and therefore untested by an matched-top-case
# witness alone.
# ===========================================================================

# The tail of the impl region — a stable anchor for appending a probe function.
_IMPL_TAIL = ("    return WhereResult(top, out_coords, out_vars)\n"
              "    # impl-end")

# Matched-top case (top_unmatched=False, named_slot=-1 so the Implies conjunct
# is vacuous): a one-coordinate / one-data-var F2P shape, the 3-DataArrays case.
_ADMISS = _swap(
    _BASE, _IMPL_TAIL,
    "    return WhereResult(top, out_coords, out_vars)\n"
    "\n"
    "\n"
    "def _admissibility_probe_matched() -> WhereResult:\n"
    "    # Admissibility witness at a STRICTLY HIGHER termination measure than\n"
    "    # the callee's (8 > 6), so the call cannot fail for an obligation leak\n"
    "    # and any failure is attributable to the precondition.\n"
    "    Requires(MustTerminate(8))\n"
    "    adm_coords = [5]  # type: List[int]\n"
    "    adm_vars = [9]  # type: List[int]\n"
    "    res = rebuild_attrs(7, adm_coords, adm_vars, False, -1)\n"
    "    Assert(res.attrs == 7)\n"
    "    Assert(len(res.coord_attrs) == 1)\n"
    "    Assert(res.coord_attrs[0] == 5)\n"
    "    Assert(len(res.var_attrs) == 1)\n"
    "    Assert(res.var_attrs[0] == 9)\n"
    "    return res\n"
    "    # impl-end")

# Unmatched-top case (top_unmatched=True, named_slot=0 in range): exercises the
# case-dependent precondition conjunct the matched probe leaves vacuous.
_ADMISS_PROMOTE = _swap(
    _BASE, _IMPL_TAIL,
    "    return WhereResult(top, out_coords, out_vars)\n"
    "\n"
    "\n"
    "def _admissibility_probe_unmatched() -> WhereResult:\n"
    "    # Same measure discipline as the matched probe (8 > 6). Here the\n"
    "    # case-dependent conjunct Implies(top_unmatched, -1 <= named_slot <\n"
    "    # len(x_var_attrs)) is LIVE rather than vacuous.\n"
    "    Requires(MustTerminate(8))\n"
    "    adm_coords = [5]  # type: List[int]\n"
    "    adm_vars = [9, 11]  # type: List[int]\n"
    "    res = rebuild_attrs(7, adm_coords, adm_vars, True, 0)\n"
    "    Assert(res.attrs == 0)\n"
    "    Assert(len(res.coord_attrs) == 1)\n"
    "    Assert(res.coord_attrs[0] == 5)\n"
    "    Assert(len(res.var_attrs) == 2)\n"
    "    Assert(res.var_attrs[0] == 7)\n"
    "    return res\n"
    "    # impl-end")


# ===========================================================================
# FRAME-MUTATION (uniqueness / reject) — MANDATORY. The source lists are
# read-only (Acc(...,1/2)). A rival writes to x_coord_attrs to satisfy a
# postcondition vacuously. Writing a list element requires FULL list_pred, but
# the function holds only 1/2 — so this must be REJECTED for INSUFFICIENT
# PERMISSION (P-frame), not for a value mismatch. The gold invariants are kept
# verbatim so the rejection is attributable to the write. Refinement: a faithful
# real patch that mutated x's own coordinate dicts in place would corrupt the
# read-only second argument; the test compares x's attrs against the expected
# (x is supposed to survive unchanged), so it would NOT resolve the F2P.
# ===========================================================================
_FRAME_MUT = _swap(
    _BASE, _IMPL_HEAD,
    "    # frame-mutation: write the read-only source list (needs full perm)\n"
    "    x_coord_attrs[0] = 0\n"
    "    coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]")

# Supporting frame-mutation near-miss: append to the read-only var list.
_FRAME_MUT_VAR = _swap(
    _BASE, _IMPL_HEAD,
    "    # frame-mutation: append to the read-only source var list (needs full perm)\n"
    "    x_var_attrs.append(0)\n"
    "    coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]")


# ===========================================================================
# VALUE / double-mask (uniqueness / reject) — THE headline pre-patch bug.
# Broadcast x's single TOP-LEVEL mapping to every output coordinate instead of
# copying each coordinate's OWN mapping. Violates P-coord (Forall k.
# coord_attrs[k] == x_coord_attrs[k]) whenever x_attrs != x_coord_attrs[k].
# Refinement: this is EXACTLY the bug the issue reports (coord attrs overwritten
# by variable/top-level attrs); the F2P sets x_coord = {"attr":"x_coord"} !=
# x_da = {"attr":"x_da"}, so assert_identical fails => would NOT resolve.
# ===========================================================================
_COORD_BROADCAST = _swap(
    _BASE, _COORD_FILL,
    "        out_coords.append(x_attrs)\n        i = i + 1")


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness / reject) — coord off-by-one. Fill every coordinate
# correctly EXCEPT the first slot, which is set to 0 (empty). Correct on the
# whole tail of the domain, wrong on index 0. Violates P-coord at k==0 (when
# x_coord_attrs[0] != 0). Refinement: a real patch that skipped the first
# coordinate would leave coordinate "a"'s attrs empty instead of {"attr":
# "x_coord"} — assert_identical on the F2P fails => would NOT resolve.
# ===========================================================================
_COORD_FIRST_WRONG = _swap(
    _BASE, _COORD_FILL,
    "        if i == 0:\n"
    "            out_coords.append(0)\n"
    "        else:\n"
    "            out_coords.append(x_coord_attrs[i])\n"
    "        i = i + 1")


# ===========================================================================
# PARTIAL-DOMAIN / case (uniqueness / reject) — unmatched-top top-level leak.
# In the unmatched-top case, set the output top-level mapping to x_attrs (the
# pre-patch over-broadcast) instead of 0. Violates P-top-pro (Implies(top_unmatched,
# Result().attrs == 0)). Refinement: this is the unmatched-top half of the
# reported defect; the desired behaviour leaves the top level EMPTY here. The
# F2P unmatched-top scenario asserts the output has EMPTY top-level attrs, so leaving x's
# top-level mapping there fails assert_identical => would NOT resolve.
# ===========================================================================
_PROMO_TOP_LEAK = _swap(
    _BASE, _TOP_PLACE,
    "    if top_unmatched:\n"
    "        top = x_attrs\n"
    "    else:\n"
    "        top = x_attrs\n"
    "    return WhereResult(top, out_coords, out_vars)")


# ===========================================================================
# PARTIAL-DOMAIN / case (uniqueness / reject) — matching-slot drop.
# In the unmatched-top case, write 0 to the matching data-var slot instead of
# x_attrs. Violates P-var-pro (Implies(top_unmatched and 0<=named_slot,
# var_attrs[named_slot] == x_attrs)). Refinement: the named sub-variable would
# lose x's attrs; the F2P unmatched-top scenario expects the data-var "x" to carry
# {"attr":"x_da"} (x's top-level mapping) — assert_identical fails => would NOT
# resolve. (The unmatched-top loop's own invariant
# Implies(0<=named_slot<j, out_vars[named_slot]==x_attrs) also fails, so the
# rejection is doubly attributable.)
# ===========================================================================
_PROMO_SLOT_DROP = _swap(
    _BASE, _PROMO_WRITE,
    "            if j == named_slot:\n"
    "                out_vars.append(0)\n"
    "            else:\n"
    "                out_vars.append(0)")


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness / reject) — ordinary var off-by-one. In the ordinary
# case, fill every data-var slot from x's own same-index var EXCEPT the first,
# set to 0. Violates P-var-ord at k==0 (when x_var_attrs[0] != 0). Refinement:
# the first data-var would lose x's per-var attrs; the 2-Datasets F2P scenario
# expects data-var "x" to carry {"attr":"x_da"} — assert_identical fails.
# Supporting near-miss complementing the coord off-by-one in the OTHER carrier.
# ===========================================================================
_VAR_FIRST_WRONG = _swap(
    _BASE, _VAR_ORD_FILL,
    "            if j == 0:\n"
    "                out_vars.append(0)\n"
    "            else:\n"
    "                out_vars.append(x_var_attrs[j])\n"
    "            j = j + 1")


SPEC_TESTS = [
    # ---- positive control (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-hoist-top",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "Structurally-different CORRECT impl: the top-level mapping "
                     "computation (top = 0 on top_unmatched else x_attrs) is hoisted to "
                     "the FRONT of the impl and reused at the return — a pure "
                     "control-flow reorder + local reshape. The two copy loops and "
                     "ALL their invariants are byte-identical (no dropped framing "
                     "assert, no loop-direction flip => no new lemma; pilot #2/#3 "
                     "avoided). It produces the identical value on every case, so "
                     "P-top-ord/P-top-pro/P-coord/P-var-* all still hold. If a "
                     "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "Admissibility witness appended as a probe FUNCTION at the tail "
                     "of the impl region (elided from the spec view, so same_spec "
                     "holds): build two fresh non-empty List[int] (a one-coordinate / "
                     "one-data-var F2P-shaped DataArray input) and call "
                     "rebuild_attrs(7, adm_coords, adm_vars, False, -1) in the "
                     "matched-top case (top_unmatched=False makes the Implies precond "
                     "vacuous), then assert the resulting mappings. Holding FULL "
                     "list_pred on the fresh lists, the 1/2 the callee Requires is "
                     "establishable. It must be a separate function, NOT an in-body "
                     "self-call: rebuild_attrs requires MustTerminate(6), and Nagini "
                     "admits a call only at a strictly LOWER measure, so a same-measure "
                     "in-body self-call is rejected for an OBLIGATION LEAK — a "
                     "call-graph property unrelated to the precondition, which "
                     "misattributes PRECOND-TOO-STRONG to a domain that actually "
                     "admits the input. The probe sits at MustTerminate(8) > 6, so the "
                     "call is legal and any failure is attributable to the "
                     "precondition. Live detector, not a rubber stamp: injecting "
                     "Requires(len(x_coord_attrs) == 0) makes this fail with 'The "
                     "precondition of method rebuild_attrs might not hold'. If the "
                     "precondition could not be met for this legitimate input => "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-shaped-input-unmatched",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_PROMOTE,
        "rationale": "Second admissibility shape, same measure discipline (probe at "
                     "MustTerminate(8) > the callee's 6). The matched-top-case witness "
                     "leaves the case-dependent precondition conjunct "
                     "Implies(top_unmatched, -1 <= named_slot < len(x_var_attrs)) VACUOUS, "
                     "so it is untested there. This probe calls rebuild_attrs(7, [5], "
                     "[9, 11], True, 0) with the conjunct LIVE (named_slot=0 in "
                     "range) — the shape where the output is richer than x — and asserts "
                     "the unmatched-top mappings (EMPTY top level, the named "
                     "sub-variable carrying the source's top-level mapping, "
                     "coordinates preserved). If this ordinary input fell "
                     "out of the domain => PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (MANDATORY; must be rejected for insufficient perm) ----
    {
        "id": "frame-mut-write-coord",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": "A faithful real patch that wrote into x's OWN coordinate "
                      "attribute dicts in place (rather than into the freshly built "
                      "output) would mutate the read-only second argument. The F2P "
                      "compares x's surviving state via assert_identical of separate "
                      "expected objects; corrupting x would diverge, so this would "
                      "NOT resolve the F2P.",
        "rationale": "x_coord_attrs is held at Acc(list_pred(.),1/2); writing an "
                     "element (x_coord_attrs[0] = 0) needs FULL list_pred. Nagini "
                     "must reject for INSUFFICIENT PERMISSION (P-frame), not for a "
                     "value mismatch. Gold invariants kept verbatim so the rejection "
                     "is attributable to the write. This is the project #1 weakness "
                     "class and a byte-fuzzer never finds it.",
    },
    {
        "id": "frame-mut-append-var",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT_VAR,
        "refinement": "Same as frame-mut-write-coord but on the var carrier: "
                      "appending to x_var_attrs mutates the read-only source and "
                      "also breaks ToSeq(x_var_attrs) == Old(ToSeq(x_var_attrs)). A "
                      "real patch mutating x in place would not resolve.",
        "rationale": "Supporting near-miss: x_var_attrs.append(0) needs FULL "
                     "list_pred but only 1/2 is held => rejected for insufficient "
                     "permission (P-frame).",
    },

    # ---- value / double-mask: the headline coord-broadcast bug ----
    {
        "id": "coord-broadcast-top",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _COORD_BROADCAST,
        "refinement": "This is EXACTLY the reported bug: each output coordinate "
                      "mapping is set to x's single top-level mapping (x_attrs) "
                      "instead of x's OWN per-coordinate mapping. The F2P sets "
                      "x_coord = {'attr':'x_coord'} distinct from x_da = "
                      "{'attr':'x_da'}; assert_identical on coordinate 'a' fails, so "
                      "a patch with this behaviour (the pre-patch lambda) does NOT "
                      "resolve.",
        "rationale": "Rejected by P-coord (Forall k. Result().coord_attrs[k] == "
                     "x_coord_attrs[k]): x_attrs is provably unequal to "
                     "x_coord_attrs[k] in general, so the postcondition cannot be "
                     "discharged. This is the model_prepatch coord half.",
    },

    # ---- partial-domain: coord first-slot wrong ----
    {
        "id": "coord-first-slot-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _COORD_FIRST_WRONG,
        "refinement": "Correct on every coordinate except index 0, which is left "
                      "empty (0). A real patch that skipped the first coordinate "
                      "would leave coordinate 'a' with empty attrs instead of "
                      "{'attr':'x_coord'}; the F2P asserts that coord, so it would "
                      "NOT resolve.",
        "rationale": "Rejected by P-coord at k==0 (Result().coord_attrs[0] must "
                     "equal x_coord_attrs[0], but 0 != x_coord_attrs[0] in general). "
                     "Partial-domain attack: pins all but the first element.",
    },

    # ---- partial-domain / case: unmatched-top top-level leak ----
    {
        "id": "unmatched-top-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PROMO_TOP_LEAK,
        "refinement": "In the unmatched-top case, the output top-level "
                      "mapping is left as x's top-level mapping (x_attrs) instead of "
                      "EMPTY. This is the unmatched-top half of the reported defect; "
                      "sets result.attrs = {}. The F2P 'DataArray + 1 Dataset' "
                      "scenario asserts the output has EMPTY top-level attrs, so "
                      "this would NOT resolve.",
        "rationale": "Rejected by P-top-pro (Implies(top_unmatched, Result().attrs == 0)): "
                     "x_attrs is not provably 0, so the unmatched-top branch "
                     "cannot discharge it. This is the verdict's D1 divergence.",
    },

    # ---- partial-domain / case: matching-slot drop ----
    {
        "id": "matching-slot-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PROMO_SLOT_DROP,
        "refinement": "In the unmatched-top case, the data-var bearing x's name is "
                      "written 0 instead of x's top-level mapping. The named "
                      "data-var 'x' would lose its attrs; the F2P unmatched-top scenario "
                      "expects data-var 'x' to carry {'attr':'x_da'} (x's top-level "
                      "mapping), so this would NOT resolve.",
        "rationale": "Rejected by P-var-pro (Implies(top_unmatched and 0<=named_slot, "
                     "Result().var_attrs[named_slot] == x_attrs)) — 0 != x_attrs "
                     "in general — and also by the unmatched-top loop invariant "
                     "Implies(0<=named_slot<j, out_vars[named_slot]==x_attrs).",
    },

    # ---- partial-domain: ordinary var first-slot wrong (supporting) ----
    {
        "id": "var-first-slot-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _VAR_FIRST_WRONG,
        "refinement": "Matched-top case: every data-var slot is filled from x's own "
                      "same-index var EXCEPT index 0, left empty. A real patch "
                      "skipping the first data-var would leave it with empty attrs; "
                      "the 2-Datasets F2P expects data-var 'x' to carry "
                      "{'attr':'x_da'}, so it would NOT resolve.",
        "rationale": "Rejected by P-var-ord at k==0 (Result().var_attrs[0] must "
                     "equal x_var_attrs[0]). Supporting partial-domain near-miss in "
                     "the var carrier (mirrors coord-first-slot-empty).",
    },
]


# No @ContractOnly axioms and no consumed deep-model axioms in this bundle
# (meta.axioms == []). The single A-reference deep model (rebuild_attrs ==
# real xarray.where(..., keep_attrs=True)) is validated out-of-band by
# axiom_check.py / G-AX (runs the real callee in the pinned container with the
# gold patch applied), so there is no Docker axiom-probe lane to duplicate here.
AXIOM_TESTS = []
