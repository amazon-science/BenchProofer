# P2 adversarial audit — django__django-11433

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
- **machine verdict:** Faithfulness verified for django__django-11433 (construct_instance). The worktree at base_commit 21b1d23912 carries the post-patch (gold) code: the 'leave defaults' guard is the 3-conjunct `f.has_default() and value_omitted_from_data(...) and cleaned_data.get(name) in empty_values`, exactly what the gold patch.diff introduces and exactly what model.py models via write_value = selected and not (has_default and omitted and value_empty).

Exhaustive comparison: enumerating all 16 boolean input combinations (selected, has_default, omitted, value_empty), the modeled write_value agrees with the real repo's 'was save_form_data called' decision on EVERY input (divergences: []). Real repo: not-selected -> continue (not written); has_default&omitted&value_empty -> continue (not written); else -> written. This is precisely write_value.

Type-refinement fidelity: the four carriers abstract unchanged bool-valued primitives (has_default(), value_omitted_from_data(...), and the `in empty_values` membership over EMPTY_VALUES=(None,'',[],(),{})). For selected fields, candidacy requires f.name in cleaned_data so cleaned_data.get(name) is well-defined; value_empty is only decision-relevant when the field is write-eligible, and write_value(False,...)=False correctly models the earlier `continue`. The FileField deferral changes only WHEN save_form_data runs, not WHETHER, so it is genuine identity for the modeled 'whether-written' observation. No axiom is consumed (the changed op is modeled deeply), so there is no axiom over-strength to exploit.

Model verifies with pinned Nagini (exit 0, 17.18s). The spec is neither too strong nor drifting from real behavior; no diverging input exists. G-AX/axiom_check truth-table and membership assertions are consistent with the real EMPTY_VALUES semantics. Note: the same-spec CLI could not run here (swebench_unified not importable from the awsbatch pyenv), but atk.py was a byte-copy of the bundle model.py, and faithfulness (spec-vs-repo) does not depend on that tool.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Audited the sealed spec view: recomputed spec_view region hash = c15969430021a0930c0a2588564960282d2305b53eb2ff32e8db1bea77dd7f3d, byte-identical to meta.json record. Gold edit adds guard conjunct `cleaned_data.get(f.name) in form[f.name].field.empty_values` (leave-at-default only when has_default AND value_omitted_from_data AND cleaned value in empty_values). Substring scan of spec_view for gold-diff solution vocabulary — empty_values, value_omitted_from_data, cleaned_data, construct_instance, add_prefix, has_default(), .get(, form.data, form.files, f.name — ALL ABSENT. Only match 'widget' occurs once in generic Django-forms prose ('the widget reports the value as omitted'), not the specific .widget.value_omitted_from_data(...) call. The spec models behavior abstractly via boolean carriers (selected/has_default/omitted/value_empty) and states the desired rule (leave at default iff has_default & omitted & cleaned-value-empty; otherwise write). Stating desired behavior is the spec's legitimate role, and the public problem_statement already requests the substance ('Allow cleaned_data to overwrite fields default values'). No spec-view line reconstructs the gold code edit beyond problem_statement. Consistent with recorded G-PANEL-3 pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
