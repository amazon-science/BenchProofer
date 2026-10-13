# P2 adversarial audit — django__django-12050

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no wrong impl produced a closing clean-axiom proof, so verify does NOT imply anything wrong is correct. The spec `problem_spec_resolveLookupValue value result := result = resolveSpec value` is exact structural equality to the concrete, input-grounded recursive function resolveSpec, so ANY behavioral deviation (tuple/list constructor drift, non-recursion, reordering, truncation, identity echo, scalar tamper) leaves a genuinely-false residual goal (e.g. `LV.lst (map resolveSpec xs) = LV.tup (...)`, `LV.tup (...).reverse = LV.tup (...)`, `LV.plain (n+1) = LV.plain n`) that cannot close under Lean soundness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,30 +69,28 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
   | LV.plain n => LV.plain n
   | LV.lst xs  => Id.run do
       let mut resolved : List LV := []
       for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
+        resolved := resolved ++ [(match sub with
+          | LV.expr e => resolveExpression e
+          | other     => other)]
+      return LV.tup resolved
   | LV.tup xs  => Id.run do
       let mut resolved : List LV := []
       for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
+        resolved := resolved ++ [(match sub with
+          | LV.expr e => resolveExpression e
+          | other     => other)]
       return LV.tup resolved
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
 theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
