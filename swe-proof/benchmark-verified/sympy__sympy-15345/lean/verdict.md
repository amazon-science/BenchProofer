# P2 adversarial audit — sympy__sympy-15345

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_16.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName ++ "(" ++ renderArgs render args ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName ++ "[" ++ String.intercalate "," (args.map render) ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,10 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  if args.length ≤ 3 then
+    return funcName ++ "[" ++ renderArgs render args ++ "]"
+  else
+    return funcName ++ "[" ++ renderArgs render args ++ ",]"
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,6 +53,8 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
+  if args.length = 1 then
+    return funcName ++ renderArgs render args
   return funcName ++ "[" ++ renderArgs render args ++ "]"
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,9 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  match args with
+  | [] => return funcName
+  | _  => return funcName ++ "[" ++ renderArgs render args ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,10 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  let mut acc := ""
+  for a in args do
+    acc := acc ++ render a ++ ", "
+  return funcName ++ "[" ++ acc ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName ++ "[" ++ renderArgs render args.reverse ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName ++ "{" ++ renderArgs render args ++ "}"
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName.toUpper ++ "[" ++ renderArgs render args ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName ++ "]" ++ renderArgs render args ++ "["
 -- impl-end
 
 -- proof-start
```

Attack 11 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,10 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  if args.length < 4 then
+    return funcName ++ "[" ++ renderArgs render args ++ "]"
+  else
+    return funcName ++ "[" ++ renderArgs render args.reverse ++ "]"
 -- impl-end
 
 -- proof-start
@@ -64,5 +67,6 @@
         (implementation_printApplication render funcName args) := by
   intro Expr render funcName args
   unfold problem_spec_printApplication implementation_printApplication
-  rfl
+  simp_all [Id.run]
+  split <;> simp_all [List.map_reverse, String.intercalate]
 -- proof-end
```

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,7 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  return funcName ++ "[" ++ String.intercalate " ," (args.map render) ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,10 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  if funcName = "Min" then
+    return funcName ++ "(" ++ renderArgs render args ++ ")"
+  else
+    return funcName ++ "[" ++ renderArgs render args ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -53,7 +53,9 @@
 def implementation_printApplication
     {Expr : Type}
     (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+  let frags := args.map render
+  let joined := frags.foldl (fun acc s => if acc.isEmpty then s else acc ++ ", " ++ s) ""
+  return funcName ++ "[" ++ joined ++ "]"
 -- impl-end
 
 -- proof-start
```

Attack 15 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -50,10 +50,10 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_printApplication
+noncomputable def implementation_printApplication
     {Expr : Type}
-    (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+    (render : Expr → String) (funcName : String) (args : List Expr) : String :=
+  Classical.epsilon (fun s => problem_spec_printApplication render funcName args s)
 -- impl-end
 
 -- proof-start
@@ -63,6 +63,6 @@
       problem_spec_printApplication render funcName args
         (implementation_printApplication render funcName args) := by
   intro Expr render funcName args
-  unfold problem_spec_printApplication implementation_printApplication
-  rfl
+  exact Classical.epsilon_spec (p := fun s =>
+    problem_spec_printApplication render funcName args s) ⟨_, rfl⟩
 -- proof-end
```

Attack 16 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -50,10 +50,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_printApplication
+open Classical in
+noncomputable def implementation_printApplication
     {Expr : Type}
-    (render : Expr → String) (funcName : String) (args : List Expr) : String := Id.run do
-  return funcName ++ "[" ++ renderArgs render args ++ "]"
+    (render : Expr → String) (funcName : String) (args : List Expr) : String :=
+  if h : ∃ s, problem_spec_printApplication render funcName args s then
+    Classical.choose h
+  else
+    ""
 -- impl-end
 
 -- proof-start
@@ -63,6 +67,8 @@
       problem_spec_printApplication render funcName args
         (implementation_printApplication render funcName args) := by
   intro Expr render funcName args
-  unfold problem_spec_printApplication implementation_printApplication
-  rfl
+  have h : ∃ s, problem_spec_printApplication render funcName args s := ⟨_, rfl⟩
+  unfold implementation_printApplication
+  rw [dif_pos h]
+  exact Classical.choose_spec h
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree at base_commit 9ef28fba5b in ./wt). All 16 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl (and, where noted, the non-frozen proof) region was edited.

