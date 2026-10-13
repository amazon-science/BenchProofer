# P2 adversarial audit — sphinx-doc__sphinx-9281

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 26 admissible attacks re-run of 26 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 26 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 20 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_20.lean`, `atk_21.lean`, `atk_22.lean`, `atk_23.lean`, `atk_24.lean`, `atk_25.lean`, `atk_26.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_18.lean`, `atk_19.lean` |

**Non-vacuity.** The positive control `ctl_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 26 same-spec admissible wrong impls were built and verified; 20 were REJECTED by correct_describeValue and the 6 that closed with clean axioms all have faithful refined patches that RESOLVE under the official harness (run_resolve = resolved), i.e. they are correct echoes of the gold, not spec weaknesses. Specifically: atk_10 (enum test hoisted to the HEAD of the isinstance chain) resolved; atk_18 (enum test first AND container guards left as independent non-chained tests) resolved; atk_19 (enum test last but the container guards left as plain `if`s rather than an `elif` chain) resolved; atk_11 (Classical.choose oracle echo) resolved; atk_12 (String.intercalate / ".".join assembly) resolved; atk_13 (classically-dead extra branch consulting the legacy renderer) resolved. Oracle discrimination was proven on this instance: patch_ctl_gold.diff resolved=True while patch_ctl_bad_sep.diff ("%s::%s", the faithful refinement of atk_2) resolved=False with note "patch did not resolve in 3 attempts (consistent — not flaky)" on a clean rerun where all 3 attempts completed — so a non-resolving faithful patch WOULD have been detected had one existed.
```

**Attacks re-run (26):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,9 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  -- ATTACK 1 (PREPATCH BUG): no dedicated enum branch at all; every value,
+  -- including a plain enumeration member, is handed straight to the existing
+  -- display routine (the pre-patch `repr`-based fall-through).
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +78,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,9 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 2: wrong separator ("::" instead of ".").
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    return className ++ "::" ++ memberName
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +78,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,9 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 3: components swapped (Member.Class).
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    return memberName ++ "." ++ className
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +78,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,12 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 4 (PARTIAL DOMAIN): the dedicated rendering is applied only when
+  -- BOTH components are non-empty; otherwise the value falls through.
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    if className ≠ "" && memberName ≠ "" then
+      return className ++ "." ++ memberName
+    return legacyDescription obj
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +81,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,12 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 5 (BOUNDARY): when the member name is empty the separator is
+  -- dropped, so the display is the bare class name.
   if let .enumMember className memberName := obj then
+    if memberName = "" then
+      return className
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +81,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,11 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  -- ATTACK 6 (CONTROL-FLOW EFFECT): the dedicated branch is hung off the WRONG
+  -- kind -- an `other` value gets a qualified-looking shape and a plain
+  -- enumeration member falls through to the existing display routine.
+  if let .other tag := obj then
+    return toString tag ++ "." ++ toString tag
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +80,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,11 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  -- ATTACK 7 (UNGROUNDED-ORACLE ECHO): the changed (enum) branch does not
+  -- build the qualified name at all -- it echoes the opaque display routine,
+  -- i.e. it describes no algorithm for the fix.
+  if let .enumMember _ _ := obj then
+    return legacyDescription obj
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +80,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,19 +68,20 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 8 (FRAME VIOLATION): the UNCHANGED leg invents a constant instead of
+  -- deferring to the existing display routine.
   if let .enumMember className memberName := obj then
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+  return "{}"
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,9 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  -- ATTACK 9: dropped component -- the class name alone is displayed.
+  if let .enumMember className _ := obj then
+    return className
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +78,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -67,20 +67,21 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+def implementation_describeValue (obj : PyValue) : String :=
+  -- ATTACK 10 (REFINEMENT BOUNDARY / control-flow ORDER): the value's kind is
+  -- decided by consulting the ENUMERATION test FIRST, ahead of the container
+  -- kinds. The Lean carrier's constructors are DISJOINT, so branch order is
+  -- invisible in the model and this is extensionally gold; its faithful Python
+  -- refinement, however, hoists `isinstance(object, enum.Enum)` to the HEAD of
+  -- the isinstance chain, which IS observable on container-mixin enum members.
+  match obj with
+  | PyValue.enumMember className memberName => className ++ "." ++ memberName
+  | PyValue.other tag => legacyDescription (PyValue.other tag)
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;> rfl
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -67,20 +67,24 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+-- ATTACK 11 (UNGROUNDED-ORACLE ECHO, classical): the implementation is a bare
+-- classical choice over the postcondition. It computes nothing and describes no
+-- algorithm; it closes iff the postcondition is satisfiable.
+theorem exists_describeValue (obj : PyValue) :
+    ∃ s, problem_spec_describeValue obj s := by
+  cases obj with
+  | enumMember className memberName =>
+      exact ⟨className ++ "." ++ memberName, rfl⟩
+  | other tag =>
+      exact ⟨legacyDescription (PyValue.other tag), rfl⟩
+
+noncomputable def implementation_describeValue (obj : PyValue) : String :=
+  Classical.choose (exists_describeValue obj)
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  exact Classical.choose_spec (exists_describeValue obj)
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,10 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  -- ATTACK 12: a DIFFERENT assembly surface -- the two components are joined
+  -- with "." via String.intercalate instead of two String.appends.
+  if let PyValue.enumMember className memberName := obj then
+    return String.intercalate "." [className, memberName]
   return legacyDescription obj
 -- impl-end
 
@@ -81,6 +80,9 @@
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
   cases obj with
-  | enumMember className memberName => rfl
+  | enumMember className memberName =>
+      show String.intercalate "." [className, memberName]
+             = className ++ "." ++ memberName
+      rfl
   | other tag => rfl
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -67,13 +67,19 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+def implementation_describeValue (obj : PyValue) : String :=
+  -- ATTACK 13: an extra branch that PREFERS the existing display routine's text
+  -- whenever it happens to COINCIDE with the qualified name. Observably dead,
+  -- but a genuinely different program that consults the opaque display routine
+  -- on the CHANGED kind.
+  match obj with
+  | PyValue.enumMember className memberName =>
+      if legacyDescription (PyValue.enumMember className memberName)
+           = className ++ "." ++ memberName then
+        legacyDescription (PyValue.enumMember className memberName)
+      else
+        className ++ "." ++ memberName
+  | PyValue.other tag => legacyDescription (PyValue.other tag)
 -- impl-end
 
 -- proof-start
@@ -81,6 +87,14 @@
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
   cases obj with
-  | enumMember className memberName => rfl
+  | enumMember className memberName =>
+      show (if legacyDescription (PyValue.enumMember className memberName)
+              = className ++ "." ++ memberName then
+              legacyDescription (PyValue.enumMember className memberName)
+            else className ++ "." ++ memberName)
+           = className ++ "." ++ memberName
+      split
+      · assumption
+      · rfl
   | other tag => rfl
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,13 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 14 (PARTIAL DOMAIN on content): the fix is skipped when a component
+  -- already contains a dot, on the theory that such a name is "already
+  -- qualified".
   if let .enumMember className memberName := obj then
+    if className.contains '.' || memberName.contains '.' then
+      return legacyDescription obj
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +82,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,9 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 15 (BOUNDARY): a trailing separator is appended.
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    return className ++ "." ++ memberName ++ "."
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +78,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,19 +68,20 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
+  -- ATTACK 16 (UNGROUNDED ORACLE / wrong argument): the existing display routine
+  -- IS consulted on the unchanged leg, but on a FIXED stand-in value rather than
+  -- on `obj`.
+  if let PyValue.enumMember className memberName := obj then
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+  return legacyDescription (PyValue.other 0)
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
 -- proof-end
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,12 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 17 (CONTROL-FLOW EFFECT): the dedicated branch is gated on the class
+  -- name being non-empty, so the guard silently narrows the fix's domain.
   if let .enumMember className memberName := obj then
+    if className = "" then
+      return legacyDescription obj
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +81,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 18 — `atk_18.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,19 +68,24 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+  -- ATTACK 18 (REFINEMENT BOUNDARY, sharpest): the dedicated enumeration test is
+  -- consulted FIRST, and the remaining kind tests are left as INDEPENDENT
+  -- (non-chained) tests. Extensionally gold in the Lean carrier -- neither the
+  -- ORDER nor the CHAINING of the kind tests is observable there, because the two
+  -- constructors are disjoint. The faithful Python refinement hoists
+  -- `if isinstance(object, enum.Enum): return "%s.%s" % (...)` to the TOP of
+  -- object_description and leaves the container guards as plain `if`s, so EVERY
+  -- container-mixin enum member is captured by the new branch.
+  match obj with
+  | PyValue.enumMember className memberName =>
+      return className ++ "." ++ memberName
+  | PyValue.other tag =>
+      return legacyDescription (PyValue.other tag)
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;> rfl
 -- proof-end
