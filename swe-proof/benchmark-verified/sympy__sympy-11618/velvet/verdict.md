# P2 adversarial audit — sympy__sympy-11618

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- axioms-end
@@ -81,23 +81,22 @@
   ensures out = distSq sameKind s q
   do
     -- impl-start
-    let L := if sameKind then min s.length q.length else max s.length q.length
+    let L := min s.length q.length
     let mut acc : Int := 0
     let mut i := L
     while i > 0
       invariant 0 ≤ i ∧ i ≤ L
-      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
+      invariant acc = sumSqZip (s.drop i) (q.drop i)
       done_with i = 0
-      decreasing i
     do
-      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
+      acc := (s[i-1]! - q[i-1]!) ^ 2 + acc
       i := i - 1
     return acc
     -- impl-end
 
 prove_correct distanceSq by
   loom_solve
-  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]
+  · rw [sumSqZip_drop_step s q i (by simp_all) (by simp_all) (by omega)]
     simp_all
   · simp only [distSq, commonLen]
     simp_all
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
 -- axioms-end
@@ -88,9 +88,8 @@
       invariant 0 ≤ i ∧ i ≤ L
       invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
       done_with i = 0
-      decreasing i
     do
-      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
+      acc := ((alignTo s L)[i]! - (alignTo q L)[i]!) ^ 2 + acc
       i := i - 1
     return acc
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
 -- axioms-end
@@ -88,10 +88,9 @@
       invariant 0 ≤ i ∧ i ≤ L
       invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
       done_with i = 0
-      decreasing i
     do
       acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
-      i := i - 1
+      i := i - 2
     return acc
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
 -- axioms-end
@@ -86,11 +86,10 @@
     let mut i := L
     while i > 0
       invariant 0 ≤ i ∧ i ≤ L
-      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
+      invariant acc = sumSqZip ((alignTo s L).drop i) (q.drop i)
       done_with i = 0
-      decreasing i
     do
-      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
+      acc := ((alignTo s L)[i-1]! - q[i-1]!) ^ 2 + acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
@@ -81,23 +81,8 @@
   ensures out = distSq sameKind s q
   do
     -- impl-start
-    let L := if sameKind then min s.length q.length else max s.length q.length
-    let mut acc : Int := 0
-    let mut i := L
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ L
-      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
-      done_with i = 0
-      decreasing i
-    do
-      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
-      i := i - 1
-    return acc
+    return distSq sameKind s q
     -- impl-end
 
 prove_correct distanceSq by
   loom_solve
-  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]
-    simp_all
-  · simp only [distSq, commonLen]
-    simp_all
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
@@ -81,23 +81,15 @@
   ensures out = distSq sameKind s q
   do
     -- impl-start
-    let L := if sameKind then min s.length q.length else max s.length q.length
-    let mut acc : Int := 0
-    let mut i := L
+    let acc : Int := distSq sameKind s q
+    let mut i := 1
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ L
-      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
+      invariant acc = distSq sameKind s q ∧ 0 ≤ i
       done_with i = 0
-      decreasing i
     do
-      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
-      i := i - 1
+      i := i
     return acc
     -- impl-end
 
 prove_correct distanceSq by
   loom_solve
-  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]
-    simp_all
-  · simp only [distSq, commonLen]
-    simp_all
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
@@ -88,11 +88,10 @@
       invariant 0 ≤ i ∧ i ≤ L
       invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
       done_with i = 0
-      decreasing i
     do
       acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
       i := i - 1
-    return acc
+    return acc + 0
     -- impl-end
 
 prove_correct distanceSq by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
@@ -85,13 +85,12 @@
     let mut acc : Int := 0
     let mut i := L
     while i > 0
+      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
       invariant 0 ≤ i ∧ i ≤ L
-      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
       done_with i = 0
-      decreasing i
     do
       acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
-      i := i - 1
+      i := i
     return acc
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Conform a coordinate vector to a target ambient dimension `n`: keep its first
   `n` entries and pad the rest of the way with zero coordinates. The origin of
   the ambient space is all-zeros, so a missing coordinate contributes as 0. -/
