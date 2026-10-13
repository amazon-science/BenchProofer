# properties.py — PBT falsification battery for django__django-15499. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py)
# ---------------------------------------------------------------------------
#   reduce_create(model: CreateModel, op_kind: int, op_name: int,
#                 op_options: int, op_managers: int) -> Optional[CreateModel]
#     Requires(Acc(model.name,       1 / 2))   # READ-ONLY (fractional) — all 6 facets
#     Requires(Acc(model.name_lower, 1 / 2))   # READ-ONLY
#     Requires(Acc(model.fields,     1 / 2))   # READ-ONLY
#     Requires(Acc(model.options,    1 / 2))   # READ-ONLY
#     Requires(Acc(model.bases,      1 / 2))   # READ-ONLY
#     Requires(Acc(model.managers,   1 / 2))   # READ-ONLY
#     Requires(op_kind in {OPTIONS=0, MANAGERS=1})   # DOMAIN: only the two modeled kinds
#     Ensures(Acc(model.{name,name_lower,fields,options,bases,managers}, 1 / 2))
#     # (IFF-1) Result is not None  =>  op_name == model.name_lower
#     # (IFF-2) op_name == model.name_lower  =>  Result is not None
#     # (NAME)   Result != None => Result.name       == model.name        (DISPLAY name, case preserved)
#     # (NAMELO) Result != None => Result.name_lower == model.name_lower  (derived key preserved)
#     # (FIELDS) Result != None => Result.fields     == model.fields      (ALWAYS from creation step)
#     # (BASES)  Result != None => Result.bases      == model.bases       (ALWAYS from creation step)
#     # (OPT-FOLD) Result != None and OPTIONS  => Result.options == op_options  and Result.managers == model.managers
#     # (MGR-FOLD) Result != None and MANAGERS => Result.managers == op_managers and Result.options  == model.options
#
# Fold truth table the iff pins (op_kind, op_name==model.name_lower) -> Result:
#   OPTIONS,  same  -> non-null, carries op_options, managers from model
#   MANAGERS, same  -> non-null, carries op_managers, options from model   <-- the F2P fix
#   OPTIONS,  diff  -> None
#   MANAGERS, diff  -> None
# Any other follow-up step kind is OUT OF DOMAIN (precondition): each such kind
# has its own reduction rule elsewhere in the optimiser and the model states
# nothing about it (the previous in-domain catch-all tag wrongly asserted
# "never folds" for kinds whose own rules DO fold — a faithfulness drift).
#
# Load-bearing clauses:
#   * (MGR-FOLD) Result.managers == op_managers — the NEWLY-ADDED behaviour
#     (gold hunk: managers=operation.managers). model_prepatch.py omits the
#     MANAGERS branch entirely (returns None), failing (IFF-2); G-DIFF.
#   * (NAME) Result.name == model.name — the folded step keeps the creation
#     step's case-preserved DISPLAY name (gold hunk: `self.name`), NOT the
#     lower-cased comparison key (op_name / operation.name_lower) used only in
#     the guard. A P1 auditor previously built exactly this wrong-but-admitted
#     impl (fold with `operation.name_lower` as the new name): with the model
#     name 'Foo' the folded op is named 'foo', deconstruct/state rebuild break,
#     hidden tests fail. This clause (with name and name_lower as DISTINCT
#     tokens) now rejects it.
#   * (MGR-FOLD) Result.options == model.options — the manager fold keeps the
#     CREATION step's options (the alter step does not touch options).
#   * (OPT-FOLD) Result.managers == model.managers — the SYMMETRIC pre-existing
#     branch keeps the creation step's managers (the alter step does not touch
#     managers).
#   * (FIELDS)/(BASES) — both folds carry fields/bases unchanged from the
#     creation step; no slot may take an alter-step token.
#   * (IFF-1)/(IFF-2) — folding happens EXACTLY for a same-keyed alter of an
#     in-domain kind; a key mismatch must NOT fold.
#   * The whole `model` is held at Acc(...,1/2) (READ-ONLY): any impl that WRITES
#     a model facet fails for INSUFFICIENT PERMISSION (frame-mutation, MANDATORY).
#
# Ungrounded-oracle note (directive 2): there is NO @Pure answer-key / opaque
# oracle in this spec. Every postcondition slot is pinned to a concrete argument
# token (op_options, op_managers) or an input facet (model.name/name_lower/
# fields/options/bases/managers) — fully grounded in the args. There is no wrong
# echo to build: the cheapest impl that satisfies the contract must select the
# correct token for each slot, which is precisely the gold fold. We instead
# supply honest positive controls (a structurally-different correct impl) plus
# partial-domain rivals that mis-select a single slot/branch.
#
# Axiom lane: meta.json axioms=[]; no @ContractOnly axiom, no A-reference deep
# model (the fold calls no library callee it does not change — it is pure
# structural token selection, modelled deeply). G-AX is 'vacuous';
# axiom_check.py validates the structural reduction against the REAL
# CreateModel.reduce, not an axiom's over-approximation. AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "django__django-15499"
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
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# ---------------------------------------------------------------------------
# TERMINATION (the spec now demands it). model.py carries
# Requires(MustTerminate(6)) on reduce_create and Requires(MustTerminate(1)) on
# CreateModel.__init__, so the spec proves TOTAL correctness: an impl that never
# reaches the return no longer satisfies the Ensures vacuously.
#
# Neither method owns a loop, so there is no loop measure here; the obligation's
# entire content is the LEVEL ORDER. Nagini requires a caller's level to be
# STRICTLY GREATER than its callee's, which has one consequence that reshapes
# this battery: a SELF-call reproduces its own method's level, so a self-call at
# a constant level can NEVER take the obligation from itself. Measured on this
# bundle, all three directions:
#   * unguarded self-call at level 6 -> 6: "Obligation leak check failed.
#     Callee reduce_create might not take all unsatisfied obligations from the
#     caller."
#   * the SAME leak for a self-call GUARDED to bottom out after one level
#     (guard `op_options != 99`, inner call passing op_options=99, so the
#     recursion is only two frames deep and genuinely terminates) — levels are
#     per-method, so descending the ARGUMENTS does not descend the LEVEL. The
#     guard was verified feasible, not dead: `Assert(False)` in that same
#     branch is REJECTED ("Assertion False might not hold").
#   * a call from a helper at level 7 -> 6 VERIFIES.
# So the admissibility probe below drives the call from `_admiss_caller` (level
# 7, an impl-region helper the spec view elides) rather than from a self-call.
# The probed property is unchanged and still exercised by a REAL call on the
# F2P-shaped input; only the CALL SITE moved to a direction the level order
# permits. The old self-call form is retained as a reject-lane rival, since it
# is a genuinely diverging impl.
# ---------------------------------------------------------------------------

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). These keep the gold token-selection but
# reshape the control flow; no loop / no fold, so no auto-undischargeable lemma
# is introduced (pilot pitfalls #2/#3 avoided).
# ===========================================================================