```

Attack 19 — `atk_19.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,19 +68,26 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 19 (REFINEMENT-BOUNDARY / if-vs-elif): the existing display routine's
+  -- text is obtained FIRST and only then is the enumeration test consulted. In
+  -- the Lean carrier this is extensionally gold, but its faithful Python
+  -- refinement leaves the container guards as plain `if`s and adds the enum test
+  -- as a further plain `if` AFTER them -- so a container-mixin enum member whose
+  -- container branch FALLS THROUGH (unsortable values) now reaches the new
+  -- branch, where gold's `elif` chain skips it and lands on the `repr` tail.
+  let fallback := legacyDescription obj
   if let .enumMember className memberName := obj then
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+  return fallback
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,12 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
+  -- ATTACK 20 (FRAME VIOLATION on the argument): the unchanged leg consults the
+  -- existing display routine on a NEIGHBOURING value rather than on `obj`.
+  if let PyValue.enumMember className memberName := obj then
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  if let PyValue.other tag := obj then
+    return legacyDescription (PyValue.other (tag + 1))
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +81,8 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
 -- proof-end
```

Attack 21 — `atk_21.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,11 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 21 (PARTIAL DOMAIN / silent normalisation): the member name is
+  -- upper-cased before being appended, which is the identity on the F2P test's
+  -- member name (`FOO`) and wrong everywhere else.
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    return className ++ "." ++ memberName.toUpper
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +80,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 22 — `atk_22.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,11 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 22 (BOUNDARY, byte-level): the separator is the look-alike ONE DOT
+  -- LEADER U+2024 rather than the ASCII FULL STOP U+002E. Visually identical in
+  -- rendered documentation; a different byte string.
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    return className ++ "․" ++ memberName
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +80,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 23 — `atk_23.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,14 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 23 (PARTIAL FRAME VIOLATION): the unchanged leg defers to the
+  -- existing display routine for almost every value, but for ONE distinguished
+  -- value it invents a qualified-looking display instead. Probes whether the
+  -- opaque carrier is load-bearing POINTWISE, not just on average.
   if let .enumMember className memberName := obj then
     return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  if let .other 0 := obj then
+    return "0.0"
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +83,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 24 — `atk_24.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,13 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
+  -- ATTACK 24 (PARTIAL DOMAIN, tuned to the F2P test): the dedicated rendering
+  -- is applied only when the member name is exactly three characters long --
+  -- true of the FAIL_TO_PASS test's `FOO`, false in general.
   if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+    if memberName.length = 3 then
+      return className ++ "." ++ memberName
+    return legacyDescription obj
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +82,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 25 — `atk_25.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,19 +68,21 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
-  return legacyDescription obj
+  -- ATTACK 25 (CONTROL-FLOW EFFECT / over-application): the dedicated rendering
+  -- is applied UNCONDITIONALLY -- the kind test is dropped and the components of
+  -- an `other` value are synthesised from its display.
+  match obj with
+  | .enumMember className memberName => return className ++ "." ++ memberName
+  | .other _ => return legacyDescription obj ++ "." ++ legacyDescription obj
 -- impl-end
 
 -- proof-start
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