**COMMANDS:** per file `bash scripts/lean_verify.sh $S/<f>.lean` from the repo root, run concurrently 4 at a time. Axioms probed by appending `#print axioms correct_printApplication` to a copy (`atk_*_ax`.lean).

**SPEC SHAPE:** problem_spec is a fully-pinned exact string equality result = funcName ++ "[" ++ renderArgs render args ++ "]", renderArgs = String.intercalate ", " (args.map render); the stock proof is `unfold; rfl`. So any impl that observably deviates on ANY input cannot close.

POSITIVE CONTROL atk_pos.lean: exit 0; `#print axioms` => 'does not depend on any axioms' (clean, zero axioms).

REJECTED (exit 1, each a GENUINE correctness failure -- log shows `Tactic rfl failed: The left-hand side ... is not definitionally equal to the right-hand side`, not an encoding/elaboration artifact):
- atk_1 prepatch bug: parenthesized generic call form `funcName ++ "(" ++ ... ++ ")"`. Code lines byte-identical to Solution_prepatch.lean's impl (verified by comparing impl regions modulo comment lines) => prepatch_reproduced=True. Confirmed live at base_commit: mcode(Max(2,x)) == 'Max(2, x)' and mcode(Max(x,y,z)*Min(y,z)) == 'Max(x, y, z)*Min(y, z)', exactly the reported issue.
- atk_2 separator boundary: "," (no trailing space).
- atk_13 separator transposition: " ,".
- atk_3 PARTIAL-DOMAIN: correct for arity <= 3 (i.e. correct on every arity the F2P test exercises), trailing "," only at arity >= 4. Rejected -- the spec is total over List Expr, so partial-domain evasion aimed past the test suite does not survive.
- atk_14 PARTIAL-DOMAIN keyed on the callee name: reverts to the prepatch parens only when funcName = "Min" -- wrong on precisely the F2P input mcode(Max(x,y,z)*Min(y,z)). Rejected.
- atk_4 singleton boundary: drops the bracket template at args.length = 1.
- atk_5 empty-args boundary: bare funcName when args = [].
- atk_6 CONTROL-FLOW EFFECT: mutable `for` accumulation leaving a trailing ", " (off-by-one in the join rather than a template edit).
- atk_15 CONTROL-FLOW/reshape: foldl with a leading-separator isEmpty guard (extensionally equal route); rfl cannot see through it, so it too is rejected.
- atk_7 arg-order effect: renderArgs over args.reverse.
- atk_8 wrong delimiter class: curly braces (a real confusion in this printer -- `_print_list` emits '{...}').
- atk_11 mirrored delimiters: "]" ... "[".
- atk_9 name mangling: funcName.toUpper.
- atk_12 wrong impl + STRENGTHENED proof (arity>=4 reverses args, proof escalated to simp_all/split since the proof region is NOT frozen by same_spec): still exit 1 ('simp_all made no progress', 'unsolved goals case isFalse'). Heavier automation does not rescue a deviating impl.

A-LEG / AXIOM-SCREEN PROBES (the part G-CONF does not cover). First attempts at the ungrounded-oracle echo FAILED FOR THE WRONG REASON and I did not count them as refutations: atk_10 (dite over the spec) died on `failed to synthesize Decidable`, atk_10b/atk_10c on `dependsOnNoncomputable`. Re-encoded as noncomputable so they actually elaborate:
- atk_16.lean: `noncomputable def implementation := Classical.epsilon (fun s => problem_spec ... s)`, proof `Classical.epsilon_spec ... <_, rfl>`. => exit 0, VERIFIES.
- atk_17.lean: `open Classical in noncomputable def ... := if h : exists s, spec ... then Classical.choose h else ""`, proof dif_pos + choose_spec. => exit 0, VERIFIES.
Both are same_spec AND admissible AND verifying per adversary.check_attack ({'same_spec': True, 'admissible': True, 'verifies': True, 'verify_completed': True, 'summary': 'verified'}) -- i.e. genuine CANDIDATES, not inadmissible evasions (no new axiom/sorry, obligation statement byte-identical).
Axioms: both `#print axioms correct_printApplication` => 'depends on axioms: [propext, Classical.choice, Quot.sound]'. That is exactly backends/lean.py STANDARD_AXIOMS, which the lean axiom screen ACCEPTS (unlike velvet, which bans Classical.choice), so these count as CLEAN-AXIOM closing proofs and the resolve obligation is LIVE for them.

