# P2 adversarial audit — astropy__astropy-12907

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
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) on astropy__astropy-12907 nagini bundle. Modeled function parallel_dependency_matrix models the PATCHED _cstack (ndarray x ndarray branch, separable.py:219): row i<lr = left[i] ++ zeros(rc); row i>=lr = zeros(lc) ++ right[i-lr]. Base commit d16bfe05 carries the buggy '=1'; the model targets the gold-patched '=right', which is correct for the verify=>resolved claim (refinement.md/mapping.md A4 is the fix). same-spec exit 0 confirms spec-region integrity.

Fidelity evidence: (1) bundle axiom_check.py passes (11 boundary + 20000 fuzz pairs + 4 real F2P separability_matrix nested models). (2) Independent 200k-pair fuzz over the realistic domain (extents>=1, 0/1 matrices) vs a faithful numpy reimplementation of the patched branch: 0 mismatches. (3) Non-0/1 entries ([[2,0],[0,3]] & [[5]]) copied exactly, matching the real callee — the int 0/1 carrier is a precision-independent stand-in since the patch is a pure copy (no arithmetic).

The only divergence found is at degenerate extents (rr=0, lr=0, empty operands): there the REAL callee itself raises ValueError (broadcast failure) while the model returns a value. But coord/separability matrices always have >=1 row and >=1 column, so these inputs never occur and lie outside the real callee's operating domain — not a genuine faithfulness defect. The precondition (is_grid, extents>=0) does not exclude rr=0/lr=0, but on those the real function crashes rather than producing a differing value, so the model never disagrees with the real callee on any input the callee actually processes. No spec drift / over-strengthening detected within the operating domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit of the nagini spec view for astropy__astropy-12907.

Spec-view provenance verified: recomputed spec_view(model.py, NaginiBackend.language) sha256 = 847d463bd5ba4d41f839e094db22fe8c4582f11c3a4ade0034105a9956e13059, matching meta.json G-HYGIENE region_hashes.spec_view. The spec view = module docstring + axioms(empty) + pure helpers (zeros, is_grid, expected_row) + pre/post-conditions of parallel_dependency_matrix; the impl region is elided.

Gold edit: astropy/modeling/separable.py:245 in _cstack, `cright[-right.shape[0]:, -right.shape[1]:] = 1` -> `= right` (lower-right block copies the ACTUAL right matrix instead of a constant all-ones fill).

Public problem_statement already discloses the full desired behavior: it exhibits the buggy output for `m.Pix2Sky_TAN() & cm` with a lower-right 2x2 all-True (all-ones) block, calls it a bug, and shows that nesting the diagonal `cm` should keep inputs/outputs separable — i.e. the corrected lower-right block must reflect the actual right matrix (its diagonal), not a constant. Thus 'lower-right block = actual right, not all-ones' is derivable purely from the public statement.

Spec view discloses nothing beyond that: it is entirely abstract-model prose over PSeq[PSeq[int]] block placement (expected_row: i>=lr row == zeros(lc) ++ right[i-lr]). It never names separable.py, _cstack, numpy, np.hstack, .shape as a repo API, or the `= 1`->`= right` diff line. Token scan of the spec view: only 'astropy' (instance-id in docstring header, public) and 'shape' (abstract matrix shape `lr x lc`, not a numpy attribute) appear; no repo symbols. The phrase 'never a constant all-ones block' restates the pre-patch bug already visible in the problem_statement's buggy matrix and adds no edit-level information.

All repo-level identifiers (_cstack, file:line, the verbatim diff) live only in mapping.md / refinement.md / meta.json, which are NOT part of the consumer-facing spec view. G-LEAK in meta records spec view clean; independent re-derivation agrees.

Conclusion: the spec view specifies the target behavior at the abstract-model level, fully derivable from the public problem_statement, and does not leak the gold code edit beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
