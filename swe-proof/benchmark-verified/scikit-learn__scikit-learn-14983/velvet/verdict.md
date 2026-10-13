# P2 adversarial audit — scikit-learn__scikit-learn-14983

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — scikit-learn__scikit-learn-14983", before this
> corpus rendered one section per audit role. It is kept verbatim because it is
> the only account of that round that ships in this bundle, and it is NOT this
> cell's record. The record is the audit gate entries in the `meta.json` beside
> this file, which are the source of truth for the cell's status; each role
> section below publishes its gate's `status (recorded)` and `machine verdict`
> straight from that entry. Each round authored and re-ran its own attacks, so
> a count in the text above is that round's own count and not this record's:
> where the two accounts differ, the record governs.

**OVERALL: ACCEPTED** (G-EQ = pass, G-PANEL = pass)

Instance fixes `RepeatedKFold` / `RepeatedStratifiedKFold.__repr__`. Gold patch:
(1) add `__repr__` delegating to `_build_repr`; (2) in `_build_repr`, when
`getattr(self,key,None) is None and hasattr(self,'cvargs')`, source the value from
`self.cvargs.get(key,None)`. The Lean spec models value-resolution as `buildReprValues`
with postcondition `out = resolveAll attrs fallback hasFallback keys`, over concrete,
fully-visible `resolveOne`/`resolveAll` (attrs-first, then fallback iff `hasFallback`).
No axioms.

## Per-gate table

| Gate | Verdict | Basis |
|---|---|---|
| G-EQ | **pass** | G-EQ SOUND + spec-strength TIGHT + no kind-3 refinement. Baseline verifies (exit 0); all 7 same_spec wrong impls fail (exit 1), each rejected by the discriminating clause; both positive controls (`echo`, structurally-distinct `pos`) verify => non-vacuous, admits distinct correct impls. Oracle `resolveAll`/`resolveOne` is a transparent executable def, not an opaque answer-key; grounded by G-AX + G-CONF. No verifying-but-wrong impl found. |
| G-PANEL | **pass** | faithfulness FAITHFUL + G-AX VACUOUS (∈ {SOUND,VACUOUS}; no consumed axioms, deep-model A-reference check reproduced passing) + leakage RELAXED (∈ {NO-LEAKAGE, RELAXED}). |
| — G-VERIFY | pass | Solution.lean verifies, no sorry (exit 0). |
| — G-DIFF | pass | Solution_prepatch.lean fails (exit 1) on the exact goal `attrs.lookup k = resolveOne attrs fallback hasFallback k` — the fallback-vs-no-fallback delta. |
| — G-AX | pass (VACUOUS) | No consumed axioms (`axioms: []`). A-reference deep-model check: `resolveOne`/`resolveAll` == real patched value resolution on 12 boundary + 20000 fuzz states. |
| — G-CONF | pass | 100,012 inputs, 0 disagreements (seed 14983); e2e leg drives 4 real patched RepeatedCV objects, rendered repr == shadow value map. |
| — G-RESOLVE | pass | patch.diff resolves; patched `RepeatedKFold()` renders the fixed repr. |
| — G-MUT | pass | killed 14/14 (100%). |
| — G-LEAK (mechanical) | pass | spec view carries no lexical repo symbol / diff line — but disposition should be `relaxed` (see defect D1). |

## Concrete defects + precise fixes

**D1 (documentation/disposition, NON-BLOCKING):** The bundle is dispositioned as a
clean G-LEAK pass, but the leakage review establishes this is a genuine RELAXED case:
the spec view's `resolveOne` docstring (Solution.lean lines 16-18) necessarily discloses
the gold's tested discriminator — the secondary-parameter-store fallback when the primary
attribute lookup yields None — which is absent from the public `problem_statement`
(token scan: no cvargs/fallback/secondary/store/attribute/getattr/param/dict/stored;
present only in `hints_text`/gold/test_patch). Faithful + non-leaking is provably
impossible here (a non-leaking attrs-only spec would be satisfied by the prepatch bug).
The leak is semantic, not lexical, so the mechanical G-LEAK screen correctly passes.

