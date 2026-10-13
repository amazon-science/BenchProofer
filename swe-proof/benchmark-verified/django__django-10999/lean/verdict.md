# P2 adversarial audit — django__django-10999

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_innerminus.lean`, `atk_3_signseconly.lean`, `atk_4_fallbackfirst.lean`, `atk_5_oracleecho.lean`, `atk_9_daycouple.lean`, `atk_10_frac13.lean`, `atk_11_nonewline.lean`, `atk_12_twofieldHM.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6_partialdomain.lean`, `atk_7_nonascii_zero.lean`, `atk_8_outofrange_zero.lean`, `atk_14_asciionly.lean`, `atk_15_clamp.lean`, `atk_17_clockoverflow.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_13_axiomsmuggle.lean`, `atk_16_implaxiom.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,55 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Pre-fix: optionally-signed seconds field, fractional µs inherit its sign. -/
+def parseSecMicroBug? (cs : List Char) : Option (Int × Int) :=
+  match splitOnChar '.' cs with
+  | [secs] =>
+      match signedIntToInt? secs with
+      | some s => some (s, 0)
+      | none => none
+  | [secs, frac] =>
+      if frac.isEmpty || frac.length > 12 || !frac.all isDigitC then none
+      else
+        let micro6 := (frac.take 6) ++ List.replicate (6 - min 6 frac.length) '0'
+        match signedIntToInt? secs, digitsToNat? micro6 with
+        | some s, some us =>
+            let neg := "-".toList.isPrefixOf secs
+            some (s, if neg then -(us : Int) else (us : Int))
+        | _, _ => none
+  | _ => none
+
+/-- Pre-fix clock decoder: every field independently signed. -/
+def parseClockMicrosBug? (body : List Char) : Option Int :=
+  match splitOnChar ':' body with
+  | [a] =>
+      match parseSecMicroBug? a with
+      | some (s, us) => some (s * 1000000 + us)
+      | none => none
+  | [m, a] =>
+      match signedIntToInt? m, parseSecMicroBug? a with
+      | some mm, some (s, us) => some (mm * 60 * 1000000 + s * 1000000 + us)
+      | _, _ => none
+  | [h, m, a] =>
+      match signedIntToInt? h, signedIntToInt? m, parseSecMicroBug? a with
+      | some hh, some mm, some (s, us) =>
+          some (hh * 3600 * 1000000 + mm * 60 * 1000000 + s * 1000000 + us)
+      | _, _, _ => none
+  | _ => none
+
+def primaryFormatMicrosBug (v : List Char) : Option Int :=
+  match splitFirstSpace (dropFinalNewline v) with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockMicrosBug? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClockMicrosBug? (dropFinalNewline v)
+  | none => parseClockMicrosBug? (dropFinalNewline v)
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primaryFormatMicrosBug v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +300,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 2 — `atk_2_innerminus.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,44 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Inner clock fields decoded with a per-field sign (drops the non-negativity). -/
+def parseClockMicrosInner? (rest : List Char) : Option Int :=
+  let (neg, body) :=
+    match rest with
+    | '-' :: t => (true, t)
+    | _ => (false, rest)
+  match splitOnChar ':' body with
+  | [a] =>
+      match parseSecMicro? a with
+      | some (s, us) => some (applySign neg (clockUs 0 0 s us))
+      | none => none
+  | [m, a] =>
+      match signedIntToInt? m, parseSecMicro? a with
+      | some mm, some (s, us) =>
+          some (applySign neg (mm * 60 * 1000000 + ((s * 1000000 + us : Nat) : Int)))
+      | _, _ => none
+  | [h, m, a] =>
+      match signedIntToInt? h, signedIntToInt? m, parseSecMicro? a with
+      | some hh, some mm, some (s, us) =>
+          some (applySign neg (hh * 3600 * 1000000 + mm * 60 * 1000000
+                               + ((s * 1000000 + us : Nat) : Int)))
+      | _, _, _ => none
+  | _ => none
+
+def primaryInner? (v : List Char) : Option Int :=
+  let w := dropFinalNewline v
+  match splitFirstSpace w with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockMicrosInner? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClockMicrosInner? w
+  | none => parseClockMicrosInner? w
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primaryInner? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +289,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 3 — `atk_3_signseconly.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,43 @@
 -- post-conditions-end
 
 -- impl-start
+/-- The leading minus is applied to the SECONDS field only, not the whole clock. -/
+def parseClockSecOnly? (rest : List Char) : Option Int :=
+  let (neg, body) :=
+    match rest with
+    | '-' :: t => (true, t)
+    | _ => (false, rest)
+  match splitOnChar ':' body with
+  | [a] =>
+      match parseSecMicro? a with
+      | some (s, us) => some (applySign neg (clockUs 0 0 s us))
+      | none => none
+  | [m, a] =>
+      match digitsToNat? m, parseSecMicro? a with
+      | some mm, some (s, us) =>
+          some (clockUs 0 mm 0 0 + applySign neg (clockUs 0 0 s us))
+      | _, _ => none
+  | [h, m, a] =>
+      match digitsToNat? h, digitsToNat? m, parseSecMicro? a with
+      | some hh, some mm, some (s, us) =>
+          some (clockUs hh mm 0 0 + applySign neg (clockUs 0 0 s us))
+      | _, _, _ => none
+  | _ => none
+
+def primarySecOnly? (v : List Char) : Option Int :=
+  let w := dropFinalNewline v
+  match splitFirstSpace w with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockSecOnly? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClockSecOnly? w
+  | none => parseClockSecOnly? w
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primarySecOnly? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +288,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 4 — `atk_4_fallbackfirst.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -240,11 +240,10 @@
 
 -- impl-start
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  -- CONTROL-FLOW EFFECT: alternative notation tried before the primary one.
+  match fallbackFormatMicros v with
   | some us => return some us
-  | none => return fallbackFormatMicros v
+  | none => return primaryFormatMicros v
 -- impl-end
 
 -- proof-start
@@ -255,4 +254,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 5 — `atk_5_oracleecho.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -240,11 +240,8 @@
 
 -- impl-start
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+  -- ORACLE ECHO: the whole answer is read off the opaque secondary interpreter.
+  return fallbackFormatMicros v
 -- impl-end
 
 -- proof-start
