# P2 adversarial audit — psf__requests-1724

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | listed per attack in the audit record below |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | listed per attack in the audit record below |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl was found whose faithful refined patch fails to resolve. The two same-spec attacks that VERIFIED (atk7_no_stub, atk8_stub_as_content_guard) both had their faithful refined patches materialized and RUN through the official harness (run_resolve, psf__requests-1724): both completed=True resolved=True — i.e. they are behaviourally correct impls, not counterexamples. Oracle discrimination was proven in the same session: gold patch resolved=True, noop patch resolved=False ('patch did not resolve in 3 attempts (consistent — not flaky)').
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,12 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
+    -- Pre-image skeleton: the supplied method is case-normalised directly,
+    -- carrying its ORIGINAL flavour into the constructed token (no native
+    -- coercion). The frozen spec requires the carried flavour to be native
+    -- irrespective of the supplied flavour, so prove_correct MUST fail on a
+    -- non-native supplied name.
+    let flavour := native
     let mut result : List Char := []
     let mut i := text.length
     while i > 0
@@ -126,13 +128,6 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  -- The content (loop-body) leg discharges exactly as in the post-image proof;
+  -- the remaining flavour leg (`native = true`) is the genuine spec failure.
+  all_goals try (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
```

Attack 2 — `atk1_assume_false.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,9 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    -- Unsatisfiable demonic pick: assume-false miracle.
+    let junk :| junk = (0 : Nat) ∧ junk = (1 : Nat)
+    return { chars := [], native := false }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +113,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 3 — `atk2_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,15 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
+    -- Diverging loop with a constant (non-decreasing) measure.
+    let mut spin : Nat := 0
+    while spin ≥ 0
+      invariant True
+      done_with spin < 0
+      decreasing spin
     do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+      spin := spin + 1
+    return { chars := [], native := false }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +119,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 4 — `atk3_partial_domain.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,11 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    if text.length = 0 then
+      return { chars := [], native := flavour }
+    else
+      return { chars := text, native := native }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +115,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 5 — `atk4_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,16 +85,13 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
     let mut result : List Char := []
     let mut i := text.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = upperSeq (text.drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let c := text[i - 1]!
@@ -126,13 +123,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 6 — `atk5_skip_a.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,9 +85,6 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
     let mut result : List Char := []
     let mut i := text.length
@@ -98,7 +95,10 @@
       decreasing i
     do
       let c := text[i - 1]!
-      result := upperCp c :: result
+      if c = 'a' then
+        result := c :: result
+      else
+        result := upperCp c :: result
       i := i - 1
     return { chars := result, native := flavour }
     -- impl-end
@@ -126,13 +126,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 7 — `atk6_oracle_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,9 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    -- Echo the postcondition into a demonic pick; nothing is computed.
+    let out :| out.chars = upperSeq text ∧ out.chars.length = text.length ∧ out.native = true
+    return out
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +113,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 8 — `atk7_no_stub.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -85,10 +85,6 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
     let mut result : List Char := []
     let mut i := text.length
     while i > 0
@@ -100,7 +96,7 @@
       let c := text[i - 1]!
       result := upperCp c :: result
       i := i - 1
-    return { chars := result, native := flavour }
+    return { chars := result, native := true }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +122,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 9 — `atk8_stub_as_content_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -85,9 +85,6 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
     let mut result : List Char := []
     let mut i := text.length
@@ -100,7 +97,10 @@
       let c := text[i - 1]!
       result := upperCp c :: result
       i := i - 1
-    return { chars := result, native := flavour }
+    if flavour then
+      return { chars := result, native := flavour }
+    else
+      return { chars := [], native := false }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +126,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 10 — `atk9_lowercase.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,9 +85,6 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
     let mut result : List Char := []
     let mut i := text.length
@@ -98,7 +95,7 @@
       decreasing i
     do
       let c := text[i - 1]!
-      result := upperCp c :: result
+      result := (if 'A' ≤ c ∧ c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c) :: result
       i := i - 1
     return { chars := result, native := flavour }
     -- impl-end
@@ -126,13 +123,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i_2 (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 11 — `atk10_content_via_stub.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,10 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    -- Ungrounded consumed stub standing in for the WHOLE content computation.
+    let chars :| chars = upperSeq text
+    return { chars := chars, native := flavour }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +114,13 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨upperSeq text, rfl, upperSeq_length text⟩
+  all_goals try exact ⟨upperSeq text, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 12 — `atk11_unsound_stub.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,9 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    -- Stub contract strengthened with a conjunct FALSE of the real callee.
+    let flavour :| flavour = true ∧ text = upperSeq text
+    return { chars := text, native := true }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +113,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨true, rfl, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 13 — `atk11c_stub_conj_swapped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,8 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    let flavour :| text = upperSeq text ∧ flavour = true
+    return { chars := text, native := true }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +112,6 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨true, rfl, rfl⟩
+  all_goals try (first | simp_all | grind | omega | rfl)
```

Attack 14 — `atk11d_stub_decide.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,8 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    let flavour :| flavour = (decide (text = upperSeq text) && true)
+    return { chars := text, native := flavour }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +112,6 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨true, rfl, rfl⟩
+  all_goals try (first | simp_all | grind | omega | rfl)
```

Attack 15 — `atk11e_stub_guard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,11 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
     let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    if text = upperSeq text then
+      return { chars := text, native := flavour }
+    else
+      return { chars := text, native := flavour }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +115,6 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨true, rfl, rfl⟩
+  all_goals try (first | simp_all | grind | omega | rfl)
```

Attack 16 — `atk12_assume_false_char.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,22 +85,8 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = upperSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := upperCp c :: result
-      i := i - 1
-    return { chars := result, native := flavour }
+    let junk :| junk = 'a' ∧ junk = 'b'
+    return { chars := text, native := native }
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -126,13 +112,13 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨upperSeq text, rfl, upperSeq_length text⟩
+  all_goals try exact ⟨upperSeq text, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

Attack 17 — `atk13_weak_stub.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out.native = true
   do
     -- impl-start
-    -- Coerce the supplied method to the native text flavour FIRST, via the
-    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
-    -- whose produced value is native irrespective of the supplied flavour).
-    let flavour :| flavour = true
+    let flavour :| flavour = true ∨ flavour = false
     let mut result : List Char := []
     let mut i := text.length
     while i > 0
@@ -126,13 +123,12 @@
 
 prove_correct normalizeMethod by
   loom_solve
-  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
-  -- statement must be shown to HAVE a value, so the method cannot discharge its
-  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
-  -- `true`, the value the real native-flavour constructor produces.
-  · exact ⟨true, rfl⟩
-  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
-  -- stub above binds the first auto-name), and the goal is exactly
-  -- `upperSeq_drop_step`.
-  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
-    simp_all
+  all_goals try exact ⟨true, rfl⟩
+  all_goals try exact ⟨true, rfl, rfl⟩
+  all_goals try (first
+    | (rw [upperSeq_drop_step text i_1 (by omega) (by omega)]; simp_all)
+    | (rw [upperSeq_drop_step text i (by omega) (by omega)]; simp_all)
+    | simp_all
+    | grind
+    | omega
+    | rfl)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- TOTAL correctness. The real method-handling step is a bounded pass over a
   finite method name, so a diverging implementation must NOT satisfy this spec:
   under partial correctness a non-terminating body discharges all three
   `ensures` clauses vacuously and verifies, while its faithful counterpart hangs
   the failing test and does not resolve.

   The `open` is the line that selects the scope, not the `set_option`: both
   namespaces define `WPGen.forWithInvariantLoop`, the later `open` wins, and
   `PartialCorrectness`'s version takes the loop measure and DISCARDS it. So
   `"total"` with `open PartialCorrectness` reads as total and checks as partial.
   Measured here: a spliced diverging loop with the constant measure
   `decreasing spin` fails with `case «decreasing_1: spin» ⊢ False` under
   `TotalCorrectness` and verifies, exit 0, under `PartialCorrectness`. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No module-level `axiom`. The unchanged callee the construction site applies
