# P2 adversarial audit — django__django-16631

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_validateToken is a total, mutually-exclusive, exhaustive 4-case partition (storedToken=[]; st!=[]&st=ct; st!=[]&st!=ct&st in alts; st!=[]&st!=ct&st not in alts) that pins result to a unique VerifyDecision on every input. No same-spec wrong impl can close correct_validateToken. atk_1 (prepatch bug) reduces exactly to the G-DIFF discriminating goal `⊢ False` under consistent hypotheses (st!=[], st!=ct, ∃t∈alts.t=st) where the impl returns .rejected but the spec mandates .acceptedAlternate.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,27 +60,21 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
+  -- prepatch bug: on any mismatch with current token, reject; alternates ignored
   let mut tokenVerified := false
   if storedToken = [] then
     tokenVerified := false
   else
     tokenVerified := (storedToken == currentToken)
   if !tokenVerified then
-    let mut alternateMatched := false
-    for t in alternateTokens do
-      if t == storedToken then
-        alternateMatched := true
-    if storedToken != [] && alternateMatched then
-      return .acceptedAlternate
-    else
-      return .rejected
+    return .rejected
   return .acceptedCurrent
 -- impl-end
-
 
 -- proof-start
 theorem correct_validateToken :
@@ -88,60 +82,21 @@
     problem_spec_validateToken storedToken currentToken alternateTokens
       (implementation_validateToken storedToken currentToken alternateTokens) := by
   intro st ct alts
-  have loop_lemma :
-      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
-        = (alts.any (fun t => t == st)) := by
-    have gen : ∀ (b : Bool),
-        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
-          = (b || alts.any (fun t => t == st)) := by
-      intro b
-      induction alts generalizing b with
-      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
-      | cons h tl ih =>
-        rw [List.forIn_cons]
-        simp only [bind, pure, Id.instMonad] at *
-        by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
-    have := gen false
-    simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
-  rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
   · intro h; simp [h]
   · intro h1 h2
-    simp only [h1] at *
     have hbeq : (st == ct) = true := by simp [h2]
-    simp [hbeq]
+    simp [h1, hbeq]
+  · intro h1 h2 h3
+    -- impl returns .rejected here but spec demands .acceptedAlternate: UNPROVABLE
+    have hbeq : (st == ct) = false := by simp [h2]
+    have hne : ¬ (st = ([] : List Char)) := h1
+    simp only [hbeq]
+    simp [hne, h1]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
-    have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
-  · intro h1 h2 h3
-    have hbeq : (st == ct) = false := by simp [h2]
-    have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
-    simp only [h1, hbeq]
-    simp [hany]
-
+    simp only [hbeq]
+    simp [h1]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,16 +60,17 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
-  let mut tokenVerified := false
-  if storedToken = [] then
-    tokenVerified := false
+  -- boundary bug: check equality with current FIRST, without the storedToken=[] guard.
+  -- When storedToken=[] and currentToken=[], returns acceptedCurrent, but spec
+  -- clause 1 mandates rejected for storedToken=[].
+  if storedToken == currentToken then
+    return .acceptedCurrent
   else
-    tokenVerified := (storedToken == currentToken)
-  if !tokenVerified then
     let mut alternateMatched := false
     for t in alternateTokens do
       if t == storedToken then
@@ -78,9 +79,7 @@
       return .acceptedAlternate
     else
       return .rejected
-  return .acceptedCurrent
 -- impl-end
-
 
 -- proof-start
 theorem correct_validateToken :
@@ -101,47 +100,33 @@
         rw [List.forIn_cons]
         simp only [bind, pure, Id.instMonad] at *
         by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
+        · simp only [hh, if_pos, ih]; simp [hh, List.any_cons]
+        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]; simp [hh, List.any_cons]
     have := gen false
     simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
   rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
-  · intro h; simp [h]
+  · intro h
+    -- st = []; if ct = [] impl gives acceptedCurrent, spec wants rejected. Try to close:
+    subst h
+    by_cases hc : ([] : List Char) == ct
+    · simp [hc]  -- goal: acceptedCurrent = rejected -> FALSE, cannot close
+    · simp [hc]
   · intro h1 h2
-    simp only [h1] at *
     have hbeq : (st == ct) = true := by simp [h2]
     simp [hbeq]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
     have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
+    have hany : (alts.any (fun t => t == st)) = true := by
+      rw [List.any_eq_true]; obtain ⟨x, hx, hxeq⟩ := h3; exact ⟨x, hx, by simp [hxeq]⟩
+    simp [hbeq, hne, hany]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
     have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
