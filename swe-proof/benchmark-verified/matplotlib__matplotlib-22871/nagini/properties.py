# properties.py — PBT falsification battery for matplotlib__matplotlib-22871.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS case is a full model.py variant whose ONLY change is inside the
# # impl-start/# impl-end region (region surgery => same_spec guaranteed); the
# frozen spec (axioms/pure/pre/post-conditions + signatures) is never touched.
# Each AXIOM_TESTS case is a self-contained probe run in the instance Docker
# image (real numpy) — it embeds the persisted axiom_check.py oracle (the runner
# mounts ONLY the probe at /work) and EXECUTES the real callee, never scrapes
# source; file reads (none here) would be utf-8-safe.
#
# Defended surface (model.py `determine_level`):
#   * Inputs c0..c5 are READ-ONLY: Requires(Acc(list_pred(ck), 1/2)) and the
#     postcondition gives back the SAME half-permission. A mutating impl cannot
#     get write permission (needs 1/1) => frame-mutation rejects for INSUFFICIENT
#     PERMISSION (lane 1, MANDATORY).
#   * Level pinning: seven Implies clauses pin Result().level to the highest-
#     indexed VARYING column (finest-to-coarsest scan), or 5 when none varies.
#   * Offset pinning: at a COARSE labelling level (month c1 / year c0, i.e.
#     level < 2), show_offset == 0 EXACTLY iff that column carries the value 1
#     (col_has_one); at a FINE level (c5..c2 vary) or the all-constant case,
#     show_offset == 1 always.
#   * The two @Pure helpers col_varies / col_has_one are GROUNDED in the inputs
#     (Exists i<j. col[i]!=col[j]  /  Exists i. col[i]==1), fully unfolded over
#     the args — there is NO opaque answer-key oracle to echo (see 'assessment').
#
# The single behavioural change the gold patch makes (G-DIFF) is the conjunct
# col_has_one on the coarse-level offset-suppression guard; the F2P is
# test_offset_changes (months Feb..Jul, January absent => the year must show in
# the offset). Every reject rival below carries the refinement argument that its
# faithful real patch would NOT resolve test_offset_changes / would corrupt P2P.

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22871"
FLOAT_ENCODING = None   # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body inside # impl-start / # impl-end (everything between
# the markers, used as the unique anchor for region surgery).
_GOLD_IMPL = '''    # impl-start
    # Default: the offset is shown. The descending scan over the six levels is
    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
    if col_varies(c5):
        return TickLevel(5, 1)
    if col_varies(c4):
        return TickLevel(4, 1)
    if col_varies(c3):
        return TickLevel(3, 1)
    if col_varies(c2):
        return TickLevel(2, 1)
    if col_varies(c1):
        if col_has_one(c1):
            return TickLevel(1, 0)
        return TickLevel(1, 1)
    if col_varies(c0):
        if col_has_one(c0):
            return TickLevel(0, 0)
        return TickLevel(0, 1)
    # No column varies: every tick is identical down to the second. The scan
    # reaches the coarsest level with all entries equal and resets to the finest
    # level; the offset keeps its default (shown).
    return TickLevel(5, 1)
    # impl-end'''

assert _GOLD_IMPL in _BASE, "gold impl anchor drifted from model.py"


def _impl(body_lines):
    """Build a full module by replacing ONLY the impl-region body with
    body_lines (a list of source lines, no markers)."""
    inner = "\n".join(body_lines)
    new_region = "    # impl-start\n" + inner + "\n    # impl-end"
    return _swap(_BASE, _GOLD_IMPL, new_region)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY: all six inputs are Acc(...,1/2) read-only) -
# A rival that, at the month level, OVERWRITES the read-only column c1 so that
# col_has_one(c1) becomes vacuously true (writing a 1 into it) and then suppresses
# the offset. To assign c1[0] = 1 it needs FULL permission Acc(list_pred(c1), 1),
# but the precondition grants only 1/2 (and the postcondition demands the same
# 1/2 back). Nagini MUST reject this for insufficient permission — the write is
# the cause. Gold invariants/clauses are untouched, so the rejection is
# attributable to the mutation, not to a contract change.
SPEC_TESTS.append({
    "id": "frame-mutation-write-c1",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        # MUTATION: write into the read-only column c1 (needs full perm).",
        "        c1[0] = 1",
        "        return TickLevel(1, 0)",
        "    if col_varies(c0):",
        "        if col_has_one(c0):",
        "            return TickLevel(0, 0)",
        "        return TickLevel(0, 1)",
        "    return TickLevel(5, 1)",
    ]),
    "refinement": (
        "The faithful real patch would WRITE into tickdate[:, 1] (the months "
        "column) before deciding the offset. tickdate is the calendar table the "
        "ticks are rendered from; mutating a month entry to 1 corrupts the tick "
        "labels and the downstream offsetfmts selection — it does not compute the "
        "January-present condition, it forges it. test_offset_changes (and the "
        "concise-formatter P2P cases that read the real months) would not resolve."
    ),
    "rationale": (
        "Rejected by the PERMISSION SYSTEM: c1 has only Acc(list_pred(c1),1/2); a "
        "store c1[0]=1 requires write (1/1) permission, which the precondition "
        "does not grant and the postcondition Ensures(Acc(list_pred(c1),1/2)) "
        "demands back. A byte-fuzzer never tries to mutate a read-only input."
    ),
})

