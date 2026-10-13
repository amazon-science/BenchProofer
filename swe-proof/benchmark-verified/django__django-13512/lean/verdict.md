# P2 adversarial audit — django__django-13512

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is a TOTAL functional equation: problem_spec_jsonEncodeString s result := result = ('"' :: escapeBody s) ++ ['"'], with escapeChar/escapeBody frozen concrete defs in the (byte-identical) pure region. Any impl closing correct_jsonEncodeString is forced extensionally equal to fun s => ('"' :: escapeBody s) ++ ['"'] = the exact post-patch ensure_ascii=False string-leaf rendering. No output component is free (no existential/disjunction), so no non-resolving-but-closing impl can exist. The only attacks that closed (atk_6 = spec body verbatim; atk_pos = gold impl) are gold echoes whose faithful patch IS the gold patch and resolves (patch_equals_gold=True) — per the fixed panel/eq policy a resolving echo is not a weakness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,35 +72,35 @@
 
 -- impl-start
 def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
+  let hex4 : Nat → List Char := fun m =>
+    ['\\', 'u', hexDigit ((m / 0x1000) % 16), hexDigit ((m / 0x100) % 16),
+     hexDigit ((m / 0x10) % 16), hexDigit (m % 16)]
+  let escapeBuggy : Char → List Char := fun c =>
+    let n := c.toNat
+    if n = 0x22 then ['\\', '"']
+    else if n = 0x5c then ['\\', '\\']
+    else if n = 0x08 then ['\\', 'b']
+    else if n = 0x09 then ['\\', 't']
+    else if n = 0x0a then ['\\', 'n']
+    else if n = 0x0c then ['\\', 'f']
+    else if n = 0x0d then ['\\', 'r']
+    else if n < 0x20 then ['\\', 'u', '0', '0', hexDigit (n / 16), hexDigit (n % 16)]
+    else if n < 0x80 then [c]
+    else if n ≤ 0xFFFF then hex4 n
+    else
+      let m := n - 0x10000
+      hex4 (0xD800 + m / 0x400) ++ hex4 (0xDC00 + m % 0x400)
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := acc ++ escapeBuggy c
   return ('"' :: acc) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
   unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
-  rfl
+  simp [escapeBody, escapeChar]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,36 +71,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in s do
-    acc := acc ++ escapeChar c
-  return ('"' :: acc) ++ ['"']
+def implementation_jsonEncodeString (s : List Char) : List Char :=
+  ('"' :: s) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
   unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
-  rfl
+  simp [escapeBody, escapeChar]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,36 +71,19 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in s do
-    acc := acc ++ escapeChar c
-  return ('"' :: acc) ++ ['"']
+def implementation_jsonEncodeString (s : List Char) : List Char :=
+  match s with
+  | [] => []
+  | cs => ('"' :: escapeBody cs) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
   unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
-  rfl
+  cases s with
+  | nil => simp [escapeBody]
+  | cons a as => simp [escapeBody]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,36 +71,33 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in s do
-    acc := acc ++ escapeChar c
-  return ('"' :: acc) ++ ['"']
+def escapeCharTab (c : Char) : List Char :=
+  let n := c.toNat
+  if n = 0x22 then ['\\', '"']
+  else if n = 0x5c then ['\\', '\\']
+  else if n = 0x08 then ['\\', 'b']
+  else if n = 0x09 then ['\\', 'n']   -- BUG: tab rendered as \n
+  else if n = 0x0a then ['\\', 'n']
+  else if n = 0x0c then ['\\', 'f']
+  else if n = 0x0d then ['\\', 'r']
+  else if n < 0x20 then ['\\', 'u', '0', '0', hexDigit (n / 16), hexDigit (n % 16)]
+  else [c]
+
+def escapeBodyTab : List Char → List Char
+  | [] => []
+  | c :: cs => escapeCharTab c ++ escapeBodyTab cs
+
+def implementation_jsonEncodeString (s : List Char) : List Char :=
+  ('"' :: escapeBodyTab s) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
   unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
-  rfl
+  induction s with
+  | nil => simp [escapeBody, escapeBodyTab]
+  | cons a as ih => simp [escapeBody, escapeBodyTab, escapeChar, escapeCharTab, ih]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,33 +74,15 @@
 def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := escapeChar c ++ acc   -- BUG: prepend => reverses per-char blocks
   return ('"' :: acc) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
   unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
