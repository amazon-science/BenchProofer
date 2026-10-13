# P2 adversarial audit — sympy__sympy-22714

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.lean`, `atk_6.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl was found whose faithful refined patch fails to resolve. The strongest candidate was atk_6 (swapped conjunct order `c.imagNonzero && c.numeric`): Lean `&&` is total and commutative so it VERIFIES against the frozen spec, but its faithful Python refinement `any(im(a).is_zero is False and a.is_number ...)` LOSES the short-circuit that protects `im(a)` from non-Expr coordinates. Real divergence exists and was demonstrated: with coords `(Basic(), Basic())`, `(Tuple(1,2), 2)`, `FiniteSet`, `Interval`, `S.Reals`, `Eq(x,1)`, `S.true`, `Range(3)` the gold predicate short-circuits to False (constructor then raises the intended `TypeError('Coordinates must be valid SymPy expressions.')`) whereas the swapped predicate raises out of `im(a)` early. This divergence is NOT observable by the official test set: every such `im()` failure is itself a `TypeError` (verified for all 10 probe objects), and the one P2P assertion that reaches this path — `raises(TypeError, lambda: Point(Basic(), Basic()))` at sympy/geometry/tests/test_point.py:437 in `test_arguments` (PASS_TO_PASS) — accepts any TypeError, so it still passes. Confirmed by executed resolve: RESOLVED.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,6 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -96,7 +92,7 @@
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      result := (c.numeric && c.imagPresent) || result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,9 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
+    if coords.length > 2 then
+      return false
+    else
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -118,5 +117,7 @@
 
 prove_correct imaginaryCoordCheck by
   loom_solve
-  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [anyImaginary_drop_step coords i (by omega) (by omega)])
+  all_goals (try simp_all [coordImaginary, anyImaginary])
+  all_goals (try grind)
+  all_goals (try omega)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,12 +83,8 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
-    let mut i := coords.length
+    let mut i := coords.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ coords.length
       invariant result = anyImaginary (coords.drop i)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,6 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -96,7 +92,9 @@
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      if c.numeric then
+        result := true
+        break
       i := i - 1
     return result
     -- impl-end
@@ -118,5 +116,7 @@
 
 prove_correct imaginaryCoordCheck by
   loom_solve
-  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [anyImaginary_drop_step coords i (by omega) (by omega)])
+  all_goals (try simp_all [coordImaginary, anyImaginary])
+  all_goals (try grind)
+  all_goals (try omega)
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,22 +83,7 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
-    let mut result : Bool := false
-    let mut i := coords.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ coords.length
-      invariant result = anyImaginary (coords.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := coords[i - 1]!
-      result := coordImaginary c || result
-      i := i - 1
-    return result
+    return anyImaginary coords
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -118,5 +103,3 @@
 
 prove_correct imaginaryCoordCheck by
   loom_solve
-  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,10 +83,6 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -96,7 +92,7 @@
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      result := (c.imagNonzero && c.numeric) || result
       i := i - 1
     return result
     -- impl-end
@@ -119,4 +115,4 @@
 prove_correct imaginaryCoordCheck by
   loom_solve
   rw [anyImaginary_drop_step coords i (by omega) (by omega)]
-  simp_all
+  simp_all [coordImaginary, Bool.and_comm]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,20 +83,15 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
-    let mut result : Bool := false
+    let mut result : Bool := true
     let mut i := coords.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ coords.length
-      invariant result = anyImaginary (coords.drop i)
       done_with i = 0
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      result := coordImaginary c && result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,6 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -96,7 +92,8 @@
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      if c.numeric && c.imagNonzero then
+        result := true
       i := i - 1
     return result
     -- impl-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,22 +83,18 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
-    let mut result : Bool := false
+    let mut acc : Bool := true
     let mut i := coords.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ coords.length
-      invariant result = anyImaginary (coords.drop i)
+      invariant acc = !anyImaginary (coords.drop i)
       done_with i = 0
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      acc := acc && !(coordImaginary c)
       i := i - 1
-    return result
+    return !acc
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,10 +83,6 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -96,7 +92,7 @@
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      result := (c.imagNonzero && c.numeric) || (c.numeric && c.imagNonzero) || result
       i := i - 1
     return result
     -- impl-end
@@ -119,4 +115,4 @@
 prove_correct imaginaryCoordCheck by
   loom_solve
   rw [anyImaginary_drop_step coords i (by omega) (by omega)]
-  simp_all
+  simp_all [coordImaginary, Bool.and_comm]
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,9 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
+    if coords.length = 0 then
+      return true
+    else
     let mut result : Bool := false
     let mut i := coords.length
     while i > 0
@@ -118,5 +117,7 @@
 
 prove_correct imaginaryCoordCheck by
   loom_solve
-  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [anyImaginary_drop_step coords i (by omega) (by omega)])
+  all_goals (try simp_all [coordImaginary, anyImaginary])
+  all_goals (try grind)
+  all_goals (try omega)
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,20 +83,19 @@
   ensures out = anyImaginary coords
   do
     -- impl-start
