# P2 adversarial audit — matplotlib__matplotlib-24026

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for matplotlib__matplotlib-24026 nagini bundle. The spec models the `colors is not None` branch of stackplot (the F2P case colors=[C0,C1,C2]) under preconditions n>=1, len(colors)>=1. Two postconditions: (1) per-layer facecolor Result()[i] == colors[i % len(colors)] (cyc_prefix), and (2) axes.cycle == Old(axes.cycle) (Axes property cycle untouched).

Real repo post-patch behavior (verified against base_commit 14c96b51 worktree, gold patch): in the colors-not-None branch the fix sets `colors = itertools.cycle(colors)` and sources each layer's facecolor via next(colors) => layer i = colors[i % len(colors)] exactly. It removes `axes.set_prop_cycle(color=colors)` and does NOT call get_next_color() in this branch, so the Axes cycle is left unchanged. Both spec postconditions therefore match the real callee.

Evidence: (a) axiom_check.py passes — deep model == real itertools.cycle drawing on 10 boundary + 20000 fuzz inputs, supplied colours never mutated (G-AX pass in meta.json). (b) My own fuzz of real itertools.cycle draw vs model colors[i%k] over 200,000 random inputs (k in 1..15, n in 1..60): 0 divergences across the entire precondition domain. (c) model.py verifies (G-GOLD pass); model_prepatch.py which reinstates axes.cycle:=colors correctly FAILS (G-DIFF pass), confirming the spec senses the fixed mutation rather than over-constraining. (d) same-spec confirms model.py shares the exact bundle spec.

No input in the modeled domain makes the spec disagree with the real repo behavior. The spec is appropriately scoped (the else/default-cycle branch is identical pre/post and out of tested scope per mapping.md/refinement.md §C) and does not over-strengthen. Verdict: FAITHFUL — no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec regions of model.py and model_prepatch.py are byte-identical (same-spec exit 0; only the impl region differs — the prepatch's `axes.cycle = ToSeq(colors)` bug line and proof comments). The public problem_statement is titled 'stackplot should not change Axes cycler' and explicitly states that supplying colors must not mutate the shared Axes color-cycle state. The spec view's read-only property — docstring 'supplying explicit colours ... MUST NOT alter the drawing context's own colour-cycle state' and `Ensures(axes.cycle == Old(axes.cycle))` — is a direct, abstract restatement of that public requirement, not new information. The cyclic-color-assignment postconditions (`colors[i % len(colors)]`, 'repeating from the beginning') specify desired output behavior at an abstract, opaque-token level and never name any gold-patch symbol (`itertools.cycle`, `set_prop_cycle`, `get_next_color`), file, or line. The pre-patch bug comment describing the mutating write lives in model_prepatch.py's impl region, which is not part of the shared spec view. No spec-view line reconstructs the gold edit beyond what the problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
