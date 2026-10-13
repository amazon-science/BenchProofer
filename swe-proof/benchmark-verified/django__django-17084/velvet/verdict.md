# P2 adversarial audit — django__django-17084

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec impl's faithful refined patch completed-and-failed-to-resolve. 12 same-spec admissible attacks were verified; 8 were rejected by the spec on GENUINELY FALSE residual goals (e.g. atk_3: `referencesWindow aggregates.tail = referencesWindow aggregates`; atk_8: `!aggregates.isEmpty = referencesWindow aggregates`; atk_7: `refs.all id = refs.any id`), and the 4 that verified (atk_5 spec-echo, atk_9 relocated fold, atk_11 one-past-the-end total-index sentinel, atk_12 eager list materialization) are value-equal echoes whose faithful refined patches ALL RESOLVED under the official harness (run_resolve completed=True resolved=True, 4/4). Two extra informational boundary probes also resolved (patch_atk_9b.diff: flags read in a DEFERRED pass after the resolving loop, from the stashed `aggregates` dict; probe_default_false.diff: getattr default flipped True->False). The postcondition `out = wrappedEvaluationDecision priorConditions aggregates` is a TOTAL functional equality under `termination "total"`, so every terminating wrong-VALUE impl fails to verify, and the divergence lane that made the PRIOR G-EQ pass INCONCLUSIVE is now closed by the semantics itself: atk_6 (`while true`) is REJECTED at exit 1 with `Decreasing annotations are required in total correctness semantics`, so no verifying attack can hang the harness and no resolve run was left incomplete.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,8 +65,8 @@
       done_with i = 0
       decreasing i
     do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
