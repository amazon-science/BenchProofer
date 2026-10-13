# properties.py — PBT falsification battery for django__django-15252. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py)
# ---------------------------------------------------------------------------
#   migrate(executor: Executor, pending: Optional[List[int]]) -> None
#     Requires(Acc(executor.table_present, 1 / 2))      # READ-ONLY (fractional)
#     Requires(Acc(executor.schema_ensured))            # FULL — mutated WRITE flag
#     Requires(executor.schema_ensured is False)
#     Requires(Acc(executor.records_read))              # FULL — mutated QUERY flag
#     Requires(executor.records_read is False)
#     Requires(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))  # READ-ONLY
#     Ensures(Acc(executor.table_present, 1 / 2))       # read-only perm returned
#     Ensures(Acc(executor.schema_ensured))
#     Ensures(Acc(executor.records_read))
#     Ensures(Implies(pending is not None, Acc(list_pred(pending), 1 / 2)))
#     Ensures(executor.table_present == Old(executor.table_present))           # (T) read-only unchanged
#     Ensures(executor.schema_ensured == (not no_pending_records(pending)))    # (1) WRITE-effect trigger
#     Ensures(executor.records_read ==
#             (not (no_pending_records(pending) and not Old(executor.table_present))))  # (2) QUERY-effect trigger
#     Ensures(Implies(not executor.records_read, executor.schema_ensured is False))     # (3) no-touch path
#   @Pure no_pending_records(pending) == (pending is not None and len(pending) == 0)
#
# Truth table the spec pins (schema_ensured, records_read, early-return):
#   plan=None  table=F/T -> (T, T, -)        write + read
#   plan=[]    table=F    -> (F, F, return)   THE no-touch short-circuit (F2P)
#   plan=[]    table=T    -> (F, T, -)        no write, but reads
#   plan=[x]   table=F/T  -> (T, T, -)        write + read
#
# Load-bearing clauses:
#   * (T) executor.table_present == Old(...) — the table-presence query is READ-ONLY.
#     `executor.table_present` is held at Acc(...,1/2): any impl that WRITES it
#     fails for INSUFFICIENT PERMISSION (frame-mutation, MANDATORY case below).
#   * (1) schema_ensured == (not no_pending_records(pending)) — the table-ensuring
#     WRITE effect occurs iff this connection was NOT determined to have no
#     migrations to record. Dropping the condition is EXACTLY the pre-patch bug
#     (model_prepatch.py, G-DIFF at line 139).
#   * (2) records_read == not (no_pending AND not Old(table_present)) — the
#     record-reading QUERY effect is skipped on EXACTLY the no-migrations +
#     no-table path. This is what the F2P assertNumQueries(0) measures; the
#     refinement (batch04_recover) calls it load-bearing: an impl that skips the
#     WRITE but still READS verifies (1) yet fails (2).
#   * (3) Implies(not records_read, schema_ensured is False) — on the no-touch
#     path NEITHER effect occurs.
#
# Ungrounded-oracle note: no_pending_records is @Pure but GROUNDED in the input
# (== `pending is not None and len(pending) == 0`, fully unfolded — no opaque
# answer-key). There is no wrong echo to build (directive 2): the cheapest impl
# that satisfies the contract must compute the real branch decision. We instead
# supply honest positive controls (different executable shape, same decision).
#
# No @ContractOnly axiom is consumed and there is no A-reference deep model
# (meta.json axioms=[]; G-AX = decision-logic equivalence, vacuous). AXIOM_TESTS
# is therefore empty; axiom_check.py validates the reduction, not an axiom.
from pathlib import Path

INSTANCE = "django__django-15252"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    if no_pending_records(pending):
        if not executor.table_present:
            # No migrations to record and no table present: assemble the result
            # without touching the connection (no write, no read).
            return
        # Table already present: fall through to the read-assembly path below;
        # no write effect on this branch.
    else:
        executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). These keep the gold DECISION but reshape
# the executable form; no loop / no fold, so no auto-undischargeable lemma is
# introduced (pilot pitfalls #2/#3 avoided).
# ===========================================================================

# pos-control-flat: compute the two boolean effects up front from the same
# observations the gold branches on, assign them, and return. The decision is
# identical to the gold (schema iff not no_pending; records iff not (no_pending
# and not table_present)); only the control shape changes (no nested if, a
# straight-line compute). The read-only field is never written.
_POS_FLAT = """    # impl-start
    npr = no_pending_records(pending)  # type: bool
    do_write = not npr  # type: bool
    do_read = not (npr and not executor.table_present)  # type: bool
    if do_write:
        executor.schema_ensured = True
    if do_read:
        executor.records_read = True
    return
    # impl-end"""