def alignTo (xs : List Int) (n : Nat) : List Int :=
  xs.take n ++ List.replicate (n - xs.length) 0

@[grind, simp] lemma alignTo_length (xs : List Int) (n : Nat) :
    (alignTo xs n).length = n := by
  simp [alignTo, List.length_take, List.length_replicate]; omega

/- The squared Euclidean distance between two equally-positioned coordinate
   vectors: the sum of the squares of the per-coordinate differences, taken
   coordinate by coordinate. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern). On unequal lengths the surplus tail is
   dropped; callers align first so both vectors share a length. -/
def sumSqZip : List Int → List Int → Int
  | a :: u, b :: v => (a - b) ^ 2 + sumSqZip u v
  | _, _ => 0

@[grind] lemma sumSqZip_cons (a b : Int) (u v : List Int) :
    sumSqZip (a :: u) (b :: v) = (a - b) ^ 2 + sumSqZip u v := rfl

@[grind, simp] lemma sumSqZip_nil_left (v : List Int) : sumSqZip [] v = 0 := rfl

@[grind, simp] lemma sumSqZip_nil_right (u : List Int) : sumSqZip u [] = 0 := by
  cases u <;> rfl

/- The ambient dimension the two vectors are compared in. When the two points
   are of the same kind their coordinate counts already agree (`min = max`);
   when they are of different kinds the comparison is carried out in the larger
   ambient space, so the shorter vector is treated as embedded at the origin in
   the extra dimensions. -/
def commonLen (sameKind : Bool) (s q : List Int) : Nat :=
  if sameKind then min s.length q.length else max s.length q.length

/- The squared Euclidean distance: align both coordinate vectors to the common
   ambient dimension (zero-padding the shorter), then sum the squared
   per-coordinate differences. No coordinate is silently discarded. -/
def distSq (sameKind : Bool) (s q : List Int) : Int :=
  sumSqZip (alignTo s (commonLen sameKind s q)) (alignTo q (commonLen sameKind s q))

/- The backward-fold step: for two equal-length vectors, dropping one fewer
   element exposes the coordinate at index `i-1` on the front of both, so
   `sumSqZip` peels one squared-difference term. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma sumSqZip_drop_step (A B : List Int) (i : Nat)
    (hA : i ≤ A.length) (hAB : A.length = B.length) (hi : 0 < i) :
    sumSqZip (A.drop (i - 1)) (B.drop (i - 1))
      = (A[i-1]! - B[i-1]!) ^ 2 + sumSqZip (A.drop i) (B.drop i) := by
  have hltA : i - 1 < A.length := by omega
  have hltB : i - 1 < B.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  have hcA : A.drop (i - 1) = A[i-1]! :: A.drop i := by
    have h := List.drop_eq_getElem_cons hltA
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hltA, Option.getD_some, h, hsucc]
  have hcB : B.drop (i - 1) = B[i-1]! :: B.drop i := by
    have h := List.drop_eq_getElem_cons hltB
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hltB, Option.getD_some, h, hsucc]
  rw [hcA, hcB, sumSqZip_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method distanceSq (sameKind : Bool) (s : List Int) (q : List Int) return (out : Int)
  ensures out = distSq sameKind s q
  do
    -- impl-start
    let L := if sameKind then min s.length q.length else max s.length q.length
    let mut acc : Int := 0
    let mut i := L
    while i > 0
      invariant 0 ≤ i ∧ i ≤ L
      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
      done_with i = 0
    do
      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
      i := i - 1
    return acc
    -- impl-end

prove_correct distanceSq by
  loom_solve
  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]
    simp_all
  · simp only [distSq, commonLen]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: method distanceSq with TOTAL postcondition `out = distSq sameKind s q` (no precondition). distSq = sumSqZip (alignTo s L) (alignTo q L), L=commonLen. No axioms, no deep_model_references (meta confirms axioms:[], deep_model_references:[]) — so the A-leg audit reduces to the model<->patch correspondence, which I verified 3 independent ways (below).