+      let _refs := aggregates[i - 1]!
+      acc := acc
       i := i - 1
     return priorConditions || acc
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,10 @@
   ensures out = wrappedEvaluationDecision priorConditions aggregates
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := aggregates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aggregates.length
-      invariant acc = referencesWindow (aggregates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
+    let acc : Bool :=
+      match aggregates with
+      | []     => false
+      | a :: _ => aggregateUsesWindow a
     return priorConditions || acc
     -- impl-end
 
@@ -87,7 +80,4 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;> simp_all [wrappedEvaluationDecision, aggregateUsesWindow]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,7 @@
   ensures out = wrappedEvaluationDecision priorConditions aggregates
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := aggregates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aggregates.length
-      invariant acc = referencesWindow (aggregates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
+    let acc : Bool := referencesWindow (aggregates.drop 1)
     return priorConditions || acc
     -- impl-end
 
@@ -87,7 +77,4 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;> simp_all [wrappedEvaluationDecision, aggregateUsesWindow]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,8 +66,10 @@
       decreasing i
     do
       let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
+      if aggregateUsesWindow refs then
+        i := 0
+      else
+        i := i - 1
     return priorConditions || acc
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,18 +57,7 @@
   ensures out = wrappedEvaluationDecision priorConditions aggregates
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := aggregates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aggregates.length
-      invariant acc = referencesWindow (aggregates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
-    return priorConditions || acc
+    return wrappedEvaluationDecision priorConditions aggregates
     -- impl-end
 
 /- The backward-fold step: dropping one fewer aggregate exposes the aggregate at
@@ -87,7 +76,4 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;> simp_all [wrappedEvaluationDecision, aggregateUsesWindow]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,17 +58,12 @@
   do
     -- impl-start
     let mut acc : Bool := false
-    let mut i := aggregates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aggregates.length
-      invariant acc = referencesWindow (aggregates.drop i)
-      done_with i = 0
-      decreasing i
+    while true
+      invariant True
+      done_with False
     do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
-    return priorConditions || acc
+      acc := acc
+    return false
     -- impl-end
 
 /- The backward-fold step: dropping one fewer aggregate exposes the aggregate at
@@ -87,7 +82,4 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;> simp_all [wrappedEvaluationDecision]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
       decreasing i
     do
       let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
+      acc := refs.all (fun b => b) || acc
       i := i - 1
     return priorConditions || acc
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,17 +57,7 @@
   ensures out = wrappedEvaluationDecision priorConditions aggregates
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := aggregates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aggregates.length
-      invariant acc = referencesWindow (aggregates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
+    let acc : Bool := !aggregates.isEmpty
     return priorConditions || acc
     -- impl-end
 
@@ -87,7 +77,4 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;> simp_all [wrappedEvaluationDecision, aggregateUsesWindow]
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,17 +57,7 @@
   ensures out = wrappedEvaluationDecision priorConditions aggregates
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := aggregates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ aggregates.length
-      invariant acc = referencesWindow (aggregates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
-      i := i - 1
+    let acc : Bool := referencesWindow aggregates
     return priorConditions || acc
     -- impl-end
 
@@ -87,7 +77,4 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;> simp_all [wrappedEvaluationDecision, aggregateUsesWindow]
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,7 +68,7 @@
       let refs := aggregates[i - 1]!
       acc := aggregateUsesWindow refs || acc
       i := i - 1
-    return priorConditions || acc
+    return acc
     -- impl-end
 
 /- The backward-fold step: dropping one fewer aggregate exposes the aggregate at
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -57,7 +57,8 @@
   ensures out = wrappedEvaluationDecision priorConditions aggregates
   do
     -- impl-start
-    let mut acc : Bool := false
+    let sentinel := aggregates[aggregates.length]!
+    let mut acc : Bool := aggregateUsesWindow sentinel
     let mut i := aggregates.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ aggregates.length
@@ -87,7 +88,8 @@
   rw [hcons, referencesWindow_cons]
 
 prove_correct wrappedEvaluationDecisionM by
-  loom_solve
-  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
-    simp_all
-  · simp_all [wrappedEvaluationDecision]
+  loom_solve <;>
+    first
+      | (rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]; simp_all)
+      | simp_all [wrappedEvaluationDecision, aggregateUsesWindow,
+                  show (default : List Bool) = [] from rfl, referencesWindow_nil]
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,7 +66,8 @@
       decreasing i
     do
       let refs := aggregates[i - 1]!
-      acc := aggregateUsesWindow refs || acc
+      let flags := refs.map (fun b => b)
+      acc := aggregateUsesWindow flags || acc
       i := i - 1
     return priorConditions || acc
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a pure boolean function
--  of already-resolved metadata: for each aggregate, the per-reference flags
--  recording whether a referenced annotation uses a window function. The
--  machinery that resolves an aggregate's references and each annotation's
--  flag is unchanged and shared by both branches, so it is not consumed as an
--  outside contract. There is no `axiom` declaration and no A-reference deep
--  model of an outside callee.)
-- axioms-end

-- pure-start
/- One aggregate references a window function iff any of its referenced
   annotations uses one. `refs` lists, for a single aggregate, the per-reference
   flags (true = that referenced annotation uses a window function). A reference
   whose flag cannot be determined is treated conservatively as using one
   (handled at the boundary; mapping.md §2). -/
def aggregateUsesWindow (refs : List Bool) : Bool :=
  refs.any (fun b => b)

/- Across a whole list of aggregates, the group references a window function iff
   any single aggregate does. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern, plan §5.4). `aggregates` carries, in
   order, the per-aggregate reference-flag lists. -/
def referencesWindow : List (List Bool) → Bool
  | []        => false
  | a :: rest => aggregateUsesWindow a || referencesWindow rest

@[grind] lemma referencesWindow_nil : referencesWindow [] = false := rfl
@[grind] lemma referencesWindow_cons (a : List Bool) (rest : List (List Bool)) :
    referencesWindow (a :: rest) = (aggregateUsesWindow a || referencesWindow rest) := rfl

/- The aggregation must be evaluated inside a wrapping outer query when either
   the pre-existing structural conditions already demand it (`priorConditions`,
   a shared disjunction the change does not touch — mapping.md §1) OR any
   requested aggregate references an annotation that uses a window function.
   The latter disjunct is what this bundle pins. -/
def wrappedEvaluationDecision (priorConditions : Bool)
    (aggregates : List (List Bool)) : Bool :=
  priorConditions || referencesWindow aggregates
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method wrappedEvaluationDecisionM (priorConditions : Bool) (aggregates : List (List Bool)) return (out : Bool)
  ensures out = wrappedEvaluationDecision priorConditions aggregates
  do
    -- impl-start
    if priorConditions then
      return true
    else
      let mut acc : Bool := false
      let mut i := aggregates.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ aggregates.length
        invariant acc = referencesWindow (aggregates.drop i)
        done_with i = 0
        decreasing i
      do
        let refs := aggregates[i - 1]!
        acc := aggregateUsesWindow refs || acc
        i := i - 1
      return acc
    -- impl-end

/- The backward-fold step: dropping one fewer aggregate exposes the aggregate at
   `i-1` on the front, so `referencesWindow` peels one `aggregateUsesWindow`.
   This is the single goal `loom_solve` leaves for the loop body. -/
lemma referencesWindow_drop_step (aggregates : List (List Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ aggregates.length) :
    referencesWindow (aggregates.drop (i - 1))
      = (aggregateUsesWindow aggregates[i - 1]! || referencesWindow (aggregates.drop i)) := by
  have hlt : i - 1 < aggregates.length := by omega
  have hcons : aggregates.drop (i - 1) = aggregates[i - 1]! :: aggregates.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, referencesWindow_cons]

prove_correct wrappedEvaluationDecisionM by
  loom_solve <;>
    first
      | (rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]; simp_all)
      | simp_all [wrappedEvaluationDecision]
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (all work; nothing written elsewhere).

SAME-SPEC: all 12 attacks + positive control are same_spec=True AND variant_scope.variant_problems=[] (admissible: no new axioms/lemmas, no sorry/admit/native_decide, prove_correct obligation retained). Only the impl region and the prove_correct tactic BODY differ (spec_view elides both; axioms/pure/pre/post byte-identical).
  CMD: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>').read(), b.language))"

### ATTACK LEDGER (CMD for each: bash scripts/lean_verify.sh <f>.lean; verifications run concurrently in background batches of 4)
 | file | wrong-impl class | verify exit | outcome |
 |---|---|---|---|
 | atk_1  | PREPATCH BUG: window disjunct absent, aggregates never inspected | 1 | rejected (false goal: aggregateUsesWindow aggregates[i-1]! = true -> referencesWindow (drop i) = true) |
 | atk_2  | PARTIAL DOMAIN: only the FIRST aggregate inspected | 1 | rejected (match-on-head vs full fold) |
 | atk_3  | BOUNDARY off-by-one: first aggregate skipped (drop 1) | 1 | rejected (referencesWindow tail vs referencesWindow) |
 | atk_4  | CONTROL-FLOW EFFECT: early loop exit on hit without recording it | 1 | rejected (invariant + ensures both fail) |
 | atk_5  | UNGROUNDED-ORACLE ECHO: `return wrappedEvaluationDecision ...` | 0 | CANDIDATE -> patch RESOLVED (echo, not a weakness) |
 | atk_6  | DIVERGENCE (partial-correctness artifact): `while true`, return false | 1 | rejected: "Decreasing annotations are required in total correctness semantics" |
 | atk_7  | QUANTIFIER SWAP: refs.all instead of refs.any per aggregate | 1 | rejected (all vs any) |
 | atk_8  | OVER-APPROXIMATION: wrap whenever any aggregate requested | 1 | rejected (!isEmpty vs fold) |
 | atk_9  | RELOCATED FOLD: whole fold at the decision site, no loop | 0 | CANDIDATE -> patch RESOLVED (echo) |
 | atk_10 | PRIOR-CONDITIONS DROPPED: structural disjunct ignored | 1 | rejected (priorConditions = true -> acc = true is false) |
 | atk_11 | BOUNDARY/total-default masking: extra read ONE PAST THE END seeds acc (Lean [i]! is TOTAL -> default = []) | 0 | CANDIDATE -> patch RESOLVED (echo) |
 | atk_12 | EAGER MATERIALIZATION: refs.map before the disjunction (probes mapping.md §2's any-short-circuit claim) | 0 | CANDIDATE -> patch RESOLVED (echo) |
 POSITIVE CONTROL: pos_control.lean — structurally different but correct (short-circuits on priorConditions, THEN the backward fold in the else branch) — exit 0, VERIFIES.
 PREPATCH REPRODUCED: yes, twice over — atk_1 (my re-encoding, exit 1) and the shipped Solution_prepatch.lean (G-DIFF pass: "verification failed").

RESOLVE RUNS (official harness; run concurrently). CMD: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-17084', open('<patch>').read()); print(r.completed, r.resolved, r.note)"
 | patch_atk_5.diff  | completed=True resolved=True note=resolved |
 | patch_atk_9.diff  | completed=True resolved=True note=resolved |
 | patch_atk_11.diff | completed=True resolved=True note=resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete) |
 | patch_atk_12.diff | completed=True resolved=True note=resolved |
 | patch_atk_9b.diff (extra probe: DEFERRED read placement) | completed=True resolved=True note=resolved |
 | probe_default_false.diff (extra probe: getattr default True->False) | completed=True resolved=True note=resolved |
 Every needed resolve run COMPLETED — no INCONCLUSIVE measurement. 4/4 verifying attacks resolve => no verify⇏correct witness.

WHY THE PRIOR G-EQ FAIL IS CLOSED: the previous pass recorded INCONCLUSIVE because its only verifying non-value-correct impl was a DIVERGING one (`while true`) under `termination "partial"`, whose faithful patch (an infinite loop in get_aggregation) hung the harness (completed=False, 900s). The frozen spec now sets `loom.semantics.termination "total"` / `open TotalCorrectness`; I re-encoded that exact counterexample as atk_6 and it is now REJECTED outright (loom demands a `decreasing` clause). The divergence lane is therefore eliminated by the spec, not merely unmeasured.

A-LEG / refinement.md AUDIT (the assigned focus):
 * Leg taxonomy is complete and legal: 4 legs, A1=R, A2=R, A3=I, A4=I. ZERO kind-3 (inexpressible-changed-op) steps; the operation that actually changed (the new window disjunct) is modeled DEEPLY as the spelled-out OR-fold referencesWindow/aggregateUsesWindow, not hidden behind an axiom about the function under change. Verified mechanically: `grep -c '^\s*axiom ' Solution.lean` = 0, meta.json axioms=[] and deep_model_references=[], G-AX correctly skip.
 * The A-consumed / A-reference legs are VACUOUSLY satisfied and the claim that they SHOULD be vacuous holds: the operands the decision reads (aggregate.get_refs(), self.annotations[ref], contains_over_clause at expressions.py:247 / Window.contains_over_clause=True at 1703 / BaseExpression.contains_over_clause=False at 858) are UNCHANGED by the gold patch and read identically by both branches, so they are shared context rather than a consumed contract. I confirmed this against the real base tree: `git show f8c43aca...:django/db/models/sql/query.py` (get_aggregation, lines 397-457) and expressions.py — the gold diff is exactly the 3 claimed additions (refs_window=False @406; refs_window |= any(getattr(..., "contains_over_clause", True) for ref in aggregate.get_refs()) @423-426; `or refs_window` @457), and nothing in the callee chain moves.
 * MODEL <-> PATCH CORRESPONDENCE holds on the discriminating disjunct: aggregateUsesWindow refs = refs.any id <-> the inner `any(...)`; referencesWindow = OR-fold <-> the cross-loop `|=` accumulation; wrappedEvaluationDecision = priorConditions || referencesWindow <-> the if-disjunction with `or refs_window` appended. A1's set-vs-list latitude (get_refs() is a set; the model uses List Bool) is genuinely observationally exact because the only consumer is a disjunction (order/multiplicity-insensitive) — I probed the reordering lane directly (atk_9/atk_9b fold at the decision site and in a deferred pass) and both resolve.
 * The mapping's most load-bearing boundary claim — the CONSERVATIVE getattr default `True` for an undeterminable reference, absorbed into the model as "that flag is already true" — is a real modeling choice the Lean carrier cannot pin, so I tested it out-of-band: flipping the default to False (probe_default_false.diff) STILL RESOLVES. That is a latent under-constraint of the model (a G-PANEL-2 faithfulness observation, advisory), NOT a G-EQ break: G-EQ requires a verifying same-spec impl whose faithful patch FAILS to resolve, and no attack or probe produced one. Worth recording for the bundle's faithfulness narrative, since the F2P test test_referenced_window_requires_wrapping cannot discriminate the default.
 * conf_skip=true rationale (refinement.md §D / mapping.md §4) checked and accepted: the operands are produced only by aggregate_expr.resolve_expression against a live ORM query graph, so there is no DB-free R/I shadow to fuzz; the R/I legs would otherwise be G-CONF's job, and my A-leg attacks above cover what G-CONF cannot reach.

VERDICT: SOUND. 12 distinct same-spec attacks run (>= the 5 floor) spanning prepatch-bug, partial-domain, boundary/off-by-one, control-flow-effect, quantifier-swap, over-approximation, prior-condition-drop, ungrounded-oracle echo, total-index masking, eager-evaluation, and divergence; prepatch reproduced; a structurally different positive control verifies; and all 4 verifying attacks' faithful patches were MATERIALIZED and RESOLVED under the official harness. No verify⇏correct witness exists for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec impl's faithful refined patch completed-and-failed-to-resolve. 12 same-spec admissible attacks were verified; 8 were rejected by the spec on GENUINELY FALSE residual goals (e.g. atk_3: `referencesWindow aggregates.tail = referencesWindow aggregates`; atk_8: `!aggregates.isEmpty = referencesWindow aggregates`; atk_7: `refs.all id = refs.any id`), and the 4 that verified (atk_5 spec-echo, atk_9 relocated fold, atk_11 one-past-the-end total-index sentinel, atk_12 eager list materialization) are value-equal echoes whose faithful refined patches ALL RESOLVED under the official harness (run_resolve completed=True resolved=True, 4/4). Two extra informational boundary probes also resolved (patch_atk_9b.diff: flags read in a DEFERRED pass after the resolving loop, from the stashed `aggregates` dict; probe_default_false.diff: getattr default flipped True->False). The postcondition `out = wrappedEvaluationDecision priorConditions aggregates` is a TOTAL functional equality under `termination "total"`, so every terminating wrong-VALUE impl fails to verify, and the divergence lane that made the PRIOR G-EQ pass INCONCLUSIVE is now closed by the semantics itself: atk_6 (`while true`) is REJECTED at exit 1 with `Decreasing annotations are required in total correctness semantics`, so no verifying attack can hang the harness and no resolve run was left incomplete.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a pure boolean function
--  of already-resolved metadata: for each aggregate, the per-reference flags
--  recording whether a referenced annotation uses a window function. The
--  machinery that resolves an aggregate's references and each annotation's
--  flag is unchanged and shared by both branches, so it is not consumed as an
--  outside contract. There is no `axiom` declaration and no A-reference deep
--  model of an outside callee.)
-- axioms-end

