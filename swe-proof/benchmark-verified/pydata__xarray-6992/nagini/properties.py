# properties.py — PBT manifest for pydata__xarray-6992.
#
# NOT a Nagini module; an adversarial falsification battery the runner
# (swebench_nagini.pbt) parses.  Each SPEC_TESTS case is a FULL model.py variant
# that shares the FROZEN spec (markers.same_spec) and edits ONLY the impl region
# of ONE of the two modeled functions (between its `# impl-start` /`# impl-end`);
# it is checked by re-running Nagini.  AXIOM_TESTS are self-contained Docker
# probes for the A-reference deep model.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md):
#
#   promote_to_index(variables0, coord_names0, indexes0, index_repr0,
#                    new_index_vars, promoted_names, displaced_index_coords) -> State
#   teardown_index  (variables0, coord_names0, indexes0, index_repr0,
#                    new_index_vars, dropped_coords, converted_coords)       -> State
#
#   * EVERY input is a `PSet[int]` — an IMMUTABLE Viper value, NOT an aliasable
#     heap object.  The model's set ops (+ , -) always produce fresh values and
#     never mutate an argument; there is NO `Acc(input, 1/2)` read-only heap
#     permission to overwrite.  The ONLY Acc(...,1/2) clauses are on the FRESH
#     `Result()` State's four fields (the output), framed back unchanged.  So the
#     frame-mutation weakness class (overwrite a half-perm READ-ONLY INPUT to
#     satisfy the postcondition vacuously) is STRUCTURALLY INAPPLICABLE here:
#     there is no input field to write.  (mapping.md §2 "Read-only inputs".)
#     => has_readonly_input = False, no frame-mutation reject case.
#
#   * LOAD-BEARING postcondition: each function pins ALL FOUR output collections
#     to an EXACT set expression OVER THE INPUT collections, PLUS well_formed:
#       teardown:  indexes    == ((indexes0    - dropped) - converted) + new_idx
#                  index_repr == ((index_repr0 - dropped) - converted) + new_idx
#                  variables  == (variables0  - dropped)               + new_idx   (converted KEPT)
#                  coord_names== (coord_names0 - dropped)               + new_idx   (converted KEPT)
#                  well_formed(variables, coord_names, indexes, index_repr)
#       promote:   indexes    == (indexes0 - displaced) + new_idx
#                  index_repr == (index_repr0 - readd)  + new_idx       (readd via promote_readd)
#                  variables  == (variables0 - promote_dropped) + (new_idx + readd)
#                  coord_names== (coord_names0 - promote_dropped) + (new_idx + readd)
#                  well_formed(...)
#     Every pin is GROUNDED in the args, fully unfolded set algebra; well_formed
#     / subset / disjoint / promote_dropped / promote_readd are @Pure helpers
#     grounded in the inputs.  There is NO opaque @Pure answer-key / exact-marker
#     oracle to echo without doing the work — so the ungrounded-oracle-echo class
#     is INAPPLICABLE (see assessment); the positive control is the honest
#     cheapest correct restructuring instead.
#
#   * The discriminating content (G-DIFF, prepatch_models):
#       - teardown coord_names equality + well_formed coord_names⊆variables is the
#         negative-DataVariables.__len__ fix (model_prepatch.py reverts it);
#       - the convert channel (converted_coords KEPT in variables/coord but removed
#         from index_repr/indexes) is the de-masked soundness hole (refinement §F);
#       - promote index_repr equality + index_repr⊆indexes is the re-add/convert
#         fix (model_prepatch_2.py reverts it).
#     Each reject rival below targets one of these clauses and carries the
#     refinement argument that its faithful real patch would NOT resolve the F2P.
#
#   * No @ContractOnly axiom (meta.axioms == []).  The whole behaviour is an
#     A-reference deep model (the PSet set algebra) validated == the REAL
#     Dataset.set_index / Dataset.reset_index by axiom_check.py (G-AX).  Per
#     PBT_PLAN §2.4 an A-reference deep model is checked like an axiom: deep model
#     == real callee on every CALLER-REACHABLE input.  The AXIOM_TESTS run that
#     oracle in-container over the 12 FAIL_TO_PASS scenarios.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "pydata__xarray-6992"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- exact gold impl bodies (text strictly BETWEEN the markers) --------------
# Each body is UNIQUE in _BASE, so a _swap on it edits ONLY that function's impl
# region; the spec (axioms/pure/pre/post + signatures) is never touched, which
# guarantees markers.same_spec for every variant.

