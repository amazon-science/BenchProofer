# P2 adversarial audit — pytest-dev__pytest-10081

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pytest-dev__pytest-10081 nagini bundle. The modeled function postpone_teardown(item, under_debugger) specifies Result() == under_debugger and not (marked_skipped(obj_skip) or marked_skipped(class_skip)), with marked_skipped(flag)==flag. This is a total function over the finite input domain (obj_skip, class_skip, under_debugger) in {T,F}^3.

Real callee (post-patch, src/_pytest/unittest.py:318-319): skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj); guard = self.config.getoption("usepdb") and not skipped, where _is_skipped(obj)=bool(getattr(obj,"__unittest_skip__",False)) (line 412).

Abstraction faithfulness verified on every axis:
- under_debugger <-> getoption("usepdb"): --pdb is registered action="store_true" (debugging.py:44-49), so the option is a genuine bool; identity refinement is exact.
- obj_skip/class_skip <-> _is_skipped(self.obj)/_is_skipped(self.parent.obj): _is_skipped returns the boolean __unittest_skip__ flag; recorded facet is exactly that boolean.
- marked_skipped deep model == real _is_skipped: ran axiom_check.py against the REAL _pytest.unittest._is_skipped with genuine @unittest.skip decorators on classes/methods in all boundary combos (had to stub _pytest/_version.py to import the module) -> 'G-AX OK ... over all 8 (obj_skip, class_skip, usepdb) combinations; pre-patch guard diverges exactly on the class-only skip case under --pdb.' exit 0.

The modeled decision equals the real post-patch guard on all 8 combinations. The auxiliary Ensures clauses (Implies(class_skip, not Result()), etc.) are logical consequences of the main equality, not extra constraints, so the spec is not too strong. The omitted assert isinstance(self.parent, UnitTestCase) has no observable effect (self.parent is always a UnitTestCase via UnitTestCase.collect). No input exists where the modeled function disagrees with the real callee. Verdict: FAITHFUL, no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction assessment for the solver-facing spec view (model.py spec region: docstring + preconditions + postconditions of postpone_teardown, with the impl-start/impl-end region excluded).

The public problem_statement already fully discloses the fix intent: it reports that tearDown() runs for classes marked with unittest.skip under --pdb, states it is 'Identical to #7215, but with skip() on the class level rather than the function level', and shows the expected outcome (the class-skipped test must be treated as skipped, so tearDown must not run). Thus the desired behavior 'suppress teardown postponement when EITHER the callable OR the enclosing class is skipped' is public knowledge.

The spec view encodes exactly that behavior and nothing more: docstring says teardown is postponed iff debugger active AND neither the callable nor the enclosing class is marked skipped; the postconditions state Result() == (under_debugger and not (marked_skipped(obj_skip) or marked_skipped(class_skip))) plus corollaries Implies(class_skip, not Result()) and Implies(obj_skip, not Result()). The two boolean facets (obj_skip, class_skip) combined with OR is a direct restatement of the publicly-stated callable-OR-class symmetry, not a disclosure of the private diff.

No repo-specific edit mechanics (self.parent.obj, _is_skipped, the added 'assert isinstance(self.parent, UnitTestCase)', src/_pytest/unittest.py locations) appear anywhere in the solver-facing spec view. Those details live only in mapping.md and refinement.md, which are audit/oracle artifacts (explicitly stated to reference patch.diff verbatim for the refinement audit, 'not referenced from the consumer spec view') and are not part of the spec presented to a solver. Therefore the spec does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