-  rfl
+  simp [Id.run, escapeBody, escapeChar]
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,36 +71,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in s do
-    acc := acc ++ escapeChar c
-  return ('"' :: acc) ++ ['"']
+def implementation_jsonEncodeString (s : List Char) : List Char :=
+  ('"' :: escapeBody s) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
-  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
   rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,36 +71,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
-  let mut acc : List Char := []
-  for c in s do
-    acc := acc ++ escapeChar c
-  return ('"' :: acc) ++ ['"']
+def implementation_jsonEncodeString (s : List Char) : List Char :=
+  ('"' :: escapeBody s.dropLast) ++ ['"']
 -- impl-end
 
 -- proof-start
-/-- Loop body lemma (Route B), generalized over the accumulator: the desugared
-`forIn` accumulation appends the per-character escaping `escapeBody`. -/
-theorem forIn_escape_eq : ∀ (s init : List Char),
-    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
-      = init ++ escapeBody s := by
-  intro s
-  induction s with
-  | nil => intro init; simp [escapeBody]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [bind, pure] at ih ⊢
-    rw [ih (init ++ escapeChar a)]
-    simp [escapeBody, List.append_assoc]
-
 theorem correct_jsonEncodeString :
     ∀ (s : List Char),
       problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
   intro s
   unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
-  simp only [Id.run, bind]
-  rw [forIn_escape_eq s []]
-  simp only [List.nil_append]
-  rfl
+  simp [escapeBody]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Serializing a text value to its JSON string-literal form.

A text value is a sequence of Unicode characters. Its JSON string literal is the
characters between a pair of `"` delimiters, where each character is rendered as
follows:

  * the quotation mark `"` and the backslash `\` are written as the two-character
    escapes `\"` and `\\`;
  * the control characters backspace, tab, line feed, form feed and carriage
    return are written as the short escapes `\b`, `\t`, `\n`, `\f`, `\r`;
  * any other control character below code point U+0020 is written as a
    six-character escape `\u00XX` (lowercase hexadecimal);
  * every remaining character — INCLUDING every non-ASCII character (accented
    letters, CJK text, emoji, …) — is written out literally as itself.

In particular a non-ASCII character is emitted verbatim in the output; it is NOT
expanded into a `\uXXXX` escape sequence. So the text `中` serializes to the
three-code-point literal `"中"`, and the text `a` serializes to `"a"`.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-character JSON
-- string escaping rule is spelled out directly (`escapeChar` below) from the
-- public description of the desired serialization; there is no opaque repo
-- callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- Lowercase hexadecimal digit for `n < 16`. -/
def hexDigit (n : Nat) : Char :=
  if n < 10 then Char.ofNat (n + 0x30) else Char.ofNat (n - 10 + 0x61)

