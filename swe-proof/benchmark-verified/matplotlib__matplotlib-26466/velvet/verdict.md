# P2 adversarial audit — matplotlib__matplotlib-26466

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — matplotlib__matplotlib-26466", before this corpus
> rendered one section per audit role. It is kept verbatim because it is the
> only account of that round that ships in this bundle, and it is NOT this
> cell's record. The record is the audit gate entries in the `meta.json` beside
> this file, which are the source of truth for the cell's status; each role
> section below publishes its gate's `status (recorded)` and `machine verdict`
> straight from that entry. Each round authored and re-ran its own attacks, so
> a count in the text above is that round's own count and not this record's:
> where the two accounts differ, the record governs.

**Overall status: ACCEPTED**

Both decision gates pass. No concrete counterexample (no verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak) was found by any of the three blind sub-reviews or by independent auditor re-checks.

## Per-gate table

| Gate | Verdict | Basis |
|---|---|---|
| **G-EQ** | **pass** | G-EQ SOUND **and** spec-strength TIGHT **and** no kind-3 refinement. Discriminating postcondition `ensures ∀ a b : Int, observe out a b = (coords[0]!, coords[1]!)` at both sites; all 6 wrong-impl attacks (`reference`, swapped, constant, dup, one-site-wrong, off-by-one) verify-FAIL while a structurally-different correct impl verifies (positive control). Both prepatch files fail on the right clause. |
| **G-PANEL** | **pass** | faithfulness FAITHFUL **and** G-AX ∈ {SOUND, VACUOUS} (= VACUOUS: empty axiom inventory) **and** leakage ∈ {NO-LEAKAGE, RELAXED} (= NO-LEAKAGE). Spec output == real post-gold output of both changed constructors on F2P float shapes; pre-gold diverges on every input; G-CONF rc=0 over 100007 inputs with gold applied. |

### Sub-verdict roll-up
- G-EQ soundness: **SOUND**
- spec-strength: **TIGHT**
- refinement: **no kind-3** (all R/I; changed op modeled deeply via `StoredCoord`/`observe`; `_get_scale` inline is a behavior-preserving refactor, correctly excluded)
- faithfulness: **FAITHFUL**
- G-AX: **VACUOUS** (zero consumed axioms, zero A-reference deep models)
- leakage: **NO-LEAKAGE**

## Concrete defects
None. No fix required.

## Auditor independent re-checks (this synthesis)
- `Solution.lean` verifies, exit 0.
- `Solution_prepatch_1.lean` fails at 70:28 and `Solution_prepatch_2.lean` fails at 93:28, both with `⊢ ∀ (a b : ℤ), observe StoredCoord.reference a b = (coords[0]!, coords[1]!)` unsolved — the discriminating clause, the right reason.
- Independent spec-weakness attack (swap components, `snapshot y x`, both sites) verify-FAILS at 67:28 and 92:28 — spec is not too-weak in the obvious adversarial direction.
- `results/matplotlib__matplotlib-26466/` clean: only the 10 expected bundle files, no stray attack/adv artifacts.
- Leak token scan on `Solution.lean`: no `OffsetFrom`/`Annotation`/`ref_coord`/`text.py`/`matplotlib`/`__init__`/`annotate`/`arrow`. Only `array` occurrences are the verbatim public-problem_statement quote ("the same array is kept instead of a copy") and the generic Lean carrier `Array Int`.
- meta.json: `axioms: []`, `deep_model_references: []` — confirms VACUOUS G-AX.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

All checks pass. Let me do a final review of the refinement audit concerns:

1. **No kind-3 steps**: All steps tagged R/I; the only genuinely-changed op (copy-on-capture) is modeled deeply via `StoredCoord`/`observe`, not hand-waved. The `_get_scale` refactor is correctly excluded as behavior-preserving.

2. **Refactor exclusion soundness**: The `_get_scale` inline produces an identical value (`1.` for "pixels" else `renderer.points_to_pixels(1.)`, vs inlined `1 if ... else renderer.points_to_pixels(1)`). Note: `points_to_pixels(1)` vs `points_to_pixels(1.)` — int vs float arg, but for matplotlib renderers `points_to_pixels` is linear scaling so `1` and `1.0` give the same result. This is observationally inert and the F2P test (`test_annotate_and_offsetfrom_copy_input`) tests copy semantics, not scale. Correctly not modeled.

