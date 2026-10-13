# P2 adversarial audit — sympy__sympy-13091

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `ctrl_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closed its proof, so no impl was owed a faithful-patch resolve run. 12 admissible attacks, ALL REFUTED (exit 1) by `decide`, which is a COMPLETE decision procedure on this 96-point Bool/Option Bool domain -- Lean's message is 'Tactic `decide` proved that the proposition ... is FALSE', i.e. the verifier refuted each attack rather than merely failing to close it. Step 2's obligation is therefore vacuous, and I ran three resolve probes anyway on the model<->patch correspondence question (results in notes).
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -119,7 +119,7 @@
   let selfVerdict : Option Bool :=
     if sameObj then some true
     else if identityOnly then some false
-    else if !interpretable then none
+    else if !interpretable then some false
     else if !sameKind then some false
     else some contentEq
   match selfVerdict with
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,9 +131,14 @@
 
 def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
-    contentEq otherVerdict
-  return !eqResult
+  let selfVerdict : Option Bool :=
+    if sameObj then some true
+    else if identityOnly then some false
+    else if !interpretable then none
+    else if !sameKind then some false
+    else some contentEq
+  let selfBool := match selfVerdict with | some b => b | none => true
+  return !selfBool
 -- impl-end
 
 -- proof-start
@@ -144,11 +149,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +159,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,7 +127,7 @@
   | none =>
     match otherVerdict with
     | some b => return b
-    | none => return false
+    | none => return true
 
 def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -117,8 +117,8 @@
 def implementation_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
   let selfVerdict : Option Bool :=
-    if sameObj then some true
-    else if identityOnly then some false
+    if identityOnly then some false
+    else if sameObj then some true
     else if !interpretable then none
     else if !sameKind then some false
     else some contentEq
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -122,10 +122,10 @@
     else if !interpretable then none
     else if !sameKind then some false
     else some contentEq
-  match selfVerdict with
+  match otherVerdict with
   | some b => return b
   | none =>
-    match otherVerdict with
+    match selfVerdict with
     | some b => return b
     | none => return false
 
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,18 +116,9 @@
 -- impl-start
 def implementation_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let selfVerdict : Option Bool :=
-    if sameObj then some true
-    else if identityOnly then some false
-    else if !interpretable then none
-    else if !sameKind then some false
-    else some contentEq
-  match selfVerdict with
+  match otherVerdict with
   | some b => return b
-  | none =>
-    match otherVerdict with
-    | some b => return b
-    | none => return false
+  | none => return sameObj
 
 def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
@@ -144,11 +135,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +145,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,7 +120,7 @@
     if sameObj then some true
     else if identityOnly then some false
     else if !interpretable then none
-    else if !sameKind then some false
+    else if !sameKind then none
     else some contentEq
   match selfVerdict with
   | some b => return b
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -118,7 +118,6 @@
     (otherVerdict : Option Bool) : Bool := Id.run do
   let selfVerdict : Option Bool :=
     if sameObj then some true
-    else if identityOnly then some false
     else if !interpretable then none
     else if !sameKind then some false
     else some contentEq
@@ -144,11 +143,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +153,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,9 +131,18 @@
 
 def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
-    contentEq otherVerdict
-  return !eqResult
+  let selfVerdict : Option Bool :=
+    if sameObj then some true
+    else if identityOnly then some false
+    else if !interpretable then none
+    else if !sameKind then some false
+    else some contentEq
+  match selfVerdict with
+  | some b => return !b
+  | none =>
+    match otherVerdict with
+    | some _ => return true
+    | none => return true
 -- impl-end
 
 -- proof-start
@@ -144,11 +153,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +163,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -121,7 +121,7 @@
     else if identityOnly then some false
     else if !interpretable then none
     else if !sameKind then some false
-    else some contentEq
+    else some (!contentEq)
   match selfVerdict with
   | some b => return b
   | none =>
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -133,7 +133,10 @@
     (otherVerdict : Option Bool) : Bool := Id.run do
   let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
     contentEq otherVerdict
-  return !eqResult
+  if !interpretable && !sameObj && !identityOnly then
+    return eqResult
+  else
+    return !eqResult
 -- impl-end
 
 -- proof-start
@@ -144,11 +147,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +157,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -117,9 +117,9 @@
 def implementation_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
   let selfVerdict : Option Bool :=
-    if sameObj then some true
-    else if identityOnly then some false
+    if identityOnly then (if sameObj then some true else some false)
     else if !interpretable then none
+    else if sameObj then some true
     else if !sameKind then some false
     else some contentEq
   match selfVerdict with
@@ -144,11 +144,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +154,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_pos.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,24 +116,17 @@
 -- impl-start
 def implementation_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let selfVerdict : Option Bool :=
-    if sameObj then some true
-    else if identityOnly then some false
-    else if !interpretable then none
-    else if !sameKind then some false
-    else some contentEq
-  match selfVerdict with
-  | some b => return b
-  | none =>
-    match otherVerdict with
-    | some b => return b
-    | none => return false
+  if sameObj then true
+  else if identityOnly then false
+  else if interpretable then (if sameKind then contentEq else false)
+  else (otherVerdict.getD false)
 
 def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
-    contentEq otherVerdict
-  return !eqResult
+  if sameObj then false
+  else if identityOnly then true
+  else if interpretable then (if sameKind then !contentEq else true)
+  else !(otherVerdict.getD false)
 -- impl-end
 
 -- proof-start
@@ -144,11 +137,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +147,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sympy__sympy-13091 (lean). VERDICT: SOUND. 12 admissible same-spec wrong impls, ALL REJECTED; no candidate arose, so no attack patch was owed to run_resolve; NO patches submitted because no attack verified. I nevertheless materialized and RAN 3 faithful patches through the official harness to attack the A-leg/correspondence surface, and I re-derived refinement.md's central measured claim from scratch.

#### STEP 1: 12 DISTINCT WRONG IMPLS (all same_spec, all admissible)
Built by gen.py, copying Solution.lean and editing ONLY the impl region + the two tactic blocks. Axioms/pure/pre/post regions and both correct_* theorem STATEMENTS byte-identical to frozen (verified: `grep -A6 '^theorem correct_richEq' | md5sum` matches frozen for all 13 files). same_spec=True and unsound_evasions=[] (ADMISSIBLE) for every file via swebench_unified.markers.same_spec + variant_scope.unsound_evasions with LeanBackend.language. No banned token (sorry/admit/native_decide) and no new axiom/opaque/extern in ANY attack file (grep -cE over all 13 => 0).

BEFORE verifying, I enumerated the WHOLE finite input space (2^5 x 3 = 96 tuples) in Python against richEqRef/richNeRef to PROVE each attack genuinely deviates, so a rejection is a real refutation and not a tautology:
  atk_1   prepatch bug #1 (op #3 unapplied: uninterpretable operand returns `some false`, never abstains)   4/96 deviations
  atk_2   prepatch bug #2 (op #7 unapplied: richNe negates the RAW self verdict, `none` coerced truthy)     8/96
  atk_3   PARTIAL-DOMAIN: gold everywhere except the DOUBLE-abstention identity fallback -> true            4/96
  atk_4   BOUNDARY/observation-order: identityOnly asked BEFORE sameObj (so `oo == oo` becomes false)      24/96
  atk_5   CONTROL-FLOW-EFFECT: dispatch inverted, reflected opinion consulted FIRST (right-priority)       28/96
  atk_6   UNGROUNDED-ORACLE ECHO: ignores all five classifier observations, echoes otherVerdict alone      29/96
  atk_7   OVER-FIX: a sympifiable but WRONG-KIND operand also abstains                                      2/96
  atk_8   DELETES the `identityOnly` branch (the observable refinement.md calls load-bearing)               7/96
  atk_9   richNe abstention branch always true (drops reflected consultation)                               4/96
  atk_10  content compare INVERTED on the deepest branch                                                    6/96
  atk_11  richNe fails to negate on exactly the clause the patch changed                                   12/96
  atk_12  NumberSymbol's REAL order: interpretability probed BEFORE literal identity (numbers.py:3339-3344) 8/96
ctrl_pos POSITIVE CONTROL, structurally different (NO Id.run, NO Option intermediate; boolean algebra + Option.getD) yet 0/96 deviations = extensionally equal to gold.

Command per file, from repo root swe-proof, run 4-at-a-time as background jobs (runver.sh):
  bash scripts/lean_verify.sh <f>.lean
EXIT CODES (results.txt, results2.txt): atk_1..atk_12 = 1 (never 3, never 124 -- no sorry, no timeout, every measurement COMPLETED); ctrl_pos = 0; ctrl_pos_ax = 0.
Each attack uses `unfold problem_spec_*; decide`. On this finite domain `decide` is COMPLETE, and the logs show refutation rather than tactic failure: 'error: Tactic `decide` proved that the proposition ... is FALSE' (present in all 12 logs). So the SPEC rejects them; this is not tactic brittleness.

POSITIVE CONTROL AXIOMS (ctrl_pos_ax.lean = ctrl_pos + `#print axioms correct_richEq/correct_richNe`), exit 0:
  'correct_richEq' depends on axioms: [propext, Classical.choice, Quot.sound]
  'correct_richNe' depends on axioms: [propext, Classical.choice, Quot.sound]
