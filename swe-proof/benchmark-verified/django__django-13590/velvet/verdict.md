# P2 adversarial audit — django__django-13590

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 6 | `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = resolvedSeq s.positionalCtor s.items f` pins the output to the UNIQUE value `Except.ok {positionalCtor := s.positionalCtor, items := s.items.map f}`. Every verifying same-spec impl computes exactly this value, which under mapping.md §2's R-bijection (positionalCtor ↔ hasattr(type_,'_make'); items ↔ list(value); f ↔ resolve_lookup_value; always-ok ↔ gold never raising) refines to the gold patch's `type_(*values)`/`type_(values)` dispatch. Hence every verifying attack's faithful refined patch is byte-identical to the gold patch.diff, which run_resolve confirmed RESOLVES (resolved=true, completed=true, single attempt, not flaky). No verify⇏¬resolve gap exists.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return resolvedSeq s.positionalCtor s.items f
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return Except.ok { positionalCtor := s.positionalCtor, items := s.items.map f }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,20 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
     let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
     let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
+      if s.items.isEmpty then rebuildPositional s.positionalCtor resolved
+      else if s.positionalCtor then rebuildPositional s.positionalCtor resolved
       else rebuildIterable s.positionalCtor resolved
     return result
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,19 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
     let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    if s.positionalCtor = true then
+      return rebuildPositional s.positionalCtor resolved
+    else
+      return rebuildIterable s.positionalCtor resolved
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return Except.ok { positionalCtor := s.positionalCtor, items := s.items.map (fun x => f x) }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,19 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
     let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
     let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
+      if _h : s.positionalCtor = true then rebuildPositional s.positionalCtor resolved
       else rebuildIterable s.positionalCtor resolved
     return result
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,17 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    let a := s.items.map f
+    let b := a
+    return Except.ok { positionalCtor := s.positionalCtor, items := b }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,19 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
     let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    if s.positionalCtor then
+      return rebuildPositional s.positionalCtor resolved
+    else
+      return Except.ok { positionalCtor := s.positionalCtor, items := resolved }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,19 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
     let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
     let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
+      if s.positionalCtor then rebuildIterable s.positionalCtor resolved
+      else rebuildPositional s.positionalCtor resolved
     return result
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,16 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
     let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return rebuildPositional s.positionalCtor resolved
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return Except.ok { positionalCtor := s.positionalCtor, items := s.items }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return Except.ok { positionalCtor := s.positionalCtor, items := (s.items.map f).reverse }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return Except.error RebuildErr.iterableNotAccepted
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-element resolution this operation applies to each
@@ -84,18 +84,15 @@
   ensures out = resolvedSeq s.positionalCtor s.items f
   do
     -- impl-start
-    -- Resolve each member independently (unchanged across the fix).
-    let resolved := s.items.map f
-    -- Reconstruct preserving the sequence's type. A type requiring positional
-    -- members is reconstructed by supplying them positionally; any other type
-    -- is reconstructed from the iterable of resolved members.
-    let result : Except RebuildErr SeqVal :=
-      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
-      else rebuildIterable s.positionalCtor resolved
-    return result
+    return Except.ok { positionalCtor := !s.positionalCtor, items := s.items.map f }
     -- impl-end
 
 prove_correct reconstructSequence by
   loom_solve