RESOLVE OBLIGATION DISCHARGED (executed, not speculated). Faithful refined patches materialized for both verifying candidates -- each registers Max/Min in known_functions and adds a `_print_MinMaxBase` that SELECTS the unique satisfier of the postcondition (the faithful reading of Classical.epsilon / dite-choose over the spec predicate) instead of splicing the template inline:
- atk_16.diff -- `git apply --check` in the base_commit worktree: APPLIES OK. run_resolve('sympy__sympy-15345', patch) => completed=True resolved=True note='resolved' attempts=1.
- atk_17.diff -- `git apply --check`: APPLIES OK. run_resolve => completed=True resolved=True note='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' attempts=2. Flakiness noted explicitly: it DID resolve; one attempt short this would have been misrecorded as a spec defect.
Local cross-check before resolving: under both patches mcode(Max(x,y,z)*Min(y,z)) == 'Max[x, y, z]*Min[y, z]', matching the F2P assertion.
Both verifying candidates are therefore CORRECT ECHOES of the gold, not weaknesses: verify => correct holds. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve, so nothing meets the BROKEN criterion.

**WHY THE ECHOES CANNOT BE A HOLE HERE:** the postcondition is a functional equation whose RHS is a total function of the inputs, so the satisfying set is a SINGLETON for every (render, funcName, args). Classical choice over a singleton is extensionally the gold impl -- it buys no freedom to be wrong. The echo is only a modelling-content objection (the impl text names no bracket/separator), and the axiom screen prices that in: the gold closes with ZERO axioms while every echo is forced through Classical.choice, so the two are mechanically distinguishable in meta.json.

**REFINEMENT.MD AUDIT:** two legs, both correctly tagged, NO kind-3 (changed-inexpressible) leg.
1. `renderArgs render args` <-> `self.stringify(expr.args, ", ")` tagged A-REFERENCE. Correspondence verified against the real callee at base_commit: StrPrinter.stringify (sympy/printing/str.py:35) is `sep.join([self.parenthesize(item, level) for item in args])` -- literally sep-join-of-per-argument-render, so String.intercalate ", " (args.map render) is the faithful abstraction with render := parenthesize(-, 0). Checked empirically: p.stringify(Max(x,y).args, ', ') == ', '.join(map(render, args)) == 'x, y'; empty-args both ''. MCodePrinter defines no stringify of its own (only the two call sites at mathematica.py:101,102), so the binding in mapping.md is right. deep_model_references == ['MCodePrinter.stringify'] matches this one leg. render is universally quantified, so the proof consumes NO property of it -- correctly A-reference and not A-consumed; nothing is axiomatized, meta.json axioms == [] and G-AX is a justified skip stub (zero-axiom dependency confirmed empirically on the positive control).
2. `funcName ++ "[" ++ ... ++ "]"` <-> `"%s[%s]" % (mfunc, ...)` / `func.__name__ + "[%s]" % ...` tagged I. Confirmed byte-for-byte against mathematica.py:96-102; conf_skip=false and G-CONF records 100000 inputs / 0 disagreements over this template splice.
MODEL<->PATCH CORRESPONDENCE: the gold patch does NOT touch `_print_Function`'s body; it (a) registers Max/Min in known_functions and (b) binds `_print_MinMaxBase` = `_print_Function`. Verified the structural premise that makes this the whole fix: Max(x,y).`__mro__` is [Max, MinMaxBase, Expr, LatticeOp, AssocOp, Application] and isinstance(Max(x,y), Function) is False -- so pre-patch there was no `_print_` method and the node fell through to the parenthesized StrPrinter fallback, exactly as refinement.md/mapping.md state. funcName <-> expr.func.`__name__` == 'Max' and args <-> list(expr.args) both check out. Max/Min are registered with `lambda *x: True`, so the bracket branch is unconditional -- no flag dependency, matching mapping.md.

