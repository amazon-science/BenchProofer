# P2 adversarial audit — django__django-14580

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 6 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 6 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for django__django-14580 (nagini). The modeled function serialize_type(value_tag) abstracts TypeSerializer.serialize (django/db/migrations/serializer.py). Precondition restricts value_tag to base_ref_tag()=1 or other_ref_tag()=2 — the two distinguished special_cases rows (models.Model and type(None)). Postconditions: base tag -> text = code points of 'models.Model' AND imports = code points of 'from django.db import models'; other tag -> text = 'type(None)' AND empty imports.

Verified against the REAL repo:
1. Decoded PSeq code points: base_ref_text()='models.Model', base_ref_directive()='from django.db import models', other_ref_text()='type(None)' (all exact).
2. worktree holds the post-patch serializer (row0 = (models.Model, 'models.Model', ['from django.db import models']); row1 = (type(None), 'type(None)', [])); confirmed the gold diff [] -> ['from django.db import models'] over the base_commit state.
3. Executed the real callee: MigrationWriter.serialize(models.Model) -> ('models.Model', {'from django.db import models'}); MigrationWriter.serialize(type(None)) -> ('type(None)', set()). These match the spec postconditions exactly.

Refinements are faithful: type-object reference identity ('case is self.value') <-> integer tag equality (only which distinguished row matches is observable); str <-> List[int] code points; the at-most-one-element directive set <-> the directive's code-point sequence (empty list = empty set); the special_cases list-of-triples <-> three index-aligned columns built inside the function, exactly where the gold edits. The precondition narrowing to the distinguished-type path is a legitimate scope restriction (the unmodeled module-based fall-through serializer.py fall-through is unchanged by the patch and is the complement of the F2P scenario test_serialize_type_model), not an over-strong spec. No input in the precondition domain {1,2} makes the modeled function disagree with the real post-patch callee; there is no diverging input. Spec is not too strong and does not drift. same-spec on the bundle model returns exit 0.

(Note: this G-PANEL-2 faithfulness verdict is independent of the recorded G-PANEL-1 spec-too-weak FAIL; that is a separate weakness finding and outside this attacker's scope.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view does not leak the gold edit beyond the public problem_statement. Gold edit: serializer.py TypeSerializer.serialize special_cases row (models.Model, 'models.Model', []) -> (..., ['from django.db import models']). The problem_statement already discloses ALL of this: the failure is 'NameError: name models is not defined' in a generated migration; the reporter's models.py literally begins with 'from django.db import models'; models.Model appears in bases; and expected behavior is 'a migration file that is valid Python' i.e. the missing models import must be emitted. Thus the exact directive string, the type (models.Model), and the required behavior (serializing models.Model must surface 'from django.db import models', while type(None) needs none) are all derivable from the public statement, not newly revealed by the spec. The special_cases table, first-match scan, and the type(None) companion row are behavior-region modeling scaffolding (identical in model_prepatch.py, which FAILS this postcondition) describing the function under specification rather than the diff. No individual spec-view line encodes the []-vs-['from django.db import models'] change more than the bug report's stated expected fix does. Verified spec region byte-identical to bundle by construction (atk.py is a copy of model.py); adversary same-spec CLI could not be exercised here due to swebench_unified not being importable in the invoked python env, but this is immaterial to the leakage judgment.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
