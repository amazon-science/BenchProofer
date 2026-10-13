# P2 adversarial audit — astropy__astropy-14365

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,9 +95,9 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Classify a source line, recognizing categories case-insensitively. -/
+/-- ATTACK (prepatch bug): case-SENSITIVE recognizer. -/
 def implementation_classify (line : List Char) : LineCategory :=
-  matchCategory true line
+  matchCategory false line
 -- impl-end
 
 -- impl-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,11 +101,11 @@
 -- impl-end
 
 -- impl-start
-/-- Read the values of a data row, building one cell per token. -/
+/-- ATTACK (prepatch bug): case-SENSITIVE sentinel test `v = ['N','O']`. -/
 def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
   let mut acc : List Cell := []
   for v in tokens do
-    if v.map Char.toUpper = ['N', 'O'] then
+    if v = ['N', 'O'] then
       acc := acc ++ [Cell.missing]
     else
       acc := acc ++ [Cell.number (parseNumber v)]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,9 +95,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Classify a source line, recognizing categories case-insensitively. -/
+/-- ATTACK (partial-domain): case-insensitive on all lines EXCEPT the empty
+line, which is hard-coded to `comment`. -/
 def implementation_classify (line : List Char) : LineCategory :=
-  matchCategory true line
+  if line = [] then LineCategory.comment else matchCategory true line
 -- impl-end
 
 -- impl-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,14 +101,15 @@
 -- impl-end
 
 -- impl-start
-/-- Read the values of a data row, building one cell per token. -/
+/-- ATTACK (control-flow-effect): PREPEND each cell instead of append, so the
+output cells come out in reversed order. -/
 def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
   let mut acc : List Cell := []
   for v in tokens do
     if v.map Char.toUpper = ['N', 'O'] then
-      acc := acc ++ [Cell.missing]
+      acc := [Cell.missing] ++ acc
     else
-      acc := acc ++ [Cell.number (parseNumber v)]
+      acc := [Cell.number (parseNumber v)] ++ acc
   return acc
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -101,11 +101,14 @@
 -- impl-end
 
 -- impl-start
-/-- Read the values of a data row, building one cell per token. -/
+/-- ATTACK (verifying echo): redundant disjunction `v = NO || v.map toUpper = NO`
+which is extensionally identical to the case-insensitive sentinel test (if
+`v = ['N','O']` then `v.map toUpper = ['N','O']` too). Functionally the gold
+impl — should verify and its refined patch should RESOLVE. -/
 def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
   let mut acc : List Cell := []
   for v in tokens do
-    if v.map Char.toUpper = ['N', 'O'] then
+    if v = ['N', 'O'] || v.map Char.toUpper = ['N', 'O'] then
       acc := acc ++ [Cell.missing]
     else
       acc := acc ++ [Cell.number (parseNumber v)]
@@ -121,11 +124,12 @@
 -- proof-end
 
 -- proof-start
-/-- The appending `forIn` over the token list in `Id` equals the accumulator
-prepended to the per-token cells. Proven by induction with `List.forIn_cons`. -/
+/-- Helper over ATTACK-5's disjunctive loop body. The disjunction
+`v = ['N','O'] || v.map toUpper = ['N','O']` is extensionally equal to the
+case-insensitive sentinel test, so this still folds to `map cellOfToken`. -/
 theorem readRow_helper (tokens : List (List Char)) (init : List Cell) :
     (Id.run (forIn tokens init (fun v r =>
-        (if v.map Char.toUpper = ['N', 'O']
+        (if v = ['N', 'O'] || v.map Char.toUpper = ['N', 'O']
           then ForInStep.yield (r ++ [Cell.missing])
           else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell))))))
     = init ++ tokens.map cellOfToken := by
@@ -135,9 +139,15 @@
     rw [List.forIn_cons, List.map_cons]
     simp only [Id.run, bind] at ih ⊢
     by_cases h : a.map Char.toUpper = ['N', 'O']
-    · simp only [h, if_true, ih]
+    · have hd : (a = ['N','O'] || a.map Char.toUpper = ['N','O']) = true := by
+        simp [h]
+      simp only [hd, if_true, ih]
       simp [cellOfToken, isSentinel, h]
