# P2 adversarial audit — matplotlib__matplotlib-24627

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — matplotlib__matplotlib-24627", before this corpus
> rendered one section per audit role. It is kept verbatim because it is the
> only account of that round that ships in this bundle, and it is NOT this
> cell's record. The record is the audit gate entries in the `meta.json` beside
> this file, which are the source of truth for the cell's status; each role
> section below publishes its gate's `status (recorded)` and `machine verdict`
> straight from that entry. Each round authored and re-ran its own attacks, so
> a count in the text above is that round's own count and not this record's:
> where the two accounts differ, the record governs.

**Overall status: ACCEPTED** (both audit gates pass)

## Per-gate table

| Gate | Verdict | Basis |
|------|---------|-------|
| **G-EQ** | **pass** | G-EQ SOUND AND spec-strength TIGHT AND no kind-3 refinement. Bundle is axiom-free; sole postcondition `out = deparentAll children` is a concrete total functional spec. 7 wrong-impl attacks (all `same_spec=True`) rejected; positive control (structurally distinct correct impl) verifies. No ungrounded oracle (N/A). |
| **G-PANEL** | **pass** | faithfulness FAITHFUL AND G-AX ∈ {SOUND, VACUOUS} (= VACUOUS) AND leakage ∈ {NO-LEAKAGE, RELAXED} (= NO-LEAKAGE). Spec models exactly the patch's observable behavior on the modeled domain `self._children`; verified against real post-gold code across 10 artist kinds + the exact F2P shape, 0 violations; G-CONF OK on 2008 inputs. No axioms / no A-reference deep models. Spec view stays within public problem_statement vocabulary. |

## Independent verification performed by lead auditor

- `results/matplotlib__matplotlib-24627/` is **git-clean** (no modification to bundle files).
- `Solution.lean` verifies: **exit 0**, no sorry.
- `Solution_prepatch.lean` genuinely fails on the discriminating clause: unsolved goal
  `⊢ result_1 = deparentAll children` under case `«ensures_1: out = deparentAll children»` (exit 1). Real G-DIFF.
- `meta.json`: `axioms: []`, `deep_model_references: []`; `axiom_check.py` only guards the empty inventory and exits 0.
- meta.json records all functional gates green (G-VERIFY/G-DIFF/G-MUT 14/14/G-CONF 2008-input/G-AX) — consistent with the sub-reviews.

## Concrete defects

**None.** No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak was found. The single trust point is the R/I bijection (`.axes`/`.figure` is-None ↔ `hasAxes`/`hasFigure = false`), which is the falsifiable leg checked by G-CONF against the real patched `clear()` (0 disagreements on 2008 fuzzed inputs). No fix required.

## Spec summary

Single method `clearAxes (children : List Artist) return (out : List Artist)` with one postcondition `ensures out = deparentAll children`, where `deparent a = {hasAxes := false, hasFigure := false}` and `deparentAll` maps it per-element (length- and order-preserving). The postcondition pins BOTH links to false for every former child — the decisive property the issue requires ("cla()/clf() should unset the `.axes` and `.figure` attributes of deparented artists").

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (quoted verbatim)

