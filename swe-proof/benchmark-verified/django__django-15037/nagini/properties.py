# properties.py — PBT manifest for django__django-15037. NOT a Nagini module; a
# record of adversarially-reasoned falsification cases against the FROZEN spec of
# `relation_field`. The runner (swebench_nagini.pbt) parses SPEC_TESTS /
# AXIOM_TESTS, writes each spec `module` to a temp file, re-runs the Nagini
# verifier on the HOST, and checks `same_spec` against model.py.
#
# Defended surface (model.py):
#   relation_field(unique_or_pk: bool,
#                  referenced_column: List[int]  Acc(.,1/2)  READ-ONLY,
#                  referenced_table:  List[int]  Acc(.,1/2)  READ-ONLY,
#                  table_name:        List[int]  Acc(.,1/2)  READ-ONLY,
#                  other_pk_column:   Optional[List[int]]    READ-ONLY 1/2)
#   -> RelationField, with five LOAD-BEARING postcondition clauses, all grounded
#      in the args via @Pure helpers names_equal / qualifier_required:
#     (1) Result().is_one_to_one == unique_or_pk
#     (2) Result().rel_to_self  == names_equal(referenced_table, table_name)
#     (3) Result().needs_qualifier == qualifier_required(unique_or_pk,
#                                       referenced_column, other_pk_column)
#     (4) Implies(needs_qualifier, ToSeq(qualifier_column) == ToSeq(referenced_column))
#     (5) Implies(not needs_qualifier, len(qualifier_column) == 0) — the absent
#         qualifier is pinned to the canonical empty value (closes the don't-care
#         gap G-PANEL-1's atk_6 exploited)
#   plus frame: all four inputs returned at Acc(.,1/2) (read-only), the result
#   fully owned.
#
# Authoring discipline: every variant is built by region-surgery (_swap) editing
# ONLY text strictly between `# impl-start` and `# impl-end` (lines 125-147 of
# model.py, the nested invariants region included). The spec_view elides the
# whole impl region, so same_spec is GUARANTEED for every case below — confirmed
# by the self-validation harness.
from pathlib import Path

INSTANCE = "django__django-15037"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats in this model)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} occurs {src.count(old)} times")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — all live strictly INSIDE the impl region (impl-start..impl-end).
# ---------------------------------------------------------------------------

# The full gold impl body (between the markers), used to splice whole-body
# rewrites for the positive controls.
_GOLD_BODY = """    out = RelationField()
    # Build a private copy of the referenced-column name up front, so all heap
    # allocation precedes the pure decisions (keeps framing local).
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_column):
        # invariants-start
        Invariant(Acc(list_pred(referenced_column), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_column))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
        # invariants-end
        col_copy.append(referenced_column[i])
        i = i + 1
    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    return out"""


# === SPEC LANE =============================================================

SPEC_TESTS = []

# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — read-only inputs). A rival that satisfies the
#    qualifier-column clause (4) NOT by copying `referenced_column` into a fresh
#    list but by mutating the half-permission read-only input itself. With only
#    Acc(list_pred(referenced_column), 1/2) a write (`.append`) needs full
#    permission, so the verifier MUST reject for INSUFFICIENT PERMISSION. A
#    byte-fuzzer never thinks to write the input. The gold postcondition is kept
#    verbatim so the rejection is attributable to the illegal write.
# ---------------------------------------------------------------------------
_FRAME_MUT_BODY = """    out = RelationField()
    # ATTACK: instead of copying into a fresh list, scribble on the read-only
    # input `referenced_column` (Acc(.,1/2)) to "produce" the qualifier value.
    referenced_column.append(0)
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = referenced_column
    return out"""

SPEC_TESTS.append({
    "id": "frame-mutation-write-readonly-col",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_BODY, _FRAME_MUT_BODY),
    "refinement": (
        "In the real patch `relations[column_name]` is the introspected loop "
        "datum (a tuple unpacked into ref_db_column/ref_db_table); the inspectdb "
        "block never writes it. A faithful patch that mutated the introspected "
        "column name in place would corrupt `relations`, change the rendered "
        "to_field / rel_to for every later column referencing that table, and "
        "diverge from the expected `to_field='people_unique_id'` output — it "
        "would NOT resolve test_foreign_key_to_field."),
    "rationale": (
        "Rejection comes from the permission system: referenced_column is held "
        "at Acc(list_pred(.),1/2) (read-only) per the Requires/Ensures frame; "
        "`.append` requires full list_pred permission, so the verifier reports "
        "insufficient permission. If it VERIFIED the frame guarantee would be "
        "hollow (a mutating impl admitted)."),
})

