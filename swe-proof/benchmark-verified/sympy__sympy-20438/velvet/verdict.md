# P2 adversarial audit — sympy__sympy-20438

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "Audit Verdict — sympy__sympy-20438", before this corpus rendered one
> section per audit role. It is kept verbatim because it is the only account of
> that round that ships in this bundle, and it is NOT this cell's record. The
> record is the audit gate entries in the `meta.json` beside this file, which
> are the source of truth for the cell's status; each role section below
> publishes its gate's `status (recorded)` and `machine verdict` straight from
> that entry. Each round authored and re-ran its own attacks, so a count in the
> text above is that round's own count and not this record's: where the two
> accounts differ, the record governs.

**Overall status: ACCEPTED**

Velvet twin-artifact P2 audit of the sympy `ProductSet.is_subset` / set-equality /
`Eq.simplify` fix. Both adjudicated gates pass.

## Per-gate table

| Gate | Verdict | Basis |
|------|---------|-------|
| **G-EQ** | **pass** | G-EQ SOUND AND spec-strength TIGHT AND no kind-3 refinement. All postconditions are exact equalities over a fully-defined pure region; 7 wrong impls (incl. all 3 real prepatch bugs) machine-rejected on their postcondition clause; positive control verifies (non-vacuous); single A-reference (`triAll`/`tand2` == real `fuzzy_and`) real-checked by G-AX (rc 0). |
| **G-PANEL** | **pass** | faithfulness FAITHFUL AND G-AX ∈ {SOUND, VACUOUS} (= VACUOUS: no consumed axioms; A-reference deep model SOUND, 20145 in-container checks, 0 disagreements) AND leakage = NO-LEAKAGE. |

## Concrete defects + precise fixes

None. No counterexample found by any sub-reviewer:
- No verifying-but-wrong impl (all 7 attacks fail verification; positive control verifies).
- No unfaithful divergence (every F2P behavior matches the real post-gold repo in-container, including the discriminating `tand2(None,False)=False` three-valued case).
- No unsound axiom (axioms region empty; A-reference deep-model SOUND).
- No genuine leak (spec view reveals strictly less than the public problem_statement).

## Machine evidence

- `Solution.lean` verifies, exit 0, no sorry (re-confirmed by lead auditor).
- G-AX A-reference: `axiom_check.py` in-container → rc 0, 20145 checks (full 3×3 table + lists ≤ len 4 + 20000 fuzz), 0 disagreements.
- G-CONF (R/I legs): `conformance_check.py` in-container with gold patch applied → rc 0, 108622 inputs, 0 disagreements (matches meta.json). Without the patch, reproduces the exact problem-statement `AttributeError: 'Complement' object has no attribute 'equals'`, confirming the oracle is the real patched code.
- All three `Solution_prepatch_{1,2,3}.lean` fail `prove_correct` at their discriminating postcondition clause.

---

## Sub-review: G-EQ / SPEC-WEAKNESS (verbatim)