-    simp only [h1, hbeq]
-    simp [hany]
-
+      rw [Bool.eq_false_iff]; intro hc; rw [List.any_eq_true] at hc
+      obtain ⟨x, hx, hxeq⟩ := hc; exact h3 ⟨x, hx, by simpa using hxeq⟩
+    simp [hbeq, hany]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,27 +60,26 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
-  let mut tokenVerified := false
+  -- control-flow-effect bug: on a fallback match, returns acceptedCurrent
+  -- (wrong decision label) instead of the mandated acceptedAlternate.
   if storedToken = [] then
-    tokenVerified := false
+    return .rejected
+  if storedToken == currentToken then
+    return .acceptedCurrent
+  let mut alternateMatched := false
+  for t in alternateTokens do
+    if t == storedToken then
+      alternateMatched := true
+  if alternateMatched then
+    return .acceptedCurrent
   else
-    tokenVerified := (storedToken == currentToken)
-  if !tokenVerified then
-    let mut alternateMatched := false
-    for t in alternateTokens do
-      if t == storedToken then
-        alternateMatched := true
-    if storedToken != [] && alternateMatched then
-      return .acceptedAlternate
-    else
-      return .rejected
-  return .acceptedCurrent
+    return .rejected
 -- impl-end
-
 
 -- proof-start
 theorem correct_validateToken :
@@ -101,47 +100,28 @@
         rw [List.forIn_cons]
         simp only [bind, pure, Id.instMonad] at *
         by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
+        · simp only [hh, if_pos, ih]; simp [hh, List.any_cons]
+        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]; simp [hh, List.any_cons]
     have := gen false
     simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
   rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
   · intro h; simp [h]
   · intro h1 h2
-    simp only [h1] at *
     have hbeq : (st == ct) = true := by simp [h2]
-    simp [hbeq]
+    simp [h1, hbeq]
   · intro h1 h2 h3
+    -- spec wants acceptedAlternate; impl returns acceptedCurrent. Try to close:
     have hbeq : (st == ct) = false := by simp [h2]
-    have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
+    have hany : (alts.any (fun t => t == st)) = true := by
+      rw [List.any_eq_true]; obtain ⟨x, hx, hxeq⟩ := h3; exact ⟨x, hx, by simp [hxeq]⟩
+    simp [h1, hbeq, hany]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
     have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
-    simp only [h1, hbeq]
-    simp [hany]
-
+      rw [Bool.eq_false_iff]; intro hc; rw [List.any_eq_true] at hc
+      obtain ⟨x, hx, hxeq⟩ := hc; exact h3 ⟨x, hx, by simpa using hxeq⟩
+    simp [h1, hbeq, hany]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,27 +60,14 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
-  let mut tokenVerified := false
-  if storedToken = [] then
-    tokenVerified := false
-  else
-    tokenVerified := (storedToken == currentToken)
-  if !tokenVerified then
-    let mut alternateMatched := false
-    for t in alternateTokens do
-      if t == storedToken then
-        alternateMatched := true
-    if storedToken != [] && alternateMatched then
-      return .acceptedAlternate
-    else
-      return .rejected
-  return .acceptedCurrent
+  -- ungrounded/degenerate: rejects everything.
+  return .rejected
 -- impl-end
-
 
 -- proof-start
 theorem correct_validateToken :
@@ -88,60 +75,13 @@
     problem_spec_validateToken storedToken currentToken alternateTokens
       (implementation_validateToken storedToken currentToken alternateTokens) := by
   intro st ct alts
-  have loop_lemma :
-      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
-        = (alts.any (fun t => t == st)) := by
-    have gen : ∀ (b : Bool),
-        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
-          = (b || alts.any (fun t => t == st)) := by
-      intro b
-      induction alts generalizing b with
-      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
-      | cons h tl ih =>
-        rw [List.forIn_cons]
-        simp only [bind, pure, Id.instMonad] at *
-        by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
-    have := gen false
-    simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
-  rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
-  · intro h; simp [h]
+  · intro h; rfl
   · intro h1 h2
-    simp only [h1] at *
-    have hbeq : (st == ct) = true := by simp [h2]
-    simp [hbeq]
-  · intro h1 h2 h3
-    have hbeq : (st == ct) = false := by simp [h2]
-    have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
-  · intro h1 h2 h3
-    have hbeq : (st == ct) = false := by simp [h2]
-    have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
-    simp only [h1, hbeq]
-    simp [hany]
-
+    -- st = ct, st != [] : spec wants acceptedCurrent, impl gives rejected. Try:
+    simp
+  · intro h1 h2 h3; simp
+  · intro h1 h2 h3; rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,13 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
+  -- partial-domain bug: no storedToken != [] guard on the alternate branch.
+  -- If storedToken = [] and [] ∈ alternateTokens, wrongly returns acceptedAlternate.
   let mut tokenVerified := false
   if storedToken = [] then
     tokenVerified := false
