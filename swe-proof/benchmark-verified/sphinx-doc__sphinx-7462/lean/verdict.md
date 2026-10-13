# P2 adversarial audit — sphinx-doc__sphinx-7462

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,8 +64,6 @@
 -- impl-start
 def implementation_renderTupleSig
     (elems : List (List SigToken)) : List SigToken := Id.run do
-  if elems.isEmpty then
-    return [SigToken.punct "(", SigToken.punct ")"]
   let mut result : List SigToken := []
   for elem in elems do
     result := result ++ elem
@@ -97,20 +95,9 @@
       problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
   intro elems
   unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
-  by_cases h : elems.isEmpty
-  · simp [h, Id.run, pure]
-  · simp only [h, Id.run]
-    have hbridge :
-        (do
-          pure PUnit.unit
-          let r ← forIn elems ([] : List SigToken) fun elem r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
-          pure r.dropLast : Id (List SigToken))
-        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
-            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
-    rw [hbridge, helper_renderTupleSig]
-    simp [pure]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, List.forIn_cons, helper_renderTupleSig] <;>
+    (try rfl) <;> (try simp_all)
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,6 @@
 -- impl-start
 def implementation_renderTupleText
     (elems : List String) : String := Id.run do
-  if elems.isEmpty then
-    return "()"
   return String.intercalate ", " elems
 -- impl-end
 
@@ -135,5 +133,6 @@
       problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by
   intro elems
   unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText
-  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, String.intercalate] <;> (try rfl)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
 def implementation_renderTupleSig
     (elems : List (List SigToken)) : List SigToken := Id.run do
   if elems.isEmpty then
-    return [SigToken.punct "(", SigToken.punct ")"]
+    return [SigToken.punct "()"]
   let mut result : List SigToken := []
   for elem in elems do
     result := result ++ elem
@@ -97,20 +97,9 @@
       problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
   intro elems
   unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
-  by_cases h : elems.isEmpty
-  · simp [h, Id.run, pure]
-  · simp only [h, Id.run]
-    have hbridge :
-        (do
-          pure PUnit.unit
-          let r ← forIn elems ([] : List SigToken) fun elem r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
-          pure r.dropLast : Id (List SigToken))
-        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
-            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
-    rw [hbridge, helper_renderTupleSig]
-    simp [pure]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, List.forIn_cons, helper_renderTupleSig] <;>
+    (try rfl) <;> (try simp_all)
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,7 +125,7 @@
 def implementation_renderTupleText
     (elems : List String) : String := Id.run do
   if elems.isEmpty then
-    return "()"
+    return "( )"
   return String.intercalate ", " elems
 -- impl-end
 
@@ -135,5 +135,6 @@
       problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by
   intro elems
   unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText
-  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, String.intercalate] <;> (try rfl)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   for elem in elems do
     result := result ++ elem
     result := result ++ [SigToken.punct ", "]
-  return result.dropLast
+  return result
 -- impl-end
 
 -- proof-start
@@ -97,20 +97,9 @@
       problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
   intro elems
   unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
-  by_cases h : elems.isEmpty
-  · simp [h, Id.run, pure]
-  · simp only [h, Id.run]
-    have hbridge :
-        (do
-          pure PUnit.unit
-          let r ← forIn elems ([] : List SigToken) fun elem r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
-          pure r.dropLast : Id (List SigToken))
-        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
-            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
-    rw [hbridge, helper_renderTupleSig]
-    simp [pure]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, List.forIn_cons, helper_renderTupleSig] <;>
+    (try rfl) <;> (try simp_all)
 -- proof-end
 
 -- post-conditions-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,7 +69,7 @@
   let mut result : List SigToken := []
   for elem in elems do
     result := result ++ elem
-    result := result ++ [SigToken.punct ", "]
+    result := result ++ [SigToken.punct ","]
   return result.dropLast
 -- impl-end
 
@@ -97,20 +97,9 @@
       problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
   intro elems
   unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
-  by_cases h : elems.isEmpty
-  · simp [h, Id.run, pure]
-  · simp only [h, Id.run]
-    have hbridge :
-        (do
-          pure PUnit.unit
-          let r ← forIn elems ([] : List SigToken) fun elem r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
-          pure r.dropLast : Id (List SigToken))
-        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
-            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
-    rw [hbridge, helper_renderTupleSig]
-    simp [pure]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, List.forIn_cons, helper_renderTupleSig] <;>
+    (try rfl) <;> (try simp_all)
 -- proof-end
 
 -- post-conditions-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -63,14 +63,8 @@
 
 -- impl-start
 def implementation_renderTupleSig
