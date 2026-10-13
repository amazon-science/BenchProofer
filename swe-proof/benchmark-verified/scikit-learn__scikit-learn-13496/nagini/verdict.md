# P2 adversarial audit — scikit-learn__scikit-learn-13496

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
- **machine verdict:** Faithfulness-break attack on scikit-learn__scikit-learn-13496 (nagini). Spec region byte-identical (same-spec exit 0); model verifies (nagini_verify exit 0, 12.15s). The bundle consumes NO @ContractOnly axiom — the reuse decision and roster update are modeled DEEPLY (refit_to_size dispatching over reuse_and_extend/rebuild_all with pure fresh_run), so the faithfulness question is whether the deep model agrees with the real callee BaseBagging._fit (bagging.py:337-385) exposed via IsolationForest's forwarded warm_start.

Ran axiom_check.py (G-AX) against real sklearn (1.2.0 installed in throwaway venv; warm-start semantics stable across 0.21→1.2): PASS on all 70 (reuse+rebuild) scenarios, incl. the F2P case (10→20) and the boundary n_total==n_first (5,5).

Domain-by-domain vs real _fit, within the precondition (len(existing)<=target_count, existing identities >=0):
 - Reuse (warm_start & members present): real does self.estimators_ += [fresh...], preserving the existing list verbatim as prefix and reaching n_estimators; model reuse_and_extend gives ToSeq(existing)+fresh_run(target-len), size==target. Agrees.
 - Rebuild (warm_start=False, or first fit / no estimators_): real sets self.estimators_=[] then builds a full forest; model rebuild_all gives all-FRESH_MEMBER roster of size target. Agrees.
 - Boundary target==len(existing): real warns and returns unchanged (prefix kept, size==target); model's extend loop is a no-op so result==existing. Agrees (axiom_check (5,5) confirms).
 - target<len(existing): real raises ValueError; model precondition len(existing)<=target_count excludes this, so no over-claim on that input.
 - Empty roster + reuse requested: effective_reuse(True, len==0)=False -> rebuild; matches real first-fit which has no estimators_ and rebuilds.

Abstractions are conservative, not too strong: object list -> List[int] identities; `is` -> int equality; freshly-built member -> sentinel -1 (distinct from non-negative existing ids), validated by axiom_check using true object identity (`is`) with retained live references (avoids CPython id() recycling false-survivors). The postcondition set (always size==target; reuse => prefix preserved + fresh tail; else all fresh) is exactly what the real incremental roster does; no reachable input where modeled function disagrees with real callee. Spec is faithful and appropriately deep; not too strong / no drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit (sklearn/ensemble/iforest.py): expose warm_start in IsolationForest.__init__(..., warm_start=False), forward it to super().__init__(warm_start=warm_start) (re-enabling BaseBagging._fit's reuse branch), plus a warm_start docstring block.

The PUBLIC problem_statement already fully specifies this fix: title 'Expose warm_start in Isolation forest'; explains warm_start is inherited from BaseBagging and does incremental tree addition; and explicitly requests 'expose warm_start in IsolationForest.__init__(), default False' AND gives the verbatim docstring 'When set to True, reuse the solution of the previous call to fit and add more estimators to the ensemble, otherwise, just fit a whole new forest.' So the reuse-vs-rebuild semantics are public, not hint-only.

The spec view (rendered via markers.spec_view over model.py: module docstring + pure defs + all Requires/Ensures) is a strict ABSTRACTION of that public ask. It speaks only of an anonymous 'incremental-ensemble estimator', a 'roster' of 'members', a 'construction-time option' governing reuse-and-extend vs rebuild. It never names iforest.py, IsolationForest, __init__, BaseBagging, warm_start, n_estimators, or the forwarding line. The docstring line 'the option ... must be carried through faithfully, not silently forced off' restates the public 'expose+forward the option' request in more abstract terms than the problem_statement itself uses.

The concrete repo mapping (file/line 167-190, the warm_start forwarding, bagging.py:338-385) lives only in mapping.md / meta.json.modeled_functions / deep_model_references — audit artifacts, NOT part of the solver-visible spec view. Checked each spec-view line: no line reveals the gold code edit beyond what the public problem_statement already discloses. G-LEAK also passed (spec view clean).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
