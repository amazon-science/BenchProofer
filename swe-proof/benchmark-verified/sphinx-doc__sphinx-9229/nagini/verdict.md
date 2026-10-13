# P2 adversarial audit — sphinx-doc__sphinx-9229

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
- **machine verdict:** same-spec exit 0; model verifies (Nagini OK, 13.8s). Site A (select_doc_block/get_doc): faithful — None/[] truthiness collapse of get_variable_comment is exact; ['']-style comment stays truthy under len>0. Site B (alias_additional_content/add_content): faithful on the tested domain. The single genuine input-level divergence is the gold's `try/except AttributeError` around `restify`, which the model omits (make_placeholder always succeeds, axiomatized non-empty). This branch is (a) NOT introduced by the patch (unchanged re-gated line), (b) explicitly disclosed in refinement.md §B and mapping.md §3.1 as an unmodeled defensive guard (directive-7), and (c) UNREACHABLE on all F2P/P2P inputs: test_class_alias targets target.classes.Foo (valid class -> restify succeeds), and test_class_alias_having_doccomment has a comment so the placeholder branch is never entered. Since the resolves claim is scoped to behavioral equality on the tested inputs, and the divergence lies strictly outside that domain, the spec is not too strong / does not drift on the exercised behavior. Sound abstraction, not a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view integrity confirmed: spec_view sha256 = 30c5102b425caf6c6a7a7e166ee593ae6320dd621eea92e85edd46b645c5ee17, byte-identical to meta.json region_hashes.spec_view. Both impl regions are correctly elided ('...  # implementation elided'); no impl text (return [] / return None / make_placeholder(target) call / the 'and not has_authored_comment' gate wiring) appears in the consumer-visible view.

Leakage assessment against the PUBLIC problem_statement (not hints; hints_text is empty here): the problem_statement already publicly establishes the full desired-behaviour contrast — type-alias authored docstrings are ignored and only 'alias of ...' is shown, and the expected behaviour is that the authored docstring/comment be displayed instead of the placeholder. The spec view merely restates this desired behaviour abstractly (a comment-present alias shows the comment / suppresses the placeholder; a comment-absent alias substitutes the placeholder), which a spec is required to do.

No gold-edit specifics leak beyond problem_statement in the spec view:
- No repo path, file, or line numbers (sphinx/ext/autodoc/__init__.py, :1676/:1724 appear only in mapping.md/refinement.md/meta.json, which are auditor docs, not the consumer spec view).
- None of the gold-patch symbol names appear in the spec view: get_variable_comment, doc_as_attr, restify, StringList, attr_docs are absent. Modeling identifiers (is_attr_alias, comment, prepared, target, more_content, select_doc_block, alias_additional_content) are generic/abstract and do not name repo symbols.
- The docstring is explicitly framed 'as desired behaviour, not as an edit', and the PRESENT-but-EMPTY vs ABSENT block distinction is presented as an observable pipeline behaviour, not as the source-level 'return []' construct; the impl that realizes it is elided.

The abstracted 'present-empty block' / 'placeholder only when no comment' behaviour is a direct, natural consequence of the publicly-described requirement, so it does not reconstruct the gold edit beyond what problem_statement already discloses. G-LEAK in meta.json is pass, consistent with this finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