-    (elems : List (List SigToken)) : List SigToken := Id.run do
-  if elems.isEmpty then
-    return [SigToken.punct "(", SigToken.punct ")"]
-  let mut result : List SigToken := []
-  for elem in elems do
-    result := result ++ elem
-    result := result ++ [SigToken.punct ", "]
-  return result.dropLast
+    (elems : List (List SigToken)) : List SigToken :=
+  assembleTupleSig elems
 -- impl-end
 
 -- proof-start
@@ -96,21 +90,7 @@
     ∀ (elems : List (List SigToken)),
       problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
   intro elems
-  unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
-  by_cases h : elems.isEmpty
-  · simp [h, Id.run, pure]
-  · simp only [h, Id.run]
-    have hbridge :
-        (do
-          pure PUnit.unit
-          let r ← forIn elems ([] : List SigToken) fun elem r => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
-          pure r.dropLast : Id (List SigToken))
-        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
-            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
-    rw [hbridge, helper_renderTupleSig]
-    simp [pure]
+  rfl
 -- proof-end
 
 -- post-conditions-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,7 +126,7 @@
     (elems : List String) : String := Id.run do
   if elems.isEmpty then
     return "()"
-  return String.intercalate ", " elems
+  return String.intercalate "," elems
 -- impl-end
 
 -- proof-start
@@ -135,5 +135,6 @@
       problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by
   intro elems
   unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText
-  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]
+  by_cases h : elems.isEmpty <;>
+    simp_all [Id.run, pure, bind, String.intercalate] <;> (try rfl)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the inline display of a parenthesised sequence (a tuple) from the
already-rendered displays of its individual elements.

Each element has already been rendered to a small list of display tokens. The
sequence display is formed by laying the element displays out in order,
separated by a comma-and-space token. A non-empty sequence therefore renders as
`e₀ , e₁ , … , eₙ` (the elements interleaved with the separator, with no
trailing separator). The empty sequence is a special case: it has no elements to
interleave, and must render as the literal opening and closing parentheses
`(` `)` so that an empty sequence still produces a visible, well-formed display.

A second view renders the same sequence as flat source text instead of display
tokens: the element texts joined by a comma-and-space, except that the empty
sequence renders as the two-character text `()`.
-/

-- axioms-start
-- The per-element renderer (which turns one element into its already-rendered
-- form) is an UNCHANGED collaborator. It is represented here by leaving the
-- elements themselves as arbitrary inputs (`elems`), universally quantified in
-- the correctness statements, so the contract holds for every possible
-- per-element rendering. No `opaque`/`axiom` callee contract is consumed; the
-- sequence-assembly rule that the specification pins is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- A single display token: either a punctuation token carrying its literal
text, or a textual/cross-reference token carrying its text. This is the abstract
carrier for the rendered display pieces. -/
inductive SigToken where
  | punct : String → SigToken
  | text  : String → SigToken
  deriving DecidableEq, Repr

/-- Assemble the display-token rendering of a sequence from the per-element
renderings `elems`. The empty sequence renders as the parenthesis pair; a
non-empty sequence lays the element renderings out in order, each followed by a
separator token, then drops the single trailing separator. -/
def assembleTupleSig (elems : List (List SigToken)) : List SigToken :=
  if elems.isEmpty then
    [SigToken.punct "(", SigToken.punct ")"]
  else
    ((elems.map (fun e => e ++ [SigToken.punct ", "])).flatten).dropLast

/-- Assemble the flat source-text rendering of a sequence from the per-element
texts `elems`. The empty sequence renders as `()`; a non-empty sequence joins
the element texts with a comma-and-space. -/
def assembleTupleText (elems : List String) : String :=
  if elems.isEmpty then "()" else String.intercalate ", " elems
-- pure-end

-- post-conditions-start
/-- The display-token rendering equals the interleaved, trailing-separator-free
layout of the element renderings, with the empty sequence rendered as `()`. -/
def problem_spec_renderTupleSig
    (elems : List (List SigToken)) (result : List SigToken) : Prop :=
  result = assembleTupleSig elems
-- post-conditions-end

-- impl-start
def implementation_renderTupleSig
    (elems : List (List SigToken)) : List SigToken := Id.run do
  if elems.isEmpty then
    return [SigToken.punct "(", SigToken.punct ")"]
  let mut result : List SigToken := []
  for elem in elems do
    result := result ++ elem
    result := result ++ [SigToken.punct ", "]
  return result.dropLast
