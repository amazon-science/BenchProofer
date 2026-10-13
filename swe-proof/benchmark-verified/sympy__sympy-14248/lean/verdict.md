# P2 adversarial audit — sympy__sympy-14248

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,53 +60,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderSum (terms : List String) : String := Id.run do
-  let mut l : List String := []
-  for t in terms do
-    if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
-    else
-      l := l ++ ["+", t]
-  let firstSign := l.headD "+"
-  let rest := l.tail
-  let firstSign := if firstSign = "+" then "" else firstSign
-  return firstSign ++ String.intercalate " " rest
+def implementation_renderSum (terms : List String) : String :=
+  String.intercalate " + " terms
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,53 +60,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderSum (terms : List String) : String := Id.run do
-  let mut l : List String := []
-  for t in terms do
-    if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
-    else
-      l := l ++ ["+", t]
-  let firstSign := l.headD "+"
-  let rest := l.tail
-  let firstSign := if firstSign = "+" then "" else firstSign
-  return firstSign ++ String.intercalate " " rest
+def implementation_renderSum (terms : List String) : String :=
+  match terms with
+  | [] => "EMPTY"
+  | _ => renderSum terms
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   let mut l : List String := []
   for t in terms do
     if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
+      l := l ++ ["-", t.drop 2]
     else
       l := l ++ ["+", t]
   let firstSign := l.headD "+"
@@ -74,39 +74,10 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,53 +60,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderSum (terms : List String) : String := Id.run do
-  let mut l : List String := []
-  for t in terms do
-    if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
-    else
-      l := l ++ ["+", t]
-  let firstSign := l.headD "+"
-  let rest := l.tail
-  let firstSign := if firstSign = "+" then "" else firstSign
-  return firstSign ++ String.intercalate " " rest
+def implementation_renderSum (terms : List String) : String :=
+  renderSum terms.reverse
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   let mut l : List String := []
   for t in terms do
     if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
+      l := l ++ ["+", t.drop 1]
     else
       l := l ++ ["+", t]
   let firstSign := l.headD "+"
@@ -74,39 +74,10 @@
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,53 +60,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderSum (terms : List String) : String := Id.run do
-  let mut l : List String := []
-  for t in terms do
-    if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
-    else
-      l := l ++ ["+", t]
-  let firstSign := l.headD "+"
-  let rest := l.tail
-  let firstSign := if firstSign = "+" then "" else firstSign
-  return firstSign ++ String.intercalate " " rest
+def implementation_renderSum (terms : List String) : String :=
+  String.intercalate " - " terms
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,53 +60,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_renderSum (terms : List String) : String := Id.run do
-  let mut l : List String := []
-  for t in terms do
-    if t.startsWith "-" then
-      l := l ++ ["-", t.drop 1]
-    else
-      l := l ++ ["+", t]
-  let firstSign := l.headD "+"
-  let rest := l.tail
-  let firstSign := if firstSign = "+" then "" else firstSign
-  return firstSign ++ String.intercalate " " rest
+def implementation_renderSum (terms : List String) : String :=
+  let l := signParts terms
+  (if l.headD "+" = "+" then "" else l.headD "+") ++ String.intercalate " " l.tail
 -- impl-end
 
 -- proof-start
-/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
-`signParts` append fold. Route B helper. -/
-theorem loop_helper_renderSum (terms : List String) (init : List String) :
-    (Id.run (forIn terms init (fun t r =>
-        if t.startsWith "-" = true then
-          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
-        else
-          pure (ForInStep.yield (r ++ ["+", t])))))
-    = terms.foldl
-        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
-        init := by
-  induction terms generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : a.startsWith "-" = true <;>
-      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]
-
 theorem correct_renderSum :
     ∀ (terms : List String),
       problem_spec_renderSum terms (implementation_renderSum terms) := by
   intro terms
   unfold problem_spec_renderSum implementation_renderSum renderSum
