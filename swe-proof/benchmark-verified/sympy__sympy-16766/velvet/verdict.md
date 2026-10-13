# P2 adversarial audit — sympy__sympy-16766

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "Audit Verdict — sympy__sympy-16766", before this corpus rendered one
> section per audit role. It is kept verbatim because it is the only account of
> that round that ships in this bundle, and it is NOT this cell's record. The
> record is the audit gate entries in the `meta.json` beside this file, which
> are the source of truth for the cell's status; each role section below
> publishes its gate's `status (recorded)` and `machine verdict` straight from
> that entry. Each round authored and re-ran its own attacks, so a count in the
> text above is that round's own count and not this record's: where the two
> accounts differ, the record governs.

**Overall: ACCEPTED** (P2 lead-auditor synthesis)

Instance: `PythonCodePrinter` gains `_print_Indexed`, rendering an element access
`base[i0, i1, ...]` (comma-space-joined subscripts) instead of the pre-patch
`# Not supported in Python:` annotation fall-through.

## Per-gate verdicts

| Gate | Verdict | Basis |
|---|---|---|
| **G-EQ** | **pass** | G-EQ SOUND + spec-strength TIGHT + no kind-3 refinement. Spec is a complete functional postcondition `ensures out = accessRender base indices` over concrete recursive functions of the inputs; 6 spec-too-weak attacks all rejected (verify exit 1) on `ensures_1`, positive control atk_7 (structurally different correct impl) verifies (exit 0). No opaque oracle to echo. |
| **G-PANEL** | **pass** | faithfulness FAITHFUL AND G-AX VACUOUS (∈ {SOUND,VACUOUS}) AND leakage NO-LEAKAGE (∈ {NO-LEAKAGE,RELAXED}). |
| G-EQ:SOUND | yes | Postcondition pins the full output string as a pure function of inputs; no axiom, no opaque symbol. |
| G-EQ:spec-strength | TIGHT | G-MUT killed 20/20; 6 hand-built weak-spec attacks all fail; positive control verifies. |
| G-EQ:refinement | R/I only, no kind-3 | A1/A2 R over unchanged-helper outputs; A3/A4/A5 concrete I. |
| faithfulness | FAITHFUL | F2P `doprint(p[0,1]) == 'p[0, 1]'` matches spec shadow in-container; pre/post discriminator (annotation prefix) captured; prepatch fails, Solution verifies. |
| G-AX | VACUOUS | Zero axioms (`axioms` region is comment only), `axioms: []`, no `axiom_check.py`. |
| leakage | NO-LEAKAGE | Every discriminating spec-view token is verbatim in the public `problem_statement` (the issue supplies the gold method body); spec view names neither `pycode.py` nor `_print_Indexed`. |
| G-VERIFY | pass | Solution.lean exit 0 (re-verified, 2.2s). |
| G-DIFF | pass | Solution_prepatch.lean fails (re-verified exit 1, `ensures_1`). |
| G-MUT | pass | killed 20/20. |
| G-CONF | pass | rc 0, 0 disagreements / 100007 inputs (seed 16766), incl. F2P boundary `p[0,1]`. |
| G-RESOLVE / G-GOLD / G-INTEGRITY / G-HYGIENE / G-LEAK | pass | per meta.json. |

## Lead-auditor independent confirmation

- `Solution.lean` re-verified: **exit 0**.
- `Solution_prepatch.lean` re-verified: **exit 1**, unsolved goal on
  `case «ensures_1: out = accessRender base indices»` showing the literal
  `'#'::' '::'N'::'o'::'t'::' '::'s'::'u'::'p'::'p'::'o'::'r'::'t'::'e'::'d'::':'::'\n'`
  bytes prefixing the output — exactly the right discriminator (supported
  rendering vs. pre-patch `# Not supported:` fall-through).
- axioms+pure regions of Solution.lean and Solution_prepatch.lean are
  **byte-identical** (diff empty): the prepatch is an impl-region-only / postcondition-
  behavior edit sharing the spec, so the rejection is genuine spec strength, not a
  moved goalpost.
