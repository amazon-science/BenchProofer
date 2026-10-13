# P2 adversarial audit — sympy__sympy-24539

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 14 same-spec wrong impls attacked; 7 closed with clean axioms; ALL 7 faithful patches were materialized and RESOLVED under the official harness (run_resolve). No verify⇏ correct witness survives.

MOST IMPORTANT RESULT — the prior pass's break is REPAIRED. atk_14.lean re-encodes the recorded counterexample p8b (SYMBOL-COLLAPSE: rebuild every generator as a named symbol from its name, which crashed on `Pi` in the real repo with AttributeError). Under the CURRENT Solution.lean it NO LONGER VERIFIES (exit 1), failing on refine_1/refine_2 with goal `exprFromDict d (List.map (fun s => Symb.named ...) ringSymbols) = exprFromDict d ringSymbols`. The repair was exactly the one verdict.md suggested: `Symb` is now an INDUCTIVE with a nameless `other (tag : Nat)` case instead of a one-field `{name : String}` structure, so `Symb.mk s.name = s` is no longer a theorem and the eta-inverse the old attack exploited does not exist. The recorded meta.json G-EQ `fail` and G-PANEL-1 `fail` are STALE with respect to this Solution.lean.

The residual model coarsenings I found are all UNOBSERVABLE to the oracle, verified by instrumentation rather than argument. I patched the real `as_expr` to log every coefficient type, monomial and generator across the whole oracle suite (all 64 tests of test_rings.py, F2P + 62 P2P): `as_expr` is only ever reached with INTEGER coefficients (One/NegativeOne/Integer 3/Integer 7), plain commutative `Symbol`s (x,y,z,u,v,w) and `Pi`. No Rational, no Float, no Dummy, no assumption-carrying generator ever reaches it. So `TermDict.coeff : Int` and the `named`/`other` carrier are faithful ON THE ORACLE'S REACHABLE DOMAIN, and the carrier-collapse attacks that diverge on unreachable inputs (atk_2 on Dummy/assumptions, atk_10 on Rational/Float) cannot be refuted — and correctly resolve.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -89,10 +89,10 @@
     (d : TermDict) (ngens : Nat) (ringSymbols symbols : List Symb) :
     Except Unit SymExpr := Id.run do
   let mut gens := symbols
-  if symbols.isEmpty then
+  if ¬ symbols.isEmpty ∧ symbols.length ≠ ngens then
+    return .error ()
+  else
     gens := ringSymbols
-  else if symbols.length ≠ ngens then
-    return .error ()
   return .ok (exprFromDict d gens)
 -- impl-end
 
@@ -102,12 +102,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,10 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict d (gens.map (fun s =>
+    match s with
+    | .named n => Symb.named n
+    | .other t => Symb.other t)))
 -- impl-end
 
 -- proof-start
@@ -102,12 +105,18 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  have hf : ∀ s : Symb,
+      (match s with | .named n => Symb.named n | .other t => Symb.other t) = s := by
+    intro s; cases s <;> rfl
+  have hid : ∀ l : List Symb,
+      (l.map (fun s => match s with | .named n => Symb.named n | .other t => Symb.other t)) = l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons a t ih => rw [List.map_cons, ih, hf]
+  simp only [Id.run, bind, pure, hid]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h, hid]
+  · intro h1 h2; simp [h1, h2, hid]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,7 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (SymExpr.mk (exprFromDict d gens).rep)
 -- impl-end
 
 -- proof-start
@@ -102,12 +102,12 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  have heta : ∀ e : SymExpr, SymExpr.mk e.rep = e := by
+    intro e; rfl
+  simp only [Id.run, bind, pure, heta]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h, heta]
+  · intro h1 h2; simp [h1, h2, heta]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,9 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict
+    { entries := d.entries.map (fun mc =>
+        (mc.1, if 0 ≤ mc.2 then (mc.2.natAbs : Int) else -(mc.2.natAbs : Int))) } gens)
 -- impl-end
 
 -- proof-start
@@ -102,12 +104,24 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  have hc : ∀ c : Int,
+      (if 0 ≤ c then (c.natAbs : Int) else -(c.natAbs : Int)) = c := by
+    intro c
+    by_cases hcc : 0 ≤ c
+    · simp only [hcc, if_true]; omega
+    · simp only [hcc, if_false]; omega
+  have hmap : ∀ l : List (List Nat × Int),
+      l.map (fun mc => (mc.1, if 0 ≤ mc.2 then (mc.2.natAbs : Int) else -(mc.2.natAbs : Int))) = l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons a t ih => rw [List.map_cons, ih, hc]
+  have hd : ({ entries := d.entries.map (fun mc =>
+      (mc.1, if 0 ≤ mc.2 then (mc.2.natAbs : Int) else -(mc.2.natAbs : Int))) } : TermDict) = d := by
+    rw [hmap]
+  simp only [Id.run, bind, pure, hd]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h, hd]
+  · intro h1 h2; simp [h1, h2, hd]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -91,7 +91,7 @@
   let mut gens := symbols
   if symbols.isEmpty then
     gens := ringSymbols