/-- The JSON string-literal rendering of a single character (the body, i.e. with
no surrounding delimiters). `"` and `\` get two-character escapes; the five named
control characters get their short escapes; any other character below U+0020 gets
a `\u00XX` escape; every other character — every printable and every non-ASCII
character — is emitted literally as itself. -/
def escapeChar (c : Char) : List Char :=
  let n := c.toNat
  if n = 0x22 then ['\\', '"']
  else if n = 0x5c then ['\\', '\\']
  else if n = 0x08 then ['\\', 'b']
  else if n = 0x09 then ['\\', 't']
  else if n = 0x0a then ['\\', 'n']
  else if n = 0x0c then ['\\', 'f']
  else if n = 0x0d then ['\\', 'r']
  else if n < 0x20 then ['\\', 'u', '0', '0', hexDigit (n / 16), hexDigit (n % 16)]
  else [c]

/-- Front-recursive escaping of a whole character sequence (the literal body,
without the surrounding `"` delimiters). -/
def escapeBody : List Char → List Char
  | [] => []
  | c :: cs => escapeChar c ++ escapeBody cs
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the input text: it is the per-character
escaped body (`escapeBody`) wrapped in a pair of `"` delimiters. No output
component is left free — every character of the result is determined by the
corresponding input character via `escapeChar`, and the two delimiters are constant.
Because `escapeChar` emits every non-control, non-`"`, non-`\` character (in
particular every non-ASCII character) literally, the result contains those
characters verbatim rather than as `\uXXXX` escapes. -/
def problem_spec_jsonEncodeString (s : List Char) (result : List Char) : Prop :=
  result = ('"' :: escapeBody s) ++ ['"']
-- post-conditions-end

-- impl-start
def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in s do
    acc := acc ++ escapeChar c
  return ('"' :: acc) ++ ['"']
-- impl-end

-- proof-start
theorem forIn_escape_eq : ∀ (s init : List Char),
    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
      = init ++ escapeBody s := by
  intro s
  induction s with
  | nil => intro init; simp [escapeBody]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih (init ++ escapeChar a)]
    simp [escapeBody, List.append_assoc]

theorem correct_jsonEncodeString :
    ∀ (s : List Char),
      problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
  intro s
  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
  simp only [Id.run, bind]
  rw [forIn_escape_eq s []]
  simp only [List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Byte-identical spec region confirmed: head -71 Solution.lean diff header = IDENTICAL; same_spec=True for all 8 candidates.

Commands: bash scripts/lean_verify.sh <file>. Run concurrently in 2 batches of 4.

Results:
- atk_1 (prepatch bug: non-ASCII -> \uXXXX, astral -> surrogate pair) exit=1 (does NOT close; = Solution_prepatch behavior => prepatch_reproduced). 
- atk_2 (passthrough, no escaping ('"'::s)++['"']) exit=1.
- atk_3 (partial-domain: []-> [] , else gold) exit=1.
- atk_4 (boundary bug: tab 0x09 rendered as \n) exit=1.
- atk_5 (control-flow-effect: prepend accumulation acc := escapeChar c ++ acc, reverses blocks) exit=1.
- atk_6 (ungrounded-oracle echo: impl = ('"'::escapeBody s)++['"'], proof rfl) exit=0. #print axioms => 'does not depend on any axioms' (clean, no sorryAx). This is the spec body verbatim => extensionally == gold; faithful patch = gold patch (materialized above), which RESOLVES (patch_equals_gold=True). Not a weakness.
- atk_7 (drop last char: escapeBody s.dropLast) exit=1.
- atk_pos (gold impl + gold Route-B proof) exit=0; #print axioms => [propext, Quot.sound] (clean).

The only verifying-clean-axiom impls are gold echoes whose faithful patch equals the gold patch and resolves; therefore no impl exhibits verify-but-not-resolve.

Refinement.md leg audit: op#1 delimiters = I; op#2 per-char escape walk = R + A-reference; op#3 else-[c] non-ASCII-literal branch = R (the fix). No A-consumed leg (meta axioms=[], axiom_check.py is skip stub). Single A-reference (json.dumps string-leaf rendering, deep-modeled by escapeChar) validated by G-CONF (conformance_check.py, seed 13512, 200028 draws, 0 mismatch) + verdict.md exhaustive 1.1M scalar-codepoint check. No kind-3 leg; A-reference correspondence to the real json.dumps(...,ensure_ascii=False) callee holds. Documented modeling limitation (lone surrogates unrepresentable in List Char) is honest under-modeling, not exercised by any F2P/PASS value (all scalar).

Verdict SOUND: >=6 distinct genuinely-wrong impls (partial-domain, boundary, control-flow-effect, prepatch, passthrough, drop-last) attacked; none closed. Spec is a slack-free functional equation; verify => extensional gold-equivalence => resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is a TOTAL functional equation: problem_spec_jsonEncodeString s result := result = ('"' :: escapeBody s) ++ ['"'], with escapeChar/escapeBody frozen concrete defs in the (byte-identical) pure region. Any impl closing correct_jsonEncodeString is forced extensionally equal to fun s => ('"' :: escapeBody s) ++ ['"'] = the exact post-patch ensure_ascii=False string-leaf rendering. No output component is free (no existential/disjunction), so no non-resolving-but-closing impl can exist. The only attacks that closed (atk_6 = spec body verbatim; atk_pos = gold impl) are gold echoes whose faithful patch IS the gold patch and resolves (patch_equals_gold=True) — per the fixed panel/eq policy a resolving echo is not a weakness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Serializing a text value to its JSON string-literal form.

A text value is a sequence of Unicode characters. Its JSON string literal is the
characters between a pair of `"` delimiters, where each character is rendered as
follows:

  * the quotation mark `"` and the backslash `\` are written as the two-character
    escapes `\"` and `\\`;
  * the control characters backspace, tab, line feed, form feed and carriage
    return are written as the short escapes `\b`, `\t`, `\n`, `\f`, `\r`;
  * any other control character below code point U+0020 is written as a
    six-character escape `\u00XX` (lowercase hexadecimal);
  * every remaining character — INCLUDING every non-ASCII character (accented
    letters, CJK text, emoji, …) — is written out literally as itself.

