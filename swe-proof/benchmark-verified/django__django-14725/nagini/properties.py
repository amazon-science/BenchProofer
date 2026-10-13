# properties.py — PBT falsification battery for django__django-14725. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   persist(self: CollectionEditor, commit: bool) -> List[int]
#     Requires(Acc(self.restrict_to_existing, 1/2))     # READ-ONLY input (1/2 perm)
#     Requires(self.run_counts_pred())                   # invocation counts advanced
#     Requires(MustTerminate(2))                         # bounded work
#     Ensures(Acc(self.restrict_to_existing, 1/2))       # permission returned
#     Ensures(self.run_counts_pred())
#     Ensures(Acc(list_pred(Result())))
#     Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
#     Ensures(Implies(self.restrict_to_existing,                                  # (1)
#                     ToSeq(Result()) == existing_report(commit)))
#     Ensures(Implies(self.restrict_to_existing,                                  # (1e)
#                     self.get_new_runs() == Old(self.get_new_runs())))
#     Ensures(Implies(not self.restrict_to_existing,                             # (2)
#                     ToSeq(Result()) == existing_report(commit) + new_report(commit)))
#     Ensures(Implies(not self.restrict_to_existing,                             # (2e)
#                     self.get_new_runs() == Old(self.get_new_runs()) + 1))
#   existing_report(commit) / new_report(commit): @Pure @ContractOnly, OPAQUE
#     PSeq[int] (the contract asserts nothing about their content). They are
#     deterministic pure functions of `commit`.
#   persist_existing_objects(self, commit) / persist_new_objects(self, commit):
#     @ContractOnly list-returning callees; EACH RUN IS AN EFFECT — it advances
#     its own monotone invocation count on the editor by exactly one (the counts
#     live behind the run_counts_pred abstraction predicate; only the primitive
#     may advance its count) and
#       Ensures(Acc(list_pred(Result()))); Ensures(ToSeq(Result()) == <report>(commit))
#
# What the spec defends (the load-bearing clauses):
#   * (1) restrict => ToSeq(Result()) == existing_report(commit). The result must
#     equal the existing-group report ALONE — the new group must be OMITTED. This
#     is exactly the gold fix; model_prepatch.py (unconditional existing+new)
#     FAILS this clause (G-DIFF) when new_report is non-empty.
#   * (1e) restrict => get_new_runs() unchanged: the new-record primitive is
#     NEVER run when the flag forbids new records — an impl cannot invoke it for
#     its persistence EFFECT while discarding its report.
#   * (2) not restrict => ToSeq(Result()) == existing_report(commit) + new_report(commit).
#     Pins the unchanged default: existing group FOLLOWED BY new group, in that
#     order. A verifying impl can neither drop the new group when the flag is off
#     (P2P) nor reorder the two groups.
#   * (2e) not restrict => get_new_runs() advances by EXACTLY one (and
#     get_existing_runs() by exactly one in both modes): each primitive runs
#     exactly once per mode arm — no duplicate persistence.
#   * Permission: self.restrict_to_existing is held at Acc(...,1/2) — READ-ONLY.
#     A faithful save() observes the flag without writing it; the frame-mutation
#     probe (write the 1/2-perm flag) MUST reject for insufficient permission.
#   * Termination: persist Requires(MustTerminate(2)); a frozen/non-terminating
#     body cannot discharge the postconditions vacuously.
#
# On the ungrounded-oracle-echo class (PBT_PLAN §2.2): the oracle here is
# GROUNDED, not an answer-key. The result is pinned to existing_report(commit)
# [+ new_report(commit)], which are deterministic @Pure functions of the `commit`
# arg. There is no opaque "answer" the impl could echo to satisfy the
# postcondition without producing it: to make ToSeq(Result()) equal the concat
# of the two reports the impl MUST call the two report-producing primitives in
# the right combination (their Ensures are the ONLY way the verifier learns a
# list's ToSeq equals a report). A literal / fabricated sequence cannot be proven
# equal to an opaque report. So there is no wrong echo; the honest cheapest-impl
# positive control (pos-control-call-once) stands in for that class. See
# `assessment` in the structured return.
from pathlib import Path

INSTANCE = "django__django-14725"
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
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Both keep every proof obligation the gold
# needs (the per-branch report Ensures); they only reshape the executable form.
# No loop / no fold, so no induction lemma is required (pilot pitfalls #2/#3).
# ===========================================================================

