# P2 adversarial audit — sympy__sympy-24443

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk1_order.lean`, `atk2_natabs.lean`, `atk3_offbyone.lean`, `atk4_identity.lean`, `atk5_first.lean`, `atk6_diverge.lean`, `atk7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies against the frozen spec, so there is no verifying wrong impl whose faithful refined patch could be materialized and run through the harness. The postcondition `out = wordProd assign syllables` under `loom.semantics.termination "total"` is a COMPLETE functional specification: it pins the exact left-to-right ordered product of `assign sym ^ p` over EVERY syllable (signed Int exponent via zpow, order-significant in non-abelian G) and forces termination via `decreasing i`. Every partial/boundary/order/sign/control-flow deviation leaves an unsolvable proof goal.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,6 +49,10 @@
   ensures out = wordProd assign syllables
   do
     -- impl-start
+    -- Pre-image skeleton: a syllable whose exponent is negative is silently
+    -- skipped — its factor never enters the running product. The frozen spec
+    -- requires the full ordered product over every syllable (including the
+    -- ones with negative exponent), so prove_correct MUST fail.
     let mut result : G := 1
     let mut i := syllables.length
     while i > 0
@@ -58,7 +62,8 @@
       decreasing i
     do
       let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
+      let factor : G := if s.2 ≥ 0 then assign s.1 ^ s.2 else 1
+      result := factor * result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk1_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,9 +58,10 @@
       decreasing i
     do
       let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
+      result := result * assign s.1 ^ s.2
       i := i - 1
     return result
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

Attack 3 — `atk2_natabs.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,9 +58,10 @@
       decreasing i
     do
       let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
+      result := assign s.1 ^ (s.2.natAbs) * result
       i := i - 1
     return result
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

Attack 4 — `atk3_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,11 @@
       done_with i = 0
       decreasing i
     do
-      let s := syllables[i - 1]!
+      let s := syllables[i]!
       result := assign s.1 ^ s.2 * result
       i := i - 1
     return result
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

Attack 5 — `atk4_identity.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,9 @@
   ensures out = wordProd assign syllables
   do
     -- impl-start
-    let mut result : G := 1
-    let mut i := syllables.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ syllables.length
-      invariant result = wordProd assign (syllables.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
-      i := i - 1
+    let result : G := 1
     return result
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

Attack 6 — `atk5_first.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,9 +58,11 @@
       decreasing i
     do
       let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
+      if i = syllables.length then
+        result := assign s.1 ^ s.2 * result
       i := i - 1
     return result
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

Attack 7 — `atk6_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,16 +51,13 @@
     -- impl-start
     let mut result : G := 1
     let mut i := syllables.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ syllables.length
-      invariant result = wordProd assign (syllables.drop i)
-      done_with i = 0
-      decreasing i
+    while true
+      invariant True
+      done_with False
     do
-      let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
-      i := i - 1
+      result := result
     return result
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

Attack 8 — `atk7_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,8 @@
   ensures out = wordProd assign syllables
   do
     -- impl-start