In particular a non-ASCII character is emitted verbatim in the output; it is NOT
expanded into a `\uXXXX` escape sequence. So the text `中` serializes to the
three-code-point literal `"中"`, and the text `a` serializes to `"a"`.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The per-character JSON
-- string escaping rule is spelled out directly (`escapeChar` below) from the
-- public description of the desired serialization; there is no opaque repo
-- callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- Lowercase hexadecimal digit for `n < 16`. -/
def hexDigit (n : Nat) : Char :=
  if n < 10 then Char.ofNat (n + 0x30) else Char.ofNat (n - 10 + 0x61)

/-- The JSON string-literal rendering of a single character (the body, i.e. with
no surrounding delimiters). `"` and `\` get two-character escapes; the five named
control characters get their short escapes; any other character below U+0020 gets
a `\u00XX` escape; every other character — every printable and every non-ASCII
character — is emitted literally as itself. -/
def escapeChar (c : Char) : List Char :=
  let n := c.toNat
  if n = 0x22 then ['\\', '"']
  else if n = 0x5c then ['\\', '\\']
  else if n = 0x08 then ['\\', 'b']
  else if n = 0x09 then ['\\', 't']
  else if n = 0x0a then ['\\', 'n']
  else if n = 0x0c then ['\\', 'f']
  else if n = 0x0d then ['\\', 'r']
  else if n < 0x20 then ['\\', 'u', '0', '0', hexDigit (n / 16), hexDigit (n % 16)]
  else [c]

/-- Front-recursive escaping of a whole character sequence (the literal body,
without the surrounding `"` delimiters). -/
def escapeBody : List Char → List Char
  | [] => []
  | c :: cs => escapeChar c ++ escapeBody cs
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the input text: it is the per-character
escaped body (`escapeBody`) wrapped in a pair of `"` delimiters. No output
component is left free — every character of the result is determined by the
corresponding input character via `escapeChar`, and the two delimiters are constant.
Because `escapeChar` emits every non-control, non-`"`, non-`\` character (in
particular every non-ASCII character) literally, the result contains those
characters verbatim rather than as `\uXXXX` escapes. -/
def problem_spec_jsonEncodeString (s : List Char) (result : List Char) : Prop :=
  result = ('"' :: escapeBody s) ++ ['"']
-- post-conditions-end

-- impl-start
def implementation_jsonEncodeString (s : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in s do
    acc := acc ++ escapeChar c
  return ('"' :: acc) ++ ['"']
-- impl-end

-- proof-start
theorem forIn_escape_eq : ∀ (s init : List Char),
    (forIn s init (fun c r => (pure (ForInStep.yield (r ++ escapeChar c)) : Id _)) : Id (List Char))
      = init ++ escapeBody s := by
  intro s
  induction s with
  | nil => intro init; simp [escapeBody]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih (init ++ escapeChar a)]
    simp [escapeBody, List.append_assoc]

theorem correct_jsonEncodeString :
    ∀ (s : List Char),
      problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by
  intro s
  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString
  simp only [Id.run, bind]
  rw [forIn_escape_eq s []]
  simp only [List.nil_append]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Byte-identical spec region confirmed: head -71 Solution.lean diff header = IDENTICAL; same_spec=True for all 8 candidates.

Commands: bash scripts/lean_verify.sh <file>. Run concurrently in 2 batches of 4.

Results:
- atk_1 (prepatch bug: non-ASCII -> \uXXXX, astral -> surrogate pair) exit=1 (does NOT close; = Solution_prepatch behavior => prepatch_reproduced). 
- atk_2 (passthrough, no escaping ('"'::s)++['"']) exit=1.
- atk_3 (partial-domain: []-> [] , else gold) exit=1.
- atk_4 (boundary bug: tab 0x09 rendered as \n) exit=1.
- atk_5 (control-flow-effect: prepend accumulation acc := escapeChar c ++ acc, reverses blocks) exit=1.
- atk_6 (ungrounded-oracle echo: impl = ('"'::escapeBody s)++['"'], proof rfl) exit=0. #print axioms => 'does not depend on any axioms' (clean, no sorryAx). This is the spec body verbatim => extensionally == gold; faithful patch = gold patch (materialized above), which RESOLVES (patch_equals_gold=True). Not a weakness.
- atk_7 (drop last char: escapeBody s.dropLast) exit=1.
- atk_pos (gold impl + gold Route-B proof) exit=0; #print axioms => [propext, Quot.sound] (clean).

The only verifying-clean-axiom impls are gold echoes whose faithful patch equals the gold patch and resolves; therefore no impl exhibits verify-but-not-resolve.

Refinement.md leg audit: op#1 delimiters = I; op#2 per-char escape walk = R + A-reference; op#3 else-[c] non-ASCII-literal branch = R (the fix). No A-consumed leg (meta axioms=[], axiom_check.py is skip stub). Single A-reference (json.dumps string-leaf rendering, deep-modeled by escapeChar) validated by G-CONF (conformance_check.py, seed 13512, 200028 draws, 0 mismatch) + verdict.md exhaustive 1.1M scalar-codepoint check. No kind-3 leg; A-reference correspondence to the real json.dumps(...,ensure_ascii=False) callee holds. Documented modeling limitation (lone surrogates unrepresentable in List Char) is honest under-modeling, not exercised by any F2P/PASS value (all scalar).

Verdict SOUND: >=6 distinct genuinely-wrong impls (partial-domain, boundary, control-flow-effect, prepatch, passthrough, drop-last) attacked; none closed. Spec is a slack-free functional equation; verify => extensional gold-equivalence => resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-13512 lean bundle. Modeled function = JSON string-leaf renderer jsonEncodeString(List Char -> List Char), the smallest carrier on which the gold patch's ensure_ascii=True->False flip is observable; real callee = json.dumps(s, ensure_ascii=False). No divergence found on any modeled input.

Evidence:
- same_spec(Solution, Solution_prepatch, LeanBackend.language) = True; spec region byte-identical between patched/prepatch.
- lean_verify.sh Solution.lean exit 0; `#print axioms correct_jsonEncodeString` = [propext, Quot.sound] (NO sorryAx -> proof genuine).
- EXHAUSTIVE single-code-point differential: for every cp in 0..0x10FFFF minus surrogates, spec ('"'::escapeBody[c]++['"']) == json.dumps(chr(cp), ensure_ascii=False) -> 0 mismatches.
- Bundle conformance_check.py: 200028 draws, 0 mismatches, pass. Independent 500k-draw multi-char fuzz over C0 controls/ASCII/quote/backslash/slash/Latin-1/CJK/astral: 0 mismatches. Directed boundaries ('/', U+000B, U+007F, U+001F, U+0020, U+10FFFF, embedded quote/backslash, empty): all agree.

