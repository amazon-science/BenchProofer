# P2 adversarial audit — sympy__sympy-21847

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec is not broken. The post-condition fully pins the output as an exact functional equality: result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum)). Every genuinely-wrong same-spec impl (atk_2..7) makes the correct_ theorem a FALSE proposition and cannot close (all fail lean_verify, exit 1; concretely disproved via #eval, each impl ≠ spec). The only same-spec impl that verifies (atk_1, the ungrounded-oracle echo returning the spec RHS verbatim) is behaviorally identical to gold, has clean axioms [propext], and its faithful patch RESOLVES under the official harness. Thus verify⇒correct holds; no verify∧¬resolve witness exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → not a counterexample (changed the spec)

```diff
@@ -46,43 +46,14 @@
 -- impl-start
 def implementation_selectMonomials
     (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
-  Id.run do
-    let mut acc := []
-    for powers in candidates do
-      if minDegree ≤ powers.sum then
-        acc := acc ++ [powers]
-    return acc
+  candidates.filter (fun powers => decide (minDegree ≤ powers.sum))
 -- impl-end
 
 -- proof-start
-theorem selectMonomials_forIn_eq
-    (minDegree : Nat) (candidates : List (List Nat)) (init : List (List Nat)) :
-    Id.run (forIn candidates init (fun powers r =>
-      if minDegree ≤ powers.sum then do
-        pure PUnit.unit
-        pure (ForInStep.yield (r ++ [powers]))
-      else do
-        pure PUnit.unit
-        pure (ForInStep.yield r)))
-      = init ++ candidates.filter (fun powers => decide (minDegree ≤ powers.sum)) := by
-  induction candidates generalizing init with
-  | nil => simp only [Id.run, List.forIn_nil, List.filter_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    by_cases h : minDegree ≤ a.sum
-    · simp [h, ih, List.append_assoc]
-    · simp [h, ih]
-
 theorem correct_selectMonomials :
     ∀ (minDegree : Nat) (candidates : List (List Nat)),
       problem_spec_selectMonomials minDegree candidates
         (implementation_selectMonomials minDegree candidates) := by
   intro minDegree candidates
   unfold problem_spec_selectMonomials implementation_selectMonomials
-  simp only [Id.run]
-  have := selectMonomials_forIn_eq minDegree candidates []
-  simp only [Id.run] at this
-  rw [this]
-  simp
--- proof-end
+  rfl
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
   Id.run do
     let mut acc := []
     for powers in candidates do
-      if minDegree ≤ powers.sum then
+      if minDegree < powers.sum then
         acc := acc ++ [powers]
     return acc
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
   Id.run do
     let mut acc := []
     for powers in candidates do
-      if minDegree ≤ powers.sum then
+      if minDegree ≤ powers.foldr Nat.max 0 then
         acc := acc ++ [powers]
     return acc
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,8 @@
 -- impl-start
 def implementation_selectMonomials
     (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
-  Id.run do
+  if minDegree = 0 then []
+  else Id.run do
     let mut acc := []
     for powers in candidates do
       if minDegree ≤ powers.sum then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
     let mut acc := []
     for powers in candidates do
       if minDegree ≤ powers.sum then
-        acc := acc ++ [powers]
+        acc := [powers] ++ acc
     return acc
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,7 @@
 -- impl-start
 def implementation_selectMonomials
     (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
-  Id.run do
-    let mut acc := []
-    for powers in candidates do
-      if minDegree ≤ powers.sum then
-        acc := acc ++ [powers]
-    return acc
+  candidates
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
   Id.run do
     let mut acc := []
     for powers in candidates do
-      if minDegree ≤ powers.sum then
+      if minDegree ≤ powers.sum + 1 then
         acc := acc ++ [powers]
     return acc
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting monomials of sufficient total degree.

A monomial over a given list of variables is described by its exponent vector:
the per-variable powers, one entry per variable. The *total degree* of such a
monomial is the sum of its exponents.

Given a list of candidate monomials (each as an exponent vector) and a minimum
total degree `minDegree`, the desired behaviour is to keep exactly those
candidates whose total degree is at least `minDegree`, leaving the others out,
and preserving the order in which the candidates were presented.

In particular a candidate is kept on the basis of its *total* degree — the
combined contribution of all its variables — not on the basis of any single
variable's contribution. So a candidate that spreads its degree across several
variables is kept whenever its total degree reaches the threshold, even if no
individual variable does.
-/

-- axioms-start
-- (no unchanged callee needs an opaque declaration: the candidate monomials —
-- already reduced to their exponent vectors — are the input to the modeled
-- selection step, and the total-degree test is modeled directly.)
-- axioms-end

-- pure-start
-- (no additional pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The selected monomials are exactly the candidates whose total degree (the
sum of the exponent vector) is at least `minDegree`, in their original order.

This pins the result completely: a candidate is in the result iff its total
degree meets the threshold, and the relative order of kept candidates is the
order they appeared in. -/
def problem_spec_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) (result : List (List Nat)) :
    Prop :=
  result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum))
-- post-conditions-end

-- impl-start
def implementation_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
  Id.run do
    let mut acc := []
    for powers in candidates do
      if minDegree ≤ powers.sum then
        acc := acc ++ [powers]
    return acc
-- impl-end

-- proof-start
theorem selectMonomials_forIn_eq
    (minDegree : Nat) (candidates : List (List Nat)) (init : List (List Nat)) :
    Id.run (forIn candidates init (fun powers r =>
      if minDegree ≤ powers.sum then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ [powers]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield r)))
      = init ++ candidates.filter (fun powers => decide (minDegree ≤ powers.sum)) := by
  induction candidates generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : minDegree ≤ a.sum
    · simp [h, ih, List.append_assoc]
    · simp [h, ih]

theorem correct_selectMonomials :
    ∀ (minDegree : Nat) (candidates : List (List Nat)),
      problem_spec_selectMonomials minDegree candidates
        (implementation_selectMonomials minDegree candidates) := by
  intro minDegree candidates
  unfold problem_spec_selectMonomials implementation_selectMonomials
  simp only [Id.run]
  have := selectMonomials_forIn_eq minDegree candidates []
  simp only [Id.run] at this
  rw [this]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (all; same_spec=True confirmed for all 7 attacks via swebench_unified.markers.same_spec + get_backend('lean')).

Spec shape: post-condition is a COMPLETE functional spec — result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum)). No axioms, no pure helpers. refinement.md legs are ALL tagged R (5 rows: accumulator init, iterate candidates, accept predicate max→sum THE FIX, order-preserving append, yield). No kind-3 (ungrounded) legs; no A-consumed / A-reference legs to audit (axioms region is a documented no-op stub — 'no unchanged callee needs an opaque declaration'; the total-degree test is modeled directly as powers.sum). Model↔patch correspondence holds: powers.sum ↔ sum(powers.values()), minDegree≤ ↔ >= min_degree, at the two byte-identical patched sub-branches (monomials.py:130 comm, :142 non-comm). A-leg concern is N/A here — no deep-model references exist.

7 attacks (≥5 distinct wrong-impl classes), verified concurrently as background jobs (≤4 at a time):
- atk_1 UNGROUNDED-ORACLE ECHO: impl = candidates.filter (…powers.sum…) verbatim RHS. `bash scripts/lean_verify.sh atk_1.lean` => exit 0 (VERIFIES). #print axioms correct_selectMonomials => [propext] (CLEAN, no sorryAx/custom). Faithful patch materialized (= gold sum-fix, atk_1.patch) and run: run_resolve('sympy__sympy-21847', patch) => RESOLVED=True, COMPLETED=True, note='resolved'. verify⇒correct upheld.
- atk_2 BOUNDARY (strict `minDegree < powers.sum`): lean_verify exit 1. #eval: i2 2 [[2]] = [] vs spec [[2]] (drops sum==min). FALSE goal.
- atk_3 CONTROL-FLOW-EFFECT / prepatch bug (`powers.foldr Nat.max 0`): exit 1. #eval: i3 2 [[1,1]] = [] vs spec [[1,1]] (drops spread degree — the real F2P bug). FALSE goal.
- atk_4 PARTIAL-DOMAIN (minDegree=0 → []): exit 1. #eval: i4 0 [[0]] = [] vs spec [[0]]. FALSE goal.
- atk_5 CONTROL-FLOW-EFFECT (reversed accumulation, prepend): exit 1. #eval: i5 1 [[1],[2]] = [[2],[1]] vs spec [[1],[2]] (wrong order). FALSE goal.
- atk_6 UNGROUNDED / identity (return candidates): exit 1. #eval: i6 5 [[1]] = [[1]] vs spec [] (keeps too much). FALSE goal.
- atk_7 BOUNDARY off-by-one (`powers.sum + 1`): exit 1. #eval: i7 3 [[2]] = [[2]] vs spec [] (too lenient). FALSE goal.

Positive control: pc.lean = unmodified Solution.lean => lean_verify exit 0; #print axioms => [propext, Quot.sound] (clean).
Prepatch: Solution_prepatch.lean (max-keyed impl w/ carried gold proof) => lean_verify exit 1 (fails to typecheck; bug reproduced, matches G-DIFF claim).

Commands used:
  bash scripts/lean_verify.sh <atk_N|pc|prepatch>.lean
  (axiom probe) appended `#print axioms correct_selectMonomials` then re-ran lean_verify => atk_1 [propext], pc [propext,Quot.sound]
  (concrete disproof) lake env lean disproof.lean under lean_shared (#eval impl vs spec == false for all 6 wrong impls)
  (resolve) python -c run_resolve('sympy__sympy-21847', atk_1.patch) => RESOLVED=True

CONCLUSION: The postcondition is a total functional specification, so verify⇔correct is tight: no wrong output can satisfy correct_, and the sole verifying impl is behaviorally gold and resolves. ≥5 distinct attacks run, none breaks it. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_1.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec is not broken. The post-condition fully pins the output as an exact functional equality: result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum)). Every genuinely-wrong same-spec impl (atk_2..7) makes the correct_ theorem a FALSE proposition and cannot close (all fail lean_verify, exit 1; concretely disproved via #eval, each impl ≠ spec). The only same-spec impl that verifies (atk_1, the ungrounded-oracle echo returning the spec RHS verbatim) is behaviorally identical to gold, has clean axioms [propext], and its faithful patch RESOLVES under the official harness. Thus verify⇒correct holds; no verify∧¬resolve witness exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → not a counterexample (changed the spec)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting monomials of sufficient total degree.

A monomial over a given list of variables is described by its exponent vector:
the per-variable powers, one entry per variable. The *total degree* of such a
monomial is the sum of its exponents.

Given a list of candidate monomials (each as an exponent vector) and a minimum
total degree `minDegree`, the desired behaviour is to keep exactly those
candidates whose total degree is at least `minDegree`, leaving the others out,
and preserving the order in which the candidates were presented.

In particular a candidate is kept on the basis of its *total* degree — the
combined contribution of all its variables — not on the basis of any single
variable's contribution. So a candidate that spreads its degree across several
variables is kept whenever its total degree reaches the threshold, even if no
individual variable does.
-/

-- axioms-start
-- (no unchanged callee needs an opaque declaration: the candidate monomials —
-- already reduced to their exponent vectors — are the input to the modeled
-- selection step, and the total-degree test is modeled directly.)
-- axioms-end

-- pure-start
-- (no additional pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The selected monomials are exactly the candidates whose total degree (the
sum of the exponent vector) is at least `minDegree`, in their original order.

This pins the result completely: a candidate is in the result iff its total
degree meets the threshold, and the relative order of kept candidates is the
order they appeared in. -/
def problem_spec_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) (result : List (List Nat)) :
    Prop :=
  result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum))