@@ -74,13 +77,12 @@
     for t in alternateTokens do
       if t == storedToken then
         alternateMatched := true
-    if storedToken != [] && alternateMatched then
+    if alternateMatched then
       return .acceptedAlternate
     else
       return .rejected
   return .acceptedCurrent
 -- impl-end
-
 
 -- proof-start
 theorem correct_validateToken :
@@ -101,47 +103,33 @@
         rw [List.forIn_cons]
         simp only [bind, pure, Id.instMonad] at *
         by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
+        · simp only [hh, if_pos, ih]; simp [hh, List.any_cons]
+        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]; simp [hh, List.any_cons]
     have := gen false
     simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
   rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
-  · intro h; simp [h]
+  · intro h
+    -- st = []; if [] ∈ alts then impl gives acceptedAlternate, spec wants rejected. Try:
+    subst h
+    simp only [reduceIte]
+    by_cases hany : (alts.any (fun t => t == ([] : List Char))) = true
+    · simp [hany]
+    · simp [hany]
   · intro h1 h2
-    simp only [h1] at *
     have hbeq : (st == ct) = true := by simp [h2]
-    simp [hbeq]
+    simp [h1, hbeq]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
-    have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
+    have hany : (alts.any (fun t => t == st)) = true := by
+      rw [List.any_eq_true]; obtain ⟨x, hx, hxeq⟩ := h3; exact ⟨x, hx, by simp [hxeq]⟩
+    simp [h1, hbeq, hany]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
     have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
-    simp only [h1, hbeq]
-    simp [hany]
-
+      rw [Bool.eq_false_iff]; intro hc; rw [List.any_eq_true] at hc
+      obtain ⟨x, hx, hxeq⟩ := hc; exact h3 ⟨x, hx, by simpa using hxeq⟩
+    simp [h1, hbeq, hany]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,12 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
+  -- wrong-operand bug: alternate matching compares against currentToken, not storedToken.
   let mut tokenVerified := false
   if storedToken = [] then
     tokenVerified := false
@@ -72,7 +74,7 @@
   if !tokenVerified then
     let mut alternateMatched := false
     for t in alternateTokens do
-      if t == storedToken then
+      if t == currentToken then
         alternateMatched := true
     if storedToken != [] && alternateMatched then
       return .acceptedAlternate
@@ -81,7 +83,6 @@
   return .acceptedCurrent
 -- impl-end
 
-
 -- proof-start
 theorem correct_validateToken :
     ∀ (storedToken currentToken : List Char) (alternateTokens : List (List Char)),
@@ -89,59 +90,38 @@
       (implementation_validateToken storedToken currentToken alternateTokens) := by
   intro st ct alts
   have loop_lemma :
-      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
-        = (alts.any (fun t => t == st)) := by
+      (forIn (m := Id) alts false (fun t r => if t == ct then ForInStep.yield true else ForInStep.yield r))
+        = (alts.any (fun t => t == ct)) := by
     have gen : ∀ (b : Bool),
-        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
-          = (b || alts.any (fun t => t == st)) := by
+        (forIn (m := Id) alts b (fun t r => if t == ct then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
+          = (b || alts.any (fun t => t == ct)) := by
       intro b
       induction alts generalizing b with
       | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
       | cons h tl ih =>
         rw [List.forIn_cons]
         simp only [bind, pure, Id.instMonad] at *
-        by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
+        by_cases hh : (h == ct) = true
+        · simp only [hh, if_pos, ih]; simp [hh, List.any_cons]
+        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]; simp [hh, List.any_cons]
     have := gen false
     simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
   rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
   · intro h; simp [h]
   · intro h1 h2
-    simp only [h1] at *
     have hbeq : (st == ct) = true := by simp [h2]
-    simp [hbeq]
+    simp [h1, hbeq]
+  · intro h1 h2 h3
+    -- spec wants acceptedAlternate (st ∈ alts); impl checks ct ∈ alts. Try to close:
+    have hbeq : (st == ct) = false := by simp [h2]
+    have hne : (st != ([] : List Char)) = true := by simp [h1]
+    simp only [h1, hbeq, Bool.not_false, hne]
+    sorry
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
-    have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
-  · intro h1 h2 h3
-    have hbeq : (st == ct) = false := by simp [h2]
-    have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
     simp only [h1, hbeq]
-    simp [hany]
-
+    sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,27 +60,26 @@
       result = .rejected)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_validateToken
     (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
     VerifyDecision := Id.run do
-  let mut tokenVerified := false
+  -- priority bug: consults alternates BEFORE the current-token check.
+  -- When storedToken = currentToken AND storedToken ∈ alternateTokens,
+  -- returns acceptedAlternate, but spec clause 2 mandates acceptedCurrent.
   if storedToken = [] then
-    tokenVerified := false
-  else
-    tokenVerified := (storedToken == currentToken)
-  if !tokenVerified then
-    let mut alternateMatched := false
-    for t in alternateTokens do
-      if t == storedToken then
-        alternateMatched := true
-    if storedToken != [] && alternateMatched then
-      return .acceptedAlternate
-    else
-      return .rejected
-  return .acceptedCurrent
+    return .rejected
+  let mut alternateMatched := false
+  for t in alternateTokens do
+    if t == storedToken then
+      alternateMatched := true
+  if alternateMatched then
+    return .acceptedAlternate
+  if storedToken == currentToken then
+    return .acceptedCurrent
+  return .rejected
 -- impl-end
-
 
 -- proof-start
 theorem correct_validateToken :
@@ -101,47 +100,30 @@
         rw [List.forIn_cons]
         simp only [bind, pure, Id.instMonad] at *
         by_cases hh : (h == st) = true
-        · simp only [hh, if_pos, ih]
-          simp [hh, List.any_cons]
-        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
-          simp [hh, List.any_cons]
+        · simp only [hh, if_pos, ih]; simp [hh, List.any_cons]
+        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]; simp [hh, List.any_cons]
     have := gen false
     simpa using this
