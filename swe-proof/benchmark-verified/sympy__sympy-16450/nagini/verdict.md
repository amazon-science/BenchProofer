# P2 adversarial audit — sympy__sympy-16450

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for the nagini spec of sympy__sympy-16450. Spec region byte-identical to bundle: `same-spec nagini sympy__sympy-16450 model.py` -> SAME (exit 0); meta region_hashes intact.

Modeled callee: resolve/derived abstracts the UNCHANGED sympy assumption-inference engine `Dummy(name, positive=True, **base).assumptions0` read back via assumptions0. The single changed operation (which declaration reaches the engine: base=stated, not empty) is modeled DEEPLY in the impl, not axiomatized. Tested against the gold-patched worktree at base_commit aefdd023 (posify at simplify.py:254 carries **s.assumptions0).

Independent faithfulness fuzz (200k draws, 87,502 consistent replaced-domain bases + 1,101 inconsistent) — ALL Ensures clauses clean, 0 violations:
(1) precondition add_positive => positive not in base: always holds — a symbol is replaced exactly when is_positive is None, and such a symbol never has 'positive' in assumptions0; sign-stating symbols (prime/real=False/commutative=False) are NOT replaced (correctly out of domain).
(2) fact-preservation Ensures (Forall k in base: derived[k]==base[k]): 0 violations.
(3) added-positivity (positive derived True): 0 violations.
(4) totality (Result() is derived(stated,True), i.e. real posify(s)[0].assumptions0 == engine map, full-dict equality): 0 fidelity violations.
(5) out-of-domain: for inconsistent base+positive the engine raises InconsistentAssumptions and real posify raises in LOCK-STEP, so the no-Exsures totality region is sound because the gold raises identically.

Targeted edge cases (finite, integer, rational, even, real, complex, nonnegative, nonzero, finite=False, zero=False, imaginary=False, negative=False, rational+even, integer+odd) all pass totality+preservation+positivity. Bundle's own axiom_check.py run against the worktree exits 0 (10139 consistent + 115 inconsistent lock-step + 15914 fuzz).

No input found where the modeled function disagrees with the real callee. The resolve axiom is the weakest sufficient contract (closure content left abstract; only fact-preservation, added-positivity, and totality asserted), not too strong. Note: the bundle's separate G-PANEL-1 records a spec-too-WEAK failure (a same-spec impl verifies) — that is the opposite direction and outside this faithfulness lens; the spec is not too strong / does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage assessed on the solver-facing spec view (model.py marked spec regions: docstring + axioms + pure + pre/post-conditions), against the PUBLIC problem_statement (excluding hints_text).

Gold edit: `Dummy(s.name, positive=True)` -> `Dummy(s.name, positive=True, **s.assumptions0)` i.e. keep adding positive=True but ALSO carry the original symbol's stated assumptions (esp. finite) instead of dropping them.

The entire behavioral content of this edit is already fully disclosed in the public problem_statement, NOT just the hints: it states 'Posify removes a finite assumption from a symbol', 'posify should preserve the finiteness assumption', and 'Possibly other assumptions should be preserved as well (integer, rational, prime, even, odd...)'. The spec's abstract description (replace an undecided-sign quantity with a stand-in declared >0 that carries EVERY property the original stated; do not drop or fabricate any) is a faithful re-expression of exactly that public text -- even its illustrative property list ('whole number, rational, even, prime') mirrors the problem_statement's parenthetical.

The spec stays at an abstraction (Dict[int,bool] token maps, POSITIVE/FINITE tokens, an opaque resolve/derived inference engine). It nowhere names posify, Dummy, s.assumptions0, or the **-unpacking mechanism, so it does not reveal the concrete code edit beyond the problem statement.

The literal gold hunk `**s.assumptions0` appears only in refinement.md and mapping.md, which are audit artifacts (the refinement map is expected to quote the gold patch) and are not part of the spec view a solver works from. That does not constitute spec-view leakage.

Verdict: the spec leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
