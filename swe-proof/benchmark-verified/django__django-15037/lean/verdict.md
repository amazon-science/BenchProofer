# P2 adversarial audit — django__django-15037

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl verifies, and this is established by PROOF rather than by an exhausted battery. forced.lean closes `spec_forces_the_gold_impl` (lean_verify.sh exit 0; `#print axioms` = [propext, Quot.sound], clean): for ANY candidate f : Bool -> Bool -> String -> String -> String -> Option String -> RelationField, if f satisfies problem_spec_relationField on every input (exactly what a same-spec attack's correct_relationField must prove) then f is POINTWISE EQUAL to implementation_relationField. Supporting lemmas in uniq.lean (exit 0, clean axioms): spec_is_functional (at most one satisfying RelationField per input) and spec_is_total (at least one). So the spec is a total single-valued functional exact-match spec admitting exactly one impl up to pointwise equality; verify => impl = gold, and no wrong impl can have a closing proof by ANY tactic. Prepatch bug reproduced as atk_1 (toField never set, matching Solution_prepatch.lean): at isUnique=false, isPrimaryKey=false, refPkColumn=some "id", refDbColumn="" the spec requires toField=some "" but the impl yields none -> lean_verify exit 1 (error: unsolved goals) = G-DIFF signal, and its faithful patch atk_1.diff was RUN through the official harness: resolved=false, completed=true, patch_successfully_applied=true, FAIL_TO_PASS 0/1, PASS_TO_PASS 14/14 -- confirming the oracle refutes the prepatch behaviour while gold.diff resolves.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -59,14 +59,11 @@
     (refDbColumn refDbTable tableName : String)
     (refPkColumn : Option String) : RelationField := Id.run do
   let mut relType : String := "ForeignKey"
-  let mut toField : Option String := none
+  let toField : Option String := none
   if isUnique || isPrimaryKey then
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
@@ -81,14 +78,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
   else
     relType := "ForeignKey"
     match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+    | some _ => toField := some refDbColumn
     | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,9 +64,7 @@
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
+    toField := some refDbColumn
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
@@ -81,14 +79,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -60,7 +60,7 @@
     (refPkColumn : Option String) : RelationField := Id.run do
   let mut relType : String := "ForeignKey"
   let mut toField : Option String := none
-  if isUnique || isPrimaryKey then
+  if isUnique then
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -67,8 +67,7 @@
     match refPkColumn with
     | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
     | none => pure ()
-  let relTo : String :=
-    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
+  let relTo : String := dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
 -- impl-end
 
@@ -81,14 +80,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
   else
     relType := "ForeignKey"
     match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+    | some pk => if pk ≠ refDbColumn then toField := some pk
     | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -60,7 +60,7 @@
     (refPkColumn : Option String) : RelationField := Id.run do
   let mut relType : String := "ForeignKey"
   let mut toField : Option String := none
-  if isUnique || isPrimaryKey then
+  if isUnique && isPrimaryKey then
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
   else
     relType := "ForeignKey"
     match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+    | some pk => if pk ≠ refDbColumn ∧ refDbColumn ≠ "" then toField := some refDbColumn
     | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
   else
     relType := "ForeignKey"
     match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+    | some pk => if pk.length ≠ refDbColumn.length then toField := some refDbColumn
     | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -60,13 +60,13 @@
     (refPkColumn : Option String) : RelationField := Id.run do
   let mut relType : String := "ForeignKey"
   let mut toField : Option String := none
+  match refPkColumn with
+  | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+  | none => pure ()
   if isUnique || isPrimaryKey then
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,9 +64,8 @@
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
+    if refDbTable = "inspectdb_peoplemoredata" ∧ refDbColumn = "people_unique_id" then
+      toField := some refDbColumn
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
@@ -81,14 +80,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -65,7 +65,7 @@
   else
     relType := "ForeignKey"
     match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+    | some pk => if pk ≠ refDbColumn ∧ pk ≠ "" then toField := some refDbColumn
     | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -64,9 +64,10 @@
     relType := "OneToOneField"
   else
     relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
+    if refDbTable ≠ tableName then
+      match refPkColumn with
+      | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
+      | none => pure ()
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
@@ -81,14 +82,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
     relType := "ForeignKey"
     match refPkColumn with
     | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
+    | none => toField := some refDbColumn
   let relTo : String :=
     if refDbTable = tableName then "self" else dbTableToModelName refDbTable
   return { relType := relType, relTo := relTo, toField := toField }
@@ -81,14 +81,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -67,8 +67,7 @@
     match refPkColumn with
     | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
     | none => pure ()
-  let relTo : String :=
-    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
+  let relTo : String := dbTableToModelName (if refDbTable = tableName then "self" else refDbTable)
   return { relType := relType, relTo := relTo, toField := toField }
 -- impl-end
 
@@ -81,14 +80,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -58,18 +58,13 @@
     (isUnique isPrimaryKey : Bool)
     (refDbColumn refDbTable tableName : String)
     (refPkColumn : Option String) : RelationField := Id.run do
-  let mut relType : String := "ForeignKey"
-  let mut toField : Option String := none
-  if isUnique || isPrimaryKey then
-    relType := "OneToOneField"
-  else
-    relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
-  let relTo : String :=
-    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
-  return { relType := relType, relTo := relTo, toField := toField }
+  let oneToOne : Bool := isUnique || isPrimaryKey
+  let tf : Option String :=
+    if oneToOne then none
+    else refPkColumn.bind (fun pk => if pk ≠ refDbColumn then some refDbColumn else none)
+  return { relType := if oneToOne then "OneToOneField" else "ForeignKey",
+           relTo := if refDbTable = tableName then "self" else dbTableToModelName refDbTable,
+           toField := tf }
 -- impl-end
 
 -- proof-start
@@ -81,14 +76,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Scratch: (only path used; base_commit worktree created at ./wt from the upstream repository @ dab48b7482295956973879d15bfd4d3bb0718772, removed after use). All 15 attacks + ctrl.lean confirmed same_spec=True via swebench_unified.markers.same_spec AND admissible via variant_scope.unsound_evasions (impl+proof regions only; axioms/pure/pre/post byte-identical). Verified concurrently in background batches of <=4 (schedule only; every attack fully verified).

**COMMANDS.** Per file: `bash scripts/lean_verify.sh <f>.lean`. Runner-parity recheck: adversary.check_attack('lean','django__django-15037',<path>) on all 16 -> 15x {same_spec=True, admissible=True, verifies=False, verify_completed=True, 'verification failed'}, ctrl {verifies=True,'verified'}.

### RESULTS (exit code / axioms).
- ctrl.lean EXIT=0 (positive control; structurally different but correct: Option.bind + record literal instead of the mut/do control flow). ctrl_ax.lean `#print axioms correct_relationField` -> [propext, Quot.sound] CLEAN.
- atk_1..atk_15 ALL EXIT=1, every one failing with `error: unsolved goals` (semantic rejection, not a syntax/elaboration accident -- classified per-log).
Critically, every attack carries the SAME generic strong tactic script that closes ctrl.lean (cases on all three scrutinees, then first | refine <rfl,rfl,rfl> | simp_all[Bool.or_eq_true,ne_eq,String.ext_iff] | constructor<;>simp_all<;>aesop | aesop | simp_all). So the 15 rejections are the SPEC's, not a tactic tuned to the frozen impl's shape.

ATTACK TAXONOMY (all 15 distinct; each has an EXHIBITED divergence witness from gold via witness.py, so none is a gold echo whose rejection would indicate tactic weakness): atk_1 prepatch (toField never set); atk_2 drops the pk!=column guard; atk_3 toField unconditional in the FK branch; atk_4 kind ignores primary_key; atk_5 drops the self-reference case (A-reference leg: routes self through the callee); atk_6 records the referenced table's pk column instead of the referenced column; atk_7 AND instead of OR; atk_8 PARTIAL-DOMAIN (refuses refDbColumn=""); atk_9 BOUNDARY (compares len(pk)!=len(col) -- needed a widened same-length-distinct-names domain to exhibit its witness: refDbColumn='id', refPkColumn='ab'); atk_10 CONTROL-FLOW-EFFECT (pk lookup hoisted out of the else, so toField leaks into the OneToOne case); atk_11 UNGROUNDED-ORACLE ECHO (hardcodes the F2P fixture's 'inspectdb_peoplemoredata'/'people_unique_id' and is prepatch elsewhere -- would pass every shipped test, so only the spec can reject it); atk_12 PARTIAL-DOMAIN on the mapping.md truthiness leg (also refuses an empty pk name); atk_13 PARTIAL-DOMAIN (a self-FK never records to_field); atk_14 INVERTED FALSY GUARD (an ABSENT pk records to_field); atk_15 A-LEG/OPACITY PROBE (routes the self case THROUGH dbTableToModelName -- sound only if the callee fixes "self", which real table2model('self')='Self' does not).

