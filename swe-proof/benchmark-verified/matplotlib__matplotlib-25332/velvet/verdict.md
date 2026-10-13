# P2 adversarial audit — matplotlib__matplotlib-25332

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The frozen spec pins both outputs by exact equality (out = strongifyMap mapping ; out = weakenMap state), so verify ⇒ output-exactly-correct. The single verifying attack (atk_9, echo `return strongifyMap mapping`) is behaviorally the gold __getstate__; its faithful refined patch RESOLVED=True (not flaky) under the official harness.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -99,10 +99,9 @@
       invariant 0 ≤ i ∧ i ≤ mapping.length
       invariant result = strongifyMap (mapping.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
+      result := e :: result
       i := i - 1
     return result
     -- impl-end
@@ -148,7 +147,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -99,7 +99,6 @@
       invariant 0 ≤ i ∧ i ≤ mapping.length
       invariant result = strongifyMap (mapping.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := mapping[i - 1]!
       result := strongifyEntry e :: result
@@ -148,10 +147,9 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
-      result := weakenEntry e :: result
+      result := e :: result
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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -99,10 +99,9 @@
       invariant 0 ≤ i ∧ i ≤ mapping.length
       invariant result = strongifyMap (mapping.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
+      result := weakenEntry e :: result
       i := i - 1
     return result
     -- impl-end
@@ -148,7 +147,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -99,10 +99,9 @@
       invariant 0 ≤ i ∧ i ≤ mapping.length
       invariant result = strongifyMap (mapping.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
+      result := (strongify e.1, e.2) :: result
       i := i - 1
     return result
     -- impl-end
@@ -148,7 +147,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -99,10 +99,12 @@
       invariant 0 ≤ i ∧ i ≤ mapping.length
       invariant result = strongifyMap (mapping.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
+      if i = 1 then
+        result := e :: result
+      else
+        result := strongifyEntry e :: result
       i := i - 1
     return result
     -- impl-end
@@ -148,7 +150,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -99,10 +99,9 @@
       invariant 0 ≤ i ∧ i ≤ mapping.length
       invariant result = strongifyMap (mapping.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
+      result := ({ target := e.1.target + 1, weak := false }, e.2.map strongify) :: result
       i := i - 1
     return result
     -- impl-end
@@ -148,7 +147,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -93,17 +93,7 @@
   ensures out = strongifyMap mapping
   do
     -- impl-start
-    let mut result : List (Ref × List Ref) := []
-    let mut i := mapping.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ mapping.length
-      invariant result = strongifyMap (mapping.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
-      i := i - 1
+    let result : List (Ref × List Ref) := []
     return result
     -- impl-end
 
@@ -148,7 +138,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -93,18 +93,7 @@
   ensures out = strongifyMap mapping
   do
     -- impl-start
-    let mut result : List (Ref × List Ref) := []
-    let mut i := mapping.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ mapping.length
-      invariant result = strongifyMap (mapping.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
-      i := i - 1
-    return result
+    return ([] : List (Ref × List Ref))
     -- impl-end
 
 /- The backward-fold step for the snapshot: dropping one fewer row exposes the
@@ -122,9 +111,7 @@
   rw [hcons, strongifyMap_cons]
 
 prove_correct snapshot by
-  loom_solve
-  rw [strongifyMap_drop_step mapping i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all
 
 /- The live grouping registry table rebuilt from a serialisable snapshot.
 
@@ -148,7 +135,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms and no deep-model reference. Two independent behaviours are
@@ -93,18 +93,7 @@
   ensures out = strongifyMap mapping
   do
     -- impl-start
-    let mut result : List (Ref × List Ref) := []
-    let mut i := mapping.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ mapping.length
-      invariant result = strongifyMap (mapping.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := mapping[i - 1]!
-      result := strongifyEntry e :: result
-      i := i - 1
-    return result
+    return strongifyMap mapping
     -- impl-end
 
 /- The backward-fold step for the snapshot: dropping one fewer row exposes the
@@ -123,8 +112,6 @@
 
 prove_correct snapshot by
   loom_solve
-  rw [strongifyMap_drop_step mapping i (by omega) (by omega)]
-  simp_all
 
 /- The live grouping registry table rebuilt from a serialisable snapshot.
 
@@ -148,7 +135,6 @@
       invariant 0 ≤ i ∧ i ≤ state.length
       invariant result = weakenMap (state.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := state[i - 1]!
       result := weakenEntry e :: result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model reference. Two independent behaviours are
-- modeled here, each a pure transform over a grouping registry's own observable
-- content: (1) the serialisable snapshot taken of the registry's reference table
-- before it is written out, and (2) the live table rebuilt from such a snapshot
-- when it is read back. Both are total functions of the registry's reference
-- table; there is no foreign callee whose contract the proof assumes and none
-- that is deep-modeled. See refinement.md §C / mapping.md §3 (no `axiom`, no
-- A-reference).
-- axioms-end

-- pure-start
/- A single reference held in the grouping registry's table. `target` is the
   identity of the object referred to; `weak` records whether this reference is
   a live (non-serialisable) weak reference or a plain (serialisable) strong one.
   The registry's live table holds only weak references; a snapshot of it holds
   only strong ones. -/
structure Ref where
  target : Int
  weak : Bool
deriving DecidableEq, Inhabited, Repr

/- Turn one reference into its strong (serialisable) form, keeping the object it
   refers to. This is the per-reference content of taking a snapshot. -/
def strongify (r : Ref) : Ref := { r with weak := false }

/- Turn one reference back into a live weak reference to the same object. This is
   the per-reference content of rebuilding the live table from a snapshot. -/
def weaken (r : Ref) : Ref := { r with weak := true }

/- One table row is a representative reference paired with the list of references
   grouped under it. Strongifying / weakening a row applies the per-reference
   transform to the representative and to every member of its group. -/
def strongifyEntry (e : Ref × List Ref) : Ref × List Ref :=
  (strongify e.1, e.2.map strongify)

def weakenEntry (e : Ref × List Ref) : Ref × List Ref :=
  (weaken e.1, e.2.map weaken)

/- The snapshot of a whole reference table: strongify every row. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def strongifyMap : List (Ref × List Ref) → List (Ref × List Ref)
  | []      => []
  | e :: es => strongifyEntry e :: strongifyMap es

/- The live table rebuilt from a snapshot: weaken every row. Same front-recursive
   shape. -/
def weakenMap : List (Ref × List Ref) → List (Ref × List Ref)
  | []      => []
  | e :: es => weakenEntry e :: weakenMap es

@[grind] lemma strongifyMap_nil : strongifyMap [] = [] := rfl
@[grind] lemma strongifyMap_cons (e : Ref × List Ref) (es : List (Ref × List Ref)) :
    strongifyMap (e :: es) = strongifyEntry e :: strongifyMap es := rfl
@[grind] lemma weakenMap_nil : weakenMap [] = [] := rfl
@[grind] lemma weakenMap_cons (e : Ref × List Ref) (es : List (Ref × List Ref)) :
    weakenMap (e :: es) = weakenEntry e :: weakenMap es := rfl

/- Round-trip fact at the level of a single reference: weakening a strongified
   reference restores exactly a weak reference to the same object — the snapshot
   and the rebuild compose to the identity on what a live table observes. Marked
   `@[grind]` so `loom_solve` discharges the round-trip postcondition. -/
@[grind] lemma weaken_strongify (r : Ref) : weaken (strongify r) = weaken r := by
  simp [weaken, strongify]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the inputs are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the methods below)
-- post-conditions-end

/- The serialisable snapshot of the grouping registry's reference table.

   Desired behaviour: the live table holds weak references, which a value
   serialiser (pickle) cannot write out. The snapshot taken just before writing
   must therefore replace every reference — both each row's representative and
   every member of its group — with a strong reference to the same object, so the
   result carries no live weak reference yet records the exact same grouping. The
   reference table `mapping` is a read-only input (not `mut`); it is never altered
   in place (directive 5) — the result is the snapshot. -/
method snapshot (mapping : List (Ref × List Ref)) return (out : List (Ref × List Ref))
  ensures out = strongifyMap mapping
  do
    -- impl-start
    let mut result : List (Ref × List Ref) := []
    let mut i := mapping.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ mapping.length
      invariant result = strongifyMap (mapping.drop i)
      done_with i = 0
    do
      let e := mapping[i - 1]!
      result := strongifyEntry e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the snapshot: dropping one fewer row exposes the
   row at `i-1` on the front, so `strongifyMap` peels one `strongifyEntry`. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma strongifyMap_drop_step (xs : List (Ref × List Ref)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    strongifyMap (xs.drop (i - 1)) = strongifyEntry xs[i - 1]! :: strongifyMap (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, strongifyMap_cons]

prove_correct snapshot by
  loom_solve
  rw [strongifyMap_drop_step mapping i (by omega) (by omega)]
  simp_all

/- The live grouping registry table rebuilt from a serialisable snapshot.

   Desired behaviour: when the registry is read back, every strong reference in
   the snapshot — each row's representative and every member of its group — must
   be turned back into a live weak reference to the same object, reconstructing
   the original grouping with live references. `state` is a read-only input (not
   `mut`); it is never altered in place (directive 5) — the result is the rebuilt
   live table. The round-trip postcondition records that weakening a snapshotted
   reference yields exactly a live reference to the same object (the snapshot is
   loss-free): rebuilding after snapshotting preserves what the live table
   observes. -/
method rebuild (state : List (Ref × List Ref)) return (out : List (Ref × List Ref))
  ensures out = weakenMap state
  ensures ∀ r : Ref, weaken (strongify r) = weaken r
  do
    -- impl-start
    let mut result : List (Ref × List Ref) := []
    let mut i := state.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ state.length
      invariant result = weakenMap (state.drop i)
      done_with i = 0
    do
      let e := state[i - 1]!
      result := weakenEntry e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the rebuild: same shape as the snapshot's. -/
lemma weakenMap_drop_step (xs : List (Ref × List Ref)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    weakenMap (xs.drop (i - 1)) = weakenEntry xs[i - 1]! :: weakenMap (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, weakenMap_cons]

prove_correct rebuild by
  loom_solve
  rw [weakenMap_drop_step state i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol completed

Spec structure: postconditions are exact equalities (out = strongifyMap mapping for snapshot; out = weakenMap state + tautological round-trip for rebuild), fully determining the output. NO axioms and NO A-references (refinement.md §C / mapping.md §3): the only 'axiom' string in Solution.lean is inside a comment; no `axiom` decl, no sorry/admit. The two changed methods (__getstate__/__setstate__, both ADDED by the patch) use only builtins + weakref.ref()/obj() primitives, which ARE the modeled per-reference weak<->strong flip (strongify/weaken), not unchanged foreign callees. A-leg / model-correspondence audit: HONEST, no kind-3 legs.

SAME_SPEC: all 10 attacks + positive control same_spec==True (swebench_unified.markers.same_spec, velvet backend).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean EXIT=0 (positive control verifies)
- atk_1 (snapshot identity = PREPATCH bug, weak not strongified) EXIT=1 — unsolved goal at invariant `result = strongifyMap (mapping.drop i)`
- atk_2 (rebuild identity = PREPATCH_2 bug) EXIT=1
- atk_3 (snapshot weakens instead of strongifies — control-flow/effect swap) EXIT=1
- atk_4 (partial-domain: strongify only row key, leave group members) EXIT=1
- atk_5 (boundary: skip first row, i=1 left identity) EXIT=1
- atk_7 (ungrounded/target-corrupting: target := target+1) EXIT=1
- atk_8 (empty return [], loop removed) EXIT=1 (proof-scaffold + goal fail)
- atk_10 (empty return [] with matching proof attempt) EXIT=1 — log shows unclosable postcond goal `strongifyMap mapping = []` (clean behavioral rejection)
- atk_9 (echo `return strongifyMap mapping` with matching `prove_correct snapshot by loom_solve`) EXIT=0 VERIFIES — but behaviorally CORRECT (= gold __getstate__ comprehension).

RESOLVE (protocol step 2 — every verifying impl's faithful patch run through official harness): atk_9 is the ONLY verifying attack. Its faithful refined patch (snapshot output = strongifyMap mapping = gold __getstate__; rebuild unchanged/correct) = gold patch behavior. run_resolve('matplotlib__matplotlib-25332', <atk_9 patch>) => RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. So the verifying impl's patch DOES resolve — no verify⇏correct break. Under resolved G-PANEL-1/eq policy a resolving echo is NOT a weakness.

CONCLUSION: No same-spec wrong impl verifies against the exact-equality spec; the one verifying impl resolves. verify ⇒ correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. The frozen spec pins both outputs by exact equality (out = strongifyMap mapping ; out = weakenMap state), so verify ⇒ output-exactly-correct. The single verifying attack (atk_9, echo `return strongifyMap mapping`) is behaviorally the gold __getstate__; its faithful refined patch RESOLVED=True (not flaky) under the official harness.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model reference. Two independent behaviours are
-- modeled here, each a pure transform over a grouping registry's own observable
-- content: (1) the serialisable snapshot taken of the registry's reference table
-- before it is written out, and (2) the live table rebuilt from such a snapshot
-- when it is read back. Both are total functions of the registry's reference
-- table; there is no foreign callee whose contract the proof assumes and none
-- that is deep-modeled. See refinement.md §C / mapping.md §3 (no `axiom`, no
-- A-reference).
-- axioms-end

-- pure-start
/- A single reference held in the grouping registry's table. `target` is the
   identity of the object referred to; `weak` records whether this reference is
   a live (non-serialisable) weak reference or a plain (serialisable) strong one.
   The registry's live table holds only weak references; a snapshot of it holds
   only strong ones. -/
structure Ref where
  target : Int
  weak : Bool
deriving DecidableEq, Inhabited, Repr

/- Turn one reference into its strong (serialisable) form, keeping the object it
   refers to. This is the per-reference content of taking a snapshot. -/
def strongify (r : Ref) : Ref := { r with weak := false }

/- Turn one reference back into a live weak reference to the same object. This is
   the per-reference content of rebuilding the live table from a snapshot. -/
def weaken (r : Ref) : Ref := { r with weak := true }

/- One table row is a representative reference paired with the list of references
   grouped under it. Strongifying / weakening a row applies the per-reference
   transform to the representative and to every member of its group. -/
def strongifyEntry (e : Ref × List Ref) : Ref × List Ref :=
  (strongify e.1, e.2.map strongify)

def weakenEntry (e : Ref × List Ref) : Ref × List Ref :=
  (weaken e.1, e.2.map weaken)

/- The snapshot of a whole reference table: strongify every row. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def strongifyMap : List (Ref × List Ref) → List (Ref × List Ref)
  | []      => []
  | e :: es => strongifyEntry e :: strongifyMap es

/- The live table rebuilt from a snapshot: weaken every row. Same front-recursive
   shape. -/
def weakenMap : List (Ref × List Ref) → List (Ref × List Ref)
  | []      => []
  | e :: es => weakenEntry e :: weakenMap es

@[grind] lemma strongifyMap_nil : strongifyMap [] = [] := rfl
@[grind] lemma strongifyMap_cons (e : Ref × List Ref) (es : List (Ref × List Ref)) :
    strongifyMap (e :: es) = strongifyEntry e :: strongifyMap es := rfl
@[grind] lemma weakenMap_nil : weakenMap [] = [] := rfl
@[grind] lemma weakenMap_cons (e : Ref × List Ref) (es : List (Ref × List Ref)) :
    weakenMap (e :: es) = weakenEntry e :: weakenMap es := rfl

/- Round-trip fact at the level of a single reference: weakening a strongified
   reference restores exactly a weak reference to the same object — the snapshot
   and the rebuild compose to the identity on what a live table observes. Marked
   `@[grind]` so `loom_solve` discharges the round-trip postcondition. -/
@[grind] lemma weaken_strongify (r : Ref) : weaken (strongify r) = weaken r := by
  simp [weaken, strongify]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the inputs are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the methods below)
-- post-conditions-end

/- The serialisable snapshot of the grouping registry's reference table.

   Desired behaviour: the live table holds weak references, which a value
   serialiser (pickle) cannot write out. The snapshot taken just before writing
   must therefore replace every reference — both each row's representative and
   every member of its group — with a strong reference to the same object, so the
   result carries no live weak reference yet records the exact same grouping. The
   reference table `mapping` is a read-only input (not `mut`); it is never altered
   in place (directive 5) — the result is the snapshot. -/
method snapshot (mapping : List (Ref × List Ref)) return (out : List (Ref × List Ref))
  ensures out = strongifyMap mapping
  do
    -- impl-start
    let mut result : List (Ref × List Ref) := []
    let mut i := mapping.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ mapping.length
      invariant result = strongifyMap (mapping.drop i)
      done_with i = 0
    do
      let e := mapping[i - 1]!
      result := strongifyEntry e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the snapshot: dropping one fewer row exposes the
   row at `i-1` on the front, so `strongifyMap` peels one `strongifyEntry`. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma strongifyMap_drop_step (xs : List (Ref × List Ref)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    strongifyMap (xs.drop (i - 1)) = strongifyEntry xs[i - 1]! :: strongifyMap (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, strongifyMap_cons]

prove_correct snapshot by
  loom_solve
  rw [strongifyMap_drop_step mapping i (by omega) (by omega)]
  simp_all

/- The live grouping registry table rebuilt from a serialisable snapshot.

   Desired behaviour: when the registry is read back, every strong reference in
   the snapshot — each row's representative and every member of its group — must
   be turned back into a live weak reference to the same object, reconstructing
   the original grouping with live references. `state` is a read-only input (not
   `mut`); it is never altered in place (directive 5) — the result is the rebuilt
   live table. The round-trip postcondition records that weakening a snapshotted
   reference yields exactly a live reference to the same object (the snapshot is
   loss-free): rebuilding after snapshotting preserves what the live table
   observes. -/
method rebuild (state : List (Ref × List Ref)) return (out : List (Ref × List Ref))
  ensures out = weakenMap state
  ensures ∀ r : Ref, weaken (strongify r) = weaken r
  do
    -- impl-start
    let mut result : List (Ref × List Ref) := []
    let mut i := state.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ state.length
      invariant result = weakenMap (state.drop i)
      done_with i = 0
    do
      let e := state[i - 1]!
      result := weakenEntry e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the rebuild: same shape as the snapshot's. -/
lemma weakenMap_drop_step (xs : List (Ref × List Ref)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    weakenMap (xs.drop (i - 1)) = weakenEntry xs[i - 1]! :: weakenMap (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, weakenMap_cons]

prove_correct rebuild by
  loom_solve
  rw [weakenMap_drop_step state i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol completed

Spec structure: postconditions are exact equalities (out = strongifyMap mapping for snapshot; out = weakenMap state + tautological round-trip for rebuild), fully determining the output. NO axioms and NO A-references (refinement.md §C / mapping.md §3): the only 'axiom' string in Solution.lean is inside a comment; no `axiom` decl, no sorry/admit. The two changed methods (__getstate__/__setstate__, both ADDED by the patch) use only builtins + weakref.ref()/obj() primitives, which ARE the modeled per-reference weak<->strong flip (strongify/weaken), not unchanged foreign callees. A-leg / model-correspondence audit: HONEST, no kind-3 legs.

SAME_SPEC: all 10 attacks + positive control same_spec==True (swebench_unified.markers.same_spec, velvet backend).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean EXIT=0 (positive control verifies)
- atk_1 (snapshot identity = PREPATCH bug, weak not strongified) EXIT=1 — unsolved goal at invariant `result = strongifyMap (mapping.drop i)`
- atk_2 (rebuild identity = PREPATCH_2 bug) EXIT=1
- atk_3 (snapshot weakens instead of strongifies — control-flow/effect swap) EXIT=1
- atk_4 (partial-domain: strongify only row key, leave group members) EXIT=1
- atk_5 (boundary: skip first row, i=1 left identity) EXIT=1
- atk_7 (ungrounded/target-corrupting: target := target+1) EXIT=1
- atk_8 (empty return [], loop removed) EXIT=1 (proof-scaffold + goal fail)
- atk_10 (empty return [] with matching proof attempt) EXIT=1 — log shows unclosable postcond goal `strongifyMap mapping = []` (clean behavioral rejection)
- atk_9 (echo `return strongifyMap mapping` with matching `prove_correct snapshot by loom_solve`) EXIT=0 VERIFIES — but behaviorally CORRECT (= gold __getstate__ comprehension).

RESOLVE (protocol step 2 — every verifying impl's faithful patch run through official harness): atk_9 is the ONLY verifying attack. Its faithful refined patch (snapshot output = strongifyMap mapping = gold __getstate__; rebuild unchanged/correct) = gold patch behavior. run_resolve('matplotlib__matplotlib-25332', <atk_9 patch>) => RESOLVED=True, COMPLETED=True, FLAKY=False, note='resolved'. So the verifying impl's patch DOES resolve — no verify⇏correct break. Under resolved G-PANEL-1/eq policy a resolving echo is NOT a weakness.

CONCLUSION: No same-spec wrong impl verifies against the exact-equality spec; the one verifying impl resolves. verify ⇒ correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independent faithfulness audit of velvet Solution.lean for matplotlib__matplotlib-25332. (1) Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True and same_spec(Solution.lean, Solution_prepatch_2.lean)=True under the real velvet backend tables — no drift can hide in a divergent spec region; the prepatch variants differ only in elided impl regions. (2) Spec verifies: scripts/lean_verify.sh exits 0, so `ensures out = strongifyMap mapping` (snapshot) and `ensures out = weakenMap state` (rebuild) are genuinely discharged against the while-loop impls (satisfiable, not vacuously too-strong). (3) Modeled functions vs real gold callees (both ADDED by patch.diff to lib/matplotlib/cbook.py): snapshot ⇔ Grouper.__getstate__ (flip weak:=false, keep target, preserve row order); rebuild ⇔ Grouper.__setstate__ (flip weak:=true). The extra rebuild postcondition ∀ r, weaken(strongify r)=weaken r is a pure simp-provable tautology over the deep models — constrains neither out nor input, so does NOT over-strengthen. (4) Differential: reproduced both gold callees verbatim and ran the R/I shadow (strongify_map/weaken_map over the (id(referent), weak-flag) carrier via mapping.md §2 bijection) against them on 100k inputs at the pinned seed 25332 plus 50k each at seeds 1 and 999999 (>200k total), covering empty tables (n=0), singletons, and shared/aliased members. ZERO disagreements — per-row (target-identity, weak-flag) tuples matched exactly for both functions. (5) Divergence-class probes all non-diverging: (a) dict-key collapse impossible — two distinct _mapping weakref keys cannot deref to the same live object and referents use identity equality, so strongifyMap's List preserves exactly the dict rows; (b) ordering preserved on both sides (dict comprehensions are order-preserving in py3.7+, folds are order-preserving); (c) **vars(self) carry-over is an observation-channel scoping choice, not a disagreement on the modeled _mapping channel. No diverging input exists on the modeled value domain (tables of live references). Conclusion: the spec reproduces the gold callees exactly and is not stronger than real behavior — FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Instance matplotlib__matplotlib-25332 (velvet). Judged the spec view (markers.spec_view over Solution.lean) against the public problem_statement only, not hints_text.

Mechanical G-LEAK screen (leakage.screen): PASSED, zero hard failures. Token audit of the spec view: 'grouper', 'getstate', 'setstate', 'cbook', '_mapping', 'weakref.ref', 'align', 'matplotlib' all appear 0 times. 'pickle' appears once — and it is already in the public problem_statement (the traceback 'cannot pickle weakref.ReferenceType object' after align_labels/pickle.dumps). No diff markers, no gold-patch line reproduced, no patched file/module path. Patch-changed distinctive symbols {Grouper, getstate, setstate} are NOT echoed anywhere in the spec view.

Semantic reconstruction check: the gold edit adds Grouper.__getstate__ / __setstate__ in lib/matplotlib/cbook.py, converting weak refs to strong ones for serialization and back on restore. The spec view models this behaviorally and abstractly (structure Ref{target, weak}; strongify/weaken; snapshot/rebuild over an anonymous 'grouping registry's reference table'). The core conceptual content — weak references aren't picklable, so make them strong for serialization and restore them afterward — IS the publicly stated bug diagnosis in problem_statement (TypeError: cannot pickle weakref.ReferenceType after align_labels + pickle.dumps). The spec view discloses no edit LOCALIZATION beyond what is public: no class name (Grouper), no method names (__getstate__/__setstate__), no file (cbook.py), no dict-field (_mapping), no pickle-protocol hook identity. A solver reading this spec view learns 'implement a weak→strong snapshot and a strong→weak rebuild over a reference table' — which does not point to Grouper's pickle protocol methods any more than the public traceback already does.

same_spec (swebench_unified.markers.same_spec) is byte-identical between Solution.lean and both Solution_prepatch.lean and Solution_prepatch_2.lean — the frozen spec region is stable across the differ variants, confirming the spec view is impl-independent. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