+    (g : List LV -> LV) (f : LV -> LV) (xs : List LV) (init : List LV) :
     (Id.run do
       let mut resolved : List LV := init
       for sub in xs do
@@ -111,8 +109,6 @@
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,20 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
   | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | LV.lst xs  => LV.tup (xs.map implementation_resolveLookupValue)
+  | LV.tup xs  => LV.tup (xs.map implementation_resolveLookupValue)
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +90,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,24 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
   | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | LV.lst xs  => LV.lst (xs.map (fun sub => match sub with
+      | LV.expr e => resolveExpression e
+      | other     => other))
+  | LV.tup xs  => LV.tup (xs.map (fun sub => match sub with
+      | LV.expr e => resolveExpression e
+      | other     => other))
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +94,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,20 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
   | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | LV.lst xs  => LV.lst ((xs.map implementation_resolveLookupValue).reverse)
+  | LV.tup xs  => LV.tup ((xs.map implementation_resolveLookupValue).reverse)
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +90,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,20 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
   | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | LV.lst xs  => LV.lst ((xs.map implementation_resolveLookupValue).tail)
+  | LV.tup xs  => LV.tup ((xs.map implementation_resolveLookupValue).tail)
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +90,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,17 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
-  | LV.expr e  => resolveExpression e
-  | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | v => v
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +87,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,20 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
   | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | LV.lst xs  => LV.tup (xs.map implementation_resolveLookupValue)
+  | LV.tup xs  => LV.lst (xs.map implementation_resolveLookupValue)
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +90,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,50 +69,20 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Resolve a lookup value. Expressions are resolved by the context resolver;
-scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
-the SAME kind, walking its entries in order and resolving each one recursively. -/
 def implementation_resolveLookupValue : LV → LV
   | LV.expr e  => resolveExpression e
-  | LV.plain n => LV.plain n
-  | LV.lst xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.lst resolved
-  | LV.tup xs  => Id.run do
-      let mut resolved : List LV := []
-      for sub in xs do
-        resolved := resolved ++ [implementation_resolveLookupValue sub]
-      return LV.tup resolved
+  | LV.plain n => LV.plain (n+1)
+  | LV.lst xs  => LV.lst (xs.map implementation_resolveLookupValue)
+  | LV.tup xs  => LV.tup (xs.map implementation_resolveLookupValue)
 -- impl-end
 
 -- proof-start
-/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
-desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
-final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
-theorem resolveLookupValue_loop_map
-    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
-    (Id.run do
-      let mut resolved : List LV := init
-      for sub in xs do
-        resolved := resolved ++ [f sub]
-      return g resolved) = g (init ++ xs.map f) := by
-  induction xs generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
-  | cons a as ih =>
-      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
-      simp only [ih]
-      simp
-
 theorem correct_resolveLookupValue :
     ∀ (value : LV),
       problem_spec_resolveLookupValue value
         (implementation_resolveLookupValue value) := by
   intro value
   unfold problem_spec_resolveLookupValue
-  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
-  -- element-wise IH for the collection cases.
   refine @LV.rec
     (fun v => implementation_resolveLookupValue v = resolveSpec v)
     (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
@@ -120,12 +90,10 @@
   · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · intro xs ih
-    simp only [implementation_resolveLookupValue, resolveSpec,
-      resolveLookupValue_loop_map, List.nil_append]
+    simp only [implementation_resolveLookupValue, resolveSpec]
     rw [ih]
   · rfl
   · intro head tail ih_head ih_tail
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving a lookup value to its canonical form.

A lookup value is one of four shapes:

  * an *expression* — a value that knows how to resolve itself in the current
    context; resolving the lookup value means asking it to resolve and taking
    the resolved result;
  * a *scalar leaf* — an ordinary value that carries no resolution behavior; it
    resolves to itself, unchanged;
  * an ordered *list* of lookup values;
  * an ordered *tuple* of lookup values.

For a collection (a list or a tuple), the result is a collection OF THE SAME KIND
whose entries are the element-wise resolutions of the original entries, taken in
order. A list resolves to a list and a tuple resolves to a tuple; the arity and
order of the entries are preserved, and each entry — including an entry that is
itself a nested collection or an expression — is resolved by the very same rule.
-/

-- axioms-start
/-- A lookup value: an expression (identified by an opaque tag), a scalar leaf
(an opaque identity), a list of lookup values, or a tuple of lookup values. The
two collection constructors are distinct so the *kind* of collection (list vs
tuple) is part of the value. -/
inductive LV where
  | expr  : Nat → LV
  | plain : Nat → LV
  | lst   : List LV → LV
  | tup   : List LV → LV
  deriving Inhabited

-- Resolving an expression to its canonical form is delegated to a context-driven
-- resolver. Its result is a deterministic function of the expression's identity;
-- the resolution logic here never inspects that result (it returns it, or stores
-- it as a collection entry), so no property of the resolver is consumed — the
-- spec and the implementation invoke it identically. The proof agent adds a
-- `_prop` axiom only if a property is later required.
opaque resolveExpression : Nat → LV
-- axioms-end

-- pure-start
/-- The canonical resolution of a lookup value (the structural "what"):
* an expression resolves via the context resolver;
* a scalar leaf resolves to itself;
* a list resolves to the list of element-wise resolutions (still a list);
* a tuple resolves to the tuple of element-wise resolutions (still a tuple).
Order and arity of collection entries are preserved, and resolution recurses
into nested entries. -/
def resolveSpec : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => LV.lst (xs.map resolveSpec)
  | LV.tup xs  => LV.tup (xs.map resolveSpec)
-- pure-end

-- post-conditions-start
/-- The result is exactly the canonical resolution of the input lookup value.
This pins every component: the kind of the result (expression/scalar/list/tuple)
is the kind dictated by the input, a collection result has the same kind, arity
and order as the input collection, and each entry is the resolution of the
corresponding input entry. Nothing is left unconstrained and no entry's kind may
drift from its input. -/
def problem_spec_resolveLookupValue (value : LV) (result : LV) : Prop :=
  result = resolveSpec value
-- post-conditions-end

-- impl-start
def implementation_resolveLookupValue : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => LV.lst (xs.map implementation_resolveLookupValue)
  | LV.tup xs  => LV.tup (xs.map implementation_resolveLookupValue)
-- impl-end

-- proof-start
theorem correct_resolveLookupValue :
    ∀ (value : LV),
      problem_spec_resolveLookupValue value
        (implementation_resolveLookupValue value) := by
  intro value
  unfold problem_spec_resolveLookupValue
  refine @LV.rec
    (fun v => implementation_resolveLookupValue v = resolveSpec v)
    (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
    ?_ ?_ ?_ ?_ ?_ ?_ value
  · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec]
    rw [ih]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec]
    rw [ih]
  · rfl
  · intro head tail ih_head ih_tail
    simp only [List.map_cons, ih_head, ih_tail]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-12050 lean. Spec is exact-equality (result = resolveSpec value) with resolveSpec a fully concrete recursive function over the input LV tree; the only opaque leaf resolveExpression is invoked IDENTICALLY on both legs (A-reference, cancels; NO consumed _prop axiom — grep confirms no `axiom` keyword in Solution.lean, only `opaque`). Therefore any impl that provably satisfies the spec is extensionally equal to resolveSpec and no behaviorally-wrong impl can verify.

Protocol executed (all same_spec=True vs Solution.lean via swebench_unified.markers.same_spec, lean backend; positive control also same_spec=True):

Positive control (genuine correct map-based impl) pc.lean:
  cmd: bash scripts/lean_verify.sh <D>/pc.lean  -> exit 0 (verifies, no sorry).
  #print axioms correct_resolveLookupValue (pc_ax.lean) -> exit 0, axioms = [propext, Classical.choice, Quot.sound] (CLEAN, no sorryAx, no _prop).

8 DISTINCT same-spec wrong impls, each given a faithful @LV.rec proof attempt (the loop-lemma proof for the Id.run form, the direct map proof otherwise); all run `bash scripts/lean_verify.sh <D>/atk_N.lean` (concurrent, <=4 batches):
  atk_1 (PREPATCH bug: emits LV.tup for BOTH list+tup branches, non-recursive single pass) -> exit 1. Residual: LV.tup (...) = LV.tup (map resolveSpec xs) unprovable for the list branch (spec wants LV.lst). prepatch_reproduced=true.
  atk_2 (list->tup coercion only, recursion correct) -> exit 1. Residual: LV.tup (map resolveSpec xs) = LV.lst (map resolveSpec xs).
  atk_3 (keeps kind but NON-recursive: nested collections left unresolved) -> exit 1.
  atk_4 (boundary/order: reverses collection entries) -> exit 1. Residual: LV.tup (...).reverse = LV.tup (...).
  atk_5 (control-flow-effect: drops first entry via .tail) -> exit 1. Residual: LV.tup (...).tail = LV.tup (...).
  atk_6 (ungrounded-oracle echo / identity: `| v => v`) -> exit 1. Residual: LV.tup xs = LV.tup (map resolveSpec xs).
  atk_7 (swap constructors: lst->tup, tup->lst) -> exit 1. Residual: LV.lst (...) = LV.tup (...).
  atk_8 (scalar tamper: plain n -> plain (n+1)) -> exit 1. Residual: LV.plain (n+1) = LV.plain n.

NONE of the 8 wrong impls closed with a clean-axiom proof, so step-2 patch materialization + run_resolve is not triggered for any attack (patches={}). Every attack fully verified; no needed run could not complete.

Refinement audit: all 6 legs are R / A-reference / I (no kind-3). Leg 1 A-reference (resolveExpression <-> value.resolve_expression, opaque, invoked identically both legs, cancels, no consumed property, G-AX skip). Leg 2 I (scalar fall-through). Legs 3-6 R (container reconstruction preserving kind + recursive self-call). A-leg correspondence to the real callee holds; spec has no ungrounded answer-key (resolveSpec is a concrete function of the actual input). G-CONF stubs resolveExpression identically both legs.

Verdict: SOUND — verify DOES imply correct for this bundle; the exact-equality spec provably rejects every same-spec behavioral deviation while admitting the genuine correct impl with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no wrong impl produced a closing clean-axiom proof, so verify does NOT imply anything wrong is correct. The spec `problem_spec_resolveLookupValue value result := result = resolveSpec value` is exact structural equality to the concrete, input-grounded recursive function resolveSpec, so ANY behavioral deviation (tuple/list constructor drift, non-recursion, reordering, truncation, identity echo, scalar tamper) leaves a genuinely-false residual goal (e.g. `LV.lst (map resolveSpec xs) = LV.tup (...)`, `LV.tup (...).reverse = LV.tup (...)`, `LV.plain (n+1) = LV.plain n`) that cannot close under Lean soundness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving a lookup value to its canonical form.

A lookup value is one of four shapes:

  * an *expression* — a value that knows how to resolve itself in the current
    context; resolving the lookup value means asking it to resolve and taking
    the resolved result;
  * a *scalar leaf* — an ordinary value that carries no resolution behavior; it
    resolves to itself, unchanged;
  * an ordered *list* of lookup values;
  * an ordered *tuple* of lookup values.

For a collection (a list or a tuple), the result is a collection OF THE SAME KIND
whose entries are the element-wise resolutions of the original entries, taken in
order. A list resolves to a list and a tuple resolves to a tuple; the arity and
order of the entries are preserved, and each entry — including an entry that is
itself a nested collection or an expression — is resolved by the very same rule.
-/

-- axioms-start
/-- A lookup value: an expression (identified by an opaque tag), a scalar leaf
(an opaque identity), a list of lookup values, or a tuple of lookup values. The
two collection constructors are distinct so the *kind* of collection (list vs
tuple) is part of the value. -/
inductive LV where
  | expr  : Nat → LV
  | plain : Nat → LV
  | lst   : List LV → LV
  | tup   : List LV → LV
  deriving Inhabited

-- Resolving an expression to its canonical form is delegated to a context-driven
-- resolver. Its result is a deterministic function of the expression's identity;
-- the resolution logic here never inspects that result (it returns it, or stores
-- it as a collection entry), so no property of the resolver is consumed — the
-- spec and the implementation invoke it identically. The proof agent adds a
-- `_prop` axiom only if a property is later required.
opaque resolveExpression : Nat → LV
-- axioms-end

-- pure-start
/-- The canonical resolution of a lookup value (the structural "what"):
* an expression resolves via the context resolver;
* a scalar leaf resolves to itself;
* a list resolves to the list of element-wise resolutions (still a list);
* a tuple resolves to the tuple of element-wise resolutions (still a tuple).
Order and arity of collection entries are preserved, and resolution recurses
into nested entries. -/
def resolveSpec : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => LV.lst (xs.map resolveSpec)
  | LV.tup xs  => LV.tup (xs.map resolveSpec)
-- pure-end

-- post-conditions-start
/-- The result is exactly the canonical resolution of the input lookup value.
This pins every component: the kind of the result (expression/scalar/list/tuple)
is the kind dictated by the input, a collection result has the same kind, arity
and order as the input collection, and each entry is the resolution of the
corresponding input entry. Nothing is left unconstrained and no entry's kind may
drift from its input. -/
def problem_spec_resolveLookupValue (value : LV) (result : LV) : Prop :=
  result = resolveSpec value
-- post-conditions-end

-- impl-start
def implementation_resolveLookupValue : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => LV.lst (xs.map implementation_resolveLookupValue)
  | LV.tup xs  => LV.tup (xs.map implementation_resolveLookupValue)
-- impl-end

-- proof-start
theorem correct_resolveLookupValue :
    ∀ (value : LV),
      problem_spec_resolveLookupValue value
        (implementation_resolveLookupValue value) := by
  intro value
  unfold problem_spec_resolveLookupValue
  refine @LV.rec
    (fun v => implementation_resolveLookupValue v = resolveSpec v)
    (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
    ?_ ?_ ?_ ?_ ?_ ?_ value
  · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec]
    rw [ih]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec]
    rw [ih]
  · rfl
  · intro head tail ih_head ih_tail
    simp only [List.map_cons, ih_head, ih_tail]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-12050 lean. Spec is exact-equality (result = resolveSpec value) with resolveSpec a fully concrete recursive function over the input LV tree; the only opaque leaf resolveExpression is invoked IDENTICALLY on both legs (A-reference, cancels; NO consumed _prop axiom — grep confirms no `axiom` keyword in Solution.lean, only `opaque`). Therefore any impl that provably satisfies the spec is extensionally equal to resolveSpec and no behaviorally-wrong impl can verify.