3. **Type refinement hiding a mismatch**: The bijection `Array Int size=2 ↔ (float,float)` is faithful because the modeled op is pure copy/identity — no arithmetic, ordering, or float precision. G-CONF (with patch) confirms agreement over 10⁵ inputs including the problem-statement reproduction `(-4,1)→(-4,3)`.

4. **Ungrounded oracle**: The postcondition pins `out` to `(coords[0]!, coords[1]!)` — a structural function of the actual input, not an opaque answer-key. `observe` is a concrete inductive function, not an axiom. No echo attack is possible.

Let me verify there's no hidden weakness from `coords[i]!` on out-of-bounds (the `require size=2` guarantees indices 0,1 valid; default-elem panic semantics don't apply).

### Verdict

**G-EQ: SOUND. spec-strength: TIGHT.**

### Spec-too-weak (machine-checked)
Copied `Solution.lean` to, changed ONLY the two `-- impl` regions, left axioms/pure/pre/post byte-identical. All shared the spec (`same_spec=True`).

| attack | wrong impl (both sites unless noted) | same_spec | verify exit | result |
|---|---|---|---|---|
| atk_1 | `return StoredCoord.reference` (**the prepatch bug**) | True | 1 (FAIL) | rejected |
| atk_2 | `snapshot y x` (swapped components) | True | 1 (FAIL) | rejected |
| atk_3 | `snapshot 0 0` (constant) | True | 1 (FAIL) | rejected |
| atk_4 | `snapshot x x` (duplicate first comp) | True | 1 (FAIL) | rejected |
| atk_5 | site A correct, site B `reference` | True | 1 (FAIL) | rejected (B caught) |
| atk_6 | `snapshot (x+1) y` (off-by-one) | True | 1 (FAIL) | rejected |
| **atk_pos** | structurally-different CORRECT (`let y:=coords[1]!; let x:=coords[0]!; let pair:=snapshot x y; return pair`) | True | **0 (VERIFIES)** | positive control passes → spec non-vacuous |

Rejecting clause for ALL wrong impls (at both sites): `ensures ∀ a b : Int, observe out a b = (coords[0]!, coords[1]!)`. The universal `∀ a b` is what does the work: `reference` fails because `observe reference a b = (a,b)` cannot equal the fixed `(coords[0]!, coords[1]!)` for all `a,b`; the snapshot variants fail because their stored components don't equal `(coords[0]!, coords[1]!)`. No wrong impl shares the spec AND verifies.

### Refinement audit
- All refinement.md steps are R or I — no kind-3. The genuinely-changed op (copy-on-capture) is modeled deeply via the `StoredCoord`/`observe` abstraction, not axiomatized. The `_get_scale` inline is a behavior-preserving refactor (identical scale value, single call site, not F2P-discriminated) and is correctly excluded — not swept under an axiom.
- `Solution_prepatch_1.lean` FAILS at line 70 (captureCoordA, `reference`) and `Solution_prepatch_2.lean` FAILS at line 93 (captureCoordB, `reference`) — both on the discriminating postcondition clause, the right reason. Two prepatches because the F2P test exercises both sites independently.
- Type refinement (`Array Int size=2 ↔ float pair`) hides no mismatch: the modeled op is pure component copy/identity (no arithmetic/ordering/float precision), so the exact-Int carrier is faithful.

### In-container differential checks
- **G-CONF with gold patch applied: rc=0** — R/I shadow agrees with the REAL patched constructors on 100,007 inputs (seed 26466, incl. problem-statement reproduction (-4,1)→(-4,3)), 0 disagreements.
- Control: G-CONF run WITHOUT the patch fails (oracle returns the later-mutated values), confirming the bug genuinely reproduces in the real repo and the patch genuinely fixes it.
- **G-AX: rc=0** — axiom/A-reference inventory genuinely empty; nothing to fuzz, no trust point.

### Ungrounded-oracle probe
No echo attack possible: the postcondition pins `out` to `(coords[0]!, coords[1]!)`, a structural function of the actual input carrier — not an opaque answer-key. `observe` is a concrete inductive definition, not an axiomatized oracle. The only `StoredCoord` satisfying `∀ a b` is `snapshot coords[0]! coords[1]!` (confirmed: every non-matching snapshot was rejected).

The single residual trust point is the type bijection in mapping.md §2, which G-CONF checks falsifiably and passes. No axiom trust point exists.

---

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

This is exactly the discriminating behavior I wanted to confirm. The results/ directory is clean (only the original 10 files, no stray adv_check.py).

Summary of findings:

**Faithfulness analysis:**
- The bug: input coordinate arrays (`ref_coord` in `OffsetFrom.__init__`, `xy` in `_AnnotationBase.__init__`) were stored by reference, so later in-place mutation of the array changed the stored coordinate. The gold fix unpacks-and-restores (`x, y = ref_coord; self._ref_coord = x, y`) to detach.
- The spec models this exactly via `StoredCoord`/`observe`: `snapshot` (detached) vs `reference` (aliased), with postcondition `∀ a b, observe out a b = (coords[0]!, coords[1]!)` — pinning the retained pair to capture-time components for ALL later source states. Only the snapshot/copy behavior satisfies it.
- POST-GOLD real code matches spec prediction on ALL probed inputs including the exact float shapes the F2P test uses (`[.5,.5]→[1,1]`, `[.5,.5]→[2,2]`): ALL_MATCH_SPEC True.
- PRE-GOLD (buggy) real code DIFFERS on every input (ALL_MATCH_SPEC False) — the spec genuinely discriminates bug from fix, and both `Solution_prepatch_*.lean` correctly fail verification with the `reference` skeleton.
- The Int carrier is faithful: the modeled op is a pure component copy (no arithmetic/ordering), so integer exact-equality fully captures the contract; float F2P values map cleanly. The unmodeled `_get_scale` inline (edit 3) is a behavior-preserving refactor producing identical scale values, not exercised discriminatingly by the F2P test — correctly omitted.

**G-AX:** axiom_check.py asserts an empty axiom/A-reference inventory; meta declares zero axioms. The only modeled behavior is the *changed* constructors, validated by G-CONF against the real patched code, not by any axiom. No opaque unchanged callee is consumed.

**Docker evidence:** G-CONF passed in-container with gold applied (100007 inputs, 0 disagreements). My independent post-gold oracle confirms `OffsetFrom._ref_coord` and `Annotation.xy` equal the capture-time pair (== spec prediction) on F2P float shapes; pre-gold differs on all.

VERDICT: faithfulness=FAITHFUL, G-AX=VACUOUS

Faithfulness FAITHFUL: spec output (snapshot/detached semantics) == real post-gold output of both changed constructors on the F2P input shapes (including the exact `np.array([.5,.5])` mutated to `[1,1]`/`[2,2]` that the F2P test `test_annotate_and_offsetfrom_copy_input` exercises); pre-gold buggy code diverges on every input and both prepatch Lean files fail verification, confirming the spec is discriminating and not too-strong. G-AX VACUOUS: zero consumed axioms and zero A-reference deep models (axiom_check.py guards the empty inventory; the changed behavior is modeled deeply and checked by G-CONF, not axioms). Docker evidence: in-container G-CONF rc=0 over 100007 inputs with gold applied; independent post-gold oracle ALL_MATCH_SPEC=True, pre-gold ALL_MATCH_SPEC=False.

---

## Sub-review 3 — LEAKAGE (verbatim)

The token scan confirms:
- No `OffsetFrom`, `Annotation`, `_AnnotationBase`, `__init__`, `ref_coord`, `self.xy`, `text.py`, `matplotlib`, `arrow`, `annotate` anywhere.
- `array` appears only as: (a) the Lean type `Array Int` (a generic carrier, not a leak), and (b) the **direct quote from the public problem_statement** "the same array is kept instead of a copy".

That quote is verbatim from the public `problem_statement` — explicitly permitted. The comment "The issue describes a coordinate pair that tracks later edits to the input container" paraphrases the public bug report.

**Reconstruction attempt from spec view alone:**

From the spec view, a solver learns: there is some object that retains a coordinate pair from a source container; the bug is that it stays aliased to the source (reflects later mutations) and the fix is to snapshot/detach it; this must hold for two independent sites. This is essentially a restatement of the public issue ("the same array is kept instead of a copy" → copy it). The spec view does NOT reveal:
- The file (`lib/matplotlib/text.py`)
- The classes (`OffsetFrom`, `_AnnotationBase`)
- The methods (`__init__`)
- The attribute names (`_ref_coord`, `self.xy`)
- The actual gold edit syntax (`x, y = xy; self.xy = x, y`)
- That one of the two sites is `OffsetFrom` (the hints-only second site)

A solver could not reconstruct the gold patch from the spec view. They'd know "copy the coordinate pair instead of aliasing it" — which is exactly what the public problem_statement already states ("same array is kept instead of a copy", and using `.copy()` fixes it).

**The two-site question (relaxed-leakage check):** The spec view reveals there are two coordinate-retaining sites. The public PS names only the `annotate`/`xy` site. The second site (`OffsetFrom`) is hints/test-patch-only. Does revealing "there are two such sites" constitute leakage?

