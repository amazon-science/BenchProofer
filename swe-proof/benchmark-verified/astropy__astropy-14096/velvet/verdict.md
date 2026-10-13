# P2 adversarial audit — astropy__astropy-14096

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — astropy__astropy-14096", before this corpus
> rendered one section per audit role. It is kept verbatim because it is the
> only account of that round that ships in this bundle, and it is NOT this
> cell's record. The record is the audit gate entries in the `meta.json` beside
> this file, which are the source of truth for the cell's status; each role
> section below publishes its gate's `status (recorded)` and `machine verdict`
> straight from that entry. Each round authored and re-ran its own attacks, so
> a count in the text above is that round's own count and not this record's:
> where the two accounts differ, the record governs.

**Overall: ACCEPTED** (G-EQ = pass, G-PANEL = pass)

One-line synthesis: Tight functional spec pins `out` pointwise to `attrFallbackSpec`; all 7 wrong impls + prepatch rejected with genuine unsolved-goals, a structurally-different correct impl verifies; spec is faithful to the post-gold verbatim-propagation behavior, carries no axioms (VACUOUS), and leaks no repo symbol or mechanism (the discriminator is already stated in the public problem_statement).

## Per-gate table

| Gate | Verdict | Basis |
|------|---------|-------|
| G-EQ | **pass** | G-EQ SOUND + spec-strength TIGHT + no kind-3 refinement. Spec `ensures out = attrFallbackSpec requested frameOutcome genuineOutcome` pins `out` pointwise (both `some`/`none` branches independently pinned). All 7 wrong impls fail with genuine "unsolved goals" on the `ensures` equation (not compile errors); prepatch fails on the discriminating none-branch; a structurally-different correct impl (`frameOutcome.elim …`/`Option.elim`) verifies → non-vacuous. Refinement steps all R/I/removed-op; the single changed op modeled deeply, no axioms, no hand-waving. |
| G-PANEL | **pass** | faithfulness FAITHFUL + G-AX ∈ {SOUND, VACUOUS} + leakage ∈ {NO-LEAKAGE, RELAXED}. Faithfulness FAITHFUL (post-gold body literally `return self.__getattribute__(attr)`; spec output == real output on all F2P input shapes, confirmed in-container). G-AX VACUOUS (axioms:[]; no axiom_check.py). leakage NO-LEAKAGE (spec view free of repo symbols/fix vocabulary; behavioral discriminator already in public problem_statement; gold mechanism abstracted to free input). |
| G-VERIFY | pass (re-checked) | `Solution.lean` verifies, exit 0. |
| G-DIFF | pass (re-checked) | `Solution_prepatch.lean` fails on the miss-path clause (`Except.error { subject := requested } = genuineOutcome` unsolved), exit 1. |
| G-MUT | pass | 7/7 killed. |
| G-AX | skip/VACUOUS | No axioms in bundle (`axioms: []`); no `axiom_check.py`. |
| G-CONF | skip (justified) | No input-dependent R/I computation; only discriminating observable is exception identity on a live CPython `__getattribute__` model. Soundness carried by G-VERIFY + G-DIFF. |
| G-LEAK | pass | Spec view clean. |

## Concrete defects + fixes

None. No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak was found. No refinement required.

Honest (non-blocking) caveat: this is an abstraction-heavy "free-input" twin — the discriminating behavior (error names `random_attr`, not `prop`) lives in the value of the free input `genuineOutcome`, about which the spec asserts nothing; the Lean obligation on the miss path is near-tautological ("return the free input"). Soundness rests on the refinement claim that `genuineOutcome : Except AttrErr Value` faithfully models the unchanged callee `self.__getattribute__(attr)`. That claim is sound: the one-line gold fix propagates the unchanged callee's outcome verbatim, so modeling it as a verbatim-propagated free input is faithful — confirmed by in-container post-gold behavior matching the spec on every F2P input shape (§3 unchanged-callee / A-leg pattern).

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS

> VERDICT: **G-EQ = SOUND, spec-strength = TIGHT**
>
> Bundle: astropy__astropy-14096. The modeled `do`-block `lookupMissingAttribute(requested, frameOutcome, genuineOutcome)` has the fully-functional postcondition `ensures out = attrFallbackSpec requested frameOutcome genuineOutcome`, where `attrFallbackSpec = match frameOutcome with | some v => Except.ok v | none => genuineOutcome`. This pins `out` pointwise for every input, so only impls provably equal to `attrFallbackSpec` can verify — the tightest possible spec.
>
> Baselines: genuine `results/.../Solution.lean` verifies (exit 0); bundled `Solution_prepatch.lean` fails (exit 1) on exactly the discriminating clause — the `none` (genuine-miss) branch reduces to `Except.error { subject := requested } = genuineOutcome`, unprovable. That is precisely the masking bug (fabricated error named after the requested property `prop` instead of propagating the genuine `random_attr` error).
>
> Spec-too-weak attacks (all `same_spec(Solution, atk)=True`, all changed ONLY the impl region; `<n>.lean`):
> - atk_1 prepatch bug (`none => Except.error {subject:=requested}`): exit 1 — goal `…|none => Except.error {subject:=requested}) = …|none => genuineOutcome`. Rejected by the none-branch.
> - atk_2 always `genuineOutcome` (ignore prefix): exit 1 — goal `genuineOutcome = match…` fails on the `some v` branch (must be `Except.ok v`).
> - atk_3 `some _ => Except.error {subject:=requested}`: exit 1 — some-branch mismatch.
> - atk_4 always `Except.error {subject:=requested}`: exit 1.
> - atk_5 re-mask only failures on miss (`error _ => error {subject:=requested}`): exit 1 — the exact subtle bug variant; none-branch error-identity mismatch.
> - atk_6 always `Except.ok 0`: exit 1.
> - atk_7 corrupt value `Except.ok (v+1)` on `some v`: exit 1 — some-branch mismatch.
> All seven fail with genuine "unsolved goals" on the `ensures` equation (not compile errors). Both spec branches (`some` and `none`) are independently pinned, so no wrong impl survives.
>
> Positive control / non-vacuity: a structurally-different correct impl `frameOutcome.elim genuineOutcome (fun v => Except.ok v)` shares the spec and verifies (exit 0) once the proof case-splits (`at14096_pos3.lean`). Spec is satisfiable by a correct impl ⇒ non-vacuous.
>
> Refinement audit: all steps R / I / removed-op (A1=R, A2=I, A3=R+free-input, A4=removed buggy op); no axioms, no kind-3 hand-waving. The single changed op (`return self.__getattribute__(attr)`) is modeled deeply as "propagate the unchanged callee's outcome verbatim," with the callee's result carried as the free input `genuineOutcome` (grounded in the real unchanged `object.__getattribute__`). The spec holds for every value of `genuineOutcome`, assuming nothing false about it.
>
> Ungrounded-oracle probe: `genuineOutcome` is not an answer-key the impl can trivially echo to escape work — both the `some` and `none` branches are pinned, and the discriminating content (genuine error identity vs. fabricated `requested` name) is exactly what separates fixed from buggy. The echo IS the correct behavior here (django-11451 precedent), and every divergence from it is rejected. G-CONF skip is justified.

## Sub-review 2 — FAITHFULNESS + G-AX