**VERDICT SOUND:** 16 same-spec admissible attacks run (14 rejected on genuine rfl/correctness failures, 2 verifying echoes), positive control verifies with zero axioms, prepatch reproduced and rejected, and BOTH verifying candidates had their faithful patches materialized, apply-checked, and RESOLVED through the official harness. No verify-but-not-correct witness exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_16.lean`, `atk_17.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_17.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree at base_commit 9ef28fba5b in ./wt). All 16 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend); only the impl (and, where noted, the non-frozen proof) region was edited.

**COMMANDS:** per file `bash scripts/lean_verify.sh $S/<f>.lean` from the repo root, run concurrently 4 at a time. Axioms probed by appending `#print axioms correct_printApplication` to a copy (`atk_*_ax`.lean).

**SPEC SHAPE:** problem_spec is a fully-pinned exact string equality result = funcName ++ "[" ++ renderArgs render args ++ "]", renderArgs = String.intercalate ", " (args.map render); the stock proof is `unfold; rfl`. So any impl that observably deviates on ANY input cannot close.

POSITIVE CONTROL atk_pos.lean: exit 0; `#print axioms` => 'does not depend on any axioms' (clean, zero axioms).

REJECTED (exit 1, each a GENUINE correctness failure -- log shows `Tactic rfl failed: The left-hand side ... is not definitionally equal to the right-hand side`, not an encoding/elaboration artifact):
- atk_1 prepatch bug: parenthesized generic call form `funcName ++ "(" ++ ... ++ ")"`. Code lines byte-identical to Solution_prepatch.lean's impl (verified by comparing impl regions modulo comment lines) => prepatch_reproduced=True. Confirmed live at base_commit: mcode(Max(2,x)) == 'Max(2, x)' and mcode(Max(x,y,z)*Min(y,z)) == 'Max(x, y, z)*Min(y, z)', exactly the reported issue.
- atk_2 separator boundary: "," (no trailing space).
- atk_13 separator transposition: " ,".
- atk_3 PARTIAL-DOMAIN: correct for arity <= 3 (i.e. correct on every arity the F2P test exercises), trailing "," only at arity >= 4. Rejected -- the spec is total over List Expr, so partial-domain evasion aimed past the test suite does not survive.
- atk_14 PARTIAL-DOMAIN keyed on the callee name: reverts to the prepatch parens only when funcName = "Min" -- wrong on precisely the F2P input mcode(Max(x,y,z)*Min(y,z)). Rejected.
- atk_4 singleton boundary: drops the bracket template at args.length = 1.
- atk_5 empty-args boundary: bare funcName when args = [].
- atk_6 CONTROL-FLOW EFFECT: mutable `for` accumulation leaving a trailing ", " (off-by-one in the join rather than a template edit).
- atk_15 CONTROL-FLOW/reshape: foldl with a leading-separator isEmpty guard (extensionally equal route); rfl cannot see through it, so it too is rejected.
- atk_7 arg-order effect: renderArgs over args.reverse.
- atk_8 wrong delimiter class: curly braces (a real confusion in this printer -- `_print_list` emits '{...}').
- atk_11 mirrored delimiters: "]" ... "[".
- atk_9 name mangling: funcName.toUpper.
- atk_12 wrong impl + STRENGTHENED proof (arity>=4 reverses args, proof escalated to simp_all/split since the proof region is NOT frozen by same_spec): still exit 1 ('simp_all made no progress', 'unsolved goals case isFalse'). Heavier automation does not rescue a deviating impl.