@@ -255,4 +252,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 6 — `atk_6_partialdomain.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+def implementation_durationFromText (v : List Char) : Option Int :=
+  -- PARTIAL DOMAIN: honours the spec exactly where the spec speaks, and
+  -- collapses to "no interpretation" wherever a side condition fails.
+  if asciiText v = true && primaryInRange v = true then
+    (match primaryFormatMicros v with
+     | some us => some us
+     | none => fallbackFormatMicros v)
+  else none
 -- impl-end
 
 -- proof-start
@@ -252,7 +254,9 @@
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
-  intro _ _
-  simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  intro h1 h2
+  simp only [h1, h2, Bool.and_self, decide_true, if_true, beq_self_eq_true,
+             Bool.and_true, ite_true]
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 7 — `atk_7_nonascii_zero.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+def implementation_durationFromText (v : List Char) : Option Int :=
+  -- Side-condition-1 escape: any non-ASCII text denotes the zero duration.
+  if asciiText v = true then
+    (match primaryFormatMicros v with
+     | some us => some us
+     | none => fallbackFormatMicros v)
+  else some 0
 -- impl-end
 
 -- proof-start
@@ -252,7 +253,8 @@
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
-  intro _ _
-  simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  intro h1 _
+  simp only [h1, ite_true, beq_self_eq_true]
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 8 — `atk_8_outofrange_zero.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,13 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+def implementation_durationFromText (v : List Char) : Option Int :=
+  -- Side-condition-2 escape: an unrepresentable magnitude denotes zero.
+  if primaryInRange v = true then
+    (match primaryFormatMicros v with
+     | some us => some us
+     | none => fallbackFormatMicros v)
+  else some 0
 -- impl-end
 
 -- proof-start
@@ -252,7 +253,8 @@
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
-  intro _ _
-  simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  intro _ h2
+  simp only [h2, ite_true, beq_self_eq_true]
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 9 — `atk_9_daycouple.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,25 @@
 -- post-conditions-end
 
 -- impl-start
+def primaryDayCoupled? (v : List Char) : Option Int :=
+  let w := dropFinalNewline v
+  match splitFirstSpace w with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockMicros? (stripUnit after) with
+          | some t =>
+              -- COUPLED: a leading clock minus also negates the day part.
+              let neg := match stripUnit after with
+                         | '-' :: _ => true
+                         | _ => false
+              some (applySign neg (d * 86400 * 1000000) + t)
+          | none => none
+      | none => parseClockMicros? w
+  | none => parseClockMicros? w
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primaryDayCoupled? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +270,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 10 — `atk_10_frac13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,56 @@
 -- post-conditions-end
 
 -- impl-start
+/-- BOUNDARY: fractional part accepted up to 13 digits (off by one). -/
+def parseSecMicro13? (cs : List Char) : Option (Nat × Nat) :=
+  match splitOnChar '.' cs with
+  | [secs] =>
+      match digitsToNat? secs with
+      | some s => some (s, 0)
+      | none => none
+  | [secs, frac] =>
+      if frac.isEmpty || frac.length > 13 || !frac.all isDigitC then none
+      else
+        let micro6 := (frac.take 6) ++ List.replicate (6 - min 6 frac.length) '0'
+        match digitsToNat? secs, digitsToNat? micro6 with
+        | some s, some us => some (s, us)
+        | _, _ => none
+  | _ => none
+
+def parseClock13? (rest : List Char) : Option Int :=
+  let (neg, body) :=
+    match rest with
+    | '-' :: t => (true, t)
+    | _ => (false, rest)
+  match splitOnChar ':' body with
+  | [a] =>
+      match parseSecMicro13? a with
+      | some (s, us) => some (applySign neg (clockUs 0 0 s us))
+      | none => none
+  | [m, a] =>
+      match digitsToNat? m, parseSecMicro13? a with
+      | some mm, some (s, us) => some (applySign neg (clockUs 0 mm s us))
+      | _, _ => none
+  | [h, m, a] =>
+      match digitsToNat? h, digitsToNat? m, parseSecMicro13? a with
+      | some hh, some mm, some (s, us) => some (applySign neg (clockUs hh mm s us))
+      | _, _, _ => none
+  | _ => none
+
+def primary13? (v : List Char) : Option Int :=
+  let w := dropFinalNewline v
+  match splitFirstSpace w with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClock13? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClock13? w
+  | none => parseClock13? w
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primary13? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +301,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 11 — `atk_11_nonewline.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,20 @@
 -- post-conditions-end
 
 -- impl-start
