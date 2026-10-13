# P2 adversarial audit — pydata__xarray-6721

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_5_dedupe_first_wins.lean`, `atk_6_raw_zip_no_dedupe.lean`, `atk_7_layout_needs_accessible.lean`, `atk_8_reverse_scan.lean`, `atk_9_partial_domain_singleton.lean`, `atk_10_merge_args_swapped.lean`, `atk_12_error_priority.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2_oracle_echo.lean`, `atk_3_accessible_probe_noneleg.lean`, `atk_4_eager_layout_read.lean`, `atk_11_probe_both_legs.lean`, `atk_13_error_identified.lean` |

**Non-vacuity.** The positive control `pos_control_inlined.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec rival's faithful refined patch failed to resolve. The nearest miss is the effect-domain family (atk_3 / atk_4 / atk_11 / atk_13): these verify because the frozen postcondition `out = chunkInventory vars` is purely extensional, so a rival may freely evaluate `VarDesc.accessible` / `VarDesc.layoutReadable` as long as both branch arms agree. Their faithful Python refinements do force `v.data` / evaluate `v.chunksizes` for exactly the variables the gold fix stopped touching -- but each force must be wrapped in `try/except` to refine a total Lean Bool, and the F2P test `test_chunks_does_not_load_data` only asserts `ds.chunks == {}`. The swallowed `UnexpectedDataAccess` is therefore unobservable, and all four resolved 1405/1405 P2P + 1/1 F2P. To break this bundle one would need a rival whose extra observation escapes as an uncaught raise or a cache mutation, but an uncaught raise changes the return value and is refuted by the postcondition, closing the loop.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,16 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            if !v.accessible then Except.error ChunkErr.valuesUnavailable
+            else match v.chunks with
+              | none       => Except.ok a
+              | some pairs =>
+                  if v.layoutReadable then mergePairs a (dedupeLast pairs)
+                  else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +236,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 2 — `atk_2_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,26 +211,8 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
-    let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
-    let mut i := 0
-    while i < vars.length
-      invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant acc = (vars.take i).foldl mergeStep (Except.ok [])
-      done_with i = vars.length
-      decreasing vars.length - i
-    do
-      acc := mergeStep acc vars[i]!
-      i := i + 1
-    return acc
+    return chunkInventory vars
     -- impl-end
 
 prove_correct buildChunkInventory by
   loom_solve
-  · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
-  · simp_all [chunkInventory, List.take_length]
```

Attack 3 — `atk_3_accessible_probe_noneleg.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => if v.accessible then Except.ok a else Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs a (dedupeLast pairs)
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 4 — `atk_4_eager_layout_read.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,17 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      let readable := v.layoutReadable
+      let live     := v.accessible
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => if readable && live then Except.ok a else Except.ok a
+            | some pairs =>
+                if readable then mergePairs a (dedupeLast pairs)
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +237,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 5 — `atk_5_dedupe_first_wins.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs a (dedupeLast pairs.reverse)
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 6 — `atk_6_raw_zip_no_dedupe.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs a pairs
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 7 — `atk_7_layout_needs_accessible.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable && v.accessible then mergePairs a (dedupeLast pairs)
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 8 — `atk_8_reverse_scan.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,26 +211,8 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
-    let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
-    let mut i := 0
-    while i < vars.length
-      invariant 0 ≤ i ∧ i ≤ vars.length
-      invariant acc = (vars.take i).foldl mergeStep (Except.ok [])
-      done_with i = vars.length
-      decreasing vars.length - i
-    do
-      acc := mergeStep acc vars[i]!
-      i := i + 1
-    return acc
+    return vars.reverse.foldl mergeStep (Except.ok [])
     -- impl-end
 
 prove_correct buildChunkInventory by
   loom_solve
-  · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
-  · simp_all [chunkInventory, List.take_length]
```

Attack 9 — `atk_9_partial_domain_singleton.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,9 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
+    if vars.length ≤ 1 then
+      return Except.ok []
+    else
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
```

Attack 10 — `atk_10_merge_args_swapped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs (dedupeLast pairs) a
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 11 — `atk_11_probe_both_legs.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,9 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      let probe := v.accessible || v.layoutReadable
+      acc := (if probe then mergeStep acc v else mergeStep acc v)
       i := i + 1
     return acc
     -- impl-end
```

