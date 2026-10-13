# P2 adversarial audit — django__django-13128

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
- **machine verdict:** Faithfulness-break attack on django__django-13128 (nagini). Modeled function resolve_kind / deep model resolved_kind vs real CombinedExpression.resolve_expression (post-patch). NOTE: bundle references /work/patch.diff but patch.diff is ABSENT from the bundle dir; I reconstructed the gold patch from data/swe_bench_verified/test.jsonl and applied it to a base_commit (2d67222) worktree. Drove the REAL patched Django resolve_expression over the FULL 144-case enumeration {already_temporal}x{is_sub}x{6 type codes}^2, reading the dispatch decision (which wrapper newly created) exactly as axiom_check.py does: 144/144 cases match resolved_kind, 0 mismatches. Additional adversarial abstraction probes with distinct non-enumerated concrete types (IntegerField-FloatField, CharField-IntegerField -> both plain; DurationField-FloatField/DurationField+IntegerField -> DurationExpression; Value-no-output-field (T_UNKNOWN) cases -> plain; Date+Date ADD -> plain) all agree with the model. The abstraction (5 named type codes + T_UNKNOWN, T_OTHER collapse) is observationally complete because the real dispatch only tests equality against the four named field strings and datetime-set membership; every other concrete type is inert exactly as T_OTHER models. The postconditions pin Result()==resolved_kind(...) fully, and this equals the real callee on every input in the modeled domain. Spec is neither too strong nor drifting. Model verifies under pinned Nagini (Verification successful, 10.3s). No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker 3 (leakage / gold-reconstruction) for django__django-13128 (nagini). I rendered the exact spec view with markers.spec_view(model.py, NaginiBackend().language): the impl region is elided ('...') and only the docstring + axioms(empty) + pure region (T_*/K_* enumerations, is_datetime_type/wants_duration/wants_temporal/resolved_kind) + pre/post-conditions are visible.

Leakage standard check: does the spec view reveal the gold EDIT beyond the public problem_statement? No.
- The problem_statement already states the goal ('make temporal subtraction work without ExpressionWrapper') and shows the FieldError: mixed-types symptom. The intended fix (infer the temporal/duration output type at resolve time) is implied by the public statement itself.
- The spec view describes only the required BEHAVIOUR in a fully abstracted integer-code model: operand output types as codes {T_UNKNOWN..T_OTHER}, connector/isinstance as bools, result as a kind code {K_PLAIN,K_DURATION,K_TEMPORAL}. It is explicitly framed 'as desired behaviour, not as an edit.'
- Token scan of the rendered spec view for repo-specific identifiers found NONE of: resolve_expression, expressions.py, CombinedExpression, DurationExpression, TemporalSubtraction, output_field, get_internal_type, FieldError, ExpressionWrapper, self.connector, self.SUB, isinstance, DateField/DateTimeField/TimeField/DurationField, base_commit. The only 'django' occurrence is the public instance id 'django__django-13128' in the docstring title (already public).
- The spec view does NOT disclose the file/function/class to change, the line numbers, the class names produced, or the diff text. It does not distinguish that the dispatch moved from as_sql to resolve_expression, nor reference the base_commit or the second (as_sql native-duration) hunk. The behavioral spec IS the legitimate correctness oracle; describing what a correct fix must satisfy is by-design, not a leak of the edit.

A consumer given only this spec view still must (a) locate CombinedExpression.resolve_expression in django/db/models/expressions.py, (b) know it operates on output-field internal-type strings/isinstance/connector, and (c) construct the actual DurationExpression/TemporalSubtraction dispatch — none of which the spec view supplies beyond what the public problem_statement/general Django knowledge would. G-LEAK in meta.json is pass; my independent render/scan concurs. No hints_text exists for this instance.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
