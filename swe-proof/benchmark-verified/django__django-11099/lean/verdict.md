# P2 adversarial audit — django__django-11099

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl both closes with clean axioms AND fails to resolve. The only closing candidate (atk_5) is an extensionally-canonical echo whose faithful patch (= the gold patch) RESOLVES under the official harness, which is NOT a weakness (G-PANEL-1/echo policy).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,67 +55,23 @@
 
 -- impl-start
 def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
+  let core := if username.getLast? = some (Char.ofNat 10) then username.dropLast else username
+  if core.isEmpty then
     return false
   let mut ok := true
-  for c in username do
+  for c in core do
     if !isAllowedAscii c then
       ok := false
   return ok
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  unfold problem_spec_validateAscii implementation_validateAscii
+  simp
+  sorry
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,68 +54,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
-    return false
-  let mut ok := true
-  for c in username do
-    if !isAllowedAscii c then
-      ok := false
-  return ok
+def implementation_validateAscii (username : List Char) : Bool :=
+  !username.isEmpty
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  unfold problem_spec_validateAscii implementation_validateAscii
+  sorry
 -- proof-end
 
 -- post-conditions-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,68 +54,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
-    return false
-  let mut ok := true
-  for c in username do
-    if !isAllowedAscii c then
-      ok := false
-  return ok
+def implementation_validateAscii (username : List Char) : Bool :=
+  !username.isEmpty && (username.drop 1).all isAllowedAscii
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  unfold problem_spec_validateAscii implementation_validateAscii
+  sorry
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,68 +54,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
-    return false
-  let mut ok := true
-  for c in username do
-    if !isAllowedAscii c then
-      ok := false
-  return ok
+def implementation_validateAscii (username : List Char) : Bool :=
+  !username.isEmpty && username.any isAllowedAscii
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  unfold problem_spec_validateAscii implementation_validateAscii
+  sorry
 -- proof-end
 
 -- post-conditions-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,68 +54,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
-    return false
-  let mut ok := true
-  for c in username do
-    if !isAllowedAscii c then
-      ok := false
-  return ok
+def implementation_validateAscii (username : List Char) : Bool :=
+  !username.isEmpty && username.all isAllowedAscii
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  rfl
 -- proof-end
 
 -- post-conditions-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,68 +54,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
-    return false
-  let mut ok := true
-  for c in username do
-    if !isAllowedAscii c then
-      ok := false
-  return ok
+def implementation_validateAscii (username : List Char) : Bool :=
+  username.all isAllowedAscii
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  unfold problem_spec_validateAscii implementation_validateAscii
+  sorry
 -- proof-end
 
 -- post-conditions-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,68 +54,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_validateAscii (username : List Char) : Bool := Id.run do
-  if username.isEmpty then
-    return false
-  let mut ok := true
-  for c in username do
-    if !isAllowedAscii c then
-      ok := false
-  return ok
+def implementation_validateAscii (username : List Char) : Bool :=
+  !username.isEmpty && username.dropLast.all isAllowedAscii
 -- impl-end
 
 -- proof-start
