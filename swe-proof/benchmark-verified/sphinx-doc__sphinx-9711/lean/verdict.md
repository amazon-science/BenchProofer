# P2 adversarial audit — sphinx-doc__sphinx-9711

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample found: no wrong-behavior implementation produced a closing clean-axiom proof. The two attacks that DID verify (atk_2 oracle echo, atk_8 ASCII-guarded partial domain) both have faithful patches that RESOLVE under the official harness (FAIL_TO_PASS tests/test_extension.py::test_needs_extensions success), so neither exhibits verify=>/=>correct. atk_8 is the sharpest probe: it exploits the spec's own ASCII admissibility hypothesis by returning 'requirement met' on any non-ASCII version string, and its materialized patch (adding `if not (req.isascii() and ver.isascii()): return False`) still resolves — the precondition narrowing is real but does not reach any behavior the correctness oracle measures, because the FAIL_TO_PASS test uses only ASCII versions ('3.9'/'3.10'/'3.11'). That is a documented, stated narrowing (mapping.md 'Admitted domain', pre-conditions region prose), not a hidden hole.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,40 @@
 
 -- impl-start
 
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
+      else stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
 def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
-      else
-        match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +354,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +371,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +398,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -311,33 +311,19 @@
 
 -- impl-start
 
+
+def echoLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if entryUnmet e then some base else echoLoop (base + 1) rest
+
 def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
