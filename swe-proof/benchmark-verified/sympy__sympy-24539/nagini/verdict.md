# P2 adversarial audit — sympy__sympy-24539

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence: the frozen spec is faithful to the real gold callee (PolyElement.as_expr, post-patch) on all tested inputs; it is not too strong.

Setup: is at base_commit 193e3825 (pre-patch, buggy as_expr — else-arm always overwrites symbols). Reconstructed gold by applying the verbatim gold hunk Confirmed gold: f.as_expr(u,v,w)==renders over supplied u,v,w; f.as_expr()==renders over ring defaults x,y,z; f.as_expr(1 sym) and f.as_expr(4 syms) both raise ValueError('Wrong number of symbols...').

Spec/model checks: same-spec exit 0 on the model itself (spec region byte-identical). nagini_verify.sh model.py: 'Verification successful' exit 0 (14.3s).

Clause-by-clause vs gold: (a) Ensures(len(symbols)==0 or len(symbols)==ngens) matches gold's normal-return domain; (b) Implies(len==ngens and len>0, ToSeq(Result)==ToSeq(symbols)) matches gold keeping the supplied sequence (the actual fix); (c) Implies(len==0, ToSeq(Result)==ToSeq(default_symbols)) matches gold using ring.symbols; (d) Exsures(SymbolCountError, len>0 and len!=ngens) matches gold's 'elif len(symbols)!=self.ring.ngens: raise ValueError'. Precondition ngens==len(default_symbols) always holds — PolyRing.__new__ sets ngens=len(symbols) (rings.py:200).

Fuzzing (env swebench-lean, PYTHONPATH gold): 400 randomized rings, ngens 1-4 over ZZ/QQ, supplied symbol counts 0..ngens+2, random polynomials — 0 raise/no-raise disagreements between the spec's abstract selection and real gold as_expr. A further 300 rings (ngens 1-5) confirmed equal-selected-gens ⇒ equal rendered expression element-for-element (supplied-symbol render == default render with default->supplied substitution). No input exhibits the spec disagreeing with the real callee.

Type abstraction (Symbol<->int identity, tuple<->List, ValueError<->SymbolCountError, ngens identity) is behavior-preserving for the tested quantity (the selected gens sequence), which is the sole quantity the unchanged deterministic callee expr_from_dict depends on. No consumed axiom / no deep model, consistent with meta.json (axioms=[], deep_model_references=[], G-AX pass on 53 real observations). Spec is neither too strong nor drifting: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage assessed against the PUBLIC problem_statement only (hints excluded). The problem_statement already fully specifies the desired fix: 'PolyElement.as_expr() ... is supposed to let you set the symbols you want to use, but ... you pass the right number of symbols, and it ignores them, using self.ring.symbols instead', plus the wrong-number-of-symbols error behavior. Thus (a) correct count -> use supplied symbols, (b) wrong non-empty count -> error, (c) empty -> ring defaults are all public.

Spec view (docstring + SymbolCountError class + pre-conditions + post-conditions; impl region fully elided as '...') exposes only these three behavioral cases stated as DESIRED behaviour, not as an edit. The discriminating clause Ensures(Implies(len(symbols)==ngens and len(symbols)>0, ToSeq(Result())==ToSeq(symbols))) is a functional restatement of the problem_statement's exact complaint ('supplied symbols must be used, not ignored'); the empty->default case is not even part of the gold edit (pre-patch already routed empty args to ring.symbols). No spec-view line goes beyond problem_statement.

No edit-structure leakage: the spec view contains no pre/post-patch contrast, no gold-hunk control flow (if not symbols / elif len != ngens), no repo symbol names (as_expr, self.ring.ngens, expr_from_dict), and no message strings. Model-side names (select_render_symbols, SymbolCountError, List[int], PSeq) are Nagini abstractions, not repo edit details. The pre-patch narrative and verbatim gold hunk appear only in refinement.md/mapping.md (auditor docs, not part of the solver's spec view), so they are not leakage vectors. Verified via markers.spec_view with NaginiBackend.language that impl-start..impl-end is elided.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
