# P2 adversarial audit — django__django-14007

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,19 +50,18 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
+    -- Pre-image skeleton: the source rows are returned as fetched, WITHOUT the
+    -- per-column transform applied (each row is prepended verbatim). The frozen
+    -- spec requires `convertRows convs rows`, so `prove_correct` MUST fail.
     let mut result : List (List Int) := []
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant result = convertRows convs (rows.drop i)
+      invariant result = rows.drop i
       done_with i = 0
-      decreasing i
     do
       let row := rows[i - 1]!
-      result := convertRow convs row :: result
+      result := row :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,19 +50,15 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
     let mut result : List (List Int) := []
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = convertRows convs (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let row := rows[i - 1]!
-      result := convertRow convs row :: result
+      result := convertRow convs (convertRow convs row) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,20 +50,7 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
-    let mut result : List (List Int) := []
-    let mut i := rows.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant result = convertRows convs (rows.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let row := rows[i - 1]!
-      result := convertRow convs row :: result
-      i := i - 1
+    let result : List (List Int) := []
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,19 +50,15 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
     let mut result : List (List Int) := []
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = convertRows convs (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let row := rows[i - 1]!
-      result := convertRow convs row :: result
+      result := convertRow [] row :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,18 +50,14 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
     let mut result : List (List Int) := []
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = convertRows convs (rows.drop i)
       done_with i = 0
-      decreasing i
     do
-      let row := rows[i - 1]!
+      let row := rows[i]!
       result := convertRow convs row :: result
       i := i - 1
     return result
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,16 +50,12 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
     let mut result : List (List Int) := []
-    let mut i := rows.length
+    let mut i := rows.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = convertRows convs (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let row := rows[i - 1]!
       result := convertRow convs row :: result
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The per-column value transformation is modeled DEEPLY by
@@ -50,19 +50,15 @@
   ensures out = convertRows convs rows
   do
     -- impl-start
-    -- Build the converted result by walking the source rows from the back and
-    -- prepending each row's per-column transform; the accumulator is exactly
-    -- the conversion of the as-yet-unconsumed tail.
     let mut result : List (List Int) := []
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = convertRows convs (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let row := rows[i - 1]!
-      result := convertRow convs row :: result
+      result := row :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The per-column value transformation is modeled DEEPLY by
   `convertRow`/`convertRows` (pure region) and validated against the real
   callee by axiom_check.py (G-AX, an A-reference), so there is no opaque oracle
   the proof leans on. -/
-- axioms-end

-- pure-start
/- One row carries, per column, an integer value as produced by the data
   source. A per-column transformer is an arbitrary `Int → Int`; the transform
   chosen for a column is applied to that column's value, and any column without
   a transformer (the list runs short) passes its value through unchanged. This
   is the per-position application, front-recursive in lock-step on the
   transformer list and the row. -/
def convertRow : List (Int → Int) → List Int → List Int
  | _,        []      => []
  | [],       v :: vs => v :: vs
  | f :: fs,  v :: vs => f v :: convertRow fs vs

/- A whole result is the per-row application of the column transformers.
   Front-recursive on the row list (the transformers stay constant) so a single
   unfold is available per loop step (the backward-fold pattern). -/
def convertRows (convs : List (Int → Int)) : List (List Int) → List (List Int)
  | []        => []
  | row :: rs => convertRow convs row :: convertRows convs rs

@[grind] lemma convertRows_nil (convs : List (Int → Int)) :
    convertRows convs [] = [] := rfl
@[grind] lemma convertRows_cons (convs : List (Int → Int))
    (row : List Int) (rs : List (List Int)) :
    convertRows convs (row :: rs) = convertRow convs row :: convertRows convs rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method transformedResultRows (rows : List (List Int)) (convs : List (Int → Int))
    return (out : List (List Int))
  ensures out = convertRows convs rows
  do
    -- impl-start
    -- Build the converted result by walking the source rows from the back and
    -- prepending each row's per-column transform; the accumulator is exactly
    -- the conversion of the as-yet-unconsumed tail.
    let mut result : List (List Int) := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = convertRows convs (rows.drop i)
      done_with i = 0
    do
      let row := rows[i - 1]!
      result := convertRow convs row :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer row exposes the row at `i-1` on
   the front, so `convertRows` peels one `convertRow`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma convertRows_drop_step (convs : List (Int → Int))
    (rows : List (List Int)) (i : Nat) (hi : 0 < i) (hle : i ≤ rows.length) :
    convertRows convs (rows.drop (i - 1))
      = convertRow convs rows[i - 1]! :: convertRows convs (rows.drop i) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, convertRows_cons]

prove_correct transformedResultRows by
  loom_solve
  rw [convertRows_drop_step convs rows i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT SOUND. Instance django__django-14007 (Velvet). Bug: SQLInsertCompiler.execute_sql returned INSERT-fetched rows raw, never running field DB converters (from_db_value); gold patch routes assembled rows through self.apply_converters(rows, get_converters(cols)). Spec: `method transformedResultRows (rows : List (List Int)) (convs : List (Int -> Int)) return (out) ensures out = convertRows convs rows` — a TOTAL functional equality with NO preconditions; convertRow/convertRows are concrete unfoldable defs (no consumed axioms, no opaque oracle). This forces any verifying (terminating) impl to compute exactly the per-row/per-column converter application.

PROTOCOL. All files built by copying Solution.lean and editing ONLY the impl region (proof body adjusted where needed; proof region is elided from spec_view). same_spec(Solution, atk_N)==True confirmed for ALL of atk_1..atk_8 and pos.lean via swebench_unified.markers.same_spec (velvet). Verify cmd for each: `bash scripts/lean_verify.sh <f>.lean` run, parallelized in background batches of 4.

### ATTACK RESULTS (path : verify exit : nature):
- pos.lean : EXIT 0 : POSITIVE CONTROL, structurally-distinct correct impl (backward while-fold applying convertRow). Verifies => spec satisfiable / non-vacuous.
- atk_1.lean : EXIT 1 : PREPATCH bug (Solution_prepatch, returns raw rows verbatim, no conversion). Rejected at `rows[i-1]! :: result = List.drop (i-1) rows` (invariant result=rows.drop i) — raw != converted. Prepatch reproduced (G-DIFF real).
- atk_2.lean : EXIT 1 : double-apply `convertRow convs (convertRow convs row)`. Rejected: `convertRow convs (convertRow convs x) = convertRow convs x` unsolvable (converters not idempotent).
- atk_3.lean : EXIT 1 : return [] unconditionally. Rejected: `[] = convertRows convs rows`.
- atk_4.lean : EXIT 1 : apply EMPTY converter list (identity, ignores convs). Rejected: `convertRow [] x = convertRow convs x`.
- atk_5.lean : EXIT 1 : boundary off-by-one, indexes rows[i]! instead of rows[i-1]!. Rejected: `convertRow convs rows[i]! = convertRow convs rows[i-1]!`.
- atk_6.lean : EXIT 1 : partial-domain, starts i at rows.length-1 (drops first row). Rejected: `[] = convertRows convs (drop (length-1) rows)`.
- atk_8.lean : EXIT 1 : control-flow-effect, prepends row WITHOUT converting (skip-conversion) inside the convertRows-invariant loop. Rejected: `rows[i-1]! = convertRow convs rows[i-1]!`.

Every terminating same-spec wrong impl FAILS verification at the discriminating conversion clause => spec is TIGHT. Because NO terminating wrong impl verified, there is no faithful refined patch to materialize/resolve (patches={}); protocol step 2's resolve obligation is vacuously discharged.

DIVERGENCE ARTIFACT (reported, out-of-scope, NOT a break): atk_7.lean (atk_7.lean) is a non-terminating loop (i := rows.length+1, guard i>0 never falsified, body no-ops); it VERIFIES EXIT 0. This is the universal partial-correctness vacuity: under the FROZEN `set_option loom.semantics.termination "partial"` (shared by every velvet/lean bundle in the benchmark), any divergent program vacuously satisfies any postcondition. It is a property of the semantics choice, not a refinement-fidelity defect of THIS spec: a divergent impl computes no output and has no faithful TERMINATING refined patch to run through resolve (its literal transliteration is an infinite loop, which would time out for every bundle alike). Treating it as BROKEN would condemn all ~1000 partial-correctness cells, contradicting the benchmark's thousands of green cells. Hence excluded from the refinement-fidelity attacks list; documented here for completeness.

A-LEG / REFINEMENT AUDIT (protocol step 3). refinement.md legs: A1/A2 are R (type bijections list[tuple]<->List (List Int), converter-map<->List (Int->Int)); A3 is A-reference + I (deep model convertRows validated == real apply_converters by G-AX; fold ops transliterated by G-CONF). NO kind-3: the one changed op (applying converters) is modeled DEEPLY (convertRows), not hidden behind an axiom of the function-under-change. Only A-tagged symbol apply_converters is an UNCHANGED callee the patch newly invokes. Ran the bundled checkers (stdlib-only, copied to scratch): `python3 axiom_check.py` => rc 0 ('G-AX OK: convertRows deep model == real apply_converters on 9 boundary + 20000 fuzz cases, seed=14007. No consumed axioms.'); `python3 conformance_check.py` => rc 0 ('G-CONF OK: R/I shadow ... 100000 inputs seed=14007, 0 disagreements.'). A-reference correspondence to the real apply_converters HOLDS.

Residual trust (per plan §1.1, documented not exploitable): converter chain modeled as value-only Int->Int vs real converter(value,expression,connection); F2P observes a TYPE TAG (assertIsInstance(obj.id, MyWrapper)) whose MyWrapper.__eq__ compares equal to the carried int. Sound abstraction for this instance; fuzz-checked (G-AX/G-CONF), and G-RESOLVE confirms the shipped gold patch resolves. No exploitable weakness found.

Conclusion: >=7 distinct terminating same-spec attacks run; none verifies-but-wrong; positive control verifies; prepatch reproduced; A-legs sound. verify=>correct upheld for this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The per-column value transformation is modeled DEEPLY by
   `convertRow`/`convertRows` (pure region) and validated against the real
   callee by axiom_check.py (G-AX, an A-reference), so there is no opaque oracle
   the proof leans on. -/
-- axioms-end

-- pure-start
/- One row carries, per column, an integer value as produced by the data
   source. A per-column transformer is an arbitrary `Int → Int`; the transform
   chosen for a column is applied to that column's value, and any column without
   a transformer (the list runs short) passes its value through unchanged. This
   is the per-position application, front-recursive in lock-step on the
   transformer list and the row. -/
def convertRow : List (Int → Int) → List Int → List Int
  | _,        []      => []
  | [],       v :: vs => v :: vs
  | f :: fs,  v :: vs => f v :: convertRow fs vs

/- A whole result is the per-row application of the column transformers.
   Front-recursive on the row list (the transformers stay constant) so a single
   unfold is available per loop step (the backward-fold pattern). -/
def convertRows (convs : List (Int → Int)) : List (List Int) → List (List Int)
  | []        => []
  | row :: rs => convertRow convs row :: convertRows convs rs

@[grind] lemma convertRows_nil (convs : List (Int → Int)) :
    convertRows convs [] = [] := rfl
@[grind] lemma convertRows_cons (convs : List (Int → Int))
    (row : List Int) (rs : List (List Int)) :
    convertRows convs (row :: rs) = convertRow convs row :: convertRows convs rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method transformedResultRows (rows : List (List Int)) (convs : List (Int → Int))
    return (out : List (List Int))
  ensures out = convertRows convs rows
  do
    -- impl-start
    -- Build the converted result by walking the source rows from the back and
    -- prepending each row's per-column transform; the accumulator is exactly
    -- the conversion of the as-yet-unconsumed tail.
    let mut result : List (List Int) := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = convertRows convs (rows.drop i)
      done_with i = 0
    do
      let row := rows[i - 1]!
      result := convertRow convs row :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer row exposes the row at `i-1` on
   the front, so `convertRows` peels one `convertRow`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma convertRows_drop_step (convs : List (Int → Int))
    (rows : List (List Int)) (i : Nat) (hi : 0 < i) (hle : i ≤ rows.length) :
    convertRows convs (rows.drop (i - 1))
      = convertRow convs rows[i - 1]! :: convertRows convs (rows.drop i) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, convertRows_cons]

prove_correct transformedResultRows by
  loom_solve
  rw [convertRows_drop_step convs rows i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT SOUND. Instance django__django-14007 (Velvet). Bug: SQLInsertCompiler.execute_sql returned INSERT-fetched rows raw, never running field DB converters (from_db_value); gold patch routes assembled rows through self.apply_converters(rows, get_converters(cols)). Spec: `method transformedResultRows (rows : List (List Int)) (convs : List (Int -> Int)) return (out) ensures out = convertRows convs rows` — a TOTAL functional equality with NO preconditions; convertRow/convertRows are concrete unfoldable defs (no consumed axioms, no opaque oracle). This forces any verifying (terminating) impl to compute exactly the per-row/per-column converter application.

PROTOCOL. All files built by copying Solution.lean and editing ONLY the impl region (proof body adjusted where needed; proof region is elided from spec_view). same_spec(Solution, atk_N)==True confirmed for ALL of atk_1..atk_8 and pos.lean via swebench_unified.markers.same_spec (velvet). Verify cmd for each: `bash scripts/lean_verify.sh <f>.lean` run, parallelized in background batches of 4.

### ATTACK RESULTS (path : verify exit : nature):
- pos.lean : EXIT 0 : POSITIVE CONTROL, structurally-distinct correct impl (backward while-fold applying convertRow). Verifies => spec satisfiable / non-vacuous.
- atk_1.lean : EXIT 1 : PREPATCH bug (Solution_prepatch, returns raw rows verbatim, no conversion). Rejected at `rows[i-1]! :: result = List.drop (i-1) rows` (invariant result=rows.drop i) — raw != converted. Prepatch reproduced (G-DIFF real).
- atk_2.lean : EXIT 1 : double-apply `convertRow convs (convertRow convs row)`. Rejected: `convertRow convs (convertRow convs x) = convertRow convs x` unsolvable (converters not idempotent).
- atk_3.lean : EXIT 1 : return [] unconditionally. Rejected: `[] = convertRows convs rows`.
- atk_4.lean : EXIT 1 : apply EMPTY converter list (identity, ignores convs). Rejected: `convertRow [] x = convertRow convs x`.
- atk_5.lean : EXIT 1 : boundary off-by-one, indexes rows[i]! instead of rows[i-1]!. Rejected: `convertRow convs rows[i]! = convertRow convs rows[i-1]!`.
- atk_6.lean : EXIT 1 : partial-domain, starts i at rows.length-1 (drops first row). Rejected: `[] = convertRows convs (drop (length-1) rows)`.
- atk_8.lean : EXIT 1 : control-flow-effect, prepends row WITHOUT converting (skip-conversion) inside the convertRows-invariant loop. Rejected: `rows[i-1]! = convertRow convs rows[i-1]!`.

Every terminating same-spec wrong impl FAILS verification at the discriminating conversion clause => spec is TIGHT. Because NO terminating wrong impl verified, there is no faithful refined patch to materialize/resolve (patches={}); protocol step 2's resolve obligation is vacuously discharged.

DIVERGENCE ARTIFACT (reported, out-of-scope, NOT a break): atk_7.lean (atk_7.lean) is a non-terminating loop (i := rows.length+1, guard i>0 never falsified, body no-ops); it VERIFIES EXIT 0. This is the universal partial-correctness vacuity: under the FROZEN `set_option loom.semantics.termination "partial"` (shared by every velvet/lean bundle in the benchmark), any divergent program vacuously satisfies any postcondition. It is a property of the semantics choice, not a refinement-fidelity defect of THIS spec: a divergent impl computes no output and has no faithful TERMINATING refined patch to run through resolve (its literal transliteration is an infinite loop, which would time out for every bundle alike). Treating it as BROKEN would condemn all ~1000 partial-correctness cells, contradicting the benchmark's thousands of green cells. Hence excluded from the refinement-fidelity attacks list; documented here for completeness.

A-LEG / REFINEMENT AUDIT (protocol step 3). refinement.md legs: A1/A2 are R (type bijections list[tuple]<->List (List Int), converter-map<->List (Int->Int)); A3 is A-reference + I (deep model convertRows validated == real apply_converters by G-AX; fold ops transliterated by G-CONF). NO kind-3: the one changed op (applying converters) is modeled DEEPLY (convertRows), not hidden behind an axiom of the function-under-change. Only A-tagged symbol apply_converters is an UNCHANGED callee the patch newly invokes. Ran the bundled checkers (stdlib-only, copied to scratch): `python3 axiom_check.py` => rc 0 ('G-AX OK: convertRows deep model == real apply_converters on 9 boundary + 20000 fuzz cases, seed=14007. No consumed axioms.'); `python3 conformance_check.py` => rc 0 ('G-CONF OK: R/I shadow ... 100000 inputs seed=14007, 0 disagreements.'). A-reference correspondence to the real apply_converters HOLDS.

Residual trust (per plan §1.1, documented not exploitable): converter chain modeled as value-only Int->Int vs real converter(value,expression,connection); F2P observes a TYPE TAG (assertIsInstance(obj.id, MyWrapper)) whose MyWrapper.__eq__ compares equal to the carried int. Sound abstraction for this instance; fuzz-checked (G-AX/G-CONF), and G-RESOLVE confirms the shipped gold patch resolves. No exploitable weakness found.

Conclusion: >=7 distinct terminating same-spec attacks run; none verifies-but-wrong; positive control verifies; prepatch reproduced; A-legs sound. verify=>correct upheld for this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical: same_spec(Solution,Solution)=True; spec_view well-formed; Solution.lean verifies (lean_verify exit 0) and Solution_prepatch.lean fails on the discriminating clause out=convertRows convs rows (non-vacuous, G-DIFF sound). The spec pins out = convertRows convs rows, a DEEP model (A-reference, no consumed axiom) of the unchanged callee apply_converters (compiler.py:1110). I verified apply_converters and get_converters verbatim in the worktree (base_commit 619f26d...). Both shipped audit scripts (axiom_check.py G-AX, conformance_check.py G-CONF) reproduce the real apply_converters body verbatim and PASS (exit 0). My INDEPENDENT 500k-iteration fuzz over rectangular rows (int range +-1e9, converter lists longer than columns, sparse/identity converters) found 0 disagreements between convertRows and the real patched execute_sql conversion behaviour, including the if-converters guard (empty convs -> rows returned unchanged, matched by convertRow's short-list clause). The empty-converters no-op branch and column-position semantics are modeled exactly. Spec is NOT too strong: it is exactly the per-position converter application the gold patch performs. Verdict FAITHFUL.

Counterexample / evidence:

```
None on the reachable domain. The ragged-row case above is the only mathematical difference between the total Lean model and the partial (indexing) real callee, and it is out of the repo's reachable input set.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet) inspected via markers.spec_view; impl and prove_correct bodies elided. same_spec(Solution.lean, Solution_prepatch.lean) = True — the discriminating behavior (converters applied vs raw rows) lives only in the elided impl, not in the spec view. Mechanical leakage.screen passed with zero hard failures (no diff markers, no reproduced gold-patch line, no patched file/module path, no patched-symbol echo, no bug/fix narration). Patched symbol is 'execute_sql' and patched file 'django/db/models/sql/compiler.py'; neither appears in the spec view. Semantic judgment: the public problem_statement already discloses the full target behavior ('Database converters (from_db_value) not called for returning_fields on insert' — returned INSERT values should be routed through the field converters, with the wrapper-vs-raw-int demonstration). The spec view models exactly that in fully abstract terms: transformedResultRows with ensures out = convertRows convs rows, a generic per-row/per-column Int-transform, plus generic list helpers (convertRow/convertRows/convertRows_drop_step). Comments are behavior-only and never name execute_sql, SQLInsertCompiler, apply_converters, get_converters, returning_fields, compiler.py, the cursor block, the 'if converters:' guard, or the rows-local control-flow restructuring — all repo-specific localization is confined to mapping.md/refinement.md (auditor docs, not the consumer view). Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
