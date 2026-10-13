# P2 adversarial audit — django__django-11728

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-11728", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED**

Modeled op: `scanGroupEnd (rest : List Char) → Option Nat` — the inner unescaped-bracket-balancing
scan shared by `replace_named_groups` / `replace_unnamed_groups` in
`django/contrib/admindocs/utils.py`. Spec is a single full functional equality
`ensures out = scanLen none 1 rest`, with `scanLen`/`nextBal` concrete computable Lean defs
(deep model; no opaque oracle, no consumed axiom).

## Per-gate table

| Gate    | Verdict | Basis |
|---------|---------|-------|
| G-EQ    | **pass** | G-EQ SOUND AND spec-strength TIGHT AND no kind-3 refinement. 7 spec-too-weak attack impls (a1–a7) all verify EXIT 1; two structurally-distinct correct positive controls (pcorr, ppos2) verify EXIT 0. Postcondition equates `out` to a concrete computable function of the input — no ungrounded oracle (a6 echo rejected by `ensures_1`). refinement.md has only R / A-reference / I steps (no kind-3). |
| G-PANEL | **pass** | faithfulness FAITHFUL AND G-AX ∈ {SOUND, VACUOUS} (= VACUOUS; empty axiom region) AND leakage ∈ {NO-LEAKAGE, RELAXED} (= NO-LEAKAGE). |
| G-AX    | VACUOUS | Axiom region empty (`axioms: []`); change modeled deeply via `nextBal`/`scanLen`. `axiom_check.py` is an A-reference validation (model == real patched scan), rc 0; no consumed axioms to be unsound. |
| Leakage | NO-LEAKAGE | Spec view describes correct end-to-end behavior recoverable from public `problem_statement` ("trailing groups", "final named group", missing "trailing '/'", exact reproducing example). No repo identifiers / file / diff lines / control-flow detail in spec view. |
| Faithfulness | FAITHFUL | In-container post-gold check: spec model == real `replace_named_groups`/`replace_unnamed_groups` on all 13 F2P `test_simplify_regex` patterns (0 div) + 200k fuzz (seed 424242, 0 div); real `simplify_regex` passes all F2P. |

## Concrete defects + fixes

None. No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no genuine leak was found by any sub-reviewer. No fix required.

## Supporting evidence

- Solution.lean verifies (exit 0, no sorry); Solution_prepatch.lean fails `prove_correct` (exit 1)
  on the trailing-group discriminating clause via `invariant_2` — confirms the spec rejects the bug.
- G-AX (`axiom_check.py`): rc 0 — `nextBal` exhaustive over alphabet×prev×bal; `scanLen` == real
  patched inner scan on 53493 matcher-driven scans.
- G-CONF (`conformance_check.py`, gold applied): rc 0 — 100019 inputs (seed 11728), 0 disagreements.
  (Without `apply_gold=True`: rc 1 / 6 disagreements — expected, oracle = unpatched buggy repo.)
- Offline: Nat-truncated-subtraction `scanLen` matches signed-int Python scan on all strings over
  `{( ) \ a}` up to length 8 (0 mismatches); truncation never diverges (scan breaks at first
  return-to-zero before depth could go negative).

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

VERDICT: G-EQ = SOUND, spec-strength = TIGHT.

Bundle: django__django-11728. Modeled op: `scanGroupEnd (rest : List Char) → Option Nat`, the inner unescaped-bracket-balancing scan shared by `replace_named_groups`/`replace_unnamed_groups`. Spec is a single full functional equality: `ensures out = scanLen none 1 rest`, where `scanLen`/`nextBal` are concrete computable Lean defs (deep model, no opaque oracle, no consumed axiom). Baseline Solution.lean verifies (exit 0).

### SPEC-TOO-WEAK PROBE (machine-checked; all share spec via `same_spec`=True, all verified with `scripts/lean_verify.sh ...`):
- a1 = prepatch bug (balance test at TOP of loop, record `some i`): verify EXIT 1. Rejected by `invariant_2` (the loop invariant tying `res` to `scanLen … = (scanLen prev bal (rest.drop i)).map (·+i)` cannot be re-established).
- a2 = off-by-one `res := some i` instead of `some (i+1)` (excludes balancing bracket): verify EXIT 1. Rejected by `invariant_2`.
- a3 = constant `none`: verify EXIT 1. Rejected at the invariant (`simp_all made no progress`); behaviorally false vs `scanLen` whenever it returns `some`.
- a4 = drop escape handling (count escaped brackets too): verify EXIT 1. Rejected by `invariant_2`.
- a5 = wrong initial depth `bal := 0`: verify EXIT 1. Rejected by the explicit goal `scanLen none 1 rest = scanLen none 0 rest` (and behaviorally returns `some 1` on `\w+)` vs correct `some 4`).
- a6 = answer-key echo `some rest.length`: verify EXIT 1. Rejected directly by `ensures_1: out = scanLen none 1 rest` with goal `(if rest=[] then none else some rest.length) = scanLen none 1 rest` — confirms the postcondition is grounded in the input, not an echo-able oracle.
- a7 = drop `prev` threading (broken escape state): verify EXIT 1. Rejected by `invariant_2` (`some (i+1) = …scanLen none bal…` mismatch).