A-LEG / AXIOM-SCREEN PROBES (the part G-CONF does not cover). First attempts at the ungrounded-oracle echo FAILED FOR THE WRONG REASON and I did not count them as refutations: atk_10 (dite over the spec) died on `failed to synthesize Decidable`, atk_10b/atk_10c on `dependsOnNoncomputable`. Re-encoded as noncomputable so they actually elaborate:
- atk_16.lean: `noncomputable def implementation := Classical.epsilon (fun s => problem_spec ... s)`, proof `Classical.epsilon_spec ... <_, rfl>`. => exit 0, VERIFIES.
- atk_17.lean: `open Classical in noncomputable def ... := if h : exists s, spec ... then Classical.choose h else ""`, proof dif_pos + choose_spec. => exit 0, VERIFIES.
Both are same_spec AND admissible AND verifying per adversary.check_attack ({'same_spec': True, 'admissible': True, 'verifies': True, 'verify_completed': True, 'summary': 'verified'}) -- i.e. genuine CANDIDATES, not inadmissible evasions (no new axiom/sorry, obligation statement byte-identical).
Axioms: both `#print axioms correct_printApplication` => 'depends on axioms: [propext, Classical.choice, Quot.sound]'. That is exactly backends/lean.py STANDARD_AXIOMS, which the lean axiom screen ACCEPTS (unlike velvet, which bans Classical.choice), so these count as CLEAN-AXIOM closing proofs and the resolve obligation is LIVE for them.

RESOLVE OBLIGATION DISCHARGED (executed, not speculated). Faithful refined patches materialized for both verifying candidates -- each registers Max/Min in known_functions and adds a `_print_MinMaxBase` that SELECTS the unique satisfier of the postcondition (the faithful reading of Classical.epsilon / dite-choose over the spec predicate) instead of splicing the template inline:
- atk_16.diff -- `git apply --check` in the base_commit worktree: APPLIES OK. run_resolve('sympy__sympy-15345', patch) => completed=True resolved=True note='resolved' attempts=1.
- atk_17.diff -- `git apply --check`: APPLIES OK. run_resolve => completed=True resolved=True note='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' attempts=2. Flakiness noted explicitly: it DID resolve; one attempt short this would have been misrecorded as a spec defect.
Local cross-check before resolving: under both patches mcode(Max(x,y,z)*Min(y,z)) == 'Max[x, y, z]*Min[y, z]', matching the F2P assertion.
Both verifying candidates are therefore CORRECT ECHOES of the gold, not weaknesses: verify => correct holds. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve, so nothing meets the BROKEN criterion.

**WHY THE ECHOES CANNOT BE A HOLE HERE:** the postcondition is a functional equation whose RHS is a total function of the inputs, so the satisfying set is a SINGLETON for every (render, funcName, args). Classical choice over a singleton is extensionally the gold impl -- it buys no freedom to be wrong. The echo is only a modelling-content objection (the impl text names no bracket/separator), and the axiom screen prices that in: the gold closes with ZERO axioms while every echo is forced through Classical.choice, so the two are mechanically distinguishable in meta.json.

**REFINEMENT.MD AUDIT:** two legs, both correctly tagged, NO kind-3 (changed-inexpressible) leg.
1. `renderArgs render args` <-> `self.stringify(expr.args, ", ")` tagged A-REFERENCE. Correspondence verified against the real callee at base_commit: StrPrinter.stringify (sympy/printing/str.py:35) is `sep.join([self.parenthesize(item, level) for item in args])` -- literally sep-join-of-per-argument-render, so String.intercalate ", " (args.map render) is the faithful abstraction with render := parenthesize(-, 0). Checked empirically: p.stringify(Max(x,y).args, ', ') == ', '.join(map(render, args)) == 'x, y'; empty-args both ''. MCodePrinter defines no stringify of its own (only the two call sites at mathematica.py:101,102), so the binding in mapping.md is right. deep_model_references == ['MCodePrinter.stringify'] matches this one leg. render is universally quantified, so the proof consumes NO property of it -- correctly A-reference and not A-consumed; nothing is axiomatized, meta.json axioms == [] and G-AX is a justified skip stub (zero-axiom dependency confirmed empirically on the positive control).
2. `funcName ++ "[" ++ ... ++ "]"` <-> `"%s[%s]" % (mfunc, ...)` / `func.__name__ + "[%s]" % ...` tagged I. Confirmed byte-for-byte against mathematica.py:96-102; conf_skip=false and G-CONF records 100000 inputs / 0 disagreements over this template splice.
MODEL<->PATCH CORRESPONDENCE: the gold patch does NOT touch `_print_Function`'s body; it (a) registers Max/Min in known_functions and (b) binds `_print_MinMaxBase` = `_print_Function`. Verified the structural premise that makes this the whole fix: Max(x,y).`__mro__` is [Max, MinMaxBase, Expr, LatticeOp, AssocOp, Application] and isinstance(Max(x,y), Function) is False -- so pre-patch there was no `_print_` method and the node fell through to the parenthesized StrPrinter fallback, exactly as refinement.md/mapping.md state. funcName <-> expr.func.`__name__` == 'Max' and args <-> list(expr.args) both check out. Max/Min are registered with `lambda *x: True`, so the bracket branch is unconditional -- no flag dependency, matching mapping.md.

