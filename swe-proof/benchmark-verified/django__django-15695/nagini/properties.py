# properties.py — PBT falsification battery for django__django-15695.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec exactly (region-surgery: only the
# text strictly inside # impl-start / # impl-end is edited; the spec_view elides
# that whole region, so same_spec is guaranteed) and differ only in the impl.
#
# DEFENDED SURFACE (read from model.py):
#   rename_existing_index(t_pre: Place, editor: SchemaEditor,
#                         old_index: ExistingIndex, new_name: int) -> None
#     Requires: MustTerminate(3)   <-- TOTAL correctness: the step must return
#               Acc(old_index.name, 1/2)                  <-- READ-ONLY share
#               Acc(editor.rename_issued) and Acc(editor.renamed_to)
#               editor.rename_issued is False              (clean editor)
#               token(t_pre, 3) and
#                 rename_index_io(t_pre, editor, old_index.name, new_name,
#                                 t_renamed)
#                    <-- THE EFFECT BUDGET: exactly ONE licence to engage the
#                        schema primitive, naming the editor it was handed, the
#                        name its index currently carries, and the target name.
#                        Granted UNCONDITIONALLY (every admissible input), so no
#                        sub-domain is privileged by withholding the capability.
#     Ensures:  Acc(old_index.name, 1/2)
#               Acc(editor.rename_issued) and Acc(editor.renamed_to)
#       (SPENT-ONCE)  Implies(Old(old_index.name) != new_name, token(t_renamed))
#            <-- the step ends holding a token at the place the ONE licence
#                names. That place is reachable only by engaging the primitive
#                through THAT editor, about THAT index, asking for THAT target;
#                and it cannot be reached twice, because no second licence
#                exists and a step cannot mint one. So multiplicity ("exactly
#                once"), the editor, and both names are all pinned.
#       (UNSPENT)     Implies(Old(old_index.name) == new_name,
#                             token(t_pre, 3) and
#                             rename_index_io(t_pre, editor, Old(old_index.name),
#                                             new_name, t_renamed))
#            <-- the no-alteration case ends still holding the ARRIVING token,
#                at the arriving place, with its measure intact, AND the licence
#                STILL UNSPENT. An implementation that engaged the primitive
#                cannot be holding an unspent licence afterwards, whatever it
#                reports about itself. This is what makes the no-op COMPLETE.
#       (DECISION iff) editor.rename_issued == (Old(old_index.name) != new_name)
#       (target pin)   Implies(editor.rename_issued, editor.renamed_to==new_name)
#       (record kept)  Implies(not editor.rename_issued,
#                             editor.renamed_to == Old(editor.renamed_to))
#
#   issue_rename(t_pre, editor, old_index, new_name) -> None   (@ContractOnly)
#     Requires: MustTerminate(2)  (bounded callee; strictly smaller measure)
#               Acc(old_index.name, 1/2)   <-- READS the name; does not move it
#               full perm on the editor's two recorded fields AND
#               old_index.name != new_name  <-- THE load-bearing DOMAIN restriction
#               (forbids asking the backend to rename X -> X; the real backend
#                rejects renaming to a name already in use — axiom_check.py part 2)
#               token(t_pre, 2) and
#                 rename_index_io(t_pre, editor, old_index.name, new_name, t_post)
#               <-- one engagement SPENDS one licence plus the token that reaches
#                   it. So an engagement is only possible where the caller's own
#                   contract licenses that exact editor/source/target triple.
#     Ensures:  token(t_post); rename_issued is True; renamed_to == new_name
#
# WHY THE EFFECT IS CARRIED AS AN IO OPERATION AND NOT AS A VALUE (the audited
# G-EQ / G-PANEL-1 weakness for THIS surface). The repository obligation on the
# differing-names path is a COUNT: tests/migrations/test_operations.py:2924-2928
# wraps database_forwards in assertNumQueries(1 if can_rename_index else 2), i.e.
# the backend primitive must be engaged EXACTLY ONCE. A boolean "was a rename
# issued?" plus an int "what was the last target?" cannot express a count, so
# before the effect was carried this way a rival could keep the gold guard
# VERBATIM and still route the rename through an intermediate name (two
# engagements), or perform the gold rename and then round-trip the index off the
# target and back (three), or engage in a bounded loop — all with a final
# abstract state bit-for-bit identical to gold's. Those VERIFIED and did not
# resolve (P2P test_rename_index). Symmetrically, with full write permission on
# the index name a rival could manufacture the primitive's whole observable
# effect without engaging it at all, or pre-move the name to escape the callee's
# domain restriction and restore it afterwards.
#
# Both holes are closed by the same move, and it is a move about OBSERVABILITY,
# not about the guard: an engagement of the primitive is an operation, a step
# receives exactly ONE licence for it, and an engagement is the only way to
# spend that licence and reach the place the postcondition demands. Multiplicity
# is then not something an implementation can choose (a second engagement needs
# a second licence and a step cannot mint one); an unmade engagement is not
# something it can report (the token at the licensed place is obtainable only by
# making it); and the equal-names no-op is witnessed POSITIVELY by handing back
# the licence unspent, which an implementation that engaged the primitive cannot
# do. The index name is a READ-ONLY share, so it also cannot be written to
# synthesise the outcome or to dodge the callee's domain.
#
# The multiplicity/forgery cases below (weak-double-engage-reguarded,
# weak-roundtrip-intermediate, weak-oracle-echo-no-engage,
# weak-laundered-editor, weak-wrong-index, weak-engage-then-report-noop) are
# exactly those shapes.
#
# SCOPE OF THE CLAIM (why the spec pins the ASK and not the DB outcome). The
# unchanged backend primitive is capability-gated: BaseDatabaseSchemaEditor.
# rename_index either executes one _rename_index_sql (can_rename_index) or falls
# back to remove_index + add_index, and BOTH of those `return None` for an
# expression index on a backend without supports_expression_indexes — so on that
# reachable slice the real primitive emits nothing and the index keeps its old
# name. The specification therefore constrains WHETHER, HOW OFTEN and WITH WHICH
# NAMES the primitive is engaged (which is the changed function's own behaviour,
# true on every backend) and deliberately does NOT claim what the backend then
# achieves in the database (which is not). There is consequently no post-state
# claim that the index carries the target name.
#
# TOTALITY: Nagini checks partial correctness by default, so a DIVERGING impl
# (no-op on the equal-names branch, an endless loop on the differing-names
# branch) would satisfy every Ensures clause vacuously. Requires(MustTerminate(3))
# rejects any body that can fail to return — covered by the nonterm-* cases.
#
# Refinement ground truth (refinement.md / mapping.md / instance.json):
#   editor       <- schema_editor (BaseDatabaseSchemaEditor; the object through
#                   which the rename primitive is engaged)
#   old_index    <- the models.Index `old_index` computed at the join of the two
#                   branches; .name is its current DB name (str -> int by equality)
#   new_name     <- self.new_name (target name; == new_index.name)
#   issue_rename <- schema_editor.rename_index(model, old_index, new_index)
#                   (the UNCHANGED backend rename primitive; A-reference whose
#                    engagement is validated against the real callee by
#                    axiom_check.py / G-AX).
#   The gold patch adds the no-op guard `if old_index.name == self.new_name: return`
#   before `schema_editor.rename_index(...)`. The F2P test
#   test_rename_index_unnamed_index applies forward, then a backward (no-op for the
#   unnamed index, leaving the DB index at the new name), then RE-APPLIES forward
#   and asserts it does not crash and the index still has "new_pony_test_idx" — i.e.
#   the re-application must be a no-op because old_index.name already equals
#   self.new_name. Any impl that issues the rename in the equal-names case asks the
#   backend to rename X -> X and crashes -> does NOT resolve. The P2P test
#   test_rename_index asserts the differing-names path engages the primitive
#   exactly once (assertNumQueries), so an impl that engages more than once also
#   does NOT resolve.
from pathlib import Path