- meta.json: `axioms: []`, `deep_model_references: []`, G-AX skip (no axiom_check.py).

## Concrete defects

**None.** No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom,
no leak found. No fix required.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (quoted verbatim)

> G-CONF passes (rc 0): the R/I shadow `base + "[" + ", ".join(index_texts) + "]"` agrees with the real patched `_print_Indexed` on 100007 inputs, including the F2P boundary case `p[0,1] → 'p[0, 1]'`. The bijection (str ↔ List Char, str.join ↔ joinComma, "{}[{}]" ↔ bracket concat) is mechanically validated against the real unchanged-helper outputs.
>
> Let me do a final sanity check on the ungrounded-oracle probe: confirm there's truly no axiom that an impl could echo, and that the spec_view (consumer-facing) doesn't smuggle the answer. The postcondition is `out = accessRender base indices`, where `accessRender` and `joinComma` are concrete recursive functions over the inputs. There is no opaque symbol — `accessRender` cannot be "echoed" as a cheat because computing it IS the work. atk_7 demonstrates exactly this: the only way to satisfy the spec is to produce the bracketed comma-joined string from the inputs.
>
> Let me confirm the refinement legs are all R/I (no kind-3) and that no verifying model could refine to a non-resolving patch. The refinement maps the modeled `renderAccess` exactly onto the gold `_print_Indexed`; the F2P test observes `doprint(p[0,1]) == 'p[0, 1]'`, which equals `accessRender` output with no annotation. The prepatch produces the annotation and is rejected. There is no room for a verifying model that wouldn't resolve: the spec pins the full output string, and G-CONF confirms that string equals the gold patch's output on the F2P case and 100k more.
>
> **VERDICT: sympy__sympy-16766**
>
> **G-EQ = SOUND. spec-strength = TIGHT.**
>
> The spec is a complete functional postcondition: `ensures out = accessRender base indices`, where `accessRender base indices := base ++ "[".toList ++ joinComma indices ++ "]".toList` and `joinComma` is a concrete recursive comma-joiner. The output is pinned exactly as a pure function of the inputs — there is no axiom, no opaque oracle, nothing to echo.
>
> **Spec-too-weak attacks** (all share spec via `same_spec=True`, verified against bundle `Solution.lean`; impl-region-only edits, axioms/pure/spec byte-identical):
>
> | atk | wrong impl | same_spec | verify exit | rejecting clause |
> |---|---|---|---|---|
> | 1 | prepatch bug: prepend `"# Not supported:\n"` annotation | True | 1 (FAIL) | `ensures_1: out = accessRender base indices` |
> | 2 | join with `","` instead of `", "` (missing space) | True | 1 (FAIL) | `ensures_1: out = accessRender base indices` |
> | 3 | wrap in `(` `)` instead of `[` `]` | True | 1 (FAIL) | `ensures_1: out = accessRender base indices` |
> | 4 | drop `base`, return `[joined]` only | True | 1 (FAIL) | `ensures_1: out = accessRender base indices` |
> | 5 | return `[]` (empty) | True | 1 (FAIL) | `ensures_1: out = accessRender base indices` |
> | 6 | omit brackets entirely: `base ++ joined` | True | 1 (FAIL) | `ensures_1: out = accessRender base indices` |
>
> **Positive control** atk_7: structurally different CORRECT impl (no loop — `return base ++ "[".toList ++ joinComma indices ++ "]".toList` directly): same_spec=True, verify **exit 0 (VERIFIES)**. Spec is non-vacuous.
>
> **Refinement audit (PASS):** All legs R or I, no kind-3. A1 (`base ↔ str(expr.args[0])`) and A2 (`indices ↔ [self._print(ind) ...]`) are R over unchanged-helper outputs; A3 (`joinComma ↔ ", ".join`), A4 (`"{}[{}]" ↔ bracket concat`), A5 (no annotation prefix) are concrete I. Zero axioms (G-AX skip is legitimate). I independently ran G-CONF in-container with patch.diff applied: **rc 0, 0 disagreements over 100007 inputs** (incl. the F2P boundary `p[0,1] → 'p[0, 1]'`), so the R/I bijection is mechanically validated against the real patched `_print_Indexed`. Prepatch (`Solution_prepatch.lean`, byte-identical to atk_1) fails on exactly `ensures_1: out = accessRender base indices` — the right discriminating clause (the supported rendering vs. the pre-patch `# Not supported` fall-through).
>
> **Ungrounded-oracle probe (PASS):** No opaque/axiomatized symbol exists in the spec. `accessRender`/`joinComma` are concrete functions of the inputs; satisfying the postcondition requires producing the bracketed comma-joined string from `base`/`indices` — atk_7 confirms the only way to verify is to do the real work. No answer-key echo is possible.