**PATCHES.** Faithful refined patch materialized for ALL 15 attacks (not only for verifying ones -- defensive, so a runner re-run that flipped any attack to verifying still grades rather than recording 'no submitted patch'). Generated mechanically by textual substitution of the real `if is_relation:` block in django/core/management/commands/inspectdb.py, so each embeds exactly its Lean impl. GENERATOR VALIDATED: the same generator's gold.diff hunk body is byte-identical to the bundle's patch.diff. Every diff checked with `git apply --check` in the base_commit worktree -> all 16 APPLY, and each patched module passes py_compile (so no attack is refuted merely by breaking the module).

### RESOLVE RUNS EXECUTED (official harness, swebench_unified.harness.run_resolve).
- gold.diff -> resolved=TRUE, completed=true (on attempt 2/3, flagged flaky).
- atk_1.diff (prepatch) -> resolved=FALSE, completed=true, patch_successfully_applied=TRUE, FAIL_TO_PASS 0/1, PASS_TO_PASS 14/14.
This pair proves the oracle DISCRIMINATES on this instance (it certifies gold and refutes a faithful wrong refinement), so 'no attack broke the spec' is not masking a dead oracle -- cf. `_oracle_cannot_refute_here`. No resolve was protocol-MANDATORY here because zero attacks had a closing proof; the resolve legs were run to validate the oracle and the patch payload.
HOST NOTE (not a spec fact): my first three resolves, launched concurrently, ALL failed identically including gold ('Cleaning cached images... Removed 2 images', then 'Error building image: Read timed out (read timeout=60)'). Concurrent resolves race on the shared docker image cache and reap each other's images; re-run SERIALLY with retries=2, gold resolved. Recorded here so a later reader does not read that load artifact as a spec verdict.