*Fix:* set `meta.json` `gates.G-LEAK.status = "relaxed"`, add an in-bundle
`RELAXED_LEAKAGE.md` per RELAXED_LEAKAGE.md §29 quoting the leaking line, and add
this id to the central RELAXED scope list. This does NOT block ACCEPTED: RELAXED ∈ the
G-PANEL-passing leakage set, and all soundness gates (G-VERIFY/G-DIFF/G-AX/G-CONF/
G-RESOLVE) are intact. The audit_verdict note flags D1 for the panel to action.

No counterexample (verifying-but-wrong impl, unfaithful divergence, unsound axiom, or
genuine unavoidable-but-unrecorded leak that fails the gate) was found.

---

## Sub-review 1 — G-EQ / spec-weakness (verbatim)

> Both positive controls locked: `echo` (trivial `return resolveAll`) and `pos`
> (structurally-different forward take-fold) both share the spec and verify. The spec is
> non-vacuous and admits genuinely different correct implementations.
>
> ## VERDICT
> **G-EQ = SOUND. spec-strength = TIGHT.**
>
> ### Bundle summary
> Instance fixes `RepeatedKFold`/`RepeatedStratifiedKFold.__repr__`. Gold patch has two
> hunks: (1) add `__repr__` delegating to `_build_repr`; (2) in `_build_repr`, when
> `getattr(self,key,None) is None and hasattr(self,'cvargs')`, source the value from
> `self.cvargs.get(key,None)`. The Lean spec models the value-resolution as
> `buildReprValues`, with postcondition `out = resolveAll attrs fallback hasFallback keys`,
> where `resolveAll`/`resolveOne` are concrete, fully-visible defs (attrs-first, then
> fallback iff `hasFallback`). No axioms.
>
> ### 1. Spec-too-weak (machine-checked) — TIGHT
> Baseline `Solution.lean` verifies (exit 0). All 7 wrong impls share the spec
> (`same_spec=True`) and FAIL to verify (exit 1), each rejected by the exact discriminating
> clause:
> - atk_prepatch/atk1 ignore fallback (prepatch bug) — rejected by `attrs.lookup k = resolveOne …`
> - atk2 always consult fallback (drop `hasFallback` gate) — `match attrs.lookup … = resolveOne …`
> - atk3 fallback priority over attrs — `if hasFallback then … = resolveOne …`
> - atk4 `return []` — `[] = resolveAll … keys`
> - atk6 off-by-one (`keys[i]` not `keys[i-1]`) — `resolveOne … keys[i] = …`
> - atk7 read only fallback — `fallback.lookup k = resolveOne …`
>
> Positive controls (both `same_spec=True`, verify exit 0): `echo` and `pos`. Spec is
> non-vacuous and admits distinct correct impls. No wrong impl verifies → not too weak.
>
> ### 2. Refinement audit — clean, no kind-3
> refinement.md tags all R / A-reference / I. The changed op (value resolution gaining the
> cvargs fallback) is modeled DEEPLY by `resolveOne`/`resolveAll`, not axiomatized away.
> `Solution_prepatch.lean` fails for the RIGHT reason: unsolved goal
> `attrs.lookup k = resolveOne attrs fallback hasFallback k`. Independently applied patch.diff
> in-container: patched `RepeatedKFold()` renders `RepeatedKFold(n_repeats=10, n_splits=5,
> random_state=None)`. G-AX re-run in-container PASS; G-CONF re-run in-container WITH patch
> applied PASS (100,012 inputs, 0 disagreements). The `__repr__` delegation hunk is
> load-bearing but introduces no computation beyond invoking the modeled `_build_repr`;
> G-CONF's e2e leg mechanically confirms reduction to the modeled value map.
>
> ### 3. Ungrounded-oracle probe — no leak
> The oracle `resolveAll`/`resolveOne` is a concrete, transparent, executable Lean def, not
> an opaque axiom or pinned answer-key. `echo` verifies but IS the correct computation, not a
> cheat. G-AX/G-CONF confirm `resolveAll` equals the real patched behavior.
>
> ### Residual trust
> Single trust point: deep model `resolveAll`/`resolveOne` faithfully captures patched
> `_build_repr` (A-reference), checked by G-AX + G-CONF + e2e. `Int`/`Option Int` abstraction
> sufficient (F2P exercises only integer/None params). No counterexample found.

## Sub-review 2 — Faithfulness + G-AX (verbatim)

