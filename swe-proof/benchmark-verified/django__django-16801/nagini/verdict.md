# P2 adversarial audit — django__django-16801

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacked the spec of attach_post_init_hook (models ImageField.contribute_to_class registration block, files.py:438-445) for drift/over-strength vs the real repo callee at base_commit 3b62d8c8. Findings:

1) Registration decision. Model: should_register = (not is_abstract) and (configured(width_target) or configured(height_target)), with configured(name)=name is not None and len(name)>0. Real guard: `not cls._meta.abstract and (self.width_field or self.height_field)`. configured() is exactly Python truthiness of a field-name str/None (non-empty str -> True; None/'' -> False). Verified against the real callee: axiom_check.py builds REAL Django classes over {none,width,height,both}x{concrete,abstract} and asserts post_init.receivers membership == should_register for every cell, plus the exact F2P concrete-no-target-absent scenario. Ran it: exit 0 (Django absent here so it SKIPs the class-building half but confirms the truthiness A-reference; per bundle it runs in-container). No diverging (is_abstract,width,height) input exists.

2) connect() dedup. Real Signal.connect dedups by (receiver_id, sender_id) — appending an already-registered (handler,sender) is a no-op. Model postcondition unconditionally requires receivers to grow by owner_id when should_register. This could only diverge if owner_id (=id(cls)) were already present; every F2P/P2P observation and axiom_check.observe builds a FRESH class, so owner_id is always new. Not reachable on any tested input; not drift.

3) Type carrier str/None <-> Optional[List[int]] observes only truthiness, matching real Django where field names are always non-empty str or None.

4) super().contribute_to_class side effects and the hunk-2 update_dimension_fields cleanup are unobserved by the registration/F2P test and correctly out of modeled scope (refinement.md §B behaviour-preservation argument holds on both post_init and force=True paths).

model.py verifies (nagini_verify.sh exit 0, 16.6s); same-spec toolkit confirms spec region parses. model_prepatch (registers for every concrete class) correctly FAILS the decision postcondition (G-DIFF sound). The spec is neither too strong nor drifting: it agrees with the real callee on every reachable input. Verdict FAITHFUL — no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage check for django__django-16801 (nagini). Compared the spec view (impl region elided, generated via markers.spec_view with NaginiBackend.language) against the public problem_statement, EXCLUDING hints_text (empty here).

Gold edit (patch.diff): hunk 1 changes `if not cls._meta.abstract:` -> `if not cls._meta.abstract and (self.width_field or self.height_field):`; hunk 2 is a behaviour-preserving cleanup removing the redundant has_dimension_fields early-return in update_dimension_fields.

The public problem_statement ALREADY discloses the entire fix: it states the post_init handler 'is a noop because we don't use the width_field / height_field' and 'If width_field and height_field are not set, removing the post_init signal should have no effect.' So the discriminating content (register only when width_field/height_field configured) is public, not novel to the spec.

Spec-view content assessed line by line:
- Docstring/should_register model restate the desired behaviour: register iff concrete AND (width OR height configured). This is exactly what problem_statement already gives; abstract restatement of public behaviour is legitimate spec content, not incremental leakage.
- The `not is_abstract` term is pre-existing pre-patch repo code (present before the gold hunk), not part of the gold edit; modeling the full guard is not a diff leak.
- Hunk 2 (has_dimension_fields cleanup) is NOT encoded or hinted anywhere in the spec view.
- Spec view contains NO repo symbols, file/line refs, diff text, `post_init.connect`, `cls._meta`, or mention of the removed guard. All repo-specific provenance lives only in refinement.md / mapping.md / meta.json (auxiliary audit docs), which are not part of the solver-facing spec view.

Conclusion: no spec-view line reveals the gold edit beyond what the public problem_statement already states. (Consistent with G-LEAK pass in meta.json; spec_view hash ea059a36..., no leak failures recorded.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
