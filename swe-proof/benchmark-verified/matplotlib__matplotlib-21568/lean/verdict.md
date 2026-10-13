# P2 adversarial audit — matplotlib__matplotlib-21568

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_prepatch.lean`, `atk_3_partial.lean`, `atk_4_boundary.lean`, `atk_5_nodroptoken.lean`, `atk_6_swap.lean`, `atk_7_identity.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,33 +110,24 @@
 -- impl-start
 def implementation_texLabel (text : List Char) : List Char := Id.run do
   let lifted := bracketLetterRuns text
+  -- Earlier behavior: only hyphens are braced; colons and spaces are left as
+  -- bare operators inside the math group.
   let mut escaped : List Char := []
   for c in lifted do
-    escaped := escaped ++ escapeMathSym c
+    if c = '-' then
+      escaped := escaped ++ ['{', '-', '}']
+    else
+      escaped := escaped ++ [c]
   let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
   return dropToken '$' "\\mathdefault{}$".toList wrapped
 -- impl-end
 
 -- proof-start
-/-- The for-loop accumulating `escapeMathSym` over the cleaned `forIn` body
-equals `init ++ flatMap`, generalized over the accumulator (Route B helper). -/
-theorem escape_loop_eq (lifted init : List Char) :
-    (forIn (m := Id) lifted init (fun c r => ForInStep.yield (r ++ escapeMathSym c)))
-      = init ++ lifted.flatMap escapeMathSym := by
-  induction lifted generalizing init with
-  | nil => simp [List.forIn_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.flatMap_cons, List.append_assoc]
-
 theorem correct_texLabel :
     ∀ (text : List Char),
       problem_spec_texLabel text (implementation_texLabel text) := by
   intro text
   unfold problem_spec_texLabel implementation_texLabel texLabel
-  simp only [Id.run, bind, pure]
-  rw [escape_loop_eq]
-  simp [escapeMathSyms]
+  simp only [Id.run]
+  rfl
 -- proof-end
```

Attack 2 — `atk_3_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,12 @@
   let lifted := bracketLetterRuns text
   let mut escaped : List Char := []
   for c in lifted do
-    escaped := escaped ++ escapeMathSym c
+    if c = '-' then
+      escaped := escaped ++ ['{', '-', '}']
+    else if c = ':' then
+      escaped := escaped ++ ['{', ':', '}']
+    else
+      escaped := escaped ++ [c]
   let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
   return dropToken '$' "\\mathdefault{}$".toList wrapped
 -- impl-end
@@ -139,4 +144,5 @@
   simp only [Id.run, bind, pure]
   rw [escape_loop_eq]
   simp [escapeMathSyms]
+
 -- proof-end
```

Attack 3 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,14 @@
   let lifted := bracketLetterRuns text
   let mut escaped : List Char := []
   for c in lifted do
-    escaped := escaped ++ escapeMathSym c
+    if c = '-' then
+      escaped := escaped ++ ['{', '-', '}']
+    else if c = ':' then
+      escaped := escaped ++ ['{', ':', '}']
+    else if c = ' ' then
+      escaped := escaped ++ [';']
+    else
+      escaped := escaped ++ [c]
   let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
   return dropToken '$' "\\mathdefault{}$".toList wrapped
 -- impl-end
@@ -139,4 +146,5 @@
   simp only [Id.run, bind, pure]
   rw [escape_loop_eq]
   simp [escapeMathSyms]
+
 -- proof-end
```

Attack 4 — `atk_5_nodroptoken.lean` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
   for c in lifted do
     escaped := escaped ++ escapeMathSym c
   let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
-  return dropToken '$' "\\mathdefault{}$".toList wrapped
+  return wrapped
 -- impl-end
 
 -- proof-start
@@ -139,4 +139,5 @@
   simp only [Id.run, bind, pure]
   rw [escape_loop_eq]
   simp [escapeMathSyms]