-  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
-  split_ifs <;> simp_all
+  all_goals (
+    set_option linter.unusedSimpArgs false in
+    first
+      | rfl
+      | (simp only [rebuildPositional, rebuildIterable, resolvedSeq]; try (split_ifs <;> simp_all))
+      | (split_ifs <;> simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
+      | simp_all [rebuildPositional, rebuildIterable, resolvedSeq])
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The per-element resolution this operation applies to each
   member of a sequence is modeled as an arbitrary total function `f`; the
   postconditions hold for EVERY `f`, so it needs no contract (it is strictly
   weaker than any concrete callee). The sequence-reconstruction behaviour — the
   only thing this bundle pins — is modeled DEEPLY in the `pure` region, not
   behind an axiom. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The outcome of reconstructing a sequence from its per-element-resolved
   members. Two reconstruction failures are distinguishable: handing the
   sequence's type a single iterable when that type instead requires its
   members as separate positional arguments, and — dually — handing a type
   its members as separate positional arguments when that type instead takes
   exactly one iterable. -/
inductive RebuildErr where
  | iterableNotAccepted
  | positionalNotAccepted
  deriving DecidableEq

/- The observable content of a reconstructed sequence: whether its type requires
   its members supplied positionally (rather than as one iterable), and the
   members themselves in order. These are the only fields the desired behaviour
   constrains (mapping.md §2). -/
structure SeqVal where
  positionalCtor : Bool
  items : List Int
  deriving DecidableEq

/- Reconstruction that supplies the members as separate positional arguments.
   A type that requires its members positionally accepts them, and the
   reconstructed sequence keeps its type and carries the members through in
   order. Any OTHER sequence type's constructor takes its members as one
   iterable, so handing it the members as separate positional arguments fails —
   except in the degenerate no-member case, where nothing is passed and the
   empty sequence is built. -/
def rebuildPositional (positionalCtor : Bool) (items : List Int) :
    Except RebuildErr SeqVal :=
  if positionalCtor || items.isEmpty then
    Except.ok { positionalCtor := positionalCtor, items := items }
  else Except.error .positionalNotAccepted

/- Reconstruction that hands the type a single iterable of the members. This
   succeeds only for a type that accepts an iterable; a type that instead
   requires positional members cannot be reconstructed this way. -/
def rebuildIterable (positionalCtor : Bool) (items : List Int) :
    Except RebuildErr SeqVal :=
  if positionalCtor then Except.error .iterableNotAccepted
  else Except.ok { positionalCtor := positionalCtor, items := items }

/- The desired reconstruction outcome: a sequence whose every member has been
   independently resolved (here by an arbitrary resolver `f`), reconstructed so
   that it ALWAYS succeeds and keeps both its type and its resolved members in
   order — regardless of whether the type requires positional members. -/
def resolvedSeq (positionalCtor : Bool) (items : List Int) (f : Int → Int) :
    Except RebuildErr SeqVal :=
  Except.ok { positionalCtor := positionalCtor, items := items.map f }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the members of a sequence value independently (each via the resolver
   `f`) and reconstruct the sequence. Desired behaviour: reconstruction must
   succeed for EVERY sequence type and preserve the type, even one that requires
   its members supplied as separate positional arguments; the result carries the
   per-member-resolved values in their original order. (`positionalCtor`
   abstracts "this type must receive its members positionally"; `f` abstracts the
   independent per-member resolution — mapping.md §1/§2.) -/
method reconstructSequence (s : SeqVal) (f : Int → Int)
    return (out : Except RebuildErr SeqVal)
  ensures out = resolvedSeq s.positionalCtor s.items f
  do
    -- impl-start
    -- Resolve each member independently (unchanged across the fix).
    let resolved := s.items.map f
    -- Reconstruct preserving the sequence's type. A type requiring positional
    -- members is reconstructed by supplying them positionally; any other type
    -- is reconstructed from the iterable of resolved members.
    let result : Except RebuildErr SeqVal :=
      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
      else rebuildIterable s.positionalCtor resolved
    return result
    -- impl-end

prove_correct reconstructSequence by
  loom_solve
  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
  split_ifs <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol complete

SAME-SPEC: all 14 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). NOTE: proof-region edits (set_option must live INSIDE the tactic body, not before `prove_correct`, or spec_view keeps the extra line and same_spec flips False) do not affect the spec signature — verified.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently ≤4 at a time):
- VERIFYING (exit 0), same-spec, all compute the pinned unique value:
  atk_1 ungrounded-oracle echo (`return resolvedSeq s.positionalCtor s.items f`)
  atk_2 direct Except.ok literal
  atk_3 empty-first three-way branch (isEmpty→positional, then positional/iterable)
  atk_4 if `s.positionalCtor = true` dispatch (positional/iterable)
  atk_5 eta-expanded map `(fun x => f x)`
  atk_6 dependent-if `if _h : s.positionalCtor = true`
  atk_7 redundant let-chain then Except.ok literal
  atk_8 positional branch via rebuildPositional else inline Except.ok
- CORRECTLY REJECTED (exit 1) — genuine unsolved-goal failures (spec has teeth):
  atk_9  swapped branches (control-flow-effect) — goal reduces to error=ok
  atk_10 always rebuildPositional (partial-domain) — ⊢ False on nonempty non-positional
  atk_11 drops f, returns s.items — ⊢ Except.ok s = ok(items.map f)
  atk_12 reversed order `.reverse` — value mismatch
  atk_13 ungrounded always-error — error=ok
  atk_14 flipped positionalCtor field — value mismatch
- pos_control (gold impl): VERIFY (exit 0).

PREPATCH: Solution_prepatch.lean fails (exit 1). Confirmed via a tolerant-proof probe (prepatch_probe.lean) that the failure is a GENUINE spec-goal, not a tactic artifact: goal reduces to `(if s.positionalCtor then Except.error .iterableNotAccepted else ok(...)) = ok(...)`, unprovable (requires s.positionalCtor=false) — exactly the namedtuple case test_range_lookup_namedtuple exercises. prepatch_reproduced=true.

