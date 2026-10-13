# P2 adversarial audit — matplotlib__matplotlib-24177

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_start_short.lean`, `atk_3_reverse.lean`, `atk_4_empty.lean`, `atk_5_step2.lean`, `atk_6_dup.lean`, `atk_8_skipfirst.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_oracle.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a single exact-equality total functional postcondition `out = collectAll segs`, where `collectAll` is concrete structural recursion (in-order concatenation of EVERY segment's point list). Every behaviorally-wrong impl is unprovable; the only verifying same-spec attack (ungrounded-oracle echo `return collectAll segs`) is behaviorally identical to gold, and its faithful refined patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,10 +69,10 @@
     -- impl-start
     let mut result : List Vertex := []
     let mut i := segs.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ segs.length
       invariant result = collectAll (segs.drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let s := segs[i - 1]!
```

Attack 2 — `atk_2_start_short.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,7 +68,7 @@
   do
     -- impl-start
     let mut result : List Vertex := []
-    let mut i := segs.length
+    let mut i := segs.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ segs.length
       invariant result = collectAll (segs.drop i)
```

Attack 3 — `atk_3_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
       decreasing i
     do
       let s := segs[i - 1]!
-      result := s ++ result
+      result := result ++ s
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,17 +67,7 @@
   ensures out = collectAll segs
   do
     -- impl-start
-    let mut result : List Vertex := []
-    let mut i := segs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ segs.length
-      invariant result = collectAll (segs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := segs[i - 1]!
-      result := s ++ result
-      i := i - 1
+    let result : List Vertex := []
     return result
     -- impl-end
 
```

Attack 5 — `atk_5_step2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
     do
       let s := segs[i - 1]!
       result := s ++ result
-      i := i - 1
+      i := i - 2
     return result
     -- impl-end
 
```

Attack 6 — `atk_6_dup.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
       decreasing i
     do
       let s := segs[i - 1]!
-      result := s ++ result
+      result := s ++ s ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,21 +67,8 @@
   ensures out = collectAll segs
   do
     -- impl-start
-    let mut result : List Vertex := []
-    let mut i := segs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ segs.length
-      invariant result = collectAll (segs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let s := segs[i - 1]!
-      result := s ++ result
-      i := i - 1
-    return result
+    return collectAll segs
     -- impl-end
 
 prove_correct collectVertices by
   loom_solve
-  rw [collectAll_drop_step segs i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_8_skipfirst.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
       done_with i = 0
       decreasing i
     do
-      let s := segs[i - 1]!
+      let s := (if i - 1 = 0 then ([] : List Vertex) else segs[i - 1]!)
       result := s ++ result
       i := i - 1
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is
--  a pure structural expansion: the input is a list of groups, each group
--  already given as its own list of points. How a single group's point list is
--  produced is the identical, unchanged upstream computation and is not modeled
--  here (refinement.md §B / mapping.md §3); it is reproduced verbatim by the
--  conformance bridge. The collected point list is a pure function of the input
--  list of groups, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- A single collected point. This model pins WHICH points are collected and in
   what order, not their coordinate values, so the point payload is kept
   abstract; the conformance bridge supplies the real coordinates. -/
opaque Vertex : Type

/- The points collected from a list of groups: the in-order concatenation of the
   per-group point lists, over EVERY group, with every group's points retained.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def collectAll : List (List Vertex) → List Vertex
  | []      => []
  | s :: ss => s ++ collectAll ss

@[grind] lemma collectAll_nil : collectAll [] = [] := rfl
@[grind] lemma collectAll_cons (s : List Vertex) (ss : List (List Vertex)) :
    collectAll (s :: ss) = s ++ collectAll ss := rfl

/- The backward-fold step: dropping one fewer group exposes the group at
   index `i-1` on the front, so `collectAll` peels one group's point list. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma collectAll_drop_step (segs : List (List Vertex)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ segs.length) :
    collectAll (segs.drop (i - 1)) = segs[i - 1]! ++ collectAll (segs.drop i) := by
  have hlt : i - 1 < segs.length := by omega
  have hcons : segs.drop (i - 1) = segs[i - 1]! :: segs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectAll_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the points of a list of groups. `segs` is the input list of groups,
   each already given as its own list of points; it is read-only (not `mut`) —
   the operation reads it and returns a fresh list (directive 5).

   Desired behaviour: the collected list is the in-order concatenation of the
   point lists of ALL the groups, with no group's points dropped on the way.
   Every group must contribute every one of its points; the result therefore
   contains exactly the points of every group, in order. -/
method collectVertices (segs : List (List Vertex)) return (out : List Vertex)
  ensures out = collectAll segs
  do
    -- impl-start
    let mut result : List Vertex := []
    let mut i := segs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ segs.length
      invariant result = collectAll (segs.drop i)
      done_with i = 0
      decreasing i
    do
      let s := segs[i - 1]!
      result := s ++ result
      i := i - 1
    return result
    -- impl-end

prove_correct collectVertices by
  loom_solve
  rw [collectAll_drop_step segs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True verified for all 8 attacks + positive control (impl+prove_correct regions collapse in velvet spec_view; axioms/pure/pre/post/method-sig/ensures kept byte-identical). Verified via `bash scripts/lean_verify.sh <f>` run concurrently (<=4 jobs).

### Results
- pos_control (exact gold impl): EXIT 0 (verifies) -> spec non-vacuous.
- atk_1_prepatch (loop guard i>1, drops leading segment = the prepatch bug): EXIT 1 (fails on ensures `result_1 = collectAll segs`). PREPATCH REPRODUCED.
- atk_2_start_short (i := segs.length-1, drops last segment; boundary): EXIT 1.
- atk_3_reverse (result := result ++ s, wrong order): EXIT 1.
- atk_4_empty (return []; partial/degenerate): EXIT 1 (unsolved `[] = collectAll segs`).
- atk_5_step2 (i := i-2, control-flow-effect skipping segments): EXIT 1.
- atk_6_dup (result := s ++ s ++ result, wrong multiplicity): EXIT 1.
- atk_7_oracle (ungrounded-oracle echo: return collectAll segs; proof loom_solve): EXIT 0 (VERIFIES).
- atk_8_skipfirst (zero out segment at index 0; partial-domain): EXIT 1.

So 7/8 genuinely-wrong impls are correctly REJECTED; the ONLY verifying same-spec attack is atk_7, which is behaviorally CORRECT (returns exactly collectAll segs = all segments enumerated in order). Per protocol its faithful refined patch was MATERIALIZED (= enumerate every segment = `iter_bezier(simplify=False)`, byte-identical to gold patch.diff, which I confirmed == frozen-dataset gold) and RUN through the official harness: run_resolve('matplotlib__matplotlib-24177', patch) -> RESOLVED=True (ran under `docker`, exit 0). So verify DOES imply correct here.

REFINEMENT.MD AUDIT: legs A1/A2/A3 are labels only; actual tags are R (input abstraction), I (concrete fold/row_stack), R (extent = min/max over points). No kind-3. There are genuinely NO A-legs: meta.json axioms=[] and deep_model_references=[] (confirmed), G-AX=skip 'no axiom_check.py (no axioms in bundle)', and Solution.lean has zero `axiom` declarations / zero `:|` stubs (only comments + payload-less `opaque Vertex : Type`, which carries no behavior to echo). So there is no A-leg correspondence obligation and no ungrounded oracle to exploit — the echo attack must actually COMPUTE collectAll, hence is behaviorally the gold.

VERDICT: SOUND. The spec is a tight exact-equality functional postcondition over a grounded concrete recursion; no verifying wrong impl's faithful patch fails to resolve. >=8 attacks run (>=5 required), positive control verifies, prepatch reproduced, and the one verifying candidate's materialized patch was executed through run_resolve (RESOLVED=True). verify does NOT imply incorrect here => spec not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_start_short.lean`, `atk_3_reverse.lean`, `atk_4_empty.lean`, `atk_5_step2.lean`, `atk_6_dup.lean`, `atk_8_skipfirst.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_oracle.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a single exact-equality total functional postcondition `out = collectAll segs`, where `collectAll` is concrete structural recursion (in-order concatenation of EVERY segment's point list). Every behaviorally-wrong impl is unprovable; the only verifying same-spec attack (ungrounded-oracle echo `return collectAll segs`) is behaviorally identical to gold, and its faithful refined patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_start_short.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_reverse.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_empty.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_step2.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_dup.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_skipfirst.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is
--  a pure structural expansion: the input is a list of groups, each group
--  already given as its own list of points. How a single group's point list is
--  produced is the identical, unchanged upstream computation and is not modeled
--  here (refinement.md §B / mapping.md §3); it is reproduced verbatim by the
--  conformance bridge. The collected point list is a pure function of the input
--  list of groups, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- A single collected point. This model pins WHICH points are collected and in
   what order, not their coordinate values, so the point payload is kept
   abstract; the conformance bridge supplies the real coordinates. -/
opaque Vertex : Type

/- The points collected from a list of groups: the in-order concatenation of the
   per-group point lists, over EVERY group, with every group's points retained.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def collectAll : List (List Vertex) → List Vertex
  | []      => []
  | s :: ss => s ++ collectAll ss

@[grind] lemma collectAll_nil : collectAll [] = [] := rfl
@[grind] lemma collectAll_cons (s : List Vertex) (ss : List (List Vertex)) :
    collectAll (s :: ss) = s ++ collectAll ss := rfl

/- The backward-fold step: dropping one fewer group exposes the group at
   index `i-1` on the front, so `collectAll` peels one group's point list. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma collectAll_drop_step (segs : List (List Vertex)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ segs.length) :
    collectAll (segs.drop (i - 1)) = segs[i - 1]! ++ collectAll (segs.drop i) := by
  have hlt : i - 1 < segs.length := by omega
  have hcons : segs.drop (i - 1) = segs[i - 1]! :: segs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectAll_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the points of a list of groups. `segs` is the input list of groups,
   each already given as its own list of points; it is read-only (not `mut`) —
   the operation reads it and returns a fresh list (directive 5).

   Desired behaviour: the collected list is the in-order concatenation of the
   point lists of ALL the groups, with no group's points dropped on the way.
   Every group must contribute every one of its points; the result therefore
   contains exactly the points of every group, in order. -/
method collectVertices (segs : List (List Vertex)) return (out : List Vertex)
  ensures out = collectAll segs
  do
    -- impl-start
    let mut result : List Vertex := []
    let mut i := segs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ segs.length
      invariant result = collectAll (segs.drop i)
      done_with i = 0
      decreasing i
    do
      let s := segs[i - 1]!
      result := s ++ result
      i := i - 1
    return result
    -- impl-end

prove_correct collectVertices by
  loom_solve
  rw [collectAll_drop_step segs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True verified for all 8 attacks + positive control (impl+prove_correct regions collapse in velvet spec_view; axioms/pure/pre/post/method-sig/ensures kept byte-identical). Verified via `bash scripts/lean_verify.sh <f>` run concurrently (<=4 jobs).

### Results
- pos_control (exact gold impl): EXIT 0 (verifies) -> spec non-vacuous.
- atk_1_prepatch (loop guard i>1, drops leading segment = the prepatch bug): EXIT 1 (fails on ensures `result_1 = collectAll segs`). PREPATCH REPRODUCED.
- atk_2_start_short (i := segs.length-1, drops last segment; boundary): EXIT 1.
- atk_3_reverse (result := result ++ s, wrong order): EXIT 1.
- atk_4_empty (return []; partial/degenerate): EXIT 1 (unsolved `[] = collectAll segs`).
- atk_5_step2 (i := i-2, control-flow-effect skipping segments): EXIT 1.
- atk_6_dup (result := s ++ s ++ result, wrong multiplicity): EXIT 1.
- atk_7_oracle (ungrounded-oracle echo: return collectAll segs; proof loom_solve): EXIT 0 (VERIFIES).
- atk_8_skipfirst (zero out segment at index 0; partial-domain): EXIT 1.

So 7/8 genuinely-wrong impls are correctly REJECTED; the ONLY verifying same-spec attack is atk_7, which is behaviorally CORRECT (returns exactly collectAll segs = all segments enumerated in order). Per protocol its faithful refined patch was MATERIALIZED (= enumerate every segment = `iter_bezier(simplify=False)`, byte-identical to gold patch.diff, which I confirmed == frozen-dataset gold) and RUN through the official harness: run_resolve('matplotlib__matplotlib-24177', patch) -> RESOLVED=True (ran under `docker`, exit 0). So verify DOES imply correct here.

REFINEMENT.MD AUDIT: legs A1/A2/A3 are labels only; actual tags are R (input abstraction), I (concrete fold/row_stack), R (extent = min/max over points). No kind-3. There are genuinely NO A-legs: meta.json axioms=[] and deep_model_references=[] (confirmed), G-AX=skip 'no axiom_check.py (no axioms in bundle)', and Solution.lean has zero `axiom` declarations / zero `:|` stubs (only comments + payload-less `opaque Vertex : Type`, which carries no behavior to echo). So there is no A-leg correspondence obligation and no ungrounded oracle to exploit — the echo attack must actually COMPUTE collectAll, hence is behaviorally the gold.

VERDICT: SOUND. The spec is a tight exact-equality functional postcondition over a grounded concrete recursion; no verifying wrong impl's faithful patch fails to resolve. >=8 attacks run (>=5 required), positive control verifies, prepatch reproduced, and the one verifying candidate's materialized patch was executed through run_resolve (RESOLVED=True). verify does NOT imply incorrect here => spec not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for velvet bundle matplotlib__matplotlib-24177.

SPEC-REGION BYTE-IDENTITY: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True. The consumer spec view (axioms/pure/pre/post regions + method signature + `ensures out = collectAll segs`) is byte-identical between the verifying Solution and the prepatch skeleton; only the elided impl/proof differ (loop guard i>0 in Solution vs i>1 in prepatch). Spec is genuinely frozen. Solution.lean verifies under scripts/lean_verify.sh (exit 0, real total-correctness proof via loom_solve + collectAll_drop_step, no sorry).

MODEL vs REAL CALLEE: Modeled function collectVertices(segs) returns out with postcondition out = collectAll segs, where collectAll is the in-order concatenation of EVERY element of segs. Per mapping.md §2, segs is the per-segment point arrays [curve([0,*dzeros,1]) for curve,code in path.iter_bezier(simplify=False)] produced by the UNCHANGED upstream and supplied as input. The real patched Axes._update_patch_limits (verified in the worktree at base_commit a302267d / v3.6.0, and via the installed matplotlib 3.6.3 which carries the fix and served as the oracle) builds `vertices` by appending exactly those arrays for every segment then np.row_stack(vertices); under the identity data transform the extent is the componentwise min/max over those points. collectAll (concat of all segments) exactly mirrors np.row_stack over all iter_bezier(simplify=False) segments. Vertex payload is opaque/coordinate-agnostic; the conformance bridge runs the real upstream to build segs, so no fabricated behavior. Empty path (collectAll [] = []) handled on both sides. The spec demands 'collect every segment's points in order', which is precisely what simplify=False yields — neither too strong nor drifting.

EMPIRICAL: conformance_check.py (seed 24177) ran to completion against the patched oracle over 100,000 fuzzed inputs plus all boundary cases (the issue's flat small-valued outline, single line, single point, triangle, cubic curve): EXIT 0 = zero R/I disagreements. Independent reduced run over 3005 inputs (incl. all boundary cases): 0 disagreements. No diverging input found; the modeled function agrees with the real callee on every tested input.

VERDICT: FAITHFUL — the spec faithfully models the real repo behavior; it is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[]) and same_spec(Solution, Solution_prepatch)=True. Reviewed the full consumer spec view (markers.spec_view over velvet tables) for SEMANTIC gold reconstruction beyond the PUBLIC problem_statement (hints_text explicitly excluded).

Gold edit: p.iter_bezier() -> p.iter_bezier(simplify=False) in _update_patch_limits (enumerate EVERY Bezier segment instead of a simplified/reduced subset when building the patch's data extent).

Public problem_statement gives only the SYMPTOM: histtype='step' density axis not auto-scaled to fit the whole histogram; rescaling data wrongly changes densities. It never names iter_bezier, simplify, Bezier segments, path simplification, or segment-dropping. Those mechanism details live ONLY in hints_text (the #19214 / iter_bezier explanation), which must not be used to judge leakage.

Spec view is fully abstracted: opaque Vertex, a generic 'list of groups, each a list of points', collectVertices/collectAll. It contains NO matplotlib symbols, NOT the changed repo symbol (_update_patch_limits / update_patch_limits absent), no patched file/module path, no diff markers, no iter_bezier/simplify/Bezier/path/histogram terms, and no narration keywords. The behavioral claim ('in-order concatenation over EVERY group, no group's points dropped') is exactly the correct-behavior spec and is derivable from the PUBLIC symptom (extent fails to bound all data => points dropped); it does not reproduce the gold diff line nor reveal the hints-only mechanism (which call, which flag). A solver sees an abstract list-concatenation obligation, not a localization of the edit to iter_bezier(simplify=False).

refinement.md and mapping.md DO name iter_bezier/simplify/_update_patch_limits, but they are auditor artifacts self-labeled 'refinement audit only, not in the consumer spec view' and are out of G-PANEL-3 / spec-view scope. No leak beyond problem_statement in the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