## Sub-review 2 — FAITHFULNESS + G-AX (quoted verbatim)

> Confirmed no axioms, no axiom_check.py. G-AX is VACUOUS.
>
> VERDICT: faithfulness = FAITHFUL, G-AX = VACUOUS.
>
> FAITHFULNESS = FAITHFUL.
> - F2P test is `test_PythonCodePrinter`, whose added assertion is `prntr.doprint(p[0, 1]) == 'p[0, 1]'`. The spec `method renderAccess` pins `ensures out = accessRender base indices`, where `accessRender base indices = base ++ "[" ++ joinComma indices ++ "]"` and `joinComma` is exactly `", ".join`. This is an exact, deterministic, structural function of the inputs — no opaque oracle (SPEC_GUIDE directive 8 satisfied), and tight enough that G-MUT killed 20/20.
> - Docker evidence (gold patch applied at base_commit, in-container): `doprint(p[0,1])` returns `'p[0, 1]'` and the spec's `accessRender` shadow returns the identical `'p[0, 1]'` (doprint == shadow == True); `doprint(p[0])` returns `'p[0]'` (the issue example). Post-gold output == spec-predicted output on the F2P input shape.
> - conformance_check.py run in-container with apply_gold=True: rc 0, "R/I shadow of renderAccess agrees with patch.diff behaviour on 100007 inputs (seed=16766), 0 disagreements" — over the F2P shape plus multi-index, symbolic, and compound-index cases. The shadow consumes the real `str(base)` / `printer._print(ind)` outputs (unchanged helpers, correctly treated as R/input-carrier), and the oracle is the real patched `_print_Indexed`. No divergence found.
> - The modeled domain (`indices : List (List Char)`, any arity) covers the F2P input `p[0,1]` (two indices). The crucial pre/post discriminator — pre-gold falls through to the generic handler that prepends a `# Not supported:` annotation, post-gold emits the bare access string with no annotation — is captured: Solution_prepatch.lean reproduces the annotation prefix and FAILS verification (G-DIFF confirmed: unsolved goal showing the `'# Not supported:\n'` bytes prefixing the output), while same_spec(Solution, prepatch) = True. Solution.lean verifies (exit 0). patch.diff is the gold patch verbatim and G-RESOLVE passes.
>
> G-AX = VACUOUS. No axiom_check.py in the bundle; Solution.lean declares zero axioms (the `axioms` region is an explanatory comment only); meta.json `axioms: []`, `deep_model_references: []`. The only callees (`str(base)`, `self._print(ind)`) are unchanged and modeled as input carrier (R), and the changed behavior is modeled deeply (joinComma/accessRender). No trust points beyond the type bijection, which G-CONF falsifiably exercised.

## Sub-review 3 — LEAKAGE (quoted verbatim)

> My leakage assessment is clear. The problem_statement contains: (1) the exact gold method code `def _print_Indexed(self, expr): base, *index = expr.args; return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))`, (2) the bug symptom showing `# Not supported in Python:` / `# Indexed`, (3) the title "PythonCodePrinter doesn't support Indexed".
>
> Every discriminating token in the spec view is present in the public problem_statement. The spec view does not name the patched file (`pycode.py`), does not name the symbol `_print_Indexed`, and does not echo a diff line beyond what the issue itself already prints. This is a case where the public issue literally contains the entire gold patch.
>
> This is NOT a relaxed-leakage situation (the discriminator is fully public, not hints-only). It is a clean NO-LEAKAGE pass. The spec view even arguably reveals *less* than the public issue (it abstracts to generic rendering vocabulary and never names the SymPy printer symbol).
>
> VERDICT: NO-LEAKAGE

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