Attack 26 — `atk_26.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -68,11 +68,11 @@
 
 -- impl-start
 def implementation_describeValue (obj : PyValue) : String := Id.run do
-  -- A plain enumeration member is displayed as its qualified name
-  -- `Class.Member`.
-  if let .enumMember className memberName := obj then
-    return className ++ "." ++ memberName
-  -- Any other value falls through to the existing display routine.
+  -- ATTACK 26 (UNGROUNDED ORACLE / test-tuned constant): the changed branch
+  -- returns the literal text the FAIL_TO_PASS test asserts, ignoring the
+  -- components entirely.
+  if let .enumMember _ _ := obj then
+    return "MyEnum.FOO"
   return legacyDescription obj
 -- impl-end
 
@@ -80,7 +80,9 @@
 theorem correct_describeValue :
     ∀ obj, problem_spec_describeValue obj (implementation_describeValue obj) := by
   intro obj
-  cases obj with
-  | enumMember className memberName => rfl
-  | other tag => rfl
+  cases obj <;>
+    first
+      | rfl
+      | simp_all [problem_spec_describeValue, implementation_describeValue, Id.run]
+      | (simp only [problem_spec_describeValue, implementation_describeValue]; split <;> simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial pass, sphinx-doc__sphinx-9281 (lean). Base-commit worktree @ 8ec06e9a1bd862cd713b9db748e039ccc7b3e15b (created with `git worktree add --detach`).

**SAME-SPEC:** all 26 attacks + the positive control edit ONLY the impl region (and, where the tactic had to change, the proof region, which spec_signature elides for the lean flavor). Verified via swebench_unified.markers.same_spec => True for all 27 files. Re-confirmed with the runner's own primitive swebench_unified.adversary.check_attack: 26/26 same_spec=True admissible=True verify_completed=True (no dropped obligation, no new axiom, no sorry).

### COMMANDS (from the repo root; 4-way concurrent background jobs, scripts verify_all.sh / verify2.sh / verify_ax.sh / resolve_all.sh):
  bash scripts/lean_verify.sh atk_N.lean

### RESULTS (exit code per attack; logs at atk_N.log):
  REJECTED (exit 1, the discriminating clause fails) — 20 attacks:
   atk_1  EXIT=1  PREPATCH BUG: no enum branch; every value -> legacyDescription. PREPATCH REPRODUCED (impl region diffed equivalent, modulo comments, to Solution_prepatch.lean).
   atk_2  EXIT=1  wrong separator "::"
   atk_3  EXIT=1  swapped components (Member.Class)
   atk_4  EXIT=1  PARTIAL DOMAIN: dedicated rendering only when both components non-empty
   atk_5  EXIT=1  BOUNDARY: empty memberName drops the separator
   atk_6  EXIT=1  CONTROL-FLOW EFFECT: branch hung off the WRONG kind (other gets the qualified shape, enumMember falls through)
   atk_7  EXIT=1  UNGROUNDED-ORACLE ECHO: the CHANGED branch echoes legacyDescription instead of building the name
   atk_8  EXIT=1  FRAME VIOLATION: the UNCHANGED leg invents the constant "{}" instead of deferring
   atk_9  EXIT=1  dropped component: class name only
   atk_14 EXIT=1  PARTIAL DOMAIN on component contents: skips the fix when a component already contains a dot
   atk_15 EXIT=1  BOUNDARY: trailing dot appended
   atk_16 EXIT=1  UNGROUNDED ORACLE / wrong argument: legacyDescription applied to a FIXED stand-in (.other 0) rather than obj
   atk_17 EXIT=1  CONTROL-FLOW EFFECT: dedicated branch gated on className != ""
   atk_20 EXIT=1  FRAME VIOLATION on the argument: legacyDescription applied to a PERTURBED value (.other (tag+1))
   atk_21 EXIT=1  PARTIAL DOMAIN / silent normalisation: memberName.toUpper (identity on the F2P member name FOO, wrong elsewhere)
   atk_22 EXIT=1  BOUNDARY, byte-level: look-alike ONE DOT LEADER U+2024 instead of ASCII FULL STOP
   atk_23 EXIT=1  PARTIAL FRAME VIOLATION: the unchanged leg defers everywhere EXCEPT one distinguished value (probes pointwise load-bearing-ness of the opaque)
   atk_24 EXIT=1  PARTIAL DOMAIN tuned to the F2P test: fix applied only when memberName.length = 3 (true of `FOO`)
   atk_25 EXIT=1  CONTROL-FLOW EFFECT / over-application: qualified shape applied to BOTH kinds
   atk_26 EXIT=1  UNGROUNDED ORACLE / test-tuned constant: the changed branch returns the literal "MyEnum.FOO"

  CANDIDATES (exit 0) — 6 attacks, all resolve => correct echoes, NOT weaknesses:
   atk_10 EXIT=0  enum test hoisted to the HEAD of the isinstance chain
   atk_11 EXIT=0  Classical.choose over the postcondition (computes nothing)
   atk_12 EXIT=0  String.intercalate "." [C, M] instead of C ++ "." ++ M
   atk_13 EXIT=0  classically-dead extra branch preferring legacyDescription when it coincides with the qualified name
   atk_18 EXIT=0  enum test FIRST *and* the remaining kind tests left independent (non-chained)
   atk_19 EXIT=0  enum test LAST but the container guards left as plain `if`s (no elif chain)

AXIOMS (`#print axioms correct_describeValue` appended, re-elaborated via lean_verify.sh; files ax_N.lean, logs ax_N.log) — all exit 0, all clean:
   ax_10  does not depend on any axioms
   ax_12  does not depend on any axioms
   ax_13  does not depend on any axioms
   ax_18  does not depend on any axioms
   ax_19  does not depend on any axioms
   ax_11  depends on axioms: [Classical.choice]  (a STANDARD_AXIOM per backends/lean.py STANDARD_AXIOMS = ('propext','Classical.choice','Quot.sound'); no sorryAx, no undeclared axiom)
   ax_ctl does not depend on any axioms  (positive control)
  No sorryAx in any log; meta.json axioms == [] for this bundle, so the allowed set is exactly STANDARD_AXIOMS.

**POSITIVE CONTROL:** ctl_gold.lean (impl+proof byte-equivalent to the shipped gold) => lean_verify.sh EXIT=0, axioms clean.

EVERY candidate's faithful refined patch was MATERIALIZED against the real base_commit file sphinx/util/inspect.py (mkpatch.py, anchored on the verbatim base text), checked with `git -C wt apply --check` (all 10 diffs APPLY_RC=0), and EXECUTED through swebench_unified.harness.run_resolve:
  atk_10 -> patch_atk_10.diff  completed=True resolved=True  note="resolved"
  atk_11 -> patch_atk_11.diff  completed=True resolved=True  note="resolved"
  atk_12 -> patch_atk_12.diff  completed=True resolved=True  note="resolved"
  atk_13 -> patch_atk_13.diff  completed=True resolved=True  note="resolved"
  atk_18 -> patch_atk_18.diff  completed=True resolved=True  note="resolved"
  atk_19 -> patch_atk_19.diff  completed=True resolved=True  note="resolved" (clean rerun; the first run read "resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)", so it was re-run and resolved outright)
All six RESOLVE, so none is a verify=>correct defect. Not speculation — these are executed run_resolve results, and the raw JSON is at resolve_<name>.json / resolve2_<name>.json.

### ORACLE DISCRIMINATION CONTROL (this is what makes the six "resolved" verdicts meaningful — a rubber-stamping oracle would resolve anything):
   patch_ctl_gold.diff     completed=True resolved=True
   patch_ctl_bad_sep.diff  completed=True resolved=False  note="patch did not resolve in 3 attempts (consistent — not flaky)"
  The bad-separator patch is atk_2's faithful refinement. Its FIRST run carried "2 attempt(s) did not complete", which under the host-saturation rule is not a clean refutation, so I RE-RAN it: the rerun refutes consistently across 3 completed attempts. So the harness CAN refute on this instance and a genuinely wrong candidate would have been caught.

INDEPENDENT CROSS-CHECK (direct_test.py): each materialized patch's object_description was extracted with ast.get_source_segment and exec'd with the real `enum` module and the real memory_address_re, then run against the F2P assertion (object_description(MyEnum.FOO) == "MyEnum.FOO") plus all six object_description P2P assertions (test_dictionary_sorting, test_set_sorting, test_set_sorting_fallback, test_frozenset_sorting, test_frozenset_sorting_fallback, test_dict_customtype). Result: ctl_gold, atk_10, atk_18, atk_19, atk_11, atk_12, atk_13 => ALL PASS; ctl_bad_sep => F2P FAILS ('MyEnum::FOO'). This corroborates every harness verdict in-process, so the resolve results are not resting on a single measurement channel.

