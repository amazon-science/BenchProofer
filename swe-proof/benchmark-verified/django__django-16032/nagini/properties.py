# properties.py — PBT falsification battery for django__django-16032.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by region-surgery — only text
# strictly INSIDE an # impl-start / # impl-end region is edited, so the frozen
# spec (axioms/pure/pre/post-conditions + signatures) is byte-identical and
# same_spec holds by construction. The runner checks each variant with the
# Nagini verifier:  expect="verify" passes iff (same_spec AND verifies);
# expect="reject" passes iff (same_spec AND does NOT verify).
#
# Defended surface (three modeled functions over the minimal Query twin):
#   * project_columns           ~ Query.set_values([col])         (query.py fix:
#                                  the new line has_select_fields = True)
#       load-bearing post: len(selected_columns)==1 AND selected_columns[0]==col
#                          AND restricted_to_explicit_columns is True
#                          AND aux_expr_materialized is False  (set_values
#                          re-derives the annotation mask for the chosen
#                          ordinary column via set_annotation_mask([]) — the
#                          mask is CLEARED, matching the real callee)
#   * attach_auxiliary_expressions ~ annotate()+alias()           (query.py fix:
#                                  has_select_fields decoupled from the mask)
#       load-bearing post: aux_expr_materialized is True
#                          AND restricted_to_explicit_columns == Old(...)  <-- THE bug
#                          AND ToSeq(selected_columns) == Old(ToSeq(...))   (frame)
#   * prepare_in_rhs            ~ RelatedIn.get_prep_lookup rhs-narrowing
#                                  (related_lookups.py fix: route narrowing
#                                  through set_values, not add_fields)
#       load-bearing post: Implies(narrow-guard, len==1 AND [0]==target AND
#                          flag True AND aux False) AND Implies(no-narrow,
#                          untouched incl. aux == Old(...))
#
# READ-ONLY INPUTS: NONE. Every function takes the q fields under FULL permission
# (Acc(q.f), not Acc(q.f, 1/2)) because all three operations WRITE q. There is no
# Acc(...,1/2) param, so the permission-level frame-mutation reject case is N/A
# (a write to q is what the spec sanctions). The frame discipline that IS
# defended here is a VALUE frame — the clauses that pin what each op does to the
# fields it must clear or leave untouched — attacked directly by the value-frame
# reject cases below (faith-aux-preserved-in-project, frame-cols-in-aux).
from pathlib import Path

INSTANCE = "django__django-16032"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each appears exactly once and lies strictly inside an impl
# region — verified by the count guard in _swap).
# ---------------------------------------------------------------------------

# project_columns impl (verbatim)
_PROJ_IMPL = (
    "    q.selected_columns = []\n"
    "    q.selected_columns = [column]\n"
    "    q.restricted_to_explicit_columns = True\n"
    "    # projection re-derives the expression-tracking structure for the chosen\n"
    "    # ordinary columns, which leaves it empty.\n"
    "    q.aux_expr_materialized = False"
)

# attach_auxiliary_expressions impl body line (verbatim, the only executable line)
_AUX_LINE = "    q.aux_expr_materialized = True"

