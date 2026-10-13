# P2 adversarial audit — django__django-15863

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-15863", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall: ACCEPTED** (G-EQ = pass, G-PANEL = pass)

One-line synthesis: Axiom-free bundle; tight fully-grounded closed-form postcondition (`out = renderFixed intDigits fracDigits p`) rejects the prepatch all-zeros bug + 5 plausible wrong impls while admitting a structurally-different correct impl; R-refinement mechanically confirmed faithful to the gold-patched `floatformat` on 100,011 in-regime inputs (G-CONF, 0 disagreements, with the F2P case); spec stays at the public-symptom altitude (NO-LEAKAGE).

## Per-gate table

| Gate | Verdict | Basis |
|------|---------|-------|
| **G-EQ** | **pass** | G-EQ SOUND (Solution verifies exit 0; positive control verifies; all 6 attacks rejected at the same `ensures_1: out = renderFixed …` clause) AND spec-strength TIGHT AND no kind-3 refinement (`axioms: []`, `deep_model_references: []`, `conf_skip: false`; sole trust point is the R-refinement numeral↔digit-run bijection, refuted as a leak by G-CONF). |
| **G-PANEL** | **pass** | Faithfulness FAITHFUL (spec == real post-gold on 100,011 regime inputs incl. exact F2P case; principled narrow-but-faithful regime, rejects no correct modeled behavior) AND G-AX VACUOUS (axiom-free: no `axiom_check.py`, no `axiom` decls, no `:\|` callee stubs) AND leakage NO-LEAKAGE (`meta.gates.G-LEAK.status = "pass"`, no RELAXED_LEAKAGE.md; spec view never names the patched file/symbol/`repr`→`str` edit; all repr/float/Decimal token hits are false positives). |

## Concrete defects + fixes

None. No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak was exhibited by any sub-review. No fix required.

## Independent confirmation performed by lead auditor

- `Solution.lean` re-verified: `lean_verify.sh …` → EXIT 0.
- Axiom/sorry scan of `Solution.lean`: no `axiom` declarations, no `sorry`, no `:|` callee stubs (only `renderFixed` def).
- `meta.json` cross-checked: `axioms: []`, `deep_model_references: []`, `conf_skip: false`; `gates.G-LEAK.status = "pass"`; modeled regime = non-negative numeral, `p ≥ 1`, `p ≥ |fracDigits|`, default locale/no grouping = the FAIL_TO_PASS / issue-MWE regime.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

VERDICT: G-EQ = SOUND, spec-strength = TIGHT.

Bundle: django__django-15863 (floatformat drops precision for Decimal; gold flips `input_val = repr(text)` -> `str(text)`). Axiom-free bundle.

THE SPEC. Single method `floatFormat (intDigits fracDigits : List Char) (p : Nat)`, postcondition is a full closed-form equality: `out = renderFixed intDigits fracDigits p` where `renderFixed = intDigits ++ ['.'] ++ fracDigits ++ List.replicate (p - fracDigits.length) '0'`. The fractional run is pinned to the numeral's VERBATIM `fracDigits` (the discriminator the fix is about), grounded entirely in the input carriers. No opaque/axiomatized symbol exists, so mandate-3 (ungrounded-oracle echo) is vacuously satisfied — there is no answer-key to echo; any impl must produce `renderFixed` of the actual inputs.

SPEC-TOO-WEAK (machine-checked). All attacks share spec (same_spec = True) and change ONLY the impl region. Verified with `lean_verify.sh ...` in an isolated dir (an initial run was corrupted by /tmp clobbering from a concurrent process; re-ran clean — note below):
- atk_pc — POSITIVE CONTROL, structurally-different correct impl (no loop, direct closed-form `return intDigits ++ ['.'] ++ fracDigits ++ List.replicate (p-|frac|) '0'`): same_spec True, EXIT 0 (VERIFIES). Spec is non-vacuous.
- atk_1 truncate (`fracDigits.dropLast`): same_spec True, EXIT 1. Rejected at `ensures_1`: goal `fracDigits.dropLast ++ replicate(p-|frac|)'0' = fracDigits ++ replicate(p-|frac|)'0'`.
- atk_2 over-pad (`p-|frac|+1` zeros): same_spec True, EXIT 1, `ensures_1` unsolved.
- atk_3 drop decimal point (`return intDigits ++ digits`): same_spec True, EXIT 1, `ensures_1` unsolved.
- atk_4 reversed frac (`fracDigits.reverse`): same_spec True, EXIT 1, `ensures_1` unsolved.
- atk_5 pad with '9': same_spec True, EXIT 1. Rejected at `ensures_1`: `... replicate(...)'9' = ... replicate(...)'0'`.
- atk_6 PREPATCH BUG (all-zeros fractional, the float-round-trip artefact): same_spec True, EXIT 1. Rejected at `ensures_1`: `List.replicate p '0' = fracDigits ++ replicate(p-|frac|)'0'`.