-    · simp only [h, if_false, ih]
+    · have hne : a ≠ ['N','O'] := by
+        intro heq; apply h; rw [heq]; rfl
+      have hd : (a = ['N','O'] || a.map Char.toUpper = ['N','O']) = false := by
+        simp [hne, h]
+      simp only [hd, if_false, ih]
       simp [cellOfToken, isSentinel, h]
 
 theorem correct_readRow :
@@ -147,13 +157,13 @@
   unfold problem_spec_readRow implementation_readRow
   have h2 : (Id.run (do
       let r ← forIn tokens ([] : List Cell) fun v r =>
-        (if v.map Char.toUpper = ['N', 'O']
+        (if v = ['N', 'O'] || v.map Char.toUpper = ['N', 'O']
           then (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.missing])))
           else (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.number (parseNumber v)])))
             : Id (ForInStep (List Cell)))
       pure r) : List Cell)
     = Id.run (forIn tokens ([] : List Cell) fun v r =>
-        (if v.map Char.toUpper = ['N', 'O']
+        (if v = ['N', 'O'] || v.map Char.toUpper = ['N', 'O']
           then ForInStep.yield (r ++ [Cell.missing])
           else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell)))) :=
     rfl
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,8 @@
 -- impl-end
 
 -- impl-start
-/-- Read the values of a data row, building one cell per token. -/
+/-- ATTACK (boundary): correct per token but emits an extra trailing `missing`
+cell, so the output has one too many cells. -/
 def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
   let mut acc : List Cell := []
   for v in tokens do
@@ -109,7 +110,7 @@
       acc := acc ++ [Cell.missing]
     else
       acc := acc ++ [Cell.number (parseNumber v)]
-  return acc
+  return acc ++ [Cell.missing]
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,14 +101,12 @@
 -- impl-end
 
 -- impl-start
-/-- Read the values of a data row, building one cell per token. -/
+/-- ATTACK (ungrounded oracle): ignore the token and always emit `missing`
+(one cell per token but wrong content on non-sentinel tokens). -/
 def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
   let mut acc : List Cell := []
-  for v in tokens do
-    if v.map Char.toUpper = ['N', 'O'] then
-      acc := acc ++ [Cell.missing]
-    else
-      acc := acc ++ [Cell.number (parseNumber v)]
+  for _v in tokens do
+    acc := acc ++ [Cell.missing]
   return acc
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,9 +95,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Classify a source line, recognizing categories case-insensitively. -/
+/-- ATTACK (ungrounded oracle): ignore the line and always return
+`unrecognized`. -/
 def implementation_classify (line : List Char) : LineCategory :=
-  matchCategory true line
+  LineCategory.unrecognized
 -- impl-end
 
 -- impl-start
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,9 +95,11 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Classify a source line, recognizing categories case-insensitively. -/
+/-- ATTACK (verifying echo): `matchCategory (!false) line` — `!false` reduces to
+`true`, so this is definitionally the gold impl. Should verify; its refined
+patch must RESOLVE. -/
 def implementation_classify (line : List Char) : LineCategory :=
-  matchCategory true line
+  matchCategory (!false) line
 -- impl-end
 
 -- impl-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reading a hand-written scientific table whose textual syntax is, by the
format's own definition, **not case sensitive**.

Two behaviors are modeled.

(1) Classifying a single source line into its syntactic category — a header
command, a table-break marker, a row of numeric values (with a column count), a
pure comment, or "unrecognized". Because the format is case-insensitive, the
category a line is assigned must not depend on the letter-case in which the line
was written: any two lines that differ only in the case of their letters belong
to the same category.

(2) Reading the individual values of a data row. One distinguished token denotes
a *missing* value; every other token denotes a number. Identifying the
missing-value token is likewise case-insensitive: the token denotes a missing
value whenever it equals the sentinel up to letter-case, and otherwise it denotes
the number obtained by parsing it.

The behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- Unchanged dependency callees, declared as opaque signatures. Property axioms
-- (if any) are added by the proof agent.
--
-- * `matchCategory ci line` : the line-category recognizer. The `Bool` selects
--   whether recognition is case-insensitive; `matchCategory true` is the
--   case-insensitive recognizer the desired behavior requires. (Its
--   case-invariance — that it gives equal-up-to-case lines the same category —
--   is a behavioral property of the real recognizer, validated against it by the
--   executable check; the proof does not need it as an axiom.)
-- * `parseNumber tok` : the numeric value obtained from a non-sentinel token.

