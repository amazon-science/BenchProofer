# P2 adversarial audit — sympy__sympy-19346

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_11_colon.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8_echo.lean`, `atk_9_double.lean`, `atk_10_oracle.lean`, `atk_12_order.lean`, `atk_13_reprify.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample found. The spec is a total extensional pin: problem_spec_dictRepr fixes the result string to "{" ++ intercalate ", " (entries.map entryText) ++ "}" and problem_spec_setRepr to the if-empty-then-"set()"-else-braced-join, both over the SAME opaque elemRepr the impl must use. Because both postconditions are single-equation total functions of the input with no existential/disjunctive slack, every same-spec impl whose correct_* closes is extensionally EQUAL to gold, and each such impl's faithful patch resolved under the official harness (5/5). The only residual gap is intensional, not extensional: elemRepr is a pure opaque carrier, so the number of calls (atk_9_double), their ORDER (atk_12_order), and whether they route through self.reprify or an inlined comprehension (atk_13_reprify) are invisible to the model. I probed all three deliberately; each verified with clean axioms AND resolved, so the gap is not exploitable here. It is genuinely closed in the real callee, not just untested: ReprPrinter never reads Printer._print_level (grep of repr.py finds no occurrence; only str.py:693 uses it) and doprint == self._str(self._print(expr)) with _str = str, so the real doprint is a pure function of its argument. An intensional weakness would therefore need an order/count-sensitive callee, and this one has none.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -72,7 +72,7 @@
   let sep := ", "
   let mut parts : List String := []
   for p in entries do
-    parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
+    parts := parts ++ [nativeRepr p.1 ++ ": " ++ nativeRepr p.2]
   return "{" ++ String.intercalate sep parts ++ "}"
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,7 +116,6 @@
 -- impl-start
 def implementation_setRepr
     (elems : List SymExpr) : String := Id.run do
-  if elems.isEmpty then return "set()"
   let mut parts : List String := []
   for e in elems do
     parts := parts ++ [elemRepr e]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -73,6 +73,8 @@
   let mut parts : List String := []
   for p in entries do
     parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
+  if parts.length == 1 then
+    return String.intercalate sep parts
   return "{" ++ String.intercalate sep parts ++ "}"
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,7 +116,7 @@
 -- impl-start
 def implementation_setRepr
     (elems : List SymExpr) : String := Id.run do
-  if elems.isEmpty then return "set()"
+  if elems.length <= 1 then return "set()"
   let mut parts : List String := []
   for e in elems do
     parts := parts ++ [elemRepr e]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -73,6 +73,7 @@
   let mut parts : List String := []
   for p in entries do
     parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
+    break
   return "{" ++ String.intercalate sep parts ++ "}"
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -119,7 +119,7 @@
   if elems.isEmpty then return "set()"
   let mut parts : List String := []
   for e in elems do
-    parts := parts ++ [elemRepr e]
+    parts := parts ++ [nativeRepr e]
   return "{" ++ String.intercalate ", " parts ++ "}"
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,7 +69,7 @@
 -- impl-start
 def implementation_dictRepr
     (entries : List (SymExpr × SymExpr)) : String := Id.run do
-  let sep := ", "
+  let sep := ","
   let mut parts : List String := []
   for p in entries do
     parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
```

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,18 +68,11 @@
 
 -- impl-start
 def implementation_dictRepr
-    (entries : List (SymExpr × SymExpr)) : String := Id.run do
-  let sep := ", "
-  let mut parts : List String := []
-  for p in entries do
-    parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
-  return "{" ++ String.intercalate sep parts ++ "}"
+    (entries : List (SymExpr × SymExpr)) : String :=
+  "{" ++ String.intercalate ", " (entries.map entryText) ++ "}"
 -- impl-end
 
 -- proof-start
-/-- Loop accumulator lemma: a `for x in xs do acc := acc ++ [f x]` loop (whose
-desugared body is `do pure PUnit.unit; pure (ForInStep.yield (r ++ [f x]))`)
-computes `init ++ xs.map f`, generalized over the accumulator. -/
 theorem forIn_append_singleton_eq_map
     {α β : Type} (f : α → β) (xs : List α) (init : List β) :
     (forIn xs init (fun x r => do
@@ -94,10 +87,6 @@
       problem_spec_dictRepr entries (implementation_dictRepr entries) := by
   intro entries
   unfold problem_spec_dictRepr implementation_dictRepr
-  simp only [Id.run]
-  rw [forIn_append_singleton_eq_map
-        (fun p : SymExpr × SymExpr => elemRepr p.1 ++ ": " ++ elemRepr p.2)]
-  simp only [List.nil_append]
   rfl
 -- proof-end
 
@@ -115,12 +104,9 @@
 
 -- impl-start
 def implementation_setRepr
-    (elems : List SymExpr) : String := Id.run do
-  if elems.isEmpty then return "set()"
-  let mut parts : List String := []
-  for e in elems do
-    parts := parts ++ [elemRepr e]
-  return "{" ++ String.intercalate ", " parts ++ "}"
+    (elems : List SymExpr) : String :=
+  if elems.isEmpty then "set()"
+  else "{" ++ String.intercalate ", " (elems.map elemRepr) ++ "}"
 -- impl-end
 
 -- proof-start
@@ -129,10 +115,5 @@
       problem_spec_setRepr elems (implementation_setRepr elems) := by
   intro elems
   unfold problem_spec_setRepr implementation_setRepr
-  by_cases h : elems.isEmpty
-  · simp only [Id.run, h]; rfl
-  · simp only [Id.run, h]
-    rw [forIn_append_singleton_eq_map elemRepr]
-    simp only [List.nil_append]
-    rfl
+  rfl
 -- proof-end
```