-- pure-start
/- One aggregate references a window function iff any of its referenced
   annotations uses one. `refs` lists, for a single aggregate, the per-reference
   flags (true = that referenced annotation uses a window function). A reference
   whose flag cannot be determined is treated conservatively as using one
   (handled at the boundary; mapping.md §2). -/
def aggregateUsesWindow (refs : List Bool) : Bool :=
  refs.any (fun b => b)

/- Across a whole list of aggregates, the group references a window function iff
   any single aggregate does. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern, plan §5.4). `aggregates` carries, in
   order, the per-aggregate reference-flag lists. -/
def referencesWindow : List (List Bool) → Bool
  | []        => false
  | a :: rest => aggregateUsesWindow a || referencesWindow rest

@[grind] lemma referencesWindow_nil : referencesWindow [] = false := rfl
@[grind] lemma referencesWindow_cons (a : List Bool) (rest : List (List Bool)) :
    referencesWindow (a :: rest) = (aggregateUsesWindow a || referencesWindow rest) := rfl

/- The aggregation must be evaluated inside a wrapping outer query when either
   the pre-existing structural conditions already demand it (`priorConditions`,
   a shared disjunction the change does not touch — mapping.md §1) OR any
   requested aggregate references an annotation that uses a window function.
   The latter disjunct is what this bundle pins. -/
