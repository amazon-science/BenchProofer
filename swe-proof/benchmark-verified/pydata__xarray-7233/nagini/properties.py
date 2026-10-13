# properties.py — PBT manifest for pydata__xarray-7233.
#
# NOT a Nagini module; a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) writes each `module` to a temp file, runs the
# Nagini verifier on the host, and checks `same_spec` against the frozen model.py.
# Every spec case is built by region-surgery: _swap edits ONLY text inside the
# # impl-start / # impl-end region (which includes the loop's # invariants-start /
# # invariants-end block — invariants live inside the impl region and are elided
# by spec_view), so the FROZEN spec (axioms/pure/pre/post-conditions) is never
# touched and same_spec is guaranteed.
#
# Defended surface (model.py rebuild_label_status):
#   * Inputs was_label, is_window, is_axis_name are READ-ONLY:
#     Requires(Acc(list_pred(x), 1/2)) and the postcondition RE-ASSERTS
#     Acc(list_pred(x), 1/2) for all three. Any impl that WRITES to an input
#     cannot return the half-permission and fails for INSUFFICIENT PERMISSION.
#     -> frame-mutation probes (MANDATORY).
#   * Four load-bearing postconditions, conjoined:
#       (P1) Forall k: Result()[k] == promoted(was_label[k], is_window[k],
#                                              is_axis_name[k])
#       (P2) Forall k: was_label[k] == 1    -> Result()[k] == 1
#       (P3) Forall k: is_axis_name[k] == 1 -> Result()[k] == 1
#       (P4) Forall k: was_label[k] == 0 and is_axis_name[k] == 0
#                                           -> Result()[k] == 0
#     P2 is the discriminating clause (prior labelling status is preserved
#     regardless of the windowed-axis bit); P3 is the container's standing
#     axis-name property; P4 closes the other direction so no position is left
#     free. Together P2/P3/P4 already pin every output bit, so P1 is not the
#     only thing carrying the value — an impl cannot satisfy P2/P3/P4 and still
#     differ from the gold on any input.
#     `promoted` is a @Pure helper but it is GROUNDED: its body is fully
#     unfolded ((wl&iw)|wl|ax) and its three Ensures clauses are provable from
#     that body. It is a function of the args, not an opaque answer key, so
#     there is no "wrong echo": echoing promoted(...) is exactly correct.
#   * TERMINATION (total correctness -- closes the vacuous-divergence hole): the
#     precondition carries Requires(MustTerminate(2)) and the loop consumes it
#     with Invariant(MustTerminate(len(was_label) - i + 1)). Without it a
#     same-spec impl that diverges before building `result` satisfies P1..P4
#     vacuously under Nagini's default partial correctness (the audited
#     G-PANEL-1 counterexample class). -> non-termination probe (MANDATORY).
from pathlib import Path

INSTANCE = "pydata__xarray-7233"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (everything below is elided by spec_view, so
# any edit here keeps same_spec=True). The gold impl body is:
#
#     wl = was_label[i]
#     iw = is_window[i]
#     ax = is_axis_name[i]
#     # status: (windowed-axis labels) | (all prior labels) | (axis names)
#     sel = 0
#     if wl == 1 and iw == 1:
#         sel = 1
#     if wl == 1:
#         sel = 1
#     if ax == 1:
#         sel = 1
#     Assert(sel == promoted(wl, iw, ax))
# ---------------------------------------------------------------------------

_GOLD_SEL = """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # status: (windowed-axis labels) | (all prior labels) | (axis names)
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        Assert(sel == promoted(wl, iw, ax))"""

# The first line of the impl region (used to splice a frame-mutation write
# before the loop, so the rejection is unambiguously the input write).
_IMPL_HEAD = "    result = []  # type: List[int]\n    i = 0\n"


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY: was_label is read-only Acc(...,1/2)) ------
# A rival that overwrites was_label[i] to 1 BEFORE computing sel. With the input
# forced to all-1 the loop trivially establishes P1/P2 against the mutated array
# -- but the function only holds Acc(list_pred(was_label), 1/2) (read
# permission), so the store `was_label[i] = 1` fails for INSUFFICIENT PERMISSION
# at translation/verification. This is the #1 weakness class and no byte-fuzzer
# reaches it. Gold asserts kept verbatim so the rejection is attributable solely
# to the write.
_frame_was = _swap(
    _BASE,
    _GOLD_SEL,
    """        was_label[i] = 1
        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        Assert(sel == promoted(wl, iw, ax))""",
)
SPEC_TESTS.append({
    "id": "frame-mut-was_label",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame_was,
    "refinement": "Writing was_label[i]=1 corresponds to the real construct() "
    "MUTATING the source object's coordinate-name set (set(self.obj.coords)) "
    "during the rebuild. A faithful patch that overwrote obj.coords would change "
    "the input Dataset's own coordinates -- the F2P asserts list(da.coords) is "
    "preserved on the ORIGINAL da, so corrupting da's coords fails the test. The "
    "spec must reject this: it only grants Acc(list_pred(was_label), 1/2).",
    "rationale": "Rejection from the permission system: the store to was_label[i] "
    "needs full Acc(list_pred(was_label)) but only 1/2 is held (Requires + the "
    "postcondition both grant 1/2 and require returning it), so insufficient "
    "permission. If it verified the read-only contract would be vacuous.",
})