-  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
-    constructor
-    · intro h
-      rw [List.any_eq_true] at h
-      obtain ⟨x, hx, hxeq⟩ := h
-      exact ⟨x, hx, by simpa using hxeq⟩
-    · rintro ⟨x, hx, hxeq⟩
-      rw [List.any_eq_true]
-      exact ⟨x, hx, by simp [hxeq]⟩
-  unfold implementation_validateToken
+  unfold implementation_validateToken problem_spec_validateToken
   simp only [Id.run, bind, pure, Id.instMonad]
   rw [loop_lemma]
-  unfold problem_spec_validateToken
   refine ⟨?_, ?_, ?_, ?_⟩
   · intro h; simp [h]
   · intro h1 h2
-    simp only [h1] at *
+    -- st = ct, st != []; if st ∈ alts impl gives acceptedAlternate, spec wants acceptedCurrent. Try:
     have hbeq : (st == ct) = true := by simp [h2]
-    simp [hbeq]
+    by_cases hany : (alts.any (fun t => t == st)) = true
+    · simp [h1, hbeq, hany]
+    · simp [h1, hbeq, hany]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
-    have hne : (st != ([] : List Char)) = true := by simp [h1]
-    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
-    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
-    split <;> rfl
+    have hany : (alts.any (fun t => t == st)) = true := by
+      rw [List.any_eq_true]; obtain ⟨x, hx, hxeq⟩ := h3; exact ⟨x, hx, by simp [hxeq]⟩
+    simp [h1, hbeq, hany]
   · intro h1 h2 h3
     have hbeq : (st == ct) = false := by simp [h2]
     have hany : (alts.any (fun t => t == st)) = false := by
-      by_contra hc
-      have : (alts.any (fun t => t == st)) = true := by
-        cases h : (alts.any (fun t => t == st)) with
-        | false => exact absurd h hc
-        | true => rfl
-      exact h3 (any_char.mp this)
-    simp only [h1, hbeq]
-    simp [hany]
-
+      rw [Bool.eq_false_iff]; intro hc; rw [List.any_eq_true] at hc
+      obtain ⟨x, hx, hxeq⟩ := hc; exact h3 ⟨x, hx, by simpa using hxeq⟩
+    simp [h1, hbeq, hany]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only callee used by the
-- modeled decision is a constant-time string equality test, which is modeled
-- DEEPLY as list equality (an I op), not axiomatized. The token values that the
-- decision compares against are taken as inputs (they are produced elsewhere and
-- are opaque to this decision). The proof agent may add `_prop` axioms only if it
-- gets stuck.
-- axioms-end

-- pure-start
/-- The decision reached when validating a stored authentication token.

* `rejected` — the token is not accepted; the principal is dropped and the
  request becomes anonymous;
* `acceptedCurrent` — the token is accepted because it equals the
  currently-valid token;
* `acceptedAlternate` — the token is accepted because it equals one of the
  additionally-accepted tokens. -/
inductive VerifyDecision
  | rejected
  | acceptedCurrent
  | acceptedAlternate
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Validation of a stored authentication token against the currently-valid token
and a list of additionally-accepted tokens.

Inputs: `storedToken` is the token currently held in the request state (the empty
list models the absence of any token); `currentToken` is the token that is valid
under the current configuration; `alternateTokens` are additional tokens that are
also accepted.

The desired decision, by case on the stored token:

1. No stored token (`storedToken = []`): the token is rejected.
2. The stored token equals the current token: accepted against the current token.
3. The stored token differs from the current token but equals one of the accepted
   alternates: accepted against an alternate token.
4. The stored token differs from the current token and matches no alternate: the
   token is rejected.

The four cases partition the input space and each pins the decision to a single
value. -/
def problem_spec_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char))
    (result : VerifyDecision) : Prop :=
  (storedToken = [] → result = .rejected) ∧
  (storedToken ≠ [] → storedToken = currentToken →
      result = .acceptedCurrent) ∧
  (storedToken ≠ [] → storedToken ≠ currentToken →
      (∃ t ∈ alternateTokens, t = storedToken) →
      result = .acceptedAlternate) ∧
  (storedToken ≠ [] → storedToken ≠ currentToken →
      (¬ ∃ t ∈ alternateTokens, t = storedToken) →
      result = .rejected)
-- post-conditions-end

-- impl-start
def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision := Id.run do
  let mut tokenVerified := false
  if storedToken = [] then
    tokenVerified := false
  else
    tokenVerified := (storedToken == currentToken)
  if !tokenVerified then
    let mut alternateMatched := false
    for t in alternateTokens do
      if t == storedToken then
        alternateMatched := true
    if storedToken != [] && alternateMatched then
      return .acceptedAlternate
    else
      return .rejected
  return .acceptedCurrent
-- impl-end

-- proof-start
theorem correct_validateToken :
    ∀ (storedToken currentToken : List Char) (alternateTokens : List (List Char)),
    problem_spec_validateToken storedToken currentToken alternateTokens
      (implementation_validateToken storedToken currentToken alternateTokens) := by
  intro st ct alts
  have loop_lemma :
      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
        = (alts.any (fun t => t == st)) := by
    have gen : ∀ (b : Bool),
        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
          = (b || alts.any (fun t => t == st)) := by
      intro b
      induction alts generalizing b with
      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
      | cons h tl ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, Id.instMonad] at *
        by_cases hh : (h == st) = true
        · simp only [hh, if_pos, ih]
          simp [hh, List.any_cons]
        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
          simp [hh, List.any_cons]
    have := gen false
    simpa using this
  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
    constructor
    · intro h
      rw [List.any_eq_true] at h
      obtain ⟨x, hx, hxeq⟩ := h
      exact ⟨x, hx, by simpa using hxeq⟩
    · rintro ⟨x, hx, hxeq⟩
      rw [List.any_eq_true]
      exact ⟨x, hx, by simp [hxeq]⟩
  unfold implementation_validateToken
  simp only [Id.run, bind, pure, Id.instMonad]
  rw [loop_lemma]
  unfold problem_spec_validateToken
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2
    simp only [h1] at *
    have hbeq : (st == ct) = true := by simp [h2]
    simp [hbeq]
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hne : (st != ([] : List Char)) = true := by simp [h1]
    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
    split <;> rfl
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hany : (alts.any (fun t => t == st)) = false := by
      by_contra hc
      have : (alts.any (fun t => t == st)) = true := by
        cases h : (alts.any (fun t => t == st)) with
        | false => exact absurd h hc
        | true => rfl
      exact h3 (any_char.mp this)
    simp only [h1, hbeq]
    simp [hany]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL:

POSITIVE CONTROL: cp gold Solution.lean -> pos_control.lean. `bash scripts/lean_verify.sh pos_control.lean` => exit 0. same_spec(gold,pos_control)=True. `#print axioms correct_validateToken` => [propext, Classical.choice, Quot.sound] (clean; no sorryAx/custom axiom).

SAME_SPEC: all 7 attacks same_spec=True (header lines 1-62 = imports+axioms+pure+post kept byte-identical; only impl+proof edited).

### ATTACKS (each: `bash scripts/lean_verify.sh atk_N.lean`):
- atk_1 PREPATCH BUG (never consults alternates; mismatch->rejected): exit 1. Unsolved goal `case refine_3 ... h3:∃t∈alts,t=st ⊢ False` — irreducible false at the G-DIFF discriminating case.
- atk_2 BOUNDARY (== check before st=[] guard; both-empty -> acceptedCurrent not rejected): exit 1, unsolved goals (clause-1 violation).
- atk_3 CONTROL-FLOW-EFFECT (fallback match returns wrong label acceptedCurrent instead of acceptedAlternate): exit 1, unsolved goals (clause-3 violation).
- atk_4 UNGROUNDED-ORACLE ECHO (always .rejected): exit 1, unsolved goals (clauses 2&3 violation).
- atk_5 PARTIAL-DOMAIN (drops st!=[] guard on alternate branch; []∈alts -> acceptedAlternate not rejected): exit 1, unsolved goals (clause-1 violation).
- atk_6 WRONG-OPERAND MEMBERSHIP (matches alternate against currentToken not storedToken): exit 3 (sorry; goal not closable — clause 3/4 mismatch).
- atk_7 PRIORITY (checks alternates before current; st=ct & st∈alts -> acceptedAlternate not acceptedCurrent): exit 1, unsolved goals (clause-2 violation).

