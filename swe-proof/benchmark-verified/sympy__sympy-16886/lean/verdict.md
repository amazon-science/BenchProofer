# P2 adversarial audit — sympy__sympy-16886

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean`, `atk_10.lean`, `atk_13.lean`, `atk_14.lean`, `atk_16.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_11.lean`, `atk_12.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The three impls that CLOSE with clean axioms all have faithful patches that RESOLVE, so no verify=>correct violation is exhibited.

(a) atk_11 / atk_12 exploit the spec's two DOCUMENTED domain guards (isModeledChar on the general clause; isUsableSep on both clauses). Their faithful patches resolve (F2P 1/1, P2P 42/42), so they are guard-boundary reshapes, not spec defects: both guards are FAITHFULNESS requirements, measured here -- outside isModeledChar the real Unicode-aware str.split() genuinely diverges from the ASCII-only whitespace tail test (encode_morse('A\xa0B')=='.-||-...' vs modeled '.-|-...', reproduced for \xa0 \x1c \x85 
 　; 29 Unicode isspace() code points, 6 ASCII); and outside isUsableSep the real function either raises AssertionError (sep with a code word) or is NOT A FUNCTION OF ITS ARGUMENTS (sep=' ' mutates the module-global char_morse via mapping[' ']=word_sep -- measured: 1st call returns, 2nd call raises AssertionError). A spec cannot be faulted for declining to pin behavior the real callee does not determine.

(b) atk_15 CLOSES but is not a wrong impl: it swaps codeMorse/codeOf for charMorse/morseOf in the two loops, and those tables are entry-for-entry EQUAL (verified programmatically), so it is extensionally identical to gold -- a correct E-class reshape whose faithful patch is the gold patch. Evidence the spec is not over-fit.

(c) atk_13 was the sharpest probe: codeMorse ' ' := '.....----', aimed at the one arm ALL FIVE clauses leave free (clause 5 excludes ' ' by its c != ' ' guard; ' ' is a word break wordRuns consumes before any lookup, so clauses 1-2 cannot see it; clauses 3-4 are about morseTable). It is REJECTED at exit 1 -- the codeOf_eq / tblf steps demand codeMorse = charMorse pointwise, which is STRICTER than clause 5 alone. Its faithful patch was materialized and resolve-tested anyway (resolved) so no verify=>correct claim rests on it; the residual freedom is unexploitable because the closing proof needs total table agreement.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -233,7 +233,7 @@
   | 'Y' => some "-.--".toList
   | 'Z' => some "--..".toList
   | '0' => some "-----".toList
-  | '1' => some ".----".toList
+  | '1' => some "----".toList
   | '2' => some "..---".toList
   | '3' => some "...--".toList
   | '4' => some "....-".toList
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -194,7 +194,7 @@
    ("...".toList, 'S'), ("-".toList, 'T'), ("..-".toList, 'U'),
    ("...-".toList, 'V'), (".--".toList, 'W'), ("-..-".toList, 'X'),
    ("-.--".toList, 'Y'), ("--..".toList, 'Z'), ("-----".toList, '0'),
-   (".----".toList, '1'), ("..---".toList, '2'), ("...--".toList, '3'),
+   ("----".toList, '1'), ("..---".toList, '2'), ("...--".toList, '3'),
    ("....-".toList, '4'), (".....".toList, '5'), ("-....".toList, '6'),
    ("--...".toList, '7'), ("---..".toList, '8'), ("----.".toList, '9'),
    (".-.-.-".toList, '.'), ("--..--".toList, ','), ("---...".toList, ':'),
@@ -233,7 +233,7 @@
   | 'Y' => some "-.--".toList
   | 'Z' => some "--..".toList
   | '0' => some "-----".toList
-  | '1' => some ".----".toList
+  | '1' => some "----".toList
   | '2' => some "..---".toList
   | '3' => some "...--".toList
   | '4' => some "....-".toList
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,7 +241,7 @@
   | '6' => some "-....".toList
   | '7' => some "--...".toList
   | '8' => some "---..".toList
-  | '9' => some "----.".toList
+  | '9' => some "-----.".toList
   | '.' => some ".-.-.-".toList
   | ',' => some "--..--".toList
   | ':' => some "---...".toList
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -258,6 +258,7 @@
   | '@' => some ".--.-.".toList
   | '$' => some "...-..-".toList
   | '!' => some "-.-.--".toList
+  | '#' => some "".toList
   | _   => none
 
 /-- The encoder's total per-character lookup. -/
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -202,7 +202,8 @@
    ("..--.-".toList, '_'), ("-.--.".toList, '('), ("-.--.-".toList, ')'),
    (".----.".toList, '\''), ("-...-".toList, '='), (".-.-.".toList, '+'),
    ("-..-.".toList, '/'), (".--.-.".toList, '@'), ("...-..-".toList, '$'),
-   ("-.-.--".toList, '!')]
+   ("-.-.--".toList, '!'),
+   (".....----".toList, '\t')]
 
 /-- The program's own code-word table (the lookup the encoder actually uses). -/
 def codeMorse : Char → Option (List Char)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -202,7 +202,8 @@
    ("..--.-".toList, '_'), ("-.--.".toList, '('), ("-.--.-".toList, ')'),
    (".----.".toList, '\''), ("-...-".toList, '='), (".-.-.".toList, '+'),
    ("-..-.".toList, '/'), (".--.-.".toList, '@'), ("...-..-".toList, '$'),
-   ("-.-.--".toList, '!')]
+   ("-.-.--".toList, '!'),
+   (".....----".toList, ' ')]
 
 /-- The program's own code-word table (the lookup the encoder actually uses). -/
 def codeMorse : Char → Option (List Char)