/-- Syntactic category of a source line. `data n` carries the number of value
columns; `unrecognized` is the rejecting outcome. -/
inductive LineCategory where
  | comment
  | command
  | newBlock
  | data (ncol : Nat)
  | unrecognized
deriving DecidableEq, Repr, Inhabited

/-- A parsed numeric value. Its concrete representation is immaterial — it never
appears in a proof obligation, only as the opaque payload of a number cell. -/
abbrev NumVal : Type := Float

/-- The line-category recognizer. The `Bool` selects case-insensitive
recognition (`true`) versus case-sensitive (`false`). -/
opaque matchCategory : Bool → List Char → LineCategory

/-- The numeric value obtained from a token that is not the missing-value
sentinel. -/
opaque parseNumber : List Char → NumVal
-- axioms-end

-- pure-start
/-- One read cell: a missing value, or a number. -/
inductive Cell where
  | missing
  | number (v : NumVal)
deriving Inhabited

/-- Is a token the missing-value sentinel, up to letter-case? The sentinel,
written in upper case, is the two letters `NO`. -/
def isSentinel (tok : List Char) : Bool :=
  tok.map Char.toUpper = ['N', 'O']

/-- The cell a single token denotes: a missing value if the token is the
sentinel (case-insensitively), otherwise the parsed number. -/
def cellOfToken (tok : List Char) : Cell :=
  if isSentinel tok then Cell.missing else Cell.number (parseNumber tok)
-- pure-end

-- post-conditions-start
/-- Category classification is case-insensitive: the result is the category the
*case-insensitive* recognizer assigns to the line — never the category a
case-sensitive recognizer would assign. -/
def problem_spec_classify (line : List Char) (result : LineCategory) : Prop :=
  result = matchCategory true line
-- post-conditions-end

-- post-conditions-start
/-- Reading a data row's values: the result is, token for token, the cell each
token denotes — a missing value when the token is the sentinel up to letter-case,
otherwise the token's parsed number. In particular there is exactly one output
cell per input token, in order. -/
def problem_spec_readRow (tokens : List (List Char)) (result : List Cell) : Prop :=
  result = tokens.map cellOfToken
-- post-conditions-end

-- impl-start
/-- Classify a source line, recognizing categories case-insensitively. -/
def implementation_classify (line : List Char) : LineCategory :=
  matchCategory true line
-- impl-end

-- impl-start
/-- Read the values of a data row, building one cell per token. -/
def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
  let mut acc : List Cell := []
  for v in tokens do
    if v.map Char.toUpper = ['N', 'O'] then
      acc := acc ++ [Cell.missing]
    else
      acc := acc ++ [Cell.number (parseNumber v)]
  return acc
-- impl-end

-- proof-start
theorem correct_classify :
    ∀ line : List Char,
      problem_spec_classify line (implementation_classify line) := by
  intro line
  rfl
-- proof-end

-- proof-start
/-- The appending `forIn` over the token list in `Id` equals the accumulator
prepended to the per-token cells. Proven by induction with `List.forIn_cons`. -/
theorem readRow_helper (tokens : List (List Char)) (init : List Cell) :
    (Id.run (forIn tokens init (fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then ForInStep.yield (r ++ [Cell.missing])
          else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell))))))
    = init ++ tokens.map cellOfToken := by
  induction tokens generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.map_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.map Char.toUpper = ['N', 'O']
    · simp only [h, if_true, ih]
      simp [cellOfToken, isSentinel, h]
    · simp only [h, if_false, ih]
      simp [cellOfToken, isSentinel, h]