# pos-control-reorder: handle the MANAGERS branch FIRST, then the OPTIONS branch,
# then fall through to None. Behaviourally identical to the gold on every
# (op_kind, op_name) combination (the two same-key branches are mutually
# exclusive on op_kind, so order is irrelevant); a pure branch-reorder.
_POS_REORDER = """    # impl-start
    if op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    return None
    # impl-end"""

# pos-control-name-first: hoist the shared key-equality test to an outer guard,
# then dispatch on op_kind inside. Same decision table; a nesting reshape that
# keeps every live constructor slot identical to the gold. The read-only model is
# never written.
_POS_NAME_FIRST = """    # impl-start
    if op_name == model.name_lower:
        if op_kind == KIND_ALTER_OPTIONS:
            return CreateModel(model.name, model.name_lower, model.fields,
                               op_options, model.bases, model.managers)
        if op_kind == KIND_ALTER_MANAGERS:
            return CreateModel(model.name, model.name_lower, model.fields,
                               model.options, model.bases, op_managers)
    return None
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). A new module-level def OUTSIDE the impl region
# would change the spec view and break same_spec, so the witness is injected
# INSIDE the impl region (which the spec view elides — verified: the helper name
# does not appear in markers.spec_view of this variant). We construct a concrete
# F2P-shaped CreateModel (display-name token 7 = "Foo", lower-key token 0 =
# "foo" — DISTINCT, as for any mixed-case model name) and make a REAL CALL of
# reduce_create on a same-keyed MANAGERS alter — exactly the F2P scenario
# CreateModel("Foo", fields=[]) + AlterModelManagers("Foo", managers=[...]). The
# constructor Ensures give full Acc on each facet, so 1/2 is establishable for
# the call's Requires; the call's Ensures hands the 1/2 back, and we assert the
# fold actually fired (non-null, managers carried, DISPLAY name kept).
#
# The call is driven from `_admiss_caller` at MustTerminate(7) rather than from a
# SELF-call inside reduce_create, because the termination obligation orders
# callers STRICTLY above callees and a self-call reproduces its own level 6 (see
# the TERMINATION note above: measured, 7 -> 6 verifies, 6 -> 6 leaks, and so
# does a self-call guarded to terminate after one level). The probed property is
# unchanged — the same seven fold clauses are asserted about the result of a real
# in-domain call — and it is NOT vacuous: an `Assert(False)` added beside those
# asserts is REJECTED, so the helper body is genuinely reachable.
_ADMISS = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None


def _admiss_caller() -> None:
    # --- admissibility witness for the F2P-shaped input (elided from spec view) ---
    # Level 7 sits STRICTLY ABOVE reduce_create's 6, which is what lets this call
    # discharge reduce_create's obligation instead of leaking it.
    Requires(MustTerminate(7))
    adm = CreateModel(7, 0, 10, 20, 30, 40)   # the "Foo" creation step: display 7, lower key 0
    # reduce_create's Requires on `adm` is establishable (1/2 of the constructor's
    # full Acc) and op_kind is in-domain; a same-keyed MANAGERS alter is admitted:
    folded = reduce_create(adm, KIND_ALTER_MANAGERS, 0, 99, 41)  # type: Optional[CreateModel]
    Assert(folded is not None)                 # (IFF-2): a same-keyed manager alter MUST fold
    Assert(folded.managers == 41)              # (MGR-FOLD): carries the alter step's managers
    Assert(folded.options == 20)               # (MGR-FOLD): keeps the creation step's options
    Assert(folded.fields == 10)                # (FIELDS): fields unchanged
    Assert(folded.bases == 30)                 # (BASES): bases unchanged
    Assert(folded.name == 7)                   # (NAME): DISPLAY name kept, NOT the lower key
    Assert(folded.name_lower == 0)             # (NAMELO): derived key preserved
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness, MANDATORY) — the whole `model` is held at
# Acc(model.X, 1/2): READ-ONLY. A rival that WRITES a model facet (here, the
# manager collection) to satisfy the postcondition vacuously MUST be rejected for
# INSUFFICIENT PERMISSION. We keep the gold token-selection verbatim and add ONE
# write to a read-only facet, so the rejection is attributable solely to the
# write, not to a value change.
# ===========================================================================

# frame-mutate-managers: before folding, overwrite model.managers (held at 1/2).
# A patch that mutated self.managers in CreateModel.reduce would corrupt the
# creation step's own manager facet (shared with later optimiser passes) — the
# reduce method is a pure read-only fold and never assigns to self's facets.
_FRAME_MUTATE_MGRS = """    # impl-start
    # Adversary: write the read-only manager facet (held at Acc(...,1/2)).
    model.managers = op_managers
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# frame-mutate-options: the symmetric write to the read-only option facet.
_FRAME_MUTATE_OPTS = """    # impl-start
    # Adversary: write the read-only option facet (held at Acc(...,1/2)).
    model.options = op_options
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN — rivals that share the spec exactly and change
# ONLY the impl. Each MUST be rejected; a verifying rival is a true
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-prepatch-no-manager-fold: the PRE-PATCH skeleton (model_prepatch.py). The
# MANAGERS branch is ABSENT, so a same-keyed manager alter falls through to None.
# This is exactly the missing gold hunk.
_UNIQ_PREPATCH = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    return None
    # impl-end"""