Protocol executed (all same_spec=True vs Solution.lean via swebench_unified.markers.same_spec, lean backend; positive control also same_spec=True):

Positive control (genuine correct map-based impl) pc.lean:
  cmd: bash scripts/lean_verify.sh <D>/pc.lean  -> exit 0 (verifies, no sorry).
  #print axioms correct_resolveLookupValue (pc_ax.lean) -> exit 0, axioms = [propext, Classical.choice, Quot.sound] (CLEAN, no sorryAx, no _prop).

8 DISTINCT same-spec wrong impls, each given a faithful @LV.rec proof attempt (the loop-lemma proof for the Id.run form, the direct map proof otherwise); all run `bash scripts/lean_verify.sh <D>/atk_N.lean` (concurrent, <=4 batches):
  atk_1 (PREPATCH bug: emits LV.tup for BOTH list+tup branches, non-recursive single pass) -> exit 1. Residual: LV.tup (...) = LV.tup (map resolveSpec xs) unprovable for the list branch (spec wants LV.lst). prepatch_reproduced=true.
  atk_2 (list->tup coercion only, recursion correct) -> exit 1. Residual: LV.tup (map resolveSpec xs) = LV.lst (map resolveSpec xs).
  atk_3 (keeps kind but NON-recursive: nested collections left unresolved) -> exit 1.
  atk_4 (boundary/order: reverses collection entries) -> exit 1. Residual: LV.tup (...).reverse = LV.tup (...).
  atk_5 (control-flow-effect: drops first entry via .tail) -> exit 1. Residual: LV.tup (...).tail = LV.tup (...).
  atk_6 (ungrounded-oracle echo / identity: `| v => v`) -> exit 1. Residual: LV.tup xs = LV.tup (map resolveSpec xs).
  atk_7 (swap constructors: lst->tup, tup->lst) -> exit 1. Residual: LV.lst (...) = LV.tup (...).
  atk_8 (scalar tamper: plain n -> plain (n+1)) -> exit 1. Residual: LV.plain (n+1) = LV.plain n.

