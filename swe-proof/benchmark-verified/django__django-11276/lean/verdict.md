# P2 adversarial audit — django__django-11276

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,35 +60,27 @@
 
 -- impl-start
 def implementation_escape (s : List Char) : List Char := Id.run do
+  let escapeAlt : Char → List Char := fun c =>
+    if c = '&' then "&amp;".toList
+    else if c = '<' then "&lt;".toList
+    else if c = '>' then "&gt;".toList
+    else if c = '"' then "&quot;".toList
+    else if c = '\'' then "&#39;".toList
+    else [c]
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := acc ++ escapeAlt c
   return acc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` accumulation, generalized over the accumulator,
-computes `init ++ escapeSeq s`. -/
-theorem forIn_escape_helper (s : List Char) : ∀ init,
-    Id.run (forIn s init
-      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
-      = init ++ escapeSeq s := by
-  induction s with
-  | nil => intro init; simp [escapeSeq, Id.run, pure]
-  | cons c cs ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [escapeSeq, List.append_assoc]
-
 theorem correct_escape :
     ∀ (s : List Char),
       problem_spec_escape s (implementation_escape s) := by
   intro s
   unfold problem_spec_escape implementation_escape
-  have h := forIn_escape_helper s []
-  simp only [Id.run] at h ⊢
-  rw [h]
-  simp
+  simp only [Id.run, bind]
+  induction s with
+  | nil => rfl
+  | cons a as ih => simp [escapeSeq, escapeChar, List.append_assoc]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,35 +60,25 @@
 
 -- impl-start
 def implementation_escape (s : List Char) : List Char := Id.run do
+  let escapeAlt : Char → List Char := fun c =>
+    if c = '&' then "&amp;".toList
+    else if c = '<' then "&lt;".toList
+    else if c = '>' then "&gt;".toList
+    else [c]
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := acc ++ escapeAlt c
   return acc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` accumulation, generalized over the accumulator,
