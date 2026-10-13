# P2 adversarial audit — django__django-13089

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
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) FAILS; verdict FAITHFUL. model.py verifies (nagini_verify exit 0, 15s), axiom_check exits 0, pbt SOUND (2 pos controls verify, 5 uniqueness mutants incl. noguard-prepatch rejected). boundary_for_prune(row: Optional[List[int]]) models the changed hunk of DatabaseCache._cull (db.py:270-272 @ 27c09043). Probed every drift candidate: (1) Guard: real 'if last_cache_key:' (truthiness) vs model 'row is not None'. fetchone() of the single-column cache_key_culling_sql SELECT returns None or a non-empty 1-tuple; a non-empty tuple is always truthy regardless of contents, so truthiness == is-not-None exactly. (2) Empty-row edge (falsy-but-not-None, e.g. ()): the ONLY theoretical divergence between truthiness and is-not-None, excluded by precondition Implies(row is not None, len(row)>0); this case is UNREACHABLE in the repo because the culling SELECT projects exactly one column, so the precondition restricts to the reachable domain rather than over-constraining. mapping.md §2 states this correctly. (3) Present row -> Result()==row[0] matches DELETE bound to last_cache_key[0]; absent -> Result() is None matches no-DELETE (the F2P _max_entries=-1 scenario). (4) str->int column refinement preserves the modeled observable (presence + first-column identity) bijectively. No consumed axiom exists, so no callee contract can be too strong. Searched for a diverging input (None, present 1-tuples, empty row); none produces a real/model disagreement on the reachable domain. Spec is faithful and correctly sensitive (prepatch unguarded subscript fails verification).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = abstracted docstring ("maintenance routine"/"store"/"boundary record", no cache/cursor/fetchone/DELETE vocabulary) plus the frozen pre/post-conditions on boundary_for_prune. The two discriminating postconditions — `(Result() is None) == (row is None)` and `Implies(row is not None, Result() == row[0])` — encode exactly 'guard the row subscript on presence; issue no prune when the row is absent.' That is precisely the fix the PUBLIC problem_statement already discloses in full: it prints the exact buggy line `[cursor.fetchone()[0]]`, diagnoses that the cursor 'is not returning any data, so cursor.fetchone()[0] afterwards fails,' and prescribes the remedy ('a simple check to see if it contains data would be enough'). Thus the spec restates, abstractly, only what the problem_statement already gives every solver; it leaks nothing about the gold edit beyond the public statement. No mapping.md/refinement.md content is part of the solver's spec view (those are audit artifacts); even so, the docstring itself carries no concrete edit disclosure. Verdict rests on the leakage criterion (beyond problem_statement, not hints_text — hints_text is empty here anyway).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