-
--- proof_aux for correct_validateAscii
-/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
-`isAllowedAscii` over the list, starting from `init`. Models the loop body
-`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
-def okFold (init : Bool) (l : List Char) : Bool :=
-  l.foldl (fun acc c => acc && isAllowedAscii c) init
-
-theorem loop_eq_fold (init : Bool) (l : List Char) :
-    (Id.run do
-      let mut ok := init
-      for c in l do
-        if !isAllowedAscii c then
-          ok := false
-      return ok) = okFold init l := by
-  induction l generalizing init with
-  | nil => rfl
-  | cons c cs ih =>
-    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
-        ← ih]
-    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
-    split <;> simp_all
-
-theorem fold_eq_all (init : Bool) (l : List Char) :
-    okFold init l = (init && l.all isAllowedAscii) := by
-  unfold okFold
-  induction l generalizing init with
-  | nil => simp
-  | cons c cs ih =>
-    simp only [List.foldl_cons, List.all_cons, ih]
-    rw [Bool.and_assoc]
-
-theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
-    implementation_validateAscii username = false ∧
-    (!username.isEmpty && username.all isAllowedAscii) = false := by
-  simp only [List.isEmpty_iff] at h
-  subst h
-  simp [implementation_validateAscii]
-
 theorem correct_validateAscii : ∀ username : List Char,
     problem_spec_validateAscii username (implementation_validateAscii username) := by
   intro username
-  unfold problem_spec_validateAscii
-  by_cases h : username.isEmpty = true
-  · obtain ⟨hl, hr⟩ := empty_branch username h
-    rw [hl, hr]
-  · unfold implementation_validateAscii
-    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
-    exact (loop_eq_fold true username).trans
-      ((fold_eq_all true username).trans (by simp))
-
+  unfold problem_spec_validateAscii implementation_validateAscii
+  sorry
 -- proof-end
 
 -- post-conditions-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Username admissibility checks.

A username is a finite sequence of characters. Two admissibility checks are
modeled, differing only in which characters they treat as *allowed*:

* one whose allowed set is the English-letter family — English letters, digits,
  the underscore, and the four punctuation characters `.`, `@`, `+`, `-`;
* one whose allowed set is the international-letter family — letters from any
  script, digits, the underscore, and the same four punctuation characters.

In both cases the intended rule is the same and is stated purely over the whole
sequence: a username is admissible exactly when it is non-empty AND every one of
its characters belongs to the relevant allowed set. In particular a sequence is
admissible only if it consists *entirely* of allowed characters from its first
character through its very last; a sequence that carries any non-allowed
character anywhere — including a terminating line-break character — is not
admissible.

The per-character membership test (whether a single character belongs to the
allowed set) is an unchanged building block and is left abstract here; only the
whole-sequence admissibility rule is modeled.
-/

-- axioms-start
/-- Whether a single character belongs to the English-letter allowed set
(English letters, digits, underscore, and `.` `@` `+` `-`). An unchanged
per-character building block; left abstract (its exact membership is
orthogonal to the whole-sequence rule modeled here — see mapping.md). -/
opaque isAllowedAscii : Char → Bool

/-- Whether a single character belongs to the international-letter allowed set
(letters from any script, digits, underscore, and `.` `@` `+` `-`). The
unicode-flavored counterpart of `isAllowedAscii`; likewise abstract. -/
opaque isAllowedUnicode : Char → Bool
-- axioms-end

-- pure-start
-- The whole-sequence admissibility rule is expressed directly with `List.all`
-- and emptiness in the post-condition; no additional functional helper is
-- needed here.
-- pure-end

-- post-conditions-start
/-- Admissibility against the English-letter allowed set: the result is `true`
exactly when the username is non-empty and every character is allowed. The whole
sequence must consist of allowed characters (frame: the result is pinned as this
exact boolean of the input — nothing about the result is left free). -/
def problem_spec_validateAscii (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedAscii)
-- post-conditions-end

-- impl-start
def implementation_validateAscii (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedAscii c then
      ok := false
  return ok
-- impl-end

-- proof-start

-- proof_aux for correct_validateAscii
/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
`isAllowedAscii` over the list, starting from `init`. Models the loop body
`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
def okFold (init : Bool) (l : List Char) : Bool :=
  l.foldl (fun acc c => acc && isAllowedAscii c) init

theorem loop_eq_fold (init : Bool) (l : List Char) :
    (Id.run do
      let mut ok := init
      for c in l do
        if !isAllowedAscii c then
          ok := false
      return ok) = okFold init l := by
  induction l generalizing init with
  | nil => rfl
  | cons c cs ih =>
    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
        ← ih]
    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
    split <;> simp_all

