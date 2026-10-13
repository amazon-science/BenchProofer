# P2 adversarial audit — django__django-13569

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-13569", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED** (both audited gates pass)

The gold patch adds `Random.get_group_by_cols(self, alias=None): return []`, so a
`RANDOM()` ordering expression contributes no GROUP BY column (previously it
inherited the generic `[self]` rule from `BaseExpression`, injecting `RANDOM()`
into GROUP BY and breaking aggregation under `order_by('?')`). The bundle models
this as `groupingColumns (e : Expr)` with `require e.isNondetGenerator = true`,
`ensures out = groupingContribution e` and `ensures out = []`; impl is `return []`.

## Per-gate verdict table

| Gate | Verdict | Basis |
|------|---------|-------|
| G-EQ | **pass** | G-EQ SOUND AND spec-strength TIGHT AND no kind-3 refinement. 5 behaviorally-wrong same-spec impls all rejected by `out = []`; structurally-distinct correct impl (`return groupingContribution e`) verifies (non-vacuous). All refinement steps R/I, no kind-3, no axioms. No ungrounded oracle: `groupingContribution` is a transparent `def`, not an opaque answer-key. |
| G-PANEL | **pass** | faithfulness FAITHFUL AND G-AX ∈ {SOUND, VACUOUS} AND leakage ∈ {NO-LEAKAGE, RELAXED}. Spec is an exact projection of patch behavior (Docker-confirmed `[]` for all alias incl None; G-CONF 10^5 inputs, 0 disagreements). G-AX VACUOUS (no axioms; modeled function is the changed function, calls no unchanged callee). Leakage NO-LEAKAGE (spec view discloses no file/symbol/`Random`/`return []`; PS strictly more revealing). |

Supporting (non-audited) gates from meta.json all pass: G-VERIFY (1.5s),
G-DIFF (prepatch fails), G-INTEGRITY, G-HYGIENE, G-LEAK, G-GOLD, G-CONF (0
disagreements), G-RESOLVE (resolved, not flaky). G-AX/G-MUT = skip (no
axioms / assignment-only impl).

## Concrete defects + precise fixes

None. No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom,
no leak was found by any reviewer. The prepatch defect (`return [e]`, i.e. a
`Random` leaf inheriting the generic `[self]` rule → `RANDOM()` in GROUP BY) is
correctly rejected by the spec for the discriminating reason (`⊢ [e] = []`).

## Sub-reviews (quoted verbatim)

### G-EQ / SPEC-WEAKNESS review