# ---------------------------------------------------------------------------
# 2. UNGROUNDED-ORACLE ECHO — N/A as a *wrong* echo. Both @Pure helpers
#    (names_equal, qualifier_required) are GROUNDED: fully unfolded boolean
#    functions of the args, no opaque answer-key. Echoing them
#    (`out.needs_qualifier = qualifier_required(...)`) is the CORRECT answer, so
#    there is no wrong echo to build. We therefore supply the honest
#    cheapest-impl positive control instead: echo the grounded oracle directly
#    (no up-front copy loop), which MUST verify.
# ---------------------------------------------------------------------------
_ECHO_POS_BODY = """    out = RelationField()
    # Cheapest honest impl: directly echo the GROUNDED @Pure decisions. There is
    # no answer-key to cheat; these are functions of the args. Build the copy
    # only on the branch that needs it.
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    qr = qualifier_required(unique_or_pk, referenced_column, other_pk_column)
    out.needs_qualifier = qr
    if out.needs_qualifier:
        col_copy = []  # type: List[int]
        i = 0
        while i < len(referenced_column):
            # invariants-start
            Invariant(Acc(list_pred(referenced_column), 1 / 2))
            # qualifier_required also reads other_pk_column, so carry its read
            # permission into the loop and pin its (unchanged) value, otherwise
            # the loop havocs the bridge between out.needs_qualifier and clause(3).
            Invariant(Implies(other_pk_column is not None, Acc(list_pred(other_pk_column), 1 / 2)))
            Invariant(Acc(list_pred(col_copy)))
            Invariant(0 <= i and i <= len(referenced_column))
            Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
            Invariant(qualifier_required(unique_or_pk, referenced_column, other_pk_column) == qr)
            # invariants-end
            col_copy.append(referenced_column[i])
            i = i + 1
        # Keep the gold framing Assert so clause (4) bridges take(len)==whole.
        Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
        out.qualifier_column = col_copy
    return out"""

SPEC_TESTS.append({
    "id": "pos-echo-grounded-oracle",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_BODY, _ECHO_POS_BODY),
    "rationale": (
        "Grounded-oracle positive control: directly assigning the @Pure "
        "decisions and copying the column only on the True branch is a faithful, "
        "structurally-different correct impl. It MUST verify (clauses 1-5 hold "
        "verbatim). If it were rejected the spec would be SPEC-TOO-STRONG. Note "
        "in assessment: qualifier_required is grounded, so no *wrong* echo "
        "exists — this is the honest positive control the plan asks for in lieu "
        "of an ungrounded-echo reject."),
})

# ---------------------------------------------------------------------------
# 3a. PARTIAL-DOMAIN — the pre-patch behaviour (model_prepatch): decide the
#     relation kind and self/other target correctly but NEVER emit the
#     qualifier. Correct on every OneToOne and every FK-to-PK input; diverges
#     exactly on the FK-to-non-PK sub-domain (clause 3). This is the literal bug
#     the gold patch fixes and the F2P test exercises.
# ---------------------------------------------------------------------------
_PREPATCH_BODY = """    out = RelationField()
    # ATTACK (pre-patch): never emit the referenced-column qualifier. Correct on
    # OneToOne and FK-to-PK inputs; wrong on the FK-to-non-PK sub-domain.
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    return out"""

SPEC_TESTS.append({
    "id": "partial-domain-never-emit-qualifier",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_BODY, _PREPATCH_BODY),
    "refinement": (
        "This is exactly model_prepatch: the pre-patch inspectdb block decides "
        "rel_type and rel_to but never sets extra_params['to_field']. On the "
        "F2P case (FK other_id -> foo(people_unique_id), PK='id' != ref column) "
        "it omits to_field, so inspectdb renders ForeignKey WITHOUT "
        "to_field='people_unique_id' — test_foreign_key_to_field FAILS. The "
        "faithful patch does NOT resolve."),
    "rationale": (
        "Rejection comes from postcondition clause (3): "
        "needs_qualifier == qualifier_required(...); leaving needs_qualifier "
        "False when qualifier_required is True falsifies it. This mirrors G-DIFF."),
})

# ---------------------------------------------------------------------------
# 3b. PARTIAL-DOMAIN — drop the `len(other_pk_column) > 0` falsy-PK guard at the
#     impl level by emitting a qualifier whenever the relation is a plain FK and
#     there IS a referenced column (ignoring whether other_pk_column differs).
#     Correct on most fuzz inputs but over-emits on the FK-to-PK and
#     empty-string-PK sub-domains. (Wrong VALUE of needs_qualifier vs clause 3.)
# ---------------------------------------------------------------------------
_OVEREMIT_BODY = """    out = RelationField()
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_column):
        # invariants-start
        Invariant(Acc(list_pred(referenced_column), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_column))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
        # invariants-end
        col_copy.append(referenced_column[i])
        i = i + 1
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    # ATTACK: emit the qualifier for EVERY plain FK (ignore PK presence/equality).
    if not unique_or_pk:
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    return out"""