# --- 2. FRAME-MUTATION on a second read-only input (is_window) ---------------
_frame_iw = _swap(
    _BASE,
    _GOLD_SEL,
    """        is_window[i] = 1
        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        Assert(sel == promoted(wl, iw, ax))""",
)
SPEC_TESTS.append({
    "id": "frame-mut-is_window",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame_iw,
    "refinement": "Writing is_window[i]=1 corresponds to construct() mutating "
    "set(window_dim) -- the dimension set being coarsened. The real routine reads "
    "window_dim; rewriting it would change which axes are reshaped and break the "
    "reshape the F2P depends on. The spec grants only Acc(list_pred(is_window),1/2), "
    "so this is read-only.",
    "rationale": "Rejection from the permission system: store to is_window[i] needs "
    "full permission but only 1/2 is held and must be returned (Ensures re-asserts "
    "Acc(list_pred(is_window),1/2)).",
})

# --- 2b. FRAME-MUTATION on the third read-only input (is_axis_name) ----------
# The axis-name bit is a property of the rebuilt container, READ by the rebuild.
# An impl that rewrites it to 1 makes P3/P4 trivial against a fabricated input.
_frame_ax = _swap(
    _BASE,
    _GOLD_SEL,
    """        is_axis_name[i] = 1
        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        Assert(sel == promoted(wl, iw, ax))""",
)
SPEC_TESTS.append({
    "id": "frame-mut-is_axis_name",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _frame_ax,
    "refinement": "Writing is_axis_name[i]=1 corresponds to construct() rewriting "
    "the rebuilt container's own axis-name set -- inventing axes the reshape did "
    "not create. The real routine only READS which insertion names coincide with "
    "the rebuilt container's axes; forcing that bit would promote every member and "
    "change list(result.data_vars), which the F2P observes.",
    "rationale": "Rejection from the permission system: store to is_axis_name[i] "
    "needs full permission but only 1/2 is held and the postcondition re-asserts "
    "Acc(list_pred(is_axis_name),1/2).",
})

# --- 3. PARTIAL-DOMAIN: the EXACT prepatch bug (intersection-only) -----------
# sel = (was_label AND is_window) OR is_axis_name: correct on every member
# EXCEPT one that was a labelling array whose name is not a windowed axis and
# whose insertion name is not one of the rebuilt container's axis names -- the
# demoted-non-dimensional-coordinate case the issue reports. This is
# model_prepatch.py's selection. It must REJECT on P1/P2.
_partial_intersection = _swap(
    _BASE,
    _GOLD_SEL,
    """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # BUG: intersection only -- omit the union with all prior labels
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if ax == 1:
            sel = 1
        Assert(sel == 0 or sel == 1)""",
)
SPEC_TESTS.append({
    "id": "partial-domain-intersection-only",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _partial_intersection,
    "refinement": "This is the verbatim pre-patch selection should_be_coords = "
    "set(window_dim) & set(self.obj.coords). On the F2P input the coordinate 'day' "
    "is NOT a windowed axis and its name is not one of the rebuilt container's "
    "axis names (was_label=1, is_window=0, is_axis_name=0), so it is dropped: "
    "list(result.coords) loses 'day' and test_coarsen_construct_keeps_all_coords "
    "FAILS. Faithful patch == the buggy original, so it does not resolve.",
    "rationale": "Rejection from postconditions P1 and P2: at a (1,0,0) member the "
    "impl yields 0 but promoted(1,0,0)=1 and P2 forces 1, so both clauses are "
    "violated. G-DIFF pins exactly this clause.",
})

