# P2 adversarial audit — django__django-14539

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for trim_trailing_punct, modeling the gold-patched trailing-punctuation trim block in django/utils/html.py:trim_punctuation. base_commit (6a5ef557) contains the PRE-fix buggy code as expected; the model specifies the gold-patched oracle behavior (G-DIFF confirms model_prepatch fails the spec).

Verification performed:
1. same-spec: unmodified model.py shares the bundle's exact spec (exit 0).
2. Precondition soundness: enumerated ALL HTML5 named entities -> zero that lengthen; 400k-input independent fuzz (named/numeric/malformed entity refs, semicolons, ampersands, high codepoints, all-punctuation, empty) -> 0 violations of the two Requires bounds (0<=decoded_len<=len(middle); 0<=kept_len<=decoded_len). The precondition is therefore not stronger than the real html.unescape+rstrip guarantees.
3. Model == gold: for every branch-entered input (kept_len<decoded_len), the model's deep code-point slicing reproduces the gold-patched str block exactly. 120,299 branch-entered fuzz inputs -> 0 mismatches, and all three postcondition clauses (moved-count = decoded_len-kept_len; moved-suffix == middle.drop(split)+trail; lossless split new_middle + moved.take == middle) held on every case, including the full-move edge (pc==len(middle)). Postcondition is exactly gold's output, so it is satisfiable / not too strong.
4. Bundled axiom_check.py passes independently (exit 0).

The str<->List[int] code-point refinement and negative<->non-negative slice equivalences (mapping.md) are exact on all tested inputs. No input found where the modeled function disagrees with the real callee behavior it abstracts. Spec is faithful; no divergence.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py docstring + contract (pre/post) region. It describes desired behaviour functionally over PSeq take/drop with abstract integers decoded_len/kept_len, explicitly framed 'as desired behaviour, not as an edit'. It contains NONE of the gold-code tokens (punctuation_count, negative slicing middle[-punctuation_count:]/[:-punctuation_count]) — those appear only in the impl region the solver writes (model.py:34-39). It does not use the repo names middle_unescaped/stripped, never references the pre-fix expression len(stripped) as the old boundary, and never frames the content as a diff. The postconditions (len==len(middle)-(decoded_len-kept_len); lossless-split clause) state the correct OUTPUT, which is the legitimate role of a functional spec and is derivable from the public problem_statement's own example (&lt decoding with 'lt' leaking into trail exposes the encoded-vs-decoded length mismatch). The only artifacts that quote the gold hunk verbatim are refinement.md and mapping.md, which are audit-side documents, NOT part of the solver-facing spec view. Nothing in the spec view leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