SPEC_TESTS.append({
    "id": "partial-domain-overemit-qualifier",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_BODY, _OVEREMIT_BODY),
    "refinement": (
        "A faithful patch of this shape would set extra_params['to_field'] = "
        "ref_db_column for EVERY ForeignKey, even when the referenced table's PK "
        "IS the referenced column (or has none / is the falsy empty string). The "
        "real `if ref_pk_column and ref_pk_column != ref_db_column` guard "
        "suppresses to_field there; emitting it always produces spurious "
        "to_field= keywords on plain FKs across the inspectdb suite (the "
        "PASS_TO_PASS field-type / introspection tests render FKs without "
        "to_field), so it would break P2P and is not the gold behaviour."),
    "rationale": (
        "Rejection from clause (3): on inputs where qualifier_required is False "
        "but unique_or_pk is also False (FK with PK == ref column, or PK None / "
        "empty), needs_qualifier is forced True != qualifier_required(...)."),
})

# ---------------------------------------------------------------------------
# 3c. PARTIAL-DOMAIN / value-double-mask — emit the qualifier on the correct
#     domain but name the WRONG column (referenced_table instead of
#     referenced_column). needs_qualifier matches clause 3, ownership holds, but
#     clause (4) ToSeq(qualifier_column) == ToSeq(referenced_column) is violated.
# ---------------------------------------------------------------------------
_WRONGCOL_BODY = """    out = RelationField()
    # Build a copy of the TABLE name (wrong source) instead of the column name.
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_table):
        # invariants-start
        Invariant(Acc(list_pred(referenced_table), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_table))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_table).take(i))
        # invariants-end
        col_copy.append(referenced_table[i])
        i = i + 1
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        # ATTACK: name the referenced TABLE, not the referenced column.
        out.qualifier_column = col_copy
    return out"""

SPEC_TESTS.append({
    "id": "wrong-qualifier-column-value",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_BODY, _WRONGCOL_BODY),
    "refinement": (
        "A faithful patch that wrote extra_params['to_field'] = ref_db_table "
        "(the other table name) instead of ref_db_column would render "
        "to_field='inspectdb_peoplemoredata' rather than "
        "to_field='people_unique_id' — test_foreign_key_to_field asserts the "
        "latter exact string, so it FAILS. Does NOT resolve."),
    "rationale": (
        "Rejection from clause (4): Implies(needs_qualifier, "
        "ToSeq(qualifier_column) == ToSeq(referenced_column)); the table-name "
        "copy has ToSeq == ToSeq(referenced_table), generally != "
        "ToSeq(referenced_column)."),
})

# ---------------------------------------------------------------------------
# 3c'. UNCONSTRAINED-ABSENT-VALUE — the historical G-PANEL-1 weakness (atk_6):
#      keep the gold decisions but ALSO write qualifier_column on the
#      needs_qualifier == False branch. Under the pre-repair spec (clause 4 an
#      Implies only) this VERIFIED; clause (5) now pins the absent case to the
#      empty canonical value, so the verifier MUST reject.
# ---------------------------------------------------------------------------
_ABSENT_SMUGGLE_BODY = """    out = RelationField()
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_column):
        # invariants-start
        Invariant(Acc(list_pred(referenced_column), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_column))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
        # invariants-end
        col_copy.append(referenced_column[i])
        i = i + 1
    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    else:
        # ATTACK (atk_6): smuggle a value into the absent-qualifier case.
        out.qualifier_column = col_copy
    return out"""

SPEC_TESTS.append({
    "id": "absent-qualifier-value-smuggled",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_BODY, _ABSENT_SMUGGLE_BODY),
    "refinement": (
        "In the repo the absent case has NO to_field value at all — the key is "
        "never set into extra_params. The model's total-record carrier must pin "
        "that absence to the canonical empty list, otherwise the qualifier_column "
        "field is a free channel on the False branch (the exact same-spec impl "
        "G-PANEL-1's atk_6 built, which the pre-repair spec admitted)."),
    "rationale": (
        "Rejection comes from clause (5): Implies(not needs_qualifier, "
        "len(qualifier_column) == 0); writing col_copy (a non-empty name on any "
        "non-empty referenced_column) on the else branch falsifies it."),
})

# ---------------------------------------------------------------------------
# 3d. PARTIAL-DOMAIN — wrong relation kind on the unique/PK sub-domain. Flip
#     is_one_to_one to the negation of unique_or_pk. (Cheap supporting reject
#     carrying a real refinement: rel_type would be inverted.)
# ---------------------------------------------------------------------------
_WRONGKIND_BODY = _GOLD_BODY.replace(
    "    out.is_one_to_one = unique_or_pk\n",
    "    out.is_one_to_one = not unique_or_pk  # ATTACK: invert relation kind\n",
    1,
)