REFINEMENT.MD AUDIT (A legs; R/I pre-cleared by G-CONF = pass, 120007 cases, 0 disagreements). All 6 rows tagged R/I/A-reference; ZERO kind-3 (changed-inexpressible) rows -- claim confirmed. Row 5 is the only A row (A-reference): `table2model` -> `opaque dbTableToModelName`.

Verified: (a) `grep -E '^\s*axiom\s'` over Solution.lean returns NOTHING, so the 'No A-consumed rows' claim is literally true and STANDARD_AXIOMS is the whole allowance; (b) the opaque appears in the IDENTICAL expression `if refDbTable = tableName then "self" else dbTableToModelName refDbTable` in BOTH the post-conditions and the impl region, so only reflexivity on it is ever needed; (c) OPACITY-INDEPENDENCE PROBED MECHANICALLY -- I replaced the opaque with two arbitrary concrete functions (ax_probe.lean: s.push '!'; ax_probe2.lean: the CONSTANT function fun _ => "K", which collapses all tables to one model id) and the frozen proof still closes, EXIT=0 for both.

So the proof consumes no property of the callee beyond functionhood, exactly as row 5 claims; the A-reference obligation is discharged by G-AX (recorded pass: determinism + alnum range over boundary + 50k fuzzed names, seed 15037) and correspondence to the real callee at inspectdb.py:43 (`re.sub(r'[^a-zA-Z0-9]','',table_name.title())`) holds. Row 4's callee `get_primary_key_column` is correctly NOT axiomatized -- a DB side-effect whose observable output is lifted to the input refPkColumn, with Python falsiness (None/'') collapsed to `none`; atk_12 and atk_14 attack precisely that truthiness modeling and both are rejected.