--  to the supplied method before any further processing — a native-flavour text
--  constructor — is modeled as an imperative-callee `:|` stub inside the impl
--  (`flavour :| flavour = true`, §3): sound by construction, with the weakest
--  sufficient contract pinned (the produced value IS of the native flavour,
--  independent of the argument flavour) and validated against the real callee by
--  axiom_check.py (G-AX). See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Case-normalisation of a single code point: an ASCII lowercase letter maps to
   its uppercase partner; every other code point passes through unchanged. -/
def upperCp (c : Char) : Char :=
  if 'a' ≤ c ∧ c ≤ 'z' then Char.ofNat (c.toNat - 32) else c

/- Case-normalisation of a whole sequence: the per-code-point upper map.
   Front-recursive so a single unfold is available per loop step (the Velvet
   backward-fold pattern, plan §5.4). -/
def upperSeq : List Char → List Char
  | []      => []
  | c :: cs => upperCp c :: upperSeq cs

@[grind] lemma upperSeq_nil : upperSeq [] = [] := rfl
@[grind] lemma upperSeq_cons (c : Char) (cs : List Char) :
    upperSeq (c :: cs) = upperCp c :: upperSeq cs := rfl
-- pure-end

/- The minimal carrier of the two aspects of a text value the desired behaviour
   touches: the code-point content (`chars`) and whether the value is of the
   native text flavour (`native`). Every other aspect of the surrounding
   constructed object is forwarded unchanged and irrelevant here, so it is
   omitted (mapping.md §2). -/
structure TextToken where
  chars  : List Char
  native : Bool
  deriving DecidableEq, Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The method-handling step of request construction.

   It is handed a caller-supplied method name (`text`, its code-point content)
   together with a boolean recording the textual flavour the caller supplied
   (`native`: whether the supplied value was already of the native flavour). It
   returns the `TextToken` carried into the constructed request.

   Desired behaviour:
   * Content — the carried method is the case-normalised supplied name: every
     code point is upper-cased per `upperSeq` and the length is preserved.
   * Flavour — the carried method is of the native text flavour, irrespective of
     the flavour the caller supplied. The carried flavour must NOT depend on the
     `native` input: even a non-native supplied name yields a native carrier.

   `text` and `native` are read-only (neither `mut`): the routine reads them and
   builds a fresh token, mutating nothing it is handed (directive 5). -/
method normalizeMethod (text : List Char) (native : Bool) return (out : TextToken)
  ensures out.chars = upperSeq text
  ensures out.chars.length = text.length
  ensures out.native = true
  do
    -- impl-start
    -- Coerce the supplied method to the native text flavour FIRST, via the
    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
    -- whose produced value is native irrespective of the supplied flavour).
    let flavour :| flavour = true
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = upperSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := upperCp c :: result
      i := i - 1
    return { chars := result, native := flavour }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `upperSeq` peels one `upperCp`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma upperSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    upperSeq (text.drop (i - 1)) = upperCp text[i - 1]! :: upperSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, upperSeq_cons]

/- The carried length equals the supplied length: `upperSeq` is a per-code-point
   map, so it preserves length. -/
@[grind] lemma upperSeq_length (s : List Char) : (upperSeq s).length = s.length := by
  induction s with
  | nil => rfl
  | cons c cs ih => simp [upperSeq_cons, ih]

prove_correct normalizeMethod by
  loom_solve
  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
  -- statement must be shown to HAVE a value, so the method cannot discharge its
  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
  -- `true`, the value the real native-flavour constructor produces.
  · exact ⟨true, rfl⟩
  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
  -- stub above binds the first auto-name), and the goal is exactly
  -- `upperSeq_drop_step`.
  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, instance psf__requests-1724 (velvet). All 19 files confirmed same_spec=True vs the frozen Solution.lean via swebench_unified.markers.same_spec (velvet/lean tables). Verifier: `bash scripts/lean_verify.sh <f>`, run from swe-proof, in concurrent batches of <=4 as instructed.