# --- 3b. PARTIAL-DOMAIN: drop the axis-name leg ------------------------------
# sel = was_label alone. Correct on every member whose insertion name is not one
# of the rebuilt container's axis names, wrong precisely on a prior plain data
# member whose insertion name IS one of them -- a real sub-domain of the callee
# (a data member whose name coincides with a rebuilt axis name is a labelling
# array in the rebuilt container). Must reject on P1/P3.
_drop_axis_leg = _swap(
    _BASE,
    _GOLD_SEL,
    """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # BUG: ignore the container's axis-name property entirely
        sel = 0
        if wl == 1:
            sel = 1
        Assert(sel == 0 or sel == 1)""",
)
SPEC_TESTS.append({
    "id": "partial-domain-drop-axis-name-leg",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _drop_axis_leg,
    "refinement": "An impl that decides status from the prior labelling bit alone "
    "would report a plain data member whose insertion name coincides with one of "
    "the rebuilt container's axis names as a data member. The real rebuilt "
    "container makes such a member a labelling array (the container imposes it on "
    "insertion), so this impl's per-member status list is not the one the real "
    "callee produces on that sub-domain.",
    "rationale": "Rejection from P1 and P3: at a (was_label=0, is_axis_name=1) "
    "member this yields 0 but promoted(0,*,1)=1 and P3 forces 1.",
})

# --- 4. PARTIAL-DOMAIN: correct everywhere EXCEPT the first element ----------
# Pins result[0]=0 always; correct on k>=1. Diverges when the first member is a
# labelling array or an axis-name member -- a real sub-domain the F2P can hit
# (the 'day' coord can be member 0). Must reject.
_partial_first = _swap(
    _BASE,
    _GOLD_SEL,
    """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # BUG: force the first member to data status regardless of its bits
        sel = 0
        if wl == 1 and iw == 1:
            sel = 1
        if wl == 1:
            sel = 1
        if ax == 1:
            sel = 1
        if i == 0:
            sel = 0
        Assert(sel == 0 or sel == 1)""",
)
SPEC_TESTS.append({
    "id": "partial-domain-first-element",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _partial_first,
    "refinement": "A patch that special-cases the first variable name (e.g. always "
    "demotes obj.variables[0]) would drop that variable from result.coords whenever "
    "the first member was a coordinate. The F2P builds a DataArray whose first "
    "coordinate is 'day'; demoting member 0 makes list(result.coords) != "
    "list(da.coords) and the test FAILS.",
    "rationale": "Rejection from P1/P2 at k=0: when was_label[0]=1 this yields "
    "result[0]=0 != promoted(1,*,*)=1, and P2 forces 1. The Forall covers k=0.",
})

# --- 5. PARTIAL-DOMAIN: echo is_window instead of the real disjunction -------
# sel = is_window: wrong on (was_label=1, is_window=0) (drops a non-windowed
# labelling array) AND on (was_label=0, is_window=1, is_axis_name=0) (promotes a
# plain data member because its name is a windowed axis). A rival that keys
# status off the windowed-axis bit rather than prior status.
_partial_window = _swap(
    _BASE,
    _GOLD_SEL,
    """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # BUG: key off the windowed-axis bit, not the prior status
        sel = 0
        if iw == 1:
            sel = 1
        Assert(sel == 0 or sel == 1)""",
)
SPEC_TESTS.append({
    "id": "partial-domain-window-keyed",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _partial_window,
    "refinement": "should_be_coords = set(window_dim) alone would promote exactly "
    "the windowed dimensions and drop non-windowed coordinates (e.g. 'day'). On the "
    "F2P, 'day' (is_window=0) is dropped and 'time' handling diverges, so "
    "list(result.coords) != list(da.coords) and the test FAILS.",
    "rationale": "Rejection from P2/P4: at a (was_label=1, is_window=0, "
    "is_axis_name=0) member it yields 0 but P2 forces 1; at (0,1,0) it yields 1 "
    "but P4 forces 0.",
})

# --- 5b. PARTIAL-DOMAIN: promote everything ---------------------------------
# sel = 1 always. Satisfies P2 and P3 but violates P4: a prior plain data member
# whose insertion name is not one of the rebuilt container's axis names must stay
# a data member. This is the attack the P4 clause exists to stop -- without P4
# the spec would only demand a SUPERSET of the labelling arrays and this would
# verify while producing a container with no data variables at all.
_promote_all = _swap(
    _BASE,
    _GOLD_SEL,
    """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # BUG: promote every member unconditionally
        sel = 1
        Assert(sel == 0 or sel == 1)""",
)
SPEC_TESTS.append({
    "id": "partial-domain-promote-all",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _promote_all,
    "refinement": "should_be_coords = set(self.obj.variables) would make every "
    "member of the rebuilt container a labelling array, leaving result.data_vars "
    "empty. The F2P checks the data variable 'T' is still a data variable "
    "(list(result.data_vars) is observed alongside list(result.coords)), so this "
    "does not resolve.",
    "rationale": "Rejection from P1 and P4: at a (was_label=0, is_axis_name=0) "
    "member this yields 1 but promoted(0,*,0)=0 and P4 forces 0.",
})

