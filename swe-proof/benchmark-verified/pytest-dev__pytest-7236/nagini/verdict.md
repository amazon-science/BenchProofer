# P2 adversarial audit — pytest-dev__pytest-7236

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
- **machine verdict:** Faithfulness-break attack on nagini pytest-dev__pytest-7236. Modeled function decide_teardown maps to the post-patch recording branch in TestCaseFunction.runtest (src/_pytest/unittest.py:223, non-async else): real decision `usepdb and not _is_skipped(self.obj)` where _is_skipped(obj)==bool(getattr(obj,'__unittest_skip__',False)). Model: teardown_recorded == (postmortem_mode and not skip_marker_set(skip_marker)) with skip_marker_set(m)==(m!=0).

The R-abstraction is a truthiness bijection: skip_marker==0 <-> marker absent-or-falsy, skip_marker!=0 <-> present-and-truthy, so (m!=0) <-> bool(getattr(...)). Verified this is exact and not too-strong on the abstracted domain:
- axiom_check.py (G-AX) runs the REAL bool(getattr(obj,'__unittest_skip__',False)) over 23 boundary values (absent + all falsy [False,0,0.0,'',None,[],{},set(),(),0j] + all truthy) + 20000 fuzz cases, reconstructs the full usepdb x marker grid against the postcondition -> exit 0. Ran it: passes. The _carrier() mapping is derived independently of _is_skipped, so the check is not a tautology.
- nagini_verify.sh model.py -> Verification successful (11.4s). model_prepatch.py (drops the `not _is_skipped` guard, records whenever usepdb) fails on the discriminating F2P input usepdb & skipped, confirming the spec is not weak and discriminates in the correct direction.
- Confirmed real base_commit c98bc4cd runtest via git show: pre-patch `if self.config.getoption('usepdb'):`, gold hunk adds `and not _is_skipped(self.obj)`. Matches mapping.

Domain scoping is honest: async path (is_async_function) and the setattr(tearDown, lambda:None) neutralisation are outside the modeled object (which carries only postmortem_mode, skip_marker, teardown_recorded). decide_teardown is scoped to the sync recording branch, matching the sync F2P test test_pdb_teardown_skipped. Both directions pinned (F2P: usepdb&skipped -> not recorded; P2P: usepdb&not-skipped -> recorded).

No within-domain input makes the model disagree with the real callee. Spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3): leakage / gold-reconstruction. Scope = solver-facing SPEC VIEW (model.py with impl region elided), judged against the PUBLIC problem_statement (not hints_text).

Gold edit (src/_pytest/unittest.py): `if self.config.getoption("usepdb"):` -> `if self.config.getoption("usepdb") and not _is_skipped(self.obj):`, plus new helper `_is_skipped(obj) = bool(getattr(obj, "__unittest_skip__", False))` (and two behaviour-identical getattr->_is_skipped refactors at unittest.py:44,92).

What the PUBLIC problem_statement already discloses: title 'unittest.TestCase.tearDown executed on skipped tests when running --pdb'; a repro showing an @unittest.skip test's tearDown runs (NameError) under --pdb but is correctly skipped without --pdb; explicit 'I would have expected the test to be skipped, even with --pdb.' => the required behaviour (under --pdb, a skipped test's teardown must NOT run) is fully public input.

Spec view content (generated via markers.spec_view over the nagini backend): a fully-abstracted model. Postcondition: teardown_recorded == (postmortem_mode and not skip_marker_set(skip_marker)); pure skip_marker_set(m) == (m != 0). Carriers are abstract (postmortem_mode:bool, skip_marker:int, teardown_recorded:bool). The spec view contains NO repo-specific identifiers: no _is_skipped, no __unittest_skip__, no usepdb, no getattr, no runtest/TestCaseFunction, no file path or line numbers. It legitimately restates the desired behaviour the problem_statement already demands; a spec stating desired behaviour is not leakage, and it gives away no localization (file/helper/line) beyond the public report.

Repo-identifying detail (_is_skipped, __unittest_skip__, unittest.py:223, the getattr default-absent lookup) lives only in mapping.md / refinement.md / meta.json, which are auditor-only artifacts, NOT in the solver-facing spec view.

Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already specifies. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