### Controls
- pos_control.lean (= Solution.lean) -> EXIT 0 (verifies).
- pos_control2.lean (structurally distinct CORRECT impl, loop-free: `return {chars:= text.map upperCp, native:= flavour}` + hmap lemma) -> EXIT 0. Spec is non-vacuous and not too strong; it admits a genuinely different correct shape.
- atk_prepatch.lean (the shipped pre-fix twin, `flavour:= native`) -> EXIT 1, failing exactly `case «ensures_...» ⊢ native = true`. PREPATCH BUG REPRODUCED; the discriminating leg is the flavour leg, as refinement.md claims.
- **NEGATIVE ORACLE CONTROL:** noop.patch (comment-only insertion at the construction site) -> run_resolve completed=True resolved=False (consistent over 3 attempts). GOLD BASELINE: patch.diff -> completed=True resolved=True (all 6 FAIL_TO_PASS + PASS_TO_PASS green). So the harness genuinely discriminates on this cell and a resolved=True below is informative, not a live-internet false green.

### ATTACKS THAT VERIFIED (protocol step 2 — faithful patch materialized and RESOLVE EXECUTED, not speculated)
1. atk7_no_stub.lean (A2 A-leg probe: delete the modeled callee entirely, assert `native:= true` by fiat after the correct upper loop) -> lean_verify EXIT 0. Faithful patch atk7_no_stub.patch (`method = builtin_str(method.upper())` — coercion retained but applied AFTER the upper map, matching the model's op order). Command: `python resolve_one.py atk7_no_stub atk7_no_stub.patch` -> completed=True, resolved=True, note='resolved'. NOT a break: the impl is behaviourally correct (asserting native=true is sound precisely because the real callee guarantees it — the A2 stub is a convenience, and dropping it does not make the impl wrong).
2. atk8_stub_as_content_guard.lean (A2 misuse probe: consume the stub value as a CONTENT guard, so the model's dead branch would be live in the real world) -> EXIT 0. Faithful patch atk8_stub_as_content_guard.patch (isinstance-on-builtin_str guard with an `''` else-branch). Command: `python resolve_one.py atk8_stub_as_content_guard atk8_stub_as_content_guard.patch` -> completed=True, resolved=True. NOT a break: `builtin_str(method)` is always a native str, so the else-branch is dead in the real repo exactly as it is dead in the model — the correspondence HOLDS rather than failing.
Both faithful patches were `git apply --check`ed clean against a worktree of psf_requests.git at base_commit 1ba83c47ce7b177efe90d5f51f7760680f72eda0.

ATTACKS REJECTED (EXIT 1) — every one with a GENUINE SEMANTIC unsolved goal, each given a brute-force proof tail (loom_solve + exact stub witnesses + upperSeq_drop_step at i/i_1/i_2 + simp_all/grind/omega/rfl) so a rejection cannot be a tactic-shape artifact:
- atk1_assume_false.lean (UNSATISFIABLE demonic pick `junk:| junk = 0 ∧ junk = 1`, the prior pass's atk7b assume-false MIRACLE) -> EXIT 1 with `case «choice_1:...» ⊢ False`. IMPORTANT REGRESSION RESULT: the prior recorded audit found this miracle VERIFIED under `open PartialCorrectness`; this bundle now ships `set_option loom.semantics.termination "total"` + `open TotalCorrectness DemonicChoice`, which imposes the `:|` satisfiability obligation and CLOSES the escape. The previously-escalated verifier-hygiene gap is no longer reachable in this bundle.
- atk12_assume_false_char.lean (same miracle at Char, not Nat) -> EXIT 1 (Findable not synthesizable). Confirms atk1's rejection is not a Nat-specific accident.
- atk2_diverge.lean (CONTROL-FLOW-EFFECT / divergence: `while spin >= 0` with constant measure) -> EXIT 1 with `case «decreasing_1: spin» ⊢ False`. Total correctness genuinely rejects the diverging body, exactly as the Solution.lean header comment claims — a hanging faithful counterpart cannot sneak through vacuously.
- atk3_partial_domain.lean (PARTIAL-DOMAIN: correct only on the empty name; non-empty gets raw content + caller's flavour) -> EXIT 1 on BOTH `⊢ native = true` and `⊢ text = upperSeq text`.
- atk4_boundary.lean (BOUNDARY off-by-one, `while i > 1`, drops the first code point) -> EXIT 1 on the length and content legs.
- atk5_skip_a.lean (control-flow effect inside the body: skip normalising 'a') -> EXIT 1 with `⊢ 'a' = upperCp 'a'`.
- atk9_lowercase.lean (per-code-point map of the WRONG direction: length preserved, content lowered) -> EXIT 1 on invariant_2. Shows the length leg alone is not what carries the content obligation.
- atk6_oracle_echo.lean (UNGROUNDED-ORACLE ECHO: `let out:| <the whole postcondition verbatim>`) -> EXIT 1, cannot synthesize `Findable` for the opaque structure predicate. The framework blocks echoing the postcondition instead of computing it.
- atk10_content_via_stub.lean (SHARPEST A-REFERENCE PROBE: replace the deep model A3 with a CONSUMED ungrounded stub `let chars:| chars = upperSeq text`, so the entire content computation is assumed rather than performed) -> EXIT 1, `Findable` not synthesizable. The A3 leg cannot be degraded from A-reference (deep, G-AX-validated) into a consumed axiom — this is the specific weakness class G-EQ exists to hunt, and it is closed.
- atk13_weak_stub.lean (WEAKENED A2 contract `flavour = true ∨ flavour = false`, i.e. a don't-care callee) -> EXIT 1 with `⊢ i = true`. The strong native-flavour contract is genuinely LOAD-BEARING; a don't-care stub does not discharge the flavour leg.
- atk11 family (UNSOUND STRENGTHENED A2 CONTRACT — the strongest break candidate: smuggle into the stub a conjunct FALSE of the real `builtin_str`, namely `text = upperSeq text`, to license skipping the upper map): atk11_unsound_stub.lean and atk11c_stub_conj_swapped.lean -> EXIT 1 but as FRAMEWORK PARSE artifacts ('Failed to parse an assertion without names'), which I did NOT score as semantic rejections. I therefore re-encoded the same attack in Findable-friendly forms: atk11d_stub_decide.lean (`flavour:| flavour = (decide (text = upperSeq text) && true)`) -> EXIT 1 with the DECISIVE semantic goals `⊢ text = upperSeq text` on both ensures_1 and ensures_3; and atk11e_stub_guard.lean (false claim as an if-guard) -> EXIT 1 with `if_neg: ¬text = upperSeq text ⊢ False`. Verdict on this class: the verifier will not let a `:|` stub ASSUME a property of its argument for free — an argument-constraining conjunct becomes a proof obligation on the caller's actual input, so an unsound strengthening of the A2 contract is not exploitable.

### REFINEMENT.MD LEG AUDIT (protocol step 3 — no kind-3 leg; A-leg correspondence verified against the real callees at base_commit)
- A1 = R (a text value -> `List Char` content + `native: Bool` flavour). Sound type refinement; the two facets modeled are exactly the two the change touches.
- A2 = A-consumed (`flavour:| flavour = true` <-> `builtin_str`, the UNCHANGED callee the patch newly invokes). Correspondence CONFIRMED by reading the real repo: requests/compat.py binds `builtin_str = str` BEFORE `str = unicode` under is_py2 (and `builtin_str = str` under is_py3), so `builtin_str(...)` yields a native-flavour value irrespective of the argument's flavour — precisely and only the contract the stub pins. The contract is the WEAKEST sufficient one (it claims nothing about character content), it is genuinely consumed (atk13 proves weakening it breaks the proof), and it is satisfiable (the proof discharges the `:|` obligation with the witness `true`, so no vacuity).
- A3 = A-reference (`upperCp`/`upperSeq` deep model <-> `str.upper`), NOT a consumed axiom — atk10 confirms it cannot be turned into one. I re-ran the correspondence myself rather than trusting axiom_check.py: exhaustive ASCII sweep 0-127 -> 0 mismatches; 10 HTTP method-name spellings -> 0 mismatches; 20 000 randomized ASCII strings (seed 1724) -> 0 mismatches. Documented boundary reproduced and confirmed OUT of domain: 'ß'->real 'SS' vs model 'ß' (length-changing), 'ﬀ'->'FF', 'é'->'É', 'µ'->'Μ'. HTTP method names are ASCII tokens and no FAIL_TO_PASS/PASS_TO_PASS test uses a non-ASCII method, so the divergence cannot admit a non-resolving impl nor reject a resolving one; mapping.md §3.2 scopes this explicitly.
- A4 = R (`return {chars, native}` <-> the `method` field of the constructed `Request`; other fields forwarded unchanged and omitted).
All legs are R / A-consumed / A-reference / I. NO kind-3 (unexpressible-changed-op) leg: the one genuinely changed operation — force the native flavour BEFORE case-normalisation — is carried by the A-consumed stub over the unchanged newly-invoked callee plus the `out.native = true` postcondition, which is exactly the leg the prepatch twin fails.

**CONCLUSION:** 17 same-spec attacks run (>=5 required), spanning partial-domain, boundary, control-flow-effect/divergence, ungrounded-oracle echo, assume-false miracle (two types), and four distinct A-leg degradations (delete the stub, misuse the stub as a content guard, replace the deep model with a consumed stub, weaken and unsoundly strengthen the stub contract). Fifteen were rejected with genuine semantic goals; the two that verified had their faithful refined patches EXECUTED through the official harness and BOTH RESOLVED (with gold=resolved / noop=not-resolved proving the oracle discriminates). No verifying wrong impl with a non-resolving faithful patch exists among these attacks, so verify => correct is not falsified here. G-EQ SOUND. Advisory note for the framework (not a defect of this bundle): the atk11/atk11c 'Failed to parse an assertion without names' outcome means some ill-formed `:|` predicates surface as parse errors rather than proof failures — an auditor who scored those as semantic rejections would be over-crediting the spec, which is why I re-encoded them as atk11d/atk11e.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | listed per attack in the audit record below |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | listed per attack in the audit record below |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl was found whose faithful refined patch fails to resolve. The two same-spec attacks that VERIFIED (atk7_no_stub, atk8_stub_as_content_guard) both had their faithful refined patches materialized and RUN through the official harness (run_resolve, psf__requests-1724): both completed=True resolved=True — i.e. they are behaviourally correct impls, not counterexamples. Oracle discrimination was proven in the same session: gold patch resolved=True, noop patch resolved=False ('patch did not resolve in 3 attempts (consistent — not flaky)').
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1_assume_false.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2_diverge.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4_boundary.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk5_skip_a.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk6_oracle_echo.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk7_no_stub.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk8_stub_as_content_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 10 — `atk9_lowercase.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk10_content_via_stub.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk11_unsound_stub.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk11c_stub_conj_swapped.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk11d_stub_decide.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk11e_stub_guard.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk12_assume_false_char.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk13_weak_stub.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- TOTAL correctness. The real method-handling step is a bounded pass over a
   finite method name, so a diverging implementation must NOT satisfy this spec:
   under partial correctness a non-terminating body discharges all three
   `ensures` clauses vacuously and verifies, while its faithful counterpart hangs
   the failing test and does not resolve.

   The `open` is the line that selects the scope, not the `set_option`: both
   namespaces define `WPGen.forWithInvariantLoop`, the later `open` wins, and
   `PartialCorrectness`'s version takes the loop measure and DISCARDS it. So
   `"total"` with `open PartialCorrectness` reads as total and checks as partial.
   Measured here: a spliced diverging loop with the constant measure
   `decreasing spin` fails with `case «decreasing_1: spin» ⊢ False` under
   `TotalCorrectness` and verifies, exit 0, under `PartialCorrectness`. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No module-level `axiom`. The unchanged callee the construction site applies
--  to the supplied method before any further processing — a native-flavour text
--  constructor — is modeled as an imperative-callee `:|` stub inside the impl
--  (`flavour :| flavour = true`, §3): sound by construction, with the weakest
--  sufficient contract pinned (the produced value IS of the native flavour,
--  independent of the argument flavour) and validated against the real callee by
--  axiom_check.py (G-AX). See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Case-normalisation of a single code point: an ASCII lowercase letter maps to
   its uppercase partner; every other code point passes through unchanged. -/
def upperCp (c : Char) : Char :=
  if 'a' ≤ c ∧ c ≤ 'z' then Char.ofNat (c.toNat - 32) else c

/- Case-normalisation of a whole sequence: the per-code-point upper map.
   Front-recursive so a single unfold is available per loop step (the Velvet
   backward-fold pattern, plan §5.4). -/
def upperSeq : List Char → List Char
  | []      => []
  | c :: cs => upperCp c :: upperSeq cs

@[grind] lemma upperSeq_nil : upperSeq [] = [] := rfl
@[grind] lemma upperSeq_cons (c : Char) (cs : List Char) :
    upperSeq (c :: cs) = upperCp c :: upperSeq cs := rfl
-- pure-end

/- The minimal carrier of the two aspects of a text value the desired behaviour
   touches: the code-point content (`chars`) and whether the value is of the
   native text flavour (`native`). Every other aspect of the surrounding
   constructed object is forwarded unchanged and irrelevant here, so it is
   omitted (mapping.md §2). -/
structure TextToken where
  chars  : List Char
  native : Bool
  deriving DecidableEq, Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The method-handling step of request construction.

   It is handed a caller-supplied method name (`text`, its code-point content)
   together with a boolean recording the textual flavour the caller supplied
   (`native`: whether the supplied value was already of the native flavour). It
   returns the `TextToken` carried into the constructed request.

   Desired behaviour:
   * Content — the carried method is the case-normalised supplied name: every
     code point is upper-cased per `upperSeq` and the length is preserved.
   * Flavour — the carried method is of the native text flavour, irrespective of
     the flavour the caller supplied. The carried flavour must NOT depend on the
     `native` input: even a non-native supplied name yields a native carrier.

   `text` and `native` are read-only (neither `mut`): the routine reads them and
   builds a fresh token, mutating nothing it is handed (directive 5). -/
method normalizeMethod (text : List Char) (native : Bool) return (out : TextToken)
  ensures out.chars = upperSeq text
  ensures out.chars.length = text.length
  ensures out.native = true
  do
    -- impl-start
    -- Coerce the supplied method to the native text flavour FIRST, via the
    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
    -- whose produced value is native irrespective of the supplied flavour).
    let flavour :| flavour = true
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = upperSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := upperCp c :: result
      i := i - 1
    return { chars := result, native := flavour }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `upperSeq` peels one `upperCp`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma upperSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    upperSeq (text.drop (i - 1)) = upperCp text[i - 1]! :: upperSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, upperSeq_cons]

/- The carried length equals the supplied length: `upperSeq` is a per-code-point
   map, so it preserves length. -/
@[grind] lemma upperSeq_length (s : List Char) : (upperSeq s).length = s.length := by
  induction s with
  | nil => rfl
  | cons c cs ih => simp [upperSeq_cons, ih]

prove_correct normalizeMethod by
  loom_solve
  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
  -- statement must be shown to HAVE a value, so the method cannot discharge its
  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
  -- `true`, the value the real native-flavour constructor produces.
  · exact ⟨true, rfl⟩
  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
  -- stub above binds the first auto-name), and the goal is exactly
  -- `upperSeq_drop_step`.
  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, instance psf__requests-1724 (velvet). All 19 files confirmed same_spec=True vs the frozen Solution.lean via swebench_unified.markers.same_spec (velvet/lean tables). Verifier: `bash scripts/lean_verify.sh <f>`, run from swe-proof, in concurrent batches of <=4 as instructed.

### Controls
- pos_control.lean (= Solution.lean) -> EXIT 0 (verifies).
- pos_control2.lean (structurally distinct CORRECT impl, loop-free: `return {chars:= text.map upperCp, native:= flavour}` + hmap lemma) -> EXIT 0. Spec is non-vacuous and not too strong; it admits a genuinely different correct shape.
- atk_prepatch.lean (the shipped pre-fix twin, `flavour:= native`) -> EXIT 1, failing exactly `case «ensures_...» ⊢ native = true`. PREPATCH BUG REPRODUCED; the discriminating leg is the flavour leg, as refinement.md claims.
- **NEGATIVE ORACLE CONTROL:** noop.patch (comment-only insertion at the construction site) -> run_resolve completed=True resolved=False (consistent over 3 attempts). GOLD BASELINE: patch.diff -> completed=True resolved=True (all 6 FAIL_TO_PASS + PASS_TO_PASS green). So the harness genuinely discriminates on this cell and a resolved=True below is informative, not a live-internet false green.

### ATTACKS THAT VERIFIED (protocol step 2 — faithful patch materialized and RESOLVE EXECUTED, not speculated)
1. atk7_no_stub.lean (A2 A-leg probe: delete the modeled callee entirely, assert `native:= true` by fiat after the correct upper loop) -> lean_verify EXIT 0. Faithful patch atk7_no_stub.patch (`method = builtin_str(method.upper())` — coercion retained but applied AFTER the upper map, matching the model's op order). Command: `python resolve_one.py atk7_no_stub atk7_no_stub.patch` -> completed=True, resolved=True, note='resolved'. NOT a break: the impl is behaviourally correct (asserting native=true is sound precisely because the real callee guarantees it — the A2 stub is a convenience, and dropping it does not make the impl wrong).
2. atk8_stub_as_content_guard.lean (A2 misuse probe: consume the stub value as a CONTENT guard, so the model's dead branch would be live in the real world) -> EXIT 0. Faithful patch atk8_stub_as_content_guard.patch (isinstance-on-builtin_str guard with an `''` else-branch). Command: `python resolve_one.py atk8_stub_as_content_guard atk8_stub_as_content_guard.patch` -> completed=True, resolved=True. NOT a break: `builtin_str(method)` is always a native str, so the else-branch is dead in the real repo exactly as it is dead in the model — the correspondence HOLDS rather than failing.
Both faithful patches were `git apply --check`ed clean against a worktree of psf_requests.git at base_commit 1ba83c47ce7b177efe90d5f51f7760680f72eda0.

ATTACKS REJECTED (EXIT 1) — every one with a GENUINE SEMANTIC unsolved goal, each given a brute-force proof tail (loom_solve + exact stub witnesses + upperSeq_drop_step at i/i_1/i_2 + simp_all/grind/omega/rfl) so a rejection cannot be a tactic-shape artifact:
- atk1_assume_false.lean (UNSATISFIABLE demonic pick `junk:| junk = 0 ∧ junk = 1`, the prior pass's atk7b assume-false MIRACLE) -> EXIT 1 with `case «choice_1:...» ⊢ False`. IMPORTANT REGRESSION RESULT: the prior recorded audit found this miracle VERIFIED under `open PartialCorrectness`; this bundle now ships `set_option loom.semantics.termination "total"` + `open TotalCorrectness DemonicChoice`, which imposes the `:|` satisfiability obligation and CLOSES the escape. The previously-escalated verifier-hygiene gap is no longer reachable in this bundle.
- atk12_assume_false_char.lean (same miracle at Char, not Nat) -> EXIT 1 (Findable not synthesizable). Confirms atk1's rejection is not a Nat-specific accident.
- atk2_diverge.lean (CONTROL-FLOW-EFFECT / divergence: `while spin >= 0` with constant measure) -> EXIT 1 with `case «decreasing_1: spin» ⊢ False`. Total correctness genuinely rejects the diverging body, exactly as the Solution.lean header comment claims — a hanging faithful counterpart cannot sneak through vacuously.
- atk3_partial_domain.lean (PARTIAL-DOMAIN: correct only on the empty name; non-empty gets raw content + caller's flavour) -> EXIT 1 on BOTH `⊢ native = true` and `⊢ text = upperSeq text`.
- atk4_boundary.lean (BOUNDARY off-by-one, `while i > 1`, drops the first code point) -> EXIT 1 on the length and content legs.
- atk5_skip_a.lean (control-flow effect inside the body: skip normalising 'a') -> EXIT 1 with `⊢ 'a' = upperCp 'a'`.
- atk9_lowercase.lean (per-code-point map of the WRONG direction: length preserved, content lowered) -> EXIT 1 on invariant_2. Shows the length leg alone is not what carries the content obligation.
- atk6_oracle_echo.lean (UNGROUNDED-ORACLE ECHO: `let out:| <the whole postcondition verbatim>`) -> EXIT 1, cannot synthesize `Findable` for the opaque structure predicate. The framework blocks echoing the postcondition instead of computing it.
- atk10_content_via_stub.lean (SHARPEST A-REFERENCE PROBE: replace the deep model A3 with a CONSUMED ungrounded stub `let chars:| chars = upperSeq text`, so the entire content computation is assumed rather than performed) -> EXIT 1, `Findable` not synthesizable. The A3 leg cannot be degraded from A-reference (deep, G-AX-validated) into a consumed axiom — this is the specific weakness class G-EQ exists to hunt, and it is closed.
- atk13_weak_stub.lean (WEAKENED A2 contract `flavour = true ∨ flavour = false`, i.e. a don't-care callee) -> EXIT 1 with `⊢ i = true`. The strong native-flavour contract is genuinely LOAD-BEARING; a don't-care stub does not discharge the flavour leg.
- atk11 family (UNSOUND STRENGTHENED A2 CONTRACT — the strongest break candidate: smuggle into the stub a conjunct FALSE of the real `builtin_str`, namely `text = upperSeq text`, to license skipping the upper map): atk11_unsound_stub.lean and atk11c_stub_conj_swapped.lean -> EXIT 1 but as FRAMEWORK PARSE artifacts ('Failed to parse an assertion without names'), which I did NOT score as semantic rejections. I therefore re-encoded the same attack in Findable-friendly forms: atk11d_stub_decide.lean (`flavour:| flavour = (decide (text = upperSeq text) && true)`) -> EXIT 1 with the DECISIVE semantic goals `⊢ text = upperSeq text` on both ensures_1 and ensures_3; and atk11e_stub_guard.lean (false claim as an if-guard) -> EXIT 1 with `if_neg: ¬text = upperSeq text ⊢ False`. Verdict on this class: the verifier will not let a `:|` stub ASSUME a property of its argument for free — an argument-constraining conjunct becomes a proof obligation on the caller's actual input, so an unsound strengthening of the A2 contract is not exploitable.

### REFINEMENT.MD LEG AUDIT (protocol step 3 — no kind-3 leg; A-leg correspondence verified against the real callees at base_commit)
- A1 = R (a text value -> `List Char` content + `native: Bool` flavour). Sound type refinement; the two facets modeled are exactly the two the change touches.
- A2 = A-consumed (`flavour:| flavour = true` <-> `builtin_str`, the UNCHANGED callee the patch newly invokes). Correspondence CONFIRMED by reading the real repo: requests/compat.py binds `builtin_str = str` BEFORE `str = unicode` under is_py2 (and `builtin_str = str` under is_py3), so `builtin_str(...)` yields a native-flavour value irrespective of the argument's flavour — precisely and only the contract the stub pins. The contract is the WEAKEST sufficient one (it claims nothing about character content), it is genuinely consumed (atk13 proves weakening it breaks the proof), and it is satisfiable (the proof discharges the `:|` obligation with the witness `true`, so no vacuity).
- A3 = A-reference (`upperCp`/`upperSeq` deep model <-> `str.upper`), NOT a consumed axiom — atk10 confirms it cannot be turned into one. I re-ran the correspondence myself rather than trusting axiom_check.py: exhaustive ASCII sweep 0-127 -> 0 mismatches; 10 HTTP method-name spellings -> 0 mismatches; 20 000 randomized ASCII strings (seed 1724) -> 0 mismatches. Documented boundary reproduced and confirmed OUT of domain: 'ß'->real 'SS' vs model 'ß' (length-changing), 'ﬀ'->'FF', 'é'->'É', 'µ'->'Μ'. HTTP method names are ASCII tokens and no FAIL_TO_PASS/PASS_TO_PASS test uses a non-ASCII method, so the divergence cannot admit a non-resolving impl nor reject a resolving one; mapping.md §3.2 scopes this explicitly.
- A4 = R (`return {chars, native}` <-> the `method` field of the constructed `Request`; other fields forwarded unchanged and omitted).
All legs are R / A-consumed / A-reference / I. NO kind-3 (unexpressible-changed-op) leg: the one genuinely changed operation — force the native flavour BEFORE case-normalisation — is carried by the A-consumed stub over the unchanged newly-invoked callee plus the `out.native = true` postcondition, which is exactly the leg the prepatch twin fails.

**CONCLUSION:** 17 same-spec attacks run (>=5 required), spanning partial-domain, boundary, control-flow-effect/divergence, ungrounded-oracle echo, assume-false miracle (two types), and four distinct A-leg degradations (delete the stub, misuse the stub as a content guard, replace the deep model with a consumed stub, weaken and unsoundly strengthen the stub contract). Fifteen were rejected with genuine semantic goals; the two that verified had their faithful refined patches EXECUTED through the official harness and BOTH RESOLVED (with gold=resolved / noop=not-resolved proving the oracle discriminates). No verifying wrong impl with a non-resolving faithful patch exists among these attacks, so verify => correct is not falsified here. G-EQ SOUND. Advisory note for the framework (not a defect of this bundle): the atk11/atk11c 'Failed to parse an assertion without names' outcome means some ill-formed `:|` predicates surface as parse errors rather than proof failures — an auditor who scored those as semantic rejections would be over-crediting the spec, which is why I re-encoded them as atk11d/atk11e.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** MECHANICAL CHECKS: markers.same_spec(Solution.lean, Solution_prepatch.lean) with the velvet backend = True — frozen spec region byte-identical across pre/post. scripts/lean_verify.sh on Solution.lean = exit 0 (verifies). Solution_prepatch.lean FAILS with the sole unsolved goal `⊢ native = true` (all content/loop legs discharge identically) — the spec senses exactly the patch delta and nothing more, so it is neither vacuous nor drifted.

**REFERENCE DISCIPLINE OBSERVED:** I compared the modelled function against the base_commit worktree WITH patch.diff APPLIED (fresh worktree at 1ba83c47, `git apply` confirmed the inserted `method = builtin_str(method)` above `method = method.upper()`). I did NOT report the patch delta itself as a divergence. Base commit was used only for the untouched callees the model axiomatizes (requests/compat.py builtin_str binding, read at base: `builtin_str = str` bound BEFORE the `str = unicode` rebind under is_py2 — confirming the stub's native-flavour contract; and requests/models.py prepare_method, which applies no transform beyond.upper()).

**WHY NOT UNFAITHFUL:** the divergence has the surface signature of a too-strong spec — on text=['ß'] the spec would reject a faithful implementation that really calls str.upper, since both `out.chars = upperSeq text` and the length postcondition fail. I took this seriously rather than waving it through. It does not rise to a defect because the divergence set is exactly the complement of the domain the model claims, and that scoping is DECLARED IN ADVANCE, not retrofitted: mapping.md §3.2 states the deep model 'claims faithfulness only on this ASCII method domain; full-Unicode str.upper has locale/multi-char expansions outside it, which the tested method names never exercise,' and refinement.md tags the step A-reference (deep model validated == real callee, no consumed upper axiom).

Consequently the divergence can neither admit a non-resolving implementation nor reject a resolving one: any impl satisfying the spec is, on all ASCII method names, bit-identical to builtin_str(method).upper(), and the gold patch resolves. The discriminating content of the fix — carried flavour must not depend on supplied flavour — is fully captured by `ensures out.native = true`, which is precisely the goal the prepatch variant cannot discharge.

This is a correctly-scoped, documented modelling boundary, not spec drift. Verdict FAITHFUL.

Counterexample / evidence:

```
No admissible counterexample. The one real model/callee divergence (non-ASCII, cited above) is unreachable in the resolution-relevant domain on three independent grounds:

(1) EXHAUSTIVE ASCII AGREEMENT — 0 mismatches: all 128 single code points; all 16,384 ASCII ordered pairs; ~300k ASCII triples (context-dependence probe, e.g. Greek final-sigma-style rules — none apply); 0 length-changing cases on ASCII. Bundle's own axiom_check.py (G-AX) exits 0 (128-sweep + 10 HTTP names + 20,000 fuzz) and conformance_check.py exits 0 (100,144 inputs, seed 1724, 0 disagreements).

(2) DOMAIN IS ASCII BY CONSTRUCTION — an HTTP method is an RFC 7230 `token`; the tchar set is ASCII-only. Every method= value in the repo's test_requests.py is 'POST' or the new test's u'POST' — all ASCII. No test exercises a non-ASCII method.

(3) UNREACHABLE ON THE ISSUE'S RUNTIME — on Python 2.7 (the runtime the problem_statement concerns), builtin_str is the byte-str constructor; str(u'\xdf') raises UnicodeEncodeError under the ascii codec BEFORE .upper() is ever reached. So the diverging inputs cannot flow through the patched line at all on py2.

Flavour leg probed for a too-strong edge: builtin_str applied to an object whose __str__ returns a str SUBCLASS yields type(v) is str == False, but isinstance(v, str) == True, so the modelled abstraction (native byte-str flavour vs unicode — mapping.md §2) still holds; and no test passes a str subclass as method. The flavour postcondition out.native = true is not too strong.
```

**MECHANICAL CHECKS:** markers.same_spec(Solution.lean, Solution_prepatch.lean) with the velvet backend = True — frozen spec region byte-identical across pre/post. scripts/lean_verify.sh on Solution.lean = exit 0 (verifies). Solution_prepatch.lean FAILS with the sole unsolved goal `⊢ native = true` (all content/loop legs discharge identically) — the spec senses exactly the patch delta and nothing more, so it is neither vacuous nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: standard (NOT relaxed) — meta.json has no `relaxed_leakage` key (confirmed: keys are additional_change_sites, axioms, band, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, same_spec, schema_version, spec_provenance, string_modeling, version) and no RELAXED_LEAKAGE.md exists in the bundle. So no unavoidability argument to re-derive; I judged this as an ordinary leakage screen.

### WHAT I RAN (my own measurements, not inherited from verdict.md):
1. Frozen-region identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) = True. markers.region_hashes(Solution.lean) recomputed and matches the G-HYGIENE record exactly on all four regions (axioms 4db5e541…, pure 93b7837b…, impl 8e610495…, spec_view e1a109b0…), so the spec view I reviewed is the stamped artifact.
2. Mechanical screen re-run: leakage.screen(Solution.lean, velvet, instance['patch'], instance['problem_statement'], instance['test_patch']) -> LeakageReport(hard_failures=[], warnings=[]), passed=True.
3. Repo-identifier sweep over markers.spec_view (post AND prepatch): zero hits for builtin_str, sessions, compat, requests, urljoin/urlparse/urlunparse/OrderedDict, httpbin, test_unicode, status_code, files, multipart, header, UnicodeDecode, \.upper, py2, py3, unicode, bare `str`, 1724, base_commit 1ba83c47…, and the line numbers 313 / 278. The only regex hit was the harness's own `-- imports-end` marker. No diff hunk is quoted and no changed file is named anywhere in the view.
4. Discriminator is load-bearing, not narrated: I stripped ALL Lean comments (block `/- -/` and line `--`) from both variants and re-ran scripts/lean_verify.sh. Comment-free post-image: exit 0. Comment-free PRE-image: exit 1 with `case «ensures_1: out.native = true» ⊢ native = true` (uncomment prepatch also exit 1, same goal). So the sensing lives in the formal clause `ensures out.native = true` against a `native: Bool` input, not in prose — the doc-comment sentences carry no information the ensures does not.

LEAKAGE JUDGEMENT vs the PUBLIC problem_statement (hints_text NOT consulted): the statement itself discloses (a) the exact contrast `method='POST'` vs `method=u'POST'`, i.e. that the caller-supplied text FLAVOUR is the input that matters; (b) the diagnosis "u'POST' is infecting the header with unicode when it should be a string", i.e. the required post-state is a native str; (c) the offending site verbatim, `req.method = method.upper()`, i.e. that case-normalisation is the operation in play. The spec view exposes exactly those three facts, abstracted: `TextToken{chars, native}`, `ensures out.chars = upperSeq text` + length preservation (the publicly-named `.upper()`), and `ensures out.native = true` with the note that the carried flavour must not depend on the `native` input. Nothing narrower than the statement.

WHAT IS WITHHELD (the actual gold edit): the callee identity `builtin_str`, the `from.compat import …, builtin_str` import hunk, the file `requests/sessions.py`, and the inserted statement `method = builtin_str(method)` appear nowhere in the spec view. The axioms-region comment describes only "a native-flavour text constructor" modeled as an imperative-callee `:|` stub — a mechanism-free restatement of "it should be a string". Those concretes appear only in mapping.md §3.1 / refinement.md §A, which are auxiliary docs outside markers.spec_view. The impl region (where `let flavour:| flavour = true` sits) is elided in the view, so the coerce-before-upper ORDERING is not exposed either; and it is not discriminating regardless, since on the ASCII method-name domain the two orders agree and neither ensures clause encodes order. A solver reading only the view must invent some native-flavour coercion — precisely the task the public statement sets.

CORE GATES I LEANED ON, INDEPENDENTLY CONFIRMED: G-VERIFY (I re-verified Solution.lean, exit 0) and G-DIFF (I re-verified Solution_prepatch.lean, exit 1 on `native = true` — the flavour leg, not a content/termination artifact). Termination note checked as sound: the file has `open TotalCorrectness DemonicChoice`, matching the header comment's own warning that the later `open`, not the set_option, selects the scope; so the pre-image failure is a real postcondition failure and not a vacuity artifact.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as its own finding, per instructions): leakage.reviewer_directed() returns [] for refinement.md, mapping.md and verdict.md. Grep for panel/attacker/reviewer/submit_result/NO-LEAKAGE/relaxed across Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md, axiom_check.py, conformance_check.py: no hits. verdict.md does contain a prior G-PANEL-3 record (agent_verdict NO-LEAKAGE) but it is a historical stamp addressed to no one and issues no instruction about how to record; I did not inherit it — the measurements above are mine and were run before reading it. Nothing in this bundle attempts to direct my verdict.

**CONCLUSION:** the spec view is faithful to the public problem_statement's disclosed intent and withholds the gold patch's mechanism. NO-LEAKAGE.

**SCOPE:** standard (NOT relaxed) — meta.json has no `relaxed_leakage` key (confirmed: keys are additional_change_sites, axioms, band, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, same_spec, schema_version, spec_provenance, string_modeling, version) and no RELAXED_LEAKAGE.md exists in the bundle. So no unavoidability argument to re-derive; I judged this as an ordinary leakage screen.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