NONE of the 8 wrong impls closed with a clean-axiom proof, so step-2 patch materialization + run_resolve is not triggered for any attack (patches={}). Every attack fully verified; no needed run could not complete.

Refinement audit: all 6 legs are R / A-reference / I (no kind-3). Leg 1 A-reference (resolveExpression <-> value.resolve_expression, opaque, invoked identically both legs, cancels, no consumed property, G-AX skip). Leg 2 I (scalar fall-through). Legs 3-6 R (container reconstruction preserving kind + recursive self-call). A-leg correspondence to the real callee holds; spec has no ungrounded answer-key (resolveSpec is a concrete function of the actual input). G-CONF stubs resolveExpression identically both legs.

Verdict: SOUND — verify DOES imply correct for this bundle; the exact-equality spec provably rejects every same-spec behavioral deviation while admitting the genuine correct impl with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no diverging input found within the modeled domain. Modeled function = Query.resolve_lookup_value (post-patch, django/db/models/sql/query.py). Verified:

1) SPEC BYTE-IDENTICAL: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True. The frozen spec (axioms LV/resolveExpression, pure resolveSpec, postcondition problem_spec_resolveLookupValue := result = resolveSpec value) is identical across the patch pair.

2) LEAN CLEAN: scripts/lean_verify.sh exit 0, no sorry; #print axioms correct_resolveLookupValue -> [propext, Classical.choice, Quot.sound] only (no sorryAx). Proof is genuine.