# uniq-fold-installs-lower-name: THE AUDITOR'S P1 BREAK, now defended. Both
# branches fold correctly slot-for-slot EXCEPT the folded step's name slot takes
# the lower-cased comparison key (op_name == operation.name_lower) instead of
# the creation step's case-preserved display name (model.name == self.name). A
# patch with `CreateModel(operation.name_lower, ...)` renames every folded model
# to its all-lowercase key ('Foo' -> 'foo'); the optimiser output then carries a
# wrong model name, breaking deconstruction/state rebuilding — the hidden F2P
# test_create_alter_model_managers fails on the name mismatch. It verified
# against the OLD one-token spec (name and key were conflated); it must now be
# rejected.
_UNIQ_LOWER_NAME = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(op_name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(op_name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# uniq-mgr-carries-model-managers: the MANAGERS branch fires but carries the
# CREATION step's managers (model.managers) instead of the alter step's
# (op_managers). This is the "fold but forget to install the new managers" bug —
# the optimiser would collapse the pair but LOSE the AlterModelManagers effect.
_UNIQ_MGR_OLD_MANAGERS = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, model.managers)
    return None
    # impl-end"""

# uniq-mgr-clobbers-options: the MANAGERS branch installs op_managers correctly
# but ALSO replaces the option facet with the alter step's op_options instead of
# keeping the creation step's model.options. The AlterModelManagers operation
# carries NO options, so a patch that wrote options=operation.options would
# install garbage/None options.
_UNIQ_MGR_CLOBBER_OPTS = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, op_managers)
    return None
    # impl-end"""