def wrappedEvaluationDecision (priorConditions : Bool)
    (aggregates : List (List Bool)) : Bool :=
  priorConditions || referencesWindow aggregates
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method wrappedEvaluationDecisionM (priorConditions : Bool) (aggregates : List (List Bool)) return (out : Bool)
  ensures out = wrappedEvaluationDecision priorConditions aggregates
  do
    -- impl-start
    if priorConditions then
      return true
    else
      let mut acc : Bool := false
      let mut i := aggregates.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ aggregates.length
        invariant acc = referencesWindow (aggregates.drop i)
        done_with i = 0
        decreasing i
      do
        let refs := aggregates[i - 1]!
        acc := aggregateUsesWindow refs || acc
        i := i - 1
      return acc
    -- impl-end

/- The backward-fold step: dropping one fewer aggregate exposes the aggregate at
   `i-1` on the front, so `referencesWindow` peels one `aggregateUsesWindow`.
   This is the single goal `loom_solve` leaves for the loop body. -/
lemma referencesWindow_drop_step (aggregates : List (List Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ aggregates.length) :
    referencesWindow (aggregates.drop (i - 1))
      = (aggregateUsesWindow aggregates[i - 1]! || referencesWindow (aggregates.drop i)) := by
  have hlt : i - 1 < aggregates.length := by omega
  have hcons : aggregates.drop (i - 1) = aggregates[i - 1]! :: aggregates.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, referencesWindow_cons]