SPEC_TESTS.append({
    "id": "wrong-relation-kind",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _GOLD_BODY, _WRONGKIND_BODY),
    "refinement": (
        "Inverting the kind makes a unique/PK relation render as ForeignKey and "
        "a plain FK as OneToOneField — every relational field in the inspectdb "
        "suite would get the wrong field type, breaking the PASS_TO_PASS "
        "field-type introspection tests; not the gold behaviour."),
    "rationale": (
        "Rejection from clause (1): Result().is_one_to_one == unique_or_pk; the "
        "negation falsifies it for both boolean inputs."),
})

# ---------------------------------------------------------------------------
# 4. CONTROL-FLOW-EFFECT — N/A. relation_field has no raise paths, no
#    capability tokens, and no side-effect channel distinct from the returned
#    RelationField value abstraction; rel_to_self / to_field rendering branch
#    downstream is unchanged by the patch. Omitted (justified in assessment).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL (soundness) — structurally different but CORRECT: reorder
#    the independent field assignments and compute the boolean decisions BEFORE
#    the (still up-front) column-copy loop. Every gold proof obligation it still
#    needs is kept: the take(i) loop invariant and the post-loop Assert that pins
#    ToSeq(col_copy) == ToSeq(referenced_column). MUST verify.
# ---------------------------------------------------------------------------
_POS_REORDER_BODY = """    out = RelationField()
    # Reorder: compute the two scalar decisions first; copy loop unchanged; the
    # post-loop framing Assert is kept so clause (4) still frames.
    out.rel_to_self = names_equal(referenced_table, table_name)
    out.is_one_to_one = unique_or_pk
    col_copy = []  # type: List[int]
    i = 0
    while i < len(referenced_column):
        # invariants-start
        Invariant(Acc(list_pred(referenced_column), 1 / 2))
        Invariant(Acc(list_pred(col_copy)))
        Invariant(0 <= i and i <= len(referenced_column))
        Invariant(ToSeq(col_copy) == ToSeq(referenced_column).take(i))
        # invariants-end
        col_copy.append(referenced_column[i])
        i = i + 1
    Assert(ToSeq(referenced_column).take(len(referenced_column)) == ToSeq(referenced_column))
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    return out"""

SPEC_TESTS.append({
    "id": "pos-reorder-decisions",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_BODY, _POS_REORDER_BODY),
    "rationale": (
        "Structurally-different correct impl: scalar decisions reordered ahead "
        "of the copy loop (they are independent of col_copy). The take(i) "
        "invariant and the post-loop Assert pinning ToSeq(col_copy) == "
        "ToSeq(referenced_column) are kept verbatim, so clause (4) still frames. "
        "Must verify; rejection would be SPEC-TOO-STRONG."),
})

# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input.
#    Expressed in-region (a new top-level caller would change the spec_view and
#    break same_spec): keep the gold impl and add an Assert that the read-only
#    Requires permission on each input is genuinely available at entry, i.e. the
#    precondition was established for this call. If the Requires were
#    unsatisfiable for a legitimate input the assert (or the unchanged body)
#    could not be proven -> PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_ADMISS_BODY = """    # ADMISSIBILITY: the precondition must admit a normal F2P-shaped input. The
    # half-permission read-only accesses on every input are available at entry.
    Assert(Acc(list_pred(referenced_column), 1 / 2))
    Assert(Acc(list_pred(referenced_table), 1 / 2))
    Assert(Acc(list_pred(table_name), 1 / 2))
    Assert(Implies(other_pk_column is not None, Acc(list_pred(other_pk_column), 1 / 2)))
""" + _GOLD_BODY

SPEC_TESTS.append({
    "id": "admiss-precond-available",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_BODY, _ADMISS_BODY),
    "rationale": (
        "In-region admissibility witness: the gold body is unchanged and a "
        "leading Assert confirms the Requires half-permission on each input is "
        "established at entry (the precondition accepts a normal column/table/"
        "Optional-PK input). If these could not be proven the precondition would "
        "be PRECOND-TOO-STRONG. Adding a top-level caller would alter the "
        "spec_view and break same_spec, so the witness is kept in-region."),
})


# === AXIOM LANE ============================================================
# No @ContractOnly axiom is consumed by the proof (meta.axioms == []). The only
# deep-model reference is the A-reference `other_pk_column <-> get_primary_key_
# column`, which is taken as an introspected input and validated by
# axiom_check.py / G-AX. There is no model-internal contract about a callee to
# probe, so the axiom lane is empty. (G-AX already runs axiom_check.py in Docker
# and passed; re-litigating it here would duplicate, not strengthen.)
AXIOM_TESTS = []