> VERDICT — astropy__astropy-14096
>
> FAITHFULNESS: FAITHFUL
> G-AX: VACUOUS (no axioms; results/astropy__astropy-14096/ ships no axiom_check.py — axioms:[] in meta.json)
>
> EVIDENCE (Docker, gold patch applied at base_commit):
> - Post-gold `SkyCoord.__getattr__` body is literally `return self.__getattribute__(attr)` on the fall-through (confirmed via inspect.getsource in-container).
> - Spec output == real post-gold output on all F2P-shaped inputs:
>   - F2P (`c.prop`, where prop's getter accesses missing `random_attr`): real raises `AttributeError("...has no attribute 'random_attr'")` (names random_attr, NOT prop). Spec models this as requested=prop, frameOutcome=none, genuineOutcome=Except.error{subject:=random_attr}; attrFallbackSpec returns genuineOutcome verbatim → matches. The F2P assertion `pytest.raises(AttributeError, match="random_attr")` passes.
>   - Prefix value path (`c.ra`): real returns a value → frameOutcome=some v, spec returns Except.ok v → matches.
>   - Plain genuine miss (`c.does_not_exist_xyz`): real raises error naming the requested attr → matches (here subject==requested, both branches coincide).
> - Pre-gold (base_commit) confirms the real masking bug: `c.prop` raises naming `prop`, not `random_attr` — exactly what Solution_prepatch.lean encodes (`none => Except.error {subject:=requested}`).
>
> MECHANICAL RE-CHECKS (independent, in /tmp):
> - G-VERIFY: Solution.lean verifies, exit 0.
> - G-DIFF: Solution_prepatch.lean fails on exactly the miss-path clause (`Except.error {subject:=requested} = genuineOutcome` unsolved), exit 1.
> - Spec tightness: an attack impl that always returns genuineOutcome (ignoring frameOutcome) is REJECTED by the spec (exit 1). G-MUT killed 7/7.
> - same_spec(Solution, prepatch)=True; spec view free of repo-symbol/fix-vocabulary leakage.
>
> HONEST CAVEAT (not a gate failure): This is an abstraction-heavy "free-input" twin. The discriminating behavior (error names random_attr not prop) lives entirely in the value of the free input `genuineOutcome`, about which the spec asserts nothing; the Lean obligation is near-tautological ("return the free input on a miss"). The full soundness load rests on the refinement claim that `genuineOutcome : Except AttrErr Value` faithfully models `self.__getattribute__(attr)`'s outcome. That claim is sound here: the one-line gold fix propagates that unchanged callee's outcome verbatim, so modeling it as a verbatim-propagated free input (§3 unchanged-callee / A-leg pattern) is faithful — confirmed by the in-container post-gold behavior matching the spec on every F2P input shape. G-CONF=skip and G-AX=skip are appropriate. No drift, no spec-too-strong divergence found.

## Sub-review 3 — LEAKAGE

> VERDICT: NO-LEAKAGE
>
> Reconstruction attempt from the spec view alone: an attacker learns only that an attribute-access fallback should, on a genuine miss, return "the genuine attribute-resolution routine's outcome verbatim" rather than "a freshly minted failure renamed to the originally-requested attribute." This is precisely the behavior the PUBLIC problem_statement already demands in plain language: "the error message is misleading because it says `prop` doesn't exist, where it should say `random_attr` doesn't exist." An attacker could thus reconstruct *a* behavior-equivalent fix — but that capability comes entirely from the public issue, not from the spec view. The spec view does NOT disclose the gold's concrete mechanism (`return self.__getattribute__(attr)`): the genuine resolver is abstracted to the free input `genuineOutcome : Except AttrErr Value` and the spec asserts nothing about how it is obtained.
>
> Leak-token scan of the spec view (incl. all comments + docstrings): `getattribute` 0, `getattr` 0, `sky_coord(inate)`/`SkyCoord` 0, `AttributeError` 0, `random_attr` 0, `descriptor`/`property`/`subclass` 0, `__dict__` 0, `self.` 0. No filename, no patched symbol, no diff line. Apparent hits are all benign: `prop` is the substring of "propagated"; `delegat` is the generic phrase "delegates to on a miss is UNCHANGED" (no symbol named); `frame` is only the abstract variable `frameOutcome` (the unchanged resolution prefix) — generic, and it models the part of `__getattr__` the gold did NOT touch, so it cannot point to the edit.
>
> Identifiers present (`Name`, `Value`, `AttrErr.subject`, `attrFallbackSpec`, `lookupMissingAttribute`, `requested`, `frameOutcome`, `genuineOutcome`) are all generic descriptions of the missing-attribute fallback role; none echoes a repo symbol.
>
> Corroborating soundness (sanity only): Solution.lean verifies (rc 0); Solution_prepatch.lean fails on exactly the miss-path clause, rc 1; `same_spec(Solution, prepatch) = True`. The `requested` variable is unused in the spec (linter warning), confirming the contract does not consult the requested name on the miss path — matching the gold. meta.json records `G-LEAK: pass` (not relaxed).

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
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec = True, velvet tables). Real patched behavior of SkyCoord.`__getattr__` at base_commit 1a4462d + gold hunk: if '`_sky_coord_frame`' in self.`__dict__` and a prefix branch yields a value -> return it; otherwise `return self.__getattribute__(attr)`, propagating its outcome (value or genuine AttributeError naming whatever attribute actually failed) verbatim. The modeled attrFallbackSpec(requested, frameOutcome, genuineOutcome) = match frameOutcome | some v => ok v | none => genuineOutcome. Under the type bijection (mapping.md §2): (a) frameOutcome=some v matches the prefix value-paths (real returns v, model ok v); (b) frameOutcome=none matches `return self.__getattribute__(attr)` because genuineOutcome is a UNIVERSALLY-QUANTIFIED free input bound exactly to that unchanged callee's outcome, so the spec holds for every value the real routine can produce and imposes NO renaming to `requested`. The model is a pure pass-through of its two free inputs; it cannot be too strong (it constrains the miss path only to equal the genuine callee's outcome, which is literally the patch). No (requested, frameOutcome, genuineOutcome) triple exists on which the model disagrees with the real observable outcome. The only abstraction gap — a prefix branch that itself raises AttributeError, not representable in Option Value — narrows coverage (weaker), it does not create disagreement on any modeled input, so it is not a faithfulness break (that would be G-PANEL-1/adequacy territory, not too-strong drift). G-DIFF correctly fails the prepatch, which fabricates Except.error {subject := requested} on the none branch, disagreeing with genuineOutcome exactly when the genuine failure names a different attribute (the random_attr masking bug).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical across twins (same_spec(patch, prepatch)=True), so the spec view carries no patch-vs-prepatch tell. The public problem_statement already fully discloses the target behavior: a genuine missing-attribute access must report the attribute that actually doesn't exist (e.g. 'random_attr'), NOT a freshly-minted error renamed to the requested attribute ('prop'). The spec view (pure region attrFallbackSpec + method ensures) encodes exactly this at an abstract level: on a genuine miss (frameOutcome = none), the result is genuineOutcome verbatim, 'never a freshly minted failure renamed to requested'. This is derivable directly from problem_statement, not from the gold implementation. The gold edit's actual MECHANISM — delegating to self.`__getattribute__`(attr) — is NOT revealed anywhere in the spec view; nor is the hints_text suggestion (catch AttributeError and re-raise). frameOutcome merely abstracts the pre-existing, unchanged frame-transform resolution prefix (context, not the edit). No line reconstructs the gold beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
