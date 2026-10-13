# P2 adversarial audit — django__django-15863

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-15863 nagini bundle. The load-bearing spec is reconstruct_digits's postcondition ToSeq(Result()) == ToSeq(text), which models the gold fix-path reconstruction (input_val = str(text); d = Decimal(input_val)) as the IDENTITY on the value's significant-digit sequence (Decimal.as_tuple().digits, the R-carrier). I tried to exhibit an input where the modeled identity disagrees with the real callee Decimal(str(value)) and found none.

Evidence:
- Model verifies under pinned Nagini (11.48s); same-spec passes (byte-identical spec region); G-AX axiom_check.py exits 0.
- Independent replay of the REAL callee Decimal(str(value)) vs identity-on-digit-tuple: 200,000 fuzz Decimals (1-40 random digits, exponents -50..50, both signs) -> 0 mismatches on both digit-tuple equality AND value equality. Boundary/special values (09.000, 1E+2, 1.230, -0, Infinity, -Infinity, NaN, sNaN, NaN123, -NaN, 1E-999999999, 35-digit values) all preserve the digit tuple exactly.
- Confirmed Decimal(str(v)) construction ignores decimal-context precision (tested under localcontext prec=2 on the 27-digit F2P value: still exact), so the identity model is genuinely exact, not silently context-rounded.
- Discriminating (G-DIFF) behavior verified live: on the F2P input Decimal('123456.123456789012345678901') the fix path preserves all 27 digits; the pre-patch repr->float fallback collapses to 15 digits (123456.123456789). model_prepatch.py builds narrowed_to_significand and fails the postcondition, so the spec correctly senses the change without overclaiming.

The lossy alternative (narrowed_to_significand) is modeled deeply and only A-referenced/validated by G-AX, never consumed as an axiom, so it cannot smuggle in strength. No input in the abstraction domain (Decimal / numeric value -> significant-digit sequence) makes the modeled function disagree with the real repo reconstruction. The spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is `input_val = repr(text)` -> `input_val = str(text)` in django/template/defaultfilters.py. The public problem_statement already states the desired behaviour and failure mechanism ('floatformat drops precision for Decimal', 'Decimal numbers are converted to float instead', plus the PR link). Reviewed the actual nagini spec_view (impl elided) produced via markers.spec_view + NaginiBackend.language: docstring + pure functions (significand_budget/narrowed_from/narrowed_to_significand) + pre/post-conditions of reconstruct_digits. Token scan of the spec view: `str(`, builtin `repr`, `input_val`, `Decimal`, `floatformat`, `defaultfilters`, `patch`, `.diff` are all ABSENT. The only 'repr' hits are substrings of 'representable'/'represent' in prose, not the Python builtin. The spec pins behaviour abstractly over List[int]/PSeq[int] (exact identity on the digit sequence vs. lossy binary-significand collapse), which is a faithful restatement of the publicly-stated desired behaviour, not a disclosure of the concrete source-level repr->str edit, file, or branch. Abstraction level does not exceed what problem_statement already discloses. No spec-view line reconstructs the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
