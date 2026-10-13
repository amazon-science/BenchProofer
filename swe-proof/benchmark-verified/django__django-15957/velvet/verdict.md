# P2 adversarial audit — django__django-15957

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.lean`, `atk_boundary.lean`, `atk_partial.lean`, `atk_ctrl.lean`, `atk_ungrounded.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo1.lean`, `atk_echo2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -57,18 +57,7 @@
   ensures out = slicedGroups low high groups
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := groups.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ groups.length
-      invariant result = slicedGroups low high (groups.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
-      i := i - 1
-    return result
+    return slicedGroups low high groups
     -- impl-end
 
 /- The backward-fold step: dropping one fewer group exposes the group at `i-1`
@@ -89,5 +78,3 @@
 
 prove_correct perGroupSlice by
   loom_solve
-  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
-  simp_all
```

Attack 2 — `atk_echo2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -58,16 +58,15 @@
   do
     -- impl-start
     let mut result : List Int := []
-    let mut i := groups.length
-    while i > 0
+    let mut i := 0
+    while i < groups.length
       invariant 0 ≤ i ∧ i ≤ groups.length
-      invariant result = slicedGroups low high (groups.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = slicedGroups low high (groups.take i)
+      done_with i = groups.length
     do
-      let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
-      i := i - 1
+      let g := groups[i]!
+      result := result ++ groupSlice low high g
+      i := i + 1
     return result
     -- impl-end
 
@@ -88,6 +87,19 @@
   rw [hcons, slicedGroups_cons]
 
 prove_correct perGroupSlice by
-  loom_solve
-  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
-  simp_all
+  have sg_append : ∀ (xs ys : List (List Int)),
+      slicedGroups low high (xs ++ ys)
+        = slicedGroups low high xs ++ slicedGroups low high ys := by
+    intro xs ys
+    induction xs with
+    | nil => simp [slicedGroups]
+    | cons a bs ih => simp [slicedGroups_cons, ih, List.append_assoc]
+  have step : ∀ (i : Nat) (result : List Int), i < groups.length →
+      result = slicedGroups low high (groups.take i) →
+      result ++ groupSlice low high (groups[i]?.getD default)
+        = slicedGroups low high (groups.take (i + 1)) := by
+    intro i result hlt hinv
+    rw [List.getElem?_eq_getElem hlt, Option.getD_some,
+        List.take_succ_eq_append_getElem hlt, sg_append, hinv]
+    simp [slicedGroups]
+  loom_solve <;> simp_all [step]
```

Attack 3 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -57,18 +57,17 @@
   ensures out = slicedGroups low high groups
   do
     -- impl-start
-    let mut result : List Int := []
+    let mut combined : List Int := []
     let mut i := groups.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ groups.length
-      invariant result = slicedGroups low high (groups.drop i)
+      invariant combined = (groups.drop i).flatten
       done_with i = 0
-      decreasing i
     do
       let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
+      combined := g ++ combined
       i := i - 1
-    return result
+    return groupSlice low high combined
     -- impl-end
 
 /- The backward-fold step: dropping one fewer group exposes the group at `i-1`
@@ -89,5 +88,14 @@
 
 prove_correct perGroupSlice by
   loom_solve
-  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
+  have flatten_drop_step :
+      (groups.drop (i - 1)).flatten = groups[i - 1]! ++ (groups.drop i).flatten := by
+    have hlt : i - 1 < groups.length := by omega
+    have hcons : groups.drop (i - 1) = groups[i - 1]! :: groups.drop i := by
+      have h := List.drop_eq_getElem_cons hlt
+      rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
+      have hsucc : i - 1 + 1 = i := by omega
+      rw [h, hsucc]
+    rw [hcons, List.flatten_cons]
+  rw [flatten_drop_step]
   simp_all
```

Attack 4 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -63,10 +63,12 @@
       invariant 0 ≤ i ∧ i ≤ groups.length
       invariant result = slicedGroups low high (groups.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
+      let s := match high with
+        | none   => g.drop (low + 1)
+        | some h => (g.drop low).take (h - low)
+      result := s ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_partial.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -63,10 +63,9 @@
       invariant 0 ≤ i ∧ i ≤ groups.length
       invariant result = slicedGroups low high (groups.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
+      result := g.drop low ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_ctrl.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -63,10 +63,9 @@
       invariant 0 ≤ i ∧ i ≤ groups.length
       invariant result = slicedGroups low high (groups.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
+      result := result ++ groupSlice low high g
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_ungrounded.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model reference of an outside callee. The
@@ -57,18 +57,7 @@
   ensures out = slicedGroups low high groups
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := groups.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ groups.length
-      invariant result = slicedGroups low high (groups.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := groups[i - 1]!
-      result := groupSlice low high g ++ result
-      i := i - 1
-    return result
+    return groups.flatten
     -- impl-end
 
 /- The backward-fold step: dropping one fewer group exposes the group at `i-1`
@@ -89,5 +78,3 @@
 
 prove_correct perGroupSlice by
   loom_solve
-  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model reference of an outside callee. The
--  operation modeled here — taking an ordered slice of each independent group of
--  related rows — is spelled out directly by `groupSlice`/`slicedGroups` over
--  the already-ordered groups. The machinery that resolves the ordering of each
--  group is unchanged and shared by both the old and new behaviour, so the
--  resolved order enters as an abstracted input (the already-ordered `groups`),
--  not as a consumed contract. See mapping.md §3. -/
-- axioms-end

-- pure-start
/- A requested slice is a half-open range of positions: a start offset `low`
   (number of leading rows to skip) and an optional stop `high` (`none` means
   "to the end"). Positions are 0-based. -/

/- The slice of ONE ordered group: skip the first `low` rows, then keep up to
   the stop. With an open-ended stop, keep everything after the offset; with a
   concrete stop `h`, keep the rows whose position is in `[low, h)`. This is the
   per-group analogue of an ordinary sequence slice `g[low:high]`. -/
def groupSlice (low : Nat) (high : Option Nat) (g : List Int) : List Int :=
  match high with
  | none   => g.drop low
  | some h => (g.drop low).take (h - low)

/- The result over many independent groups: each group is sliced ON ITS OWN
   (the offset/stop are measured from the start of that group, not across the
   combined sequence), and the per-group slices are concatenated in group order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def slicedGroups (low : Nat) (high : Option Nat) : List (List Int) → List Int
  | []      => []
  | g :: gs => groupSlice low high g ++ slicedGroups low high gs

@[grind] lemma slicedGroups_nil (low : Nat) (high : Option Nat) :
    slicedGroups low high [] = [] := rfl
@[grind] lemma slicedGroups_cons (low : Nat) (high : Option Nat)
    (g : List Int) (gs : List (List Int)) :
    slicedGroups low high (g :: gs) = groupSlice low high g ++ slicedGroups low high gs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method perGroupSlice (groups : List (List Int)) (low : Nat) (high : Option Nat)
    return (out : List Int)
  ensures out = slicedGroups low high groups
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := groups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ groups.length
      invariant result = slicedGroups low high (groups.drop i)
      done_with i = 0
    do
      let g := groups[i - 1]!
      result := groupSlice low high g ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer group exposes the group at `i-1`
   on the front, so `slicedGroups` peels one `groupSlice`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma slicedGroups_drop_step (low : Nat) (high : Option Nat)
    (groups : List (List Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ groups.length) :
    slicedGroups low high (groups.drop (i - 1))
      = groupSlice low high groups[i - 1]! ++ slicedGroups low high (groups.drop i) := by
  have hlt : i - 1 < groups.length := by omega
  have hcons : groups.drop (i - 1) = groups[i - 1]! :: groups.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, slicedGroups_cons]

prove_correct perGroupSlice by
  loom_solve
  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

scripts+env. same_spec verified True for all 8 files against Solution.lean (velvet backend) via python -c 'from swebench_unified.markers import same_spec ...'. Only impl region + prove_correct body edited; axioms/pure/pre/post byte-identical.

SPEC SHAPE: frozen spec-view keeps `ensures out = slicedGroups low high groups` (an EXACT, TOTAL functional equality, no preconditions) plus the pure groupSlice/slicedGroups defs and the slicedGroups_drop_step helper lemma. Any verifying impl is therefore output-identical to gold.

### VERIFY MATRIX (cmd: `bash scripts/lean_verify.sh <file>`, exit 0=verifies):
  pos_control.lean (gold backward fold)          = exit 0  VERIFIES (positive control)
  atk_echo1.lean (return slicedGroups oracle)    = exit 0  VERIFIES (output-equal)
  atk_echo2.lean (forward foldl, distinct CF)    = exit 0  VERIFIES (output-equal)
  atk_prepatch.lean (GLOBAL slice of flatten)    = exit 1  FAILS (G-DIFF; prepatch bug reproduced)
  atk_boundary.lean (off-by-one drop(low+1))     = exit 1  FAILS (boundary)
  atk_partial.lean (ignores high stop)           = exit 1  FAILS (partial-domain)
  atk_ctrl.lean (reversed group append order)    = exit 1  FAILS (control-flow-effect)
  atk_ungrounded.lean (return groups.flatten)    = exit 1  FAILS (ungrounded-oracle echo)
Only the 3 output-equal impls verify; all 5 wrong-OUTPUT impls are rejected by the exact postcondition. 7 distinct attacks (>=5) + positive control.

RESOLVE (protocol step 2): every verifying attack (echo1, echo2, and the gold pos_control) refines to IDENTICAL per-group-slice Python net behavior, so their faithful refined patch = the gold patch verbatim. Materialized at faithful_patch.diff and RUN through the official harness:
  cmd: python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-15957", <faithful_patch.diff>, timeout=3600, retries=1)'
  RESULT: {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}
Thus every verifying wrong-impl's faithful patch RESOLVES -> no verify=>correct hole. (patches map above lists echo1/echo2; pos_control is the correct control, not a wrong impl.)

REFINEMENT.MD LEG AUDIT (A-legs / deep-model refs, per plan §4): refinement.md declares NO A-legs. Legs A1 (groups<->grouped/ordered rows) and A2 (low/high<->low_mark/high_mark, none<->None) are R (type refinement); the ordering machinery get_compiler(...).get_order_by() is UNCHANGED and shared by both branches, so it is an abstracted input (R), not a consumed axiom. Legs A3 (groupSlice<->window predicate low_mark<rn<=high_mark within one partition) and A4 (slicedGroups<->union over partitions) are I (identical concrete op) and are FULLY EXPRESSIBLE in Lean's pure take/drop/++ fragment. NO A-consumed / NO A-reference / NO kind-3 (inexpressible-changed-op) leg exists — the global->per-group slice change is modeled directly, not hidden behind an opaque axiom. axiom_check.py is a legitimate status=skip stub (verified consistent). This is the decisive point: the classic verify=>correct hole (kind-3 op behind an ungrounded axiom) is absent, and atk_ungrounded empirically confirms the spec is not trivially satisfiable.

G-CONF conf_skip=true is correct (DB-effect oracle: patched net effect only observable via live window-capable backend inside prefetch pipeline); correctness carried by G-VERIFY+G-DIFF+G-RESOLVE+G-EQ per mapping.md §4.

VERDICT: SOUND. >=5 distinct verified attacks run; the prepatch bug and 4 further wrong-output classes all fail verification; the only verifying impls are output-equal to gold and their materialized faithful patch RESOLVES under run_resolve. No falsification found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.lean`, `atk_boundary.lean`, `atk_partial.lean`, `atk_ctrl.lean`, `atk_ungrounded.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo1.lean`, `atk_echo2.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_echo2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_ctrl.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_ungrounded.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model reference of an outside callee. The
--  operation modeled here — taking an ordered slice of each independent group of
--  related rows — is spelled out directly by `groupSlice`/`slicedGroups` over
--  the already-ordered groups. The machinery that resolves the ordering of each
--  group is unchanged and shared by both the old and new behaviour, so the
--  resolved order enters as an abstracted input (the already-ordered `groups`),
--  not as a consumed contract. See mapping.md §3. -/
-- axioms-end

-- pure-start
/- A requested slice is a half-open range of positions: a start offset `low`
   (number of leading rows to skip) and an optional stop `high` (`none` means
   "to the end"). Positions are 0-based. -/

/- The slice of ONE ordered group: skip the first `low` rows, then keep up to
   the stop. With an open-ended stop, keep everything after the offset; with a
   concrete stop `h`, keep the rows whose position is in `[low, h)`. This is the
   per-group analogue of an ordinary sequence slice `g[low:high]`. -/
def groupSlice (low : Nat) (high : Option Nat) (g : List Int) : List Int :=
  match high with
  | none   => g.drop low
  | some h => (g.drop low).take (h - low)

/- The result over many independent groups: each group is sliced ON ITS OWN
   (the offset/stop are measured from the start of that group, not across the
   combined sequence), and the per-group slices are concatenated in group order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def slicedGroups (low : Nat) (high : Option Nat) : List (List Int) → List Int
  | []      => []
  | g :: gs => groupSlice low high g ++ slicedGroups low high gs

@[grind] lemma slicedGroups_nil (low : Nat) (high : Option Nat) :
    slicedGroups low high [] = [] := rfl
@[grind] lemma slicedGroups_cons (low : Nat) (high : Option Nat)
    (g : List Int) (gs : List (List Int)) :
    slicedGroups low high (g :: gs) = groupSlice low high g ++ slicedGroups low high gs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method perGroupSlice (groups : List (List Int)) (low : Nat) (high : Option Nat)
    return (out : List Int)
  ensures out = slicedGroups low high groups
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := groups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ groups.length
      invariant result = slicedGroups low high (groups.drop i)
      done_with i = 0
    do
      let g := groups[i - 1]!
      result := groupSlice low high g ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer group exposes the group at `i-1`
   on the front, so `slicedGroups` peels one `groupSlice`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma slicedGroups_drop_step (low : Nat) (high : Option Nat)
    (groups : List (List Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ groups.length) :
    slicedGroups low high (groups.drop (i - 1))
      = groupSlice low high groups[i - 1]! ++ slicedGroups low high (groups.drop i) := by
  have hlt : i - 1 < groups.length := by omega
  have hcons : groups.drop (i - 1) = groups[i - 1]! :: groups.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, slicedGroups_cons]

prove_correct perGroupSlice by
  loom_solve
  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

scripts+env. same_spec verified True for all 8 files against Solution.lean (velvet backend) via python -c 'from swebench_unified.markers import same_spec ...'. Only impl region + prove_correct body edited; axioms/pure/pre/post byte-identical.

SPEC SHAPE: frozen spec-view keeps `ensures out = slicedGroups low high groups` (an EXACT, TOTAL functional equality, no preconditions) plus the pure groupSlice/slicedGroups defs and the slicedGroups_drop_step helper lemma. Any verifying impl is therefore output-identical to gold.

### VERIFY MATRIX (cmd: `bash scripts/lean_verify.sh <file>`, exit 0=verifies):
  pos_control.lean (gold backward fold)          = exit 0  VERIFIES (positive control)
  atk_echo1.lean (return slicedGroups oracle)    = exit 0  VERIFIES (output-equal)
  atk_echo2.lean (forward foldl, distinct CF)    = exit 0  VERIFIES (output-equal)
  atk_prepatch.lean (GLOBAL slice of flatten)    = exit 1  FAILS (G-DIFF; prepatch bug reproduced)
  atk_boundary.lean (off-by-one drop(low+1))     = exit 1  FAILS (boundary)
  atk_partial.lean (ignores high stop)           = exit 1  FAILS (partial-domain)
  atk_ctrl.lean (reversed group append order)    = exit 1  FAILS (control-flow-effect)
  atk_ungrounded.lean (return groups.flatten)    = exit 1  FAILS (ungrounded-oracle echo)
Only the 3 output-equal impls verify; all 5 wrong-OUTPUT impls are rejected by the exact postcondition. 7 distinct attacks (>=5) + positive control.

RESOLVE (protocol step 2): every verifying attack (echo1, echo2, and the gold pos_control) refines to IDENTICAL per-group-slice Python net behavior, so their faithful refined patch = the gold patch verbatim. Materialized at faithful_patch.diff and RUN through the official harness:
  cmd: python -c 'from swebench_unified.harness import run_resolve; run_resolve("django__django-15957", <faithful_patch.diff>, timeout=3600, retries=1)'
  RESULT: {"resolved": true, "completed": true, "note": "resolved", "attempts": 1, "flaky": false}
Thus every verifying wrong-impl's faithful patch RESOLVES -> no verify=>correct hole. (patches map above lists echo1/echo2; pos_control is the correct control, not a wrong impl.)

REFINEMENT.MD LEG AUDIT (A-legs / deep-model refs, per plan §4): refinement.md declares NO A-legs. Legs A1 (groups<->grouped/ordered rows) and A2 (low/high<->low_mark/high_mark, none<->None) are R (type refinement); the ordering machinery get_compiler(...).get_order_by() is UNCHANGED and shared by both branches, so it is an abstracted input (R), not a consumed axiom. Legs A3 (groupSlice<->window predicate low_mark<rn<=high_mark within one partition) and A4 (slicedGroups<->union over partitions) are I (identical concrete op) and are FULLY EXPRESSIBLE in Lean's pure take/drop/++ fragment. NO A-consumed / NO A-reference / NO kind-3 (inexpressible-changed-op) leg exists — the global->per-group slice change is modeled directly, not hidden behind an opaque axiom. axiom_check.py is a legitimate status=skip stub (verified consistent). This is the decisive point: the classic verify=>correct hole (kind-3 op behind an ungrounded axiom) is absent, and atk_ungrounded empirically confirms the spec is not trivially satisfiable.

G-CONF conf_skip=true is correct (DB-effect oracle: patched net effect only observable via live window-capable backend inside prefetch pipeline); correctness carried by G-VERIFY+G-DIFF+G-RESOLVE+G-EQ per mapping.md §4.

VERDICT: SOUND. >=5 distinct verified attacks run; the prepatch bug and 4 further wrong-output classes all fail verification; the only verifying impls are output-equal to gold and their materialized faithful patch RESOLVES under run_resolve. No falsification found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo callee. (1) Spec region is byte-identical Solution vs prepatch: same_spec=True via velvet backend; Solution.lean verifies EXIT=0; prepatch (global flatten-slice) fails on the discriminating clause groupSlice low high (flatten groups) = slicedGroups low high groups (honest G-DIFF). (2) I independently mechanized the gold patch's real net effect — Window(RowNumber() PARTITION BY field_name ORDER BY order_by) filtered to low_mark<rn<=high_mark (open when high_mark is None) then clear_limits() — as a 1-based row-number keep-predicate in Lean and cross-checked it against slicedGroups/groupSlice on: bounded slice [1:2] with an empty trailing group, open-ended stop (high=none), high<low truncation (some 0), and a 6-elem group + 2-elem group with independent per-partition numbering. ALL FOUR AGREE (decide=true, EXIT=0). The 1-based rn>low ∧ rn<=high ⇔ 0-based [low,high) mapping is exact. (3) A1 abstraction legitimate: ordering machinery get_compiler(...).get_order_by() is byte-unchanged between pre/post patch (patch only adds _filter_prefetch_queryset helper + two call-site swaps), so already-ordered `groups` enters as R, not a hidden axiom — no divergence concealed there. (4) Nat domain sound: Django slice marks always >=0 and low<=high when both set; Nat truncated h-low harmless in-domain and even matches out-of-domain. (5) conf_skip is correct for this DB-effect bundle (oracle only observable through live ORM window query); soundness carried by G-VERIFY+G-DIFF+G-RESOLVE+G-EQ, consistent with meta.json. Spec is TIGHT (exact equality to a concrete axiom-free computable function), not too strong. No FAITHFUL-is-a-defect diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: no hard failures) and same_spec(Solution, Solution_prepatch) is True (spec region byte-identical). Semantic review: the spec view (groupSlice/slicedGroups/perGroupSlice, ensures out = slicedGroups low high groups) models ONLY the public behavioral target. The public problem_statement already establishes per-group slicing: Prefetch on sliced querysets should return each category's own 'couple of example objects from each category' rather than prefetching all objects — so 'independent slice per group' is public, not a leak. The spec view reveals NONE of the gold-edit specifics: no Window/RowNumber/partition_by/GreaterThan/LessThanOrEqual/clear_limits, no low_mark/high_mark, no _filter_prefetch_queryset or get_prefetch_queryset symbol, no related_descriptors.py path, no diff markers, no gold-patch line, no bug/fix narration. Comments stay abstract ('half-open range of positions', 'per-group analogue of an ordinary sequence slice g[low:high]'). A solver learns WHAT correct behavior is (already public) but not HOW the gold patch achieves it (SQL window-function mechanism, the actual edit). Specifying desired behavior is inherent to any spec and not leakage beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