# pos-control-reorder: reorder the branch structure — handle the non-empty
# (write) case FIRST, then within the no_pending case split on table presence,
# setting records_read on the table-present sub-branch and short-circuiting on
# the no-table sub-branch. Behaviourally identical to the gold (same 6-case
# truth table); a branch-reorder, not a loop-direction flip.
_POS_REORDER = """    # impl-start
    if not no_pending_records(pending):
        executor.schema_ensured = True
        executor.records_read = True
        return
    if executor.table_present:
        executor.records_read = True
        return
    # no migrations to record and no table: no-touch short-circuit.
    return
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). A new module-level def would change the spec
# view and break same_spec, so the admissibility witness is injected INSIDE the
# impl region (elided from the spec view): construct a concrete F2P-shaped
# executor (table absent, as the F2P mocks has_table->False) and assert it
# satisfies migrate's exact Requires on the touched facets. The constructor
# Ensures give full Acc on the two effect flags both starting False, and 1/2 of
# table_present is sub-dividable. The real impl then runs unchanged over the
# actual params.
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm = Executor(False)  # table absent, exactly as the F2P mocks has_table->False
    # migrate's Requires on the touched facets is establishable for this object:
    Assert(Acc(adm.table_present, 1 / 2))     # 1/2 of the constructor's full Acc
    Assert(Acc(adm.schema_ensured))           # full perm from the constructor
    Assert(adm.schema_ensured is False)       # starts un-occurred
    Assert(Acc(adm.records_read))             # full perm from the constructor
    Assert(adm.records_read is False)         # starts un-occurred
    # A present, length-zero pending (plan==[]) is admissible too: no_pending_records
    # is well-defined on it (the F2P-shaped empty plan).
    empty = []  # type: List[int]
    Assert(no_pending_records(empty))
    # --- end admissibility witness; the real impl follows unchanged ---
    if no_pending_records(pending):
        if not executor.table_present:
            return
    else:
        executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness, MANDATORY) — executor.table_present is held at
# Acc(...,1/2): READ-ONLY. A rival that WRITES it to satisfy the read-only
# postcondition (T) executor.table_present == Old(executor.table_present)
# vacuously MUST be rejected for INSUFFICIENT PERMISSION. We keep every gold
# effect assignment verbatim and add ONE write to the read-only field, so the
# rejection is attributable solely to the write, not to a value change.
# ===========================================================================
_FRAME_MUTATE = """    # impl-start
    # Adversary: overwrite the read-only table-presence flag (held at 1/2 perm).
    # This must be rejected for insufficient permission to assign.
    executor.table_present = executor.table_present
    if no_pending_records(pending):
        if not executor.table_present:
            return
    else:
        executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""

# frame-mutate-flip: the sharper variant — write the OPPOSITE value to the
# read-only field, which would also violate (T) if it could be written. Still
# rejected first for insufficient permission (the spec never grants > 1/2 on
# table_present, so any assignment fails before any value reasoning).
_FRAME_FLIP = """    # impl-start
    executor.table_present = not executor.table_present
    if no_pending_records(pending):
        if not executor.table_present:
            return
    else:
        executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN / CONTROL-FLOW-EFFECT — rivals that share the spec
# exactly and change ONLY the impl. Each MUST be rejected; a verifying rival is
# a true verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-unconditional-schema: THE pre-patch bug (model_prepatch.py). Set
# schema_ensured = True UNCONDITIONALLY (ensure_schema first, always), then
# always read. Correct on plan!=[] but diverges on plan==[] (it writes the
# table even when there is nothing to record). Rejected by clause (1).
_UNIQ_UNCOND_SCHEMA = """    # impl-start
    executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""

# uniq-always-read: skip the WRITE correctly (clause 1 holds) but ALWAYS issue
# the record-reading QUERY effect — i.e. drop the no-touch short-circuit and
# read records even on the plan==[] + no-table path. This is the control-flow-
# effect attack the refinement calls load-bearing: it verifies (1) yet performs
# the QUERY effect the F2P assertNumQueries(0) forbids. Rejected by clause (2).
_UNIQ_ALWAYS_READ = """    # impl-start
    if not no_pending_records(pending):
        executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""

# uniq-ignore-table: short-circuit on plan==[] REGARDLESS of table presence —
# i.e. skip the read even when the table IS already present. Correct on the
# no-table empty path, but on plan==[] + table-present it leaves records_read
# False, whereas the spec requires the QUERY effect there. Rejected by clause
# (2) on the (no_pending, table_present) sub-domain.
_UNIQ_IGNORE_TABLE = """    # impl-start
    if no_pending_records(pending):
        return
    executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""

