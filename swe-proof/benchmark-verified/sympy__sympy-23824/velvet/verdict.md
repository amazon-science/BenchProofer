# P2 adversarial audit — sympy__sympy-23824

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,17 +53,17 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
+let mut result : List Int := tail
+    let mut i := 0
+    while i < leading.length
       invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
+      invariant result = restoreSeq ((leading.take i).reverse) tail
+      done_with i = leading.length
+      decreasing leading.length - i
     do
-      let c := leading[i - 1]!
+      let c := leading[i]!
       result := c :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -82,6 +82,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return leading
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return tail ++ leading
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return leading.reverse ++ tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,10 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+if leading.length ≤ 1 then
+      return leading ++ tail
+    else
+      return tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +74,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return leading.drop 1 ++ tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return leading ++ leading ++ tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,16 +53,14 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
+let mut result : List Int := tail
     let mut i := leading.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
+      invariant result = tail
       done_with i = 0
       decreasing i
     do
-      let c := leading[i - 1]!
-      result := c :: result
       i := i - 1
     return result
     -- impl-end
@@ -82,6 +80,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,18 +53,7 @@
   ensures out = leading ++ tail
   do
     -- impl-start
-    let mut result : List Int := tail
-    let mut i := leading.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ leading.length
-      invariant result = restoreSeq (leading.drop i) tail
-      done_with i = 0
-      decreasing i
-    do
-      let c := leading[i - 1]!
-      result := c :: result
-      i := i - 1
-    return result
+    return leading.take 1 ++ tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -82,6 +71,4 @@
   rw [hcons, restoreSeq_cons]
 
 prove_correct restoreLeading by
-  loom_solve
-  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The restoration of a leading run in front of a core term, preserving the
   leading run's original left-to-right order: the front element of the leading
   run, followed by the restoration of the rest of the run onto the same term.
   Front-recursive (one unfold per leading element) so a backward loop that
   prepends one element per step can discharge it (the Velvet fold pattern,
   plan §5.4). This is the deep model of the leading-run restoration's net
   effect — spelled out as the order-preserving concatenation, not hidden behind
   a callee axiom. -/
def restoreSeq : List Int → List Int → List Int
  | [],      tail => tail
  | c :: cs, tail => c :: restoreSeq cs tail

@[grind] lemma restoreSeq_nil (tail : List Int) : restoreSeq [] tail = tail := rfl
@[grind] lemma restoreSeq_cons (c : Int) (cs tail : List Int) :
    restoreSeq (c :: cs) tail = c :: restoreSeq cs tail := rfl

/- The restoration is exactly the order-preserving concatenation of the leading
   run and the core term: the leading factors, in their original order, then the
   term. (Pins the postcondition to ordinary list concatenation.) -/
@[grind] lemma restoreSeq_eq_append (leading tail : List Int) :
    restoreSeq leading tail = leading ++ tail := by
  induction leading with
  | nil => rfl
  | cons c cs ih => simp [restoreSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restore a leading run of uncontracted factors in front of one core-result
   term, preserving the leading factors' original left-to-right order. The
   leading run is the factors that precede the first contracted factor (in the
   order they appear in the input); the core term is one additive term produced
   by the surrounding rewrite. The restored term is the leading run, in its
   original order, followed by the core term. Both inputs are read only — a
   fresh term is built and returned. -/
method restoreLeading (leading : List Int) (tail : List Int) return (out : List Int)
  ensures out = leading ++ tail
  do
    -- impl-start
    return leading ++ tail
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `restoreSeq` peels one head onto the front of its
   output. This is the single goal `loom_solve` leaves for the loop body. -/
lemma restoreSeq_drop_step (leading tail : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ leading.length) :
    restoreSeq (leading.drop (i - 1)) tail = leading[i - 1]! :: restoreSeq (leading.drop i) tail := by
  have hlt : i - 1 < leading.length := by omega
  have hcons : leading.drop (i - 1) = leading[i - 1]! :: leading.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, restoreSeq_cons]

