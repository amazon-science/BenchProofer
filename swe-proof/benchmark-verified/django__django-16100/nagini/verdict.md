# P2 adversarial audit — django__django-16100

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-16100 nagini bundle. Modeled function apply_batch models the list-editable bulk-save loop of ModelAdmin.changelist_view (options.py:2012-2021); the deep model committed_value/any_fails models transaction.atomic's commit/rollback semantics (the callee the gold patch introduces). Spec: each row's committed value = replacement iff any_fails(fails,0) is False (no edit raises), else original — the SAME batch-global verdict for every row (full commit or full rollback, no committed prefix on mid-batch failure).

Verification performed:
1. same-spec on bundle model: SAME (spec byte-identical, exit 0).
2. nagini_verify.sh on model.py: Verification successful (17.07s).
3. G-AX axiom_check.py re-run against the REAL worktree Django 4.2.dev at base_commit (+ asgiref/sqlparse from ax16100_libs): PASS — 'committed_value/any_fails deep model == real transaction.atomic commit/rollback over 2029 batches'. This executes an actual transaction.atomic block over in-memory SQLite, injects a failure at every position (and none), plus the F2P witnesses [1,0],[0,1],[0,0] and 2000 fuzz batches. The critical no-committed-prefix case [0,1] (first row succeeds, second raises -> both revert) matches exactly.

No diverging input found: the modeled function agrees with the real transaction.atomic callee on every tested batch including boundary and adversarial cases. The abstraction that allows fails[r]==1 on an unchanged row (newvals[r]==original[r]) is a SUPERSET of reality (harmless generalization, not over-strengthening), and committed_value yields the same value on either verdict there. Spec matches gold-patch behavior; no drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view (rendered via swebench_unified.markers.spec_view over model.py; impl region elided) was inspected directly. Contents: (1) an abstract behavioral docstring stating ALL-OR-NOTHING batch semantics — commit every row's replacement on full-batch success, revert every row to its original on ANY failure, no committed prefix on mid-batch failure; (2) generic pure helpers any_fails / committed_value and the apply_batch signature over List[int]; (3) pre/post conditions phrased purely over PSeq[int] via ToSeq; (4) an axioms comment noting an abstract 'write-grouping boundary whose failure path discards grouped writes'.

The public problem_statement already discloses the gold intent: 'Add transaction handling to Changelist list_editable processing ... it should be wrapped in a transaction to prevent unexpected states in case of errors.' The spec view's all-or-nothing content is exactly the legitimate formalization of that stated feature (atomicity = commit-on-success / rollback-on-any-error), not an additional disclosure.

No code-level gold edit is revealed anywhere in the spec view: there is NO mention of Django, django/contrib/admin/options.py, changelist_view, formset.forms, transaction.atomic, router.db_for_write(self.model), the with-block wrapping the save loop, or the file:line. Those concrete gold-patch tokens appear ONLY in refinement.md and mapping.md, which are audit documents and are NOT part of the consumer spec view — they never reach the solver. The spec stays at an integer-list abstraction and leaks nothing beyond the public problem_statement (hints_text excluded from consideration).

Spec view was generated with the pinned markers projection; impl fully collapsed to the elision placeholder, so no implementation strategy (staging + single-verdict commit loop) leaks either.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
