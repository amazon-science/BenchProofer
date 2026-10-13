# P2 adversarial audit — astropy__astropy-12907

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — astropy__astropy-12907", before this corpus
> rendered one section per audit role. It is kept verbatim because it is the
> only account of that round that ships in this bundle, and it is NOT this
> cell's record. The record is the audit gate entries in the `meta.json` beside
> this file, which are the source of truth for the cell's status; each role
> section below publishes its gate's `status (recorded)` and `machine verdict`
> straight from that entry. Each round authored and re-ran its own attacks, so
> a count in the text above is that round's own count and not this record's:
> where the two accounts differ, the record governs.

**Overall status: ACCEPTED**

Both decision gates pass. The frozen spec `out = blockDiag left right lc rc`
is a closed equality to a fully-concrete pure function (no axioms), it is
sound and tight against every wrong-impl attack, it faithfully reproduces the
post-gold `_cstack` array/array branch (G-CONF 0 disagreements over 100007
inputs + exact F2P discriminating shapes), and the spec view leaks no
beyond-public-problem-statement discriminator.

## Per-gate table

| Gate | Verdict | Basis |
|---|---|---|
| **G-EQ** | **pass** | G-EQ SOUND (every behaviorally-wrong impl rejected by the single `ensures: out = blockDiag left right lc rc` clause; 8 attack impls all `same_spec=True` + verify exit=1) AND spec-strength TIGHT (postcondition functionally pins the entire output; a structurally-different correct impl still verifies → non-vacuous) AND no kind-3 refinement (the changed op — lower-right block carries `right`'s own rows vs constant fill — is modeled concretely in `widenLeft`/`blockDiag`, refinement.md A1–A5 all R/I). |
| **G-PANEL** | **pass** | FAITHFUL (spec == post-gold `_cstack` array/array branch; G-CONF in-container with `apply_gold=True` = 0 disagreements over 100007 inputs seed=12907; F2P tests cm8/cm11 provably hit the (ndarray,ndarray) branch; model matches `cm_4d_expected`) AND G-AX VACUOUS (empty axioms region, no axiom_check.py, mapping.md §3 = 0 consumed axioms; concrete R/I list arithmetic) AND leakage NO-LEAKAGE (spec view carries no repo filename/symbol/numpy/diff-line; the only discriminator — "block keeps its own internal structure, not a constant fill" — is exactly what the public problem_statement's example matrices already show). |

Per the rubric: G-EQ = pass iff (SOUND ∧ TIGHT ∧ no kind-3); G-PANEL = pass
iff (FAITHFUL ∧ G-AX∈{SOUND,VACUOUS} ∧ leakage∈{NO-LEAKAGE,RELAXED}). Both
satisfied.

## Concrete defects

**None.** No verifying-but-wrong impl, no unfaithful divergence, no unsound
axiom (none exist), no leak. No fix required.

## Lead-auditor independent re-checks

- `bash scripts/lean_verify.sh results/astropy__astropy-12907/Solution.lean` → **exit 0** (verifies).
- `bash scripts/lean_verify.sh results/astropy__astropy-12907/Solution_prepatch.lean` → **exit 1**, unsolved goal on the discriminating clause:
  ```
  case «ensures_1: out = blockDiag left right lc rc»
  ⊢ List.map (widenRight rc) left ++ List.map (fun x => List.replicate lc 0 ++ List.replicate rc 1) right
      = blockDiag left right lc rc
  ```
  i.e. the pre-patch constant `= 1` fill (`replicate lc 0 ++ replicate rc 1`)
  cannot equal the block-diagonal carrying `right`'s own rows — exactly the bug
  the issue reports, failing for the RIGHT reason.
- `patch.diff` is the gold patch verbatim: `cright[-right.shape[0]:, -right.shape[1]:] = 1` → `= right`.
- meta.json axioms region empty; G-AX status `skip` (no axioms to fuzz); G-CONF status `pass` (0 disagreements); G-DIFF/G-GOLD/G-MUT/G-RESOLVE all pass.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

> VERDICT: G-EQ = SOUND, spec-strength = TIGHT.
>
> Bundle: astropy__astropy-12907 (`_cstack` array/array branch fix: `cright[-rr:,-rc:] = 1` → `= right`). Modeled by `combineParallel` with the single postcondition `ensures out = blockDiag left right lc rc`, a closed equality to a concrete pure function (no axioms — `axioms` region empty).
>
> SPEC-TOO-WEAK (machine-checked). Copied Solution.lean, changed ONLY the `-- impl` region, kept axioms/pure/pre/post byte-identical. All shared the spec (`same_spec=True`) and the original + a structurally-different correct impl verify; every wrong impl is rejected by the same `ensures` clause. Note: my first attack batch was silently overwritten in shared /tmp by a concurrent process (files came back containing other instances' content — `collectLoader`/`selectedTarget`); I re-ran the entire battery in a private `mktemp -d` dir. Final results:
>
> - positive control (orig impl): same_spec=True, verify exit=0.
> - positive control (CORRECT, structurally different — `widenLeft`/`widenRight` named, blocks computed in reversed let-order): same_spec=True, verify exit=0 → spec non-vacuous.
> - atk_1 PREPATCH BUG (lower block = constant `replicate lc 0 ++ replicate rc 1`, all-ones): same_spec=True, exit=1.
> - atk_2 (blocks concatenated in wrong order `lower ++ upper`): same_spec=True, exit=1.
> - atk_3 (widen wrong sides — left widened left, right widened right): same_spec=True, exit=1.
> - atk_4 (drop the right block): same_spec=True, exit=1.
> - atk_5 (return `[]`): same_spec=True, exit=1.
> - atk_6 (raw `left ++ right`, no zero-padding): same_spec=True, exit=1.
> - atk_7 (pad off-diagonal blocks with ones instead of zeros): same_spec=True, exit=1.
>
> Every wrong impl is rejected by the SAME clause: `«ensures_1: out = blockDiag left right lc rc»` (unsolved goal). The spec functionally pins the entire output, so no behaviorally-wrong impl can satisfy it.
>
> REFINEMENT AUDIT. refinement.md steps A1–A5 are all R or I; no kind-A (no axiomatized callee — confirmed by empty axioms region and mapping.md §3) and no kind-3 (the operation that changed — filling the lower-right block with the right operand's own rows vs a constant — is modeled concretely in `widenLeft`/`blockDiag`, not hand-waved). G-CONF run in-container WITH the gold patch applied (`apply_gold=True`): "G-CONF OK ... 0 disagreements" over 100,007 inputs (seed 12907) — the spec's `blockDiag` matches the patched `_cstack`. (An earlier "G-CONF FAIL" I saw was my own harness misuse: I omitted `apply_gold`, so the oracle ran the unpatched buggy `_cstack`; that run actually confirmed `blockDiag` correctly diverges from the pre-patch all-ones behavior.) Solution_prepatch.lean fails for the RIGHT reason: unsolved goal `... = blockDiag left right lc rc` with lower block `replicate lc 0 ++ replicate rc 1` — exactly the pre-patch `= 1` bug, the discriminating clause.
>
> UNGROUNDED-ORACLE PROBE. No opaque/axiomatized symbol exists; the postcondition equals a fully-concrete pure function (`blockDiag` = `(left.map (widenRight rc)) ++ (right.map (widenLeft lc))`), so there is no answer-key oracle a wrong impl could echo. The only trust point is refinement fidelity, discharged by G-CONF (passes) + the prepatch discriminator (fails correctly).

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

> The model's `blockDiag` output exactly equals the real post-gold `_cstack` output on the discriminating diagonal-right-block cases (which is precisely the cm8 `rot & (sh1 & sh2)` F2P shape: `(2,2) & diag(2,2)` → the exact F2P expected matrix `cm_4d_expected`). The prepatch's constant `= 1` fill would produce `[0,0,1,1]/[0,0,1,1]` for the lower block instead of the diagonal, which is the bug the issue reports — and the prepatch correctly fails verification.
>
> I have all the evidence needed. Summary of my findings:
>
> **Faithfulness:**
> - The spec models `_cstack`'s array/array branch as `out = blockDiag left right lc rc` (upper block = left rows zero-padded right, lower block = right rows zero-padded left).
> - Real post-gold `_cstack` array/array branch: `cleft[:lr,:lc]=left` (upper), `cright[-rr:,-rc:]=right` (lower), `np.hstack`. Row-wise this is exactly `widenRight`/`widenLeft`/`++` = `blockDiag`.
> - F2P tests (cm8=`rot&(sh1&sh2)` → compound_model6, cm11=`rot&sh1&(scl1&scl2)` → compound_model9) genuinely exercise the array/array branch (confirmed by instrumentation: multiple `(ndarray,ndarray)` `_cstack` calls).
> - Model output == real post-gold output on 100007 fuzzed inputs (0 disagreements, in-container) AND on the exact discriminating F2P shapes (diagonal right block) — the spec is neither too strong nor drifting. The `require` rectangularity preconditions are sound (numpy coord matrices are always rectangular).
>
> **G-AX:** No `axiom_check.py`, empty axioms region, mapping.md §3 confirms zero consumed axioms / zero A-references. The whole assembly is concrete R/I list arithmetic. → VACUOUS.
>
> **Mechanical re-checks I ran independently:** Solution.lean verifies (exit 0); Solution_prepatch.lean fails verification (exit 1, unsolved `out = blockDiag` goal); same_spec(Solution, prepatch)=True (genuine spec-sharing G-DIFF); G-CONF re-run against post-gold = 0 disagreements.
>
> FAITHFULNESS: FAITHFUL — The frozen spec `out = blockDiag left right lc rc` exactly reproduces the real post-gold `astropy.modeling.separable._cstack` array/array branch. Docker evidence: re-ran conformance_check.py in-container against the gold-patched repo (apply_gold=True) → "G-CONF OK: R/I shadow agrees with patch.diff behaviour on 100007 inputs (seed=12907), 0 disagreements." The two F2P tests (compound_model6 = `rot & (sh1 & sh2)`, compound_model9 = `rot & sh1 & (scl1 & scl2)`) provably take the array/array branch (instrumented `_cstack` shows repeated (ndarray,ndarray) calls), and post-gold output matches the F2P expected matrices. Direct model-vs-real comparison on the discriminating diagonal-right-block shape `[[1,1],[1,1]] & [[1,0],[0,1]]` yields the exact F2P `cm_4d_expected` matrix in both — model and real post-gold agree. The prepatch's constant `=1` fill (the real bug) is faithfully reproduced and correctly fails G-DIFF. Spec is not too-strong (require rectangularity is always satisfied by real numpy coord matrices) and does not drift.
>
> G-AX: VACUOUS — no axiom_check.py, empty axioms region, mapping.md §3 declares 0 consumed axioms and 0 A-references; the entire block-diagonal assembly is concrete R/I list arithmetic, not an axiomatized callee. Nothing to fuzz for soundness.
>
> Independent mechanical confirmations: Solution.lean verifies (exit 0); Solution_prepatch.lean fails verification (exit 1, unsolved `out = blockDiag` goal); same_spec(Solution, Solution_prepatch)=True.

## Sub-review 3 — LEAKAGE (verbatim)

> Now I have everything I need for the leakage audit. Let me reason carefully.
>
> **Gold patch**: in `_cstack`, the array-branch fill changes `cright[...] = 1` to `cright[...] = right`. The discriminating behavior: the lower-right block of the block-diagonal matrix must carry the right operand's own dependency rows, not a constant all-ones fill.
>
> **What the public problem_statement reveals:**
> - `separability_matrix` for parallel composition (`&`) of models
> - The matrix is block-diagonal: each model's outputs depend only on its own inputs
> - The BUG is precisely shown: when nesting, the lower-right block becomes all-True (`[[True,True],[True,True]]`) instead of the correct diagonal `[[True,False],[False,True]]`
> - The correct expected output is the block-diagonal where each block preserves its own structure
>
> So the public issue literally shows: the buggy output is the all-ones lower-right block, and the correct output preserves the inner block's own (diagonal) structure. This is exactly the gold fix's discriminator — "carry the right operand's own structure, not a constant fill."
>
> **Now the spec view leakage assessment:**
>
> The spec view describes a generic block-diagonal matrix assembly for parallel composition of two transforms. Let me check each potential leak vector:
>
> 1. **Patched file/symbol**: The spec view names `combineParallel`, `blockDiag`, `widenRight`, `widenLeft`. None of these echo `_cstack`, `separable.py`, `cright`, `np.hstack`, or `np.zeros`. No repo symbol/filename leaks. Good.
> 2. **A diff line**: No `= right` / `= 1` / numpy syntax appears. The fix is modeled abstractly as "each block keeps its own internal dependency structure" via `widenLeft lc row = replicate lc 0 ++ row`. This is the abstract mathematical content, which is exactly what the public issue describes (the nested block must keep its own diagonal).
> 3. **Repo-symbol-echoing identifier**: `combineParallel`, `blockDiag` are generic CS/linalg names, not astropy-specific. "transforms," "dependency matrix," "parallel composition" are domain-neutral descriptions consistent with the public separability problem framing.
> 4. **Bug/fix narration**: The docstring says "Each block keeps its own internal dependency structure; the off-diagonal blocks are zero." This is the spec's CORRECT behavior. Is this beyond the public issue? No — the public issue explicitly shows that the correct separability matrix is block-diagonal where each nested block preserves its own structure (`[[True,False],[False,True]]`), and the bug is precisely the off-diagonal/all-ones contamination. The spec view does NOT narrate the bug ("= 1 was wrong") nor the fix site.
>
> **Reconstruction attempt from spec view alone**: From the spec view I learn: "to compose two dependency matrices in parallel, build a block-diagonal where the lower-right block carries the right operand's own rows." Could I locate `_cstack` and write the gold patch? The spec view gives no file, no function name, no `cright`, no numpy. I would need the public problem_statement (which names `separability_matrix`, `separable`, the `&` composition) to find the file. Even then, the spec view tells me the correct behavior is what the public issue already states (block preserves own structure). The actual one-line fix location (`= 1` → `= right`) is NOT derivable from the spec view; it requires reading the source.
>
> The key test: does the spec view reveal the gold edit BEYOND what the public problem_statement already says? The public problem_statement ALREADY shows: the bug is the lower-right block being all-True instead of preserving the inner model's own diagonal structure. The spec view's "block keeps its own internal dependency structure" is a faithful, abstract restatement of exactly that publicly-visible expected output. It adds nothing about the patched symbol, the `= 1`/`= right` line, or the file.
>
> This is a clean NO-LEAKAGE. The discriminator (preserve own structure vs constant fill) is fully present in the public problem_statement's own example matrices.
>
> Let me confirm there's no in-bundle relaxed-leakage claim (meta.json shows G-LEAK status "pass", not "relaxed"), which is consistent.
>
> NO-LEAKAGE
>
> Reconstruction attempt from the spec view alone: The spec view describes only a generic "block-diagonal dependency-matrix assembly for the parallel composition of two transforms" — operating on `List (List Int)` via `combineParallel`/`blockDiag`/`widenRight`/`widenLeft`. It carries no repo filename, no Python symbol, no numpy construct, and no diff line. From the spec view alone I cannot locate the edit: there is no echo of `separable.py`, `_cstack`, `cright`, `np.hstack`, `np.zeros`, or the `= 1`→`= right` line. To find the file I would still need the public `problem_statement` (which itself names `separability_matrix`/`separable` and the `&` composition). The one-line gold fix is not reconstructible from the spec view — it requires reading the source.
>
> Beyond-PS check: The only behavioral discriminator the spec encodes is "the lower-right block carries the right operand's OWN dependency rows (`widenLeft lc row = replicate lc 0 ++ row`), not a constant fill — each block keeps its own internal dependency structure." This is exactly what the public `problem_statement` already demonstrates: it explicitly shows the BUGGY output as an all-`True` lower-right block (`[[True,True],[True,True]]`) and the CORRECT output as the block preserving its own diagonal (`[[True,False],[False,True]]`) for the nested `Pix2Sky_TAN() & (Linear1D & Linear1D)` case. The spec view's docstring is a domain-neutral abstract restatement of that publicly-visible expected behavior; it does not narrate the bug, the `= 1` constant, or the fix site. `hints_text` is empty here, so there is no hidden-only discriminator being smuggled in. No leaking token is present (the identifiers `combineParallel`/`blockDiag`/`widenRight`/`widenLeft`/`left`/`right`/`lc`/`rc` are generic linear-algebra names, not repo-echoing). meta.json records `G-LEAK.status = "pass"`, consistent with this finding (not a relaxed-leakage instance).
>
> Verdict: NO-LEAKAGE

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

Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec with velvet LanguageTables == True; both reduce to the same spec_view: identical axioms(empty)/pure(widenRight/widenLeft/blockDiag)/pre/post + the `ensures out = blockDiag left right lc rc` contract).

The spec models the array/array branch of astropy.modeling.separable.`_cstack` (base_commit d16bfe05a744909de4b27f5875fe0d4ed41ce607). Real patched branch (read verbatim, separable.py:243-245): cright=np.zeros((noutp,right.shape[1])); cright[-rr:,-rc:]=right; return np.hstack([cleft,cright]); with cleft[:lr,:lc]=left and noutp=lr+rr from `_compute_n_outputs`. This is exactly blockDiag: upper = left rows padded right with rc zeros, lower = right rows padded left with lc zeros.

Faithfulness (spec-not-too-strong) evidence:
1. Ran a standalone oracle transliterating the real patched numpy code path against the model on 200,000 fuzzed inputs with entries in [-3,3] (negatives and values >1, well beyond the 0/1 domain) and shapes 1..5 in each dim: 0 disagreements. Also 8 boundary/F2P shapes (rot&sh1, rot&(sh1&sh2), identity, all-zero, single-row/col): all match.
2. The `require ∀ r ∈ left, r.length = lc` / `∀ r ∈ right, r.length = rc` preconditions are sound abstractions, not over-constraints: for every reachable coord_matrix (a real rectangular ndarray with >=1 row) they pin lc=left.shape[1], rc=right.shape[1] exactly — the same widths the real code reads. The only inputs where lc/rc could differ from real shape are empty left/right, which cannot arise (coord_matrix has n_outputs>=1 rows; an empty ndarray would IndexError in real code too, so it is not a real callee input). Hence the contract does not admit an input where the model and real callee are both defined yet disagree.
3. Lean checks: Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (lower block = constant all-ones fill, modeling the pre-patch `=1` bug) FAILS with unsolved goal out=blockDiag — confirming the spec genuinely discriminates the buggy behavior from the fix (G-DIFF non-vacuous).

No A-tagged/axiomatized callee exists (axioms region empty); the whole assembly is concrete numpy primitives (np.zeros/slice-assign/np.hstack) transliterated to list arithmetic, so there is no hidden over-strong contract on an opaque callee. No divergence found: the modeled combineParallel agrees with the real patched `_cstack` on all Requires-satisfying, reachable inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage/gold-reconstruction sub-review for astropy__astropy-12907 (velvet). Gold edit: separable.py `_cstack`, `cright[-rr:,-rc:] = 1` -> `= right` (lower-right block must carry the right operand's own dependency rows, not a constant all-ones fill).

**BYTE-IDENTITY CONFIRMED:** markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. Computed the real spec_view: impl region and proof are elided; consumer sees only the method signature, the two `require` rectangularity clauses, `ensures out = blockDiag left right lc rc`, and the pure defs widenRight/widenLeft/blockDiag. hints_text is EMPTY, so no hidden-only discriminator can be smuggled in.

LEAK-VECTOR SWEEP over the spec view:
(1) Repo tokens: NONE. No `_cstack`, `separable.py`, `cright`, `np.hstack`, `np.zeros`, `= 1`, or `= right`. Identifiers combineParallel/blockDiag/widenRight/widenLeft/left/right/lc/rc are generic linear-algebra names, not repo-echoing.
(2) Diff line: NONE. The `=1`->`=right` change and the constant-fill bug appear only in the ELIDED prepatch impl, never in the spec view.
(3) Behavioral discriminator: spec encodes 'block-diagonal where each block keeps its OWN internal dependency structure; off-diagonal blocks zero.' The public problem_statement ALREADY shows exactly this - correct diagonal [[True,False],[False,True]] vs the buggy all-True lower-right block for the nested Pix2Sky_TAN() & (Linear1D & Linear1D) case. The spec docstring is a domain-neutral abstract restatement of the publicly-visible expected output; it does not narrate the bug, the constant fill, or the fix site.
(4) Reconstruction: from the spec view alone one cannot locate the file/symbol or derive the one-line fix; that needs the public PS (which names separability_matrix/separable/the `&` composition) plus reading the source. Nothing beyond problem_statement is added.

meta.json G-LEAK.status = pass, consistent. Clean NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