prove_correct wrappedEvaluationDecisionM by
  loom_solve <;>
    first
      | (rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]; simp_all)
      | simp_all [wrappedEvaluationDecision]
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (all work; nothing written elsewhere).

SAME-SPEC: all 12 attacks + positive control are same_spec=True AND variant_scope.variant_problems=[] (admissible: no new axioms/lemmas, no sorry/admit/native_decide, prove_correct obligation retained). Only the impl region and the prove_correct tactic BODY differ (spec_view elides both; axioms/pure/pre/post byte-identical).
  CMD: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>').read(), b.language))"

### ATTACK LEDGER (CMD for each: bash scripts/lean_verify.sh <f>.lean; verifications run concurrently in background batches of 4)
 | file | wrong-impl class | verify exit | outcome |
 |---|---|---|---|
 | atk_1  | PREPATCH BUG: window disjunct absent, aggregates never inspected | 1 | rejected (false goal: aggregateUsesWindow aggregates[i-1]! = true -> referencesWindow (drop i) = true) |
 | atk_2  | PARTIAL DOMAIN: only the FIRST aggregate inspected | 1 | rejected (match-on-head vs full fold) |
 | atk_3  | BOUNDARY off-by-one: first aggregate skipped (drop 1) | 1 | rejected (referencesWindow tail vs referencesWindow) |
 | atk_4  | CONTROL-FLOW EFFECT: early loop exit on hit without recording it | 1 | rejected (invariant + ensures both fail) |
 | atk_5  | UNGROUNDED-ORACLE ECHO: `return wrappedEvaluationDecision ...` | 0 | CANDIDATE -> patch RESOLVED (echo, not a weakness) |
 | atk_6  | DIVERGENCE (partial-correctness artifact): `while true`, return false | 1 | rejected: "Decreasing annotations are required in total correctness semantics" |
 | atk_7  | QUANTIFIER SWAP: refs.all instead of refs.any per aggregate | 1 | rejected (all vs any) |
 | atk_8  | OVER-APPROXIMATION: wrap whenever any aggregate requested | 1 | rejected (!isEmpty vs fold) |
 | atk_9  | RELOCATED FOLD: whole fold at the decision site, no loop | 0 | CANDIDATE -> patch RESOLVED (echo) |
 | atk_10 | PRIOR-CONDITIONS DROPPED: structural disjunct ignored | 1 | rejected (priorConditions = true -> acc = true is false) |
 | atk_11 | BOUNDARY/total-default masking: extra read ONE PAST THE END seeds acc (Lean [i]! is TOTAL -> default = []) | 0 | CANDIDATE -> patch RESOLVED (echo) |
 | atk_12 | EAGER MATERIALIZATION: refs.map before the disjunction (probes mapping.md §2's any-short-circuit claim) | 0 | CANDIDATE -> patch RESOLVED (echo) |
 POSITIVE CONTROL: pos_control.lean — structurally different but correct (short-circuits on priorConditions, THEN the backward fold in the else branch) — exit 0, VERIFIES.
 PREPATCH REPRODUCED: yes, twice over — atk_1 (my re-encoding, exit 1) and the shipped Solution_prepatch.lean (G-DIFF pass: "verification failed").

RESOLVE RUNS (official harness; run concurrently). CMD: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-17084', open('<patch>').read()); print(r.completed, r.resolved, r.note)"
 | patch_atk_5.diff  | completed=True resolved=True note=resolved |
 | patch_atk_9.diff  | completed=True resolved=True note=resolved |
 | patch_atk_11.diff | completed=True resolved=True note=resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete) |
 | patch_atk_12.diff | completed=True resolved=True note=resolved |
 | patch_atk_9b.diff (extra probe: DEFERRED read placement) | completed=True resolved=True note=resolved |
 | probe_default_false.diff (extra probe: getattr default True->False) | completed=True resolved=True note=resolved |
 Every needed resolve run COMPLETED — no INCONCLUSIVE measurement. 4/4 verifying attacks resolve => no verify⇏correct witness.