theorem correct_readRow :
    ∀ tokens : List (List Char),
      problem_spec_readRow tokens (implementation_readRow tokens) := by
  intro tokens
  unfold problem_spec_readRow implementation_readRow
  have h2 : (Id.run (do
      let r ← forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.missing])))
          else (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.number (parseNumber v)])))
            : Id (ForInStep (List Cell)))
      pure r) : List Cell)
    = Id.run (forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then ForInStep.yield (r ++ [Cell.missing])
          else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell)))) :=
    rfl
  show (Id.run _ : List Cell) = tokens.map cellOfToken
  rw [h2, readRow_helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: both post-conditions are EXACT universal equalities against opaque callees: problem_spec_classify = (result = matchCategory true line); problem_spec_readRow = (result = tokens.map cellOfToken). This pins every verifying impl to be functionally identical to gold, so a genuinely-different impl makes the goal an unprovable proposition (opaque matchCategory/parseNumber have no reduction rules). Confirmed empirically.

SAME-SPEC: all 9 attacks + pos_control return same_spec=True (spec/axioms/pre/post byte-identical; only impl region edited). Re-confirmed after proof edits for atk_5/atk_9.

### ATTACKS (verify = bash scripts/lean_verify.sh <f>, run concurrently ≤4/batch):
- atk_1 classify PREPATCH (matchCategory false): exit 1 (gold rfl fails; goal result=matchCategory true line irreducible). prepatch bug reproduced.
- atk_2 readRow PREPATCH (v = ['N','O'] case-sensitive): exit 1. prepatch bug reproduced.
- atk_3 classify partial-domain (empty line hard-coded to comment): exit 1.
- atk_4 readRow control-flow-effect (prepend => reversed order): exit 1.
- atk_5 readRow VERIFYING ECHO (v=['N','O'] || v.map toUpper=['N','O'], extensionally = case-insensitive test): exit 0, authored genuine proof. #print axioms clean [propext, Classical.choice, Quot.sound]. Faithful patch (P1 gold + P2 'v == "NO" or v.upper() == "NO"') RESOLVED=True COMPLETED=True (FAIL_TO_PASS test_roundtrip[True] + 8 PASS_TO_PASS all pass).
- atk_6 readRow boundary (extra trailing missing cell => length+1): exit 1.
- atk_7 readRow ungrounded oracle (always Cell.missing): exit 1.
- atk_8 classify ungrounded oracle (always unrecognized): exit 1.
- atk_9 classify VERIFYING ECHO (matchCategory (!false) line, !false reduces to true => definitionally gold): exit 0. #print axioms clean. Faithful patch = gold P1+P2 RESOLVED=True COMPLETED=True.

POSITIVE CONTROL pos_control.lean (unmodified gold Solution.lean): verifies exit 0; #print axioms clean.

RESOLVE: run_resolve('astropy__astropy-14365', ...) via official harness (Docker), timeout 1800, on the two verifying attacks. BOTH resolved (patch_successfully_applied=True, resolved=True). => verify⇒correct holds; no verifying impl with a closing clean-axiom proof has a non-resolving faithful patch.

REFINEMENT.MD A-LEG AUDIT: Triple 1 op1 matchCategory true = A-reference ↔ patched _line_type re.IGNORECASE; rfl-discharged, no property axiom; case-invariance validated by G-AX axiom_check.py (git-applies gold patch, 20k fuzz + issue lines). matchCategory false (prepatch) fails spec = confirmed G-DIFF discriminator (atk_1). Triple 2: op3 sentinel test + op4/5 cell-tagging = R (deeply modeled, G-CONF differential-tested 1e5 seed 20240629); parseNumber = A-reference (unchanged int/float parser, never reached for sentinel, no property axiom); init/iter/return = I. Every leg is R / A-reference / I — NO kind-3 (no changed op axiomatized). A-references correspond to the real patched callees. Audit PASSES.

VERDICT: SOUND. 9 distinct same-spec wrong/echo attacks run (>=5 required); 7 genuinely-wrong impls all fail to verify (spec is a tight exact-equality); the 2 that verify are functional echoes whose faithful refined patches both RESOLVE under the official harness. No break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reading a hand-written scientific table whose textual syntax is, by the
format's own definition, **not case sensitive**.

Two behaviors are modeled.

(1) Classifying a single source line into its syntactic category — a header
command, a table-break marker, a row of numeric values (with a column count), a
pure comment, or "unrecognized". Because the format is case-insensitive, the
category a line is assigned must not depend on the letter-case in which the line
was written: any two lines that differ only in the case of their letters belong
to the same category.

(2) Reading the individual values of a data row. One distinguished token denotes
a *missing* value; every other token denotes a number. Identifying the
missing-value token is likewise case-insensitive: the token denotes a missing
value whenever it equals the sentinel up to letter-case, and otherwise it denotes
the number obtained by parsing it.

The behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- Unchanged dependency callees, declared as opaque signatures. Property axioms
-- (if any) are added by the proof agent.
--
-- * `matchCategory ci line` : the line-category recognizer. The `Bool` selects
--   whether recognition is case-insensitive; `matchCategory true` is the
--   case-insensitive recognizer the desired behavior requires. (Its
--   case-invariance — that it gives equal-up-to-case lines the same category —
--   is a behavioral property of the real recognizer, validated against it by the
--   executable check; the proof does not need it as an axiom.)
-- * `parseNumber tok` : the numeric value obtained from a non-sentinel token.

/-- Syntactic category of a source line. `data n` carries the number of value
columns; `unrecognized` is the rejecting outcome. -/
inductive LineCategory where
  | comment
  | command
  | newBlock
  | data (ncol : Nat)
  | unrecognized
deriving DecidableEq, Repr, Inhabited

/-- A parsed numeric value. Its concrete representation is immaterial — it never
appears in a proof obligation, only as the opaque payload of a number cell. -/
abbrev NumVal : Type := Float

/-- The line-category recognizer. The `Bool` selects case-insensitive
recognition (`true`) versus case-sensitive (`false`). -/
opaque matchCategory : Bool → List Char → LineCategory

/-- The numeric value obtained from a token that is not the missing-value
sentinel. -/
opaque parseNumber : List Char → NumVal
-- axioms-end

-- pure-start
/-- One read cell: a missing value, or a number. -/
inductive Cell where
  | missing
  | number (v : NumVal)
deriving Inhabited

/-- Is a token the missing-value sentinel, up to letter-case? The sentinel,
written in upper case, is the two letters `NO`. -/
def isSentinel (tok : List Char) : Bool :=
  tok.map Char.toUpper = ['N', 'O']

/-- The cell a single token denotes: a missing value if the token is the
sentinel (case-insensitively), otherwise the parsed number. -/
def cellOfToken (tok : List Char) : Cell :=
  if isSentinel tok then Cell.missing else Cell.number (parseNumber tok)
-- pure-end

-- post-conditions-start
/-- Category classification is case-insensitive: the result is the category the
*case-insensitive* recognizer assigns to the line — never the category a
case-sensitive recognizer would assign. -/
def problem_spec_classify (line : List Char) (result : LineCategory) : Prop :=
  result = matchCategory true line
-- post-conditions-end

-- post-conditions-start
/-- Reading a data row's values: the result is, token for token, the cell each
token denotes — a missing value when the token is the sentinel up to letter-case,
otherwise the token's parsed number. In particular there is exactly one output
cell per input token, in order. -/
def problem_spec_readRow (tokens : List (List Char)) (result : List Cell) : Prop :=
  result = tokens.map cellOfToken
-- post-conditions-end

-- impl-start
/-- Classify a source line, recognizing categories case-insensitively. -/
def implementation_classify (line : List Char) : LineCategory :=
  matchCategory true line
-- impl-end

-- impl-start
/-- Read the values of a data row, building one cell per token. -/
def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
  let mut acc : List Cell := []
  for v in tokens do
    if v.map Char.toUpper = ['N', 'O'] then
      acc := acc ++ [Cell.missing]
    else
      acc := acc ++ [Cell.number (parseNumber v)]
  return acc
-- impl-end

-- proof-start
theorem correct_classify :
    ∀ line : List Char,
      problem_spec_classify line (implementation_classify line) := by
  intro line
  rfl
-- proof-end

-- proof-start
/-- The appending `forIn` over the token list in `Id` equals the accumulator
prepended to the per-token cells. Proven by induction with `List.forIn_cons`. -/
theorem readRow_helper (tokens : List (List Char)) (init : List Cell) :
    (Id.run (forIn tokens init (fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then ForInStep.yield (r ++ [Cell.missing])
          else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell))))))
    = init ++ tokens.map cellOfToken := by
  induction tokens generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.map_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.map Char.toUpper = ['N', 'O']
    · simp only [h, if_true, ih]
      simp [cellOfToken, isSentinel, h]
    · simp only [h, if_false, ih]
      simp [cellOfToken, isSentinel, h]