theorem fold_eq_all (init : Bool) (l : List Char) :
    okFold init l = (init && l.all isAllowedAscii) := by
  unfold okFold
  induction l generalizing init with
  | nil => simp
  | cons c cs ih =>
    simp only [List.foldl_cons, List.all_cons, ih]
    rw [Bool.and_assoc]

theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
    implementation_validateAscii username = false ∧
    (!username.isEmpty && username.all isAllowedAscii) = false := by
  simp only [List.isEmpty_iff] at h
  subst h
  simp [implementation_validateAscii]

theorem correct_validateAscii : ∀ username : List Char,
    problem_spec_validateAscii username (implementation_validateAscii username) := by
  intro username
  unfold problem_spec_validateAscii
  by_cases h : username.isEmpty = true
  · obtain ⟨hl, hr⟩ := empty_branch username h
    rw [hl, hr]
  · unfold implementation_validateAscii
    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
    exact (loop_eq_fold true username).trans
      ((fold_eq_all true username).trans (by simp))

-- proof-end

-- post-conditions-start
/-- Admissibility against the international-letter allowed set: the result is
`true` exactly when the username is non-empty and every character is allowed. -/
def problem_spec_validateUnicode (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedUnicode)
-- post-conditions-end

-- impl-start
def implementation_validateUnicode (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedUnicode c then
      ok := false
  return ok
-- impl-end

-- proof-start
theorem correct_validateUnicode : ∀ username : List Char,
    problem_spec_validateUnicode username (implementation_validateUnicode username) := by
  intro username
  have key : ∀ (l : List Char) (r : Bool),
      (forIn (m := Id) l r (fun c r =>
        if !isAllowedUnicode c then pure (ForInStep.yield false)
        else pure (ForInStep.yield r))) = (r && l.all isAllowedUnicode) := by
    intro l
    induction l with
    | nil => intro r; simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
    | cons a as ih =>
      intro r
      rw [List.forIn_cons]
      by_cases h : isAllowedUnicode a
      · simp only [h, Bool.not_true, Bool.false_eq_true, ↓reduceIte, ih, List.all_cons, Bool.true_and]
        rfl
      · simp only [h, Bool.not_false, ↓reduceIte, ih, List.all_cons, Bool.false_and, Bool.and_false]
        rfl
  unfold problem_spec_validateUnicode implementation_validateUnicode
  cases username with
  | nil => rfl
  | cons a as =>
    simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, ↓reduceIte, bind_pure_comp, map_pure]
    rw [show (forIn (m := Id) (a::as) true (fun c r => if !isAllowedUnicode c then pure (ForInStep.yield false) else pure (ForInStep.yield r))) = _ from key (a::as) true]
    simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_validate{Ascii,Unicode} pin `result` as an EXACT boolean equality to `(!username.isEmpty && username.all isAllowed*)`. This makes correct_* a total functional-equivalence obligation — a closing proof forces the impl to equal the canonical function for ALL values of the opaque predicates. The opacity of isAllowedAscii/isAllowedUnicode gives NO escape hatch: the result is grounded in `all isAllowed*` over the whole list, so any structurally-divergent impl fails to unify.

ATTACKS (all same_spec=True vs Solution.lean, verified via markers.same_spec; impl+proof regions collapse to placeholders in _lean_spec_view so editing them is spec-neutral):
- atk_1 (boundary / PREPATCH BUG): exempt one trailing '\n' before whole-seq check (getLast?=='\n' -> dropLast). lean_verify exit=3 (sorry) — correct_validateAscii is a FALSE statement (on "abc\n": spec demands false, impl yields true) so it cannot close. Matches shipped Solution_prepatch.lean (also exit=3).
- atk_2 (ungrounded oracle): `!username.isEmpty` (ignores per-char). exit=3.
- atk_3 (boundary): `!isEmpty && (drop 1).all isAllowedAscii` (skip first char). exit=3.
- atk_4 (control-flow-effect): `!isEmpty && username.any isAllowedAscii` (any vs all). exit=3.
- atk_5 (ungrounded-oracle echo / extensionally CANONICAL): `!isEmpty && all isAllowedAscii`. exit=0 CLOSES. #print axioms correct_validateAscii = 'does not depend on any axioms'; correct_validateUnicode = [propext, Quot.sound] (standard, clean; no sorryAx/custom). Faithful patch = gold patch. run_resolve('django__django-11099', patch, timeout=1800) => RESOLVED=True. NOT a weakness.
- atk_6 (control-flow): `username.all isAllowedAscii` (drop emptiness guard; on [] spec=false impl=true). exit=3.
- atk_7 (boundary/off-by-one): `!isEmpty && username.dropLast.all isAllowedAscii` (last-char exempt unconditionally). exit=3.