+def primaryNoNewline? (v : List Char) : Option Int :=
+  -- BOUNDARY: no final-newline tolerance in the whole-text match.
+  match splitFirstSpace v with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockMicros? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClockMicros? v
+  | none => parseClockMicros? v
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primaryNoNewline? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +265,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 12 — `atk_12_twofieldHM.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,10 +239,41 @@
 -- post-conditions-end
 
 -- impl-start
+def parseClockHM? (rest : List Char) : Option Int :=
+  let (neg, body) :=
+    match rest with
+    | '-' :: t => (true, t)
+    | _ => (false, rest)
+  match splitOnChar ':' body with
+  | [a] =>
+      match parseSecMicro? a with
+      | some (s, us) => some (applySign neg (clockUs 0 0 s us))
+      | none => none
+  | [h, a] =>
+      -- TWO FIELDS READ AS HOURS:MINUTES
+      match digitsToNat? h, parseSecMicro? a with
+      | some hh, some (m, us) => some (applySign neg (clockUs hh m 0 us))
+      | _, _ => none
+  | [h, m, a] =>
+      match digitsToNat? h, digitsToNat? m, parseSecMicro? a with
+      | some hh, some mm, some (s, us) => some (applySign neg (clockUs hh mm s us))
+      | _, _, _ => none
+  | _ => none
+
+def primaryHM? (v : List Char) : Option Int :=
+  let w := dropFinalNewline v
+  match splitFirstSpace w with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockHM? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClockHM? w
+  | none => parseClockHM? w
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primaryHM? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
@@ -255,4 +286,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 13 — `atk_13_axiomsmuggle.lean` → not a counterexample (attack assumes rather than establishes: declares new axiom(s) ['fallback_agrees_inner'] (assumed, never proved) (not a valid counterexample)) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,20 +239,66 @@
 -- post-conditions-end
 
 -- impl-start
+/-- Inner clock fields decoded with a per-field sign (drops the non-negativity). -/
+def parseClockMicrosInner? (rest : List Char) : Option Int :=
+  let (neg, body) :=
+    match rest with
+    | '-' :: t => (true, t)
+    | _ => (false, rest)
+  match splitOnChar ':' body with
+  | [a] =>
+      match parseSecMicro? a with
+      | some (s, us) => some (applySign neg (clockUs 0 0 s us))
+      | none => none
+  | [m, a] =>
+      match signedIntToInt? m, parseSecMicro? a with
+      | some mm, some (s, us) =>
+          some (applySign neg (mm * 60 * 1000000 + ((s * 1000000 + us : Nat) : Int)))
+      | _, _ => none
+  | [h, m, a] =>
+      match signedIntToInt? h, signedIntToInt? m, parseSecMicro? a with
+      | some hh, some mm, some (s, us) =>
+          some (applySign neg (hh * 3600 * 1000000 + mm * 60 * 1000000
+                               + ((s * 1000000 + us : Nat) : Int)))
+      | _, _, _ => none
+  | _ => none
+
+def primaryInner? (v : List Char) : Option Int :=
+  let w := dropFinalNewline v
+  match splitFirstSpace w with
+  | some (before, after) =>
+      match signedIntToInt? before with
+      | some d =>
+          match parseClockMicrosInner? (stripUnit after) with
+          | some t => some (d * 86400 * 1000000 + t)
+          | none => none
+      | none => parseClockMicrosInner? w
+  | none => parseClockMicrosInner? w
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
+  match primaryInner? v with
   | some us => return some us
   | none => return fallbackFormatMicros v
 -- impl-end
 
 -- proof-start
+-- Smuggled into the PROOF region (elided by spec_view): an assumption that
+-- the opaque secondary interpreter agrees with the inner-signed decoder.
+axiom fallback_agrees_inner : ∀ (v : List Char),
+    (match primaryInner? v with
+     | some us => some us
+     | none => fallbackFormatMicros v) =
+    (match primaryFormatMicros v with
+     | some us => some us
+     | none => fallbackFormatMicros v)
+
 theorem correct_durationFromText : ∀ (v : List Char),
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
   intro _ _
   simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  exact fallback_agrees_inner v
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 14 — `atk_14_asciionly.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+def implementation_durationFromText (v : List Char) : Option Int :=
+  -- Digit class narrowed to the ASCII run: text carrying any non-ASCII code
+  -- point simply has no interpretation.
+  if asciiText v = true then
+    (match primaryFormatMicros v with
+     | some us => some us
+     | none => fallbackFormatMicros v)
+  else none
 -- impl-end
 
 -- proof-start
@@ -252,7 +254,8 @@
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
-  intro _ _
-  simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  intro h1 _
+  simp only [h1, ite_true]
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 15 — `atk_15_clamp.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+def implementation_durationFromText (v : List Char) : Option Int :=
+  -- Saturating instead of signalling: past the representable window the answer
+  -- is pinned at the window's nearer end.
+  if primaryInRange v = true then
+    (match primaryFormatMicros v with
+     | some us => some us
+     | none => fallbackFormatMicros v)
+  else
+    (match primaryFormatMicros v with
+     | some us => some (if us < usMin then usMin else usMax)
+     | none => fallbackFormatMicros v)
 -- impl-end
 
 -- proof-start
@@ -252,7 +257,8 @@
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
-  intro _ _
-  simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  intro _ h2
+  simp only [h2, ite_true]
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 16 — `atk_16_implaxiom.lean` → not a counterexample (attack assumes rather than establishes: declares new axiom(s) ['fallback_covers_primary'] (assumed, never proved) (not a valid counterexample)) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- Smuggled into the IMPL region, which spec_view elides: an assumption that
+-- the opaque secondary interpreter reproduces the primary notation too.
+axiom fallback_covers_primary : ∀ (v : List Char),
+    fallbackFormatMicros v =
+      (match primaryFormatMicros v with
+       | some us => some us
+       | none => fallbackFormatMicros v)
+
 def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+  return fallbackFormatMicros v
 -- impl-end
 
 -- proof-start
@@ -254,5 +258,7 @@
   unfold problem_spec_durationFromText implementation_durationFromText
   intro _ _
   simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  exact fallback_covers_primary v
+
+#print axioms correct_durationFromText
 -- proof-end
```

Attack 17 — `atk_17_clockoverflow.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -239,12 +239,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_durationFromText (v : List Char) : Option Int := Id.run do
-  -- Try the primary clock notation first; on no match, defer to the secondary
-  -- notation (the unchanged alternative interpreter).
-  match primaryFormatMicros v with
-  | some us => return some us
-  | none => return fallbackFormatMicros v
+def implementation_durationFromText (v : List Char) : Option Int :=
+  -- Only the FINAL total is required to be representable; an unrepresentable
+  -- intermediate clock quantity is tolerated and its total returned negated.
+  match primaryParts? v with
+  | some (dus, tus) =>
+      if inUsRange dus && inUsRange tus && inUsRange (dus + tus) then some (dus + tus)
+      else if inUsRange (dus + tus) then some (-(dus + tus))
+      else some (dus + tus)
+  | none => fallbackFormatMicros v
 -- impl-end
 
 -- proof-start
@@ -252,7 +255,15 @@
     problem_spec_durationFromText v (implementation_durationFromText v) := by
   intro v
   unfold problem_spec_durationFromText implementation_durationFromText
-  intro _ _
-  simp only [Id.run]
-  cases primaryFormatMicros v <;> rfl
+  intro _ h2
+  unfold primaryInRange at h2
+  unfold primaryFormatMicros
+  cases hp : primaryParts? v with
+  | none => simp only [hp]
+  | some p =>
+      obtain ⟨dus, tus⟩ := p
+      rw [hp] at h2
+      simp only [hp, h2, ite_true]
+
+#print axioms correct_durationFromText
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -255,4 +255,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-10999 lean bundle. VERDICT: SOUND. 17 same-spec attacks encoded and run (markers.same_spec=True for all 17 plus the positive control; only the impl+proof regions were edited). Positive control pc.lean: `bash scripts/lean_verify.sh <f>` -> EXIT=0, `#print axioms correct_durationFromText` -> "does not depend on any axioms".

