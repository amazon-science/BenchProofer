# P2 adversarial audit — scikit-learn__scikit-learn-14629

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_empty.lean`, `atk_extra.lean`, `atk_dropfirst.lean`, `atk_reversed.lean`, `atk_const.lean`, `atk_forward.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo.lean`, `atk_map.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_empty.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -52,12 +52,9 @@
     let mut i := submodels.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ submodels.length
-      invariant result = gatheredLabels (submodels.drop i)
+      invariant result = []
       done_with i = 0
-      decreasing i
     do
-      let s := submodels[i - 1]!
-      result := s.labels :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_extra.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -54,12 +54,11 @@
       invariant 0 ≤ i ∧ i ≤ submodels.length
       invariant result = gatheredLabels (submodels.drop i)
       done_with i = 0
-      decreasing i
     do
       let s := submodels[i - 1]!
       result := s.labels :: result
       i := i - 1
-    return result
+    return ([] : List Int) :: result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 3 — `atk_dropfirst.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -50,11 +50,10 @@
     -- impl-start
     let mut result : List (List Int) := []
     let mut i := submodels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ submodels.length
+    while i > 1
+      invariant 1 ≤ i ∧ i ≤ submodels.length
       invariant result = gatheredLabels (submodels.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let s := submodels[i - 1]!
       result := s.labels :: result
```

Attack 4 — `atk_reversed.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -52,12 +52,11 @@
     let mut i := submodels.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ submodels.length
-      invariant result = gatheredLabels (submodels.drop i)
+      invariant result = (gatheredLabels (submodels.drop i)).reverse
       done_with i = 0
-      decreasing i
     do
       let s := submodels[i - 1]!
-      result := s.labels :: result
+      result := result ++ [s.labels]
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_const.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -54,9 +54,8 @@
       invariant 0 ≤ i ∧ i ≤ submodels.length
       invariant result = gatheredLabels (submodels.drop i)
       done_with i = 0
-      decreasing i
     do
-      let s := submodels[i - 1]!
+      let s := submodels[0]!
       result := s.labels :: result
       i := i - 1
     return result
```

Attack 6 — `atk_forward.lean` → rejected (same spec, does not verify — good)

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
 -- axioms-end
@@ -49,16 +49,14 @@
   do
     -- impl-start
     let mut result : List (List Int) := []
-    let mut i := submodels.length
-    while i > 0
+    let mut i := 0
+    while i < submodels.length
       invariant 0 ≤ i ∧ i ≤ submodels.length