-    -- Walk the coordinate list and accumulate the disjunction of the
-    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
-    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
-    -- a real coordinate with an unsimplified imaginary part is accepted.
     let mut result : Bool := false
     let mut i := coords.length
+    let mut stop : Bool := false
     while i > 0
       invariant 0 ≤ i ∧ i ≤ coords.length
-      invariant result = anyImaginary (coords.drop i)
       done_with i = 0
       decreasing i
     do
       let c := coords[i - 1]!
-      result := coordImaginary c || result
+      if !stop then
+        result := coordImaginary c || result
+        if c.numeric then
+          stop := true
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model of an outside callee.
--  The decision modeled here is a self-contained per-element predicate over a
--  list of coordinate observations; it is spelled out DEEPLY in the `pure`
--  region below. The queries used to obtain each coordinate's observations are
--  unchanged and are not separately modeled — their results ARE the fields of
--  `Coord`. There is no `axiom` declaration.)
-- axioms-end

-- pure-start
/- The observations the admissibility decision can make about a single
   coordinate of a candidate point. A coordinate is abstracted to three
   independent booleans:

     * `numeric`      — the coordinate is a concrete number (as opposed to a
                        symbolic/undetermined expression);
     * `imagNonzero`  — the coordinate's imaginary part is *rigorously*
                        determined to be nonzero (a strict, three-valued
                        judgement: it is true only when the imaginary part is
                        provably not zero, and false when the imaginary part is
                        provably zero OR cannot be decided);
     * `imagPresent`  — a *coarse* indicator that the coordinate carries a
                        non-trivial imaginary-part object. It can be true even
                        for a coordinate whose imaginary part is in fact zero,
                        when that zero is left in an unsimplified form rather
                        than reduced to the literal zero object.

   `imagNonzero` and `imagPresent` are deliberately distinct: a real coordinate
   whose imaginary part is carried unsimplified has `imagNonzero = false` but
   `imagPresent = true`. The admissibility decision below consults only
   `numeric` and `imagNonzero`. -/
structure Coord where
  numeric     : Bool
  imagNonzero : Bool
  imagPresent : Bool
  deriving Inhabited, DecidableEq

/- A single coordinate counts as imaginary for the admissibility check exactly
   when it is a concrete number AND its imaginary part is rigorously determined
   to be nonzero. A coordinate whose imaginary part cannot be decided, or is
   only coarsely "present" but not provably nonzero, does NOT count. -/
def coordImaginary (c : Coord) : Bool :=
  c.numeric && c.imagNonzero

/- Whether ANY coordinate of the list counts as imaginary — the disjunction the
   admissibility guard evaluates over the coordinate sequence. Front-recursive so
   a single unfold is available per loop step (the backward-fold pattern). -/
def anyImaginary : List Coord → Bool
  | []      => false
  | c :: cs => coordImaginary c || anyImaginary cs