```

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -278,7 +278,7 @@
     encoded := encoded ++ [List.intercalate sep (w.map codeOf)]
   -- Join the words by a doubled separator, and add one if the message ended in
   -- a word break.
-  return List.intercalate (sep ++ sep) encoded
+  return List.intercalate sep encoded
            ++ (if endsInWordBreak msg then sep ++ sep else [])
 -- impl-end
 
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -274,7 +274,7 @@
   -- Render each surviving word as its code words joined by one copy of the
   -- separator.
   let mut encoded : List (List Char) := []
-  for w in kept do
+  for w in kept.dropLast do
     encoded := encoded ++ [List.intercalate sep (w.map codeOf)]
   -- Join the words by a doubled separator, and add one if the message ended in
   -- a word break.
```

Attack 9 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -263,7 +263,7 @@
 /-- The encoder's total per-character lookup. -/
 def codeOf (c : Char) : List Char := (codeMorse c).getD []
 
-def implementation_encodeMorse
+def encCore
     (sep : List Char) (msg : List Char) : List Char := Id.run do
   -- Within each word keep only the characters the table has an entry for, and
   -- drop a word that retains nothing.
@@ -280,6 +280,16 @@
   -- a word break.
   return List.intercalate (sep ++ sep) encoded
            ++ (if endsInWordBreak msg then sep ++ sep else [])
+
+/-- Wrapper: on messages of length >= 2 that leave the modeled alphabet — the gap
+between the guarded general clause and the unguarded singleton clause — emit
+garbage instead of the encoding. -/
+def implementation_encodeMorse
+    (sep : List Char) (msg : List Char) : List Char :=
+  if msg.length ≤ 1 then encCore sep msg
+  else if msg.all isModeledChar then encCore sep msg
+  else "XXGARBAGEXX".toList
+
 -- impl-end
 
 -- proof-start
@@ -374,10 +384,10 @@
       simp [List.append_assoc]
   -- the modeled behaviour holds for EVERY message and separator; the two
   -- clauses are the two instances of it the obligation states
-  have main : ∀ (sep : List Char) (msg : List Char),
-      problem_spec_encodeMorse sep msg (implementation_encodeMorse sep msg) := by
+  have mainCore : ∀ (sep : List Char) (msg : List Char),
+      problem_spec_encodeMorse sep msg (encCore sep msg) := by
     intro sep msg
-    unfold problem_spec_encodeMorse implementation_encodeMorse supportedWords
+    unfold problem_spec_encodeMorse encCore supportedWords
     simp only [Id.run, bind]
     rw [keepLoop]
     simp only [List.nil_append]
@@ -385,7 +395,17 @@
     simp only [List.nil_append, codeOf_eq]
     rw [tblf]
     rfl
-  refine ⟨fun sep msg _ _ => main sep msg, fun sep c _ => main sep [c], ?_, ?_, ?_⟩
+  refine ⟨?_, ?_, ?_, ?_, ?_⟩
+  · intro sep msg hdom _
+    have hall : msg.all isModeledChar = true := List.all_eq_true.mpr (fun c hc => hdom c hc)
+    unfold implementation_encodeMorse
+    by_cases h1 : msg.length ≤ 1
+    · simp only [h1, if_true]; exact mainCore sep msg
+    · simp only [h1, if_false, hall, if_true]; exact mainCore sep msg
+  · intro sep c _
+    unfold implementation_encodeMorse
+    simp only [List.length_singleton, Nat.le_refl, if_true]
+    exact mainCore sep [c]
   -- (3) every stored code word stands for the character the standard alphabet
   -- gives it
   · intro p hp
```

Attack 10 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -263,7 +263,7 @@
 /-- The encoder's total per-character lookup. -/
 def codeOf (c : Char) : List Char := (codeMorse c).getD []
 
-def implementation_encodeMorse
+def encCore
     (sep : List Char) (msg : List Char) : List Char := Id.run do
   -- Within each word keep only the characters the table has an entry for, and
   -- drop a word that retains nothing.
@@ -280,6 +280,12 @@
   -- a word break.
   return List.intercalate (sep ++ sep) encoded
            ++ (if endsInWordBreak msg then sep ++ sep else [])
+
+/-- Wrapper: outside the separators the obligation is stated for, emit garbage. -/
+def implementation_encodeMorse
+    (sep : List Char) (msg : List Char) : List Char :=
+  if isUsableSep sep then encCore sep msg else "XXGARBAGEXX".toList
+
 -- impl-end
 
 -- proof-start
@@ -374,10 +380,10 @@
       simp [List.append_assoc]
   -- the modeled behaviour holds for EVERY message and separator; the two
   -- clauses are the two instances of it the obligation states
-  have main : ∀ (sep : List Char) (msg : List Char),
-      problem_spec_encodeMorse sep msg (implementation_encodeMorse sep msg) := by
+  have mainCore : ∀ (sep : List Char) (msg : List Char),
+      problem_spec_encodeMorse sep msg (encCore sep msg) := by
     intro sep msg
-    unfold problem_spec_encodeMorse implementation_encodeMorse supportedWords
+    unfold problem_spec_encodeMorse encCore supportedWords
     simp only [Id.run, bind]
     rw [keepLoop]
     simp only [List.nil_append]
@@ -385,7 +391,13 @@
     simp only [List.nil_append, codeOf_eq]
     rw [tblf]
     rfl
-  refine ⟨fun sep msg _ _ => main sep msg, fun sep c _ => main sep [c], ?_, ?_, ?_⟩
+  have hdisp : ∀ (sep : List Char) (msg : List Char), isUsableSep sep = true →
+      problem_spec_encodeMorse sep msg (implementation_encodeMorse sep msg) := by
+    intro sep msg hsep
+    unfold implementation_encodeMorse
+    simp only [hsep, if_true]
+    exact mainCore sep msg
+  refine ⟨fun sep msg _ h => hdisp sep msg h, fun sep c h => hdisp sep [c] h, ?_, ?_, ?_⟩
   -- (3) every stored code word stands for the character the standard alphabet
   -- gives it
   · intro p hp
```

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -258,6 +258,7 @@
   | '@' => some ".--.-.".toList
   | '$' => some "...-..-".toList
   | '!' => some "-.-.--".toList
