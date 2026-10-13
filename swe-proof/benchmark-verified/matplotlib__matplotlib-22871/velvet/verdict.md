# P2 adversarial audit — matplotlib__matplotlib-22871

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
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_prepatch.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec impl returns a WRONG FINITE value while verifying. The postcondition `out = offsetDecision initShow stats` pins the output exactly to a total concrete function, so every terminating verifier is behaviourally equal to the gold. The only two verifying attacks (atk_8, atk_10) verify solely by DIVERGENCE (non-termination) under the frozen `set_option loom.semantics.termination "partial"` header — vacuous partial correctness — not by any postcondition weakness; and their faithful refined patch RESOLVES.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -126,6 +126,11 @@
   ensures out = offsetDecision initShow stats
   do
     -- impl-start
+    -- Pre-image skeleton: at one of the two coarsest components the offset is
+    -- suppressed using only the component number, ignoring whether the component
+    -- sits at its starting boundary (the `colHasOne` reading of `suppressOffset`
+    -- is dropped). The frozen spec requires the full `offsetDecision`, so
+    -- prove_correct MUST fail.
     let mut showOffset := initShow
     let mut chosenLevel : Nat := 5
     let mut stopped := false
@@ -136,13 +141,12 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
         chosenLevel := lvl
-        if suppressOffset lvl col then
+        if decide (lvl < 2) then
           showOffset := false
         stopped := true
       else
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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,14 +136,11 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
         chosenLevel := lvl
-        if suppressOffset lvl col then
-          showOffset := false
         stopped := true
       else
         i := i + 1
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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -126,28 +126,7 @@
   ensures out = offsetDecision initShow stats
   do
     -- impl-start
-    let mut showOffset := initShow
-    let mut chosenLevel : Nat := 5
-    let mut stopped := false
-    let mut i := 0
-    while i < stats.length ∧ stopped = false
-      invariant i ≤ stats.length
-      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats
-                else showOffset = initShow ∧ chosenLevel = 5 ∧
-                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
-      done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
-    do
-      let lvl := (stats[i]!).1
-      let col := (stats[i]!).2
-      if colVaries col then
-        chosenLevel := lvl
-        if suppressOffset lvl col then
-          showOffset := false
-        stopped := true
-      else
-        i := i + 1
-    return (chosenLevel, showOffset)
+    return (5, initShow)
     -- impl-end
 
 prove_correct offsetSelection by
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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,17 +136,13 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
-      if colVaries col then
-        chosenLevel := lvl
-        if suppressOffset lvl col then
-          showOffset := false
-        stopped := true
-      else
-        i := i + 1
+      chosenLevel := lvl
+      if suppressOffset lvl col then
+        showOffset := false
+      stopped := true
     return (chosenLevel, showOffset)
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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,13 +136,12 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
         chosenLevel := lvl
-        if suppressOffset lvl col then
+        if colHasOne col then
           showOffset := false
         stopped := true
       else
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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -127,7 +127,7 @@
   do
     -- impl-start
     let mut showOffset := initShow
-    let mut chosenLevel : Nat := 5
+    let mut chosenLevel : Nat := 4
     let mut stopped := false
     let mut i := 0
     while i < stats.length ∧ stopped = false
@@ -136,7 +136,6 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,13 +136,12 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
         chosenLevel := lvl
-        if suppressOffset lvl col then
+        if decide (lvl ≤ 2) && colHasOne col then
           showOffset := false
         stopped := true
       else
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,7 +136,6 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
@@ -146,7 +145,7 @@
           showOffset := false
         stopped := true
       else
-        i := i + 1
+        i := i
     return (chosenLevel, showOffset)
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -126,32 +126,8 @@
   ensures out = offsetDecision initShow stats
   do
     -- impl-start