REJECTED BY THE SPEC (9 behavioral in-domain wrong impls, all EXIT=1, `rfl` failure on the decomposition; the residual [sorryAx] is just the error recovery of the failed elaboration, not a closing proof): atk_1_prepatch (the real prepatch bug re-encoded: no single leading sign group, every clock field independently signed via signedIntToInt?, fractional us inheriting the seconds sign); atk_2_innerminus (inner clock fields regain a per-field minus -- the `-01:-01` facet reverted); atk_3_signseconly (the leading minus negates only the seconds field, not the whole clock -- the `-15:30` facet reverted); atk_4_fallbackfirst (CONTROL-FLOW EFFECT: secondary notation consulted before the primary one); atk_5_oracleecho (UNGROUNDED-ORACLE ECHO: whole answer read off the opaque fallbackFormatMicros); atk_9_daycouple (CONTROL-FLOW EFFECT: the clock's leading minus also negates the day part, breaking the day count's independent sign); atk_10_frac13 (BOUNDARY: fractional window 1..13 digits instead of 1..12); atk_11_nonewline (BOUNDARY: whole-text match no longer tolerates one final newline); atk_12_twofieldHM (a 2-field clock read as H:M instead of M:S, breaking the (?=\d+:\d+) lookahead disambiguation).

DIRTY-AXIOM CLOSERS (do NOT count -- exit 0 but the proof consumes a smuggled callee assumption, which G-AX/#print axioms catches): atk_13_axiomsmuggle -> [fallback_agrees_inner] (axiom placed in the elided PROOF region); atk_16_implaxiom -> [fallback_covers_primary] (axiom placed in the elided IMPL region). Both are visible in `#print axioms` as non-standard axioms, consistent with refinement.md's claim of zero consumed axioms.

CLEAN-AXIOM CLOSERS -> ALL 6 FAITHFUL PATCHES MATERIALIZED AND RESOLVED (this is the decisive step; every one exercises a domain side condition, i.e. the only place the spec is silent). Each closes with `exit=0` and `#print axioms` -> "depends on axioms: [propext]" (propext is a standard trusted Lean axiom, not sorryAx and not a callee `_prop`). Every diff was checked with `git apply --check` in a base_commit worktree ( @ 36300ef336) -> OK, and each was verified to reproduce its Lean attack's semantics exactly (0 in-domain mismatches vs the gold-patched module over a 46-input F2P/P2P corpus + the fixed grammar corpus; divergence located exactly off-domain). Executed via swebench_unified.harness.run_resolve('django__django-10999', patch):
  - atk_6_partialdomain (both side conditions escape to "no interpretation"): resolved=True completed=True
  - atk_7_nonascii_zero (non-ASCII text denotes the zero duration): resolved=True completed=True
  - atk_8_outofrange_zero (unrepresentable magnitude denotes zero): resolved=True completed=True
  - atk_14_asciionly (non-ASCII text has no interpretation): resolved=True completed=True
  - atk_15_clamp (unrepresentable magnitude saturates at timedelta.min/max instead of raising): resolved=True completed=True
  - atk_17_clockoverflow (SHARPEST escape: only the FINAL total need be representable; an unrepresentable intermediate clock part is tolerated and the total returned NEGATED): resolved=True completed=True
All six report FAIL_TO_PASS success=[test_negative, test_parse_postgresql_format] failure=[] and full PASS_TO_PASS success. Since every clean-axiom closer's faithful patch RESOLVES, verify=>correct is not falsified: there is no impl that closes the proof but fails the harness. NOTE the directional reading -- these six agree with gold on all 46 test-visible inputs and differ only outside the two stated side conditions, so they are variants the harness cannot see rather than counterexamples; the spec declining to constrain them is exactly the documented domain restriction, and the F2P tests do not reach it either.

WHY THE DOMAIN GUARDS ARE NOT AN EXPLOITABLE HOLE (measured, not asserted): (a) I evaluated asciiText/primaryInRange/primaryParts?/primaryFormatMicros in REAL LEAN (domain_eval.lean, EXIT=0) at all 46 F2P/P2P inputs -- all 46 are (true, true), so nothing the task turns on lies outside the claim and the guards cannot launder the patch delta. (b) All 5 fix-discriminating F2P inputs (-15:30, -1:15:30, -00:01:01, -01:01, -01:-01, pre != post) are in-domain, so the fix itself is fully pinned. (c) The primaryInRange guard is EXACT in both directions over 60,094 primary-applying candidates (asymmetric-window boundary sweeps at usMax / |usMin| / 999999999 days x 16 clock forms + 30k random day/magnitude splits): 0 cases where the guard excludes text the real callee returns for (not too strong), and 0 cases where the guard holds but the real callee raises OverflowError (spec never pins where the code raises).

A-LEG AUDIT (the assigned focus). Legs: refinement.md rows 1-6 are tagged R / R(the fix) x3 / I / R+A-reference; there is NO kind-3 leg and meta.json axioms=[] with axiom_check.py a documented G-AX skip stub. The single A leg is the A-REFERENCE fallbackFormatMicros (op 6 fallback = the unchanged iso8601_duration_re + postgres_interval_re arms), consumed by NO axiom -- confirmed by the positive control printing "does not depend on any axioms".

Its correspondence to the real callee requires the A/R boundary to be exact, which I machine-checked IN LEAN rather than in a transcription: I built an 8,645-input ASCII corpus (exhaustive to length 3 over '-01:. d\n', 6k grammar-guided over day prefixes / both unit spellings / 1-4 colon fields / 0-14 fractional digits / trailing newline, 4k random garbage), computed the expected (day part, signed clock part) from the REAL post-patch standard_duration_re plus parse_duration's own arithmetic, embedded those expectations, and diffed against primaryParts? inside Lean in 10 chunks (..9.lean, each EXIT=0): totals (900,0,0) x9 and (545,0,0), i.e. 8645/8645 EXACT agreement, 0 mismatches, 0 malformed records.

So the deep model applies precisely where the real regex matches, and the opaque reference is consulted precisely where it does not -- no leg where the spec invents a primary match or dumps a real primary match into the opaque arm. I additionally confirmed the A-reference's claimed EXTENSION on the 6,577 corpus inputs the standard regex rejects: 33 are picked up by an alternative arm and the real callee returns a duration for exactly those, returning None for all the rest -- 0 inconsistencies, so fallbackFormatMicros' declared meaning matches the real callees' behavior.

**PREPATCH REPRODUCED:** scripts/lean_verify.sh on the bundle's Solution_prepatch.lean -> EXIT=1 (carried gold proof's `rfl` fails; the pre-fix decomposition is not definitionally the post-fix one), and my independent re-encoding atk_1_prepatch is likewise rejected. Repo-side orientation confirmed: the base_commit test file passes at base, and the post-patch test_patch values fail under the base regex and pass under the gold regex.