+
 -- proof-end
```

Attack 5 — `atk_6_swap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,14 @@
   let lifted := bracketLetterRuns text
   let mut escaped : List Char := []
   for c in lifted do
-    escaped := escaped ++ escapeMathSym c
+    if c = '-' then
+      escaped := escaped ++ ['{', '-', '}']
+    else if c = ':' then
+      escaped := escaped ++ ['\\', ';']
+    else if c = ' ' then
+      escaped := escaped ++ ['{', ':', '}']
+    else
+      escaped := escaped ++ [c]
   let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
   return dropToken '$' "\\mathdefault{}$".toList wrapped
 -- impl-end
@@ -139,4 +146,5 @@
   simp only [Id.run, bind, pure]
   rw [escape_loop_eq]
   simp [escapeMathSyms]
+
 -- proof-end
```

Attack 6 — `atk_7_identity.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,35 +108,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_texLabel (text : List Char) : List Char := Id.run do
-  let lifted := bracketLetterRuns text
-  let mut escaped : List Char := []
-  for c in lifted do
-    escaped := escaped ++ escapeMathSym c
-  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
-  return dropToken '$' "\\mathdefault{}$".toList wrapped
+def implementation_texLabel (text : List Char) : List Char := text
 -- impl-end
 
 -- proof-start
-/-- The for-loop accumulating `escapeMathSym` over the cleaned `forIn` body
-equals `init ++ flatMap`, generalized over the accumulator (Route B helper). -/
-theorem escape_loop_eq (lifted init : List Char) :
-    (forIn (m := Id) lifted init (fun c r => ForInStep.yield (r ++ escapeMathSym c)))
-      = init ++ lifted.flatMap escapeMathSym := by
-  induction lifted generalizing init with
-  | nil => simp [List.forIn_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.flatMap_cons, List.append_assoc]
-
 theorem correct_texLabel :
     ∀ (text : List Char),
       problem_spec_texLabel text (implementation_texLabel text) := by
   intro text
   unfold problem_spec_texLabel implementation_texLabel texLabel
-  simp only [Id.run, bind, pure]
-  rw [escape_loop_eq]
-  simp [escapeMathSyms]
+  simp [Id.run, escapeMathSyms]
 -- proof-end