All files confirmed same_spec=True vs frozen Solution.lean (velvet spec_view collapses impl + prove_correct body). Verify via `bash scripts/lean_verify.sh <f>` (0=verifies,1=err,3=sorry,124=timeout).

BASELINES: positive_control.lean (gold model) -> EXIT 0 (verifies). prepatch.lean (min-truncation bug, L:=min, no alignment) -> EXIT 1 (bug reproduced: fails `out=distSq` on unequal lengths).

ATTACKS (8, >=5 floor met; 4 distinct wrong-impl families all correctly REJECTED because the postcondition is a total functional equation, leaving no behavioral slack):
- atk_1 min-truncation / partial-domain (L:=min, raw drops) -> EXIT 1 REJECTED.
- atk_2 boundary off-by-one (aligned[i]! instead of [i-1]!) -> EXIT 1 REJECTED.
- atk_3 control-flow effect (i:=i-2, skips coordinates) -> EXIT 1 REJECTED.
- atk_4 partial-domain (align s only, q raw) -> EXIT 1 REJECTED.
- atk_8 control-flow (i:=i non-decrementing, non-oracle) -> EXIT 1 REJECTED.
VERIFYING candidates (echo family):
- atk_5 ungrounded-oracle echo (`return distSq sameKind s q`) -> EXIT 0 VERIFIES.
- atk_6 divergent-loop partial-correctness escape (`acc := distSq ...; while i>0 do i:=i; return acc`) -> EXIT 0 VERIFIES. Adversarially interesting (termination "partial" -> a divergent loop can verify vacuously) but its only observable = distSq (correct); the added loop refines NO repo op (spurious, no callee) so its faithful patch is still the gold; treating partial-corr divergence as a break would void every velvet bundle.
- atk_7 correct fold variant (`return acc + 0`) -> EXIT 0 VERIFIES.

RESOLVE (mandatory step, EXECUTED, not speculated): all 3 verifying impls compute exactly distSq = the gold's squared distance, so each faithfully refines to the GOLD patch. run_resolve('sympy__sympy-11618', gold_patch, timeout=1200) -> RESOLVED=True, COMPLETED=True, NOTE='resolved'. Therefore all 3 are 'correct echoes' (verify AND patch resolves) — none is a spec weakness. No verifying impl's faithful patch fails to resolve.

MODEL<->PATCH FIDELITY (A-leg crux) verified independently inside the instance Docker image (mirror.gcr.io/swebench/sweb.eval.x86_64.sympy_1776_sympy-11618, gold patch git-applied): distSq shadow vs real patched Point.distance(p)**2 -> 3750 fuzzed integer-coord pairs (dims 1-5, both same/diff kind) with 0 mismatches, plus 8 targeted boundary cases (F2P Point3D(1,0,2) vs Point2D(2,0)=5, both longer/shorter directions, equal-len diff-kind, base-Point same-kind min-truncation) all matching. commonLen's min on same-kind matches gold's truncating zip; max on diff-kind matches the p1=[0]*max padding branch; alignTo = the p1 zero-extension.

REFINEMENT.MD LEG AUDIT: legs A1-A7 all tagged R (A1 args->List Int, A2 p.args, A3 sameKind<->type(p) is type(self), A7 sqrt injective on [0,inf) so squared pins distance) or I (A4 commonLen, A5 alignTo, A6 sumSqZip). No kind-3 (inexpressible-changed-op) legs: the operation that actually changed (zero-pad-shorter vs truncate) is modeled DEEPLY in pure arithmetic (alignTo+commonLen), not hidden behind an axiom. No axioms / no A-legs to check callee-correspondence for; the model-fidelity probe above discharges the R/I legs empirically.

FLOOR: 8 attacks (>=5), prepatch reproduced, positive control verifies & is distinct from all attacks. No confirmed break after running the required resolve on every verifying candidate.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- Conform a coordinate vector to a target ambient dimension `n`: keep its first
   `n` entries and pad the rest of the way with zero coordinates. The origin of
   the ambient space is all-zeros, so a missing coordinate contributes as 0. -/