> The model uses `List.lookup` (first match) for attrs/fallback, but real objects have unique
> attribute names → "first match" semantics irrelevant. Conformance uses dicts (unique keys),
> matching reality. No divergence. Real code sorts `args` and iterates; model takes `keys` as
> already-sorted and preserves order via backward fold; e2e leg confirms real repr ordering.
> Spec view passes leak check (no `cvargs`/`_build_repr`/`RepeatedKFold`; comments say
> "secondary parameter store", "attribute table"). Clean.
>
> VERDICT
> faithfulness = FAITHFUL
> G-AX = VACUOUS (no consumed axioms; `axioms` region empty; changed value-resolution modeled
> deeply via `resolveOne`/`resolveAll`; the "G-AX" script is an A-reference deep-model
> soundness check, independently reproduced passing)
>
> EVIDENCE
> - patch.diff is the gold patch verbatim.
> - Solution.lean verifies no sorry (exit 0); Solution_prepatch.lean fails (exit 1) with goal
>   `List.lookup k attrs = resolveOne attrs fallback hasFallback k`. same_spec = True.
> - Spec output == real post-gold output on F2P inputs `RepeatedKFold(n_splits=2, n_repeats=6)`
>   and `RepeatedStratifiedKFold(n_splits=2, n_repeats=6)`: real `repr()` =
>   `'<Class>(n_repeats=6, n_splits=2, random_state=None)'`, matching F2P-expected. resolveAll
>   over `["n_repeats","n_splits","random_state"]` with attrs `{n_repeats:6}`, fallback
>   `{n_splits:2}`, hasFallback=true yields `[some 6, some 2, none]` → exactly that string.
> - G-CONF (post-gold, in-container, need_hypothesis=True): rc 0, 0 disagreements / 100012
>   inputs, e2e "ok (4 real RepeatedCV objects)".
> - G-AX deep-model check (in-container): rc 0, deep model == real patched value resolution on
>   12 boundary + 20000 fuzz states.
> "None-valued own attribute ≡ absent from attrs" is sound; value→`Int`/`Option Int` faithful
> for F2P params; orthogonal deprecation-warning `continue` path unchanged + never triggers
> (refinement.md A4 out-of-scope-unchanged). `ensures` grounded; G-MUT killed 14/14. No
> spec-too-strong or drift. Single trust point backstopped by G-CONF + A-reference G-AX, both
> reproduced passing. No consumed axioms → G-AX = VACUOUS.

## Sub-review 3 — Leakage (verbatim)