```

Attack 7 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -108,35 +108,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_texLabel (text : List Char) : List Char := Id.run do
-  let lifted := bracketLetterRuns text
-  let mut escaped : List Char := []
-  for c in lifted do
-    escaped := escaped ++ escapeMathSym c
-  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
-  return dropToken '$' "\\mathdefault{}$".toList wrapped
+def implementation_texLabel (text : List Char) : List Char := texLabel text
 -- impl-end
 
 -- proof-start
-/-- The for-loop accumulating `escapeMathSym` over the cleaned `forIn` body
-equals `init ++ flatMap`, generalized over the accumulator (Route B helper). -/
-theorem escape_loop_eq (lifted init : List Char) :
-    (forIn (m := Id) lifted init (fun c r => ForInStep.yield (r ++ escapeMathSym c)))
-      = init ++ lifted.flatMap escapeMathSym := by
-  induction lifted generalizing init with
-  | nil => simp [List.forIn_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.flatMap_cons, List.append_assoc]
-
 theorem correct_texLabel :
     ∀ (text : List Char),
       problem_spec_texLabel text (implementation_texLabel text) := by
   intro text
-  unfold problem_spec_texLabel implementation_texLabel texLabel
-  simp only [Id.run, bind, pure]
-  rw [escape_loop_eq]
-  simp [escapeMathSyms]
+  unfold problem_spec_texLabel implementation_texLabel
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a short tick-label string into a math-mode typesetting fragment.

When a date/time tick label is typeset through the math renderer, alphabetic
runs are kept as upright text while the surrounding numeric material is placed
in a math-default group. Inside that math group, individual symbols must be
braced or escaped so the typesetter does not treat them as binary operators or
collapse the spacing between numbers:

  * a hyphen `-` becomes `{-}`;
  * a colon `:` becomes `{:}`;
  * a space ` ` becomes a thin-space command `\;`.

The label is produced in four stages:

  1. every maximal run of ASCII letters is lifted out of the math group: the run
     is surrounded so that it renders as upright text and a fresh math-default
     group is opened after it;
  2. each remaining symbol is rewritten per the table above (letters and digits
     and every other character pass through unchanged);
  3. the whole thing is wrapped in one outer math-default group;
  4. any empty math-default group `$\mathdefault{}$` that results is removed.

The desired output is exactly the string these four stages produce for the given
input. Every input character's contribution is pinned, so no part of the result
is left free.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom. The one nontrivial
-- library operation the computation relies on — the regular-expression
-- substitution that lifts maximal alphabetic runs out of the math group — is
-- modeled DEEPLY (`bracketLetterRuns`, a front-recursive run scanner) rather
-- than axiomatized, and the model is validated against the real callee by G-AX.
-- Hence no `opaque`/`axiom` callee contract is declared here.
-- axioms-end

-- pure-start
/-- Stage 1. Lift each maximal run of ASCII letters out of the surrounding math
group: close the current group with `}$`, emit the letter run verbatim, then
reopen a fresh math-default group with `$\mathdefault{`; non-letter characters
pass through unchanged. This is the per-run rewrite the substitution performs. -/
def bracketLetterRuns : List Char → List Char
  | [] => []
  | c :: cs =>
    if c.isAlpha then
      let rest := (c :: cs).dropWhile Char.isAlpha
      "}$".toList ++ (c :: cs).takeWhile Char.isAlpha
        ++ "$\\mathdefault{".toList ++ bracketLetterRuns rest
    else
      c :: bracketLetterRuns cs
  termination_by xs => xs.length
  decreasing_by
    · have hc : Char.isAlpha c = true := by assumption
      have h2 : ((c :: cs).dropWhile Char.isAlpha) = cs.dropWhile Char.isAlpha := by
        simp [List.dropWhile_cons_of_pos, hc]
      rw [h2]
      calc (cs.dropWhile Char.isAlpha).length ≤ cs.length := List.length_dropWhile_le _ _
        _ < (c :: cs).length := by simp
    · simp

/-- Stage 2, per character: brace a hyphen as `{-}`, a colon as `{:}`, rewrite a
space as the thin-space command `\;`, and leave every other character alone. -/
def escapeMathSym (c : Char) : List Char :=
  if c = '-' then ['{', '-', '}']
  else if c = ':' then ['{', ':', '}']
  else if c = ' ' then ['\\', ';']
  else [c]

/-- Stage 2: rewrite every symbol of the string by `escapeMathSym`. -/
def escapeMathSyms (cs : List Char) : List Char := cs.flatMap escapeMathSym

/-- Stage 4: delete every (non-overlapping, left-to-right) occurrence of the
literal token `o :: os` from the string. Used to drop the empty math-default
group `$\mathdefault{}$`. -/
def dropToken (o : Char) (os : List Char) : List Char → List Char
  | [] => []
  | c :: cs =>
    if (o :: os).isPrefixOf (c :: cs) then dropToken o os ((c :: cs).drop (os.length + 1))
    else c :: dropToken o os cs
  termination_by s => s.length
  decreasing_by
    · calc ((c :: cs).drop (os.length + 1)).length
            ≤ (c :: cs).length - (os.length + 1) := by simp [List.length_drop]
        _ < (c :: cs).length := by simp; omega
    · simp

/-- The full four-stage label transform: lift letter runs, rewrite symbols, wrap
in one outer math-default group, then drop any resulting empty math group. This
is the desired output for a given input string. -/
def texLabel (text : List Char) : List Char :=
  let lifted := bracketLetterRuns text
  let escaped := escapeMathSyms lifted
  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
  dropToken '$' "\\mathdefault{}$".toList wrapped
-- pure-end

-- post-conditions-start
/-- The result is exactly the four-stage label transform of the input string.
Every character of the input contributes deterministically (letters via the
run-lifting stage, hyphen/colon/space via the symbol-rewrite stage, all other
characters verbatim), so the whole output is pinned to the input. -/
def problem_spec_texLabel (text : List Char) (result : List Char) : Prop :=
  result = texLabel text
-- post-conditions-end

-- impl-start
def implementation_texLabel (text : List Char) : List Char := Id.run do
  let lifted := bracketLetterRuns text
  let mut escaped : List Char := []
  for c in lifted do
    escaped := escaped ++ escapeMathSym c
  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
  return dropToken '$' "\\mathdefault{}$".toList wrapped
-- impl-end

-- proof-start
/-- The for-loop accumulating `escapeMathSym` over the cleaned `forIn` body
equals `init ++ flatMap`, generalized over the accumulator (Route B helper). -/
theorem escape_loop_eq (lifted init : List Char) :
    (forIn (m := Id) lifted init (fun c r => ForInStep.yield (r ++ escapeMathSym c)))
      = init ++ lifted.flatMap escapeMathSym := by
  induction lifted generalizing init with
  | nil => simp [List.forIn_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.flatMap_cons, List.append_assoc]

theorem correct_texLabel :
    ∀ (text : List Char),
      problem_spec_texLabel text (implementation_texLabel text) := by
  intro text
  unfold problem_spec_texLabel implementation_texLabel texLabel
  simp only [Id.run, bind, pure]
  rw [escape_loop_eq]
  simp [escapeMathSyms]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition problem_spec_texLabel text result := (result = texLabel text) is FULLY PINNED to a concrete total pure function texLabel; hence any impl whose correct_texLabel proof closes must be extensionally equal to texLabel (gold-equivalent). No axiom/opaque is declared in Solution.lean (axioms region is comment-only) => NO A-consumed leg / no ungrounded oracle to echo. The single non-identity leg is the A-reference bracketLetterRuns modeling re.sub(r'([a-zA-Z]+)', r'}$\1$\mathdefault{', text).

Protocol executed (all same_spec==True, verified). Command: `bash scripts/lean_verify.sh <file>` from project root.

### Verify results
- pos_control.lean (gold): exit 0 VERIFIES.
- atk_8_echo.lean (gold-equivalent, impl := texLabel text): exit 0 VERIFIES.
- atk_2_prepatch.lean (prepatch bug: only '-'->{-}, colon/space bare): exit 1 FAILS (prepatch reproduced).
- atk_3_partial.lean (partial-domain: handles '-' and ':' but NOT ' '): exit 1 FAILS.
- atk_4_boundary.lean (boundary: ' '->[';'] instead of ['\\',';']): exit 1 FAILS.
- atk_5_nodroptoken.lean (control-flow-effect: omit final dropToken stage): exit 1 FAILS.
- atk_6_swap.lean (map swap: ':'->'\;' and ' '->'{:}'): exit 1 FAILS.
- atk_7_identity.lean (ungrounded/trivial: return text): exit 1 FAILS.
All 6 behavior-differing wrong impls fail to verify => pinned spec rejects every non-gold behavior.

### CLEAN AXIOMS (#print axioms correct_texLabel):
- pos_control: 'depends on axioms: [propext, Classical.choice, Quot.sound]' (exit 0, no sorry).
- atk_8_echo:  'depends on axioms: [propext, Classical.choice, Quot.sound]' (exit 0, no sorry).
Both clean (standard Lean/Mathlib axioms only), no sorry/admit.

MANDATORY RESOLVE FOR EVERY VERIFYING ATTACK: only atk_8_echo verifies (besides positive control). Its impl computes exactly texLabel = the exact post-patch _wrap_in_tex body, so its FAITHFUL refined patch is the gold post-patch body (patch.diff). Materialized as atk_8_echo.patch and run through the official harness: run_resolve('matplotlib__matplotlib-21568', ...) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. Per the resolved echo-attack policy, a same-spec verifying attack whose faithful patch RESOLVES is NOT a weakness (it only breaks verify=>correct if the patch does NOT resolve). No verifying attack has a non-resolving faithful patch => verify does not diverge from correct.

MODEL/CALLEE CORRESPONDENCE (A-reference audit): ran the bundle's own gates in-place:
- axiom_check.py (G-AX): status=pass, checked=200024 (bracketLetterRuns == re.sub over EDGE + 2e5 fuzz, seed 21568).
- conformance_check.py (G-CONF): checked=200021 disagreements=0, status=pass (full shadow of implementation_texLabel == exact post-patch _wrap_in_tex).
The A-reference model faithfully reproduces the real re.sub callee; refinement.md legs are op1 A-reference, ops 2&4 R, op3 I — no kind-3 leg, correspondence holds.

CONCLUSION: The spec is a tight equality to a concrete total function grounded (via A-reference) in the real callee and validated over 4e5+ inputs; every wrong impl is unprovable, the only verifying same-spec impl is gold-equivalent and its faithful patch resolves. verify => correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_prepatch.lean`, `atk_3_partial.lean`, `atk_4_boundary.lean`, `atk_5_nodroptoken.lean`, `atk_6_swap.lean`, `atk_7_identity.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_nodroptoken.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_swap.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_identity.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a short tick-label string into a math-mode typesetting fragment.

When a date/time tick label is typeset through the math renderer, alphabetic
runs are kept as upright text while the surrounding numeric material is placed
in a math-default group. Inside that math group, individual symbols must be
braced or escaped so the typesetter does not treat them as binary operators or
collapse the spacing between numbers:

  * a hyphen `-` becomes `{-}`;
  * a colon `:` becomes `{:}`;
  * a space ` ` becomes a thin-space command `\;`.

The label is produced in four stages:

  1. every maximal run of ASCII letters is lifted out of the math group: the run
     is surrounded so that it renders as upright text and a fresh math-default
     group is opened after it;
  2. each remaining symbol is rewritten per the table above (letters and digits
     and every other character pass through unchanged);
  3. the whole thing is wrapped in one outer math-default group;
  4. any empty math-default group `$\mathdefault{}$` that results is removed.

The desired output is exactly the string these four stages produce for the given
input. Every input character's contribution is pinned, so no part of the result
is left free.
-/

-- axioms-start
-- No unchanged outside callee is CONSUMED as an axiom. The one nontrivial
-- library operation the computation relies on — the regular-expression
-- substitution that lifts maximal alphabetic runs out of the math group — is
-- modeled DEEPLY (`bracketLetterRuns`, a front-recursive run scanner) rather
-- than axiomatized, and the model is validated against the real callee by G-AX.
-- Hence no `opaque`/`axiom` callee contract is declared here.
-- axioms-end

-- pure-start
/-- Stage 1. Lift each maximal run of ASCII letters out of the surrounding math
group: close the current group with `}$`, emit the letter run verbatim, then
reopen a fresh math-default group with `$\mathdefault{`; non-letter characters
pass through unchanged. This is the per-run rewrite the substitution performs. -/
def bracketLetterRuns : List Char → List Char
  | [] => []
  | c :: cs =>
    if c.isAlpha then
      let rest := (c :: cs).dropWhile Char.isAlpha
      "}$".toList ++ (c :: cs).takeWhile Char.isAlpha
        ++ "$\\mathdefault{".toList ++ bracketLetterRuns rest
    else
      c :: bracketLetterRuns cs
  termination_by xs => xs.length
  decreasing_by
    · have hc : Char.isAlpha c = true := by assumption
      have h2 : ((c :: cs).dropWhile Char.isAlpha) = cs.dropWhile Char.isAlpha := by
        simp [List.dropWhile_cons_of_pos, hc]
      rw [h2]
      calc (cs.dropWhile Char.isAlpha).length ≤ cs.length := List.length_dropWhile_le _ _
        _ < (c :: cs).length := by simp
    · simp

/-- Stage 2, per character: brace a hyphen as `{-}`, a colon as `{:}`, rewrite a
space as the thin-space command `\;`, and leave every other character alone. -/
def escapeMathSym (c : Char) : List Char :=
  if c = '-' then ['{', '-', '}']
  else if c = ':' then ['{', ':', '}']
  else if c = ' ' then ['\\', ';']
  else [c]

/-- Stage 2: rewrite every symbol of the string by `escapeMathSym`. -/
def escapeMathSyms (cs : List Char) : List Char := cs.flatMap escapeMathSym

/-- Stage 4: delete every (non-overlapping, left-to-right) occurrence of the
literal token `o :: os` from the string. Used to drop the empty math-default
group `$\mathdefault{}$`. -/
def dropToken (o : Char) (os : List Char) : List Char → List Char
  | [] => []
  | c :: cs =>
    if (o :: os).isPrefixOf (c :: cs) then dropToken o os ((c :: cs).drop (os.length + 1))
    else c :: dropToken o os cs
  termination_by s => s.length
  decreasing_by
    · calc ((c :: cs).drop (os.length + 1)).length
            ≤ (c :: cs).length - (os.length + 1) := by simp [List.length_drop]
        _ < (c :: cs).length := by simp; omega
    · simp

/-- The full four-stage label transform: lift letter runs, rewrite symbols, wrap
in one outer math-default group, then drop any resulting empty math group. This
is the desired output for a given input string. -/
def texLabel (text : List Char) : List Char :=
  let lifted := bracketLetterRuns text
  let escaped := escapeMathSyms lifted
  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
  dropToken '$' "\\mathdefault{}$".toList wrapped
-- pure-end

-- post-conditions-start
/-- The result is exactly the four-stage label transform of the input string.
Every character of the input contributes deterministically (letters via the
run-lifting stage, hyphen/colon/space via the symbol-rewrite stage, all other
characters verbatim), so the whole output is pinned to the input. -/
def problem_spec_texLabel (text : List Char) (result : List Char) : Prop :=
  result = texLabel text
-- post-conditions-end

-- impl-start
def implementation_texLabel (text : List Char) : List Char := Id.run do
  let lifted := bracketLetterRuns text
  let mut escaped : List Char := []
  for c in lifted do
    escaped := escaped ++ escapeMathSym c
  let wrapped := "$\\mathdefault{".toList ++ escaped ++ "}$".toList
  return dropToken '$' "\\mathdefault{}$".toList wrapped
-- impl-end

-- proof-start
/-- The for-loop accumulating `escapeMathSym` over the cleaned `forIn` body
equals `init ++ flatMap`, generalized over the accumulator (Route B helper). -/
theorem escape_loop_eq (lifted init : List Char) :
    (forIn (m := Id) lifted init (fun c r => ForInStep.yield (r ++ escapeMathSym c)))
      = init ++ lifted.flatMap escapeMathSym := by
  induction lifted generalizing init with
  | nil => simp [List.forIn_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.flatMap_cons, List.append_assoc]

theorem correct_texLabel :
    ∀ (text : List Char),
      problem_spec_texLabel text (implementation_texLabel text) := by
  intro text
  unfold problem_spec_texLabel implementation_texLabel texLabel
  simp only [Id.run, bind, pure]
  rw [escape_loop_eq]
  simp [escapeMathSyms]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition problem_spec_texLabel text result := (result = texLabel text) is FULLY PINNED to a concrete total pure function texLabel; hence any impl whose correct_texLabel proof closes must be extensionally equal to texLabel (gold-equivalent). No axiom/opaque is declared in Solution.lean (axioms region is comment-only) => NO A-consumed leg / no ungrounded oracle to echo. The single non-identity leg is the A-reference bracketLetterRuns modeling re.sub(r'([a-zA-Z]+)', r'}$\1$\mathdefault{', text).

Protocol executed (all same_spec==True, verified). Command: `bash scripts/lean_verify.sh <file>` from project root.

### Verify results
- pos_control.lean (gold): exit 0 VERIFIES.
- atk_8_echo.lean (gold-equivalent, impl := texLabel text): exit 0 VERIFIES.
- atk_2_prepatch.lean (prepatch bug: only '-'->{-}, colon/space bare): exit 1 FAILS (prepatch reproduced).
- atk_3_partial.lean (partial-domain: handles '-' and ':' but NOT ' '): exit 1 FAILS.
- atk_4_boundary.lean (boundary: ' '->[';'] instead of ['\\',';']): exit 1 FAILS.
- atk_5_nodroptoken.lean (control-flow-effect: omit final dropToken stage): exit 1 FAILS.
- atk_6_swap.lean (map swap: ':'->'\;' and ' '->'{:}'): exit 1 FAILS.
- atk_7_identity.lean (ungrounded/trivial: return text): exit 1 FAILS.
All 6 behavior-differing wrong impls fail to verify => pinned spec rejects every non-gold behavior.

### CLEAN AXIOMS (#print axioms correct_texLabel):
- pos_control: 'depends on axioms: [propext, Classical.choice, Quot.sound]' (exit 0, no sorry).
- atk_8_echo:  'depends on axioms: [propext, Classical.choice, Quot.sound]' (exit 0, no sorry).
Both clean (standard Lean/Mathlib axioms only), no sorry/admit.

MANDATORY RESOLVE FOR EVERY VERIFYING ATTACK: only atk_8_echo verifies (besides positive control). Its impl computes exactly texLabel = the exact post-patch _wrap_in_tex body, so its FAITHFUL refined patch is the gold post-patch body (patch.diff). Materialized as atk_8_echo.patch and run through the official harness: run_resolve('matplotlib__matplotlib-21568', ...) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. Per the resolved echo-attack policy, a same-spec verifying attack whose faithful patch RESOLVES is NOT a weakness (it only breaks verify=>correct if the patch does NOT resolve). No verifying attack has a non-resolving faithful patch => verify does not diverge from correct.

MODEL/CALLEE CORRESPONDENCE (A-reference audit): ran the bundle's own gates in-place:
- axiom_check.py (G-AX): status=pass, checked=200024 (bracketLetterRuns == re.sub over EDGE + 2e5 fuzz, seed 21568).
- conformance_check.py (G-CONF): checked=200021 disagreements=0, status=pass (full shadow of implementation_texLabel == exact post-patch _wrap_in_tex).
The A-reference model faithfully reproduces the real re.sub callee; refinement.md legs are op1 A-reference, ops 2&4 R, op3 I — no kind-3 leg, correspondence holds.

CONCLUSION: The spec is a tight equality to a concrete total function grounded (via A-reference) in the real callee and validated over 4e5+ inputs; every wrong impl is unprovable, the only verifying same-spec impl is gold-equivalent and its faithful patch resolves. verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on matplotlib__matplotlib-21568 (lean). Modeled function: `_wrap_in_tex(text)` at lib/matplotlib/dates.py:594-601 (post-patch). Spec: `problem_spec_texLabel text result := result = texLabel text`, where texLabel = bracketLetterRuns → per-char escapeMathSym loop → outer `$\mathdefault{`…`}$` wrap → dropToken('$\mathdefault{}$').

Checks performed:
1. Extracted the REAL post-patch callee from the repo worktree (dates.py, and confirmed base is the buggy prepatch — hyphen-only). Post-patch body matches the refinement.md/conformance oracle byte-for-byte: re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text); .replace('-','{-}').replace(':','{:}'); .replace(' ', r'\;'); wrap; .replace('$\mathdefault{}$','').
2. Wrote an INDEPENDENT transliteration of Solution.lean's texLabel (not reusing the bundle shadow) — Char.isAlpha as ASCII-only [A-Za-z], front-recursive run scanner, escapeMathSym, dropToken as non-rescanning left-to-right deletion — and differentially fuzzed against the real callee: 500k mixed-pool + exhaustive over all strings length ≤3 from {a,0,-,:,space,$,\,{,}}, plus a targeted adversarial set (non-ASCII letters é/Ω/café/日 where Python's [a-zA-Z] is ASCII-only and Lean's Char.isAlpha is likewise ASCII-only — they agree; the exact empty-group token as input; back-to-back tokens; recombination pieces `}$$\mathdefault{`; whitespace variety incl. tab/newline where only ' ' is escaped; long runs), plus a 1M unicode-heavy fuzz. ZERO disagreements.
3. Verified the two subtle legs the refinement leans on: (a) dropToken vs Python str.replace over 300k token/fragment-built strings incl. deletions that could create new adjacent matches — NO mismatch (str.replace does not rescan left of cursor, matching dropToken); (b) run-lifting on adjacent runs / letter-symbol boundaries — covered by fuzz.
4. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) == True. Prepatch (hyphen-only) genuinely fails the spec (real bug), confirming the spec is not vacuous.
5. Solution.lean compiles under lean_verify.sh (exit 0) and `#print axioms correct_texLabel` = [propext, Classical.choice, Quot.sound] only — no sorryAx, proof is real.

The modeled function agrees with the real repo callee on every input tried; the spec is neither too strong nor drifted. No diverging input found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment for matplotlib__matplotlib-21568 (lean). Baseline: the public problem_statement is a vague bug report ('Datetime axis with usetex is unclear'; 3.4 spacing wrong vs 3.3) that never names colons, spaces, braces, {:}, \;, {-}, _wrap_in_tex, re.sub, or mathdefault. The gold-edit specifics (colon->{:}, space->\;) live ONLY in hints_text (the monkey-patch snippet), which is NOT the leakage baseline and NOT public.

Mechanical screen (leakage.screen, lean flavor) PASSES clean: no diff markers, no gold-patch line reproduced (>=8-char normalized), no patched file path (lib/matplotlib/dates.py) or module path, no narration terms, and the sole distinctive patched symbol 'wrap_in_tex' is neither embedded in any spec-view identifier (modeled name is 'texLabel', no substring overlap) nor named in any spec-view comment/docstring.

Substantive G-PANEL-3 judgment = NO-LEAKAGE: the spec view (the /-! .. -/ doc + problem_spec_texLabel/texLabel) states the COMPLETE target behavior of the string transform (all four stages, including the UNCHANGED hyphen->{-} handling) rather than the diff. It never marks which stage is 'the fix', never says the old code omitted colon/space handling, contains no bug/fix/regression narration, and mentions nothing matplotlib-specific (no dates/usetex/re.sub). The {-}/{:}/\; and $\mathdefault{}$ literals appear solely as the concrete OUTPUT the behavior must produce (describing behavior, not the edit) — the standard, unavoidable disclosure any faithful spec makes. A solver gets a self-contained generic string-transform specification, not a reconstruction of the gold patch beyond what problem-agnostic correctness requires.

Verified: same_spec(Solution_prepatch.lean, Solution.lean)=True (spec region byte-identical; pre/post differ only in impl+proof), so no leak was introduced via a spec-region edit. Not a relaxed bundle (no RELAXED_LEAKAGE.md, relaxed_leakage flag absent). Recorded meta G-LEAK=pass and prior G-PANEL-3=NO-LEAKAGE are consistent with this independent re-derivation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