WHY THE 6 CANDIDATES ARE ECHOES, NOT HOLES (the interesting ones are 10/18/19 — the refinement-boundary family):
  The Lean carrier makes PyValue.enumMember and PyValue.other DISJOINT constructors, so neither the ORDER of the kind tests nor their CHAINING (if vs elif) is observable in the model. That is the one structural place this spec could hide a hole, so I attacked it three independent ways and MEASURED the real-Python consequence of each with probe.py (in-process replicas of base / gold / enum-first / plain-if):
   - atk_10 & atk_18 (enum test hoisted to the head): DIVERGE from gold on container-mixin enum members — FZE.X (class FZE(frozenset, enum.Enum)) renders 'frozenset({1, 2})' under gold but 'FZE.X' under the enum-first patch; the unsortable UNSORT.Y renders "<UNSORT.Y: frozenset({'a', 1})>" under gold but 'UNSORT.Y'.
   - atk_19 (enum test last, but plain `if`s instead of the elif chain): DIVERGES from gold on exactly the unsortable container-mixin enum member — UNSORT.Y gives "<UNSORT.Y: frozenset({'a', 1})>" under gold vs 'UNSORT.Y' under the plain-if patch, because gold's elif chain SKIPS the enum test once the frozenset arm matched-and-fell-through, whereas an independent `if` still runs it.
So all three ARE behaviourally distinct from gold on real Python. They still RESOLVE because the instance's suite (test_object_description_enum plus 38 P2P tests, all in tests/test_util_inspect.py) contains no container-mixin enum member — the divergence is real but UNOBSERVED by the oracle. That is a coverage limit of the upstream test suite, NOT a defect in this Lean spec: a patch that resolves is by the gate's own definition a correct echo (`_derive_audit_verdict`: a CANDIDATE fails only if its faithful patch does NOT resolve). Recording it as BROKEN would invent a spec weakness out of an upstream test gap.

Note this is exactly the asymmetry refinement.md already DISCLOSES under "DISCLOSED ASYMMETRY" — the bundle states the propagation is carried, not pinned, and states the reason it does not weaken verify=>resolved; my measurements confirm both halves of that claim. atk_11 (Classical.choose) is the canonical ungrounded-oracle echo: it verifies precisely BECAUSE the postcondition is a total function pinning a UNIQUE result for every kind — the witness set is a singleton, so choosing from it necessarily returns the gold string. Its verifying is evidence the spec is TIGHT, not loose. atk_12 and atk_13 are extensional variants (a different assembly surface; a provably-dead extra branch), so their patches are behaviourally identical to gold and resolve.

### A-LEG AUDIT (the assigned focus; R/I legs are G-CONF's):
meta.json axioms == [], deep_model_references == []. `grep -nE '^\s*axiom '` over Solution.lean finds NOTHING — the bundle declares no `axiom` at all, so there is no A-consumed and no A-reference leg. G-AX's skip stub (axiom_check.py, status=skip) is therefore correct, and check_proof_axioms' allowed set is exactly STANDARD_AXIOMS, which the #print axioms runs above confirm is respected. The sole `opaque`, legacyDescription : PyValue -> String (line 39), carries no `_prop` axiom.

I confirmed the claimed reason mechanically: for .other the symbol appears verbatim on BOTH sides of the spec equation (the post-condition pins result = legacyDescription obj) and for .enumMember it is absent, so the proof consumes no property of it — neither A-consumed nor A-reference, and G-AX legitimately skips.

Crucially the opaque is NOT a free hole, and I proved that with four separate attacks rather than by argument: atk_8 (unchanged leg returns "{}") FAILS, so an impl cannot substitute anything for it; atk_16 (applied to a FIXED stand-in .other 0) FAILS; atk_20 (applied to a PERTURBED argument .other (tag+1)) FAILS, so it cannot be mis-applied even to a neighbouring value; atk_23 (defers everywhere EXCEPT one distinguished value) FAILS, so it is load-bearing POINTWISE, not merely on average. atk_7 (the CHANGED branch echoes legacyDescription) also FAILS, so the opaque cannot leak into the changed branch. This is the weakest faithful model and it is demonstrably not vacuous.

**REFINEMENT.MD LEG AUDIT:** 3 legs, all tagged R; no kind-3 (changed-but-inexpressible) leg is claimed as unmodeled, and the one genuine granularity boundary IS disclosed rather than hidden. Every leg is R / A-consumed / A-reference / I with no kind-3 defect. op 1 (R) — `if let .enumMember ...` <-> fails the dict/set/frozenset guards AND satisfies isinstance(object, enum.Enum). CORRESPONDENCE HOLDS, verified empirically by probe.py against real Python enum semantics: every PLAIN enum member CHANGES display under gold (Plain.FOO: '<Plain.FOO: 1>' -> 'Plain.FOO'; SE.S str-mixin likewise) => .enumMember; every container-mixin enum member is displayed by its container branch (FZE.X, and the unsortable UNSORT.Y landing on the repr tail) => .other; every non-enum value unchanged => .other.

The model boundary is exactly the patch's boundary. op 2 (R) — `C ++ "." ++ M` <-> `"%s.%s" % (C, M)`. Checked on the adversarial string cases refinement.md claims nothing about: ('MyEnum','FOO'), ('',''), ('A.B','C.D'), ('','X'), ('X',''), non-ascii ('Ünïcode','Mémber'), 300-char components, and ('X','None') (the composite-Flag text case mapping.md calls out). Byte-identical in all eight, so %s is identity on str and the concatenation is faithful with no hidden assumption. op 3 (R) — fall-through <-> the dict/set/frozenset renderings plus the repr + memory-address scrub + newline flatten tail, modeled as the opaque legacyDescription denoted POST-PATCH.

Frame-correct, and the post-patch denotation is the right one: an earlier "unchanged pre-existing rendering" denotation would be falsified by {'a': MyEnum.FOO}, which probe.py confirms moves from "{'a': <Plain.FOO: 1>}" at base to "{'a': Plain.FOO}" post-patch. The shipped file already records that correction rather than quietly dropping it.

The `if`->`elif` conversion is the one thing that could have hidden a changed-but-unmodeled op, so I proved it BEHAVIOUR-PRESERVING for every non-enum value mechanically (elif_audit.py): the conversion is observable only for a value satisfying TWO container guards (so a `pass` fall-through would reach the next `if` pre-patch but skip the chain post-patch), and no such value exists — dict+set, dict+frozenset and set+frozenset ALL raise TypeError "multiple bases have instance lay-out conflict" at class creation, and isinstance(set(), frozenset) / isinstance(frozenset(), set) / isinstance({}, set) / isinstance({}, frozenset) / issubclass(set, frozenset) / issubclass(frozenset, set) are all False.

So at most one container guard can ever be true and the elif chain is equivalent for non-enum values; its ONLY real consequence is on the NEW enum test, which the chain now skips when a preceding container guard matched but fell through — precisely the UNSORT.Y case refinement.md names and measures. refinement.md's claim is CORRECT.

**FLOOR:** 26 admissible attacks (>= 5 required), 20 rejected, 6 candidates all resolving under executed run_resolve, prepatch bug reproduced (atk_1), positive control verifies with clean axioms, oracle discrimination proven on a clean 3-of-3-completed rerun, and every candidate corroborated in-process against the real F2P+P2P assertions.