# prepare_in_rhs impl guarded call (verbatim)
_RHS_CALL = "        project_columns(q, target_column)"
_RHS_GUARD = (
    "    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls
    # that MUST verify. If one fails, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-project-reorder-no-reset",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _PROJ_IMPL,
            # Correct but restructured: clear the aux mask and set the flag
            # FIRST, and assign the single column directly without the
            # intermediate empty-list reset. The post (len==1, [0]==column,
            # flag True, aux False) still holds; no proof obligation is
            # dropped (no loop / framing lemma).
            "    q.aux_expr_materialized = False\n"
            "    q.restricted_to_explicit_columns = True\n"
            "    q.selected_columns = [column]",
        ),
        "rationale": (
            "set_values's effect is order-independent for the twin's three "
            "fields; clearing the mask and setting the flag first while "
            "skipping the redundant empty reset is still exactly the gold "
            "projection. Must verify — else the post is pinned to an "
            "incidental statement ORDER (SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-rhs-inline-projection",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _RHS_CALL,
            # Correct but different shape: instead of calling project_columns,
            # inline the SAME state updates the projection performs (including
            # the mask clearing). This is behaviourally identical to
            # set_values([target_column]) and must verify under
            # prepare_in_rhs's own postcondition.
            "        q.selected_columns = []\n"
            "        q.selected_columns = [target_column]\n"
            "        q.restricted_to_explicit_columns = True\n"
            "        q.aux_expr_materialized = False",
        ),
        "rationale": (
            "narrowing the rhs by inlining the projection state-updates is the "
            "same observable effect as calling project_columns / set_values; the "
            "narrowing-implication post (one col == target AND flag True) holds. "
            "Must verify — else the spec forces a particular CALL structure, not "
            "the behaviour (SPEC-TOO-STRONG)."
        ),
    },
    # =====================================================================
    # ADMISSIBILITY — the precondition admits a normal F2P-shaped input.
    # The narrowing branch is reachable: inside the guard the in-domain
    # property (rhs unprojected) is assertable and project_columns's Requires
    # is establishable. If this can't verify => PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-rhs-narrow-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _RHS_CALL,
            # Keep the gold call but assert the in-domain narrowing precondition
            # (rhs was never projected) holds at the call site — proving the
            # branch is reachable for a legitimate unprojected, non-pk-target rhs
            # and that project_columns's Acc/Requires are framed for that input.
            "        Assert(not q.restricted_to_explicit_columns)\n"
            "        Assert(not target_is_unique_key)\n"
            "        project_columns(q, target_column)",
        ),
        "rationale": (
            "an F2P-shaped rhs (annotate+alias, unprojected, non-pk target) must "
            "satisfy prepare_in_rhs's Requires AND reach the narrowing branch; the "
            "two Asserts hold from the guard and the call's Requires is framed. "
            "Must verify — else PRECOND-TOO-STRONG (the spec rejects a normal in)."
        ),
    },
    # =====================================================================
    # UNIQUENESS / REJECT — same-spec WRONG impls that MUST be rejected.
    # Each carries the refinement argument that its faithful real patch would
    # NOT resolve the F2P/P2P. If any VERIFIES => SPEC-TOO-WEAK.
    # =====================================================================
    {
        # THE primary reported bug (query.py): the pre-patch derived property
        # re-coupled has_select_fields to the annotation mask.
        "id": "weak-aux-recouples-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _AUX_LINE,
            "    q.aux_expr_materialized = True\n"
            "    if q.aux_expr_materialized:\n"
            "        q.restricted_to_explicit_columns = True",
        ),
        "refinement": (
            "this is the PRE-PATCH dynamic property verbatim: has_select_fields "
            "DERIVED from a non-empty annotation_select_mask. Its faithful real "
            "patch (the @property over self.annotation_select_mask) makes an "
            "annotate().alias() rhs report has_select_fields True, so RelatedIn "
            "skips narrowing and the sub-select returns N columns -> "
            "OperationalError 'sub-select returns 10 columns - expected 1'. F2P "
            "test_annotation_and_alias_filter_in_subquery would FAIL -> NOT "
            "resolved."
        ),
        "rationale": (
            "rejected by attach_auxiliary_expressions's post "
            "restricted_to_explicit_columns == Old(restricted_to_explicit_columns): "
            "on an unprojected query Old(...) is False but the rival sets it True. "
            "(This is exactly model_prepatch.py's failing clause.)"
        ),
    },
    {
        # Second fixed behaviour (related_lookups.py): pre-patch narrowing via
        # clear_select_clause()+add_fields set the columns but NOT the flag.
        "id": "weak-rhs-narrow-without-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _RHS_CALL,
            # PRE-PATCH narrowing: set selected_columns to [target] WITHOUT going
            # through project_columns, so the explicit-projection flag is NOT set.
            "        q.selected_columns = []\n"
            "        q.selected_columns = [target_column]",
        ),
        "refinement": (
            "this is the PRE-PATCH related_lookups narrowing: clear_select_clause() "
            "+ add_fields([target], True). Under the new flag regime this sets the "
            "SELECT columns but leaves has_select_fields False, so the rhs is not "
            "recognised as explicitly projected — the ToFieldTests / "
            "test_annotation_and_alias_filter_related_in_subquery behaviour the "
            "patch fixes regresses -> NOT resolved. (model_prepatch_2.py.)"
        ),
        "rationale": (
            "rejected by prepare_in_rhs's narrowing implication: "
            "Implies((not Old(flag)) and (not target_is_unique_key), ... AND "
            "restricted_to_explicit_columns is True). The rival narrows the "
            "columns but never sets the flag, so the True conjunct fails."
        ),
    },
    {
        # PARTIAL-DOMAIN: correct on the (unprojected, non-pk) sub-domain but
        # over-fires — narrows even when the target IS a unique key (pk target),
        # which the patch must leave untouched (reverse-FK / pk-target case).
        "id": "weak-rhs-overfires-on-pk-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _RHS_GUARD,
            # Drop the `and not target_is_unique_key` half of the guard: now the
            # branch fires on a pk-target rhs too, narrowing a query the patch
            # leaves alone.
            "    if (not q.restricted_to_explicit_columns):",
        ),
        "refinement": (
            "drops the `not target_field.primary_key` half of the real guard. Its "
            "faithful real patch would narrow the rhs of a reverse-FK / pk-target "
            "related __in (e.g. child__in where the target is the pk) that the "
            "real RelatedIn.get_prep_lookup must leave untouched — changing SQL on "
            "the pk-target sub-domain that the annotations/ToField P2P suite "
            "exercises -> NOT resolved (and G-AX A-reference-3c asserts a pk-target "
            "rhs stays unprojected)."
        ),
        "rationale": (
            "rejected by prepare_in_rhs's no-narrow implication: "
            "Implies(Old(flag) or target_is_unique_key, flag == Old(flag) AND "
            "ToSeq(selected_columns) == Old(ToSeq(...))). With "
            "target_is_unique_key True and Old(flag) False the rival still "
            "narrows, breaking the 'left untouched' clause."
        ),
    },
    {
        # FAITHFULNESS: project_columns must CLEAR the aux-expr structure
        # (set_values re-derives the annotation mask empty for an ordinary
        # column). A rival that PRESERVES the materialized mask across the
        # projection — the exact unfaithful frame the G-PANEL-2 re-audit
        # caught — must be rejected.
        "id": "faith-aux-preserved-in-project",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _PROJ_IMPL,
            "    q.selected_columns = []\n"
            "    q.selected_columns = [column]\n"
            "    q.restricted_to_explicit_columns = True",
        ),
        "refinement": (
            "a real set_values that left the annotation_select_mask untouched "
            "(instead of re-deriving it via set_annotation_mask(annotation_names)) "
            "would keep the annotate()+alias() annotations in the SELECT of a "
            "narrowed __in rhs: the sub-select would return the target column "
            "PLUS the annotation -> 'sub-select returns 2 columns - expected 1' "
            "-> F2P test_annotation_and_alias_filter_in_subquery FAILS -> NOT "
            "resolved. (This preserved-mask frame was the model's own prior, "
            "unfaithful postcondition.)"
        ),
        "rationale": (
            "rejected by project_columns's post aux_expr_materialized is False: "
            "on an input whose Old aux is True (annotate+alias already attached), "
            "leaving the mask materialized violates the clearing clause."
        ),
    },
    {
        # VALUE-FRAME: attach_auxiliary_expressions must NOT touch the SELECT
        # columns. A rival that clears selected_columns while materializing.
        "id": "frame-cols-in-aux",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _AUX_LINE,
            "    q.aux_expr_materialized = True\n"
            "    q.selected_columns = []",
        ),
        "refinement": (
            "annotate()/alias() materialize the annotation mask but must leave the "
            "SELECT projection columns alone. A real add_annotation that wiped the "
            "values()-selected columns would change the result rows of an "
            "already-projected queryset that is then annotated/aliased — the "
            "alias-after-annotation / values-with-alias P2P tests would regress -> "
            "NOT resolved."
        ),
        "rationale": (
            "rejected by attach_auxiliary_expressions's frame post "
            "ToSeq(selected_columns) == Old(ToSeq(selected_columns)): clearing a "
            "non-empty selection breaks the sequence equality."
        ),
    },
    {
        # SUPPORTING mechanical near-miss (still carries a refinement): the
        # narrowing branch narrows to the WRONG column (a constant 0 rather
        # than the target). Pins the value-grounded post clause.
        "id": "weak-rhs-wrong-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _RHS_CALL,
            # narrow (with the full projection effect: flag set, mask cleared)
            # but to the wrong column id (0, not target).
            "        q.selected_columns = []\n"
            "        q.selected_columns = [0]\n"
            "        q.restricted_to_explicit_columns = True\n"
            "        q.aux_expr_materialized = False",
        ),
        "refinement": (
            "narrowing to a fixed column id 0 rather than the lookup's actual "
            "target_field column means set_values would project the rhs onto the "
            "wrong column — the sub-select would return the wrong column / wrong "
            "rows for any non-zero target, so the related __in result set is wrong "
            "-> F2P test_annotation_and_alias_filter_related_in_subquery fails -> "
            "NOT resolved. (Supporting near-miss; still a real refinement.)"
        ),
        "rationale": (
            "rejected by prepare_in_rhs's narrowing implication conjunct "
            "selected_columns[0] == target_column: the value is grounded in the "
            "arg target_column, so a constant 0 fails whenever target_column != 0 "
            "(the post quantifies over all in-domain inputs)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane: this bundle consumes NO @ContractOnly axioms (meta.axioms == []).
# The three operations are modelled DEEPLY (spelled-out state updates); the real
# Django primitives they correspond to are A-reference observations validated
# out-of-band by axiom_check.py / G-AX (already pass, 11 observations on real
# post-patch Django 4.2 in-container). There are no consumed-axiom soundness or
# caller-domain-containment obligations to probe here, so AXIOM_TESTS is empty.
# ---------------------------------------------------------------------------
AXIOM_TESTS = []