INSTANCE = "django__django-15695"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body of rename_existing_index (everything strictly inside
# its # impl-start / # impl-end). All region surgery replaces this single block,
# so the spec_view is untouched and same_spec is guaranteed.
_GOLD_IMPL = (
    "    # The FIX: don't alter when the current name already equals the target.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block not unique in model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return model.py with ONLY the rename_existing_index impl body replaced
    (the frozen spec — incl. issue_rename's spec — is never touched)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL — structurally-different but CORRECT (soundness).
# Reorder the guard: instead of "if equal: return; issue_rename(...)", use the
# NEGATED branch "if differs: issue_rename(...)" (and otherwise fall off the end,
# a no-op). Behaviourally identical to gold; the branch guard old_index.name !=
# new_name discharges issue_rename's Requires(old_index.name != new_name) on the
# only path that engages the primitive, and that single engagement spends the
# single licence. No proof obligation is dropped. MUST verify (else
# SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_POS_REORDER = (
    "    # Reordered guard: engage the primitive only on the differing-names\n"
    "    # branch; the equal-names branch falls through to a no-op return with\n"
    "    # the licence unspent. The branch guard establishes issue_rename's\n"
    "    # Requires(old_index.name != new_name).\n"
    "    if old_index.name != new_name:\n"
    "        issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (2) POSITIVE CONTROL — the decision hoisted into a local, then acted on. A
# correct impl may compute the discriminator first and branch on the local; the
# effect discipline must not punish that (it is the same one engagement, on the
# same branch). MUST verify (else SPEC-TOO-STRONG: the spec would be pinning an
# incidental syntactic shape of the gold body rather than its behaviour).
# ---------------------------------------------------------------------------
_POS_HOISTED = (
    "    # Hoist the decision into a local and branch on it: same behaviour,\n"
    "    # different shape (one engagement on the differing-names branch, none\n"
    "    # otherwise).\n"
    "    differs = old_index.name != new_name\n"
    "    if differs:\n"
    "        issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (3) ADMISSIBILITY — an IN-REGION positive control proving the precondition
# admits a normal, F2P-shaped input: the RE-APPLICATION case where the current
# name already equals the target (exactly what the F2P test exercises on the
# second forward apply). We build a fresh clean editor + an index already at the
# target name and Assert exactly the state conjuncts of the top-level Requires
# (rename_issued is False, the index readable at the target name) — i.e. the
# precondition is SATISFIABLE for this normal input — then run the gold decision
# inline on that input and assert the guaranteed no-op (nothing engaged, the
# editor's record untouched). NOTE: a literal self-call of rename_existing_index
# is not usable as the witness: it needs a second token/licence the step does not
# have (and a strictly smaller termination measure), which would be a false
# PRECOND-TOO-STRONG signal. The inline gold decision on the constructed input
# exercises the same equal-names no-op observable. If the constructors/Asserts
# could not establish the Requires conjuncts for this normal input ->
# PRECOND-TOO-STRONG. The real (gold) body then runs for the actual args, so the
# module still verifies. Edited strictly inside the impl region.
# ---------------------------------------------------------------------------
_ADMISS_IMPL = (
    "    # --- admissibility witness on the F2P re-apply (equal-names) input ---\n"
    "    # A fresh clean editor and an index already AT the target name 7 (the\n"
    "    # state after backward leaves the unnamed index at new_pony_test_idx).\n"
    "    e2 = SchemaEditor()\n"
    "    idx2 = ExistingIndex(7)\n"
    "    # Exactly the top-level Requires' state conjuncts, established for a\n"
    "    # normal F2P-shaped input (the precondition admits it).\n"
    "    Assert(e2.rename_issued is False)\n"
    "    Assert(idx2.name == 7)\n"
    "    # The gold decision applied inline to that input: equal names -> no-op\n"
    "    # (the guarded branch never engages the schema primitive, so it needs\n"
    "    # no licence of its own).\n"
    "    if idx2.name != 7:\n"
    "        Assert(False)\n"
    "    # The re-application is a COMPLETE no-op: nothing was engaged and the\n"
    "    # editor's rename record is untouched.\n"
    "    Assert(e2.rename_issued is False)\n"
    "    Assert(e2.renamed_to == 0)\n"
    "    Assert(idx2.name == 7)\n"
    "    # --- the real (gold) decision for the actual args ---\n"
    "    # The FIX: don't alter when the current name already equals the target.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (4) UNIQUENESS — the prepatch bug: engage the primitive UNCONDITIONALLY (drop
# the no-op guard entirely). This is exactly model_prepatch.py. In the
# equal-names case it engages with old_index.name == new_name, violating
# issue_rename's Requires(old_index.name != new_name) -> REJECT at the call site.
# expect="reject".
# ---------------------------------------------------------------------------
_WEAK_UNCONDITIONAL = (
    "    # ADVERSARY (prepatch bug): no no-op guard; always engage the backend\n"
    "    # rename primitive. When old_index.name == new_name this asks the backend\n"
    "    # to rename X -> X, which is forbidden by issue_rename's precondition.\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (5) UNIQUENESS — the RESETTABLE-WITNESS cheat. Engage UNCONDITIONALLY, then on
# the equal-names branch RESET the recorded fields so the post-state decision iff
# appears to hold. The unconditional engagement in the equal-names case violates
# issue_rename's Requires(old_index.name != new_name) -> REJECT at the call site,
# BEFORE any reset can paper it over. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_RESETTABLE = (
    "    # ADVERSARY (resettable witness): engage unconditionally, then on the\n"
    "    # equal-names branch reset the recorded flag/target so the post-state\n"
    "    # decision iff appears to hold. The unconditional engagement is\n"
    "    # forbidden when old_index.name == new_name.\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
    "    if old_index.name == new_name:\n"
    "        editor.rename_issued = False\n"
    "        editor.renamed_to = 0\n"
)

# ---------------------------------------------------------------------------
# (6) UNIQUENESS — COUNT BLINDNESS, re-guarded (the audited G-EQ atk_3 BREAKER
# family, in its sharpest form). Keep the gold guard VERBATIM, engage the
# primitive, then RE-CHECK the guard and engage AGAIN. Each engagement discharges
# the callee's domain restriction on its own, so the domain restriction cannot be
# what rejects this: only the EFFECT BUDGET can. There is one licence, and a
# second engagement needs a second one. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_DOUBLE_REGUARDED = (
    "    # ADVERSARY (count blindness): engage, re-establish the guard, engage a\n"
    "    # SECOND time. Same reported values as gold; twice the schema traffic.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
    "    if old_index.name != new_name:\n"
    "        issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (7) UNIQUENESS — ROUND TRIP THROUGH AN INTERMEDIATE NAME (the audited atk_3 /
# atk_11 shape). Reach the target by asking the primitive for some OTHER name
# first and then for the target. Every call site's domain restriction holds; the
# reported values are gold's. Two engagements, and one of them names a pair the
# step was never licensed for. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_ROUNDTRIP = (
    "    # ADVERSARY (intermediate name): ask the primitive for a different name\n"
    "    # first, then for the target. Final reported values identical to gold.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    other = new_name + 1\n"
    "    if old_index.name != other:\n"
    "        issue_rename(t_pre, editor, old_index, other)\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (8) UNIQUENESS — ORACLE ECHO, no engagement at all (the audited atk_5 / atk_6
# shape). Never engage the primitive; just write the spec's own discriminator
# into the recorded fields. The decision iff and the target pin are both
# satisfied by the report. What rejects it is that the differing-names branch
# must end holding a token at the licensed place, and that place is reachable
# ONLY by making the engagement. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_ORACLE_ECHO = (
    "    # ADVERSARY (oracle echo): never engage the primitive; write the spec's\n"
    "    # own discriminator into the recorded fields — a reported answer rather\n"
    "    # than an alteration.\n"
    "    if old_index.name != new_name:\n"
    "        editor.rename_issued = True\n"
    "        editor.renamed_to = new_name\n"
)

# ---------------------------------------------------------------------------
# (9) UNIQUENESS — LAUNDERED EDITOR. Engage the primitive honestly, but against
# a PRIVATE editor object the step procures for itself, then hand-write the
# caller's editor to the values the spec asks for. Every value clause holds and
# an engagement really happened — but not through the editor the caller supplied,
# so the real migration's schema_editor is never asked and no SQL reaches the
# caller's connection. The licence names the editor, so this is rejected.
# expect="reject".
# ---------------------------------------------------------------------------
_WEAK_LAUNDERED_EDITOR = (
    "    # ADVERSARY (laundered editor): engage a PRIVATE editor of the step's\n"
    "    # own, then hand-write the caller's editor to the expected values.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    shadow = SchemaEditor()\n"
    "    issue_rename(t_pre, shadow, old_index, new_name)\n"
    "    editor.rename_issued = True\n"
    "    editor.renamed_to = new_name\n"
)

# ---------------------------------------------------------------------------
# (10) UNIQUENESS — WRONG INDEX. Engage the primitive, through the right editor,
# asking for the right target — but ABOUT A DIFFERENT INDEX the step made up,
# never about the existing index the caller handed in. Refined, the emitted SQL
# renames an index that is not the one the migration is about. The licence names
# the source name (the name the caller's index currently carries), so this is
# rejected. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_WRONG_INDEX = (
    "    # ADVERSARY (wrong index): engage the primitive about a DIFFERENT index\n"
    "    # this step invented, not about the existing index handed in.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    other = ExistingIndex(new_name + 1)\n"
    "    issue_rename(t_pre, editor, other, new_name)\n"
)

# ---------------------------------------------------------------------------
# (11) UNIQUENESS — ENGAGE THEN REPORT NO-OP. Engage the primitive on the
# differing-names branch (spending the licence honestly), then report the
# equal-names answer. The effect happened and the report denies it: rejected by
# the decision iff, which is anchored to the pre-state name rather than to
# whatever the step chooses to say. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_ENGAGE_REPORT_NOOP = (
    "    # ADVERSARY: engage the primitive, then report the no-alteration answer.\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
    "    editor.rename_issued = False\n"
    "    editor.renamed_to = 0\n"
)

# ---------------------------------------------------------------------------
# (12) PARTIAL-DOMAIN — always-no-op: never engage the primitive and never
# report anything. Correct on the equal-names sub-domain, wrong on the rest: the
# differing-names branch must end holding a token at the licensed place (only an
# engagement gets there) and must report the rename. expect="reject".
# ---------------------------------------------------------------------------
_PARTIAL_DOMAIN = (
    "    # ADVERSARY: treat EVERY case as the no-alteration case (correct only\n"
    "    # when the names already match).\n"
    "    return\n"
)

# ---------------------------------------------------------------------------
# (13) PARTIAL-DOMAIN on an ORDER slice (the audited atk_8 / atk_12 shape).
# Decline whenever the current name does not order below the target and engage
# otherwise — an ORDER test on a carrier the mapping declares is only ever
# equality-compared. Correct on part of the differing-names domain, a silent
# no-op on the rest. expect="reject".
# ---------------------------------------------------------------------------
_PARTIAL_ORDER_SLICE = (
    "    # ADVERSARY (partial domain on an order slice): decline whenever the\n"
    "    # current name does not order below the target, engage otherwise.\n"
    "    if old_index.name >= new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (14) BOUNDARY — treat ADJACENT names as already-equal, widening the
# no-alteration case beyond the one input it holds for. A genuine rename of an
# index whose name happens to be the neighbouring identifier silently does
# nothing. expect="reject".
# ---------------------------------------------------------------------------
_BOUNDARY_ADJACENT = (
    "    # ADVERSARY (boundary): widen the no-alteration case to adjacent names.\n"
    "    if old_index.name == new_name or old_index.name + 1 == new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (15) BOUNDARY — sentinel transit (the audited atk_10 shape): decline whenever
# the target is the identifier the editor's record starts at, which the mapping
# declares can never be a real name. Correct nowhere it matters, and a silent
# no-op on a reachable input. expect="reject".
# ---------------------------------------------------------------------------
_BOUNDARY_SENTINEL = (
    "    # ADVERSARY (boundary at the record's initial sentinel value).\n"
    "    if new_name == 0:\n"
    "        return\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (16) UNIQUENESS — SWAPPED BRANCHES: engage when the names already match and
# decline when they differ. The exact inverse of the behaviour. expect="reject".
# ---------------------------------------------------------------------------
_WEAK_SWAPPED = (
    "    # ADVERSARY (swapped branches): engage when the names already match,\n"
    "    # decline when they differ.\n"
    "    if old_index.name != new_name:\n"
    "        return\n"
    "    issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (17) UNIQUENESS — PRE-REPORT ECHO: write the recorded fields from the spec's
# own discriminator BEFORE deciding, then engage only if the record says so. The
# record is no longer the trace of a decision; on the equal-names branch the
# rename target has already been moved, so the "record kept" clause fails.
# expect="reject".
# ---------------------------------------------------------------------------
_WEAK_PREREPORT = (
    "    # ADVERSARY (pre-report echo): write the recorded fields from the\n"
    "    # discriminator first, then engage only if the record says so.\n"
    "    differed = old_index.name != new_name\n"
    "    editor.renamed_to = new_name\n"
    "    editor.rename_issued = differed\n"
    "    if differed:\n"
    "        issue_rename(t_pre, editor, old_index, new_name)\n"
)

# ---------------------------------------------------------------------------
# (18) UNIQUENESS — NON-TERMINATION on the differing-names branch (the audited
# G-PANEL-1 counterexample shape): equal names -> honest early-return no-op;
# differing names -> loop forever BEFORE ever engaging the primitive. Under
# partial correctness every Ensures clause on that branch is vacuously satisfied,
# so a MustTerminate-free spec ADMITS this impl even though its faithful
# transliteration hangs the migration instead of renaming. expect="reject".
# ---------------------------------------------------------------------------
_NT_DIFFER_LOOP = (
    "    # ADVERSARY (diverging differ-branch): honest no-op when the names\n"
    "    # already match, but an endless loop instead of the rename otherwise —\n"
    "    # every postcondition on that branch holds only vacuously. (No code\n"
    "    # follows the loop: the loop itself must be what the spec rejects,\n"
    "    # not an incidental dead-code type error after it.)\n"
    "    if old_index.name == new_name:\n"
    "        return\n"
    "    while True:\n"
    "        pass\n"
)

# ---------------------------------------------------------------------------
# (19) UNIQUENESS — NON-TERMINATION via unbounded self-recursion: delegate to
# yourself forever (never reach any branch). Vacuously satisfies every Ensures
# under partial correctness. expect="reject".
# ---------------------------------------------------------------------------
_NT_SELF_RECURSION = (
    "    # ADVERSARY (bare self-recursion): never decide, never return.\n"
    "    rename_existing_index(t_pre, editor, old_index, new_name)\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER),
        "rationale": (
            "Structurally-different CORRECT impl: the guard is reframed as the "
            "negated branch `if old_index.name != new_name: issue_rename(...)` "
            "with the equal-names case falling through to a no-op return. "
            "Behaviourally identical to gold; the branch guard discharges "
            "issue_rename's Requires(old_index.name != new_name) on the only "
            "path that engages the primitive, and that one engagement spends the "
            "one licence. No proof obligation is dropped. A faithful correct "
            "impl MUST verify; if it cannot -> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-hoisted-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_HOISTED),
        "rationale": (
            "A second CORRECT shape: compute the discriminator into a local and "
            "branch on the local. Same behaviour (one engagement on the "
            "differing-names branch, none otherwise), different syntax. This "
            "guards specifically against the effect discipline being over-fitted "
            "to the gold body's syntactic form: the obligation is about WHICH "
            "engagements happen, not about how the branch is written. If this "
            "cannot verify -> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-fshaped-reapply",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": (
            "A positive control builds the exact F2P re-apply input (a fresh "
            "clean editor and an index already AT the target name), Asserts the "
            "top-level Requires' state conjuncts hold for it (rename_issued is "
            "False, the index readable at the target name — the precondition "
            "admits this normal input), runs the gold decision inline on it, and "
            "asserts the guaranteed no-op (nothing engaged, the editor's record "
            "untouched). A literal self-call is deliberately NOT the witness: it "
            "would need a second token and licence the step does not hold, "
            "fabricating a PRECOND-TOO-STRONG signal. If the witness cannot be "
            "established -> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "weak-unconditional-rename",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_UNCONDITIONAL),
        "refinement": (
            "This IS the prepatch behaviour (model_prepatch.py): dropping the "
            "no-op guard so database_forwards calls schema_editor.rename_index "
            "unconditionally. The F2P test test_rename_index_unnamed_index "
            "re-applies the forward step when the unnamed index is already at "
            "new_pony_test_idx, so the unconditional call asks the backend to "
            "rename the index to a name already in use (X -> X) and the operation "
            "fails (on PostgreSQL: relation already exists). The faithful real "
            "patch therefore does NOT resolve the F2P."
        ),
        "rationale": (
            "UNIQUENESS: engaging the primitive in the equal-names case violates "
            "issue_rename's Requires(old_index.name != new_name) -> REJECT at "
            "the call site. If it verified, the spec would admit the prepatch "
            "bug => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-resettable-witness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_RESETTABLE),
        "refinement": (
            "Engage the backend rename unconditionally, then in the equal-names "
            "branch reset the recorded fields so the post-state appears like a "
            "no-op. Its faithful real refinement is STILL 'call "
            "schema_editor.rename_index unconditionally' — the backend rename to "
            "X -> X has already been issued before the reset, so the operation "
            "crashes exactly as the prepatch bug; resetting a Python flag "
            "afterwards cannot un-issue the SQL. The F2P does NOT resolve."
        ),
        "rationale": (
            "UNIQUENESS (resettable witness): the unconditional engagement in "
            "the equal-names case is REJECTED at the call site by "
            "issue_rename's domain restriction, before any reset. The rejection "
            "comes from the primitive's domain, not from a resettable post-state "
            "flag. If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-double-engage-reguarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_DOUBLE_REGUARDED),
        "refinement": (
            "This is the audited G-EQ atk_3 BREAKER family in its sharpest form. "
            "Its faithful transliteration keeps the gold guard verbatim and calls "
            "schema_editor.rename_index TWICE on the differing-names path. The "
            "F2P passes (the guard is intact), but P2P test_rename_index wraps "
            "database_forwards in assertNumQueries(1 if "
            "connection.features.can_rename_index else 2) — twice the engagements "
            "means twice the statements, and the count assertion FAILS. Executed "
            "on the pre-repair spec: resolved=FALSE, FAIL_TO_PASS 1/1 pass, "
            "PASS_TO_PASS failure=['test_rename_index']."
        ),
        "rationale": (
            "UNIQUENESS (invocation MULTIPLICITY — the load-bearing hole this "
            "battery exists to keep closed). Each engagement re-establishes "
            "issue_rename's Requires(old_index.name != new_name) on its own, so "
            "the callee's domain restriction canNOT be what rejects this; only "
            "the EFFECT BUDGET can. The step holds exactly ONE licence for an "
            "engagement, an engagement spends it, and a step cannot mint another "
            "— so the second engagement has no licence and is REJECTED. This is "
            "the sharpest test that the spec pins HOW OFTEN the primitive is "
            "engaged and not merely the final reported values, which are "
            "bit-for-bit gold's here. If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-roundtrip-intermediate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ROUNDTRIP),
        "refinement": (
            "The audited atk_3/atk_11 shape: reach the target name by asking the "
            "backend for some OTHER name first and then for the target. Refined, "
            "that emits two renames instead of one and moves the live DB index "
            "through a name the migration never mentions, so P2P "
            "test_rename_index's assertNumQueries FAILS (resolved=FALSE, "
            "PASS_TO_PASS failure=['test_rename_index'])."
        ),
        "rationale": (
            "UNIQUENESS (multiplicity + which names are asked for): both call "
            "sites satisfy the callee's domain restriction and the final reported "
            "values are gold's, so nothing about the VALUES can reject this. The "
            "single licence names one editor/source/target triple; the "
            "intermediate engagement asks about a pair the step was never "
            "licensed for, and the second engagement has no licence left. If it "
            "verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-oracle-echo-no-engage",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ORACLE_ECHO),
        "refinement": (
            "The audited atk_5/atk_6 shape: never call schema_editor.rename_index "
            "at all; just report that a rename happened. Refined, the actual "
            "database index is never renamed, so the F2P and the P2P rename tests "
            "that assert the target index name exists FAIL (resolved=FALSE, "
            "FAIL_TO_PASS failure=['test_rename_index_unnamed_index'])."
        ),
        "rationale": (
            "UNIQUENESS (ungrounded-oracle echo): the recorded fields are "
            "assigned the spec's own discriminator, so the decision iff and the "
            "target pin are free to satisfy — this is the sharpest test that the "
            "spec pins the OCCURRENCE of the alteration and not a self-reported "
            "boolean. The differing-names branch must end holding a token at the "
            "place the licence names, and that place is reachable ONLY by making "
            "the engagement; a report cannot get there. If it verified => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-laundered-editor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_LAUNDERED_EDITOR),
        "refinement": (
            "Refined: construct a private schema editor (a second "
            "connection.schema_editor()) and call rename_index on THAT, while "
            "reporting success on the one the migration executor handed in. The "
            "caller's editor — the one inside the test's "
            "`with connection.schema_editor() as editor` block, whose statements "
            "assertNumQueries counts — is never asked, so the counted query never "
            "happens and the rename does not reach the migration's own "
            "transaction. P2P test_rename_index FAILS."
        ),
        "rationale": (
            "UNIQUENESS (right effect, wrong object): an engagement really "
            "happens and every value clause is satisfied, so neither the "
            "decision iff nor the target pin can reject this. The licence names "
            "the EDITOR the step was handed; an engagement of any other editor "
            "is unlicensed. If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-wrong-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_WRONG_INDEX),
        "refinement": (
            "Refined: call schema_editor.rename_index with a fabricated "
            "models.Index as the old_index rather than the one resolved at the "
            "join point. The emitted SQL renames an index that is not the one the "
            "migration is about (and whose name may not exist on the table at "
            "all), so the rename tests asserting the old name is gone and the new "
            "one present FAIL."
        ),
        "rationale": (
            "UNIQUENESS (right effect, wrong subject): the engagement happens, "
            "through the right editor, asking for the right target, and every "
            "value clause holds. The licence names the SOURCE name — the name the "
            "caller's own index currently carries — so an engagement about any "
            "other index is unlicensed. If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-engage-then-report-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ENGAGE_REPORT_NOOP),
        "refinement": (
            "Refined: call rename_index on the differing-names path and then "
            "report that no rename happened. The SQL has already been emitted, so "
            "a caller that trusts the report (and the count assertions that go "
            "with it) is told the opposite of what the schema did."
        ),
        "rationale": (
            "UNIQUENESS: the effect is honest but the report denies it. The "
            "decision iff is anchored to the PRE-STATE name "
            "(Old(old_index.name) != new_name), not to whatever the step chooses "
            "to say afterwards, so the false report is REJECTED. If it verified "
            "=> SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-always-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_DOMAIN),
        "refinement": (
            "A patch that ALWAYS returns early (never calls "
            "schema_editor.rename_index) is correct only when the names already "
            "match; on the differing-names sub-domain it never performs the "
            "rename the migration exists to perform. The forward RenameIndex on a "
            "real name change would leave the DB index under its old name, so the "
            "P2P/F2P rename tests asserting the target index name exists FAIL."
        ),
        "rationale": (
            "PARTIAL-DOMAIN: correct on the equal-names sub-domain, wrong on the "
            "rest. On the differing-names sub-domain the step must end holding a "
            "token at the licensed place — reachable only by engaging the "
            "primitive — and must report the rename; this impl does neither. If "
            "it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-order-slice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_ORDER_SLICE),
        "refinement": (
            "The audited atk_8/atk_12 shape: engage the backend only on the "
            "sub-domain where the current name orders below the target and "
            "silently do nothing on the rest — an ORDER test on index names, "
            "which the mapping declares are only ever equality-compared. Refined, "
            "roughly half of all real renames become silent no-ops, so the rename "
            "tests FAIL."
        ),
        "rationale": (
            "PARTIAL-DOMAIN on a value slice: correct where it engages, a silent "
            "no-op elsewhere in the precondition's domain. The differing-names "
            "postconditions hold for EVERY admissible input, so the declining "
            "slice is REJECTED. If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "boundary-adjacent-treated-equal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_BOUNDARY_ADJACENT),
        "refinement": (
            "Refined: widen the guard from `old_index.name == self.new_name` to "
            "also skip when the two names are 'nearly' the same. A genuine rename "
            "between two such names becomes a silent no-op, so the DB index keeps "
            "its old name and the rename tests FAIL."
        ),
        "rationale": (
            "BOUNDARY: the no-alteration case holds for exactly one relation "
            "between the two names — equality. Widening it leaves a reachable "
            "differing-names input on which nothing is engaged, which the "
            "differing-names postconditions REJECT. If it verified => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "boundary-sentinel-transit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_BOUNDARY_SENTINEL),
        "refinement": (
            "The audited atk_10 shape: special-case the identifier the editor's "
            "rename record starts at (which the mapping declares can never be a "
            "real index name) and decline to engage there. Refined, a legal "
            "rename is silently skipped, so the rename tests FAIL."
        ),
        "rationale": (
            "BOUNDARY: a sub-domain carved out by a value the specification never "
            "privileges. The differing-names obligations apply to every "
            "admissible input, so the carve-out is REJECTED. If it verified => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-swapped-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_SWAPPED),
        "refinement": (
            "Refined: engage the backend exactly when the names already match "
            "and skip when they differ — the inverse of the behaviour. The F2P "
            "re-apply asks the backend to rename X -> X and crashes, and real "
            "renames never happen. Resolves nothing."
        ),
        "rationale": (
            "UNIQUENESS: the equal-names branch engages the primitive, violating "
            "its domain restriction, and the differing-names branch never reaches "
            "the licensed place. Rejected on both. If it verified => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-prereport-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_PREREPORT),
        "refinement": (
            "Refined: set the observable record from the discriminator before "
            "deciding, then call rename_index only if the record says so. On the "
            "equal-names path the recorded rename target has already been moved "
            "to the new name although nothing was asked of the backend, so a "
            "caller reading that record is misinformed about a no-op step."
        ),
        "rationale": (
            "UNIQUENESS (ungrounded echo, report side): the record is no longer "
            "the trace of a decision. The 'record kept' clause "
            "Implies(not editor.rename_issued, editor.renamed_to == "
            "Old(editor.renamed_to)) REJECTS it on the equal-names branch: a "
            "COMPLETE no-op leaves that record exactly as it found it. If it "
            "verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "nonterm-differ-branch-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NT_DIFFER_LOOP),
        "refinement": (
            "The faithful transliteration keeps the equal-names early return but "
            "replaces the rename call with an infinite loop in "
            "RenameIndex.database_forwards: any forward rename to a genuinely new "
            "name HANGS the migration instead of renaming, so the P2P rename "
            "tests (and any F2P run reaching a real rename) never complete — it "
            "does not resolve. This is exactly the audited G-PANEL-1 "
            "counterexample shape."
        ),
        "rationale": (
            "NON-TERMINATION: under partial correctness the differ-branch "
            "postconditions are vacuously satisfied (the exit is unreachable), "
            "so without a termination obligation this VERIFIED (the G-PANEL-1 "
            "finding). Requires(MustTerminate(3)) rejects the unbounded "
            "`while True` ('Loop might not take all unsatisfied obligations'). "
            "If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "nonterm-self-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NT_SELF_RECURSION),
        "refinement": (
            "A database_forwards that re-enters itself forever never returns "
            "control to the migration executor: applying RenameIndex hangs on "
            "every input, so no rename test completes — it does not resolve."
        ),
        "rationale": (
            "NON-TERMINATION: bare self-recursion discharges every Ensures "
            "vacuously under partial correctness. The self-call is rejected — it "
            "has neither a strictly smaller termination measure nor the token and "
            "licence a fresh step requires (the step's own were consumed by its "
            "obligations). If it verified => SPEC-TOO-WEAK."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — issue_rename is the A-reference for the UNCHANGED backend rename
# primitive BaseDatabaseSchemaEditor.rename_index(model, old_index, new_index).
# The model pins its ENGAGEMENT (that it was asked, through which editor, about
# which index, for which target) and deliberately not what the backend achieves
# in the database, because rename_index is capability-gated: it either executes
# one _rename_index_sql or falls back to remove_index + add_index, and both of
# those return None for an expression index on a backend without
# supports_expression_indexes. The plan (§4) checks an A-reference the same way
# as an axiom: it must agree with the real callee on every caller-reachable
# input, AND its domain restriction Requires(old_index.name != new_name) must be
# sound for the caller.
#
#   ax-sound-rename (axiom-soundness): drive the REAL Django rename_index on
#   in-memory sqlite over a sequence of distinct (old -> new) names and assert it
#   engages the backend to move the index from old_index.name to new_index.name.
#   Also confirm the rename-to-itself hazard: creating an index under a name
#   already in use RAISES — which is exactly why issue_rename's
#   Requires(old_index.name != new_name) is sound (the caller must never engage
#   the primitive in the equal-names case). This embeds the proven axiom_check.py
#   logic (read on the HOST at load time; the runner mounts only the probe).
#
# CALLER-DOMAIN CONTAINMENT (axiom-containment): the only call site of
# issue_rename is rename_existing_index, and it is guarded by `if old_index.name
# == new_name: return` BEFORE the call, so the only caller-reachable input to
# issue_rename has old_index.name != new_name -- exactly issue_rename's Requires
# domain. There is no caller-reachable input OUTSIDE the domain, so there is no
# AXIOM-TOO-WEAK-FOR-CALLER risk. Covering only the differing-names case is
# SOUND (the equal-names case is the guarded no-op). This is argued statically
# from the model's control flow (the guard is the verified gold impl), so it
# needs no separate Docker probe; the soundness probe below also confirms the
# equal-names call would be illegal (part 2), corroborating the containment
# argument.
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

AXIOM_TESTS = [
    {
        "id": "ax-sound-rename",
        "axiom": "issue_rename",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": (
            "Validates the issue_rename A-reference against the REAL "
            "BaseDatabaseSchemaEditor.rename_index on in-memory sqlite: (1) "
            "engaging it with a differing target really asks the backend to move "
            "the index from old_index.name to new_index.name (the engagement the "
            "model records, with renamed_to == new_name), over a chain of "
            "distinct renames; (2) the rename-to-itself hazard — creating an "
            "index under an already-present name RAISES — confirming "
            "issue_rename's Requires(old_index.name != new_name) is sound "
            "(engaging the primitive in the equal-names case is forbidden). Exit "
            "0 iff every obligation holds; any violation => AXIOM-UNSOUND. This "
            "embeds the proven axiom_check.py / G-AX logic."
        ),
    },
]