WHY THE PRIOR G-EQ FAIL IS CLOSED: the previous pass recorded INCONCLUSIVE because its only verifying non-value-correct impl was a DIVERGING one (`while true`) under `termination "partial"`, whose faithful patch (an infinite loop in get_aggregation) hung the harness (completed=False, 900s). The frozen spec now sets `loom.semantics.termination "total"` / `open TotalCorrectness`; I re-encoded that exact counterexample as atk_6 and it is now REJECTED outright (loom demands a `decreasing` clause). The divergence lane is therefore eliminated by the spec, not merely unmeasured.

A-LEG / refinement.md AUDIT (the assigned focus):
 * Leg taxonomy is complete and legal: 4 legs, A1=R, A2=R, A3=I, A4=I. ZERO kind-3 (inexpressible-changed-op) steps; the operation that actually changed (the new window disjunct) is modeled DEEPLY as the spelled-out OR-fold referencesWindow/aggregateUsesWindow, not hidden behind an axiom about the function under change. Verified mechanically: `grep -c '^\s*axiom ' Solution.lean` = 0, meta.json axioms=[] and deep_model_references=[], G-AX correctly skip.
 * The A-consumed / A-reference legs are VACUOUSLY satisfied and the claim that they SHOULD be vacuous holds: the operands the decision reads (aggregate.get_refs(), self.annotations[ref], contains_over_clause at expressions.py:247 / Window.contains_over_clause=True at 1703 / BaseExpression.contains_over_clause=False at 858) are UNCHANGED by the gold patch and read identically by both branches, so they are shared context rather than a consumed contract. I confirmed this against the real base tree: `git show f8c43aca...:django/db/models/sql/query.py` (get_aggregation, lines 397-457) and expressions.py — the gold diff is exactly the 3 claimed additions (refs_window=False @406; refs_window |= any(getattr(..., "contains_over_clause", True) for ref in aggregate.get_refs()) @423-426; `or refs_window` @457), and nothing in the callee chain moves.
 * MODEL <-> PATCH CORRESPONDENCE holds on the discriminating disjunct: aggregateUsesWindow refs = refs.any id <-> the inner `any(...)`; referencesWindow = OR-fold <-> the cross-loop `|=` accumulation; wrappedEvaluationDecision = priorConditions || referencesWindow <-> the if-disjunction with `or refs_window` appended. A1's set-vs-list latitude (get_refs() is a set; the model uses List Bool) is genuinely observationally exact because the only consumer is a disjunction (order/multiplicity-insensitive) — I probed the reordering lane directly (atk_9/atk_9b fold at the decision site and in a deferred pass) and both resolve.
 * The mapping's most load-bearing boundary claim — the CONSERVATIVE getattr default `True` for an undeterminable reference, absorbed into the model as "that flag is already true" — is a real modeling choice the Lean carrier cannot pin, so I tested it out-of-band: flipping the default to False (probe_default_false.diff) STILL RESOLVES. That is a latent under-constraint of the model (a G-PANEL-2 faithfulness observation, advisory), NOT a G-EQ break: G-EQ requires a verifying same-spec impl whose faithful patch FAILS to resolve, and no attack or probe produced one. Worth recording for the bundle's faithfulness narrative, since the F2P test test_referenced_window_requires_wrapping cannot discriminate the default.
 * conf_skip=true rationale (refinement.md §D / mapping.md §4) checked and accepted: the operands are produced only by aggregate_expr.resolve_expression against a live ORM query graph, so there is no DB-free R/I shadow to fuzz; the R/I legs would otherwise be G-CONF's job, and my A-leg attacks above cover what G-CONF cannot reach.

VERDICT: SOUND. 12 distinct same-spec attacks run (>= the 5 floor) spanning prepatch-bug, partial-domain, boundary/off-by-one, control-flow-effect, quantifier-swap, over-approximation, prior-condition-drop, ungrounded-oracle echo, total-index masking, eager-evaluation, and divergence; prepatch reproduced; a structurally different positive control verifies; and all 4 verifying attacks' faithful patches were MATERIALIZED and RESOLVED under the official harness. No verify⇏correct witness exists for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No faithfulness defect found. The modeled function agrees with the real post-patch callee on every input I could reach, including 11 live discriminating cells.

### What was checked