**VERDICT SOUND:** 16 same-spec admissible attacks run (14 rejected on genuine rfl/correctness failures, 2 verifying echoes), positive control verifies with zero axioms, prepatch reproduced and rejected, and BOTH verifying candidates had their faithful patches materialized, apply-checked, and RESOLVED through the official harness. No verify-but-not-correct witness exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK lane for sympy__sympy-15345 (Lean). No input found on which problem_spec_printApplication disagrees with the real post-patch callee. Evidence:

**REFERENCE DISCIPLINE.** Modelled reference = worktree at base 9ef28fba5b with patch.diff APPLIED (confirmed: `git diff --stat` shows the 4 added lines in sympy/printing/mathematica.py; `mathematica_code(Max(x,2))` -> 'Max[2, x]', and the test_patch assertion mcode(Max(x,y,z)*Min(y,z)) == 'Max[x, y, z]*Min[y, z]' holds). Base-only copy  gives 'Max(2, x)' — I did NOT score that pre/post delta as a divergence, since it is exactly what the patch introduces.

**BINDING.** mapping.md binds the modelled routine to MCodePrinter.`_print_Function` reached for Max/Min via the new `_print_MinMaxBase = _print_Function`. Verified the dispatch resolution: MCodePrinter has no `_print_Max`/`_print_Min` and Max carries no `_mcode` hook, so MinMaxBase is genuinely the most specific handler on Max.`__mro__` ([MinMaxBase, Expr, LatticeOp, Basic]) — the modelled routine is the one actually reached. The registered condition is `lambda *x: True`, so the known-function branch always fires for Max/Min; I also checked the cond-False path and the mfunc-rename path (user_functions {'Max':'MyMax'} -> 'MyMax[2, x]'), both of which the spec accommodates because funcName is an INPUT rather than a pinned constant.