# --- 2. PARTIAL-DOMAIN: the pre-patch month-level bug (the real defect) -------
# At the month labelling level (c1 varies, c5..c2 constant) suppress the offset
# UNCONDITIONALLY (return TickLevel(1,0)) — drop the col_has_one(c1) conjunct.
# This is EXACTLY the pre-patch behaviour. It fails the load-bearing month-level
# postcondition Implies(col_varies(c1) and not c5..c2 vary,
#   (show_offset==0) == col_has_one(c1))  whenever January is ABSENT (col_has_one
# false but show_offset==0).
SPEC_TESTS.append({
    "id": "partial-domain-month-suppress-always",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        # pre-patch: suppress offset whenever level<2, ignoring col_has_one",
        "        return TickLevel(1, 0)",
        "    if col_varies(c0):",
        "        if col_has_one(c0):",
        "            return TickLevel(0, 0)",
        "        return TickLevel(0, 1)",
        "    return TickLevel(5, 1)",
    ]),
    "refinement": (
        "This is the pre-patch guard `if level < 2: show_offset = False` with NO "
        "`np.any(unique == 1)` conjunct (model_prepatch.py reproduces it). On the "
        "F2P test_offset_changes the months span Feb..Jul (January absent), so the "
        "offset is wrongly suppressed and the year '1997' never shows — the "
        "reported bug. The faithful real patch is the un-fixed code; it does NOT "
        "resolve test_offset_changes."
    ),
    "rationale": (
        "Rejected by the month-level offset postcondition clause: "
        "Implies(col_varies(c1) and not col_varies(c5..c2), "
        "(Result().show_offset==0) == col_has_one(c1)). With col_has_one(c1) "
        "false and show_offset==0 the biconditional is violated."
    ),
})

# --- 3. PARTIAL-DOMAIN: the year-level analogue ------------------------------
# At the year labelling level (only c0 varies) suppress the offset unconditionally.
# Fails the year-level clause Implies(col_varies(c0) and not c5..c1 vary,
#   (show_offset==0) == col_has_one(c0)) when the years do not include the value 1.
SPEC_TESTS.append({
    "id": "partial-domain-year-suppress-always",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        if col_has_one(c1):",
        "            return TickLevel(1, 0)",
        "        return TickLevel(1, 1)",
        "    if col_varies(c0):",
        "        # pre-patch: suppress offset at the year level regardless of value 1",
        "        return TickLevel(0, 0)",
        "    return TickLevel(5, 1)",
    ]),
    "refinement": (
        "Same un-fixed `if level < 2` guard, exercised at the year labelling "
        "level. A real tick table whose only varying coarse column is the year and "
        "whose years do not contain the literal 1 (e.g. 1996/1997/1998) would have "
        "its year-offset wrongly hidden. The pre-patch code does not resolve the "
        "coarse-level offset behaviour the issue/F2P demands."
    ),
    "rationale": (
        "Rejected by the year-level offset postcondition clause: "
        "Implies(col_varies(c0) and not col_varies(c5..c1), "
        "(Result().show_offset==0) == col_has_one(c0))."
    ),
})