@[grind] lemma anyImaginary_nil : anyImaginary [] = false := rfl
@[grind] lemma anyImaginary_cons (c : Coord) (cs : List Coord) :
    anyImaginary (c :: cs) = (coordImaginary c || anyImaginary cs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a candidate point's coordinate list must be rejected as
   having an imaginary coordinate. The desired behavior: reject (return `true`)
   exactly when some coordinate is a concrete number whose imaginary part is
   rigorously determined to be nonzero; otherwise accept (return `false`). In
   particular a real coordinate must be ACCEPTED even when its imaginary part
   happens to be carried in an unsimplified, non-reduced form — a coordinate is
   never rejected merely because a coarse "imaginary part present" indicator is
   set; rejection requires the imaginary part to be provably nonzero.

   `coords` is the read-only coordinate list (not `mut`): the decision inspects
   it and mutates no input (directive 5). -/
method imaginaryCoordCheck (coords : List Coord) return (out : Bool)
  ensures out = anyImaginary coords
  do
    -- impl-start
    -- Walk the coordinate list and accumulate the disjunction of the
    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
    -- a real coordinate with an unsimplified imaginary part is accepted.
    let mut result : Bool := false
    let mut i := coords.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ coords.length
      invariant result = anyImaginary (coords.drop i)
      done_with i = 0
      decreasing i
    do
      let c := coords[i - 1]!
      result := coordImaginary c || result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyImaginary` peels one `coordImaginary`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma anyImaginary_drop_step (coords : List Coord) (i : Nat)
    (hi : 0 < i) (hle : i ≤ coords.length) :
    anyImaginary (coords.drop (i - 1))
      = (coordImaginary coords[i - 1]! || anyImaginary (coords.drop i)) := by
  have hlt : i - 1 < coords.length := by omega
  have hcons : coords.drop (i - 1) = coords[i - 1]! :: coords.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyImaginary_cons]

prove_correct imaginaryCoordCheck by
  loom_solve
  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SETUP CORRECTION: the project root given in the prompt is permission-denied for this user; the live tree (scripts/lean_verify.sh, src/swebench_unified). All commands below were run from there. The bundle dir also has NO patch.diff (only the instance-level benchmark-verified/sympy__sympy-22714/patch.diff exists) — worth flagging for G-RESOLVE, which returns "patch.diff missing" for a bundle lacking it.

SPEC/FREEZE ANALYSIS. For velvet, spec_view elides ONLY the impl region and the prove_correct tactic body; the `pure` region (structure Coord, coordImaginary, anyImaginary, the two @[grind] lemmas), the `ensures out = anyImaginary coords` clause, AND the top-level lemma anyImaginary_drop_step are all FROZEN. Loop invariants live inside the impl region and are therefore consumer-supplied, so attacks were free to retune invariants and proofs — I did so (best-effort tactic `loom_solve; all_goals (try rw [...]); try simp_all; try grind; try omega`) to avoid scoring mere tactic mismatches as spec strength.

SAME-SPEC: all 12 attacks + positive_control + prepatch confirmed True via swebench_unified.markers.same_spec (velvet tables).

POSITIVE CONTROL: positive_control.lean (byte copy of shipped Solution.lean) — `bash scripts/lean_verify.sh <f>` → exit 0.
PREPATCH REPRODUCED: atk_1 re-encodes the historical bug (`c.numeric && c.imagPresent`) → exit 1, unsolved goal on the ensures. Real-repo confirmation at base: `with sp.evaluate(False): sp.S('Point2D(Integer(1),Integer(2))')` → ValueError: Imaginary coordinates are not permitted. And for that coord, is_number=True, bool(im(a))=True (imagPresent), im(a).is_zero=True so imagNonzero=False — exactly the frozen model's discriminator.

### ATTACK RESULTS (command: bash scripts/lean_verify.sh atk_N.lean; run 4-way concurrently in background batches):
- atk_1 coarse-flag prepatch bug → exit 1 (REJECTED, semantic)
- atk_2 partial domain (accept-all when length>2) → exit 1; goal `if_pos : 2 < coords.length ⊢ anyImaginary coords = false`
- atk_3 boundary/off-by-one (never inspects last coord, starts i = length-1) → exit 1
- atk_4 control-flow effect (break with result:=true on first NUMERIC coord) → exit 1; goal `(coords[i-1]?.getD default).numeric = true ⊢ anyImaginary (List.drop i coords) = true`
- atk_5 ungrounded-oracle echo (`return anyImaginary coords`) → exit 0 VERIFIES
- atk_6 swapped conjuncts (`c.imagNonzero && c.numeric`) → exit 0 VERIFIES
- atk_7 aggregation swap (all instead of any) → exit 1
- atk_8 if-then result:=true forward variant with frozen proof → exit 1 (tactic-shape, retained as a rejected variant)
- atk_9 De Morgan via all + negated accumulator → exit 1
- atk_10 redundant disjunction of both conjunct orders → exit 0 VERIFIES
- atk_11 boundary (over-reject empty list) → exit 1; goal `if_pos : coords = [] ⊢ False`
- atk_12 control-flow effect (stop scanning after first numeric) → exit 1
Net: 12 distinct same-spec wrong/variant impls, 9 REJECTED on genuine semantic goals, 3 VERIFY.

MANDATORY RESOLVE RUNS — all 3 verifying impls had their faithful refined patch materialized and EXECUTED through the official harness (swebench_unified.harness.run_resolve, instance sympy__sympy-22714, image swebench/sweb.eval.x86_64.sympy_1776_sympy-22714:latest, timeout 1800):
- atk_5.patch → {"completed": true, "resolved": true, "note": "resolved", "attempts": 1, "flaky": false}  (refines to exactly the gold predicate — sanity check that the plumbing reports resolved)
- atk_6.patch → {"completed": true, "resolved": true, "note": "resolved", "attempts": 1, "flaky": false}
- atk_10.patch → {"completed": true, "resolved": true, "note": "resolved", "attempts": 1, "flaky": false}
No verifying wrong impl's faithful patch failed to resolve ⇒ no verify⇏correct witness. Also corroborated locally in a git worktree at base_commit 3ff4717b6aef6086e78f01cdfa06f64ae23aed7e with the official test_patch applied: `python3 -m pytest sympy/geometry/tests/test_point.py -q` → 13 passed for both atk_6 and atk_10.

REFINEMENT.MD AUDIT (§4 legs). meta.json declares axioms=[] and deep_model_references=[]; grep confirms NO `axiom` declaration in Solution.lean. So there are no A-consumed and no A-reference legs to discharge — the changed decision is modeled DEEPLY in the frozen `pure` region (coordImaginary = numeric && imagNonzero). Legs as tagged: A1 R (coords tuple ↔ List Coord), A2 R+I (per-element predicate ↔ `a.is_number and im(a).is_zero is False`), A3 I (any ↔ front-recursive || fold; backward loop computes the same disjunction — order-insensitive), A4 R (out=true ↔ the ValueError raise). Every leg is R or I; NO kind-3 (inexpressible-changed-op) leg, matching §C of refinement.md. The claim in §C that the two consulted SymPy queries are unchanged by the patch is correct — the patch only rewrites the guard expression, not `is_number` or `im`.

MODEL↔PATCH CORRESPONDENCE (independently re-derived, gold patch applied in the worktree): abstracting each real coordinate as numeric=bool(a.is_number), imagNonzero=(im(a).is_zero is False) and evaluating `anyImaginary`, I compared the model's prediction against the REAL patched constructor's raise/no-raise of 'Imaginary coordinates are not permitted' over 4000 random 2-4-tuples (seed 22714; pool Integer/Rational/Float/I/2I/1+I/sqrt(2)/sqrt(-2)/pi/oo/zoo/nan/real, imaginary, complex symbols/x+I/3x): 0 mismatches. Against the UNPATCHED base the same abstraction mismatches 628/4000 — i.e. the model discriminates pre- from post-patch behavior in the right direction.

RESIDUAL RISK (advisory, not a gate failure). The one real fidelity gap is that Lean's `&&` is total and commutative while the refined Python `and` short-circuits, so conjunct ORDER is unconstrained by the frozen spec (atk_6/atk_10 verify). The frozen `Coord` abstraction cannot express "evaluating imagNonzero on a non-numeric coordinate diverges", because imagNonzero is a plain Bool field rather than an option/partial value. This is a genuine expressiveness limitation of the abstraction, and it does hide a real behavioral difference in the repo (im() raising on non-Expr coords). It does not break this instance because every such failure is a TypeError and the only P2P assertion on that path, `raises(TypeError, lambda: Point(Basic(), Basic()))`, is satisfied by any TypeError — verified by executed resolve, not speculation. A stricter spec would model the coordinate observation as three-valued/partial. Flagging for the plan's records; on the stated pass criteria (a verifying wrong impl whose faithful patch does NOT resolve) nothing breaks, so: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.lean`, `atk_6.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl was found whose faithful refined patch fails to resolve. The strongest candidate was atk_6 (swapped conjunct order `c.imagNonzero && c.numeric`): Lean `&&` is total and commutative so it VERIFIES against the frozen spec, but its faithful Python refinement `any(im(a).is_zero is False and a.is_number ...)` LOSES the short-circuit that protects `im(a)` from non-Expr coordinates. Real divergence exists and was demonstrated: with coords `(Basic(), Basic())`, `(Tuple(1,2), 2)`, `FiniteSet`, `Interval`, `S.Reals`, `Eq(x,1)`, `S.true`, `Range(3)` the gold predicate short-circuits to False (constructor then raises the intended `TypeError('Coordinates must be valid SymPy expressions.')`) whereas the swapped predicate raises out of `im(a)` early. This divergence is NOT observable by the official test set: every such `im()` failure is itself a `TypeError` (verified for all 10 probe objects), and the one P2P assertion that reaches this path — `raises(TypeError, lambda: Point(Basic(), Basic()))` at sympy/geometry/tests/test_point.py:437 in `test_arguments` (PASS_TO_PASS) — accepts any TypeError, so it still passes. Confirmed by executed resolve: RESOLVED.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model of an outside callee.
--  The decision modeled here is a self-contained per-element predicate over a
--  list of coordinate observations; it is spelled out DEEPLY in the `pure`
--  region below. The queries used to obtain each coordinate's observations are
--  unchanged and are not separately modeled — their results ARE the fields of
--  `Coord`. There is no `axiom` declaration.)
-- axioms-end

-- pure-start
/- The observations the admissibility decision can make about a single
   coordinate of a candidate point. A coordinate is abstracted to three
   independent booleans:

     * `numeric`      — the coordinate is a concrete number (as opposed to a
                        symbolic/undetermined expression);
     * `imagNonzero`  — the coordinate's imaginary part is *rigorously*
                        determined to be nonzero (a strict, three-valued
                        judgement: it is true only when the imaginary part is
                        provably not zero, and false when the imaginary part is
                        provably zero OR cannot be decided);
     * `imagPresent`  — a *coarse* indicator that the coordinate carries a
                        non-trivial imaginary-part object. It can be true even
                        for a coordinate whose imaginary part is in fact zero,
                        when that zero is left in an unsimplified form rather
                        than reduced to the literal zero object.

   `imagNonzero` and `imagPresent` are deliberately distinct: a real coordinate
   whose imaginary part is carried unsimplified has `imagNonzero = false` but
   `imagPresent = true`. The admissibility decision below consults only
   `numeric` and `imagNonzero`. -/
structure Coord where
  numeric     : Bool
  imagNonzero : Bool
  imagPresent : Bool
  deriving Inhabited, DecidableEq

/- A single coordinate counts as imaginary for the admissibility check exactly
   when it is a concrete number AND its imaginary part is rigorously determined
   to be nonzero. A coordinate whose imaginary part cannot be decided, or is
   only coarsely "present" but not provably nonzero, does NOT count. -/
def coordImaginary (c : Coord) : Bool :=
  c.numeric && c.imagNonzero

/- Whether ANY coordinate of the list counts as imaginary — the disjunction the
   admissibility guard evaluates over the coordinate sequence. Front-recursive so
   a single unfold is available per loop step (the backward-fold pattern). -/
def anyImaginary : List Coord → Bool
  | []      => false
  | c :: cs => coordImaginary c || anyImaginary cs

@[grind] lemma anyImaginary_nil : anyImaginary [] = false := rfl
@[grind] lemma anyImaginary_cons (c : Coord) (cs : List Coord) :
    anyImaginary (c :: cs) = (coordImaginary c || anyImaginary cs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a candidate point's coordinate list must be rejected as
   having an imaginary coordinate. The desired behavior: reject (return `true`)
   exactly when some coordinate is a concrete number whose imaginary part is
   rigorously determined to be nonzero; otherwise accept (return `false`). In
   particular a real coordinate must be ACCEPTED even when its imaginary part
   happens to be carried in an unsimplified, non-reduced form — a coordinate is
   never rejected merely because a coarse "imaginary part present" indicator is
   set; rejection requires the imaginary part to be provably nonzero.

   `coords` is the read-only coordinate list (not `mut`): the decision inspects
   it and mutates no input (directive 5). -/
method imaginaryCoordCheck (coords : List Coord) return (out : Bool)
  ensures out = anyImaginary coords
  do
    -- impl-start
    -- Walk the coordinate list and accumulate the disjunction of the
    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
    -- a real coordinate with an unsimplified imaginary part is accepted.
    let mut result : Bool := false
    let mut i := coords.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ coords.length
      invariant result = anyImaginary (coords.drop i)
      done_with i = 0
      decreasing i
    do
      let c := coords[i - 1]!
      result := coordImaginary c || result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyImaginary` peels one `coordImaginary`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma anyImaginary_drop_step (coords : List Coord) (i : Nat)
    (hi : 0 < i) (hle : i ≤ coords.length) :
    anyImaginary (coords.drop (i - 1))
      = (coordImaginary coords[i - 1]! || anyImaginary (coords.drop i)) := by
  have hlt : i - 1 < coords.length := by omega
  have hcons : coords.drop (i - 1) = coords[i - 1]! :: coords.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyImaginary_cons]