_PROMOTE_IMPL = (
    "    # drop_variables: names whose array is removed before the result is rebuilt\n"
    "    # (the promoted names AND the displaced pre-existing index coordinates).\n"
    "    drop_variables = promoted_names + displaced_index_coords\n"
    "    # re-add deindexed coordinates AS PLAIN stored arrays: a displaced coordinate\n"
    "    # that is neither promoted nor part of the new index is converted out of the\n"
    "    # index-backed representation.\n"
    "    readd = (drop_variables - new_index_vars) - promoted_names\n"
    "    new_variables_all = new_index_vars + readd\n"
    "    # index status after promotion: surviving old index coords (the displaced\n"
    "    # ones lose their index), plus the new index's coordinates.\n"
    "    indexes_out = (indexes0 - displaced_index_coords) + new_index_vars\n"
    "    # index-backed representation: the converted (re-added) coords leave it.\n"
    "    index_repr_out = (index_repr0 - readd) + new_index_vars\n"
    "    variables_out = (variables0 - drop_variables) + new_variables_all\n"
    "    coord_names_out = (coord_names0 - drop_variables) + new_variables_all\n"
    "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
)
assert _BASE.count(_PROMOTE_IMPL) == 1, "promote impl body drift"

_TEARDOWN_IMPL = (
    "    # index status after teardown: surviving index coords are those neither\n"
    "    # dropped nor converted, plus any freshly created replacement index.\n"
    "    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars\n"
    "    # index-backed representation: dropped names lose their array; converted\n"
    "    # names are re-stored as PLAIN arrays (leave the index-backed kind).\n"
    "    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars\n"
    "    # variables: only the dropped names lose their stored array; converted names\n"
    "    # keep theirs. Take in the replacement index coordinates.\n"
    "    variables_out = (variables0 - dropped_coords) + new_index_vars\n"
    "    # the coordinate set must DROP every name that lost its array, KEEP every\n"
    "    # converted name, then take in any replacement index coordinate.\n"
    "    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars\n"
    "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
)
assert _BASE.count(_TEARDOWN_IMPL) == 1, "teardown impl body drift"


def _promote(body):
    """Swap ONLY promote_to_index's impl body (teardown stays gold)."""
    return _swap(_BASE, _PROMOTE_IMPL, body)