EXECUTED COMMANDS: `bash scripts/lean_verify.sh <atk_N.lean>` (from project root). Results exit codes: atk_1=3, atk_2=3, atk_3=3, atk_4=3, atk_5=0, atk_6=3, atk_7=3. pos_control (Solution.lean copy) exit=0. Verifications run concurrently in two background batches (1-4, then 5-7), ≤4 at a time.

STEP-2 (mandatory resolve of every closing clean-axiom impl): atk_5 is the ONLY closing candidate. run_resolve returned RESOLVED=True (Docker harness, django__django-11099). No closing impl fails to resolve => verify does NOT imply broken.

REFINEMENT.MD A-LEG AUDIT: 5 legs. Row1 (input carrier str<->List Char)=R; Row2 (empty->false from `+` quantifier)=R; Row3 (whole-seq \Z match = all over full list, the fixed op)=I deep-model; Row4 (isAllowedAscii = [\w.@+-] class membership, UNCHANGED callee)=A-reference; Row5 (return ok = accept bool)=R. Unicode leg identical with isAllowedUnicode. NO kind-3 leg, NO A-consumed axiom claimed. VERIFIED: atk_5 '#print axioms correct_validateAscii' shows NO axiom dependency, confirming the opaque callees inject no axiom and the proof consumes no _prop about them — genuine A-reference (loop=fold=all is purely structural, predicate-agnostic), matching the doc. A-reference correspondence to real callees ([\w.@+-] under re.ASCII / flags 0) is exercised by conformance_check.py against the real compiled regex over edge cases + 120k fuzzed inputs (seed 1109920190320), covering the \Z-vs-$ discriminator ('\n' cases).

CONCLUSION: The exact-equality spec, grounded in `all isAllowed*` over the whole list, admits no same-spec wrong impl that both verifies with clean axioms and fails to resolve. verify => correct holds here. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl both closes with clean axioms AND fails to resolve. The only closing candidate (atk_5) is an extensionally-canonical echo whose faithful patch (= the gold patch) RESOLVES under the official harness, which is NOT a weakness (G-PANEL-1/echo policy).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Username admissibility checks.

A username is a finite sequence of characters. Two admissibility checks are
modeled, differing only in which characters they treat as *allowed*:

* one whose allowed set is the English-letter family — English letters, digits,
  the underscore, and the four punctuation characters `.`, `@`, `+`, `-`;
* one whose allowed set is the international-letter family — letters from any
  script, digits, the underscore, and the same four punctuation characters.

In both cases the intended rule is the same and is stated purely over the whole
sequence: a username is admissible exactly when it is non-empty AND every one of
its characters belongs to the relevant allowed set. In particular a sequence is
admissible only if it consists *entirely* of allowed characters from its first
character through its very last; a sequence that carries any non-allowed
character anywhere — including a terminating line-break character — is not
admissible.

The per-character membership test (whether a single character belongs to the
allowed set) is an unchanged building block and is left abstract here; only the
whole-sequence admissibility rule is modeled.
-/

-- axioms-start
/-- Whether a single character belongs to the English-letter allowed set
(English letters, digits, underscore, and `.` `@` `+` `-`). An unchanged
per-character building block; left abstract (its exact membership is
orthogonal to the whole-sequence rule modeled here — see mapping.md). -/
opaque isAllowedAscii : Char → Bool