POSITIVE CONTROLS (prove non-vacuity): gold-faithful impl (pcorr) verifies EXIT 0; structurally-different correct variant with inverted branch (ppos2, tests `bal' ≠ 0` first) verifies EXIT 0. So the spec is satisfiable and tight: exactly the correct scan passes.

REFINEMENT AUDIT: refinement.md has only R / A-reference / I steps — no kind-3. `Solution_prepatch.lean` fails for the RIGHT reason (verify EXIT 1, `invariant_2` on the trailing-group discriminating clause). A-reference soundness confirmed in-container: G-AX passes (rc 0; nextBal exhaustive over alphabet×prev×bal; scanLen == real patched inner scan on 53493 matcher-driven scans). G-CONF passes in-container WITH gold applied (rc 0; 100019 inputs, 0 disagreements). I also exhaustively verified offline that the Lean `Nat`-truncated-subtraction `scanLen` matches the real signed-int Python scan on all strings over `{( ) \ a}` up to length 8 (0 mismatches) — the truncation never diverges because the scan breaks at the first return-to-zero before depth could go negative.

UNGROUNDED-ORACLE PROBE: none possible. The postcondition equates `out` to a concrete computable function of the input (`scanLen none 1 rest`), not to any axiom/opaque symbol; a6's echo attempt is rejected by the postcondition itself.

**GATE READING:** a fresh `run_in_container(... conformance_check.py)` without `apply_gold=True` reports rc 1 / 6 disagreements — this is expected (oracle = unpatched buggy repo, shadow = correct); the gate is correct only with `apply_gold=True`, under which it passes. My own attack files are named per instance rather than generically, so no result below can be an output of a different audit read back by mistake. No issues found in the bundle.

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

The spec correctly returns `some rest.length` (4) for a trailing balancing bracket — exactly the bug fix — and `none` when never balanced, and correctly skips escaped `)`. This is the discriminating behavior the F2P test exercises.

Summary of audit:
- **Solution.lean verifies** (exit 0, no sorry); the proof's `ensures out = scanLen none 1 rest` is a real, non-trivial spec.
- **Prepatch fails** (G-DIFF): the buggy top-of-loop/`some i` skeleton cannot meet the frozen spec — confirms the spec discriminates the fix.
- **G-AX VACUOUS**: axiom region is empty (`-- axioms-start`/`-- axioms-end` carries only a comment, no `axiom` declarations). The change is modeled deeply via `nextBal`/`scanLen`. The bundle's `axiom_check.py` is an A-reference validation (model == real patched scan), not an axiom-soundness check. No consumed axioms exist to be unsound.
- **Faithfulness FAITHFUL**: My independent in-container check (real post-gold functions, exact F2P corpus, plus 200k fuzz at a fresh seed 424242 with a richer alphabet) found 0 divergences between the spec model and the genuine post-gold `replace_named_groups`/`replace_unnamed_groups`, and the real post-gold `simplify_regex` passes every F2P expectation. The modeled domain (`List Char` ↔ `str` per code-point) covers all F2P inputs. Nat-truncated subtraction in `nextBal` is harmless (scan halts at depth 0). Escape semantics (`prev ≠ some '\\'`) match the repo.

verdict: faithfulness = FAITHFUL, G-AX = VACUOUS.

Docker evidence (gold patch applied in-container): the spec model embedded in the unchanged host functions == real post-gold `replace_named_groups`/`replace_unnamed_groups` on all 13 F2P `test_simplify_regex` patterns (0 divergences) and on 200,000 independent fuzz inputs (seed 424242, 0 divergences); real post-gold `simplify_regex` passes all F2P expectations (0 fails). The bundle's own conformance_check.py (100,019 inputs, seed 11728) and axiom_check.py (53,493 matcher-driven scans + exhaustive next_bal) both returned rc 0. Solution.lean verifies (exit 0); Solution_prepatch.lean fails prove_correct (exit 1), confirming the spec rejects the buggy behavior.

## Sub-review 3 — LEAKAGE (verbatim)

None of the repo-specific identifiers, the patched file/symbol, diff lines, or bug/fix narration tokens appear in the spec view.