-- post-conditions-end

-- impl-start
def implementation_selectMonomials
    (minDegree : Nat) (candidates : List (List Nat)) : List (List Nat) :=
  Id.run do
    let mut acc := []
    for powers in candidates do
      if minDegree ≤ powers.sum then
        acc := acc ++ [powers]
    return acc
-- impl-end

-- proof-start
theorem selectMonomials_forIn_eq
    (minDegree : Nat) (candidates : List (List Nat)) (init : List (List Nat)) :
    Id.run (forIn candidates init (fun powers r =>
      if minDegree ≤ powers.sum then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ [powers]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield r)))
      = init ++ candidates.filter (fun powers => decide (minDegree ≤ powers.sum)) := by
  induction candidates generalizing init with
  | nil => simp only [Id.run, List.forIn_nil, List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : minDegree ≤ a.sum
    · simp [h, ih, List.append_assoc]
    · simp [h, ih]

theorem correct_selectMonomials :
    ∀ (minDegree : Nat) (candidates : List (List Nat)),
      problem_spec_selectMonomials minDegree candidates
        (implementation_selectMonomials minDegree candidates) := by
  intro minDegree candidates
  unfold problem_spec_selectMonomials implementation_selectMonomials
  simp only [Id.run]
  have := selectMonomials_forIn_eq minDegree candidates []
  simp only [Id.run] at this
  rw [this]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (all; same_spec=True confirmed for all 7 attacks via swebench_unified.markers.same_spec + get_backend('lean')).

Spec shape: post-condition is a COMPLETE functional spec — result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum)). No axioms, no pure helpers. refinement.md legs are ALL tagged R (5 rows: accumulator init, iterate candidates, accept predicate max→sum THE FIX, order-preserving append, yield). No kind-3 (ungrounded) legs; no A-consumed / A-reference legs to audit (axioms region is a documented no-op stub — 'no unchanged callee needs an opaque declaration'; the total-degree test is modeled directly as powers.sum). Model↔patch correspondence holds: powers.sum ↔ sum(powers.values()), minDegree≤ ↔ >= min_degree, at the two byte-identical patched sub-branches (monomials.py:130 comm, :142 non-comm). A-leg concern is N/A here — no deep-model references exist.