prove_correct imaginaryCoordCheck by
  loom_solve
  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SETUP CORRECTION: the project root given in the prompt is permission-denied for this user; the live tree (scripts/lean_verify.sh, src/swebench_unified). All commands below were run from there. The bundle dir also has NO patch.diff (only the instance-level benchmark-verified/sympy__sympy-22714/patch.diff exists) — worth flagging for G-RESOLVE, which returns "patch.diff missing" for a bundle lacking it.

SPEC/FREEZE ANALYSIS. For velvet, spec_view elides ONLY the impl region and the prove_correct tactic body; the `pure` region (structure Coord, coordImaginary, anyImaginary, the two @[grind] lemmas), the `ensures out = anyImaginary coords` clause, AND the top-level lemma anyImaginary_drop_step are all FROZEN. Loop invariants live inside the impl region and are therefore consumer-supplied, so attacks were free to retune invariants and proofs — I did so (best-effort tactic `loom_solve; all_goals (try rw [...]); try simp_all; try grind; try omega`) to avoid scoring mere tactic mismatches as spec strength.

SAME-SPEC: all 12 attacks + positive_control + prepatch confirmed True via swebench_unified.markers.same_spec (velvet tables).

POSITIVE CONTROL: positive_control.lean (byte copy of shipped Solution.lean) — `bash scripts/lean_verify.sh <f>` → exit 0.
PREPATCH REPRODUCED: atk_1 re-encodes the historical bug (`c.numeric && c.imagPresent`) → exit 1, unsolved goal on the ensures. Real-repo confirmation at base: `with sp.evaluate(False): sp.S('Point2D(Integer(1),Integer(2))')` → ValueError: Imaginary coordinates are not permitted. And for that coord, is_number=True, bool(im(a))=True (imagPresent), im(a).is_zero=True so imagNonzero=False — exactly the frozen model's discriminator.

