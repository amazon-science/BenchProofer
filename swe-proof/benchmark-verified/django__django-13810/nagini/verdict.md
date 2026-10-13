# P2 adversarial audit — django__django-13810

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
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) FAILED — no diverging input found; spec is a faithful (indeed slightly conservative) model of the real patched load_middleware.

Evidence gathered:
1. Base state confirmed: at base_commit (fbe82f8255) contains the PRE-PATCH buggy load_middleware (django/core/handlers/base.py:39-89): `handler = self.adapt_method_mode` assigned BEFORE `mw_instance = middleware(handler)`, and the MiddlewareNotUsed `except: continue` has no rollback and no `else` — so a declining layer poisons the running handler. This is a fix-bundle; the model.py spec models the DESIRED (patched) behavior and senses the bug via G-DIFF. Correct construction.
2. Gold-hunk fidelity: patched code introduces `adapted_handler` + `else: handler = adapted_handler`; on decline neither handler nor handler_is_async is reassigned, on participate handler=convert_exception_to_response(mw_instance) and handler_is_async=middleware_is_async. model.py's final_handler/final_async folds (committed_handler = wrap(adapt(h,m)), flag->target_mode[i], decline = pass-through) mirror this exactly. refinement.md rows A3-A6 map correctly.
3. `target_mode[i]` modeled as a FREE input while real middleware_is_async is derived from handler_is_async + sync/async capability. This is an OVER-approximation (superset of realizable traces) — the safe direction; it never makes the model disagree with the real callee on any realizable input, only admits extra ones.
4. adapt_method_mode returns `method` UNCHANGED when is_async==method_is_async (not always a fresh object). This does not break the List[int] token-trace identity encoding: on the participate path convert_exception_to_response always produces a fresh closure regardless, so identity stays injective; adapt's [1,m] tokens are deterministic trace markers, not physical-wrapping claims. Faithful.

Machine checks all consistent with FAITHFUL:
- same-spec on the bundle model: SAME.
- bash scripts/nagini_verify.sh model.py: Verification successful (12.12s), exit 0.
- axiom_check.py (G-AX): reconstructs real patched threading (_RealAdapter.run matches gold control flow) and asserts model==real on 12 boundary + 50000 fuzz layer sequences INCLUDING the decline-no-trace property; passed.

No input exhibited where the modeled function disagrees with the real (patched) callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Audited the consumer spec view for django__django-13810 (nagini). Recomputed spec_view hash = fdd02cd392badfc335996a8388d86988cb2aeccd2f8e72fba79bf317ec0e0f9e, byte-identical to meta.region_hashes.spec_view, confirming the view audited is authentic and the impl region is cleanly elided ('... # implementation elided — supplied by the consumer'). The impl and nested invariant regions (which carry the actual 'compute tentative adaptation, commit only on the participating branch' mechanics that ARE the gold edit) are not present in the spec view.

Gold edit: rename the in-place 'handler = self.adapt_method_mode(...)' to a fresh local 'adapted_handler', pass it to middleware(...), and commit 'handler = adapted_handler' only in the try/except's else branch, so a MiddlewareNotUsed decline leaves the running handler/async flag untouched.

The PUBLIC problem_statement already discloses this at full detail: it names base.py#L58, states 'MiddlewareNotUsed ... does leave handler variable overwritten with output of self.adapt_method_mode()', and 'On next pass, this handler is passed to next middleware instance, disregarding all the previous checks for (lack of) async support' — i.e. the exact bug, its async-flag consequence, and the implied fix (do not carry the adaptation forward on decline).

The spec view expresses only desired behaviour (explicit: 'stated as desired behaviour, not as an edit'). Its discriminating clause — declining layer must leave 'both the running handler and the running async-mode flag ... exactly the values ... before this declining layer was visited' — is a behavioural restatement at or below the disclosure level of the public problem_statement, not a code-level reveal. No line mentions 'adapted_handler', the else-branch, the line rename, or any solution detail beyond problem_statement. Remaining vocabulary (List[int] token traces, PSeq, parallel target_mode/declines columns, adapt_token/wrap_token deep models) is Nagini modeling machinery, not gold-edit disclosure. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
