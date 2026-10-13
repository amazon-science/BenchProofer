# P2 adversarial audit — django__django-16801

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-16801", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED** (G-EQ pass, G-PANEL pass)

## Per-gate table

| Gate | Verdict | Basis |
|---|---|---|
| **G-EQ** | **pass** | G-EQ SOUND + spec-strength TIGHT + no kind-3 refinement. All 7 wrong impls (atk_1..6, atk_8) share spec (`same_spec=True`) and fail to verify (exit 1); positive control atk_7 (structurally different correct impl) verifies (exit 0) -> spec is tight and non-vacuous. Both postconditions pin output to a total concrete pure Boolean function over universally-quantified `Bool` inputs (`out = shouldRegister ...`, `out = dimUpdate ...`); axioms region empty -> no ungrounded oracle to echo. Refinement audit: all tags R/I, no consumed axioms, no deep-model references, no kind-3 inexpressible op. |
| **G-PANEL** | **pass** | faithfulness FAITHFUL + G-AX VACUOUS + leakage NO-LEAKAGE. Site-1 spec `shouldRegister = !isAbstract && (hasWidthField \|\| hasHeightField)` is a verbatim transliteration of the post-gold guard `not cls._meta.abstract and (self.width_field or self.height_field)`; site-2 `dimUpdate` matches post-gold `update_dimension_fields` write-decision logic. F2P config inside modeled cube and exhaustively conformance-checked. No axioms in bundle (G-AX VACUOUS). Spec view carries no repo-specific identifier. |

### Underlying gate facts (from meta.json + independent re-check)
- G-VERIFY pass (Solution.lean exit 0, re-verified). G-DIFF pass (Solution_prepatch.lean fails). G-CONF pass (0/100136). G-RESOLVE pass (resolved, non-flaky). G-AX skip (no axioms). G-MUT 20/20 killed.
- Independent re-verification: `bash scripts/lean_verify.sh results/django__django-16801/Solution.lean` -> exit 0; `... Solution_prepatch.lean 300` -> exit 1 with unsolved goal `hasWidthField = true ∨ hasHeightField = true` (under `isAbstract = false`) — the discriminating F2P clause.
- patch.diff confirmed to match refinement.md narrative (site 1 adds `(self.width_field or self.height_field)` conjunct; site 2 removes the now-redundant `has_dimension_fields` leading guard).
- spec-view token scan: contribute_to_class, update_dimension_fields, imagefield, files.py, post_init, _meta, setattr, getattr, attname, signals, connect, width_field, height_field — ALL absent (count 0).

## Concrete defects + precise fixes

**None.** No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak was found. No refinement required.

A harness caveat was noted (NOT a bundle defect): the audit's prescribed `conformance_check.py` invocation can omit `apply_gold`/`gold_patch_path`, running PRE-PATCH testbed code (`if not cls._meta.abstract:` without the conjunct), which yields one spurious site-1 disagreement `(False,False,False) shadow=False oracle=True`. Re-running with the gold patch applied (as the gate does) yields 0 disagreements, matching meta.json. This is an artifact of the simplified audit invocation, not a spec-too-weak signal.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

