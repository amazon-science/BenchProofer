# P2 adversarial audit — matplotlib__matplotlib-24570

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
- **machine verdict:** Faithfulness (spec-drift) check for matplotlib__matplotlib-24570 nagini bundle. The modeled function offset_for / aligned_offsets was validated against the REAL post-patch matplotlib.offsetbox._get_aligned_offsets. Confirmed the post-patch worktree has the fixed grouping: {'left','bottom'}->[d] (low-edge) and {'right','top'}->[height-h+d] (high-edge). Reran the axiom_check protocol against the verbatim real function over 8 boundary layouts (incl. F2P geometry [(30,0),(60,0)]) + 20,000 seeded (rng=24570) fuzz layouts x all 6 anchors; every real offset equals the deep model under the x2 un-scaling (real == model/2). No divergence found. The x2 integer scaling is a uniform positive scaling making center's *.5 exact; it preserves every positional relationship the alignment expresses. The spec pins exactly offset_for(...) per box plus the LOWER/UPPER contrast clauses, which match the real callee's arithmetic on the validated domain (height=None -> total=max(h), mirroring the packers' self.height is None). Spec is not too strong and does not drift. Bundle integrity: same-spec exit 0, Nagini verification successful (20.3s). Verdict: FAITHFUL, no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms(empty) + pure + pre/post-conditions; impl elided) verified byte-identical to stored region_hashes (spec_view + all spec regions OK). The gold edit is a string-membership swap in _get_aligned_offsets: move 'top' from the low-edge ['left','top']->[d] branch to the high-edge branch and 'bottom' the other way, i.e. ['left','top']->['left','bottom'] and ['right','bottom']->['right','top']. The discriminating content of the edit is WHICH repo string ('top'/'bottom') belongs to WHICH offset class. The public problem_statement ALREADY discloses this fully: '`align` in `HPacker` is reversed ... the options `top` and `bottom` seems reversed'. The spec view reveals strictly LESS: it uses only abstract anchor names (BASELINE, LOWER/SIDE_A, UPPER/SIDE_B, CENTER) and integer codes 0-3, and NEVER mentions the strings top/bottom/left/right. It states the correct, invariant per-anchor arithmetic (low-edge offset = own descent; high-edge offset = slack + descent) which is the natural correctness spec any consumer must meet, not a description of the edit. The actual leaking binding LOWER<->{left,bottom}, UPPER<->{right,top} lives only in mapping.md / refinement.md, which are NOT part of the spec view. The generic note 'the changed operation is the offset arithmetic' is non-localizing and reveals nothing beyond the public statement. Conclusion: nothing in the spec view points to the gold edit beyond what problem_statement already makes public (in fact it is more abstract than the public statement).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