theorem correct_readRow :
    ∀ tokens : List (List Char),
      problem_spec_readRow tokens (implementation_readRow tokens) := by
  intro tokens
  unfold problem_spec_readRow implementation_readRow
  have h2 : (Id.run (do
      let r ← forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.missing])))
          else (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.number (parseNumber v)])))
            : Id (ForInStep (List Cell)))
      pure r) : List Cell)
    = Id.run (forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then ForInStep.yield (r ++ [Cell.missing])
          else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell)))) :=
    rfl
  show (Id.run _ : List Cell) = tokens.map cellOfToken
  rw [h2, readRow_helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: both post-conditions are EXACT universal equalities against opaque callees: problem_spec_classify = (result = matchCategory true line); problem_spec_readRow = (result = tokens.map cellOfToken). This pins every verifying impl to be functionally identical to gold, so a genuinely-different impl makes the goal an unprovable proposition (opaque matchCategory/parseNumber have no reduction rules). Confirmed empirically.

SAME-SPEC: all 9 attacks + pos_control return same_spec=True (spec/axioms/pre/post byte-identical; only impl region edited). Re-confirmed after proof edits for atk_5/atk_9.

### ATTACKS (verify = bash scripts/lean_verify.sh <f>, run concurrently ≤4/batch):
- atk_1 classify PREPATCH (matchCategory false): exit 1 (gold rfl fails; goal result=matchCategory true line irreducible). prepatch bug reproduced.
- atk_2 readRow PREPATCH (v = ['N','O'] case-sensitive): exit 1. prepatch bug reproduced.
- atk_3 classify partial-domain (empty line hard-coded to comment): exit 1.
- atk_4 readRow control-flow-effect (prepend => reversed order): exit 1.
- atk_5 readRow VERIFYING ECHO (v=['N','O'] || v.map toUpper=['N','O'], extensionally = case-insensitive test): exit 0, authored genuine proof. #print axioms clean [propext, Classical.choice, Quot.sound]. Faithful patch (P1 gold + P2 'v == "NO" or v.upper() == "NO"') RESOLVED=True COMPLETED=True (FAIL_TO_PASS test_roundtrip[True] + 8 PASS_TO_PASS all pass).
- atk_6 readRow boundary (extra trailing missing cell => length+1): exit 1.
- atk_7 readRow ungrounded oracle (always Cell.missing): exit 1.
- atk_8 classify ungrounded oracle (always unrecognized): exit 1.
- atk_9 classify VERIFYING ECHO (matchCategory (!false) line, !false reduces to true => definitionally gold): exit 0. #print axioms clean. Faithful patch = gold P1+P2 RESOLVED=True COMPLETED=True.

POSITIVE CONTROL pos_control.lean (unmodified gold Solution.lean): verifies exit 0; #print axioms clean.

RESOLVE: run_resolve('astropy__astropy-14365', ...) via official harness (Docker), timeout 1800, on the two verifying attacks. BOTH resolved (patch_successfully_applied=True, resolved=True). => verify⇒correct holds; no verifying impl with a closing clean-axiom proof has a non-resolving faithful patch.

REFINEMENT.MD A-LEG AUDIT: Triple 1 op1 matchCategory true = A-reference ↔ patched _line_type re.IGNORECASE; rfl-discharged, no property axiom; case-invariance validated by G-AX axiom_check.py (git-applies gold patch, 20k fuzz + issue lines). matchCategory false (prepatch) fails spec = confirmed G-DIFF discriminator (atk_1). Triple 2: op3 sentinel test + op4/5 cell-tagging = R (deeply modeled, G-CONF differential-tested 1e5 seed 20240629); parseNumber = A-reference (unchanged int/float parser, never reached for sentinel, no property axiom); init/iter/return = I. Every leg is R / A-reference / I — NO kind-3 (no changed op axiomatized). A-references correspond to the real patched callees. Audit PASSES.

VERDICT: SOUND. 9 distinct same-spec wrong/echo attacks run (>=5 required); 7 genuinely-wrong impls all fail to verify (spec is a tight exact-equality); the 2 that verify are functional echoes whose faithful refined patches both RESOLVE under the official harness. No break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of astropy__astropy-14365 lean bundle.

ARTIFACT SANITY: Solution.lean compiles clean via lean_verify.sh (exit 0, no sorry). `#print axioms`: correct_classify depends on NO axioms; correct_readRow depends only on [propext, Classical.choice, Quot.sound] — no sorryAx, proofs are genuine. Spec region byte-identical to both prepatch variants under swebench_unified.markers.same_spec(...,backend=lean) → True/True.

Model maps two independently-fixed behaviors of astropy/io/ascii/qdp.py (patch.diff P1: re.compile(_type_re) → re.IGNORECASE; P2: `if v == "NO"` → `if v.upper() == "NO"`).

BEHAVIOR 1 (classify): problem_spec_classify line result := result = matchCategory true line, with matchCategory an opaque A-reference = the real patched regex recognizer. Spec is a pure pin to the case-insensitive-mode callee (rfl-discharged, no property axiom). No spec-side over-strength possible: it asserts nothing beyond "= the real callee's output". The semantic case-invariance property is validated externally by G-AX (axiom_check.py) against the real re.IGNORECASE matcher, not asserted in Lean.

BEHAVIOR 2 (readRow): problem_spec_readRow tokens result := result = tokens.map cellOfToken, cellOfToken = if isSentinel tok then missing else number (parseNumber tok). parseNumber opaque = real int()/float() parser (A-reference, untouched by patch). The only concrete/R modeled decision is isSentinel tok := tok.map Char.toUpper = ['N','O'] vs the real Python `v.upper() == "NO"`.

FAITHFULNESS PROBE of the sole discriminator: exhaustively scanned all 0x110000 Unicode code points. Only chars whose upper() equals 'N' are {0x4E,0x6E}, only ones equal to 'O' are {0x4F,0x6F}; NO char upper()s to the two-char string 'NO', and no char has empty/expanding upper() relevant here. Therefore the Python sentinel set is exactly {NO,No,nO,no}. Lean's ASCII-only Char.toUpper fold produces the SAME set (verified: zero disagreements). So the R leg does not over- or under-constrain relative to the real callee.

G-CONF EXECUTED: patched installed astropy (both P1+P2), ran conformance_check.py → 'G-CONF OK: 96837 cases agree (of 100000 generated), seed=20240629'. Shadow (v.upper()==NO + real int/float) matches the patched reader's masked-vs-number cells exactly.

CONCLUSION: The modeled functions agree with the real patched repo callees on every input tested and, for the only concretely-modeled leg (isSentinel), on the entire Unicode input domain by exhaustive proof. No input found where the spec is stronger than / drifts from real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures); spec regions byte-identical across Solution.lean and both prepatch variants; same_spec = True.

