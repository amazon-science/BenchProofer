# P2 adversarial audit — pydata__xarray-4695

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — pydata__xarray-4695", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED**

Bundle: `results/pydata__xarray-4695/`. Verifier: Velvet (Lean 4 v4.24.0).
Spec (frozen, byte-identical Solution ↔ prepatch):
`method labelSelect (key : List (String × Label)) return (out : Except String (List (String × Label))) ensures out = Except.ok key`, `Label = List String`. No axioms (`meta.json axioms=[]`, `deep_model_references=[]`), G-AX legitimately skipped.

## Per-gate verdict

| Gate | Verdict | Basis |
|------|---------|-------|
| **G-EQ** | **pass** | G-EQ SOUND + spec-strength TIGHT + no kind-3 refinement. 9 wrong impls (reject / drop / reorder / truncate / clobber-labels / per-label-empty) all share the spec (`same_spec=True`) and all FAIL verification; structurally-different correct control (foldr rebuild) shares the spec and VERIFIES (exit 0) ⇒ non-vacuous. The single equality post-condition `out = Except.ok key` pins output to input exactly, rejecting every corruption mode the issue describes. No ungrounded oracle: the postcondition references the input `key`, not an axiomatized answer-key. |
| **G-PANEL** | **pass** | faithfulness FAITHFUL + G-AX VACUOUS + leakage NO-LEAKAGE. Modeled `labelSelect ↔ _LocIndexer.__getitem__` (changed `dataarray.py:199` `sel(**key)`→`sel(key)`). Spec output == real post-gold `da.loc[...]` on F2P input `[[0],[1]]` (Docker-verified); G-CONF 100000 fuzzed inputs, seed=4695, 0 disagreements, reserved names exercised. No axiom trust point. Spec view discloses nothing beyond the public problem statement. |

### Reproduction (this session)
- `Solution.lean` verifies clean: exit 0.
- `Solution_prepatch.lean` fails for the RIGHT reason: exit 1, unsolved goals on both bug branches — `Except.error "Invalid fill method" = Except.ok key` and `Except.ok (filter …) = Except.ok key`. Byte-identical contract (`same_spec=True`); only impl region differs.
- Spec-too-weak probe (fresh regeneration): wrong impl (drop `method`-named entries) `same_spec=True`, exit 1; positive control (foldr identity rebuild) `same_spec=True`, exit 0.

## Concrete defects
None. No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no leak.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