> VERDICT: G-EQ = SOUND, spec-strength = TIGHT.
>
> Bundle: results/sympy__sympy-20438/ (sympy ProductSet.is_subset / set-equality / Eq.simplify fix). Three modeled behaviors, all postconditions are exact equalities over a fully-defined pure region (`tand2`/`triAll`), no consumed axioms, one A-reference (`triAll`/`tand2` == real `fuzzy_and`) validated by G-AX.
>
> SPEC-TOO-WEAK (machine-checked). Baseline Solution.lean verifies (exit 0). Built 7 wrong impls + 1 positive control; each changed ONLY an `-- impl` region (pure/axioms/pre/post byte-identical), all confirmed `same_spec(Solution, atk)=True`. Every wrong impl FAILED verification on the postcondition clause; the positive control (structurally different correct impl) VERIFIED.
>
> - atk_1 everyElementMember `return none` (prepatch bug #1): exit 1 — rejected by `ensures out = triAll memberships`, goal `none = triAll memberships`.
> - atk_2 everyElementMember `return some true` (ignores list): exit 1 — `some true = triAll memberships`.
> - atk_7 everyElementMember `return memberships.headD (some true)` (head only): exit 1 — `memberships.headD (some true) = triAll memberships`.
> - atk_3 setsCoincide `return subAB` (echo one side): exit 1 — `subAB = triAll [subAB, subBA]`.
> - atk_4 setsCoincide `return none` (prepatch bug #2): exit 1 — `none = triAll [subAB, subBA]`.
> - atk_5 guardedSimplify swapped branches (`r` when bothExpr else `normal`): exit 1 — both clauses `bothExpr=true → r=normal` and `bothExpr=false → normal=r` unsolved.
> - atk_6 guardedSimplify `return normal` always (prepatch bug #3): exit 1 — `ensures bothExpr=false → out = r`, goal `bothExpr=false → normal=r`.
> - POSITIVE CONTROL atk_pos: everyElementMember `return memberships.foldr tand2 (some true)` (different shape than the verified backward `while` fold) VERIFIED (exit 0) — spec is non-vacuous and not over-fitted to the loop form.
>
> UNGROUNDED-ORACLE probe: no opaque answer-key to echo. The fold targets (`triAll`/`tand2`) are concrete pure defs, so atk_2/atk_3/atk_7 echoes were all caught. The only opaque tokens are guardedSimplify's `Int` `r`/`normal`, but the postcondition pins WHICH token per branch; atk_5/atk_6 prove an impl cannot return the wrong one. No echo discharges the postcondition.
>
> REFINEMENT AUDIT: refinement.md steps are all R / A-reference / I — no kind-3. The single A obligation (`triAll`/`tand2` == `fuzzy_and`, an unchanged stdlib callee) is real-checked: ran axiom_check.py in-container → rc 0 (20145 checks, full 3×3 table + all lists ≤ len 4 + 20000 fuzz, 0 disagreements). The R/I legs: ran conformance_check.py in-container with the gold patch git-applied (apply_gold) → rc 0, "108622 inputs, 0 disagreements" (matches meta.json exactly); patch applies cleanly. The shadow exercises the patched repo end-to-end including is_subset routing through behavior #1's new rule for behavior #2. (Note: running G-CONF WITHOUT the patch reproduces the exact problem-statement `AttributeError: 'Complement' object has no attribute 'equals'`, confirming the oracle is the real patched code, not a stub.) All three Solution_prepatch_{1,2,3}.lean FAIL for the RIGHT reason — each on its discriminating postcondition clause (`none = triAll memberships`; `none = triAll [subAB,subBA]`; `bothExpr=false → normal=r`), not an unrelated error.
>
> No counterexample found. The spec is tight (every plausible wrong impl, including all three real prepatch bugs, is rejected by its postcondition equality), non-vacuous (positive control verifies), and the type refinement / single A-reference hide no mismatch (G-AX and G-CONF both pass in-container against the real callee and the real patched repo).

## Sub-review: FAITHFULNESS + G-AX (verbatim)

> Confirmed: `axioms-start`/`axioms-end` region is empty (no consumed axioms). The `tand2`/`triAll` are pure definitions, and G-AX validates them against the real `fuzzy_and` (A-reference). This makes G-AX VACUOUS in the consumed-axiom sense, though the A-reference deep-model check passed (SOUND).
>
> My audit is complete. Summary of findings:
>
> **Faithfulness (FAITHFUL):**
> - Solution.lean verifies cleanly (exit 0, no sorry).
> - All three F2P behaviors independently verified against the REAL post-gold repo (gold patch applied in-container):
>   - `Eq(ProductSet({1},{2}), Interval(1,2))`: subAB=None, subBA=False → `tand2(None,False)`=False = oracle `S.false`. This is the discriminating subtlety (False dominates None in three-valued logic) and the model gets it right. Note this is a `ProductSet↔Interval` mixed pair routed through the patched `(Set,Set)` rule — NOT in the G-CONF fuzz set (which only fuzzes FiniteSet↔ProductSet), but I verified it directly.
>   - `b.is_subset(c)`=True, `b.is_subset(d)`=False: beh1 `triAll`-model matches both.
>   - `Eq(c,b).simplify() is S.true`, `Eq(a,c).simplify() is S.false`: matches (Eq(a,c) is same-type FiniteSet/FiniteSet, handled by unchanged code, honestly out of scope per mapping.md §1).
>   - `Eq({1},{x}).simplify()==Eq({1},{x})`: behavior #3 guard, relation survives unchanged.
> - The Lean↔Python bridge is exact: when `contains` returns a symbolic `Contains(...)`, `fuzzy_bool`/`threeval` collapse it to `None`, matching the `Option Bool` `none` carrier.
> - Three prepatch files each break exactly one behavior and fail `prove_correct` at precisely the discriminating clause (G-DIFF discriminates; spec is non-vacuous).
> - The deleted `(FiniteSet,Interval)` rule is confirmed behavior-neutral (two identical rules existed at base_commit).
> - G-CONF passes (5918 inputs, 0 disagreements with reduced fuzz; the full 115K fuzz is just more of the same distribution and exceeds the 1190s wall — too-heavy, not a soundness concern).
> - No behavior the spec rejects that the real post-gold code accepts. Spec is an exact equality (`out = triAll ...`), not over- or under-constrained.
>
> **G-AX (VACUOUS):** No consumed axioms (axioms region empty). The only A-obligation is an A-reference deep model (`tand2`/`triAll` == real `fuzzy_and`), independently re-run in-container: 20145 checks, 0 disagreements (SOUND as a reference check).
>
> VERDICT: faithfulness = FAITHFUL, G-AX = VACUOUS (no consumed axioms; the A-reference deep model `triAll`/`tand2` == real `sympy.core.logic.fuzzy_and` is SOUND — 20145 in-container checks, 0 disagreements).
>
> Docker evidence (gold patch applied, post-gold repo): every F2P input shape matches the spec model exactly — `Eq(ProductSet({1},{2}),Interval(1,2))`: model `tand2(None,False)`=False == oracle `S.false`; `b.is_subset(c)` model True == oracle True; `b.is_subset(d)` model False == oracle False; `Eq(c,b)` model True == oracle `S.true`; `Eq(a,c)` model False == oracle `S.false`; `Eq({1},{x})` survives unchanged. G-CONF: 5918 inputs, 0 disagreements (full 115K fuzz exceeds the 1190s wall — heavy, not unsound). Solution.lean verifies (exit 0); all 3 prepatch files fail `prove_correct` at the discriminating clause.

## Sub-review: LEAKAGE (verbatim)

> Solution.lean verifies (exit 0). My mandate is leakage; the verification confirms bundle integrity.
>
> **Leakage verdict analysis complete.**
>
> NO-LEAKAGE
>
> Reconstruction attempt from the spec view alone:
>
> The spec view (`results/sympy__sympy-20438/Solution.lean`, spec_view rendering) describes three behaviors in fully de-narrated, repo-agnostic English:
> 1. `everyElementMember` — "a finite product of values is wholly contained in a finite collection ... exactly when EVERY one of its elements is a member of the collection, combined under three-valued logic."
> 2. `setsCoincide` — "two collections coincide ... when each is contained in the other, combined under three-valued logic."
> 3. `guardedSimplify` — "only when BOTH operands are algebraic expressions may the general simplification proceed ... when they are not both expressions the relation must be returned UNCHANGED."
>
> From the spec view ALONE I cannot reconstruct the gold patch's locating detail: no file names (`issubset.py` / `comparison.py` / `relational.py`), no repo symbols (`is_subset_sets`, `_eval_is_eq`, `_eval_simplify`), no `@dispatch(ProductSet, FiniteSet)`, no `fuzzy_and`/`contains`/`tfn`, no `isinstance(..., Expr)`. The view yields only the abstract behaviors, not the gold hunks.
>
> Crucially the public `problem_statement` already discloses strictly MORE concrete repo detail than the spec view does — it names `is_subset`, `ProductSet`, `FiniteSet`, `Eq(b, c).simplify()`, and prints the `_eval_simplify` traceback (`AttributeError: 'Complement' object has no attribute 'equals'`). Each of the three spec-view behaviors maps 1:1 onto a symptom that is explicitly in the public issue:
> - behavior #1 ⇐ `b.is_subset(c)` giving the wrong (empty/unknown) result;
> - behavior #2 ⇐ `Eq(b, c)` / `c.is_subset(b)` set-equality symptom;
> - behavior #3 ⇐ the `Eq(b, c).simplify()` AttributeError in `_eval_simplify` (the natural fix being: don't take the arithmetic-difference path when an operand isn't a proper expression).
>
> Token scan of the spec view for repo-internal vocabulary: the only hit, "Expr", is exclusively the English word "expression(s)" and the model-internal parameter name `bothExpr` — never the repo `Expr` type, `isinstance`, or any dispatch decorator. No diff line, no patched-symbol echo, no bug/fix narration beyond the public symptoms.
>
> No leaking token to quote — there is none. The spec view reveals less than the public problem statement and stays within problem_statement-only grounding. This is not a relaxed-leakage instance (the gold's discriminators are all public symptoms, not hints_text/test_patch-only vocabulary).
>
> Verdict: NO-LEAKAGE

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 11 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 11 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness attack (spec-too-strong / spec-drifts-from-repo): could NOT find a diverging input; verdict FAITHFUL.

**SETUP:** worktree at base_commit 33b47e4bd6, gold patch.diff applied cleanly. Ran real repo python. Spec region byte-identical across Solution.lean and all 3 prepatch variants (same_spec=True); Solution.lean verifies (lean_verify exit 0). G-AX reproduced (20145 checks, 0 disagreements). G-CONF reproduced on a fresh checkout+patch (108622 inputs, 0 disagreements) — matches meta.json.

The three ensures clauses are near-literal transliterations of the gold hunks:

#1 everyElementMember: `out = triAll memberships`. Real is_subset_sets(ProductSet,FiniteSet) IS `fuzzy_and(b.contains(x) for x in a_ps)`; memberships = the real contains verdicts; triAll==fuzzy_and is G-AX-proven. Independent 784-case probe (incl. is_subset intersection fallback, symbolic/unknown elements, superset/partial/disjoint collections): 0 divergences with the full real ps.is_subset(b).

#2 setsCoincide: `out = triAll [subAB,subBA]`. Real `_eval_is_eq`(Set,Set) IS `tfn[fuzzy_and(is_subset pairs)]`; tfn is identity on the {True,False,None} domain (verified defaultdict at sympy/sets/sets.py:31), tand2==triAll[.,.]. Independent 2268-case probe over mixed FiniteSet<->ProductSet pairs (the only pairs reaching the generic rule per scope note): 0 divergences with real is_eq.

#3 guardedSimplify: models the two added `if not isinstance(...Expr...): return r` guards. Note the real `_eval_simplify` returns the ARG-SIMPLIFIED relation (`r = self.func(*[i.simplify() for i in r.args])`) in the false branch, while the spec models `out = r` (unchanged token). I specifically attacked this drift: mixed Expr/Set Eq pre-evaluate to BooleanFalse (not guard-relevant), and Set operands that survive as a Relational do not change under .simplify() (tested FiniteSet with sin^2+cos^2 elements, ConditionSet, ImageSet, Complement, unevaluated Intersection — Set.simplify does not recurse into finite-set elements). No observable in-scope divergence: the opaque-Int-token abstraction plus the pre-evaluation of mixed-operand Eq make the arg-simplification a no-op on exactly the surviving relations. G-DIFF confirms all 3 prepatch variants fail (discriminating content present).

**Conclusion:** the modeled functions agree with the real callees on every input I could construct; the spec is not too strong and does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Attacker-3 (leakage / gold-reconstruction) on sympy__sympy-20438 velvet. Rendered the actual consumer spec_view via swebench_unified.markers.spec_view (velvet backend) and compared against the public problem_statement (NOT hints_text).

Public problem_statement already discloses all three affected areas: (1) is_subset wrong for ProductSet.is_subset(FiniteSet) [blank/None shown -> three-valued semantics visible]; (3) Eq(b,c).simplify() AttributeError 'Complement' object has no attribute 'equals' in `_eval_simplify` (relational.py:308, dif.equals(0)); and the set-equality path via Eq(b,c) / intersection symmetry (behavior 2).

**Spec view contents:** abstract method names only (everyElementMember/setsCoincide/guardedSimplify), abstract carriers (Option Bool, Int), pure three-valued-logic helpers (tand2/triAll). NO repo identifiers (is_subset, is_subset_sets, `_eval_is_eq`, `_eval_simplify`, fuzzy_and, tfn, ProductSet, FiniteSet, @dispatch, contains), NO file/line references (issubset.py, comparison.py, relational.py), NO literal Python patch code. Grep of spec_view for gold-patch tokens: all False except 'Expr' which matches only the English word 'expression(s)' and the Lean param 'bothExpr'.

No pre-patch facts in the spec view: mapping.md §1 explicitly quarantines the overturned pre-patch behavior to the refinement audit ('NOT in the consumer spec view'); confirmed absent.

same_spec(gold, prepatch_k) = True for all three prepatch variants -> discriminating content lives entirely in the elided impl region, so the spec view does not encode which impl is gold. G-LEAK recorded pass and my independently-rendered spec_view is consistent with meta.json's spec_view hash.

The spec view specifies desired behavior (necessary for any spec) using abstract carriers and hands over no gold-patch code/identifiers/files/pre-patch reconstruction material beyond what the public problem_statement already implies. Not gold-edit leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