No attack produced a clean-axiom closing proof (all exits 1 or 3; none exit 0). Therefore NO faithful refined patch could be materialized/resolved — the mandated resolve step applies only to verifying impls, of which there are none. This is the expected outcome for a total exhaustive partition spec: verify=>correct holds.

REFINEMENT AUDIT: rows 1-3 = R (type refinement), rows 4-8 = I (identical op; constant_time_compare<=>list == is a faithful behavioral reproduction, decision->glue wiring fixed by the doc). No A-consumed rows (axioms region confirmed EMPTY — comments only; #print axioms clean). No A-reference rows (constant_time_compare reproduced concretely, not abstracted; G-AX skip stub justified by axiom_check.py). No kind-3 (changed-inexpressible) legs. Model<->patch correspondence holds: changed op (row 6) routes fallback match to .acceptedAlternate; G-DIFF clause matches atk_1's `⊢ False` reduction and F2P test_get_user_fallback_secret.

VERDICT: SOUND. >=7 distinct attacks run, none breaks the spec; positive control verifies with clean axioms; prepatch bug reproduced (Solution_prepatch carries sorry, and my re-encoded atk_1 fails to close at the exact discriminating goal).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_validateToken is a total, mutually-exclusive, exhaustive 4-case partition (storedToken=[]; st!=[]&st=ct; st!=[]&st!=ct&st in alts; st!=[]&st!=ct&st not in alts) that pins result to a unique VerifyDecision on every input. No same-spec wrong impl can close correct_validateToken. atk_1 (prepatch bug) reduces exactly to the G-DIFF discriminating goal `⊢ False` under consistent hypotheses (st!=[], st!=ct, ∃t∈alts.t=st) where the impl returns .rejected but the spec mandates .acceptedAlternate.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only callee used by the
-- modeled decision is a constant-time string equality test, which is modeled
-- DEEPLY as list equality (an I op), not axiomatized. The token values that the
-- decision compares against are taken as inputs (they are produced elsewhere and
-- are opaque to this decision). The proof agent may add `_prop` axioms only if it
-- gets stuck.
-- axioms-end

-- pure-start
/-- The decision reached when validating a stored authentication token.

* `rejected` — the token is not accepted; the principal is dropped and the
  request becomes anonymous;
* `acceptedCurrent` — the token is accepted because it equals the
  currently-valid token;
* `acceptedAlternate` — the token is accepted because it equals one of the
  additionally-accepted tokens. -/
inductive VerifyDecision
  | rejected
  | acceptedCurrent
  | acceptedAlternate
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Validation of a stored authentication token against the currently-valid token
and a list of additionally-accepted tokens.

Inputs: `storedToken` is the token currently held in the request state (the empty
list models the absence of any token); `currentToken` is the token that is valid
under the current configuration; `alternateTokens` are additional tokens that are
also accepted.

The desired decision, by case on the stored token:

1. No stored token (`storedToken = []`): the token is rejected.
2. The stored token equals the current token: accepted against the current token.
3. The stored token differs from the current token but equals one of the accepted
   alternates: accepted against an alternate token.
4. The stored token differs from the current token and matches no alternate: the
   token is rejected.

The four cases partition the input space and each pins the decision to a single
value. -/
def problem_spec_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char))
    (result : VerifyDecision) : Prop :=
  (storedToken = [] → result = .rejected) ∧
  (storedToken ≠ [] → storedToken = currentToken →
      result = .acceptedCurrent) ∧
  (storedToken ≠ [] → storedToken ≠ currentToken →
      (∃ t ∈ alternateTokens, t = storedToken) →
      result = .acceptedAlternate) ∧
  (storedToken ≠ [] → storedToken ≠ currentToken →
      (¬ ∃ t ∈ alternateTokens, t = storedToken) →
      result = .rejected)
-- post-conditions-end

-- impl-start
def implementation_validateToken
    (storedToken currentToken : List Char) (alternateTokens : List (List Char)) :
    VerifyDecision := Id.run do
  let mut tokenVerified := false
  if storedToken = [] then
    tokenVerified := false
  else
    tokenVerified := (storedToken == currentToken)
  if !tokenVerified then
    let mut alternateMatched := false
    for t in alternateTokens do
      if t == storedToken then
        alternateMatched := true
    if storedToken != [] && alternateMatched then
      return .acceptedAlternate
    else
      return .rejected
  return .acceptedCurrent
