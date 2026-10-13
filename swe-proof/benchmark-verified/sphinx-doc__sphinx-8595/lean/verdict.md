# P2 adversarial audit — sphinx-doc__sphinx-8595

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,17 +79,22 @@
     (members : List String) (requested : List String) :
     Bool × List (String × Bool) := Id.run do
   if wantAll then
-    match allAttr with
-    | none =>
+    let absentOrEmpty : Bool := match allAttr with
+      | none => true
+      | some xs => xs.isEmpty
+    if absentOrEmpty then
       let mut out : List (String × Bool) := []
       for n in members do
         out := out ++ [(n, false)]
       return (true, out)
-    | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
+    else
+      match allAttr with
+      | none => return (true, [])
+      | some allNames =>
+        let mut out : List (String × Bool) := []
+        for n in members do
+          out := out ++ [(n, !allNames.contains n)]
+        return (false, out)
   else
     let mut ret : List (String × Bool) := []
     for name in requested do
@@ -106,41 +111,10 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
   unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  first
+    | rfl
+    | (cases wantAll <;> cases allAttr <;> simp_all <;> rfl)
+    | (simp_all <;> rfl)
+    | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,25 +77,14 @@
 def implementation_selectMembers
     (wantAll : Bool) (allAttr : Option (List String))
     (members : List String) (requested : List String) :
-    Bool × List (String × Bool) := Id.run do
+    Bool × List (String × Bool) := 
   if wantAll then
     match allAttr with
-    | none =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, false)]
-      return (true, out)
-    | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
+    | none => (true, members.map (fun n => (n, false)))
+    | some allNames => (false, members.map (fun n => (n, allNames.contains n)))
   else
-    let mut ret : List (String × Bool) := []
-    for name in requested do
-      if members.contains name then
-        ret := ret ++ [(name, false)]
-    return (false, ret)
+    (false, requested.filterMap
+      (fun name => if members.contains name then some (name, false) else none))
 -- impl-end
 
 
@@ -106,41 +95,10 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
   unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  first
+    | rfl
+    | (cases wantAll <;> cases allAttr <;> simp_all <;> rfl)
+    | (simp_all <;> rfl)
+    | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,25 +77,14 @@
 def implementation_selectMembers
     (wantAll : Bool) (allAttr : Option (List String))
     (members : List String) (requested : List String) :
-    Bool × List (String × Bool) := Id.run do
+    Bool × List (String × Bool) := 
   if wantAll then
     match allAttr with
-    | none =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, false)]
-      return (true, out)
-    | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
+    | none => (false, members.map (fun n => (n, false)))
+    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
   else
-    let mut ret : List (String × Bool) := []
-    for name in requested do
-      if members.contains name then
-        ret := ret ++ [(name, false)]
-    return (false, ret)
+    (false, requested.filterMap
+      (fun name => if members.contains name then some (name, false) else none))
 -- impl-end
 
 
@@ -106,41 +95,10 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
   unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  first
+    | rfl
+    | (cases wantAll <;> cases allAttr <;> simp_all <;> rfl)
+    | (simp_all <;> rfl)
+    | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,25 +77,13 @@
 def implementation_selectMembers
     (wantAll : Bool) (allAttr : Option (List String))
     (members : List String) (requested : List String) :
-    Bool × List (String × Bool) := Id.run do
+    Bool × List (String × Bool) := 
   if wantAll then
     match allAttr with
-    | none =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, false)]
-      return (true, out)
-    | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
+    | none => (true, members.map (fun n => (n, false)))
+    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
   else
-    let mut ret : List (String × Bool) := []
-    for name in requested do
-      if members.contains name then
-        ret := ret ++ [(name, false)]
-    return (false, ret)
+    (false, requested.map (fun name => (name, false)))
 -- impl-end
 
 
@@ -106,41 +94,10 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
   unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  first
+    | rfl
+    | (cases wantAll <;> cases allAttr <;> simp_all <;> rfl)
+    | (simp_all <;> rfl)
+    | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,25 +77,14 @@
 def implementation_selectMembers
     (wantAll : Bool) (allAttr : Option (List String))
     (members : List String) (requested : List String) :
-    Bool × List (String × Bool) := Id.run do
+    Bool × List (String × Bool) := 
   if wantAll then
     match allAttr with
