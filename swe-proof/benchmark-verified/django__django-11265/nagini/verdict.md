# P2 adversarial audit — django__django-11265

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on nagini django__django-11265. Two modeled sites, both faithful to the repo at base_commit 21aa2a5e (django/db/models/sql/query.py).

Site 1 propagate_relation_registry ↔ split_exclude added line `query._filtered_relations = self._filtered_relations` (query.py:1669). Patch is a direct dict reference-assignment: inner registry becomes exactly the outer's. Model post ToSeq(Result())==ToSeq(outer_relations) captures this content-equality exactly. Precondition referenced_alias∈outer_relations is a legitimate domain restriction (alias IS declared on the outer query in the F2P case) and within it the model agrees with the repo. No divergence.

Site 2 subquery_retained_filters ↔ trim_start guard (query.py:2145). Patched guard `first_join.join_type != LOUTER and not first_join.filtered_relation` is byte-for-byte may_trim_leading_join = join_type!=LOUTER() and not is_filtered_relation. Exhaustively checked all 4 (join_type × filtered) combinations: all agree with the repo guard. Trim ⇒ leading join removed ⇒ its ON-clause filter dropped ⇒ Result==other_filters; not-trim ⇒ leading join kept ⇒ Result==PSeq(leading_filter)+other_filters. Downstream conditions untouched by trim path ⇒ always retained (faithful). The unmodeled trim-branch extra_restriction is orthogonal (generic join_field restriction, not the filtered_relation ON-condition that leading_filter denotes); omitting an unmodeled feature is abstraction, not a false claim about repo behavior.

Machine-checkable evidence: bundle model verifies (nagini_verify exit 0, 12.7s); same-spec harness reports SAME (spec byte-identical); model_prepatch_1 fails exactly ToSeq(Result())==ToSeq(outer_relations); model_prepatch_2 fails exactly the not-may_trim retention implication. Prepatch failures land on the fix's discriminating clauses, confirming the spec is calibrated to the repo (not too weak, not extrapolated beyond it). No input found where the modeled functions disagree with the real callees within their preconditions.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the relaxed-leakage disposition (not a rubber-stamp). (1) Spec view regenerated via swebench_unified.markers.spec_view over model.py: sha256=195b72188a55f91e… byte-matches meta.json region_hashes.spec_view — reviewing the frozen spec. (2) A real semantic leak exists: the site-2 spec content (docstring item (2); the transparent guard may_trim_leading_join(join_type,is_filtered_relation)=join_type!=LOUTER() and not is_filtered_relation; and the four site-2 postconditions keyed on it) encodes the gold's second hunk `and not first_join.filtered_relation`. I re-scanned the public problem_statement: it is ENTIRELY the FieldError resolution symptom plus the reporter's site-1-only diagnosis ('a new query is created without all extra datas'); it never mentions left-outer/inner joins, trimming/collapsing, retained filters, subquery pushdown, or wrong-rows. Those appear only in hints_text/gold/test_patch. So site-2 does leak beyond problem_statement. (3) Unavoidability re-derived: the sole F2P test pins wrong-rows correctness; site-1 fix alone leaves it failing (alias resolves but its filtered-relation join is trimmed away), site-2 fix alone fails with the original FieldError — both hunks independently necessary and site-2 not PS-derivable => genuine problem_statement↔gold mismatch (spec_guide directive-6 relaxed-leakage condition). (4) No leak BEYOND the dispositioned facet: forbidden-token scan of the spec view — split_exclude, trim_start, first_join, alias_map, query.py, _filtered_relations, names_to_path, OuterRef, unref_alias, 'diff --git' — all absent; LOUTER()/INNER()/is_filtered_relation are the model's own mnemonic tokens for the two join kinds, within the facet. Site 1 is fully PS-derivable and does not leak. (5) Core sound (meta.json): G-VERIFY pass, G-DIFF pass (both prepatches fail their discriminators), G-MUT 20/20, G-PBT SOUND, G-RESOLVE resolved, G-GOLD pass; G-LEAK status='relaxed' via relaxed_leakage:true + RELAXED_LEAKAGE.md; leak.py + _audit.py confirm a properly-dispositioned relaxed-leakage panel records as pass/NO-LEAKAGE + note. The known dispositioned site-2 facet was re-confirmed; no new leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