**VERDICT:** SOUND. 15 distinct same-spec admissible attacks run, none verifies; positive control verifies with clean axioms; prepatch reproduced and its faithful patch confirmed non-resolving under the official harness while gold resolves. The spec is not merely tight but PROVABLY UNIQUE (spec_forces_the_gold_impl), so verify => correct holds for this bundle and no counterexample exists to be found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl verifies, and this is established by PROOF rather than by an exhausted battery. forced.lean closes `spec_forces_the_gold_impl` (lean_verify.sh exit 0; `#print axioms` = [propext, Quot.sound], clean): for ANY candidate f : Bool -> Bool -> String -> String -> String -> Option String -> RelationField, if f satisfies problem_spec_relationField on every input (exactly what a same-spec attack's correct_relationField must prove) then f is POINTWISE EQUAL to implementation_relationField. Supporting lemmas in uniq.lean (exit 0, clean axioms): spec_is_functional (at most one satisfying RelationField per input) and spec_is_total (at least one). So the spec is a total single-valued functional exact-match spec admitting exactly one impl up to pointwise equality; verify => impl = gold, and no wrong impl can have a closing proof by ANY tactic. Prepatch bug reproduced as atk_1 (toField never set, matching Solution_prepatch.lean): at isUnique=false, isPrimaryKey=false, refPkColumn=some "id", refDbColumn="" the spec requires toField=some "" but the impl yields none -> lean_verify exit 1 (error: unsolved goals) = G-DIFF signal, and its faithful patch atk_1.diff was RUN through the official harness: resolved=false, completed=true, patch_successfully_applied=true, FAIL_TO_PASS 0/1, PASS_TO_PASS 14/14 -- confirming the oracle refutes the prepatch behaviour while gold.diff resolves.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -58,18 +58,13 @@
     (isUnique isPrimaryKey : Bool)
     (refDbColumn refDbTable tableName : String)
     (refPkColumn : Option String) : RelationField := Id.run do
-  let mut relType : String := "ForeignKey"
-  let mut toField : Option String := none
-  if isUnique || isPrimaryKey then
-    relType := "OneToOneField"
-  else
-    relType := "ForeignKey"
-    match refPkColumn with
-    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
-    | none => pure ()
-  let relTo : String :=
-    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
-  return { relType := relType, relTo := relTo, toField := toField }
+  let oneToOne : Bool := isUnique || isPrimaryKey
+  let tf : Option String :=
+    if oneToOne then none
+    else refPkColumn.bind (fun pk => if pk ≠ refDbColumn then some refDbColumn else none)
+  return { relType := if oneToOne then "OneToOneField" else "ForeignKey",
+           relTo := if refDbTable = tableName then "self" else dbTableToModelName refDbTable,
+           toField := tf }
 -- impl-end
 
 -- proof-start
@@ -81,14 +76,11 @@
   intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
   unfold problem_spec_relationField implementation_relationField
   simp only [Id.run, bind, pure]
-  by_cases h : isUnique || isPrimaryKey
-  · simp only [h, if_true, and_self]
-  · cases refPkColumn with
-    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
-    | some pk =>
-      by_cases hk : pk = refDbColumn
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
-        exact ⟨rfl, rfl, rfl⟩
-      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
-        exact ⟨rfl, rfl, rfl⟩
+  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
+    first
+      | (refine ⟨rfl, rfl, rfl⟩)
+      | (simp_all [Bool.or_eq_true, ne_eq, String.ext_iff])
+      | (constructor <;> simp_all <;> aesop)
+      | aesop
+      | simp_all
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Scratch: (only path used; base_commit worktree created at ./wt from the upstream repository @ dab48b7482295956973879d15bfd4d3bb0718772, removed after use). All 15 attacks + ctrl.lean confirmed same_spec=True via swebench_unified.markers.same_spec AND admissible via variant_scope.unsound_evasions (impl+proof regions only; axioms/pure/pre/post byte-identical). Verified concurrently in background batches of <=4 (schedule only; every attack fully verified).

**COMMANDS.** Per file: `bash scripts/lean_verify.sh <f>.lean`. Runner-parity recheck: adversary.check_attack('lean','django__django-15037',<path>) on all 16 -> 15x {same_spec=True, admissible=True, verifies=False, verify_completed=True, 'verification failed'}, ctrl {verifies=True,'verified'}.

### RESULTS (exit code / axioms).
- ctrl.lean EXIT=0 (positive control; structurally different but correct: Option.bind + record literal instead of the mut/do control flow). ctrl_ax.lean `#print axioms correct_relationField` -> [propext, Quot.sound] CLEAN.
- atk_1..atk_15 ALL EXIT=1, every one failing with `error: unsolved goals` (semantic rejection, not a syntax/elaboration accident -- classified per-log).
Critically, every attack carries the SAME generic strong tactic script that closes ctrl.lean (cases on all three scrutinees, then first | refine <rfl,rfl,rfl> | simp_all[Bool.or_eq_true,ne_eq,String.ext_iff] | constructor<;>simp_all<;>aesop | aesop | simp_all). So the 15 rejections are the SPEC's, not a tactic tuned to the frozen impl's shape.

ATTACK TAXONOMY (all 15 distinct; each has an EXHIBITED divergence witness from gold via witness.py, so none is a gold echo whose rejection would indicate tactic weakness): atk_1 prepatch (toField never set); atk_2 drops the pk!=column guard; atk_3 toField unconditional in the FK branch; atk_4 kind ignores primary_key; atk_5 drops the self-reference case (A-reference leg: routes self through the callee); atk_6 records the referenced table's pk column instead of the referenced column; atk_7 AND instead of OR; atk_8 PARTIAL-DOMAIN (refuses refDbColumn=""); atk_9 BOUNDARY (compares len(pk)!=len(col) -- needed a widened same-length-distinct-names domain to exhibit its witness: refDbColumn='id', refPkColumn='ab'); atk_10 CONTROL-FLOW-EFFECT (pk lookup hoisted out of the else, so toField leaks into the OneToOne case); atk_11 UNGROUNDED-ORACLE ECHO (hardcodes the F2P fixture's 'inspectdb_peoplemoredata'/'people_unique_id' and is prepatch elsewhere -- would pass every shipped test, so only the spec can reject it); atk_12 PARTIAL-DOMAIN on the mapping.md truthiness leg (also refuses an empty pk name); atk_13 PARTIAL-DOMAIN (a self-FK never records to_field); atk_14 INVERTED FALSY GUARD (an ABSENT pk records to_field); atk_15 A-LEG/OPACITY PROBE (routes the self case THROUGH dbTableToModelName -- sound only if the callee fixes "self", which real table2model('self')='Self' does not).