-  else if symbols.length ≠ ngens then
+  else if ngens < symbols.length then
     return .error ()
   return .ok (exprFromDict d gens)
 -- impl-end
@@ -102,12 +102,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -91,8 +91,6 @@
   let mut gens := symbols
   if symbols.isEmpty then
     gens := ringSymbols
-  else if symbols.length ≠ ngens then
-    return .error ()
   return .ok (exprFromDict d gens)
 -- impl-end
 
@@ -102,12 +100,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,6 +93,8 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
+  else if 3 < ngens then
+    gens := ringSymbols
   return .ok (exprFromDict d gens)
 -- impl-end
 
@@ -102,12 +104,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -90,7 +90,7 @@
     Except Unit SymExpr := Id.run do
   let mut gens := symbols
   if symbols.isEmpty then
-    gens := ringSymbols
+    gens := ringSymbols.reverse
   else if symbols.length ≠ ngens then
     return .error ()
   return .ok (exprFromDict d gens)
@@ -102,12 +102,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,6 +93,8 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
+  else
+    gens := symbols.take ngens
   return .ok (exprFromDict d gens)
 -- impl-end
 
@@ -102,12 +104,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; subst h2; simp [h1, List.take_length]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,8 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict
+    { entries := d.entries.map (fun mc => (mc.1, ((mc.2.toNat : Int) - ((-mc.2).toNat : Int)))) } gens)
 -- impl-end
 
 -- proof-start
@@ -102,12 +103,19 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  have hc : ∀ c : Int, ((c.toNat : Int) - ((-c).toNat : Int)) = c := by
+    intro c; omega
+  have hmap : ∀ l : List (List Nat × Int),
+      l.map (fun mc => (mc.1, ((mc.2.toNat : Int) - ((-mc.2).toNat : Int)))) = l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons a t ih => rw [List.map_cons, ih, hc]
+  have hd : ({ entries := d.entries.map (fun mc => (mc.1, ((mc.2.toNat : Int) - ((-mc.2).toNat : Int)))) } : TermDict) = d := by
+    rw [hmap]
+  simp only [Id.run, bind, pure, hd]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h, hd]
+  · intro h1 h2; simp [h1, h2, hd]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,8 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict
+    { entries := d.entries.map (fun mc => (mc.1.map (fun e => e - 0 + 0), mc.2)) } gens)
 -- impl-end
 
 -- proof-start
@@ -102,12 +103,22 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  have he : ∀ e : Nat, e - 0 + 0 = e := by intro e; omega
+  have hm : ∀ l : List Nat, l.map (fun e => e - 0 + 0) = l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons a t ih => rw [List.map_cons, ih, he]
+  have hmap : ∀ l : List (List Nat × Int),
+      l.map (fun mc => (mc.1.map (fun e => e - 0 + 0), mc.2)) = l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons a t ih => rw [List.map_cons, ih, hm]
+  have hd : ({ entries := d.entries.map (fun mc => (mc.1.map (fun e => e - 0 + 0), mc.2)) } : TermDict) = d := by
+    rw [hmap]
+  simp only [Id.run, bind, pure, hd]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h, hd]
+  · intro h1 h2; simp [h1, h2, hd]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,8 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict
+    { entries := d.entries.filter (fun mc => 0 ≤ mc.1.length) } gens)
 -- impl-end
 
 -- proof-start
@@ -102,12 +103,18 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  have hfil : ∀ l : List (List Nat × Int), l.filter (fun mc => 0 ≤ mc.1.length) = l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons a t ih =>
+      rw [List.filter_cons, ih]
+      simp only [Nat.zero_le, decide_true, if_true]
+  have hd : ({ entries := d.entries.filter (fun mc => 0 ≤ mc.1.length) } : TermDict) = d := by
+    rw [hfil]
+  simp only [Id.run, bind, pure, hd]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h, hd]
+  · intro h1 h2; simp [h1, h2, hd]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,7 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict d (if 4 ≤ ngens then gens.reverse else gens))
 -- impl-end
 
 -- proof-start
@@ -102,12 +102,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,7 +93,8 @@
     gens := ringSymbols
   else if symbols.length ≠ ngens then
     return .error ()
-  return .ok (exprFromDict d gens)
+  return .ok (exprFromDict d (gens.map (fun s =>
+    Symb.named (match s with | .named n => n | .other t => toString t))))
 -- impl-end
 
 -- proof-start
@@ -102,12 +103,10 @@
       problem_spec_asExpr d ngens ringSymbols symbols
         (implementation_asExpr d ngens ringSymbols symbols) := by
   intro d ngens ringSymbols symbols