-      else
-        match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+    (entries : List (String × Option String)) : Option Nat := echoLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +333,12 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem echo_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (echoLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [echoLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold echoLoop
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +349,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : echoLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +376,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (echoLoop 0 entries)
+  have h := echo_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : echoLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,44 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision (faithful — the variants below attack the INDEX, not the
+per-entry decision, so this leg is the reference one). -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => verGt a b
+        | _, _ => stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some (base + 1) else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +358,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +375,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +402,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,48 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision (faithful — the variants below attack the INDEX, not the
+per-entry decision, so this leg is the reference one). -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => verGt a b
+        | _, _ => stringGt req ver
+
+/-- Reports the LAST unmet entry rather than the first. -/
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest =>
+      match decLoop (base + 1) rest with
+      | some k => some k
+      | none => if decUnmet e then some base else none
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +362,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +379,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +406,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,49 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision (faithful — the variants below attack the INDEX, not the
+per-entry decision, so this leg is the reference one). -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => verGt a b
+        | _, _ => stringGt req ver
+
+/-- The running index advances only on entries that carry a present version, so
+an unloaded entry does not occupy a position. -/
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest =>
+      match e.2 with
+      | none => decLoop base rest
+      | some _ => if decUnmet e then some base else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +363,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +380,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +407,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,41 @@
 
 -- impl-start
 
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      match parseVersion req, parseVersion ver with
+      | some a, some b => verGt a b
+      | _, _ => stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
 def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
-      else
-        match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +355,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +372,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +399,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 7 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -311,33 +311,38 @@
 
 -- impl-start
 
+
+/-- Guarded per-entry decision: only decide when both strings are ASCII;
+otherwise declare the requirement met. -/
+def entryUnmetGuarded (e : String × Option String) : Bool :=
+  match e.2 with
+  | none => false
+  | some ver =>
+      if asciiStr e.1 && asciiStr ver then requirementUnmet e.1 ver else false
+
+def guardLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if entryUnmetGuarded e then some base else guardLoop (base + 1) rest
+
 def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
-      else
-        match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+    (entries : List (String × Option String)) : Option Nat := guardLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+
+theorem guarded_eq_of_ascii (e : String × Option String) (h : entryAscii e = true) :
+    entryUnmetGuarded e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [entryUnmetGuarded, entryUnmet]
+  | some ver =>
+    simp only [entryAscii] at h
+    simp only [entryUnmetGuarded, entryUnmet]
+    simp only [Bool.and_eq_true] at h
+    simp [h.1, h.2]
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +352,33 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
+def echoLoop (base : Nat) : List (String × Option String) → Option Nat
   | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+  | e :: rest => if entryUnmet e then some base else echoLoop (base + 1) rest
+
+theorem guard_eq_echo (rest : List (String × Option String)) :
+    ∀ (base : Nat), (∀ e ∈ rest, entryAscii e = true) →
+      guardLoop base rest = echoLoop base rest := by
+  induction rest with
+  | nil => intro base _; rfl
+  | cons e rest' ih =>
+    intro base hasc
+    have he : entryAscii e = true := hasc e (by simp)
+    have hrest : ∀ e' ∈ rest', entryAscii e' = true := by
+      intro e' he'; exact hasc e' (by simp [he'])
+    rw [guardLoop, echoLoop, guarded_eq_of_ascii e he]
+    cases h : entryUnmet e with
+    | true => simp
+    | false =>
+      simp only [Bool.false_eq_true, if_false]
+      exact ih (base + 1) hrest
+
+theorem echo_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (echoLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [echoLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold echoLoop
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +389,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : echoLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +416,18 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
-  intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  intro entries hpre
+  show problem_spec_verifyExtensionVersions entries (guardLoop 0 entries)
+  rw [guard_eq_echo entries 0 hpre]
+  have h := echo_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : echoLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,43 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => natListCmp a.release b.release == .gt
+        | _, _ => stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +357,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +374,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +401,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,43 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => verGt a b
+        | _, _ => false
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +357,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +374,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +401,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,43 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => verCmp a b != .lt
+        | _, _ => stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +357,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +374,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +401,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 11 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,49 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b =>
+            (if a.epoch < b.epoch then false
+             else if b.epoch < a.epoch then true
+             else match natListCmp a.release b.release with
+               | .lt => false
+               | .gt => true
+               | .eq => natListCmp a.suffix b.suffix == .gt)
+        | _, _ => stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +363,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +380,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +407,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -311,33 +311,43 @@
 
 -- impl-start
 
-def implementation_verifyExtensionVersions
-    (entries : List (String × Option String)) : Option Nat := Id.run do
-  let mut idx := 0
-  for (req, loaded) in entries do
-    match loaded with
-    | none => pure ()
-    | some ver =>
-      let mut fulfilled := true
-      if ver == "unknown version" then
-        fulfilled := false
+/-- Per-entry decision this variant computes. -/
+def decUnmet (e : String × Option String) : Bool :=
+  match e.1, e.2 with
+  | _, none => false
+  | req, some ver =>
+      if ver == "unknown version" then true
       else
         match parseVersion req, parseVersion ver with
-        | some a, some b => if verGt a b then fulfilled := false
-        | _, _ => if stringGt req ver then fulfilled := false
-      if !fulfilled then
-        return some idx
-    idx := idx + 1
-  return none
+        | some a, some b => verGt b a
+        | _, _ => stringGt req ver
+
+def decLoop (base : Nat) : List (String × Option String) → Option Nat
+  | [] => none
+  | e :: rest => if decUnmet e then some base else decLoop (base + 1) rest
+
+def implementation_verifyExtensionVersions
+    (entries : List (String × Option String)) : Option Nat := decLoop 0 entries
 
 -- impl-end
 
 
 -- proof-start
-/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
-`r` of running the loop over `rest` starting at running index `base` reports the
-first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
-`rest` is met. -/
+/-- The variant's per-entry decision agrees with the spec predicate. This is the
+one obligation the variant must discharge; everything below is the same index
+bookkeeping the reference proof uses. -/
+theorem dec_eq_entryUnmet (e : String × Option String) : decUnmet e = entryUnmet e := by
+  obtain ⟨req, loaded⟩ := e
+  cases loaded with
+  | none => simp [decUnmet, entryUnmet]
+  | some ver =>
+    simp only [decUnmet, entryUnmet, requirementUnmet]
+    split <;> first
+      | rfl
+      | (split <;> split <;> simp_all)
+      | simp_all
+      | decide
+
 def loopSpec (base : Nat) (rest : List (String × Option String))
     (r : Option Nat) : Prop :=
   match r with
@@ -347,36 +357,13 @@
       (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
       (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)
 
-/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
-for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
-its negation collapses onto the spec predicate `entryUnmet`. -/
-theorem body_fulfilled_eq (req ver : String) :
-    (!(if ver == "unknown version" then false
-       else match parseVersion req, parseVersion ver with
-            | some a, some b => if verGt a b then false else true
-            | _, _ => if stringGt req ver then false else true))
-      = entryUnmet (req, some ver) := by
-  simp only [entryUnmet, requirementUnmet]
-  split
-  · simp
-  · split <;> split <;> simp_all
-
-/-- Clean recursive shape of the desugared loop tail run from index `base`:
-return the current index at the first unmet entry, otherwise recurse with the
-index advanced by one; `none` when the list is exhausted. -/
-def loopFrom (base : Nat) : List (String × Option String) → Option Nat
-  | [] => none
-  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest
-
-/-- Inductive characterization: for every starting index `base` and remaining
-entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
-(both the all-met `none` branch and the first-unmet `some` branch). -/
-theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
-    loopSpec base rest (loopFrom base rest) := by
+theorem dec_char_ind (base : Nat) (rest : List (String × Option String)) :
+    loopSpec base rest (decLoop base rest) := by
   induction rest generalizing base with
-  | nil => simp [loopFrom, loopSpec]
+  | nil => simp [decLoop, loopSpec]
   | cons e rest' ih =>
-    unfold loopFrom
+    unfold decLoop
+    rw [dec_eq_entryUnmet e]
     cases h : entryUnmet e with
     | true =>
       simp only [if_true]
@@ -387,7 +374,7 @@
     | false =>
       simp only [Bool.false_eq_true, if_false]
       have IH := ih (base + 1)
-      cases hr : loopFrom (base + 1) rest' with
+      cases hr : decLoop (base + 1) rest' with
       | none =>
         rw [hr] at IH
         simp only [loopSpec] at IH ⊢
@@ -414,60 +401,17 @@
             rw [List.getElem?_cons_succ] at hje
             exact hbefore n (by omega) e'' hje
 
-/-- The implementation's returned value coincides with the clean recursion started
-at index `0`. -/
-theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
-    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
-  unfold implementation_verifyExtensionVersions
-  generalize (0 : ℕ) = base
-  induction entries generalizing base with
-  | nil => rfl
-  | cons e rest ih =>
-    simp only [List.forIn_cons]
-    obtain ⟨req, loaded⟩ := e
-    cases loaded with
-    | none =>
-      simp only [loopFrom, entryUnmet]
-      exact ih (base + 1)
-    | some ver =>
-      have ih' := ih (base + 1)
-      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
-        if_true, if_false] at ih' ⊢
-      rw [loopFrom]
-      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
-      by_cases hu : (ver == "unknown version") = true
-      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
-      · simp only [hu, entryUnmet, requirementUnmet]
-        cases ha : parseVersion req with
-        | none =>
-          simp only [ha]
-          by_cases hs : stringGt req ver = true
-          · simp only [hs, if_true]; rfl
-          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-        | some a =>
-          cases hb : parseVersion ver with
-          | none =>
-            by_cases hs : stringGt req ver = true
-            · simp only [hs, if_true]; rfl
-            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
-          | some b =>
-            simp only [ha, hb]
-            by_cases hg : verGt a b = true
-            · simp only [hg, if_true]; rfl
-            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'
-
-
 theorem correct_verifyExtensionVersions :
     ∀ entries : List (String × Option String),
       problem_pre_verifyExtensionVersions entries →
       problem_spec_verifyExtensionVersions entries
         (implementation_verifyExtensionVersions entries) := by
   intro entries _hpre
-  rw [impl_eq_loopFrom0 entries]
-  have h := loop_char_ind 0 entries
+  show problem_spec_verifyExtensionVersions entries (decLoop 0 entries)
+  have h := dec_char_ind 0 entries
   simp only [loopSpec, Nat.sub_zero] at h
   unfold problem_spec_verifyExtensionVersions
-  cases hr : loopFrom 0 entries with
+  cases hr : decLoop 0 entries with
   | none => simpa [hr] using h
   | some k =>
       rw [hr] at h
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No callee is consumed as an axiom: the version-ordering operation is the
-- behavior under specification, so it is modeled deeply in the `pure` region and
-- validated against the real library routine (G-AX A-reference), not axiomatized.
-- axioms-end

-- pure-start

/-- The blank code points tolerated around a version string; a leading/trailing
run of these is ignored when reading a version. -/
def blankChars : List Char :=
  [⟨0x9, by decide⟩, ⟨0xa, by decide⟩, ⟨0xb, by decide⟩, ⟨0xc, by decide⟩,
   ⟨0xd, by decide⟩, ⟨0x1c, by decide⟩, ⟨0x1d, by decide⟩, ⟨0x1e, by decide⟩,
   ⟨0x1f, by decide⟩, ⟨0x20, by decide⟩, ⟨0x85, by decide⟩, ⟨0xa0, by decide⟩,
   ⟨0x1680, by decide⟩, ⟨0x2000, by decide⟩, ⟨0x2001, by decide⟩,
   ⟨0x2002, by decide⟩, ⟨0x2003, by decide⟩, ⟨0x2004, by decide⟩,
   ⟨0x2005, by decide⟩, ⟨0x2006, by decide⟩, ⟨0x2007, by decide⟩,
   ⟨0x2008, by decide⟩, ⟨0x2009, by decide⟩, ⟨0x200a, by decide⟩,
   ⟨0x2028, by decide⟩, ⟨0x2029, by decide⟩, ⟨0x202f, by decide⟩,
   ⟨0x205f, by decide⟩, ⟨0x3000, by decide⟩]

def isBlank (c : Char) : Bool := blankChars.contains c

/-- Case folding used when reading a version: ASCII upper case maps to lower
case, and nothing else folds. The qualifier tags below are therefore matched
case-insensitively within ASCII (`RC` and `rc` name the same tag) and a code
point outside ASCII never spells a tag; see the admissibility note in the
`pre-conditions` region for why the claim is drawn at that boundary. -/
def foldChar (c : Char) : Char :=
  if 'A' ≤ c && c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c

def isDigitC (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/-- The separators that may appear between a version's parts. -/
def isSep (c : Char) : Bool := c == '.' || c == '-' || c == '_'

def isWordC (c : Char) : Bool := isDigitC c || ('a' ≤ c && c ≤ 'z')

/-- Split off the longest leading run of decimal digits. -/
def takeDigits : List Char → List Char × List Char
  | [] => ([], [])
  | c :: cs =>
      if isDigitC c then
        let (d, r) := takeDigits cs
        (c :: d, r)
      else ([], c :: cs)

def digitsToNat (ds : List Char) : Nat :=
  ds.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/-- One segment of a version's trailing build tag: either numeric or a word. -/
structure LocalSeg where
  isNum : Bool
  num   : Nat
  word  : String

/-- The ordering key of a version: its era, its numeric components, a flat
encoding of its qualifier tags, and its build-tag segments. Two versions compare
by comparing these keys in order. -/
structure VerKey where
  epoch     : Nat
  release   : List Nat
  suffix    : List Nat
  localSegs : List LocalSeg

/-- Lexicographic comparison of numeric component lists; a proper prefix is
smaller than its extension. -/
def natListCmp : List Nat → List Nat → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | x :: xs, y :: ys =>
      if x < y then .lt else if y < x then .gt else natListCmp xs ys

/-- Build-tag comparison: word segments order before numeric ones, words compare
alphabetically, numbers numerically, and a proper prefix is smaller. -/
def localCmp : List LocalSeg → List LocalSeg → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | a :: as, b :: bs =>
      if a.isNum == b.isNum then
        (if a.isNum then
           (if a.num < b.num then .lt else if b.num < a.num then .gt else localCmp as bs)
         else
           (if a.word < b.word then .lt else if b.word < a.word then .gt
            else localCmp as bs))
      else if a.isNum then .gt else .lt

/-- Compare two version keys: era, then numeric components, then qualifier
tags, then build tag. -/
def verCmp (a b : VerKey) : Ordering :=
  if a.epoch < b.epoch then .lt else if b.epoch < a.epoch then .gt
  else match natListCmp a.release b.release with
    | .lt => .lt
    | .gt => .gt
    | .eq => match natListCmp a.suffix b.suffix with
      | .lt => .lt
      | .gt => .gt
      | .eq => localCmp a.localSegs b.localSegs

/-- `a` is a strictly later version than `b`. -/
def verGt (a b : VerKey) : Bool := verCmp a b == .gt

def dropSep (s : List Char) : List Char :=
  match s with | c :: cs => if isSep c then cs else s | [] => s

/-- Read an optional separator, then one of `toks` (longest spelling first),
then an optional separator and an optional number. -/
def tryTok : List (String × Nat) → List Char → Option (Nat × Nat × List Char)
  | [], _ => none
  | (t, rank) :: rest, s =>
      let s1 := dropSep s
      if t.toList.isPrefixOf s1 then
        let (d, r) := takeDigits (dropSep (s1.drop t.length))
        some (rank, digitsToNat d, r)
      else tryTok rest s

/-- Spellings of the pre-qualifier tags, with the rank each denotes. -/
def preToks : List (String × Nat) :=
  [("alpha", 1), ("beta", 2), ("preview", 3), ("pre", 3), ("rc", 3),
   ("a", 1), ("b", 2), ("c", 3)]

/-- Spellings of the revision-qualifier tags. -/
def postToks : List (String × Nat) := [("post", 1), ("rev", 1), ("r", 1)]

/-- Drop trailing zero components, so `1`, `1.0` and `1.0.0` share a key. -/
def stripZeros (xs : List Nat) : List Nat :=
  (xs.reverse.dropWhile (· == 0)).reverse

def mkLocalSeg (cur : List Char) : LocalSeg :=
  if cur.all isDigitC then ⟨true, digitsToNat cur, ""⟩
  else ⟨false, 0, String.mk cur⟩

/-- Read the build tag: non-empty word/number segments separated by single
separators. -/
def localLoop : List Char → List Char → Option (List LocalSeg)
  | cur, [] => if cur.isEmpty then none else some [mkLocalSeg cur]
  | cur, c :: cs =>
      if isWordC c then localLoop (cur ++ [c]) cs
      else if isSep c then
        if cur.isEmpty then none
        else match localLoop [] cs with
          | none => none
          | some segs => some (mkLocalSeg cur :: segs)
      else none

/-- Read the `.`-separated numeric components after the first one. The `Nat`
argument only bounds the recursion (each step consumes at least two characters). -/
def relLoop : Nat → List Char → List Nat × List Char
  | 0, s => ([], s)
  | n + 1, s =>
      match s with
      | '.' :: cs =>
          let (d, r) := takeDigits cs
          if d.isEmpty then ([], s)
          else
            let (more, rest) := relLoop n r
            (digitsToNat d :: more, rest)
      | _ => ([], s)

/-- Assemble the ordering key from the pieces read off a version string. A
version with no pre-qualifier but a development tag ranks below every
pre-qualifier; one with neither ranks above them all. -/
def mkKey (epoch : Nat) (rel : List Nat) (preRank : Option Nat) (preNum : Nat)
    (postRank : Option Nat) (postNum : Nat) (devRank : Option Nat) (devNum : Nat)
    (segs : List LocalSeg) : VerKey :=
  let pr :=
    match preRank, postRank, devRank with
    | none, none, some _ => 0
    | none, _, _ => 4
    | some p, _, _ => p
  let pn := match preRank with | some _ => preNum | none => 0
  ⟨epoch, stripZeros rel,
   [pr, pn, (if postRank.isSome then 1 else 0), postNum,
    (if devRank.isSome then 0 else 1), devNum], segs⟩

/-- Read everything after the optional era marker: the numeric components, then
the optional pre-, revision- and development-qualifier tags, then the optional
build tag. `none` when the text is not a readable version. -/
def parseAfterEpoch (epoch : Nat) (s : List Char) : Option VerKey :=
  let (d, r0) := takeDigits s
  if d.isEmpty then none else
  let (rel, r1) := relLoop s.length r0
  let (preRank, preNum, r2) :=
    match tryTok preToks r1 with
    | some (rk, n, rr) => (some rk, n, rr)
    | none => (none, 0, r1)
  let (postRank, postNum, r3) :=
    match r2 with
    | '-' :: cs =>
        let (d2, rr) := takeDigits cs
        if d2.isEmpty then
          match tryTok postToks r2 with
          | some (rk, n, rr2) => (some rk, n, rr2)
          | none => (none, 0, r2)
        else (some 1, digitsToNat d2, rr)
    | _ =>
        match tryTok postToks r2 with
        | some (rk, n, rr) => (some rk, n, rr)
        | none => (none, 0, r2)
  let (devRank, devNum, r4) :=
    match tryTok [("dev", 0)] r3 with
    | some (_, n, rr) => (some 0, n, rr)
    | none => (none, 0, r3)
  match r4 with
  | '+' :: cs =>
      match localLoop [] cs with
      | none => none
      | some segs =>
          some (mkKey epoch (digitsToNat d :: rel) preRank preNum postRank postNum
            devRank devNum segs)
  | [] =>
      some (mkKey epoch (digitsToNat d :: rel) preRank preNum postRank postNum
        devRank devNum [])
  | _ => none

/-- Read a version string into its ordering key, or `none` when the text is not
a readable version. Surrounding blanks are ignored, letter case is folded, an
optional leading `v` is dropped, and an optional `<digits>!` era marker is read
first. -/
def parseVersion (raw : String) : Option VerKey :=
  let t := ((raw.toList.dropWhile isBlank).reverse.dropWhile isBlank).reverse
  let s0 := t.map foldChar
  let s1 := match s0 with | c :: cs => if c == 'v' then cs else s0 | [] => s0
  match s1.idxOf? '!' with
  | some k =>
      let e := s1.take k
      if !e.isEmpty && e.all isDigitC then
        parseAfterEpoch (digitsToNat e) (s1.drop (k + 1))
      else none
  | none => parseAfterEpoch 0 s1

/-- Plain lexicographic ordering on the raw strings (Unicode code-point order).
This is the comparison used when one operand is not a readable version. -/
def stringGt (a b : String) : Bool := decide (a > b)

/-- The minimum-version requirement is NOT met for a required string `req`
against a present `ver` exactly when: the present version is the sentinel
`"unknown version"`, or — comparing as versions when both are readable as
versions, else comparing the raw strings — the required version is strictly
greater than the present one. -/
def requirementUnmet (req ver : String) : Bool :=
  if ver == "unknown version" then true
  else
    match parseVersion req, parseVersion ver with
    | some a, some b => verGt a b
    | _, _ => stringGt req ver

/-- An entry is `(req, loaded?)`: `req` is the required minimum version string;
`loaded?` is `some v` when an extension providing version string `v` is present,
or `none` when no such extension is present (in which case the requirement
imposes no failure here). The entry triggers a failure iff a version is present
and does not meet the requirement. -/
def entryUnmet (e : String × Option String) : Bool :=
  match e.2 with
  | none => false
  | some ver => requirementUnmet e.1 ver

-- pure-end

-- pre-conditions-start

/-- `true` when every code point of `s` is an ASCII one. -/
def asciiStr (s : String) : Bool := s.toList.all (fun c => c.toNat < 128)

/-- `true` when both version strings an entry mentions are ASCII text (an entry
that mentions no present version only has to have an ASCII requirement). -/
def entryAscii (e : String × Option String) : Bool :=
  asciiStr e.1 && (match e.2 with | none => true | some v => asciiStr v)

/-- Admissibility: every version string an entry mentions is ASCII text.

The version grammar read above is an ASCII grammar, and every ASCII string is
admitted — including strings that are not readable versions at all (those are
ordered as raw text) and the sentinel that stands for an unreported version. The
restriction excludes exactly one class of input: a string carrying a code point
outside ASCII that a case-folding table maps onto an ASCII letter. Released
revisions of the routine being modeled disagree about those: some scope their
case-insensitive tag matching to ASCII and refuse such a string, others accept it
and read it as a tag whose spelling then also orders above the ASCII spelling of
the same tag — and the two readings give different verdicts on the same pair of
inputs. There is therefore no single faithful reading of that class, and the
claim below deliberately does not make one; on ASCII input the readings agree,
and that agreement is what is measured against the real routine. -/
def problem_pre_verifyExtensionVersions
    (entries : List (String × Option String)) : Prop :=
  ∀ e ∈ entries, entryAscii e = true

-- pre-conditions-end

-- post-conditions-start

/-- The result reports the position of the FIRST entry whose version requirement
is not met, or `none` when every present version meets its requirement.

  * `none`  ⟺ no entry is unmet;
  * `some k` ⟺ entry `k` is unmet and every earlier entry is met. -/
def problem_spec_verifyExtensionVersions
    (entries : List (String × Option String)) (result : Option Nat) : Prop :=
  match result with
  | none => ∀ e ∈ entries, entryUnmet e = false
  | some k =>
      (∃ e, entries[k]? = some e ∧ entryUnmet e = true) ∧
      (∀ j, j < k → ∀ e, entries[j]? = some e → entryUnmet e = false)

-- post-conditions-end

-- impl-start

def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion req, parseVersion ver with
        | some a, some b => if verGt a b then fulfilled := false
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none

-- impl-end

-- proof-start
/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
`r` of running the loop over `rest` starting at running index `base` reports the
first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
`rest` is met. -/
def loopSpec (base : Nat) (rest : List (String × Option String))
    (r : Option Nat) : Prop :=
  match r with
  | none => ∀ e ∈ rest, entryUnmet e = false
  | some k =>
      k ≥ base ∧
      (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
      (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)

/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
its negation collapses onto the spec predicate `entryUnmet`. -/
theorem body_fulfilled_eq (req ver : String) :
    (!(if ver == "unknown version" then false
       else match parseVersion req, parseVersion ver with
            | some a, some b => if verGt a b then false else true
            | _, _ => if stringGt req ver then false else true))
      = entryUnmet (req, some ver) := by
  simp only [entryUnmet, requirementUnmet]
  split
  · simp
  · split <;> split <;> simp_all

/-- Clean recursive shape of the desugared loop tail run from index `base`:
return the current index at the first unmet entry, otherwise recurse with the
index advanced by one; `none` when the list is exhausted. -/
def loopFrom (base : Nat) : List (String × Option String) → Option Nat
  | [] => none
  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest

/-- Inductive characterization: for every starting index `base` and remaining
entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
(both the all-met `none` branch and the first-unmet `some` branch). -/
theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
    loopSpec base rest (loopFrom base rest) := by
  induction rest generalizing base with
  | nil => simp [loopFrom, loopSpec]
  | cons e rest' ih =>
    unfold loopFrom
    cases h : entryUnmet e with
    | true =>
      simp only [if_true]
      simp only [loopSpec]
      refine ⟨le_refl base, ⟨e, ?_, h⟩, ?_⟩
      · simp
      · intro j hj; omega
    | false =>
      simp only [Bool.false_eq_true, if_false]
      have IH := ih (base + 1)
      cases hr : loopFrom (base + 1) rest' with
      | none =>
        rw [hr] at IH
        simp only [loopSpec] at IH ⊢
        intro e' he'
        rcases List.mem_cons.mp he' with rfl | hmem
        · exact h
        · exact IH e' hmem
      | some k =>
        rw [hr] at IH
        simp only [loopSpec] at IH ⊢
        obtain ⟨hk, ⟨e', hek, hue'⟩, hbefore⟩ := IH
        refine ⟨by omega, ⟨e', ?_, hue'⟩, ?_⟩
        · have hkb : k - base = (k - (base + 1)) + 1 := by omega
          rw [hkb, List.getElem?_cons_succ]
          exact hek
        · intro j hj e'' hje
          cases j with
          | zero =>
            simp only [List.getElem?_cons_zero] at hje
            rw [Option.some_inj] at hje
            subst hje
            exact h
          | succ n =>
            rw [List.getElem?_cons_succ] at hje
            exact hbefore n (by omega) e'' hje

/-- The implementation's returned value coincides with the clean recursion started
at index `0`. -/
theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
  unfold implementation_verifyExtensionVersions
  generalize (0 : ℕ) = base
  induction entries generalizing base with
  | nil => rfl
  | cons e rest ih =>
    simp only [List.forIn_cons]
    obtain ⟨req, loaded⟩ := e
    cases loaded with
    | none =>
      simp only [loopFrom, entryUnmet]
      exact ih (base + 1)
    | some ver =>
      have ih' := ih (base + 1)
      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
        if_true, if_false] at ih' ⊢
      rw [loopFrom]
      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
      by_cases hu : (ver == "unknown version") = true
      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
      · simp only [hu, entryUnmet, requirementUnmet]
        cases ha : parseVersion req with
        | none =>
          simp only [ha]
          by_cases hs : stringGt req ver = true
          · simp only [hs, if_true]; rfl
          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
        | some a =>
          cases hb : parseVersion ver with
          | none =>
            by_cases hs : stringGt req ver = true
            · simp only [hs, if_true]; rfl
            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
          | some b =>
            simp only [ha, hb]
            by_cases hg : verGt a b = true
            · simp only [hg, if_true]; rfl
            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'

theorem correct_verifyExtensionVersions :
    ∀ entries : List (String × Option String),
      problem_pre_verifyExtensionVersions entries →
      problem_spec_verifyExtensionVersions entries
        (implementation_verifyExtensionVersions entries) := by
  intro entries _hpre
  rw [impl_eq_loopFrom0 entries]
  have h := loop_char_ind 0 entries
  simp only [loopSpec, Nat.sub_zero] at h
  unfold problem_spec_verifyExtensionVersions
  cases hr : loopFrom 0 entries with
  | none => simpa [hr] using h
  | some k =>
      rw [hr] at h
      exact ⟨h.2.1, h.2.2⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 12 same-spec attacks, all same_spec=True vs bundle Solution.lean (verified with swebench_unified.markers.same_spec, lean backend, via python). Every attack edits ONLY the impl+proof regions; axioms/pure/pre/post byte-identical.

**COMMANDS:** verification for each file X: `bash scripts/lean_verify.sh X.lean` from swe-proof. Run 4-at-a-time as concurrent background jobs.

### LEDGER (file / exit / meaning):
  pos_control 0 VERIFIES (unmodified bundle impl+proof)
  atk_1  1 rejected  PREPATCH BUG: string-only compare, version parse dropped
  atk_2  0 VERIFIES  ungrounded oracle echo (impl := entryUnmet loop)
  atk_3  1 rejected  off-by-one: reports index+1
  atk_4  1 rejected  reports LAST unmet entry, not FIRST
  atk_5  1 rejected  control-flow effect: index counts only LOADED entries
  atk_7  1 rejected  'unknown version' sentinel test dropped
  atk_8  0 VERIFIES  partial domain: no-op on non-ASCII (exploits the precondition)
  atk_9  1 rejected  A-leg: release-only compare, qualifier tags/epoch/local ignored
  atk_10 1 rejected  A-leg: InvalidVersion string fallback dropped
  atk_11 1 rejected  boundary: >= instead of > (equal versions rejected)
  atk_12 1 rejected  A-leg: '+' build tag (localSegs) ignored in the ordering
  atk_13 1 rejected  operands swapped in the version branch

AXIOM PROBES (`#print axioms correct_verifyExtensionVersions` appended; files probe_pos_ax.lean / probe_atk_2_ax.lean / probe_atk_8_ax.lean, kept OUT of the atk_ namespace so they are not counted as attacks): all three exit 0 with `[propext, Classical.choice, Quot.sound]` — clean, identical to the positive control. No axiom/opaque/unsafe/partial/implemented_by/extern declaration anywhere in Solution.lean; the axioms region is comment-only.

RESOLVE RUNS (mandatory for every clean-axiom verifier), via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9711', patch), driver do_resolve.py, results in resolve_atk_2.json / resolve_atk_8.json:
  atk_2: resolved=True, patch_successfully_applied=True, FAIL_TO_PASS success=['tests/test_extension.py::test_needs_extensions'], no failures
  atk_8: resolved=True, patch_successfully_applied=True, FAIL_TO_PASS success=['tests/test_extension.py::test_needs_extensions'], no failures
Both patches were confirmed to `git apply --check -p1` cleanly against sphinx/extension.py at base_commit 81a4fd973d4cfcb25d01a7b0be62cdb28f82406d (temp git repo at .../wt2). Therefore NO verifying impl has a non-resolving faithful patch => not BROKEN.

GENUINE-GAP WITNESSES (guard against 'rejected only because the tactic was too weak'). Each rejected attack was given a TAILORED proof isomorphic to the reference proof, so the only failing step is the per-entry `dec_eq_entryUnmet` lemma (or, for atk_3/4/5, the index algebra) — i.e. the rejection lands exactly at the semantic gap.
  witness.lean  (exit 3 = ONLY the one deliberate trailing sorry; all 14 `native_decide` goals CLOSED): machine-checked disagreement pairs proving each wrong decision differs from the spec's `entryUnmet` on a concrete ASCII input — prepatch: entryUnmet("3.9","3.10")=false but string-compare says true (this IS the instance's own bug, so prepatch_reproduced=true); atk_9 on "1.0" vs "1.0rc1"; atk_10 on "zzz" vs "aaa"; atk_11 on equal "3.10"/"3.10"; atk_13 on "3.11"/"3.10"; atk_12 on "1.0+b"/"1.0+a"; atk_7 on the "unknown version" sentinel.
  witness2.lean (exit 3 = only the deliberate sorry): FULL Lean proofs `atk3_violates`, `atk4_violates`, `atk5_violates` of the form `¬ problem_spec_verifyExtensionVersions E (loopN 0 E)` — the postcondition itself positively REFUTES each index-shape variant (atk_3 points one past the end so the 'entry k is unmet' conjunct is unsatisfiable; atk_4 reports entry 1 while entry 0 is also unmet, breaking 'every earlier met'; atk_5 reports index 0 which is the UNLOADED entry, which is met).

REFINEMENT.MD LEG AUDIT (8 legs, no kind-3 present): ops 1,2,7 = R (Python dict-iteration+dict-get -> List (String x Option String); warn+continue -> no failure; raise -> some idx). Ops 3,4,8 = I (fulfilled flag, sentinel test, implicit None). Ops 5,6 = A-reference, correctly tagged: the version comparison IS the behavior the patch changed, so per SPEC_GUIDE it is modeled deeply in the `pure` region rather than axiomatized — and indeed nothing is axiomatized (axioms region empty, #print axioms clean). Correspondence of the A-legs to the real callees HOLDS: I re-ran the bundle's own G-AX and G-CONF in the instance environment — axiom_check.py: checked=112432 violations=0 status=pass (P0 accept-set, P1 ordering, P2 raw-string fallback, P3 composed decision, all against the REAL `packaging.version.Version`, imported at axiom_check.py:65; `real_unmet` is a verbatim transliteration of the patched block); conformance_check.py: checked=200560 disagreements=0 status=pass. The A-reference scope equals the theorem's admitted domain (ASCII), every checked string is asserted ASCII, and the 23 out-of-scope strings are asserted NON-ASCII so the exclusion cannot absorb an admitted input.

HONEST RESIDUAL (not a break, recorded): the ASCII precondition is a real narrowing, and atk_8 demonstrates it is exploitable in the sense that a non-ASCII no-op still verifies AND still resolves. It is not a G-EQ break because (a) it is explicitly stated in the pre-conditions region prose and mapping.md 'Admitted domain', (b) the reason is callee instability across `packaging` revisions on exactly the four case-folding code points (U+0130, U+0131, U+017F, U+212A), documented with a concrete divergent end-to-end pair, and (c) the verify=>correct direction holds: its patch resolves. Only 11 of the 12 attacks were needed for the >=5 threshold; atk_6 was dropped during iteration (numbering gap is intentional, not a missing file).

**VERDICT:** SOUND. 12 attacks run to completion (10 wrong-behavior attacks all REJECTED at a machine-checked semantic gap; 2 verifiers both RESOLVE), positive control verifies with clean axioms, prepatch bug reproduced and rejected. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No counterexample found: no wrong-behavior implementation produced a closing clean-axiom proof. The two attacks that DID verify (atk_2 oracle echo, atk_8 ASCII-guarded partial domain) both have faithful patches that RESOLVE under the official harness (FAIL_TO_PASS tests/test_extension.py::test_needs_extensions success), so neither exhibits verify=>/=>correct. atk_8 is the sharpest probe: it exploits the spec's own ASCII admissibility hypothesis by returning 'requirement met' on any non-ASCII version string, and its materialized patch (adding `if not (req.isascii() and ver.isascii()): return False`) still resolves — the precondition narrowing is real but does not reach any behavior the correctness oracle measures, because the FAIL_TO_PASS test uses only ASCII versions ('3.9'/'3.10'/'3.11'). That is a documented, stated narrowing (mapping.md 'Admitted domain', pre-conditions region prose), not a hidden hole.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No callee is consumed as an axiom: the version-ordering operation is the
-- behavior under specification, so it is modeled deeply in the `pure` region and
-- validated against the real library routine (G-AX A-reference), not axiomatized.
-- axioms-end

-- pure-start

/-- The blank code points tolerated around a version string; a leading/trailing
run of these is ignored when reading a version. -/
def blankChars : List Char :=
  [⟨0x9, by decide⟩, ⟨0xa, by decide⟩, ⟨0xb, by decide⟩, ⟨0xc, by decide⟩,
   ⟨0xd, by decide⟩, ⟨0x1c, by decide⟩, ⟨0x1d, by decide⟩, ⟨0x1e, by decide⟩,
   ⟨0x1f, by decide⟩, ⟨0x20, by decide⟩, ⟨0x85, by decide⟩, ⟨0xa0, by decide⟩,
   ⟨0x1680, by decide⟩, ⟨0x2000, by decide⟩, ⟨0x2001, by decide⟩,
   ⟨0x2002, by decide⟩, ⟨0x2003, by decide⟩, ⟨0x2004, by decide⟩,
   ⟨0x2005, by decide⟩, ⟨0x2006, by decide⟩, ⟨0x2007, by decide⟩,
   ⟨0x2008, by decide⟩, ⟨0x2009, by decide⟩, ⟨0x200a, by decide⟩,
   ⟨0x2028, by decide⟩, ⟨0x2029, by decide⟩, ⟨0x202f, by decide⟩,
   ⟨0x205f, by decide⟩, ⟨0x3000, by decide⟩]

def isBlank (c : Char) : Bool := blankChars.contains c

/-- Case folding used when reading a version: ASCII upper case maps to lower
case, and nothing else folds. The qualifier tags below are therefore matched
case-insensitively within ASCII (`RC` and `rc` name the same tag) and a code
point outside ASCII never spells a tag; see the admissibility note in the
`pre-conditions` region for why the claim is drawn at that boundary. -/
def foldChar (c : Char) : Char :=
  if 'A' ≤ c && c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c

def isDigitC (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/-- The separators that may appear between a version's parts. -/
def isSep (c : Char) : Bool := c == '.' || c == '-' || c == '_'

def isWordC (c : Char) : Bool := isDigitC c || ('a' ≤ c && c ≤ 'z')

/-- Split off the longest leading run of decimal digits. -/
def takeDigits : List Char → List Char × List Char
  | [] => ([], [])
  | c :: cs =>
      if isDigitC c then
        let (d, r) := takeDigits cs
        (c :: d, r)
      else ([], c :: cs)

def digitsToNat (ds : List Char) : Nat :=
  ds.foldl (fun acc c => acc * 10 + (c.toNat - 48)) 0

/-- One segment of a version's trailing build tag: either numeric or a word. -/
structure LocalSeg where
  isNum : Bool
  num   : Nat
  word  : String

/-- The ordering key of a version: its era, its numeric components, a flat
encoding of its qualifier tags, and its build-tag segments. Two versions compare
by comparing these keys in order. -/
structure VerKey where
  epoch     : Nat
  release   : List Nat
  suffix    : List Nat
  localSegs : List LocalSeg

/-- Lexicographic comparison of numeric component lists; a proper prefix is
smaller than its extension. -/
def natListCmp : List Nat → List Nat → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | x :: xs, y :: ys =>
      if x < y then .lt else if y < x then .gt else natListCmp xs ys

/-- Build-tag comparison: word segments order before numeric ones, words compare
alphabetically, numbers numerically, and a proper prefix is smaller. -/
def localCmp : List LocalSeg → List LocalSeg → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | a :: as, b :: bs =>
      if a.isNum == b.isNum then
        (if a.isNum then
           (if a.num < b.num then .lt else if b.num < a.num then .gt else localCmp as bs)
         else
           (if a.word < b.word then .lt else if b.word < a.word then .gt
            else localCmp as bs))
      else if a.isNum then .gt else .lt

/-- Compare two version keys: era, then numeric components, then qualifier
tags, then build tag. -/
def verCmp (a b : VerKey) : Ordering :=
  if a.epoch < b.epoch then .lt else if b.epoch < a.epoch then .gt
  else match natListCmp a.release b.release with
    | .lt => .lt
    | .gt => .gt
    | .eq => match natListCmp a.suffix b.suffix with
      | .lt => .lt
      | .gt => .gt
      | .eq => localCmp a.localSegs b.localSegs

/-- `a` is a strictly later version than `b`. -/
def verGt (a b : VerKey) : Bool := verCmp a b == .gt

def dropSep (s : List Char) : List Char :=
  match s with | c :: cs => if isSep c then cs else s | [] => s

/-- Read an optional separator, then one of `toks` (longest spelling first),
then an optional separator and an optional number. -/
def tryTok : List (String × Nat) → List Char → Option (Nat × Nat × List Char)
  | [], _ => none
  | (t, rank) :: rest, s =>
      let s1 := dropSep s
      if t.toList.isPrefixOf s1 then
        let (d, r) := takeDigits (dropSep (s1.drop t.length))
        some (rank, digitsToNat d, r)
      else tryTok rest s

/-- Spellings of the pre-qualifier tags, with the rank each denotes. -/
def preToks : List (String × Nat) :=
  [("alpha", 1), ("beta", 2), ("preview", 3), ("pre", 3), ("rc", 3),
   ("a", 1), ("b", 2), ("c", 3)]

/-- Spellings of the revision-qualifier tags. -/
def postToks : List (String × Nat) := [("post", 1), ("rev", 1), ("r", 1)]

/-- Drop trailing zero components, so `1`, `1.0` and `1.0.0` share a key. -/
def stripZeros (xs : List Nat) : List Nat :=
  (xs.reverse.dropWhile (· == 0)).reverse

def mkLocalSeg (cur : List Char) : LocalSeg :=
  if cur.all isDigitC then ⟨true, digitsToNat cur, ""⟩
  else ⟨false, 0, String.mk cur⟩

/-- Read the build tag: non-empty word/number segments separated by single
separators. -/
def localLoop : List Char → List Char → Option (List LocalSeg)
  | cur, [] => if cur.isEmpty then none else some [mkLocalSeg cur]
  | cur, c :: cs =>
      if isWordC c then localLoop (cur ++ [c]) cs
      else if isSep c then
        if cur.isEmpty then none
        else match localLoop [] cs with
          | none => none
          | some segs => some (mkLocalSeg cur :: segs)
      else none

/-- Read the `.`-separated numeric components after the first one. The `Nat`
argument only bounds the recursion (each step consumes at least two characters). -/
def relLoop : Nat → List Char → List Nat × List Char
  | 0, s => ([], s)
  | n + 1, s =>
      match s with
      | '.' :: cs =>
          let (d, r) := takeDigits cs
          if d.isEmpty then ([], s)
          else
            let (more, rest) := relLoop n r
            (digitsToNat d :: more, rest)
      | _ => ([], s)

/-- Assemble the ordering key from the pieces read off a version string. A
version with no pre-qualifier but a development tag ranks below every
pre-qualifier; one with neither ranks above them all. -/
def mkKey (epoch : Nat) (rel : List Nat) (preRank : Option Nat) (preNum : Nat)
    (postRank : Option Nat) (postNum : Nat) (devRank : Option Nat) (devNum : Nat)
    (segs : List LocalSeg) : VerKey :=
  let pr :=
    match preRank, postRank, devRank with
    | none, none, some _ => 0
    | none, _, _ => 4
    | some p, _, _ => p
  let pn := match preRank with | some _ => preNum | none => 0
  ⟨epoch, stripZeros rel,
   [pr, pn, (if postRank.isSome then 1 else 0), postNum,
    (if devRank.isSome then 0 else 1), devNum], segs⟩

/-- Read everything after the optional era marker: the numeric components, then
the optional pre-, revision- and development-qualifier tags, then the optional
build tag. `none` when the text is not a readable version. -/
def parseAfterEpoch (epoch : Nat) (s : List Char) : Option VerKey :=
  let (d, r0) := takeDigits s
  if d.isEmpty then none else
  let (rel, r1) := relLoop s.length r0
  let (preRank, preNum, r2) :=
    match tryTok preToks r1 with
    | some (rk, n, rr) => (some rk, n, rr)
    | none => (none, 0, r1)
  let (postRank, postNum, r3) :=
    match r2 with
    | '-' :: cs =>
        let (d2, rr) := takeDigits cs
        if d2.isEmpty then
          match tryTok postToks r2 with
          | some (rk, n, rr2) => (some rk, n, rr2)
          | none => (none, 0, r2)
        else (some 1, digitsToNat d2, rr)
    | _ =>
        match tryTok postToks r2 with
        | some (rk, n, rr) => (some rk, n, rr)
        | none => (none, 0, r2)
  let (devRank, devNum, r4) :=
    match tryTok [("dev", 0)] r3 with
    | some (_, n, rr) => (some 0, n, rr)
    | none => (none, 0, r3)
  match r4 with
  | '+' :: cs =>
      match localLoop [] cs with
      | none => none
      | some segs =>
          some (mkKey epoch (digitsToNat d :: rel) preRank preNum postRank postNum
            devRank devNum segs)
  | [] =>
      some (mkKey epoch (digitsToNat d :: rel) preRank preNum postRank postNum
        devRank devNum [])
  | _ => none

/-- Read a version string into its ordering key, or `none` when the text is not
a readable version. Surrounding blanks are ignored, letter case is folded, an
optional leading `v` is dropped, and an optional `<digits>!` era marker is read
first. -/
def parseVersion (raw : String) : Option VerKey :=
  let t := ((raw.toList.dropWhile isBlank).reverse.dropWhile isBlank).reverse
  let s0 := t.map foldChar
  let s1 := match s0 with | c :: cs => if c == 'v' then cs else s0 | [] => s0
  match s1.idxOf? '!' with
  | some k =>
      let e := s1.take k
      if !e.isEmpty && e.all isDigitC then
        parseAfterEpoch (digitsToNat e) (s1.drop (k + 1))
      else none
  | none => parseAfterEpoch 0 s1

/-- Plain lexicographic ordering on the raw strings (Unicode code-point order).
This is the comparison used when one operand is not a readable version. -/
def stringGt (a b : String) : Bool := decide (a > b)

/-- The minimum-version requirement is NOT met for a required string `req`
against a present `ver` exactly when: the present version is the sentinel
`"unknown version"`, or — comparing as versions when both are readable as
versions, else comparing the raw strings — the required version is strictly
greater than the present one. -/
def requirementUnmet (req ver : String) : Bool :=
  if ver == "unknown version" then true
  else
    match parseVersion req, parseVersion ver with
    | some a, some b => verGt a b
    | _, _ => stringGt req ver

/-- An entry is `(req, loaded?)`: `req` is the required minimum version string;
`loaded?` is `some v` when an extension providing version string `v` is present,
or `none` when no such extension is present (in which case the requirement
imposes no failure here). The entry triggers a failure iff a version is present
and does not meet the requirement. -/
def entryUnmet (e : String × Option String) : Bool :=
  match e.2 with
  | none => false
  | some ver => requirementUnmet e.1 ver

-- pure-end

-- pre-conditions-start

/-- `true` when every code point of `s` is an ASCII one. -/
def asciiStr (s : String) : Bool := s.toList.all (fun c => c.toNat < 128)

/-- `true` when both version strings an entry mentions are ASCII text (an entry
that mentions no present version only has to have an ASCII requirement). -/
def entryAscii (e : String × Option String) : Bool :=
  asciiStr e.1 && (match e.2 with | none => true | some v => asciiStr v)

/-- Admissibility: every version string an entry mentions is ASCII text.

The version grammar read above is an ASCII grammar, and every ASCII string is
admitted — including strings that are not readable versions at all (those are
ordered as raw text) and the sentinel that stands for an unreported version. The
restriction excludes exactly one class of input: a string carrying a code point
outside ASCII that a case-folding table maps onto an ASCII letter. Released
revisions of the routine being modeled disagree about those: some scope their
case-insensitive tag matching to ASCII and refuse such a string, others accept it
and read it as a tag whose spelling then also orders above the ASCII spelling of
the same tag — and the two readings give different verdicts on the same pair of
inputs. There is therefore no single faithful reading of that class, and the
claim below deliberately does not make one; on ASCII input the readings agree,
and that agreement is what is measured against the real routine. -/
def problem_pre_verifyExtensionVersions
    (entries : List (String × Option String)) : Prop :=
  ∀ e ∈ entries, entryAscii e = true

-- pre-conditions-end

-- post-conditions-start

/-- The result reports the position of the FIRST entry whose version requirement
is not met, or `none` when every present version meets its requirement.

  * `none`  ⟺ no entry is unmet;
  * `some k` ⟺ entry `k` is unmet and every earlier entry is met. -/
def problem_spec_verifyExtensionVersions
    (entries : List (String × Option String)) (result : Option Nat) : Prop :=
  match result with
  | none => ∀ e ∈ entries, entryUnmet e = false
  | some k =>
      (∃ e, entries[k]? = some e ∧ entryUnmet e = true) ∧
      (∀ j, j < k → ∀ e, entries[j]? = some e → entryUnmet e = false)

-- post-conditions-end

-- impl-start

def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion req, parseVersion ver with
        | some a, some b => if verGt a b then fulfilled := false
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none

-- impl-end

-- proof-start
/-- Base-relative postcondition wrapper: `loopSpec base rest r` says the result
`r` of running the loop over `rest` starting at running index `base` reports the
first-in-`rest` unmet entry (offset by `base`), or `none` when every entry in
`rest` is met. -/
def loopSpec (base : Nat) (rest : List (String × Option String))
    (r : Option Nat) : Prop :=
  match r with
  | none => ∀ e ∈ rest, entryUnmet e = false
  | some k =>
      k ≥ base ∧
      (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
      (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)

/-- Per-entry body correspondence: the boolean `fulfilled` the loop body computes
for a present version `ver` is exactly `!entryUnmet (req, some ver)`; equivalently
its negation collapses onto the spec predicate `entryUnmet`. -/
theorem body_fulfilled_eq (req ver : String) :
    (!(if ver == "unknown version" then false
       else match parseVersion req, parseVersion ver with
            | some a, some b => if verGt a b then false else true
            | _, _ => if stringGt req ver then false else true))
      = entryUnmet (req, some ver) := by
  simp only [entryUnmet, requirementUnmet]
  split
  · simp
  · split <;> split <;> simp_all

/-- Clean recursive shape of the desugared loop tail run from index `base`:
return the current index at the first unmet entry, otherwise recurse with the
index advanced by one; `none` when the list is exhausted. -/
def loopFrom (base : Nat) : List (String × Option String) → Option Nat
  | [] => none
  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest

/-- Inductive characterization: for every starting index `base` and remaining
entry list `rest`, `loopFrom base rest` satisfies the base-relative `loopSpec`
(both the all-met `none` branch and the first-unmet `some` branch). -/
theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
    loopSpec base rest (loopFrom base rest) := by
  induction rest generalizing base with
  | nil => simp [loopFrom, loopSpec]
  | cons e rest' ih =>
    unfold loopFrom
    cases h : entryUnmet e with
    | true =>
      simp only [if_true]
      simp only [loopSpec]
      refine ⟨le_refl base, ⟨e, ?_, h⟩, ?_⟩
      · simp
      · intro j hj; omega
    | false =>
      simp only [Bool.false_eq_true, if_false]
      have IH := ih (base + 1)
      cases hr : loopFrom (base + 1) rest' with
      | none =>
        rw [hr] at IH
        simp only [loopSpec] at IH ⊢
        intro e' he'
        rcases List.mem_cons.mp he' with rfl | hmem
        · exact h
        · exact IH e' hmem
      | some k =>
        rw [hr] at IH
        simp only [loopSpec] at IH ⊢
        obtain ⟨hk, ⟨e', hek, hue'⟩, hbefore⟩ := IH
        refine ⟨by omega, ⟨e', ?_, hue'⟩, ?_⟩
        · have hkb : k - base = (k - (base + 1)) + 1 := by omega
          rw [hkb, List.getElem?_cons_succ]
          exact hek
        · intro j hj e'' hje
          cases j with
          | zero =>
            simp only [List.getElem?_cons_zero] at hje
            rw [Option.some_inj] at hje
            subst hje
            exact h
          | succ n =>
            rw [List.getElem?_cons_succ] at hje
            exact hbefore n (by omega) e'' hje

/-- The implementation's returned value coincides with the clean recursion started
at index `0`. -/
theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
  unfold implementation_verifyExtensionVersions
  generalize (0 : ℕ) = base
  induction entries generalizing base with
  | nil => rfl
  | cons e rest ih =>
    simp only [List.forIn_cons]
    obtain ⟨req, loaded⟩ := e
    cases loaded with
    | none =>
      simp only [loopFrom, entryUnmet]
      exact ih (base + 1)
    | some ver =>
      have ih' := ih (base + 1)
      simp only [Id.run_bind, bind_pure_comp, map_pure, Bool.not_false, Bool.not_true,
        if_true, if_false] at ih' ⊢
      rw [loopFrom]
      simp only [Bool.false_eq_true, if_false, bind_pure_comp, map_pure]
      by_cases hu : (ver == "unknown version") = true
      · simp only [hu, entryUnmet, requirementUnmet, if_true]; rfl
      · simp only [hu, entryUnmet, requirementUnmet]
        cases ha : parseVersion req with
        | none =>
          simp only [ha]
          by_cases hs : stringGt req ver = true
          · simp only [hs, if_true]; rfl
          · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
        | some a =>
          cases hb : parseVersion ver with
          | none =>
            by_cases hs : stringGt req ver = true
            · simp only [hs, if_true]; rfl
            · simp only [hs, Bool.false_eq_true, if_false]; exact ih'
          | some b =>
            simp only [ha, hb]
            by_cases hg : verGt a b = true
            · simp only [hg, if_true]; rfl
            · simp only [hg, Bool.false_eq_true, if_false]; exact ih'

theorem correct_verifyExtensionVersions :
    ∀ entries : List (String × Option String),
      problem_pre_verifyExtensionVersions entries →
      problem_spec_verifyExtensionVersions entries
        (implementation_verifyExtensionVersions entries) := by
  intro entries _hpre
  rw [impl_eq_loopFrom0 entries]
  have h := loop_char_ind 0 entries
  simp only [loopSpec, Nat.sub_zero] at h
  unfold problem_spec_verifyExtensionVersions
  cases hr : loopFrom 0 entries with
  | none => simpa [hr] using h
  | some k =>
      rw [hr] at h
      exact ⟨h.2.1, h.2.2⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 12 same-spec attacks, all same_spec=True vs bundle Solution.lean (verified with swebench_unified.markers.same_spec, lean backend, via python). Every attack edits ONLY the impl+proof regions; axioms/pure/pre/post byte-identical.

**COMMANDS:** verification for each file X: `bash scripts/lean_verify.sh X.lean` from swe-proof. Run 4-at-a-time as concurrent background jobs.

### LEDGER (file / exit / meaning):
  pos_control 0 VERIFIES (unmodified bundle impl+proof)
  atk_1  1 rejected  PREPATCH BUG: string-only compare, version parse dropped
  atk_2  0 VERIFIES  ungrounded oracle echo (impl := entryUnmet loop)
  atk_3  1 rejected  off-by-one: reports index+1
  atk_4  1 rejected  reports LAST unmet entry, not FIRST
  atk_5  1 rejected  control-flow effect: index counts only LOADED entries
  atk_7  1 rejected  'unknown version' sentinel test dropped
  atk_8  0 VERIFIES  partial domain: no-op on non-ASCII (exploits the precondition)
  atk_9  1 rejected  A-leg: release-only compare, qualifier tags/epoch/local ignored
  atk_10 1 rejected  A-leg: InvalidVersion string fallback dropped
  atk_11 1 rejected  boundary: >= instead of > (equal versions rejected)
  atk_12 1 rejected  A-leg: '+' build tag (localSegs) ignored in the ordering
  atk_13 1 rejected  operands swapped in the version branch

AXIOM PROBES (`#print axioms correct_verifyExtensionVersions` appended; files probe_pos_ax.lean / probe_atk_2_ax.lean / probe_atk_8_ax.lean, kept OUT of the atk_ namespace so they are not counted as attacks): all three exit 0 with `[propext, Classical.choice, Quot.sound]` — clean, identical to the positive control. No axiom/opaque/unsafe/partial/implemented_by/extern declaration anywhere in Solution.lean; the axioms region is comment-only.

RESOLVE RUNS (mandatory for every clean-axiom verifier), via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9711', patch), driver do_resolve.py, results in resolve_atk_2.json / resolve_atk_8.json:
  atk_2: resolved=True, patch_successfully_applied=True, FAIL_TO_PASS success=['tests/test_extension.py::test_needs_extensions'], no failures
  atk_8: resolved=True, patch_successfully_applied=True, FAIL_TO_PASS success=['tests/test_extension.py::test_needs_extensions'], no failures
Both patches were confirmed to `git apply --check -p1` cleanly against sphinx/extension.py at base_commit 81a4fd973d4cfcb25d01a7b0be62cdb28f82406d (temp git repo at .../wt2). Therefore NO verifying impl has a non-resolving faithful patch => not BROKEN.

GENUINE-GAP WITNESSES (guard against 'rejected only because the tactic was too weak'). Each rejected attack was given a TAILORED proof isomorphic to the reference proof, so the only failing step is the per-entry `dec_eq_entryUnmet` lemma (or, for atk_3/4/5, the index algebra) — i.e. the rejection lands exactly at the semantic gap.
  witness.lean  (exit 3 = ONLY the one deliberate trailing sorry; all 14 `native_decide` goals CLOSED): machine-checked disagreement pairs proving each wrong decision differs from the spec's `entryUnmet` on a concrete ASCII input — prepatch: entryUnmet("3.9","3.10")=false but string-compare says true (this IS the instance's own bug, so prepatch_reproduced=true); atk_9 on "1.0" vs "1.0rc1"; atk_10 on "zzz" vs "aaa"; atk_11 on equal "3.10"/"3.10"; atk_13 on "3.11"/"3.10"; atk_12 on "1.0+b"/"1.0+a"; atk_7 on the "unknown version" sentinel.
  witness2.lean (exit 3 = only the deliberate sorry): FULL Lean proofs `atk3_violates`, `atk4_violates`, `atk5_violates` of the form `¬ problem_spec_verifyExtensionVersions E (loopN 0 E)` — the postcondition itself positively REFUTES each index-shape variant (atk_3 points one past the end so the 'entry k is unmet' conjunct is unsatisfiable; atk_4 reports entry 1 while entry 0 is also unmet, breaking 'every earlier met'; atk_5 reports index 0 which is the UNLOADED entry, which is met).

REFINEMENT.MD LEG AUDIT (8 legs, no kind-3 present): ops 1,2,7 = R (Python dict-iteration+dict-get -> List (String x Option String); warn+continue -> no failure; raise -> some idx). Ops 3,4,8 = I (fulfilled flag, sentinel test, implicit None). Ops 5,6 = A-reference, correctly tagged: the version comparison IS the behavior the patch changed, so per SPEC_GUIDE it is modeled deeply in the `pure` region rather than axiomatized — and indeed nothing is axiomatized (axioms region empty, #print axioms clean). Correspondence of the A-legs to the real callees HOLDS: I re-ran the bundle's own G-AX and G-CONF in the instance environment — axiom_check.py: checked=112432 violations=0 status=pass (P0 accept-set, P1 ordering, P2 raw-string fallback, P3 composed decision, all against the REAL `packaging.version.Version`, imported at axiom_check.py:65; `real_unmet` is a verbatim transliteration of the patched block); conformance_check.py: checked=200560 disagreements=0 status=pass. The A-reference scope equals the theorem's admitted domain (ASCII), every checked string is asserted ASCII, and the 23 out-of-scope strings are asserted NON-ASCII so the exclusion cannot absorb an admitted input.

HONEST RESIDUAL (not a break, recorded): the ASCII precondition is a real narrowing, and atk_8 demonstrates it is exploitable in the sense that a non-ASCII no-op still verifies AND still resolves. It is not a G-EQ break because (a) it is explicitly stated in the pre-conditions region prose and mapping.md 'Admitted domain', (b) the reason is callee instability across `packaging` revisions on exactly the four case-folding code points (U+0130, U+0131, U+017F, U+212A), documented with a concrete divergent end-to-end pair, and (c) the verify=>correct direction holds: its patch resolves. Only 11 of the 12 attacks were needed for the >=5 threshold; atk_6 was dropped during iteration (numbering gap is intentional, not a missing file).

**VERDICT:** SOUND. 12 attacks run to completion (10 wrong-behavior attacks all REJECTED at a machine-checked semantic gap; 2 verifiers both RESOLVE), positive control verifies with clean axioms, prepatch bug reproduced and rejected. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness / spec-too-strong) on sphinx-doc__sphinx-9711 (lean). Reference = base_commit worktree with patch.diff APPLIED (verified: `git apply -v` reports 'Applied patch sphinx/extension.py cleanly', and the resulting sphinx/extension.py contains the fulfilled/try-Version/except-InvalidVersion block). Real callee run in the instance image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-9711 (testbed env, python 3.9.20, packaging 24.1). NO divergence found on any input the spec admits.

### Artifact integrity
- Solution.lean compiles: scripts/lean_verify.sh Sol.lean -> EXIT 0 (no sorry).
- `#print axioms correct_verifyExtensionVersions` => [propext, Classical.choice, Quot.sound]. Clean: no sorryAx, so the proof is not fake.
- Spec region identity: markers.spec_view(Solution.lean, lean backend) sha256 = 05c52ae8f92688917dacc9415f7d04ca140f916bb1c4d2c9b18b182cc2135513 == meta.json region_hashes.spec_view. markers.same_spec(gold, specview_9711.txt) = True. Spec region is byte-identical to the recorded view.

### What I checked that the bundle did not
The bundle's G-AX (axiom_check.py) validates a *Python transliteration* of the pure region against real packaging; it passes here (checked=112432 violations=0). But the leg that was never closed is LEAN-vs-real: the prior panel_2 run's probe.out is 0 bytes (its probe died on `maximum recursion depth has been reached` from one huge list literal + noncomputable IR errors -- a tooling failure, not a spec defect). That empty probe is why this role recorded no verdict. I closed the leg directly:
- Built Probe.lean from Solution.lean's own pure region (split at impl-start, so the REAL definitions parseVersion/verGt/requirementUnmet/stringGt are exercised, not a retyped copy), sharded the pool into 19 chunks of 400 and set maxRecDepth 20000 to defeat the elaboration failure. EXIT 0, real output emitted.
- Pool: 7,242 ASCII strings (token prefix-conflict grid over alpha/a/beta/b/preview/pre/c/rc/post/rev/r/dev x 4 separators x optional numbers; two- and three-token chains; the bare -N post form vs pre-with-dash; epoch/v grid incl. '1!2!3','v1!2','1.0!'; local(+) segment grid incl. rejects '+a..b','+A','+a+b'; release shapes '00','1..2','.1','1.'; all 10 ASCII \s blanks leading/trailing/interior; lexicographic stressors; exhaustive short strings; 4,000 random mutations). 36,210 (req,ver) pairs via 5 rotations incl. the diagonal.
- Diffed four fingerprints, Lean output vs real packaging in-container: ACCEPT-SET 0 mismatches; GT (ordering key comparison) 0; STR (str.`__gt__` fallback) 0; DEC (composed requirementUnmet == the patched block's own decision) 0. TOTAL 0.

### HARNESS SENSITIVITY (a 0 from a dead probe is worthless)
- Positive control: mutated ONLY `stripZeros` to the identity in the probe (breaking the 1 == 1.0 == 1.0.0 equality), rebuilt, re-diffed => 156 mismatches surfaced, incl. req='1' ver='1.0\t'. The harness detects real key-level drift.
- e2e negative control: removed the 'unknown version' sentinel rule from the model => 231/2000 end-to-end mismatches. The e2e harness is sensitive too.

REFINEMENT LEGS (ops 1,2,7 of refinement.md) DRIVEN END-TO-END
Called the REAL patched verify_needs_extensions(app, config) with a fake app/Config, recovering the raised extension's index from the VersionRequirementError message, and compared to the modeled first-unmet index: 3,512 cases (0..4 entries, drawn from 28 version strings incl. 'unknown version', 'abc', '1!2.0', 'v1.0', '1.0.dev1', '1.0+a', '', '1.x', ' 1.0', None-for-not-loaded) => 0 mismatches. This confirms: not-loaded => no failure (warning is non-observable), raise-on-first == `some k` with all earlier entries met, and fall-through == `none`. NOTE ON A TRAP I HIT: my first e2e run showed 261 'mismatches' because `git apply` had silently no-op'd and I was driving the BASE (unpatched) function -- e.g. ('0.6','0.10') real=0 model=None, which is precisely the string-comparison bug the patch fixes. Reporting that would have been the base-commit-as-reference error; I re-ran with the patch verifiably applied and it went to 0.

**ASCII FUZZ:** 400,000 additional generated ASCII pairs (asserted ASCII, so none skipped) => P0 accept-set 0, P3 composed-decision 0.

### ON THE PRECONDITION (the spec-too-strong question)
problem_pre restricts every version string an entry mentions to ASCII. I verified this narrowing is LOAD-BEARING rather than a shield: in this exact environment the model and the real callee genuinely disagree on the documented class -- '1.0poſt1' (U+017F) model_accept=False real_accept=True; '1.0dev1+ſ' model_accept=False real_accept=True; '1.0+K' (U+212A) model_accept=False real_accept=True -- because packaging compiles VERSION_PATTERN with re.IGNORECASE, which folds those code points onto ASCII letters, while foldChar folds ASCII only. Every such witness is strictly non-ASCII, so it is excluded by problem_pre and cannot be reached by any admitted input; 5.2M exhaustive ASCII strings + 400k ASCII fuzz pairs + 36,210 Lean-vs-real pairs produced no ASCII witness. The exclusion is disclosed in the pre-conditions docstring, mapping.md and axiom_check.py's OUT_OF_SCOPE (each entry asserted non-ASCII so it cannot absorb an admitted input). This is a stated, genuine narrowing of coverage, not a drift that hides a disagreement inside the admitted domain -- so it is not a faithfulness defect under this gate.

**CONCLUSION:** no input exists on which the modeled function disagrees with the real (patched) callee within the admitted domain. Verdict FAITHFUL. Caveat: the ASCII precondition does mean the cell proves nothing about configurations mentioning non-ASCII version strings; that is a coverage limitation the bundle documents, and I flag it as the one thing a reader should weigh, not as a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: sphinx-doc__sphinx-9711/lean. NO relaxation is claimed in this bundle: no RELAXED_LEAKAGE.md exists anywhere under the instance dir, meta.json has relaxed_leakage=None, and gates.G-LEAK.status="pass" (detail "spec view clean"), so there was no unavoidability argument to inherit or re-derive; I judged the spec view on the ordinary standard.

### WHAT I MEASURED (all re-run myself, not read off the stamps):
1. Spec view identity/integrity. Computed the consumer view with swebench_unified.markers.spec_view(Solution.lean, LeanBackend().language) -- the same projection eval/dataset.py ships to modes 1/2 (impl + proof regions elided; comments/docstrings retained). sha256 of the computed view = 05c52ae8f92688917dacc9415f7d04ca140f916bb1c4d2c9b18b182cc2135513, byte-equal to meta.json region_hashes.spec_view. markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True, so the spec region is byte-identical across the twin and I am reviewing the view both variants expose. patch.diff is byte-equal to instance.json["patch"] (gold), so the leak target is the real gold edit.
2. Mechanical screen re-run from source: leakage.screen(Solution.lean, lean tables, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Judged against problem_statement only; hints_text for this instance is empty anyway.
3. Proof is real, not fake. scripts/lean_verify.sh on Solution.lean exits 0 (warnings only: unusedSimpArgs linter). Appended `#print axioms correct_verifyExtensionVersions` to a copy  and rebuilt: exit 0, "depends on axioms: [propext, Classical.choice, Quot.sound]" -- no sorryAx. The axioms region is empty (comment only), so nothing is over-claimed via an axiom either.
4. Manual leak hunt beyond the lexer, term by term, against the gold diff (sphinx/extension.py, changed symbol verify_needs_extensions):
   - No diff markers, no "sphinx/extension.py", no dotted module path, no gold-diff line quoted or near-quoted (the diff is Python; the view is a Lean key/ordering model -- `Version(reqversion) > Version(extension.version)` appears nowhere, it is `verGt a b` over a parsed key).
   - The newly imported callee is NOT named: zero occurrences of "packaging", "InvalidVersion", "PEP", "440", "pkg_resources", "distutils", "LooseVersion", "setuptools". The axioms comment and the pre-conditions docstring say only "the real library routine" / "the routine being modeled" -- exactly the de-narration the spec guide prescribes (the html.unescape precedent), not the callee name.
   - No repo-symbol echo. Gold symbol verify_needs_extensions; spec identifiers are problem_spec_/problem_pre_verifyExtensionVersions, requirementUnmet, entryUnmet. "verify_needs_extensions" is not embedded in any of them, and every word in verifyExtensionVersions is public prose in the issue ("handy for verifying minimum extension versions", "needs_extensions"), so the name localizes nothing the solver cannot read in the problem_statement.
   - No bug->fix narration: no "fix/bug/patched/previously/incorrectly/wrong/broken/regression". (The "fix" substring hits are inside `suffix` and `isPrefixOf`; the narration regex is word-bounded, and I confirmed by reading each line.)
   - The literal "unknown version" in requirementUnmet is NOT edit information: it is pre-existing unchanged behavior sitting in the solver's own worktree at base_commit (verified in extension.py: Extension.`__init__` defaults version to 'unknown version' and the pre-patch guard already tests it), and it is a context/removed-side fact rather than something the fix introduces.
5. The substantive judgement call. The view does state the required behavior in full -- an epoch/release/pre-post-dev/local ordering key with trailing-zero equality, case folding, optional leading `v`, plus a lexicographic raw-string comparison when either operand is unreadable. The public problem_statement already discloses the discriminator itself ("only checks versions in a 'string-like' manner", "'0.6' > '0.10'" as strings vs "'0.6' < '0.10'" as versions, 0.10.0 must be accepted against a 0.6 minimum), so the semantic-comparison requirement is public. The extra content -- the qualifier/local-tag ordering detail and the unreadable-operand fallback -- is abstract post-state, stated with no exception mechanism, no library name, no control-flow shape and no edit site; that is the specification mode's intended trade (and what G-PANEL-1 demands strength for), not edit disclosure. Nothing in the view narrows WHERE to edit or reveals the diagnosis beyond the issue text.
6. Bundle-integrity check on this layer: I ran leakage.reviewer_directed over EVERY file in the instance directory (all four backends, not just lean) -- zero hits. No file addresses this role, prescribes a verdict, or states a recording convention, so there is nothing of that kind to report as a finding. lean/verdict.md does record all four roles as "fail" with machine verdicts of the form "this role reached no verdict on the latest attempt" (and meta G-EQ is INCONCLUSIVE: 0 admissible attacks, no positive control) -- i.e. prior runs of these roles never reached a verdict; that is a separate no-verdict/host-side condition, it is not a leakage argument, and it does not weigh on this verdict.

**CONCLUSION:** the spec view leaks nothing about the gold edit beyond the solver-visible problem_statement. NO-LEAKAGE. (Caveat outside my gate, recorded for the reader: G-EQ/G-PANEL-1/G-PANEL-2 currently carry no reached verdict for this cell, so the cell is not green on my say-so.)

**Bundle:** sphinx-doc__sphinx-9711/lean. NO relaxation is claimed in this bundle: no RELAXED_LEAKAGE.md exists anywhere under the instance dir, meta.json has relaxed_leakage=None, and gates.G-LEAK.status="pass" (detail "spec view clean"), so there was no unavoidability argument to inherit or re-derive; I judged the spec view on the ordinary standard.