prove_correct restoreLeading by
  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a single TOTAL functional postcondition `ensures out = leading ++ tail` over restoreLeading (leading tail : List Int); no preconditions, no axioms (axioms region empty; grep for `axiom `/`:|`/`sorry` = NONE), no oracle constant. Velvet spec_view collapses the impl region AND elides the prove_correct body, so impl+proof are attacker-controlled while same_spec stays True; the restoreSeq_drop_step lemma and all spec lines kept byte-identical. same_spec=True confirmed for all 12 files via swebench_unified.markers.same_spec (velvet backend).

Battery of 11 DISTINCT same-spec wrong impls + positive control, verified with `bash scripts/lean_verify.sh <f>`, run concurrently in 3 batches of 4:
- pos_control (`return leading ++ tail`, structurally distinct, no loop): EXIT=0 -> spec NON-VACUOUS.
- atk_1 prepatch bug reproduced (forward front-insert loop building reverse(leading)++tail): EXIT=1, fails invariant_2 + `ensures_1: out = leading ++ tail`.
- atk_2 `return tail` (ungrounded echo): EXIT=1, residual `tail = leading ++ tail`.
- atk_3 `return leading` (ungrounded echo): EXIT=1, residual `leading = leading ++ tail`.
- atk_4 `return tail ++ leading` (wrong order): EXIT=1, fails ensures_1.
- atk_5 `return leading.reverse ++ tail` (EXACT issue bug, direct): EXIT=1, residual `leading.reverse = leading`.
- atk_6 `return []`: EXIT=1, residual `[] = leading ++ tail`.
- atk_7 partial-domain (correct only if len<=1 else return tail): EXIT=1, residual `leading = []`.
- atk_8 boundary/off-by-one `leading.drop 1 ++ tail`: EXIT=1, fails ensures_1.
- atk_9 duplication `leading ++ leading ++ tail`: EXIT=1, fails ensures_1.
- atk_10 control-flow-effect (terminating loop that never mutates result; net no-op): EXIT=1, residual `leading = []` -- partial/demonic semantics do not let the no-op escape.
- atk_11 boundary `leading.take 1 ++ tail`: EXIT=1, fails ensures_1.
Every wrong impl fails genuinely at `case ensures_1: out = leading ++ tail` with an irreducible residual goal (verified by inspecting *.lean.out), not a tactic/syntax artifact.

RESOLVE STEP: conditional on a wrong impl VERIFYING. ZERO wrong impls verified, so there are no faithful refined patches to materialize/run through run_resolve; none is missing. patches={} accordingly.

REFINEMENT AUDIT (refinement.md A1-A5): all legs are R (List Int <-> Python list of integer gamma-factor index labels; Lean `++` <-> Python list `+`) or I (identical order-preserving concatenation). NO A-consumed, NO A-reference, NO kind-3, NO axioms. The only deep-model symbol restoreSeq is a PROVEN lemma (restoreSeq_eq_append: restoreSeq leading tail = leading ++ tail), not an ungrounded oracle/axiom, so there is no A-leg trust point to break. Model<->callee correspondence (pure list concatenation `free_pos[0:first_dum_pos] + ri`) holds and is independently confirmed by conformance_check.py (100009 inputs, 0 disagreements, seed 23824). G-AX vacuous.

CONCLUSION: verify => out = leading ++ tail => equals gold `free_pos[0:first_dum_pos] + ri` for each term; the surrounding comprehension applies this uniformly (unchanged R/I wrapper). No verify-but-incorrect gap. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The restoration of a leading run in front of a core term, preserving the
   leading run's original left-to-right order: the front element of the leading
   run, followed by the restoration of the rest of the run onto the same term.
   Front-recursive (one unfold per leading element) so a backward loop that
   prepends one element per step can discharge it (the Velvet fold pattern,
   plan §5.4). This is the deep model of the leading-run restoration's net
   effect — spelled out as the order-preserving concatenation, not hidden behind
   a callee axiom. -/
def restoreSeq : List Int → List Int → List Int
  | [],      tail => tail
  | c :: cs, tail => c :: restoreSeq cs tail

