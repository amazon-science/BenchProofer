# P2 adversarial audit — django__django-13363

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 AUDIT VERDICT — django__django-13363", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall: ACCEPTED** (go). Both audit gates pass.

## Per-gate table

| Gate | Verdict | Basis |
|---|---|---|
| **G-EQ** | **PASS** | G-EQ SOUND ∧ spec-strength TIGHT ∧ no kind-3 refinement. Single total `ensures out = resolveZoneName tzAware explicitZone currentZone`; 7 spec-too-weak / echo attacks all REJECTED; positive control verifies (non-vacuous); `resolveZoneName` is a concrete total `def`, not an opaque oracle. |
| **G-PANEL** | **PASS** | faithfulness FAITHFUL ∧ G-AX SOUND ∧ leakage NO-LEAKAGE. Spec models the unchanged `get_tzname` callee the gold patch delegates to; matches real post-gold behavior on F2P shapes + 100,006 (G-CONF) + 30,000 (independent) obs; empty axioms region; spec view leaks no repo symbol / patched file / hints-only token. |

### Underlying construction gates (from meta.json, all pass)
G-VERIFY pass · G-DIFF pass · G-MUT pass (12/12) · G-INTEGRITY pass · G-HYGIENE pass · G-LEAK pass · G-GOLD pass · G-CONF pass (100006 inputs, 0 disagreements) · G-RESOLVE pass · G-AX pass (20130 obs). Independent re-verify of `Solution.lean`: exit 0.

## Concrete defects + fixes

**None.** No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak was found across the three sub-reviews. No refinement required.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