Attack 12 — `atk_12_error_priority.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match v.chunks with
+        | none       => acc
+        | some pairs =>
+            if v.layoutReadable then
+              (match acc with
+               | Except.error _ => mergePairs [] (dedupeLast pairs)
+               | Except.ok a    => mergePairs a (dedupeLast pairs))
+            else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Attack 13 — `atk_13_error_identified.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,10 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
+    -- The three repo raises out of the layout read are IDENTIFIED by the model
+    -- (mapping.md §2: it records only THAT the read failed), so the failure
+    -- value is hoisted into a single named constant, making the identification
+    -- explicit in the impl rather than implicit in the abstraction function.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +223,16 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      let readFailure : ChunkErr := ChunkErr.layoutUnavailable
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs a (dedupeLast pairs)
+                else Except.error readFailure)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +240,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_inlined.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs a (dedupeLast pairs)
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Scratch: (base_commit worktree at ./wt, cc183652). Generators: gen.py, mkpatch.py, resolve.py. 13 attacks + 1 positive control, all built by editing ONLY the impl region and the (also-elided) prove_correct body.

**SAME-SPEC:** all 14 files True via swebench_unified.markers.same_spec against the bundle Solution.lean (velvet tables). Command:
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>.lean').read(), b.language))"

### VERIFY (all via `bash scripts/lean_verify.sh <file>`, run 4-concurrent in background batches; ledger rc.txt):
  pos_control_inlined            rc=0  VERIFIES  <- positive control: inlines mergeVar's case analysis instead of calling mergeStep (structurally different), proof needs an extra `simp [mergeStep, mergeVar]`
  atk_1_prepatch                 rc=1  REJECTED  <- PREPATCH BUG REPRODUCED: value-forcing guard emits valuesUnavailable when accessible=false
  atk_2_oracle_echo              rc=0  VERIFIES  (ungrounded oracle echo: `return chunkInventory vars`)
  atk_3_accessible_probe_noneleg rc=0  VERIFIES  (control-flow-effect: probes accessible on the unadvertised leg, identical arms)
  atk_4_eager_layout_read        rc=0  VERIFIES  (control-flow-effect: binds BOTH value-side observations eagerly for every variable)
  atk_5_dedupe_first_wins        rc=1  REJECTED  (boundary: repeated dim resolved FIRST-wins)
  atk_6_raw_zip_no_dedupe        rc=1  REJECTED  (boundary: merges the raw zip, so a repeated dim raises `inconsistent` -- the earlier refuted model)
  atk_7_layout_needs_accessible  rc=1  REJECTED  (boundary: makes layoutUnavailable depend on accessible -- the two observations are independent)
  atk_8_reverse_scan             rc=1  REJECTED  (control-flow: back-to-front scan, wrong insertion order / first-error)
  atk_9_partial_domain_singleton rc=1  REJECTED  (PARTIAL DOMAIN: singleton answered with the empty inventory)
  atk_10_merge_args_swapped      rc=1  REJECTED  (cross-variable merge with arguments swapped)
  atk_11_probe_both_legs         rc=0  VERIFIES  (control-flow-effect: `probe := v.accessible || v.layoutReadable` on BOTH legs, identical arms)
  atk_12_error_priority          rc=1  REJECTED  (error-priority: no short-circuit, a later error overwrites an earlier one)
  atk_13_error_identified        rc=0  VERIFIES  (A-leg: hoists the identified read-failure into a named constant; refines to the gold patch itself)
All 8 rejections are genuine proof-obligation failures -- each log contains `error: unsolved goals`, none is a parse/elaboration error.

**HYGIENE:** Solution.lean declares no `axiom`, no `sorry`/`admit`, no `native_decide`, no `opaque`/`partial def`; the axioms region is prose only. No attack drops the obligation or adds an axiom, so all 13 are admissible.

**PATCHES:** 5 verifying attacks -> 5 faithful unified diffs, each generated by `git diff` against the base_commit worktree and each checked with `git apply --check` in that worktree (all rc=0). patch_atk_13 is byte-identical to patch_gold_control, since atk_13's impl differs from the reference only by naming the (model-identified) failure value.

RESOLVE (ONE AT A TIME, per the ImageNotFound hazard; `python resolve.py <name>` wrapping swebench_unified.harness.run_resolve on pydata__xarray-6721; ledger resolve_summary.txt + resolve_*.json):
  gold_control                   resolved=True completed=True attempts=1 flaky=False  <- GOLD CONTROL CERTIFIED FIRST; payload byte-identical to the bundle's patch.diff
  atk_2_oracle_echo              resolved=True completed=True attempts=1 flaky=False
  atk_3_accessible_probe_noneleg resolved=True completed=True attempts=1 flaky=False
  atk_4_eager_layout_read        resolved=True completed=True attempts=1 flaky=False
  atk_11_probe_both_legs         resolved=True completed=True attempts=1 flaky=False
Every run: F2P 1/1 success, P2P 1405/1405 success, 0 failures. No run was flaky, none needed a retry, none hit ImageNotFound. atk_13 needed no separate run: its patch IS the certified gold patch.