-  have key : (forIn terms ([] : List String) (fun t r =>
-      if t.startsWith "-" = true then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
-      = signParts terms := loop_helper_renderSum terms []
-  simp only [Id.run]
-  rw [key]
   rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering an additive expression — a sequence of already-formatted summand
strings — into a single displayed sum.

Each summand has already been rendered to text. When that text carries a leading
minus sign, the summand is a negative quantity and must be joined into the sum as
a *subtraction* rather than as the addition of an explicitly-negated term. The
desired behaviour is:

* the summands appear left to right in their input order;
* a summand whose rendered text begins with `-` contributes its remaining text
  preceded by a subtraction connective; any other summand contributes its text
  preceded by an addition connective;
* the very first summand has no leading addition connective — if it is positive
  it stands alone, and if it is negative it keeps its leading minus and stands
  alone;
* connectives between summands are surrounded by single spaces.

So a leading-minus summand turns into a genuine subtraction in the joined output
instead of being shown as the addition of a negated term.
-/

-- axioms-start
-- The modeled routine is a self-contained transform over a list of already
-- rendered summand strings: it consumes no unchanged repo callee, so there is no
-- `opaque` declaration and no consumed `axiom … _prop`. (The per-summand renderer
-- that PRODUCES these strings is upstream of this routine and out of scope.)
-- axioms-end

-- pure-start
/-- The signed, split pieces of the summand list, in order: for each summand,
two entries — a connective (`"-"` for a leading-minus summand, `"+"` otherwise)
followed by the summand's body (its text with a leading minus removed when
present). Front-of-list accumulation by an append fold, matching the imperative
build of the working list. -/
def signParts (terms : List String) : List String :=
  terms.foldl
    (fun acc t =>
      if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
    []

/-- The displayed sum: drop the very first connective (a leading `"+"` becomes
nothing, a leading `"-"` is kept and glued directly to the first body), then join
the remaining connectives and bodies with single spaces. -/
def renderSum (terms : List String) : String :=
  let l := signParts terms
  let firstSign := l.headD "+"
  (if firstSign = "+" then "" else firstSign) ++ String.intercalate " " l.tail
-- pure-end

-- post-conditions-start
/-- The rendered output is exactly the displayed sum of the summand texts: each
leading-minus summand contributes as a subtraction, every other summand as an
addition, in input order, with the first connective elided. -/
def problem_spec_renderSum (terms : List String) (result : String) : Prop :=
  result = renderSum terms
-- post-conditions-end

-- impl-start
def implementation_renderSum (terms : List String) : String := Id.run do
  let mut l : List String := []
  for t in terms do
    if t.startsWith "-" then
      l := l ++ ["-", t.drop 1]
    else
      l := l ++ ["+", t]
  let firstSign := l.headD "+"
  let rest := l.tail
  let firstSign := if firstSign = "+" then "" else firstSign
  return firstSign ++ String.intercalate " " rest
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
`signParts` append fold. Route B helper. -/
theorem loop_helper_renderSum (terms : List String) (init : List String) :
    (Id.run (forIn terms init (fun t r =>
        if t.startsWith "-" = true then
          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
        else
          pure (ForInStep.yield (r ++ ["+", t])))))
    = terms.foldl
        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
        init := by
  induction terms generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.startsWith "-" = true <;>
      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]

theorem correct_renderSum :
    ∀ (terms : List String),
      problem_spec_renderSum terms (implementation_renderSum terms) := by
  intro terms
  unfold problem_spec_renderSum implementation_renderSum renderSum
  have key : (forIn terms ([] : List String) (fun t r =>
      if t.startsWith "-" = true then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
      = signParts terms := loop_helper_renderSum terms []
  simp only [Id.run]
  rw [key]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

EXACT-EQUALITY spec: problem_spec_renderSum terms result := result = renderSum terms, pinned to the TOTAL concrete function renderSum. Any impl closing correct_renderSum is provably extensionally equal to renderSum on all inputs. Axioms region is EMPTY (Solution.lean lines 26-31) — self-contained pure transform over List String, NO callee, so NO A-leg / callee-substitution surface. refinement.md audit: all 9 legs tagged R or I (no A-consumed, no A-reference, no kind-3); correspondence is the mechanical R/I transliteration covered by G-CONF — verified consistent.

All 7 attacks are same_spec=True (impl-region-only edits; spec/axioms/pure/post byte-identical). Verified concurrently (<=4 jobs) via scripts/lean_verify.sh, 300s cap.

GENUINELY-WRONG impls (must NOT close, and none did):
- atk_1 prepatch bug (String.intercalate " + " terms): exit=1, rfl failed on LHS. Cannot close.
- atk_2 partial-domain ("EMPTY" on []): exit=1.
- atk_3 boundary (t.drop 2 instead of drop 1): exit=1.
- atk_4 control-flow-effect (renderSum terms.reverse): exit=1.
- atk_5 wrong-connective (always "+", strip minus): exit=1.
- atk_6 ungrounded-oracle (String.intercalate " - " terms): exit=1.

ECHO closer:
- atk_7 (extensionally-equal reformulation via signParts): exit=0, #print axioms correct_renderSum = [propext] (clean, no sorryAx). Its FAITHFUL refined patch = the gold _print_MatAdd implementation (byte-identical to bundle patch.diff, since atk_7 == renderSum == gold algorithm). Ran through official harness (swebench_unified.harness.run_resolve AND direct run_evaluation): RESOLVED=True, COMPLETED=True, FAIL_TO_PASS 2/2 pass (test_MatrixElement_printing, test_MatrixSymbol_printing). Report: experiments/logs/run_evaluation/sbu-audit-14248-diag/.../report.json resolved=true.

Positive control (shipped Solution.lean): exit=0, #print axioms = [propext, Quot.sound] (clean).

prepatch_reproduced=true: empty/base-commit prediction through run_resolve => RESOLVED=False (prepatch does not pass F2P). Divergence witness divergence.lean (exit=0) machine-proves: renderSum reproduces all 3 gold anchors (["-B","-A*B","A"]->"-B - A*B + A", ["-(A + B)","A*B"]->"-(A + B) + A*B", ["-B","A"]->"-B + A") AND prepatch(join " + ") != renderSum on ["-B","-A*B","A"].

CONCLUSION: the only impl that closes the exact-equality proof is extensionally == renderSum == gold, and its faithful patch RESOLVES. No wrong impl closes. verify => correct holds. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering an additive expression — a sequence of already-formatted summand
strings — into a single displayed sum.

Each summand has already been rendered to text. When that text carries a leading
minus sign, the summand is a negative quantity and must be joined into the sum as
a *subtraction* rather than as the addition of an explicitly-negated term. The
desired behaviour is:

* the summands appear left to right in their input order;
* a summand whose rendered text begins with `-` contributes its remaining text
  preceded by a subtraction connective; any other summand contributes its text
  preceded by an addition connective;
* the very first summand has no leading addition connective — if it is positive
  it stands alone, and if it is negative it keeps its leading minus and stands
  alone;
* connectives between summands are surrounded by single spaces.

So a leading-minus summand turns into a genuine subtraction in the joined output
instead of being shown as the addition of a negated term.
-/

-- axioms-start
-- The modeled routine is a self-contained transform over a list of already
-- rendered summand strings: it consumes no unchanged repo callee, so there is no
-- `opaque` declaration and no consumed `axiom … _prop`. (The per-summand renderer
-- that PRODUCES these strings is upstream of this routine and out of scope.)
-- axioms-end

-- pure-start
/-- The signed, split pieces of the summand list, in order: for each summand,
two entries — a connective (`"-"` for a leading-minus summand, `"+"` otherwise)
followed by the summand's body (its text with a leading minus removed when
present). Front-of-list accumulation by an append fold, matching the imperative
build of the working list. -/
def signParts (terms : List String) : List String :=
  terms.foldl
    (fun acc t =>
      if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
    []

/-- The displayed sum: drop the very first connective (a leading `"+"` becomes
nothing, a leading `"-"` is kept and glued directly to the first body), then join
the remaining connectives and bodies with single spaces. -/
def renderSum (terms : List String) : String :=
  let l := signParts terms
  let firstSign := l.headD "+"
  (if firstSign = "+" then "" else firstSign) ++ String.intercalate " " l.tail
-- pure-end

-- post-conditions-start
/-- The rendered output is exactly the displayed sum of the summand texts: each
leading-minus summand contributes as a subtraction, every other summand as an
addition, in input order, with the first connective elided. -/
def problem_spec_renderSum (terms : List String) (result : String) : Prop :=
  result = renderSum terms
-- post-conditions-end

-- impl-start
def implementation_renderSum (terms : List String) : String := Id.run do
  let mut l : List String := []
  for t in terms do
    if t.startsWith "-" then
      l := l ++ ["-", t.drop 1]
    else
      l := l ++ ["+", t]
  let firstSign := l.headD "+"
  let rest := l.tail
  let firstSign := if firstSign = "+" then "" else firstSign
  return firstSign ++ String.intercalate " " rest
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
`signParts` append fold. Route B helper. -/
theorem loop_helper_renderSum (terms : List String) (init : List String) :
    (Id.run (forIn terms init (fun t r =>
        if t.startsWith "-" = true then
          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
        else
          pure (ForInStep.yield (r ++ ["+", t])))))
    = terms.foldl
        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
        init := by
  induction terms generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.startsWith "-" = true <;>
      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]

theorem correct_renderSum :
    ∀ (terms : List String),
      problem_spec_renderSum terms (implementation_renderSum terms) := by
  intro terms
  unfold problem_spec_renderSum implementation_renderSum renderSum
  have key : (forIn terms ([] : List String) (fun t r =>
      if t.startsWith "-" = true then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
      = signParts terms := loop_helper_renderSum terms []
  simp only [Id.run]
  rw [key]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

EXACT-EQUALITY spec: problem_spec_renderSum terms result := result = renderSum terms, pinned to the TOTAL concrete function renderSum. Any impl closing correct_renderSum is provably extensionally equal to renderSum on all inputs. Axioms region is EMPTY (Solution.lean lines 26-31) — self-contained pure transform over List String, NO callee, so NO A-leg / callee-substitution surface. refinement.md audit: all 9 legs tagged R or I (no A-consumed, no A-reference, no kind-3); correspondence is the mechanical R/I transliteration covered by G-CONF — verified consistent.

All 7 attacks are same_spec=True (impl-region-only edits; spec/axioms/pure/post byte-identical). Verified concurrently (<=4 jobs) via scripts/lean_verify.sh, 300s cap.

GENUINELY-WRONG impls (must NOT close, and none did):
- atk_1 prepatch bug (String.intercalate " + " terms): exit=1, rfl failed on LHS. Cannot close.
- atk_2 partial-domain ("EMPTY" on []): exit=1.
- atk_3 boundary (t.drop 2 instead of drop 1): exit=1.
- atk_4 control-flow-effect (renderSum terms.reverse): exit=1.
- atk_5 wrong-connective (always "+", strip minus): exit=1.
- atk_6 ungrounded-oracle (String.intercalate " - " terms): exit=1.

ECHO closer:
- atk_7 (extensionally-equal reformulation via signParts): exit=0, #print axioms correct_renderSum = [propext] (clean, no sorryAx). Its FAITHFUL refined patch = the gold _print_MatAdd implementation (byte-identical to bundle patch.diff, since atk_7 == renderSum == gold algorithm). Ran through official harness (swebench_unified.harness.run_resolve AND direct run_evaluation): RESOLVED=True, COMPLETED=True, FAIL_TO_PASS 2/2 pass (test_MatrixElement_printing, test_MatrixSymbol_printing). Report: experiments/logs/run_evaluation/sbu-audit-14248-diag/.../report.json resolved=true.

Positive control (shipped Solution.lean): exit=0, #print axioms = [propext, Quot.sound] (clean).

prepatch_reproduced=true: empty/base-commit prediction through run_resolve => RESOLVED=False (prepatch does not pass F2P). Divergence witness divergence.lean (exit=0) machine-proves: renderSum reproduces all 3 gold anchors (["-B","-A*B","A"]->"-B - A*B + A", ["-(A + B)","A*B"]->"-(A + B) + A*B", ["-B","A"]->"-B + A") AND prepatch(join " + ") != renderSum on ["-B","-A*B","A"].

CONCLUSION: the only impl that closes the exact-equality proof is extensionally == renderSum == gold, and its faithful patch RESOLVES. No wrong impl closes. verify => correct holds. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) verdict: FAITHFUL — no diverging input on the reachable domain.

Modeled routine: the join transform of `_print_MatAdd` (sympy/printing/str.py:314-330 and latex.py:1479, algorithm byte-identical), over the already-rendered summand list `terms : list[str]`. Spec = `renderSum`/`signParts` + `problem_spec_renderSum`. Mapping correctly scopes the per-term renderer (`parenthesize`/`_print`, `_print_MatMul` neg-coeff) as upstream/out-of-scope, so the model has no callee.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean)=True (lean backend); spec region byte-identical, impl/proof elided in spec view.
2. lean_verify.sh exit 0; `#print axioms correct_renderSum` = [propext, Quot.sound] — no sorryAx, genuine proof of impl↔spec equivalence.
3. Differential vs REAL repo (python3.8 + worktree, sympy 1.1.2.dev @ 9986b38181): 3544 real MatAdd expressions (products, negatives, integer coeffs) driven through the actual `_print_MatAdd` of BOTH StrPrinter and LatexPrinter, comparing real output to op-for-op shadow of `renderSum` applied to the real computed `terms` list → 0 mismatches.
4. 200k arbitrary-string fuzz of the isolated join body (leading '-', empty strings, tabs, multi-char, parens) → 0 mismatches. Bundle conformance_check.py: 120008 checked, 0 disagreements.

Only divergence: empty list. Real `l.pop(0)` raises IndexError on `[]`; model returns "". This is strictly out of the real callee's domain — MatAdd.args is never empty — so it is unreachable and NOT a faithfulness defect (total model harmlessly extends a partial function off-domain; documented in refinement.md). On every input the real callee can actually receive, the model agrees exactly. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution, Solution_prepatch)=True with the lean LanguageTables; the spec region is byte-identical and the only diff is the elided impl/proof — verified. The spec view (imports + docstring + axioms note + pure helpers signParts/renderSum + post-conditions) has impl and proof elided.

Leakage assessment: The spec view is entirely at the abstract 'list of already-rendered summand strings → displayed sum' level. It never mentions any gold-edit-locating specifics — no _print_MatAdd, str.py/latex.py, parenthesize, MatAdd, MatrixSymbol, or the (-1) coefficient mechanism; those Python-code binding details live only in mapping.md/refinement.md, which are NOT part of the spec view. No F2P anchor test cases (they exist only in mapping.md) and no verbatim problem_statement phrasing appear in the view, so the lexical screen is clean.

The public problem_statement already fully discloses the desired behavior (that `A - A*B - B` must print with genuine subtractions instead of `(-1)*B + ...`). The postcondition (leading-`-` summand → subtraction, first connective elided, single-space connectives) is a faithful behavioral formalization of exactly that stated intent — congruent with, not beyond, the problem statement. The pure helpers give the reference algorithm, which is the legitimate contract every such bundle exposes; the genuinely hard artifacts (the Lean imperative impl and the Route-B accumulator-induction proof) remain elided. Nothing in the view reconstructs the gold edit beyond what the public problem statement already conveys.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