**PATCHES.** Faithful refined patch materialized for ALL 15 attacks (not only for verifying ones -- defensive, so a runner re-run that flipped any attack to verifying still grades rather than recording 'no submitted patch'). Generated mechanically by textual substitution of the real `if is_relation:` block in django/core/management/commands/inspectdb.py, so each embeds exactly its Lean impl. GENERATOR VALIDATED: the same generator's gold.diff hunk body is byte-identical to the bundle's patch.diff. Every diff checked with `git apply --check` in the base_commit worktree -> all 16 APPLY, and each patched module passes py_compile (so no attack is refuted merely by breaking the module).

### RESOLVE RUNS EXECUTED (official harness, swebench_unified.harness.run_resolve).
- gold.diff -> resolved=TRUE, completed=true (on attempt 2/3, flagged flaky).
- atk_1.diff (prepatch) -> resolved=FALSE, completed=true, patch_successfully_applied=TRUE, FAIL_TO_PASS 0/1, PASS_TO_PASS 14/14.
This pair proves the oracle DISCRIMINATES on this instance (it certifies gold and refutes a faithful wrong refinement), so 'no attack broke the spec' is not masking a dead oracle -- cf. `_oracle_cannot_refute_here`. No resolve was protocol-MANDATORY here because zero attacks had a closing proof; the resolve legs were run to validate the oracle and the patch payload.
HOST NOTE (not a spec fact): my first three resolves, launched concurrently, ALL failed identically including gold ('Cleaning cached images... Removed 2 images', then 'Error building image: Read timed out (read timeout=60)'). Concurrent resolves race on the shared docker image cache and reap each other's images; re-run SERIALLY with retries=2, gold resolved. Recorded here so a later reader does not read that load artifact as a spec verdict.

