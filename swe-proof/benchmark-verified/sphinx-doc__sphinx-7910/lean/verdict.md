# P2 adversarial audit — sphinx-doc__sphinx-7910

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_4s.lean`, `atk_5.lean`, `atk_5s.lean`, `atk_6.lean`, `atk_6s.lean`, `atk_7.lean`, `atk_7s.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -138,7 +138,7 @@
       match clsPathSingle obj.qualname with
       | some clsPath =>
         -- resolve the owning class via the UNDERLYING object's scope
-        match (obj.coreObject.globalsMap).lookup clsPath with
+        match (obj.globalsMap).lookup clsPath with
         | some cls => clsOwner := cls.attrs.contains name
         | none => clsOwner := false
       | none => clsOwner := false
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,80 +129,21 @@
 
 -- impl-start
 def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
-    (obj : PyObj) : Option Bool := Id.run do
-  let hasDoc := obj.hasDoc
-  let isMember := what == "module" || what == "class" || what == "exception"
-  if name != "__weakref__" && hasDoc && isMember then
-    let mut clsOwner := false
-    if what == "class" || what == "exception" then
-      match clsPathSingle obj.qualname with
-      | some clsPath =>
-        -- resolve the owning class via the UNDERLYING object's scope
-        match (obj.coreObject.globalsMap).lookup clsPath with
-        | some cls => clsOwner := cls.attrs.contains name
-        | none => clsOwner := false
-      | none => clsOwner := false
-    if what == "module" || clsOwner then
-      let isInit := name == "__init__"
-      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
-      let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
-      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
-         (isInit && cfg.incInit) then
-        return some false
-  return none
+    (obj : PyObj) : Option Bool := none
 -- impl-end
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
+-- Adversary: give the wrong impl its strongest shot with heavy automation.
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion shouldInclude clsIsOwner
+    isSpecialName isPrivateName isInitName implementation_memberInclusion
+  simp only [Id.run, bind, pure, Bool.and_eq_true, Bool.or_eq_true]
+  refine ⟨?_, ?_⟩ <;> intro h <;>
+    (repeat' split) <;> (first | rfl | simp_all | grind)
+#print axioms correct_memberInclusion
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,80 +129,21 @@
 
 -- impl-start
 def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
-    (obj : PyObj) : Option Bool := Id.run do
-  let hasDoc := obj.hasDoc
-  let isMember := what == "module" || what == "class" || what == "exception"
-  if name != "__weakref__" && hasDoc && isMember then
-    let mut clsOwner := false
-    if what == "class" || what == "exception" then
-      match clsPathSingle obj.qualname with
-      | some clsPath =>
-        -- resolve the owning class via the UNDERLYING object's scope
-        match (obj.coreObject.globalsMap).lookup clsPath with
-        | some cls => clsOwner := cls.attrs.contains name
-        | none => clsOwner := false
-      | none => clsOwner := false
-    if what == "module" || clsOwner then
-      let isInit := name == "__init__"
-      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
-      let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
-      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
-         (isInit && cfg.incInit) then
-        return some false
-  return none
+    (obj : PyObj) : Option Bool := some false
 -- impl-end
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
+-- Adversary: give the wrong impl its strongest shot with heavy automation.
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion shouldInclude clsIsOwner
+    isSpecialName isPrivateName isInitName implementation_memberInclusion
+  simp only [Id.run, bind, pure, Bool.and_eq_true, Bool.or_eq_true]
+  refine ⟨?_, ?_⟩ <;> intro h <;>
+    (repeat' split) <;> (first | rfl | simp_all | grind)
+#print axioms correct_memberInclusion
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,7 +132,7 @@
     (obj : PyObj) : Option Bool := Id.run do
   let hasDoc := obj.hasDoc
   let isMember := what == "module" || what == "class" || what == "exception"
-  if name != "__weakref__" && hasDoc && isMember then
+  if hasDoc && isMember then
     let mut clsOwner := false
     if what == "class" || what == "exception" then
       match clsPathSingle obj.qualname with
```

Attack 5 — `atk_4s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -132,7 +132,7 @@
     (obj : PyObj) : Option Bool := Id.run do
   let hasDoc := obj.hasDoc
   let isMember := what == "module" || what == "class" || what == "exception"
-  if name != "__weakref__" && hasDoc && isMember then
+  if hasDoc && isMember then
     let mut clsOwner := false
     if what == "class" || what == "exception" then
       match clsPathSingle obj.qualname with
@@ -154,55 +154,16 @@
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
+-- Adversary: give the wrong impl its strongest shot with heavy automation.
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion shouldInclude clsIsOwner
+    isSpecialName isPrivateName isInitName implementation_memberInclusion
+  simp only [Id.run, bind, pure, Bool.and_eq_true, Bool.or_eq_true]
+  refine ⟨?_, ?_⟩ <;> intro h <;>
+    (repeat' split) <;> (first | rfl | simp_all | grind)
+#print axioms correct_memberInclusion
 -- proof-end
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -146,8 +146,7 @@
       let isInit := name == "__init__"
       let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
       let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
-      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
-         (isInit && cfg.incInit) then
+      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) then
         return some false
   return none
 -- impl-end
```

Attack 7 — `atk_5s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -146,63 +146,23 @@
       let isInit := name == "__init__"
       let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
       let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
-      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
-         (isInit && cfg.incInit) then
+      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) then
         return some false
   return none
 -- impl-end
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
+-- Adversary: give the wrong impl its strongest shot with heavy automation.
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion shouldInclude clsIsOwner
+    isSpecialName isPrivateName isInitName implementation_memberInclusion
+  simp only [Id.run, bind, pure, Bool.and_eq_true, Bool.or_eq_true]
+  refine ⟨?_, ?_⟩ <;> intro h <;>
+    (repeat' split) <;> (first | rfl | simp_all | grind)
+#print axioms correct_memberInclusion
 -- proof-end
```

Attack 8 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
 def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
     (obj : PyObj) : Option Bool := Id.run do
   let hasDoc := obj.hasDoc
-  let isMember := what == "module" || what == "class" || what == "exception"
+  let isMember := what == "module" || what == "class"
   if name != "__weakref__" && hasDoc && isMember then
     let mut clsOwner := false
     if what == "class" || what == "exception" then
```

Attack 9 — `atk_6s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
 def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
     (obj : PyObj) : Option Bool := Id.run do
   let hasDoc := obj.hasDoc
-  let isMember := what == "module" || what == "class" || what == "exception"
+  let isMember := what == "module" || what == "class"
   if name != "__weakref__" && hasDoc && isMember then
     let mut clsOwner := false
     if what == "class" || what == "exception" then
@@ -154,55 +154,16 @@
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
+-- Adversary: give the wrong impl its strongest shot with heavy automation.
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion shouldInclude clsIsOwner
+    isSpecialName isPrivateName isInitName implementation_memberInclusion
+  simp only [Id.run, bind, pure, Bool.and_eq_true, Bool.or_eq_true]
+  refine ⟨?_, ?_⟩ <;> intro h <;>
+    (repeat' split) <;> (first | rfl | simp_all | grind)
+#print axioms correct_memberInclusion
 -- proof-end
```

Attack 10 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,7 +144,7 @@
       | none => clsOwner := false
     if what == "module" || clsOwner then
       let isInit := name == "__init__"
-      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
+      let isSpecial := (!isInit) && name.startsWith "__"
       let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
       if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
          (isInit && cfg.incInit) then
```

Attack 11 — `atk_7s.lean` → rejected (same spec, does not verify — good)

```diff
@@ -144,7 +144,7 @@
       | none => clsOwner := false
     if what == "module" || clsOwner then
       let isInit := name == "__init__"
-      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
+      let isSpecial := (!isInit) && name.startsWith "__"
       let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
       if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
          (isInit && cfg.incInit) then
@@ -154,55 +154,16 @@
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
+-- Adversary: give the wrong impl its strongest shot with heavy automation.
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion shouldInclude clsIsOwner
+    isSpecialName isPrivateName isInitName implementation_memberInclusion
+  simp only [Id.run, bind, pure, Bool.and_eq_true, Bool.or_eq_true]
+  refine ⟨?_, ?_⟩ <;> intro h <;>
+    (repeat' split) <;> (first | rfl | simp_all | grind)
+#print axioms correct_memberInclusion
 -- proof-end
```

Attack 12 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -129,80 +129,18 @@
 
 -- impl-start
 def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
-    (obj : PyObj) : Option Bool := Id.run do
-  let hasDoc := obj.hasDoc
-  let isMember := what == "module" || what == "class" || what == "exception"
-  if name != "__weakref__" && hasDoc && isMember then
-    let mut clsOwner := false
-    if what == "class" || what == "exception" then
-      match clsPathSingle obj.qualname with
-      | some clsPath =>
-        -- resolve the owning class via the UNDERLYING object's scope
-        match (obj.coreObject.globalsMap).lookup clsPath with
-        | some cls => clsOwner := cls.attrs.contains name
-        | none => clsOwner := false
-      | none => clsOwner := false
-    if what == "module" || clsOwner then
-      let isInit := name == "__init__"
-      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
-      let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
-      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
-         (isInit && cfg.incInit) then
-        return some false
-  return none
+    (obj : PyObj) : Option Bool :=
+  if shouldInclude cfg what name obj then some false else none
 -- impl-end
 
 
 -- proof-start
--- The boolean value the implementation computes into its local `clsOwner`
--- at the point of the `if what == "module" || clsOwner` test: mirrors the
--- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
--- neither "class" nor "exception" (the inner `if` is skipped).
-def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
-  if what == "class" || what == "exception" then
-    match clsPathSingle obj.qualname with
-    | some clsPath =>
-      match (obj.coreObject.globalsMap).lookup clsPath with
-      | some cls => cls.attrs.contains name
-      | none => false
-    | none => false
-  else
-    false
-
--- OwnershipBridge: the impl's locally-computed ownership boolean equals the
--- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
-theorem clsOwner_eq (what name : String) (obj : PyObj) :
-    ImplClsOwner what name obj = clsIsOwner what name obj := rfl
-
--- Directions: the two implications of `problem_spec_memberInclusion`, proved
--- directly by matching the impl's control-flow branches to `shouldInclude`'s
--- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
-theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = true →
-      implementation_memberInclusion cfg what name obj = some false := by
-  intro h
-  unfold shouldInclude at h
-  unfold implementation_memberInclusion
-  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
-    isSpecialName, isPrivateName, isInitName] at h
-  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
-  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
-  grind
-
-theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
-    shouldInclude cfg what name obj = false →
-      implementation_memberInclusion cfg what name obj = none := by
-  intro h
-  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
-  simp only [implementation_memberInclusion, Id.run, bind, pure]
-  repeat' split
-  all_goals (first | rfl | (exfalso; grind))
-
 theorem correct_memberInclusion :
     ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
       problem_spec_memberInclusion cfg what name obj
         (implementation_memberInclusion cfg what name obj) := by
   intro cfg what name obj
-  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
-
+  unfold problem_spec_memberInclusion implementation_memberInclusion
+  constructor <;> intro h <;> simp [h]
+#print axioms correct_memberInclusion
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a documented private / special / init member of a class,
exception, or module should be *included* in generated API documentation.

A member is described by its declaring kind (`what`: "module", "class",
"exception", "method", …), its `name` (e.g. `__init__`, `__repr__`,
`_helper`), and the member object itself. The member object carries:

* whether it has a docstring,
* its qualified name (`Owner.member`), from which the owning class's short
  name is taken as everything before the final dot,
* a table mapping class short-names visible in the object's defining scope to
  those classes (each class knows the attribute names it directly declares),
* and, when the object is a wrapper produced by decoration, a link to the
  object it wraps. Following these links to the end yields the *underlying*
  object — the original, undecorated member, whose defining scope is the one
  that actually declares the owning class.

Three independent toggles control inclusion: one each for init members,
other special (`__dunder__`) members, and private (`_name`) members.

A member is included exactly when it has a docstring, is not the weak-reference
slot, belongs to a documentable kind, is genuinely owned by the resolved class
(or sits directly in a module), and its category toggle is on. The owning class
must be resolved from the underlying object's defining scope, so that a
*decorated* member — whose wrapper is defined in a different scope — is still
recognized as owned by its class. "Included" is reported as `some false`
("do not skip"); every other case defers with `none`. The implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No dependency callee requires a consumed contract. Resolving an object to the
-- underlying object it wraps is modeled DEEPLY here (`coreObject`, following the
-- wrapper links to the end), so it is validated against the real operation
-- rather than axiomatized.
-- axioms-end

-- pure-start
/-- A class, modeled by the attribute names it directly declares (its
`__dict__` keys). -/
structure ClsInfo where
  attrs : List String
deriving Repr

/-- A member object. `inner` links a decoration wrapper to the object it wraps
(`none` once the underlying object is reached). `globalsMap` maps class
short-names visible in this object's defining scope to those classes. -/
inductive PyObj where
  | node (qualname : String) (hasDoc : Bool)
         (globalsMap : List (String × ClsInfo)) (inner : Option PyObj)

namespace PyObj

def qualname : PyObj → String
  | node q _ _ _ => q
def hasDoc : PyObj → Bool
  | node _ d _ _ => d
def globalsMap : PyObj → List (String × ClsInfo)
  | node _ _ g _ => g
def inner : PyObj → Option PyObj
  | node _ _ _ i => i

/-- The underlying object: follow the wrapper links to the end. -/
def coreObject : PyObj → PyObj
  | node q d g none => node q d g none
  | node _ _ _ (some o) => coreObject o

end PyObj

/-- The three inclusion toggles. -/
structure IncludeFlags where
  incInit : Bool
  incSpecial : Bool
  incPrivate : Bool

/-- The owning class's short-name: everything before the final dot of the
qualified name, but only when that prefix is itself a single dotless segment
(`Owner.member`). `none` otherwise (no dot, or a nested `A.B.member`). -/
def clsPathSingle (qualname : String) : Option String :=
  match qualname.splitOn "." with
  | [c, _] => some c
  | _ => none

def isInitName (name : String) : Bool := name == "__init__"

def isSpecialName (name : String) : Bool :=
  !(isInitName name) && name.startsWith "__" && name.endsWith "__"

def isPrivateName (name : String) : Bool :=
  !(isInitName name) && !(isSpecialName name) && name.startsWith "_"

/-- The resolved class (from the underlying object's scope) genuinely owns the
member: the class exists in scope and `name` is one of its directly-declared
attributes. Only meaningful for class / exception members. -/
def clsIsOwner (what name : String) (obj : PyObj) : Bool :=
  if what == "class" || what == "exception" then
    match clsPathSingle obj.qualname with
    | some cp =>
      match (obj.coreObject.globalsMap).lookup cp with
      | some cls => cls.attrs.contains name
      | none => false
    | none => false
  else
    false

/-- The full inclusion predicate over the inputs. -/
def shouldInclude (cfg : IncludeFlags) (what name : String) (obj : PyObj) : Bool :=
  name != "__weakref__" && obj.hasDoc &&
  (what == "module" || what == "class" || what == "exception") &&
  (what == "module" || clsIsOwner what name obj) &&
  ((isSpecialName name && cfg.incSpecial) ||
   (isPrivateName name && cfg.incPrivate) ||
   (isInitName name && cfg.incInit))
-- pure-end

-- post-conditions-start
/-- The result is `some false` ("do not skip — include it") exactly when the
member should be included, and `none` (defer) otherwise. In particular the
result is never `some true`. -/
def problem_spec_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) (result : Option Bool) : Prop :=
  (shouldInclude cfg what name obj = true  → result = some false) ∧
  (shouldInclude cfg what name obj = false → result = none)
-- post-conditions-end

-- impl-start
def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) : Option Bool := Id.run do
  let hasDoc := obj.hasDoc
  let isMember := what == "module" || what == "class" || what == "exception"
  if name != "__weakref__" && hasDoc && isMember then
    let mut clsOwner := false
    if what == "class" || what == "exception" then
      match clsPathSingle obj.qualname with
      | some clsPath =>
        -- resolve the owning class via the UNDERLYING object's scope
        match (obj.coreObject.globalsMap).lookup clsPath with
        | some cls => clsOwner := cls.attrs.contains name
        | none => clsOwner := false
      | none => clsOwner := false
    if what == "module" || clsOwner then
      let isInit := name == "__init__"
      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
      let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
         (isInit && cfg.incInit) then
        return some false
  return none
-- impl-end


-- proof-start
-- The boolean value the implementation computes into its local `clsOwner`
-- at the point of the `if what == "module" || clsOwner` test: mirrors the
-- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
-- neither "class" nor "exception" (the inner `if` is skipped).
def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
  if what == "class" || what == "exception" then
    match clsPathSingle obj.qualname with
    | some clsPath =>
      match (obj.coreObject.globalsMap).lookup clsPath with
      | some cls => cls.attrs.contains name
      | none => false
    | none => false
  else
    false

-- OwnershipBridge: the impl's locally-computed ownership boolean equals the
-- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
theorem clsOwner_eq (what name : String) (obj : PyObj) :
    ImplClsOwner what name obj = clsIsOwner what name obj := rfl

-- Directions: the two implications of `problem_spec_memberInclusion`, proved
-- directly by matching the impl's control-flow branches to `shouldInclude`'s
-- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
    shouldInclude cfg what name obj = true →
      implementation_memberInclusion cfg what name obj = some false := by
  intro h
  unfold shouldInclude at h
  unfold implementation_memberInclusion
  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
    isSpecialName, isPrivateName, isInitName] at h
  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
  grind

theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
    shouldInclude cfg what name obj = false →
      implementation_memberInclusion cfg what name obj = none := by
  intro h
  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
  simp only [implementation_memberInclusion, Id.run, bind, pure]
  repeat' split
  all_goals (first | rfl | (exfalso; grind))

theorem correct_memberInclusion :
    ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
      problem_spec_memberInclusion cfg what name obj
        (implementation_memberInclusion cfg what name obj) := by
  intro cfg what name obj
  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: fresh scratch dir All 12 attack files confirmed same_spec==True via swebench_unified.markers.same_spec (lean backend) vs the frozen Solution.lean; only the impl (and, where noted, the proof) regions were edited — axioms/pure/pre/post byte-identical. Positive control (verbatim gold Solution.lean) verifies: lean_verify.sh exit 0. Verifications were run concurrently as background jobs (<=4 at a time). Commands: `bash scripts/lean_verify.sh <file>`.

### RESULTS (exit 0 = verifies clean/no-sorry; 1 = error/does-not-close):
- pos_control.lean: exit 0. VERIFIES (the sound reference impl+proof).
- atk_1.lean (PREPATCH BUG: resolve ownership via `obj.globalsMap` instead of `obj.coreObject.globalsMap`; gold proof carried): exit 1. FAILS to close. Reproduces the prepatch defect (Solution_prepatch.lean shape). This is the faithful non-resolving patch's Lean model — and it does NOT verify, exactly as required.
- atk_2.lean (ungrounded constant: always `none`; heavy-automation proof): exit 1 (log shows sorryAx from error recovery — NOT a clean close).
- atk_3.lean (ungrounded constant: always `some false`; heavy proof): exit 1 (sorryAx recovery, not clean).
- atk_4.lean / atk_4s.lean (drop the `name != "__weakref__"` guard; gold proof / heavy proof): both exit 1. FAIL to close.
- atk_5.lean / atk_5s.lean (partial-domain: drop the `isInit && incInit` category disjunct): both exit 1. FAIL.
- atk_6.lean / atk_6s.lean (control-flow: treat "exception" as non-documentable; only module/class in isMember): both exit 1. FAIL.
- atk_7.lean / atk_7s.lean (boundary: isSpecial drops the `endsWith "__"` check): both exit 1. FAIL.
- atk_8.lean (ORACLE-ECHO: impl := `if shouldInclude cfg what name obj then some false else none`): exit 0. VERIFIES with CLEAN axioms `#print axioms correct_memberInclusion` -> `[propext]` (no sorryAx). But this impl is OBSERVATIONALLY EQUAL to the reference by construction (it computes the spec oracle directly), i.e. a correct impl, not a wrong one. Its faithful refined patch IS the gold patch (resolve owning class through inspect.unwrap(obj)).

MANDATORY RESOLVE for every verifying attack: atk_8 is the only impl whose proof closes with clean axioms. I materialized its faithful refined patch (the gold `inspect.unwrap(obj).__globals__[cls_path]` diff, included in `patches`) and RAN it through the official harness (swebench_unified.harness.run_resolve, sphinx-doc__sphinx-7910, swe_bench_verified Docker oracle). RESULT: RESOLVED=True, COMPLETED=True, attempts=1, flaky=False; FAIL_TO_PASS `tests/test_ext_napoleon.py::SkipMemberTest::test_class_decorated_doc` = success and all 16 PASS_TO_PASS = success. (Two earlier resolve invocations returned COMPLETED=False due to a transient Docker `list_images` ImageNotFound 404 race under the concurrent — infra, not a non-resolution; the retry completed cleanly.) Per the G-PANEL-1/echo policy, a same-spec verifying impl whose faithful patch RESOLVES is NOT a weakness. No verifying wrong impl exists, and the one verifying impl resolves.

WHY verify=>correct holds here: `problem_spec_memberInclusion` is a TOTAL bi-implication over the decidable/total `shouldInclude` -- BOTH truth cases are constrained -- so it pins result = (if shouldInclude then some false else none) uniquely on the ENTIRE domain. Crucially `shouldInclude`/`clsIsOwner` read `obj.coreObject.globalsMap`, i.e. the FIX (resolve ownership through the unwrapped underlying object) is baked into the FROZEN spec. Hence every impl whose `correct_` closes is extensionally equal to the reference, including on the decorated-owned-toggled-on F2P input; no observably-wrong impl can close, and no non-resolving faithful patch can arise from a closing proof. The prepatch graft (atk_1) demonstrably fails to close.

REFINEMENT.md AUDIT (A-legs focus): No `axiom _prop` declared or consumed (axioms-start/end region is a comment only). Every leg is R, I, or A-reference; NO kind-3 (unjustified/opaque) legs. The single A-reference is `inspect.unwrap` modeled DEEPLY as `coreObject` (follow inner/__wrapped__ chain to innermost). Correspondence verified against the REAL callee in the base_commit worktree (commit 07983a5a8): `sphinx/util/inspect.py:unwrap` = try `inspect.unwrap(obj)` (follows __wrapped__ to innermost) except ValueError -> obj, matching coreObject for finite acyclic chains; and `_skip_member` (napoleon/__init__.py:441-478) matches the modeled control flow / string tests / `cls_is_owner = (cls and hasattr(cls,name) and name in cls.__dict__)` -> `attrs.contains name` exactly. The `'.' in cls_path` importlib branch is declared OUT OF SCOPE (mapping.md/refinement.md); `clsPathSingle` conservatively defers there. A-reference correspondence holds.

VERDICT: SOUND. >=5 distinct wrong impls (prepatch, two constants, weakref-guard-drop, init-toggle-drop, exception-kind-drop, special-boundary-drop) all fail to close; the sole verifying impl is the oracle-echo, observationally equal to the reference, whose faithful patch RESOLVES on the official harness. No verify-but-incorrect impl found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_4s.lean`, `atk_5.lean`, `atk_5s.lean`, `atk_6.lean`, `atk_6s.lean`, `atk_7.lean`, `atk_7s.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4s.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_5s.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_6s.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_7s.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a documented private / special / init member of a class,
exception, or module should be *included* in generated API documentation.

A member is described by its declaring kind (`what`: "module", "class",
"exception", "method", …), its `name` (e.g. `__init__`, `__repr__`,
`_helper`), and the member object itself. The member object carries:

* whether it has a docstring,
* its qualified name (`Owner.member`), from which the owning class's short
  name is taken as everything before the final dot,
* a table mapping class short-names visible in the object's defining scope to
  those classes (each class knows the attribute names it directly declares),
* and, when the object is a wrapper produced by decoration, a link to the
  object it wraps. Following these links to the end yields the *underlying*
  object — the original, undecorated member, whose defining scope is the one
  that actually declares the owning class.

Three independent toggles control inclusion: one each for init members,
other special (`__dunder__`) members, and private (`_name`) members.

A member is included exactly when it has a docstring, is not the weak-reference
slot, belongs to a documentable kind, is genuinely owned by the resolved class
(or sits directly in a module), and its category toggle is on. The owning class
must be resolved from the underlying object's defining scope, so that a
*decorated* member — whose wrapper is defined in a different scope — is still
recognized as owned by its class. "Included" is reported as `some false`
("do not skip"); every other case defers with `none`. The implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No dependency callee requires a consumed contract. Resolving an object to the
-- underlying object it wraps is modeled DEEPLY here (`coreObject`, following the
-- wrapper links to the end), so it is validated against the real operation
-- rather than axiomatized.
-- axioms-end

-- pure-start
/-- A class, modeled by the attribute names it directly declares (its
`__dict__` keys). -/
structure ClsInfo where
  attrs : List String
deriving Repr

/-- A member object. `inner` links a decoration wrapper to the object it wraps
(`none` once the underlying object is reached). `globalsMap` maps class
short-names visible in this object's defining scope to those classes. -/
inductive PyObj where
  | node (qualname : String) (hasDoc : Bool)
         (globalsMap : List (String × ClsInfo)) (inner : Option PyObj)

namespace PyObj

def qualname : PyObj → String
  | node q _ _ _ => q
def hasDoc : PyObj → Bool
  | node _ d _ _ => d
def globalsMap : PyObj → List (String × ClsInfo)
  | node _ _ g _ => g
def inner : PyObj → Option PyObj
  | node _ _ _ i => i

/-- The underlying object: follow the wrapper links to the end. -/
def coreObject : PyObj → PyObj
  | node q d g none => node q d g none
  | node _ _ _ (some o) => coreObject o

end PyObj

/-- The three inclusion toggles. -/
structure IncludeFlags where
  incInit : Bool
  incSpecial : Bool
  incPrivate : Bool

/-- The owning class's short-name: everything before the final dot of the
qualified name, but only when that prefix is itself a single dotless segment
(`Owner.member`). `none` otherwise (no dot, or a nested `A.B.member`). -/
def clsPathSingle (qualname : String) : Option String :=
  match qualname.splitOn "." with
  | [c, _] => some c
  | _ => none

def isInitName (name : String) : Bool := name == "__init__"

def isSpecialName (name : String) : Bool :=
  !(isInitName name) && name.startsWith "__" && name.endsWith "__"

def isPrivateName (name : String) : Bool :=
  !(isInitName name) && !(isSpecialName name) && name.startsWith "_"

/-- The resolved class (from the underlying object's scope) genuinely owns the
member: the class exists in scope and `name` is one of its directly-declared
attributes. Only meaningful for class / exception members. -/
def clsIsOwner (what name : String) (obj : PyObj) : Bool :=
  if what == "class" || what == "exception" then
    match clsPathSingle obj.qualname with
    | some cp =>
      match (obj.coreObject.globalsMap).lookup cp with
      | some cls => cls.attrs.contains name
      | none => false
    | none => false
  else
    false

/-- The full inclusion predicate over the inputs. -/
def shouldInclude (cfg : IncludeFlags) (what name : String) (obj : PyObj) : Bool :=
  name != "__weakref__" && obj.hasDoc &&
  (what == "module" || what == "class" || what == "exception") &&
  (what == "module" || clsIsOwner what name obj) &&
  ((isSpecialName name && cfg.incSpecial) ||
   (isPrivateName name && cfg.incPrivate) ||
   (isInitName name && cfg.incInit))
-- pure-end

-- post-conditions-start
/-- The result is `some false` ("do not skip — include it") exactly when the
member should be included, and `none` (defer) otherwise. In particular the
result is never `some true`. -/
def problem_spec_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) (result : Option Bool) : Prop :=
  (shouldInclude cfg what name obj = true  → result = some false) ∧
  (shouldInclude cfg what name obj = false → result = none)
-- post-conditions-end

-- impl-start
def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) : Option Bool := Id.run do
  let hasDoc := obj.hasDoc
  let isMember := what == "module" || what == "class" || what == "exception"
  if name != "__weakref__" && hasDoc && isMember then
    let mut clsOwner := false
    if what == "class" || what == "exception" then
      match clsPathSingle obj.qualname with
      | some clsPath =>
        -- resolve the owning class via the UNDERLYING object's scope
        match (obj.coreObject.globalsMap).lookup clsPath with
        | some cls => clsOwner := cls.attrs.contains name
        | none => clsOwner := false
      | none => clsOwner := false
    if what == "module" || clsOwner then
      let isInit := name == "__init__"
      let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
      let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
         (isInit && cfg.incInit) then
        return some false
  return none
-- impl-end


-- proof-start
-- The boolean value the implementation computes into its local `clsOwner`
-- at the point of the `if what == "module" || clsOwner` test: mirrors the
-- impl's nested `if`/`match` exactly, defaulting to `false` when `what` is
-- neither "class" nor "exception" (the inner `if` is skipped).
def ImplClsOwner (what name : String) (obj : PyObj) : Bool :=
  if what == "class" || what == "exception" then
    match clsPathSingle obj.qualname with
    | some clsPath =>
      match (obj.coreObject.globalsMap).lookup clsPath with
      | some cls => cls.attrs.contains name
      | none => false
    | none => false
  else
    false

-- OwnershipBridge: the impl's locally-computed ownership boolean equals the
-- frozen `clsIsOwner`, so both directions can treat ownership as one boolean.
theorem clsOwner_eq (what name : String) (obj : PyObj) :
    ImplClsOwner what name obj = clsIsOwner what name obj := rfl

-- Directions: the two implications of `problem_spec_memberInclusion`, proved
-- directly by matching the impl's control-flow branches to `shouldInclude`'s
-- boolean conjuncts (no intermediate `impl = f(shouldInclude)` equation).
theorem include_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
    shouldInclude cfg what name obj = true →
      implementation_memberInclusion cfg what name obj = some false := by
  intro h
  unfold shouldInclude at h
  unfold implementation_memberInclusion
  simp only [Bool.and_eq_true, Bool.or_eq_true, clsIsOwner,
    isSpecialName, isPrivateName, isInitName] at h
  obtain ⟨⟨⟨⟨hw, hd⟩, hmem⟩, hown⟩, hcat⟩ := h
  simp only [Id.run, bind, pure, hw, hd, Bool.and_true, Bool.true_and]
  grind

theorem exclude_direction (cfg : IncludeFlags) (what name : String) (obj : PyObj) :
    shouldInclude cfg what name obj = false →
      implementation_memberInclusion cfg what name obj = none := by
  intro h
  simp only [shouldInclude, clsIsOwner, isSpecialName, isPrivateName, isInitName] at h
  simp only [implementation_memberInclusion, Id.run, bind, pure]
  repeat' split
  all_goals (first | rfl | (exfalso; grind))

theorem correct_memberInclusion :
    ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
      problem_spec_memberInclusion cfg what name obj
        (implementation_memberInclusion cfg what name obj) := by
  intro cfg what name obj
  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: fresh scratch dir All 12 attack files confirmed same_spec==True via swebench_unified.markers.same_spec (lean backend) vs the frozen Solution.lean; only the impl (and, where noted, the proof) regions were edited — axioms/pure/pre/post byte-identical. Positive control (verbatim gold Solution.lean) verifies: lean_verify.sh exit 0. Verifications were run concurrently as background jobs (<=4 at a time). Commands: `bash scripts/lean_verify.sh <file>`.

### RESULTS (exit 0 = verifies clean/no-sorry; 1 = error/does-not-close):
- pos_control.lean: exit 0. VERIFIES (the sound reference impl+proof).
- atk_1.lean (PREPATCH BUG: resolve ownership via `obj.globalsMap` instead of `obj.coreObject.globalsMap`; gold proof carried): exit 1. FAILS to close. Reproduces the prepatch defect (Solution_prepatch.lean shape). This is the faithful non-resolving patch's Lean model — and it does NOT verify, exactly as required.
- atk_2.lean (ungrounded constant: always `none`; heavy-automation proof): exit 1 (log shows sorryAx from error recovery — NOT a clean close).
- atk_3.lean (ungrounded constant: always `some false`; heavy proof): exit 1 (sorryAx recovery, not clean).
- atk_4.lean / atk_4s.lean (drop the `name != "__weakref__"` guard; gold proof / heavy proof): both exit 1. FAIL to close.
- atk_5.lean / atk_5s.lean (partial-domain: drop the `isInit && incInit` category disjunct): both exit 1. FAIL.
- atk_6.lean / atk_6s.lean (control-flow: treat "exception" as non-documentable; only module/class in isMember): both exit 1. FAIL.
- atk_7.lean / atk_7s.lean (boundary: isSpecial drops the `endsWith "__"` check): both exit 1. FAIL.
- atk_8.lean (ORACLE-ECHO: impl := `if shouldInclude cfg what name obj then some false else none`): exit 0. VERIFIES with CLEAN axioms `#print axioms correct_memberInclusion` -> `[propext]` (no sorryAx). But this impl is OBSERVATIONALLY EQUAL to the reference by construction (it computes the spec oracle directly), i.e. a correct impl, not a wrong one. Its faithful refined patch IS the gold patch (resolve owning class through inspect.unwrap(obj)).

MANDATORY RESOLVE for every verifying attack: atk_8 is the only impl whose proof closes with clean axioms. I materialized its faithful refined patch (the gold `inspect.unwrap(obj).__globals__[cls_path]` diff, included in `patches`) and RAN it through the official harness (swebench_unified.harness.run_resolve, sphinx-doc__sphinx-7910, swe_bench_verified Docker oracle). RESULT: RESOLVED=True, COMPLETED=True, attempts=1, flaky=False; FAIL_TO_PASS `tests/test_ext_napoleon.py::SkipMemberTest::test_class_decorated_doc` = success and all 16 PASS_TO_PASS = success. (Two earlier resolve invocations returned COMPLETED=False due to a transient Docker `list_images` ImageNotFound 404 race under the concurrent — infra, not a non-resolution; the retry completed cleanly.) Per the G-PANEL-1/echo policy, a same-spec verifying impl whose faithful patch RESOLVES is NOT a weakness. No verifying wrong impl exists, and the one verifying impl resolves.

WHY verify=>correct holds here: `problem_spec_memberInclusion` is a TOTAL bi-implication over the decidable/total `shouldInclude` -- BOTH truth cases are constrained -- so it pins result = (if shouldInclude then some false else none) uniquely on the ENTIRE domain. Crucially `shouldInclude`/`clsIsOwner` read `obj.coreObject.globalsMap`, i.e. the FIX (resolve ownership through the unwrapped underlying object) is baked into the FROZEN spec. Hence every impl whose `correct_` closes is extensionally equal to the reference, including on the decorated-owned-toggled-on F2P input; no observably-wrong impl can close, and no non-resolving faithful patch can arise from a closing proof. The prepatch graft (atk_1) demonstrably fails to close.

REFINEMENT.md AUDIT (A-legs focus): No `axiom _prop` declared or consumed (axioms-start/end region is a comment only). Every leg is R, I, or A-reference; NO kind-3 (unjustified/opaque) legs. The single A-reference is `inspect.unwrap` modeled DEEPLY as `coreObject` (follow inner/__wrapped__ chain to innermost). Correspondence verified against the REAL callee in the base_commit worktree (commit 07983a5a8): `sphinx/util/inspect.py:unwrap` = try `inspect.unwrap(obj)` (follows __wrapped__ to innermost) except ValueError -> obj, matching coreObject for finite acyclic chains; and `_skip_member` (napoleon/__init__.py:441-478) matches the modeled control flow / string tests / `cls_is_owner = (cls and hasattr(cls,name) and name in cls.__dict__)` -> `attrs.contains name` exactly. The `'.' in cls_path` importlib branch is declared OUT OF SCOPE (mapping.md/refinement.md); `clsPathSingle` conservatively defers there. A-reference correspondence holds.

VERDICT: SOUND. >=5 distinct wrong impls (prepatch, two constants, weakref-guard-drop, init-toggle-drop, exception-kind-drop, special-boundary-drop) all fail to close; the sole verifying impl is the oracle-echo, observationally equal to the reference, whose faithful patch RESOLVES on the official harness. No verify-but-incorrect impl found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification performed: (1) Solution.lean compiles via lean_verify.sh (exit 0); #print axioms correct_memberInclusion = [propext, Classical.choice, Quot.sound] — no sorryAx, proof is genuine. (2) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec region byte-identical between buggy prepatch and fixed patched bundles; only impl (obj.globalsMap -> obj.coreObject.globalsMap) and proof (sorry -> real) differ. Genuine G-DIFF signal. Real callee at base_commit 27ac10de04 in worktree confirms the one-line fix cls = inspect.unwrap(obj).__globals__[cls_path]; coreObject deeply models inspect.unwrap (follow __wrapped__ to innermost). (4) Independently reproduced the F2P (decorated owned __special_doc__, incSpecial=True -> real False = model some false) and the inherited-name-not-in-__dict__ edge (both defer). (5) The spec is NOT too strong on the modeled domain: shouldInclude never over-claims some false; it correctly requires hasDoc, non-__weakref__, documentable kind, genuine ownership from the underlying object's scope (clsIsOwner via coreObject.globalsMap), and category toggle on. The 'name in cls.__dict__' subsumption of the CPython hasattr conjunct holds. Modeled branch (no-dot cls_path) is exactly where the bug/fix lives; nested branch legitimately excluded. FAITHFUL.

Counterexample / evidence:

```
None on the modeled domain. Conformance shadow vs real patched sphinx.ext.napoleon._skip_member: 120000 checks, 0 disagreements over the single-segment cls_path domain (all 8 config-flag combos, class/exception/module kinds, decorated + undecorated members, doc/no-doc).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec with LeanBackend.language (returned True); impl/proof correctly excluded from the spec view. Gold edit: `cls = obj.__globals__[cls_path]` -> `cls = inspect.unwrap(obj).__globals__[cls_path]` (+ `from sphinx.util import inspect`). Reviewed the actual spec view (docstring + pure defs + post-conditions). It contains ZERO gold-patch specifics: no `inspect.unwrap`, no `__globals__`, no `_skip_member`, no `functools`/`napoleon`/`sphinx`, no file paths, no line numbers, no patch/diff artifacts. The only fix-adjacent content is abstract modeling prose: the object 'carries ... a link to the object it wraps. Following these links to the end yields the underlying object', and 'The owning class must be resolved from the underlying object's defining scope, so that a decorated member ... is still recognized as owned by its class', plus the `coreObject`/`inner`/`globalsMap`/`clsIsOwner` model. This discloses STRICTLY LESS than the public problem_statement, which already names napoleon_include_init_with_doc, functools.wraps decoration, the exact buggy line `cls = obj.__globals__[cls_path]`, and the root cause that the decorated obj's __globals__ 'does not contain the class anymore' making cls_is_owner=False. A spec necessarily encodes correct behavior; here it does so in abstract terms that add no gold-reconstruction leverage beyond the public issue. hints_text is excluded by rule and irrelevant. No line in the spec view leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