-    | none =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, false)]
-      return (true, out)
-    | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
+    | none => (true, members.map (fun n => (n, false)))
+    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
   else
-    let mut ret : List (String × Bool) := []
-    for name in requested do
-      if members.contains name then
-        ret := ret ++ [(name, false)]
-    return (false, ret)
+    (false, requested.reverse.filterMap
+      (fun name => if members.contains name then some (name, false) else none))
 -- impl-end
 
 
@@ -106,41 +95,10 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
   unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  first
+    | rfl
+    | (cases wantAll <;> cases allAttr <;> simp_all <;> rfl)
+    | (simp_all <;> rfl)
+    | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,25 +77,18 @@
 def implementation_selectMembers
     (wantAll : Bool) (allAttr : Option (List String))
     (members : List String) (requested : List String) :
-    Bool × List (String × Bool) := Id.run do
+    Bool × List (String × Bool) := 
   if wantAll then
     match allAttr with
-    | none =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, false)]
-      return (true, out)
+    | none => (true, members.map (fun n => (n, false)))
     | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
+        if allNames.isEmpty then
+          (false, members.map (fun n => (n, false)))
+        else
+          (false, members.map (fun n => (n, !allNames.contains n)))
   else
-    let mut ret : List (String × Bool) := []
-    for name in requested do
-      if members.contains name then
-        ret := ret ++ [(name, false)]
-    return (false, ret)
+    (false, requested.filterMap
+      (fun name => if members.contains name then some (name, false) else none))
 -- impl-end
 
 
@@ -106,41 +99,10 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
   unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  first
+    | rfl
+    | (cases wantAll <;> cases allAttr <;> simp_all <;> rfl)
+    | (simp_all <;> rfl)
+    | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,25 +77,7 @@
 def implementation_selectMembers
     (wantAll : Bool) (allAttr : Option (List String))
     (members : List String) (requested : List String) :
-    Bool × List (String × Bool) := Id.run do
-  if wantAll then
-    match allAttr with
-    | none =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, false)]
-      return (true, out)
-    | some allNames =>
-      let mut out : List (String × Bool) := []
-      for n in members do
-        out := out ++ [(n, !allNames.contains n)]
-      return (false, out)
-  else
-    let mut ret : List (String × Bool) := []
-    for name in requested do
-      if members.contains name then
-        ret := ret ++ [(name, false)]
-    return (false, ret)
+    Bool × List (String × Bool) := selectMembers wantAll allAttr members requested
 -- impl-end
 
 
@@ -106,41 +88,5 @@
       problem_spec_selectMembers wantAll allAttr members requested
         (implementation_selectMembers wantAll allAttr members requested) := by
   intro wantAll allAttr members requested
-  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
-      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
-    intro f xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
-      rw [ih]; simp
-  have fmKey : ∀ (xs : List String) (acc),
-      (forIn (m := Id) xs acc
-        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
-          else pure (ForInStep.yield r))) =
-        acc ++ xs.filterMap
-          (fun name => if name ∈ members then some (name, false) else none) := by
-    intro xs
-    induction xs with
-    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
-    | cons h t ih =>
-      intro acc
-      rw [List.forIn_cons]
-      by_cases hh : h ∈ members
-      · simp only [hh, if_true]
-        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
-        rw [ih]; simp [hh]
-      · simp only [hh, if_false]
-        show (forIn (m:=Id) t acc _) = _
-        rw [ih]; simp [hh]
-  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
-  cases wantAll
-  · simp only [Bool.false_eq_true, if_false]
-    simp [fmKey]
-    rfl
-  · simp only [if_true]
-    cases allAttr <;> simp [mapKey] <;> rfl
-
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing which members of a module to document.