1. Spec-region identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. Dumped both spec_views; they are identical (pure region, ensures clause, pre/post regions all match; only impl-start/impl-end and the prove_correct body differ, which are elided).

2. Artifact verifies: scripts/lean_verify.sh Solution.lean -> exit 0, no sorry/admit.

3. patch.diff is the gold patch verbatim (byte-compare against instance.json['patch'] -> True, 1421 bytes). Three additions only: refs_window=False (406), the refs_window |= any(getattr(..., 'contains_over_clause', True) for ref in aggregate.get_refs()) accumulation (423-426), and 'or refs_window' in the guard (457). Confirmed against base_commit f8c43aca.

4. LIVE DIFFERENTIAL ORACLE (the core test). Built a worktree at base_commit, applied gold + test patch, then instrumented get_aggregation to record on every call the exact Lean carrier (per-aggregate list of resolved contains_over_clause flags, collected in aggregate_exprs order into a call-LOCAL list so nested/recursive get_aggregation calls cannot interleave), priorConditions (the 7 unchanged operands OR'd, refs_window excluded), and the ACTUAL guard value. Compared against wrappedEvaluationDecision transliterated verbatim from the pure region.
   - Broad sweep (aggregation, aggregation_regress, annotations, expressions, expressions_case, expressions_window, queries, lookup, ordering, db_functions): 381 observations, 0 mismatches.
   - Purpose-built adversarial app (window annotation referenced vs merely annotated; multiple window annotations; window nested under ExpressionWrapper/Case-When; Rank/RowNumber; window + Subquery; window under distinct/sliced/values; filtered aggregate over window; aggregate referencing another aggregate's mid-loop alias in both orders; plain no-window controls): 22 observations, 0 mismatches, with coverage prior=False/window=True/actual=True x11, prior=True/window=True x1, prior=False/window=False x3. Multi-aggregate carriers exercised, e.g. [[False],[],[],[],[True]], [[True],[True]], [[],[True]].
   - F2P test_referenced_window_requires_wrapping passes on the patched tree (all 7 AggregateAnnotationPruningTests ok).

5. Exhaustive fold equivalence: all carriers up to 4 aggregates x 0-3 refs each x all boolean assignments x both priorConditions = 108,482 cases. model == real Python |=/any accumulation == the Lean backward while-loop impl. 0 divergences. This closes the order/duplicate-insensitivity claim in mapping.md §2 (get_refs() is a set; the OR-fold is commutative/idempotent, so the List Bool model is observationally exact).

6. Domain edges: at aggregates=[] the model returns priorConditions, and the real guard is unreachable there (early 'if not aggregate_exprs: return {}'), so the model makes no false claim about reachable behavior. Not-an-aggregate inputs raise TypeError before the guard. All 8 guard operands are already-computed locals or plain attributes, so Python's value-returning/short-circuiting 'or' is observationally equal to the Lean Bool '||' chain for the if's truthiness — no side effects and no operand whose evaluation order matters.

DISCRIMINATION / ANTI-VACUITY CONTROLS

7. Prepatch rival fails at exactly the discriminating obligation: 'unsolved goals, invariant_2: acc = referencesWindow (aggregates.drop i)', goal aggregateUsesWindow aggregates[i-1] = true -> referencesWindow (drop i) = true. G-DIFF is genuine, not an incidental break.

8. Mutation controls on the artifact: impl drops the window disjunct -> exit 1; impl drops priorConditions -> exit 1; referencesWindow cons || -> && -> exit 1; loop body stops accumulating -> exit 1. (Note: my first mutation run reported all-pass because $(basename) in the echo clobbered $?; rerun with the exit code captured before any substitution gave the results above. Flagging so nobody reuses the broken loop.)

9. Oracle-power control (guards against a rubber stamp): mutating the PURE def (any->all, ||->&&) still verifies under G-VERIFY, because spec and impl move together — so G-VERIFY alone cannot police faithfulness of the pure def. I therefore replayed the recorded live carriers through those mutant models: any->all diverges from the real callee on the observed carrier [[]] (model True, real False) and ||->&& diverges on 6 observed carriers. The true spec showed 0 divergences on the same carriers. The oracle demonstrably has the power to detect an unfaithful pure def, and did not fire on the shipped one.

### Observations not rising to a defect

- The getattr(..., 'contains_over_clause', True) default-True branch never fired in any live run (every annotation reached was a real Expression with the cached_property). The model handles this at the boundary (such a reference simply enters as flag=true), so it is a carrier-population concern rather than a disagreement between the modeled function and the callee; I could not construct a reachable input where it changes the guard.
- mapping.md §4 / refinement.md §D justify conf_skip=true by asserting there is 'no DB-free R/I shadow' and the discriminator is 'reproducible only by the F2P integration test itself, not as a pure transliteration a gate can fuzz'. That rationale is overstated: I built a working differential harness against sqlite in roughly 30 lines that reaches 11 discriminating window=True cells, and the pure fold is exhaustively fuzzable (item 5). The skip is defensible in that the CARRIER requires a live ORM to populate, but the stated 'not fuzzable' framing is stronger than the facts. This is a documentation-quality issue for whoever owns G-CONF policy, not a spec-too-strong or drift defect, so it does not change my verdict.

CLEANUP: my worktree was removed and pruned; other worktrees in the listing belong to concurrent processes and were left untouched. No git operations were run against the shared tree beyond worktree add/remove of my own scratch.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** METHOD. (1) Recomputed the spec view with markers.spec_view under the velvet backend and read the full 79-line projection. (2) same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region byte-identical, so the discriminator lives only in the elided impl/prove_correct body, not the consumer view. (3) Ran leakage.screen with the frozen instance row: zero hard failures. Confirmed mechanically that no gold-patch line is reproduced, the patched path django/db/models/sql/query.py and its dotted form are absent, and the single distinctive changed symbol (`get_aggregation`) appears in no spec-view identifier or comment. `refs_window`, `contains_over_clause`, `get_refs` are all absent. Narration vocabulary (bug/fix/patched/regression/...) is clean. (4) Ran the counterfactual reconstruction experiment above, which is the substantive test my role turns on rather than the mechanical screen.

EXPERIMENT INTEGRITY. My first attempt was VOID and I discarded it: I placed the control and spec-view arms in one shared worktree, so the control arm found the spec-view arm's patch already applied to query.py and was reporting on a pre-patched tree by its own admission. I re-ran with five isolated per-agent worktrees, read-only instructions, an explicit ban on git log/--all/branch -a/stash, and 3 replicates for the discriminating detail. All experiment worktrees have been removed and the bare repo's worktree list is clean.

WHY NO-LEAKAGE. The spec view encodes the abstract desired BEHAVIOR — wrap the aggregation in an outer query when the pre-existing structural conditions hold OR any requested aggregate references a window-using annotation — which is exactly what directive 6 requires a spec to state ('state the abstract desired behavior; never the edit or the diagnosis'). It does not disclose the edit's mechanism or location: no accumulator variable, no attribute name, no getattr, no insertion point in get_aggregation's disjunction, no file/line. The public problem_statement already discloses that aggregate-over-Window fails with GroupingError and gives the exact Sum("cumul_DJR")-over-Window(Sum(...)) shape, so 'aggregate referencing a window-using annotation must be evaluated in a wrapping query' is a direct inference from the public task. No hints_text term is echoed (hints_text here is only a maintainer asking for a reproduction project, and nothing from it appears). The Lean names wrappedEvaluationDecision / referencesWindow / aggregateUsesWindow / priorConditions are abstract model symbols, not repo symbols.

BORDERLINE ITEM, recorded honestly rather than suppressed. The 'treated conservatively as using one' clause is the closest thing to a mechanism hint in the view: it is the only sentence that pins a boundary decision the problem_statement never mentions, and its natural Python realization is precisely the default-True getattr. I judge it non-leaking because it is independently derivable (3/3 controls) and because it is phrased at the Bool-flag level rather than naming the attribute-missing mechanism. But it is also verifiably NON-LOAD-BEARING, so removing it is free hygiene: I deleted the clause from both files and confirmed (a) Solution.lean still verifies clean under scripts/lean_verify.sh (exit 0), (b) the de-narrated prepatch still FAILS (exit 1), preserving G-DIFF, and (c) same_spec still holds between the two de-narrated files. Recommendation (optional, not a gate failure): drop that clause and keep the boundary note in mapping.md §2, which is not part of the screened consumer view. This removes the only sentence a future attacker could argue over at zero cost to verification.

SCOPE. I reviewed leakage only. I did not assess spec strength or faithfulness; note for the record that meta.json carries G-PANEL-1 fail and G-EQ fail on this bundle, and nothing in my analysis speaks to those — a clean leakage verdict does not imply the bundle is releasable.

Counterexample / evidence:

```
None — the one leak hypothesis I formed was empirically falsified. Hypothesis: the pure-region comment 'A reference whose flag cannot be determined is treated conservatively as using one (handled at the boundary; mapping.md §2)' encodes the gold edit's non-obvious getattr default, i.e. that `getattr(self.annotations[ref], "contains_over_clause", True)` defaults True rather than False. This detail is absent from problem_statement (verified: 'conservat', 'cannot be determined', 'default', 'missing', 'attribute', 'getattr', 'contains_over_clause' all absent). Refutation by controlled reconstruction: 3 independent replicate agents, each in its own clean read-only worktree at base_commit f8c43aca, given ONLY the public problem_statement (no spec view, git history/stashes forbidden), all three independently produced the gold patch and all three chose default `True`, at confidence 90/90/88. Each cited repo-local precedent discoverable without the spec: `getattr(annotation, "contains_aggregate", True)` at query.py:434, the sibling conservative default inside the very same function, and each correctly distinguished it from the non-parallel `getattr(..., "subquery", False)` at line 419. The default is therefore recoverable from problem_statement + repo, not privileged information the spec view uniquely supplies. The spec-view arm's self-report that the default 'came only from the specification' is a post-hoc attribution artifact (it had the spec, so it credited the spec) and is contradicted by the controls.
```

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