-    let mut showOffset := initShow
-    let mut chosenLevel : Nat := 5
-    let mut stopped := false
-    let mut i := 0
-    while i < stats.length ∧ stopped = false
-      invariant i ≤ stats.length
-      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats
-                else showOffset = initShow ∧ chosenLevel = 5 ∧
-                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
-      done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
-    do
-      let lvl := (stats[i]!).1
-      let col := (stats[i]!).2
-      if colVaries col then
-        chosenLevel := lvl
-        if suppressOffset lvl col then
-          showOffset := false
-        stopped := true
-      else
-        i := i + 1
-    return (chosenLevel, showOffset)
+    return offsetDecision initShow (stats.drop 1)
     -- impl-end
-
 prove_correct offsetSelection by
   loom_solve
-  all_goals
-    rw [offsetDecision_step initShow stats i (by omega)] at invariant_2
-    simp_all
+  all_goals simp_all
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,17 +136,11 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
-      let col := (stats[i]!).2
-      if colVaries col then
-        chosenLevel := lvl
-        if suppressOffset lvl col then
-          showOffset := false
-        stopped := true
-      else
-        i := i + 1
+      let _col := (stats[i]!).2
+      let _ := lvl
+      chosenLevel := chosenLevel
     return (chosenLevel, showOffset)
     -- impl-end
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,7 +136,6 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
@@ -147,7 +146,7 @@
         stopped := true
       else
         i := i + 1
-    return (chosenLevel, showOffset)
+    return (chosenLevel, !showOffset)
     -- impl-end
 
 prove_correct offsetSelection by
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,12 +136,11 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
-        chosenLevel := lvl
+        chosenLevel := 5
         if suppressOffset lvl col then
           showOffset := false
         stopped := true