RESOLVE (MANDATORY step for every verifying attack): the faithful refined patch of each of atk_1..8 is byte-identical to the gold patch.diff (sha1 1ae84b9829... matches benchmark-verified/django__django-13590/patch.diff). Executed once through the official harness:
  python run_resolve.py faithful_patch.diff  =>  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}
Since all 8 faithful patches are identical, this one executed resolve run covers all of them; result is RESOLVED. No verifying wrong-impl produces a non-resolving faithful patch.

WHY the spec cannot be broken here: the postcondition is a total, single-valued functional equality (out MUST equal one specific Except.ok value for all inputs). There is no impl freedom in the returned VALUE, only in the syntactic route to it. So verify ⇒ (out = the gold value) ⇒ faithful patch = gold patch ⇒ resolves. verify⇒correct holds.

REFINEMENT.MD AUDIT: No axioms in this bundle (no A-consumed / A-reference / kind-3 legs; G-AX=skip, consistent with mapping.md §3 and django__django-11149). The only CHANGED op (container reconstruction) is modeled DEEPLY (resolvedSeq / rebuildPositional / rebuildIterable + positionalCtor branch), and the deep-model↔callee correspondence holds: rebuildPositional↔type_(*values), rebuildIterable↔type_(values), the two RebuildErr constructors↔the two real TypeError partialities, always-ok↔gold path never raising. All legs are R or I (§C). The A-legs I was asked to focus on are absent (none exist), so there is nothing over-claimed. conformance_check.py additionally differential-tests both helper primitives and the dispatch over list/tuple/namedtuple carriers (seed 13590), covering the R/I legs mechanically.

VERDICT: SOUND. ≥8 verifying same-spec attacks run; all resolve (via the shared byte-identical faithful=gold patch, executed once through run_resolve = resolved:true); 6 behaviorally-wrong same-spec impls correctly rejected; prepatch reproduced; refinement.md legs all R/I with sound deep-model correspondence. No verify⇏correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 6 | `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = resolvedSeq s.positionalCtor s.items f` pins the output to the UNIQUE value `Except.ok {positionalCtor := s.positionalCtor, items := s.items.map f}`. Every verifying same-spec impl computes exactly this value, which under mapping.md §2's R-bijection (positionalCtor ↔ hasattr(type_,'_make'); items ↔ list(value); f ↔ resolve_lookup_value; always-ok ↔ gold never raising) refines to the gold patch's `type_(*values)`/`type_(values)` dispatch. Hence every verifying attack's faithful refined patch is byte-identical to the gold patch.diff, which run_resolve confirmed RESOLVES (resolved=true, completed=true, single attempt, not flaky). No verify⇏¬resolve gap exists.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The per-element resolution this operation applies to each
   member of a sequence is modeled as an arbitrary total function `f`; the
   postconditions hold for EVERY `f`, so it needs no contract (it is strictly
   weaker than any concrete callee). The sequence-reconstruction behaviour — the
   only thing this bundle pins — is modeled DEEPLY in the `pure` region, not
   behind an axiom. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The outcome of reconstructing a sequence from its per-element-resolved
   members. Two reconstruction failures are distinguishable: handing the
   sequence's type a single iterable when that type instead requires its
   members as separate positional arguments, and — dually — handing a type
   its members as separate positional arguments when that type instead takes
   exactly one iterable. -/
inductive RebuildErr where
  | iterableNotAccepted
  | positionalNotAccepted
  deriving DecidableEq

/- The observable content of a reconstructed sequence: whether its type requires
   its members supplied positionally (rather than as one iterable), and the
   members themselves in order. These are the only fields the desired behaviour
   constrains (mapping.md §2). -/
structure SeqVal where
  positionalCtor : Bool
  items : List Int
  deriving DecidableEq

/- Reconstruction that supplies the members as separate positional arguments.
   A type that requires its members positionally accepts them, and the
   reconstructed sequence keeps its type and carries the members through in
   order. Any OTHER sequence type's constructor takes its members as one
   iterable, so handing it the members as separate positional arguments fails —
   except in the degenerate no-member case, where nothing is passed and the
   empty sequence is built. -/
def rebuildPositional (positionalCtor : Bool) (items : List Int) :
    Except RebuildErr SeqVal :=
  if positionalCtor || items.isEmpty then
    Except.ok { positionalCtor := positionalCtor, items := items }
  else Except.error .positionalNotAccepted