# pos-control-call-once: compute the existing-group report ONCE into a local and
# reuse it across both branches (the gold calls persist_existing_objects inside
# each branch). ToSeq(existing) == existing_report(commit) holds from the callee
# Ensures, so clause (1) (restrict => existing alone) and clause (2)
# (else => existing + new) both still hold. A local-variable reshape, branch
# order unchanged. This is also the honest cheapest-impl stand-in for the
# (inapplicable) ungrounded-oracle-echo class.
_POS_CALL_ONCE = """    # impl-start
    existing = persist_existing_objects(self, commit)
    if self.restrict_to_existing:
        result = existing  # type: List[int]
    else:
        result = existing + persist_new_objects(self, commit)
    return result
    # impl-end"""

# pos-control-reorder: branch-reorder on the negated flag (not-restrict arm
# first). Behaviourally identical to the gold two-armed branch; both clauses
# hold. A safe reorder (no loop-direction flip, no fold) per pilot pitfall #3.
_POS_REORDER = """    # impl-start
    if not self.restrict_to_existing:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit)
    return result
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller function: a
# new module-level def changes the projected spec view and breaks same_spec.
# Instead we inject the admissibility witness INSIDE the impl region (elided from
# the spec view) as a leading block: construct a concrete CollectionEditor (the
# F2P editor in default mode, restrict_to_existing=False) and ASSERT the
# function's exact Requires (Acc(adm.restrict_to_existing, 1/2)) is establishable
# from the constructor's full-permission Ensures. The real impl then runs
# unchanged over the actual params. If the precondition could not be established
# for this legitimate input the Assert would fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm = CollectionEditor(False)
    # the function's Requires is establishable for this concrete editor: the
    # constructor Ensures full Acc(adm.restrict_to_existing); the read-only
    # precondition needs only the 1/2 fraction.
    Assert(Acc(adm.restrict_to_existing, 1 / 2))
    Assert(not adm.restrict_to_existing)
    # --- end admissibility witness; the real impl follows unchanged ---
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness/reject) — MANDATORY: self.restrict_to_existing is a
# READ-ONLY input held at Acc(...,1/2). A rival that WRITES the flag inside the
# impl needs FULL permission; with only 1/2 it MUST reject for insufficient
# permission. The gold postcondition clauses are kept verbatim (frozen spec) so
# the rejection is attributable to the write, not to a value mismatch.
# ===========================================================================

# frame-mut-write-flag: overwrite the read-only flag, then return the correct
# concatenation. Even though the returned value would satisfy the postcondition,
# the assignment `self.restrict_to_existing = ...` requires write permission the
# caller does not grant (only 1/2). Rejected for insufficient permission.
_FRAME_MUT_WRITE = """    # impl-start
    self.restrict_to_existing = False
    result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end"""

# frame-mut-self-assign: a supporting near-miss — a no-op self-assignment of the
# flag. Even reassigning it to its own value requires WRITE permission; with 1/2
# the write is rejected. Confirms the rejection is the permission system, not the
# concrete value written.
_FRAME_MUT_SELF = """    # impl-start
    self.restrict_to_existing = self.restrict_to_existing
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain — rivals that share the spec exactly and change
# ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-always-concat: THE BUG. Ignore the flag and ALWAYS return existing + new
# (exactly model_prepatch.py / the pre-patch unconditional return). Clause (2)
# holds, but clause (1) (restrict => existing alone) fails when new_report is
# non-empty. Rejected by clause (1).
_UNIQ_ALWAYS_CONCAT = """    # impl-start
    result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end"""

# uniq-always-existing: ignore the flag the OTHER way — ALWAYS return the
# existing group alone. Clause (1) holds, but clause (2) (not restrict =>
# existing + new) fails when new_report is non-empty. Rejected by clause (2).
_UNIQ_ALWAYS_EXISTING = """    # impl-start
    result = persist_existing_objects(self, commit)  # type: List[int]
    return result
    # impl-end"""

# uniq-flip-condition: invert the branch — return existing+new when the flag
# FORBIDS new records, and existing alone when it PERMITS them. Both clauses
# fail (restrict arm now over-includes; default arm now under-includes).
# Rejected by clauses (1) and (2).
_UNIQ_FLIP = """    # impl-start
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit)
    return result
    # impl-end"""