-  unfold implementation_asExpr
+  unfold problem_spec_asExpr implementation_asExpr
+  simp only [Id.run, bind, pure]
   refine ⟨?_, ?_, ?_⟩
-  · intro h
-    simp only [h, Id.run, if_true, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, h2, ne_eq, not_true_eq_false, if_false, bind, pure]
-  · intro h1 h2
-    simp only [Id.run, if_neg h1, if_pos h2, bind, pure]
+  · intro h; simp [h]
+  · intro h1 h2; simp [h1, h2]
+  · intro h1 h2; simp [h1, h2]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base_commit worktree at .../wt @ 193e3825645d93c73e31cdceb6d742cc6919624d. All 14 attacks + ctrl.lean are byte-identical in spec: same_spec == True for every one (checked with swebench_unified.markers.same_spec, lean tables). Attack verifications and resolve runs were launched as concurrent background jobs, ≤4 at a time.

VERIFY — `bash scripts/lean_verify.sh <f>` from repo root:
  ctrl.lean    EXIT 0  <= POSITIVE CONTROL, gold impl verifies
  atk_1.lean   EXIT 1  <= PREPATCH BUG REPRODUCED
  atk_2.lean   EXIT 0     atk_3.lean  EXIT 0     atk_4.lean  EXIT 0
  atk_5.lean   EXIT 1     atk_6.lean  EXIT 1     atk_7.lean  EXIT 1
  atk_8.lean   EXIT 1     atk_9.lean  EXIT 0     atk_10.lean EXIT 0
  atk_11.lean  EXIT 0     atk_12.lean EXIT 0     atk_13.lean EXIT 1
  atk_14.lean  EXIT 1  <= PRIOR COUNTEREXAMPLE, NOW REJECTED

PREPATCH (atk_1, control-flow-effect / the literal pre-patch): `if ¬ symbols.isEmpty ∧ symbols.length ≠ ngens then return .error () else gens := ringSymbols`. Fails at line 109 with EXACTLY the goal refinement.md's G-DIFF section predicts: `⊢ exprFromDict d ringSymbols = exprFromDict d symbols` (clause 2 unprovable). Matches FAIL_TO_PASS test_PolyElement_as_expr.

SPEC CORRECTLY REJECTS (exit 1) — these are the legs that hold:
  atk_5  boundary: reject only when `ngens < symbols.length` (admits too-few)
  atk_6  ungrounded/no-reject: drop the error branch entirely
  atk_7  partial-domain: correct only for ngens ≤ 3, else use ringSymbols
  atk_8  control-flow-effect: `ringSymbols.reverse` on the empty-caller branch
  atk_13 partial-domain order: reverse gens only when 4 ≤ ngens
  atk_14 the prior pass's p8b symbol-collapse (see counterexample)
The rejections of atk_7/atk_13 are what makes this spec strong: it pins `exprFromDict d gens` for ALL ngens, so no partial-domain or order attack survives.

CLOSING ATTACKS — `#print axioms correct_asExpr` appended and re-elaborated (files atk_N_ax.lean, all AXEXIT 0). STANDARD_AXIOMS = (propext, Classical.choice, Quot.sound); no `axiom _prop` is declared, so allowed == STANDARD_AXIOMS. Every result is a SUBSET — all clean, no sorryAx:
  atk_2  [propext]              atk_3  [propext]
  atk_4  [propext, Quot.sound]  atk_9  [propext]
  atk_10 [propext, Quot.sound]  atk_11 [propext, Quot.sound]
  atk_12 [propext]

RESOLVE — every one of the 7 clean-axiom attacks had its faithful patch MATERIALIZED and EXECUTED through the official harness (`run_resolve('sympy__sympy-24539', patch, timeout=2400, retries=2)`, driver resolve_one.py, results in resolve_<n>.json).

Each diff was checked with `git apply --check` in the base_commit worktree first (all OK), and pre-screened against the real test_rings.py + test_patch locally (all 64 passed) before docker: atk_2  (carrier: rebuild named gens via Symbol(g.name))         resolved=True  F2P 1/1  P2P 62/62 atk_3  (carrier: SymExpr rebuilt from its String rep, sstr/sympify) resolved=True  F2P 1/1  P2P 62/62 atk_4  (carrier: coeff -> `sign*abs`(coeff))                       resolved=True  F2P 1/1  P2P 62/62 atk_9  (echo: symbols[:ngens] truncation)                        resolved=True  F2P 1/1  P2P 62/62 atk_10 (carrier: coeff -> toNat-pair round trip)                 resolved=True  F2P 1/1  P2P 62/62 atk_11 (carrier: exponent vector -> max(e-0,0)+0 round trip)      resolved=True  F2P 1/1  P2P 62/62 atk_12 (term dict filtered on len(monom) >= 0)                    resolved=True  F2P 1/1  P2P 62/62 All completed=True, patch_successfully_applied=True, attempts=1, flaky=False, zero P2P failures. No attack breaks the spec.