**VERDICT:** SOUND. No same-spec wrong impl with a closing clean-axiom proof has a faithful refined patch that fails to resolve; verify => correct holds on every executed measurement.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 26 admissible attacks re-run of 26 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 26 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 20 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean`, `atk_20.lean`, `atk_21.lean`, `atk_22.lean`, `atk_23.lean`, `atk_24.lean`, `atk_25.lean`, `atk_26.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_18.lean`, `atk_19.lean` |

**Non-vacuity.** The positive control `ctl_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 26 same-spec admissible wrong impls were built and verified; 20 were REJECTED by correct_describeValue and the 6 that closed with clean axioms all have faithful refined patches that RESOLVE under the official harness (run_resolve = resolved), i.e. they are correct echoes of the gold, not spec weaknesses. Specifically: atk_10 (enum test hoisted to the HEAD of the isinstance chain) resolved; atk_18 (enum test first AND container guards left as independent non-chained tests) resolved; atk_19 (enum test last but the container guards left as plain `if`s rather than an `elif` chain) resolved; atk_11 (Classical.choose oracle echo) resolved; atk_12 (String.intercalate / ".".join assembly) resolved; atk_13 (classically-dead extra branch consulting the legacy renderer) resolved. Oracle discrimination was proven on this instance: patch_ctl_gold.diff resolved=True while patch_ctl_bad_sep.diff ("%s::%s", the faithful refinement of atk_2) resolved=False with note "patch did not resolve in 3 attempts (consistent — not flaky)" on a clean rerun where all 3 attempts completed — so a non-resolving faithful patch WOULD have been detected had one existed.
```

**Attacks re-run (26):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 26 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_19.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22.lean` → rejected (same spec, does not verify — good)

Attack 23 — `atk_23.lean` → rejected (same spec, does not verify — good)

Attack 24 — `atk_24.lean` → rejected (same spec, does not verify — good)

Attack 25 — `atk_25.lean` → rejected (same spec, does not verify — good)

Attack 26 — `atk_26.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial pass, sphinx-doc__sphinx-9281 (lean). Base-commit worktree @ 8ec06e9a1bd862cd713b9db748e039ccc7b3e15b (created with `git worktree add --detach`).

**SAME-SPEC:** all 26 attacks + the positive control edit ONLY the impl region (and, where the tactic had to change, the proof region, which spec_signature elides for the lean flavor). Verified via swebench_unified.markers.same_spec => True for all 27 files. Re-confirmed with the runner's own primitive swebench_unified.adversary.check_attack: 26/26 same_spec=True admissible=True verify_completed=True (no dropped obligation, no new axiom, no sorry).

### COMMANDS (from the repo root; 4-way concurrent background jobs, scripts verify_all.sh / verify2.sh / verify_ax.sh / resolve_all.sh):
  bash scripts/lean_verify.sh atk_N.lean

### RESULTS (exit code per attack; logs at atk_N.log):
  REJECTED (exit 1, the discriminating clause fails) — 20 attacks:
   atk_1  EXIT=1  PREPATCH BUG: no enum branch; every value -> legacyDescription. PREPATCH REPRODUCED (impl region diffed equivalent, modulo comments, to Solution_prepatch.lean).
   atk_2  EXIT=1  wrong separator "::"
   atk_3  EXIT=1  swapped components (Member.Class)
   atk_4  EXIT=1  PARTIAL DOMAIN: dedicated rendering only when both components non-empty
   atk_5  EXIT=1  BOUNDARY: empty memberName drops the separator
   atk_6  EXIT=1  CONTROL-FLOW EFFECT: branch hung off the WRONG kind (other gets the qualified shape, enumMember falls through)
   atk_7  EXIT=1  UNGROUNDED-ORACLE ECHO: the CHANGED branch echoes legacyDescription instead of building the name
   atk_8  EXIT=1  FRAME VIOLATION: the UNCHANGED leg invents the constant "{}" instead of deferring
   atk_9  EXIT=1  dropped component: class name only
   atk_14 EXIT=1  PARTIAL DOMAIN on component contents: skips the fix when a component already contains a dot
   atk_15 EXIT=1  BOUNDARY: trailing dot appended
   atk_16 EXIT=1  UNGROUNDED ORACLE / wrong argument: legacyDescription applied to a FIXED stand-in (.other 0) rather than obj
   atk_17 EXIT=1  CONTROL-FLOW EFFECT: dedicated branch gated on className != ""
   atk_20 EXIT=1  FRAME VIOLATION on the argument: legacyDescription applied to a PERTURBED value (.other (tag+1))
   atk_21 EXIT=1  PARTIAL DOMAIN / silent normalisation: memberName.toUpper (identity on the F2P member name FOO, wrong elsewhere)
   atk_22 EXIT=1  BOUNDARY, byte-level: look-alike ONE DOT LEADER U+2024 instead of ASCII FULL STOP
   atk_23 EXIT=1  PARTIAL FRAME VIOLATION: the unchanged leg defers everywhere EXCEPT one distinguished value (probes pointwise load-bearing-ness of the opaque)
   atk_24 EXIT=1  PARTIAL DOMAIN tuned to the F2P test: fix applied only when memberName.length = 3 (true of `FOO`)
   atk_25 EXIT=1  CONTROL-FLOW EFFECT / over-application: qualified shape applied to BOTH kinds
   atk_26 EXIT=1  UNGROUNDED ORACLE / test-tuned constant: the changed branch returns the literal "MyEnum.FOO"

  CANDIDATES (exit 0) — 6 attacks, all resolve => correct echoes, NOT weaknesses:
   atk_10 EXIT=0  enum test hoisted to the HEAD of the isinstance chain
   atk_11 EXIT=0  Classical.choose over the postcondition (computes nothing)
   atk_12 EXIT=0  String.intercalate "." [C, M] instead of C ++ "." ++ M
   atk_13 EXIT=0  classically-dead extra branch preferring legacyDescription when it coincides with the qualified name
   atk_18 EXIT=0  enum test FIRST *and* the remaining kind tests left independent (non-chained)
   atk_19 EXIT=0  enum test LAST but the container guards left as plain `if`s (no elif chain)

AXIOMS (`#print axioms correct_describeValue` appended, re-elaborated via lean_verify.sh; files ax_N.lean, logs ax_N.log) — all exit 0, all clean:
   ax_10  does not depend on any axioms
   ax_12  does not depend on any axioms
   ax_13  does not depend on any axioms
   ax_18  does not depend on any axioms
   ax_19  does not depend on any axioms
   ax_11  depends on axioms: [Classical.choice]  (a STANDARD_AXIOM per backends/lean.py STANDARD_AXIOMS = ('propext','Classical.choice','Quot.sound'); no sorryAx, no undeclared axiom)
   ax_ctl does not depend on any axioms  (positive control)
  No sorryAx in any log; meta.json axioms == [] for this bundle, so the allowed set is exactly STANDARD_AXIOMS.

**POSITIVE CONTROL:** ctl_gold.lean (impl+proof byte-equivalent to the shipped gold) => lean_verify.sh EXIT=0, axioms clean.

EVERY candidate's faithful refined patch was MATERIALIZED against the real base_commit file sphinx/util/inspect.py (mkpatch.py, anchored on the verbatim base text), checked with `git -C wt apply --check` (all 10 diffs APPLY_RC=0), and EXECUTED through swebench_unified.harness.run_resolve:
  atk_10 -> patch_atk_10.diff  completed=True resolved=True  note="resolved"
  atk_11 -> patch_atk_11.diff  completed=True resolved=True  note="resolved"
  atk_12 -> patch_atk_12.diff  completed=True resolved=True  note="resolved"
  atk_13 -> patch_atk_13.diff  completed=True resolved=True  note="resolved"
  atk_18 -> patch_atk_18.diff  completed=True resolved=True  note="resolved"
  atk_19 -> patch_atk_19.diff  completed=True resolved=True  note="resolved" (clean rerun; the first run read "resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)", so it was re-run and resolved outright)