Exactly STANDARD_AXIOMS; no sorryAx. So a CORRECT impl of a different shape does close cleanly -- the spec is not vacuously unsatisfiable, and rejection of the 12 is discriminating power, not over-strength.

RUNNER-PRIMITIVE CROSS-CHECK (swebench_unified.adversary.check_attack, the exact code the runner re-runs), xcheck.txt: atk_1..atk_12 all same_spec=True admissible=True verifies=False verify_completed=True; ctrl_pos same_spec=True admissible=True verifies=True. 12 admissible attacks >= floor of 5.

**PREPATCH REPRODUCED:** yes, BOTH. atk_1's impl region is byte-identical to Solution_prepatch_1.lean's and atk_2's to Solution_prepatch_2.lean's, modulo only the bundle's explanatory `-- Pre-patch behavior:` prose comments (diff of the impl regions shows ONLY those comment lines).

#### Step 2: no candidate => no resolve owed; I ran three anyway
No wrong impl closed with clean axioms, so the mandatory obligation is vacuous. But 'no attack verified' only shows tightness over the MODEL; G-EQ's live surface is whether the model's boundary corresponds to the real callees. I materialized 3 faithful refined patches at base_commit (mkpatch.py, editing ONLY the 8 methods mapping.md binds -- no collateral, no test edits) and ran ALL THREE CONCURRENTLY through the official harness (swebench_unified.harness.run_resolve, sympy__sympy-13091). All three: `git apply --check` in wt_base @ d1320814ed -> rc=0 APPLIES CLEAN.

P1 = patch_P1.diff (89 lines) -- the faithful refinement of the ONLY impl that verifies (gold/ctrl_pos): op #3 abstain (`except SympifyError: return NotImplemented`) at basic.py + 3 numbers.py sites, and op #7 (`return not self == other`) at basic.py + 4 numbers.py sites. Deliberately OMITS every collateral gold edit (`_has_matcher`, exprtools, geometry, optics, vector, polys x11, rootoftools, ndim_array, enumerative, and all 16 `__lt__`/`__le__`/`__gt__`/`__ge__` NumberSymbol-delegation flips).
  run_resolve -> {"resolved": true, "completed": true, "note": "resolved on attempt 2/3"}  [res_P1.json]
  => THE DECISIVE POSITIVE LEG. Because problem_spec_* pins `result = richEqRef` EXACTLY (total equality, no existential slack, no precondition), gold's extensional class is the only verifying class -- and its faithful patch RESOLVES. verify => correct holds on the one class the spec admits. It also proves the modeled scope is SUFFICIENT: gold's other ~30 edits are consistency collateral, not gated behavior, so mapping.md's abstraction boundary is honest and not narrower than the fix it claims to capture.

P3 = patch_P3.diff (53 lines) -- the faithful refinement of atk_1 (PREPATCH BUG #1): op #7 APPLIED but op #3 NOT (uninterpretable operand still gets a definite False, never abstains).
  run_resolve -> {"resolved": false, "completed": true, "note": "patch did not resolve in 3 attempts (consistent -- not flaky)"}  [res_P3.json]
  => CORRECT DIRECTION and the sharpest available agreement check: atk_1 is a wrong impl, the spec REJECTS it (exit 1, decide-refuted), AND its faithful patch does NOT resolve. Spec verdict and oracle verdict AGREE. Had the spec admitted atk_1 this would have been the BROKEN finding.

P2 = patch_P2.diff (147 lines) -- the faithful refinement of atk_8, the impl with the `identityOnly` branch DELETED: P1 plus Infinity/NegativeInfinity/NaN.`__eq__` rewritten from bare identity tests into classify-then-compare (so they abstain on an uninterpretable operand). run_resolve -> {"resolved": true, "completed": true, "note": "resolved on attempt 2/3"}  [res_P2.json] => I checked this one hard because it is the only asymmetry, and it is NOT a break. It is the spec being STRICTER than the F2P tests, which is the SAFE direction (verify => correct is preserved; only correct => verify would fail, and G-EQ does not require that).

Confirmed BEHAVIOURALLY that P2 genuinely diverges from gold (p2diff.py, run in the sympy-1.1.2.dev image against each tree): with test_basic.py's `Bar`, GOLD gives `oo == Bar()` -> False, `-oo == Bar()` -> False, `nan == Bar()` -> False, `oo != Bar()` -> True; P2 gives True/True/True/False. So atk_8 is a REAL behavior change that the spec correctly refutes; the hidden tests simply never exercise an `oo`-vs-reflected-True operand (test_numbers.py's Bar returns a definite False for oo/-oo/zoo/nan, measured identical in both trees), so the oracle is blind where the spec is not. A spec tighter than the tests is not a verify=>correct counterexample.

