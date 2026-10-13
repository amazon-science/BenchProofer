# P2 adversarial audit — sympy__sympy-21847

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl found. The discriminating input remains the issue's own case: candidate multiplicity vector [1,1] (total degree 2, max single component 1) at minDeg=2 is KEPT by the spec (selectByDegree, minDeg ≤ p.sum) but DROPPED by the pre-patch max-threshold (p.foldr Nat.max 0). atk_1 reproduces that pre-patch bug and is rejected at exactly that goal.
```

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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,10 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      let largest := p.foldr Nat.max 0
+      result := (if minDeg ≤ largest then [p] else []) ++ result
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      result := (if minDeg < totalDegree p then [p] else []) ++ result
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      result := [p] ++ result
       i := i - 1
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      result := (if minDeg ≤ totalDegree p then [] else []) ++ result
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      result := (if minDeg ≤ p.length then [p] else []) ++ result
       i := i - 1
     return result
     -- impl-end
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,10 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      let deg := p.foldr (· + ·) 1
+      result := (if minDeg ≤ deg then [p] else []) ++ result
       i := i - 1
     return result
     -- impl-end
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,11 +60,10 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
       result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
-      i := i - 1
+      i := i
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The surrounding machinery the selection consults —
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ candidates.length
       invariant result = selectByDegree minDeg (candidates.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := candidates[i - 1]!
-      result := (if minDeg ≤ totalDegree p then [p] else []) ++ result
+      result := result ++ (if minDeg ≤ totalDegree p then [p] else [])
       i := i - 1
     return result
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
-- (No axiomatized callees. The surrounding machinery the selection consults —
--  the enumerator that produces the bounded candidate exponent vectors and the
--  product constructor that turns a kept vector back into a term — is UNCHANGED
--  and is folded into the free input `candidates : List (List Nat)` (one entry
--  per enumerated candidate, holding its per-component multiplicities). The spec
--  makes no behavioural claim about that machinery and holds for EVERY candidate
--  list, so there is nothing to validate against a real callee — hence no G-AX.
--  See mapping.md §3 / refinement.md §C.)
-- axioms-end

-- pure-start
/- The total degree of one candidate: the sum of its per-component
   multiplicities. For a candidate whose components count how many times each
   generator occurs, this is the documented size measure — the quantity the
   public contract compares against the lower bound
   (`min_degree <= total_degree(...) <= max_degree`). -/
def totalDegree (p : List Nat) : Nat := p.sum

/- Retain, in their original order, exactly the candidates whose total degree
   is at least the supplied lower bound `minDeg`. Front-recursive (one unfold
   per element) so a single drop-step is available to the backward loop below
   (the Velvet fold pattern, plan §5.4). -/
def selectByDegree (minDeg : Nat) : List (List Nat) → List (List Nat)
  | []      => []
  | p :: ps => (if minDeg ≤ totalDegree p then [p] else []) ++ selectByDegree minDeg ps

@[grind] lemma selectByDegree_nil (minDeg : Nat) : selectByDegree minDeg [] = [] := rfl
@[grind] lemma selectByDegree_cons (minDeg : Nat) (p : List Nat) (ps : List (List Nat)) :
    selectByDegree minDeg (p :: ps)
      = (if minDeg ≤ totalDegree p then [p] else []) ++ selectByDegree minDeg ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- From a list of enumerated candidates (each given by its per-component
   multiplicities) and a lower bound `minDeg`, keep exactly those candidates
   whose total degree is at least `minDeg`, preserving their enumeration order.
   `candidates` and `minDeg` are read-only (not `mut`): the scan threads a fresh
   accumulator and never mutates anything it is handed (directive 5). -/
method selectMonomials (candidates : List (List Nat)) (minDeg : Nat) return (out : List (List Nat))
  ensures out = selectByDegree minDeg candidates
  do
    -- impl-start
    let mut result : List (List Nat) := []
    let mut i := candidates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ candidates.length
      invariant result = selectByDegree minDeg (candidates.drop i)
      done_with i = 0
    do
      let j := i - 1
      let p := candidates[j]!
      let kept := if minDeg ≤ totalDegree p then [p] else []
      result := kept ++ result
      i := j
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the candidate at
   `i-1` on the front, so `selectByDegree` peels one decision. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selectByDegree_drop_step (minDeg : Nat) (candidates : List (List Nat)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ candidates.length) :
    selectByDegree minDeg (candidates.drop (i - 1))
      = (if minDeg ≤ totalDegree candidates[i - 1]! then [candidates[i - 1]!] else [])
        ++ selectByDegree minDeg (candidates.drop i) := by
  have hlt : i - 1 < candidates.length := by omega
  have hcons : candidates.drop (i - 1) = candidates[i - 1]! :: candidates.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectByDegree_cons]

prove_correct selectMonomials by
  loom_solve
  rw [selectByDegree_drop_step minDeg candidates i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: same_spec confirmed True for all 8 attacks + positive control (Solution.lean axioms/pure/pre/post byte-identical; only impl region edited).

VERIFY COMMANDS (run concurrently, ≤4 jobs): bash scripts/lean_verify.sh <atk>.lean. RESULTS: positive_control exit=0 (VERIFIES); atk_1..atk_8 ALL exit=1 (rejected). No sorry/timeout.

Every rejection lands at the SAME spec-discriminating locus — the loop invariant `result = selectByDegree minDeg (candidates.drop i)` (the exact functional-equality ensures pinning the sum-threshold), not an incidental/automation failure:
- atk_1 (prepatch bug, foldr Nat.max 0): residual goal is precisely the max-vs-sum keep test (foldr Nat.max 0 vs totalDegree). prepatch_reproduced=true.
- atk_2 (strict < instead of ≤): boundary off-by-one at minDeg = totalDegree p.
- atk_3 (keep everything [p]): fails when p should be dropped.
- atk_4 (keep nothing []): fails when p should be kept.
- atk_5 (length threshold, minDeg ≤ p.length — #components not sum, partial-domain wrong): length-vs-sum mismatch.
- atk_6 (ungrounded off-by-one sum, foldr (·+·) 1 = sum+1): boundary mismatch.
- atk_7 (control-flow-effect / non-termination probe: i := i, loop never decreases): REJECTED at invariant preservation — the `done_with i=0` + invariant machinery defends against partial-correctness vacuity despite loom.semantics.termination=partial / choice=demonic.
- atk_8 (reversed accumulation, result ++ kept): enumeration-order mismatch; spec pins order.

STEP 2 (materialize faithful patch → run_resolve): NO applicable target. Protocol requires a resolve run only for a wrong impl that VERIFIES; none verified, so verify⇏correct is not exhibited. patches={} accordingly. (The one verifying impl is the correct positive control, which is behaviorally the gold — its patch would resolve, which is expected, not a break.)

REFINEMENT AUDIT (refinement.md / mapping.md): axioms region EMPTY (0 axiom decls in Solution.lean; meta axioms=[]); NO A-consumed and NO A-reference legs (G-AX skip stub legitimate). Legs are R (int≥0 ↔ Nat; item ↔ per-variable multiplicity vector abstracting the UNCHANGED itertools enumerator+counter into the free `candidates` input; Mul(*item)/set(...) a content-preserving postprocess applied equally pre/post-patch) and I (the CHANGED op — the per-candidate degree threshold — modeled DEEPLY and concretely as totalDegree = p.sum / selectByDegree; directive 7 satisfied, the changed op is not axiomatized). NO kind-3 leg. Correspondence to real callees holds: the abstracted machinery is genuinely untouched by patch.diff (max→sum edit is confined to the keep test) and the spec quantifies over EVERY candidate list. G-CONF (conformance_check.py, seed 21847, ≥1e5 fuzzed inputs across both comm/non-comm enumerations, apply_gold) is the mechanical R/I check per plan §4.

CONCLUSION: spec is an exact functional equality to a fully-concrete pure function; every same-spec behavioral deviation (incl. the prepatch bug and a non-termination probe) is rejected, a structurally-distinct correct impl verifies. verify⇒correct holds on all attacks. Verdict SOUND (≥5 distinct attacks — partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, order — all run and none breaks the spec; no resolve run was needed because no wrong impl verified).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl found. The discriminating input remains the issue's own case: candidate multiplicity vector [1,1] (total degree 2, max single component 1) at minDeg=2 is KEPT by the spec (selectByDegree, minDeg ≤ p.sum) but DROPPED by the pre-patch max-threshold (p.foldr Nat.max 0). atk_1 reproduces that pre-patch bug and is rejected at exactly that goal.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The surrounding machinery the selection consults —
--  the enumerator that produces the bounded candidate exponent vectors and the
--  product constructor that turns a kept vector back into a term — is UNCHANGED
--  and is folded into the free input `candidates : List (List Nat)` (one entry
--  per enumerated candidate, holding its per-component multiplicities). The spec
--  makes no behavioural claim about that machinery and holds for EVERY candidate
--  list, so there is nothing to validate against a real callee — hence no G-AX.
--  See mapping.md §3 / refinement.md §C.)
-- axioms-end

-- pure-start
/- The total degree of one candidate: the sum of its per-component
   multiplicities. For a candidate whose components count how many times each
   generator occurs, this is the documented size measure — the quantity the
   public contract compares against the lower bound
   (`min_degree <= total_degree(...) <= max_degree`). -/
def totalDegree (p : List Nat) : Nat := p.sum

/- Retain, in their original order, exactly the candidates whose total degree
   is at least the supplied lower bound `minDeg`. Front-recursive (one unfold
   per element) so a single drop-step is available to the backward loop below
   (the Velvet fold pattern, plan §5.4). -/
def selectByDegree (minDeg : Nat) : List (List Nat) → List (List Nat)
  | []      => []
  | p :: ps => (if minDeg ≤ totalDegree p then [p] else []) ++ selectByDegree minDeg ps

@[grind] lemma selectByDegree_nil (minDeg : Nat) : selectByDegree minDeg [] = [] := rfl
@[grind] lemma selectByDegree_cons (minDeg : Nat) (p : List Nat) (ps : List (List Nat)) :
    selectByDegree minDeg (p :: ps)
      = (if minDeg ≤ totalDegree p then [p] else []) ++ selectByDegree minDeg ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- From a list of enumerated candidates (each given by its per-component
   multiplicities) and a lower bound `minDeg`, keep exactly those candidates
   whose total degree is at least `minDeg`, preserving their enumeration order.
   `candidates` and `minDeg` are read-only (not `mut`): the scan threads a fresh
   accumulator and never mutates anything it is handed (directive 5). -/
method selectMonomials (candidates : List (List Nat)) (minDeg : Nat) return (out : List (List Nat))
  ensures out = selectByDegree minDeg candidates
  do
    -- impl-start
    let mut result : List (List Nat) := []
    let mut i := candidates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ candidates.length
      invariant result = selectByDegree minDeg (candidates.drop i)
      done_with i = 0
    do
      let j := i - 1
      let p := candidates[j]!
      let kept := if minDeg ≤ totalDegree p then [p] else []
      result := kept ++ result
      i := j
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the candidate at
   `i-1` on the front, so `selectByDegree` peels one decision. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selectByDegree_drop_step (minDeg : Nat) (candidates : List (List Nat)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ candidates.length) :
    selectByDegree minDeg (candidates.drop (i - 1))
      = (if minDeg ≤ totalDegree candidates[i - 1]! then [candidates[i - 1]!] else [])
        ++ selectByDegree minDeg (candidates.drop i) := by
  have hlt : i - 1 < candidates.length := by omega
  have hcons : candidates.drop (i - 1) = candidates[i - 1]! :: candidates.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectByDegree_cons]

prove_correct selectMonomials by
  loom_solve
  rw [selectByDegree_drop_step minDeg candidates i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: same_spec confirmed True for all 8 attacks + positive control (Solution.lean axioms/pure/pre/post byte-identical; only impl region edited).

VERIFY COMMANDS (run concurrently, ≤4 jobs): bash scripts/lean_verify.sh <atk>.lean. RESULTS: positive_control exit=0 (VERIFIES); atk_1..atk_8 ALL exit=1 (rejected). No sorry/timeout.

Every rejection lands at the SAME spec-discriminating locus — the loop invariant `result = selectByDegree minDeg (candidates.drop i)` (the exact functional-equality ensures pinning the sum-threshold), not an incidental/automation failure:
- atk_1 (prepatch bug, foldr Nat.max 0): residual goal is precisely the max-vs-sum keep test (foldr Nat.max 0 vs totalDegree). prepatch_reproduced=true.
- atk_2 (strict < instead of ≤): boundary off-by-one at minDeg = totalDegree p.
- atk_3 (keep everything [p]): fails when p should be dropped.
- atk_4 (keep nothing []): fails when p should be kept.
- atk_5 (length threshold, minDeg ≤ p.length — #components not sum, partial-domain wrong): length-vs-sum mismatch.
- atk_6 (ungrounded off-by-one sum, foldr (·+·) 1 = sum+1): boundary mismatch.
- atk_7 (control-flow-effect / non-termination probe: i := i, loop never decreases): REJECTED at invariant preservation — the `done_with i=0` + invariant machinery defends against partial-correctness vacuity despite loom.semantics.termination=partial / choice=demonic.
- atk_8 (reversed accumulation, result ++ kept): enumeration-order mismatch; spec pins order.

STEP 2 (materialize faithful patch → run_resolve): NO applicable target. Protocol requires a resolve run only for a wrong impl that VERIFIES; none verified, so verify⇏correct is not exhibited. patches={} accordingly. (The one verifying impl is the correct positive control, which is behaviorally the gold — its patch would resolve, which is expected, not a break.)

REFINEMENT AUDIT (refinement.md / mapping.md): axioms region EMPTY (0 axiom decls in Solution.lean; meta axioms=[]); NO A-consumed and NO A-reference legs (G-AX skip stub legitimate). Legs are R (int≥0 ↔ Nat; item ↔ per-variable multiplicity vector abstracting the UNCHANGED itertools enumerator+counter into the free `candidates` input; Mul(*item)/set(...) a content-preserving postprocess applied equally pre/post-patch) and I (the CHANGED op — the per-candidate degree threshold — modeled DEEPLY and concretely as totalDegree = p.sum / selectByDegree; directive 7 satisfied, the changed op is not axiomatized). NO kind-3 leg. Correspondence to real callees holds: the abstracted machinery is genuinely untouched by patch.diff (max→sum edit is confined to the keep test) and the spec quantifies over EVERY candidate list. G-CONF (conformance_check.py, seed 21847, ≥1e5 fuzzed inputs across both comm/non-comm enumerations, apply_gold) is the mechanical R/I check per plan §4.

CONCLUSION: spec is an exact functional equality to a fully-concrete pure function; every same-spec behavioral deviation (incl. the prepatch bug and a non-termination probe) is rejected, a structurally-distinct correct impl verifies. verify⇒correct holds on all attacks. Verdict SOUND (≥5 distinct attacks — partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, order — all run and none breaks the spec; no resolve run was needed because no wrong impl verified).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. The spec models the total-degree branch of itermonomials (sympy/polys/monomials.py): selectByDegree keeps a candidate iff minDeg <= totalDegree p, with totalDegree p = p.sum. This is exactly the GOLD-PATCHED behavior (`if sum(powers.values()) >= min_degree`). The gold patch.diff file in the bundle is empty, but the base commit d9b18c5 uses the pre-patch `max(powers.values()) >= min_degree`; I materialized the patched callee (max->sum in both commutative and non-commutative hunks) in a base worktree and ran a differential shadow-vs-oracle check.

Evidence: (1) 200,000 fuzzed (variables, max_degree in 0..4, min_degree in 0..5) inputs over commutative and non-commutative pools with seed 21847 — 0 disagreements. (2) Additional 200k/50k random inputs at higher degrees and a bounded exhaustive grid (175 cases, pools x max_degree 0..4 x min_degree 0..6) — 0 disagreements. The spec's abstraction (item ↔ multiplicity vector, S.One padding slot contributes 0, Mul+set as content-preserving postprocess) reconstructs the real yielded-monomial set faithfully, and the min_degree>max_degree / max_degree==0 / no-variables edge cases match.

The spec is neither too strong nor too weak on any input tried: it is behaviorally equal to the real patched callee. The discriminating input [1,1] at minDeg=2 (total degree 2, max component 1) is kept by the sum-spec and dropped by the max pre-patch — consistent with the fix.

Orthogonal confirmations: swebench_unified.markers.same_spec(Solution, Solution_prepatch) = True (frozen spec region byte-identical). Solution.lean elaborates clean via lean_verify.sh (exit 0). Solution_prepatch.lean (max-based impl) correctly FAILS prove_correct on the sum-vs-max goal (exit 1), confirming the spec genuinely pins the sum threshold rather than being trivially satisfiable. No diverging input exists; spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean, impl+proof elided) encodes only the PUBLICLY-DOCUMENTED intended behavior: totalDegree p = p.sum, selectByDegree keeps candidates whose total degree >= minDeg, postcondition `out = selectByDegree minDeg candidates`. The public problem_statement already discloses (a) the changed symbol `itermonomials`, (b) the intended contract verbatim `min_degree <= total_degree(monom) <= max_degree`, and (c) that monomials meeting total-degree should be kept (`x1*x2**2 ... that also have total degree of 3`). The spec view's `totalDegree`/`selectByDegree` and its comment quoting `min_degree <= total_degree(...) <= max_degree` merely restate that public contract; they do not reveal the gold edit's mechanics beyond it. Crucially the PRE-PATCH `max(powers.values())` test appears NOWHERE in the consumer spec view — it lives only in Solution_prepatch.lean (`p.foldr Nat.max 0`), which is not part of the spec view; same_spec(post, prepatch)=True, confirming the discriminator is entirely in the elided impl region. No diff markers, no patched file path/module, no 'max'/'sum instead of max' narration, no bug/fix language in spec-view comments. Mechanical G-LEAK screen PASSES (verified via leakage.screen: hard_failures=[]); changed symbol `itermonomials` is exempt since it is present in problem_statement. The discriminating counterexample ([1,1] total-degree-2 kept but max-component-1 dropped) and 'wrongly missing' narration exist only in refinement.md/mapping.md (auditor artifacts, out of spec-view scope). A solver seeing this spec learns the target = total-degree lower-bound filter, which the public issue already fully specifies; it does not disclose that the gold implementation-change was max->sum beyond what the problem statement states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