@[grind] lemma restoreSeq_nil (tail : List Int) : restoreSeq [] tail = tail := rfl
@[grind] lemma restoreSeq_cons (c : Int) (cs tail : List Int) :
    restoreSeq (c :: cs) tail = c :: restoreSeq cs tail := rfl

/- The restoration is exactly the order-preserving concatenation of the leading
   run and the core term: the leading factors, in their original order, then the
   term. (Pins the postcondition to ordinary list concatenation.) -/
@[grind] lemma restoreSeq_eq_append (leading tail : List Int) :
    restoreSeq leading tail = leading ++ tail := by
  induction leading with
  | nil => rfl
  | cons c cs ih => simp [restoreSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restore a leading run of uncontracted factors in front of one core-result
   term, preserving the leading factors' original left-to-right order. The
   leading run is the factors that precede the first contracted factor (in the
   order they appear in the input); the core term is one additive term produced
   by the surrounding rewrite. The restored term is the leading run, in its
   original order, followed by the core term. Both inputs are read only — a
   fresh term is built and returned. -/
method restoreLeading (leading : List Int) (tail : List Int) return (out : List Int)
  ensures out = leading ++ tail
  do
    -- impl-start
    return leading ++ tail
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `restoreSeq` peels one head onto the front of its
   output. This is the single goal `loom_solve` leaves for the loop body. -/
lemma restoreSeq_drop_step (leading tail : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ leading.length) :
    restoreSeq (leading.drop (i - 1)) tail = leading[i - 1]! :: restoreSeq (leading.drop i) tail := by
  have hlt : i - 1 < leading.length := by omega
  have hcons : leading.drop (i - 1) = leading[i - 1]! :: leading.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, restoreSeq_cons]

prove_correct restoreLeading by
  loom_solve <;> simp_all <;> (try omega) <;> (try grind)
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a single TOTAL functional postcondition `ensures out = leading ++ tail` over restoreLeading (leading tail : List Int); no preconditions, no axioms (axioms region empty; grep for `axiom `/`:|`/`sorry` = NONE), no oracle constant. Velvet spec_view collapses the impl region AND elides the prove_correct body, so impl+proof are attacker-controlled while same_spec stays True; the restoreSeq_drop_step lemma and all spec lines kept byte-identical. same_spec=True confirmed for all 12 files via swebench_unified.markers.same_spec (velvet backend).

Battery of 11 DISTINCT same-spec wrong impls + positive control, verified with `bash scripts/lean_verify.sh <f>`, run concurrently in 3 batches of 4:
- pos_control (`return leading ++ tail`, structurally distinct, no loop): EXIT=0 -> spec NON-VACUOUS.
- atk_1 prepatch bug reproduced (forward front-insert loop building reverse(leading)++tail): EXIT=1, fails invariant_2 + `ensures_1: out = leading ++ tail`.
- atk_2 `return tail` (ungrounded echo): EXIT=1, residual `tail = leading ++ tail`.
- atk_3 `return leading` (ungrounded echo): EXIT=1, residual `leading = leading ++ tail`.
- atk_4 `return tail ++ leading` (wrong order): EXIT=1, fails ensures_1.
- atk_5 `return leading.reverse ++ tail` (EXACT issue bug, direct): EXIT=1, residual `leading.reverse = leading`.
- atk_6 `return []`: EXIT=1, residual `[] = leading ++ tail`.
- atk_7 partial-domain (correct only if len<=1 else return tail): EXIT=1, residual `leading = []`.
- atk_8 boundary/off-by-one `leading.drop 1 ++ tail`: EXIT=1, fails ensures_1.
- atk_9 duplication `leading ++ leading ++ tail`: EXIT=1, fails ensures_1.
- atk_10 control-flow-effect (terminating loop that never mutates result; net no-op): EXIT=1, residual `leading = []` -- partial/demonic semantics do not let the no-op escape.
- atk_11 boundary `leading.take 1 ++ tail`: EXIT=1, fails ensures_1.
Every wrong impl fails genuinely at `case ensures_1: out = leading ++ tail` with an irreducible residual goal (verified by inspecting *.lean.out), not a tactic/syntax artifact.