# --- 4. PARTIAL-DOMAIN: wrong scan direction (coarsest-first) -----------------
# Pick the LOWEST-indexed varying column instead of the highest (coarsest-to-
# finest). On a tick table where BOTH a coarse and a fine column vary this picks
# the wrong level, violating the level-pinning clauses (e.g. col_varies(c5) true
# but Result().level != 5).
SPEC_TESTS.append({
    "id": "partial-domain-wrong-scan-direction",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl([
        "    # WRONG: coarsest-to-finest scan picks the lowest-indexed varying col",
        "    if col_varies(c0):",
        "        if col_has_one(c0):",
        "            return TickLevel(0, 0)",
        "        return TickLevel(0, 1)",
        "    if col_varies(c1):",
        "        if col_has_one(c1):",
        "            return TickLevel(1, 0)",
        "        return TickLevel(1, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    return TickLevel(5, 1)",
    ]),
    "refinement": (
        "The real loop is `for level in range(5, -1, -1): ... break`, which "
        "selects the FINEST (highest-indexed) varying component and indexes "
        "offsetfmts/fmts with it. Scanning coarsest-first selects the wrong level "
        "(e.g. year instead of second when both vary), producing wrong tick "
        "format strings — the concise-formatter P2P assertions on the rendered "
        "labels (test_concise_formatter*) would not resolve."
    ),
    "rationale": (
        "Rejected by the level-pinning clauses, e.g. Implies(col_varies(c5), "
        "Result().level == 5): when c5 and c0 both vary this impl returns level 0, "
        "contradicting the c5 clause."
    ),
})

# --- 5. PARTIAL-DOMAIN: wrong all-constant level ------------------------------
# When NO column varies the spec pins level to 5 (reset to finest). Return 0 in
# that case — passes everything except the all-constant level clause.
SPEC_TESTS.append({
    "id": "partial-domain-allconst-wrong-level",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        if col_has_one(c1):",
        "            return TickLevel(1, 0)",
        "        return TickLevel(1, 1)",
        "    if col_varies(c0):",
        "        if col_has_one(c0):",
        "            return TickLevel(0, 0)",
        "        return TickLevel(0, 1)",
        "    # WRONG: no column varies, but return level 0 instead of the finest 5",
        "    return TickLevel(0, 1)",
    ]),
    "refinement": (
        "The real loop, finding no varying component, runs the `elif level == 0: "
        "level = 5` reset, leaving level == 5 (the finest format) when all ticks "
        "are identical down to the second. Returning 0 would index offsetfmts[0] "
        "('%Y') for a single-instant axis — wrong label. P2P concise-formatter "
        "cases with a degenerate/constant range would not resolve."
    ),
    "rationale": (
        "Rejected by the all-constant level clause: Implies(not col_varies(c5..c0), "
        "Result().level == 5)."
    ),
})

# --- 6. PARTIAL-DOMAIN (complement): never suppress the offset ----------------
# Always show the offset (show_offset == 1), even at a coarse level whose column
# DOES contain 1. This is the OTHER half of the offset domain: it fails the
# coarse-level clause when col_has_one is TRUE (should be suppressed).
SPEC_TESTS.append({
    "id": "partial-domain-never-suppress",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        # WRONG: never suppress, even when January (value 1) is present",
        "        return TickLevel(1, 1)",
        "    if col_varies(c0):",
        "        return TickLevel(0, 1)",
        "    return TickLevel(5, 1)",
    ]),
    "refinement": (
        "Real post-patch code DOES suppress the offset at a coarse level when "
        "`np.any(unique == 1)` (January / year-1 present), so the redundant "
        "year-in-offset is hidden. Never suppressing reintroduces the duplicate "
        "label the original #21785 fix removed: test_concise_formatter_show_offset "
        "cases that expect an empty offset ('t_delta5-' / 't_delta6-') would not "
        "resolve."
    ),
    "rationale": (
        "Rejected by the coarse-level offset clause "
        "(Result().show_offset==0) == col_has_one(c1): with col_has_one(c1) true "
        "and show_offset==1 the biconditional is violated."
    ),
})

# --- 7. POSITIVE CONTROL (soundness): structurally different but CORRECT ------
# Reorder the offset sub-branch (test the NEGATIVE of col_has_one first) and
# compute show_offset via an explicit local, keeping every return semantically
# identical. No loop-direction flip, no dropped framing assert, no fold lemma —
# the @Pure helpers are Exists-based, not recursive, so a branch reshape keeps
# all proof obligations trivial. MUST verify (else SPEC-TOO-STRONG).
SPEC_TESTS.append({
    "id": "pos-control-branch-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        # reordered: handle the offset-shown branch first via a local flag",
        "        if not col_has_one(c1):",
        "            return TickLevel(1, 1)",
        "        flag1 = 0  # type: int",
        "        return TickLevel(1, flag1)",
        "    if col_varies(c0):",
        "        if not col_has_one(c0):",
        "            return TickLevel(0, 1)",
        "        flag0 = 0  # type: int",
        "        return TickLevel(0, flag0)",
        "    return TickLevel(5, 1)",
    ]),
    "rationale": (
        "A correct impl with the same returns but the offset sub-branches "
        "reordered (negative-first) and the suppressed flag bound to a typed "
        "local. It satisfies every postcondition clause identically; if Nagini "
        "cannot verify it, the spec is SPEC-TOO-STRONG."
    ),
})