# --- 5c. NON-TERMINATION (vacuous divergence; the audited G-PANEL-1 hole) -----
# Replace the ENTIRE impl region with an endless `while True` loop that never
# returns. Under partial correctness the value postconditions P1..P4 are
# unreachable, hence vacuously satisfied -- exactly the counterexample the
# G-PANEL-1 auditor built against the pre-repair spec. The MustTerminate(2)
# precondition obligation must reject it: the loop carries no decreasing
# measure ('Loop might not take all unsatisfied obligations'). The surgery is
# by region slicing (not _swap) because the whole impl body is replaced; both
# markers are preserved, so spec_view / same_spec are unaffected.
_nt_start = _BASE.index("    # impl-start\n")
_nt_end = _BASE.index("    # impl-end")
_nonterm_loop = (
    _BASE[:_nt_start]
    + "    # impl-start\n"
    + "    result = []  # type: List[int]\n"
    + "    i = 0\n"
    + "    while True:\n"
    + "        # invariants-start\n"
    + "        Invariant(True)\n"
    + "        # invariants-end\n"
    + "        i = i + 0\n"
    + _BASE[_nt_end:]
)
SPEC_TESTS.append({
    "id": "nonterm-endless-loop",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _nonterm_loop,
    "refinement": "A construct() tail that never returns is not the gold patch: "
    "the real coordinate restoration always delivers the rebuilt object (the F2P "
    "observable IS the returned value: list(result.coords) == list(da.coords)). "
    "A diverging real patch would hang test_coarsen_construct_keeps_all_coords "
    "instead of resolving it.",
    "rationale": "An unbounded `while True` before the real body makes P1..P4 "
    "unreachable, hence vacuously satisfied under partial correctness (this was "
    "the audited G-PANEL-1 counterexample). The MustTerminate(2) obligation in "
    "the precondition rejects the loop: it carries no strictly decreasing "
    "measure, so it 'might not take all unsatisfied obligations'.",
})

# --- 6. POSITIVE CONTROL (soundness): structurally-different CORRECT impl -----
# Replace the three cascaded `if` clauses with a single guarded branch on the
# disjunction of the prior-status bit and the axis-name bit. This is a genuine
# control-flow reshape, value-equivalent to the gold. Every gold framing
# assert/invariant is KEPT verbatim (only the sel computation changes), so the
# gold loop proof still discharges -- a faithful correct impl MUST verify (else
# SPEC-TOO-STRONG).
_pos_branch = _swap(
    _BASE,
    _GOLD_SEL,
    """        wl = was_label[i]
        iw = is_window[i]
        ax = is_axis_name[i]
        # equivalent reshape: status afterwards == prior status OR axis-name;
        # promoted(wl, iw, ax) is that disjunction, so branch on it directly.
        if wl == 1 or ax == 1:
            sel = 1
        else:
            sel = 0
        Assert(sel == promoted(wl, iw, ax))""",
)
SPEC_TESTS.append({
    "id": "pos-control-direct-branch",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_branch,
    "rationale": "A structurally-different but correct impl (single if/else on the "
    "disjunction instead of three cascaded ifs) must verify. It keeps every gold "
    "framing assert/invariant and computes the same value, so the gold loop proof "
    "still discharges. If it failed, the spec would be SPEC-TOO-STRONG (rejecting "
    "a correct output).",
})