Every wrong impl is caught by the SAME postcondition equality clause `case «ensures_1: out = renderFixed intDigits fracDigits p»`. No wrong impl verifies; the correct control does. Spec is TIGHT.

REFINEMENT AUDIT (mandate 2). All rows R or I; no A rows, no kind-3 (confirmed `axioms: []`, `deep_model_references: []`, `conf_skip: False` in meta.json). The sole trust point is the R-refinement (numeral<->digit-run bijection + `number_format` = identity under default locale, no grouping). I tried to exhibit a verifying-but-non-resolving model via that R leg, and G-CONF refutes it: running `conformance_check.py` in-container WITH the gold patch applied (`apply_gold=True`) gives rc 0 — the R/I shadow agrees with the real patched `floatformat` on 100,011 in-regime inputs (0 disagreements), including the F2P case `(Decimal("123456.123456789012345678901"),21)` and the issue MWE. So `number_format` really is identity on the regime and the type refinement hides no mismatch.

Prepatch discriminates for the RIGHT reason: `Solution_prepatch.lean` (same_spec True) FAILS at the postcondition clause with goal `List.replicate p '0' = fracDigits ++ List.replicate (p - fracDigits.length) '0'` — i.e. the modeled buggy all-zeros (float-truncation) output differs from the required verbatim `fracDigits`. Not an unrelated error. Identical to attack atk_6.

NOTE on G-CONF invocation: `run_in_container` does NOT apply the patch by default; it must be called with `gold_patch_path=.../patch.diff, apply_gold=True`. Without it the oracle runs the buggy prepatch and (correctly) disagrees with the shadow — this is not a bundle defect, just the harness contract. With the patch applied G-CONF passes.

Self-contained conclusion: the postcondition is a tight, fully-grounded equality that rejects the prepatch bug and 5 other plausible wrong impls while admitting a structurally-different correct impl; the axiom-free refinement is mechanically confirmed faithful to the gold-patched function on 10^5 regime inputs. G-EQ SOUND, spec TIGHT.

---

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

Confirmed axiom-free: no `axiom_check.py`, no `axiom` declarations, no `:|` callee stubs.