# --- 8. POSITIVE CONTROL #2: single-tail offset decision ----------------------
# A second structurally-different correct shape: compute the coarse-level flag in
# one place. Still a straight-line cascade (no loop, no induction), keeps the
# gold returns' values. MUST verify.
SPEC_TESTS.append({
    "id": "pos-control-collapsed-coarse",
    "kind": "soundness",
    "expect": "verify",
    "module": _impl([
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        s1 = 1  # type: int",
        "        if col_has_one(c1):",
        "            s1 = 0",
        "        return TickLevel(1, s1)",
        "    if col_varies(c0):",
        "        s0 = 1  # type: int",
        "        if col_has_one(c0):",
        "            s0 = 0",
        "        return TickLevel(0, s0)",
        "    return TickLevel(5, 1)",
    ]),
    "rationale": (
        "Correct impl that picks the coarse-level flag via a mutable typed local "
        "(default 1, set to 0 iff col_has_one) instead of two literal returns. "
        "Behaviourally identical; must verify (else SPEC-TOO-STRONG)."
    ),
})

# --- 9. ADMISSIBILITY: the precondition admits a normal F2P-shaped input ------
# Inside the impl region, exercise the precondition facts: read c0[0] (valid
# given len(c0) >= 1 and the read permission) and assert each column length
# equals len(c0). If the Requires could not be established for a legitimate
# input, this read/assert would fail to verify => PRECOND-TOO-STRONG. The gold
# behaviour follows unchanged, so the function still meets its postcondition.
SPEC_TESTS.append({
    "id": "admissibility-read-first-element",
    "kind": "admissibility",
    "expect": "verify",
    "module": _impl([
        "    # Admissibility: a normal F2P-shaped input (>=1 tick, equal-length",
        "    # columns) lets us read the first element and confirm the lengths.",
        "    Assert(len(c0) >= 1)",
        "    Assert(len(c1) == len(c0))",
        "    probe = c0[0]  # type: int",
        "    Assert(probe == c0[0])",
        "    if col_varies(c5):",
        "        return TickLevel(5, 1)",
        "    if col_varies(c4):",
        "        return TickLevel(4, 1)",
        "    if col_varies(c3):",
        "        return TickLevel(3, 1)",
        "    if col_varies(c2):",
        "        return TickLevel(2, 1)",
        "    if col_varies(c1):",
        "        if col_has_one(c1):",
        "            return TickLevel(1, 0)",
        "        return TickLevel(1, 1)",
        "    if col_varies(c0):",
        "        if col_has_one(c0):",
        "            return TickLevel(0, 0)",
        "        return TickLevel(0, 1)",
        "    return TickLevel(5, 1)",
    ]),
    "rationale": (
        "The precondition (len(c0)>=1, equal lengths, Acc(...,1/2) read perm) must "
        "admit a representative tick table: reading c0[0] and asserting the length "
        "equalities must verify. If it cannot, PRECOND-TOO-STRONG."
    ),
})


# ===========================================================================
# AXIOM LANE  (no consumed @ContractOnly axioms; two A-reference deep models:
# col_varies == len(np.unique(col))>1 and col_has_one == np.any(np.unique==1),
# plus the whole determine_level == real format_ticks scan). The deep models are
# checked the same way as axioms: the real numpy callee must equal the model on
# every caller-reachable input. The runner mounts ONLY the probe at /work, so the
# soundness probe EMBEDS axiom_check.py (read on the HOST at load time) and runs
# the REAL numpy reductions; it never scrapes source.
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

AXIOM_TESTS = []