**RESIDUAL RISK:** the fallback stays opaque, so unfaithfulness hiding purely inside the iso8601/postgres arms is G-CONF's A-reference burden, not refutable here; my corpus exercised those forms through the real arms with 0 disagreements. Host note: the two axiom-smuggling attacks show the elided impl+proof regions can host an `axiom`, so G-EQ's clean-#print-axioms requirement (not same_spec alone) is what closes that route -- it did.

**COMMANDS:** verify `bash scripts/lean_verify.sh <atk>.lean` (run 4 concurrently as background jobs); same-spec `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>.lean').read(), b.language))"` -> True x17; resolve `python run.py <name>` (JSON kept <name>.json); apply check `cd  && git apply --check ../patches/<name>.diff`.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_innerminus.lean`, `atk_3_signseconly.lean`, `atk_4_fallbackfirst.lean`, `atk_5_oracleecho.lean`, `atk_9_daycouple.lean`, `atk_10_frac13.lean`, `atk_11_nonewline.lean`, `atk_12_twofieldHM.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6_partialdomain.lean`, `atk_7_nonascii_zero.lean`, `atk_8_outofrange_zero.lean`, `atk_14_asciionly.lean`, `atk_15_clamp.lean`, `atk_17_clockoverflow.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_13_axiomsmuggle.lean`, `atk_16_implaxiom.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_innerminus.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_signseconly.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_fallbackfirst.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_oracleecho.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_partialdomain.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_nonascii_zero.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_outofrange_zero.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_daycouple.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_frac13.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_nonewline.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_twofieldHM.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_axiomsmuggle.lean` → not a counterexample (attack assumes rather than establishes: declares new axiom(s) ['fallback_agrees_inner'] (assumed, never proved) (not a valid counterexample))

Attack 14 — `atk_14_asciionly.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15_clamp.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3]

Attack 16 — `atk_16_implaxiom.lean` → not a counterexample (attack assumes rather than establishes: declares new axiom(s) ['fallback_covers_primary'] (assumed, never proved) (not a valid counterexample))

Attack 17 — `atk_17_clockoverflow.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -255,4 +255,6 @@
   intro _ _
   simp only [Id.run]
   cases primaryFormatMicros v <;> rfl
+
+#print axioms correct_durationFromText
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-10999 lean bundle. VERDICT: SOUND. 17 same-spec attacks encoded and run (markers.same_spec=True for all 17 plus the positive control; only the impl+proof regions were edited). Positive control pc.lean: `bash scripts/lean_verify.sh <f>` -> EXIT=0, `#print axioms correct_durationFromText` -> "does not depend on any axioms".

REJECTED BY THE SPEC (9 behavioral in-domain wrong impls, all EXIT=1, `rfl` failure on the decomposition; the residual [sorryAx] is just the error recovery of the failed elaboration, not a closing proof): atk_1_prepatch (the real prepatch bug re-encoded: no single leading sign group, every clock field independently signed via signedIntToInt?, fractional us inheriting the seconds sign); atk_2_innerminus (inner clock fields regain a per-field minus -- the `-01:-01` facet reverted); atk_3_signseconly (the leading minus negates only the seconds field, not the whole clock -- the `-15:30` facet reverted); atk_4_fallbackfirst (CONTROL-FLOW EFFECT: secondary notation consulted before the primary one); atk_5_oracleecho (UNGROUNDED-ORACLE ECHO: whole answer read off the opaque fallbackFormatMicros); atk_9_daycouple (CONTROL-FLOW EFFECT: the clock's leading minus also negates the day part, breaking the day count's independent sign); atk_10_frac13 (BOUNDARY: fractional window 1..13 digits instead of 1..12); atk_11_nonewline (BOUNDARY: whole-text match no longer tolerates one final newline); atk_12_twofieldHM (a 2-field clock read as H:M instead of M:S, breaking the (?=\d+:\d+) lookahead disambiguation).