def alignTo (xs : List Int) (n : Nat) : List Int :=
  xs.take n ++ List.replicate (n - xs.length) 0

@[grind, simp] lemma alignTo_length (xs : List Int) (n : Nat) :
    (alignTo xs n).length = n := by
  simp [alignTo, List.length_take, List.length_replicate]; omega

/- The squared Euclidean distance between two equally-positioned coordinate
   vectors: the sum of the squares of the per-coordinate differences, taken
   coordinate by coordinate. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern). On unequal lengths the surplus tail is
   dropped; callers align first so both vectors share a length. -/
def sumSqZip : List Int → List Int → Int
  | a :: u, b :: v => (a - b) ^ 2 + sumSqZip u v
  | _, _ => 0

@[grind] lemma sumSqZip_cons (a b : Int) (u v : List Int) :
    sumSqZip (a :: u) (b :: v) = (a - b) ^ 2 + sumSqZip u v := rfl

@[grind, simp] lemma sumSqZip_nil_left (v : List Int) : sumSqZip [] v = 0 := rfl

@[grind, simp] lemma sumSqZip_nil_right (u : List Int) : sumSqZip u [] = 0 := by
  cases u <;> rfl

/- The ambient dimension the two vectors are compared in. When the two points
   are of the same kind their coordinate counts already agree (`min = max`);
   when they are of different kinds the comparison is carried out in the larger
   ambient space, so the shorter vector is treated as embedded at the origin in
   the extra dimensions. -/
def commonLen (sameKind : Bool) (s q : List Int) : Nat :=
  if sameKind then min s.length q.length else max s.length q.length

/- The squared Euclidean distance: align both coordinate vectors to the common
   ambient dimension (zero-padding the shorter), then sum the squared
   per-coordinate differences. No coordinate is silently discarded. -/
def distSq (sameKind : Bool) (s q : List Int) : Int :=
  sumSqZip (alignTo s (commonLen sameKind s q)) (alignTo q (commonLen sameKind s q))