> VERDICT: matplotlib__matplotlib-24627 — G-EQ = SOUND, spec-strength = TIGHT.
>
> Bundle is axiom-free (zero consumed axioms, zero A-reference deep models; axiom_check.py + meta.json confirm empty inventory). The single method `clearAxes (children : List Artist) return (out : List Artist)` has one postcondition: `ensures out = deparentAll children`, where `deparent a = {hasAxes := false, hasFigure := false}` and `deparentAll` is the per-element map. This is a fully-determined, total functional spec — there is no opaque/axiomatized oracle to echo, so the ungrounded-oracle probe is N/A (nothing to discharge a postcondition against an answer-key; `deparent`/`deparentAll` are concrete total Lean defs).
>
> Setup note: a separate `build_all` run (swebench-lean env) was concurrently writing `*_NNNNN.lean` and clobbered my first `/tmp` scratch files; I re-ran in an isolated dir. results/ never modified (git clean).
>
> Spec-too-weak (machine-checked). All attacks change ONLY the impl region (and proof body, both elided from spec_view); same_spec(Solution, atk_n) = True for every one. Verify via `lean_verify.sh ...`:
>
> - atk_1 (PREPATCH bug: `result := a :: result`, no deparent): same_spec True, exit 1. Residual `result_1 = deparentAll children` under case «ensures_1: out = deparentAll children» with `result = List.drop i children` — unprovable.
> - atk_2 (identity, `return children`): same_spec True, exit 1. Bare-loom_solve residual is exactly `⊢ children = deparentAll children` under case «ensures_1: out = deparentAll children». REJECTED by the ensures clause.
> - atk_3 (`return []`): same_spec True, exit 1. `¬ deparentAll children = []` — wrong length for nonempty input.
> - atk_4 (per-element, unsets hasAxes but keeps `hasFigure := a.hasFigure`): same_spec True, exit 1. `result_1 = deparentAll children` fails — REJECTED.
> - atk_5 (loop bound `length - 1`, drops one artist): same_spec True, exit 1. Length mismatch vs `deparentAll children`.
> - atk_6 (`deparent a :: deparent a :: result`, double length): same_spec True, exit 1. Length mismatch.
> - atk_7 (`children.map (fun _ => {hasAxes := false, hasFigure := true})`, the half-fix): same_spec True, exit 1. Residual `List.replicate children.length {hasAxes := false, hasFigure := true} = deparentAll children` fails because deparentAll forces hasFigure = false. This is the decisive half-fix attack — proves the postcondition pins BOTH links, not just `.axes`.
>
> POSITIVE CONTROL (non-vacuity): atk_pos — structurally different correct impl `return children.map deparent` (forward map instead of the backward `while`-fold), proof by induction. same_spec True, exit 0 (VERIFIES). Spec is satisfiable.
>
> Rejecting clause for every wrong impl: the sole postcondition «ensures_1: out = deparentAll children». Because `deparentAll` is a concrete total function forcing every output element to `{hasAxes:=false, hasFigure:=false}` and preserving length+order, it simultaneously catches: no-deparent (atk_1/2), wrong length (atk_3/5/6), and partial-deparent leaving one link set (atk_4/7).
>
> Refinement audit. refinement.md has only I and R legs (A1 R, A2 I+R, A3 I, A4 R+I) — no kind-3 hand-waved inexpressible op; the genuinely-changed op (unset both links on each former child) is modeled deeply as `deparent`/`deparentAll`, not behind an axiom. The R/I bijection (mapping.md §2: `.axes`/`.figure` is-None ↔ hasAxes/hasFigure = false) is the only trust point and is the falsifiable leg checked by G-CONF (conformance_check.py drives the REAL patched `Axes.clear()` on 2008 fuzzed inputs, 0 disagreements). Solution_prepatch.lean (atk_1) fails for the right reason — the discriminating ensures clause, not an unrelated error.

## Sub-review 2 — FAITHFULNESS + G-AX (quoted verbatim)