def _teardown(body):
    """Swap ONLY teardown_index's impl body (promote stays gold)."""
    return _swap(_BASE, _TEARDOWN_IMPL, body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ====================== POSITIVE CONTROLS (soundness) ===================

    # -- pos-teardown-combined: structurally-different CORRECT teardown -------
    # Combine the two index-channel removals into a single `gone_idx = dropped +
    # converted` intermediate and reverse the union operand order; keep the same
    # variables/coord_names difference structure.  Same total set algebra, a
    # different executable shape.  The verifier must prove
    #   ((i0 - d) - c) == (i0 - (d + c))  and  (X + y) == (y + X)
    # which are quantifier-free PSet (set-sort) identities the SMT backend
    # discharges directly (NO induction lemma needed — these are not folds).
    # refinement.md §F confirms this combined variant verifies.  Must VERIFY
    # (else SPEC-TOO-STRONG).
    {
        "id": "pos-teardown-combined",
        "kind": "soundness",
        "expect": "verify",
        "module": _teardown(
            "    # combined-channel restructuring of the SAME set algebra.\n"
            "    gone_idx = dropped_coords + converted_coords\n"
            "    indexes_out = new_index_vars + (indexes0 - gone_idx)\n"
            "    index_repr_out = new_index_vars + (index_repr0 - gone_idx)\n"
            "    variables_out = new_index_vars + (variables0 - dropped_coords)\n"
            "    coord_names_out = new_index_vars + (coord_names0 - dropped_coords)\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "rationale": "a correct teardown with a combined `gone_idx = dropped + "
                     "converted` intermediate and reversed union operands computes "
                     "the identical four collections; ((i0-d)-c)==(i0-(d+c)) and "
                     "commutativity of + are quantifier-free PSet identities the SMT "
                     "backend discharges (no fold/induction). If it fails => "
                     "SPEC-TOO-STRONG. (refinement.md §F positive control.)",
    },

    # -- pos-promote-reorder: structurally-different CORRECT promote ----------
    # Reverse every union operand order and rename intermediates; the difference
    # structure (drop_variables, readd) is preserved verbatim so the gold proof
    # of the index_repr / variables / coord_names equalities still discharges.
    # Commutativity of PSet `+` is quantifier-free.  Must VERIFY.
    {
        "id": "pos-promote-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _promote(
            "    drops = promoted_names + displaced_index_coords\n"
            "    conv = (drops - new_index_vars) - promoted_names\n"
            "    added = conv + new_index_vars\n"
            "    indexes_out = new_index_vars + (indexes0 - displaced_index_coords)\n"
            "    index_repr_out = new_index_vars + (index_repr0 - conv)\n"
            "    variables_out = added + (variables0 - drops)\n"
            "    coord_names_out = added + (coord_names0 - drops)\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "rationale": "structurally-different but CORRECT promote: renamed locals, "
                     "reversed union operands, identical difference structure "
                     "(`drops`==drop_variables, `conv`==readd). Commutativity of PSet "
                     "+ is quantifier-free; the gold proof of all four equalities "
                     "still discharges. Must verify (else SPEC-TOO-STRONG).",
    },

    # ====================== ADMISSIBILITY ===================================

    # -- admiss-teardown: the precondition admits a normal F2P-shaped input ---
    # Keep the gold teardown impl, but FIRST Assert the well_formed precondition
    # holds and that the pinned indexes_out lies inside indexes after removing the
    # torn-down names — i.e. the Requires (well_formed + subset/disjoint) is
    # establishable and unfolds for a legitimate input.  If the precondition were
    # too strong these Asserts could not be discharged => PRECOND-TOO-STRONG.
    {
        "id": "admiss-teardown",
        "kind": "admissibility",
        "expect": "verify",
        "module": _teardown(
            "    Assert(well_formed(variables0, coord_names0, indexes0, index_repr0))\n"
            "    Assert(subset(dropped_coords, indexes0))\n"
            "    Assert(disjoint(dropped_coords, converted_coords))\n"
            "    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    variables_out = (variables0 - dropped_coords) + new_index_vars\n"
            "    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "rationale": "the precondition must admit a normal teardown input: the "
                     "well_formed + subset(dropped, indexes0) + "
                     "disjoint(dropped, converted) Requires must be establishable and "
                     "unfold inside the body. If an Assert cannot discharge => "
                     "PRECOND-TOO-STRONG.",
    },

    # ====================== UNIQUENESS / REJECT =============================

    # -- reject-convert-as-drop: THE de-masked soundness hole (refinement §F D1)
    # Treat a CONVERTED coordinate as if DROPPED: subtract converted_coords from
    # variables_out (and coord_names_out) too.  A converted coordinate then
    # VANISHES from variables/coord_names although it kept its stored array.  This
    # is exactly the masked gap the three-channel teardown closed.  Shares the
    # spec; must be REJECTED by the pinned `variables == (variables0 - dropped) +
    # new_idx` (and coord_names) equality — converted is NOT subtracted there.
    {
        "id": "reject-convert-as-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _teardown(
            "    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    variables_out = ((variables0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    coord_names_out = ((coord_names0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "refinement": "a real reset_index that routed the drop=False (convert) names "
                      "through drop_variables instead of new_variables would DELETE the "
                      "converted coordinate's stored array. The F2P "
                      "test_reset_index_drop_convert asserts `reset[name].variable == "
                      "ds[name].variable.to_base_variable()` (the array survives as a "
                      "PLAIN variable); deleting it makes that name a KeyError / missing "
                      "variable, so the convert cases (drop=False) of the parametrized "
                      "grid FAIL. The faithful patch would NOT resolve.",
        "rationale": "rejected by the pinned `Result().variables == (variables0 - "
                     "dropped_coords) + new_index_vars` and the coord_names equality: "
                     "converted_coords must be KEPT in variables/coord_names, so "
                     "subtracting it makes the impl differ from the postcondition.",
    },

    # -- reject-no-convert: leave converted names INDEX-BACKED (no conversion) -
    # Drop the `- converted_coords` from index_repr_out only: a converted name
    # leaves `indexes` (still subtracted there) but STAYS in index_repr.  This is
    # a coordinate left in the index-backed representation without a live index —
    # rejected by BOTH the pinned index_repr equality AND well_formed's
    # index_repr ⊆ indexes clause.
    {
        "id": "reject-no-convert-repr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _teardown(
            "    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    index_repr_out = (index_repr0 - dropped_coords) + new_index_vars\n"
            "    variables_out = (variables0 - dropped_coords) + new_index_vars\n"
            "    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "refinement": "a real patch that reset the index but did NOT call "
                      "`.to_base_variable()` on the convert (drop=False) names leaves "
                      "those coordinates stored as IndexVariables with no live index — "
                      "the dangling index-backed state the repr code cannot tolerate "
                      "(the issue's broken-repr / negative-len symptom class). The F2P "
                      "convert assertions (variable equals the to_base_variable form) "
                      "would FAIL. Faithful patch would NOT resolve.",
        "rationale": "rejected by the pinned `Result().index_repr == ((index_repr0 - "
                     "dropped) - converted) + new_idx` AND well_formed's "
                     "`subset(index_repr, indexes)`: a converted name left in "
                     "index_repr but removed from indexes breaks index_repr ⊆ indexes.",
    },

    # -- reject-prepatch-coordnames: the EXACT base-commit bug (B7 / prepatch) -
    # Union the replacement index onto the ORIGINAL coord_names WITHOUT subtracting
    # the dropped names (the pre-patch `coord_names = set(new_variables) |
    # self._coord_names`).  A torn-down (dropped) coordinate stays NAMED with no
    # stored array => coord_names ⊄ variables => negative DataVariables.__len__.
    # This is model_prepatch.py verbatim; rejected by the pinned coord_names
    # equality AND well_formed's coord_names ⊆ variables clause.
    {
        "id": "reject-prepatch-coordnames",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _teardown(
            "    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    variables_out = (variables0 - dropped_coords) + new_index_vars\n"
            "    coord_names_out = coord_names0 + new_index_vars\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "refinement": "this IS the base-commit reset_index (`coord_names = "
                      "set(new_variables) | self._coord_names`, no subtraction of the "
                      "dropped names). A dropped coordinate stays in _coord_names with "
                      "its variable deleted, so DataVariables.__len__ = "
                      "len(_variables) - len(_coord_names) goes NEGATIVE -> the "
                      "reported `ValueError: __len__() should return >= 0` on repr / "
                      "len(data_vars). G-DIFF: model_prepatch.py reverts exactly this "
                      "and FAILS. The faithful (pre-patch) code does NOT resolve.",
        "rationale": "rejected by the pinned `Result().coord_names == (coord_names0 - "
                     "dropped_coords) + new_index_vars` AND well_formed's "
                     "`subset(coord_names, variables)`: keeping a dropped name in "
                     "coord_names while it left variables breaks coord_names ⊆ "
                     "variables (the negative-len symptom).",
    },

    # -- reject-identity-teardown: PARTIAL-DOMAIN — drop nothing --------------
    # Return the inputs unchanged (only adding the replacement index).  Correct
    # ONLY when dropped_coords and converted_coords are both empty; WRONG on every
    # F2P scenario where a name is actually torn down.  Shares the spec; rejected
    # by the indexes/index_repr/variables/coord_names equalities for any non-empty
    # dropped/converted.
    {
        "id": "reject-identity-teardown",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _teardown(
            "    indexes_out = indexes0 + new_index_vars\n"
            "    index_repr_out = index_repr0 + new_index_vars\n"
            "    variables_out = variables0 + new_index_vars\n"
            "    coord_names_out = coord_names0 + new_index_vars\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "refinement": "a no-op reset_index that never removes the torn-down names "
                      "leaves the reset index live: reset_index('z') still reports z as "
                      "an index/coordinate, so test_reset_index (the index actually "
                      "disappears) and the drop cases of the parametrized grid FAIL. "
                      "Faithful no-op patch would NOT resolve.",
        "rationale": "rejected by the pinned `Result().indexes == ((indexes0 - "
                     "dropped) - converted) + new_idx` (and the other three): for a "
                     "non-empty dropped_coords the gold expression removes it but the "
                     "identity impl keeps it, so the four equalities differ.",
    },

    # -- reject-promote-no-readd: model_prepatch_2 — no re-add/convert loop ----
    # In promote, set readd to EMPTY (drop_variables - drop_variables): the
    # displaced index coordinates are never converted out of the index-backed
    # representation, so index_repr keeps them with no live index.  This is the
    # base-commit set_index (drop only var_names, no re-add loop).  Rejected by
    # the pinned index_repr equality (which removes `readd`) AND well_formed's
    # index_repr ⊆ indexes clause.
    {
        "id": "reject-promote-no-readd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _promote(
            "    drop_variables = promoted_names + displaced_index_coords\n"
            "    readd = (drop_variables - new_index_vars) - promoted_names\n"
            "    new_variables_all = new_index_vars + readd\n"
            "    indexes_out = (indexes0 - displaced_index_coords) + new_index_vars\n"
            "    index_repr_out = index_repr0 + new_index_vars\n"
            "    variables_out = (variables0 - drop_variables) + new_variables_all\n"
            "    coord_names_out = (coord_names0 - drop_variables) + new_variables_all\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "refinement": "this IS the base-commit set_index: it drops the promoted names "
                      "but never re-adds the displaced index coordinates as base "
                      "variables (`.to_base_variable()`), so a displaced coordinate "
                      "stays an IndexVariable with no live index. "
                      "test_set_index_deindexed_coords (the displaced coords are "
                      "converted to base variables, repr/len stay valid) FAILS. G-DIFF: "
                      "model_prepatch_2.py reverts exactly this. Faithful pre-patch "
                      "code does NOT resolve.",
        "rationale": "rejected by the pinned `Result().index_repr == (index_repr0 - "
                     "promote_readd(...)) + new_index_vars` AND well_formed's "
                     "`subset(index_repr, indexes)`: leaving the displaced (readd) "
                     "coords in index_repr while they left indexes breaks "
                     "index_repr ⊆ indexes.",
    },

    # -- reject-teardown-overkeep-indexes: well_formed double-check -----------
    # Forget to remove the CONVERTED names from indexes_out (subtract dropped
    # only).  A converted name then carries a live index but is NOT index-backed
    # (it left index_repr) — but more sharply it differs from the pinned indexes
    # equality, and re-adds an index for a name that is no longer a coordinate's
    # index.  Rejected by the pinned indexes equality.
    {
        "id": "reject-teardown-overkeep-indexes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _teardown(
            "    indexes_out = (indexes0 - dropped_coords) + new_index_vars\n"
            "    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars\n"
            "    variables_out = (variables0 - dropped_coords) + new_index_vars\n"
            "    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars\n"
            "    return State(variables_out, coord_names_out, indexes_out, index_repr_out)"
        ),
        "refinement": "a real patch that removed the converted names from the variable "
                      "store / index_repr but LEFT them in the index map (`indexes` "
                      "dict) keeps a stale Index entry for a coordinate that no longer "
                      "carries one. The F2P asserts the converted name is no longer in "
                      "`reset.xindexes` (it became a plain coordinate); leaving the "
                      "index entry FAILS that assertion. Faithful patch would NOT "
                      "resolve.",
        "rationale": "rejected by the pinned `Result().indexes == ((indexes0 - "
                     "dropped) - converted) + new_idx`: not subtracting converted "
                     "leaves it in indexes, so the impl differs from the postcondition "
                     "for any non-empty converted_coords.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE  (A-reference deep model; no @ContractOnly axiom — meta.axioms==[])
# ---------------------------------------------------------------------------
# Per PBT_PLAN §2.4 an A-reference deep model is checked the same way as an
# axiom: the deep model must equal the REAL callee on every CALLER-REACHABLE
# input.  axiom_check.py (G-AX) is exactly that oracle: it builds the 12
# FAIL_TO_PASS input datasets, runs the REAL set_index / reset_index, reads the
# four name collections from the result (index_repr via isinstance(v,
# IndexVariable) — a DIRECT structural read, no value proxy / double-mask),
# derives the three teardown channels STRUCTURALLY from the real input/output,
# and asserts the model's PSet set algebra predicts the real result EXACTLY on
# all four collections for every scenario (no WF-only relaxation, no skip-guard).
#
# We embed axiom_check.py's source (read on the HOST at load time — the runner
# mounts ONLY the probe at /work; axiom_check.py is NOT in-container) and exec it
# in-Docker against the GOLD-applied callees.  Two views of the same oracle:
#   * soundness   — the real callee's result is well-formed AND the deep model
#                   matches it exactly (a disagreement => AXIOM-UNSOUND);
#   * containment — every callee-input the model can reach (the three teardown
#                   channels derived from the real call) satisfies the model
#                   preconditions (subset/disjoint), and the real callees are
#                   total over the dict/set name collections the model abstracts,
#                   so no caller-reachable input lies outside the deep model's
#                   domain (a missed sub-domain would have failed soundness).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# --- embedded bundle oracle (axiom_check.py), read on host at load time ---\n"
    "_ORACLE_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '_embedded_axiom_check'}\n"
    "exec(compile(_ORACLE_SRC, 'axiom_check.py', 'exec'), g)\n"
    "# main() EXECUTES the real Dataset.set_index / Dataset.reset_index on the 12\n"
    "# FAIL_TO_PASS scenarios, asserts each real result is well-formed (indexes ⊆\n"
    "# coord_names ⊆ variables, index_repr ⊆ indexes), and asserts the deep PSet\n"
    "# model predicts the real four collections EXACTLY on every scenario.\n"
    "rc = g['main']()\n"
    "print('A-reference deep model soundness+containment: PASS' if rc == 0 "
    "else 'FAIL')\n"
    "sys.exit(rc)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-ref-setalgebra-sound",
        "axiom": "promote_to_index / teardown_index (PSet set algebra) + well_formed",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "A-reference deep model: the PSet set algebra of "
                     "promote_to_index / teardown_index must EQUAL the real "
                     "Dataset.set_index / Dataset.reset_index on the four name "
                     "collections for every FAIL_TO_PASS scenario, and each real "
                     "result must be well-formed (index_repr read via "
                     "isinstance(v, IndexVariable) — direct structural read, no value "
                     "proxy). The probe EXECUTES the real callees (no source scraping). "
                     "Any disagreement / WF violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-ref-setalgebra-containment",
        "axiom": "promote_to_index / teardown_index (PSet set algebra) + well_formed",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_PROBE
                 + "# Containment: the teardown channels are derived structurally from\n"
                   "# the real call (dropped = variables_in - variables_out;\n"
                   "# new_index_vars = indexes_out - indexes_in; converted =\n"
                   "# (indexes_in - indexes_out) - dropped - new_index_vars) and the\n"
                   "# oracle ASSERTS they satisfy the model preconditions "
                   "(dropped<=i0,\n"
                   "# converted<=i0, dropped & converted == empty). The real callees are\n"
                   "# total over the dict/set name collections the model abstracts to\n"
                   "# PSet[int], so every caller-reachable input lies in the deep "
                   "model's\n"
                   "# domain; a missed sub-domain would have failed the soundness "
                   "assert.\n",
        "rationale": "containment: every callee-input the model can reach (the three "
                     "teardown channels / the promote channels) is derived from the "
                     "real call and asserted to satisfy the model preconditions; the "
                     "real set_index/reset_index are total over the name collections, "
                     "so the caller never reaches an input outside the deep model's "
                     "domain. A reachable input the model mishandled would have failed "
                     "the soundness probe => AXIOM-TOO-WEAK-FOR-CALLER otherwise.",
    },
]