> With the gold patch applied, G-CONF passes with 0 disagreements over 100136 inputs. The earlier "disagreement" was purely my harness invocation omitting `apply_gold` — not a spec defect. The spec's discriminating clause (`hasWidthField || hasHeightField`) matches the patched behavior exactly.
>
> Now the ungrounded-oracle probe: the postconditions are `out = shouldRegister ...` and `out = dimUpdate ...` where both RHS are total concrete pure Boolean functions, fully defined over universally-quantified Bool inputs. There's no opaque/axiomatized symbol (axioms region is empty). An impl can only satisfy `out = f(inputs)` by computing `f` — it cannot "echo an answer key" because there's no oracle input carrying the answer; the answer is forced for every one of the 8 (site1) / 128 (site2) input combinations. My atk_2 (`return true`) is exactly the echo-attempt and it failed. So no ungrounded oracle.
>
> Let me do a final faithfulness check on the refinement: confirm the spec's `dimUpdate` matches the patched `update_dimension_fields` semantics including the "already populated" guard direction, which G-CONF's site-2 exhaustive {0,1}^7 already covered with 0 disagreements. That's sufficient.
>
> All checks complete. Let me write the verdict.
>
> Summary of findings:
> - All 7 wrong impls share spec and fail to verify; positive control verifies. Spec is tight and non-vacuous.
> - Refinement audit: all R/I, no kind-3; prepatch fails on exactly the discriminating clause; G-CONF passes (0/100136) when correctly invoked with the gold patch.
> - The transient G-CONF "disagreement" I hit was a harness artifact (audit invocation omitted `apply_gold`), not a spec defect.
>
> VERDICT
>
> G-EQ: SOUND. spec-strength: TIGHT.
>
> Bundle: django__django-16801. Both methods pin output to a total concrete pure Boolean function over universally-quantified `Bool` inputs (`registerInitHandler`: `ensures out = shouldRegister isAbstract hasWidthField hasHeightField`; `dimensionWrites`: `ensures out = dimUpdate ...`). Axioms region is empty — no opaque/oracle symbol exists, so there is nothing for a wrong impl to echo. Baseline Solution.lean verifies (exit 0).
>
> Spec-too-weak attacks (impl-only edits; `same_spec` vs results/.../Solution.lean confirmed True for all; verified with `lean_verify.sh ...`):
> - atk_1 (prepatch site-1 bug: register every concrete model, drop `width||height` conjunct): same_spec=True, verify exit=1. REJECTED by `out = shouldRegister` — goal `hasWidthField = true ∨ hasHeightField = true` unsolved when `isAbstract=false`.
> - atk_2 (echo/ungrounded-oracle probe: `return true`): same_spec=True, verify exit=1. REJECTED — cannot satisfy the equality on `isAbstract=true` and on `(false,false,false)`.
> - atk_3 (register only on width, drop height): same_spec=True, verify exit=1. REJECTED on `hasWidthField=false, hasHeightField=true`.
> - atk_4 (dim: `writeWidth:=hasWidthField`, drop `proceed` gating): same_spec=True, verify exit=1. REJECTED — disagrees with `dimUpdate` whenever `proceed=false` and a field is declared (e.g. deferred).
> - atk_5 (dim: drop the `deferred` guard): same_spec=True, verify exit=1. REJECTED — writes when `deferred=true` contra `dimUpdate`'s `!deferred` conjunct.
> - atk_6 (dim: swap width/height write targets): same_spec=True, verify exit=1. REJECTED on asymmetric configs.
> - atk_8 (dim: drop the already-populated `dimFilled && !force` guard): same_spec=True, verify exit=1. REJECTED — writes when dims already filled and not forced.
> - atk_7 POSITIVE CONTROL (structurally different but correct: nested-if `registerInitHandler` + `if`-expression `dimUpdate` body): same_spec=True, verify exit=0. Confirms the spec is non-vacuous / satisfiable by a genuinely different correct impl.
>
> Refinement audit:
> - refinement.md tags are all R / I; no consumed axioms, no deep-model references (axioms/deep_model lists empty in meta.json); no kind-3 hand-waved inexpressible op. The one observable behavior change (site-1 added `(width or height)` conjunct) is modeled directly in `shouldRegister`, not hidden behind an axiom.
> - Solution_prepatch.lean FAILS for the RIGHT reason — its `registerInitHandler` leaves exactly the discriminating goal `hasWidthField = true ∨ hasHeightField = true` (under `isAbstract = false`), which is the F2P `test_post_init_not_connected` configuration; its `dimensionWrites` (extra redundant leading guard) still verifies, correctly demonstrating site 2 is a behavior-preserving refactor.
> - G-CONF faithfulness: when correctly invoked with `apply_gold=True`/`gold_patch_path` (mirroring how the gate runs it), conformance_check.py passes 0 disagreements over 100136 inputs — site 1 exhaustive {0,1}^3, site 2 exhaustive {0,1}^7 + 100000 fuzz — so the R/I shadow of `shouldRegister`/`dimUpdate` matches the gold-patched Django behavior at both sites.
>
> NOTE (harness caveat, not a bundle defect): the audit's prescribed `run_in_container(..., 'conformance_check.py')` invocation omits `apply_gold`/`gold_patch_path`, so it runs PRE-PATCH testbed code (verified: `inspect.getsource` showed `if not cls._meta.abstract:` without the conjunct). That produced one spurious site-1 disagreement `(False,False,False) shadow=False oracle=True` — i.e. the oracle was the unpatched code registering for every concrete model. Re-running with the gold patch applied yields 0 disagreements, matching meta.json. The disagreement is an artifact of the simplified audit invocation, not a spec-too-weak signal.

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