### ATTACK RESULTS (command: bash scripts/lean_verify.sh atk_N.lean; run 4-way concurrently in background batches):
- atk_1 coarse-flag prepatch bug → exit 1 (REJECTED, semantic)
- atk_2 partial domain (accept-all when length>2) → exit 1; goal `if_pos : 2 < coords.length ⊢ anyImaginary coords = false`
- atk_3 boundary/off-by-one (never inspects last coord, starts i = length-1) → exit 1
- atk_4 control-flow effect (break with result:=true on first NUMERIC coord) → exit 1; goal `(coords[i-1]?.getD default).numeric = true ⊢ anyImaginary (List.drop i coords) = true`
- atk_5 ungrounded-oracle echo (`return anyImaginary coords`) → exit 0 VERIFIES
- atk_6 swapped conjuncts (`c.imagNonzero && c.numeric`) → exit 0 VERIFIES
- atk_7 aggregation swap (all instead of any) → exit 1
- atk_8 if-then result:=true forward variant with frozen proof → exit 1 (tactic-shape, retained as a rejected variant)
- atk_9 De Morgan via all + negated accumulator → exit 1
- atk_10 redundant disjunction of both conjunct orders → exit 0 VERIFIES
- atk_11 boundary (over-reject empty list) → exit 1; goal `if_pos : coords = [] ⊢ False`
- atk_12 control-flow effect (stop scanning after first numeric) → exit 1
Net: 12 distinct same-spec wrong/variant impls, 9 REJECTED on genuine semantic goals, 3 VERIFY.