ORACLE LIVENESS (this is what makes 7/7 resolved a real signal and not a dead oracle). neg_control.diff applies the PREPATCH behaviour (atk_1's Lean impl, gold error message so only the control flow differs) at base_commit:
  neg_control  resolved=FALSE  completed=True  attempts=3 (consistent, not flaky)
               FAIL_TO_PASS 0/1, failure=['test_PolyElement_as_expr']; PASS_TO_PASS 62/62
So the harness DOES refute a wrong `as_expr` on this instance, on the same lane, with the same driver.

INSTRUMENTATION (the evidence behind the coarsening argument).  is a gold-patched + test-patched copy whose `as_expr` logs every coefficient/monomial/generator it sees; the full suite was run (64 passed) and instr.log contains only:
  COEFF: One 1 (x10), Integer 3 (x3), NegativeOne -1 (x2), Integer 7 (x2)  -- integers ONLY
  GEN:   Pi pi (x8); Symbol x/y/z/u/v/w, assumptions0 == [('commutative', True)] ONLY
No Rational/Float/Dummy/assumption-carrying input reaches the modeled surface anywhere in the oracle's 63 tests. `Pi` appears, and is exactly the `Symb.other` case the repaired carrier now models — which is why atk_14 can no longer hide.

REFINEMENT.MD AUDIT — clean. 5 legs, tags 2xR + 2xR/I + 1xA-reference, NO kind-3, no hedging vocabulary (grep for kind-3/unmodeled/assumed/approximate: none). The single A-leg is `return .ok (exprFromDict d gens)` <-> `return expr_from_dict(self.as_expr_dict(), *symbols)`, tagged A-reference. Correspondence HOLDS: (a) the patch genuinely does not touch expr_from_dict (polyutils.py:375-387 — confirmed the gold patch.diff only edits rings.py as_expr); (b) no `axiom _prop` is declared, so no property is consumed and G-AX's skip stub is honest — the proof uses `opaque exprFromDict` purely as an uninterpreted function, and the spec's only claim is WHICH list reaches it; (c) G-CONF leaves it as the REAL callee — I read conformance_check.py and its shadow_outcome invokes `f.as_expr(*gens)` on the shadow-selected list, so the real expr_from_dict is on both sides of the 120005 checks. mapping.md's line citations verified at base_commit: as_expr @ rings.py:618-624, `_parse_symbols` @ rings.py:181-192 (does accept `isinstance(symbols, Expr)`, so nameless generators are real), as_expr_dict @ rings.py:626-628.

**STALE RECORD.** meta.json gates.G-EQ = fail and G-PANEL-1 = fail both cite p8b, whose exploit (`Symb.mk s.name = s` by structure eta) is dead under the current inductive `Symb`; source_digests is null so the record cannot self-invalidate. Recommend re-stamping G-EQ/G-PANEL-1 against Solution.lean sha256 e5842d1bafe842d0f5af4f5ccdf32dbace983ec3e53c8b43b81f6a276d06a49d.

RESIDUAL RISK (advisory, not a break). The spec is tight on the A-leg only up to provable-identity maps on the carriers; `TermDict.coeff : Int` remains coarser than the repo's arbitrary-Expr coefficients, so a QQ/RR/EX-coefficient divergence is expressible in the model but unobservable to this instance's tests (atk_10 is the mechanized witness that it verifies AND resolves). That is a limit of the oracle's test set, not a defect in this spec: no same-spec impl can be BOTH provable and wrong on any input the F2P/P2P lanes actually exercise. Hardening would mean making the coefficient carrier opaque, but that buys no additional refutation power here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 14 same-spec wrong impls attacked; 7 closed with clean axioms; ALL 7 faithful patches were materialized and RESOLVED under the official harness (run_resolve). No verify⇏ correct witness survives.

MOST IMPORTANT RESULT — the prior pass's break is REPAIRED. atk_14.lean re-encodes the recorded counterexample p8b (SYMBOL-COLLAPSE: rebuild every generator as a named symbol from its name, which crashed on `Pi` in the real repo with AttributeError). Under the CURRENT Solution.lean it NO LONGER VERIFIES (exit 1), failing on refine_1/refine_2 with goal `exprFromDict d (List.map (fun s => Symb.named ...) ringSymbols) = exprFromDict d ringSymbols`. The repair was exactly the one verdict.md suggested: `Symb` is now an INDUCTIVE with a nameless `other (tag : Nat)` case instead of a one-field `{name : String}` structure, so `Symb.mk s.name = s` is no longer a theorem and the eta-inverse the old attack exploited does not exist. The recorded meta.json G-EQ `fail` and G-PANEL-1 `fail` are STALE with respect to this Solution.lean.

The residual model coarsenings I found are all UNOBSERVABLE to the oracle, verified by instrumentation rather than argument. I patched the real `as_expr` to log every coefficient type, monomial and generator across the whole oracle suite (all 64 tests of test_rings.py, F2P + 62 P2P): `as_expr` is only ever reached with INTEGER coefficients (One/NegativeOne/Integer 3/Integer 7), plain commutative `Symbol`s (x,y,z,u,v,w) and `Pi`. No Rational, no Float, no Dummy, no assumption-carrying generator ever reaches it. So `TermDict.coeff : Int` and the `named`/`other` carrier are faithful ON THE ORACLE'S REACHABLE DOMAIN, and the carrier-collapse attacks that diverge on unreachable inputs (atk_2 on Dummy/assumptions, atk_10 on Rational/Float) cannot be refuted — and correctly resolve.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base_commit worktree at .../wt @ 193e3825645d93c73e31cdceb6d742cc6919624d. All 14 attacks + ctrl.lean are byte-identical in spec: same_spec == True for every one (checked with swebench_unified.markers.same_spec, lean tables). Attack verifications and resolve runs were launched as concurrent background jobs, ≤4 at a time.

VERIFY — `bash scripts/lean_verify.sh <f>` from repo root:
  ctrl.lean    EXIT 0  <= POSITIVE CONTROL, gold impl verifies
  atk_1.lean   EXIT 1  <= PREPATCH BUG REPRODUCED
  atk_2.lean   EXIT 0     atk_3.lean  EXIT 0     atk_4.lean  EXIT 0
  atk_5.lean   EXIT 1     atk_6.lean  EXIT 1     atk_7.lean  EXIT 1
  atk_8.lean   EXIT 1     atk_9.lean  EXIT 0     atk_10.lean EXIT 0
  atk_11.lean  EXIT 0     atk_12.lean EXIT 0     atk_13.lean EXIT 1
  atk_14.lean  EXIT 1  <= PRIOR COUNTEREXAMPLE, NOW REJECTED

PREPATCH (atk_1, control-flow-effect / the literal pre-patch): `if ¬ symbols.isEmpty ∧ symbols.length ≠ ngens then return .error () else gens := ringSymbols`. Fails at line 109 with EXACTLY the goal refinement.md's G-DIFF section predicts: `⊢ exprFromDict d ringSymbols = exprFromDict d symbols` (clause 2 unprovable). Matches FAIL_TO_PASS test_PolyElement_as_expr.

SPEC CORRECTLY REJECTS (exit 1) — these are the legs that hold:
  atk_5  boundary: reject only when `ngens < symbols.length` (admits too-few)
  atk_6  ungrounded/no-reject: drop the error branch entirely
  atk_7  partial-domain: correct only for ngens ≤ 3, else use ringSymbols
  atk_8  control-flow-effect: `ringSymbols.reverse` on the empty-caller branch
  atk_13 partial-domain order: reverse gens only when 4 ≤ ngens
  atk_14 the prior pass's p8b symbol-collapse (see counterexample)
The rejections of atk_7/atk_13 are what makes this spec strong: it pins `exprFromDict d gens` for ALL ngens, so no partial-domain or order attack survives.

CLOSING ATTACKS — `#print axioms correct_asExpr` appended and re-elaborated (files atk_N_ax.lean, all AXEXIT 0). STANDARD_AXIOMS = (propext, Classical.choice, Quot.sound); no `axiom _prop` is declared, so allowed == STANDARD_AXIOMS. Every result is a SUBSET — all clean, no sorryAx:
  atk_2  [propext]              atk_3  [propext]
  atk_4  [propext, Quot.sound]  atk_9  [propext]
  atk_10 [propext, Quot.sound]  atk_11 [propext, Quot.sound]
  atk_12 [propext]

RESOLVE — every one of the 7 clean-axiom attacks had its faithful patch MATERIALIZED and EXECUTED through the official harness (`run_resolve('sympy__sympy-24539', patch, timeout=2400, retries=2)`, driver resolve_one.py, results in resolve_<n>.json).

Each diff was checked with `git apply --check` in the base_commit worktree first (all OK), and pre-screened against the real test_rings.py + test_patch locally (all 64 passed) before docker: atk_2  (carrier: rebuild named gens via Symbol(g.name))         resolved=True  F2P 1/1  P2P 62/62 atk_3  (carrier: SymExpr rebuilt from its String rep, sstr/sympify) resolved=True  F2P 1/1  P2P 62/62 atk_4  (carrier: coeff -> `sign*abs`(coeff))                       resolved=True  F2P 1/1  P2P 62/62 atk_9  (echo: symbols[:ngens] truncation)                        resolved=True  F2P 1/1  P2P 62/62 atk_10 (carrier: coeff -> toNat-pair round trip)                 resolved=True  F2P 1/1  P2P 62/62 atk_11 (carrier: exponent vector -> max(e-0,0)+0 round trip)      resolved=True  F2P 1/1  P2P 62/62 atk_12 (term dict filtered on len(monom) >= 0)                    resolved=True  F2P 1/1  P2P 62/62 All completed=True, patch_successfully_applied=True, attempts=1, flaky=False, zero P2P failures. No attack breaks the spec.

ORACLE LIVENESS (this is what makes 7/7 resolved a real signal and not a dead oracle). neg_control.diff applies the PREPATCH behaviour (atk_1's Lean impl, gold error message so only the control flow differs) at base_commit:
  neg_control  resolved=FALSE  completed=True  attempts=3 (consistent, not flaky)
               FAIL_TO_PASS 0/1, failure=['test_PolyElement_as_expr']; PASS_TO_PASS 62/62
So the harness DOES refute a wrong `as_expr` on this instance, on the same lane, with the same driver.

INSTRUMENTATION (the evidence behind the coarsening argument).  is a gold-patched + test-patched copy whose `as_expr` logs every coefficient/monomial/generator it sees; the full suite was run (64 passed) and instr.log contains only:
  COEFF: One 1 (x10), Integer 3 (x3), NegativeOne -1 (x2), Integer 7 (x2)  -- integers ONLY
  GEN:   Pi pi (x8); Symbol x/y/z/u/v/w, assumptions0 == [('commutative', True)] ONLY
No Rational/Float/Dummy/assumption-carrying input reaches the modeled surface anywhere in the oracle's 63 tests. `Pi` appears, and is exactly the `Symb.other` case the repaired carrier now models — which is why atk_14 can no longer hide.

REFINEMENT.MD AUDIT — clean. 5 legs, tags 2xR + 2xR/I + 1xA-reference, NO kind-3, no hedging vocabulary (grep for kind-3/unmodeled/assumed/approximate: none). The single A-leg is `return .ok (exprFromDict d gens)` <-> `return expr_from_dict(self.as_expr_dict(), *symbols)`, tagged A-reference. Correspondence HOLDS: (a) the patch genuinely does not touch expr_from_dict (polyutils.py:375-387 — confirmed the gold patch.diff only edits rings.py as_expr); (b) no `axiom _prop` is declared, so no property is consumed and G-AX's skip stub is honest — the proof uses `opaque exprFromDict` purely as an uninterpreted function, and the spec's only claim is WHICH list reaches it; (c) G-CONF leaves it as the REAL callee — I read conformance_check.py and its shadow_outcome invokes `f.as_expr(*gens)` on the shadow-selected list, so the real expr_from_dict is on both sides of the 120005 checks. mapping.md's line citations verified at base_commit: as_expr @ rings.py:618-624, `_parse_symbols` @ rings.py:181-192 (does accept `isinstance(symbols, Expr)`, so nameless generators are real), as_expr_dict @ rings.py:626-628.

**STALE RECORD.** meta.json gates.G-EQ = fail and G-PANEL-1 = fail both cite p8b, whose exploit (`Symb.mk s.name = s` by structure eta) is dead under the current inductive `Symb`; source_digests is null so the record cannot self-invalidate. Recommend re-stamping G-EQ/G-PANEL-1 against Solution.lean sha256 e5842d1bafe842d0f5af4f5ccdf32dbace983ec3e53c8b43b81f6a276d06a49d.

RESIDUAL RISK (advisory, not a break). The spec is tight on the A-leg only up to provable-identity maps on the carriers; `TermDict.coeff : Int` remains coarser than the repo's arbitrary-Expr coefficients, so a QQ/RR/EX-coefficient divergence is expressible in the model but unobservable to this instance's tests (atk_10 is the mechanized witness that it verifies AND resolves). That is a limit of the oracle's test set, not a defect in this spec: no same-spec impl can be BOTH provable and wrong on any input the F2P/P2P lanes actually exercise. Hardening would mean making the coefficient carrier opaque, but that buys no additional refutation power here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK LANE:** faithfulness-break (spec too strong / drifts from real repo behavior). Result: no divergence found; spec is faithful to the patched reference.

### REFERENCE SETUP (verified, not assumed)
- Worktree at base_commit 193e382564; `git diff` is byte-for-byte the bundle patch.diff (as_expr reordered to `if not symbols: symbols = self.ring.symbols / elif len(symbols) != ngens: raise ValueError`). Confirmed via inspect.getsource that 'Wrong number of symbols' is present, i.e. I compared against the POST-patch behavior, not the base version. Base commit used only for the untouched callee expr_from_dict (polyutils.py:375-387), which the patch does not touch.

### DIFFERENTIAL PROBE (model vs real patched as_expr)
Modeled the three spec clauses in Python and compared against real f.as_expr(*cs) outputs:
- Probe 1: 140 cases, nvars 0..3, ZZ, polys incl. R.zero/R.one, caller lists of length ngens-1/ngens/ngens+1/ngens+2, incl. exactly-ring-symbols and a permutation of them. 0 mismatches.
- Probe 2: 41 edge cases — duplicate caller symbols ([U,U],[pi,pi]), non-Symbol generators (Integer, Rational, sin(U)), rings over NAMELESS generators PolyRing((pi,sqrt(2))) and PolyRing((sin u,cos u,E)), zero-generator ring R0 (ngens=0, symbols=()), QQ domain, same-name/different-assumption symbols. 0 real mismatches.
- Probe 3: randomized sweep, seed 24539, 7 rings x random polys x 60 random caller lists drawn from a 21-element Expr pool (pi, sqrt2, I, E, GoldenRatio, Abs, Function h(u), U+V, `U*V`, sqrt(U), assumption-variant Symbols): 2520 cases, 0 mismatches, 0 cases where either side raised a non-ValueError.
Total ~2700 differential cases, zero divergence.

### Specific over-strength hypotheses tested and refuted
1. ngens vs len(ringSymbols) independence: spec takes ngens and ringSymbols as INDEPENDENT params, so clause 1 asserts the empty-symbols result for ALL ngens. This is not too strong: real as_expr does not consult ngens at all when symbols is empty (the length check sits in the elif). Also asserted ngens == len(R.symbols) on all 7 rings constructed — invariant holds, so no reachable input separates them.
2. Python truthiness vs List.isEmpty drift: `not symbols` is TUPLE emptiness, so a FALSY ELEMENT must not be conflated with an empty tuple. Verified bool((Integer(0),)) / bool((S.false,)) / bool((S.EmptySet,)) are all True, and one-element falsy caller lists take the caller branch on both sides (0 -> ok/ok match; S.false and S.EmptySet raise identically on both sides inside the shared callee). `symbols.isEmpty` is exact.
3. Wrong-count -> Except.error (): real raises ValueError. Matched in every wrong-length case. Noted SympifyError subclasses ValueError, so the harness separated it; the one flag in probe 2 ([x,y] PolyElement args) was a harness artifact — both sides raise SympifyError inside the shared callee, and PolyElement is outside the modeled Symb type. Re-ran with symmetric exception handling: match.

### Artifact integrity
- scripts/lean_verify.sh Solution.lean -> exit 0.
- `#print axioms correct_asExpr` -> [propext] only. NO sorryAx; proof is real, matching the G-VERIFY record.
- markers.same_spec(Solution, Solution_prepatch) = True; parse_regions ok with no errors on both, regions {axioms, pure, post-conditions, impl, proof}. Spec region byte-identical, so the prepatch rival attacks the same spec.
- G-DIFF confirmed live, not asserted: Solution_prepatch.lean fails at exactly `case refine_2 ... exprFromDict d ringSymbols = exprFromDict d symbols` — clause 2, the fix. Not vacuous.
- F2P test_PolyElement_as_expr passes on the patched worktree (1 passed), and its assertions (f.as_expr()==g, f.as_expr(X,Y,Z)==g, raises(ValueError, f.as_expr(X)), R(3).as_expr()==3 for the 0-gen ring) map onto spec clauses 1/2/3/1 respectively.

### ONE GRANULARITY OBSERVATION (examined, NOT a defect — did not submit as the finding)
Symb.named collapses distinct sympy Symbols sharing a name, so Symbol('u') and Symbol('u', commutative=False) map to the same Symb. Those DO give different real outputs (`u**2` + 1 vs 1 + `u**2`, since Add ordering depends on commutativity) — 114 such string differences out of 2142 pairs, all traced to commutative=False alone. I judged this NOT a faithfulness break: exprFromDict is `opaque`, so the spec never asserts any value for it, and every clause has the form 'result = callee applied to THIS argument list'. Real as_expr passes its list straight through to the real expr_from_dict, so the square commutes on every concrete input, and refinement.md tags the callee A-reference (left as the real callee in the G-CONF shadow, no property consumed by the proof). Verified directly on a ring built over the noncommutative generator: clause 1 and clause 2 both hold concretely, and the caller list is genuinely the one used (as_expr() != as_expr(u)). The coarsening is not exploitable to make the spec assert anything false about the repo.

**CONCLUSION:** the spec's three clauses partition every input and reproduce the patched as_expr exactly on ~2700 differential inputs including nameless generators, duplicates, non-Symbol generators, zero-generator rings, and falsy elements. No diverging input exists to report. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

ATTACKER 3 (leakage / gold-reconstruction), sympy__sympy-24539/lean.

**No relaxation in play:** no RELAXED_LEAKAGE.md anywhere in the bundle (`find -iname '*RELAX*'` empty) and no `relaxed_leakage` key in meta.json (recursive key walk for 'relax'/'leak' hits only gates/G-LEAK). So this is judged as a plain strict-mode leakage review, not an inherited disposition.

### What I ran
- Projected the consumer spec view myself with swebench_unified.markers.spec_view(src, get_backend('lean')) rather than trusting meta.json: impl and proof regions are both elided to placeholders, so the view is imports + module docstring + axioms + pure + post-conditions only.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True -> the spec region is byte-identical (modulo blank lines, per spec_signature) between the gold and pre-patch carriers, so the spec was not tuned to the post-patch impl.
- scripts/lean_verify.sh Solution.lean -> exit 0. Appended `#print axioms correct_asExpr` in a mktemp copy and re-verified: "depends on axioms: [propext]" -- no sorryAx, the proof is real.
- scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, unsolved goal on `refine_2` only: `exprFromDict d ringSymbols = exprFromDict d symbols` under `h1 : ¬symbols.isEmpty`, `h2 : symbols.length = ngens`. This is the strip-the-narration control from the other direction: it localizes the entire discriminating power of the spec to post-condition clause 2. Clauses 1 (empty -> ringSymbols) and 3 (wrong count -> error) are satisfied by BOTH the pre- and post-patch control flow, so they carry no information about the edit at all.

### Leakage analysis
The public problem_statement already states all three clauses explicitly: "is supposed to let you set the symbols you want to use"; "either you pass the wrong number of symbols, and get an error message"; "or you pass the right number of symbols, and it ignores them, using `self.ring.symbols` instead", plus a worked repro showing f.as_expr(U,V,W) coming back in x,y,z. The one discriminating clause (2) is a direct transcription of the statement's own diagnosis, and docstring lines 19-21 ("a correctly-sized list of caller symbols must actually be the list used to build the expression, never silently replaced by the ring's own symbols") paraphrase the statement's "it ignores them, using self.ring.symbols instead". Nothing there exceeds the statement.

What the spec view notably does NOT reveal, and which a gold-reconstruction attack would want:
- The message-text half of the gold edit ("not enough symbols" -> "Wrong number of symbols, expected %s got %s") is absent: errors are modeled as bare `Except.error ()` with no payload.
- The structural shape of the fix (if/else -> if not symbols / elif len != ngens, i.e. hoisting the empty case ahead of the count check) is not stated. The spec is a case-partition postcondition over inputs, not a control-flow sketch; the three clauses are order-free conjuncts and admit implementations unlike the gold body.
- No file/line/symbol pointers, no diff vocabulary. Leak-vocabulary sweep over the spec view for fix/bug/patch/regress/issue/previous/before/after/now/instead of/copy/prepatch/gold/commit/github/rings.py/ValueError/"not enough"/"Wrong number"/elif/24539 returned only two false positives: "used to" inside "the list used to build" (L20) and "PR " matching "structure" (L40).
- The `Symb` two-case carrier (named/other) and the opaque `exprFromDict` are modeling of UNCHANGED surrounding code (generators are arbitrary Exprs; the callee in polyutils.py is untouched by the patch). Neither discriminates pre- from post-patch. The axioms comment "the behaviour of interest is WHICH list of symbols is handed to it" is the closest thing to a pointer, but it says exactly what the problem_statement says (ring.symbols is being substituted for the caller's), so it is not beyond-statement.

**Verdict:** NO-LEAKAGE. The spec is derivable end-to-end from the public problem_statement; the only edit-discriminating clause is the statement's own bug report.

### TWO ADJACENT OBSERVATIONS (out of scope for this gate, flagged for the record, neither affecting the verdict)
1. In-bundle text addressing an agent: Solution.lean axioms region, "No property of this callee is consumed by the proof, so no `axiom … _prop` is declared (the proof agent may add one only if it gets stuck)." This is guidance aimed at a downstream proof agent, embedded in the consumer-visible spec view. It does not instruct me how to record a verdict and it does not leak the edit, so I did not treat it as a leak, but per role instructions I report that the bundle contains agent-directed instructions inside the shipped spec text.
2. meta.json staleness: region_hashes.spec_view = 980399108de0... reproduces the version of Solution.lean at commit 1332b51f5 (the old single-field `structure Symb where name : String`), NOT the current file, whose spec_view digest is b04e34e2170480a8be59c0d46fb1f3b7eb90044f0b8aa85011164ab8ff94c39d. The axioms region was rewritten at 09:07 (commit 55d1ce591) and region_hashes were not restamped. The G-LEAK record itself IS fresh -- its sources digest e5842d1b... equals sha256(Solution.lean) as it stands now, checked_at 09:20 > mtime 09:07 -- so my NO-LEAKAGE stands on current bytes, and I re-derived the view from source rather than from the digest. The stale region_hashes are a hygiene/restamp item for the owning gate, and I also note G-EQ/G-PANEL-1 are recorded fail (spec-too-weak, p8b.lean verifies but breaks PASS_TO_PASS test_PolyElement___mul__), which is a strength question, not a leakage one.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