Modeling boundary is sound, not drift: lone surrogates U+D800-U+DFFF are not representable as Lean Char (Char = Unicode scalar values) and are explicitly declared out of scope in mapping.md; every F2P/PASS value (CJK, emoji, Latin diacritics, ASCII) is a scalar string. The spec makes no claim over surrogates, so it is not too strong. escapeChar's `else [c]` branch is exactly the post-patch ensure_ascii=False literal-emission behavior; the prepatch \uXXXX impl is genuinely discriminated. G-CONF conf_skip=false is justified (real R/I content). Spec is FAITHFUL to the real post-patch serializer on all modeled inputs; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified canonical: reconstructed spec_view (impl + proof regions elided per Lean marker rules) hashes to d5d83786e03c898287a4f6ee0c4332f44e49d894dff5b16877db27b9a67f68f7, byte-identical to meta.json spec_view and G-HYGIENE. Spec view = docstring + escapeChar/escapeBody/problem_spec_jsonEncodeString.

The one load-bearing behavioral clause — non-ASCII characters emitted verbatim, NOT expanded to \uXXXX (illustrated by 中 -> "中") — is fully derivable from the PUBLIC problem_statement, which itself shows json.dumps('中国') -> "中国" as the bug, states json.dumps uses ASCII escaping by default, and requests unicode chars display properly (literally) in admin JSONFields. The docstring's 中 example mirrors the statement's own 中国 example.

The spec view does NOT expose gold-edit specifics beyond problem_statement: no ensure_ascii=False flag, no json.dumps/cls/encoder, no file/line, no prepare_value / display_for_field / get_prep_value call sites. Those appear only in mapping.md and refinement.md (audit/reviewer artifacts, not the solver-facing spec view). The remaining escape-table clauses (", \, short control escapes, \u00XX for sub-U+0020) are the standard public JSON string grammar, flag-invariant, not gold-specific. Pinning correct output shape is inherent to any specification and does not disclose the gold mechanism.

Note: hints_text (which discusses ensure_ascii=False, MySQL utf8mb4, and the specific fields.py:1261 line) is explicitly EXCLUDED from the leakage baseline per instructions; even so the spec view does not surface those specifics. Conclusion: no leakage beyond public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