REFINEMENT.MD AUDIT (§3 of the protocol). Legs are A1 (R), A2 (I), A3 (R+I), A3b (R+I), A4 (I), A4b (I), A5 (R) -- 2 R, 3 I, 2 R+I. There are NO A-consumed and NO A-reference legs, and no kind-3: the operation that actually changed (descriptor-vs-values guard) is modeled deeply as `mergeVar` branching on `VarDesc.chunks`, not hidden behind an axiom, so §B's claim holds and there is nothing left symbolic to trust. I re-derived each R-leg against the real callees at base_commit and all hold:
  * A3/`VarDesc.chunks` <-> `hasattr(v._data,"chunks")` -- common.py:2026 confirmed, and the patch is exactly `v.data -> v._data`.
  * A3b/`layoutReadable` <-> "`v.chunksizes` completes" -- CONFIRMED genuinely separate: variable.py:1017 guards on `self._data` but then indexes `self.data.chunks`, and `.data` (variable.py:337) falls through to `self.values` for a non-duck array. So passing the descriptor guard does NOT imply the layout is obtainable. A model omitting this leg would describe a different program; atk_7 confirms the spec keeps the two observations independent.
  * A4/`dedupeLast` <-> the dict comprehension in `Variable.chunksizes` -- CONFIRMED load-bearing: the comprehension is keyed by dimension and `Variable(("x","x"), arr)` is an ordinary publicly-reachable variable, so a repeated dim is overwritten (first position, last length), never compared. atk_5 and atk_6 confirm the spec pins this exactly, refuting both the first-wins and the raise-on-repeat models.
  * A4b/`mergePair(s)` <-> `if dim in chunks and c != chunks[dim]: raise` over the inventory built from the PRECEDING variables -- confirmed between-variable only; atk_10 and atk_12 confirm argument order and error priority are both pinned.
  * A5 identifies the three raises out of the layout read into one `layoutUnavailable`; sound because the scan aborts identically on all three and the model records only THAT it failed. atk_13 verifies and resolves, consistent with the identification.
  * A1/A2 order: the forward left-fold matches the real iteration order at the two call sites (dataset.py:2138/2155 over `self.variables.values()`, dataarray.py:1143 over a list); atk_8 confirms reversal is refuted.

RESIDUAL RISK (advisory, not a finding). The frozen postcondition is extensional, so it cannot constrain *effects* -- the verifier admits rivals that make extra value-side observations with identical arms (atk_3/4/11/13). That is a real gap between `verify` and "is the gold patch", but it is NOT a verify-does-not-imply-resolve gap for this instance: the refinement of a total Lean Bool must swallow the raise, and the F2P test asserts only `ds.chunks == {}`, so the extra force is invisible to the oracle. Recorded here so a future reviewer does not re-derive it as new; no repair is implied.

**PRIOR-PASS COVERAGE:** the two earlier scratch dirs (`_3j1crsbv`, `_m7u9lka1`) named oracle-echo, accessible-probe, eager-layout-read and probe-after-error as verifying candidates whose patches all resolved. I re-encoded that family independently (atk_2/3/4/11) rather than inheriting the labels, and reproduced resolved=True for each on my own gold-certified runs.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_5_dedupe_first_wins.lean`, `atk_6_raw_zip_no_dedupe.lean`, `atk_7_layout_needs_accessible.lean`, `atk_8_reverse_scan.lean`, `atk_9_partial_domain_singleton.lean`, `atk_10_merge_args_swapped.lean`, `atk_12_error_priority.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2_oracle_echo.lean`, `atk_3_accessible_probe_noneleg.lean`, `atk_4_eager_layout_read.lean`, `atk_11_probe_both_legs.lean`, `atk_13_error_identified.lean` |

**Non-vacuity.** The positive control `pos_control_inlined.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec rival's faithful refined patch failed to resolve. The nearest miss is the effect-domain family (atk_3 / atk_4 / atk_11 / atk_13): these verify because the frozen postcondition `out = chunkInventory vars` is purely extensional, so a rival may freely evaluate `VarDesc.accessible` / `VarDesc.layoutReadable` as long as both branch arms agree. Their faithful Python refinements do force `v.data` / evaluate `v.chunksizes` for exactly the variables the gold fix stopped touching -- but each force must be wrapped in `try/except` to refine a total Lean Bool, and the F2P test `test_chunks_does_not_load_data` only asserts `ds.chunks == {}`. The swallowed `UnexpectedDataAccess` is therefore unobservable, and all four resolved 1405/1405 P2P + 1/1 F2P. To break this bundle one would need a rival whose extra observation escapes as an uncaught raise or a cache mutation, but an uncaught raise changes the return value and is refuted by the postcondition, closing the loop.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_accessible_probe_noneleg.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_eager_layout_read.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5_dedupe_first_wins.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_raw_zip_no_dedupe.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_layout_needs_accessible.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_reverse_scan.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_partial_domain_singleton.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_merge_args_swapped.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_probe_both_legs.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_error_priority.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_error_identified.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_inlined.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,12 +211,6 @@
   ensures out = chunkInventory vars
   do
     -- impl-start