3) SPEC NOT TOO WEAK: prepatch impl (always emits LV.tup; single non-recursive pass) cannot satisfy the spec (e.g. LV.lst [plain 1] -> spec LV.lst[...] vs prepatch LV.tup[...]); prepatch carries sorry. So the spec discriminates the bug fix.

4) FAITHFUL to real callee: confirmed the real post-patch source (base_commit family): `elif isinstance(value,(list,tuple)): return type(value)(self.resolve_lookup_value(sub, can_reuse, allow_joins, simple_col) for sub in value)`. resolveSpec transliterates this exactly: expr->resolveExpression (unchanged callee, A-reference, identical on both legs so it cancels), scalar->itself, list->LV.lst of element-wise recursive resolutions, tuple->LV.tup ditto; arity/order preserved; recursion re-enters full dispatch. conformance_check.py oracle (post-patch replica) agrees on all 120,011 inputs (11 hand-picked edge cases + 120k fuzzed LV trees), 0 disagreements.

5) NO OVER-STRONG DRIFT: the simple_col/F kwarg selection is soundly folded into the opaque resolveExpression (fixed expression identity => fixed F-ness => deterministic result; post-patch threads simple_col into the recursive call so top-level and nested resolution agree). Real-Python edge cases where the model does NOT apply (namedtuple whose type(value)(generator) would raise; a list-subclass carrying resolve_expression) are OUTSIDE the modeled LV domain (four disjoint constructors modeling plain scalars/expressions/list/tuple) -- a legitimate abstraction boundary, not a representable input on which spec and callee disagree. Every representable LV maps to the real post-patch result identically.

Verdict: FAITHFUL. The spec is a faithful and discriminating model of the post-patch function; no diverging input exists within the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes (rep.passed=True, hard_failures=[]) and same_spec(Solution vs prepatch)=True (spec region byte-identical). Semantic review of the spec view (impl+proof elided): the public problem_statement already discloses the gold edit's essence — 'coerces value of type list to tuple' and 'The expected iterable return type should match input iterable type.' The spec's 'collection OF THE SAME KIND / a list resolves to a list and a tuple resolves to a tuple' is a faithful restatement of that public expected behavior, not a leak. The additional detail (element-wise recursion into nested entries, order/arity preserved) is correct-behavior specification expressed entirely in the bundle's own abstract model (LV, resolveSpec, resolveExpression); it is the legitimate purpose of a formal spec and does not narrate the edit. Concretely: (1) no gold-patch line reproduced — no 'type(value)(...)' nor 'tuple(resolved_values)'; (2) no diff markers; (3) patched file path django/db/models/sql/query.py absent; (4) no spec-view identifier embeds the patched repo symbol resolve_lookup_value (Lean symbols are implementation_/problem_spec_resolveLookupValue — the changed-symbol check confirms resolve_lookup_value is the only distinctive symbol and it appears in neither identifiers nor comments); (5) NO bug/fix narration — comments describe only correct semantics prospectively, never mention the pre-fix tuple coercion, 'bug', 'fix', 'previously', 'incorrectly', etc. No relaxed_leakage flag / no RELAXED_LEAKAGE.md, so no deferral needed. The spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).