MANDATORY RESOLVE RUNS — all 3 verifying impls had their faithful refined patch materialized and EXECUTED through the official harness (swebench_unified.harness.run_resolve, instance sympy__sympy-22714, image swebench/sweb.eval.x86_64.sympy_1776_sympy-22714:latest, timeout 1800):
- atk_5.patch → {"completed": true, "resolved": true, "note": "resolved", "attempts": 1, "flaky": false}  (refines to exactly the gold predicate — sanity check that the plumbing reports resolved)
- atk_6.patch → {"completed": true, "resolved": true, "note": "resolved", "attempts": 1, "flaky": false}
- atk_10.patch → {"completed": true, "resolved": true, "note": "resolved", "attempts": 1, "flaky": false}
No verifying wrong impl's faithful patch failed to resolve ⇒ no verify⇏correct witness. Also corroborated locally in a git worktree at base_commit 3ff4717b6aef6086e78f01cdfa06f64ae23aed7e with the official test_patch applied: `python3 -m pytest sympy/geometry/tests/test_point.py -q` → 13 passed for both atk_6 and atk_10.

REFINEMENT.MD AUDIT (§4 legs). meta.json declares axioms=[] and deep_model_references=[]; grep confirms NO `axiom` declaration in Solution.lean. So there are no A-consumed and no A-reference legs to discharge — the changed decision is modeled DEEPLY in the frozen `pure` region (coordImaginary = numeric && imagNonzero). Legs as tagged: A1 R (coords tuple ↔ List Coord), A2 R+I (per-element predicate ↔ `a.is_number and im(a).is_zero is False`), A3 I (any ↔ front-recursive || fold; backward loop computes the same disjunction — order-insensitive), A4 R (out=true ↔ the ValueError raise). Every leg is R or I; NO kind-3 (inexpressible-changed-op) leg, matching §C of refinement.md. The claim in §C that the two consulted SymPy queries are unchanged by the patch is correct — the patch only rewrites the guard expression, not `is_number` or `im`.

MODEL↔PATCH CORRESPONDENCE (independently re-derived, gold patch applied in the worktree): abstracting each real coordinate as numeric=bool(a.is_number), imagNonzero=(im(a).is_zero is False) and evaluating `anyImaginary`, I compared the model's prediction against the REAL patched constructor's raise/no-raise of 'Imaginary coordinates are not permitted' over 4000 random 2-4-tuples (seed 22714; pool Integer/Rational/Float/I/2I/1+I/sqrt(2)/sqrt(-2)/pi/oo/zoo/nan/real, imaginary, complex symbols/x+I/3x): 0 mismatches. Against the UNPATCHED base the same abstraction mismatches 628/4000 — i.e. the model discriminates pre- from post-patch behavior in the right direction.

RESIDUAL RISK (advisory, not a gate failure). The one real fidelity gap is that Lean's `&&` is total and commutative while the refined Python `and` short-circuits, so conjunct ORDER is unconstrained by the frozen spec (atk_6/atk_10 verify). The frozen `Coord` abstraction cannot express "evaluating imagNonzero on a non-numeric coordinate diverges", because imagNonzero is a plain Bool field rather than an option/partial value. This is a genuine expressiveness limitation of the abstraction, and it does hide a real behavioral difference in the repo (im() raising on non-Expr coords). It does not break this instance because every such failure is a TypeError and the only P2P assertion on that path, `raises(TypeError, lambda: Point(Basic(), Basic()))`, is satisfied by any TypeError — verified by executed resolve, not speculation. A stricter spec would model the coordinate observation as three-valued/partial. Flagging for the plan's records; on the stated pass criteria (a verifying wrong impl whose faithful patch does NOT resolve) nothing breaks, so: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness-break) on sympy__sympy-22714. Attacked the spec as too-strong / drifted from real repo behavior. Found no diverging input; verdict FAITHFUL.