> VERDICT: G-EQ = SOUND, spec-strength = TIGHT.
>
> bundle: django__django-13569 (Random.get_group_by_cols returns [] so a RANDOM() ordering expression contributes no GROUP BY column). Modeled as `groupingColumns (e : Expr)` with `require e.isNondetGenerator = true`, `ensures out = groupingContribution e`, `ensures out = []`. Single-statement impl `return []`.
>
> NOTE ON METHOD: /tmp is shared across concurrent reviewers and was actively overwriting my fixed-name attack files mid-run (saw another bundle's `chunkInventory`/`rebuildPositional` content bleed into my .out files). I re-ran everything inside a private `mktemp -d` dir; all results below are from that clean, content-verified run.
>
> SPEC-TOO-WEAK (machine-checked) — 5 wrong impls + prepatch + 1 positive control, all same_spec=True (spec byte-identical; only impl region changed):
> - atk_1 `return [e]` (the prepatch bug: Random contributes itself) — verify exit=1. Rejected by `ensures_1: out = []` (goal `⊢ [e] = []`) and `ensures_2` (`⊢ [e] = groupingContribution e`).
> - atk_2 `return [e, e]` — verify exit=1. Rejected by `out = []` (`⊢ [e, e] = []`).
> - atk_3 `return [{ isNondetGenerator := false }]` (fabricate a non-generator leaf) — verify exit=1. Rejected by `out = []` (`⊢ [{ isNondetGenerator := false }] = []`).
> - atk_4 `if e.isNondetGenerator then return [e] else return []` (conditional that returns self on the actual domain) — verify exit=1. Under `require isNondetGenerator = true` the live branch is `[e]`; rejected by `out = []` (`⊢ [e] = []`).
> - atk_6 `return e :: []` (= `[e]`, syntactic variant) — verify exit=1. Rejected by `out = []` (`⊢ [e] = []`).
> - POSITIVE CONTROL atk_pos `return groupingContribution e` (structurally different from literal `return []`, computes via the pure model) — verify exit=0, 0-byte error output. Spec is NON-VACUOUS.
> - Solution_prepatch.lean (`return [e]`) — verify exit=1, fails for the RIGHT/discriminating reason: `ensures_1: out = []` with `⊢ [e] = []` (the literal pre-patch defect: a Random leaf inheriting the generic `[self]` rule, i.e. RANDOM() injected into GROUP BY). Not an unrelated/parse error.
>
> REFINEMENT AUDIT: all steps R or I, no kind-3, no axioms (axioms region empty; meta `axioms: []`, `deep_model_references: []`).
> - A1/A2 (R): receiver always Random → `isNondetGenerator = true`; `alias` dropped (patched body `return []` ignores it). G-CONF fuzzes 8 alias values incl None — invariant.
> - A3 (I): `return []` ↔ empty Python list.
> - B1 (deep model, I): the inherited generic `[self]` rule is spelled out in `groupingContribution`'s `else` branch, NOT axiomatized. It lies outside the consumer spec view (which is taken under `isNondetGenerator = true`); it only feeds the prepatch pre-image and the G-CONF non-generator leg (Pi/Now → [self]). G-CONF (seed 13569, 10^5 inputs) executes shadow vs. patched repo on real Random/Pi/Now nodes, 0 disagreements.
>
> UNGROUNDED-ORACLE PROBE: no opaque/axiomatized symbol exists to echo. `groupingContribution` is a transparent `def` (`if isNondetGenerator then [] else [e]`); under the precondition it provably reduces to `[]`, and the redundant `ensures out = []` pins the concrete observable. The `out = groupingContribution e` postcondition is therefore not a circular answer-key — the only satisfying output is `[]`, which matches the real patched repo (G-CONF). The positive control returning `groupingContribution e` is the genuine correct computation, not a cheat.
>
> CONCLUSION: every behaviorally-wrong impl that shares the spec is rejected by the `out = []` clause (equivalently `out = groupingContribution e`); a structurally-distinct correct impl verifies. Spec is tight and non-vacuous for its abstraction; refinement is faithful (Random-only domain, alias-irrelevant, deep-modeled contrast rule, no axioms). G-EQ SOUND, spec TIGHT.

### FAITHFULNESS + G-AX review

> faithfulness = FAITHFUL
> G-AX = VACUOUS
>
> Spec content. The gold patch adds `Random.get_group_by_cols(self, alias=None): return []`. The full behavioral content is: a `Random` node contributes `[]` to GROUP BY (vs. the inherited `[self]`). The spec, under `require e.isNondetGenerator = true` (= `isinstance(node, Random)`), requires `out = []` (and `out = groupingContribution e`, which under that guard reduces to `[]`). This is an exact projection of the patch.
>
> Docker evidence (spec output == real post-gold on F2P inputs):
> - Independent probe, gold applied, in `django__django-13569` eval image: `Random().get_group_by_cols()` = `[]`; `get_group_by_cols(alias='x')` = `[]`; `get_group_by_cols(None)` = `[]`. Random has its own `get_group_by_cols` post-patch. All match spec's `out = []` across every alias value (the spec faithfully drops the ignored `alias` param).
> - Generic non-aggregate leaves post-gold: `Pi()` → `[Pi()]`, `Now()` → `[Now()]` (= `[self]`), matching the `else` branch of `groupingContribution`.
> - Bundle's `conformance_check.py` (gold applied, seed 13569): R/I shadow agrees with real patched repo on 100000 inputs, 0 disagreements (rc 0).
> - F2P test `test_aggregation_random_ordering` exercises `order_by('?')` → a `Random()` node whose `get_group_by_cols` must be `[]` so RANDOM() stays out of GROUP BY. The modeled domain (`isNondetGenerator=true`) covers exactly this input. FAITHFUL — no correct behavior rejected, no drift.
>
> Discrimination / G-DIFF. Pre-patch probe (base_commit, no gold): `Random().get_group_by_cols()` = `[Random()]` (= `[self]`, the defect). `Solution_prepatch.lean` models exactly this (`return [e]`) and FAILS the spec (unsolved goal `[e] = []`), exit 1. `same_spec(Solution, prepatch)` = True (identical frozen spec; only impl differs).
>
> G-AX = VACUOUS: no `axiom_check.py`; `meta.json` has `axioms: []`, `deep_model_references: []`. The modeled function is the changed function itself; its body (`return []`) consumes no unchanged-callee contract — nothing to axiomatize.

### LEAKAGE review

> LEAKAGE VERDICT: NO-LEAKAGE
>
> From the spec view alone an attacker learns only: "some function returns, for a non-deterministic value generator, the empty list of grouping columns it contributes to GROUP BY." This is angle-neutral and abstract. It does NOT disclose: the patched file (`django/db/models/functions/math.py`), the gold symbol (`get_group_by_cols`), the `Random` class, the `alias=None` signature, the `return []` literal, the insertion point (`as_sqlite`), or even the word "Random". The PS itself already names `Random`, `GROUP BY`, `get_group_by`, `isinstance`, `contains_aggregate` and supplies a concrete (different-angle) candidate patch — so the public text is strictly more revealing than the spec view. The gold's distinguishing implementation choice (override `get_group_by_cols` on `Random` vs. the user's proposed `compiler.get_group_by` filter) is not derivable from the spec view. No diff line, file, symbol, or repo-echoing identifier appears.
>
> Token audit (spec view, case-insensitive): `get_group_by_cols`=absent, `get_group_by`=absent, `math.py`=absent, `as_sqlite`=absent, `random`=absent, `isinstance`=absent, `alias`=absent, `contains_aggregate`=absent, `expressions.py`=absent. meta.json records `G-LEAK.status="pass"` (not relaxed), consistent with this analysis.

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
- **machine verdict:** faithfulness-break attack: no divergence found. Modeled function = Random.get_group_by_cols(self, alias=None), gold patch body `return []`. Spec models it as groupingColumns under `require e.isNondetGenerator=true` (= isinstance(node,Random)) with `ensures out=[]` (and out=groupingContribution e, which reduces to [] under the guard). Independently reproduced real post-patch behavior on a base-commit (257f8495) worktree with the gold hunk applied: Random().get_group_by_cols(alias=X) = [] for X in {None,'','x','T1'} — invariant in alias, exactly []; Random has its own get_group_by_cols post-patch. Base repo: Random has no get_group_by_cols, inherits BaseExpression → [self] for a non-aggregate leaf (verified in expressions.py:349), matching Solution_prepatch.lean's `return [e]` which correctly fails `[e]=[]`. On the entire modeled domain the spec output ([]) equals the real callee's output; the spec is not too strong (it asserts exactly the real behavior, and the alias drop is sound because behavior is alias-invariant). The [self] `else` leg is a deep model of the UNCHANGED inherited rule, lies outside the consumer domain (isNondetGenerator=true), and only feeds the prepatch pre-image / G-CONF non-generator leg (Pi,Now → [self], also reproduced). same_spec(Solution,Solution_prepatch)=True via velvet backend; Solution.lean verifies (lean_verify exit 0). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction). Gold edit = add Random.get_group_by_cols(self, alias=None): return [] in django/db/models/functions/math.py. The spec view (verified via swebench_unified.markers.spec_view over the velvet backend) contains only abstract symbols — structure Expr{isNondetGenerator:Bool}, groupingContribution e = if isNondetGenerator then [] else [e], and method groupingColumns requiring isNondetGenerator=true / ensuring out=[]. It names NO repo symbol (Random, get_group_by_cols), NO file path (math.py), and does not reveal the gold implementation site or shape (a method override on the Random class — which even differs from the reporter's own compiler.get_group_by proposal). The entire behavioral content it encodes — a non-deterministic value generator (RANDOM()) must contribute the empty grouping-column list — is already fully public in problem_statement: the reporter shows GROUP BY ..., RANDOM() as the defect, states 'the random function call has nothing to do with the aggregation,' and supplies a patch that excludes Random from the group_by expressions. Nothing in the spec view goes beyond problem_statement (hints_text excluded from consideration). same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True: the spec regions are byte-identical (confirmed by diff and by markers.spec_signature), only the impl region differs (return [] vs return [e]), so the prepatch is a faithful pre-image rather than a re-spec'd cell. G-LEAK in meta.json = pass, consistent. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
