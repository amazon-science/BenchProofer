# P2 adversarial audit — sympy__sympy-12096

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on eval_implemented(leaf, layers), the abstraction of the _imp_ branch of Function._eval_evalf recursively driven by Expr.evalf after the gold patch (Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)). Spec domain: Requires(leaf>=0) and Requires(eval_seq(leaf,layers)<1e14); postcondition Ensures(Result() is not None) and Ensures(Result()==eval_seq(leaf,layers)) with eval_seq the inside-out fold of imp(x)=x*x once per layer.

Setup: cloned at base_commit d7c3045115693e887bcd03599b7ca4650ac5f2cb, applied the gold patch verbatim (verified the changed return line), and exercised the REAL patched callee with implemented_function('f', lambda x: x**2) using the py38 env (mpmath 1.3.0) since the old sympy needs collections.Mapping.

Evidence the modeled function agrees with the real callee everywhere in the declared domain:
- Exhaustive in-domain sweep leaf 0..399 x depth 0..39 filtered to eval_seq<1e14: 0 mismatches (every real evalf was a present Number equal to Float(eval_seq)).
- Boundary sweep at the 1e14 edge: leaf=99999999999999 @depth0, leaf=9999999 @depth1 (99999980000001), leaf=3162 @depth2 (99964883083536), leaf=56 @depth3 (96717311574016), plus deep chains leaf in {0,1} @depth49 -- all present, all == Float(eval_seq). 0 mismatches.
- Out-of-domain inputs (e.g. leaf=16 depth4 -> 1.8e19, leaf=11 depth4 cited in mapping) are correctly excluded by the precondition eval_seq<1e14, so the exact-int equality is never asserted where the real Float rounds. Spec is NOT too strong: it does not over-claim outside the representable window.
- Intermediate-rounding gap ruled out: for the squaring map, intermediate reductions eval_seq(leaf,k) for k<n are monotonically <= the final value, so a final value <1e14 implies all intermediate values are also exactly representable -> no hidden precision loss during the recursive i.evalf() reduction.

Non-vacuity: model.py verifies under the pinned Nagini (exit 0, 11.33s), so the postconditions are provable, not spec-unsatisfiable. axiom_check.py (G-AX) passes against the patched repo (32 boundary + 343 fuzz + F2P discriminator f(f(2)).evalf()==Float(16)); its within_precision filter mirrors the Requires domain exactly.

Conclusion: no in-domain input was found where the modeled function disagrees with the real callee. The spec is faithful (neither too strong nor drifting from real repo behavior).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view rendered via markers.spec_view(model.py, nagini.language); sha256 = f76e51f6...48c4, byte-identical to meta.json region_hashes.spec_view. same-spec toolkit confirms self-consistency (exit 0). The gold edit is the one-line change in Function._eval_evalf: `Float(self._imp_(*self.args), prec)` -> `Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)` (recurse-on-args before applying the implementation). LEAKAGE TEST: does the spec view reveal this beyond the PUBLIC problem_statement? (a) The problem_statement already names Function._eval_evalf, states the fix concept verbatim ('evalf does not call _imp_ recursively ... It isn't calling evalf recursively on the return of _imp_'), and gives the worked example `f = implemented_function('f', lambda x: x ** 2)` with the failing composition `f(g(2)).evalf()`. (b) The spec view describes ONLY behaviour ('stated as desired behaviour, not as an edit'): inside-out reduction, args reduced to a number before `imp` applies, deep composition must yield a PRESENT number. Its `imp(x)=x*x` is exactly the public `lambda x: x**2` example -- not new info. (c) Grepped the spec view for repo-localizing tokens: _eval_evalf, self.args, evalf(prec), function.py, Float(, _imp_, lambdify, expr.py, :510, base_commit -- ALL ABSENT. All concrete localization (file:line, the verbatim gold hunk, Expr.evalf driver) lives only in refinement.md / mapping.md / meta.json (audit artifacts), NOT in the solver-facing spec view. The spec view discloses nothing about the gold edit beyond what the public problem_statement already states. Concurs with the recorded G-LEAK pass ('spec view clean').

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