All six RESOLVE, so none is a verify=>correct defect. Not speculation — these are executed run_resolve results, and the raw JSON is at resolve_<name>.json / resolve2_<name>.json.

### ORACLE DISCRIMINATION CONTROL (this is what makes the six "resolved" verdicts meaningful — a rubber-stamping oracle would resolve anything):
   patch_ctl_gold.diff     completed=True resolved=True
   patch_ctl_bad_sep.diff  completed=True resolved=False  note="patch did not resolve in 3 attempts (consistent — not flaky)"
  The bad-separator patch is atk_2's faithful refinement. Its FIRST run carried "2 attempt(s) did not complete", which under the host-saturation rule is not a clean refutation, so I RE-RAN it: the rerun refutes consistently across 3 completed attempts. So the harness CAN refute on this instance and a genuinely wrong candidate would have been caught.

INDEPENDENT CROSS-CHECK (direct_test.py): each materialized patch's object_description was extracted with ast.get_source_segment and exec'd with the real `enum` module and the real memory_address_re, then run against the F2P assertion (object_description(MyEnum.FOO) == "MyEnum.FOO") plus all six object_description P2P assertions (test_dictionary_sorting, test_set_sorting, test_set_sorting_fallback, test_frozenset_sorting, test_frozenset_sorting_fallback, test_dict_customtype). Result: ctl_gold, atk_10, atk_18, atk_19, atk_11, atk_12, atk_13 => ALL PASS; ctl_bad_sep => F2P FAILS ('MyEnum::FOO'). This corroborates every harness verdict in-process, so the resolve results are not resting on a single measurement channel.

WHY THE 6 CANDIDATES ARE ECHOES, NOT HOLES (the interesting ones are 10/18/19 — the refinement-boundary family):
  The Lean carrier makes PyValue.enumMember and PyValue.other DISJOINT constructors, so neither the ORDER of the kind tests nor their CHAINING (if vs elif) is observable in the model. That is the one structural place this spec could hide a hole, so I attacked it three independent ways and MEASURED the real-Python consequence of each with probe.py (in-process replicas of base / gold / enum-first / plain-if):
   - atk_10 & atk_18 (enum test hoisted to the head): DIVERGE from gold on container-mixin enum members — FZE.X (class FZE(frozenset, enum.Enum)) renders 'frozenset({1, 2})' under gold but 'FZE.X' under the enum-first patch; the unsortable UNSORT.Y renders "<UNSORT.Y: frozenset({'a', 1})>" under gold but 'UNSORT.Y'.
   - atk_19 (enum test last, but plain `if`s instead of the elif chain): DIVERGES from gold on exactly the unsortable container-mixin enum member — UNSORT.Y gives "<UNSORT.Y: frozenset({'a', 1})>" under gold vs 'UNSORT.Y' under the plain-if patch, because gold's elif chain SKIPS the enum test once the frozenset arm matched-and-fell-through, whereas an independent `if` still runs it.
So all three ARE behaviourally distinct from gold on real Python. They still RESOLVE because the instance's suite (test_object_description_enum plus 38 P2P tests, all in tests/test_util_inspect.py) contains no container-mixin enum member — the divergence is real but UNOBSERVED by the oracle. That is a coverage limit of the upstream test suite, NOT a defect in this Lean spec: a patch that resolves is by the gate's own definition a correct echo (`_derive_audit_verdict`: a CANDIDATE fails only if its faithful patch does NOT resolve). Recording it as BROKEN would invent a spec weakness out of an upstream test gap.

Note this is exactly the asymmetry refinement.md already DISCLOSES under "DISCLOSED ASYMMETRY" — the bundle states the propagation is carried, not pinned, and states the reason it does not weaken verify=>resolved; my measurements confirm both halves of that claim. atk_11 (Classical.choose) is the canonical ungrounded-oracle echo: it verifies precisely BECAUSE the postcondition is a total function pinning a UNIQUE result for every kind — the witness set is a singleton, so choosing from it necessarily returns the gold string. Its verifying is evidence the spec is TIGHT, not loose. atk_12 and atk_13 are extensional variants (a different assembly surface; a provably-dead extra branch), so their patches are behaviourally identical to gold and resolve.

### A-LEG AUDIT (the assigned focus; R/I legs are G-CONF's):
meta.json axioms == [], deep_model_references == []. `grep -nE '^\s*axiom '` over Solution.lean finds NOTHING — the bundle declares no `axiom` at all, so there is no A-consumed and no A-reference leg. G-AX's skip stub (axiom_check.py, status=skip) is therefore correct, and check_proof_axioms' allowed set is exactly STANDARD_AXIOMS, which the #print axioms runs above confirm is respected. The sole `opaque`, legacyDescription : PyValue -> String (line 39), carries no `_prop` axiom.

I confirmed the claimed reason mechanically: for .other the symbol appears verbatim on BOTH sides of the spec equation (the post-condition pins result = legacyDescription obj) and for .enumMember it is absent, so the proof consumes no property of it — neither A-consumed nor A-reference, and G-AX legitimately skips.

Crucially the opaque is NOT a free hole, and I proved that with four separate attacks rather than by argument: atk_8 (unchanged leg returns "{}") FAILS, so an impl cannot substitute anything for it; atk_16 (applied to a FIXED stand-in .other 0) FAILS; atk_20 (applied to a PERTURBED argument .other (tag+1)) FAILS, so it cannot be mis-applied even to a neighbouring value; atk_23 (defers everywhere EXCEPT one distinguished value) FAILS, so it is load-bearing POINTWISE, not merely on average. atk_7 (the CHANGED branch echoes legacyDescription) also FAILS, so the opaque cannot leak into the changed branch. This is the weakest faithful model and it is demonstrably not vacuous.

**REFINEMENT.MD LEG AUDIT:** 3 legs, all tagged R; no kind-3 (changed-but-inexpressible) leg is claimed as unmodeled, and the one genuine granularity boundary IS disclosed rather than hidden. Every leg is R / A-consumed / A-reference / I with no kind-3 defect. op 1 (R) — `if let .enumMember ...` <-> fails the dict/set/frozenset guards AND satisfies isinstance(object, enum.Enum). CORRESPONDENCE HOLDS, verified empirically by probe.py against real Python enum semantics: every PLAIN enum member CHANGES display under gold (Plain.FOO: '<Plain.FOO: 1>' -> 'Plain.FOO'; SE.S str-mixin likewise) => .enumMember; every container-mixin enum member is displayed by its container branch (FZE.X, and the unsortable UNSORT.Y landing on the repr tail) => .other; every non-enum value unchanged => .other.