-computes `init ++ escapeSeq s`. -/
-theorem forIn_escape_helper (s : List Char) : ∀ init,
-    Id.run (forIn s init
-      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
-      = init ++ escapeSeq s := by
-  induction s with
-  | nil => intro init; simp [escapeSeq, Id.run, pure]
-  | cons c cs ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [escapeSeq, List.append_assoc]
-
 theorem correct_escape :
     ∀ (s : List Char),
       problem_spec_escape s (implementation_escape s) := by
   intro s
   unfold problem_spec_escape implementation_escape
-  have h := forIn_escape_helper s []
-  simp only [Id.run] at h ⊢
-  rw [h]
-  simp
+  simp only [Id.run, bind]
+  induction s with
+  | nil => rfl
+  | cons a as ih => simp [escapeSeq, escapeChar, List.append_assoc]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,33 +62,18 @@
 def implementation_escape (s : List Char) : List Char := Id.run do
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := acc ++ [c]
   return acc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` accumulation, generalized over the accumulator,
-computes `init ++ escapeSeq s`. -/
-theorem forIn_escape_helper (s : List Char) : ∀ init,
-    Id.run (forIn s init
-      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
-      = init ++ escapeSeq s := by
-  induction s with
-  | nil => intro init; simp [escapeSeq, Id.run, pure]
-  | cons c cs ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [escapeSeq, List.append_assoc]
-
 theorem correct_escape :
     ∀ (s : List Char),
       problem_spec_escape s (implementation_escape s) := by
   intro s
   unfold problem_spec_escape implementation_escape
-  have h := forIn_escape_helper s []
-  simp only [Id.run] at h ⊢
-  rw [h]
-  simp
+  simp only [Id.run, bind]
+  induction s with
+  | nil => rfl
+  | cons a as ih => simp [escapeSeq, escapeChar, List.append_assoc]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,34 +61,17 @@
 -- impl-start
 def implementation_escape (s : List Char) : List Char := Id.run do
   let mut acc : List Char := []
-  for c in s do
-    acc := acc ++ escapeChar c
   return acc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` accumulation, generalized over the accumulator,
-computes `init ++ escapeSeq s`. -/
-theorem forIn_escape_helper (s : List Char) : ∀ init,
-    Id.run (forIn s init
-      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
-      = init ++ escapeSeq s := by
-  induction s with
-  | nil => intro init; simp [escapeSeq, Id.run, pure]
-  | cons c cs ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [escapeSeq, List.append_assoc]
-
 theorem correct_escape :
     ∀ (s : List Char),
       problem_spec_escape s (implementation_escape s) := by
   intro s
   unfold problem_spec_escape implementation_escape
-  have h := forIn_escape_helper s []
-  simp only [Id.run] at h ⊢
-  rw [h]
-  simp
+  simp only [Id.run, bind]
+  induction s with
+  | nil => rfl
+  | cons a as ih => simp [escapeSeq, escapeChar]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,35 +60,27 @@
 
 -- impl-start
 def implementation_escape (s : List Char) : List Char := Id.run do
+  let escapeAlt : Char → List Char := fun c =>
+    if c = '&' then "&amp;".toList
+    else if c = '<' then "&gt;".toList
+    else if c = '>' then "&lt;".toList
+    else if c = '"' then "&quot;".toList
+    else if c = '\'' then "&#x27;".toList
+    else [c]
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := acc ++ escapeAlt c
   return acc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` accumulation, generalized over the accumulator,
-computes `init ++ escapeSeq s`. -/
-theorem forIn_escape_helper (s : List Char) : ∀ init,
-    Id.run (forIn s init
-      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
-      = init ++ escapeSeq s := by
-  induction s with
-  | nil => intro init; simp [escapeSeq, Id.run, pure]
-  | cons c cs ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [escapeSeq, List.append_assoc]
-
 theorem correct_escape :
     ∀ (s : List Char),
       problem_spec_escape s (implementation_escape s) := by
   intro s
   unfold problem_spec_escape implementation_escape
-  have h := forIn_escape_helper s []
-  simp only [Id.run] at h ⊢
-  rw [h]
-  simp
+  simp only [Id.run, bind]
+  induction s with
+  | nil => rfl
+  | cons a as ih => simp [escapeSeq, escapeChar, List.append_assoc]
 -- proof-end
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,35 +60,27 @@
 
 -- impl-start
 def implementation_escape (s : List Char) : List Char := Id.run do
+  let escapeAlt : Char → List Char := fun c =>
+    if c = '&' then "&amp;&amp;".toList
+    else if c = '<' then "&lt;".toList
+    else if c = '>' then "&gt;".toList
+    else if c = '"' then "&quot;".toList
+    else if c = '\'' then "&#x27;".toList
+    else [c]
   let mut acc : List Char := []
   for c in s do
-    acc := acc ++ escapeChar c
+    acc := acc ++ escapeAlt c
   return acc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` accumulation, generalized over the accumulator,
-computes `init ++ escapeSeq s`. -/
-theorem forIn_escape_helper (s : List Char) : ∀ init,
-    Id.run (forIn s init
-      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
-      = init ++ escapeSeq s := by
-  induction s with
-  | nil => intro init; simp [escapeSeq, Id.run, pure]
-  | cons c cs ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [escapeSeq, List.append_assoc]
-
 theorem correct_escape :
     ∀ (s : List Char),
       problem_spec_escape s (implementation_escape s) := by
   intro s
   unfold problem_spec_escape implementation_escape
-  have h := forIn_escape_helper s []
-  simp only [Id.run] at h ⊢
-  rw [h]
-  simp
+  simp only [Id.run, bind]
+  induction s with
+  | nil => rfl
+  | cons a as ih => simp [escapeSeq, escapeChar, List.append_assoc]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Escaping arbitrary text so that it may be safely embedded in HTML.

The transformation walks the input one code point at a time and rewrites the
five characters that carry syntactic meaning in HTML into their corresponding
character-reference entities, leaving every other code point untouched:

* `&` becomes `&amp;`
* `<` becomes `&lt;`
* `>` becomes `&gt;`
* `"` becomes `&quot;`
* `'` becomes `&#x27;`

Every other character maps to itself. The result is the concatenation, in
order, of the per-code-point encodings; the encoding is applied
unconditionally, so already-encoded input is encoded again (its leading `&`
is re-escaped). Only the relative order and the above substitutions determine
the output — no other characters are altered, inserted, or removed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- per-code-point HTML encoding is modeled DEEPLY over the observable input
-- (the list of characters of the text) as `escapeSeq`, so no `opaque`/`axiom`
-- callee contract is needed; its faithfulness to the standard encoder is
-- validated by the mechanical differential check.
-- axioms-end

-- pure-start
/-- The HTML character-reference encoding of a single code point: the five
HTML-significant characters map to their entity form; every other character
maps to itself. -/
def escapeChar (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/-- The HTML encoding of a whole text: the in-order concatenation of the
per-code-point encodings. Front-recursive so it pairs with an accumulating
loop. -/
def escapeSeq : List Char → List Char
  | [] => []
  | c :: cs => escapeChar c ++ escapeSeq cs
-- pure-end

-- post-conditions-start
/-- The escaped text is exactly the in-order concatenation of the per-code-point
HTML encodings of the input characters. This pins the full output to the input:
its length, character order, and every substitution are determined, so no other
result can satisfy it. -/
def problem_spec_escape (s : List Char) (result : List Char) : Prop :=
  result = escapeSeq s
-- post-conditions-end

-- impl-start
def implementation_escape (s : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in s do
    acc := acc ++ escapeChar c
  return acc
-- impl-end

-- proof-start
/-- The desugared `forIn` accumulation, generalized over the accumulator,
computes `init ++ escapeSeq s`. -/
theorem forIn_escape_helper (s : List Char) : ∀ init,
    Id.run (forIn s init
      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
      = init ++ escapeSeq s := by
  induction s with
  | nil => intro init; simp [escapeSeq, Id.run, pure]
  | cons c cs ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [escapeSeq, List.append_assoc]

theorem correct_escape :
    ∀ (s : List Char),
      problem_spec_escape s (implementation_escape s) := by
  intro s
  unfold problem_spec_escape implementation_escape
  have h := forIn_escape_helper s []
  simp only [Id.run] at h ⊢
  rw [h]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE. problem_spec_escape s result := (result = escapeSeq s) is a TOTAL functional equality: the output is pinned exactly to the deterministic escapeSeq. Both impl and proof regions are collapsed in the Lean spec_view (markers.py _lean_spec_view), so all attacks below keep same_spec=True (confirmed True for all 7 via swebench_unified.markers.same_spec + LeanBackend). Positive control (unmodified Solution.lean) verifies: lean_verify.sh exit 0.

atk_1 (PREPATCH BUG: apostrophe -> &#39; decimal instead of &#x27; hex): same_spec=True; EXIT=1 (error: unsolved goals @ correct_escape). Reproduces the exact pre-patch defect / F2P discriminator. REJECTED (good).
- atk_2 (PARTIAL-DOMAIN: only &,<,> escaped; " and ' pass through as identity): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
- atk_3 (IDENTITY: returns input unchanged, no escaping): same_spec=True; EXIT=1 (unsolved goals). REJECTED. adversary.check_attack -> {same_spec:True, verifies:False}.
- atk_4 (BOUNDARY/EMPTY: always returns [] regardless of input): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
- atk_5 (CONTROL-FLOW-EFFECT: swaps < and > encodings, &lt;/&gt; transposed): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
- atk_7 (DUPLICATION bug: '&' -> "&amp;&amp;"): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
All six honest wrong impls fail with `error: unsolved goals` at the correct_escape theorem — the exact-equality post-condition reduces each to a genuinely FALSE character-list equality on the diverging input, which Lean (sound) cannot discharge. No wrong impl closes with clean axioms => per protocol step 2 NO resolve run is required or possible (patches={}).

CONTROL atk_6 (behaviorally CORRECT foldr formulation): same_spec=True; EXIT=0; #print axioms correct_escape -> [propext] only. Confirms a correctly-behaving alternative impl verifies cleanly (the spec is not vacuously unsatisfiable / not too strong).

FORGERY PROBE atk_8 (identity impl WRONG, proof closed by self-injected `axiom escape_cheat`): lean_verify.sh EXIT=0 and adversary.check_attack reports verifies=True — BUT `#print axioms correct_escape` -> [escape_cheat, propext], i.e. NOT clean. This does NOT meet the break condition (which requires a closing proof with a CLEAN #print axioms), so it is proof forgery, NOT a spec weakness; I deliberately do NOT submit it as a breaking attack.

NOTE for maintainers (harness-hygiene, out of scope for this spec's soundness): gates/_lean_axioms.check_proof_axioms builds its allowed-axiom set via declared_axiom_names(src) which scans the WHOLE FILE (not just the axioms region) and is not cross-checked against meta.json axioms=[]; verified live that check_proof_axioms(atk_8) returns ok=True 'axioms clean' with reported {'correct_escape': ['escape_cheat','propext']}. G-VERIFY/G-HYGIENE would thus accept a proof forged by an axiom declared in the proof region. This is a general Lean-backend gate observation, not specific to django-11276, and it does not affect THIS bundle's verify=>correct soundness (the committed Solution.lean's proof depends only on [propext]/standard axioms).

Also note the adversary.check_attack primitive used by the audit re-derivation does NOT call check_proof_axioms at all (only compile+sorry via check_bundle_file), so a forged-axiom attack would register verifies=True in the audit pipeline — flagged for hygiene, but not exploited here since the clean-axiom bar is part of the break definition.

REFINEMENT.MD A-LEG AUDIT. Legs: row1 R (str<->List Char per-code-point), row2 I, row3 R (iterate str code points <-> for c in List Char), row4 A-reference (escapeChar/escapeSeq deep-models html.escape(quote=True)), row5 I; two 'outside boundary' identity rows (mark_safe, str) not modeled. No kind-3 (changed-inexpressible) leg; meta.json axioms=[] (no A-consumed). Correspondence of the single A-reference (row4) holds: escapeChar's five substitutions {&->&amp;,<->&lt;,>->&gt;,\"->&quot;,'->&#x27;} match html.escape default exactly; order-independence is real because none of the five replacement strings reintroduces a target char, so html.escape's whole-string .replace chain equals a left-to-right per-code-point map (= escapeSeq). axiom_check.py drives the REAL html.escape per code point (0..0x250 + significant 5 + astral) AND whole-string over edges + 1e5 fuzz; conformance_check.py diffs shadow vs real html.escape over edges + 1.5e5 fuzz (seed 11276). The A-reference is validated == the real callee, and the deep-model choice is correct per s0.7 (the changed op must be modeled deeply, not axiomatized). R/I legs are mechanically covered by G-CONF (G-CONF territory per instructions).

VERDICT: SOUND. 6 distinct same-spec wrong impls (prepatch bug + partial-domain + identity + boundary/empty + control-flow-effect + duplication) all fail to verify; only a behaviorally-correct impl verifies; the sole verifying wrong impl relies on a forged axiom that violates the clean-#print-axioms break condition. The exact functional-equality post-condition admits no verify-clean wrong implementation, so verify=>correct holds for this bundle. (Independent harness-hygiene note on whole-file axiom whitelisting recorded above for maintainers.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Escaping arbitrary text so that it may be safely embedded in HTML.

The transformation walks the input one code point at a time and rewrites the
five characters that carry syntactic meaning in HTML into their corresponding
character-reference entities, leaving every other code point untouched:

* `&` becomes `&amp;`
* `<` becomes `&lt;`
* `>` becomes `&gt;`
* `"` becomes `&quot;`
* `'` becomes `&#x27;`

Every other character maps to itself. The result is the concatenation, in
order, of the per-code-point encodings; the encoding is applied
unconditionally, so already-encoded input is encoded again (its leading `&`
is re-escaped). Only the relative order and the above substitutions determine
the output — no other characters are altered, inserted, or removed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- per-code-point HTML encoding is modeled DEEPLY over the observable input
-- (the list of characters of the text) as `escapeSeq`, so no `opaque`/`axiom`
-- callee contract is needed; its faithfulness to the standard encoder is
-- validated by the mechanical differential check.
-- axioms-end

-- pure-start
/-- The HTML character-reference encoding of a single code point: the five
HTML-significant characters map to their entity form; every other character
maps to itself. -/
def escapeChar (c : Char) : List Char :=
  if c = '&' then "&amp;".toList
  else if c = '<' then "&lt;".toList
  else if c = '>' then "&gt;".toList
  else if c = '"' then "&quot;".toList
  else if c = '\'' then "&#x27;".toList
  else [c]

/-- The HTML encoding of a whole text: the in-order concatenation of the
per-code-point encodings. Front-recursive so it pairs with an accumulating
loop. -/
def escapeSeq : List Char → List Char
  | [] => []
  | c :: cs => escapeChar c ++ escapeSeq cs
-- pure-end

-- post-conditions-start
/-- The escaped text is exactly the in-order concatenation of the per-code-point
HTML encodings of the input characters. This pins the full output to the input:
its length, character order, and every substitution are determined, so no other
result can satisfy it. -/
def problem_spec_escape (s : List Char) (result : List Char) : Prop :=
  result = escapeSeq s
-- post-conditions-end

-- impl-start
def implementation_escape (s : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in s do
    acc := acc ++ escapeChar c
  return acc
-- impl-end

-- proof-start
/-- The desugared `forIn` accumulation, generalized over the accumulator,
computes `init ++ escapeSeq s`. -/
theorem forIn_escape_helper (s : List Char) : ∀ init,
    Id.run (forIn s init
      (fun c r => do pure PUnit.unit; pure (ForInStep.yield (r ++ escapeChar c))))
      = init ++ escapeSeq s := by
  induction s with
  | nil => intro init; simp [escapeSeq, Id.run, pure]
  | cons c cs ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [escapeSeq, List.append_assoc]

theorem correct_escape :
    ∀ (s : List Char),
      problem_spec_escape s (implementation_escape s) := by
  intro s
  unfold problem_spec_escape implementation_escape
  have h := forIn_escape_helper s []
  simp only [Id.run] at h ⊢
  rw [h]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE. problem_spec_escape s result := (result = escapeSeq s) is a TOTAL functional equality: the output is pinned exactly to the deterministic escapeSeq. Both impl and proof regions are collapsed in the Lean spec_view (markers.py _lean_spec_view), so all attacks below keep same_spec=True (confirmed True for all 7 via swebench_unified.markers.same_spec + LeanBackend). Positive control (unmodified Solution.lean) verifies: lean_verify.sh exit 0.

atk_1 (PREPATCH BUG: apostrophe -> &#39; decimal instead of &#x27; hex): same_spec=True; EXIT=1 (error: unsolved goals @ correct_escape). Reproduces the exact pre-patch defect / F2P discriminator. REJECTED (good).
- atk_2 (PARTIAL-DOMAIN: only &,<,> escaped; " and ' pass through as identity): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
- atk_3 (IDENTITY: returns input unchanged, no escaping): same_spec=True; EXIT=1 (unsolved goals). REJECTED. adversary.check_attack -> {same_spec:True, verifies:False}.
- atk_4 (BOUNDARY/EMPTY: always returns [] regardless of input): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
- atk_5 (CONTROL-FLOW-EFFECT: swaps < and > encodings, &lt;/&gt; transposed): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
- atk_7 (DUPLICATION bug: '&' -> "&amp;&amp;"): same_spec=True; EXIT=1 (unsolved goals). REJECTED.
All six honest wrong impls fail with `error: unsolved goals` at the correct_escape theorem — the exact-equality post-condition reduces each to a genuinely FALSE character-list equality on the diverging input, which Lean (sound) cannot discharge. No wrong impl closes with clean axioms => per protocol step 2 NO resolve run is required or possible (patches={}).

CONTROL atk_6 (behaviorally CORRECT foldr formulation): same_spec=True; EXIT=0; #print axioms correct_escape -> [propext] only. Confirms a correctly-behaving alternative impl verifies cleanly (the spec is not vacuously unsatisfiable / not too strong).

FORGERY PROBE atk_8 (identity impl WRONG, proof closed by self-injected `axiom escape_cheat`): lean_verify.sh EXIT=0 and adversary.check_attack reports verifies=True — BUT `#print axioms correct_escape` -> [escape_cheat, propext], i.e. NOT clean. This does NOT meet the break condition (which requires a closing proof with a CLEAN #print axioms), so it is proof forgery, NOT a spec weakness; I deliberately do NOT submit it as a breaking attack.

NOTE for maintainers (harness-hygiene, out of scope for this spec's soundness): gates/_lean_axioms.check_proof_axioms builds its allowed-axiom set via declared_axiom_names(src) which scans the WHOLE FILE (not just the axioms region) and is not cross-checked against meta.json axioms=[]; verified live that check_proof_axioms(atk_8) returns ok=True 'axioms clean' with reported {'correct_escape': ['escape_cheat','propext']}. G-VERIFY/G-HYGIENE would thus accept a proof forged by an axiom declared in the proof region. This is a general Lean-backend gate observation, not specific to django-11276, and it does not affect THIS bundle's verify=>correct soundness (the committed Solution.lean's proof depends only on [propext]/standard axioms).

Also note the adversary.check_attack primitive used by the audit re-derivation does NOT call check_proof_axioms at all (only compile+sorry via check_bundle_file), so a forged-axiom attack would register verifies=True in the audit pipeline — flagged for hygiene, but not exploited here since the clean-axiom bar is part of the break definition.

REFINEMENT.MD A-LEG AUDIT. Legs: row1 R (str<->List Char per-code-point), row2 I, row3 R (iterate str code points <-> for c in List Char), row4 A-reference (escapeChar/escapeSeq deep-models html.escape(quote=True)), row5 I; two 'outside boundary' identity rows (mark_safe, str) not modeled. No kind-3 (changed-inexpressible) leg; meta.json axioms=[] (no A-consumed). Correspondence of the single A-reference (row4) holds: escapeChar's five substitutions {&->&amp;,<->&lt;,>->&gt;,\"->&quot;,'->&#x27;} match html.escape default exactly; order-independence is real because none of the five replacement strings reintroduces a target char, so html.escape's whole-string .replace chain equals a left-to-right per-code-point map (= escapeSeq). axiom_check.py drives the REAL html.escape per code point (0..0x250 + significant 5 + astral) AND whole-string over edges + 1e5 fuzz; conformance_check.py diffs shadow vs real html.escape over edges + 1.5e5 fuzz (seed 11276). The A-reference is validated == the real callee, and the deep-model choice is correct per s0.7 (the changed op must be modeled deeply, not axiomatized). R/I legs are mechanically covered by G-CONF (G-CONF territory per instructions).

VERDICT: SOUND. 6 distinct same-spec wrong impls (prepatch bug + partial-domain + identity + boundary/empty + control-flow-effect + duplication) all fail to verify; only a behaviorally-correct impl verifies; the sole verifying wrong impl relies on a forged axiom that violates the clean-#print-axioms break condition. The exact functional-equality post-condition admits no verify-clean wrong implementation, so verify=>correct holds for this bundle. (Independent harness-hygiene note on whole-file axiom whitelisting recorded above for maintainers.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function escape(text) post-patch = mark_safe(html.escape(str(text))) (confirmed: `return SafeString(html.escape(str(text)))`). Spec models the string->string encoding as escapeSeq (per-code-point escapeChar map): &->&amp;, <->&lt;, >->&gt;, "->&quot;, '->&#x27;, else identity; mark_safe/str() are identity on the char sequence (faithful — mark_safe only tags SafeString). Differential test of escapeSeq vs REAL html.escape(quote=True, the Django call-site default): boundary set + 300k+200k fuzzed inputs (astral, control, U+2028/29, pre-encoded &amp;/&#39;) + EXHAUSTIVE over dangerous alphabet up to length 3 => 0 divergences. The only genuine modeling hazard (sequential .replace() ordering vs per-char map) is safe because '&' is replaced first and no replacement text reintroduces <>"', so the chain equals a left-to-right per-code-point map. Lean compiles (exit 0, no sorry); #print axioms correct_escape = [propext, Quot.sound] (clean, no sorryAx). Spec region byte-identical across Solution/Solution_prepatch (same_spec=True); sole diff is the '->&#x27; (post) vs &#39; (pre) discriminating clause = the gold behavioral change. No input where the spec disagrees with the real callee; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Computed the spec view via swebench_unified.markers.spec_view(Solution.lean, LeanBackend); impl and proof regions are correctly elided. same_spec(Solution.lean, Solution_prepatch.lean)=True confirmed — the spec region is byte-identical across the patch, so nothing gold-distinguishing lives outside the elided impl/proof.

Spec view = docstring + escapeChar/escapeSeq pure region + problem_spec_escape post-condition. It discloses the per-code-point HTML encoding, including the single behavioral discriminator the gold edit introduces: ' -> &#x27; (pre-patch was &#39;). That exact fact is ALREADY PUBLIC in problem_statement verbatim: 'html.escape() converts ' to &#x27 rather than &#39.' Also, the overall strategy ('Use Python stdlib html.escape()') is the problem_statement's title. The other four substitutions (&,<,>,") are standard, universally-known HTML escaping and are byte-identical across the patch, so they reveal nothing about the gold edit.

The spec view never names html.escape, str.translate, or the _html_escapes table — those appear only in refinement.md / mapping.md / meta.json, which are NOT the spec view. No spec-view line reveals the gold edit beyond the public problem_statement. Leakage judged against problem_statement only (hints_text was empty). Concur with recorded G-PANEL-3 pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.