# P2 adversarial audit — django__django-14034

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
- **machine verdict:** Faithfulness-break attack on django__django-14034 nagini bundle. The modeled function build_widget_attrs abstracts BoundField.build_widget_attrs (boundfield.py:232, post-patch). I checked whether the spec disagrees with the real repo callee on any input.

Method: Ran axiom_check.py (G-AX) against the REAL patched repo at base_commit db1fc5cd worktree (PYTHONPATH-injected) -> exit 0: constituent_marker deep model == real use_required_attribute(initial) and subfield.required over 7x8x2 combos + 20000 random pairs; rendering rule holds; F2P regime-A/B end-to-end match. (2) Independent differential harness: for every combination of subfield-required-flag tuples {(T,F),(F,T),(T,T),(F,F),(T,)} x field.required {T,F} x form.use_required_attribute {T,F} x disabled {T,F}, built real partial MultiValueField forms and compared the spec's predicted observable (aggregate `required` present/absent + per-subwidget `required` attr) against the real bf.build_widget_attrs output. 0 divergences. (3) Edge cases: all-HiddenInput MultiWidget (widget_mark=False -> guard fails, spec_req=-1 matches real <unset>, all sub markers unset) and mixed Hidden/Text subwidgets (spec [False,True] == real [False,True]). (4) model.py verifies under pinned Nagini (exit 0, 14.7s) so this is a live spec.

The three boolean guards (widget_mark, field_required, form_marks) collapse are faithful — field.required, form.use_required_attribute, subfield.required are genuine bools, and only the truthiness of use_required_attribute is consumed in the real `and` chain. The is_partial_multi three-way conjunction is a single bool the real code only tests for truth. zip truncation is a non-issue since Django builds field.fields and widget.widgets equal-length. The tri-state aggregate slot models presence/absence of the `required` dict key correctly (regime A never sets aggregate; the 0/explicit-False state only arises per-constituent where the patch assigns a boolean, matching sub markers 1/0). Disabled marker modeled independently and matches.

No diverging input found; the spec is neither too strong nor drifting. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker 3 (leakage / gold-reconstruction) verdict: NO-LEAKAGE.

Spec view derived via swebench_unified.markers.spec_view(model.py, nagini) — impl region elided to a placeholder; spec regions (module docstring, Constituent/Result2 classes, empty axioms, pure constituent_marker, pre/post-conditions of build_required_attrs) are what the solver sees. Ran swebench_unified.leakage.screen against the frozen instance row (problem_statement ONLY, not hints_text): PASSED, zero hard failures.

Manual gold-reconstruction check:
- Gold edit lives in django/forms/boundfield.py, symbol BoundField.build_widget_attrs; the one distinctive changed symbol is 'build_widget_attrs'. The spec view NEVER names it — the modeled function is renamed build_required_attrs and every repo callee is abstracted (widget_mark for use_required_attribute, is_partial_multi for the hasattr/require_all_fields/MultiWidget conjunction, field_required/form_marks/field_disabled for the attribute reads).
- No diff markers, no patched file path 'django/forms/boundfield.py', no dotted module path, and no verbatim gold-diff line appear in the spec view.
- No bug/fix/regression narration in any spec-view comment or docstring. The docstring explicitly frames the behaviour 'as desired behaviour, not as an edit' and describes the two regimes (A: per-constituent markers when the composite field's per-constituent policy is off; B: aggregate marker otherwise) abstractly.
- Everything the spec abstracts is already grounded in the PUBLIC problem_statement, which itself supplies the MultiValueField/MultiWidget/require_all_fields=False/required=False example, the subfields with individual required flags, and the observed symptom (both sub-inputs wrongly get the HTML 'required' attribute). The regime-A behaviour (mandatory field with optional constituents => constituent renders without the marker) is exactly the fix implied by the ticket's own discussion, not information beyond the public statement.
- The verbatim gold hunk and real repo symbols DO appear in refinement.md and mapping.md, but those are audit-side artifacts, not part of the solver-visible spec view, so they do not constitute leakage into the spec.

Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