SETUP / HYGIENE
- same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers.same_spec with the velvet backend tables. Region hashes: pure=bb59dc70..., impl=d3b3d27b..., spec_view=679a7f74.... The frozen spec region is byte-identical between the two skeletons; only impl differs (prepatch uses c.numeric && c.imagPresent).
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (elaborates, no sorry/error).
- patch.diff is the gold hunk verbatim: point.py:153 `any(a.is_number and im(a) for a in coords)` -> `any(a.is_number and im(a).is_zero is False for a in coords)`.

### IMPORTANT METHODOLOGY NOTE (two false alarms I had to discard)
1. My first worktree was being concurrently rewritten by a concurrent process's rival-testing harness -- point.py:155 mutated between reads (`not im.is_zero`, `im != 0`, `im.is_zero == False`), and `git apply` silently failed. My first e2e run was therefore against PRE-PATCH code and its 9 'mismatches' were artifacts. Redone in a private mktemp -d worktree with md5 of point.py pinned (cfb86294...) and re-verified before AND after every run.
2. Second false alarm: remaining mismatches all involved `zoo` under evaluate(False). Root cause was my harness, not the spec: I computed the abstraction OUTSIDE the evaluate(False) context. im(zoo) is `nan` (is_zero=None -> imagNonzero=False) outside, but `im(zoo)` unevaluated (is_zero=False -> imagNonzero=True) inside. The guard and the abstraction must be sampled at the SAME program point. Once alpha and Point(*coords) were evaluated in one shared context, mismatches went to 0.

### Evidence of faithfulness
- Abstraction-level differential fuzz, 400,000 random coordinate lists (len 0-5) over 74 atoms incl. evaluate(False)-unevaluated forms: model (anyImaginary/coordImaginary transliterated from the pure region, walked with the same backward loop as impl) vs the post-patch guard verbatim over REAL SymPy expressions -> 0 divergences.
- End-to-end refinement leg A4 (out=true <-> constructor raises the imaginary ValueError), abstraction computed in-context, 5,815 comparisons across evaluate(True)/evaluate(False) -> 0 mismatches, 0 cases where a different guard preempted.
- Extended fuzz incl. container/odd-Basic coords whose im() is defined (ImmutableMatrix, Order, Integral, Sum, Limit, AccumBounds), 200,000 lists -> 0 divergences.
- All 5 realizable Coord combos are exercised: (F,F,F)=xr, (F,F,T)=x, (T,F,F)=0, (T,F,T)=nan, (T,T,T)=I. The discriminating regime is genuinely covered: under evaluate(False), im(Integer(1)) is unevaluated -> is_zero=True but bool(...)=True, i.e. imagNonzero=False / imagPresent=True, exactly the imagPresent-vs-imagNonzero split the patch turns on. Prepatch rule rejects Point(1,2); patched accepts (F2P test_issue_22684 passes; full test_point.py 12 passed).

SPEC STRENGTH: NOT TOO STRONG. The ensures is `out = anyImaginary coords`, an exact equality to the transliterated post-patch predicate -- no extra obligation beyond what the gold patch delivers. Where the model is loose it is loose in the SAFE direction: `Coord` admits unrealizable combos (e.g. numeric=false with imagNonzero=true, which reality cannot produce since imagNonzero is defined as `a.is_number and ...`), but coordImaginary = numeric && imagNonzero returns false there and so does the real guard, so the wider domain yields no disagreement. The unrealizable (T,T,F) combo was checked and confirmed unreachable. imagPresent is carried but unread by the modeled decision, exactly as mapping.md §2 documents.

### RESIDUAL (domain-coverage gap, NOT a faithfulness break -- disclosing for the record)
The abstraction map alpha is undefined for coordinates where im(a) or .is_zero raises: Tuple, FiniteSet, Interval, Dict, S.true (TypeError from ImaginaryUnit.__mul__), and notably Lambda/IdentityFunction, which has is_number=True but im() raises IndexError('tuple index out of range'). Real behavior there: Point(Lambda(x,x),1) -> IndexError, and Python's `any()` short-circuits left-to-right so ordering is observable -- Point(I, Lambda) raises the imaginary ValueError (I short-circuits first) while Point(Lambda, I) raises IndexError. The Lean model is a total exception-free fold over already-computed observations, so this exception/ordering behavior is unmodeled. This is not a divergence on a shared input: such coordinates have no Coord image at all, so there is no input on which the modeled function and the real callee both produce a boolean and disagree. It is also behavior the gold patch neither introduces nor changes (pre-patch im(a) raises identically), and it is unreachable from the F2P/P2P tests. Flagging as a completeness note for G-EQ, not as grounds for UNFAITHFUL.

CONCLUSION: no input found on which the modeled function disagrees with the real post-patch callee. Spec is faithful and not over-strong. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** INDEPENDENT RE-DERIVATION (did not rely on the prior panel_3 note). Verdict: NO-LEAKAGE.