-- impl-end

-- proof-start
theorem correct_validateToken :
    ∀ (storedToken currentToken : List Char) (alternateTokens : List (List Char)),
    problem_spec_validateToken storedToken currentToken alternateTokens
      (implementation_validateToken storedToken currentToken alternateTokens) := by
  intro st ct alts
  have loop_lemma :
      (forIn (m := Id) alts false (fun t r => if t == st then ForInStep.yield true else ForInStep.yield r))
        = (alts.any (fun t => t == st)) := by
    have gen : ∀ (b : Bool),
        (forIn (m := Id) alts b (fun t r => if t == st then pure (ForInStep.yield true) else pure (ForInStep.yield r)))
          = (b || alts.any (fun t => t == st)) := by
      intro b
      induction alts generalizing b with
      | nil => simp only [List.forIn_nil, List.any_nil, Bool.or_false]; rfl
      | cons h tl ih =>
        rw [List.forIn_cons]
        simp only [bind, pure, Id.instMonad] at *
        by_cases hh : (h == st) = true
        · simp only [hh, if_pos, ih]
          simp [hh, List.any_cons]
        · simp only [hh, Bool.false_eq_true, if_neg, ih, not_false_iff]
          simp [hh, List.any_cons]
    have := gen false
    simpa using this
  have any_char : (alts.any (fun t => t == st)) = true ↔ (∃ t ∈ alts, t = st) := by
    constructor
    · intro h
      rw [List.any_eq_true] at h
      obtain ⟨x, hx, hxeq⟩ := h
      exact ⟨x, hx, by simpa using hxeq⟩
    · rintro ⟨x, hx, hxeq⟩
      rw [List.any_eq_true]
      exact ⟨x, hx, by simp [hxeq]⟩
  unfold implementation_validateToken
  simp only [Id.run, bind, pure, Id.instMonad]
  rw [loop_lemma]
  unfold problem_spec_validateToken
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h1 h2
    simp only [h1] at *
    have hbeq : (st == ct) = true := by simp [h2]
    simp [hbeq]
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hne : (st != ([] : List Char)) = true := by simp [h1]
    have hany : (alts.any (fun t => t == st)) = true := any_char.mpr h3
    simp only [h1, hbeq, Bool.not_false, hne, hany, Bool.and_self]
    split <;> rfl
  · intro h1 h2 h3
    have hbeq : (st == ct) = false := by simp [h2]
    have hany : (alts.any (fun t => t == st)) = false := by
      by_contra hc
      have : (alts.any (fun t => t == st)) = true := by
        cases h : (alts.any (fun t => t == st)) with
        | false => exact absurd h hc
        | true => rfl
      exact h3 (any_char.mp this)
    simp only [h1, hbeq]
    simp [hany]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL:

POSITIVE CONTROL: cp gold Solution.lean -> pos_control.lean. `bash scripts/lean_verify.sh pos_control.lean` => exit 0. same_spec(gold,pos_control)=True. `#print axioms correct_validateToken` => [propext, Classical.choice, Quot.sound] (clean; no sorryAx/custom axiom).

SAME_SPEC: all 7 attacks same_spec=True (header lines 1-62 = imports+axioms+pure+post kept byte-identical; only impl+proof edited).

### ATTACKS (each: `bash scripts/lean_verify.sh atk_N.lean`):
- atk_1 PREPATCH BUG (never consults alternates; mismatch->rejected): exit 1. Unsolved goal `case refine_3 ... h3:∃t∈alts,t=st ⊢ False` — irreducible false at the G-DIFF discriminating case.
- atk_2 BOUNDARY (== check before st=[] guard; both-empty -> acceptedCurrent not rejected): exit 1, unsolved goals (clause-1 violation).
- atk_3 CONTROL-FLOW-EFFECT (fallback match returns wrong label acceptedCurrent instead of acceptedAlternate): exit 1, unsolved goals (clause-3 violation).
- atk_4 UNGROUNDED-ORACLE ECHO (always .rejected): exit 1, unsolved goals (clauses 2&3 violation).
- atk_5 PARTIAL-DOMAIN (drops st!=[] guard on alternate branch; []∈alts -> acceptedAlternate not rejected): exit 1, unsolved goals (clause-1 violation).
- atk_6 WRONG-OPERAND MEMBERSHIP (matches alternate against currentToken not storedToken): exit 3 (sorry; goal not closable — clause 3/4 mismatch).
- atk_7 PRIORITY (checks alternates before current; st=ct & st∈alts -> acceptedAlternate not acceptedCurrent): exit 1, unsolved goals (clause-2 violation).

