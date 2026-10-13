# P2 adversarial audit — django__django-15380

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attack goal: show the spec is too strong / drifts from the real callee (modeled function disagrees with the real repo on some input). Result: no divergence found — spec is FAITHFUL.

Real repo verification (worktree @ base_commit 71e7c8e73712...): generate_renamed_fields() body at autodetector.py:824-828 has pre-patch `new_model_state = self.to_state.models[app_label, old_model_name]`; applied patch.diff changes it to `[app_label, model_name]` — exactly the gold fix in refinement.md/mapping.md.

Model ↔ callee correspondence (refinement: app_label fixed, (app,name) tuple key → int name token, ModelState → int descriptor token):
- prior_name(corr, later) = corr[later] if later in corr else later  ==  renamed_models.get((app,model_name), model_name). axiom_check.py confirms prior_name == dict.get(k,default) over 4 boundary + 50000 fuzz configs (exit 0).
- Result()[0] == prior_registry[prior_name(...)]  ==  from_state.models[app, old_model_name] (unchanged lookup).
- Result()[1] == later_registry[later]  ==  to_state.models[app, model_name] (the corrected + line).

Preconditions faithfully mirror the real callee's implicit domain, not a stronger one: the real code subscripts to_state.models[app,model_name] and from_state.models[app,old_model_name] UNGUARDED, so it assumes exactly model_name∈to_state and old_model_name∈from_state — precisely `later in later_registry` and `prior_name(...) in prior_registry`. On every input in that domain the modeled tuple equals the real (post-patch) callee's (old_model_state, new_model_state) selection. Outside the domain the real callee raises KeyError (no defined behavior to disagree with), so no diverging input exists.

Discriminating check holds: buggy model_prepatch.py (later_registry[old_name]) fails Nagini with 'precondition of later_registry[old_name] might not hold' — the spec correctly does NOT over-promise old_name∈later_registry, matching the real KeyError on renamed models.

Mechanical facts: nagini_verify.sh model.py -> Verification successful (11.13s, exit 0); axiom_check.py -> exit 0; same-spec model.py -> SAME (spec region byte-identical); nagini_verify.sh model_prepatch.py -> fails as expected (exit 1).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage scope: spec view (model.py docstring + Requires/Ensures contracts) vs. the public problem_statement (traceback included, hints excluded).

The public problem_statement already discloses the entire gold edit: its traceback quotes the buggy line VERBATIM ('new_model_state = self.to_state.models[app_label, old_model_name]'), reports 'KeyError: (test_one, mymodel)', pins the crash to generate_renamed_fields when 'renaming a model and field in a single step', and cites the regression commit. The fix (index the later-state registry by the model's LATER name, model_name, instead of the prior name old_model_name) is directly derivable from this public traceback + title.

The spec view (model.py) states the desired behaviour in abstracted int-token form: the later descriptor MUST be looked up by the later name (Result()[1] == later_registry[later]) and the prior descriptor by prior_name. That is precisely what a specification is supposed to encode, and it reveals nothing beyond what the public traceback already implies — the same later-vs-prior-name distinction and the same missing-key consequence. No spec-view line exposes the gold edit beyond problem_statement.

Note: refinement.md and mapping.md quote patch.diff verbatim and name post-/pre-patch lines, but these are the G-EQ refinement/audit documents (permitted to reference the gold oracle), not the solver-facing spec view; leakage is judged on the spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