REFINEMENT.MD AUDIT (A legs; R/I pre-cleared by G-CONF = pass, 120007 cases, 0 disagreements). All 6 rows tagged R/I/A-reference; ZERO kind-3 (changed-inexpressible) rows -- claim confirmed. Row 5 is the only A row (A-reference): `table2model` -> `opaque dbTableToModelName`.

Verified: (a) `grep -E '^\s*axiom\s'` over Solution.lean returns NOTHING, so the 'No A-consumed rows' claim is literally true and STANDARD_AXIOMS is the whole allowance; (b) the opaque appears in the IDENTICAL expression `if refDbTable = tableName then "self" else dbTableToModelName refDbTable` in BOTH the post-conditions and the impl region, so only reflexivity on it is ever needed; (c) OPACITY-INDEPENDENCE PROBED MECHANICALLY -- I replaced the opaque with two arbitrary concrete functions (ax_probe.lean: s.push '!'; ax_probe2.lean: the CONSTANT function fun _ => "K", which collapses all tables to one model id) and the frozen proof still closes, EXIT=0 for both.

So the proof consumes no property of the callee beyond functionhood, exactly as row 5 claims; the A-reference obligation is discharged by G-AX (recorded pass: determinism + alnum range over boundary + 50k fuzzed names, seed 15037) and correspondence to the real callee at inspectdb.py:43 (`re.sub(r'[^a-zA-Z0-9]','',table_name.title())`) holds. Row 4's callee `get_primary_key_column` is correctly NOT axiomatized -- a DB side-effect whose observable output is lifted to the input refPkColumn, with Python falsiness (None/'') collapsed to `none`; atk_12 and atk_14 attack precisely that truthiness modeling and both are rejected.

**VERDICT:** SOUND. 15 distinct same-spec admissible attacks run, none verifies; positive control verifies with clean axioms; prepatch reproduced and its faithful patch confirmed non-resolving under the official harness while gold resolves. The spec is not merely tight but PROVABLY UNIQUE (spec_forces_the_gold_impl), so verify => correct holds for this bundle and no counterexample exists to be found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK:** faithfulness-break (is problem_spec_relationField too strong / drifted from real repo behavior?). Result: NO divergence found. Reference used correctly = base_commit dab48b7 worktree WITH patch.diff APPLIED (the modeled function is the post-patch `if is_relation:` branch, inspectdb.py:118-133); base commit used only for the untouched callee table2model.

### Evidence

1. **ARTIFACT INTEGRITY.** scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). `#print axioms correct_relationField` -> [propext, Quot.sound]; `implementation_relationField` -> no axioms. NO sorryAx, so the proof is real, not fake. Spec region byte-identity: markers.region_hashes recomputed vs meta.json -> axioms/pure/post-conditions/impl/spec_view ALL match exactly (spec_view 3fa3c804...). Only the `proof` region hash differs (9e5b5a32 computed vs a7c4c675 recorded) — a proof-region repair, which does NOT touch the contract; spec_signature/spec_view is unchanged, so the frozen spec is intact and retained attacks remain valid.

2. **EXHAUSTIVE DIFFERENTIAL vs REAL POST-PATCH CODE.** Transcribed the patched block verbatim (including `extra_params.pop('unique', False) or extra_params.get('primary_key')` and the `if ref_pk_column and ref_pk_column != ref_db_column` falsy guard) and cross-producted isUnique x isPrimaryKey x refDbColumn x refDbTable x tableName x refPkColumn over an 11-name alphabet incl. '', 'id', 'other_id', 'people_unique_id', case variants, digits, spaces, trailing space, plus pk=None. 63,888 cases, 0 divergences on all three outputs (relType, relTo, toField).