/- Reconstruction that hands the type a single iterable of the members. This
   succeeds only for a type that accepts an iterable; a type that instead
   requires positional members cannot be reconstructed this way. -/
def rebuildIterable (positionalCtor : Bool) (items : List Int) :
    Except RebuildErr SeqVal :=
  if positionalCtor then Except.error .iterableNotAccepted
  else Except.ok { positionalCtor := positionalCtor, items := items }

/- The desired reconstruction outcome: a sequence whose every member has been
   independently resolved (here by an arbitrary resolver `f`), reconstructed so
   that it ALWAYS succeeds and keeps both its type and its resolved members in
   order — regardless of whether the type requires positional members. -/
def resolvedSeq (positionalCtor : Bool) (items : List Int) (f : Int → Int) :
    Except RebuildErr SeqVal :=
  Except.ok { positionalCtor := positionalCtor, items := items.map f }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the members of a sequence value independently (each via the resolver
   `f`) and reconstruct the sequence. Desired behaviour: reconstruction must
   succeed for EVERY sequence type and preserve the type, even one that requires
   its members supplied as separate positional arguments; the result carries the
   per-member-resolved values in their original order. (`positionalCtor`
   abstracts "this type must receive its members positionally"; `f` abstracts the
   independent per-member resolution — mapping.md §1/§2.) -/
method reconstructSequence (s : SeqVal) (f : Int → Int)
    return (out : Except RebuildErr SeqVal)
  ensures out = resolvedSeq s.positionalCtor s.items f
  do
    -- impl-start
    -- Resolve each member independently (unchanged across the fix).
    let resolved := s.items.map f
    -- Reconstruct preserving the sequence's type. A type requiring positional
    -- members is reconstructed by supplying them positionally; any other type
    -- is reconstructed from the iterable of resolved members.
    let result : Except RebuildErr SeqVal :=
      if s.positionalCtor then rebuildPositional s.positionalCtor resolved
      else rebuildIterable s.positionalCtor resolved
    return result
    -- impl-end

prove_correct reconstructSequence by
  loom_solve
  simp only [rebuildPositional, rebuildIterable, resolvedSeq]
  split_ifs <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol complete

SAME-SPEC: all 14 attacks + pos_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet). NOTE: proof-region edits (set_option must live INSIDE the tactic body, not before `prove_correct`, or spec_view keeps the extra line and same_spec flips False) do not affect the spec signature — verified.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently ≤4 at a time):
- VERIFYING (exit 0), same-spec, all compute the pinned unique value:
  atk_1 ungrounded-oracle echo (`return resolvedSeq s.positionalCtor s.items f`)
  atk_2 direct Except.ok literal
  atk_3 empty-first three-way branch (isEmpty→positional, then positional/iterable)
  atk_4 if `s.positionalCtor = true` dispatch (positional/iterable)
  atk_5 eta-expanded map `(fun x => f x)`
  atk_6 dependent-if `if _h : s.positionalCtor = true`
  atk_7 redundant let-chain then Except.ok literal
  atk_8 positional branch via rebuildPositional else inline Except.ok
- CORRECTLY REJECTED (exit 1) — genuine unsolved-goal failures (spec has teeth):
  atk_9  swapped branches (control-flow-effect) — goal reduces to error=ok
  atk_10 always rebuildPositional (partial-domain) — ⊢ False on nonempty non-positional
  atk_11 drops f, returns s.items — ⊢ Except.ok s = ok(items.map f)
  atk_12 reversed order `.reverse` — value mismatch
  atk_13 ungrounded always-error — error=ok
  atk_14 flipped positionalCtor field — value mismatch
- pos_control (gold impl): VERIFY (exit 0).

PREPATCH: Solution_prepatch.lean fails (exit 1). Confirmed via a tolerant-proof probe (prepatch_probe.lean) that the failure is a GENUINE spec-goal, not a tactic artifact: goal reduces to `(if s.positionalCtor then Except.error .iterableNotAccepted else ok(...)) = ok(...)`, unprovable (requires s.positionalCtor=false) — exactly the namedtuple case test_range_lookup_namedtuple exercises. prepatch_reproduced=true.

RESOLVE (MANDATORY step for every verifying attack): the faithful refined patch of each of atk_1..8 is byte-identical to the gold patch.diff (sha1 1ae84b9829... matches benchmark-verified/django__django-13590/patch.diff). Executed once through the official harness:
  python run_resolve.py faithful_patch.diff  =>  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}
Since all 8 faithful patches are identical, this one executed resolve run covers all of them; result is RESOLVED. No verifying wrong-impl produces a non-resolving faithful patch.