/- The backward-fold step: for two equal-length vectors, dropping one fewer
   element exposes the coordinate at index `i-1` on the front of both, so
   `sumSqZip` peels one squared-difference term. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma sumSqZip_drop_step (A B : List Int) (i : Nat)
    (hA : i ≤ A.length) (hAB : A.length = B.length) (hi : 0 < i) :
    sumSqZip (A.drop (i - 1)) (B.drop (i - 1))
      = (A[i-1]! - B[i-1]!) ^ 2 + sumSqZip (A.drop i) (B.drop i) := by
  have hltA : i - 1 < A.length := by omega
  have hltB : i - 1 < B.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  have hcA : A.drop (i - 1) = A[i-1]! :: A.drop i := by
    have h := List.drop_eq_getElem_cons hltA
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hltA, Option.getD_some, h, hsucc]
  have hcB : B.drop (i - 1) = B[i-1]! :: B.drop i := by
    have h := List.drop_eq_getElem_cons hltB
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hltB, Option.getD_some, h, hsucc]
  rw [hcA, hcB, sumSqZip_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method distanceSq (sameKind : Bool) (s : List Int) (q : List Int) return (out : Int)
  ensures out = distSq sameKind s q
  do
    -- impl-start
    let L := if sameKind then min s.length q.length else max s.length q.length
    let mut acc : Int := 0
    let mut i := L
    while i > 0
      invariant 0 ≤ i ∧ i ≤ L
      invariant acc = sumSqZip ((alignTo s L).drop i) ((alignTo q L).drop i)
      done_with i = 0
    do
      acc := ((alignTo s L)[i-1]! - (alignTo q L)[i-1]!) ^ 2 + acc
      i := i - 1
    return acc
    -- impl-end

prove_correct distanceSq by
  loom_solve
  · rw [sumSqZip_drop_step (alignTo s _) (alignTo q _) i (by simp_all) (by simp) (by omega)]
    simp_all
  · simp only [distSq, commonLen]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: method distanceSq with TOTAL postcondition `out = distSq sameKind s q` (no precondition). distSq = sumSqZip (alignTo s L) (alignTo q L), L=commonLen. No axioms, no deep_model_references (meta confirms axioms:[], deep_model_references:[]) — so the A-leg audit reduces to the model<->patch correspondence, which I verified 3 independent ways (below).

All files confirmed same_spec=True vs frozen Solution.lean (velvet spec_view collapses impl + prove_correct body). Verify via `bash scripts/lean_verify.sh <f>` (0=verifies,1=err,3=sorry,124=timeout).

BASELINES: positive_control.lean (gold model) -> EXIT 0 (verifies). prepatch.lean (min-truncation bug, L:=min, no alignment) -> EXIT 1 (bug reproduced: fails `out=distSq` on unequal lengths).

ATTACKS (8, >=5 floor met; 4 distinct wrong-impl families all correctly REJECTED because the postcondition is a total functional equation, leaving no behavioral slack):
- atk_1 min-truncation / partial-domain (L:=min, raw drops) -> EXIT 1 REJECTED.
- atk_2 boundary off-by-one (aligned[i]! instead of [i-1]!) -> EXIT 1 REJECTED.
- atk_3 control-flow effect (i:=i-2, skips coordinates) -> EXIT 1 REJECTED.
- atk_4 partial-domain (align s only, q raw) -> EXIT 1 REJECTED.
- atk_8 control-flow (i:=i non-decrementing, non-oracle) -> EXIT 1 REJECTED.
VERIFYING candidates (echo family):
- atk_5 ungrounded-oracle echo (`return distSq sameKind s q`) -> EXIT 0 VERIFIES.
- atk_6 divergent-loop partial-correctness escape (`acc := distSq ...; while i>0 do i:=i; return acc`) -> EXIT 0 VERIFIES. Adversarially interesting (termination "partial" -> a divergent loop can verify vacuously) but its only observable = distSq (correct); the added loop refines NO repo op (spurious, no callee) so its faithful patch is still the gold; treating partial-corr divergence as a break would void every velvet bundle.
- atk_7 correct fold variant (`return acc + 0`) -> EXIT 0 VERIFIES.

RESOLVE (mandatory step, EXECUTED, not speculated): all 3 verifying impls compute exactly distSq = the gold's squared distance, so each faithfully refines to the GOLD patch. run_resolve('sympy__sympy-11618', gold_patch, timeout=1200) -> RESOLVED=True, COMPLETED=True, NOTE='resolved'. Therefore all 3 are 'correct echoes' (verify AND patch resolves) — none is a spec weakness. No verifying impl's faithful patch fails to resolve.

MODEL<->PATCH FIDELITY (A-leg crux) verified independently inside the instance Docker image (mirror.gcr.io/swebench/sweb.eval.x86_64.sympy_1776_sympy-11618, gold patch git-applied): distSq shadow vs real patched Point.distance(p)**2 -> 3750 fuzzed integer-coord pairs (dims 1-5, both same/diff kind) with 0 mismatches, plus 8 targeted boundary cases (F2P Point3D(1,0,2) vs Point2D(2,0)=5, both longer/shorter directions, equal-len diff-kind, base-Point same-kind min-truncation) all matching. commonLen's min on same-kind matches gold's truncating zip; max on diff-kind matches the p1=[0]*max padding branch; alignTo = the p1 zero-extension.

REFINEMENT.MD LEG AUDIT: legs A1-A7 all tagged R (A1 args->List Int, A2 p.args, A3 sameKind<->type(p) is type(self), A7 sqrt injective on [0,inf) so squared pins distance) or I (A4 commonLen, A5 alignTo, A6 sumSqZip). No kind-3 (inexpressible-changed-op) legs: the operation that actually changed (zero-pad-shorter vs truncate) is modeled DEEPLY in pure arithmetic (alignTo+commonLen), not hidden behind an axiom. No axioms / no A-legs to check callee-correspondence for; the model-fidelity probe above discharges the R/I legs empirically.

FLOOR: 8 attacks (>=5), prepatch reproduced, positive control verifies & is distinct from all attacks. No confirmed break after running the required resolve on every verifying candidate.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit of the velvet model for sympy__sympy-11618 (Point.distance).

SPEC REGION: same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the VelvetBackend tables. Freshly computed region_hashes {pure, impl, spec_view} match meta.json exactly. Solution.lean verifies independently under lean_verify.sh (exit 0, ~6s).

MODEL vs REAL REPO: I transliterated the modeled ops (commonLen / alignTo / sumSqZip / distSq) to Python and diffed against the REAL gold-patched sympy.geometry.point.Point.distance**2 executed in the base_commit worktree (HEAD 360290c4c4, gold branch applied). The observable modeled is the squared distance (distance = sqrt(out); sqrt injective on [0,inf)), which sympy evaluates exactly for integer coordinates.

  - 30,000 fuzzed pairs over dims 1-6: 0 divergences.
  - 20,000 adversarial same-type-different-length base-Point cases, coords in [-50,50]: 0 divergences.
  - Same-type truncating-zip (min) path confirmed, e.g. Point([5]) vs Point([1,2,3,4]) -> real 16 == model 16 (sameKind=True).
  - Different-type zero-pad (max) path confirmed.
  - F2P boundary Point3D(1,0,2) vs Point2D(2,0): real dist^2 = 5 == model distSq = 5, sameKind=False. Matches.

The sameKind:Bool parameter faithfully carries `type(p) is type(self)`, which is determined by the coordinate-vector lengths given Point.__new__'s length dispatch (len 2->Point2D, 3->Point3D, else base Point). commonLen reproduces the exact ambient dimension each gold branch runs in (min for the same-type/equal-length truncating zip; max for the padding branch). No axioms in bundle; the changed operation is modeled deeply (no over-abstraction).

The spec is neither too strong nor drifting: within the R-refinement domain (integer coordinates, the domain G-CONF fuzzes) the modeled distSq agrees with the real callee on every tested input, and no diverging input was found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the actual consumer spec view via markers.spec_view (velvet) and ran leakage.screen against the frozen row: mechanical screen passes (no hard failures). same_spec(Solution, Solution_prepatch)=True, so the frozen spec region is byte-identical (only impl/proof differ). Semantic leakage review beyond the lexical screen:

Public problem_statement already discloses the full corrected behavior: method name `distance`; the failing example `Point(2,0).distance(Point(1,0,2))` -> 1; the diagnosis that 'the 3rd dimension is being ignored when the Points are zipped'; and the expected result sqrt(5) instead of sqrt((2-1)**2+(0-0)**2). So the desired fix (do not drop surplus coordinates; treat a missing coordinate as 0) is public.

Spec view contents: pure helpers alignTo (zero-pad shorter vector to target ambient dim), sumSqZip (sum of squared per-coord diffs), commonLen (min for same-kind, max for different-kind), distSq, and the contract `ensures out = distSq sameKind s q`; impl and prove_correct bodies are elided.

Leak checks: (L1) no diff markers, no reproduced gold-patch line (>=8 normalized chars); (L2) patched file path 'sympy/geometry/point.py' and its dotted module path do NOT appear in the view; the only distinctive patched symbol is `distance`, and although identifier `distanceSq` embeds it, `distance` is already public in the problem statement so it is exempt (and mechanically not flagged); (L3) no narration terms (bug/fix/wrong/broken/previously/incorrectly/regression/off-by-one) in any spec-view comment or docstring — comments are abstract behavioral descriptions of the math model. The zero-padding / min-vs-max modeling encodes exactly the corrected behavior the public problem statement already demands (embed shorter vector at origin in extra dimensions); this is legitimate behavioral specification, not disclosure of the gold edit's location, control-flow structure, or any specifics beyond the public task. The F2P numeric fact (sqrt(5)) is itself already in the problem statement. relaxed_leakage flag is unset; no relaxation invoked. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
