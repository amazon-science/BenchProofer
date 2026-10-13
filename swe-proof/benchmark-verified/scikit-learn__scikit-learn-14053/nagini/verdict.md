# P2 adversarial audit — scikit-learn__scikit-learn-14053

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
- **machine verdict:** Faithfulness-break attack on scikit-learn__scikit-learn-14053 nagini bundle. Modeled function resolve_node_names models export_text's feature_names_ construction; gold patch is `[feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in tree_.feature]` (export.py:893; TREE_UNDEFINED==-2 at _tree.pyx:64). Postcondition ToSeq(Result())==built_seq(ToSeq(names),ToSeq(feat)); precondition in_domain = every selector is -2 or a valid position in names. (1) Precondition is the GENUINE domain of tree_.feature: internal nodes hold valid feature indices, leaf nodes hold -2, and export_text validates len(feature_names)==tree_.n_features (export.py:873-877) — not a spec weakening. (2) built_seq matches the real patched comprehension EXACTLY over the full precondition domain: 500k randomized fuzz inputs (n in 0..6 names, 0..12 nodes, selectors incl. -2/valid/out-of-range, filtered to in_domain) produced 0 divergences and no in-domain IndexError. built_seq's additional guard (head!=-2 and 0<=head<len(names)) is vacuous under the precondition (the only permitted non-position selector is -2, mapped to None by both model and patch). (3) len(Result())==len(feat) matches the one-name-per-node comprehension. (4) Model verifies (Nagini, 13.9s). No input within the modeled domain makes the modeled function disagree with the real callee. Spec is neither too strong nor drifting. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms + pure + pre/post-conditions, impl elided) screened both mechanically and by hand. Automated leakage.screen() passes (0 hard failures). Manual adversarial pass confirms:

1. No gold-patch line reproduced. Gold changed lines use `feature_names`, `tree_.feature`, `_tree.TREE_UNDEFINED`, `feature_names_`; the spec view uses abstracted carriers `names`/`feat`/`built_seq`/`None`. No verbatim collision.
2. No diff markers, no patched file path (`sklearn/tree/export.py`) or dotted module path in the view.
3. Only distinctive patched symbol is `export_text`, which is ALREADY public in the problem_statement title ('IndexError ... in export_text when the tree only has one feature'); no spec-view identifier embeds it and no comment names it. All model identifiers (resolve_node_names, built_seq, in_domain, names, feat) are abstraction-level, not repo symbols.
4. No bug/fix narration terms ('bug','fix','wrong','broken','previously','regression', or 'IndexError'/'crash') in any spec-view comment or docstring.

The view discloses the abstract behavioral contract: selectors are table positions or the reserved out-of-band value -2, -2 resolves to a None placeholder, and resolution is total for a name table of any size. This is the legitimate specification of correct behavior grounded in the documented domain of tree_.feature (leaf marker -2), phrased with no reference to the edit, the crash, or the buggy code. Every spec necessarily encodes post-fix behavior; that is not leakage. The gold edit (add the `i != TREE_UNDEFINED else None` guard) is not reconstructable from the view beyond what the public problem_statement already implies (single-feature IndexError in export_text). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