# uniq-opt-carries-alter-managers: the OPTIONS branch installs op_options
# correctly but ALSO replaces the manager facet with op_managers instead of
# keeping model.managers. The AlterModelOptions operation carries NO managers, so
# this is the symmetric clobber on the pre-existing branch.
_UNIQ_OPT_CLOBBER_MGRS = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, op_managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# uniq-ignore-name: fold on op_kind ALONE, dropping the op_name ==
# model.name_lower guard. A patch that omitted the `self.name_lower ==
# operation.name_lower` check would fold a CreateModel with an alter step naming
# a DIFFERENT model — merging two unrelated models' facets, corrupting the
# migration graph.
_UNIQ_IGNORE_NAME = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# uniq-mgr-clobbers-fields: the MANAGERS branch installs op_managers correctly
# but puts the alter step's token into the FIELDS slot (fields=op_managers)
# instead of keeping model.fields. A patch that wired fields=operation.managers
# would destroy the creation step's field list. Rejected by (FIELDS).
_UNIQ_MGR_CLOBBER_FIELDS = """    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, op_managers,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# uniq-diverging-self-call: DIVERGENCE — the unguarded self-call. This is the
# impl region the admissibility case used to carry, moved here because it does
# NOT terminate: the self-call is the first statement of reduce_create's body and
# there is no guard, and it passes the SAME arguments (adm, KIND_ALTER_MANAGERS,
# 0, 99, 41) on every frame, so reduce_create re-enters itself forever and
# reaches no return for ANY input. Established by EXECUTION, not inspection: a
# faithful control-flow simulation of this exact region (contracts are runtime
# no-ops, so only control flow matters) raises RecursionError at depth 501 for
# the in-domain input (MANAGERS, same key) — it returns for no input at all.
#
# It belongs in the reject lane because the OLD, termination-silent spec ACCEPTED
# it: with the MustTerminate lines stripped from the preconditions this very
# source verifies ("Verification successful", measured) — exactly the
# partial-correctness hole the obligation closes, every Ensures holding vacuously
# of a run that never reaches the return. With the obligation present Nagini
# rejects it: "Obligation leak check failed. Callee reduce_create might not take
# all unsatisfied obligations from the caller." The rejection source is
# Requires(MustTerminate(6)) ALONE, not any value pin: the values this impl would
# return, if it ever returned, are gold's.
_UNIQ_DIVERGE = """    # impl-start
    # Adversary: unguarded self-call at the same obligation level — never returns.
    adm = CreateModel(7, 0, 10, 20, 30, 40)
    folded = reduce_create(adm, KIND_ALTER_MANAGERS, 0, 99, 41)  # type: Optional[CreateModel]
    Assert(folded is not None)
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end"""

# uniq-skip-all: never fold (always return None). Correct only when no same-keyed
# OPTIONS/MANAGERS alter is present; wrong on every fold case. Supporting
# near-miss for (IFF-2): a patch that removed BOTH fold branches resolves nothing.
_UNIQ_SKIP_ALL = """    # impl-start
    return None
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "structurally-different CORRECT impl: handle the MANAGERS fold "
                     "branch FIRST, then the OPTIONS branch, then None. The two same-key "
                     "branches are mutually exclusive on op_kind, so reordering changes "
                     "nothing; every constructor slot is identical to the gold. No loop / "
                     "no fold => no auto-undischargeable lemma (pilot #2/#3). If a "
                     "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-name-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_NAME_FIRST),
        "rationale": "branch-reshape: hoist the shared op_name == model.name_lower test "
                     "to an outer guard, then dispatch on op_kind in a nested if. Every "
                     "live constructor slot is identical to the gold (model.options kept, "
                     "op_managers carried in the MANAGERS arm; op_options carried, "
                     "model.managers kept in the OPTIONS arm; display name + lower key "
                     "both preserved). Same decision table on all inputs; a nesting "
                     "reshape, not a loop-direction flip. Must verify (else "
                     "SPEC-TOO-STRONG).",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        # Id retained verbatim although the probe is no longer a SELF-call: the
        # lean and velvet ports cross-reference this exact id (their
        # properties.py port notes and meta.json `nagini_case` fields), so
        # renaming it would silently break that traceability. What changed is the
        # call SITE (now _admiss_caller at level 7), not the question asked.
        "id": "admiss-f2p-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) constructs a concrete "
                     "F2P-shaped CreateModel(7,0,10,20,30,40) (the 'Foo' creation step: "
                     "display-name token 7, lower-key token 0 — distinct, as for any "
                     "mixed-case model name) and makes a REAL CALL, from the level-7 "
                     "in-region helper _admiss_caller (a self-call cannot discharge "
                     "reduce_create's own level-6 obligation; see the TERMINATION note), "
                     "reduce_create(adm, KIND_ALTER_MANAGERS, 0, 99, 41) — exactly the "
                     "F2P scenario CreateModel('Foo',fields=[]) + AlterModelManagers("
                     "'Foo', managers=[...]). The constructor's full Acc supplies the 1/2 "
                     "the call's Requires needs and op_kind is in-domain, so the "
                     "precondition is establishable; the call's Ensures let us assert the "
                     "fold fired (non-null, managers==41 carried, options==20 kept, "
                     "display name 7 kept — NOT the lower key 0). If the precondition "
                     "could not be established for this legitimate input the call site "
                     "fails => PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (must reject for insufficient permission) ----
    {
        "id": "frame-mutate-managers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUTATE_MGRS),
        "refinement": "writing model.managers corresponds to a patch that MUTATES "
                      "self.managers inside CreateModel.reduce. reduce is a pure "
                      "read-only fold: it inspects self's facets and constructs a NEW "
                      "CreateModel; it never assigns to self. The CreateModel `self` is a "
                      "live operation object shared with the rest of the optimiser pass "
                      "(it may be left un-collapsed and reused by later reduce calls). A "
                      "patch that wrote self.managers would corrupt that shared operation "
                      "and is not the gold edit; it does not resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: model.managers is held at "
                     "Acc(model.managers, 1/2) (read-only). An assignment requires full "
                     "permission; only 1/2 is held, so the write fails for insufficient "
                     "permission BEFORE any value reasoning. The gold token-selection is "
                     "kept verbatim, so the rejection is attributable solely to the "
                     "read-only write.",
    },
    {
        "id": "frame-mutate-options",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUTATE_OPTS),
        "refinement": "the symmetric frame-mutation: writing model.options corresponds "
                      "to a patch that mutated self.options inside CreateModel.reduce — "
                      "again corrupting the shared creation-step operation object that "
                      "later optimiser passes reuse. reduce never assigns to self; such a "
                      "patch is not the gold edit and does not resolve. Supporting "
                      "frame-mutation variant.",
        "rationale": "rejected by the PERMISSION SYSTEM: any assignment to model.options "
                     "needs full Acc; only Acc(model.options, 1/2) is held, so it fails "
                     "for insufficient permission before any value reasoning.",
    },

    # ---- uniqueness / partial-domain (must reject) ----
    {
        "id": "uniq-prepatch-no-manager-fold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PREPATCH),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces and "
                      "G-DIFF flags (meta.json prepatch_models): the MANAGERS branch is "
                      "absent, so a same-named AlterModelManagers falls through to the "
                      "unmodelled remainder (None = not folded). The F2P "
                      "test_create_alter_model_managers builds CreateModel('Foo',fields=[]) "
                      "+ AlterModelManagers('Foo', managers=[('objects',...),"
                      "('things',...)]) and asserts it optimises to a SINGLE CreateModel "
                      "carrying those managers; without the branch the pair is left "
                      "un-collapsed (two operations) and the assertOptimizesTo fails. This "
                      "is exactly the missing gold hunk; it does NOT resolve.",
        "rationale": "rejected by (IFF-2): op_name == model.name_lower => Result is not "
                     "None. On (MANAGERS, same key) the spec demands a non-null fold but "
                     "the rival returns None.",
    },
    {
        "id": "uniq-fold-installs-lower-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_LOWER_NAME),
        "refinement": "THE PREVIOUSLY-ADMITTED P1 BREAK (G-EQ atk_1): a patch whose "
                      "added AlterModelManagers branch (and/or the AlterModelOptions "
                      "branch) constructs `CreateModel(operation.name_lower, ...)` "
                      "instead of `CreateModel(self.name, ...)`. It folds the pair and "
                      "installs the right managers, but RENAMES the folded model to the "
                      "all-lowercase comparison key ('Foo' -> 'foo'). The F2P "
                      "test_create_alter_model_managers asserts the optimised result "
                      "equals CreateModel('Foo', fields=[], managers=[...]); the folded "
                      "op is named 'foo', the deep-equality assertion fails, the patch "
                      "does NOT resolve (verified against the old one-token spec, "
                      "confirmed failing hidden tests in the recorded G-EQ run).",
        "rationale": "rejected by (NAME): Result != None => Result.name == model.name. "
                     "The rival sets Result.name == op_name == model.name_lower, and the "
                     "display-name token model.name is a DISTINCT token from the "
                     "lower-key token model.name_lower in general (mixed-case model "
                     "names), so the verifier cannot prove op_name == model.name.",
    },
    {
        "id": "uniq-mgr-carries-model-managers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_MGR_OLD_MANAGERS),
        "refinement": "the MANAGERS branch fires (folds) but carries the CREATION step's "
                      "managers (self.managers) instead of the alter step's "
                      "(operation.managers) — a patch with `managers=self.managers` in the "
                      "added hunk. The pair collapses to one CreateModel but LOSES the "
                      "AlterModelManagers effect: the F2P expects the folded CreateModel "
                      "to carry [('objects',...),('things',...)] (the alter step's "
                      "managers), but this yields the creation step's original managers "
                      "([] in the F2P). assertOptimizesTo fails; it does NOT resolve.",
        "rationale": "rejected by (MGR-FOLD): Result != None and MANAGERS => "
                     "Result.managers == op_managers. The rival sets Result.managers == "
                     "model.managers; the verifier cannot prove op_managers == "
                     "model.managers (arbitrary distinct tokens). The load-bearing "
                     "newly-added clause.",
    },
    {
        "id": "uniq-mgr-clobbers-options",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_MGR_CLOBBER_OPTS),
        "refinement": "the MANAGERS branch installs op_managers correctly but ALSO "
                      "overwrites the option facet with the alter step's op_options "
                      "instead of keeping the creation step's model.options. An "
                      "AlterModelManagers operation carries NO options attribute (it only "
                      "has managers), so a patch wiring options=operation.options would "
                      "install a wrong/missing option set on the folded model, dropping "
                      "the model's declared Meta options. It does NOT resolve.",
        "rationale": "rejected by (MGR-FOLD): Result != None and MANAGERS => "
                     "Result.options == model.options. The rival sets Result.options == "
                     "op_options; op_options != model.options is not provable (distinct "
                     "tokens). Diverges on the manager-fold sub-domain.",
    },
    {
        "id": "uniq-opt-carries-alter-managers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OPT_CLOBBER_MGRS),
        "refinement": "the symmetric clobber on the PRE-EXISTING OPTIONS branch: it "
                      "installs op_options correctly but replaces the manager facet with "
                      "op_managers instead of keeping the creation step's model.managers. "
                      "An AlterModelOptions operation carries NO managers, so a patch "
                      "wiring managers=operation.managers in the option fold would drop "
                      "the model's managers (the P2P test_create_alter_model_options "
                      "asserts the option fold preserves the creation step's other "
                      "facets). It does NOT resolve.",
        "rationale": "rejected by (OPT-FOLD): Result != None and OPTIONS => "
                     "Result.managers == model.managers. The rival sets Result.managers "
                     "== op_managers; op_managers != model.managers is not provable. "
                     "Partial-domain divergence on the option-fold sub-domain.",
    },
    {
        "id": "uniq-mgr-clobbers-fields",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_MGR_CLOBBER_FIELDS),
        "refinement": "the MANAGERS branch folds and carries op_managers, but wires the "
                      "FIELDS slot to op_managers instead of model.fields — a patch with "
                      "`fields=operation.managers`. The folded CreateModel would lose the "
                      "creation step's field list (replaced by the manager collection), "
                      "producing a model with no/garbage fields. The F2P expects "
                      "fields=[] (the creation step's fields) preserved; it does NOT "
                      "resolve.",
        "rationale": "rejected by (FIELDS): Result != None => Result.fields == "
                     "model.fields (ALWAYS from the creation step). The rival sets "
                     "Result.fields == op_managers; not provable equal to model.fields.",
    },
    {
        "id": "uniq-ignore-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_IGNORE_NAME),
        "refinement": "folds on op_kind ALONE, dropping the op_name == model.name_lower "
                      "guard — a patch that omitted `self.name_lower == "
                      "operation.name_lower` from both fold branches. It would collapse a "
                      "CreateModel('Foo') with an AlterModelManagers('Bar') for a "
                      "DIFFERENT model, merging unrelated models' facets and corrupting "
                      "the migration graph. The P2P optimiser tests (and the "
                      "differing-name path in axiom_check.py) require that a "
                      "differently-named alter does NOT fold; it does NOT resolve.",
        "rationale": "rejected by (IFF-1): Result is not None => op_name == "
                     "model.name_lower. On (MANAGERS, op_name != model.name_lower) the "
                     "rival returns a non-null fold, but the spec forbids a non-null "
                     "Result there. Partial-domain divergence on the differing-name "
                     "sub-domain.",
    },
    {
        "id": "uniq-diverging-self-call",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIVERGE),
        "refinement": "DIVERGES — it never returns. The unguarded self-call is the first "
                      "statement of reduce_create's impl and it passes the same arguments on "
                      "every frame, so the function re-enters itself before reaching any "
                      "return; a faithful control-flow simulation of this exact region raises "
                      "RecursionError (depth 501) even for the in-domain F2P input (a "
                      "same-keyed MANAGERS alter). A real patch whose CreateModel.reduce "
                      "re-entered itself before dispatching would HANG the F2P "
                      "test_create_alter_model_managers rather than fail it — the optimiser "
                      "would never return, so the patch does NOT resolve.",
        "rationale": "the partial-correctness hole the termination obligation closes, and the "
                     "reason this case sits in the reject lane rather than the accept lane it "
                     "started in (it was the admissibility probe, which asserted the spec "
                     "ACCEPTS it — true only while the spec demanded no termination). Measured "
                     "both ways on this exact source: with MustTerminate stripped from the "
                     "preconditions it VERIFIES (every Ensures holds vacuously of a run that "
                     "never reaches the return — verify without correct); with the obligation "
                     "present Nagini rejects it, 'Obligation leak check failed. Callee "
                     "reduce_create might not take all unsatisfied obligations from the "
                     "caller.' Rejection source is Requires(MustTerminate(6)) alone, NOT a "
                     "value pin: the values it would return, if it ever returned, are gold's. "
                     "So this case is only refutable by a spec that demands termination — a "
                     "strictly stronger claim than the accept-lane case it replaces.",
    },
    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-skip-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_ALL),
        "refinement": "never folds (always None) — a patch that removed BOTH fold "
                      "branches (no option fold, no manager fold). The optimiser would "
                      "never collapse a CreateModel + same-named option/manager alter; the "
                      "F2P test_create_alter_model_managers AND the P2P "
                      "test_create_alter_model_options both fail (the pairs stay "
                      "un-collapsed). Supporting near-miss for the fold-existence clause; "
                      "it resolves nothing.",
        "rationale": "rejected by (IFF-2): op_name == model.name_lower => Result is not "
                     "None. On any same-keyed option/manager alter the spec demands a "
                     "non-null fold; the rival returns None.",
    },
]


# ===========================================================================
# AXIOM LANE — none. meta.json axioms=[]; no @ContractOnly axiom is consumed and
# there is no A-reference deep model. The fold calls no library/utility callee it
# does not change: it compares an integer name-key token, branches on a kind tag,
# and constructs a new CreateModel by selecting which facet token to place in
# which slot — all modelled DEEPLY over integers and the minimal CreateModel
# object. There is nothing to over-approximate, so no axiom-soundness /
# axiom-containment obligation to probe. axiom_check.py / G-AX validates the
# STRUCTURAL reduction against the REAL CreateModel.reduce (same-named manager
# alter folds carrying the alter step's managers AND the creation step's
# case-preserved display name; option fold symmetric; differing name does not
# fold), not an axiom. (G-AX status is 'vacuous' in meta.json.)
# ===========================================================================
AXIOM_TESTS = []
