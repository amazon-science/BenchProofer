# P2 adversarial audit — psf__requests-1921

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "Verdict — psf__requests-1921", before this corpus rendered one
> section per audit role. It is kept verbatim because it is the only account of
> that round that ships in this bundle, and it is NOT this cell's record. The
> record is the audit gate entries in the `meta.json` beside this file, which
> are the source of truth for the cell's status; each role section below
> publishes its gate's `status (recorded)` and `machine verdict` straight from
> that entry. Each round authored and re-ran its own attacks, so a count in the
> text above is that round's own count and not this record's: where the two
> accounts differ, the record governs.

## Guided improvement pass

### Artifact-safe change summary
The discriminating behavior of this fix is "drop every key whose EFFECTIVE
(post precedence-merge) value equals the unset value, regardless of which side
(session-level default or per-request override) supplied it." The improvement
pass ported a sound modeling refinement: instead of leaving the changed merge
operation behind an opaque/axiomatized symbol, the changed operation is now
modeled deeply. The spec is an exact functional equality
`out = combinedSeq session request`, where the deep model spells out the
precedence overlay (request-wins via `effective`), the min-length backward fold
that builds the result, and the post-merge drop on `noneVal`. This removes any
ungrounded oracle: the dict↔List Int refinement (key position; absent=0;
unset=-1) maps the real merge-then-drop onto the deep model, and the equality
provably rejects every behavioral deviation. No axioms, opaque symbols, sorry,
or native_decide are introduced (meta axioms `[]`).

### Sub-verdicts

**EQ** — gEq=SOUND, specStrength=TIGHT, kind3Present=false. Spec (2 ensures):
`out = combinedSeq session request` (total functional equality to a fully
spelled-out deep definition) AND `∀ x∈out, x≠noneVal`. All 7 wrong impls
(w1_prepatch, w2_nodrop, w3_sessionwins, w4_empty, w5_sessonly, w6_session,
w7_allabsent) share the frozen spec yet fail verification (exit 1) ⇒ spec
rejects each behavioral deviation; no wrong impl verifies ⇒ SOUND. Positive
control pc3 (structurally different accumulator, renamed result var) verifies
(exit 0) ⇒ non-vacuous. Refinement: A1=R (dict↔List Int over key positions),
A2=R (per-request-wins overlay↔effective), A3=A-reference (combine-and-drop
modeled deeply, validated against the real op by G-CONF, no consumed axiom),
A4=R (return mapping). No kind-3 echo.

**FAITH** — faithfulness=FAITHFUL, gAx=VACUOUS. Solution.lean verifies (rc 0);
Solution_prepatch.lean fails (rc 1) on exactly the discriminating clause —
prepatch keys the drop off the per-request value while the spec keys off the
effective merged value, diverging on the session-only unset key (sv=unset,
rv=absent). Conformance check drives the REAL operation over 100010 fuzz inputs
(seed=1921) plus boundary shapes with 0 disagreements; an independent fuzz of
300000 inputs with unequal lengths and a larger alphabet also yielded 0
mismatches. Spec rejects no correct gold behavior ⇒ FAITHFUL, no drift.
meta.json axioms `[]`, no axiom file ⇒ G-AX VACUOUS.

**LEAK** — leakage=NO-LEAKAGE, no external-reference token found. grep for repo/spec
identifiers in the bundle is empty. spec_view contains no gold-specific
identifiers; it uses only generic model vocabulary (session, request,
effective, combined, absent=0, unset=-1, combinedSeq). The discriminating
behavior is fully described by the PUBLIC problem statement (setting a session
default to the unset value should not send it; the per-request unset-drop
already works) ⇒ reconstruction stays within the public issue scope and does
not reveal the patched file or symbol. G-LEAK=pass (not relaxed).

### Per-gate table

| Gate    | Verdict |
|---------|---------|
| G-EQ    | pass    |
| G-PANEL | pass    |

staticGatesPass=true

### Outcome