# --- 7. ADMISSIBILITY: precondition admits a normal F2P-shaped input ----------
# A separate top-level `def` would change the spec_view (everything outside the
# impl region is part of the spec signature), breaking same_spec. So admissibility
# is proved INSIDE the impl region: right after # impl-start we construct an
# F2P-shaped witness (member 0 = the 'day' coordinate, a prior label that is NOT a
# windowed axis and not an axis name of the rebuilt container; member 1 = the 'T'
# data var) and ASSERT that the precondition's load-bearing facts (equal lengths +
# the per-position 0/1 quantifiers) can be ESTABLISHED for it. If the verifier
# could not discharge those asserts the precondition domain would be vacuous for a
# legitimate F2P input -> PRECOND-TOO-STRONG. The witness construction is dead
# w.r.t. the return value (the gold loop below still drives the function), so the
# gold proof is preserved. This edit is entirely inside # impl-start / # impl-end,
# so same_spec holds.
_admiss = _swap(
    _BASE,
    "    # impl-start\n    result = []  # type: List[int]\n",
    "    # impl-start\n"
    "    # admissibility witness: an F2P-shaped in-domain input (a prior\n"
    "    # labelling array 'day' that is NOT a windowed axis and is not an\n"
    "    # axis name of the rebuilt container, plus a data member 'T').\n"
    "    wit_wl = [1, 0]  # type: List[int]\n"
    "    wit_iw = [0, 0]  # type: List[int]\n"
    "    wit_ax = [0, 0]  # type: List[int]\n"
    "    Assert(len(wit_wl) == len(wit_iw))\n"
    "    Assert(len(wit_wl) == len(wit_ax))\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(wit_wl),\n"
    "                                          wit_wl[k] == 0 or wit_wl[k] == 1),\n"
    "                                   [[wit_wl[k]]])))\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(wit_ax),\n"
    "                                          wit_ax[k] == 0 or wit_ax[k] == 1),\n"
    "                                   [[wit_ax[k]]])))\n"
    "    result = []  # type: List[int]\n",
)
SPEC_TESTS.append({
    "id": "admissibility-f2p-shaped",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss,
    "rationale": "The precondition's facts (length equalities + the per-position "
    "0/1 quantifiers) must be establishable for an F2P-shaped input (a prior "
    "coordinate that is NOT a windowed axis -- the demoted-coordinate scenario). "
    "The asserts are spliced after # impl-start so same_spec holds; the gold loop "
    "still drives the result. If the asserts could not discharge, the precondition "
    "would reject a legitimate input -> PRECOND-TOO-STRONG.",
})

# --- 7b. ADMISSIBILITY: the axis-name sub-domain is in-domain too ------------
# The precondition must also admit an input in which a member's insertion name
# coincides with one of the rebuilt container's axis names (is_axis_name=1) --
# otherwise the P3/P4 clauses would be quantified over an empty sub-domain and
# the spec would say nothing about it.
_admiss_ax = _swap(
    _BASE,
    "    # impl-start\n    result = []  # type: List[int]\n",
    "    # impl-start\n"
    "    # admissibility witness for the axis-name sub-domain: member 0 is a\n"
    "    # plain data member whose insertion name coincides with one of the\n"
    "    # rebuilt container's axis names; member 1 is an ordinary data member.\n"
    "    wit_wl = [0, 0]  # type: List[int]\n"
    "    wit_iw = [0, 0]  # type: List[int]\n"
    "    wit_ax = [1, 0]  # type: List[int]\n"
    "    Assert(len(wit_wl) == len(wit_iw))\n"
    "    Assert(len(wit_wl) == len(wit_ax))\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(wit_wl),\n"
    "                                          wit_wl[k] == 0 or wit_wl[k] == 1),\n"
    "                                   [[wit_wl[k]]])))\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(wit_ax),\n"
    "                                          wit_ax[k] == 0 or wit_ax[k] == 1),\n"
    "                                   [[wit_ax[k]]])))\n"
    "    Assert(promoted(wit_wl[0], wit_iw[0], wit_ax[0]) == 1)\n"
    "    Assert(promoted(wit_wl[1], wit_iw[1], wit_ax[1]) == 0)\n"
    "    result = []  # type: List[int]\n",
)
SPEC_TESTS.append({
    "id": "admissibility-axis-name-subdomain",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss_ax,
    "rationale": "The axis-name sub-domain (is_axis_name=1) must be admissible and "
    "non-vacuous, else P3 and P4 would quantify over nothing. The two promoted() "
    "asserts also pin that the modelled per-member function genuinely separates "
    "the two cases (1 for the axis-name member, 0 for the plain one) -- if either "
    "assert failed, promoted would be constant and the spec toothless.",
})


# ===========================================================================
# AXIOM_TESTS — none. meta.json axioms == [], no @ContractOnly axiom; the changed
# selection is modeled DEEPLY (promoted + verified loop), and the real callees
# involved (the container's own insertion behaviour and Dataset.set_coords) are
# UNCHANGED and handled by the set->bit type refinement.
# There is no axiom-soundness or axiom-containment obligation for this bundle.
# ===========================================================================
AXIOM_TESTS = []