The spec view describes a generic "find the balancing bracket in a forward scan, including the bracket, return none if never balanced." The discriminating behavior — a group whose balancing `)` is the FINAL character of the pattern must be recorded with full consumed length — is exactly the publicly-reported symptom. The public `problem_statement` states it directly: "simplify_regexp() doesn't replace **trailing** groups", "fails to replace the **final** named group if the urlpattern is missing a **trailing '/'**", the exact reproducing example `r'...relationships/(?P<related_field>\w+)'`, and "A workaround is to tack on a '/' at the end and then it works."

Reconstruction attempt from the spec view alone: I cannot reconstruct the gold patch — the spec view contains none of the repo identifiers (`replace_named_groups`, `replace_unnamed_groups`, `unmatched_open_brackets`, `prev_char`), the patched file (`django/contrib/admindocs/utils.py`), any diff line, the top-of-loop-vs-bottom-of-loop control-flow detail, or the `end+idx` → `end+idx+1` slice-index arithmetic. The bracket-nesting/escape machinery (`prev ≠ some '\\'`) is pre-existing, unchanged surrounding code preserved verbatim by the gold, not part of the edit; describing it to state the contract is not gold-edit leakage. The spec is both faithful (prepatch fails the trailing clause per G-DIFF) and non-leaking against problem_statement-only, so this is not a RELAXED case.

No leaking token found. Verdict: NO-LEAKAGE.

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

Faithfulness-break attack (G-PANEL sub-2). Spec region byte-identical between Solution.lean and Solution_prepatch.lean per swebench_unified.markers.same_spec with velvet LanguageTables (True). Solution.lean verifies via scripts/lean_verify.sh (exit 0); Solution_prepatch.lean fails prove_correct (exit 1) at the trailing-group clause (goal: some(i+1)=map(+i+1)(scanLen ... 0 ...)), confirming the spec discriminates the fix.

**Modeled op:** scanGroupEnd(rest:List Char)->Option Nat, the inner unescaped-bracket-balancing scan shared by replace_named_groups/replace_unnamed_groups in django/contrib/admindocs/utils.py. Spec ensures out = scanLen none 1 rest, a concrete computable deep model (nextBal/scanLen); axiom region empty.

Independent faithfulness check against the REAL gold-patched Python inner scan (returns idx+1 on the unmatched_open_brackets==0 break, None otherwise): transliterated the Lean model (Nat truncated subtraction in nextBal, front-recursive scanLen, init bal=1/prev=none) and diffed vs real_scan. Exhaustive over alphabet {( ) \ a} for all lengths 0-9: 0 divergences. 300k random fuzz over rich alphabet ()\abc/<>?P=|_+* len<=30 (seed 999): 0 divergences.

No diverging input exists. Truncated subtraction is inert (bal starts at 1, scan returns the moment depth hits 0, so it never underflows first). Escape semantics prev != some '\\' reproduce the repo's immediate single-char lookback exactly, including the repo's own escaped-backslash quirk, so the model tracks the real code rather than an idealization. Result offset some(i+1) = one-past the balancing bracket matches patched slice end+idx+1. Spec is not too strong and does not drift from real repo behavior. FAITHFUL; no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**Scope:** spec view = elided Solution.lean via markers.spec_view (VelvetBackend). Confirmed spec signature byte-identical patched vs prepatch (same_spec=True, len 5022) — the spec is a stable contract, not something that mutates with the fix. mapping.md/refinement.md reproduce the gold hunk verbatim but are auditor-facing (G-EQ/G-AX) and NOT part of the consumer spec view, so out of scope here.

Public problem_statement already discloses the target behavior: the final named group (related_field) must be replaced even without a trailing '/', expected '<related_field>'. I.e. a group whose balancing bracket is the last char must be handled correctly.

**The spec view exposes:** (1) nextBal — the unescaped-bracket depth update, which is behavior present in the ORIGINAL buggy code, not the edit; (2) scanLen and the ensures contract 'out = scanLen none 1 rest' — specifies correct semantics ('up to and INCLUDING the balancing bracket', none if never balanced) at an abstract List Char altitude. It contains NONE of the gold edit's Python specifics: no loop, no unmatched_open_brackets, no idx/end+idx vs end+idx+1 arithmetic, no top-vs-bottom placement of the balance test, no 'move the check' comment, no mention of replace_named_groups/replace_unnamed_groups. Those specifics appear only in hints_text (excluded) and the auditor docs.

Specifying correct behavior is intrinsic to any spec and is not leakage; leakage would require disclosing the specific gold delta/impl approach beyond the public problem. The scanLen fold-then-test recursion mirrors correct control flow only as an abstract math function (the contract), not the Python diff. Nothing in the spec view reconstructs the gold edit beyond what problem_statement already implies.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