> The F2P test `test_post_init_not_connected` lives in `ImageFieldNoDimensionsTests`, whose model is a `Person` with an ImageField configured with no width_field/height_field — exactly `(isAbstract=F, hasWidthField=F, hasHeightField=F)`, the config where `shouldRegister=False` (no receiver). This is in the modeled Boolean cube and exhaustively conformance-checked against the real patched `contribute_to_class`. G-RESOLVE already confirms the gold patch passes this F2P plus all P2P.
>
> **Summary of findings:**
>
> 1. **Lean verification**: Solution.lean verifies (exit 0); Solution_prepatch.lean fails on `registerInitHandler` exactly on `hasWidthField = true ∨ hasHeightField = true` (the F2P discriminating clause). G-DIFF sound.
>
> 2. **Faithfulness**:
>    - Site 1 spec `shouldRegister = !isAbstract && (hasWidthField || hasHeightField)` is a *verbatim* transliteration of the post-gold guard `not cls._meta.abstract and (self.width_field or self.height_field)`. Confirmed against real post-gold source.
>    - Site 2 spec `dimUpdate` exactly matches the post-gold `update_dimension_fields` write-decision logic; confirmed against real source line-by-line.
>    - The Boolean abstraction is lossless for the modeled decision (control flow branches only on truthiness; the actual assigned width/height values are unchanged by the patch and not observed by tests).
>    - The F2P input config falls inside the modeled domain and was exhaustively checked.
>    - The spec is not too-strong: the site-2 prepatch body (extra redundant guard) also verifies, so the spec correctly admits the valid guard-keeping variant.
>
> 3. **G-CONF**: ran in-container with gold applied — 0 disagreements over site-1 exhaustive {0,1}³ (real Django class construction + real receiver inspection) and site-2 exhaustive {0,1}⁷ + 100k fuzz. The site-1 oracle is faithful (real model classes); site-2 uses a fake instance but faithfully controls the truthiness inputs the write-decision depends on.
>
> 4. **G-AX**: No axioms in the bundle (no `axiom_check.py`; `axioms = []`). VACUOUS.
>
> No spec-too-strong, no drift, no unsound axiom found.
>
> FAITHFULNESS: FAITHFUL. G-AX: VACUOUS.
>
> Docker evidence (gold patch applied in the official instance image): G-CONF `conformance_check.py` returned rc=0 — "R/I shadow of registerInitHandler/dimensionWrites agrees with patch.diff behaviour on 100136 inputs (seed=16801): site 1 exhaustive ({0,1}^3 via real Django model-class construction + post_init receiver inspection), site 2 exhaustive ({0,1}^7) + 100000 fuzz, 0 disagreements." I independently dumped the real post-gold source of both `ImageField.contribute_to_class` and `ImageField.update_dimension_fields` from the container and confirmed line-by-line that `shouldRegister` and `dimUpdate` are exact transliterations of the post-gold logic.
>
> Faithfulness checks:
> - Site 1 (the only F2P-observed site): spec `shouldRegister = !isAbstract && (hasWidthField || hasHeightField)` == post-gold guard `not cls._meta.abstract and (self.width_field or self.height_field)`. The F2P test `test_post_init_not_connected` exercises config (isAbstract=F, hasWidth=F, hasHeight=F) → shouldRegister=False, which is inside the modeled Boolean cube and exhaustively conformance-checked against real Django class construction.
> - Site 2: spec `dimUpdate` == post-gold write-decision logic (deferred guard, file/force guard, dimension_fields_filled guard, per-field write); the unchanged assigned width/height values are correctly out of model. Not too-strong: I verified that a Solution with gold `registerInitHandler` + the prepatch's redundant-extra-guard `dimensionWrites` body still verifies (site2.lean → exit 0), confirming the spec admits the valid guard-keeping variant rather than rejecting it.
> - The Boolean abstraction is lossless for the modeled control-flow decision.
>
> Lean evidence: Solution.lean verifies (exit 0, 2.3s); Solution_prepatch.lean fails G-DIFF on `registerInitHandler` precisely at `hasWidthField = true ∨ hasHeightField = true` — the discriminating F2P clause.
>
> VERDICT: faithfulness = FAITHFUL, G-AX = VACUOUS (no axioms in bundle; no axiom_check.py, axioms=[]).

## Sub-review 3 — LEAKAGE (verbatim)