Attack 9 — `atk_9_double.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -72,6 +72,7 @@
   let sep := ", "
   let mut parts : List String := []
   for p in entries do
+    let _discard := elemRepr p.1
     parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
   return "{" ++ String.intercalate sep parts ++ "}"
 -- impl-end
```

Attack 10 — `atk_10_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -67,19 +67,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_dictRepr
-    (entries : List (SymExpr × SymExpr)) : String := Id.run do
-  let sep := ", "
-  let mut parts : List String := []
-  for p in entries do
-    parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
-  return "{" ++ String.intercalate sep parts ++ "}"
+noncomputable def implementation_dictRepr
+    (entries : List (SymExpr × SymExpr)) : String :=
+  Classical.choose (⟨"{" ++ String.intercalate ", " (entries.map entryText) ++ "}", rfl⟩ :
+    ∃ s : String, problem_spec_dictRepr entries s)
 -- impl-end
 
 -- proof-start
-/-- Loop accumulator lemma: a `for x in xs do acc := acc ++ [f x]` loop (whose
-desugared body is `do pure PUnit.unit; pure (ForInStep.yield (r ++ [f x]))`)
-computes `init ++ xs.map f`, generalized over the accumulator. -/
 theorem forIn_append_singleton_eq_map
     {α β : Type} (f : α → β) (xs : List α) (init : List β) :
     (forIn xs init (fun x r => do
@@ -93,12 +87,9 @@
     ∀ (entries : List (SymExpr × SymExpr)),
       problem_spec_dictRepr entries (implementation_dictRepr entries) := by
   intro entries
-  unfold problem_spec_dictRepr implementation_dictRepr
-  simp only [Id.run]
-  rw [forIn_append_singleton_eq_map
-        (fun p : SymExpr × SymExpr => elemRepr p.1 ++ ": " ++ elemRepr p.2)]
-  simp only [List.nil_append]
-  rfl
+  exact Classical.choose_spec
+    (⟨"{" ++ String.intercalate ", " (entries.map entryText) ++ "}", rfl⟩ :
+      ∃ s : String, problem_spec_dictRepr entries s)
 -- proof-end
 
 -- post-conditions-start
```

Attack 11 — `atk_11_colon.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -72,7 +72,7 @@
   let sep := ", "
   let mut parts : List String := []
   for p in entries do
-    parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
+    parts := parts ++ [elemRepr p.1 ++ ":" ++ elemRepr p.2]
   return "{" ++ String.intercalate sep parts ++ "}"
 -- impl-end
 
```

Attack 12 — `atk_12_order.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -72,7 +72,9 @@
   let sep := ", "
   let mut parts : List String := []
   for p in entries do
-    parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]
+    let v := elemRepr p.2
+    let k := elemRepr p.1
+    parts := parts ++ [k ++ ": " ++ v]
   return "{" ++ String.intercalate sep parts ++ "}"
 -- impl-end
 
```

