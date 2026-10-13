# P2 adversarial audit — django__django-14608

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-14608", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED**

Velvet twin-artifact for the "Add `nonform` CSS class for non form errors in
FormSets" change. The spec `buildNonFormErrors` pins the two F2P observables —
messages preserved (`out.data = errors`) and rendered class `errorlist nonform`
(`out.cssClass = cssClassFor (some "nonform")`). Both audit gates pass.

## Per-gate verdict table

| Gate    | Verdict | Basis |
|---------|---------|-------|
| G-EQ    | **pass** | G-EQ SOUND ∧ spec-strength TIGHT ∧ no kind-3 refinement. Solution.lean verifies (rc 0); `#print axioms buildNonFormErrors` → does not depend on any axioms; prepatch fails on the exact discriminator; 6 spec-too-weak attacks all rejected, positive control (atk_7) verifies. |
| G-PANEL | **pass** | faithfulness FAITHFUL ∧ G-AX SOUND ∧ leakage NO-LEAKAGE. In-container probe of all 4 real F2P scenarios matches spec prediction; G-CONF 0/100011 disagreements; axiom_check.py sound on 84+20000 combos; no gold-internal token in spec view. |

### Lead-auditor independent reconfirmation
- `Solution.lean` verifies, exit 0.
- `#print axioms buildNonFormErrors` → `'buildNonFormErrors' does not depend on any axioms`.
- `Solution_prepatch.lean` fails (exit 1) with unsolved goal
  `cssClassFor none = cssClassFor (some "nonform".toList)` — the exact bug→fix delta.
- `patch.diff` matches the modeled delta: both `full_clean` sites
  (formsets.py:336 empty, :383 validation-error) gain `error_class='nonform'`.
- `meta.json`: `axioms: []`; all pipeline gates (G-VERIFY, G-DIFF, G-CONF, G-AX,
  G-RESOLVE, G-MUT, G-INTEGRITY, G-HYGIENE, G-LEAK, G-GOLD) green; `results/` clean.

## Concrete defects
None. No verifying-but-wrong implementation, no unfaithful divergence, no unsound
axiom (zero consumed axioms; sole A-reference `cssClassFor` validated by G-AX), no
leak. No fix required.

## Process caveat (not a bundle flaw)
The G-EQ reviewer's first G-CONF run omitted `apply_gold`/`gold_patch_path`,
yielding a spurious FAIL where live anchors showed prepatch `errorlist`; re-running
in the gate's actual mode (gold patch applied) passes cleanly (rc 0, 0/100011).

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

VERDICT: G-EQ = SOUND, spec-strength = TIGHT

Bundle: django__django-14608. Spec: `buildNonFormErrors (errors : List (List Char)) → ErrorBox` with two postconditions: `out.data = errors` (messages preserved) and `out.cssClass = cssClassFor (some "nonform")` (which reduces to the literal `"errorlist nonform"`). `cssClassFor` is a concrete `def`, not an axiom.

REFERENCE checks (all confirmed):
- Original Solution.lean verifies (exit 0).
- `#print axioms buildNonFormErrors` → "does not depend on any axioms" (axioms-start/end empty; the only kind-A construct is the A-reference deep model `cssClassFor`, NOT consumed).
- Solution_prepatch.lean FAILS for the RIGHT reason: unsolved goal `cssClassFor none = cssClassFor (some "nonform".toList)` on the `out.cssClass` clause — the exact F2P-asserted discriminator (bare `errorlist` vs `errorlist nonform`), not an unrelated error.
- G-AX (in-container, gold not needed): rc 0 — `cssClassFor` deep model == real `ErrorList.__init__` class string on 84 boundary + 20000 fuzz combos.
- G-CONF (in-container, gold patch applied as the gate does): rc 0, 100011 inputs, 0 disagreements. Note: the live-anchor leg is genuinely patch-sensitive — run WITHOUT the patch it reports the prepatch `errorlist` (I verified this), run WITH it reports `errorlist nonform`. The conformance check is discriminating, not tautological.

### SPEC-TOO-WEAK ATTACKS (all share spec via same_spec=True; impl region only changed; all verify exit 1 = rejected):
- atk_1 (prepatch bug, `cssClassFor none`): rejected by clause `out.cssClass = cssClassFor (some "nonform")` → `cssClassFor none = cssClassFor (some "nonform")`.
- atk_2 (wrong modifier `nonfield`): rejected by `cssClass` clause → `cssClassFor (some "nonfield") = cssClassFor (some "nonform")`.
- atk_3 (drop messages, `data := []`): rejected by `out.data = errors` clause → `[] = errors`.
- atk_4 (hardcoded `"errorlist"`): rejected by `cssClass` clause → `"errorlist".toList = cssClassFor (some "nonform")`.
- atk_5 (no-space concat `"errorlist"++"nonform"` = `errorlistnonform`): rejected by `cssClass` clause → `"errorlist".toList ++ "nonform".toList = cssClassFor (some "nonform")`. Confirms the separating space is load-bearing and matches real Django `'errorlist {}'.format('nonform')`.
- atk_6 (`data := errors.reverse`): rejected by `out.data = errors` clause → `errors.reverse = errors`.