> The spec view is clean: impl elided, postcondition `out = deparentAll children` is on a pure independently-defined function. No leak, no smuggled implementation. The contract is a genuine, falsifiable specification of the patch's observable behavior.
>
> **Faithfulness assessment:**
> - The F2P test (`test_cla_clears_children_axes_and_fig`) attaches lines + image to `_children`, calls `ax.clear()`, asserts each artist's `.axes is None` and `.figure is None`.
> - The spec models exactly this: `clearAxes children = deparentAll children`, every former child → `(hasAxes=false, hasFigure=false)`.
> - I independently verified against the **real post-gold code** across 10 artist kinds (lines, empty lines, images, patches, collections, bars, errorbars, fill_between, annotations, tables, legends). Every member of `self._children` (the modeled domain per mapping.md §2) is deparented — both links unset — by the post-gold clear. **Zero violations within the modeled domain.**
> - The one "survivor" (a Legend) is **not** a member of `self._children` (it's stored in `ax.legend_`), so it is outside the spec's modeled domain — and the gold patch itself deliberately only deparents `_children`. This is correct, not drift: the spec matches exactly what the patch does on its domain.
> - The spec is not too strong: it doesn't reject any correct behavior. The modeled domain (`_children` as `List Artist` with order preserved) covers the F2P inputs exactly.
>
> **G-AX:** No axioms, no A-reference deep models (meta.json `axioms: []`, `deep_model_references: []`; axiom_check.py only asserts empty inventory). VACUOUS.
>
> **Genuineness checks:** Solution.lean verifies (exit 0, no sorry); prepatch genuinely fails on `result_1 = deparentAll children` (G-DIFF real); spec view is clean (impl elided, postcondition on independently-defined pure `deparentAll`, no leak/circularity).
>
> VERDICT: faithfulness = FAITHFUL; G-AX = VACUOUS
>
> Evidence (Docker, real post-gold code with patch.diff applied): the spec models `clearAxes children = deparentAll children` — every former child returned with `.axes`/`.figure` both unset. Running the REAL patched `clear()` in-container:
> - Bundle conformance_check.py: G-CONF OK on 2008 inputs, 0 disagreements.
> - My independent probe across 10 artist kinds (including the exact F2P shape `ax.plot([],[],[],[]) + [ax.imshow([[1]])]`): every member of `self._children` post-clear has `(.axes is None, .figure is None)` — VIOLATIONS in `_children`: NONE for all cases. F2P_exact: n_children=3, all deparented OK.
> - The only artist surviving with links set is a `Legend`, which is NOT in `self._children` (`legend_in_children=False`; it lives in `ax.legend_`). The gold patch deliberately deparents only `old_children = self._children`, so this is outside the modeled domain (mapping.md §2: domain = `self._children`) — correct, not drift, and not spec-too-strong.
>
> Spec output == real post-gold output on the F2P input shapes and across all probed artist kinds within the modeled domain. The modeled domain (`List Artist` ↔ `self._children`, order-preserved) covers the F2P inputs exactly. Solution.lean verifies (exit 0, no sorry); Solution_prepatch.lean genuinely fails on `result_1 = deparentAll children` (real G-DIFF). Spec view is clean — postcondition is on an independently-defined pure `deparentAll`, no leak or circularity. No axioms or A-reference deep models exist (meta.json `axioms: []`, `deep_model_references: []`); axiom_check.py only guards the empty inventory.

## Sub-review 3 — LEAKAGE (quoted verbatim)

> Solution.lean verifies clean (exit 0, no sorry).
>
> Now let me assess leakage. The spec view references `mapping.md §2` and `plan §5.4` in comments — those are bundle-internal doc pointers, not repo internals, and are standard. No file path, no `_children`/`__clear`/`_base.py`, no `old_children` loop mechanism appears in the spec view.
>
> **Reconstruction attempt from spec view alone:** The spec view tells me: artists have two links `.axes`/`.figure`; clearing the axes must return every formerly-attached artist with both links unset ("deparented"). To reconstruct the gold patch I'd need to know: which function (`__clear`), which collection (`self._children`), and the mechanism (snapshot old list, loop setting `chld.axes = chld.figure = None`). The spec view gives me the *behavior* (unset both attrs on clear) but none of the implementation specifics. However — this behavior is exactly what the public problem_statement already states verbatim: "cla(), clf() should unset the `.axes` and `.figure` attributes of deparented artists." So the spec view reveals nothing the PS does not.
>
> **Token-by-token leakage check:**
> - `.axes`, `.figure` — present in PS title and body.
> - "deparented"/"deparent" — PS title says "deparented artists".
> - `clearAxes` / "clearing the axes" — PS is about `cla()`/clearing axes.
> - "every formerly-attached artist comes back deparented" — PS: "clearing the axes does not [unset]" → the fix unsets them.
> - `hasAxes`/`hasFigure` — direct renderings of the two named attributes.
>
> Nothing in the spec view names: the patched file (`_base.py`), the patched symbol (`__clear`/`_children`), any diff line, or the snapshot-and-loop mechanism. The `mapping.md §2` / `plan §5.4` pointers are bundle-doc references, not repo-symbol echoes.
>
> This is a fully public, symptom-and-fix issue (no hints_text exists — it is empty). The spec view stays within problem_statement vocabulary. This is NO-LEAKAGE, not RELAXED.
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

Faithfulness-break attack: could not construct any input on which the modeled clearAxes disagrees with the real patched callee.

Real callee (gold patch, lib/matplotlib/axes/`_base`.py `__clear`, base_commit 9d22ab09): `old_children, self._children = self._children, []; for chld in old_children: chld.axes = chld.figure = None`. This unconditionally sets BOTH links to None on every element of the former child list, with no branch that could leave a child's .axes/.figure set, and preserves count/order (result collection is not observed).

**Model:** `out = deparentAll children`, where deparentAll maps every artist to {hasAxes:=false, hasFigure:=false} unconditionally, order/length preserved. Bijection (mapping.md §2): .axes is None ↔ hasAxes=false, .figure is None ↔ hasFigure=false, i-th former child ↔ children[i]. Only the set/unset bits of the two links are the F2P-observable contract (test_cla_clears_children_axes_and_fig asserts art.axes is None and art.figure is None for lines+image).

For EVERY input (any count/mix of attached artists, including artists already partially deparented or with only one link set), the real patch drives every former child to (None,None), which the model's per-element deparent reproduces exactly. The spec neither over-claims (no input leaves a link set post-clear in the real code) nor under-claims. No divergence exists.

**Corroboration:** spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with VelvetBackend.language tables). Solution.lean verifies via scripts/lean_verify.sh (exit 0). G-CONF: 0 disagreements over 2008 fuzzed inputs (seed 24627) between the transliterated shadow and the real patched clear() oracle. G-RESOLVE passes. Prepatch (loop returns each artist unchanged) correctly fails the same spec (G-DIFF). No axioms consumed, so no over-approximation surface. The model is a faithful observable projection of the changed op, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage/gold-reconstruction audit for matplotlib__matplotlib-24627 (velvet). Spec region is frozen: markers.same_spec(Solution.lean, Solution_prepatch.lean) == True, and the spec_view region hash matches meta G-HYGIENE (1609843d...). The consumer spec view (Artist{hasAxes,hasFigure}; deparent -> both false; deparentAll; method clearAxes ensures out = deparentAll children) contains NO repo-internal artifacts of the gold edit: scanned and found no `_children`, `__clear`, `_AxesBase`, `old_children`, `self.`, filename `_base.py`, line `1315`, or base_commit. Those identifiers live only in mapping.md/refinement.md, which are not part of the spec view.

The modeled contract exactly paraphrases the PUBLIC problem_statement, not the patch: the issue title is literally "cla(), clf() should unset the `.axes` and `.figure` attributes of deparented artists" and the body shows `a.cla(); print(l.axes)` returning an Axes instead of None. So the observable requirement (on clear, unset BOTH `.axes`/`.figure` links of every former child) is public; even the term 'deparent' is drawn from the issue. The spec discloses nothing about the gold edit's MECHANISM (the `old_children, self._children = self._children, []` snapshot-and-rebind + `for chld: chld.axes = chld.figure = None` loop) beyond the publicly-stated behavior. The Lean while/fold is a proof-shape artifact of the functional model, not a transcription of the Python. G-LEAK gate independently passed (spec view clean). No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