When every member of a module is to be considered, an explicit export list (the
module's `__all__`) governs the selection:

* if the module declares no export list at all, every discovered member is kept
  and documentation proceeds over all of them (an implicit check on origin is
  left to a later stage);
* if the module declares an export list — *including one that names nothing* —
  the selection is restricted to exactly the named members: every discovered
  member is kept in the result but any member whose name is not in the export
  list is marked as skipped.

When members are instead requested by name, only the requested names that are
actually present as members are returned, in the order requested.

The result is a pair: a flag saying whether the caller should still apply the
implicit origin check, together with the list of discovered members each tagged
with whether it is skipped.

A present-but-naming-nothing export list therefore keeps no member: every
discovered member is marked skipped, so the module contributes no documented
entries. This is the behavior that must hold for any export list, regardless of
how many names it carries.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The member
-- selection — the export-list-driven skipped tagging and the by-name lookup —
-- is modeled DEEPLY over the observable inputs (the export list, the discovered
-- member names, the requested names), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Select the members to document.

`wantAll` is true when every member is to be considered. `allAttr` is the
module's export list: `none` when the module declares none, `some names` when it
declares one (possibly naming nothing). `members` are the discovered member
names, in order. `requested` are the member names explicitly asked for (used
only when `wantAll` is false).

Returns `(check, tagged)` where `check` is the flag asking the caller to still
apply the implicit origin check, and `tagged` pairs each kept member name with
its skipped flag. -/
def selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) :=
  if wantAll then
    match allAttr with
    | none => (true, members.map (fun n => (n, false)))
    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
  else
    (false, requested.filterMap
      (fun name => if members.contains name then some (name, false) else none))
-- pure-end

-- post-conditions-start
/-- The selection produces exactly the pair dictated by the rule above: the
correct origin-check flag, and the discovered members each tagged with the right
skipped flag (or, when members are requested by name, exactly the present
requested names). -/
def problem_spec_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String)
    (result : Bool × List (String × Bool)) : Prop :=
  result = selectMembers wantAll allAttr members requested
-- post-conditions-end

-- impl-start
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)
-- impl-end


-- proof-start
theorem correct_selectMembers :
    ∀ (wantAll : Bool) (allAttr : Option (List String))
      (members : List String) (requested : List String),
      problem_spec_selectMembers wantAll allAttr members requested
        (implementation_selectMembers wantAll allAttr members requested) := by
  intro wantAll allAttr members requested
  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
    intro f xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
      rw [ih]; simp
  have fmKey : ∀ (xs : List String) (acc),
      (forIn (m := Id) xs acc
        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
          else pure (ForInStep.yield r))) =
        acc ++ xs.filterMap
          (fun name => if name ∈ members then some (name, false) else none) := by
    intro xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      by_cases hh : h ∈ members
      · simp only [hh, if_true]
        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
        rw [ih]; simp [hh]
      · simp only [hh, if_false]
        show (forIn (m:=Id) t acc _) = _
        rw [ih]; simp [hh]
  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
  cases wantAll
  · simp only [Bool.false_eq_true, if_false]
    simp [fmKey]
    rfl
  · simp only [if_true]
    cases allAttr <;> simp [mapKey] <;> rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: strongest possible. problem_spec_selectMembers := (result = selectMembers wantAll allAttr members requested) — EXACT pointwise equality against a TOTAL COMPUTABLE oracle (selectMembers), with an EMPTY axioms region (no opaque/axiom callees, no A-legs; G-AX legitimately skips). Any impl differing from the oracle at even one input makes the equality provably FALSE, so no closing proof can exist for a genuinely-wrong impl.

PROTOCOL: All work Every attack built by copying Solution.lean and editing ONLY the impl (+ its own proof attempt); axioms/pure/pre/post byte-identical. same_spec(lean) = True verified for all 7 attacks AND pos_control.

VERIFY COMMAND: `bash scripts/lean_verify.sh <file>`. Run concurrently in batches of 4 (background jobs).

### RESULTS (verify exit code):
- pos_control (gold impl): EXIT 0 (verifies). #print axioms => [propext, Quot.sound] (clean, standard Mathlib).
- atk_1 PREPATCH BUG (some [] treated like none => keep-all): EXIT 1, proof fails (unsolved goals on empty-__all__ case). Bug reproduced.
- atk_2 BOUNDARY (flipped skipped flag: allNames.contains n instead of !contains): EXIT 1, proof fails.
- atk_3 FLAG (none-path returns check=false instead of true): EXIT 1, proof fails.
- atk_4 CONTROL-FLOW-EFFECT (by-name branch drops membership filter, requested.map): EXIT 1, proof fails.
- atk_5 PARTIAL-DOMAIN (by-name uses requested.reverse): EXIT 1, proof fails.
- atk_6 PARTIAL-DOMAIN (some [] special-cased to keep-all unskipped; agrees except empty allNames + nonempty members): EXIT 1, proof fails.
- atk_7 UNGROUNDED-ORACLE ECHO (impl := selectMembers ...; semantically CORRECT): EXIT 0 (verifies). #print axioms => does not depend on any axioms (clean).