3. REAL RUNTIME TRACES (strongest check). Instrumented the patched inspectdb.py in the worktree to log the actual (input, output) tuple at the real call site, staged asgiref+sqlparse, applied the test_patch, and ran the live `inspectdb` suite against the real sqlite introspection. Captured 14 real tuples; the Lean spec reproduces relType/relTo/toField on 14/14, 0 divergences. This includes the exact F2P case (refDbColumn='people_unique_id', refDbTable='inspectdb_peoplemoredata', refPkColumn='id' -> toField='people_unique_id') and the self-reference case (refDbTable==tableName -> relTo='self'). F2P test test_foreign_key_to_field PASSES on the patched worktree. (Only test_custom_fields failed — not in PASS_TO_PASS, an env/field-type artifact, unrelated to this branch.)

4. TOO-STRONG PROBES, all refuted:
- Option-String truthiness collapse (mapping.md maps None and '' -> none): checked '' pk. Real code treats '' as FALSY -> no to_field; spec with `none` -> toField=none. AGREE. The collapse is sound, not a strengthening.
- toField in the OneToOneField branch: spec demands `none` unconditionally when isUnique||isPrimaryKey. Real code never even computes ref_pk_column on that path AND `pop('unique')` removes the key, so to_field is genuinely absent. AGREE — the spec is not over-committing.
- (isUnique,isPrimaryKey)=(True,True): confirmed UNREACHABLE in the real repo (inspectdb.py:113-115 is `if column_name == primary_key_column: ... elif column_name in unique_columns: ...`, mutually exclusive). The spec is total over a superset of reachable inputs, but even on that unreachable point both legs give ('OneToOneField', ..., none). No spurious obligation.
- pk == refDbColumn (ordinary FK-to-pk): both give toField=none, so the spec does NOT over-fire to_field on the common case. This is the precise `exactly when` boundary and it is correct.
- relTo when refDbTable==tableName AND a to_field is also due: real gives ('ForeignKey','self','other_id'); spec agrees — the two conjuncts are independent in the real code too, so conjoining them is not a strengthening.
- Opaque dbTableToModelName: validated as an A-reference against real table2model (re.sub(r'[^a-zA-Z0-9]','',name.title())) on all 11 non-self observed traces — computed == observed relTo every time. It also appears identically in spec and impl, so no axiom property is consumed and it cannot hide a strengthening.

5. NOT VACUOUS (the control). Solution_prepatch.lean against the frozen spec -> lean_verify exit 1, error at line 79 'Application type mismatch' on the .toField conjunct. So the spec genuinely discriminates the pre-patch behavior; it is not trivially satisfiable, and the FAITHFUL verdict is not a vacuity artifact. The discriminating clause in refinement.md (row 4) matches the observed failure.

**CONCLUSION:** the spec is exactly as strong as the patched code — no input on which the modeled function disagrees with the real callee. No diverging input exists to cite, so no defect is claimed. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

### MEASUREMENTS I RAN (not inherited from any bundle file).

0. Relaxation status: this bundle carries NO relaxation. `meta.json` has no `relaxed_leakage` key (python check: `'relaxed_leakage' in meta` -> False), there is no RELAXED_LEAKAGE.md in lean/, and `gates['G-LEAK']` records mode='strict', status='pass'. So I judged under the strict rule, with no unavoidability argument to re-derive. (The 3 grep hits for 'relaxed_leakage' in meta.json are inside the archived verdict/prose blobs, not a top-level disposition.) Nothing in Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, axiom_check.py or conformance_check.py addresses the reviewer, prescribes a verdict, or tells me how to record; `leakage.reviewer_directed()` returns [] on the spec view, mapping.md and refinement.md. No bundle-directed-at-panel finding to report.

1. Spec region identity. `markers.same_spec(Solution.lean, Solution_prepatch.lean, lean_tables)` = True. Recomputed `markers.region_hashes` and the spec_view sha256 = 3fa3c8042f41392ac8166f2af07afa50b195332a171a5623a02d48fdb8454bf3, byte-matching meta.json region_hashes.spec_view. `diff` of the two Solution files touches only the impl region (the `match refPkColumn` toField assignment, `let mut`) and the proof region -- zero spec-side delta, so there is no spec surface that differs pre/post-patch and could carry the edit.

