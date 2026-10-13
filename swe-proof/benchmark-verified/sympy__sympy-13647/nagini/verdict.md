# P2 adversarial audit — sympy__sympy-13647

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-13647 nagini bundle. The modeled function insert_row's postcondition pins Result()[j] == output_value(...) for the corrected banding: j<pos -> self_row[j]; pos<=j<pos+other_cols -> other_row[j-pos]; else -> self_row[j-other_cols]. This is byte-identical to the gold-patched entry(i,j) in MatrixShaping._eval_col_insert (patch.diff: 'self[i, j - other.cols]').

Method: built the real repo at base_commit 67e3c956 in a /tmp worktree, applied the gold patch, and ran an EXHAUSTIVE comparison of model.py's output_value banding against the REAL patched _eval_col_insert result (via _MinimalMatrix._new/__getitem__, the same ShapingOnlyMatrix the repo test uses) over the FULL modeled domain: cols 0..7, other_cols 0..7, every valid pos in [0,cols], rows 1..3 — cell by cell. Result: 0 divergences. The bundle's own axiom_check.py also passes against the patched repo (issue example eye(6).col_insert(3,6x2) + 13 boundary + 4000 fuzz, plus _new value-preservation over 2000 fuzz shapes).

Preconditions faithfully mirror the state _eval_col_insert receives: col_insert (unchanged) clamps pos into [0,cols] and raises ShapeError if rows mismatch, so 0<=pos<=cols and rows==other.rows are exactly the already-validated state; the model takes these as Requires, not an over-strengthening. Row-independence (entry reads only self[i,.]/other[i,.], never moves values across rows) justifies the 1-D List[int] per-row abstraction; entries abstracted to int is faithful for the integer-matrix F2P test. No input found where the modeled function disagrees with the real callee. same-spec check: exit 0 (byte-identical spec).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Instance sympy__sympy-13647. Gold edit: in sympy/matrices/common.py, _eval_col_insert.entry right band changes `self[i, j - pos - other.cols]` -> `self[i, j - other.cols]`.

Spec view examined = the frozen (non-impl) regions of model.py confirmed by same-spec (exit 0): module docstring, new_matrix_cell axiom (@ContractOnly), output_value pure region, and insert_row pre/post-conditions + loop invariants. Compared against the public problem_statement (which names Matrix.col_insert(), gives the exact repro eye(6).col_insert(3, 2*ones(6,2)), shows the wrong output, and explains the trailing identity block is misplaced across rows).

Finding: NO-LEAKAGE.
- The spec's output_value encodes the CORRECT three-band semantics, including right band `self_row[j - other_cols]`. Encoding intended behaviour is exactly a specification's job; the correct col-insert semantics (trailing original columns shift right by the inserted block width, staying in their rows) are directly derivable from the public problem_statement + ordinary col_insert domain knowledge. This does not localize the fix beyond the public issue.
- The spec view contains NO repo file/line pointers (no `sympy/matrices/common.py`, no `_eval_col_insert`, no line 86), NO mention of the pre-patch buggy formula `j - pos - other_cols`, and NO 'this is the bug / discriminating clause' narrative. All three bands are stated neutrally and symmetrically.
- The gold-edit disclosures (pre-patch formula `j - pos - other_cols`, the 'discriminating clause is the right band' framing, file:line 82-88/90 provenance, prepatch model reproducing the bug) live ONLY in the audit artifacts refinement.md / mapping.md / meta.json.deep_model_references — these are auditor-facing, NOT part of the solver's spec view.

Conclusion: the spec view specifies correct behaviour without revealing the edit's location, its pre->post delta, or which line to change — nothing beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