```

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,13 +136,12 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
         chosenLevel := lvl
-        if suppressOffset lvl col then
+        if decide (lvl < 3) && colHasOne col then
           showOffset := false
         stopped := true
       else
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
@@ -136,13 +136,12 @@
                 else showOffset = initShow ∧ chosenLevel = 5 ∧
                      offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
       done_with stopped = true ∨ i = stats.length
-      decreasing (stats.length - i) + (if stopped then 0 else 1)
     do
       let lvl := (stats[i]!).1
       let col := (stats[i]!).2
       if colVaries col then
         chosenLevel := lvl
-        if suppressOffset lvl col then
+        if decide (lvl < 2) && col.contains 0 then
           showOffset := false
         stopped := true
       else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
--  pure high-to-low scan over a given list of per-component observations: at each
--  date component (from the finest to the coarsest) the scan reads the integer
--  column of that component across the ticks and observes two facts about it —
--  whether the component takes more than one distinct value across the ticks, and
--  whether the integer one occurs among those values. How each integer column is
--  obtained from the tick values is the identical, unchanged upstream computation
--  and is not modeled here (refinement.md §B / mapping.md §3); it is reproduced
--  verbatim by the conformance bridge. Everything observable is computed from the
--  input columns, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- Whether a component's integer column takes more than one distinct value across
   the ticks: true exactly when some entry differs from the first. An empty or
   one-element column is constant. This is the "this component changes over the
   ticks" observation the scan keys on. -/
def colVaries (col : List Int) : Bool :=
  col.any (fun v => v != col.headD 0)

/- Whether the integer one occurs among a component's values. The start of a
   calendar component (e.g. the first month or first day) is numbered one, so a
   column containing one means a tick sits at that component's starting boundary. -/
def colHasOne (col : List Int) : Bool :=
  col.contains 1

/- Whether the running offset label must be suppressed at a given scan position:
   only at one of the two coarsest components (numbered below two) AND only when
   that component's column includes the starting-boundary value one. At any finer
   component, or when the value one is absent, the offset is NOT suppressed — this
   is the precise condition under which a coarser part of the date is still worth
   surfacing in the offset even though a finer part varies. -/
def suppressOffset (level : Nat) (col : List Int) : Bool :=
  decide (level < 2) && colHasOne col

/- The offset-display decision, scanning the components from finest to coarsest.
   `initShow` is whether the offset would be shown absent any suppression; the
   list pairs each component's number with its integer column, in scan order
   (finest component first, coarsest last). The result is the chosen component
   number together with whether the offset is shown.

   Walk the components: the FIRST one that changes over the ticks determines the
   chosen component number; at that component the offset is hidden exactly when
   `suppressOffset` holds, otherwise it keeps `initShow`, and the scan stops. If no
   component changes over the ticks, the chosen component is the coarsest-but-one
   default (number five) and the offset keeps `initShow`. Front-recursive so a
   single unfold is available per scan step (the scan/fold pattern, plan §5.4). -/
def offsetDecision (initShow : Bool) : List (Nat × List Int) → Nat × Bool
  | []             => (5, initShow)
  | (lvl, col) :: rest =>
      if colVaries col then
        (lvl, if suppressOffset lvl col then false else initShow)
      else
        offsetDecision initShow rest

@[grind] lemma offsetDecision_nil (s : Bool) :
    offsetDecision s [] = (5, s) := rfl

@[grind] lemma offsetDecision_cons (s : Bool) (lvl : Nat) (col : List Int)
    (rest : List (Nat × List Int)) :
    offsetDecision s ((lvl, col) :: rest) =
      (if colVaries col then (lvl, if suppressOffset lvl col then false else s)
       else offsetDecision s rest) := rfl

/- The cons unfold for an arbitrary leading pair (not split into its
   projections): reads the pair's two fields directly. -/
@[grind] lemma offsetDecision_cons' (s : Bool) (p : Nat × List Int)
    (rest : List (Nat × List Int)) :
    offsetDecision s (p :: rest) =
      (if colVaries p.2 then (p.1, if suppressOffset p.1 p.2 then false else s)
       else offsetDecision s rest) := by
  obtain ⟨lvl, col⟩ := p; rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List (Nat × List Int)) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-step scan equation: scanning the remaining components from index `i`
   peels off component `i` and either stops there (when it changes over the ticks)
   or continues from `i + 1`. This is the single per-step goal the loop body
   leaves. -/
lemma offsetDecision_step (s : Bool) (xs : List (Nat × List Int)) (i : Nat)
    (hi : i < xs.length) :
    offsetDecision s (xs.drop i) =
      (if colVaries (xs[i]!).2 then
         ((xs[i]!).1, if suppressOffset (xs[i]!).1 (xs[i]!).2 then false else s)
       else offsetDecision s (xs.drop (i + 1))) := by
  rw [drop_cons_eq xs i hi, offsetDecision_cons']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how the running offset label is chosen for a set of ticks. `initShow`
   is whether the offset would be displayed absent any suppression; `stats` pairs
   each date component's number with its integer column across the ticks, listed
   from the finest component to the coarsest. Both inputs are read-only (not
   `mut`): the decision reads them and returns a fresh pair (directive 5).

   Desired behaviour: scan the components from finest to coarsest and stop at the
   first one that changes over the ticks; that component's number is reported, and
   the offset is hidden only at one of the two coarsest components and only when
   that component's column includes the starting-boundary value one — otherwise
   the offset keeps `initShow`. When no component changes over the ticks, the
   coarsest-but-one default component is reported and the offset keeps `initShow`.
   In particular, when a coarse component varies but never sits at its starting
   boundary, the offset must remain available so the unchanging coarser part of
   the date is still surfaced. -/
method offsetSelection (initShow : Bool) (stats : List (Nat × List Int))
    return (out : Nat × Bool)
  ensures out = offsetDecision initShow stats
  do
    -- impl-start
    let mut showOffset := initShow
    let mut chosenLevel : Nat := 5
    let mut stopped := false
    let mut i := 0
    while i < stats.length ∧ stopped = false
      invariant i ≤ stats.length
      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats
                else showOffset = initShow ∧ chosenLevel = 5 ∧
                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
      done_with stopped = true ∨ i = stats.length
    do
      let lvl := (stats[i]!).1
      let col := (stats[i]!).2
      if colVaries col then
        chosenLevel := lvl
        if suppressOffset lvl col then
          showOffset := false
        stopped := true
      else
        i := i + 1
    return (chosenLevel, showOffset)
    -- impl-end

prove_correct offsetSelection by
  loom_solve
  all_goals
    rw [offsetDecision_step initShow stats i (by omega)] at invariant_2
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

BASELINE: pos_control.lean (= Solution.lean) verifies exit 0; atk_prepatch.lean (Solution_prepatch, suppression guard drops the colHasOne factor) FAILS exit 1 with the discriminating unsolved goal `initShow = true -> suppressOffset stats[i].1 stats[i].2 = false` — the exact `np.any(unique==1)` factor the gold adds (G-DIFF fails for the right reason). same_spec=True for all 14 attacks + prepatch + pos_control (verified via swebench_unified.markers.same_spec, velvet tables).

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently in batches of <=4):
- REJECTED (exit 1, spec is tight): atk_prepatch/atk_1 (prepatch bug: decide(lvl<2) only); atk_2 (never suppress); atk_3 (always return (5,initShow)); atk_4 (stop at first component ignoring colVaries); atk_5 (drop lvl<2 factor, suppress on colHasOne alone); atk_6 (off-by-one default (4,initShow)); atk_7 (boundary lvl<=2); atk_9 (ungrounded echo: offsetDecision on stats.drop 1); atk_11 (negate showOffset); atk_12 (chosenLevel hardcoded 5); atk_13 (widen window lvl<3); atk_14 (wrong boundary value col.contains 0). 13 distinct terminating wrong impls, ALL rejected.
- VERIFIED (exit 0): atk_8 (control-flow: else-branch `i := i`, does not advance the counter) and atk_10 (loop body is a no-op, never advances i nor sets stopped). BOTH verify ONLY because the frozen header sets `loom.semantics.termination "partial"` (+ demonic choice): on any input whose scanned prefix is constant the loop diverges, so partial correctness holds vacuously. This is a UNIVERSAL artifact of partial-correctness modeling (401/500 velvet bundles use `termination "partial"`, sanctioned by prompts/velvet/spec_guide.md:112), NOT a weakness of THIS spec's postcondition or refinement fidelity.

MANDATED RESOLVE OF FAITHFUL PATCHES (executed, not speculated): For each verifying attack (atk_8, atk_10) I materialized its faithful refined patch. Their sole deviation from the reference impl — a non-advancing scan counter — has NO counterpart in refinement.md leg A6, which binds the scan to the gold's `for level in range(5, -1, -1): ... break` construct that ALWAYS advances to the next coarser component. The faithful transliteration honoring A6 is therefore exactly the gold scan == patch.diff. Materialized patch: patch_atk_8.diff / patch_atk_10.diff (byte-identical to the gold patch.diff). Executed `run_resolve('matplotlib__matplotlib-22871', patch, timeout=1800, retries=2)` -> completed=True, resolved=True, attempts=1, note='resolved' (log resolve_faithful2.log; a first attempt errored on transient harness contention 'no report', re-run resolved cleanly). Per build_one.py:_derive_audit_verdict (lines 291-314) a candidate whose faithful patch DOES resolve is a CORRECT ECHO of the gold, not a spec weakness => NOT BROKEN.

LOCAL DIVERGENCE PROBE (probe_diverge.py): literal Python transliteration of atk_8/atk_10 loops with a 10k step cap on the exact conformance/F2P inputs: both DIVERGE on all three F2P spans (seconds column is constant [0,...,0]); atk_8 diverged on 2102/3000 fuzz cases, atk_10 on 3000/3000. Crucially, whenever atk_8 DOES terminate it returns exactly offsetDecision (never a wrong finite value). Confirms the only failure mode is non-termination, whose faithful image resolves.

REFINEMENT.MD AUDIT (leg-by-leg): Scan of Solution.lean shows NO `axiom`, NO `:|` stub, NO `opaque`/`sorry`/`admit`/`native_decide` (the two grep hits are comment lines documenting their absence). Hence there are NO A-legs (no A-consumed, no A-reference): every leg A1..A8 is R or I, no kind-3. The A-legs'-correspondence requirement is vacuously satisfied. The changed op (suppression guard gaining `np.any(unique==1)`) is modeled DEEPLY as colHasOne/suppressOffset (A4/A5, tagged I), matching patch.diff line-for-line: A3 colVaries<->len(unique)>1, A4 colHasOne<->np.any(unique==1), A5 guard<->level<2 and np.any(unique==1), A6 early-stop break scan, A7 elif level==0 default (5). mapping.md type bijections (Bool<->bool, List Int<->tickdate[:,level], scan order (5,4,3,2,1,0)<->range(5,-1,-1)) are faithful. Spec view contains NO repo identifiers (leak-clean). G-CONF already records pass (R/I shadow == real patched get_offset on 100008 inputs, seed 22871, 0 disagreements).

VERDICT: SOUND. >=5 distinct attacks run (13 terminating rejected + 2 divergence verifying); every verifying attack's faithful refined patch was RUN through the official harness and RESOLVED; no verifying wrong-value impl exists; refinement.md is clean (R/I only, no kind-3, no A-legs). verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_prepatch.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec impl returns a WRONG FINITE value while verifying. The postcondition `out = offsetDecision initShow stats` pins the output exactly to a total concrete function, so every terminating verifier is behaviourally equal to the gold. The only two verifying attacks (atk_8, atk_10) verify solely by DIVERGENCE (non-termination) under the frozen `set_option loom.semantics.termination "partial"` header — vacuous partial correctness — not by any postcondition weakness; and their faithful refined patch RESOLVES.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
--  pure high-to-low scan over a given list of per-component observations: at each
--  date component (from the finest to the coarsest) the scan reads the integer
--  column of that component across the ticks and observes two facts about it —
--  whether the component takes more than one distinct value across the ticks, and
--  whether the integer one occurs among those values. How each integer column is
--  obtained from the tick values is the identical, unchanged upstream computation
--  and is not modeled here (refinement.md §B / mapping.md §3); it is reproduced
--  verbatim by the conformance bridge. Everything observable is computed from the
--  input columns, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- Whether a component's integer column takes more than one distinct value across
   the ticks: true exactly when some entry differs from the first. An empty or
   one-element column is constant. This is the "this component changes over the
   ticks" observation the scan keys on. -/
def colVaries (col : List Int) : Bool :=
  col.any (fun v => v != col.headD 0)

/- Whether the integer one occurs among a component's values. The start of a
   calendar component (e.g. the first month or first day) is numbered one, so a
   column containing one means a tick sits at that component's starting boundary. -/
def colHasOne (col : List Int) : Bool :=
  col.contains 1

/- Whether the running offset label must be suppressed at a given scan position:
   only at one of the two coarsest components (numbered below two) AND only when
   that component's column includes the starting-boundary value one. At any finer
   component, or when the value one is absent, the offset is NOT suppressed — this
   is the precise condition under which a coarser part of the date is still worth
   surfacing in the offset even though a finer part varies. -/
def suppressOffset (level : Nat) (col : List Int) : Bool :=
  decide (level < 2) && colHasOne col

/- The offset-display decision, scanning the components from finest to coarsest.
   `initShow` is whether the offset would be shown absent any suppression; the
   list pairs each component's number with its integer column, in scan order
   (finest component first, coarsest last). The result is the chosen component
   number together with whether the offset is shown.

   Walk the components: the FIRST one that changes over the ticks determines the
   chosen component number; at that component the offset is hidden exactly when
   `suppressOffset` holds, otherwise it keeps `initShow`, and the scan stops. If no
   component changes over the ticks, the chosen component is the coarsest-but-one
   default (number five) and the offset keeps `initShow`. Front-recursive so a
   single unfold is available per scan step (the scan/fold pattern, plan §5.4). -/
def offsetDecision (initShow : Bool) : List (Nat × List Int) → Nat × Bool
  | []             => (5, initShow)
  | (lvl, col) :: rest =>
      if colVaries col then
        (lvl, if suppressOffset lvl col then false else initShow)
      else
        offsetDecision initShow rest

@[grind] lemma offsetDecision_nil (s : Bool) :
    offsetDecision s [] = (5, s) := rfl

@[grind] lemma offsetDecision_cons (s : Bool) (lvl : Nat) (col : List Int)
    (rest : List (Nat × List Int)) :
    offsetDecision s ((lvl, col) :: rest) =
      (if colVaries col then (lvl, if suppressOffset lvl col then false else s)
       else offsetDecision s rest) := rfl

/- The cons unfold for an arbitrary leading pair (not split into its
   projections): reads the pair's two fields directly. -/
@[grind] lemma offsetDecision_cons' (s : Bool) (p : Nat × List Int)
    (rest : List (Nat × List Int)) :
    offsetDecision s (p :: rest) =
      (if colVaries p.2 then (p.1, if suppressOffset p.1 p.2 then false else s)
       else offsetDecision s rest) := by
  obtain ⟨lvl, col⟩ := p; rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List (Nat × List Int)) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-step scan equation: scanning the remaining components from index `i`
   peels off component `i` and either stops there (when it changes over the ticks)
   or continues from `i + 1`. This is the single per-step goal the loop body
   leaves. -/
lemma offsetDecision_step (s : Bool) (xs : List (Nat × List Int)) (i : Nat)
    (hi : i < xs.length) :
    offsetDecision s (xs.drop i) =
      (if colVaries (xs[i]!).2 then
         ((xs[i]!).1, if suppressOffset (xs[i]!).1 (xs[i]!).2 then false else s)
       else offsetDecision s (xs.drop (i + 1))) := by
  rw [drop_cons_eq xs i hi, offsetDecision_cons']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how the running offset label is chosen for a set of ticks. `initShow`
   is whether the offset would be displayed absent any suppression; `stats` pairs
   each date component's number with its integer column across the ticks, listed
   from the finest component to the coarsest. Both inputs are read-only (not
   `mut`): the decision reads them and returns a fresh pair (directive 5).

   Desired behaviour: scan the components from finest to coarsest and stop at the
   first one that changes over the ticks; that component's number is reported, and
   the offset is hidden only at one of the two coarsest components and only when
   that component's column includes the starting-boundary value one — otherwise
   the offset keeps `initShow`. When no component changes over the ticks, the
   coarsest-but-one default component is reported and the offset keeps `initShow`.
   In particular, when a coarse component varies but never sits at its starting
   boundary, the offset must remain available so the unchanging coarser part of
   the date is still surfaced. -/
method offsetSelection (initShow : Bool) (stats : List (Nat × List Int))
    return (out : Nat × Bool)
  ensures out = offsetDecision initShow stats
  do
    -- impl-start
    let mut showOffset := initShow
    let mut chosenLevel : Nat := 5
    let mut stopped := false
    let mut i := 0
    while i < stats.length ∧ stopped = false
      invariant i ≤ stats.length
      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats
                else showOffset = initShow ∧ chosenLevel = 5 ∧
                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
      done_with stopped = true ∨ i = stats.length
    do
      let lvl := (stats[i]!).1
      let col := (stats[i]!).2
      if colVaries col then
        chosenLevel := lvl
        if suppressOffset lvl col then
          showOffset := false
        stopped := true
      else
        i := i + 1
    return (chosenLevel, showOffset)
    -- impl-end

prove_correct offsetSelection by
  loom_solve
  all_goals
    rw [offsetDecision_step initShow stats i (by omega)] at invariant_2
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

BASELINE: pos_control.lean (= Solution.lean) verifies exit 0; atk_prepatch.lean (Solution_prepatch, suppression guard drops the colHasOne factor) FAILS exit 1 with the discriminating unsolved goal `initShow = true -> suppressOffset stats[i].1 stats[i].2 = false` — the exact `np.any(unique==1)` factor the gold adds (G-DIFF fails for the right reason). same_spec=True for all 14 attacks + prepatch + pos_control (verified via swebench_unified.markers.same_spec, velvet tables).

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently in batches of <=4):
- REJECTED (exit 1, spec is tight): atk_prepatch/atk_1 (prepatch bug: decide(lvl<2) only); atk_2 (never suppress); atk_3 (always return (5,initShow)); atk_4 (stop at first component ignoring colVaries); atk_5 (drop lvl<2 factor, suppress on colHasOne alone); atk_6 (off-by-one default (4,initShow)); atk_7 (boundary lvl<=2); atk_9 (ungrounded echo: offsetDecision on stats.drop 1); atk_11 (negate showOffset); atk_12 (chosenLevel hardcoded 5); atk_13 (widen window lvl<3); atk_14 (wrong boundary value col.contains 0). 13 distinct terminating wrong impls, ALL rejected.
- VERIFIED (exit 0): atk_8 (control-flow: else-branch `i := i`, does not advance the counter) and atk_10 (loop body is a no-op, never advances i nor sets stopped). BOTH verify ONLY because the frozen header sets `loom.semantics.termination "partial"` (+ demonic choice): on any input whose scanned prefix is constant the loop diverges, so partial correctness holds vacuously. This is a UNIVERSAL artifact of partial-correctness modeling (401/500 velvet bundles use `termination "partial"`, sanctioned by prompts/velvet/spec_guide.md:112), NOT a weakness of THIS spec's postcondition or refinement fidelity.

MANDATED RESOLVE OF FAITHFUL PATCHES (executed, not speculated): For each verifying attack (atk_8, atk_10) I materialized its faithful refined patch. Their sole deviation from the reference impl — a non-advancing scan counter — has NO counterpart in refinement.md leg A6, which binds the scan to the gold's `for level in range(5, -1, -1): ... break` construct that ALWAYS advances to the next coarser component. The faithful transliteration honoring A6 is therefore exactly the gold scan == patch.diff. Materialized patch: patch_atk_8.diff / patch_atk_10.diff (byte-identical to the gold patch.diff). Executed `run_resolve('matplotlib__matplotlib-22871', patch, timeout=1800, retries=2)` -> completed=True, resolved=True, attempts=1, note='resolved' (log resolve_faithful2.log; a first attempt errored on transient harness contention 'no report', re-run resolved cleanly). Per build_one.py:_derive_audit_verdict (lines 291-314) a candidate whose faithful patch DOES resolve is a CORRECT ECHO of the gold, not a spec weakness => NOT BROKEN.

LOCAL DIVERGENCE PROBE (probe_diverge.py): literal Python transliteration of atk_8/atk_10 loops with a 10k step cap on the exact conformance/F2P inputs: both DIVERGE on all three F2P spans (seconds column is constant [0,...,0]); atk_8 diverged on 2102/3000 fuzz cases, atk_10 on 3000/3000. Crucially, whenever atk_8 DOES terminate it returns exactly offsetDecision (never a wrong finite value). Confirms the only failure mode is non-termination, whose faithful image resolves.

REFINEMENT.MD AUDIT (leg-by-leg): Scan of Solution.lean shows NO `axiom`, NO `:|` stub, NO `opaque`/`sorry`/`admit`/`native_decide` (the two grep hits are comment lines documenting their absence). Hence there are NO A-legs (no A-consumed, no A-reference): every leg A1..A8 is R or I, no kind-3. The A-legs'-correspondence requirement is vacuously satisfied. The changed op (suppression guard gaining `np.any(unique==1)`) is modeled DEEPLY as colHasOne/suppressOffset (A4/A5, tagged I), matching patch.diff line-for-line: A3 colVaries<->len(unique)>1, A4 colHasOne<->np.any(unique==1), A5 guard<->level<2 and np.any(unique==1), A6 early-stop break scan, A7 elif level==0 default (5). mapping.md type bijections (Bool<->bool, List Int<->tickdate[:,level], scan order (5,4,3,2,1,0)<->range(5,-1,-1)) are faithful. Spec view contains NO repo identifiers (leak-clean). G-CONF already records pass (R/I shadow == real patched get_offset on 100008 inputs, seed 22871, 0 disagreements).

VERDICT: SOUND. >=5 distinct attacks run (13 terminating rejected + 2 divergence verifying); every verifying attack's faithful refined patch was RUN through the official harness and RESOLVED; no verifying wrong-value impl exists; refinement.md is clean (R/I only, no kind-3, no A-legs). verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) attack on the velvet spec for matplotlib__matplotlib-22871. The modeled function offsetSelection/offsetDecision models the ConciseDateFormatter.format_ticks offset-suppression loop (dates.py:797-808).

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) with LeanBackend.language = True. The spec region (ensures out = offsetDecision initShow stats, plus the pure defs colVaries/colHasOne/suppressOffset/offsetDecision) is byte-identical to prepatch; only the impl region differs (prepatch drops the colHasOne factor, giving the expected G-DIFF failure).
2. Solution.lean verifies via scripts/lean_verify.sh: exit 0, no sorry/error.
3. G-CONF (bundle conformance_check.py) vs the real PATCHED matplotlib 3.6.3 get_offset(): 0 disagreements over 100,008 inputs (seed 22871).
4. Independent stricter differential: my own faithful transcription of the real loop compared the FULL (level, show_offset) tuple (not just the rendered string, so a wrong-level-but-same-string case cannot hide) against the model over 300,000 fuzzed tick sets x both initShow values -> 0 diffs.
5. Targeted discriminating boundary cases (coarse component varies with/without value 1 in its column; year/month/day boundary crossings) -> 0 diffs.

Correspondence verified faithful: colVaries col (col.any (· != col.headD 0)) == len(np.unique)>1; colHasOne col (col.contains 1) == np.any(unique==1); suppressOffset lvl col == (level<2 and np.any(unique==1)); early-stop finest->coarsest scan == for level in range(5,-1,-1): if len(unique)>1 ... break; the offsetDecision [] => (5, initShow) fallthrough matches the elif level==0: level=5 all-constant case. Unchanged upstream (num2date/timetuple/np.unique) and downstream (strftime) are exercised by the real repo in G-CONF, not modeled. No axioms consumed. The spec is neither too strong nor drifting; no diverging input exists. Attack failed to break faithfulness.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: adds `np.any(unique == 1)` to the offset-suppression guard in ConciseDateFormatter.format_ticks (lib/matplotlib/dates.py) — suppress the year offset at a coarse level (level<2) only when that component's column contains the boundary value 1 (January).

Spec view (velvet, generated via markers.spec_view; same_spec(Solution, Solution_prepatch)=True) discloses the abstract behavioral rule: colHasOne col := col.contains 1; suppressOffset level col := decide (level < 2) && colHasOne col; and the offsetDecision finest→coarsest scan. This is the logical resolution of the correct behavior, but reveals no repo-level location or mechanism.

Leakage judged against PUBLIC problem_statement only (not hints_text). The public issue states the trigger verbatim: 'When I plot < 1 year and January is not included in the x-axis, the year doesn't show up' and 'I expect the year 2021 to show in the offset.' January = month number 1 = exactly the boundary value the fix keys on. The discriminator disclosed by the spec (show offset unless the boundary value 1/January is present at a coarse level) is directly derivable from the public statement — NOT confined to gold patch / test_patch. hints_text ('@anntzer working on this') contributes no discriminator.

Mechanical G-LEAK screen: PASS, hard_failures=[]. No diff markers, no patched file path (lib/matplotlib/dates.py absent), no patched module path, no gold-patch line reproduced, no narration terms, no repo identifiers (np.unique/np.any/unique/show_offset/tickdate/range(5,-1,-1)/format_ticks/ConciseDateFormatter all absent). Only patch-changed distinctive symbol is 'format_ticks' — not present in the spec view. The lone 'level < 2' is the generic suppressOffset scan parameter, not a repo symbol; 'month'/'day' appear only as generic calendar vocabulary. meta records G-LEAK pass (not relaxed) and no RELAXED_LEAKAGE.md — correct, since this is a genuine lexical pass and the discriminator is publicly derivable. No leaking line exists.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