-    -- Scan the variables front-to-back — the repo's own iteration order — and
-    -- fold each into the inventory built for the ones before it, so every
-    -- dimension is inserted the first time it is advertised. Each step inspects
-    -- only the variable's advertised chunk layout (`mergeStep`/`mergeVar` read
-    -- `v.chunks`), never forcing its values into memory to decide whether it is
-    -- chunked — so an un-materializable, un-chunked variable is passed over.
     let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
     let mut i := 0
     while i < vars.length
@@ -225,7 +219,15 @@
       done_with i = vars.length
       decreasing vars.length - i
     do
-      acc := mergeStep acc vars[i]!
+      let v := vars[i]!
+      acc := (match acc with
+        | Except.error e => Except.error e
+        | Except.ok a =>
+            match v.chunks with
+            | none       => Except.ok a
+            | some pairs =>
+                if v.layoutReadable then mergePairs a (dedupeLast pairs)
+                else Except.error ChunkErr.layoutUnavailable)
       i := i + 1
     return acc
     -- impl-end
@@ -233,4 +235,5 @@
 prove_correct buildChunkInventory by
   loom_solve
   · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
+    simp [mergeStep, mergeVar]
   · simp_all [chunkInventory, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Scratch: (base_commit worktree at ./wt, cc183652). Generators: gen.py, mkpatch.py, resolve.py. 13 attacks + 1 positive control, all built by editing ONLY the impl region and the (also-elided) prove_correct body.

**SAME-SPEC:** all 14 files True via swebench_unified.markers.same_spec against the bundle Solution.lean (velvet tables). Command:
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>.lean').read(), b.language))"

### VERIFY (all via `bash scripts/lean_verify.sh <file>`, run 4-concurrent in background batches; ledger rc.txt):
  pos_control_inlined            rc=0  VERIFIES  <- positive control: inlines mergeVar's case analysis instead of calling mergeStep (structurally different), proof needs an extra `simp [mergeStep, mergeVar]`
  atk_1_prepatch                 rc=1  REJECTED  <- PREPATCH BUG REPRODUCED: value-forcing guard emits valuesUnavailable when accessible=false
  atk_2_oracle_echo              rc=0  VERIFIES  (ungrounded oracle echo: `return chunkInventory vars`)
  atk_3_accessible_probe_noneleg rc=0  VERIFIES  (control-flow-effect: probes accessible on the unadvertised leg, identical arms)
  atk_4_eager_layout_read        rc=0  VERIFIES  (control-flow-effect: binds BOTH value-side observations eagerly for every variable)
  atk_5_dedupe_first_wins        rc=1  REJECTED  (boundary: repeated dim resolved FIRST-wins)
  atk_6_raw_zip_no_dedupe        rc=1  REJECTED  (boundary: merges the raw zip, so a repeated dim raises `inconsistent` -- the earlier refuted model)
  atk_7_layout_needs_accessible  rc=1  REJECTED  (boundary: makes layoutUnavailable depend on accessible -- the two observations are independent)
  atk_8_reverse_scan             rc=1  REJECTED  (control-flow: back-to-front scan, wrong insertion order / first-error)
  atk_9_partial_domain_singleton rc=1  REJECTED  (PARTIAL DOMAIN: singleton answered with the empty inventory)
  atk_10_merge_args_swapped      rc=1  REJECTED  (cross-variable merge with arguments swapped)
  atk_11_probe_both_legs         rc=0  VERIFIES  (control-flow-effect: `probe := v.accessible || v.layoutReadable` on BOTH legs, identical arms)
  atk_12_error_priority          rc=1  REJECTED  (error-priority: no short-circuit, a later error overwrites an earlier one)
  atk_13_error_identified        rc=0  VERIFIES  (A-leg: hoists the identified read-failure into a named constant; refines to the gold patch itself)
All 8 rejections are genuine proof-obligation failures -- each log contains `error: unsolved goals`, none is a parse/elaboration error.

**HYGIENE:** Solution.lean declares no `axiom`, no `sorry`/`admit`, no `native_decide`, no `opaque`/`partial def`; the axioms region is prose only. No attack drops the obligation or adds an axiom, so all 13 are admissible.

**PATCHES:** 5 verifying attacks -> 5 faithful unified diffs, each generated by `git diff` against the base_commit worktree and each checked with `git apply --check` in that worktree (all rc=0). patch_atk_13 is byte-identical to patch_gold_control, since atk_13's impl differs from the reference only by naming the (model-identified) failure value.

RESOLVE (ONE AT A TIME, per the ImageNotFound hazard; `python resolve.py <name>` wrapping swebench_unified.harness.run_resolve on pydata__xarray-6721; ledger resolve_summary.txt + resolve_*.json):
  gold_control                   resolved=True completed=True attempts=1 flaky=False  <- GOLD CONTROL CERTIFIED FIRST; payload byte-identical to the bundle's patch.diff
  atk_2_oracle_echo              resolved=True completed=True attempts=1 flaky=False
  atk_3_accessible_probe_noneleg resolved=True completed=True attempts=1 flaky=False
  atk_4_eager_layout_read        resolved=True completed=True attempts=1 flaky=False
  atk_11_probe_both_legs         resolved=True completed=True attempts=1 flaky=False
Every run: F2P 1/1 success, P2P 1405/1405 success, 0 failures. No run was flaky, none needed a retry, none hit ImageNotFound. atk_13 needed no separate run: its patch IS the certified gold patch.

REFINEMENT.MD AUDIT (§3 of the protocol). Legs are A1 (R), A2 (I), A3 (R+I), A3b (R+I), A4 (I), A4b (I), A5 (R) -- 2 R, 3 I, 2 R+I. There are NO A-consumed and NO A-reference legs, and no kind-3: the operation that actually changed (descriptor-vs-values guard) is modeled deeply as `mergeVar` branching on `VarDesc.chunks`, not hidden behind an axiom, so §B's claim holds and there is nothing left symbolic to trust. I re-derived each R-leg against the real callees at base_commit and all hold:
  * A3/`VarDesc.chunks` <-> `hasattr(v._data,"chunks")` -- common.py:2026 confirmed, and the patch is exactly `v.data -> v._data`.
  * A3b/`layoutReadable` <-> "`v.chunksizes` completes" -- CONFIRMED genuinely separate: variable.py:1017 guards on `self._data` but then indexes `self.data.chunks`, and `.data` (variable.py:337) falls through to `self.values` for a non-duck array. So passing the descriptor guard does NOT imply the layout is obtainable. A model omitting this leg would describe a different program; atk_7 confirms the spec keeps the two observations independent.
  * A4/`dedupeLast` <-> the dict comprehension in `Variable.chunksizes` -- CONFIRMED load-bearing: the comprehension is keyed by dimension and `Variable(("x","x"), arr)` is an ordinary publicly-reachable variable, so a repeated dim is overwritten (first position, last length), never compared. atk_5 and atk_6 confirm the spec pins this exactly, refuting both the first-wins and the raise-on-repeat models.
  * A4b/`mergePair(s)` <-> `if dim in chunks and c != chunks[dim]: raise` over the inventory built from the PRECEDING variables -- confirmed between-variable only; atk_10 and atk_12 confirm argument order and error priority are both pinned.
  * A5 identifies the three raises out of the layout read into one `layoutUnavailable`; sound because the scan aborts identically on all three and the model records only THAT it failed. atk_13 verifies and resolves, consistent with the identification.
  * A1/A2 order: the forward left-fold matches the real iteration order at the two call sites (dataset.py:2138/2155 over `self.variables.values()`, dataarray.py:1143 over a list); atk_8 confirms reversal is refuted.

RESIDUAL RISK (advisory, not a finding). The frozen postcondition is extensional, so it cannot constrain *effects* -- the verifier admits rivals that make extra value-side observations with identical arms (atk_3/4/11/13). That is a real gap between `verify` and "is the gold patch", but it is NOT a verify-does-not-imply-resolve gap for this instance: the refinement of a total Lean Bool must swallow the raise, and the F2P test asserts only `ds.chunks == {}`, so the extra force is invisible to the oracle. Recorded here so a future reviewer does not re-derive it as new; no repair is implied.

**PRIOR-PASS COVERAGE:** the two earlier scratch dirs (`_3j1crsbv`, `_m7u9lka1`) named oracle-echo, accessible-probe, eager-layout-read and probe-after-error as verifying candidates whose patches all resolved. I re-encoded that family independently (atk_2/3/4/11) rather than inheriting the labels, and reproduced resolved=True for each on my own gold-certified runs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK ATTACK on pydata__xarray-6721 / velvet. No diverging reachable input found: I could not make the modelled function disagree with the real PATCHED get_chunksizes. Verdict FAITHFUL. Everything below is freshly measured on the bytes now on disk (Solution.lean sha256[:16]=41f2dbcdb03ef441, spec_signature hash 8dc212271c78afed); I inherited no prior panel verdict.

**REFERENCE DISCIPLINE.** Per the brief the modelled function's reference is the base worktree with patch.diff APPLIED. I ran a fresh container from swebench/sweb.eval.x86_64.pydata_1776_xarray-6721:latest (base commit 8e4d928f, xarray 2022.6.0rc1.dev17+gcc183652b, numpy 1.23.0, dask 2022.8.1), applied patch.diff, and confirmed the guard now reads `hasattr(v._data, "chunks")`. So the `accessible=false / chunks=none` leg (the patch delta, where BASE raises UnexpectedDataAccess and the spec returns ok) is NOT counted as a divergence -- that is the delta the patch introduces, and reporting it would condemn a correct spec.

**SPEC REGION IDENTITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True, so the twin attacks the identical frozen spec view. Solution.lean itself verifies clean via scripts/lean_verify.sh (exit 0).

METHOD -- I did NOT trust the bundle's own Python shadow. I drove the LEAN model directly: extracted the `pure` region with markers.region_text, generated `#eval` harnesses calling the real `chunkInventory`, and diffed against an oracle that is the REAL patched get_chunksizes fed REAL xarray Variable objects. The VarDesc abstraction was computed FROM each real object (hasattr(v.`_data`,'chunks') for the constructor, zip(v.dims, v.data.chunks) for the payload, whether v.chunksizes completes for layoutReadable, whether v.data raises for accessible) rather than asserted by hand.

### Results
1. 32 hand-built adversarial cases: 0 disagreements. Covered all 7 descriptor kinds, error PRECEDENCE both ways (inconsistency-before-unreadable -> inconsistent; unreadable-before-inconsistency -> layoutUnavailable, matching the real scan's short-circuit), zip truncation short AND long, scalar/no-dims, real IndexVariable, chunks attribute = int/str/None/empty-tuple, NonDuck wrapping a real dask array, and the F2P shape.
2. Randomized fuzz, 4000 inputs, 12 descriptor kinds incl. real dask and real xarray wrapper stacks (LazilyIndexedArray / CopyOnWriteArray / MemoryCachedArray), dimension names drawn WITH replacement from a 3-pool so repeated dims are reachable: 0 disagreements. All three legs genuinely reached -- 2235 ok, 1512 layoutUnavailable, 253 inconsistent -- and 709 variables advertised a repeated dimension, so the dedupeLast leg was exercised rather than assumed.
3. 8 further edge cases (multi-block dask layouts, repeated dim with multi-block dask, 4-variable mix combining a repeated dim + an inaccessible unchunked var + an inconsistency + an unreadable layout): 0 disagreements.

SELF-CAUGHT DEFECT IN MY OWN ARTIFACT (this is why I report 0 and not 23). My first fuzz run showed 23 apparent divergences, all real=inconsistent vs lean=ok. They were MY bug, not the spec's: I interned block lengths by repr() through a JSON round-trip, which collapsed tuple `(3,)` and list `[3]` to the same Int, while Python compares them UNEQUAL -- so the repo correctly raised inconsistent where my Lean input had been made to agree. mapping.md explicitly requires the interning be an INJECTION w.r.t. tuple ==, and repr-interning is not one. I re-ran with interning done in-container by equality class on the real objects (type-aware), and all 23 resolved to agreement. Crediting those as spec weakness would have invented a defect.

FOUR THEOREMS PROVED (not merely fuzzed), all verifying, no sorry/admit:
  (A) inventory_ignores_accessible : chunkInventory vs = chunkInventory (vs.map wipeAcc) -- the `accessible` axis is provably unreachable from the outcome, closing the whole 'does the spec smuggle value-materializability' question rather than sampling it.
  (B) unadvertised_total_dontcare -- on chunks=none, NO other field of the variable can reach the outcome (both bits quantified).
  (C) never_values_unavailable : chunkInventory vs never = error valuesUnavailable -- the spec provably cannot emit the PRE-patch error, i.e. it describes the patched program, not the unpatched one.
  (D) mergePairs_only_inconsistent -- mergePairs' only failure mode is `inconsistent`.

NEGATIVE CONTROLS (my harness has teeth). I mutated the Lean model three ways and re-ran the same 4000-input diff: (1) drop dedupeLast -> ELABORATES CLEANLY yet diverges on 304/4000 (this is exactly the 'spec too strong' mutation -- it would raise on Variable(("x","x"), ...) where the repo returns the overwritten mapping); (2) make the fold consult `accessible` (pre-patch behaviour) -> 476/4000 diverge and lemma mergeVar_unadvertised breaks; (3) dedupeLast keeps FIRST instead of LAST block length -> 224/4000 diverge. A false theorem injected as a vacuity control fails to compile (exit 1). So a zero-disagreement result on this harness is informative, not vacuous.

**CROSS-CHECKS.** The bundle's own axiom_check.py (G-AX) and conformance_check.py (G-CONF) both exit 0 in the patched image; G-CONF reports 100026 inputs / 0 disagreements with 41538 advertising a repeated dimension. These agree with my independent measurement but are not what I based the verdict on.

OVER-STRENGTH LEGS PROBED AND FOUND CORRECTLY DESCRIBED (each is a place a weaker-than-repo or stronger-than-repo spec would show): the within-variable repeated dimension (spec overwrites last-wins via dedupeLast, matching the repo's dict comprehension, and does NOT raise -- reachable publicly via xr.Dataset({"a": v}).chunks); the unguarded value-forcing v.chunksizes read that patch.diff does NOT touch (spec carries it as layoutReadable, so the three real raise types UnexpectedDataAccess/AttributeError/TypeError are inside the described region instead of being wrongly placed on the ok leg); zip truncation (payload bound to the zip absorbs arity mismatch, no side-condition needed); error precedence under short-circuit; and accessible-independence (proved, not sampled).

**CONCLUSION.** The spec is not too strong and does not drift from the real repo. The three-way split it claims (no layout advertised -> passed over silently; advertised and delivered -> merged; advertised but not delivered -> layoutUnavailable) is exactly what the patched repo does on every input I could construct or fuzz, including the two legs (dedupeLast, layoutReadable) that an earlier version of this model reportedly got wrong. No diverging input exists to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / RELAXATION. No relaxation claim exists to inherit or re-derive, and I established that myself rather than reading it off prose: `find -iname '*relax*'` under benchmark-verified/pydata__xarray-6721/ returns empty, and a recursive walk of all 497 key paths in velvet/meta.json yields zero keys matching /relax/i (the only 'relaxed_leakage' substrings in the file sit inside prior G-PANEL-3 note prose asserting the key is absent). So this is an ordinary STRICT review: spec view judged against problem_statement ONLY. hints_text here is a two-line maintainer ack ('I agree this is a major regression...'); I read it solely to exclude it and nothing in my reasoning uses it.

**BYTES MEASURED.** Solution.lean sha256 41f2dbcdb03e..., Solution_prepatch.lean 82499221a8ea..., properties.py c53c9e3297fe.... markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True; spec_signature digest 8dc212271c78afed. The twins differ ONLY in the elided impl region (diff is confined to lines 214-229 / the do-block), so the view I screened is byte-identical across both. meta.json G-PANEL-3 sources pin exactly the current Solution.lean hash, so this record is fresh, not a SPEC-MOVED echo. patch.diff is byte-verbatim instance['patch'] (confirmed by equality against instance.json).

LIVE SCREEN + MY OWN LIVENESS CONTROLS. leakage.screen(Solution.lean, velvet, patch.diff, problem_statement) -> hard_failures=[], warnings=[]. Gold changed set: 1 file xarray/core/common.py, 1 symbol get_chunksizes, changed lines `if hasattr(v.data, "chunks"):` / `if hasattr(v._data, "chunks"):`. I injected 6 controls into the FROZEN pure region (so they survive spec_view) and all fired: post-patch gold line -> L1; pre-patch gold line -> L1; `xarray/core/common.py` -> L2 x2; `/- fixes the pre-patch bug -/` -> L3 narration; diff-marked `+ if hasattr(v._data, ...)` -> L1. The 7th (renaming chunkInventory -> get_chunksizesInventory) was NOT caught against the real patch -- correctly, since get_chunksizes is public in the problem_statement and the rule exempts public text. To prove that exemption is not masking a dead rule I built a doctored patch renaming the def to zzzSecretHelper (a symbol absent from the PS) and re-ran: the L2/L5 identifier rule fired ('zzzSecretHelperInv_nil embeds patched repo symbol') and the L2/L3 comment rule fired. Both rules are live; the clean spec against that doctored patch still screens [].

TOKEN AUDIT (substring, my measurement). Present in problem_statement but ABSENT from the spec view: `_data`, `v.data`, `.data`, `hasattr`, `chunksizes`, `encoding`, `xarray`, `common.py`, `variable.py`, any `py:` frame reference, `dask`, `zarr`, `Variable`, `Lazily`, `MemoryCached`, `get_chunksizes`. Also absent: `Frozen`, `ValueError`, `InaccessibleArray`, the F2P test name `test_chunks_does_not_load_data`, `test_dataset`, `ds.chunks`. Word-boundary narration scan over every comment in the view: the ONLY hit for the whole narration vocabulary (bug/fix/regression/patch/previously/pre-patch/defect/instead of/used to/no longer/wrong/gold/oracle/harness) is the word 'twin' on view line 37; 'fix'/'diff'/'before' appear only as substrings of 'prefix', 'different', 'compares before inserting'. Identifiers are pure model vocabulary (VarDesc, chunks, accessible, layoutReadable, mergeVar, mergePair(s), dedupeLast, chunkInventory, buildChunkInventory).

STRIP-THE-NARRATION TEST -- run, not asserted. I mechanically deleted every /- ... -/ block and every non-region-marker -- comment from BOTH twins (fresh mktemp -d, per the /tmp-reaping rule) and re-verified with scripts/lean_verify.sh at a 900s cap. Result: stripped Solution.lean exits 0 (still verifies), stripped Solution_prepatch.lean exits 1 with `unsolved goals` at the prove_correct. So the discriminating power lives entirely in the FORMAL content -- mergeVar branching on `v.chunks` with no branch producing `valuesUnavailable`, plus the postcondition `out = chunkInventory vars` -- and NOT in any prose clause. No comment line is load-bearing, which is exactly the condition under which no comment line can be the leak. Unstripped controls for the same pair: Solution.lean exit 0, Solution_prepatch.lean exit 1 with the residual goal literally displaying the prepatch step emitting `Except.error ChunkErr.valuesUnavailable` when `!vars[i]!.accessible` against `mergeStep acc vars[i]!` -- so G-DIFF/G-GOLD are re-derived by me and the spec is genuinely load-bearing on the descriptor-vs-values axis (not vacuous).

**WHY THE VIEW ADDS NO DISCRIMINATOR BEYOND THE PS.** The gold edit is one token, v.data -> v.`_data`. The problem_statement is unusually self-diagnosing: it quotes the pre-patch guard `if hasattr(v.data, "chunks"):` at common.py:1815 in get_chunksizes, then the very next frame `variable.py:339, in Variable.data` showing `return self._data` (duck) vs `return self.values` (materialize), then the whole materialization chain down to the zarr fetch, and states the expectation that reading chunks should merely inspect cheap metadata rather than load the array. A solver holding only the statement can already derive 'decide chunkedness off the cheap descriptor, never off the materialized values' -- and the statement even names `_data` verbatim. The spec view is strictly LESS localizing than that: it says only that a variable's chunk advertisement is 'ALWAYS observable, independent of the values' and that materializability 'MUST NOT' decide chunkedness, at an abstraction (VarDesc fields) that names no repo path, symbol, attribute, or line. It does not tell a solver that `_data` is the attribute to read; the PS traceback does.

CLOSEST CALLS, both cleared on my own reading. (i) `ChunkErr.valuesUnavailable` is declared in the frozen pure region with the comment 'the outcome is named here only so the twin can express it'. That does disclose harness machinery (a differential twin exists) and it is the weakest line in the view -- I record it as a hygiene wart, not leakage: chunkInventory provably never emits the constructor (mergeVar has no such branch; the prepatch failure above IS that gap), it names no path/symbol/line/diff text, and the behavioural fact it carries -- that deciding chunkedness currently forces values into memory -- is the literal subject of the public traceback. (ii) The layoutReadable / layoutUnavailable leg is described REGION, not delta: patch.diff touches only the guard at common.py:2026, so Variable.chunksizes is untouched and that leg behaves identically pre- and post-edit (mapping.md 2.1 measurements agree), so it cannot point at the change. Neither is a discriminator the PS does not already supply.

**NO BUNDLE FILE ADDRESSED ME.** leakage.reviewer_directed() returns [] for all nine bundle files. My own grep for reviewer-steering vocabulary (reviewer/auditor/attacker/G-PANEL/audit_panel/NO-LEAKAGE/submit_result/'honest verdict'/'should record'/'do not flag'/'you must'/'please') finds ZERO hits in Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, properties.py, conformance_check.py, axiom_check.py. Hits exist only in verdict.md and meta.json, and they are a prior G-PANEL-3 role's own recorded note -- factual self-report, not an instruction to me and not a statement of which verdict is honest. Worth recording as a record-hygiene observation: that prior note is duplicated verbatim FIVE times (verdict.md twice, meta.json gates/G-PANEL/data/roles/G-PANEL-3/detail, gates/G-PANEL/detail, gates/G-PANEL-3/note), which pre-supplies a complete rationale a lazy reviewer could copy. I did not inherit it: my controls differ from its controls (my doctored-patch construction and, notably, the actual strip-and-reverify of both twins, which that note argues for but does not run), and my conclusion rests on the measurements listed above.

**VERDICT.** NO-LEAKAGE. The facet I re-confirmed is the descriptor-vs-values discriminator; the spec expresses it as behaviour (chunk advertisement observable independent of values; accessible never reaching the outcome, pinned by mergeVar_unadvertised) at a repo-agnostic abstraction, every repo-identifying token is absent, all screen rules are demonstrably live including on a symbol outside the public text, and with all prose removed the spec still verifies post and still rejects pre -- so no prose line carries the fix.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
