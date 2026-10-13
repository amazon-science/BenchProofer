# P2 adversarial audit — sphinx-doc__sphinx-7462

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
- **machine verdict:** Faithfulness-break attack found NO diverging input; spec is faithful and not over-strong.

Checks run:
- same-spec (nagini, atk_faith.py == bundle model.py): exit 0, SAME — spec region byte-identical.
- nagini_verify.sh on model.py: 'Verification successful' (13.6s), exit 0 — the frozen spec is discharged by its impl (not a vacuous/rubber-stamp spec).
- axiom_check.py (G-AX): exit 0 — join_tokens == real token loop and join_comma == real ', '.join on 8 boundary + 30000 fuzz non-empty inputs; real token loop raises IndexError on empty group; real ', '.join(()) == ''.

Real-repo faithfulness of each modeled function at base_commit b3e26a6:
- tuple_tokens (sphinx/domains/python.py unparse ast.Tuple branch, gold): non-empty -> members interleaved with single ', ' separator token (PSeq(44,32) = display text of desc_sig_punctuation('', ', ')), no trailing sep == the gold loop's flattened token sequence; empty -> PSeq(open_paren(), close_paren()) == gold [desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]. Matches gold on every input.
- tuple_text (sphinx/pycode/ast.py unparse ast.Tuple branch, gold): non-empty -> join_comma == ', '.join(unparse(e) ...); empty -> PSeq(40,41) == '()'. Matches gold on every input.

The only changed operation (empty-group rendering) is concrete in both model and gold and matches the F2P tests: Tuple[()] -> '(' ')' punctuation tokens; '()' -> '()' text. Prepatch models (join_comma([])=='' ; token pop() crash) FAIL exactly the empty-group clauses (G-DIFF pass), so the spec is tight to the actual repair, not over-tightened beyond real behavior. Confirmed no input where the modeled postconditions disagree with the real gold callee across empty / single / multi / comma-containing members.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage check for sphinx-doc__sphinx-7462 (nagini). Compared the consumer spec view (markers.spec_view with Nagini tables; impl regions elided as '... supplied by the consumer') against the public problem_statement.

Public problem_statement discloses: 'IndexError: pop from empty list' for an empty tuple annotation Tuple[()] at sphinx/domains/python.py unparse, and that the expected behavior is that docs build with valid type annotations for the empty tuple.

Gold edit (from patch.diff/meta): add `if node.elts:` guard; empty group renders as ['(', ')'] tokens (site A, python.py) and "()" text (site B, pycode/ast.py).

Spec view contains ONLY: (a) desired input/output behaviour — empty group renders as the two symbols '(' ')' / "()", non-empty group is the ', '-separated join; (b) abstract model names tuple_tokens/tuple_text/join_tokens/join_comma with PSeq[int] carriers. It contains NO repo file paths, NO line numbers, NO `if node.elts:` guard text, NO diff, and the impl bodies are elided. Repo-level edit detail (files, the pop()/guard structure, the second site) lives only in mapping.md/refinement.md/meta.json, which are NOT part of the spec view.

Assessment: stating the correct rendering of the empty tuple ('()') is the legitimate job of a specification and is directly and obviously implied by the public problem_statement's 'valid type annotations for Tuple[()]'. The lone mechanism allusion ('removal of a non-existent trailing separator') merely restates the public 'pop from empty list' crash and adds nothing beyond problem_statement. The text-surface site (pycode/ast.py returning "") is expressed only as an abstract 'text rendering' behaviour, not as a code location or edit, so it does not leak the second gold hunk as an edit.

Machine check: `same-spec nagini sphinx-doc__sphinx-7462` on the bundle model returns exit 0 (spec region byte-identical). No spec-view line reconstructs the gold code edit beyond the public problem statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