Semantic leakage assessment against the PUBLIC problem_statement only (not hints_text):

The public problem statement already establishes the entire fix theme: 'ascii.qdp assumes that commands in a QDP file are upper case ... QDP itself is not case sensitive ... the expectation that all commands be all-caps should be removed', with the worked example of lowercase `read serr 1 2` needing to parse. Thus case-insensitivity of QDP parsing is the publicly-declared intended behavior.

Spec view checks:
- No patched repo symbols disclosed: view uses abstract names (matchCategory, parseNumber, isSentinel, cellOfToken, LineCategory, Cell). The patched functions _line_type / _get_tables_from_qdp_file never appear; changed symbols {line_type, get_tables_from_qdp_file} not present.
- No diff markers, no patched file path (astropy/io/ascii/qdp.py) or dotted module path in the view.
- No gold-patch changed line reproduced (`re.IGNORECASE`, `if v.upper() == "NO":` do not appear; normalized-form collisions none).
- No bug/fix narration terms in comments/docstrings; prose is normative present-tense stating required input->output behavior.
- Behavior 1 (case-insensitive classification) is exactly the reported issue. Behavior 2 (case-insensitive missing-value sentinel 'NO') is not verbatim in the problem statement, but it is a direct application of the SAME public general principle ('QDP is not case sensitive') to a second parsing location; it discloses the required behavior, not the edit mechanic (`.upper()`) or its file/line location. The concrete sentinel token 'NO' is a documented QDP-format fact needed for a well-defined spec, not a gold-edit disclosure.

The spec states required behavior abstractly with no edit-localization beyond the public theme. Nothing leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
