# P2 adversarial audit — sympy__sympy-19783

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-19783 nagini bundle. Two modeled functions: identity_mul (== IdentityOperator.__mul__) and dagger_mul (== Dagger.__mul__, new post-patch method). Both validated against the REAL callees on the gold-patched worktree (base_commit 586a43201d, sympy 1.7.dev; post-patch source byte-identical to model's documented hunks).

Enumerated all 4 operand kinds directly against the real methods:
  identity_mul: kind0 I*O=O (collapse, model is_mul=False OK); kind1 I*I=I (collapse, False OK); kind2 I*Dagger(O)=Dagger(O) (collapse, False OK); kind3 I*x=x*I (product, is_mul=True OK).
  dagger_mul: kind0 Dag*O=Dagger(O)*O (product, True OK); kind1 Dag*I=Dagger(O) (collapse, False OK); kind2 Dag*Dag=Dagger(O)**2 (product, True OK); kind3 Dag*x=x*Dagger(O) (product, True OK).
Every model prediction matches the real result; result_kind matches the surviving operand's kind on every collapse.

Abstraction soundness beyond representatives: the real __mul__ methods branch ONLY on isinstance(other,(Operator,Dagger)) and isinstance(other,IdentityOperator). The kind partition {0,1,2,3} is defined by exactly those isinstance tests (real_kind orders IdentityOperator<Operator first, Dagger not Operator), so all members of a kind take the identical branch — the per-kind model extends faithfully to every operand, not just one witness. is_mul==True is definitionally the Mul(self,other) case; scalar edge cases (I*0, I*3, I*x all == Mul(I,other)) and Dagger(I)==I (correctly kind 1) confirmed. No operand escapes the partition.

The postconditions are precisely as strong as the real behavior: is_mul == not(is_operator_like or is_conjugate) for identity_mul and is_mul == not is_identity for dagger_mul both hold exactly. same-spec check on the bundle model returns exit 0 (SAME). No diverging input exists — spec is FAITHFUL, not too strong and not drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view hash recomputed = f6288dc1688fa246a745c472ef7db36703f7060c3db2325263fc1c90eb6f5bc1, byte-identical to frozen meta.json spec_view hash; judging the real spec. Mechanical G-LEAK screen (leakage.screen against the frozen problem_statement + gold patch) passes with zero hard_failures: no diff markers, no reproduced gold-patch line, no patched file/module path (operator.py/dagger.py), no spec-view identifier or comment embedding a patched repo symbol, no bug/fix narration. Distinctive changed symbol detected is only 'print_contents_latex' (a hunk section-header artifact, absent from the spec view). The dunders __mul__/__new__ and public classes IdentityOperator/Dagger (already named in problem_statement) are not disclosed as edit locations. Semantic check: the gold patch is two-site (site 1 Dagger.__mul__: Dagger(O)*I==Dagger(O), which IS the public problem statement; site 2 IdentityOperator.__mul__ Dagger disjunct: I*Dagger(O)==Dagger(O), which is NOT in the public problem statement, only in hidden F2P test_identity). The spec view describes BOTH directions in abstract kind-tag/behavioral terms. This is not gold-edit reconstruction: it names no repo file/method/diff mechanics and narrates behaviour as desired-behaviour, not as an edit. Encoding the second (I*Dagger) direction is required for the spec to be faithful to the F2P oracle and to resolve (G-RESOLVE); a spec omitting it would be unfaithful, not cleaner. Describing the correctness target that the hidden tests enforce is the legitimate role of a behavioral spec and does not constitute leaking the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