POSITIVE CONTROL (atk_7, structurally different — named `modifier` binding, reordered fields, `let box`): same_spec=True, verifies exit 0. Spec is non-vacuous/satisfiable.

UNGROUNDED-ORACLE PROBE: No opaque/axiomatized symbol exists to echo. `cssClassFor` is a concrete computable def validated against real Django; the postcondition pins the literal `"errorlist nonform"`, and near-miss strings (atk_4/5) are rejected. No answer-key echo possible.

REFINEMENT AUDIT: refinement.md steps are all R/A-reference/I, no kind-3. The changed op (which `error_class` argument `full_clean` supplies) is modeled directly in the do-block; the unchanged class-string computation is the A-reference (`cssClassFor`), validated by G-AX not hidden behind a consumed axiom. The two-field abstraction (messages + rendered class) captures exactly the F2P observable (`<ul class="errorlist nonform">`); both gold construction sites apply the identical delta and are correctly collapsed to one method.

Caveat on my process (not a bundle flaw): my first G-CONF run omitted `apply_gold`/`gold_patch_path`, producing a spurious FAIL where live anchors showed prepatch `errorlist`; re-running with the gold patch applied (the gate's actual mode) passes cleanly.

---

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

results/ is clean (no modifications). The prepatch differs only in the impl region: `cssClassFor none` (pre-patch: bare `errorlist`) vs `cssClassFor (some "nonform")` — the exact bug→fix delta the F2P tests assert.

Let me do a final adversarial consideration on spec-too-strong. The spec requires `out.cssClass = cssClassFor (some "nonform")` — exactly `errorlist nonform`. Is there any correct implementation the gold accepts that this would reject? The gold patch hardcodes `error_class='nonform'`, so `errorlist nonform` is the unique correct output; no valid alternative renders a different class. The messages clause `out.data = errors` is the identity-preservation the patch maintains. Neither over-constrains beyond what the F2P tests observe.

One more: confirm the modeled domain covers F2P inputs — messages are arbitrary `List (List Char)` with no `require` precondition, so all F2P message shapes (single/multi messages, special chars) are in domain. Confirmed.

### Verdict

faithfulness = FAITHFUL
G-AX = SOUND

Change under test: gold patch (`patch.diff`, verbatim) makes `BaseFormSet.full_clean` construct the non-form-error collection with `error_class='nonform'` at both sites (`django/forms/formsets.py:336` empty, `:383` validation-error), so it renders under CSS class `errorlist nonform` instead of bare `errorlist`; messages unchanged.

Spec (`Solution.lean`, verifies clean, exit 0): `method buildNonFormErrors` with `ensures out.data = errors` (messages preserved) and `ensures out.cssClass = cssClassFor (some "nonform")` (= `"errorlist nonform"`). These are exactly the two F2P observables.

Faithfulness — FAITHFUL:
- F2P tests assert (a) `str(non_form_errors()) == '<ul class="errorlist nonform">...'` and (b) `non_form_errors() == [<message>]` across validate_max / validate_min / custom-clean / admin scenarios.
- My independent in-container probe applying the gold patch ran all 4 real F2P scenarios and read the real post-gold observables: every one produced `error_class = "errorlist nonform"` and preserved messages — exactly the spec's prediction. No divergence.
- G-CONF with the gold patch applied: spec-shadow == real `patch.diff` behavior on 100,011 inputs, 0 disagreements (rc 0).
- The spec does not over-constrain; domain (arbitrary `List (List Char)`, no precondition) covers all F2P input shapes.
- G-DIFF confirmed: `Solution_prepatch.lean` fails `prove_correct` with unsolved goal `cssClassFor none = cssClassFor (some "nonform")`.

G-AX — SOUND (one A-reference, no consumed axioms; `axioms: []` in meta):
- The only kind-A construct is the deep model `cssClassFor` for the UNCHANGED callee `ErrorList.__init__` class-string branch (`None→'errorlist'`, `label→'errorlist '+label`).
- Independently confirmed sound in-container: axiom_check.py ran the REAL `django.forms.utils.ErrorList` on 84 boundary + 20,000 fuzzed (label, message-list) combinations — including `''`, multi-token, whitespace, sentinel/unicode chars — and every observed `.error_class` equaled the model, and `list(el) == list(messages)` round-tripped. rc 0.

---

## Sub-review 3 — LEAKAGE (verbatim)

All gold-internal tokens (patched method `full_clean`, file `formsets.py`, the `error_class=` kwarg, the `_non_form_errors` attribute) are absent from the spec view. The only behavioral content revealed — non-form errors render under class `errorlist nonform` — is verbatim what the public problem_statement requests.

### Verdict: NO-LEAKAGE

Reconstruction attempt from the spec view alone: The spec view exposes the method `buildNonFormErrors`, an `ErrorBox` (an error collection carrying ordered `data` messages plus a `cssClass` string), `cssClassFor` (`none -> "errorlist"`, `some m -> "errorlist " ++ m`), and the discriminating postcondition `out.cssClass = cssClassFor (some "nonform".toList)` — i.e. "the non-form-error collection renders under CSS class `errorlist nonform`, with its messages preserved." An engineer reading this would learn exactly: non-form errors in a FormSet should be tagged with the `nonform` CSS modifier so they render as `errorlist nonform`. They would then go find the FormSet's non-form-error construction and supply the `nonform` label.

But that is precisely, and only, what the public `problem_statement` already states — and the PS here is maximally explicit. Its literal title is "Add `nonform` CSS class for non form errors in FormSets," it names `ErrorList`, the `nonfield` precedent for non-field errors, "rendering form error messages," and asks to "add this nonform CSS class." Every token in the spec view (`nonform`, `errorlist`, ErrorList-as-collection, non-form-errors, CSS-class rendering) is present in the problem_statement. No gold-internal discriminator is revealed: the patched method `full_clean`, the file `formsets.py`, the `error_class=` keyword argument, the `e.error_list`/`_non_form_errors` internals, and the `'errorlist {}'.format(...)` mechanism are all ABSENT from the spec view (confirmed by grep). The `cssClassFor` base-class string `"errorlist"` is the public rendered form of an ErrorList (named in the PS), not a gold-only leak. No leaking token to quote — the spec view stays at problem_statement altitude. This instance does not require the relaxed-leakage policy; it is a clean NO-LEAKAGE.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 12 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 12 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness (spec-too-strong / drift) audit for django__django-14608 velvet bundle.

SPEC REGION byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True. Spec (structure ErrorBox {data, cssClass}; def cssClassFor; method buildNonFormErrors with `ensures out.data = errors` and `ensures out.cssClass = cssClassFor (some "nonform".toList)`) is identical across post/pre files; only the impl region differs.

**LEAN:** Solution.lean elaborates exit 0. Solution_prepatch.lean (supplies cssClassFor none) FAILS with `cssClassFor none = cssClassFor (some "nonform".toList)` unsolved — G-DIFF/the discriminating clause is real, not vacuous.

**MODELED FUNCTION vs REAL CALLEE:** the modeled behavior is the `self._non_form_errors = self.error_class(...)` construction in BaseFormSet.full_clean (django/forms/formsets.py:336 empty-case, :383 validation-error case) at base_commit 7f33c1e2. Gold patch adds `error_class='nonform'` at BOTH sites — identical delta. The unchanged callee ErrorList.`__init__` (django/forms/utils.py:83-90) stores messages verbatim via super().`__init__`(initlist) and sets self.error_class = 'errorlist {}'.format(error_class) => 'errorlist nonform'. Ran axiom_check.py against the REAL ErrorList in the base worktree: G-AX OK on 84 boundary + 20000 fuzz label/message combos — cssClassFor deep model == ErrorList.`__init__` class string, and .data round-trips messages.

Too-strong check: both ensures are satisfied by the real callee on EVERY input — messages preserved (super().`__init__` stores initlist unmodified) and class string deterministically 'errorlist nonform'. No input makes the real repo produce a different .data or .error_class. Drift check: 'nonform' literal matches the gold patch exactly; type refinements (str<->List Char, str-list<->List(List Char), None/label<->Option) are sound and total. No diverging input exists.

**Verdict:** FAITHFUL. No defect found; spec neither over-constrains nor drifts from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(...) == True under the velvet LanguageTables. Assessed the consumer-facing spec_view (not the auditor docs) against the public problem_statement (NOT hints_text).

Public problem_statement discloses: title 'Add `nonform` CSS class for non form errors in FormSets'; the literal token `nonform` verbatim; that FormSets should get this CSS class for non-form errors mirroring the `nonfield` class Forms already add for non-field errors in ErrorList instances (the 'rendering form error messages' precedent).

Spec view formalizes exactly and only that public content:
  - `cssClassFor`: none -> 'errorlist', some m -> 'errorlist ' ++ m  (the errorlist {label} rendering — derivable from the cited nonfield precedent)
  - postcondition `out.cssClass = cssClassFor (some "nonform".toList)` -> renders 'errorlist nonform'
  - postcondition `out.data = errors` (messages preserved — trivially implied, the feature only adds a class).

The `nonform` literal and the space-joined `errorlist nonform` rendering are both directly derivable from the problem_statement, so surfacing them in the spec is not leakage beyond the public statement.

Crucially, the spec view does NOT reveal edit specifics that are absent from the problem_statement: the `error_class=` keyword-argument mechanism, the two construction sites in BaseFormSet.full_clean, and the file/line locations (formsets.py:336/383) appear ONLY in mapping.md/refinement.md (auditor artifacts), not in the shipped Solution.lean spec regions. The impl/proof are elided in the spec_view. Conclusion: the spec is a faithful formalization that leaks nothing about the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