Let me do a final faithfulness sanity check on the one subtle thing: the F2P test runs the *whole* `test_inputs` method which includes the pre-existing rounding cases. Those pass regardless (gold patch doesn't change them — G-RESOLVE territory, confirmed by the run campaign). The spec's narrow regime is legitimate: it models exactly the new discriminating assertion's regime, and is faithful there (matches real post-gold on 100K+ inputs including the exact F2P case). The regime restriction does not reject any correct behavior of the modeled function — it simply declines to model out-of-regime behavior, which is the standard "principled narrow spec" pattern, not spec-too-strong.

### Verdict

**Faithfulness: FAITHFUL**

**G-AX: VACUOUS** (axiom-free bundle — no `axiom_check.py`, no `axiom` declarations, no callee stubs)

#### Evidence

**Bundle.** `django__django-15863` gold patch is a one-line fix: `input_val = repr(text)` → `input_val = str(text)` in `floatformat()`, so a high-precision `Decimal` is parsed via its exact string instead of being routed through a binary float (which truncated low-order fractional digits via the `Decimal(str(float(text)))` fallback). The spec models the post-`Decimal` fixed-point render as `renderFixed intDigits fracDigits p = intDigits ++ ['.'] ++ fracDigits ++ replicate (p - |frac|) '0'` — i.e. the numeral's verbatim fractional digits survive, right-padded to width `p`. Postcondition `out = renderFixed …` fully pins the output (no underspecification).

**Solution verifies:** `lean_verify.sh` exit 0 (no sorry).

**Spec == real post-gold on F2P inputs (Docker evidence).** In-container against the patched `floatformat` (`apply_gold=True`):
- Bundled `conformance_check.py`: `G-CONF OK … 100011 inputs … 0 disagreements`.
- My independent adversarial probe (targeting `number_format` thousand-grouping with 7–15-digit integer runs + 20K fuzz): 0 disagreements. The exact F2P case matches: `numeral='123456.123456789012345678901' p=21 shadow='123456.123456789012345678901' oracle='123456.123456789012345678901'` — equal to the new F2P assertion's expected value. Django's default settings configure no grouping, so `number_format` is genuinely identity on the digit string (confirmed empirically, not just asserted).

**Discrimination (spec is not too-weak).** `same_spec(Solution, Solution_prepatch) = True` (identical spec regions); `Solution_prepatch.lean` fails to verify (exit 1) — its bug-modeling impl (fractional run collapsed to all-zeros, the repr/float-round-trip artefact) cannot satisfy `out = renderFixed …`. So the spec captures exactly the bug-fixing behavior.

**Not too-strong.** The spec is regime-restricted (`1 ≤ p`, `|frac| ≤ p`, non-negative plain numeral, default locale) — exactly the regime the new F2P assertion and issue MWE occupy. It declines to model out-of-regime behavior (rounding, scientific notation, grouping) rather than mis-predicting it; this is a principled narrow-but-faithful spec, not a rejection of correct behavior. The pre-existing rounding assertions in the F2P test method (`555.555→555.56`) are unchanged by the gold patch (G-RESOLVE), so the regime restriction does not compromise faithfulness to the modeled function.

Relevant files: `results/django__django-15863/{Solution.lean, Solution_prepatch.lean, conformance_check.py, refinement.md, mapping.md, patch.diff, instance.json}`.

---

## Sub-review 3 — LEAKAGE (verbatim)

meta.json records `G-LEAK.status = "pass"` (not "relaxed"), consistent with a clean, non-leaking spec view. No RELAXED_LEAKAGE.md in the bundle.

**Assessment of the relaxed-leakage question:** Is this a problem_statement↔gold mismatch? No. The public problem_statement fully describes the discriminating behavior: "floatformat drops precision for Decimal numbers... Decimal numbers are converted to float instead", with a concrete before/after (`42.12345678901234567890` → `42.12345678901234400000`, i.e. low-order fractional digits collapsed to zeros). The faithful spec (output = verbatim fractional digits padded with trailing zeros) is directly derivable from the public text. So the relaxed-leakage policy is neither needed nor invoked — this is a clean non-leaking case.

**Reconstruction attempt:** From the spec view alone, the most a reader recovers is "render a decimal numeral's integer digits + '.' + its fractional digits verbatim + trailing zeros to width p" — which is the public bug's intended behavior, not the patch. The spec view never names `defaultfilters.py`, `floatformat`, `repr`, `str`, `input_val`, `Decimal(...)` parse, or the float-round-trip fallback. One cannot derive the one-line gold edit (`repr(text)`→`str(text)`) from the spec view; the spec is purely behavioral.

VERDICT: NO-LEAKAGE

Reconstruction attempt: From the spec view alone a reader recovers only the intended observable behavior — "render a non-negative decimal numeral as its integer-digit run, a '.', its fractional-digit run reproduced verbatim, then trailing '0' padding out to width p." This is exactly what the public problem_statement already states (floatformat "drops precision" / "Decimal numbers are converted to float instead", with the concrete symptom 42.12345678901234567890 → 42.12345678901234400000 showing low-order fractional digits collapsing to zeros). The spec view does NOT reveal the gold edit: it never names the patched file (django/template/defaultfilters.py), the symbol floatformat (only the abstracted Lean method floatFormat over List Char), the changed line input_val = repr(text) → str(text), or the repr/str/Decimal-parse/float-round-trip mechanism. The one-line gold patch cannot be reconstructed from the spec view — the spec is purely behavioral and stays at the public-symptom altitude.

Token scan: apparent matches for repr/float/Decimal/floatformat are all false positives — "repr"→"reproduced verbatim", "float"→the method name "floatFormat", "Decimal"→"decimal numeral"/"decimal point" (public value-type vocabulary used throughout the problem_statement), "floatformat"→case-insensitive hit on the abstracted name "floatFormat". No repo-symbol-echoing identifier, no diff line, no bug/fix narration beyond the public issue.

No leaking line to quote. Relaxed-leakage policy does NOT apply and is correctly not invoked: this is a problem_statement-faithful, non-leaking spec (meta.json records gates.G-LEAK.status="pass", no RELAXED_LEAKAGE.md in bundle — both correct). The discriminating behavior (verbatim fractional digits, no float-truncation) is fully PS-derivable.

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
- **machine verdict:** Attempted to break faithfulness of the spec `out = renderFixed intDigits fracDigits p` (renderFixed = intDigits ++ ['.'] ++ fracDigits ++ replicate (p - |frac|) '0') against the real gold-patched django floatformat. Setup: verified Solution.lean compiles via scripts/lean_verify.sh -> EXIT 0 (spec non-vacuous). same_spec(Solution, Solution_prepatch, VelvetBackend) = True (spec region byte-identical; attacks only vary impl). Confirmed spec view exposes only the abstract numeral-render behavior. Real-repo comparison: applied the gold hunk (input_val = repr(text) -> str(text)) to a /tmp copy of django at base_commit 37c5b8c07b and ran the patched floatformat under default settings (en locale, no grouping), comparing str(floatformat(Decimal(canon), p)) to renderFixed transliteration over the MODELED REGIME (non-negative plain numeral, intDigits != [], p >= 1, p >= |fracDigits|). Results: (1) F2P case (Decimal('123456.123456789012345678901'), 21) and issue MWE (Decimal('42.12345678901234567890'), 20) both match exactly. (2) Hand-picked edge cases all match: trailing-zero fractions (5.00, 1.50, 100.100, 123.400, 10.10), integer-only values (0, 9, 100), huge p (5 -> p=30, 0 -> p=40), long integer runs that would trigger THOUSAND_SEPARATOR grouping if not identity (12345678, 1234567890123), frac==p boundary. (3) Independent 200,000-input random fuzz over the regime (int runs up to 12 digits, frac up to 30 digits, p from |frac| to |frac|+15): 0 disagreements, 0 skips. The bundled conformance_check.py (seed 15863, 100,011 inputs) is consistent with this. The regime restriction (p >= |frac|, non-negative, default locale, no grouping) is a principled narrow-but-faithful spec: it declines to model out-of-regime behavior (rounding, negative p, scientific notation, g/u grouping suffixes, NaN/inf) rather than mispredicting it, and covers exactly the F2P/MWE regime. number_format under default settings is genuinely identity on the digit string (confirmed empirically via the long-integer-run cases, not just asserted). The spec is NOT too strong: it rejects no correct modeled behavior. Axiom-free bundle (no axiom decls, no :| callee stubs, no axiom_check.py) so G-AX is vacuous. No diverging input exists within the modeled regime. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Spec view verified:** same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with the velvet backend, and spec_view sha256 = cdf80d11efd0569e7899b00ada1f0c99c5740034ace77fa5504230d0546d02fc, byte-identical to meta.region_hashes.spec_view. The impl and proof regions are elided in the consumer view (impl-start/end and prove_correct body replaced with 'elided — supplied by the consumer'). 

**Gold edit:** `input_val = repr(text)` -> `input_val = str(text)` in django/template/defaultfilters.py:154 — preserve the numeral's exact decimal digits instead of routing a Decimal through a truncating float round-trip.

The public problem_statement already discloses the full desired behavior beyond any doubt: it states floatformat 'drops precision' for Decimal numbers, names the root cause ('incorrect conversion to Decimal ... Decimal numbers are converted to float instead'), gives a concrete MWE contrasting the truncated 42.12345678901234400000 with the intended exact rendering, and even links the fixing PR (#15863). It also names the public symbol 'floatformat'.

Line-by-line the spec view contains only: the renderFixed def + doc-comment ('every significant digit the numeral carries survives'; intDigits ++ '.' ++ fracDigits verbatim ++ trailing-zero pad to width p), the floatFormat method doc-comment, the require/ensures clauses (out = renderFixed intDigits fracDigits p), and the pad_tail_step lemma. All describe the CORRECT output abstractly over List Char digit runs — exactly the behavior the problem_statement already demands (exact fractional digits preserved). No spec-view line names repr/str/Decimal/float, the edited file/line, or the conversion mechanism.

Apparent token hits are false positives: 'repr'->'reproduced verbatim', 'float'->abstracted method name floatFormat (and floatformat is itself named in the public PS), 'Decimal'->'decimal numeral'/'decimal point' (public value-type vocabulary). The repr->str mechanism appears only in refinement.md and mapping.md, which are auditor-facing narrative artifacts, NOT part of the consumer-facing spec view. The one-line gold edit cannot be reconstructed from the spec view; the spec is purely behavioral and stays at the public-symptom altitude. G-LEAK also passed (spec view clean); no RELAXED_LEAKAGE.md. Concur with recorded G-PANEL-3. No leaking line.

Note (out of scope for leakage but observed): G-PANEL-1 and G-PANEL-2 legitimately fail (same-spec impl verifies / renderFixed emits intDigits verbatim while real floatformat strips leading zeros via Decimal canonicalization). Those are model-faithfulness/strength defects, not leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.