CLOSING IMPLS: only pos_control and atk_7 close, both semantically CORRECT (== oracle) with clean axioms. Every one of the 6 genuinely-wrong impls FAILS its proof (exit 1).

MANDATORY RESOLVE (protocol step 2): atk_7 is the correct oracle echo => its faithful refined patch is the gold fix (if not self.__all__: => if self.__all__ is None:). Materialized to atk_7.patch and executed via run_resolve('sphinx-doc__sphinx-8595', patch): RESOLVED=True, completed=True, applied=True, FAIL_TO_PASS={'test_empty_all': success}, attempts=1, not flaky. A resolving echo of the gold is NOT a weakness (per unified G-PANEL-1/eq policy). No wrong-impl with a closing clean-axiom proof has a non-resolving faithful patch => no verify=>correct break.

PREPATCH: bundled Solution_prepatch.lean (buggy impl + gold proof body) elaborates with sorry => lean_verify EXIT 3 (G-DIFF: verification failed, as recorded). atk_1 independently re-encodes the prepatch bug with a genuine proof attempt and fails to close (exit 1), confirming the buggy impl cannot satisfy the exact-equality spec.

REFINEMENT.MD AUDIT: 5 legs, all R or I (leg 1 = I control-flow transliteration; legs 2-5 = R type refinements of the Dict/ObjectMember/list carrier to Bool x List (String x Bool)). NO A-consumed, NO A-reference legs — axioms region empty. No kind-3 (ungrounded-axiom) legs present; the A-leg-correspondence mandate is vacuous here. The G-AX skip is justified: the changed op (Option-constructor split distinguishing none from some [] rather than Python truthiness) is deeply modeled over observable inputs, which SPEC_GUIDE §3 requires NOT be axiomatized. mapping.md bijection (None<->none; declared list incl [] <-> some xs; membership <-> List.contains) is faithful to sphinx/ext/autodoc/__init__.py:1073-1098 @ base_commit b19bce97. G-CONF replica mirrors the impl shadow op-for-op.

VERDICT: SOUND. >=5 distinct wrong impls (7 total incl echo) attacked; none with a closing clean-axiom proof has a materialized faithful patch that fails to resolve. The exact-equality-against-total-oracle spec with empty axioms admits no verify=>!correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing which members of a module to document.

When every member of a module is to be considered, an explicit export list (the
module's `__all__`) governs the selection:

* if the module declares no export list at all, every discovered member is kept
  and documentation proceeds over all of them (an implicit check on origin is
  left to a later stage);
* if the module declares an export list — *including one that names nothing* —
  the selection is restricted to exactly the named members: every discovered
  member is kept in the result but any member whose name is not in the export
  list is marked as skipped.

When members are instead requested by name, only the requested names that are
actually present as members are returned, in the order requested.

The result is a pair: a flag saying whether the caller should still apply the
implicit origin check, together with the list of discovered members each tagged
with whether it is skipped.

A present-but-naming-nothing export list therefore keeps no member: every
discovered member is marked skipped, so the module contributes no documented
entries. This is the behavior that must hold for any export list, regardless of
how many names it carries.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The member
-- selection — the export-list-driven skipped tagging and the by-name lookup —
-- is modeled DEEPLY over the observable inputs (the export list, the discovered
-- member names, the requested names), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Select the members to document.

`wantAll` is true when every member is to be considered. `allAttr` is the
module's export list: `none` when the module declares none, `some names` when it
declares one (possibly naming nothing). `members` are the discovered member
names, in order. `requested` are the member names explicitly asked for (used
only when `wantAll` is false).

Returns `(check, tagged)` where `check` is the flag asking the caller to still
apply the implicit origin check, and `tagged` pairs each kept member name with
its skipped flag. -/
def selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) :=
  if wantAll then
    match allAttr with
    | none => (true, members.map (fun n => (n, false)))
    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
  else
    (false, requested.filterMap
      (fun name => if members.contains name then some (name, false) else none))
-- pure-end

-- post-conditions-start
/-- The selection produces exactly the pair dictated by the rule above: the
correct origin-check flag, and the discovered members each tagged with the right
skipped flag (or, when members are requested by name, exactly the present
requested names). -/
def problem_spec_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String)
    (result : Bool × List (String × Bool)) : Prop :=
  result = selectMembers wantAll allAttr members requested