# uniq-write-on-notouch: on the no-touch path, ALSO set the WRITE flag before
# returning. This violates clause (3) Implies(not records_read, schema_ensured
# is False) AND clause (1) on plan==[]. The faithful patch would call
# ensure_schema (CREATE TABLE) on a connection with nothing to record and no
# table — exactly the side effect the fix removes. Rejected by clauses (1)/(3).
_UNIQ_WRITE_NOTOUCH = """    # impl-start
    if no_pending_records(pending):
        if not executor.table_present:
            executor.schema_ensured = True
            return
    else:
        executor.schema_ensured = True
    executor.records_read = True
    return
    # impl-end"""

# uniq-skip-all: never set either effect flag (vacuous "do nothing"). Correct
# only on the single no-touch path; wrong everywhere a write and/or read is
# required. Rejected by clause (1) on plan!=[] (and clause (2) on plan==[]+table).
# Supporting near-miss with a real refinement (a patch that removed both the
# ensure_schema call and the record-reading assembly would resolve nothing).
_UNIQ_SKIP_ALL = """    # impl-start
    return
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-flat",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_FLAT),
        "rationale": "structurally-different CORRECT impl: compute the two boolean "
                     "effects up front from the same observations the gold branches "
                     "on (do_write = not no_pending_records; do_read = not (no_pending "
                     "and not table_present)) and assign them straight-line. Identical "
                     "6-case truth table; the read-only field is never written. No loop "
                     "/ no fold => no auto-undischargeable lemma (pilot #2/#3). If a "
                     "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "branch-reorder: handle the write (plan!=[]) case first with an "
                     "early return, then split the no_pending case on table presence "
                     "(read on table-present, no-touch short-circuit otherwise). Same "
                     "decision as the gold on all 6 cases; a control-shape reshape, not "
                     "a loop-direction flip. Must verify (else SPEC-TOO-STRONG).",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) constructs a concrete "
                     "F2P-shaped Executor(False) (table absent, exactly as the F2P "
                     "mocks has_table->False) and asserts migrate's exact Requires on "
                     "the touched facets hold for it: 1/2 of table_present, full Acc on "
                     "both effect flags, both starting False; plus that an empty plan "
                     "(plan==[]) is a well-defined no_pending_records input. The real "
                     "impl then runs unchanged. If the precondition could not be "
                     "established for this legitimate input the Asserts fail => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (must reject for insufficient permission) ----
    {
        "id": "frame-mutate-readonly-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUTATE),
        "refinement": "writing executor.table_present corresponds to a patch that "
                      "MUTATES the result of self.recorder.has_table() — the bookkeeping "
                      "table-presence query. has_table() (recorder.py:53) is a pure "
                      "read-only introspection query that returns whether the table "
                      "exists; nothing in the gold prologue assigns it. A patch that "
                      "wrote to it would corrupt the table-existence observation the "
                      "WHOLE decision branches on (has_table gates the short-circuit), "
                      "changing which connections create the table — it does not resolve "
                      "and is not the gold edit.",
        "rationale": "rejected by the PERMISSION SYSTEM: executor.table_present is held "
                     "at Acc(executor.table_present, 1/2) (read-only). An assignment "
                     "requires full permission; only 1/2 is held, so the write fails "
                     "for insufficient permission BEFORE any value reasoning. Every gold "
                     "effect assignment is kept verbatim, so the rejection is "
                     "attributable solely to the read-only write.",
    },
    {
        "id": "frame-flip-readonly-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_FLIP),
        "refinement": "the sharper frame-mutation: writing the OPPOSITE value to the "
                      "read-only table-presence flag corresponds to a patch that flipped "
                      "the has_table() observation — it would short-circuit on the wrong "
                      "connections (create the table where it should not, or skip where "
                      "it should). Such a patch does not resolve and is not the gold "
                      "edit. Supporting frame-mutation variant.",
        "rationale": "rejected by the PERMISSION SYSTEM: any assignment to "
                     "executor.table_present needs full Acc; only Acc(...,1/2) is held, "
                     "so it fails for insufficient permission. (It would ALSO violate (T) "
                     "table_present == Old(table_present) if it could be written, but the "
                     "permission failure fires first.)",
    },

    # ---- uniqueness / partial-domain / control-flow-effect (must reject) ----
    {
        "id": "uniq-unconditional-schema",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_UNCOND_SCHEMA),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags at model_prepatch.py:139: the "
                      "prologue ran self.recorder.ensure_schema() UNCONDITIONALLY, first, "
                      "then always read records. The F2P "
                      "test_migrate_test_setting_false_ensure_schema / 'The "
                      "django_migrations table is not created if there are no migrations' "
                      "mocks has_table->False, runs migrate([], plan=[]), and asserts "
                      "ensure_schema is NOT called (assertNumQueries(0)); with the WRITE "
                      "unconditional, ensure_schema runs and CREATE TABLE is issued — the "
                      "assertion fails. Its faithful real patch (the un-patched "
                      "unconditional ensure_schema) is exactly what does NOT resolve.",
        "rationale": "rejected by clause (1) schema_ensured == (not "
                     "no_pending_records(pending)): on plan==[] (no_pending True) the "
                     "spec requires schema_ensured False, but the rival sets it True. "
                     "(It also violates clause (2) on the no-table empty path.)",
    },
    {
        "id": "uniq-always-read",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_READ),
        "refinement": "skips the WRITE correctly (clause 1 holds) but ALWAYS issues the "
                      "record-reading QUERY effect — i.e. a patch that gated ensure_schema "
                      "on plan!=[] but DID NOT add the no-table short-circuit "
                      "(return _create_project_state(with_applied_migrations=False)). On "
                      "the F2P shape (plan==[], no table) it still assembles the result by "
                      "reading applied-migration records, issuing queries — failing the "
                      "F2P assertNumQueries(0) even though ensure_schema is not called. "
                      "This is the partial fix the batch04_recover refinement was written "
                      "to catch; it does NOT resolve.",
        "rationale": "rejected by clause (2) records_read == not (no_pending_records "
                     "AND not Old(table_present)): on plan==[] + table absent the spec "
                     "requires records_read False, but the rival sets it True. The QUERY "
                     "effect on the no-touch path is the load-bearing discriminator.",
    },
    {
        "id": "uniq-ignore-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_IGNORE_TABLE),
        "refinement": "short-circuits on plan==[] REGARDLESS of table presence — a patch "
                      "that wrote `if plan == []: return _create_project_state(...)` "
                      "WITHOUT the inner `if not self.recorder.has_table()` guard. On "
                      "plan==[] with the table ALREADY present, the gold code falls "
                      "through and reads records (assertNumQueries>0 P2P paths), but this "
                      "rival skips the read. Dropping the has_table guard changes "
                      "behaviour on the table-present empty-plan sub-domain — the P2P "
                      "migration tests that run with an existing django_migrations table "
                      "would see the normal record-reading assembly skipped; it does NOT "
                      "resolve.",
        "rationale": "rejected by clause (2) records_read == not (no_pending_records AND "
                     "not Old(table_present)): on plan==[] + table PRESENT, no_pending is "
                     "True but Old(table_present) is True, so the spec requires "
                     "records_read True; the rival returns early leaving it False. "
                     "Partial-domain divergence on the (no_pending, table_present) "
                     "sub-domain.",
    },
    {
        "id": "uniq-write-on-notouch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_WRITE_NOTOUCH),
        "refinement": "on the no-touch path it ALSO sets the WRITE flag — a patch that "
                      "called ensure_schema (CREATE TABLE) on a connection with no "
                      "migrations to record AND no table, the exact side effect the fix "
                      "removes. The F2P asserts ensure_schema is NOT called on this path; "
                      "this rival calls it. It does NOT resolve.",
        "rationale": "rejected by clause (1) schema_ensured == (not "
                     "no_pending_records(pending)) on plan==[] (requires False, rival "
                     "sets True) AND by clause (3) Implies(not records_read, "
                     "schema_ensured is False) on the no-touch path (records_read False "
                     "but schema_ensured True).",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-skip-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_ALL),
        "refinement": "a do-nothing prologue (neither WRITE nor READ on any path) "
                      "corresponds to a patch that removed BOTH ensure_schema AND the "
                      "record-reading assembly — migrations would never be recorded and "
                      "no applied-record state would be read. It is correct only on the "
                      "single no-touch path and wrong on every path requiring a write "
                      "and/or read; it resolves nothing. Supporting near-miss for the "
                      "two effect-trigger clauses.",
        "rationale": "rejected by clause (1) on plan!=[] (schema_ensured must be True, "
                     "rival leaves it False) and by clause (2) on plan==[] + table "
                     "present (records_read must be True, rival leaves it False).",
    },
]


# ===========================================================================
# AXIOM LANE — none. meta.json axioms=[]; no @ContractOnly axiom is consumed and
# there is no A-reference deep model. The three primitives the prologue consults
# (has_table, ensure_schema, the record-reading result assembly) are each reduced
# to the single boolean observation the F2P tests make, and the changed DECISION
# over those observations is modelled DEEPLY in the impl region. axiom_check.py /
# G-AX validates the decision-logic equivalence (model observations ==
# gold-patched observations on every work-list-shape x table-existence combo,
# plus the F2P witness), NOT an axiom's over-approximation — so there is no
# axiom-soundness / axiom-containment obligation to probe. (G-AX status is
# 'vacuous' in meta.json.)
# ===========================================================================
AXIOM_TESTS = []