-- impl-end

-- proof-start
/-- Loop body of `implementation_renderTupleSig`, generalized over the
accumulator: folding `r ↦ r ++ elem ++ [sep]` over the elements appends, in
order, each element followed by the separator. -/
theorem helper_renderTupleSig (sep : SigToken) :
    ∀ (elems : List (List SigToken)) (init : List SigToken),
      Id.run (forIn elems init (fun elem r =>
        (pure (ForInStep.yield (r ++ elem ++ [sep])) : Id _)))
      = init ++ (elems.map (fun e => e ++ [sep])).flatten := by
  intro elems
  induction elems with
  | nil => intro init; simp [Id.run, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_renderTupleSig :
    ∀ (elems : List (List SigToken)),
      problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
  intro elems
  unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
  by_cases h : elems.isEmpty
  · simp [h, Id.run, pure]
  · simp only [h, Id.run]
    have hbridge :
        (do
          pure PUnit.unit
          let r ← forIn elems ([] : List SigToken) fun elem r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
          pure r.dropLast : Id (List SigToken))
        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
    rw [hbridge, helper_renderTupleSig]
    simp [pure]
-- proof-end

-- post-conditions-start
/-- The flat source-text rendering equals the comma-and-space join of the
element texts, with the empty sequence rendered as `()`. -/
def problem_spec_renderTupleText
    (elems : List String) (result : String) : Prop :=
  result = assembleTupleText elems
-- post-conditions-end

-- impl-start
def implementation_renderTupleText
    (elems : List String) : String := Id.run do
  if elems.isEmpty then
    return "()"
  return String.intercalate ", " elems
-- impl-end

-- proof-start
theorem correct_renderTupleText :
    ∀ (elems : List String),
      problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by
  intro elems
  unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText
  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for sphinx-doc__sphinx-7462 / lean. All work Verifier: `bash scripts/lean_verify.sh <file>` (exit0=verifies/no-sorry, 1=error). same_spec confirmed True for ALL 8 attacks via swebench_unified.markers.same_spec (get_backend('lean')) — impl-only edits, axioms/pure/pre/post byte-identical.

SPEC SHAPE: both post-conditions are EXACT FUNCTIONAL EQUALITY to a deeply-modeled function: problem_spec_renderTupleSig elems result := result = assembleTupleSig elems; problem_spec_renderTupleText elems result := result = assembleTupleText elems. Therefore any implementation_* whose correct_* closes is pointwise-equal to gold on EVERY input, so its faithful Python transliteration necessarily reproduces gold behavior incl. the discriminating empty-tuple case and resolves the F2P tests. A closing-but-non-resolving impl cannot exist by construction.

### ATTACKS (8 distinct same-spec wrong/echo impls; verifications run concurrently ≤4 as background jobs):
- atk_1 (prepatch bug 1 / control-flow-effect): Sig drops empty branch → [] on empty. lean_verify exit=1 (cannot close; empty goal []=[punct "(",punct ")"]).
- atk_2 (prepatch bug 2): Text drops empty branch → "" on empty. exit=1 (goal ""="()").
- atk_3 (partial-domain/boundary): Sig empty → [punct "()"] (single token, wrong shape). exit=1.
- atk_4 (boundary): Text empty → "( )" (space) instead of "()". exit=1.
- atk_5 (control-flow-effect): Sig omits dropLast → trailing separator kept. exit=1.
- atk_6 (wrong-separator): Sig uses punct "," instead of punct ", ". exit=1.
- atk_7 (ungrounded-oracle ECHO): Sig impl literally = assembleTupleSig elems (extensionally identical to gold; Text unchanged gold). lean_verify exit=0; #print axioms correct_renderTupleSig → 'does not depend on any axioms', correct_renderTupleText → [propext] — CLEAN (no sorryAx). Its faithful patch = the GOLD post-patch (extensional equality). MATERIALIZED at atk_7.patch and RUN through official harness: SBU_BENCHMARK=swe_bench_verified run_resolve('sphinx-doc__sphinx-7462', patch, timeout=1800, retries=1) → RESOLVED: True, completed: True, note='resolved'. So the ONLY closing-clean-axiom attack RESOLVES — spec NOT broken.
- atk_8 (wrong-separator text): Text non-empty joins with "," (no space). exit=1.

POSITIVE CONTROL: verbatim Solution.lean → lean_verify exit=0 (verifies).
prepatch_reproduced=true: atk_1 = Solution_prepatch_1 bug (Sig IndexError/empty path), atk_2 = Solution_prepatch_2 bug (Text "" instead of "()"), both fail the frozen gold proof, matching bundle G-DIFF.

REFINEMENT AUDIT: refinement.md has ONLY R and I legs; NO A-legs and NO kind-3. The sole collaborator (recursive per-element renderer unparse(elem)) is UNCHANGED and represented by leaving already-rendered elements as arbitrary ∀-quantified inputs (elems) — legitimate deep modeling per SPEC_GUIDE §0.7/§3, not an axiomatized changed op. G-AX is a correct skip stub (axiom_check.py). R/I correspondence to the real callees VERIFIED against the gold patch: Sig empty→[desc_sig_punctuation('','('),desc_sig_punctuation('','')] ↔ [punct "(",punct ")"]; non-empty extend/append/pop() ↔ map(·++[sep])|>.flatten|>.dropLast; Text empty→"()"; non-empty ", ".join ↔ String.intercalate ", ". No drift. G-CONF differential (oracle=faithful post-patch replica, 120k fuzz, seed 7462) passes.

CONCLUSION: ≥5 (8) distinct same-spec attacks run + verified; 7 genuinely-wrong impls cannot close (exact-equality spec maximally constrains result); the single closing clean-axiom impl (atk_7 echo) has a materialized faithful patch that RESOLVES under the official harness. verify⇒correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the inline display of a parenthesised sequence (a tuple) from the
already-rendered displays of its individual elements.

Each element has already been rendered to a small list of display tokens. The
sequence display is formed by laying the element displays out in order,
separated by a comma-and-space token. A non-empty sequence therefore renders as
`e₀ , e₁ , … , eₙ` (the elements interleaved with the separator, with no
trailing separator). The empty sequence is a special case: it has no elements to
interleave, and must render as the literal opening and closing parentheses
`(` `)` so that an empty sequence still produces a visible, well-formed display.

A second view renders the same sequence as flat source text instead of display
tokens: the element texts joined by a comma-and-space, except that the empty
sequence renders as the two-character text `()`.
-/

-- axioms-start
-- The per-element renderer (which turns one element into its already-rendered
-- form) is an UNCHANGED collaborator. It is represented here by leaving the
-- elements themselves as arbitrary inputs (`elems`), universally quantified in
-- the correctness statements, so the contract holds for every possible
-- per-element rendering. No `opaque`/`axiom` callee contract is consumed; the
-- sequence-assembly rule that the specification pins is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- A single display token: either a punctuation token carrying its literal
text, or a textual/cross-reference token carrying its text. This is the abstract
carrier for the rendered display pieces. -/
inductive SigToken where
  | punct : String → SigToken
  | text  : String → SigToken
  deriving DecidableEq, Repr

/-- Assemble the display-token rendering of a sequence from the per-element
renderings `elems`. The empty sequence renders as the parenthesis pair; a
non-empty sequence lays the element renderings out in order, each followed by a
separator token, then drops the single trailing separator. -/
def assembleTupleSig (elems : List (List SigToken)) : List SigToken :=
  if elems.isEmpty then
    [SigToken.punct "(", SigToken.punct ")"]
  else
    ((elems.map (fun e => e ++ [SigToken.punct ", "])).flatten).dropLast

/-- Assemble the flat source-text rendering of a sequence from the per-element
texts `elems`. The empty sequence renders as `()`; a non-empty sequence joins
the element texts with a comma-and-space. -/
def assembleTupleText (elems : List String) : String :=
  if elems.isEmpty then "()" else String.intercalate ", " elems
-- pure-end

-- post-conditions-start
/-- The display-token rendering equals the interleaved, trailing-separator-free
layout of the element renderings, with the empty sequence rendered as `()`. -/
def problem_spec_renderTupleSig
    (elems : List (List SigToken)) (result : List SigToken) : Prop :=
  result = assembleTupleSig elems
-- post-conditions-end

-- impl-start
def implementation_renderTupleSig
    (elems : List (List SigToken)) : List SigToken := Id.run do
  if elems.isEmpty then
    return [SigToken.punct "(", SigToken.punct ")"]
  let mut result : List SigToken := []
  for elem in elems do
    result := result ++ elem
    result := result ++ [SigToken.punct ", "]
  return result.dropLast
-- impl-end

-- proof-start
/-- Loop body of `implementation_renderTupleSig`, generalized over the
accumulator: folding `r ↦ r ++ elem ++ [sep]` over the elements appends, in
order, each element followed by the separator. -/
theorem helper_renderTupleSig (sep : SigToken) :
    ∀ (elems : List (List SigToken)) (init : List SigToken),
      Id.run (forIn elems init (fun elem r =>
        (pure (ForInStep.yield (r ++ elem ++ [sep])) : Id _)))
      = init ++ (elems.map (fun e => e ++ [sep])).flatten := by
  intro elems
  induction elems with
  | nil => intro init; simp [Id.run, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_renderTupleSig :
    ∀ (elems : List (List SigToken)),
      problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
  intro elems
  unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
  by_cases h : elems.isEmpty
  · simp [h, Id.run, pure]
  · simp only [h, Id.run]
    have hbridge :
        (do
          pure PUnit.unit
          let r ← forIn elems ([] : List SigToken) fun elem r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
          pure r.dropLast : Id (List SigToken))
        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
    rw [hbridge, helper_renderTupleSig]
    simp [pure]
-- proof-end

-- post-conditions-start
/-- The flat source-text rendering equals the comma-and-space join of the
element texts, with the empty sequence rendered as `()`. -/
def problem_spec_renderTupleText
    (elems : List String) (result : String) : Prop :=
  result = assembleTupleText elems
-- post-conditions-end

-- impl-start
def implementation_renderTupleText
    (elems : List String) : String := Id.run do
  if elems.isEmpty then
    return "()"
  return String.intercalate ", " elems
-- impl-end

-- proof-start
theorem correct_renderTupleText :
    ∀ (elems : List String),
      problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by
  intro elems
  unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText
  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for sphinx-doc__sphinx-7462 / lean. All work Verifier: `bash scripts/lean_verify.sh <file>` (exit0=verifies/no-sorry, 1=error). same_spec confirmed True for ALL 8 attacks via swebench_unified.markers.same_spec (get_backend('lean')) — impl-only edits, axioms/pure/pre/post byte-identical.

SPEC SHAPE: both post-conditions are EXACT FUNCTIONAL EQUALITY to a deeply-modeled function: problem_spec_renderTupleSig elems result := result = assembleTupleSig elems; problem_spec_renderTupleText elems result := result = assembleTupleText elems. Therefore any implementation_* whose correct_* closes is pointwise-equal to gold on EVERY input, so its faithful Python transliteration necessarily reproduces gold behavior incl. the discriminating empty-tuple case and resolves the F2P tests. A closing-but-non-resolving impl cannot exist by construction.

### ATTACKS (8 distinct same-spec wrong/echo impls; verifications run concurrently ≤4 as background jobs):
- atk_1 (prepatch bug 1 / control-flow-effect): Sig drops empty branch → [] on empty. lean_verify exit=1 (cannot close; empty goal []=[punct "(",punct ")"]).
- atk_2 (prepatch bug 2): Text drops empty branch → "" on empty. exit=1 (goal ""="()").
- atk_3 (partial-domain/boundary): Sig empty → [punct "()"] (single token, wrong shape). exit=1.
- atk_4 (boundary): Text empty → "( )" (space) instead of "()". exit=1.
- atk_5 (control-flow-effect): Sig omits dropLast → trailing separator kept. exit=1.
- atk_6 (wrong-separator): Sig uses punct "," instead of punct ", ". exit=1.
- atk_7 (ungrounded-oracle ECHO): Sig impl literally = assembleTupleSig elems (extensionally identical to gold; Text unchanged gold). lean_verify exit=0; #print axioms correct_renderTupleSig → 'does not depend on any axioms', correct_renderTupleText → [propext] — CLEAN (no sorryAx). Its faithful patch = the GOLD post-patch (extensional equality). MATERIALIZED at atk_7.patch and RUN through official harness: SBU_BENCHMARK=swe_bench_verified run_resolve('sphinx-doc__sphinx-7462', patch, timeout=1800, retries=1) → RESOLVED: True, completed: True, note='resolved'. So the ONLY closing-clean-axiom attack RESOLVES — spec NOT broken.
- atk_8 (wrong-separator text): Text non-empty joins with "," (no space). exit=1.

POSITIVE CONTROL: verbatim Solution.lean → lean_verify exit=0 (verifies).
prepatch_reproduced=true: atk_1 = Solution_prepatch_1 bug (Sig IndexError/empty path), atk_2 = Solution_prepatch_2 bug (Text "" instead of "()"), both fail the frozen gold proof, matching bundle G-DIFF.

REFINEMENT AUDIT: refinement.md has ONLY R and I legs; NO A-legs and NO kind-3. The sole collaborator (recursive per-element renderer unparse(elem)) is UNCHANGED and represented by leaving already-rendered elements as arbitrary ∀-quantified inputs (elems) — legitimate deep modeling per SPEC_GUIDE §0.7/§3, not an axiomatized changed op. G-AX is a correct skip stub (axiom_check.py). R/I correspondence to the real callees VERIFIED against the gold patch: Sig empty→[desc_sig_punctuation('','('),desc_sig_punctuation('','')] ↔ [punct "(",punct ")"]; non-empty extend/append/pop() ↔ map(·++[sep])|>.flatten|>.dropLast; Text empty→"()"; non-empty ", ".join ↔ String.intercalate ", ". No drift. G-CONF differential (oracle=faithful post-patch replica, 120k fuzz, seed 7462) passes.

CONCLUSION: ≥5 (8) distinct same-spec attacks run + verified; 7 genuinely-wrong impls cannot close (exact-equality spec maximally constrains result); the single closing clean-axiom impl (atk_7 echo) has a materialized faithful patch that RESOLVES under the official harness. verify⇒correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed; no divergence found. Verification performed: Real callee at base_commit b3e26a6c (worktree) confirmed — pre-patch sphinx/domains/python.py and sphinx/pycode/ast.py ast.Tuple branches, and the gold post-patch (patch.diff), match the modeled behavior exactly. Post-patch: empty node.elts -> [desc_sig_punctuation('','('), desc_sig_punctuation('',')')] / "()" ; non-empty -> extend(unparse(elem)) + append(punct ', ') then result.pop() ~ List.dropLast ; ", ".join(...) ~ String.intercalate ", ". (2) lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). (3) #print axioms: correct_renderTupleSig=[propext, Quot.sound], correct_renderTupleText=[propext] — no sorryAx, proofs genuine. (4) same_spec byte-identity: both Solution_prepatch_1/2 share identical spec region (True). (5) conformance_check.py: 240,010 cases (edges + 120k fuzz seed 7462), 0 disagreements, status=pass. (6) Independent exhaustive faithfulness cross-check of real-python semantics vs Lean model over tricky cases (empty tuple, singleton (x,) -> no trailing comma, empty rendered elements, nested () elements, empty text elements): 0 divergences. The specs are exact functional equality (result = assembleTupleSig/Text elems) to a deep model that agrees with the real callee on every input; the only collaborator (per-element unparse recursion) is genuinely unchanged and correctly left universally-quantified, so the spec is neither too strong nor drifted. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage role only: spec view (markers.spec_view for LeanBackend) vs public problem_statement; hints_text excluded by construction.

Authenticity checks: spec_view sha256 = 315ca160...e2b9, byte-identical to meta.region_hashes.spec_view. same_spec = True for BOTH Solution_prepatch_1.lean and Solution_prepatch_2.lean (spec region identical; only impl/proof differ). Consumer sees: docstring (/-! ... -/), axioms region, pure region (SigToken + assembleTupleSig/assembleTupleText), and two post-conditions blocks; impl and proof regions correctly elided.

Public problem_statement discloses: empty tuple Tuple[()] crashes with 'IndexError: pop from empty list' at sphinx/domains/python.py unparse -> result.pop(); expected = docs build with valid annotations. It does NOT disclose the expected empty-tuple rendering, nor that sphinx/pycode/ast.py is a second fix site.

Lexical screen over the spec view: NONE of the gold-patch-specific tokens/identifiers/paths appear — no node.elts, desc_sig_punctuation, result.pop(), ", ".join, ast.Tuple, unparse, python.py, or pycode/ast.py. The spec is written in fully abstract Lean/domain terms ('parenthesised sequence', 'display tokens', 'per-element renderer', 'elems', String.intercalate, dropLast). The word 'tuple' is already public in the problem_statement (Tuple[()]).

The spec encodes the correct empty-tuple outputs ([punct "(", punct ")"] and "()"), but that is the legitimate, unavoidable content of a reference specification — the consumer must still supply the elided impl+proof to satisfy it. Encoding correct behavior is what a spec is for, not gold-edit leakage; the leak screen targets gold-patch phrasing/identifiers/localization lifted beyond problem_statement, and none is present. The second fix site (ast.py) is modeled abstractly as the 'flat source text view' without naming it. Consistent with recorded G-PANEL-3 = NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