-- post-conditions-end

-- impl-start
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)
-- impl-end


-- proof-start
theorem correct_selectMembers :
    ∀ (wantAll : Bool) (allAttr : Option (List String))
      (members : List String) (requested : List String),
      problem_spec_selectMembers wantAll allAttr members requested
        (implementation_selectMembers wantAll allAttr members requested) := by
  intro wantAll allAttr members requested
  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
    intro f xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
      rw [ih]; simp
  have fmKey : ∀ (xs : List String) (acc),
      (forIn (m := Id) xs acc
        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
          else pure (ForInStep.yield r))) =
        acc ++ xs.filterMap
          (fun name => if name ∈ members then some (name, false) else none) := by
    intro xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      by_cases hh : h ∈ members
      · simp only [hh, if_true]
        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
        rw [ih]; simp [hh]
      · simp only [hh, if_false]
        show (forIn (m:=Id) t acc _) = _
        rw [ih]; simp [hh]
  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
  cases wantAll
  · simp only [Bool.false_eq_true, if_false]
    simp [fmKey]
    rfl
  · simp only [if_true]
    cases allAttr <;> simp [mapKey] <;> rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: strongest possible. problem_spec_selectMembers := (result = selectMembers wantAll allAttr members requested) — EXACT pointwise equality against a TOTAL COMPUTABLE oracle (selectMembers), with an EMPTY axioms region (no opaque/axiom callees, no A-legs; G-AX legitimately skips). Any impl differing from the oracle at even one input makes the equality provably FALSE, so no closing proof can exist for a genuinely-wrong impl.

PROTOCOL: All work Every attack built by copying Solution.lean and editing ONLY the impl (+ its own proof attempt); axioms/pure/pre/post byte-identical. same_spec(lean) = True verified for all 7 attacks AND pos_control.

VERIFY COMMAND: `bash scripts/lean_verify.sh <file>`. Run concurrently in batches of 4 (background jobs).

### RESULTS (verify exit code):
- pos_control (gold impl): EXIT 0 (verifies). #print axioms => [propext, Quot.sound] (clean, standard Mathlib).
- atk_1 PREPATCH BUG (some [] treated like none => keep-all): EXIT 1, proof fails (unsolved goals on empty-__all__ case). Bug reproduced.
- atk_2 BOUNDARY (flipped skipped flag: allNames.contains n instead of !contains): EXIT 1, proof fails.
- atk_3 FLAG (none-path returns check=false instead of true): EXIT 1, proof fails.
- atk_4 CONTROL-FLOW-EFFECT (by-name branch drops membership filter, requested.map): EXIT 1, proof fails.
- atk_5 PARTIAL-DOMAIN (by-name uses requested.reverse): EXIT 1, proof fails.
- atk_6 PARTIAL-DOMAIN (some [] special-cased to keep-all unskipped; agrees except empty allNames + nonempty members): EXIT 1, proof fails.
- atk_7 UNGROUNDED-ORACLE ECHO (impl := selectMembers ...; semantically CORRECT): EXIT 0 (verifies). #print axioms => does not depend on any axioms (clean).

CLOSING IMPLS: only pos_control and atk_7 close, both semantically CORRECT (== oracle) with clean axioms. Every one of the 6 genuinely-wrong impls FAILS its proof (exit 1).

MANDATORY RESOLVE (protocol step 2): atk_7 is the correct oracle echo => its faithful refined patch is the gold fix (if not self.__all__: => if self.__all__ is None:). Materialized to atk_7.patch and executed via run_resolve('sphinx-doc__sphinx-8595', patch): RESOLVED=True, completed=True, applied=True, FAIL_TO_PASS={'test_empty_all': success}, attempts=1, not flaky. A resolving echo of the gold is NOT a weakness (per unified G-PANEL-1/eq policy). No wrong-impl with a closing clean-axiom proof has a non-resolving faithful patch => no verify=>correct break.

PREPATCH: bundled Solution_prepatch.lean (buggy impl + gold proof body) elaborates with sorry => lean_verify EXIT 3 (G-DIFF: verification failed, as recorded). atk_1 independently re-encodes the prepatch bug with a genuine proof attempt and fails to close (exit 1), confirming the buggy impl cannot satisfy the exact-equality spec.