/-- Whether a single character belongs to the international-letter allowed set
(letters from any script, digits, underscore, and `.` `@` `+` `-`). The
unicode-flavored counterpart of `isAllowedAscii`; likewise abstract. -/
opaque isAllowedUnicode : Char → Bool
-- axioms-end

-- pure-start
-- The whole-sequence admissibility rule is expressed directly with `List.all`
-- and emptiness in the post-condition; no additional functional helper is
-- needed here.
-- pure-end

-- post-conditions-start
/-- Admissibility against the English-letter allowed set: the result is `true`
exactly when the username is non-empty and every character is allowed. The whole
sequence must consist of allowed characters (frame: the result is pinned as this
exact boolean of the input — nothing about the result is left free). -/
def problem_spec_validateAscii (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedAscii)
-- post-conditions-end

-- impl-start
def implementation_validateAscii (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedAscii c then
      ok := false
  return ok
-- impl-end

-- proof-start

-- proof_aux for correct_validateAscii
/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
`isAllowedAscii` over the list, starting from `init`. Models the loop body
`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
def okFold (init : Bool) (l : List Char) : Bool :=
  l.foldl (fun acc c => acc && isAllowedAscii c) init

theorem loop_eq_fold (init : Bool) (l : List Char) :
    (Id.run do
      let mut ok := init
      for c in l do
        if !isAllowedAscii c then
          ok := false
      return ok) = okFold init l := by
  induction l generalizing init with
  | nil => rfl
  | cons c cs ih =>
    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
        ← ih]
    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
    split <;> simp_all

theorem fold_eq_all (init : Bool) (l : List Char) :
    okFold init l = (init && l.all isAllowedAscii) := by
  unfold okFold
  induction l generalizing init with
  | nil => simp
  | cons c cs ih =>
    simp only [List.foldl_cons, List.all_cons, ih]
    rw [Bool.and_assoc]

theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
    implementation_validateAscii username = false ∧
    (!username.isEmpty && username.all isAllowedAscii) = false := by
  simp only [List.isEmpty_iff] at h
  subst h
  simp [implementation_validateAscii]

theorem correct_validateAscii : ∀ username : List Char,
    problem_spec_validateAscii username (implementation_validateAscii username) := by
  intro username
  unfold problem_spec_validateAscii
  by_cases h : username.isEmpty = true
  · obtain ⟨hl, hr⟩ := empty_branch username h
    rw [hl, hr]
  · unfold implementation_validateAscii
    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
    exact (loop_eq_fold true username).trans
      ((fold_eq_all true username).trans (by simp))

-- proof-end

-- post-conditions-start
/-- Admissibility against the international-letter allowed set: the result is
`true` exactly when the username is non-empty and every character is allowed. -/
def problem_spec_validateUnicode (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedUnicode)
-- post-conditions-end

-- impl-start
def implementation_validateUnicode (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedUnicode c then
      ok := false
  return ok
-- impl-end

-- proof-start
theorem correct_validateUnicode : ∀ username : List Char,
    problem_spec_validateUnicode username (implementation_validateUnicode username) := by
  intro username
  have key : ∀ (l : List Char) (r : Bool),
      (forIn (m := Id) l r (fun c r =>
        if !isAllowedUnicode c then pure (ForInStep.yield false)
        else pure (ForInStep.yield r))) = (r && l.all isAllowedUnicode) := by
    intro l
    induction l with
    | nil => intro r; simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
    | cons a as ih =>
      intro r
      rw [List.forIn_cons]
      by_cases h : isAllowedUnicode a
      · simp only [h, Bool.not_true, Bool.false_eq_true, ↓reduceIte, ih, List.all_cons, Bool.true_and]
        rfl
      · simp only [h, Bool.not_false, ↓reduceIte, ih, List.all_cons, Bool.false_and, Bool.and_false]
        rfl
  unfold problem_spec_validateUnicode implementation_validateUnicode
  cases username with
  | nil => rfl
  | cons a as =>
    simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, ↓reduceIte, bind_pure_comp, map_pure]
    rw [show (forIn (m := Id) (a::as) true (fun c r => if !isAllowedUnicode c then pure (ForInStep.yield false) else pure (ForInStep.yield r))) = _ from key (a::as) true]
    simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_validate{Ascii,Unicode} pin `result` as an EXACT boolean equality to `(!username.isEmpty && username.all isAllowed*)`. This makes correct_* a total functional-equivalence obligation — a closing proof forces the impl to equal the canonical function for ALL values of the opaque predicates. The opacity of isAllowedAscii/isAllowedUnicode gives NO escape hatch: the result is grounded in `all isAllowed*` over the whole list, so any structurally-divergent impl fails to unify.

ATTACKS (all same_spec=True vs Solution.lean, verified via markers.same_spec; impl+proof regions collapse to placeholders in _lean_spec_view so editing them is spec-neutral):
- atk_1 (boundary / PREPATCH BUG): exempt one trailing '\n' before whole-seq check (getLast?=='\n' -> dropLast). lean_verify exit=3 (sorry) — correct_validateAscii is a FALSE statement (on "abc\n": spec demands false, impl yields true) so it cannot close. Matches shipped Solution_prepatch.lean (also exit=3).
- atk_2 (ungrounded oracle): `!username.isEmpty` (ignores per-char). exit=3.
- atk_3 (boundary): `!isEmpty && (drop 1).all isAllowedAscii` (skip first char). exit=3.
- atk_4 (control-flow-effect): `!isEmpty && username.any isAllowedAscii` (any vs all). exit=3.
- atk_5 (ungrounded-oracle echo / extensionally CANONICAL): `!isEmpty && all isAllowedAscii`. exit=0 CLOSES. #print axioms correct_validateAscii = 'does not depend on any axioms'; correct_validateUnicode = [propext, Quot.sound] (standard, clean; no sorryAx/custom). Faithful patch = gold patch. run_resolve('django__django-11099', patch, timeout=1800) => RESOLVED=True. NOT a weakness.
- atk_6 (control-flow): `username.all isAllowedAscii` (drop emptiness guard; on [] spec=false impl=true). exit=3.
- atk_7 (boundary/off-by-one): `!isEmpty && username.dropLast.all isAllowedAscii` (last-char exempt unconditionally). exit=3.

EXECUTED COMMANDS: `bash scripts/lean_verify.sh <atk_N.lean>` (from project root). Results exit codes: atk_1=3, atk_2=3, atk_3=3, atk_4=3, atk_5=0, atk_6=3, atk_7=3. pos_control (Solution.lean copy) exit=0. Verifications run concurrently in two background batches (1-4, then 5-7), ≤4 at a time.

STEP-2 (mandatory resolve of every closing clean-axiom impl): atk_5 is the ONLY closing candidate. run_resolve returned RESOLVED=True (Docker harness, django__django-11099). No closing impl fails to resolve => verify does NOT imply broken.

REFINEMENT.MD A-LEG AUDIT: 5 legs. Row1 (input carrier str<->List Char)=R; Row2 (empty->false from `+` quantifier)=R; Row3 (whole-seq \Z match = all over full list, the fixed op)=I deep-model; Row4 (isAllowedAscii = [\w.@+-] class membership, UNCHANGED callee)=A-reference; Row5 (return ok = accept bool)=R. Unicode leg identical with isAllowedUnicode. NO kind-3 leg, NO A-consumed axiom claimed. VERIFIED: atk_5 '#print axioms correct_validateAscii' shows NO axiom dependency, confirming the opaque callees inject no axiom and the proof consumes no _prop about them — genuine A-reference (loop=fold=all is purely structural, predicate-agnostic), matching the doc. A-reference correspondence to real callees ([\w.@+-] under re.ASCII / flags 0) is exercised by conformance_check.py against the real compiled regex over edge cases + 120k fuzzed inputs (seed 1109920190320), covering the \Z-vs-$ discriminator ('\n' cases).

CONCLUSION: The exact-equality spec, grounded in `all isAllowed*` over the whole list, admits no same-spec wrong impl that both verifies with clean axioms and fails to resolve. verify => correct holds here. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-11099 lean bundle. Spec models two functions applying ASCII/UnicodeUsernameValidator, each as RegexValidator.__call__ with the POST-PATCH regex r'^[\w.@+-]+\Z' (accept iff regex.search(s) is not None). Modeled function: problem_spec_validate* pins result = (!username.isEmpty && username.all isAllowed*), with the per-char [\w.@+-] class test left as an A-reference opaque callee.

### Verification steps
1. Spec region byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True; spec_view is clean.
2. Lean compiles: scripts/lean_verify.sh Solution.lean exit 0. #print axioms correct_validateAscii/correct_validateUnicode => [propext, Quot.sound] only — NO sorryAx; proofs are genuine.
3. Faithfulness differential (spec formula vs real Python regex under the real [\w.@+-] per-char callee, both re.ASCII and flags=0 legs):
   - Full Unicode single-codepoint sweep 0..0x10FFFF (surrogates skipped): 0 disagreements.
   - Exhaustive all-combinations of length <=3 over a control/newline/unicode alphabet incl. \n \r \x0b \x0c \x1c \x1d \x1e \x85 (exactly the chars where \Z vs $/MULTILINE could diverge): 0 disagreements.
   - 2,000,000 randomized fuzz strings (len 0..6) incl. line separators, non-ASCII letters, other-script digits: 0 disagreements.
   - Bundle's own conformance_check.py (240,030 checks) passes.

The \Z-vs-$ fix is faithfully captured: trailing newline 'abc\n' rejected because the loop conjoins isAllowed over the WHOLE list with no last-char exemption, matching \Z (not $). The empty-string case is rejected via the isEmpty branch, matching the '+' quantifier. Spec is neither too strong nor too weak relative to the real repo behavior. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the spec view (spec_view of Solution.lean) against the SOLVER-VISIBLE problem_statement only (not hints_text; hints_text is empty here anyway). Findings:

1. Mechanical screen (leakage.screen, lean flavor) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced (`regex = r'^[\w.@+-]+\Z'` never appears; the Lean spec models admissibility abstractly, not the regex text), no patched file path (`django/contrib/auth/validators.py`) or module path, no spec-view identifier embedding a patched symbol, no narration terms.

2. same_spec confirms both Solution_prepatch.lean and Solution_prepatch_2.lean are byte-identical in the spec region to Solution.lean (frozen spec, discriminating impls differ only in body).

3. Semantic leakage analysis: the public problem_statement ALREADY discloses the complete gold edit — it names both ASCIIUsernameValidator and UnicodeUsernameValidator, quotes the pre-fix regex `r'^[\w.@+-]+$'`, explains the `$`-matches-trailing-newline quirk, AND states the exact fix `r'\A[\w.@+-]+\Z'` to 'reject usernames that end with a newline.' The gold edit is therefore fully public by the task itself.

4. The spec view's docstring line 'a sequence that carries any non-allowed character anywhere — including a terminating line-break character — is not admissible' describes exactly the post-fix behavior the problem_statement is explicitly about (trailing-newline rejection). It reveals nothing beyond the public statement; it is a faithful behavioral spec, not an edit-localizing disclosure. The identifiers validateAscii/validateUnicode map to the two validator classes the problem_statement already names.

5. Mapping/refinement docs are auditor-facing, not part of the consumer spec view, so their explicit reference to the regex change (`$` -> `\Z`) does not count toward the spec-view leak.

Conclusion: the spec view discloses nothing about the gold edit beyond what the public problem_statement already states in full. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