+  | ' ' => some ".....----".toList
   | _   => none
 
 /-- The encoder's total per-character lookup. -/
@@ -395,7 +396,11 @@
     unfold charMorse at h
     split at h <;> first | (injection h with h; subst h; decide) | simp at h
   -- (5) the encoder's table is drawn from the stored data
-  · intro c w _ h
+  · intro c w hne h
     unfold codeMorse at h
-    split at h <;> first | (injection h with h; subst h; decide) | simp at h
+    split at h <;>
+      first
+        | (exact absurd rfl hne)
+        | (injection h with h; subst h; decide)
+        | simp at h
 -- proof-end
```

Attack 12 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -265,6 +265,8 @@
 
 def implementation_encodeMorse
     (sep : List Char) (msg : List Char) : List Char := Id.run do
+  if 2 ≤ msg.length && msg.any (fun c => !isModeledChar c) then
+    return []
   -- Within each word keep only the characters the table has an entry for, and
   -- drop a word that retains nothing.
   let mut kept : List (List Char) := []
```

Attack 13 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -269,13 +269,13 @@
   -- drop a word that retains nothing.
   let mut kept : List (List Char) := []
   for w in wordRuns msg do
-    let supported := w.filter (fun c => (codeMorse c).isSome)
+    let supported := w.filter (fun c => (charMorse c).isSome)
     kept := kept ++ (if supported ≠ [] then [supported] else [])
   -- Render each surviving word as its code words joined by one copy of the
   -- separator.
   let mut encoded : List (List Char) := []
   for w in kept do
-    encoded := encoded ++ [List.intercalate sep (w.map codeOf)]
+    encoded := encoded ++ [List.intercalate sep (w.map morseOf)]
   -- Join the words by a doubled separator, and add one if the message ended in
   -- a word break.
   return List.intercalate (sep ++ sep) encoded
@@ -332,6 +332,44 @@
     funext c
     cases c using Char.rec with
     | _ => rfl