**ACCEPTED**

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness-break audit for psf__requests-1921 (velvet). Spec region byte-identical: markers.same_spec(Solution, prepatch, LeanBackend.language)=True. Solution.lean verifies via lean_verify.sh (exit 0); Solution_prepatch.lean fails (exit 1) on the discriminating clause (drop keyed off rv rather than the effective merged value ev) => spec is discriminating and non-trivial.

**Modeled function:** effectiveCollection/combinedSeq = precedence merge (request wins via `effective`) then drop every key whose EFFECTIVE value is the unset sentinel (`combined`, noneVal=-1 -> absent=0), plus postcondition (no output position holds noneVal). Real callee: requests.sessions.merge_setting dict-merge branch POST-patch, incl. gold line `merged_setting = dict((k,v) for (k,v) in merged_setting.items() if v is not None)`.

Differential testing against a verbatim copy of the real post-patch merge_setting:
  - 300k equal-length fuzz inputs (alphabet {absent,-1,1,2,7}): 0 disagreements.
  - 300k directly-constructed disjoint/overlapping-keyset real dict pairs (values in {None,1,2,7}), lifted per the mapping.md bijection (absent<->key omitted; -1<->None; other int<->itself), driven through the REAL merge_setting and compared to the model over the union key universe: 0 disagreements.
The model reproduces request-wins precedence, the all-sides None-drop, and the no-surviving-None guarantee exactly on the abstraction's domain.

On the question of a diverging input: unequal-length list carriers DO diverge (combinedSeq truncates to min length while the real op keeps the union of keys — 142k/200k unequal-length fuzz mismatches). However these inputs are OUTSIDE the bijection's image: every real (dict,dict) pair over the shared/union key universe {0..n-1} encodes to EQUAL-LENGTH lists (missing keys padded with absent=0). No real input ever produces unequal-length carriers, so the truncation branch never fires on an in-domain input. This is under-constraint of non-image inputs, not a case where the modeled function disagrees with the real callee on a REAL input. Therefore the spec is not too strong / does not drift: on every input in the abstraction's domain the model equals the real op. Verdict FAITHFUL.

**Secondary checks:** noneVal=-1 disjoint from ordinary values (>=1) so 'explicitly unset' vs 'ordinary value' vs 'absent' are cleanly distinguished, matching the conformance-check carrier. conformance_check.py truncates the oracle to min length too (consistent with model), and pins SEED=1921 for reproducibility.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage audit of the consumer spec view (markers.spec_view under VelvetBackend). Verified independently: same_spec(Solution, Solution_prepatch)=True and spec_view hash = ddc84ad1904f... matches meta.json G-HYGIENE, so the frozen spec is byte-identical to the prepatch view (no impl-specific content survives into the spec).

Spec view content is purely generic modeling vocabulary: method effectiveCollection(session, request); pure helpers effective (request-wins precedence: `if rv != absent then rv else sv`), combined (drop when effective value = unset: `if effective sv rv = noneVal then absent`), combinedSeq; constants absent=0, noneVal=-1; and the two ensures clauses `out = combinedSeq session request` and `forall x in out, x != noneVal`. NO repo-specific identifier appears: no merge_setting, sessions.py, OrderedDict, dict-comprehension, Accept-Encoding, filename, or line number. (Those appear only in refinement.md/mapping.md audit artifacts, which are NOT part of the consumer spec view.)

Every behavioral commitment in the spec view maps onto the PUBLIC problem_statement, not hints_text: (1) session vs request collections <-> session default headers vs per-request/method-argument headers; (2) request-wins precedence (effective) <-> the docs' statement that method-argument headers override session defaults and the already-working per-request None-unset; (3) drop-key-when-effective-value-is-unset (combined / forall x != noneVal) <-> the issue's core ask that setting a session header to None should prevent it being sent instead of literally sending 'None'. The only arguably 'extra' detail — that the drop keys off the merged/effective value regardless of which side supplied it — is exactly the fix the public issue requests (make permanent session-default None behave like the already-working per-request None). Nothing reveals the patched file/symbol or the specific edit (the added dict-comprehension drop pass) beyond what the public issue already states.

**Conclusion:** reconstruction from the spec view stays within public problem_statement scope; no gold-edit leakage. Consistent with G-LEAK=pass (not relaxed).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