7 attacks (≥5 distinct wrong-impl classes), verified concurrently as background jobs (≤4 at a time):
- atk_1 UNGROUNDED-ORACLE ECHO: impl = candidates.filter (…powers.sum…) verbatim RHS. `bash scripts/lean_verify.sh atk_1.lean` => exit 0 (VERIFIES). #print axioms correct_selectMonomials => [propext] (CLEAN, no sorryAx/custom). Faithful patch materialized (= gold sum-fix, atk_1.patch) and run: run_resolve('sympy__sympy-21847', patch) => RESOLVED=True, COMPLETED=True, note='resolved'. verify⇒correct upheld.
- atk_2 BOUNDARY (strict `minDegree < powers.sum`): lean_verify exit 1. #eval: i2 2 [[2]] = [] vs spec [[2]] (drops sum==min). FALSE goal.
- atk_3 CONTROL-FLOW-EFFECT / prepatch bug (`powers.foldr Nat.max 0`): exit 1. #eval: i3 2 [[1,1]] = [] vs spec [[1,1]] (drops spread degree — the real F2P bug). FALSE goal.
- atk_4 PARTIAL-DOMAIN (minDegree=0 → []): exit 1. #eval: i4 0 [[0]] = [] vs spec [[0]]. FALSE goal.
- atk_5 CONTROL-FLOW-EFFECT (reversed accumulation, prepend): exit 1. #eval: i5 1 [[1],[2]] = [[2],[1]] vs spec [[1],[2]] (wrong order). FALSE goal.
- atk_6 UNGROUNDED / identity (return candidates): exit 1. #eval: i6 5 [[1]] = [[1]] vs spec [] (keeps too much). FALSE goal.
- atk_7 BOUNDARY off-by-one (`powers.sum + 1`): exit 1. #eval: i7 3 [[2]] = [[2]] vs spec [] (too lenient). FALSE goal.