Faithfulness (spec-too-strong / drift) audit for sympy__sympy-16766 velvet bundle.

**SPEC REGION:** same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True — the spec view (imports/set_options/axioms(empty)/pure(joinComma+accessRender+lemmas)/pre(empty)/post(empty)/method signature+ensures) is byte-identical between gold and prepatch variants. G-HYGIENE region hashes present. spec_view is well-formed.

**MODELED FUNCTION:** renderAccess (base : List Char) (indices : List (List Char)) return out ensures out = accessRender base indices, where accessRender base indices = base ++ "[" ++ joinComma indices ++ "]" and joinComma interleaves ", " between fragments (no leading/trailing). Models PythonCodePrinter.`_print_Indexed` (added by patch at pycode.py:360): return "{}[{}]".format(str(base), ", ".join([self.`_print`(ind) for ind in index])).

**REAL-REPO DIFFERENTIAL TEST:** checked out sympy at base_commit b8fe457a02cc24b3470ff678d0099c350b7fef43, applied the gold hunk, and ran the model (accessRender over the REAL str(base)/self.`_print`(ind) components) against the REAL patched `_print_Indexed` oracle over 1632 diverse inputs: base names {p,q,A,data,x1,M_2,tbl, unicode 'αβ', 'p q', 'p[0]', empty '', '1x'} × 1..4 subscripts drawn from {integers incl negative, symbolic i,j,k,m,n, compounds i+1,`2*j`,i+j,k-3,`m*n`, Rational, pi, sin, Float, i/j, `i**2`}. Result: 0 disagreements. This subsumes the pinned G-CONF run (100007 inputs, seed=16766, 0 disagreements) and adds edge cases (empty/space/unicode base, rational/float/nested indices).

The spec is a pure total structural function of the inputs; there is no exception path in the patch and none is claimed. str(base) and self.`_print`(ind) are unchanged-helper outputs treated as input carrier (R), not axiomatized oracles — no answer-key borrowing. The bijection List Char↔str char-for-char, str.format('{}[{}]')↔bracket concat, str.join↔joinComma is correct (verified via differential test). No axioms consumed (G-AX skip legitimate). Spec is neither too strong nor drifting from real callee behavior.

**SANITY:** Solution.lean verifies via lean_verify.sh (exit 0), so the strong ensures is non-vacuous; Solution_prepatch.lean (which prepends '# Not supported:\n') fails verification as expected (G-DIFF pass), confirming the spec discriminates the behavioral change.

No diverging input found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage/gold-reconstruction check for sympy__sympy-16766 (velvet). Spec region confirmed byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True; spec_view generated cleanly (imports/axioms/pure/pre/post + method signature + ensures, with impl and prove_correct elided).

**Baseline:** the PUBLIC problem_statement already discloses the gold edit VERBATIM. It states 'We should add following method to PythonCodePrinter:' and gives the full body:
  def `_print_Indexed`(self, expr):
      base, *index = expr.args
      return "{}[{}]".format(str(base), ", ".join([self.`_print`(ind) for ind in index]))
The gold patch is precisely this method (added after `_print_Not`). So the public statement is already maximally revealing — it hands over the exact code to add.

**Spec view content:** models accessRender base indices = base ++ "[" ++ joinComma indices ++ "]" with joinComma = comma-join, and the narrative 'emit as supported code, no unsupported annotation'. Every disclosed element (the "{}[{}]" template, the ", " join separator, the bracket wrapping, str(base)/self.`_print`(ind) as inputs) is already fully present in problem_statement. The spec adds no information about the gold edit beyond what problem_statement supplies; it merely re-expresses the same publicly-given formula in Lean value terms.

Since the public problem_statement already contains the complete gold method, the spec view cannot leak the gold BEYOND problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
