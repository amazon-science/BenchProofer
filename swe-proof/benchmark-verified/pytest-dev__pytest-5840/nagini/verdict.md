# P2 adversarial audit — pytest-dev__pytest-5840

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 13 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 13 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on nagini/pytest-dev__pytest-5840. Question: is the spec too strong / does the modeled function disagree with the real callee on any input?

Modeled function conftest_dedup_key requires the result to (a) carry the canonical location string of the input (ToSeq(Result())==canonical(Old(ToSeq(loc)))) and (b) hold the abstract lookup_recognised token. Real callee = gold _importconftest key computation `key = Path(str(conftestpath)).resolve()`.

Evidence the spec does NOT diverge from real behavior:
- model.py verifies (exit 0, 12.5s): recognised convention make_key(loc,True) discharges both clauses.
- model_prepatch.py FAILS exactly on the lookup_recognised postcondition (make_key(loc,False)) — the spec genuinely discriminates the load-bearing change (unrecognised py.path.local key convention is rejected), so it is not vacuous/too-weak in the wrong direction.
- axiom_check.py PASSES (exit 0) on 10 boundary + 2000 fuzz REAL files, incl. the actual F2P subdir names test/tests (lowercase — proves discriminator is NOT casing), case-insensitivity issue scenarios (JenkinsRoot, Foo, imageProcessing): (i) both conventions carry IDENTICAL canonical location string str(Path(str(p)).resolve()); (ii) a recomputed Path(...).resolve() lookup HITS a dict keyed by the recognised key; (iii) same lookup MISSES a dict keyed by the unrecognised unique_path/py.path.local key despite identical string.

Clause (a): canonical is defined as exactly str(Path(str(loc)).resolve()), i.e. the gold key's own string — no input can make the gold key's string differ from canonical.
Clause (b): the gold key IS the recognised convention (pathlib.Path resolved identically at lookup), so lookup_recognised holds for the real key on every checked input. The gold patch therefore always satisfies both postconditions; there is no input where the spec rejects the real correct behavior.

The discriminator is correctly modeled as the membership-recognition EFFECT (unforgeable @ContractOnly @Predicate token — no body, cannot be Fold'd or laundered across value-equal copies), matching the real repo where the two key kinds carry identical strings but incompatible __hash__/membership. Spec is not too strong; no diverging input exists. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage bar: does the consumer spec view reveal the gold edit beyond the public problem_statement (NOT hints)? Public problem_statement is only a Windows bug report ('the path was converted to lower case' -> ModuleNotFoundError); it names the casing symptom, not the fix. Gold edit: replace `unique_path(conftestpath)` (py.path.local key via normcase(realpath(...))) with `key = Path(str(conftestpath)).resolve()` (pathlib.Path key) and delete the `unique_path` helper.

I rendered the actual consumer spec view via markers.spec_view(src, nagini): impl region is elided to `...` before submission, so `result = make_key(loc, True)` is NOT visible. The visible spec (docstring + axioms + pre/post) contains NO concrete gold-patch token: no `Path`, `resolve`, `pathlib`, `unique_path`, `py.path.local`, `normcase`, or `realpath` appears anywhere. The edit is abstracted into a 'recognised convention' vs 'unrecognised convention' and an unforgeable `lookup_recognised` token whose defining property is a genuine behavioral spec (a recomputed-key lookup must HIT the stored entry). Notably the spec deliberately DIVERGES from the public casing framing, stating explicitly that the discriminator is dict-membership recognition (hash/class mismatch), NOT letter casing — so it does not even echo the public symptom, let alone reconstruct the fix.

The concrete binding recognised_convention=True <-> Path(...).resolve() lives only in mapping.md / axiom_check.py, which are audit-side artifacts and NOT part of the consumer spec view. The impl collapsing to make_key(loc, True) is intrinsic to the twin-artifact format (a spec constrains its impl) and is elided from the solver's view regardless; it is not concrete gold-edit reconstruction. A solver reading only the spec view learns the abstract correctness property (key must be recognised by a recomputed-key membership test) but nothing that maps it to the repository's `Path().resolve()`-replacing-`unique_path` change. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