No attack produced a clean-axiom closing proof (all exits 1 or 3; none exit 0). Therefore NO faithful refined patch could be materialized/resolved — the mandated resolve step applies only to verifying impls, of which there are none. This is the expected outcome for a total exhaustive partition spec: verify=>correct holds.

REFINEMENT AUDIT: rows 1-3 = R (type refinement), rows 4-8 = I (identical op; constant_time_compare<=>list == is a faithful behavioral reproduction, decision->glue wiring fixed by the doc). No A-consumed rows (axioms region confirmed EMPTY — comments only; #print axioms clean). No A-reference rows (constant_time_compare reproduced concretely, not abstracted; G-AX skip stub justified by axiom_check.py). No kind-3 (changed-inexpressible) legs. Model<->patch correspondence holds: changed op (row 6) routes fallback match to .acceptedAlternate; G-DIFF clause matches atk_1's `⊢ False` reduction and F2P test_get_user_fallback_secret.

VERDICT: SOUND. >=7 distinct attacks run, none breaks the spec; positive control verifies with clean axioms; prepatch bug reproduced (Solution_prepatch carries sorry, and my re-encoded atk_1 fails to close at the exact discriminating goal).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** faithfulness-break attacker: could NOT break faithfulness. Verified: (1) Solution.lean compiles via scripts/lean_verify.sh (exit 0); `#print axioms correct_validateToken` = [propext, Classical.choice, Quot.sound] — NO sorryAx, proof is real. (2) same_spec(Solution, Solution_prepatch)=True — spec region byte-identical; prepatch impl (returns .rejected on any current-token mismatch, never consulting alternates) carries `sorry` = genuine G-DIFF signal. (3) The modeled decision function `implementation_validateToken` (spec's 4 clauses partition the input space and pin one decision each) matches the real post-patch get_user verification block. I transcribed the patched Python from scratch (base_commit tree + patch.diff): `if not session_hash: verified=False; else verified = constant_time_compare(session_hash, current); if not verified: if session_hash and any(ct_compare(session_hash, fb) for fb in fallbacks): cycle_key/rehash (=acceptedAlternate) else flush/user=None (=rejected); else falls through (=acceptedCurrent)`. Branch-taken → three-way decision maps exactly to spec clauses 1-4. Exhaustive small-domain check (stored,current ∈ {'',a,b,c}, alt lists to length 3): 0 divergences. Bundle's conformance_check.py: 120009 fuzzed inputs, 0 disagreements. Edge cases confirmed faithful: stored=[] absent → rejected (short-circuit `session_hash and`); stored==current even when also an alternate → acceptedCurrent (current-secret compared first); ∃-in-alternates vs short-circuiting any(...) is order-independent because the acceptedAlternate glue rehashes with session_auth_hash(=current), not the matched fallback, so which fallback matched is irrelevant. constant_time_compare ⟺ list equality is a faithful I-op (observable result is value equality). The spec is NOT too strong and does not drift: it agrees with the real repo callee on all inputs, including inputs outside the real HMAC-digest domain (empty current/alternates). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigor first: scripts spec-region byte-identical — markers.same_spec(Solution.lean, Solution_prepatch.lean)=True. Mechanical G-LEAK screen (leakage.screen with LeanBackend, frozen row patch+problem_statement) passes with zero hard failures: no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier embedding a patched repo symbol (patched symbols = {get_user, get_session_auth_hash, get_session_auth_fallback_hash}), no L3 narration. No relaxed_leakage flag / no RELAXED_LEAKAGE.md, so no G-PANEL-3 deferral.

Semantic analysis of the spec view (regions kept: axioms/pure/post-conditions; impl+proof elided): it discloses only VerifyDecision={rejected,acceptedCurrent,acceptedAlternate} and problem_spec_validateToken, a 4-clause total decision over opaque storedToken/currentToken/alternateTokens whose clause 3 states a stored token differing from the current token but equal to one of the 'additionally-accepted tokens' yields acceptedAlternate. This is a language-neutral restatement of behavior ALREADY public in problem_statement ('SECRET_KEY_FALLBACKS is not used for sessions' — session hashes derived under fallback secrets should remain valid during rotation; get_session_auth_hash omits the fallback secret).

The spec view carries NO Django symbols, NO SECRET_KEY_FALLBACKS naming, NO get_session_auth_fallback_hash, NO HMAC/salted_hmac mechanics. The distinctive gold glue (request.session.cycle_key() + HASH_SESSION_KEY refresh on a fallback match) is held OUTSIDE the modeled slice (mapping.md Effect glue) and is not reconstructed. Spec-region comments reference only the UNCHANGED constant_time_compare abstractly (constant-time equality <-> list equality). Nothing reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
