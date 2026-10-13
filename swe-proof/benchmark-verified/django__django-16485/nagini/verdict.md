# P2 adversarial audit — django__django-16485

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
- **machine verdict:** Ran all checks against the patched worktree (base_commit 39f83765, gold hunk `if not m and p <= 0:` confirmed). (1) Bare-integer regime (integral & p<=0), which the spec pins end-to-end as int_render and which is the ONLY class the gold patch changes: swept 32,128 cases (ints -2000..2000, +/-10^15, 1E400/1E1000, decimal-string integral forms; p in {0,-1,-2,-3,-5,-10,-50,-100}) -> 0 divergences; model exactly matches real floatformat. (2) Core-layer discriminator '.' in core <=> NOT(integral & p<=0): ~200 mixed inputs, 0 violations. (3) Fix-localisation (post==pre outside bare-integer regime) confirmed by G-AX (exit 0, 100+120 observations) and check_fix_localised. (4) number_format A-reference digit-content preserving. The single genuine drift (else-branch exact fractional digits, e.g. 5555.00 vs 5555.56) is explicitly documented in refinement.md/mapping.md as an A-reference skeleton whose only load-bearing property is core-layer separator-presence; those inputs are patch-unchanged, so gold produces the correct digits via the real unchanged decimal path regardless of the model's zeros, and the drift is discarded under refinement. inf/nan and int(d)-raising huge values fall outside the modeled domain (real filter returns the string repr / int-branch, not the bare-integer model). Within the class that determines resolution (integral & p<=0) the model is exactly faithful. Spec is neither too strong nor drifting in a way that breaks verify=>resolve.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction attacker for django__django-16485 (nagini). Method: (1) recomputed spec_view hash = 100311d1c4653652fab361f35dd0e1c55995f2c3f04177bc2d35c3e4e8602190, byte-identical to meta.json region_hashes.spec_view; (2) ran the real G-LEAK screen (swebench_unified.leakage.screen) against the frozen instance.json patch+problem_statement: passed=True, 0 hard failures, 0 warnings; (3) manual gold-reconstruction probe of the projected spec view.

Gold edit: `if not m and p < 0:` -> `if not m and p <= 0:` in django/template/defaultfilters.py.

Findings on the SPEC VIEW (impl elided): pre-patch operator `p < 0`/`p<0` ABSENT; patched file path (`django/template`), repo symbols (`floatformat`, `defaultfilters`, `number_format`, `mark_safe`, `not m`) ABSENT; no diff markers; no narration (bug/fix/patch/regression). The two 'changed'/'unchanged' occurrences describe behavior of a branch-selection and an unchanged localisation callee, not the edit.

The token `p <= 0` DOES appear in the spec — but as the behavioral boundary of the 'non-positive decimal places' regime that a postcondition must state, not as a reproduction of the diff (the diff line `if not m and p <= 0:` with its repo variables `not m`/`floatformat` is not present). Critically, the public problem_statement already discloses the exact failing case verbatim: floatformat('0.00', 0) and floatformat(Decimal('0.00'), 0) crash — i.e. an integral value at p==0. The spec only pins the correct output (bare integer '0', no separator) for that publicly-known boundary. That is legitimate behavioral specification and does not reveal the edit location, the patched operator's pre-image, or narrate the fix beyond the solver-visible problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