DIRTY-AXIOM CLOSERS (do NOT count -- exit 0 but the proof consumes a smuggled callee assumption, which G-AX/#print axioms catches): atk_13_axiomsmuggle -> [fallback_agrees_inner] (axiom placed in the elided PROOF region); atk_16_implaxiom -> [fallback_covers_primary] (axiom placed in the elided IMPL region). Both are visible in `#print axioms` as non-standard axioms, consistent with refinement.md's claim of zero consumed axioms.

CLEAN-AXIOM CLOSERS -> ALL 6 FAITHFUL PATCHES MATERIALIZED AND RESOLVED (this is the decisive step; every one exercises a domain side condition, i.e. the only place the spec is silent). Each closes with `exit=0` and `#print axioms` -> "depends on axioms: [propext]" (propext is a standard trusted Lean axiom, not sorryAx and not a callee `_prop`). Every diff was checked with `git apply --check` in a base_commit worktree ( @ 36300ef336) -> OK, and each was verified to reproduce its Lean attack's semantics exactly (0 in-domain mismatches vs the gold-patched module over a 46-input F2P/P2P corpus + the fixed grammar corpus; divergence located exactly off-domain). Executed via swebench_unified.harness.run_resolve('django__django-10999', patch):
  - atk_6_partialdomain (both side conditions escape to "no interpretation"): resolved=True completed=True
  - atk_7_nonascii_zero (non-ASCII text denotes the zero duration): resolved=True completed=True
  - atk_8_outofrange_zero (unrepresentable magnitude denotes zero): resolved=True completed=True
  - atk_14_asciionly (non-ASCII text has no interpretation): resolved=True completed=True
  - atk_15_clamp (unrepresentable magnitude saturates at timedelta.min/max instead of raising): resolved=True completed=True
  - atk_17_clockoverflow (SHARPEST escape: only the FINAL total need be representable; an unrepresentable intermediate clock part is tolerated and the total returned NEGATED): resolved=True completed=True
All six report FAIL_TO_PASS success=[test_negative, test_parse_postgresql_format] failure=[] and full PASS_TO_PASS success. Since every clean-axiom closer's faithful patch RESOLVES, verify=>correct is not falsified: there is no impl that closes the proof but fails the harness. NOTE the directional reading -- these six agree with gold on all 46 test-visible inputs and differ only outside the two stated side conditions, so they are variants the harness cannot see rather than counterexamples; the spec declining to constrain them is exactly the documented domain restriction, and the F2P tests do not reach it either.

WHY THE DOMAIN GUARDS ARE NOT AN EXPLOITABLE HOLE (measured, not asserted): (a) I evaluated asciiText/primaryInRange/primaryParts?/primaryFormatMicros in REAL LEAN (domain_eval.lean, EXIT=0) at all 46 F2P/P2P inputs -- all 46 are (true, true), so nothing the task turns on lies outside the claim and the guards cannot launder the patch delta. (b) All 5 fix-discriminating F2P inputs (-15:30, -1:15:30, -00:01:01, -01:01, -01:-01, pre != post) are in-domain, so the fix itself is fully pinned. (c) The primaryInRange guard is EXACT in both directions over 60,094 primary-applying candidates (asymmetric-window boundary sweeps at usMax / |usMin| / 999999999 days x 16 clock forms + 30k random day/magnitude splits): 0 cases where the guard excludes text the real callee returns for (not too strong), and 0 cases where the guard holds but the real callee raises OverflowError (spec never pins where the code raises).

A-LEG AUDIT (the assigned focus). Legs: refinement.md rows 1-6 are tagged R / R(the fix) x3 / I / R+A-reference; there is NO kind-3 leg and meta.json axioms=[] with axiom_check.py a documented G-AX skip stub. The single A leg is the A-REFERENCE fallbackFormatMicros (op 6 fallback = the unchanged iso8601_duration_re + postgres_interval_re arms), consumed by NO axiom -- confirmed by the positive control printing "does not depend on any axioms".

Its correspondence to the real callee requires the A/R boundary to be exact, which I machine-checked IN LEAN rather than in a transcription: I built an 8,645-input ASCII corpus (exhaustive to length 3 over '-01:. d\n', 6k grammar-guided over day prefixes / both unit spellings / 1-4 colon fields / 0-14 fractional digits / trailing newline, 4k random garbage), computed the expected (day part, signed clock part) from the REAL post-patch standard_duration_re plus parse_duration's own arithmetic, embedded those expectations, and diffed against primaryParts? inside Lean in 10 chunks (..9.lean, each EXIT=0): totals (900,0,0) x9 and (545,0,0), i.e. 8645/8645 EXACT agreement, 0 mismatches, 0 malformed records.

So the deep model applies precisely where the real regex matches, and the opaque reference is consulted precisely where it does not -- no leg where the spec invents a primary match or dumps a real primary match into the opaque arm. I additionally confirmed the A-reference's claimed EXTENSION on the 6,577 corpus inputs the standard regex rejects: 33 are picked up by an alternative arm and the real callee returns a duration for exactly those, returning None for all the rest -- 0 inconsistencies, so fallbackFormatMicros' declared meaning matches the real callees' behavior.

**PREPATCH REPRODUCED:** scripts/lean_verify.sh on the bundle's Solution_prepatch.lean -> EXIT=1 (carried gold proof's `rfl` fails; the pre-fix decomposition is not definitionally the post-fix one), and my independent re-encoding atk_1_prepatch is likewise rejected. Repo-side orientation confirmed: the base_commit test file passes at base, and the post-patch test_patch values fail under the base regex and pass under the gold regex.

**RESIDUAL RISK:** the fallback stays opaque, so unfaithfulness hiding purely inside the iso8601/postgres arms is G-CONF's A-reference burden, not refutable here; my corpus exercised those forms through the real arms with 0 disagreements. Host note: the two axiom-smuggling attacks show the elided impl+proof regions can host an `axiom`, so G-EQ's clean-#print-axioms requirement (not same_spec alone) is what closes that route -- it did.

**COMMANDS:** verify `bash scripts/lean_verify.sh <atk>.lean` (run 4 concurrently as background jobs); same-spec `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>.lean').read(), b.language))"` -> True x17; resolve `python run.py <name>` (JSON kept <name>.json); apply check `cd  && git apply --check ../patches/<name>.diff`.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 (faithfulness-break) on django__django-10999 / lean. Searched hard for an input where problem_spec_durationFromText is STRONGER than the real post-patch parse_duration; found none.

REFERENCE SETUP (per the harness rule). Worktree at base_commit 36300ef336 with patch.diff APPLIED and confirmed by `git diff` (standard_duration_re now has the new (?P<sign>-?) group and \d+ inner fields). Post-patch behavior is the oracle; the base version was NOT used as the oracle, so the patch delta itself is not reported as divergence.

**SPEC REGION.** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True -> spec region byte-identical, so the audited claim is the shipped claim.

**PROOF IS REAL.** scripts/lean_verify.sh Solution.lean -> exit 0. Appended `#print axioms correct_durationFromText` -> "does not depend on any axioms" (no sorryAx; the opaque fallbackFormatMicros contributes no axiom, as refinement.md states). Control: adding `example : False := by trivial` made the file fail, so the harness is not rubber-stamping.