The spec view does NOT name the second site, does NOT say it is `OffsetFrom`, and does not give any repo-specific token to identify it. It only abstractly states "a second, independent coordinate-retaining site with the same obligation." This is a structural fact (count = 2) but carries no discriminating vocabulary that points to OffsetFrom. The fix at both sites is *identical* (the same copy-on-capture), and the public issue itself invites broad application ("the same array is kept instead of a copy" — a class of aliasing bug). Revealing that the fix applies at two places, without identifying where the second place is, does not let a solver reconstruct the gold patch beyond the public framing.

This is a borderline case. The count "2" is not derivable purely from the PS (which shows only one site). However, no leaking token names or locates the second site — it is described in fully generic terms. Under the standard (patched file/symbol, diff line, repo-symbol-echoing identifier, or bug/fix narration revealing the gold edit), nothing here meets the bar. The narration tracks the public bug report; the only quote is verbatim-public.

Verdict: NO-LEAKAGE. The spec view stays at the abstraction level of the public problem_statement.

### Verdict: NO-LEAKAGE

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical across Solution.lean and both prepatch variants (same_spec=True, lean LanguageTables). Solution.lean verifies clean (exit 0). The modeled contract — StoredCoord.snapshot with postcondition `∀ a b, observe out a b = (coords[0]!, coords[1]!)` (detachment for every later source state) — exactly matches the real patched repo: OffsetFrom.`__init__` (`x,y=ref_coord; self._ref_coord=x,y`) and `_AnnotationBase`.`__init__` (`x,y=xy; self.xy=x,y`), both of which detach the stored pair. Ran the G-CONF oracle against the REAL patched constructors (mpl 3.11.1): construct from a numpy array, mutate the array, read back `_ref_coord` / xy, over all boundary cases including the problem-statement repro — 0 disagreements; stored pair always equals capture-time components. The Int carrier is faithful because the modeled op is pure component copy/identity (no arithmetic or ordering), so no float-precision drift is possible. The universal `∀ a b` is not over-strong: it is precisely the fix's guarantee, satisfied by the patched code and correctly refuted by the prepatch `reference` skeletons (which yield (a,b)). The unmodeled `_get_scale` inline is a behavior-preserving refactor, legitimately outside the modeled surface. No diverging input exists between the modeled function and the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage judged on the velvet consumer spec view (rendered via markers.spec_view) against the public problem_statement ONLY, excluding hints_text.

Mechanical screen (leakage.screen, lean flavor) returns passed=True, zero hard failures. Corroborated by manual review:
- No diff markers in view (`_LEAN_DIFF_MARKERS` clean).
- No gold-patch line reproduced (>=8 char normalized). The gold hunks ('x, y = ref_coord', 'self.`_ref_coord` = x, y', 'x, y = xy', 'self.xy = x, y', the `_get_scale` deletion/inline) appear nowhere.
- No patched file path/module: 'lib/matplotlib/text.py' and 'lib.matplotlib.text' absent from view.
- No patched repo symbols in identifiers or comments: OffsetFrom, `_AnnotationBase`, ref_coord, xy, `_get_scale`, get_unit/get_scale all absent. Distinctive changed symbols the screen tracks are {'get_unit','get_scale'} — neither appears.
- No fix/bug narration tokens (`_NARRATION_RE`) in comments. 'issue'/'desired behaviour' language describes the observable contract, not the edit.

The spec content — StoredCoord(snapshot/reference), observe, and postcondition (forall a b, observe out a b = (coords[0]!, coords[1]!)) — models copy-vs-alias retention. This is already public: problem_statement states 'It is very likely that the same array is kept instead of a copy' and the reproduction (mutate array after annotate, arrow moves). So the snapshot/detachment framing reveals nothing beyond the public bug report.

Second-site concern examined: OffsetFrom is a hints-only symbol (not in problem_statement). But the spec view abstracts the second site to 'Second, independent coordinate-retaining site' with NO repo-symbol name, file, or line. The OffsetFrom<->captureCoordA binding lives only in mapping.md/refinement.md (auditor artifacts, not the consumer spec view). So no hints-only term is echoed in-view.

**Structural checks:** same_spec(main, prepatch_1)=True and same_spec(main, prepatch_2)=True (impl regions differ, frozen spec identical); spec_view idempotent. impl/proof regions properly elided to placeholders in the view.

**Conclusion:** the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