Positive control: pc.lean = unmodified Solution.lean => lean_verify exit 0; #print axioms => [propext, Quot.sound] (clean).
Prepatch: Solution_prepatch.lean (max-keyed impl w/ carried gold proof) => lean_verify exit 1 (fails to typecheck; bug reproduced, matches G-DIFF claim).

Commands used:
  bash scripts/lean_verify.sh <atk_N|pc|prepatch>.lean
  (axiom probe) appended `#print axioms correct_selectMonomials` then re-ran lean_verify => atk_1 [propext], pc [propext,Quot.sound]
  (concrete disproof) lake env lean disproof.lean under lean_shared (#eval impl vs spec == false for all 6 wrong impls)
  (resolve) python -c run_resolve('sympy__sympy-21847', atk_1.patch) => RESOLVED=True

CONCLUSION: The postcondition is a total functional specification, so verify⇔correct is tight: no wrong output can satisfy correct_, and the sole verifying impl is behaviorally gold and resolves. ≥5 distinct attacks run, none breaks it. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): NO divergence found. Model: implementation_selectMonomials keeps a candidate iff minDegree <= powers.sum; spec problem_spec_selectMonomials = candidates.filter(fun powers => decide (minDegree <= powers.sum)). Real callee: itermonomials integer-degree branch (total_degree is True), gold-patched accept predicate `sum(powers.values()) >= min_degree` at both the commutative (combinations_with_replacement) and non-commutative (product) sub-branches, which are byte-identical.