> No repo-specific identifiers leak. The spec view uses only de-narrated, generic vocabulary.
>
> The spec view's discriminating content is entirely the registration decision: register the post-init dimension handler only when a concrete model declares a width or height field. This is precisely what the public problem statement describes:
> - "ImageField unnecessarily adds a post_init signal handler"
> - "the post_init signal handler is a noop because we don't use the width_field / height_field"
> - "If width_field and height_field are not set, removing the post_init signal should have no effect"
>
> So the F2P-tested fix (hunk 1) is fully PS-derivable. The spec view does not name the patched file, symbol, or any diff line. The docstring phrase "post-initialization dimension-synchronization handler" paraphrases the public "post_init signal handler" + the publicly-named width/height dimension fields.
>
> Hunk 2 (`update_dimension_fields` guard removal) is not in the PS, but the spec deliberately does NOT pin any hunk-2 fixed behavior — the prepatch with the extra guard still verifies. The `dimUpdate` docstring describes the general synchronization-pass semantics (which the PS itself references: "the signal handler will return right away"), not the specific guard removal. No leak there.
>
> **Reconstruction:** From the spec view alone, a reader could reconstruct "guard the post_init handler registration on `not abstract and (width_field or height_field)`" — but that reconstruction is equally achievable from the problem_statement alone. The `abstract` conjunct is the pre-existing baseline. No diff line, no patched symbol, no bug/fix narration beyond the public issue.
>
> NO-LEAKAGE
>
> Token scan of the spec view (case-insensitive) for repo-specific identifiers — all ABSENT: contribute_to_class, update_dimension_fields, imagefield, files.py, post_init, _meta, setattr, getattr, attname, signals, connect, has_dimension_fields, sender, cls, instance.__dict__, self. The identifiers used (`shouldRegister`, `registerInitHandler`, `dimUpdate`, `dimensionWrites`, `DimWrites`) are generic and echo no repo symbol; no diff line, no patched file/symbol, no bug/fix narration beyond the public issue appears.
>
> No leaking token to quote — the spec view reveals nothing beyond the public problem_statement.
>
> Verdict: leakage = NO-LEAKAGE

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit for django__django-16801 (velvet). Spec models two changed sites in django/db/models/fields/files.py: (1) registerInitHandler over shouldRegister = !isAbstract && (hasWidthField||hasHeightField), mapping the patched contribute_to_class guard `not cls._meta.abstract and (self.width_field or self.height_field)`; (2) dimensionWrites over dimUpdate, mapping the patched update_dimension_fields write-set. Verified: (a) base-commit source + gold patch match the two hunks; (b) Solution.lean elaborates cleanly via lean_verify.sh (exit 0); (c) same_spec(Solution.lean, Solution_prepatch.lean)==True (identical spec, differing impl — valid G-DIFF); (d) super-chain (FileField/Field.contribute_to_class) connects no signal, so out is the complete registration decision (A3 holds); (e) INDEPENDENTLY applied the gold patch to a fresh base-commit checkout and ran an exhaustive differential test of MY reading of the Lean spec against the REAL patched Django code — full Boolean cube (8 cases site1 + 128 cases site2 = 136 total), 0 disagreements; also re-ran bundle conformance_check.py against the real patched source: 100136 inputs (site1 exhaustive {0,1}^3, site2 exhaustive {0,1}^7 + 100000 fuzz seed=16801), 0 disagreements. The Python-truthiness↔Bool abstraction is faithful; concrete field-name strings and width/height values are immaterial to the control-flow decision the patch changes (unchanged by patch, correctly not modeled). No input makes the modeled function disagree with the real callee. Spec is not too strong and does not drift. FAITHFUL; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Spec region confirmed frozen:** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True, and the recomputed spec-view SHA256 6229ab55af5a983cbffe2bdbaec773fa25f6b088d0e38f53c5262a4923264e98 matches meta.json region_hashes.spec_view byte-for-byte. Audited the correct frozen view.

Leakage assessment (vs public problem_statement only, NOT hints_text — hints are empty anyway):

The public problem_statement already discloses the gold fix in plain language: 'the post_init signal handler is a noop because we don't use the width_field / height_field. If width_field and height_field are not set, removing the post_init signal should have no effect.' That publicly states the registration rule the patch implements.

Spec-view contents examined:
- shouldRegister := !isAbstract && (hasWidthField || hasHeightField): the post-patch registration predicate. It is fully derivable from the public problem_statement (non-abstract model that declares a width/height field). No information beyond the public statement.
- dimUpdate: the sync-pass logic for site 2. This is edit-INVARIANT: the prepatch dimensionWrites (which retains the removed leading has_dimension_fields guard) verifies against this SAME spec view, and same_spec confirms the two views are byte-identical. The spec view therefore cannot reveal the direction/content of the site-2 guard-removal edit at all.
- Prose docstrings describe desired behaviour abstractly (Boolean truthiness), matching the public statement's framing.

**What the view does NOT expose:** no Python source, no diff text, no repo line numbers, no gold comment strings (e.g. 'with width_field/height_field'), no F2P test name. test_post_init_not_connected and the repo line/site details appear only in meta.json / refinement.md / mapping.md — none of which are part of the consumer spec view. In-view references to conformance_check.py and mapping.md are audit-framework meta-commentary, not gold-edit content.

**Conclusion:** every fact in the spec view is either (a) already public in problem_statement (the width/height registration rule), or (b) edit-invariant across the gold patch (dimUpdate/DimWrites), or (c) generic modeling/framework prose. No spec-view line reconstructs the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
