# P2 adversarial audit — django__django-13925

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
- **machine verdict:** Faithfulness-break attack found no divergence. The modeled check_default_pk / advisory_warranted is a total boolean function of five booleans (auto, reuses_ancestor_key_a, reuses_ancestor_key_b, setting_overridden, appconfig_overridden). The real callee Model._check_default_pk (django/db/models/base.py:1298, Django 3.2 == post-patch/gold) evaluates the byte-identical branch condition: pk.auto_created and not (isinstance(pk, OneToOneField) and pk.remote_field.parent_link) and not settings.is_overridden('DEFAULT_AUTO_FIELD') and not app_config._is_default_auto_field_overridden. G-AX (axiom_check.py) enumerates the FULL 2**5 truth table (finite domain, exhaustive — boundary==fuzz) and model predicate == real branch condition on all 32 assignments (exit 0). The int-count (0/1) abstraction of the singleton-vs-empty warning list loses nothing observable: the models.W042 content is constant and identical pre/post-patch. The type refinement (isinstance/attribute reads -> booleans) is validated as an A-reference over the same exhaustive table, with the discriminating auto-created parent-link case (True,True,True) correctly suppressed. Verified independently: pulled Django 3.2 source and confirmed the branch matches; ran axiom_check.py (exit 0); same-spec = SAME; nagini_verify.sh on model.py = Verification successful (7.07s). No input exists where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: nagini django__django-13925. Spec view = model.py with only the impl region elided; mapping.md and refinement.md are audit artifacts OUTSIDE the spec view. Verified the spec_view is byte-identical to meta.json region_hashes.spec_view (both sha256 723e80fd9fa4ce583d007f65e60ca6f52ae9b0bf6405ae1b8d0a85799f55c62d) via markers.spec_view.

Gold edit: add conjunct `not (isinstance(cls._meta.pk, OneToOneField) and cls._meta.pk.remote_field.parent_link)` to Model._check_default_pk in django/db/models/base.py.

Public problem_statement already states the target behavior explicitly and repeatedly: models that INHERIT a manually-specified primary key from an ancestor must NOT raise the models.W042 auto-created-PK advisory ('These models should not use auto-created primary keys! I already defined the primary key in the ancestor of the model.').

Leakage assessment: the spec view models the fix behaviorally, not by reconstruction. The reuse condition is abstracted into two generic booleans reuses_ancestor_key_a/reuses_ancestor_key_b and the pure predicate reuses_ancestor_declared_key ('the key re-uses a concrete ancestor's already-declared key'). This is the SAME behavioral abstraction level as the problem_statement (inherited ancestor PK). The gold edit's implementation-specific tokens — OneToOneField, remote_field, parent_link, auto_created, is_overridden, base.py — appear NOWHERE in the spec view; they live only in mapping.md/refinement.md (out of scope). The two-flag decomposition mirrors the gold's two-conjunct structure but does not reveal what the flags are, so a solver cannot derive the concrete attribute checks from the spec view. No spec-view line exposes the gold mechanism beyond what problem_statement already gives.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