Checks performed:
1) Solution.lean verifies (lean_verify exit 0); #print axioms correct_selectMonomials => [propext, Quot.sound], no sorryAx => proof genuine.
2) same_spec(Solution, Solution_prepatch, LeanBackend)=True: spec region byte-identical; discrimination lives in the impl, not a weakened spec.
3) G-DIFF: prepatch (max-keyed buggy) impl genuinely FAILS to typecheck against the same spec (rewrite pattern mismatch) => spec has real discriminating power, not vacuous.
4) Differential faithfulness: reconstructed base_commit itermonomials WITH gold patch (max->sum) and ran the model's shadow (sum-filter over the same enumeration + S.One padding + early-outs) against it over the boundary catalogue plus 150,000 randomized (variables in {comm,noncomm}, max_degree 0..4, min_degree 0..max+1) draws => 0 disagreements. Reproduces conformance_check.py logic exactly.

Why no input can diverge: the sole modeled operation is the per-candidate accept predicate; `sum(powers.values()) >= min_degree` maps exactly to `minDegree <= powers.sum` (direction preserved; the appended S.One contributes 0 to sum in both real and shadow), the exponent-vector abstraction (dict.values() -> List Nat) is exact, the order-preserving accumulator faithfully mirrors the pre-set() append list, and set-output equality is confirmed empirically. min_degree is validated in [0,max_degree] before the loop so Nat is exact. The list-degree branch is correctly out of scope (unchanged by the patch). Spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: max(powers.values())>=min_degree -> sum(powers.values())>=min_degree at two byte-identical sites; the discriminator is 'accept on total degree (sum) not largest single exponent (max)'. The public problem_statement ALREADY fully discloses this: it quotes the documented contract 'min_degree <= total_degree(monom) <= max_degree' and gives concrete examples (min_degrees=3 wrongly returns only [x3**3,x2**3,x1**3] but should also return x1*x2**2, x2*x3**2 which have total degree 3 but max single exponent 2) — i.e. the exact max-vs-sum failure class is public. The spec view describes only the correct target semantics (keep candidates whose total degree >= minDegree; powers.sum; 'on the basis of its total degree, not any single variable's contribution'), which is directly derivable from the public statement. It contains no diff markers, no patched file path, no reproduced gold-diff line, no 'max' token, no pre-patch/fix/bug narration, and no spec-view identifier echoing a patched repo symbol. Mechanical leakage.screen() passes (hard_failures=[], warnings=[]). Spec region byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec True), confirming the rendered spec_view is the true solver-visible view. Nothing is revealed beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