# axiom-soundness: run the persisted, gold-grounded axiom_check.py end-to-end in
# the instance image (real numpy). It asserts col_varies / col_has_one match the
# real np.unique / np.any on 19 boundary + 20000 fuzz columns AND the whole
# determine_level deep model == the real post-patch format_ticks scan on 7
# boundary + 20000 fuzz tick tables. Exit 0 iff every deep model is sound.
AXIOM_TESTS.append({
    "id": "ax-sound-deep-models",
    "axiom": "col_varies/col_has_one/determine_level (A-reference deep models)",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running the REAL numpy np.unique/np.any reductions "
      "and the real post-patch format_ticks scan against the model.py deep "
      "models (col_varies, col_has_one, determine_level) on boundary + 20000 "
      "fuzz columns and tick tables.")
_rc = main()
_sys.exit(0 if _rc == 0 else 1)
""",
    "rationale": (
        "If the REAL np.unique / np.any (or the real loop body) ever disagrees "
        "with the structural deep models on an input in their Requires domain, the "
        "A-reference model is unsound (AXIOM-UNSOUND). The probe executes the real "
        "callee — it does not scrape source."
    ),
})

# axiom-containment: every callee input the MODEL can reach is inside the deep
# models' / numpy's domain. determine_level's Requires give each ck as a
# List[int] with len >= 1; col_varies / col_has_one require only
# Acc(list_pred(col),1/4) (any list). The real np.unique / np.any accept any 1-D
# integer array (incl. length-1, negatives, duplicates). So every reachable input
# is integer columns of length >= 1, all inside numpy's domain — covering MORE
# (length 0) than the caller reaches is SOUND. This probe enumerates the
# caller-reachable column shapes the model can pass and confirms the real
# reductions accept each (no exception, well-defined result), and asserts model.py
# never passes a non-list / float / empty column to a helper.
AXIOM_TESTS.append({
    "id": "ax-cover-callee-domain",
    "axiom": "col_varies/col_has_one (A-reference deep-model Requires domain)",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": (
        "import sys, ast\n"
        "import numpy as np\n"
        "MODEL_SRC = " + repr(_MODEL_SRC) + "\n"
        "# 1) STATIC: every call to col_varies / col_has_one in determine_level\n"
        "#    passes one of the parameter columns c0..c5 (a List[int]). No other\n"
        "#    caller, no derived/empty/float argument reaches the deep models.\n"
        "tree = ast.parse(MODEL_SRC)\n"
        "PARAMS = {'c0', 'c1', 'c2', 'c3', 'c4', 'c5'}\n"
        "HELPERS = {'col_varies', 'col_has_one'}\n"
        "bad = []\n"
        "for node in ast.walk(tree):\n"
        "    if isinstance(node, ast.Call) and getattr(node.func, 'id', None) in HELPERS:\n"
        "        if len(node.args) != 1:\n"
        "            bad.append(('arity', ast.dump(node)))\n"
        "            continue\n"
        "        a = node.args[0]\n"
        "        if not (isinstance(a, ast.Name) and a.id in PARAMS):\n"
        "            bad.append(('non-param-arg', ast.dump(a)))\n"
        "if bad:\n"
        "    print('CONTAINMENT FAIL: a deep-model call takes an arg outside {c0..c5}:', bad)\n"
        "    sys.exit(1)\n"
        "print('static: every col_varies/col_has_one call passes a parameter column c0..c5')\n"
        "# 2) The model Requires: each ck is List[int], len(c0) >= 1, all equal\n"
        "#    length. The DEEP-MODEL Requires (Acc(list_pred,1/4)) is any list, so\n"
        "#    the caller-reachable shapes (int columns, len >= 1) are a SUBSET of\n"
        "#    the modeled domain. Confirm the REAL numpy callee is well-defined on\n"
        "#    exactly those reachable shapes (no exception, deterministic result).\n"
        "import random\n"
        "rng = random.Random(2287122)\n"
        "reach = [[1], [0], [-3], [1, 1], [1, 2], [-5, 7], [1, 1, 1],\n"
        "         [12, 1, 7], [1997, 1998, 1997], [0, 0, 0, 0]]\n"
        "for _ in range(5000):\n"
        "    n = rng.randint(1, 8)  # len >= 1, matching len(c0) >= 1\n"
        "    reach.append([rng.randint(-5, 13) for _ in range(n)])\n"
        "for col in reach:\n"
        "    arr = np.asarray(col)\n"
        "    if arr.ndim != 1 or len(arr) < 1:\n"
        "        print('UNEXPECTED reachable shape:', col); sys.exit(1)\n"
        "    u = np.unique(arr)            # real col_varies callee\n"
        "    _ = len(u) > 1\n"
        "    _ = bool(np.any(u == 1))      # real col_has_one callee\n"
        "print('AXIOM-CONTAINMENT OK: every caller-reachable column (int, len>=1) "
        "is inside the np.unique/np.any domain; the deep-model Requires "
        "Acc(list_pred,1/4) covers all reachable inputs (and more, which is "
        "sound). No empty/float/non-list column can reach the helpers.')\n"
        "sys.exit(0)\n"
    ),
    "rationale": (
        "A caller-reachable callee input outside the deep-model / numpy domain "
        "would be AXIOM-TOO-WEAK-FOR-CALLER. Here every reachable input is an "
        "int column of length >= 1 (from determine_level's Requires), strictly "
        "inside numpy's any-1-D-array domain; covering empty columns too is sound."
    ),
})