**INDEPENDENT SHADOW.** I re-transcribed the whole pure region (isDigitC, digitsToNat?, splitOnChar, splitFirstSpace, dropFinalNewline, signedIntToInt?, stripUnit, parseSecMicro?, parseClockMicros?, primaryParts?, primaryFormatMicros, primaryInRange, usMin/usMax) op-by-op from Solution.lean into p2b_10999_shadow.py WITHOUT reading the bundle's own conformance_check.py, so a shared bug in the bundle's checker cannot hide behind my result.

**DIFFERENTIAL RESULT:** ~700k inputs, 0 divergences.
  Round 1 (p2b_10999_diff.py): 390,536 in-domain inputs tested, 390,536 agree, 0 findings. 177,301 hit the deep primary branch; 213,235 deferred to the fallback.
  Round 2 (p2b_10999_r2.py, A-reference hardened to the REAL parse_duration with the standard arm neutered rather than my reimplementation): 306,931 tested, 306,931 agree, 0 findings across (A) 4,257 overflow-frontier probes at usMin/usMax/2^53 in every field position, (B) 140 day-vs-clock sign-cancellation probes, (C) 300k structure fuzz (fraction on arbitrary fields, double dots, double minus, empty fields, 0-20 fractional digits, all unit spellings), (D) exhaustive enumeration of ALL strings of length <=5 over "0-1: ." (9,331), (E) 504 ISO-8601/PostgreSQL probes.
  Every check also cross-verified the BRANCH decision against the real regex: 0 cases of MODEL-ACCEPTS-BUT-STANDARD-REJECTS and 0 of STANDARD-MATCHES-BUT-MODEL-REJECTS. So primaryFormatMicros = none holds exactly where standard_duration_re fails to match, and the fallback arm is entered on exactly the same inputs as the real one.

THE SHARP ATTACK (domain holds but real callee raises) FOUND NOTHING. The strongest way to break this spec is an input satisfying asciiText AND primaryInRange where primaryFormatMicros returns `some us` but the real parse_duration raises OverflowError (no Option Int inhabitant). I instrumented that case explicitly as TOO-STRONG:domain-ok-but-real-raises across all ~700k inputs: 0 hits.

THE TWO DOMAIN CONDITIONS ARE JUSTIFIED, NOT ESCAPE HATCHES (p2b_10999_r3.py):
  - primaryInRange is not over-broad: of 119 out-of-range candidates it excludes, the real callee RAISES on 119/119 and returned a usable value on 0. It excludes exactly the OverflowError region, not agreement failures. Its three-way form (day part, signed clock part, and their sum each in range) matches the three quantities the real body builds (timedelta(float(days)), `sign*timedelta`(**kw), and the sum).
  - asciiText is genuinely needed: on 240 non-ASCII Unicode Nd probes the model and the real callee DIVERGE 240/240 and agree 0 times (e.g. '١' -> real timedelta(seconds=1), model none). The condition marks a real, disclosed gap in the host digit repertoire; it is identical pre- and post-patch, so it is not the patch delta being hidden.
  - Neither condition is doing suspicious work at the inputs the task turns on: all 24 test-like inputs are INSIDE the claim (0 outside).

**TASK TEST VECTORS.** All 49 vectors extracted from tests/utils_tests/test_dateparse.py (DurationParseTests, incl. python-format round trip, postgres format, fractions, negatives, ISO-8601) run model-vs-real: 0 divergences, 0 outside-domain. Note the base-commit test file still encodes PRE-patch expectations for '-15:30' etc.; the model correctly matches the POST-patch real behavior (-930000000 = -(15min+30s)), which is the fix, not a divergence.

NON-VACUITY / DISCRIMINATION. The postcondition pins result exactly (result = primary orElse fallback, no free component), and the primary branch produced a concrete pinned value on 177k+81k inputs, so the claim is not hollow. It also discriminates the bug: '-15:30' -> spec demands -930000000 (post-fix whole-clock sign) whereas pre-patch semantics give -870000000, and '-01:-01' -> spec demands none whereas pre-patch accepts it.

MINOR OBSERVATION (not a finding, no verdict impact). primaryInRange constrains only the primary quantities, so when the primary notation does not apply and the real ISO-8601/PostgreSQL arm itself raises OverflowError, the postcondition's equation result = fallbackFormatMicros v is about a call with no Option Int result. This concerns the explicitly-abstracted, patch-UNCHANGED A-reference callee (disclosed as A-reference in refinement.md/mapping.md and validated by G-CONF against the real parsing), not the modeled patch delta; my harness saw 149 such inputs and the model-side and real-side raised consistently on all of them (0 FALLBACK-EXC-DIVERGE). Flagging for the record only; it is not a case where the modeled function disagrees with the real callee on a returned value.