REFINEMENT.MD AUDIT: 5 legs, all R or I (leg 1 = I control-flow transliteration; legs 2-5 = R type refinements of the Dict/ObjectMember/list carrier to Bool x List (String x Bool)). NO A-consumed, NO A-reference legs — axioms region empty. No kind-3 (ungrounded-axiom) legs present; the A-leg-correspondence mandate is vacuous here. The G-AX skip is justified: the changed op (Option-constructor split distinguishing none from some [] rather than Python truthiness) is deeply modeled over observable inputs, which SPEC_GUIDE §3 requires NOT be axiomatized. mapping.md bijection (None<->none; declared list incl [] <-> some xs; membership <-> List.contains) is faithful to sphinx/ext/autodoc/__init__.py:1073-1098 @ base_commit b19bce97. G-CONF replica mirrors the impl shadow op-for-op.

VERDICT: SOUND. >=5 distinct wrong impls (7 total incl echo) attacked; none with a closing clean-axiom proof has a materialized faithful patch that fails to resolve. The exact-equality-against-total-oracle spec with empty axioms admits no verify=>!correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break attempted; none found. The spec's postcondition is `result = selectMembers wantAll allAttr members requested`, so the modeled function IS selectMembers. Compared branch-by-branch against the real POST-PATCH ModuleDocumenter.get_object_members at base_commit b19bce971 (the `is None` guard applied), fetched fresh from upstream (the provided /tmp worktree was at the wrong commit e188d56, an older non-Dict/ObjectMember version — did NOT rely on it).

Correspondence, all faithful:
- want_all, __all__ is None: real returns (True, list(members.values())) with default skipped=False  ⇔ selectMembers none => (true, map (n,false)). ✓
- want_all, __all__=some names: real returns (False, all members) each mutated skipped = (__name__ not in __all__)  ⇔ (false, map (n, !allNames.contains n)). ✓
- want_all, __all__=[] (the F2P/discriminating case): [] is not None so falls to else branch, every member skipped=True  ⇔ some [] => every (n, true). ✓ This is exactly the modeled Option split (none vs some []); the bug (truthiness guard conflating none with some []) lives ONLY in the prepatch impl.
- not want_all: real returns (False, [present requested names in dict-membership, in requested order]); the logger.warning for absent names is an observational side-effect, not in the return value  ⇔ (false, requested.filterMap keep-if-present). ✓

Modeling soundness checks: members is a Dict (unique keys) so member.__name__ equals its dict key by construction in get_module_members — a single List String faithfully serves both the `name in __all__` test and the `name in members` dict-key test; dict-iteration order ↔ List.map order; requested order ↔ filterMap order; ObjectMember default skipped=False matches the unmutated none/None path. No reachable input distinguishes the model from the callee (duplicates are non-reachable given the Dict source, and behave consistently regardless).

Evidence: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical, fix is impl-only). lean_verify exit 0 (compiles, no sorry). `#print axioms correct_selectMembers` => [propext, Quot.sound] — no sorryAx, proof is genuine. conformance_check.py: checked=120009 disagreements=0, status=pass, with the empty-__all__ / None / nonempty edge cases pinned. Spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (verified live via swebench_unified.leakage.screen over the real spec_view): no diff markers, no reproduced gold-patch line, no patched file path/module path, no narration keywords, and no spec-view identifier or comment echoing the changed repo symbol (patch touches get_object_members/get_module_members; spec uses the neutral name `selectMembers`). same_spec(Solution, Solution_prepatch)=True, confirming the spec region is fixed across impls. Semantic (panel-3) analysis: the gold edit is `if not self.__all__:` -> `if self.__all__ is None:`, distinguishing an absent export list from a declared-but-empty one. The public problem_statement ALREADY discloses the intended behavior fully: 'empty __all__ attribute is ignored ... No entries should be shown because __all__ is empty.' The spec-view docstring restates exactly that public expected behavior (no list -> keep all; a declared list 'including one that names nothing' -> members not named are skipped, so an empty list documents nothing) and models it as `Option (List String)` with none vs `some []`. This is the natural faithful specification of behavior already public via the task; it never narrates the fix mechanism (truthiness vs is-None), never quotes the guard, and never names the edited function or file. No leakage of the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