The model boundary is exactly the patch's boundary. op 2 (R) — `C ++ "." ++ M` <-> `"%s.%s" % (C, M)`. Checked on the adversarial string cases refinement.md claims nothing about: ('MyEnum','FOO'), ('',''), ('A.B','C.D'), ('','X'), ('X',''), non-ascii ('Ünïcode','Mémber'), 300-char components, and ('X','None') (the composite-Flag text case mapping.md calls out). Byte-identical in all eight, so %s is identity on str and the concatenation is faithful with no hidden assumption. op 3 (R) — fall-through <-> the dict/set/frozenset renderings plus the repr + memory-address scrub + newline flatten tail, modeled as the opaque legacyDescription denoted POST-PATCH.

Frame-correct, and the post-patch denotation is the right one: an earlier "unchanged pre-existing rendering" denotation would be falsified by {'a': MyEnum.FOO}, which probe.py confirms moves from "{'a': <Plain.FOO: 1>}" at base to "{'a': Plain.FOO}" post-patch. The shipped file already records that correction rather than quietly dropping it.

The `if`->`elif` conversion is the one thing that could have hidden a changed-but-unmodeled op, so I proved it BEHAVIOUR-PRESERVING for every non-enum value mechanically (elif_audit.py): the conversion is observable only for a value satisfying TWO container guards (so a `pass` fall-through would reach the next `if` pre-patch but skip the chain post-patch), and no such value exists — dict+set, dict+frozenset and set+frozenset ALL raise TypeError "multiple bases have instance lay-out conflict" at class creation, and isinstance(set(), frozenset) / isinstance(frozenset(), set) / isinstance({}, set) / isinstance({}, frozenset) / issubclass(set, frozenset) / issubclass(frozenset, set) are all False.

So at most one container guard can ever be true and the elif chain is equivalent for non-enum values; its ONLY real consequence is on the NEW enum test, which the chain now skips when a preceding container guard matched but fell through — precisely the UNSORT.Y case refinement.md names and measures. refinement.md's claim is CORRECT.

**FLOOR:** 26 admissible attacks (>= 5 required), 20 rejected, 6 candidates all resolving under executed run_resolve, prepatch bug reproduced (atk_1), positive control verifies with clean axioms, oracle discrimination proven on a clean 3-of-3-completed rerun, and every candidate corroborated in-process against the real F2P+P2P assertions.

**VERDICT:** SOUND. No same-spec wrong impl with a closing clean-axiom proof has a faithful refined patch that fails to resolve; verify => correct holds on every executed measurement.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFUL — no input found where problem_spec_describeValue disagrees with the real post-patch object_description.

REFERENCE SETUP (correct polarity). Worktree at base_commit 8ec06e9a1 with patch.diff APPLIED; `git diff sphinx/util/inspect.py` is byte-identical to patch.diff (5 insertions / 2 deletions: if->elif on set+frozenset, new `elif isinstance(object, enum.Enum): return "%s.%s" % (object.__class__.__name__, object.name)`). I compared the model against the PATCHED tree, not base, so the patch delta itself was never miscounted as drift. object_description extracted verbatim via ast.get_source_segment (md5 72297c14fe23d2a22abf45a553d8fad7) and exec'd with the real `enum` module and the real memory_address_re; CPython 3.10.20.

**MECHANICAL.** lean_verify.sh Solution.lean exit 0 (compiles, no sorry). `#print axioms`: BOTH correct_describeValue and problem_spec_describeValue report 'does not depend on any axioms' — no sorryAx, clean. same_spec(Solution, Solution_prepatch, LeanBackend()) = True, so the spec region is byte-identical across the discriminating pair (prepatch is a genuine same-spec rival). conformance_check.py: checked=120010 disagreements=0, status=pass. axiom_check.py: skip (no consumed axiom / no A-reference) — consistent with the sole opaque carrying no `_prop` axiom.

ENUM ARM (the changed/pinned op) — EXHAUSTED, no divergence.

(a) %-format vs concat: "%s.%s" % (C,M) vs C++"."++M over 225 adversarial pairs from {'%','s','.','','\n','%s','%d','{}','é','\\','"',"'",' at 0x7f68cb685710',...} — 0 divergences, so %s is identity on str with no hidden assumption.

(b) Real enum members with exotic identity: class `__name__` containing a dot ('Re.Named.A'), EMPTY class `__name__` ('.A'), newline in class name ('A\nB.M' — confirms the enum branch does NOT newline-flatten, and the model doesn't either), memory-address-looking class name ('<X at 0x7f68cb685710>.M' — confirms the branch does NOT run memory_address_re.sub, and the model doesn't either; these two were the sharpest drift candidates since the repr tail DOES scrub/flatten). All AGREE.

(c) Enum flavors: str-mixin SE.S, tuple-mixin TE.T, list-mixin LE.L (list has no guard, correctly enum arm), IntEnum, EnumMeta subclass, ALIAS member (Al.B -> 'Al.A', model uses .name so it tracks), Flag canonical Perm.R, Flag COMPOSITE Perm.R|Perm.W where .name is None on 3.10 -> real 'Perm.None' and the model's memberName is the %s TEXT 'None' — AGREE, so mapping.md's claim of no interpreter-version assumption on .name holds. IntFlag composite likewise 'IF.None'. Plain enum whose VALUE has a raising `__repr__` -> 'BE.B' (branch never calls repr). All AGREE.

(d) Broad differential fuzz, 670 real Python inputs (90 functional-API enums with adversarial class/member names, flags, mixins, plus containers at nesting depth 0/1/2 through dict/list/tuple): enumMember-arm divergences = 0.

DISPATCH BOUNDARY — the elif-chain ordering is modeled CORRECTLY (this is where an over-strong spec would show). Container-mixin enum members satisfy BOTH isinstance tests, and because the container branches precede the enum branch they never reach it. I confirmed each lands in PyValue.other, exactly as mapping.md claims: frozenset-mixin FZE.X -> 'frozenset({IE.A, IE.B})' (NOT 'FZE.X'), set-mixin SetE.S -> '{1, 2}', dict-mixin DE.D -> "{'a': 1}", dict-mixin holding a plain enum -> "{'k': IE.A}", and the unsortable mixin UN.U -> "<UN.U: frozenset({1, 'a'})>" (frozenset branch matches, sorting raises TypeError, elif SKIPS the enum test, repr tail). The model puts all of these in the `other` arm whose text is the unconstrained opaque, so the spec asserts NOTHING falsifiable about them. My initial probe that showed 'DIVERGE' on dict-/frozenset-mixin rows was my own bug — I had forced them into the enum arm; the model's own classify() puts them in `other`.

PRIOR PANEL-2 FAIL IS GENUINELY REPAIRED, verified not taken on faith. verdict.md:1055 records an earlier G-PANEL-2 UNFAITHFUL: legacyDescription was denoted 'the unchanged PRE-EXISTING rendering', which the container recursion falsifies on {'a': MyEnum.FOO}. The shipped denotation is now 'the display the POST-PATCH routine produces for a value that does not itself take the new enum branch'. I re-measured the exact former counterexamples against the patched tree: {'a': MyEnum.FOO} -> "{'a': MyEnum.FOO}" (base: "{'a': <MyEnum.FOO: 1>}"), {'k':{'inner':MyEnum.BAR}} -> nested new display, {IE.A,IE.B} -> '{IE.A, IE.B}', frozenset -> 'frozenset({IE.A, IE.B})', FZE.X text moves too. Under the post-patch denotation the `other` clause equals the shipped routine's own output on every one, so it is tautological against the reference and cannot be over-strong. The old hole is closed.