> `results/` is unmodified. Final verdict below.
>
> ## VERDICT — django__django-13363
>
> **G-EQ: SOUND. Spec-strength: TIGHT.**
>
> ### Summary
> The bundle models two changed functions (`TruncDate.as_sql`, `TruncTime.as_sql`) as `dateCastZoneName`/`timeCastZoneName`, both with the single `ensures out = resolveZoneName tzAware explicitZone currentZone`. `resolveZoneName` is a concrete total `def` (deeply modeled), NOT an opaque axiom — there are zero axioms in the bundle. The spec is a total equality to a function of the three observable inputs, so it is maximally tight: any impl that deviates on any input fails.
>
> ### 1. Spec-too-weak attacks (machine-checked; impl-only swaps, spec byte-identical)
> All shared the spec (`same_spec = True`, with a negative control confirming `same_spec` returns False when the `ensures` is altered). All wrong impls were REJECTED on the discriminating clause `«ensures_1: out = resolveZoneName tzAware explicitZone currentZone»`.
>
> | attack | wrong impl | same_spec | verify exit | rejecting clause |
> |---|---|---|---|---|
> | atk_1 | **prepatch bug**: aware ⇒ `some currentZone` (ignores explicit) | True | 1 (fail) | `some currentZone = match explicitZone \| some z => some z` unprovable on the `some z` branch |
> | atk_2 | drop `tzAware` guard (never returns `none`) | True | 1 (fail) | `none`-branch goal unmet when `¬tzAware` |
> | atk_3 | swapped branches (explicit↔current/none) | True | 1 (fail) | same ensures |
> | atk_4 | always `return none` | True | 1 (fail) | same ensures |
> | atk_5 | aware+explicit ⇒ `return none` | True | 1 (fail) | `none = some z` on the explicit branch |
> | atk_6 | invert `tzAware` guard | True | 1 (fail) | same ensures |
> | atk_7 | prepatch on date site only (mixed) | True | 1 (fail) | date method fails; isolates per-site obligation |
>
> **Positive control (non-vacuity):** structurally different but correct impl — outer `match explicitZone`, inner `if tzAware` — `same_spec = True`, **verify exit 0**. The spec is satisfiable and non-vacuous. (An earlier `explicitZone.getD currentZone` form was semantically correct but the shipped tactic couldn't close `getD`; the match-form control verifies, confirming non-vacuity.)
>
> ### 2. Refinement audit
> - **No kind-3 steps.** The single changed op (replacing inline `get_current_timezone_name()-or-None` with the `tzinfo`-honouring selection) is modeled deeply as `resolveZoneName` (A-reference + I), not hidden behind an axiom on the function under change. Refinement steps are R / A-reference / I only.
> - **G-AX (deep-model soundness)** re-run in-container: rc 0 — `resolveZoneName == real TimezoneMixin.get_tzname` over 20,130 observations (boundary + 20,000 fuzz, seed 13363).
> - **G-CONF (R/I fidelity)**: re-run with `apply_gold=True` (the way the real gate runs it): rc 0, 0 disagreements over 100,006 inputs. NOTE: running `conformance_check.py` WITHOUT applying the gold patch yields rc 1 / 6 disagreements (the base-commit `as_sql` is the buggy code), but `gates.gate_conf` calls `run_in_container(..., gold_patch_path=patch.diff, apply_gold=True)` (gates.py:220-222), so the recorded PASS is correct — the apparent failure was purely an invocation artifact on my side, not a bundle defect.
> - **Prepatches fail for the RIGHT reason.** `Solution_prepatch_date.lean` and `Solution_prepatch_time.lean` both fail (exit 1) on exactly the discriminating clause: goal `some currentZone = match explicitZone with | some z => some z …` (the explicit-zone branch). The shipped `Solution.lean` verifies (exit 0). This is precisely the bug the F2P test `test_trunc_timezone_applied_before_truncation` exercises (melb/pacific tzinfo honoured).
> - No verifying model can refine to a non-resolving patch: the R-mappings (`Bool↔USE_TZ`, name `str↔String`, `tzinfo↔Option String` via rendered name) are exact because the downstream cast callees consume only the `tzname` string (mapping.md §3.2, confirmed by G-CONF capturing that exact argument).
>
> ### 3. Ungrounded-oracle probe
> No opaque oracle exists. `resolveZoneName` is a concrete total `def` over the inputs; the ensures pins `out` to it exactly. An impl cannot "echo" an answer-key — it must recompute the same total function of `(tzAware, explicitZone, currentZone)`. Every echo/permutation attempt (atk_1, atk_3) fails. The postcondition is fully grounded in the inputs.
>
> ### Which clause caught each attack
> The single `ensures out = resolveZoneName tzAware explicitZone currentZone` is the universal discriminator. Because `resolveZoneName` is total and the impl's output must equal it pointwise, the explicit-zone branch (`some z => some z`) is the load-bearing clause that catches the actual bug (atk_1, atk_5, prepatches), and the `none`/`tzAware`-guard structure catches the rest (atk_2, atk_4, atk_6).
>
> **Conclusion: bundle is SOUND, spec is TIGHT. No defect found.** `results/` left unmodified.

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

> Both prepatches share the identical spec (same `ensures` + pure region) as Solution.lean, and differ only in the impl region — so the G-DIFF failures genuinely demonstrate the frozen spec rejects the pre-patch (buggy) behavior, not a weakened spec.
>
> Let me do a final adversarial review of the spec strength. Key concern: could the spec be TOO STRONG? The spec is an exact equality `out = resolveZoneName ...`. I confirmed the real `get_tzname` matches it exactly on 30k inputs (PROBE1, independent expected). The only abstraction is modeling zones by their rendered string name (`Option String`), justified because nothing downstream inspects the zone beyond its rendered name. Let me confirm that claim: the patched `as_sql` only passes `tzname` (a str) to the cast callee. That's verified in PROBE2 and visible in the patch.diff.
>
> One last subtlety to probe adversarially: the spec models `explicitZone` as `Option String` (the rendered name), but the real `self.tzinfo` is an object. Two distinct tzinfo objects could render to the same name, or the same logical zone could render differently. This doesn't cause too-strong/drift since the spec only constrains the rendered-name carrier, which is exactly what flows downstream. The abstraction is faithful.
>
> Let me verify there is genuinely no consumed axiom in Solution.lean (the axioms region is empty — confirmed by reading lines 9-10: `-- axioms-start` / `-- axioms-end` with nothing between). So G-AX is about the A-reference deep model, which my independent fuzz validated as sound.
>
> Summary of findings:
>
> **Faithfulness: FAITHFUL.** The bundle models the timezone-name selection (`get_tzname`) that the gold patch delegates to. The F2P test `test_trunc_timezone_applied_before_truncation` adds `TruncDate`/`TruncTime` annotations with `tzinfo=melb`/`pacific` under `USE_TZ=True`, asserting the truncation uses the explicit zone. My independent in-container check (post-gold) confirms (PROBE2) the patched `TruncDate.as_sql`/`TruncTime.as_sql` thread the explicit zone name (`Australia/Melbourne`, `US/Pacific`) — not the ambient `UTC` — into the cast callee, exactly matching the spec's `tzAware ∧ explicitZone=some z ⇒ some z` leg. The spec's predicted output equals the real post-gold `tzname` on the F2P input shapes and on 100,006 conformance inputs (their G-CONF) plus my 30,000 independent observations. The `Option String` abstraction is faithful: nothing downstream inspects the zone beyond its rendered name. The two prepatches (sharing the identical frozen spec, confirmed via `same_spec`) both FAIL verification precisely on the discriminating clause the F2P test exercises, so the spec is not too weak. No correct behavior is rejected; no drift from observed test behavior.
>
> **G-AX: SOUND.** The only kind-A object is the deep-model A-reference `resolveZoneName` vs the unchanged real callee `TimezoneMixin.get_tzname`. The `-- axioms-start/end` region is empty (no consumed axiom). My independent fuzz (30,000 randomized observations over an extended zone set including fixed-offset `Etc/GMT±N`, DST-edge `Pacific/Chatham`, and abbreviation zones `GMT`/`EST`, with the expected computed from first principles, not by replaying `get_tzname`'s internals) found ZERO inputs where the real `get_tzname` violates the spec's resolution. The model's control flow (USE_TZ gate, explicit-vs-ambient selection) is an exact match.
>
> Docker evidence: post-gold (apply_gold=True), `TruncDate`/`TruncTime.as_sql` produce `tzname='Australia/Melbourne'` and `tzname='US/Pacific'` (explicit zone honored, ambient was `UTC`), matching the spec output; G-CONF 100,006 inputs 0 disagreements; my PROBE1 30,000 obs spec==real==independent-expected.
>
> VERDICT: faithfulness = FAITHFUL, G-AX = SOUND.

## Sub-review 3 — LEAKAGE (verbatim)

> The "pr" match is a substring false positive (it appears in words like "precedence", "expressed"). No actual repo symbol, patched file/function, diff line, hints-only token (ticket 31640, the PR/commit links, `get_tzname`), or fix-mechanism narration leaks into the spec view. The "pr" substring is in "precedence"/"surrounding" etc., not the literal token "PR".
>
> I have completed the full audit. Summary of findings:
>
> - **Verification**: Solution.lean verifies clean (exit 0).
> - **G-AX**: re-ran in-container — `resolveZoneName` == real `TimezoneMixin.get_tzname` on 20130 observations. Sound, not vacuous, and it's a deep model of the UNCHANGED callee (no consumed axiom). The spec is grounded concretely, not echoed to an opaque oracle (directive 8 clean).
> - **G-CONF**: re-ran correctly with `apply_gold=True` — 100006 inputs, 0 disagreements (my first run failed only because I forgot to apply the patch; the harness applies it).
> - **G-DIFF/soundness**: the prepatch (ambient-zone-unconditional — exactly the buggy behavior the public issue describes) fails to verify; the spec genuinely pins the discriminating `some z` (explicit-zone-honored) clause.
> - **Leakage**: spec view uses abstracted descriptive names; the discriminator it states ("a caller-supplied zone takes precedence over the ambient zone") is precisely the publicly-requested feature.
>
> NO-LEAKAGE
>
> Reconstruction attempt from spec view alone: The spec view describes "the timezone name selected when casting a stored datetime down to a calendar date / wall-clock time for a database backend," with the obligation that "a caller-supplied target zone is honoured rather than discarded in favour of the ambient one" (when zone-awareness is in effect). This reconstructs to: "make the date/time cast use the passed-in timezone instead of always using the active/current one." That is verbatim the public problem_statement, which already names `TruncDate()`/`TruncTime()`, the `tzinfo` parameter, and states the bug as "it actually uses the return value from get_current_timezone_name() unconditionally and completely discards the passed in timezone info object." The spec view therefore reveals nothing beyond the public issue and does not enable reconstruction of the gold edit's specifics — it does NOT name the patched file `django/db/models/functions/datetime.py`, the patched methods `TruncDate.as_sql`/`TruncTime.as_sql`, the delegate `self.get_tzname()`, the removed line `timezone.get_current_timezone_name() if settings.USE_TZ else None`, or any hints_text-only token (ticket 31640, the PR/commit links, `get_tzname`). Token scans confirm: spec-view identifiers (`dateCastZoneName`, `timeCastZoneName`, `resolveZoneName`) are abstract paraphrases that echo no repo symbol; the only repo-derived concepts present (cast-to-date/time, supplied-zone-honored-vs-discarded) are all in the public problem_statement.
>
> Leaking token: none. (The G-LEAK "pass" status in meta.json is correct; this is a genuine problem_statement↔gold alignment, NOT a relaxed-leakage case.)
>
> verdict: NO-LEAKAGE

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

**Machine verdict**

Rigorous checks performed at base_commit 76e0151 (Django 3.1.dev):

1. **SPEC BYTE-IDENTITY:** same_spec(Solution.lean, Solution_prepatch_date.lean, velvet)=True and same_spec(Solution.lean, Solution_prepatch_time.lean, velvet)=True. spec_view/spec_signature over the velvet backend are identical for all three files (the differences are confined to the elided impl region). Earlier False result was an artifact of passing file paths instead of file contents to same_spec; re-run with contents confirms True.

2. **LEAN VERIFICATION:** scripts/lean_verify.sh Solution.lean -> exit 0 (both dateCastZoneName and timeCastZoneName prove_correct against `out = resolveZoneName ...`). Both prepatch diff-detectors FAIL verification (exit 1) precisely on the `| some z => some z` explicit-zone clause, so G-DIFF is real and the spec discriminates the fix.

3. FAITHFULNESS (the G-PANEL-2 concern): resolveZoneName is a DEEP MODEL (A-reference, no consumed axiom) of the unchanged callee TimezoneMixin.get_tzname (datetime.py:17). Real get_tzname:
   tzname=None; if settings.USE_TZ: if self.tzinfo is None: tzname=get_current_timezone_name() else: tzname=`_get_timezone_name`(self.tzinfo); return tzname.
   axiom_check.py PASSES against the real repo: 'G-AX OK ... sound on 20130 observations (boundary + 20000 fuzz, seed=13363)'.
   Independent adversarial sweeps I ran against the REAL get_tzname:
     - ALL 597 pytz zones x {3 ambient zones} x {USE_TZ on/off}: 0 mismatches (3588 obs).
     - 28 datetime.timezone fixed offsets (utc + -12..+14h): 0 mismatches.
   The model is neither too strong nor drifting on any input reachable at this commit. The gold change (as_sql delegating to self.get_tzname()) is captured deeply; downstream cast callees (datetime_cast_date_sql/time_sql) are unchanged and deterministic in tzname, and the mapping observes exactly the tzname argument.

4. The one divergence exists only for a None-rendering tzinfo (zoneinfo), which is not constructible in Django 3.1 and lies outside the declared Option-String-of-rendered-names bijection domain. It does not make the spec too strong on the modeled domain; it is a boundary of the abstraction, not a repo disagreement on any exercisable input.

**Conclusion:** spec is FAITHFUL — no reachable input where resolveZoneName disagrees with the real TimezoneMixin.get_tzname.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Attacker-3 (leakage / gold-reconstruction) for django__django-13363 (velvet). Gold edit (patch.diff verbatim, patch_is_gold=true): at TruncDate.as_sql (datetime.py:292/295) and TruncTime.as_sql (:305/308) replace `tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None` with `tzname = self.get_tzname()` — behaviorally: when USE_TZ and an explicit tzinfo is supplied, honour that explicit zone instead of discarding it for the ambient zone.

Verification performed:
1. Reconstructed the exact spec view the consumer sees via swebench_unified.markers.spec_view with the velvet LanguageTables (flavor=lean). impl regions and prove_correct bodies are elided; only imports, options, the `resolveZoneName` pure def, empty pre/post-condition regions, and the two `method … ensures out = resolveZoneName …` obligation headers remain.
2. Confirmed spec region is byte-identical across variants: markers.same_spec(gold, prepatch_date)=True and same_spec(gold, prepatch_time)=True (spec_signature len 2670). So the frozen spec is stable and prepatch differences live only in the elided impl.

Leakage assessment — spec view vs PUBLIC problem_statement (NOT hints_text): the public problem_statement already discloses the entire fix explicitly: it states TruncDate 'uses the return value from get_current_timezone_name() unconditionally and completely discards the passed in timezone info object', names the offending line (datetime.py#L295), notes 'a similar issue is happening in TruncTime', and points directly to the method it expects to be used (datetime.py#L17 = TimezoneMixin.get_tzname). Thus the edit sites, the removed expression, and the delegated callee are all public.

The spec view models this behavior ABSTRACTLY as resolveZoneName (none when not aware; explicit zone when supplied; else ambient) with docstrings stating 'a caller-supplied zone takes precedence over the ambient zone.' This is a faithful formalization of behavior the problem_statement already spells out in prose, and it actually reveals LESS repo specificity than the public statement: no file/line, no `get_tzname`, no `TruncDate/TruncTime`, no `settings.USE_TZ`, generic symbol names. No spec-view line adds gold-edit information beyond problem_statement. G-AX/G-CONF/G-DIFF/G-GOLD all pass; axioms=[] (no consumed axiom; resolveZoneName is an A-reference deep model of the unchanged callee). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