SPEC REGION FROZEN — VERIFIED BYTE-EXACT, NOT JUST NORMALIZED. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True; I additionally confirmed the raw spec_view strings are BYTE-identical (sha256 679a7f74d637d076 for both), and each spec region matches exactly (axioms 439B, pure 2363B, pre/post empty, all identical=True). The sole diff between the two files lies inside impl-start/impl-end (prepatch uses `c.numeric && c.imagPresent`). Elision guards hold: spec view contains both elision placeholders and none of `let mut`/`invariant`/`while i > 0`/`decreasing`. Solution.lean elaborates clean (scripts/lean_verify.sh exit 0).

MECHANICAL SCREEN. leakage.screen(velvet flavor, gold_patch, problem_statement, test_patch) => passed=True, zero hard failures, zero warnings (prepatch variant also clean). No relaxation on file (no RELAXED_LEAKAGE.md).

DIRECT ARTIFACT SCAN (my own, over the computed spec view). All ABSENT: `is_zero`, `is_number`, `im(`, `a.is_number`, `is False`, `point.py`, `geometry`, `sympy`, `Point2D`, `__new__`, `ValueError`, the literal 'Imaginary coordinates are not permitted', `coords[dim`, `evaluate(False)`, `test_issue`, `22684`, and every diff marker (`diff --git`, `@@`, `+++`). Zero _NARRATION tokens (bug/fix/patch/regression/previously/incorrectly/wrong/broken). All spec-view declared identifiers are author-invented (Coord, coordImaginary, anyImaginary, anyImaginary_nil/_cons/_drop_step, imaginaryCoordCheck); _patch_changed_symbols is empty (only __new__ is touched, and it is in _COMMON_NONDISTINCTIVE), so no identifier-embed leak is possible.

DECISIVE EMPIRICAL TEST — THE SPEC'S SHARPEST-LOOKING CLAUSE IS NOT LOAD-BEARING. My strongest attack was that the spec discloses a strict THREE-VALUED rule ('false when the imaginary part is provably zero OR cannot be decided') that the public problem_statement never mentions — indeterminacy appears nowhere in the PS. I tested whether that precision is actually required to resolve.

Worktree at base_commit 3ff4717b6a with the gold test_patch applied (F2P test_issue_22684 + all 11 P2P): GOLD `im(a).is_zero is False`      -> F2P PASS, P2P PASS PREPATCH `im(a)` (truthy)         -> F2P FAIL, P2P PASS  (positive control fires) R1 `im(a) != 0`                   -> F2P FAIL, P2P PASS R2 `not im(a).is_zero`            -> F2P PASS, P2P PASS R3 `im(a).is_zero == False`       -> F2P PASS, P2P PASS R4 `simplify(im(a)) != 0`         -> F2P PASS, P2P PASS R5 `a.is_real is False`           -> F2P PASS, P2P PASS Four materially different rivals resolve, including R2 (`not ... .is_zero`), which treats INDETERMINATE as reject — the exact opposite of the spec's stated three-valued clause.

So the fine-grained 'cannot be decided => accept' content the spec spells out is NOT the discriminator between resolving and non-resolving fixes; it neither hands over the gold token nor narrows the solver to gold. The only load-bearing fact is 'a concrete real coordinate under suppressed evaluation must be ACCEPTED', and that is fully public.

BASELINE IS PS AND PS ALREADY LOCALIZES MORE THAN THE SPEC VIEW. hints_text is EMPTY for this instance, so the classic hints-only leak channel (the astropy-14598 failure mode) cannot exist here. The problem_statement itself exhibits the whole failing case (`with sp.evaluate(False): sp.S('Point2D(Integer(1),Integer(2))')` raising 'Imaginary coordinates are not permitted.', and notes it works without evaluate(False)), and its traceback names sympy/geometry/point.py line 153 and __new__ outright. The spec view names none of that. The spec view is strictly LESS localizing than the public text.

RESIDUAL CONCERN, WEIGHED AND REJECTED AS A LEAK. The `Coord.imagPresent` field is carried but never consulted, and the prose states the decision reads only `numeric`/`imagNonzero` — an attacker can argue this signposts 'coarse truthiness is the wrong route', echoing the shape of the gold edit (truthiness -> rigorous test). I do not sustain it: (a) it is stated at the abstract observation level with no repo symbol, (b) the field is structurally REQUIRED so the frozen spec can refute the pre-image skeleton (G-DIFF), (c) the accept-a-real-coordinate-under-suppressed-evaluation behavior it encodes is exactly what the PS demonstrates, and (d) per the empirical table the distinction is not what separates resolving from non-resolving fixes. Stating intended behavior derived from a public bug report is a spec's job, not leakage.

SCOPE NOTE. mapping.md and refinement.md DO quote the gold hunk verbatim ('- if any(a.is_number and im(a) ...' / '+ ... im(a).is_zero is False ...'), but these are audit-only artifacts; eval/prompts.py ships only task.spec_view to consumers, and eval/adapter.py hard-refuses to expose a view whose impl/proof/prove_correct body failed to elide. No consumer-visible leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.