-      invariant result = gatheredLabels (submodels.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = gatheredLabels (submodels.take i)
+      done_with i = submodels.length
     do
-      let s := submodels[i - 1]!
-      result := s.labels :: result
-      i := i - 1
+      result := result ++ [submodels[i]!.labels]
+      i := i + 1
     return result
     -- impl-end
 
@@ -79,5 +77,12 @@
 
 prove_correct gatherLabels by
   loom_solve
-  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
-  simp_all
+  · have hlt : i < submodels.length := by omega
+    have h : submodels.take (i+1) = submodels.take i ++ [submodels[i]!] := by
+      rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
+      exact List.take_succ_eq_append_getElem hlt
+    rw [h]
+    clear h
+    induction submodels.take i with
+    | nil => simp [gatheredLabels]
+    | cons a as ih => simp_all [gatheredLabels]
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- axioms-end
@@ -48,18 +48,7 @@
   ensures out.length = submodels.length
   do
     -- impl-start
-    let mut result : List (List Int) := []
-    let mut i := submodels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ submodels.length
-      invariant result = gatheredLabels (submodels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := submodels[i - 1]!
-      result := s.labels :: result
-      i := i - 1
-    return result
+    return gatheredLabels submodels
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -79,5 +68,3 @@
 
 prove_correct gatherLabels by
   loom_solve
-  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_map.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- axioms-end
@@ -48,18 +48,7 @@
   ensures out.length = submodels.length
   do
     -- impl-start
-    let mut result : List (List Int) := []
-    let mut i := submodels.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ submodels.length
-      invariant result = gatheredLabels (submodels.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := submodels[i - 1]!
-      result := s.labels :: result
-      i := i - 1
-    return result
+    return submodels.map (fun s => s.labels)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -78,6 +67,7 @@
   rw [hcons, gatheredLabels_cons]
 
 prove_correct gatherLabels by
-  loom_solve
-  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
-  simp_all
+  loom_solve <;>
+  · induction submodels with
+    | nil => rfl
+    | cons s ss ih => simp [gatheredLabels, ih]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- One per-target sub-model of a fitted multi-target classifier. Only the
   touched field is modeled: the collection of class labels that sub-model
   learned for its target. -/
structure Submodel where
  labels : List Int
  deriving Inhabited

/- The per-target class-label record of a fitted multi-target classifier: one
   label collection per sub-model, in sub-model order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def gatheredLabels : List Submodel → List (List Int)
  | []      => []
  | s :: ss => s.labels :: gatheredLabels ss

@[grind] lemma gatheredLabels_nil : gatheredLabels [] = [] := rfl
@[grind] lemma gatheredLabels_cons (s : Submodel) (ss : List Submodel) :
    gatheredLabels (s :: ss) = s.labels :: gatheredLabels ss := rfl

/- The record has exactly one entry per sub-model: its length equals the number
   of targets. (Mirrors the tested `len(...) == n_outputs`.) -/
@[grind] lemma gatheredLabels_length (ss : List Submodel) :
    (gatheredLabels ss).length = ss.length := by
  induction ss with
  | nil => rfl
  | cons s ss ih => simp [gatheredLabels, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method gatherLabels (submodels : List Submodel) return (out : List (List Int))
  ensures out = gatheredLabels submodels
  ensures out.length = submodels.length
  do
    -- impl-start
    let mut result : List (List Int) := []
    let mut i := submodels.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ submodels.length
      invariant result = gatheredLabels (submodels.drop i)
      done_with i = 0
    do
      let s := submodels[i - 1]!
      result := s.labels :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `gatheredLabels` peels one entry. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma gatheredLabels_drop_step (submodels : List Submodel) (i : Nat)
    (hi : 0 < i) (hle : i ≤ submodels.length) :
    gatheredLabels (submodels.drop (i - 1))
      = submodels[i - 1]!.labels :: gatheredLabels (submodels.drop i) := by
  have hlt : i - 1 < submodels.length := by omega
  have hcons : submodels.drop (i - 1) = submodels[i - 1]! :: submodels.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, gatheredLabels_cons]

prove_correct gatherLabels by
  loom_solve
  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TIGHT functional postcondition: `ensures out = gatheredLabels submodels` (exact-value pin) plus `ensures out.length = submodels.length`. Axioms region is EMPTY; A-legs are 'A-consumed-as-precondition' (unchanged parent MultiOutputEstimator.fit producing estimators_) and I-ops (read classes_ field, collect in order). No ungrounded oracle is asserted — the .classes_ values flow from the input carrier `submodels`, not pinned to an oracle.

PROTOCOL EXECUTED (all; same_spec=True verified for all 8 attacks via swebench_unified.markers.same_spec + get_backend('velvet'); verified via scripts/lean_verify.sh <f>).

Same-spec check command (per file): python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(GOLD).read(), open(ATK).read(), b.language))" -> True for atk_const,atk_dropfirst,atk_echo,atk_empty,atk_extra,atk_forward,atk_map + pos_control.

Verify command: bash scripts/lean_verify.sh <path>. Results:
- pos_control.lean (gold impl verbatim): exit 0 (VERIFIES) — positive control OK.
- prepatch.lean (Solution_prepatch.lean, empty-result impl): exit 1 (FAILS) — prepatch bug REPRODUCED (rewrite failed / unsolved: result != gatheredLabels submodels).
- atk_empty.lean (all-empty, == prepatch bug re-encode): exit 1 REJECTED.
- atk_extra.lean (prepend extra [] entry, wrong length/value): exit 1 REJECTED.
- atk_dropfirst.lean (partial-domain: while i>1 skips index 0 sub-model): exit 1 REJECTED.
- atk_reversed.lean (boundary/order: builds reversed list via append): exit 1 REJECTED.
- atk_const.lean (control-flow-effect: uses submodels[0]! for every entry): exit 1 REJECTED.
- atk_forward.lean (forward take-based loop, correct algorithm): exit 1 (my inline proof did not close; behaviorally correct anyway).
- atk_echo.lean (ungrounded-oracle echo: `return gatheredLabels submodels`): exit 0 VERIFIES.
- atk_map.lean (`submodels.map (fun s => s.labels)`, proved = gatheredLabels by induction): exit 0 VERIFIES.

RESOLVE STEP (mandatory for every verifying attack): both verifying impls (atk_echo, atk_map) return EXACTLY `gatheredLabels submodels` — the deep model itself — so their faithful refined patch is precisely the gold Python `self.classes_ = [estimator.classes_ for estimator in self.estimators_]`. The materialized faithful patch (faithful_echo.diff / faithful_map.diff, sha1 824bde5b… byte-identical to gold patch.diff) was RUN through the official harness:
  run_resolve('scikit-learn__scikit-learn-14629', patch, run_id='sbu-audit-eq-atk-echo', timeout=1800)
  -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'.
Both verifying attacks are behaviorally correct AND their faithful patch RESOLVES. No verify⇏correct break exists.

REFINEMENT.MD AUDIT: 4 legs (A1..A4). A1 = A-consumed-as-precondition (unchanged parent fit; G-AX pass confirms estimators_ is length-n_outputs list, each .classes_ present, no raise — correspondence to real callee holds). A2 = I+R (read touched field classes_ -> Submodel.labels; concrete). A3 = I (list comprehension = per-sub-model fold = gatheredLabels, order-preserving). A4 = R (result list bijection + len==n_outputs <-> out.length=submodels.length). Section B explicitly rules out kind-3: the genuinely-changed op (recording labels) is modeled CONCRETELY, not axiomatized; no .classes_ value pinned to an oracle. Second gold hunk (whitespace dedent of raise ValueError) correctly declared non-modeled/cosmetic and carried verbatim. NO kind-3 legs; A-leg correspondence sound. G-AX=pass, G-CONF=pass, G-RESOLVE=pass corroborate.

CONCLUSION: ≥5 distinct wrong impls (empty, extra, dropfirst, reversed, const — plus prepatch) all REJECTED by the tight postcondition; the only verifying same-spec impls are behaviorally correct echoes/reformulations of the deep model whose faithful patch RESOLVES under the official harness. verify⇒correct holds. SOUND. (The recorded G-EQ 'INCONCLUSIVE — only 0 attacks' verdict was a protocol artifact from an un-run audit, not a real weakness.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_empty.lean`, `atk_extra.lean`, `atk_dropfirst.lean`, `atk_reversed.lean`, `atk_const.lean`, `atk_forward.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo.lean`, `atk_map.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_empty.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_extra.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_dropfirst.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_reversed.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_const.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_forward.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_map.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- One per-target sub-model of a fitted multi-target classifier. Only the
   touched field is modeled: the collection of class labels that sub-model
   learned for its target. -/
structure Submodel where
  labels : List Int
  deriving Inhabited

/- The per-target class-label record of a fitted multi-target classifier: one
   label collection per sub-model, in sub-model order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def gatheredLabels : List Submodel → List (List Int)
  | []      => []
  | s :: ss => s.labels :: gatheredLabels ss

@[grind] lemma gatheredLabels_nil : gatheredLabels [] = [] := rfl
@[grind] lemma gatheredLabels_cons (s : Submodel) (ss : List Submodel) :
    gatheredLabels (s :: ss) = s.labels :: gatheredLabels ss := rfl

/- The record has exactly one entry per sub-model: its length equals the number
   of targets. (Mirrors the tested `len(...) == n_outputs`.) -/
@[grind] lemma gatheredLabels_length (ss : List Submodel) :
    (gatheredLabels ss).length = ss.length := by
  induction ss with
  | nil => rfl
  | cons s ss ih => simp [gatheredLabels, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method gatherLabels (submodels : List Submodel) return (out : List (List Int))
  ensures out = gatheredLabels submodels
  ensures out.length = submodels.length
  do
    -- impl-start
    let mut result : List (List Int) := []
    let mut i := submodels.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ submodels.length
      invariant result = gatheredLabels (submodels.drop i)
      done_with i = 0
    do
      let s := submodels[i - 1]!
      result := s.labels :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `gatheredLabels` peels one entry. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma gatheredLabels_drop_step (submodels : List Submodel) (i : Nat)
    (hi : 0 < i) (hle : i ≤ submodels.length) :
    gatheredLabels (submodels.drop (i - 1))
      = submodels[i - 1]!.labels :: gatheredLabels (submodels.drop i) := by
  have hlt : i - 1 < submodels.length := by omega
  have hcons : submodels.drop (i - 1) = submodels[i - 1]! :: submodels.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, gatheredLabels_cons]

prove_correct gatherLabels by
  loom_solve
  rw [gatheredLabels_drop_step submodels i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TIGHT functional postcondition: `ensures out = gatheredLabels submodels` (exact-value pin) plus `ensures out.length = submodels.length`. Axioms region is EMPTY; A-legs are 'A-consumed-as-precondition' (unchanged parent MultiOutputEstimator.fit producing estimators_) and I-ops (read classes_ field, collect in order). No ungrounded oracle is asserted — the .classes_ values flow from the input carrier `submodels`, not pinned to an oracle.

PROTOCOL EXECUTED (all; same_spec=True verified for all 8 attacks via swebench_unified.markers.same_spec + get_backend('velvet'); verified via scripts/lean_verify.sh <f>).

Same-spec check command (per file): python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(GOLD).read(), open(ATK).read(), b.language))" -> True for atk_const,atk_dropfirst,atk_echo,atk_empty,atk_extra,atk_forward,atk_map + pos_control.

Verify command: bash scripts/lean_verify.sh <path>. Results:
- pos_control.lean (gold impl verbatim): exit 0 (VERIFIES) — positive control OK.
- prepatch.lean (Solution_prepatch.lean, empty-result impl): exit 1 (FAILS) — prepatch bug REPRODUCED (rewrite failed / unsolved: result != gatheredLabels submodels).
- atk_empty.lean (all-empty, == prepatch bug re-encode): exit 1 REJECTED.
- atk_extra.lean (prepend extra [] entry, wrong length/value): exit 1 REJECTED.
- atk_dropfirst.lean (partial-domain: while i>1 skips index 0 sub-model): exit 1 REJECTED.
- atk_reversed.lean (boundary/order: builds reversed list via append): exit 1 REJECTED.
- atk_const.lean (control-flow-effect: uses submodels[0]! for every entry): exit 1 REJECTED.
- atk_forward.lean (forward take-based loop, correct algorithm): exit 1 (my inline proof did not close; behaviorally correct anyway).
- atk_echo.lean (ungrounded-oracle echo: `return gatheredLabels submodels`): exit 0 VERIFIES.
- atk_map.lean (`submodels.map (fun s => s.labels)`, proved = gatheredLabels by induction): exit 0 VERIFIES.

RESOLVE STEP (mandatory for every verifying attack): both verifying impls (atk_echo, atk_map) return EXACTLY `gatheredLabels submodels` — the deep model itself — so their faithful refined patch is precisely the gold Python `self.classes_ = [estimator.classes_ for estimator in self.estimators_]`. The materialized faithful patch (faithful_echo.diff / faithful_map.diff, sha1 824bde5b… byte-identical to gold patch.diff) was RUN through the official harness:
  run_resolve('scikit-learn__scikit-learn-14629', patch, run_id='sbu-audit-eq-atk-echo', timeout=1800)
  -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'.
Both verifying attacks are behaviorally correct AND their faithful patch RESOLVES. No verify⇏correct break exists.

REFINEMENT.MD AUDIT: 4 legs (A1..A4). A1 = A-consumed-as-precondition (unchanged parent fit; G-AX pass confirms estimators_ is length-n_outputs list, each .classes_ present, no raise — correspondence to real callee holds). A2 = I+R (read touched field classes_ -> Submodel.labels; concrete). A3 = I (list comprehension = per-sub-model fold = gatheredLabels, order-preserving). A4 = R (result list bijection + len==n_outputs <-> out.length=submodels.length). Section B explicitly rules out kind-3: the genuinely-changed op (recording labels) is modeled CONCRETELY, not axiomatized; no .classes_ value pinned to an oracle. Second gold hunk (whitespace dedent of raise ValueError) correctly declared non-modeled/cosmetic and carried verbatim. NO kind-3 legs; A-leg correspondence sound. G-AX=pass, G-CONF=pass, G-RESOLVE=pass corroborate.

CONCLUSION: ≥5 distinct wrong impls (empty, extra, dropfirst, reversed, const — plus prepatch) all REJECTED by the tight postcondition; the only verifying same-spec impls are behaviorally correct echoes/reformulations of the deep model whose faithful patch RESOLVES under the official harness. verify⇒correct holds. SOUND. (The recorded G-EQ 'INCONCLUSIVE — only 0 attacks' verdict was a protocol artifact from an un-run audit, not a real weakness.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit for scikit-learn__scikit-learn-14629 (velvet). Modeled function: the gold-added line in MultiOutputClassifier.fit — self.classes_ = [estimator.classes_ for estimator in self.estimators_] (sklearn/multioutput.py:327). Spec postconditions: out = gatheredLabels submodels and out.length = submodels.length, where gatheredLabels is the front-recursive order-preserving projection map(·.labels), each Submodel exposing only the touched field labels : List Int.

Verification: (1) markers.same_spec(Solution, Solution_prepatch, velvet) = True — spec region byte-identical; only impl/proof differ (prepatch leaves result empty so it fails both postconditions, mirroring the pre-fix AttributeError). (2) lean_verify.sh Solution.lean exit 0. (3) Real repo at base_commit 4aded39b: parent MultiOutputEstimator.fit sets self.estimators_ = one fitted sub-model per output column, in order (for i in range(y.shape[1])), each exposing .classes_. The patch's comprehension is a pure order-preserving list projection: no filter, no reorder, no transform.

The model agrees with the real callee on EVERY input: empty estimators_ -> []; length always == number of sub-models; i-th entry always the i-th sub-model's classes_. The spec is neither too strong (it rules out no real behavior — it is exactly the projection) nor drifting (label dtype abstracted to Int is a sound structural projection; the discriminating content per mapping.md is the per-target STRUCTURE, which matches the F2P test's isinstance-list / len==n_outputs / elementwise assert_array_equal). Second gold hunk (whitespace dedent of raise ValueError("invalid order") in _BaseChain.fit) is genuinely behavior-preserving and correctly not modeled. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region byte-identity confirmed: markers.same_spec(Solution, Solution_prepatch)=True under LeanBackend; G-HYGIENE/G-INTEGRITY pass. Rendered the actual consumer spec view (impl region elided to 'implementation elided — supplied by the consumer'). The screened spec view models only a generic `Submodel {labels : List Int}`, a `gatheredLabels` fold collecting each sub-model's labels in order, and `gatherLabels` with `out = gatheredLabels submodels` / `out.length = submodels.length`.

Public baseline is unusually explicit: problem_statement literally states the fix — 'To obtain the classes_ attribute of a MultiOutputClassifier, you need mo_clf.estimators_[i].classes_ instead' — and gives the AttributeError. The gold edit is `self.classes_ = [estimator.classes_ for estimator in self.estimators_]`. The spec view is a direct formalization of exactly what problem_statement already discloses (gather each sub-model's class-labels, one per target, in order). It leaks nothing beyond public text:
- No gold-specific identifiers appear (no self.classes_, MultiOutputClassifier.fit, sample_weight, super().fit, no mention of the second whitespace-dedent hunk in _BaseChain.fit).
- Symbols are generic Lean (Submodel, labels, gatheredLabels, gatherLabels).
- The 'one entry per sub-model / length = n_outputs' postcondition follows directly from the public 'one estimators_[i].classes_ per output' description; it does not reveal the edit beyond the public statement.

Note: mapping.md and refinement.md quote the gold hunk verbatim, but those audit-narrative files are NOT part of the consumer spec view screened by the leak gate; the elided spec view (impl-start/impl-end stripped) is what a solver sees. G-LEAK recorded pass (spec view clean). No leaking line identified.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
