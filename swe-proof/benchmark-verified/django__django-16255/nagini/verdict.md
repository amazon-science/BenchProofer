# P2 adversarial audit — django__django-16255

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
- **machine verdict:** Faithfulness-break attack on django__django-16255 nagini bundle: no divergence found. Modeled function latest_stamp(stamps: List[int]) -> Optional[int] specifies empty->None (no failure), non-empty->max (member + dominates all). Real repo callee (patched, django/contrib/sitemaps/__init__.py:170) callable branch is `max([self.lastmod(item) for item in self.items()], default=None)`. Checks: (1) nagini_verify.sh -> 'Verification successful' (12.4s); (2) axiom_check.py G-AX passes on 14 boundary + 50000 fuzz inputs asserting latest_stamp(values)==max(values,default=None) incl. the empty list; (3) real pre/post diff confirmed: sole delta is adding default=None, and the empty-section->None behavior is the entire F2P bug fix; (4) type refinement date/datetime->int is order-preserving (total order both sides), so max over carrier == max over reality and empty behavior is type-independent. The spec's postconditions (empty=>None; non-empty=>Result is one of stamps AND >= every stamp, i.e. exactly the maximum) coincide pointwise with max(values, default=None) over the whole abstraction domain the patch touches. Unchanged guards (hasattr/callable/except TypeError/non-callable branch) are correctly scoped out as unchanged code per mapping.md, not a spec drift of the modeled op. No input where the spec disagrees with the real callee. Spec is neither too strong nor too weak: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py spec region) describes behavior abstractly over List[int]: empty collection -> None (absent marker, no failure); non-empty -> greatest collected stamp (membership + dominance). This behavioral requirement is exactly what the PUBLIC problem_statement already discloses: it names get_latest_lastmod, shows the exact buggy line max([self.lastmod(item) for item in self.items()]), reports the ValueError on empty sections, and demands the empty case return None instead of raising. The problem_statement even sketches a solution (except (TypeError, ValueError)). The spec view mentions no 'max', no 'default=None', and no edit mechanism, so it does not reveal HOW to fix beyond the public statement. The exact gold hunk (default=None) does appear in refinement.md and mapping.md, but those are auditor-facing refinement/provenance documents (refinement.md states patch.diff is the gold patch verbatim), not the spec view a solver fills in; they legitimately cite the gold patch. Even so, that hunk is the same information class already public (the exact buggy line + the required empty-case behavior). No leakage of the gold edit beyond problem_statement via the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