RESOLVE STEP: conditional on a wrong impl VERIFYING. ZERO wrong impls verified, so there are no faithful refined patches to materialize/run through run_resolve; none is missing. patches={} accordingly.

REFINEMENT AUDIT (refinement.md A1-A5): all legs are R (List Int <-> Python list of integer gamma-factor index labels; Lean `++` <-> Python list `+`) or I (identical order-preserving concatenation). NO A-consumed, NO A-reference, NO kind-3, NO axioms. The only deep-model symbol restoreSeq is a PROVEN lemma (restoreSeq_eq_append: restoreSeq leading tail = leading ++ tail), not an ungrounded oracle/axiom, so there is no A-leg trust point to break. Model<->callee correspondence (pure list concatenation `free_pos[0:first_dum_pos] + ri`) holds and is independently confirmed by conformance_check.py (100009 inputs, 0 disagreements, seed 23824). G-AX vacuous.

CONCLUSION: verify => out = leading ++ tail => equals gold `free_pos[0:first_dum_pos] + ri` for each term; the surrounding comprehension applies this uniformly (unchanged R/I wrapper). No verify-but-incorrect gap. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for velvet/sympy__sympy-23824, restoreLeading.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean) = True under swebench_unified.markers with the velvet backend — the spec region (method signature, `ensures out = leading ++ tail`, pure helpers restoreSeq + lemmas, empty pre/post regions) is byte-identical; only the impl-start/impl-end body and prove_correct proof differ. Solution.lean verifies via lean_verify.sh (exit 0).

Modeled function vs real callee: spec postcondition is `out = leading ++ tail` with NO precondition (total, applies to all inputs). Real repo at base_commit (39de9a2) gamma_matrices.py:697 gold hunk is `resulting_indices = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )`. Per mapping.md, leading = free_pos[0:first_dum_pos], tail = ri; the per-term operation is Python list `+` = order-preserving concatenation. Lean `List Int` `++` ↔ Python list `+` over integer index labels is an exact total bijection.

Drift search: I looked for any input where the spec disagrees with the real callee. For every (leading, tail) both sides produce leading (original order) followed by tail. The comprehension wrapper applies the identical per-term map uniformly, so modeling one representative ri captures the full observable change (unchanged structural map). No narrowing precondition, so the spec is not stronger than the callee's domain, and no relaxation either. conformance_check.py (G-CONF) confirms: 0 disagreements over 100009 fuzzed inputs (seed 23824), including empty leading/tail, single/multi leading, the F2P witness [rho,sigma], and reversed cases.

No diverging input exists. The spec is neither too strong nor drifted from real repo behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view for restoreLeading models only the publicly-stated required behavior: prepend the leading uncontracted run in original left-to-right order (ensures out = leading ++ tail). The problem_statement already fully discloses this — 'Leading gamma matrices without contractions should be unaffected... prepended in reverse order [is the bug]' and 'the insertion loop is just backward.' So the spec's order-preserving concatenation semantics leaks nothing beyond the public task. Mechanical leakage.screen PASSED (no hard failures). No diff markers, no gold-patch line reproduced, no patched file path (sympy/physics/hep/gamma_matrices.py) or dotted module path in the view. No repo-specific identifiers present (free_pos, first_dum_pos, resulting_indices, kahane, gamma, ri.insert all absent); abstraction is generic List Int. same_spec(Solution, Solution_prepatch)=True — spec region byte-identical, the order differentiator lives only in the elided impl/proof regions. The single occurrence of 'backward' is in restoreSeq_drop_step's comment describing the Lean fold's loop direction, not narrating the Python bug, and is not narration-flagged nor part of problem-statement-exclusive info. No relaxed_leakage flag / no RELAXED_LEAKAGE.md; strict judgment. G-LEAK meta status 'pass' corroborated independently.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