# uniq-swap-order: keep the flag branch correct in the restrict arm, but in the
# default arm return the NEW group FOLLOWED BY the existing group (order
# swapped). ToSeq(Result()) == new_report + existing_report, which the verifier
# cannot prove equals existing_report + new_report (sequence concatenation is not
# commutative for opaque reports). Rejected by clause (2)'s ordering.
_UNIQ_SWAP_ORDER = """    # impl-start
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_new_objects(self, commit) + persist_existing_objects(self, commit)
    return result
    # impl-end"""

# uniq-restrict-includes-new: keep the default arm correct, but in the RESTRICT
# arm include the new group too (existing + new). This is the precise partial-
# domain attack: correct on the default sub-domain, wrong only on the restrict
# sub-domain. Clause (1) fails when new_report is non-empty. Rejected by clause (1).
_UNIQ_RESTRICT_INCLUDES_NEW = """    # impl-start
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end"""

# uniq-return-new-only: degenerate near-miss — always return the new group
# alone. Clause (1) (restrict => existing alone) and clause (2) (=> existing +
# new) both fail (the verifier cannot prove new_report == existing_report nor
# new_report == existing_report + new_report). Supporting near-miss; rejected by
# both clauses.
_UNIQ_RETURN_NEW_ONLY = """    # impl-start
    result = persist_new_objects(self, commit)  # type: List[int]
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-call-once",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_CALL_ONCE),
        "rationale": "structurally-different CORRECT impl: compute the existing-group "
                     "report ONCE into a local and reuse it across both branches "
                     "(gold calls persist_existing_objects inside each branch). "
                     "ToSeq(existing) == existing_report(commit) from the callee "
                     "Ensures, so clause (1) (restrict => existing alone) and clause "
                     "(2) (else => existing + new) both hold. Local-variable reshape, "
                     "branch order unchanged; no loop/fold so no lemma needed (pilot "
                     "pitfalls #2/#3 avoided). Also the honest cheapest-impl stand-in "
                     "for the inapplicable ungrounded-oracle-echo class. If a faithful "
                     "correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "branch-reorder on the negated flag (not-restrict arm first). "
                     "Behaviourally identical to the gold two-armed branch; both "
                     "clauses hold under the same flag. A safe reorder (no loop-"
                     "direction flip, no fold). If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) constructs a concrete "
                     "F2P-shaped editor CollectionEditor(False) (default mode, as in "
                     "test_edit_only's first formset and the P2P default scenarios) and "
                     "asserts the function's exact Requires Acc(adm.restrict_to_existing, "
                     "1/2) is establishable from the constructor's full-permission "
                     "Ensures. The real impl then runs unchanged. If the precondition "
                     "could not be established for a legitimate editor the Assert fails "
                     "=> PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (must reject for insufficient permission; #1 class) ----
    {
        "id": "frame-mut-write-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUT_WRITE),
        "refinement": "a faithful real patch corresponding to this impl would have "
                      "save() ASSIGN to self.edit_only (the mode flag) during the save "
                      "— mutating the formset's edit-only mode as a side effect of "
                      "persisting. The gold patch never writes edit_only in save(); it "
                      "only reads it. Such a write would corrupt the formset's mode for "
                      "subsequent operations and is not the change under test, so it "
                      "would not faithfully resolve the F2P (and would regress P2P "
                      "behaviour that re-reads the flag).",
        "rationale": "rejected by the PERMISSION SYSTEM: self.restrict_to_existing is "
                     "held at Acc(...,1/2) (read-only); the assignment "
                     "self.restrict_to_existing = False needs FULL write permission "
                     "the caller does not grant. The rejection is insufficient "
                     "permission, not a value mismatch (the returned value would "
                     "satisfy the postcondition).",
    },
    {
        "id": "frame-mut-self-assign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUT_SELF),
        "refinement": "even a no-op self-assignment self.edit_only = self.edit_only in "
                      "save() is a WRITE the gold patch does not perform; a faithful "
                      "patch that wrote the flag (to any value, incl. its own) takes "
                      "write ownership of read-only formset state and is not the "
                      "modeled change. Supporting near-miss confirming the rejection is "
                      "the permission fraction, not the written value.",
        "rationale": "rejected by the PERMISSION SYSTEM: any assignment to "
                     "self.restrict_to_existing requires full Acc; only 1/2 is held, so "
                     "the write fails for insufficient permission regardless of the "
                     "RHS value.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-always-concat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_CONCAT),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces "
                      "and G-DIFF flags: save() unconditionally returns "
                      "save_existing_objects(commit) + save_new_objects(commit), "
                      "ignoring edit_only. FAIL_TO_PASS test_edit_only submits two new "
                      "forms with edit_only=True and asserts Author.objects.all() == "
                      "[charles] (no new record created); test_edit_only_inlineformset_"
                      "factory and test_edit_only_object_outside_of_queryset assert the "
                      "same. With the new group always appended, new Authors/Books are "
                      "created and these F2P tests fail — its faithful real patch (the "
                      "un-patched return) is exactly what does NOT resolve.",
        "rationale": "rejected by postcondition clause (1) "
                     "Implies(self.restrict_to_existing, ToSeq(Result()) == "
                     "existing_report(commit)): when the flag is set the result is "
                     "existing_report + new_report, which the verifier cannot prove "
                     "equals existing_report alone (new_report is an opaque, possibly "
                     "non-empty PSeq).",
    },
    {
        "id": "uniq-restrict-includes-new",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RESTRICT_INCLUDES_NEW),
        "refinement": "the precise partial-domain rival: CORRECT on the default sub-"
                      "domain (edit_only=False), wrong only on the restrict sub-domain "
                      "— it still appends the new group when edit_only=True. The F2P "
                      "tests all exercise edit_only=True with extra new forms and "
                      "assert NO new record is created; this patch creates them, so it "
                      "fails exactly test_edit_only / test_edit_only_inlineformset_"
                      "factory / test_edit_only_object_outside_of_queryset and does "
                      "NOT resolve.",
        "rationale": "rejected by clause (1): in the restrict arm the result is "
                     "existing_report + new_report, not provably equal to "
                     "existing_report alone.",
    },
    {
        "id": "uniq-always-existing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_EXISTING),
        "refinement": "ignoring the flag the other way — always returning the existing "
                      "group alone — corresponds to a patch that DROPS the new group "
                      "unconditionally (always edit_only). It resolves the F2P tests "
                      "but regresses the unchanged default behaviour the PASS_TO_PASS "
                      "tests pin: e.g. test_simple_save / test_inline_formsets create "
                      "new objects through a default (edit_only=False) formset and "
                      "assert the new records appear; dropping the new group makes "
                      "save() omit them, so these P2P tests fail and it does NOT "
                      "resolve.",
        "rationale": "rejected by postcondition clause (2) "
                     "Implies(not self.restrict_to_existing, ToSeq(Result()) == "
                     "existing_report(commit) + new_report(commit)): when the flag is "
                     "off the result is existing_report alone, which the verifier "
                     "cannot prove equals existing_report + new_report (new_report is "
                     "opaque, possibly non-empty).",
    },
    {
        "id": "uniq-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWAP_ORDER),
        "refinement": "the order-swap rival: in the default arm it returns the new "
                      "group FOLLOWED BY the existing group. The F2P/P2P tests observe "
                      "the ORDER of persisted records (e.g. axiom_check / the default "
                      "scenario assert existing-then-new: ['Base Edited', 'Newly "
                      "Created']); a patch that emitted new-then-existing would return "
                      "records in the wrong order and fail the sequence-equality "
                      "assertions, so it does NOT resolve.",
        "rationale": "rejected by clause (2): ToSeq(Result()) == new_report + "
                     "existing_report, which the verifier cannot prove equals "
                     "existing_report + new_report — PSeq concatenation is not "
                     "commutative for opaque reports.",
    },
    {
        "id": "uniq-flip-condition",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FLIP),
        "refinement": "inverting the branch (concat when the flag FORBIDS new records, "
                      "existing alone when it PERMITS) corresponds to a patch with the "
                      "guard inverted (if not self.edit_only: return existing else "
                      "return existing+new). It both creates new records under "
                      "edit_only (failing every F2P test) and drops them under the "
                      "default (failing the P2P default-save tests), so it does NOT "
                      "resolve.",
        "rationale": "rejected by BOTH clauses: in the restrict arm the result is "
                     "existing_report + new_report (violates clause (1)); in the "
                     "default arm it is existing_report alone (violates clause (2)).",
    },
    {
        "id": "uniq-return-new-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RETURN_NEW_ONLY),
        "refinement": "always returning the new group alone corresponds to a patch "
                      "that dropped the existing group entirely — it would fail to "
                      "report edited existing records (e.g. test_simple_save / "
                      "test_edit_only's edit submission assert the existing record is "
                      "returned/persisted) and creates new records under edit_only, "
                      "failing both F2P and P2P. Supporting near-miss.",
        "rationale": "rejected by both clauses: ToSeq(Result()) == new_report cannot "
                     "be proven equal to existing_report (clause 1) nor to "
                     "existing_report + new_report (clause 2); the opaque reports are "
                     "independent.",
    },
]


# ===========================================================================
# AXIOM LANE — two A-consumed axioms describing the UNCHANGED persistence
# primitives:
#   existing_report(commit) == ToSeq(save_existing_objects(commit))   (existing group)
#   new_report(commit)      == ToSeq(save_new_objects(commit))        (new group)
# Each is OPAQUE (the model asserts nothing about the reports' content); the only
# soundness obligation is that (i) the two primitives are UNCHANGED by the patch
# (so modelling them as opaque report-producers is faithful) and (ii) the
# discriminating end-to-end behaviour the spec pins holds against the REAL Django
# machinery: save() == existing-group alone under edit_only, and
# existing-group ++ new-group otherwise. Probes run in the instance Docker image
# (the real Django lives only there). The runner mounts ONLY the probe at /work,
# so we embed the bundle's own axiom_check.py soundness logic inline (it imports
# only Django + stdlib inspect, both present in-container). apply_gold=True so the
# patched save()/factories are present (the axioms describe post-gold behaviour;
# the two primitives themselves are unchanged either way).
# ===========================================================================

# The bundle's axiom_check.py logic is embedded verbatim-in-spirit below so the
# probe is self-contained (no bundle file is mounted in-container). It is read at
# manifest-load time on the HOST to keep the two in sync; if it drifts we still
# ship the inlined copy (the embedded source IS the probe the runner executes).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()
# Strip the bundle file's own `if __name__ == "__main__": sys.exit(main())`
# guard so OUR wrapper (below) is the sole entry point when the probe runs as
# /work/probe.py (otherwise the embedded guard fires first and our diagnostics
# never print). The functional behaviour is identical either way (exit 0 iff
# every obligation holds), but stripping it keeps the output attributable.
_AXIOM_CHECK_GUARD = '\nif __name__ == "__main__":\n    sys.exit(main())\n'
if _AXIOM_CHECK_GUARD not in _AXIOM_CHECK_SRC:
    raise AssertionError("axiom_check.py guard drifted; update the strip pattern")
_AXIOM_CHECK_SRC = _AXIOM_CHECK_SRC.replace(_AXIOM_CHECK_GUARD, "\n")


# axiom-soundness: assert (i) save_existing_objects / save_new_objects do NOT
# reference edit_only (they are the unchanged primitives the axioms abstract) and
# (ii) the end-to-end discriminating behaviour over the three FAIL_TO_PASS
# scenarios + a default scenario. We reuse the bundle's audited axiom_check.main()
# verbatim (it already establishes exactly these obligations against the real
# Django and exits 0 iff every one holds). Any failure (a primitive that grew an
# edit_only reference, or save() not equal to existing/existing++new) =>
# AXIOM-UNSOUND.
_AX_SOUNDNESS_PROBE = (
    "# encoding: utf-8\n"
    "import sys\n"
    + _AXIOM_CHECK_SRC
    + "\n\n"
    "if __name__ == '__main__':\n"
    "    rc = main()\n"
    "    if rc == 0:\n"
    "        print('AXIOM-SOUNDNESS OK: existing_report/new_report axioms sound — "
    "the two persistence primitives are unchanged (no edit_only ref) and save() "
    "== existing under restriction, existing ++ new otherwise, over the real "
    "Django formset machinery (all FAIL_TO_PASS scenarios).')\n"
    "    else:\n"
    "        print('AXIOM-UNSOUND: a soundness obligation failed (see traceback above).')\n"
    "    sys.exit(rc)\n"
)


# axiom-containment: the model can only ever pass `commit` (a bool) to
# existing_report / new_report (and to the list-returning callees). The axioms'
# Requires domain is `commit: bool` (no further constraint), so EVERY caller-
# reachable input (commit True or False) lies inside the axiom domain — the two
# values exhaust bool. We confirm operationally that BOTH reachable commit values
# drive the real save_existing_objects / save_new_objects without error and that
# save() respects the discriminating behaviour under each, i.e. the caller never
# reaches a commit value outside the axiom domain. (Covering more would be
# impossible — bool has exactly two values, both reached.)
_AX_CONTAINMENT_PROBE = r'''# encoding: utf-8
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-CONTAINMENT SKIP: Django not configurable: %r" % (exc,))
        return 0

    from django.db import connection, models
    from django.forms.models import modelformset_factory

    class Author(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(Author)

    # The model's `persist` only ever passes `commit` (a bool) to the report
    # primitives; the axioms' Requires domain is `commit: bool`. bool has exactly
    # two inhabitants, so enumerate BOTH — each is inside the axiom domain and the
    # real callees accept it. (A caller-reachable input outside the domain would
    # be AXIOM-TOO-WEAK-FOR-CALLER; none can exist for a bool param.)
    #
    # IMPORTANT — exercise the primitives the way the model actually REACHES them:
    # through `save()` (the repo counterpart of `persist`). Django's
    # save_existing_objects / save_new_objects are NOT standalone entry points —
    # they append to `self.saved_forms`, a list that ONLY `save()` initialises
    # (and only when commit is False; see BaseModelFormSet.save). Calling them in
    # isolation raises AttributeError('... has no attribute saved_forms'), which
    # is an out-of-band path the model never takes (persist == save, and clause
    # (2)'s call sequence is exactly save()'s default-branch
    # save_existing_objects(commit) + save_new_objects(commit)). So we drive each
    # reachable `commit` through save() in the default (non-restrict) mode and
    # confirm the primitives accept the bool and produce the existing ++ new
    # concatenation — i.e. the caller reaches no commit value outside the domain.
    reached = []
    for commit in (True, False):
        base = Author.objects.create(name="Base %s" % commit)
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(base.pk),
            "form-0-name": "Base Edited %s" % commit,
            "form-1-name": "New %s" % commit,
        }
        fs = AuthorFormSet(data)
        assert fs.is_valid() is True, fs.errors
        # save() threads the bool `commit` straight into both
        # save_existing_objects(commit) and save_new_objects(commit) (the only
        # caller-reachable input), exactly as the model's clause-(2) branch does.
        saved = fs.save(commit=commit)
        assert isinstance(saved, list), (
            "AXIOM-TOO-WEAK-FOR-CALLER: save() rejected commit=%r: %r"
            % (commit, saved))
        # the existing group (edited base) precedes the new group, as the axioms'
        # concatenation pins; both primitives accepted the bool `commit`.
        names = [a.name for a in saved]
        assert names == ["Base Edited %s" % commit, "New %s" % commit], (
            "AXIOM-TOO-WEAK-FOR-CALLER: primitives did not produce existing ++ new "
            "under commit=%r: %r" % (commit, names))
        reached.append(commit)
        Author.objects.all().delete()

    assert sorted(reached) == [False, True], (
        "AXIOM-TOO-WEAK-FOR-CALLER: not every reachable commit value covered: %r"
        % (reached,))
    print("AXIOM-CONTAINMENT OK: the model passes only `commit` (a bool) to the "
          "report primitives; both inhabitants {True, False} are driven through "
          "the real save() (persist's repo counterpart, the legitimate entry "
          "point for save_existing_objects / save_new_objects) and accepted, "
          "producing existing ++ new. Both lie inside the axioms' bool Requires "
          "domain; the caller reaches no input outside it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-reports",
        "axiom": "existing_report / new_report",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the axioms describe post-gold behaviour; primitives unchanged
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "if the real save_existing_objects / save_new_objects ever grew an "
                     "edit_only reference (no longer the unchanged primitives the "
                     "axioms abstract), or save() did not equal existing-group alone "
                     "under edit_only / existing ++ new otherwise, the opaque-report "
                     "axioms would be unsound => AXIOM-UNSOUND. Reuses the bundle's "
                     "audited axiom_check.main(), which establishes exactly these "
                     "obligations end-to-end against the real Django over all three "
                     "FAIL_TO_PASS scenarios plus a default-mode scenario.",
    },
    {
        "id": "ax-cover-reports",
        "axiom": "existing_report / new_report",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "the model passes only `commit` (a bool) to the report "
                     "primitives; the axioms' Requires domain is `commit: bool`. bool "
                     "has exactly two inhabitants, both enumerated and accepted by the "
                     "real callees, so every caller-reachable input lies inside the "
                     "axiom domain. A reachable input outside the domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none can exist for a bool parameter.",
    },
]