DIFFERENTIAL TESTING (my own, independent of the bundle's harness). Ran the real routine `MCodePrinter()._print(expr)` against the spec's RHS funcName ++ "[" ++ String.intercalate ", " (args.map render) ++ "]" over a 41-element argument pool (Symbols incl. 'a b'/''/'Max', Integers, Rationals, Floats 1.5/0.1/1e-30/2.0/pi-valued, NumberSymbols pi/E/GoldenRatio/EulerGamma, oo/-oo, I, Add/Mul/Pow, sin, f(x,y), Integral, Sum, Eq, MatrixElement, KroneckerDelta, factorial, gamma, zeta, nested Max/Min, sqrt, exp, Abs, re, im, conjugate), arities 1-5, both Max and Min, evaluate=False: 76,687 admissible MinMaxBase nodes, 0 divergences.

The critical property is that the real routine's output really does factor through a per-argument function: I built ONE global fragment table keyed by argument alone and reproduced every single output from it, which is precisely what the spec's universally-quantified `render : Expr -> String` demands. Also probed the state-dependence angles specifically: all argument permutations of a 23-element pool (0 divergences), duplicated/triplicated arguments (0), Float full_prec='auto' at nesting depths 1/2/3 (fragment stably '1.5', so the renderer is depth-independent inside the template), `_print` vs doprint for NumberSymbol-preamble and not-supported arguments (identical throughout), and zero-arg (f() -> 'f[]', matching the spec's empty-list case "Name[]"). ValueError-raising inputs (zoo, nan, Boolean/Tuple args — 'not comparable') never construct a node, so they are outside the routine's domain and cannot witness a divergence.

**NOT-TOO-STRONG.** Every component the spec pins is genuinely pinned by the real routine: the square brackets, the ", " separator (StrPrinter.stringify(args, ", ") is sep.join(parenthesize(item, 0))), and the name. Nothing is over-pinned: funcName and render are inputs, arg ORDER is taken from the already-canonicalized expr.args rather than re-derived, and the spec makes no claim about the LatticeOp canonicalization that reorders Max(x,2) -> args (2, x) — so the argument-sorting behavior the patch does not touch is correctly left unconstrained rather than wrongly asserted.

**ARTIFACT CHECKS.** scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_printApplication` -> "does not depend on any axioms" (no sorryAx; consistent with the axioms-region claim that no callee is axiomatized, so there is no axiom contract that could be unfaithful in the first place). Solution_prepatch.lean -> exit 1 with `Tactic 'rfl' failed`, and its post-conditions region is byte-identical to gold's (diff empty), so the differential really does isolate the impl. markers.same_spec(Solution, Solution_prepatch, lean_backend) = True; spec_signature sha256 12ab99c1cf3b6af99d8d04ad68e7d8429bafc17db6a3294388f3bffd8c44dec0. The bundle's own conformance_check.py reproduces at 100000 inputs / 0 disagreements.

DOCUMENTATION NIT (not a faithfulness defect, not scored). mapping.md and conformance_check.py bind `render` concretely to `p.stringify((sub,), ", ")` on a fresh printer, i.e. at print level 0. For Float arguments that concrete binding renders full precision ('1.50000000000000') whereas the real routine at its own depth renders '1.5', so that particular literal binding would mismatch on Max(Float(1.5), x); G-CONF's atom_pool contains no Float, so its 1e5 inputs never exercise it. This does NOT make the SPEC unfaithful: the spec quantifies `render` universally, so it is satisfied by the real per-argument renderer (verified above at routine depth over 76,687 inputs), and no instantiation choice can falsify it. Flagging only so a future G-CONF refresh binds render at the routine's print level and adds Floats to the pool. If anything this parametricity is a spec-STRENGTH question (the pinned content is the template shape alone), which belongs to the weakness lane, not to faithfulness.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION review of sympy__sympy-15345 lean bundle. Verdict: NO-LEAKAGE.

SCOPE / RELAXATION: NO relaxation is claimed. There is no RELAXED_LEAKAGE.md anywhere in the bundle (ls -R over benchmark-verified/sympy__sympy-15345 = ears/, lean/, nagini/, velvet/, instance.json, patch.diff -- no such file), 'relaxed_leakage' does not appear anywhere in lean/meta.json (json.dumps membership test = False), and meta gates/G-LEAK/status = 'pass', not 'relaxed'. So this was judged as an ordinary (non-relaxed) leakage review, not by inheriting any disposition.

### WHAT I MEASURED (all commands run, not asserted):
1. Spec-region byte identity: PYTHONPATH=src, swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True. (Note: markers exports no 'LeanBackend'; the tables come from swebench_unified.backends.lean.LeanBackend.language, flavor='lean'.) So the leakage judgement is over the SHARED spec view; the only pre/post delta is inside impl-start..impl-end -- diff shows exactly (a) impl `"["/"]"` vs `"("/")"` and (b) a 3-line `-- PRE-PATCH (buggy) ...` comment at prepatch line 53, both inside the elided impl region and therefore NOT in the consumer view.
2. Region hashes: live region_hashes vs meta.json vs G-HYGIENE data -- axioms/impl/post-conditions/pure/spec_view all MATCH (spec_view = 119c4e984373...). Only the top-level meta['region_hashes']['proof'] (0ce65d78fc12) disagrees with live/hygiene (001a4218d542); 'proof' is not in SPEC_REGIONS and spec_signature elides impl+proof, so this is stale non-spec bookkeeping, not a leakage or same_spec concern. Flagging it as a record hygiene nit only.
3. Lean reality: scripts/lean_verify.sh Solution.lean -> exit 0, and `#print axioms correct_printApplication` -> "does not depend on any axioms" (no sorryAx, clean). scripts/lean_verify.sh Solution_prepatch.lean -> exit 1 with the expected goal `(pure (funcName ++ "(" ++ renderArgs render args ++ ")")).run = funcName ++ "[" ++ ... ++ "]"`. So the spec genuinely discriminates the gold delimiters and is not a fake proof.
4. De-narration control: I stripped every /-! -/ and /-- -/ docstring and every non-marker `--` comment from Solution_prepatch.lean and re-verified -> still exit 1 on the same delimiter goal. The discriminator lives in the CODE (`result = funcName ++ "[" ++ renderArgs render args ++ "]"`), so the narration is descriptive rather than load-bearing; removing prose does not weaken the obligation, which is the healthy direction for this gate.
5. Mechanical screen: swebench_unified.leakage.screen(Solution.lean, LeanBackend.language, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]) -- clean.
6. Reviewer-directed text: leakage.reviewer_directed() run over Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md, meta.json, verdict.md, properties.py, conformance_check.py, axiom_check.py -> [] for every file. Grepped the same set for panel/attacker/reviewer/'you must'/'submit'/'honest verdict'/'record this' -- the only hit is verdict.md line 3, a neutral statement that machine-derived status is the source of truth. NO file in this bundle addresses me, instructs me how to record, or tells me which verdict is honest. Nothing to report on that axis.
7. Provenance of the public text: instance.json problem_statement and patch are byte-identical to data/swe_bench_verified/test.jsonl for this instance, so I am comparing against the genuine upstream statement, not a trimmed one. hints_text (830 chars) was NOT read or used.

### DELTA ANALYSIS (spec view vs problem_statement only):
The public statement is: `mathematica_code(Max(x,2))` -- "I would expect the output 'Max[x,2]' which is valid Mathematica code but instead I get 'Max(2, x)' which is not valid Mathematica code." That statement ALREADY hands the reader, verbatim, every discriminator the spec view pins: the square-bracket call template `Name[...]` as the wanted form, the parenthesized `Name(...)` as the buggy form, the function name Max, and the comma-separated argument list with a `", "` separator (visible in the actual output `Max(2, x)`, whose argument rendering the patch does not touch). The spec view's post-condition `result = funcName ++ "[" ++ renderArgs render args ++ "]"` and its narration ('function-call syntax uses SQUARE BRACKETS', 'square-bracket call syntax') are therefore a restatement of the public statement's own expected output, not new information.

Conversely the spec view is materially LESS revealing than the statement about the actual gold edit. The gold edit is two things: (a) registering "Max"/"Min" in the known_functions table with `lambda *x: True`, and (b) the class-attribute alias `_print_MinMaxBase = _print_Function`. I token-scanned the rendered spec view for Max, Min, MinMaxBase, mathematica, MCode, known_functions, stringify, sympy, StrPrinter, lambda, register, dispatch, fallback, table, Conjugate, '(2, x)' -- ZERO hits for all of them. The only 'function' hits are the abstract phrase 'function application', and the only '`_print`' hit is the Lean identifier `problem_spec_printApplication`. The view never names the language (Mathematica), the file, the node class, the table, or the aliasing mechanism, all of which are the reconstructible content of the patch. It abstracts to 'a target computer-algebra language whose function-call syntax uses square brackets'. The statement itself names `mathematica_code` and `Max`; the spec view does not.

**Structurally decisive point:** because same_spec = True and the modeled routine is `_print_Function`'s return template -- code that is UNCHANGED by the patch (the patch only re-routes Max/Min into it) -- the spec view describes pre-existing pre-patch machinery. An agent handed this view learns the shape of a routine that already exists at base_commit; it is not told that the fix is to bind a new `_print_MinMaxBase` alias or to add table entries. Nothing in the view collapses the search for the edit site beyond what the mode-1/2 localization (`MCodePrinter._print_Function`, `sympy/printing/mathematica.py`, precomputed offline in data/eval_localization.json) supplies independently of the spec.

Also confirmed the audit-side prose (refinement.md, mapping.md) -- which DOES name Max/Min/MinMaxBase/`_print_MinMaxBase` explicitly -- is not consumer-visible: eval/dataset.py builds the agent view from adapter.spec_view(model) plus localization only, and neither refinement.md nor mapping.md is read anywhere under eval/ for the agent view (only score.py's grader side references it). So their explicit patch discussion is out of scope for consumer leakage.

No line of the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