Attack 13 — `atk_13_reprify.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -117,9 +117,7 @@
 def implementation_setRepr
     (elems : List SymExpr) : String := Id.run do
   if elems.isEmpty then return "set()"
-  let mut parts : List String := []
-  for e in elems do
-    parts := parts ++ [elemRepr e]
+  let parts := elems.map elemRepr
   return "{" ++ String.intercalate ", " parts ++ "}"
 -- impl-end
 
@@ -131,8 +129,5 @@
   unfold problem_spec_setRepr implementation_setRepr
   by_cases h : elems.isEmpty
   · simp only [Id.run, h]; rfl
-  · simp only [Id.run, h]
-    rw [forIn_append_singleton_eq_map elemRepr]
-    simp only [List.nil_append]
-    rfl
+  · simp only [Id.run, h]; rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all work; base_commit worktree at ./wt @ 94fb720696). same_spec=True for all 13 attacks + positive control (verified with the env python python; /usr/bin/python3 lacks swebench_unified).

**POSITIVE CONTROL:** `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. Axioms via ax_probe.lean (same file + #print axioms): correct_dictRepr and correct_setRepr each `[propext, Quot.sound]` -> clean.

**PREPATCH REPRODUCED:** `bash scripts/lean_verify.sh Solution_prepatch.lean` -> exit 1, unsolved goals at BOTH legs (lines 92, 130), i.e. one prepatch breaks correct_dictRepr and correct_setRepr independently, as refinement.md claims. Independently confirmed in Python at base_commit: srepr({x:y})=='{x: y}' and srepr({x,y})=='{y, x}' (non-canonical), vs the patched trees' "{Symbol('x'): Symbol('y')}".

#### 8 REJECTED (exit 1; all on genuine spec-mismatch goals, not syntax)
Command for each: `bash scripts/lean_verify.sh <name>.lean`
- atk_1 (prepatch dict A-leg: nativeRepr per entry) exit 1 - rewrite failed, pattern absent
- atk_2 (prepatch set leg: empty guard deleted) exit 1 - rfl failed (LHS)
- atk_3 (PARTIAL-DOMAIN: braces omitted for exactly 1 entry) exit 1 - rfl failed
- atk_4 (BOUNDARY off-by-one: "set()" returned when length <= 1) exit 1 - rfl failed x2
- atk_5 (CONTROL-FLOW-EFFECT: `break` after first entry) exit 1 - rewrite failed
- atk_6 (set-side A-leg: nativeRepr per element) exit 1 - rewrite failed
- atk_7 (separator "," loses the space) exit 1 - rfl failed
- atk_11_colon (entry format "k:v", space after colon dropped) exit 1 - rewrite failed

#### 5 VERIFIED w/ CLEAN AXIOMS -> faithful patch MATERIALIZED and RESOLVED
Axioms read from <name>`_ax`.lean (attack + `#print axioms correct_dictRepr/correct_setRepr`); every patch checked with `git apply --check` in the base_commit worktree BEFORE submitting, and each patched tree was semantically spot-checked against the F2P expectations (semcheck.py over <name>/).
Resolve command for each: `python do_resolve.py <name> <name>.diff` (harness.run_resolve, instance sympy__sympy-19346, timeout 3600); JSON <name>.json.
- atk_8_echo (ungrounded-oracle echo: impl := the spec RHS verbatim; proof is `rfl`) exit 0, axioms: `does not depend on any axioms` -> RESOLVED (attempts=3, flaky)
- atk_9_double (A-leg CALL-COUNT: an extra discarded elemRepr p.1 per entry; patch calls the real doprint twice per key) exit 0, `[propext, Quot.sound]` -> RESOLVED (attempts=1)
- atk_10_oracle (Classical.choose of the postcondition witness) exit 0, correct_dictRepr `[Classical.choice]`, correct_setRepr `[propext, Quot.sound]` -> RESOLVED (attempts=2, flaky). NOTE: Classical.choice IS accepted -- backends/lean.py STANDARD_AXIOMS = (propext, Classical.choice, Quot.sound) -- so this counts as clean axioms, and its patch resolving is what keeps it from being a break.
- atk_12_order (A-leg CALL-ORDER: value rendered before key via let-bindings; zeta-reduces to gold so the gold proof closes, but the patch calls doprint on the VALUE first) exit 0, `[propext, Quot.sound]` -> RESOLVED (attempts=2, flaky)
- atk_13_reprify (set leg via List.map; patch BYPASSES self.reprify and inlines map(self.doprint, expr)) exit 0, correct_dictRepr `[propext, Quot.sound]`, correct_setRepr `[propext]` -> RESOLVED (attempts=1)

TWO ATTACKS INITIALLY MISFIRED ON MY OWN PROOF, NOT ON THE SPEC -- reported for honesty: the v1 atk_12_order and atk_13_reprify (heavier accumulator/zip formulations) failed with `sorryAx` in the axiom footprint, i.e. MY tactic scripts were incomplete. Since both impls are extensionally equal to gold they must be provable, so I rewrote them in simpler zeta/rfl-reducible form (mk4.py) and both then closed at exit 0 with clean axioms. Recording a v1 tactic failure as "spec rejects it" would have been a false refutation; the submitted files are the v2 ones.

#### refinement.md AUDIT (no kind-3 leg)
Every row is R / A-reference / I; there are no A-consumed legs and meta.json has axioms=[] with opaque_callees=[SymExpr, elemRepr, nativeRepr], consistent with axiom_check.py being a skip stub and with the measured clean footprint. Tag-by-tag: fn1 op1 R (dict <-> ordered pair list), ops 2/3/5 I (verified literal-for-literal against the gold hunk: sep=", ", the dict_kvs accumulator, "{%s}" % sep.join), op4 A-reference; fn2 op1 R, ops 2/3/5 I (`if not expr: return "set()"`, reprify's list, "{%s}"), op4 A-reference. The two A-reference legs assert elemRepr == self.doprint == srepr on a sub-value.

Confirmed against the real callees at base_commit: doprint (printer.py:249-251) is `self._str(self._print(expr))` with `_str` = str (printer.py:214), `_print` dispatches on type(expr).`__mro__` to the per-type `_print_`* method (the canonical recursion), and reprify (repr.py:27-31) is `sep.join([self.doprint(item) for item in args])` -- so modeling reprify's per-element rendering as elemRepr is exact. The carrier is legitimately NOT axiomatized: it occurs identically in spec and impl, so no property of it is consumed. Its purity (the one thing the opaque model assumes) is real, not assumed: ReprPrinter reads no printer state -- grep for `_print_level` in repr.py finds NONE (only str.py:693) -- which is precisely why atk_9_double/atk_12_order resolve.

Dispatch keys on the type NAME so the methods are setting-independent, matching mapping.md's "flag deps: none" (the printer's `order`/`perm_cyclic` settings only reach `_print_Add`/`_print_Mul`/`_print_Permutation`, none of which the two new methods call). ONE MINOR OVER-MODEL, not a soundness defect and not gate-affecting: refinement.md and mapping.md present the empty-collection literal "set()" as part of the discriminator, but at base_commit str(set()) already == 'set()' (measured), so the empty-set case does NOT distinguish prepatch from gold in reality -- the real discriminator is the per-element renderer alone (elemRepr vs nativeRepr).

The prepatch is still correctly unclosable on both legs for the sound reason (nativeRepr vs elemRepr), and the set-leg empty guard is a faithful I-leg of the gold patch (the gold really does add `if not expr: return "set()"`), so the encoding is right; only the prose's claim that the empty case is discriminating is slightly stronger than the repo supports. Worth a prose touch-up on a future refinement edit, not a repair.

**VERDICT SOUND:** 13 same-spec attacks run (>=5 required), 8 rejected on real spec goals, 5 verified with clean axioms and ALL 5 faithful patches executed through the official harness with resolved=true. No impl with a closing clean-axiom proof has a non-resolving patch, so verify=>correct is not falsified here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_11_colon.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_8_echo.lean`, `atk_9_double.lean`, `atk_10_oracle.lean`, `atk_12_order.lean`, `atk_13_reprify.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample found. The spec is a total extensional pin: problem_spec_dictRepr fixes the result string to "{" ++ intercalate ", " (entries.map entryText) ++ "}" and problem_spec_setRepr to the if-empty-then-"set()"-else-braced-join, both over the SAME opaque elemRepr the impl must use. Because both postconditions are single-equation total functions of the input with no existential/disjunctive slack, every same-spec impl whose correct_* closes is extensionally EQUAL to gold, and each such impl's faithful patch resolved under the official harness (5/5). The only residual gap is intensional, not extensional: elemRepr is a pure opaque carrier, so the number of calls (atk_9_double), their ORDER (atk_12_order), and whether they route through self.reprify or an inlined comprehension (atk_13_reprify) are invisible to the model. I probed all three deliberately; each verified with clean axioms AND resolved, so the gap is not exploitable here. It is genuinely closed in the real callee, not just untested: ReprPrinter never reads Printer._print_level (grep of repr.py finds no occurrence; only str.py:693 uses it) and doprint == self._str(self._print(expr)) with _str = str, so the real doprint is a pure function of its argument. An intensional weakness would therefore need an order/count-sensitive callee, and this one has none.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3]

Attack 9 — `atk_9_double.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 11 — `atk_11_colon.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_order.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_reprify.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (all work; base_commit worktree at ./wt @ 94fb720696). same_spec=True for all 13 attacks + positive control (verified with the env python python; /usr/bin/python3 lacks swebench_unified).

**POSITIVE CONTROL:** `bash scripts/lean_verify.sh pos_control.lean` -> exit 0. Axioms via ax_probe.lean (same file + #print axioms): correct_dictRepr and correct_setRepr each `[propext, Quot.sound]` -> clean.

**PREPATCH REPRODUCED:** `bash scripts/lean_verify.sh Solution_prepatch.lean` -> exit 1, unsolved goals at BOTH legs (lines 92, 130), i.e. one prepatch breaks correct_dictRepr and correct_setRepr independently, as refinement.md claims. Independently confirmed in Python at base_commit: srepr({x:y})=='{x: y}' and srepr({x,y})=='{y, x}' (non-canonical), vs the patched trees' "{Symbol('x'): Symbol('y')}".

#### 8 REJECTED (exit 1; all on genuine spec-mismatch goals, not syntax)
Command for each: `bash scripts/lean_verify.sh <name>.lean`
- atk_1 (prepatch dict A-leg: nativeRepr per entry) exit 1 - rewrite failed, pattern absent
- atk_2 (prepatch set leg: empty guard deleted) exit 1 - rfl failed (LHS)
- atk_3 (PARTIAL-DOMAIN: braces omitted for exactly 1 entry) exit 1 - rfl failed
- atk_4 (BOUNDARY off-by-one: "set()" returned when length <= 1) exit 1 - rfl failed x2
- atk_5 (CONTROL-FLOW-EFFECT: `break` after first entry) exit 1 - rewrite failed
- atk_6 (set-side A-leg: nativeRepr per element) exit 1 - rewrite failed
- atk_7 (separator "," loses the space) exit 1 - rfl failed
- atk_11_colon (entry format "k:v", space after colon dropped) exit 1 - rewrite failed

#### 5 VERIFIED w/ CLEAN AXIOMS -> faithful patch MATERIALIZED and RESOLVED
Axioms read from <name>`_ax`.lean (attack + `#print axioms correct_dictRepr/correct_setRepr`); every patch checked with `git apply --check` in the base_commit worktree BEFORE submitting, and each patched tree was semantically spot-checked against the F2P expectations (semcheck.py over <name>/).
Resolve command for each: `python do_resolve.py <name> <name>.diff` (harness.run_resolve, instance sympy__sympy-19346, timeout 3600); JSON <name>.json.
- atk_8_echo (ungrounded-oracle echo: impl := the spec RHS verbatim; proof is `rfl`) exit 0, axioms: `does not depend on any axioms` -> RESOLVED (attempts=3, flaky)
- atk_9_double (A-leg CALL-COUNT: an extra discarded elemRepr p.1 per entry; patch calls the real doprint twice per key) exit 0, `[propext, Quot.sound]` -> RESOLVED (attempts=1)
- atk_10_oracle (Classical.choose of the postcondition witness) exit 0, correct_dictRepr `[Classical.choice]`, correct_setRepr `[propext, Quot.sound]` -> RESOLVED (attempts=2, flaky). NOTE: Classical.choice IS accepted -- backends/lean.py STANDARD_AXIOMS = (propext, Classical.choice, Quot.sound) -- so this counts as clean axioms, and its patch resolving is what keeps it from being a break.
- atk_12_order (A-leg CALL-ORDER: value rendered before key via let-bindings; zeta-reduces to gold so the gold proof closes, but the patch calls doprint on the VALUE first) exit 0, `[propext, Quot.sound]` -> RESOLVED (attempts=2, flaky)
- atk_13_reprify (set leg via List.map; patch BYPASSES self.reprify and inlines map(self.doprint, expr)) exit 0, correct_dictRepr `[propext, Quot.sound]`, correct_setRepr `[propext]` -> RESOLVED (attempts=1)

TWO ATTACKS INITIALLY MISFIRED ON MY OWN PROOF, NOT ON THE SPEC -- reported for honesty: the v1 atk_12_order and atk_13_reprify (heavier accumulator/zip formulations) failed with `sorryAx` in the axiom footprint, i.e. MY tactic scripts were incomplete. Since both impls are extensionally equal to gold they must be provable, so I rewrote them in simpler zeta/rfl-reducible form (mk4.py) and both then closed at exit 0 with clean axioms. Recording a v1 tactic failure as "spec rejects it" would have been a false refutation; the submitted files are the v2 ones.

#### refinement.md AUDIT (no kind-3 leg)
Every row is R / A-reference / I; there are no A-consumed legs and meta.json has axioms=[] with opaque_callees=[SymExpr, elemRepr, nativeRepr], consistent with axiom_check.py being a skip stub and with the measured clean footprint. Tag-by-tag: fn1 op1 R (dict <-> ordered pair list), ops 2/3/5 I (verified literal-for-literal against the gold hunk: sep=", ", the dict_kvs accumulator, "{%s}" % sep.join), op4 A-reference; fn2 op1 R, ops 2/3/5 I (`if not expr: return "set()"`, reprify's list, "{%s}"), op4 A-reference. The two A-reference legs assert elemRepr == self.doprint == srepr on a sub-value.

Confirmed against the real callees at base_commit: doprint (printer.py:249-251) is `self._str(self._print(expr))` with `_str` = str (printer.py:214), `_print` dispatches on type(expr).`__mro__` to the per-type `_print_`* method (the canonical recursion), and reprify (repr.py:27-31) is `sep.join([self.doprint(item) for item in args])` -- so modeling reprify's per-element rendering as elemRepr is exact. The carrier is legitimately NOT axiomatized: it occurs identically in spec and impl, so no property of it is consumed. Its purity (the one thing the opaque model assumes) is real, not assumed: ReprPrinter reads no printer state -- grep for `_print_level` in repr.py finds NONE (only str.py:693) -- which is precisely why atk_9_double/atk_12_order resolve.

Dispatch keys on the type NAME so the methods are setting-independent, matching mapping.md's "flag deps: none" (the printer's `order`/`perm_cyclic` settings only reach `_print_Add`/`_print_Mul`/`_print_Permutation`, none of which the two new methods call). ONE MINOR OVER-MODEL, not a soundness defect and not gate-affecting: refinement.md and mapping.md present the empty-collection literal "set()" as part of the discriminator, but at base_commit str(set()) already == 'set()' (measured), so the empty-set case does NOT distinguish prepatch from gold in reality -- the real discriminator is the per-element renderer alone (elemRepr vs nativeRepr).

The prepatch is still correctly unclosable on both legs for the sound reason (nativeRepr vs elemRepr), and the set-leg empty guard is a faithful I-leg of the gold patch (the gold really does add `if not expr: return "set()"`), so the encoding is right; only the prose's claim that the empty case is discriminating is slightly stronger than the repo supports. Worth a prose touch-up on a future refinement edit, not a repair.

**VERDICT SOUND:** 13 same-spec attacks run (>=5 required), 8 rejected on real spec goals, 5 verified with clean axioms and ALL 5 faithful patches executed through the official harness with resolved=true. No impl with a closing clean-axiom proof has a non-resolving patch, so verify=>correct is not falsified here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness attack (spec-too-strong / drift) on sympy__sympy-19346 lean bundle. No divergence found on any input in the modeled domain; spec is faithful to the real post-patch repo behavior.

SCOPE / REFERENCE. Modeled functions are ReprPrinter.`_print_dict` and ReprPrinter.`_print_set` (sympy/printing/repr.py), both INTRODUCED by patch.diff. Reference = base_commit worktree with patch.diff APPLIED (built a private mktemp'd copy of  at 94fb7206 and `git apply`'d patch.diff cleanly; did not mutate the shared worktree). Base commit used only for the unchanged callees the model abstracts (doprint/`_print`/reprify/emptyPrinter). Ran real srepr live:: (mpmath + distutils.LooseVersion shim  3.12).

### Artifact integrity
- scripts/lean_verify.sh Solution.lean -> exit 0 (elaborates, no sorry/error).
- #print axioms correct_dictRepr / correct_setRepr / forIn_append_singleton_eq_map -> all [propext, Quot.sound]. No sorryAx, so the proof is real, and no bundle-local axiom is consumed (meta axioms=[] corroborated).
- markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True -> spec region byte-identical; prepatch differs only in impl (nativeRepr for elements, and the set empty-guard dropped).
- markers.region_hashes matches meta.json region_hashes for axioms/pure/post-conditions/impl/spec_view (proof hash differs, which is expected: proof is elided from the spec view and is not spec-constituting).

**CORE FAITHFULNESS QUESTION.** The spec models the recursive element renderer as ONE pure function `elemRepr : SymExpr -> String`, reused for dict keys, dict values, and set members. The real code calls self.doprint on the SAME printer instance, threading printer state (`_print_level`, `_context`, `_settings`, Permutation deprecation warn-once). If any element's rendering were state- or position-dependent, the model would diverge. Attacked this directly:
- Purity, per-element: rebuilt each container from a FRESH ReprPrinter() per element (a STRICTLY STRONGER purity check than reusing one printer) and compared byte-exact to real srepr(container) over the same live object (so iteration order matches). Boundary catalogue of 109 checks over Symbol/Integer/Rational/Float(incl. 30- and 60-digit precision)/Dummy/Wild/Function/sin/pi/E/oo/I/NaN/BooleanTrue/False/EmptySet/Reals/Integers/Tuple/tuple/list/str/frozenset/FiniteSet/Matrix/assumption-carrying Symbols in key, value, and member position: 0 mismatches.
- Shared-instance vs fresh-instance: rendering all elements through one shared ReprPrinter gave byte-identical output to fresh-per-element for Float pairs, Dummy pairs, and Permutation pairs (the warn-once candidate). 0 divergences -> doprint is position/state independent here, so collapsing it to one pure elemRepr is sound.
- Same element in both key and value position ({e: e}) for Float/Dummy/Permutation/Integer: no order sensitivity.
- Determinism: repeated srepr of the same object stable.
- Printer SETTINGS sensitivity: {}, perm_cyclic True/False, order lex/none/old, over dict/set/Permutation/nested/empty collections -> 0 mismatches. Corroborates mapping.md's 'flag deps: none' (dispatch keys on the MRO, not on any setting).
- Randomized differential fuzz, seed 19346, 120,000 draws (60,040 dicts / 59,960 sets) over nested dict/set/list/Tuple values, mixed sympy+native atoms, depth<=2: 0 mismatches.
- Bundle's own conformance_check.py against the real patched tree: 'conformance OK (120014 checks, 0 disagreements)', exit 0.
- F2P ground truth reproduced against real patched repo: srepr({})=='{}', srepr({x:y})=="{Symbol('x'): Symbol('y')}", srepr({x:{y:z}}) nests, srepr(set())=='set()', srepr({x,y}) is a brace-wrapped ', '-join. All match the spec.
- String.intercalate == Python ', '.join checked in Lean by native_decide for arity 0/1/2/3, incl. the empty case giving '{}' and an element whose own rendering CONTAINS ', ' (not re-split).
- Dispatch scope: dict/set SUBCLASSES (OrderedDict, defaultdict, and user dict/set subclasses) still route to `_print_dict`/`_print_set` via the MRO walk and match the model. frozenset correctly does NOT route to `_print_set` (falls to emptyPrinter -> 'frozenset({x})'), so it is outside the modeled domain and not a counterexample.

**ONE BOUNDARY CASE EXAMINED AND REJECTED AS A DEFECT.** The spec's set empty-guard is `elems.isEmpty` (length-based) while the real patch writes `if not expr` (truthiness). I constructed a pathological set subclass overriding `__bool__` to contradict `__len__`: class LyingSet(set) with `__bool__` -> False holding {x,y} gives real 'set()' vs model "{Symbol('y'), Symbol('x')}", and a TruthyEmpty() gives real '{}' vs model 'set()'. I do NOT report this as unfaithfulness, for three independent reasons:

(1) it is not representable in the model at all -- the Lean input is just `elems : List SymExpr`, with no separate truthiness channel, so per mapping.md's bijection ('a set enumerated in iteration order') such an object is OUTSIDE the abstraction's domain rather than a point of disagreement inside it;

(2) for every builtin dict/set -- the entire modeled domain -- truthiness is exactly nonemptiness, verified: `set` defines `__len__` and has NO `__bool__` in its `__dict__`, so bool(s) == (len(s)>0) identically, checked over empty/1/3-element sets and dicts;

(3) no such lying subclass exists in sympy. Reporting it would condemn a correct spec on an input the bijection does not cover. Note the dict side has no exposure at all: the patch's `_print_dict` has no emptiness guard (the empty dict falls out of the join as '{}'), matching the spec unconditionally.

**NOT-TOO-STRONG ASSESSMENT.** The spec pins exactly what the patch pins and no more: the postcondition is a structural string identity (delimited, ', '-joined element renderings; 'set()' for the empty collection; '{}' for the empty mapping) with the element renderer left OPAQUE. Because elemRepr is an opaque carrier appearing identically in spec and impl, the spec asserts no property of srepr's per-element output -- it cannot over-constrain the recursive renderer. The only discriminating content is (a) which renderer wraps each element and (b) the empty-set literal, which is precisely the patch delta (G-DIFF: prepatch fails on both). Spec is neither stronger nor weaker than the real post-patch callee on the modeled domain.

**VERDICT:** FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION review of sympy__sympy-19346 (lean). No relaxation claim present: `find -iname '*RELAX*'` in the bundle returns nothing and meta.json has no `relaxed_leakage` key (keys: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins, pbt_audit), so this is a straight leakage judgement, not an inherited disposition.

### WHAT I MEASURED (all re-run myself, not read off verdict.md):
1. Spec region integrity: `markers.spec_view(Solution.lean, get_backend('lean'))` sha256 = 2bcfc816e112a89a2d8b096fb72e55e51d371b00114c3d5984fd52eebc66a1d9, byte-identical to meta.json region_hashes.spec_view. `markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True` -> the spec region is byte-identical across the pre/post pair, so the prepatch cannot have been weakened to make the spec pass.
2. Proof genuineness: scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms` -> 'correct_dictRepr depends on axioms: [propext, Quot.sound]' and 'correct_setRepr depends on axioms: [propext, Quot.sound]'. No sorryAx.
3. Load-bearing check (the strip-the-narration test in the direction that matters here): scripts/lean_verify.sh Solution_prepatch.lean FAILS with exactly the two discriminating goals -- `nativeRepr x.1 ++ ": " ++ nativeRepr x.2` vs `elemRepr p.1 ++ ": " ++ elemRepr p.2`, and `"{" ++ ... nativeRepr ... "}"` vs `if elems.isEmpty then "set()" else ...`. So the spec's two discriminating clauses (every element through the recursive canonical renderer; the dedicated empty-collection literal) are genuinely load-bearing, i.e. the spec is not vacuous and G-DIFF's recorded pass is sound as re-derived, not just stamped.
4. Lexical screen re-run: `leakage.screen(Solution.lean, lean_backend, patch.diff, instance.problem_statement, instance.test_patch)` -> passed=True, hard_failures=[], warnings=[]. Confirms meta G-LEAK 'failures: []'.
5. Manual edit-localization sweep over the 96-line spec view: NO patched file path (`sympy/printing/repr.py`), NO patched module path, NO patched symbols (`_print_dict`, `_print_set`, `ReprPrinter`, `doprint`, `reprify`, `srepr`, `emptyPrinter`), NO diff markers, NO verbatim gold-patch line (checked normalized against every +/- line of patch.diff), no bug/fix narration. Modeling vocabulary is fully abstract: 'mapping' / 'unordered collection' / 'canonical representation', opaque SymExpr / elemRepr / nativeRepr. Only lexical overlap with the repo is the generic English 'symbolic-expression', and 'Symbol' is itself already in the public problem_statement.

SEMANTIC (beyond-problem_statement) ANALYSIS -- the part a lexical gate cannot do. The public problem_statement already (a) shows list/tuple rendering each element canonically (`[Symbol('x'), Symbol('y')]`), (b) shows dict and set rendering elements NON-canonically (`srepr({x, y})` -> `{x, y}`, `srepr({x: y})` -> `{x: y}`), and (c) names dict and set as the two broken containers. So each discriminating clause in the spec view is publicly derivable:
- 'each contained element rendered through the recursive canonical renderer, not any other textual conversion' == the list/tuple-vs-dict/set contrast shown verbatim in the statement;
- brace delimiters, `", "` separator, and `"%s: %s"`-style `key: value` entry shape == literally visible in the statement's own buggy outputs `{x, y}` / `{x: y}`;
- `nativeRepr`'s docstring ('element's own plain textual form, does not recurse') describes exactly the pre-patch behaviour the statement exhibits; it is declared but never referenced by either postcondition, so it adds no information;
- the empty cases are the only content not literally in the statement. `"{}"` for the empty mapping is Python's own dict repr. `"set()"` for the empty collection is forced by the round-trip requirement `eval(srepr(expr)) == expr` stated in the repo's OWN module docstring at base_commit (sympy/printing/repr.py:5, checked in the worktree at 94fb720696) -- `"{}"` would eval back to a dict, so any correct answer must special-case it. That is a solver-derivable consequence of a public requirement, not edit-localization: it does not reveal WHERE to edit, which class/method to add, or how the printer dispatches.
The spec view therefore pins required observable behaviour (which is its job -- the consumer must supply impl+proof) without handing over the gold patch's location or shape. The gold edit's actual content that a leak would give away -- 'add `_print_dict` and `_print_set` methods to ReprPrinter in sympy/printing/repr.py after `_print_list`, using `self.doprint` / `self.reprify`' -- is absent in every particular.

**ADVERSARIAL/INTEGRITY CHECK ON THE BUNDLE ITSELF:** I grepped Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md, axiom_check.py, conformance_check.py and meta.json for any text addressing a panel/auditor or prescribing a verdict ('you must submit', 'the honest verdict', 'record as', 'NO-LEAKAGE'/'LEAKAGE' directives, 'panel', 'reviewer'): no hits in any authored spec/refinement/mapping file. meta.json/verdict.md do contain prior recorded G-PANEL-3 role text with a NO-LEAKAGE string, but that is the gate ledger of a previous run, not an instruction aimed at me, and I did not rely on it -- every claim above is from a command I ran in this session. Nothing in the bundle attempted to dictate this verdict.

**VERDICT:** NO-LEAKAGE. Facet re-confirmed: the spec view's discriminating content (canonical recursive element rendering + empty-collection literals) is fully covered by the public problem_statement plus the repo's own stated eval-round-trip contract, and carries zero repo edit-localization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