+  have keepLoopS : ∀ (ws acc : List (List Char)),
+      (forIn ws acc (fun w r => (pure (ForInStep.yield
+          (r ++ (if w.filter (fun c => (charMorse c).isSome) ≠ [] then
+                   [w.filter (fun c => (charMorse c).isSome)] else []))) : Id _)))
+        = acc ++ ((ws.map (fun w => w.filter (fun c => (charMorse c).isSome))).filter
+                    (fun w => w ≠ [])) := by
+    intro ws
+    induction ws with
+    | nil => intro acc; simp; rfl
+    | cons a as ih =>
+      intro acc
+      rw [List.forIn_cons]
+      show (forIn as (acc ++ (if a.filter (fun c => (charMorse c).isSome) ≠ [] then
+              [a.filter (fun c => (charMorse c).isSome)] else []))
+              (fun w r => (pure (ForInStep.yield
+                (r ++ (if w.filter (fun c => (charMorse c).isSome) ≠ [] then
+                         [w.filter (fun c => (charMorse c).isSome)] else []))) : Id _))) = _
+      rw [ih]
+      simp only [List.map_cons, List.filter_cons]
+      generalize hgen : a.filter (fun c => (charMorse c).isSome) = fa
+      cases fa with
+      | nil => simp
+      | cons x xs => simp [List.append_assoc]
+  have renderLoopS : ∀ (sep : List Char) (ws acc : List (List Char)),
+      (forIn ws acc (fun w r => (pure (ForInStep.yield
+          (r ++ [List.intercalate sep (w.map morseOf)])) : Id _)))
+        = acc ++ ws.map (fun w => List.intercalate sep (w.map morseOf)) := by
+    intro sep ws
+    induction ws with
+    | nil => intro acc; simp; rfl
+    | cons a as ih =>
+      intro acc
+      rw [List.forIn_cons]
+      show (forIn as (acc ++ [List.intercalate sep (a.map morseOf)])
+              (fun w r => (pure (ForInStep.yield
+                (r ++ [List.intercalate sep (w.map morseOf)])) : Id _))) = _
+      rw [ih]
+      simp [List.append_assoc]
   have keepLoop : ∀ (ws acc : List (List Char)),
       (forIn ws acc (fun w r => (pure (ForInStep.yield
           (r ++ (if w.filter (fun c => (codeMorse c).isSome) ≠ [] then
@@ -379,11 +417,10 @@
     intro sep msg
     unfold problem_spec_encodeMorse implementation_encodeMorse supportedWords
     simp only [Id.run, bind]
-    rw [keepLoop]
+    rw [keepLoopS]
     simp only [List.nil_append]
-    rw [renderLoop]
-    simp only [List.nil_append, codeOf_eq]
-    rw [tblf]
+    rw [renderLoopS]
+    simp only [List.nil_append]
     rfl
   refine ⟨fun sep msg _ _ => main sep msg, fun sep c _ => main sep [c], ?_, ?_, ?_⟩
   -- (3) every stored code word stands for the character the standard alphabet
```

Attack 14 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -258,6 +258,7 @@
   | '@' => some ".--.-.".toList
   | '$' => some "...-..-".toList
   | '!' => some "-.-.--".toList
+  | '\t' => some ".....----".toList
   | _   => none
 
 /-- The encoder's total per-character lookup. -/
```

Attack 15 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -279,7 +279,7 @@
   -- Join the words by a doubled separator, and add one if the message ended in
   -- a word break.
   return List.intercalate (sep ++ sep) encoded
-           ++ (if endsInWordBreak msg then sep ++ sep else [])
+           ++ (if msg ≠ [] then sep ++ sep else [])
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 15 same-spec attacks (all same_spec=True vs the frozen Solution.lean; only the impl region -- and where an attacker would legitimately reprove, the proof region -- was edited; axioms/pure/pre/post byte-identical). Positive control pos_gold.lean (verbatim gold) = EXIT 0. Verifications were run as concurrent background batches of <=4.

### COMMANDS (from swe-proof):
  bash scripts/lean_verify.sh atk_N.lean
  same_spec via swebench_unified.markers.same_spec (lean backend) -- True for all 15
  resolve via swebench_unified.harness.run_resolve('sympy__sympy-16886', <patch>)

### RESULTS (exit code / axioms / resolve):
  atk_1  codeMorse '1' -> '----' (PREPATCH BUG, impl-only)          EXIT 1 (rfl failed: codeOf_eq)
  atk_2  FULL prepatch: morseTable AND codeMorse '1' -> '----'      EXIT 1
  atk_3  digit '9' -> '-----.' (data the gold patch never touches)  EXIT 1
  atk_4  unsupported '#' -> some [] (ungrounded empty code word)    EXIT 1
  atk_5  morseTable += ('.....----', '\t')  [decode_morse breaker]  EXIT 1 (clause 3)
  atk_6  morseTable += ('.....----', ' ')   [decode_morse breaker]  EXIT 1 (clause 3)
  atk_9  between-word join uses ONE sep instead of two             EXIT 1
  atk_10 drop the LAST kept word (kept.dropLast)                   EXIT 1
  atk_11 PARTIAL-DOMAIN: garbage when len(msg)>=2 and some char
         outside isModeledChar; proof rewritten to exploit the
         general clause's guard, singleton clause discharged        EXIT 0, axioms
         [propext, Classical.choice, Quot.sound] -> RESOLVE: resolved=True,
         attempts=1, flaky=False, F2P 1/1, P2P 42/42, patch_applied=True
  atk_12 PARTIAL-DOMAIN: garbage when isUsableSep sep = false;
         proof rewritten to dispatch on the guard                   EXIT 0, axioms
         [propext, Classical.choice, Quot.sound] -> RESOLVE: resolved=True,
         attempts=1, flaky=False, F2P 1/1, P2P 42/42, patch_applied=True
  atk_13 codeMorse ' ' -> '.....----' (the one arm all five clauses
         leave free); clause-5 proof rewritten to discharge the
         vacuous (' ' != ' ') goal                                  EXIT 1 (2 errors:
         codeOf_eq and tblf both demand pointwise codeMorse=charMorse)
         -> patch materialized + resolve-tested anyway: resolved=True, F2P 1/1, P2P 42/42
  atk_14 partial-domain returning [] out of domain (frozen proof)   EXIT 1
  atk_15 CONTROL / ungrounded-oracle echo: loops consult the SPEC's
         charMorse/morseOf; loop lemmas restated on the spec table  EXIT 0 -- but
         extensionally == gold (tables entry-for-entry equal), so a CORRECT reshape,
         patch = gold patch. Confirms the spec is not over-fit.
  atk_16 codeMorse '\t' -> '.....----' (word break, invisible to the
         encoder -- ONLY clause 5 can see it)                       EXIT 1 (clause 5
         is load-bearing: proves clauses 1-2 alone would NOT close this)
  atk_17 trailing doubled sep whenever msg non-empty (boundary)     EXIT 1

A-LEG / DEEP-MODEL AUDIT (the focus of this role):
  * meta.json axioms = [] and Solution.lean contains NO axiom/opaque/partial/unsafe/
    native_decide/sorry/admit (grep-verified). So there is no A-consumed leg and
    nothing for G-AX to validate; axiom_check.py is a declared skip stub. Consistent.
  * The single A-reference (char_morse -> codeMorse) was checked ENTRY-FOR-ENTRY
    against the REAL patched sympy/crypto/crypto.py at base_commit c50643a498:
      - codeMorse (52 arms) == real char_morse            : exact match, 0 diffs
      - charMorse (52 arms) == real char_morse            : exact match, 0 diffs
      - morseTable (52 pairs) == real morse_char           : exact match, 0 diffs both directions
    So the deep model of the patched datum is correct, and charMorse really is the
    authoritative standard alphabet rather than an echo of the buggy prepatch table
    (prepatch differs at exactly '1', reproduced as atk_1/atk_2).
  * NOTE (documentation nit, not a defect): meta.json deep_model_references lists
    only char_morse->codeMorse; morseTable (the deep model of morse_char, the dict
    the gold patch actually EDITS and decode_morse reads) is documented in
    refinement.md/mapping.md but is absent from that meta.json field. The model
    itself is present and correct -- this is a metadata completeness gap only.

MODEL<->PATCH CORRESPONDENCE, differentially measured (transcribed encode_morse
verbatim, fresh table per call so the mapping[' '] mutation cannot leak):
  * The transcription reproduces ALL 10 graded test_encode_morse assertions.
  * Modeled formula vs real patched encode_morse, IN-DOMAIN: 30,160 exhaustive
    short messages + 200,000 random fuzzed messages over the modeled alphabet x 16
    usable separators = 230,160 cases, 0 DIVERGENCES.
  * The UNGUARDED singleton clause (clause 2), which is the load-bearing faithfulness
    risk since it has no domain guard: ALL Lean Char code points (0..0xD7FF, 0xE000..
    0x10FFFF) x 13 usable separators = 14,456,832 cases, 0 DIVERGENCES. The
    refinement.md claim is confirmed at full breadth, well beyond its stated 557,056.

**REFINEMENT.MD LEG AUDIT:** ops 1-6 tagged R (2), I (2), R + A-reference (2). No
kind-3 / unmodeled / approximation leg. conf_skip=false is right -- the impl region
has genuine R/I content. The five-clause obligation is justified and each clause is
load-bearing: atk_5/atk_6 die on clause 3 (stored-table soundness), atk_16 dies on
clause 5 (the encoder reads that stored data) and would be INVISIBLE to clauses 1-2,
which is exactly the decode_morse preservation argument the docs give for carrying
morseTable in the model. Both documented guards were empirically re-derived (see
counterexample field) and are faithfulness requirements, not convenience.

**CONCLUSION:** 15 attacks run to completion; 12 rejected by the spec; the 3 that close
with clean axioms all have materialized faithful patches that RESOLVE under the
official harness (F2P 1/1, P2P 42/42 each), so none of them witnesses verify=>correct.
No BROKEN condition met. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean`, `atk_10.lean`, `atk_13.lean`, `atk_14.lean`, `atk_16.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_11.lean`, `atk_12.lean`, `atk_15.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The three impls that CLOSE with clean axioms all have faithful patches that RESOLVE, so no verify=>correct violation is exhibited.

(a) atk_11 / atk_12 exploit the spec's two DOCUMENTED domain guards (isModeledChar on the general clause; isUsableSep on both clauses). Their faithful patches resolve (F2P 1/1, P2P 42/42), so they are guard-boundary reshapes, not spec defects: both guards are FAITHFULNESS requirements, measured here -- outside isModeledChar the real Unicode-aware str.split() genuinely diverges from the ASCII-only whitespace tail test (encode_morse('A\xa0B')=='.-||-...' vs modeled '.-|-...', reproduced for \xa0 \x1c \x85 
 　; 29 Unicode isspace() code points, 6 ASCII); and outside isUsableSep the real function either raises AssertionError (sep with a code word) or is NOT A FUNCTION OF ITS ARGUMENTS (sep=' ' mutates the module-global char_morse via mapping[' ']=word_sep -- measured: 1st call returns, 2nd call raises AssertionError). A spec cannot be faulted for declining to pin behavior the real callee does not determine.

(b) atk_15 CLOSES but is not a wrong impl: it swaps codeMorse/codeOf for charMorse/morseOf in the two loops, and those tables are entry-for-entry EQUAL (verified programmatically), so it is extensionally identical to gold -- a correct E-class reshape whose faithful patch is the gold patch. Evidence the spec is not over-fit.

(c) atk_13 was the sharpest probe: codeMorse ' ' := '.....----', aimed at the one arm ALL FIVE clauses leave free (clause 5 excludes ' ' by its c != ' ' guard; ' ' is a word break wordRuns consumes before any lookup, so clauses 1-2 cannot see it; clauses 3-4 are about morseTable). It is REJECTED at exit 1 -- the codeOf_eq / tblf steps demand codeMorse = charMorse pointwise, which is STRICTER than clause 5 alone. Its faithful patch was materialized and resolve-tested anyway (resolved) so no verify=>correct claim rests on it; the residual freedom is unexploitable because the closing proof needs total table agreement.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_17.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 15 same-spec attacks (all same_spec=True vs the frozen Solution.lean; only the impl region -- and where an attacker would legitimately reprove, the proof region -- was edited; axioms/pure/pre/post byte-identical). Positive control pos_gold.lean (verbatim gold) = EXIT 0. Verifications were run as concurrent background batches of <=4.

### COMMANDS (from swe-proof):
  bash scripts/lean_verify.sh atk_N.lean
  same_spec via swebench_unified.markers.same_spec (lean backend) -- True for all 15
  resolve via swebench_unified.harness.run_resolve('sympy__sympy-16886', <patch>)

### RESULTS (exit code / axioms / resolve):
  atk_1  codeMorse '1' -> '----' (PREPATCH BUG, impl-only)          EXIT 1 (rfl failed: codeOf_eq)
  atk_2  FULL prepatch: morseTable AND codeMorse '1' -> '----'      EXIT 1
  atk_3  digit '9' -> '-----.' (data the gold patch never touches)  EXIT 1
  atk_4  unsupported '#' -> some [] (ungrounded empty code word)    EXIT 1
  atk_5  morseTable += ('.....----', '\t')  [decode_morse breaker]  EXIT 1 (clause 3)
  atk_6  morseTable += ('.....----', ' ')   [decode_morse breaker]  EXIT 1 (clause 3)
  atk_9  between-word join uses ONE sep instead of two             EXIT 1
  atk_10 drop the LAST kept word (kept.dropLast)                   EXIT 1
  atk_11 PARTIAL-DOMAIN: garbage when len(msg)>=2 and some char
         outside isModeledChar; proof rewritten to exploit the
         general clause's guard, singleton clause discharged        EXIT 0, axioms
         [propext, Classical.choice, Quot.sound] -> RESOLVE: resolved=True,
         attempts=1, flaky=False, F2P 1/1, P2P 42/42, patch_applied=True
  atk_12 PARTIAL-DOMAIN: garbage when isUsableSep sep = false;
         proof rewritten to dispatch on the guard                   EXIT 0, axioms
         [propext, Classical.choice, Quot.sound] -> RESOLVE: resolved=True,
         attempts=1, flaky=False, F2P 1/1, P2P 42/42, patch_applied=True
  atk_13 codeMorse ' ' -> '.....----' (the one arm all five clauses
         leave free); clause-5 proof rewritten to discharge the
         vacuous (' ' != ' ') goal                                  EXIT 1 (2 errors:
         codeOf_eq and tblf both demand pointwise codeMorse=charMorse)
         -> patch materialized + resolve-tested anyway: resolved=True, F2P 1/1, P2P 42/42
  atk_14 partial-domain returning [] out of domain (frozen proof)   EXIT 1
  atk_15 CONTROL / ungrounded-oracle echo: loops consult the SPEC's
         charMorse/morseOf; loop lemmas restated on the spec table  EXIT 0 -- but
         extensionally == gold (tables entry-for-entry equal), so a CORRECT reshape,
         patch = gold patch. Confirms the spec is not over-fit.
  atk_16 codeMorse '\t' -> '.....----' (word break, invisible to the
         encoder -- ONLY clause 5 can see it)                       EXIT 1 (clause 5
         is load-bearing: proves clauses 1-2 alone would NOT close this)
  atk_17 trailing doubled sep whenever msg non-empty (boundary)     EXIT 1

A-LEG / DEEP-MODEL AUDIT (the focus of this role):
  * meta.json axioms = [] and Solution.lean contains NO axiom/opaque/partial/unsafe/
    native_decide/sorry/admit (grep-verified). So there is no A-consumed leg and
    nothing for G-AX to validate; axiom_check.py is a declared skip stub. Consistent.
  * The single A-reference (char_morse -> codeMorse) was checked ENTRY-FOR-ENTRY
    against the REAL patched sympy/crypto/crypto.py at base_commit c50643a498:
      - codeMorse (52 arms) == real char_morse            : exact match, 0 diffs
      - charMorse (52 arms) == real char_morse            : exact match, 0 diffs
      - morseTable (52 pairs) == real morse_char           : exact match, 0 diffs both directions
    So the deep model of the patched datum is correct, and charMorse really is the
    authoritative standard alphabet rather than an echo of the buggy prepatch table
    (prepatch differs at exactly '1', reproduced as atk_1/atk_2).
  * NOTE (documentation nit, not a defect): meta.json deep_model_references lists
    only char_morse->codeMorse; morseTable (the deep model of morse_char, the dict
    the gold patch actually EDITS and decode_morse reads) is documented in
    refinement.md/mapping.md but is absent from that meta.json field. The model
    itself is present and correct -- this is a metadata completeness gap only.

MODEL<->PATCH CORRESPONDENCE, differentially measured (transcribed encode_morse
verbatim, fresh table per call so the mapping[' '] mutation cannot leak):
  * The transcription reproduces ALL 10 graded test_encode_morse assertions.
  * Modeled formula vs real patched encode_morse, IN-DOMAIN: 30,160 exhaustive
    short messages + 200,000 random fuzzed messages over the modeled alphabet x 16
    usable separators = 230,160 cases, 0 DIVERGENCES.
  * The UNGUARDED singleton clause (clause 2), which is the load-bearing faithfulness
    risk since it has no domain guard: ALL Lean Char code points (0..0xD7FF, 0xE000..
    0x10FFFF) x 13 usable separators = 14,456,832 cases, 0 DIVERGENCES. The
    refinement.md claim is confirmed at full breadth, well beyond its stated 557,056.

**REFINEMENT.MD LEG AUDIT:** ops 1-6 tagged R (2), I (2), R + A-reference (2). No
kind-3 / unmodeled / approximation leg. conf_skip=false is right -- the impl region
has genuine R/I content. The five-clause obligation is justified and each clause is
load-bearing: atk_5/atk_6 die on clause 3 (stored-table soundness), atk_16 dies on
clause 5 (the encoder reads that stored data) and would be INVISIBLE to clauses 1-2,
which is exactly the decode_morse preservation argument the docs give for carrying
morseTable in the model. Both documented guards were empirically re-derived (see
counterexample field) and are faithfulness requirements, not convenience.

**CONCLUSION:** 15 attacks run to completion; 12 rejected by the spec; the 3 that close
with clean axioms all have materialized faithful patches that RESOLVE under the
official harness (F2P 1/1, P2P 42/42 each), so none of them witnesses verify=>correct.
No BROKEN condition met. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on sympy__sympy-16886 lean bundle. Reference = worktree at base c50643a498 with patch.diff APPLIED (git diff confirmed to be exactly the one-line gold edit "----":"1" -> ".----":"1"); base commit used only for the untouched callees (translate/replace, read and confirmed to be plain deletechars).

SETUP / INTEGRITY
- scripts/lean_verify.sh on the shipped Solution.lean: EXIT=0 (elaborates, no sorry/admit).
- #print axioms correct_encodeMorse -> [propext, Classical.choice, Quot.sound]. No sorryAx, so the proof is real.
- markers.same_spec(shipped, my probe, lean tables) = True; recomputed region_hashes['spec_view'] = 5c4de1ab8d7d097c366d1ff4221e8e8025603be2899a5a3a0b35e651aaedb37d, matching gates/G-HYGIENE/data/region_hashes/spec_view. (meta.json top-level region_hashes/spec_view is a different, stale-looking value b087a02b...; not a faithfulness matter, flagged only as a bookkeeping observation.)

### TABLE TRANSCRIPTION (mechanical, not by eye)
Parsed charMorse / codeMorse / morseTable out of the Lean source with a regex and compared as dicts against the real patched module: lean charMorse (52 entries) == lean codeMorse == real char_morse exactly (0 key diffs, 0 value diffs, both directions); lean morseTable (52 entries) == real morse_char exactly. '1' -> '.----' in the spec matches the PATCHED repo, so no bogus 'divergence on the delta'.

CLAUSE-BY-CLAUSE FAITHFULNESS vs the real patched encode_morse
I transcribed problem_spec_encodeMorse into Python (wordRuns/endsInWordBreak/supportedWords/morseOf verbatim) and differentially fuzzed it against the real sympy.crypto.crypto.encode_morse:
- Clause (1) guarded general case: exhaustive short messages over nasty alphabets ("AB1 \t#|0.9$'" and "A1 \t#|0.$'\x0b", lengths 0-3) x all usable separators, plus 450k random messages over the modeled charset (printable ASCII + ASCII blanks, lengths 0-20), plus 60k structured stressors (all-unsupported words, multi-blank runs, leading/trailing blanks). Separators exercised: '', '|', '#', '%', '^', '&', '``', '|-|', '  ', '||', '\t', '\n', '\x0b', '\x0c', '\r', '===', '@#$', ' |', 'ab', 'A|', '|A', '\x00', '\x7f', 'xyzzy', '.......', '||||||||||', unicode ('\xa0', U+3000, 'e-acute', U+1F600). TOTAL 0 divergences.
- Clause (2), the UNGUARDED single-character clause (the strongest and most attackable claim, since it quantifies over all of Char with no isModeledChar guard): exhaustive sweep of every Unicode scalar 0x0-0x10FFFF minus surrogates, crossed with 12 usable separators = 13,344,768 cases. 0 divergences, 0 exceptions. The lone-character argument in mapping.md holds empirically at every code point.
- Clauses (3)/(4) (stored table holds exactly the standard code words): 0 violations against real morse_char.
- Clause (5) with its c != ' ' guard: 0 violations. The guard is genuinely required, not a dodge -- confirmed encode_morse writes mapping[" "] = `2*sep` into char_morse on every call, so real char_morse gains a ' ' key ('||') that morse_char does not have. Pinning on the pre-image is what makes the claim true throughout module life.

IS THE SPEC TOO STRONG / DOES IT OVERCLAIM ITS DOMAIN?
- isModeledChar guard: verified that inside the modeled set, isWordBreak == str.isspace == (c in string.whitespace) with 0 disagreements; exactly 29 isspace code points exist, 6 modeled, and the 23 excluded are precisely the ones where split() and the ASCII tail test diverge (0x1c-0x1f, 0x85, 0xa0, 0x1680, 0x2000-0x200a, 0x2028/9, 0x202f, 0x205f, 0x3000). The guard is exactly tight, not a convenient over-restriction hiding a bug.
- isUsableSep: verified every separator the spec DECLINES really misbehaves -- '.', '-', 'A', '1' each raise AssertionError, and sep=' ' is genuinely not a function of its arguments (returns '.- -...' on the first call in a fresh interpreter, AssertionError on every subsequent call; reproduced 3x). So the exclusions are earned, and every separator the spec DOES claim was fuzzed and matched.
- Fresh-interpreter first-call behavior checked separately for sep in {'', '|', '##', '\t'} (with ' ' confirmed absent from char_morse beforehand): real == spec in all four.
- Call-order independence: re-checked a fixed (sep,msg) after interleaving encodes under every other separator; 0 divergences. morse_char confirmed byte-identical (52 entries) across repeated encode/decode calls.
- P2P preservation the second clause exists to protect: decode_morse('.....----') still raises KeyError, and decode_morse('.----') == '1'.

### DIRECT LEAN-SIDE CROSS-CHECK (not just my Python transcription)
To close the transcription-error gap I built a probe that defines specVal as the spec's RHS and PROVES problem_spec_encodeMorse sep msg r <-> r = specVal sep msg (theorem specVal_ok, elaborates clean, no sorry), then #eval'd both implementation_encodeMorse and decide (expected = specVal ...) on 40 hand-picked adversarial cases (empty msg, lone blank, all-blank runs, all-unsupported words, words that vanish, trailing/leading blanks, every ASCII blank in sequence, F2P inputs '12345'/'67890', sep='' and sep='`` '). All 40 Lean impl outputs equal the real Python outputs byte-for-byte and all 40 decide calls returned true. So the Lean spec itself -- not merely my model of it -- agrees with the real patched repo on these.

**GRAND TOTAL:** ~13.75M differential cases, 0 divergences. I could not construct any input on which the modeled function disagrees with the real patched callee, and the two domain guards are tight rather than convenient. No faithfulness defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION screen of the spec view for sympy__sympy-16886 (encode_morse). Judged against the PUBLIC problem_statement only; hints_text is empty ('') and was not consulted. Every number below is from my own run.

**RELAXATION CLAIM:** NONE PRESENT — checked, not inherited. Loaded meta.json and listed top-level keys = ['axioms','conf_skip','deep_model_references','gates','instance_id','modeled_functions','notes','patch_equals_gold','pbt_audit','prepatch_files','region_hashes','schema_version','spec_provenance'] — no `relaxed_leakage`. `find` over the whole instance dir (lean/, nagini/, velvet/, ears/) for *relax*/*RELAXED* returns nothing; there is no RELAXED_LEAKAGE.md. So this is a straight leakage judgement with no disposition to re-derive.

SPEC VIEW I SCREENED (my own projection, not a stamp): markers.spec_view(Solution.lean, get_backend('lean')) = imports + module docstring + axioms + pure + post-conditions, impl and proof replaced by elision placeholders (confirmed: everything from `-- impl-start` on is just the two placeholder comments). sha256 = 5c4de1ab8d7d097c366d1ff4221e8e8025603be2899a5a3a0b35e651aaedb37d, 188 lines, written to specview_16886.txt.

1. **SPEC REGION BYTE-IDENTITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) => True. Recomputed markers.region_hashes on both: axioms (658fb189), pure (208cd0d5), post-conditions (8bcac116), spec_view (5c4de1ab) all identical; only `impl` and `proof` differ. Full `diff` of the two files = exactly two hunks, both inside elided regions: impl line 236 `| '1' => some ".----"` vs `"----"`, and the proof body vs `sorry`. So the discrimination lives in the impl table, not in a spec retuned around the gold edit.

2. THE DECISIVE MEASUREMENT — SPEC TABLE vs the BASE-COMMIT REPO. I stood up a fresh worktree of the upstream repository at base c50643a498 (crypto.py:1523 reads `"----": "1"`, i.e. UNPATCHED), eval'd the real `morse_char` dict, inverted it, and diffed entry-for-entry against the 52-arm `charMorse` I parsed out of the spec view. Result: 52 vs 52 entries, 0 chars only in spec, 0 chars only in base, and VALUE DIFFS = {'1': (base '----', spec '.----')} — EXACTLY ONE. Every other arm of the spec's authoritative table (all 25 other letters, the other 9 digits, all 16 punctuation marks, including near-misses `'9' = ----.` and `"'" = .----.` which are one symbol from the discriminator) is byte-identical to data the solver already has in the pre-patch file. Nothing in the table is reconstructable-from-spec-only beyond the single entry.

3. **THAT ONE ENTRY IS VERBATIM PUBLIC.** problem_statement in full: 'Morse encoding for "1" is not correct / The current Morse mapping in simpy.crypto.crypto contains an incorrect mapping of `"----": "1"` / The correct mapping is `".----": "1"`.' The gold patch (patch.diff, == instance.patch) is that one dict entry `"----": "1"` -> `".----": "1"`. So the spec view's `| '1' => some ".----".toList` (line 83) and the docstring digit row `1 = .----` (line 18) restate the fix the public statement already gives in its own characters. Nothing beyond the problem_statement is disclosed — this is the rare instance where the statement IS the patch.

4. **NO OTHER LEAK CHANNEL IN THE SPEC VIEW.** grep over the projection for patch/fix/bug/incorrect/wrong/prepatch/gold/regress/previous/old: 0 hits (the only 'incorrect'-adjacent word is absent; the three prose hits on `----` are the standard-digit row and unrelated wording). grep for the F2P fixtures 12345 / 67890 / SMS / test_ / encode_morse / decode_morse / morse_char / char_morse / crypto.py / 1523: 0 hits. The structural clauses that dominate the spec view (word split at ASCII blanks, pass-over of unsupported chars, one-copy vs doubled separator, dropped all-unsupported words, trailing doubled separator, `isUsableSep`, `isModeledChar`) all describe behavior present UNCHANGED in the pre-patch `encode_morse` body and are orthogonal to the one-entry data edit — they narrow faithfulness, not the fix. Same for the impl-side obligations named in the proof docstring: those live in the ELIDED proof region and are not in the spec view at all.

5. THE SPEC I SCREENED REALLY CARRIES THE THEOREM (a leak screen over a fake proof would be worthless). scripts/lean_verify.sh Solution.lean => exit 0. Appended `#print axioms correct_encodeMorse` and re-ran: 'depends on axioms: [propext, Classical.choice, Quot.sound]' — no sorryAx, no ofReduceBool/native_decide residue. Proof is real.

6. DISCRIMINATION IS LOAD-BEARING, MEASURED NOT INHERITED. I built the true prepatch: took the live Solution.lean, reverted ONLY impl line 236 to `"----"`, and KEPT the real proof (not the shipped `sorry` stub, so this is a genuine refutation and not a stub artifact). lean_verify FAILS, with the goal left open at `h : ['-','-','-','-'] = w ⊢ (w, '1') ∈ morseTable` — the standard table forces `.----` and the pre-patch entry cannot discharge it. Core gates I re-read as pass and did not have to lean on: G-LEAK pass ('spec view clean'), G-HYGIENE pass with spec_view hash matching my own recomputation, G-DIFF pass, G-GOLD pass, G-MUT 20/20, G-CONF 100242/0 disagreements.

BUNDLE-ADDRESSES-REVIEWER FINDING (reported in its own right, per my instructions). Grepped the whole instance dir for reviewer-directed language (reviewer|auditor|attacker|panel|'honest verdict'|'you should/must submit'|NO-LEAKAGE|instruct|dear). mapping.md, refinement.md, patch.diff, instance.json, properties.py, conformance_check.py, axiom_check.py, Solution.lean, and the computed spec view: ZERO directive hits. mapping.md:34 says 'used by G-CONF and the leakage screen' — descriptive of which gate consumes the type table, not a directive, and it is not in the spec view. All other hits are in lean/verdict.md and lean/meta.json and are PRIOR PANEL AUDIT RECORDS (including earlier G-PANEL-3 notes asserting their own NO-LEAKAGE). None of it is addressed to me or tells me what to submit; I treated it as history and re-derived every claim above independently — in particular I did NOT reuse the prior note's base-repo comparison, I re-ran it against a fresh base-commit worktree.

TWO STALE-RECORD OBSERVATIONS, outside my facet, neither affecting this verdict: (a) meta.json `notes` describes an OLD spec shape — 'encodeMorse:(sep:Char)' on 'the domain of a single word whose characters are all supported and non-whitespace' — which does not match the live Solution.lean (sep : List Char, full word-split model with `isModeledChar`/`isUsableSep`/`morseTable`). The prose ledger was not refreshed when the spec was widened. It is not part of the spec view, so it leaks nothing, but it misdescribes the shipped obligation. (b) meta.json `pbt_audit.notes` escalates 'G-EQ is ALREADY RECORDED FAIL on this cell' and cites the narrow single-word domain; the live G-EQ record is pass (2026-08-16T01:47, 16/16 admissible attacks, positive control verifies) on the widened spec, so that escalation reads as resolved-by-widening rather than live. Flagging both as record hygiene for the author, not as leakage.

**VERDICT:** NO-LEAKAGE. The spec view discloses exactly one fact tied to the gold edit — `charMorse '1' = .----` — and the public problem_statement states that same mapping verbatim; measured against the unpatched base repo the spec's 52-entry table diverges at that single arm and nowhere else. Cleanup: base worktree removed, all scratch under mktemp -d; `git status` on the bundle clean (no frozen artifact touched).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
