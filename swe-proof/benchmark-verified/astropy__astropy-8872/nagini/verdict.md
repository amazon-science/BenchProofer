# P2 adversarial audit — astropy__astropy-8872

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
- **machine verdict:** Faithfulness-break attack on astropy__astropy-8872 (Nagini). The modeled functions' postconditions are Result()==is_int_like(kind) (homogeneous, quantity.py:299-301) and Result()==(is_int_like(kind) or kind==KIND_OBJECT()) (generic, quantity.py:380-383). With kind==ord(dtype.kind), these are IDENTICALLY the gold patch's new predicates dtype.kind in 'iu' and dtype.kind in 'iuO' (confirmed against astropy cloned at base_commit b750a0e6, both hunks match verbatim). I enumerated every numpy dtype kind (b i u f c O V S U M m) plus parametrized (datetime64[s], timedelta64[h], S5, U3, V16, V0, S0, U0), byteorder-swapped, and structured/single-field dtypes: the model decision equals the real repo (gold) decision on EVERY dtype — zero mismatches. G-AX passes (19 boundary + 20000 fuzz) and the model verifies (positive control, 10.8s). The float16 discriminator (kind 'f', fits_ref_real32==False) is correctly preserved by both paths, matching the fix vs. the width-based pre-patch bug.

Minor observation (NOT a defect): realizable() is marginally narrower than the full numpy dtype universe — it rejects fieldless/zero-length void (V16, V0) and zero-length strings (S0/U0), which are genuine numpy dtypes, so mapping.md's claim 'excludes only combinations numpy never produces' is slightly overstated. However this narrowing yields NO behavioral disagreement: on every excluded dtype the modeled decision would still be False (preserve) = the real repo decision, and S/U kinds are caught by the unchanged 'OSU' TypeError guard before the generic coercion anyway (F2P/P2P tests only build numeric/object/composite dtypes). There is no input on which the modeled function disagrees with the real callee. Spec is neither too strong nor drifting. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3): leakage / gold-reconstruction. The gold edit replaces the width-based test `not (np.can_cast(np.float32, value.dtype) or value.dtype.fields)` with the kind-based `value.dtype.kind in 'iu'` (hunk1, homogeneous) and `value.dtype.kind in 'iuO'` (hunk2, generic). The public problem_statement discloses only the SYMPTOM (float16 upgraded to float64; float32/64/128 preserved) and nothing about the mechanism, the two call sites, integer/object coercion, or the can_cast vs. kind change.

Examined the actual consumer spec view via markers.spec_view(model.py, nagini): both impl-start/impl-end regions are ELIDED ('implementation elided — supplied by the consumer'), so the literal gold predicates (`return is_int_like(kind)`, `return is_int_like(kind) or kind == KIND_OBJECT()`) are NOT shown to the consumer. The proof region is likewise elided.

What the spec view DOES contain is a purely abstract behavioral oracle: a docstring describing the desired decision (coerce int/uint in both paths + object in the generic path; preserve every real kind regardless of storage width, plus complex/composite/bool), and a deep model over three abstract observables (kind code-points, fits_ref_real32, is_composite) with pre/postconditions. This is exactly the role of a correctness oracle — fully specifying the intended behavior is inherent to the spec and cannot itself count as leakage (otherwise no oracle could pass). Crucially, it contains NO gold-patch source text, NO diff/hunk, NO file paths or line numbers, and does NOT reproduce either the patched expression (`dtype.kind in 'iu'`/`'iuO'`) or the pre-patch expression (`np.can_cast`/`dtype.fields`). The numpy kind tags mentioned in comments ('i','u','f','O','V','c','b' and their code points) are standard-library general knowledge, not patch-specific disclosure.

The abstract-observable framing describes the behavioral contract without handing over the mechanical edit or letting one reconstruct the diff verbatim. No single spec-view line leaks the gold edit beyond the problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