2. Verifier. scripts/lean_verify.sh on Solution.lean + `#print axioms correct_relationField`: exit 0, output `depends on axioms: [propext, Quot.sound]` -- compiles, no sorry, no sorryAx. Control: lean_verify.sh on Solution_prepatch.lean FAILS with the expected `rfl ... but is expected to have type (implementation_relationField ...).toField = if (isUnique || isPrimaryKey) = true then none else match refPkColumn with | some pk => if pk != refDbColumn ...` -- i.e. the frozen spec's toField conjunct is load-bearing and the G-DIFF signal is real, not vacuous.

3. Mechanical screen, reproduced independently. `leakage.screen(Solution.lean, lean_tables, instance.patch, instance.problem_statement, instance.test_patch)` -> hard_failures=[], warnings=[], passed=True. Judged against problem_statement only, never hints_text (I read hints_text -- 'simple patch to handle FK to non pk field' -- and confirmed no spec-view token is sourced from it).

4. Per-rule detail I checked by hand on the projected view:
 - L1 diff markers: none of '@@', 'diff --git', '+++ ', '\nindex ' occur ('diff' appears only as the English word 'differs' in the postcondition docstring; the substring match is on the marker forms, and 'differs' is behavioral prose).
 - L1 gold lines: all 8 added/removed gold lines checked normalized (whitespace-stripped, len>=8) against the normalized view -- 0 hits. In particular none of `ref_pk_column = connection.introspection.get_primary_key_column(cursor`, `if ref_pk_column and ref_pk_column != ref_db_column:`, `extra_params['to_field'] = ref_db_column`, `else table2model(ref_db_table)` appear in any form.
 - L2 paths: 'django/core/management/commands/inspectdb.py' and its dotted module form absent; 'inspectdb', 'django', 'commands/', '.py' all absent from the view.
 - L2/L5 patched symbols: the only distinctive changed def/class symbol is `table2model` (not in problem_statement). It appears in NO spec-view identifier -- the opaque callee is named `dbTableToModelName`, which does not embed 'table2model' -- and in no comment/docstring. Also confirmed absent from the view: extra_params, get_primary_key_column, introspection, rel_type, rel_to, to_field, ref_db_column, ref_db_table, ref_pk_column, relations[, known_models, cursor, connection, handle_inspection.
 - L3 narration: full `_NARRATION` vocabulary re-run with word boundaries over the view -- 0 hits (no fix/patch/bug/wrong/broken/previously/incorrectly).

5. Semantic (beyond-mechanical) judgement -- the part a screen cannot make. The public problem_statement states the DB shape (`foo(id serial primary key, other_id int UNIQUE)`, bar's FK referencing `foo(other_id)`) and the required outcome: the generated model's other_id should be a FK to `foo(other_id)`, not to `foo`. The spec view's third bullet -- an explicit target column is recorded exactly when the field is a plain foreign key and the referenced table has a detected pk column differing from the referenced column -- is the abstract behavior the issue demands, and its discriminator (referenced column != referenced table's pk) is directly derivable from the statement's own example, where other_id is precisely not the pk `id`. That is a public-behavior restatement, not edit disclosure: it names no callee, no file, no line, no mechanism, and does not say a lookup must be added inside the ForeignKey branch. `refPkColumn` is lifted to an INPUT of the modeled function rather than modeled as the introspection call, so the mechanism stays hidden. 'ForeignKey'/'OneToOneField' are public Django field-type names (the issue itself says 'a FK to foo'), not patched repo symbols. The OneToOne/plain-FK split and the 'in every other case none' clause are frame discipline required by spec strength (attacker 1), not extra localization -- a solver reading the view learns the required contract, which is the point of a spec mode, and learns nothing about where or how to edit that the sanctioned localization channel does not already give.

**Conclusion:** NO-LEAKAGE. The spec view discloses only publicly-derivable behavior; the one distinctive patched symbol is renamed away; strict mode holds with no relaxation invoked or needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