> atk_9 (subtle: empties the label list only for a `method`-named dim — the exact kind of data corruption the bug causes) shares the spec and FAILS. The spec catches even label-level corruption, not just dim drops.
>
> I have enough evidence. Let me finalize my verdict.
>
> VERDICT
>
> G-EQ: SOUND. spec-strength: TIGHT.
>
> Bundle: pydata__xarray-4695. Spec (frozen, byte-identical across all attacks):
> `method labelSelect (key : List (String × Label)) return (out : Except String (List (String × Label))) ensures out = Except.ok key`
> Impl region in Solution.lean: `return Except.ok key`. `Label = List String`. No axioms, no deep-model refs (meta.json `axioms=[]`, `deep_model_references=[]`); G-AX legitimately skipped.
>
> 1. SPEC-TOO-WEAK PROBE (machine-checked). 9 wrong impls + 1 positive control, all confirmed `same_spec(Solution, atk)=True` (only impl region changed). Verify via `scripts/lean_verify.sh ...`:
> - atk_1 (= the prepatch bug: reject if a `method` dim present, else drop reserved-named dims): same_spec True, exit 1. Rejected by `ensures out = Except.ok key` on both branches (`Except.error ... = Except.ok key` and `Except.ok (filter ...) = Except.ok key`).
> - atk_2 (silently drop `method`-named entries): True, exit 1 — `Except.ok (filter (·.1≠"method") key) = Except.ok key` unprovable.
> - atk_3 (reorder: `key.reverse`): True, exit 1 — `Except.ok key.reverse = Except.ok key` unprovable.
> - atk_4 (always reject): True, exit 1 — `Except.error ... = Except.ok key`.
> - atk_5 (return `Except.ok []`): True, exit 1.
> - atk_6 (keep only head entry): True, exit 1 — `Except.ok [i] = Except.ok key`.
> - atk_7 (clobber every label list to `["a"]`): True, exit 1 — label corruption caught.
> - atk_9 (subtle: empty the label list of only the `method`-named dim): True, exit 1 — even per-label data loss caught.
> - POSITIVE CONTROL atk_8 (structurally different correct impl: `key.foldr (· :: ·) []` rebuilding the identity): True, exit 0 — VERIFIES. Spec is non-vacuous.
> No wrong impl verified. The single equality post-condition `out = Except.ok key` pins the output to the input exactly, so it rejects every form of corruption: rejection, drop, reorder, truncation, and label-level data loss — exactly the failure modes the issue describes.
>
> 2. REFINEMENT AUDIT. refinement.md steps A1 (param R) and A2 (R+I) are R/I only; §C explicitly establishes no A-tagged op and no kind-3 (the changed op — kwargs-splat → positional dict — is directly expressible as "apply the whole mapping," which the spec pins). The "changed inexpressible op hand-waved" failure mode is absent: the selection engine is neither axiomatized nor modeled; its effect is the deterministic function of the applied mapping that G-CONF executes against the REAL patched `da.loc[key]`. Solution_prepatch.lean fails for the RIGHT reason (verified exit 1) — byte-identical to atk_1, the discriminating `method`-reject + reserved-drop branches diverging from `Except.ok key`, i.e. the exact bug and exactly what F2P `test_loc_dim_name_collision_with_sel_params` exercises. No verifying model whose refined patch would fail to resolve: the abstract identity ⇔ "every entry applied unchanged" is bridged to real selected values/dims/coords by G-CONF (100000 cases, seed=4695, 0 disagreements, reserved names forced).
>
> 3. UNGROUNDED-ORACLE PROBE. The postcondition references the input `key`, not an opaque/axiomatized answer-key — there is no opaque oracle symbol to echo. "Return the input unchanged" is the genuinely correct behavior for this fix (the patch's whole effect is that the applied mapping equals the supplied mapping), not a cheat: any impl that alters the mapping fails (atk_1-7,9). No echo of an axiomatized symbol can discharge the goal without doing the real (identity) work. Not too weak.
>
> Files: attacks at atk_1.lean … atk_9.lean (atk_8 = positive control); base = benchmark-verified/pydata__xarray-4695/velvet/Solution.lean.
>
> Note: the helper `swebench_lean.markers.spec_view`/`same_spec` take the file CONTENT as args (not a path); be sure attack files are freshly regenerated before checking (a stale /tmp file from a prior session initially produced bogus `same_spec=False` results until regenerated). After regeneration every result above is reproducible.

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

> Audit complete. All evidence gathered.
>
> VERDICT: faithfulness = FAITHFUL, G-AX = VACUOUS
>
> Bundle: benchmark-verified/pydata__xarray-4695/velvet
>
> FAITHFULNESS = FAITHFUL
> - Modeled function: `labelSelect` ↔ `_LocIndexer.__getitem__` (`DataArray.loc[key]`), changed line `dataarray.py:199` (`sel(**key)` → `sel(key)`). Spec: `out = Except.ok key` — every entry of the indexer mapping is applied as a (dimension, labels) request regardless of name (no entry diverted to a `sel` option, dropped, or rejected). This is exactly the issue's intent ("the name of the dimension should be irrelevant") and exactly what the F2P test forbids.
> - F2P test: `test_loc_dim_name_collision_with_sel_params` — `dims=["dim1","method"]`, `da.loc[dict(dim1=["x","y"], method=["a"])]` expecting `[[0],[1]]`. The dimension named `method` is the discriminating subtlety (collides with `sel`'s `method=` option).
> - Docker evidence (post-gold, in-container): the REAL patched `da.loc[...]` on the exact F2P input returns `dims=['dim1','method']`, `values=[[0],[1]]` — MATCH_F2P True. The spec's R-refinement shadow (gather by the applied mapping = whole `key`) produces `[[0],[1]]` — SHADOW==real True. So spec output == real post-gold output on the F2P input.
> - G-CONF re-run independently: shadow of `labelSelect` (`out=Except.ok key`, never calling `.sel`/`.loc`) agrees with real patched `da.loc` on 100,000 fuzzed inputs, 0 disagreements, with all four reserved names (`method`/`tolerance`/`drop`/`indexers`) exercised at 60% bias. Domain (1-3 dims, list-valued label subsets, reserved+ordinary names) covers the F2P shapes.
> - Discrimination is real, not cosmetic: prepatch (no gold) on the F2P input RAISES `TypeError: method must be a string` (the issue's bug class); the prepatch Lean model returns `Except.error`/reserved-drop and FAILS verification (unsolved goals on both branches), while `same_spec(Solution, prepatch)=True` — the contract is byte-identical, only the impl region differs. So the frozen spec genuinely sees the defect.
> - No spec-too-strong / drift observed: the spec is not narrower than the post-gold behavior on the modeled domain, and the F2P expected output is produced exactly.
>
> G-AX = VACUOUS
> - No `axiom_check.py` in the bundle; `meta.json` `axioms=[]`, `deep_model_references=[]`. Solution.lean declares no axioms (axioms region is a comment only). The changed behavior (kwargs-splat → positional dict routing) is modeled directly as the identity carry-through, not via any axiomatized callee. No axiom-soundness trust point exists.
>
> Cross-checks: Solution.lean verifies clean (exit 0, no sorry); prepatch fails as expected (exit 1).

## Sub-review 3 — LEAKAGE (verbatim)

> Spec is frozen between Solution and prepatch (G-DIFF integrity holds — the prepatch differs only in the elided impl).
>
> My leakage audit is complete. Final verdict:
>
> NO-LEAKAGE
>
> Reconstruction attempt from the spec view alone: The spec view describes a "label-based selection" routine `labelSelect` taking `key : List (String × Label)` (a dimension-name → label-list mapping) and pins `out = Except.ok key` — i.e. the whole mapping must be applied as the dimension/label request "REGARDLESS of the textual dimension names involved," with no entry "omitted, re-purposed, or rejected," even when a dimension name "happens to coincide with an option of the selection routine." From this alone an attacker can only reconstruct what the PUBLIC problem statement already states verbatim: that naming a dimension "method" wrongly triggers the selection function's `method=` option ("Invalid fill method ...") and that "the name of the dimension should be irrelevant" / "the dims are given to another method in unsanitized form." The spec view does NOT disclose the patched file (`xarray/core/dataarray.py`), the patched symbol (`_LocIndexer.__getitem__`), the actual fix mechanism (`self.data_array.sel(**key)` → `self.data_array.sel(key)`, kwargs-splat → positional dict via `either_dict_or_kwargs`), the four reserved parameter names (`indexers`/`method`/`tolerance`/`drop` — only `method` is public, and the spec view names none of them, deferring to the elided impl), or any diff line. The model name `labelSelect` is generic and does not echo a repo symbol.
>
> Checks performed: token scan of the spec view found no `**`/splat/positional/`either_dict_or_kwargs`/`_LocIndexer`/`__getitem__`/`dataarray.py`/`indexers` (only "sel"/"Select" as English inside `labelSelect`/`selection`). The discriminating behavior — the dimension-name/option collision — is fully present in the public `problem_statement` (the "Invalid fill method" error and the "given to another method in unsanitized form" diagnosis), so this is NOT even a relaxed-leakage case. The spec view stays at problem-statement altitude: it pins the public contract ("name should be irrelevant" = "apply the whole mapping") without revealing the gold edit.
>
> Supporting confirmations (not part of the leakage mandate but verified): Solution.lean verifies clean (exit 0); `same_spec(Solution, Solution_prepatch) = True` (spec is frozen, prepatch diverges only in the elided impl). No leaking token to quote — none exists.
>
> Files reviewed (all absolute): benchmark-verified/pydata__xarray-4695/velvet{Solution.lean, Solution_prepatch.lean, patch.diff, refinement.md, mapping.md, instance.json, meta.json}.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Attacker (2) faithfulness-break: sought an input in the modeled domain where the modeled function `labelSelect(key) = Except.ok key` disagrees with the real patched callee `_LocIndexer.__getitem__` (`DataArray.loc[key]`, changed line dataarray.py:199 `sel(**key)`->`sel(key)`). Found none.

**Setup verified:** worktree is POST-patch (source shows `return self.data_array.sel(key)`; F2P `da.loc[dict(dim1=['x','y'],method=['a'])]` returns dims=['dim1','method'] vals=[[0],[1]]). Ran G-CONF (conformance_check.py) against this REAL patched repo: `G-CONF OK ... 100000 inputs (seed=4695), 0 disagreements`, exit 0, reserved names exercised.

Drift probes (the too-strong axis) all agree with real callee within the modeled domain (mapping.md §2 bijection = normalized indexer mapping over existing coord labels):
- All four reserved dim names (method/tolerance/drop/indexers) => whole mapping applied, Except.ok key. 
- key order != array dim order: real result unchanged (Except.ok key holds regardless of textual name/order).
- requested label order preserved (dim1=['c','a'] -> coord ['c','a']); duplicate labels preserved; scalar vs singleton-list consistent with Label=List String.
- Out-of-domain error paths (invalid label -> KeyError, nonexistent dim -> KeyError, empty label list -> empty selection) are OUTSIDE the modeled input domain (valid coordinate labels over existing dims); the spec deliberately models the success/routing behavior the fix targets. Not drift.

**Spec integrity:** same_spec(Solution, Solution_prepatch)=True with velvet LanguageTables (byte-identical contract; only impl region differs). Solution.lean verifies exit 0. Solution_prepatch.lean fails exit 1 with the expected unsolved goals on both bug branches (Except.error 'Invalid fill method' = Except.ok key; Except.ok (filter reserved) key = Except.ok key), confirming the frozen spec genuinely sees the defect. No axioms/deep-model refs => no axiom trust point. Spec is neither too strong nor drifting: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Leakage check:** does the consumer spec view disclose the gold edit (self.data_array.sel(**key) -> self.data_array.sel(key), i.e. kwargs-splat -> positional dict) beyond what the public problem_statement already reveals? hints_text is excluded from the baseline (and it is where the one-line fix is literally spelled out).

**Verified:** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend()) == True — the spec region (imports/set_option/axioms/pure/pre/post + method signature + `ensures out = Except.ok key`) is byte-identical between gold and the G-DIFF discriminator; the extra pre-patch logic lives entirely inside the elided impl region. Spec-view projection confirmed clean (impl/proof elided).

Baseline (problem_statement, public) already discloses more than the spec: a dimension named `method` breaks `.loc`; 'the name of the dimension should be irrelevant'; the 'Invalid fill method' error; and the diagnosis that dims are being fed to another method 'in unsanitized form' (i.e. a dim name is consumed as an option).

Spec view content assessed line by line:
- `ensures out = Except.ok key` and the docstring ('EVERY entry ... honoured ... REGARDLESS of the textual dimension names', 'a dimension whose name happens to coincide with an option of the selection routine must NOT cause that entry to be diverted/dropped/rejected') restate the problem_statement's behavioural requirement ('name should be irrelevant'). This is at or below the disclosure level of the public statement.
- The spec is strictly MORE abstract than problem_statement in that it does not even name `method`, and it does not enumerate the extra reserved names {tolerance, drop, indexers} — those appear only in mapping.md/refinement.md (auditor docs, not consumer-visible) and in hints_text (excluded).
- Crucially, the spec view does NOT reveal the gold MECHANISM: no mention of kwargs-splat vs positional passing, `sel`'s parameter list, or `either_dict_or_kwargs`. The behavioural post-condition admits many distinct fixes (rename/sanitize dims, pass positionally, special-case reserved names); it does not uniquely reconstruct the one-line `**key`->`key` change.

Axioms/pure region carries only the `Label := List String` abbrev and prose describing the R-refinement rationale — no impl detail leaks. No spec-view line advances past problem_statement toward the gold edit. Consistent with meta.json G-LEAK pass. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