WHY the spec cannot be broken here: the postcondition is a total, single-valued functional equality (out MUST equal one specific Except.ok value for all inputs). There is no impl freedom in the returned VALUE, only in the syntactic route to it. So verify ⇒ (out = the gold value) ⇒ faithful patch = gold patch ⇒ resolves. verify⇒correct holds.

REFINEMENT.MD AUDIT: No axioms in this bundle (no A-consumed / A-reference / kind-3 legs; G-AX=skip, consistent with mapping.md §3 and django__django-11149). The only CHANGED op (container reconstruction) is modeled DEEPLY (resolvedSeq / rebuildPositional / rebuildIterable + positionalCtor branch), and the deep-model↔callee correspondence holds: rebuildPositional↔type_(*values), rebuildIterable↔type_(values), the two RebuildErr constructors↔the two real TypeError partialities, always-ok↔gold path never raising. All legs are R or I (§C). The A-legs I was asked to focus on are absent (none exist), so there is nothing over-claimed. conformance_check.py additionally differential-tests both helper primitives and the dispatch over list/tuple/namedtuple carriers (seed 13590), covering the R/I legs mechanically.

VERDICT: SOUND. ≥8 verifying same-spec attacks run; all resolve (via the shared byte-identical faithful=gold patch, executed once through run_resolve = resolved:true); 6 behaviorally-wrong same-spec impls correctly rejected; prepatch reproduced; refinement.md legs all R/I with sound deep-model correspondence. No verify⇏correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to Solution_prepatch.lean via swebench_unified.markers.same_spec (velvet backend) -> True. Solution.lean verifies (lean_verify exit 0); prepatch correctly FAILS the postcondition (spec is discriminating, matching the F2P namedtuple case, not vacuous). Faithfulness check of the modeled function vs the real post-patch callee Query.resolve_lookup_value list/tuple branch (django/db/models/sql/query.py:1077-1086): SeqVal abstracts value by (positionalCtor=hasattr(type_,'_make'), items=list(value)); f abstracts the unchanged per-member self.resolve_lookup_value call as an arbitrary total function (strictly weaker than any concrete callee -> no over-claim, directive 7). Spec postcondition resolvedSeq = Except.ok {positionalCtor, items.map f}: always succeeds, preserves type and member order. On the real side, post-patch: type_(values) for list/tuple always builds a same-type container of resolved members in order; type_(*values) for namedtuple gets exactly the arity of value's members so always succeeds — observable (type, positionalCtor, members) equals items.map f for EVERY carrier in the modeled domain (list/tuple/namedtuple). No modeled input drives the real callee to diverge from the always-ok spec. Ran conformance_check.py: 100009 inputs (seed 13590), 0 disagreements across dispatch AND both helper-level primitives (rebuildPositional/rebuildIterable vs unguarded type_(*values)/type_(values)), so the partiality of the (off-gold, unreachable-on-gold-path) helpers also faithfully mirrors the real primitives' TypeError behavior — the spec is not too strong. The spec does not constrain the unchanged non-list/tuple legs (resolve_expression branch, final return value), correctly kept outside the modeled branch. No axiom (G-AX skip) so no hidden over-strong contract. Conclusion: modeled function agrees with real callee on all inputs in the abstraction domain; spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet, computed via markers.spec_view) contains only signatures/axioms/pure helpers/contracts + elided impl and proof. same_spec(Solution, Solution_prepatch)=True. Mechanical leakage.screen PASSES (no diff markers, no gold-patch lines reproduced, no patched file/module path, no spec-view identifier or comment echoing patched symbol resolve_lookup_value, no bug/fix narration tokens). Semantic check beyond problem_statement: the PUBLIC problem_statement is unusually explicit and already discloses the function (Query.resolve_lookup_value reconstitutes the tuple), the bug (preserves the named-tuple type but passes an iterator to its constructor; NamedTuples lack the iterator-copy path), AND the fix verbatim ('The fix is to * expand the contents of the iterator into the constructor'). The spec view's abstract model — reconstruct positionally (rebuildPositional/splat) for positional-constructor types (positionalCtor = hasattr(type_,'_make')) vs. via single iterable (rebuildIterable) otherwise, always succeeding and preserving type/order — is exactly congruent with what the public statement states, and is stated at a behavioral (not edit-localizing) altitude. The changed repo symbol never appears; the method is abstractly named reconstructSequence. The two RebuildErr constructors encode symmetric constructor-partiality modes (behavior spec), not edit disclosure, and are fully implied by the public account. Nothing in the spec view leaks the gold edit beyond the public problem_statement (edit-narrating prose lives only in refinement.md/mapping.md, which are not in the spec view).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