-    let mut result : G := 1
-    let mut i := syllables.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ syllables.length
-      invariant result = wordProd assign (syllables.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := syllables[i - 1]!
-      result := assign s.1 ^ s.2 * result
-      i := i - 1
-    return result
+    return wordProd assign syllables
+
     -- impl-end
 
 /- The backward-fold step: dropping one fewer syllable exposes the syllable at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"
set_option linter.unusedSectionVars false

open TotalCorrectness DemonicChoice

/- The codomain is an arbitrary group `G`. A *word* is presented by its
   syllables — a list of `(symbol, exponent)` pairs, where `symbol : Nat`
   identifies a generator and `exponent : Int` is the (possibly negative)
   power that generator is raised to in that syllable. An *assignment*
   `assign : Nat → G` sends each generator symbol to a codomain element. -/
variable {G : Type} [Group G] [Inhabited G]

-- axioms-start
-- axioms-end

-- pure-start
/- The value of a word under an assignment: the ordered product, syllable by
   syllable from left to right, of each generator's assigned codomain element
   raised to that syllable's exponent. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). The exponent is a
   signed integer (`zpow`), so a syllable's contribution is `assign sym ^ p`
   for every `p : Int` — negative exponents invert. The group `G` need not be
   abelian, so the left-to-right order is significant. -/
def wordProd (assign : Nat → G) : List (Nat × Int) → G
  | []               => 1
  | (sym, p) :: rest => assign sym ^ p * wordProd assign rest

omit [Inhabited G] in
@[grind] lemma wordProd_nil (assign : Nat → G) :
    wordProd assign ([] : List (Nat × Int)) = 1 := rfl

omit [Inhabited G] in
@[grind] lemma wordProd_cons (assign : Nat → G) (sym : Nat) (p : Int)
    (rest : List (Nat × Int)) :
    wordProd assign ((sym, p) :: rest) = assign sym ^ p * wordProd assign rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method evalWord (assign : Nat → G) (syllables : List (Nat × Int)) return (out : G)
  ensures out = wordProd assign syllables
  do
    -- impl-start
    let mut result : G := 1
    let mut i := syllables.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ syllables.length
      invariant result = wordProd assign (syllables.drop i)
      done_with i = 0
      decreasing i
    do
      let s := syllables[i - 1]!
      result := assign s.1 ^ s.2 * result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer syllable exposes the syllable at
   `i-1` on the front, so `wordProd` peels one factor. This is the single goal
   `loom_solve` leaves for the loop body. -/
omit [Inhabited G] in
lemma wordProd_drop_step (assign : Nat → G) (syllables : List (Nat × Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ syllables.length) :
    wordProd assign (syllables.drop (i - 1))
      = assign (syllables[i - 1]!).1 ^ (syllables[i - 1]!).2
          * wordProd assign (syllables.drop i) := by
  have hlt : i - 1 < syllables.length := by omega
  have hcons : syllables.drop (i - 1) = syllables[i - 1]! :: syllables.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, wordProd_cons]

prove_correct evalWord by
  loom_solve
  rw [wordProd_drop_step assign syllables i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attacks confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet) = True. Positive control (unmodified Solution.lean) VERIFIES: `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0. Verifications run concurrently in two background batches of 4 (lean_verify.sh, 300s cap).

### ATTACKS (each: path / command `bash scripts/lean_verify.sh <path>` / observed exit + reason):
1. atk_prepatch.lean (PREPATCH BUG, negative-exponent syllable zeroed via `if s.2 >= 0 then assign s.1^s.2 else 1`): EXIT=1, unsolved goal `s.2 < 0 -> assign s.1 ^ s.2 = 1` (false in any nontrivial group). PREPATCH REPRODUCED.
2. atk1_order.lean (multiplication order flipped `result * assign s.1^s.2` — wrong in non-abelian G): EXIT=1, invariant_2 unsolved (a*b vs b*a).
3. atk2_natabs.lean (sign dropped, `^ s.2.natAbs`): EXIT=1, unsolved `^natAbs = ^p`.
4. atk3_offbyone.lean (boundary: index `syllables[i]!` instead of `[i-1]!`): EXIT=1, invariant unsolved.
5. atk4_identity.lean (ungrounded constant `return 1`): EXIT=1, postcondition `1 = wordProd assign syllables` unsolved.
6. atk5_first.lean (partial-domain: only the first-processed syllable folded): EXIT=1, invariant unsolved.
7. atk6_diverge.lean (control-flow-effect: `while true`, trivial invariant): EXIT=1, REJECTED — 'Decreasing annotations are required in total correctness semantics' + WPGen sorry. Total semantics excludes the diverging class (matches refinement.md's documented earlier partial-correctness counterexample now closed).
8. atk7_echo.lean (ungrounded-oracle echo: `return wordProd assign syllables`): EXIT=1 — does NOT verify against the frozen `prove_correct` proof block ('No goals to be solved' at line 75); the frozen proof is written for the concrete fold, so even the literal-oracle body fails to elaborate. No free pass for echoing the spec.

Step 2 (materialize + run_resolve for verifying wrong impls) is VACUOUS: zero wrong impls verify, so no faithful patch exists to run; BROKEN (verify NOT=> correct) is unreachable here.

REFINEMENT AUDIT (refinement.md + mapping.md): legs A1-A5 are all R (type refinement: array_form<->List(Nat x Int); symbol->domain-gen->image composite <-> assign; codomain identity/*/^/is_identity <-> 1/*/zpow/=1) or I (concrete init + backward fold structure). No kind-3 (inexpressible-changed-op) leg: the operation that changed (_image's per-syllable group product) is modeled DEEPLY as wordProd, per SPEC 0.7, NOT hidden behind an axiom. Consequently there are NO consumed axioms and NO A-reference deep-model callees (axioms region empty; mapping.md 3 + refinement.md C confirm G-AX=skip). The A-leg correspondences bind to REAL repo callees (r.array_form, symbols_to_domain_generators, images, codomain group arithmetic) which G-CONF exercises for real on both shadow and oracle — no assumed contract / ungrounded oracle to falsify. Correspondence holds. G-LEAK not in scope for this gate.

Verdict SOUND: >=5 distinct verifying-wrong-impl attacks attempted (7 + prepatch = 8), none verifies, so none can break verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.lean`, `atk1_order.lean`, `atk2_natabs.lean`, `atk3_offbyone.lean`, `atk4_identity.lean`, `atk5_first.lean`, `atk6_diverge.lean`, `atk7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies against the frozen spec, so there is no verifying wrong impl whose faithful refined patch could be materialized and run through the harness. The postcondition `out = wordProd assign syllables` under `loom.semantics.termination "total"` is a COMPLETE functional specification: it pins the exact left-to-right ordered product of `assign sym ^ p` over EVERY syllable (signed Int exponent via zpow, order-significant in non-abelian G) and forces termination via `decreasing i`. Every partial/boundary/order/sign/control-flow deviation leaves an unsolvable proof goal.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1_order.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2_natabs.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4_identity.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk5_first.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk6_diverge.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk7_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"
set_option linter.unusedSectionVars false

open TotalCorrectness DemonicChoice

/- The codomain is an arbitrary group `G`. A *word* is presented by its
   syllables — a list of `(symbol, exponent)` pairs, where `symbol : Nat`
   identifies a generator and `exponent : Int` is the (possibly negative)
   power that generator is raised to in that syllable. An *assignment*
   `assign : Nat → G` sends each generator symbol to a codomain element. -/
variable {G : Type} [Group G] [Inhabited G]

-- axioms-start
-- axioms-end

-- pure-start
/- The value of a word under an assignment: the ordered product, syllable by
   syllable from left to right, of each generator's assigned codomain element
   raised to that syllable's exponent. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). The exponent is a
   signed integer (`zpow`), so a syllable's contribution is `assign sym ^ p`
   for every `p : Int` — negative exponents invert. The group `G` need not be
   abelian, so the left-to-right order is significant. -/
def wordProd (assign : Nat → G) : List (Nat × Int) → G
  | []               => 1
  | (sym, p) :: rest => assign sym ^ p * wordProd assign rest

omit [Inhabited G] in
@[grind] lemma wordProd_nil (assign : Nat → G) :
    wordProd assign ([] : List (Nat × Int)) = 1 := rfl

omit [Inhabited G] in
@[grind] lemma wordProd_cons (assign : Nat → G) (sym : Nat) (p : Int)
    (rest : List (Nat × Int)) :
    wordProd assign ((sym, p) :: rest) = assign sym ^ p * wordProd assign rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method evalWord (assign : Nat → G) (syllables : List (Nat × Int)) return (out : G)
  ensures out = wordProd assign syllables
  do
    -- impl-start
    let mut result : G := 1
    let mut i := syllables.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ syllables.length
      invariant result = wordProd assign (syllables.drop i)
      done_with i = 0
      decreasing i
    do
      let s := syllables[i - 1]!
      result := assign s.1 ^ s.2 * result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer syllable exposes the syllable at
   `i-1` on the front, so `wordProd` peels one factor. This is the single goal
   `loom_solve` leaves for the loop body. -/
omit [Inhabited G] in
lemma wordProd_drop_step (assign : Nat → G) (syllables : List (Nat × Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ syllables.length) :
    wordProd assign (syllables.drop (i - 1))
      = assign (syllables[i - 1]!).1 ^ (syllables[i - 1]!).2
          * wordProd assign (syllables.drop i) := by
  have hlt : i - 1 < syllables.length := by omega
  have hcons : syllables.drop (i - 1) = syllables[i - 1]! :: syllables.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, wordProd_cons]

prove_correct evalWord by
  loom_solve
  rw [wordProd_drop_step assign syllables i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attacks confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet) = True. Positive control (unmodified Solution.lean) VERIFIES: `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0. Verifications run concurrently in two background batches of 4 (lean_verify.sh, 300s cap).

### ATTACKS (each: path / command `bash scripts/lean_verify.sh <path>` / observed exit + reason):
1. atk_prepatch.lean (PREPATCH BUG, negative-exponent syllable zeroed via `if s.2 >= 0 then assign s.1^s.2 else 1`): EXIT=1, unsolved goal `s.2 < 0 -> assign s.1 ^ s.2 = 1` (false in any nontrivial group). PREPATCH REPRODUCED.
2. atk1_order.lean (multiplication order flipped `result * assign s.1^s.2` — wrong in non-abelian G): EXIT=1, invariant_2 unsolved (a*b vs b*a).
3. atk2_natabs.lean (sign dropped, `^ s.2.natAbs`): EXIT=1, unsolved `^natAbs = ^p`.
4. atk3_offbyone.lean (boundary: index `syllables[i]!` instead of `[i-1]!`): EXIT=1, invariant unsolved.
5. atk4_identity.lean (ungrounded constant `return 1`): EXIT=1, postcondition `1 = wordProd assign syllables` unsolved.
6. atk5_first.lean (partial-domain: only the first-processed syllable folded): EXIT=1, invariant unsolved.
7. atk6_diverge.lean (control-flow-effect: `while true`, trivial invariant): EXIT=1, REJECTED — 'Decreasing annotations are required in total correctness semantics' + WPGen sorry. Total semantics excludes the diverging class (matches refinement.md's documented earlier partial-correctness counterexample now closed).
8. atk7_echo.lean (ungrounded-oracle echo: `return wordProd assign syllables`): EXIT=1 — does NOT verify against the frozen `prove_correct` proof block ('No goals to be solved' at line 75); the frozen proof is written for the concrete fold, so even the literal-oracle body fails to elaborate. No free pass for echoing the spec.

Step 2 (materialize + run_resolve for verifying wrong impls) is VACUOUS: zero wrong impls verify, so no faithful patch exists to run; BROKEN (verify NOT=> correct) is unreachable here.

REFINEMENT AUDIT (refinement.md + mapping.md): legs A1-A5 are all R (type refinement: array_form<->List(Nat x Int); symbol->domain-gen->image composite <-> assign; codomain identity/*/^/is_identity <-> 1/*/zpow/=1) or I (concrete init + backward fold structure). No kind-3 (inexpressible-changed-op) leg: the operation that changed (_image's per-syllable group product) is modeled DEEPLY as wordProd, per SPEC 0.7, NOT hidden behind an axiom. Consequently there are NO consumed axioms and NO A-reference deep-model callees (axioms region empty; mapping.md 3 + refinement.md C confirm G-AX=skip). The A-leg correspondences bind to REAL repo callees (r.array_form, symbols_to_domain_generators, images, codomain group arithmetic) which G-CONF exercises for real on both shadow and oracle — no assumed contract / ungrounded oracle to falsify. Correspondence holds. G-LEAK not in scope for this gate.

Verdict SOUND: >=5 distinct verifying-wrong-impl attacks attempted (7 + prepatch = 8), none verifies, so none can break verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on velvet sympy__sympy-24443. The spec models the post-patch internal `_image(r)` of `_check_homomorphism` as `wordProd assign syllables` = ordered left-to-right group product `∏ₖ assign(symₖ)^{pₖ}` with signed integer exponents (zpow), over ALL syllables of `r.array_form`. This is exactly the gold-patch body `w=identity; for symbol,power in r.array_form: w *= images[symbols_to_domain_generators[symbol]]**power`.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec regions (axioms/pure/pre/post + signature `ensures out = wordProd assign syllables`) are byte-identical; the model is what's under audit.
2. Solution.lean verifies under total-correctness semantics: `bash scripts/lean_verify.sh ...` → EXIT 0. Spec is satisfiable (not vacuous), and its unique satisfying output is `wordProd assign syllables` (the ensures is an equality).
3. Ran the bundle's conformance_check.py against the /tmp worktree source at base_commit WITH the gold patch applied: `G-CONF OK ... 100024 inputs (seed=24443), 0 disagreements`. (The venv's *installed* sympy is pre-patch and errors — must point PYTHONPATH at the patched worktree.)
4. Stronger than the verdict-level G-CONF: compared `wordProd` ELEMENT-WISE against a faithful extraction of the real post-patch `_image` over 87,000 (relator × random assignment) evaluations across Dihedral(3-6), Cyclic(4-7), Symmetric(3-4), Alternating(4-5) with random codomain images including relators carrying negative exponents — 0 mismatches. The Lean group ops (`*`, `^` as zpow, `1`) refine the sympy Permutation/PermutationGroup arithmetic per mapping.md §2, and negative-exponent syllables invert correctly on both sides.

No diverging input exists on the modeled domain. The spec is neither too strong (it is the exact ordered signed product the patched code computes) nor drifted: the abelian-vs-nonabelian ordering, signed zpow, and full-syllable coverage all match. The prepatch model (`if p≥0 then a^p else 1`) correctly fails the spec, confirming the discriminating negative-exponent behavior is captured. Scope restriction to PermutationGroup domain==codomain matches the F2P/issue scenario and the `all(_image(r).is_identity)` verdict; FpGroup codomains (codomain.equals/make_confluent) are explicitly out of the modeled observable and correctly excluded rather than mismodeled. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec == True). Mechanical leakage.screen (lean flavor) passes clean: no diff markers, no patched file path/module (sympy/combinatorics/homomorphisms.py), no gold-patch line reproduced, no narration terms, no spec-view identifier embedding a patched repo symbol. Semantic review beyond the lexical screen: the public problem_statement already discloses (a) the defective function `_image()` inside `_check_homomorphism`, (b) that it is broken on PermutationGroups, and (c) the exact discriminator — inverted generators fail the `in gens` test (i.e. negative-power/inverted syllables are dropped), plus 'the whole thing can be greatly simplified'. The spec view models the CORRECT target behavior abstractly: wordProd = ordered group product over syllables with signed exponents (zpow, negatives invert) on an arbitrary group G, with `ensures out = wordProd assign syllables` and impl/proof elided. The comments stress 'negative exponents invert' and left-to-right order — this is faithful spec semantics, and it does not exceed the problem statement (which already fingers inverted/negative-power generators). If anything the abstraction (arbitrary G, symbol=Nat) HIDES the concrete gold-patch mechanics (r.array_form iteration, symbols_to_domain_generators dict, images lookup, presentation() preamble hoist) rather than revealing them, so the patch structure is not reconstructible from the spec view beyond what the task already licenses. Note: refinement.md and mapping.md quote the gold hunk verbatim, but these are AUDITOR documents, not the consumer spec view, and are out of scope for G-LEAK. No incremental leak of the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