ONE OBSERVATION, deliberately NOT recorded as the defect. The real routine is PARTIAL on three `other`-kind inputs: BadRepr() (repr raises -> `raise ValueError from exc`), and set/frozenset whose elements raise a NON-TypeError from sorted (only TypeError is caught) — e.g. frozenset of objects whose `__lt__` raises ValueError. The Lean model is total (PyValue -> String), so it implicitly asserts a String exists there. I judged this NOT a faithfulness break: (i) all three paths are UNTOUCHED by the patch and sit entirely inside the opaque carrier, which asserts no text; (ii) PyValue.other's Nat tag is an opaque identity tag, not a claim to enumerate every Python value, so the `other` arm need not be read as quantifying over raising inputs; (iii) no text the spec pins is contradicted on any input. It is a partiality omission on an unchanged path — worth a line in mapping.md, which currently discusses `raise ValueError from exc` only in passing (mapping.md:44-45) without stating the model is total — but not spec drift.

The refinement.md 'DISCLOSED ASYMMETRY' (spec does not FORCE the container propagation) is a too-WEAK concern, i.e. attacker-1 lane, not mine; it is explicitly disclosed and the F2P test test_object_description_enum observes only the top-level case.

**Conclusion:** the enum arm is pinned byte-exactly and matches the real patched callee on every input I could construct; the other arm is tautological against the shipped routine. No diverging input exists to cite. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAN bundle sphinx-doc__sphinx-9281, leakage/gold-reconstruction role. ALL MEASUREMENTS RE-RUN FROM SOURCE.

NO RELAXATION IN PLAY (checked, not inherited). `find -iname '*RELAX*'` over the whole instance dir -> nothing; `'relaxed_leakage' in meta` -> False; recursive walk over every key AND every string value of the 107KB meta.json for /[Rr]elax/ -> 21 hits, ALL of them inside gates.G-PANEL*.detail / .note, i.e. prior panel prose recording that no relaxation exists, not a disposition. gates.G-LEAK.status = "pass" (mode strict), not "relaxed". So this is an ordinary non-relaxed leakage review and no unavoidability argument had to be re-derived.

**NO BUNDLE FILE ADDRESSES THIS ROLE.** Ran leakage.reviewer_directed() over Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py, meta.json, verdict.md, patch.diff -> [] on every one (zero hits on all four rules). verdict.md does contain a PRIOR G-PANEL-3 NO-LEAKAGE note, but it is the gate-owned ledger, it prescribes nothing, and my verdict is derived from my own measurements below.

**SPEC REGION BYTE-IDENTITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) -> True; markers.region_hashes agree on axioms/pure/post-conditions/spec_view across the pair (spec_view 6fcdd7bb70...), differing only in impl+proof as required.

**MECHANICAL SCREEN.** leakage.screen(Solution.lean, LeanBackend, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Independent audit on top of it: normalized every added/removed gold line against the normalized spec view -> zero reproduced fragments; the only symbol `_patch_changed_symbols` extracts is `object_description`, absent from the spec view; patched path `sphinx/util/inspect.py` absent; `_NARRATION_RE` hits = []. Diffed gold-patch tokens against problem_statement tokens and word-boundary-searched the spec view: survivors are only generic English/Lean (`Any`, `def`, `for`, `name`, `repr`) -- and `repr` occurs solely inside the de-Pythonized phrase "general-purpose rendering", never as the identifier (checked every line containing it). Absent entirely: elif, isinstance, enum.Enum, `__class__`, `__name__`, %s.%s, memory_address, sorted(, frozenset(, dict, MyEnum, ValueA, sphinx, inspect. impl and proof regions are genuinely elided in the projection.

THE FACET THE SPEC PINS, vs the PUBLIC PS. Spec view pins exactly two things: (a) a plain enumeration member displays as `C ++ "." ++ M`; (b) every other value displays as whatever the display routine gives it (opaque legacyDescription). (a) is verbatim public: the PS's "Expected behavior" block shows `= MyEnum.ValueA` against the actual `= <MyEnum.ValueA: 10>`. That PS pair also settles the sharpest discriminator a solver could otherwise miss -- BARE class name, not module-qualified (`MyEnum.ValueA`, even though the PS's own annotation in the same line is the qualified `ugly_enum.MyEnum`), and value+angle-brackets dropped. So the spec names no discriminator the PS does not already spell out; PS and gold AGREE here, which is why no relaxation is needed.

THE CLAUSE I SCRUTINIZED HARDEST -- the container carve-out. The spec view goes beyond the PS in stating that mappings/sets/frozen sets have their own dedicated renderings and that an enumeration member which is ALSO such a container keeps that container rendering (the behavioral shadow of the gold if->elif ordering). Judged NOT leakage on grounds I measured: (1) it is PRE-patch repo state I read directly -- `git show 8ec06e9a...:sphinx/util/inspect.py` shows the dict/set/frozenset branches already present and already preceding the repr+memory_address_re tail; the solver has that checkout plus changed_files=['sphinx/util/inspect.py'] from data/eval_localization.json, so nothing is newly disclosed and no edit is localized; (2) it is a frame condition, which spec_guide.md §5 REQUIRES (unchanged parts pinned) and which PASS_TO_PASS already enforces (test_set_sorting, test_set_sorting_fallback, test_frozenset_sorting, test_frozenset_sorting_fallback all in P2P); (3) it names no mechanism -- nothing says the new branch is an `elif` hung off a chain, or where in the function it goes, only that container kinds keep their display. A solver could not read the gold hunk out of it.

CORROBORATING VERIFICATION (my own runs, not the stamps). scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms correct_describeValue` / `implementation_describeValue` in a mktemp copy -> "does not depend on any axioms" for both, so no sorryAx and the proof is real. Solution_prepatch.lean -> exit 1, failing exactly on the discriminating clause (rfl cannot equate `legacyDescription (.enumMember C M)` with `C ++ "." ++ M`), confirming the spec view's pinned facet is load-bearing rather than decorative narration.

NOTED, NOT MY GATE: (i) meta.json's TOP-LEVEL region_hashes are stale (spec_view 4c31229338..., impl 6867124..., vs current-on-disk 6fcdd7bb70.../99b3139...); the authoritative gates.G-HYGIENE.data.region_hashes DO reproduce byte-exactly from Solution.lean, and grep shows no code reads the top-level copy, so it is dead stale data, not an unsound record. (ii) The G-PANEL rollup is fail because G-PANEL-2 (faithfulness) is fail -- a rollup echo of a sibling role, orthogonal to leakage.

**CONCLUSION:** the spec view discloses only "an enum member renders as Class.Member" (verbatim in the public problem_statement) plus a pre-patch frame condition the solver can read from its own checkout. No spec-view line reconstructs the gold edit beyond the problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