> The prepatch reads only `attrs.lookup k` (own-attribute only); the spec
> `out = resolveAll ...` requires the secondary-store fallback → prepatch fails. The
> discriminating clause IS the secondary-store fallback. A non-leaking spec would be
> `out = attrs.lookup`-based, which the prepatch satisfies — non-faithful. So faithful +
> non-leaking is impossible.
>
> Is the fallback derivable from the public problem_statement? The problem_statement just
> shows desired output; the "params stored in cvargs, getattr returns None" diagnosis lives in
> `hints_text`. Genuine, unavoidable leak — matches relaxed-leakage criteria. Spec view does
> not name `cvargs`/`_build_repr`/`RepeatedKFold`/`n_splits`/`sklearn` or any diff line. Leak
> is purely semantic.
>
> VERDICT: **RELAXED**
> Token scan of `problem_statement` confirms none of {cvargs, fallback, secondary, store,
> attribute, getattr, param, dict, stored}; public issue is pure symptom report. Leak is
> unavoidable: faithful + non-leaking provably impossible. Leak is semantic not lexical →
> mechanical G-LEAK correctly passes.
>
> Leaking line (Solution.lean `resolveOne` docstring, lines 16-18):
> "When the primary source yields no value and a secondary parameter store is present
> (`hasFallback`), the value is taken from that store `fallback` instead."
>
> DISPOSITION DEFECT: bundle dispositioned as clean pass — `meta.json`
> `gates.G-LEAK.status = "pass"`, no `RELAXED_LEAKAGE.md`. Under RELAXED_LEAKAGE.md §29
> should be `G-LEAK.status = "relaxed"` with in-bundle `RELAXED_LEAKAGE.md` + central scope
> list entry. Core soundness gates intact (G-VERIFY pass, G-DIFF fail on discriminating
> clause, G-AX/G-CONF clean, G-RESOLVE resolved) → relaxed disposition appropriate, just not
> currently recorded.

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
- **machine verdict:** Faithfulness (spec-too-strong/drift) attack found NO diverging input. Spec: resolveOne = attrs.lookup key; if none and hasFallback then fallback.lookup key else none; resolveAll maps over keys in order; postcondition out = resolveAll attrs fallback hasFallback keys. Real callee (base_commit 06632c0d, sklearn/model_selection/`_split`.py `_build_repr`, post-patch): value = getattr(self,key,None); if value is None and hasattr(self,'cvargs'): value = self.cvargs.get(key,None); collected in order over sorted args. Bijection (mapping.md §2): attrs ↔ self.`__dict__` params with getattr()==None ↔ attrs.lookup=none (so None-valued/absent attrs both map to absent); fallback ↔ self.cvargs; hasFallback ↔ hasattr(self,'cvargs'); Option Int ↔ Optional[int]. Verification performed: (1) same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers.same_spec with velvet backend — spec signature identical, prepatch differs only in impl region. (2) Solution.lean verifies under scripts/lean_verify.sh, exit 0, no sorry. (3) Re-ran axiom_check.py (G-AX): deep model == real getattr+cvargs.get composition on 12 boundary + 20000 fuzz states, exit 0. (4) Independent edge-case checks against real Python: F2P object (n_repeats=6 attr, n_splits=2 in cvargs) → real [6,2,None] == model; falsy 0 present in attrs does NOT trigger fallback (real & model both [0]) — confirms the `is None` test, not falsiness, gates the fallback and the model's `some 0` path agrees; attribute explicitly None with cvargs value → both yield the cvargs value (real getattr→None→fallback; model present-None modeled as absent→fallback). The `None↔none↔attrs-absent` bijection is exact because getattr(...,None) is None is precisely resolveOne's none-branch. No spec-too-strong drift: postcondition pins exactly the patched value map, ordered; surrounding `_pprint`/format/signature-introspection are unchanged and identity-on-content, correctly out of modeled scope. Leakage relaxation (secondary-store-fallback facet) is a dispositioned G-LEAK matter, not a faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the recorded relaxed-leakage disposition independently rather than rubber-stamping. Findings: (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean via markers.same_spec (True). (2) G-VERIFY: Solution.lean elaborates clean, exit 0 (~30s recorded, re-ran OK). (3) G-DIFF sound: prepatch (attrs-only resolveOne) fails for the correct reason — unsolved goal `List.lookup (keys[i-1]) attrs = resolveOne attrs fallback hasFallback (keys[i-1])`, i.e. the missing secondary-store fallback. (4) Relaxed-leakage policy is a genuine codebase mechanism (spec_guide.md directive 6; gates/leak.py honors relaxed_leakage flag + RELAXED_LEAKAGE.md; `_audit`.py records a relaxed-leakage panel as pass+note, no separate 'relaxed' panel status). (5) problem_statement token scan: purely a symptom report (object-address repr vs parameter repr); no occurrence of cvargs/fallback/secondary/store/attribute/getattr/dict — it says nothing about WHERE displayed values are sourced. The cvargs diagnosis lives only in hints_text (excluded from the leakage baseline), the gold diff, and the hidden test_patch. (6) Unavoidability re-derived: a spec faithful to post-gold behavior must reject the prepatch bug (which would render store-only params as None), and doing so REQUIRES the spec to express the secondary-store fallback (resolveOne's none-branch + the frozen postcondition). A problem_statement-only spec ('repr shows the params') is satisfied by the buggy attrs-only resolution and is spec-too-weak. Hence faithful ∧ non-leaking is impossible. The disclosed mechanism (resolveOne docstring 'secondary parameter store... value taken from that store instead' + the `if hasFallback then fallback.lookup key else none` branch) IS a genuine semantic leak of the gold discriminator beyond problem_statement — but it is exactly the single dispositioned facet, names no repo symbol (cvargs/`_build_repr`/RepeatedKFold/sklearn) and quotes no diff line. (7) Scanned the full spec view for any NEW leak beyond the fallback facet: none found. Disposition confirmed intact; recording NO-LEAKAGE (pass) per the panel convention for a properly-dispositioned, unavoidable, semantic leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