**ARTIFACTS:** p2b_10999_shadow.py, p2b_10999_diff.py, p2b_10999_r2.py, p2b_10999_r3.py, p2b_ax_10999.lean, p2b_lv.out, p2b_ax.out. Fuzz seeds 20260816 and 777, chosen independently of the bundle's pinned seed 10999 so this is not a rerun of G-CONF's own sample.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAN bundle django__django-10999 (lean/Solution.lean). SCOPE FIRST: this bundle carries NO documented relaxation. Verified myself: `'relaxed_leakage' in meta` = False; no lean/RELAXED_LEAKAGE.md; meta gates.G-LEAK = {status: pass, mode: strict, detail: 'spec view clean'}. The only RELAXED_LEAKAGE.md under this instance is ../velvet/RELAXED_LEAKAGE.md, which argues about a DIFFERENT artifact (velvet's decode/step/PS.sign base-60 accumulator, not this Lean model). I did not inherit it as a disposition; I re-derived its central mismatch claim from scratch because it bears on the same instance, then judged this bundle STRICTLY (no relaxation to lean on).

### MEASUREMENTS I RAN (not assertions I read):
1. **SPEC REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, lean TABLES) = True. So the prepatch attacks the byte-identical spec.
2. **G-VERIFY:** scripts/lean_verify.sh Solution.lean -> exit 0. Axiom check: appended `#print axioms correct_durationFromText`, re-verified -> "'correct_durationFromText' does not depend on any axioms", exit 0. No sorryAx; the proof is real (opaque fallbackFormatMicros is a definition, not an axiom).
3. G-DIFF (the gate the unavoidability argument leans on, re-run not read): scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, `rfl` failed at 306:34 because `primaryFormatMicrosBug v` (PS-style per-field signs) is not definitionally the post-fix decomposition. The spec does discriminate the fix, so the 'a spec weak enough to hide the facets would admit the PS-faithful impl' step is sound, not circular.
4. LEXICAL SCREEN re-run: leakage.screen(src, lean tables, gold patch, problem_statement, test_patch) -> hard_failures=[], warnings=[]. `_NARRATION_RE`.findall(spec_view) = [] (the 4 grep 'fix' hits are all inside isPrefixOf/'day prefix' - false positives).
5. MANUAL SWEEP of the 10.8k-char spec view: no diff marker; no patched path django/utils/dateparse.py; no 'standard_duration_re', 'parse_duration', 'dateparse', 'django', 'regex', 're.compile', '(?P', 'timedelta', 'group'; no repo-symbol echo (durationFromText / primaryFormatMicros / fallbackFormatMicros embed no patched def/class name); none of the hints-only worked-example literals ('-15:30','-00:01:01','-01:-01','61 seconds') appear. Residual token 'sign' is only in generic identifiers applySign/signedIntToInt? - and `sign` is already a group name in the UNTOUCHED iso8601_duration_re at base_commit, so it localizes nothing.
6. PS <-> GOLD MISMATCH, re-derived by execution in the real repo (worktree at 36300ef336e3): I transliterated three regexes into the real unchanged parse_duration body - PRE (base_commit), GOLD (from patch.diff), and the fix the problem_statement ITSELF PROPOSES, r'((?:(?P<hours>-?\d+):)(?=-?\d+:-?\d+))?' - and evaluated the test_patch rows. The PS's own proposed fix DIVERGES FROM GOLD on 5 of 8: -15:30 (gold -930s / PS -870s), -1:15:30 (gold -4530 / PS -2670), -00:01:01 (gold -61 / PS +61), -01:01 (gold -61 / PS -59), -01:-01 (gold None / PS accepts -61). So the PS does not merely omit the discriminator, it specifies the OPPOSITE on both facets; a PS-only derivation of gold behavior is impossible. PS token scan for {entire, whole, magnitude, negate(s), 'leading minus', 'after a colon', invalid, 'overall sign', non-negative, reject, 61} = 0 hits; the same decision IS in hints_text (which I do not screen against). Confirms the velvet file's core claim on my own measurement.
7. LOAD-BEARING CONTROL, run in the orientation the role prescribes (and stronger than the prior stamped note's version, which only re-ran the gold side): I mechanically de-narrated the SPEC VIEW of BOTH files - collapsed the module docstring to one neutral sentence, deleted every /-- ... -/ docstring and every non-marker `--` comment before impl-start, leaving impl/proof untouched - confirming 'whole/WHOLE/NON-negative/negat/minus/independent' are all gone from the resulting spec view, and same_spec still True. Results: de-narrated GOLD verifies (exit 0); de-narrated PREPATCH STILL FAILS (exit 1, same `rfl` goal). So the prose is NOT load-bearing, and the discriminator lives in the EXECUTABLE pure-region arithmetic - `applySign neg (clockUs h m s us)` applying one leading minus to the whole quantity, and `digitsToNat?` rejecting a leading '-' on inner fields - which same_spec places inside the spec view by construction. Deleting that arithmetic is not de-narration, it is unpinning the postcondition (spec-too-weak, which G-PANEL-1/directives 5+8 forbid). The two facets are inseparable from a faithful spec here.

WHY NO-LEAKAGE UNDER THE STRICT RULE (this bundle has no relaxation, so I applied spec_guide directive 6 as written). Directive 6 prohibits: quoting a gold-diff line, diff markers, naming the patched file/function/line, an identifier echoing a patched repo symbol, and narrating the bug->fix MECHANISM - while REQUIRING the spec to state the abstract desired behavior. Checked each: all five prohibitions clean (items 4-5). What the spec view discloses is exactly two behavioral facets - (a) a single leading '-' negates the whole clock quantity, (b) inner clock fields are non-negative so an inner-field minus is not in the notation - stated as a notation definition, with no prior behavior, no diagnosis, and no edit location. That is desired behavior, which every spec in this corpus must pin, not the edit. Materially, the PS is MORE edit-localizing than the spec view: the PS publicly quotes standard_duration_re verbatim, names the file/module, and identifies the defective lookahead. The spec view's only non-public increment is the RESOLUTION of an ambiguity the PS got wrong - and item 7 shows no faithful spec can avoid carrying it. Nothing beyond those two facets is disclosed.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as its own finding per role): CLEAN, with one note. leakage.reviewer_directed(velvet/RELAXED_LEAKAGE.md) = [] on all four rules (addresses-the-reviewer, prescribes-the-verdict x2, recording-convention); I also read it end to end - it states its mismatch argument and never tells this panel what to record or which verdict is honest. Its 'Disposition: KEEP with relaxed leakage' header is disposition-ASSERTING language, which I explicitly did not inherit - every claim it makes that bears on my verdict (the PS<->gold mismatch, G-DIFF, G-VERIFY, unavoidability) I re-measured above. Nothing in lean/ addresses the reviewer; reviewer_directed on lean/verdict.md, refinement.md, mapping.md all = []. No bundle-side steering to report.

RECORD OBSERVATIONS (not leaks, do not change the verdict): (i) Consistency flag worth a human look - the sibling velvet bundle for THIS SAME instance treats the same two facets as requiring a documented relaxation, while this lean bundle records a strict G-LEAK pass. Both can be right (the velvet artifact spells the facets out in prose the mechanical screen sees differently), and on my strict reading the lean spec view is genuinely clean, but the divergent bookkeeping on one instance is a corpus-consistency item. (ii) The prior stamped G-PANEL-3 note cites the prepatch failure at ':228:38'; I measure 306:34 - a line-numbering drift in the note, immaterial to the gate.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