#### STEP 3: refinement.md LEG AUDIT
8 legs, tags counted mechanically: 7x R + 1x I. ZERO kind-3 (no changed-inexpressible op), zero A-consumed, zero A-reference -- consistent with an EMPTY axioms region (the region carries only prose; grep for ^axiom/opaque/unsafe/extern/@[implemented_by in Solution.lean -> NONE; meta.json axioms=[] and deep_model_references=[]). So there is no axiom-soundness surface to attack, G-AX correctly SKIPS, and no dead axiom is shipped. The changed ops (#3 abstain, #6 operator resolution, #7 operator-level negation) are modeled DEEPLY as total functions over the observables and are correctly NOT axiomatized (SPEC_GUIDE §3).

Leg-by-leg correspondence re-derived against the real code, base @ d1320814ed and post-patch in wt_gold: #1 sameObj -> some true        <-> `if self is other: return True` basic.py:303-304 CONFIRMED #2 identityOnly -> some false  <-> Infinity/NegativeInfinity/NaN `return other is S.<singleton>` numbers.py:2833/3054/3219 CONFIRMED (untouched by patch.diff, correctly ABOVE the changed clause) #3 !interpretable -> none      <-> `except SympifyError: return NotImplemented` (was `return False    # sympy != other`) basic.py:315-317 + numbers.py 1258/1719/3341 CONFIRMED -- the fix #4 !sameKind -> some false     <-> `if type(self) != type(other): return False` basic.py:319-320 CONFIRMED #5 contentEq                   <-> `self._hashable_content() == other._hashable_content()` basic.py:321 CONFIRMED #6 resolveEq                   <-> CPython `==` resolution (left method -> reflected -> `is`).

Not taken on the datamodel doc's word: probe P3 shows the reflected consultation is genuinely what the hidden tests gate. #7 richNe via the resolved operator <-> `not self == other` (was `not self.__eq__(other)`) basic.py:332 CONFIRMED #8 `!eqResult`                 <-> `not (self == other)` -- tagged I, correct.

I INDEPENDENTLY RE-DERIVED refinement.md's central measured claim rather than trusting it. Its `identityOnly` criterion ('body minus docstring is a single `return <second parameter> is <expr>`') applied by my own AST walker over the WHOLE post-patch tree (wt_gold): 87 `__eq__` definitions found, criterion selects EXACTLY 3 -- Infinity numbers.py:2833, NegativeInfinity 3054, NaN 3219. That reproduces refinement.md's counts and line numbers exactly, so the observable is a mechanical function of type(L), not an enumeration fitted to the answer. Also AST-confirmed that ComplexInfinity (`zoo`) defines NEITHER `__eq__` nor `__ne__` (methods: `__new__`, `_latex`, `__abs__`, floor, ceiling, `__neg__`, `_eval_power`, `_sage_`), so it resolves to Basic.`__eq__` -- exactly as mapping.md claims, which is what puts `zoo == Bar()` on the other side of the documented collision.

THE ONE GENUINE SUBTLETY I CHASED AND CLEARED (atk_12). mapping.md binds richEq to Basic.`__eq__` AND to NumberSymbol.`__eq__`, but post-patch NumberSymbol.`__eq__` (numbers.py:3339-3344) sympifies BEFORE its `if self is other` check -- the OPPOSITE observation order from Basic.`__eq__` (identity first). If that cell were reachable, one modeled function would be covering two inequivalent real orderings and the collapse would be unfaithful. It is not reachable: `sameObj` means `self is other`, so `other` IS a sympy object, and `_sympify` of a sympy object never raises; hence sameObj => interpretable and the cell (sameObj=True, interpretable=False) is EMPTY.

Verified MECHANICALLY (all 8 of atk_12's deviations lie inside that cell, 0 outside) and EMPIRICALLY inside the sympy-1.1.2.dev image (reach.py, run against wt_gold/wt_base/wt_P1/wt_P2/wt_P3): 0/26 sympy objects -- Basic, Integer, Float, Rational, Symbol, unevaluated Pow(x,1), oo, -oo, zoo, nan, pi, E, GoldenRatio, EulerGamma, Catalan, S.One/Zero/Half/NegativeOne, sqrt(2), Add, Mul -- make `_sympify` raise, while the CONTROL `_sympify(Foo()/Bar()/object())` all DO raise (so `interpretable` is a live observable, not vacuously true). The two orderings therefore coincide on every reachable input and the single-function collapse is faithful. Note this makes atk_12 the weakest of the twelve as a repo-behavior counterexample -- the spec still refutes it, and the other eleven deviate on reachable inputs, so the floor does not lean on it.

I also re-ran refinement.md's own well-definedness style measurement myself with an independent replica (reach.py, 294 ordered pairs over 14 sympy left operands x 21 right operands incl. native scalars, bool, Foo, Bar, str, list, None, unevaluated Pow): wt_gold 0 == divergences / 0 != divergences; wt_P1 0/0 (P1 reproduces gold's modeled behavior exactly); wt_base 11/11 and wt_P3 11/11 (both carry the bug -- and P3's 11 are the SAME 11, confirming P3 is a faithful prepatch-bug-#1 refinement). A methodology note in the interest of not overclaiming: my FIRST divergence run reported 22 for the gold tree; that was my own harness bug (the container's /testbed sympy shadowed the mounted worktree without PYTHONPATH), and with PYTHONPATH set the gold tree measures 0/0. I report the corrected numbers.

### Why the spec resists
problem_spec_richEq/richNe pin `result = richEqRef/richNeRef` EXACTLY over a 96-point finite domain -- total equality, no existential slack, no precondition to hide behind. Any impl differing on even ONE tuple is refuted by `decide`. The observable-collapse to five booleans + Option Bool is the only place a weakness could hide, and that is precisely what probes P1/P2/P3, the independent 87-class criterion re-derivation, and the reachability measurement test; all came out on the spec's side.

### LIMITS (stated so this is not read as more than it is)
(a) The model is a 96-point abstraction and cannot speak to CPython's subclass-priority rule for a right operand whose type subclasses the left's; mapping.md declares that out of scope, and the F2P operands (Foo/Bar) are not subclasses, so the modeled scope does cover the gated behavior. (b) The 16 `__lt__`/`__le__`/`__gt__`/`__ge__` NumberSymbol-delegation flips in gold are not modeled at all; probe P1 proves they are not needed to resolve, so this is an honest boundary rather than an unmodeled gate. (c) The spec is strictly TIGHTER than the F2P tests on the identityOnly axis (probe P2 resolves although the spec rejects atk_8); that direction cannot produce a verify-but-incorrect artifact, so it is not a G-EQ defect, but a future G-PANEL soundness-lane author should know a 'correct' rival that drops identityOnly will be rejected by design. (d) Everything asserted above is a COMPLETED measurement: no exit 124, no exit 3, and all three resolve runs returned completed=true.

**ARTIFACTS:** atk_1..atk_12.lean + .log, ctrl_pos.lean/.log, ctrl_pos_ax.lean/.log, results.txt, results2.txt, xcheck.txt, gen.py, mkpatch.py, reach.py, p2diff.py, patch_P1.diff, patch_P2.diff, patch_P3.diff, res_P1.json, res_P2.json, res_P3.json, reach_wt_{gold,base,P1,P2,P3}.txt, worktrees wt_base/wt_gold/wt_P1/wt_P2/wt_P3 @ d1320814ed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `ctrl_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closed its proof, so no impl was owed a faithful-patch resolve run. 12 admissible attacks, ALL REFUTED (exit 1) by `decide`, which is a COMPLETE decision procedure on this 96-point Bool/Option Bool domain -- Lean's message is 'Tactic `decide` proved that the proposition ... is FALSE', i.e. the verifier refuted each attack rather than merely failing to close it. Step 2's obligation is therefore vacuous, and I ran three resolve probes anyway on the model<->patch correspondence question (results in notes).
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_pos.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,24 +116,17 @@
 -- impl-start
 def implementation_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let selfVerdict : Option Bool :=
-    if sameObj then some true
-    else if identityOnly then some false
-    else if !interpretable then none
-    else if !sameKind then some false
-    else some contentEq
-  match selfVerdict with
-  | some b => return b
-  | none =>
-    match otherVerdict with
-    | some b => return b
-    | none => return false
+  if sameObj then true
+  else if identityOnly then false
+  else if interpretable then (if sameKind then contentEq else false)
+  else (otherVerdict.getD false)
 
 def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
     (otherVerdict : Option Bool) : Bool := Id.run do
-  let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
-    contentEq otherVerdict
-  return !eqResult
+  if sameObj then false
+  else if identityOnly then true
+  else if interpretable then (if sameKind then !contentEq else true)
+  else !(otherVerdict.getD false)
 -- impl-end
 
 -- proof-start
@@ -144,11 +137,8 @@
           otherVerdict
         (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richEq
+  decide
 
 theorem correct_richNe :
     ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
@@ -157,10 +147,6 @@
           otherVerdict
         (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
           otherVerdict) := by
-  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
-  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
-    selfEqVerdict
-  simp only [Id.run]
-  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
-    cases otherVerdict <;> rfl
+  unfold problem_spec_richNe
+  decide
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, sympy__sympy-13091 (lean). VERDICT: SOUND. 12 admissible same-spec wrong impls, ALL REJECTED; no candidate arose, so no attack patch was owed to run_resolve; NO patches submitted because no attack verified. I nevertheless materialized and RAN 3 faithful patches through the official harness to attack the A-leg/correspondence surface, and I re-derived refinement.md's central measured claim from scratch.

#### STEP 1: 12 DISTINCT WRONG IMPLS (all same_spec, all admissible)
Built by gen.py, copying Solution.lean and editing ONLY the impl region + the two tactic blocks. Axioms/pure/pre/post regions and both correct_* theorem STATEMENTS byte-identical to frozen (verified: `grep -A6 '^theorem correct_richEq' | md5sum` matches frozen for all 13 files). same_spec=True and unsound_evasions=[] (ADMISSIBLE) for every file via swebench_unified.markers.same_spec + variant_scope.unsound_evasions with LeanBackend.language. No banned token (sorry/admit/native_decide) and no new axiom/opaque/extern in ANY attack file (grep -cE over all 13 => 0).

BEFORE verifying, I enumerated the WHOLE finite input space (2^5 x 3 = 96 tuples) in Python against richEqRef/richNeRef to PROVE each attack genuinely deviates, so a rejection is a real refutation and not a tautology:
  atk_1   prepatch bug #1 (op #3 unapplied: uninterpretable operand returns `some false`, never abstains)   4/96 deviations
  atk_2   prepatch bug #2 (op #7 unapplied: richNe negates the RAW self verdict, `none` coerced truthy)     8/96
  atk_3   PARTIAL-DOMAIN: gold everywhere except the DOUBLE-abstention identity fallback -> true            4/96
  atk_4   BOUNDARY/observation-order: identityOnly asked BEFORE sameObj (so `oo == oo` becomes false)      24/96
  atk_5   CONTROL-FLOW-EFFECT: dispatch inverted, reflected opinion consulted FIRST (right-priority)       28/96
  atk_6   UNGROUNDED-ORACLE ECHO: ignores all five classifier observations, echoes otherVerdict alone      29/96
  atk_7   OVER-FIX: a sympifiable but WRONG-KIND operand also abstains                                      2/96
  atk_8   DELETES the `identityOnly` branch (the observable refinement.md calls load-bearing)               7/96
  atk_9   richNe abstention branch always true (drops reflected consultation)                               4/96
  atk_10  content compare INVERTED on the deepest branch                                                    6/96
  atk_11  richNe fails to negate on exactly the clause the patch changed                                   12/96
  atk_12  NumberSymbol's REAL order: interpretability probed BEFORE literal identity (numbers.py:3339-3344) 8/96
ctrl_pos POSITIVE CONTROL, structurally different (NO Id.run, NO Option intermediate; boolean algebra + Option.getD) yet 0/96 deviations = extensionally equal to gold.

Command per file, from repo root swe-proof, run 4-at-a-time as background jobs (runver.sh):
  bash scripts/lean_verify.sh <f>.lean
EXIT CODES (results.txt, results2.txt): atk_1..atk_12 = 1 (never 3, never 124 -- no sorry, no timeout, every measurement COMPLETED); ctrl_pos = 0; ctrl_pos_ax = 0.
Each attack uses `unfold problem_spec_*; decide`. On this finite domain `decide` is COMPLETE, and the logs show refutation rather than tactic failure: 'error: Tactic `decide` proved that the proposition ... is FALSE' (present in all 12 logs). So the SPEC rejects them; this is not tactic brittleness.

POSITIVE CONTROL AXIOMS (ctrl_pos_ax.lean = ctrl_pos + `#print axioms correct_richEq/correct_richNe`), exit 0:
  'correct_richEq' depends on axioms: [propext, Classical.choice, Quot.sound]
  'correct_richNe' depends on axioms: [propext, Classical.choice, Quot.sound]
Exactly STANDARD_AXIOMS; no sorryAx. So a CORRECT impl of a different shape does close cleanly -- the spec is not vacuously unsatisfiable, and rejection of the 12 is discriminating power, not over-strength.

RUNNER-PRIMITIVE CROSS-CHECK (swebench_unified.adversary.check_attack, the exact code the runner re-runs), xcheck.txt: atk_1..atk_12 all same_spec=True admissible=True verifies=False verify_completed=True; ctrl_pos same_spec=True admissible=True verifies=True. 12 admissible attacks >= floor of 5.

**PREPATCH REPRODUCED:** yes, BOTH. atk_1's impl region is byte-identical to Solution_prepatch_1.lean's and atk_2's to Solution_prepatch_2.lean's, modulo only the bundle's explanatory `-- Pre-patch behavior:` prose comments (diff of the impl regions shows ONLY those comment lines).

#### Step 2: no candidate => no resolve owed; I ran three anyway
No wrong impl closed with clean axioms, so the mandatory obligation is vacuous. But 'no attack verified' only shows tightness over the MODEL; G-EQ's live surface is whether the model's boundary corresponds to the real callees. I materialized 3 faithful refined patches at base_commit (mkpatch.py, editing ONLY the 8 methods mapping.md binds -- no collateral, no test edits) and ran ALL THREE CONCURRENTLY through the official harness (swebench_unified.harness.run_resolve, sympy__sympy-13091). All three: `git apply --check` in wt_base @ d1320814ed -> rc=0 APPLIES CLEAN.

P1 = patch_P1.diff (89 lines) -- the faithful refinement of the ONLY impl that verifies (gold/ctrl_pos): op #3 abstain (`except SympifyError: return NotImplemented`) at basic.py + 3 numbers.py sites, and op #7 (`return not self == other`) at basic.py + 4 numbers.py sites. Deliberately OMITS every collateral gold edit (`_has_matcher`, exprtools, geometry, optics, vector, polys x11, rootoftools, ndim_array, enumerative, and all 16 `__lt__`/`__le__`/`__gt__`/`__ge__` NumberSymbol-delegation flips).
  run_resolve -> {"resolved": true, "completed": true, "note": "resolved on attempt 2/3"}  [res_P1.json]
  => THE DECISIVE POSITIVE LEG. Because problem_spec_* pins `result = richEqRef` EXACTLY (total equality, no existential slack, no precondition), gold's extensional class is the only verifying class -- and its faithful patch RESOLVES. verify => correct holds on the one class the spec admits. It also proves the modeled scope is SUFFICIENT: gold's other ~30 edits are consistency collateral, not gated behavior, so mapping.md's abstraction boundary is honest and not narrower than the fix it claims to capture.

P3 = patch_P3.diff (53 lines) -- the faithful refinement of atk_1 (PREPATCH BUG #1): op #7 APPLIED but op #3 NOT (uninterpretable operand still gets a definite False, never abstains).
  run_resolve -> {"resolved": false, "completed": true, "note": "patch did not resolve in 3 attempts (consistent -- not flaky)"}  [res_P3.json]
  => CORRECT DIRECTION and the sharpest available agreement check: atk_1 is a wrong impl, the spec REJECTS it (exit 1, decide-refuted), AND its faithful patch does NOT resolve. Spec verdict and oracle verdict AGREE. Had the spec admitted atk_1 this would have been the BROKEN finding.

P2 = patch_P2.diff (147 lines) -- the faithful refinement of atk_8, the impl with the `identityOnly` branch DELETED: P1 plus Infinity/NegativeInfinity/NaN.`__eq__` rewritten from bare identity tests into classify-then-compare (so they abstain on an uninterpretable operand). run_resolve -> {"resolved": true, "completed": true, "note": "resolved on attempt 2/3"}  [res_P2.json] => I checked this one hard because it is the only asymmetry, and it is NOT a break. It is the spec being STRICTER than the F2P tests, which is the SAFE direction (verify => correct is preserved; only correct => verify would fail, and G-EQ does not require that).

Confirmed BEHAVIOURALLY that P2 genuinely diverges from gold (p2diff.py, run in the sympy-1.1.2.dev image against each tree): with test_basic.py's `Bar`, GOLD gives `oo == Bar()` -> False, `-oo == Bar()` -> False, `nan == Bar()` -> False, `oo != Bar()` -> True; P2 gives True/True/True/False. So atk_8 is a REAL behavior change that the spec correctly refutes; the hidden tests simply never exercise an `oo`-vs-reflected-True operand (test_numbers.py's Bar returns a definite False for oo/-oo/zoo/nan, measured identical in both trees), so the oracle is blind where the spec is not. A spec tighter than the tests is not a verify=>correct counterexample.

#### STEP 3: refinement.md LEG AUDIT
8 legs, tags counted mechanically: 7x R + 1x I. ZERO kind-3 (no changed-inexpressible op), zero A-consumed, zero A-reference -- consistent with an EMPTY axioms region (the region carries only prose; grep for ^axiom/opaque/unsafe/extern/@[implemented_by in Solution.lean -> NONE; meta.json axioms=[] and deep_model_references=[]). So there is no axiom-soundness surface to attack, G-AX correctly SKIPS, and no dead axiom is shipped. The changed ops (#3 abstain, #6 operator resolution, #7 operator-level negation) are modeled DEEPLY as total functions over the observables and are correctly NOT axiomatized (SPEC_GUIDE §3).

Leg-by-leg correspondence re-derived against the real code, base @ d1320814ed and post-patch in wt_gold: #1 sameObj -> some true        <-> `if self is other: return True` basic.py:303-304 CONFIRMED #2 identityOnly -> some false  <-> Infinity/NegativeInfinity/NaN `return other is S.<singleton>` numbers.py:2833/3054/3219 CONFIRMED (untouched by patch.diff, correctly ABOVE the changed clause) #3 !interpretable -> none      <-> `except SympifyError: return NotImplemented` (was `return False    # sympy != other`) basic.py:315-317 + numbers.py 1258/1719/3341 CONFIRMED -- the fix #4 !sameKind -> some false     <-> `if type(self) != type(other): return False` basic.py:319-320 CONFIRMED #5 contentEq                   <-> `self._hashable_content() == other._hashable_content()` basic.py:321 CONFIRMED #6 resolveEq                   <-> CPython `==` resolution (left method -> reflected -> `is`).

Not taken on the datamodel doc's word: probe P3 shows the reflected consultation is genuinely what the hidden tests gate. #7 richNe via the resolved operator <-> `not self == other` (was `not self.__eq__(other)`) basic.py:332 CONFIRMED #8 `!eqResult`                 <-> `not (self == other)` -- tagged I, correct.

I INDEPENDENTLY RE-DERIVED refinement.md's central measured claim rather than trusting it. Its `identityOnly` criterion ('body minus docstring is a single `return <second parameter> is <expr>`') applied by my own AST walker over the WHOLE post-patch tree (wt_gold): 87 `__eq__` definitions found, criterion selects EXACTLY 3 -- Infinity numbers.py:2833, NegativeInfinity 3054, NaN 3219. That reproduces refinement.md's counts and line numbers exactly, so the observable is a mechanical function of type(L), not an enumeration fitted to the answer. Also AST-confirmed that ComplexInfinity (`zoo`) defines NEITHER `__eq__` nor `__ne__` (methods: `__new__`, `_latex`, `__abs__`, floor, ceiling, `__neg__`, `_eval_power`, `_sage_`), so it resolves to Basic.`__eq__` -- exactly as mapping.md claims, which is what puts `zoo == Bar()` on the other side of the documented collision.

THE ONE GENUINE SUBTLETY I CHASED AND CLEARED (atk_12). mapping.md binds richEq to Basic.`__eq__` AND to NumberSymbol.`__eq__`, but post-patch NumberSymbol.`__eq__` (numbers.py:3339-3344) sympifies BEFORE its `if self is other` check -- the OPPOSITE observation order from Basic.`__eq__` (identity first). If that cell were reachable, one modeled function would be covering two inequivalent real orderings and the collapse would be unfaithful. It is not reachable: `sameObj` means `self is other`, so `other` IS a sympy object, and `_sympify` of a sympy object never raises; hence sameObj => interpretable and the cell (sameObj=True, interpretable=False) is EMPTY.

Verified MECHANICALLY (all 8 of atk_12's deviations lie inside that cell, 0 outside) and EMPIRICALLY inside the sympy-1.1.2.dev image (reach.py, run against wt_gold/wt_base/wt_P1/wt_P2/wt_P3): 0/26 sympy objects -- Basic, Integer, Float, Rational, Symbol, unevaluated Pow(x,1), oo, -oo, zoo, nan, pi, E, GoldenRatio, EulerGamma, Catalan, S.One/Zero/Half/NegativeOne, sqrt(2), Add, Mul -- make `_sympify` raise, while the CONTROL `_sympify(Foo()/Bar()/object())` all DO raise (so `interpretable` is a live observable, not vacuously true). The two orderings therefore coincide on every reachable input and the single-function collapse is faithful. Note this makes atk_12 the weakest of the twelve as a repo-behavior counterexample -- the spec still refutes it, and the other eleven deviate on reachable inputs, so the floor does not lean on it.

I also re-ran refinement.md's own well-definedness style measurement myself with an independent replica (reach.py, 294 ordered pairs over 14 sympy left operands x 21 right operands incl. native scalars, bool, Foo, Bar, str, list, None, unevaluated Pow): wt_gold 0 == divergences / 0 != divergences; wt_P1 0/0 (P1 reproduces gold's modeled behavior exactly); wt_base 11/11 and wt_P3 11/11 (both carry the bug -- and P3's 11 are the SAME 11, confirming P3 is a faithful prepatch-bug-#1 refinement). A methodology note in the interest of not overclaiming: my FIRST divergence run reported 22 for the gold tree; that was my own harness bug (the container's /testbed sympy shadowed the mounted worktree without PYTHONPATH), and with PYTHONPATH set the gold tree measures 0/0. I report the corrected numbers.

### Why the spec resists
problem_spec_richEq/richNe pin `result = richEqRef/richNeRef` EXACTLY over a 96-point finite domain -- total equality, no existential slack, no precondition to hide behind. Any impl differing on even ONE tuple is refuted by `decide`. The observable-collapse to five booleans + Option Bool is the only place a weakness could hide, and that is precisely what probes P1/P2/P3, the independent 87-class criterion re-derivation, and the reachability measurement test; all came out on the spec's side.

### LIMITS (stated so this is not read as more than it is)
(a) The model is a 96-point abstraction and cannot speak to CPython's subclass-priority rule for a right operand whose type subclasses the left's; mapping.md declares that out of scope, and the F2P operands (Foo/Bar) are not subclasses, so the modeled scope does cover the gated behavior. (b) The 16 `__lt__`/`__le__`/`__gt__`/`__ge__` NumberSymbol-delegation flips in gold are not modeled at all; probe P1 proves they are not needed to resolve, so this is an honest boundary rather than an unmodeled gate. (c) The spec is strictly TIGHTER than the F2P tests on the identityOnly axis (probe P2 resolves although the spec rejects atk_8); that direction cannot produce a verify-but-incorrect artifact, so it is not a G-EQ defect, but a future G-PANEL soundness-lane author should know a 'correct' rival that drops identityOnly will be rejected by design. (d) Everything asserted above is a COMPLETED measurement: no exit 124, no exit 3, and all three resolve runs returned completed=true.

**ARTIFACTS:** atk_1..atk_12.lean + .log, ctrl_pos.lean/.log, ctrl_pos_ax.lean/.log, results.txt, results2.txt, xcheck.txt, gen.py, mkpatch.py, reach.py, p2diff.py, patch_P1.diff, patch_P2.diff, patch_P3.diff, res_P1.json, res_P2.json, res_P3.json, reach_wt_{gold,base,P1,P2,P3}.txt, worktrees wt_base/wt_gold/wt_P1/wt_P2/wt_P3 @ d1320814ed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK ROLE:** faithfulness-break (is the spec too strong / does the modeled function disagree with the real post-patch callee?). Reference =  at base d1320814eda6549996190618a21eaf212cfd4d1e with patch.diff APPLIED (confirmed via `git apply --check --reverse` -> PATCH_FULLY_APPLIED). Real sympy 1.1.2.dev runs  (py3.8; the repo-root env's py3.10 cannot import `from collections import Mapping`).

**NO DIVERGENCE FOUND.** I wrote an INDEPENDENT transcription of the five-observable model straight from mapping.md (gp2_model.py: operative_pair, identityOnly AST criterion, interpretable/sameKind/contentEq per-arm, otherVerdict) and diffed it against the REAL post-patch `==` and `!=` operators over ~86,000 ordered pairs in five separate sweeps. Every sweep: 0 eq-divergences, 0 ne-divergences, 0 colliding tuples (no tuple carrying two different real results).

(1) Broad structured sweep, 3572 pairs (46 in-scope left operands x 78 rights incl. sympy exprs, unevaluated Pow(x,1), all numeric singletons, native scalars bool/int/float/str/None/list/tuple/dict/complex, and 6 foreign classes covering all three reflected replies True/False/NotImplemented, both sympifiable and not): 0/0, 21 tuples, 0 collisions.

(2) Multi-precision Float pool, 22,120 pairs (15 decimal values x precisions {5,8,10,15,20,25,30,40,53,80}): 0/0, 0 collisions. This is the arm the refinement flags as the subtlest -- I confirmed the raw-mpf vs re-precise split is load-bearing and correctly modeled: Rational(1,10).evalf(15) == Rational(1,10).evalf(30) is really False (raw tuples differ) and the model agrees, while Rational('0.1').evalf(10) == 0.1 is really True via the RE-PRECISING native-float fast path -- the two arms are genuinely non-interchangeable in BOTH directions and mapping.md orders them exactly as numbers.py 1250/1266/1268 does.

(3) Nested unit-power redirection, 493 pairs (Pow(x,1), Pow(Pow(x,1),1), triple-nested, Pow(oo,1)/Pow(nan,1)/Pow(zoo,1)/Pow(pi,1), Pow(x,Float(1.0))): 0/0. The operative_pair loop's `type(a).__eq__ is Basic.__eq__` guard is correct -- the two redirecting branches exist only in Basic.`__eq__`.

(4) Delegation/aliasing adversarial probe: wrappers whose `_sympy_` returns the LHS ITSELF (attempting to break the spec's sameObj-first ordering vs the real methods' sympify-first ordering) and wrappers returning a different same-type object, x3 reflected replies, over 15 targets: 0 divergences. Ordering is safe because if `other is self` then other is necessarily sympifiable, so the two orderings cannot be distinguished.

(5) Randomized fuzz, 60,000 pairs, depth-3 generated expressions with `evaluate` toggled so unevaluated unit powers are really produced, seed 1309102: 0 divergences, 0 collisions, 23 distinct tuples -- independently reproducing the bundle's own 0/0/23 claim.

SPECIAL-VALUE probe: Float.`_new`(mlib.fnan) returns a NaN (not a Float) and finf/fninf give genuine inf/-inf Floats; all tested against the full numeric pool -> 0 divergences, including the ValueError arm of the native-float fast path (float('nan'), float('inf'), 1e400 all handled correctly as False).

identityOnly INDEPENDENTLY REPRODUCED, not taken on trust: I re-ran the AST criterion (body minus docstring is a single `return <2nd param> is <expr>`) over the whole patched tree myself -- 89 `__eq__` definitions found, the criterion selects EXACTLY Infinity (numbers.py:2833), NegativeInfinity (3054), NaN (3219) and nothing else. Confirmed zoo/ComplexInfinity defines no `__eq__` and resolves to Basic.`__eq__`, so it sits on the OTHER side of the documented collision, exactly as mapping.md states. The observable is a pure function of type(L), never inspects R, never consults the answer -- it is not an enumeration of the result.

ONLY candidate counterexample examined and REJECTED as illegitimate: `o = Basic.__new__(Infinity)` yields a non-singleton Infinity where real `o == o` is False (since `other is S.Infinity` fails) while the spec's sameObj-first rule gives True. This is NOT a repo behavior -- it deliberately bypasses the Singleton metaclass to construct an object violating its class invariant (the sibling `object.__new__(Infinity)` attempt died with AttributeError: `_mhash`, confirming such objects are malformed). I verified the singleton is unbreakable by every normal route: Infinity(), sympify('oo'), exp(oo), oo+1, S(2)*oo, and a limit computation ALL return `is oo` True. mapping.md already documents this precise reasoning (the class is a Singleton, so self IS that singleton, hence its value is exactly `other is self`). Not a faithfulness defect.

SPEC-STRENGTH / DIRECTION CHECKS (guarding against condemning a correct spec by comparing to base): the spec models the FIXED behavior -- op #3 abstains (`none` <-> NotImplemented) where base returned `some false`, and richNe negates the RESOLVED operator rather than the raw self-verdict. Both are the patch delta, correctly on the post-patch side. Spec is not vacuous or over-strong: Solution.lean verifies (lean_verify.sh exit 0) with `#print axioms` clean -- correct_richEq, correct_richNe, richEqRef, richNeRef all report 'does not depend on any axioms', so no sorryAx and no fake proof. Both carried prepatch rivals FAIL to verify (exit 1, 4 errors each, unsolved goals on the `interpretable = false` branch -- i.e. rejected precisely on the clause the patch changed), so the postcondition is strong enough to separate fixed from buggy. markers.same_spec(Solution, prepatch_1) and (Solution, prepatch_2) are both True, so the rivals differ only in impl and the spec region is byte-identical -- the rejection is real spec strength, not a spec edit. Both F2P tests (test_equality, test_comparisons_with_unknown_type) pass on the patched worktree.

**Axioms region is legitimately EMPTY:** otherVerdict is arbitrary caller-supplied user code (the Foo/Bar test classes), a free input rather than a repo callee, so there is no unchanged-callee contract to declare and no A-reference to validate; G-AX correctly skips. Dispatch-priority scope (CPython's right-operand-subclass priority) is explicitly declared out of scope in mapping.md and the F2P operands are not subclasses of the symbolic types, so left-first resolution is exact for the modeled scope -- a documented boundary, not a hidden over-strength.

**Conclusion:** the modeled function agrees with the real patched callee on every input I could reach across ~86,000 differential pairs plus five targeted adversarial probes at the arm splits, the redirection, the singleton family, and the special mpf values. I found no diverging input, so I cannot claim the spec is too strong or that it drifts from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE audit of sympy__sympy-13091 (lean), measured by me on the CURRENT bytes (Solution.lean sha256 fdefeb4c0a1b...), judged against the public problem_statement ONLY -- hints_text deliberately excluded from the excuse set.

NO RELAXATION IN THIS BUNDLE, checked rather than assumed: no RELAXED_LEAKAGE.md anywhere under the instance dir (`find -iname '*RELAX*'` = empty), meta.json has no `relaxed_leakage` key (top-level keys: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins), and gates.G-LEAK.status == "pass", not "relaxed". The only 'relax' substrings in the serialized meta are inside PRIOR panel-note prose asserting there is no relaxation -- not a disposition. So this is judged under the ordinary rule; there was no unavoidability argument to re-derive.

SPEC VIEW MEASURED, not assumed: markers.spec_view(Solution.lean, lean backend) -- impl and proof regions elided; what a consumer sees is the module docstring + axioms + pure + post-conditions. same_spec(Solution.lean, prepatch_1) = True and same_spec(..., prepatch_2) = True, and the rendered spec_view bytes are IDENTICAL across all three files (not merely signature-equal), so the discrimination between gold and both prepatch rivals lives entirely in the elided impl, never in the visible view.

**WHY THE VIEW LEAKS NOTHING BEYOND THE STATEMENT.** The problem_statement is already maximally explicit about the gold edit -- title 'Return NotImplemented, not False, upon rich comparison with unknown type'; the reflected-method delegation mechanism; 'If both sides return NotImplemented, the final return value is False, as expected'; and literally 'the line to edit is line 316 in basic.py -- just replace `return False` with `return NotImplemented`'; plus 'The other rich comparison methods ... behave similarly'. Every discriminating clause in the view is a strictly de-identified abstraction of that: three-valued own opinion (definite true / definite false / ABSTENTION = `none`), operator resolution definite -> reflected opinion (`otherVerdict`) -> object identity = false, and the symmetry property. The `!=` clause ('negates the fully resolved `==` ... not merely the value's own equality test') is the abstract postcondition a spec cannot omit and follows from the statement's 'behave similarly' + public CPython semantics; it names no method, file, or sentinel.

What the view adds beyond the statement is about code the patch does NOT touch, so it localizes no edit: (a) the `identityOnly` family ('a kind may decide equality by BARE OBJECT IDENTITY ... outside that property by construction'), which I confirmed against the base commit d1320814 -- numbers.py:2833/3054/3219 are `return other is S.Infinity` / `S.NegativeInfinity` / `S.NaN`, and PatchSet(patch.diff) shows the numbers.py hunks are at 1258/1276/1284/1298/1312/1326/1719/1734/1742/1760/1778/1797/2112/3339/3348 -- none of the three identity-only methods is in the diff; (b) the unit-power operative-pair normalization, which maps to basic.py:307-311 (`isinstance(self, Pow) and self.exp == 1`), also unchanged (the basic.py hunks are @@313, @@329, @@1180 only). Both are modeling-totality observables, not the edit.

**MECHANICAL CROSS-CHECKS I RAN MYSELF.** leakage.screen(Solution.lean, lean tables, patch.diff, problem_statement, test_patch) => passed=True, hard_failures=[], warnings=[]. Re-ran with problem_statement='' (strictest -- no public-statement excuse at all) => still passed=True, empty failures: the view does not lean on the statement to clear the screen. `_NARRATION_RE` over the rendered view => [] (no bug/fix/patched/previously/incorrectly/wrong). Whitespace-normalized containment of ALL patch changed lines in the view => none reproduced. `_lean_spec_view_identifiers`(view) INTERSECT `_patch_changed_symbols`(patch) (= {eval_Eq, getnewargs, nonzero, strict_eq}) => empty, including substring-embedding. No patched-file basename appears in the view.

Hand token scan => ZERO hits for basic.py, numbers.py, exprtools, entity.py, medium.py, dyadic, polyclasses, rootoftools, NotImplemented, sympify, SympifyError, `__eq__`, `__ne__`, `__lt__`, `__ge__`, `__le__`, `__gt__`, hashable, `_hashable_content`, 'return False', 'line 316', 'line 329', sympy, Factors, Term, mpf, NaN, Infinity, `_has_matcher`, lambda, `_strict_eq`, `__nonzero__`, eval_Eq, `__getnewargs__`, '@@', 'diff --git', '+++ '. F2P names (test_equality, test_comparisons_with_unknown_type) absent; `_test_param_ids`(test_patch) INTERSECT view => empty; the only test-patch tokens present are generic English (Class, False, assert, equal, equality, object, order, other, symmetric). leakage.reviewer_directed(view) => [].

I also grepped refinement.md, mapping.md, conformance_check.py, axiom_check.py, verdict.md for reviewer-directed text (panel/attacker/auditor/'you must'/'the honest verdict'/'record as'/'do not submit') => nothing; no file in this bundle addresses me or tries to steer this verdict. mapping.md DOES name basic.py:316 and the NotImplemented fix, but mapping.md is not in the consumer spec view (markers.spec_view projects Solution.lean only), so that is provenance, not leakage.

SOUNDNESS SPOT-CHECKS behind the verdict (so this is not a screen-only pass): lean_verify.sh Solution.lean => exit 0; `#print axioms correct_richEq` / `correct_richNe` => 'does not depend on any axioms' (no sorryAx, no classical leak). lean_verify.sh on both prepatch variants => exit 1, and the failures are exactly the interpretable=false goals (prepatch_1 rfl failures at 154/168, prepatch_2 at 174), i.e. the rivals die on the clause the patch changed, with the spec view held byte-identical. patch.diff == instance.json['patch'] (True), meta.patch_equals_gold True.

TWO RECORD DEFECTS -- neither changes this verdict, both flagged because they are stale-bookkeeping, not leakage:

(1) THE PRIOR G-PANEL-3 PASS IS STALE AND DOES NOT COVER THIS SPEC VIEW. meta.gates['G-PANEL-3'] (pass, 12:56:52) and its verdict.md twin were recorded against sources.Solution.lean = e5f549280e00..., but the current file is fdefeb4c0a1b.... I diffed the two spec views from git (1332b51f5 vs 7a2700d40): the current one ADDS the whole operative-pair paragraph, the two-family/BARE OBJECT IDENTITY paragraph, the 'outside that property by construction' paragraph, four->five observations, and the `identityOnly` parameter across selfEqVerdict/richEqRef/richNeRef/problem_spec_*. That is a substantive prose+signature edit to the consumer-visible region after the retained pass, so the old note's token scan is not a measurement of these bytes. Everything above is re-measured on fdefeb4c. (Related: the old note's claim that only region_hashes.proof was stale and the other four 'match raw region_text exactly' was true of the OLD file, not this one.)

(2) meta.json's top-level region_hashes block is stale WHOLESALE, not just `proof`. markers.region_hashes(current Solution.lean) disagrees with meta on all six entries (axioms 232d81e9 vs 78e23fa6, impl 93f08655 vs 24f25de0, post-conditions 9e7aac1d vs cbeb60a1, pure 7b9099e2 vs 794aac11, proof 7bca7723 vs e80871e1, spec_view b9d18eb7 vs 227794d3). Recomputing on the git-previous revision 1332b51f5 reproduces 5 of the 6 recorded values (proof matches neither revision, so that one entry matches nothing in the bundle's history). Meanwhile gates['G-HYGIENE'] (14:37:03, sources fdefeb4c) recorded the CORRECT current six in its own data -- so the gate ran clean and only the top-level ledger block was never refreshed after the 14:34 spec edit. Worth a regate of the hash-writing step; spec_view/same_spec are computed from the bytes, so the leakage question is untouched.

**CONCLUSION:** no spec-view line discloses the gold edit beyond what the public problem_statement already states outright; the view is strictly more abstract than the statement, clears the mechanical screen even with the statement excuse removed, its extra content concerns provably unchanged code, and the gold/prepatch discrimination is formal (elided impl) rather than narrated. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
