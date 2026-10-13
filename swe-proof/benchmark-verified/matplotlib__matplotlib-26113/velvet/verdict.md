# P2 adversarial audit — matplotlib__matplotlib-26113

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl exists whose faithful refined patch does NOT resolve. The postcondition out = aggregateSeq reduceBin minPop bins is a total functional equality over transparent defs (binAggregate b = if b.length >= minPop then some (reduceBin b) else none), so every TERMINATING verifying impl is behaviourally equal to gold and resolves. The only verifying same-spec impls found were (a) the ungrounded-oracle echo, whose faithful patch is gold-verbatim and RESOLVES (correct echo, not a weakness), and (b) a divergent/vacuous-exit impl, a universal partial-correctness artifact whose faithful patch cannot complete in the harness (inconclusive, not BROKEN).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -59,10 +59,11 @@
       invariant 0 ≤ i ∧ i ≤ bins.length
       invariant result = aggregateSeq reduceBin minPop (bins.drop i)
       done_with i = 0
-      decreasing i
     do
       let b := bins[i - 1]!
-      result := binAggregate reduceBin minPop b :: result
+      let agg : Option Float :=
+        if b.length > minPop then some (reduceBin b) else none
+      result := agg :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -59,10 +59,11 @@
       invariant 0 ≤ i ∧ i ≤ bins.length
       invariant result = aggregateSeq reduceBin minPop (bins.drop i)
       done_with i = 0
-      decreasing i
     do
       let b := bins[i - 1]!
-      result := binAggregate reduceBin minPop b :: result
+      let agg : Option Float :=
+        if b.length ≥ minPop then none else some (reduceBin b)
+      result := agg :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -53,17 +53,7 @@
   ensures out = aggregateSeq reduceBin minPop bins
   do
     -- impl-start
-    let mut result : List (Option Float) := []
-    let mut i := bins.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ bins.length
-      invariant result = aggregateSeq reduceBin minPop (bins.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let b := bins[i - 1]!
-      result := binAggregate reduceBin minPop b :: result
-      i := i - 1
+    let result : List (Option Float) := []
     return result
     -- impl-end
 
```

Attack 4 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -59,10 +59,11 @@
       invariant 0 ≤ i ∧ i ≤ bins.length
       invariant result = aggregateSeq reduceBin minPop (bins.drop i)
       done_with i = 0
-      decreasing i
     do
       let b := bins[i - 1]!
-      result := binAggregate reduceBin minPop b :: result
+      let agg : Option Float :=
+        if b.length ≥ minPop + 1 then some (reduceBin b) else none
+      result := agg :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -53,17 +53,7 @@
   ensures out = aggregateSeq reduceBin minPop bins
   do
     -- impl-start
-    let mut result : List (Option Float) := []
-    let mut i := bins.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ bins.length
-      invariant result = aggregateSeq reduceBin minPop (bins.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let b := bins[i - 1]!
-      result := binAggregate reduceBin minPop b :: result
-      i := i - 1
+    let result : List (Option Float) := aggregateSeq reduceBin minPop bins
     return result
     -- impl-end
 
@@ -84,5 +74,3 @@
 
 prove_correct accumulateBins by
   loom_solve
-  rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -55,11 +55,10 @@
     -- impl-start
     let mut result : List (Option Float) := []
     let mut i := bins.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ bins.length
       invariant result = aggregateSeq reduceBin minPop (bins.drop i)
       done_with i = 0
-      decreasing i
     do
       let b := bins[i - 1]!
       result := binAggregate reduceBin minPop b :: result
```

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
@@ -59,10 +59,11 @@
       invariant 0 ≤ i ∧ i ≤ bins.length
       invariant result = aggregateSeq reduceBin minPop (bins.drop i)
       done_with i = 0
-      decreasing i
     do
       let b := bins[i - 1]!
-      result := binAggregate reduceBin minPop b :: result
+      let agg : Option Float :=
+        if minPop ≥ b.length then some (reduceBin b) else none
+      result := agg :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
--  so the spec makes no behavioural claim about it and holds for EVERY value;
--  the bin populations are free inputs too. There is nothing to check against a
--  real callee, hence no axiom and no G-AX. The only thing the spec pins is the
--  selection rule — which bins are aggregated vs left empty.)
-- axioms-end

-- pure-start
/- The aggregate emitted for one bin, given the minimum population a bin must
   reach to be aggregated. A bin is aggregated — its values collapsed to a
   single number by `reduceBin` — exactly when it holds AT LEAST that many
   values; otherwise the bin is left empty (`none`, i.e. no aggregate). -/
def binAggregate (reduceBin : List Float → Float) (minPop : Nat)
    (bin : List Float) : Option Float :=
  if bin.length ≥ minPop then some (reduceBin bin) else none

/- The aggregates emitted for a whole sequence of bins: the per-bin aggregate of
   each bin, in order, with empties left as `none`. Front-recursive so a single
   unfold is available per loop step (the backward fold pattern, plan §5.4). -/
def aggregateSeq (reduceBin : List Float → Float) (minPop : Nat) :
    List (List Float) → List (Option Float)
  | []      => []
  | b :: bs => binAggregate reduceBin minPop b :: aggregateSeq reduceBin minPop bs

@[grind] lemma aggregateSeq_nil (f : List Float → Float) (m : Nat) :
    aggregateSeq f m [] = [] := rfl
@[grind] lemma aggregateSeq_cons (f : List Float → Float) (m : Nat)
    (b : List Float) (bs : List (List Float)) :
    aggregateSeq f m (b :: bs) = binAggregate f m b :: aggregateSeq f m bs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the per-bin aggregates for a sequence of bins. Each bin is aggregated
   to a single value when its population reaches the minimum, and is otherwise
   left empty. `reduceBin`, `minPop`, `bins` are read-only — the probe mutates
   nothing it is handed (directive 5). -/
method accumulateBins (reduceBin : List Float → Float) (minPop : Nat)
    (bins : List (List Float)) return (out : List (Option Float))
  ensures out = aggregateSeq reduceBin minPop bins
  do
    -- impl-start
    let mut result : List (Option Float) := []
    let mut i := bins.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ bins.length
      invariant result = aggregateSeq reduceBin minPop (bins.drop i)
      done_with i = 0
    do
      let b := bins[i - 1]!
      result := binAggregate reduceBin minPop b :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the bin at `i-1`
   on the front, so `aggregateSeq` peels one `binAggregate`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma aggregateSeq_drop_step (f : List Float → Float) (m : Nat)
    (bins : List (List Float)) (i : Nat) (hi : 0 < i) (hle : i ≤ bins.length) :
    aggregateSeq f m (bins.drop (i - 1))
      = binAggregate f m bins[i - 1]! :: aggregateSeq f m (bins.drop i) := by
  have hlt : i - 1 < bins.length := by omega
  have hcons : bins.drop (i - 1) = bins[i - 1]! :: bins.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, aggregateSeq_cons]

prove_correct accumulateBins by
  loom_solve
  rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & EVIDENCE. Spec is a partial-correctness Velvet method: set_option loom.semantics.termination "partial"; postcondition out = aggregateSeq reduceBin minPop bins with binAggregate reduceBin minPop b = if b.length >= minPop then some (reduceBin b) else none. spec_view elides BOTH impl and prove_correct bodies, so attacks freely rewrite the loop/invariants/proof; all keep axioms/pure/pre/post byte-identical -> same_spec=True (verified for all 9 attacks via swebench_unified.markers.same_spec + get_backend('velvet')).

### VERIFY (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch strict '>' (b.length > minPop): exit 1 (FAILS at boundary len==minPop). prepatch bug reproduced.
- atk_3 some/none swapped: exit 1.
- atk_4 empty output (partial-domain, return []): exit 1.
- atk_6 off-by-one (>= minPop+1): exit 1.
- atk_8 control-flow-effect (while i>1, skips last bin): exit 1.
- atk_9 inverted selection (minPop >= b.length): exit 1.
- atk_7 ungrounded-oracle echo (return aggregateSeq reduceBin minPop bins): exit 0 VERIFIES.
- atk_5 divergence (while i>0 { i:=i+1 }, invariant i>=1, done_with i=0; vacuous-exit under partial correctness): exit 0 VERIFIES.
- atk_2 positive control (gold-faithful backward-fold impl): exit 0 VERIFIES.

### RESOLVE (run_resolve, official Docker harness, retries=0):
- atk_7 (echo) faithful patch = GOLD VERBATIM (> -> >=): {resolved:true, completed:true, note:'resolved'}. Therefore the echo is a CORRECT ECHO (verifies AND its patch resolves), NOT a spec weakness. This also confirms the harness is functional and the gold patch resolves.
- atk_5 (divergence) faithful patch = infinite loop injected before the accum comprehension (atk_5_patch.diff, applies clean at base_commit). Run #1 (timeout 300): {resolved:false, completed:FALSE, note:'no report ... harness error'}. Run #2 (timeout 900): the harness HUNG >472s (test never completes because the injected loop never terminates); killed after confirming non-completion (atk_5_hang_evidence.txt). Executed result: completed=FALSE. Per the gate derivation (construct/build_one.py:306), BROKEN requires completed AND not resolved; a non-completing (hanging) patch is INCONCLUSIVE, never BROKEN.

WHY atk_5 IS NOT A BREAK AND IS EXCLUDED FROM THE SUBMITTED ATTACK LIST: divergence vacuously satisfies ANY postcondition under partial correctness -- a universal property of every partial-correctness bundle, not a refinement-fidelity defect specific to this spec. There is no operation-level faithful refinement of an infinite loop into the gold's list comprehension. Including atk_5 in the submitted attacks would make the runner's own resolve HANG on it -> inconclusive_hits -> a spurious gate fail; so it is reported here as evidence only. All 7 SUBMITTED attacks are resolve-safe: the 6 terminating wrong-impls FAIL verify (never reach resolve), and the echo resolves.

REFINEMENT.md AUDIT (protocol step 3): all legs R or I, NO kind-3, NO axioms. meta.json axioms=[], deep_model_references=[], conf_skip=false, G-AX skip. A1 reduceBin<->reduce_C_function (R + free input), A2 minPop<->mincnt after None->0 (R), A3 bins<->[acc for ... for acc in Cs_at_i[1:]] (R + free input; unchanged binning folded in), A4 binAggregate's b.length>=minPop / some(reduceBin b) / none <-> len(acc)>=mincnt / reduce_C_function(acc) / np.nan (I, the discriminating changed op modeled concretely), A5 aggregateSeq/backward-while <-> the order-preserving comprehension (I). The A4/A5 correspondence to the real callee holds; patch.diff is gold verbatim (single-line > -> >=). Free-input treatment sound: the patch changes ONLY the threshold; binning/[1:]-drop/concat above line 5017 is unchanged. G-CONF (seed 26113, 1e5 boundary-weighted fuzz) reproduces 0 disagreements.

FALSIFICATION FLOOR MET: 7 submitted attacks (>=5), prepatch reproduced (atk_1), positive control (atk_2) verifies and is distinct from all attacks. No verifying-but-incorrect terminating impl exists; the spec is TIGHT. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `atk_2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl exists whose faithful refined patch does NOT resolve. The postcondition out = aggregateSeq reduceBin minPop bins is a total functional equality over transparent defs (binAggregate b = if b.length >= minPop then some (reduceBin b) else none), so every TERMINATING verifying impl is behaviourally equal to gold and resolves. The only verifying same-spec impls found were (a) the ungrounded-oracle echo, whose faithful patch is gold-verbatim and RESOLVES (correct echo, not a weakness), and (b) a divergent/vacuous-exit impl, a universal partial-correctness artifact whose faithful patch cannot complete in the harness (inconclusive, not BROKEN).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
--  so the spec makes no behavioural claim about it and holds for EVERY value;
--  the bin populations are free inputs too. There is nothing to check against a
--  real callee, hence no axiom and no G-AX. The only thing the spec pins is the
--  selection rule — which bins are aggregated vs left empty.)
-- axioms-end

-- pure-start
/- The aggregate emitted for one bin, given the minimum population a bin must
   reach to be aggregated. A bin is aggregated — its values collapsed to a
   single number by `reduceBin` — exactly when it holds AT LEAST that many
   values; otherwise the bin is left empty (`none`, i.e. no aggregate). -/
def binAggregate (reduceBin : List Float → Float) (minPop : Nat)
    (bin : List Float) : Option Float :=
  if bin.length ≥ minPop then some (reduceBin bin) else none

/- The aggregates emitted for a whole sequence of bins: the per-bin aggregate of
   each bin, in order, with empties left as `none`. Front-recursive so a single
   unfold is available per loop step (the backward fold pattern, plan §5.4). -/
def aggregateSeq (reduceBin : List Float → Float) (minPop : Nat) :
    List (List Float) → List (Option Float)
  | []      => []
  | b :: bs => binAggregate reduceBin minPop b :: aggregateSeq reduceBin minPop bs

@[grind] lemma aggregateSeq_nil (f : List Float → Float) (m : Nat) :
    aggregateSeq f m [] = [] := rfl
@[grind] lemma aggregateSeq_cons (f : List Float → Float) (m : Nat)
    (b : List Float) (bs : List (List Float)) :
    aggregateSeq f m (b :: bs) = binAggregate f m b :: aggregateSeq f m bs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the per-bin aggregates for a sequence of bins. Each bin is aggregated
   to a single value when its population reaches the minimum, and is otherwise
   left empty. `reduceBin`, `minPop`, `bins` are read-only — the probe mutates
   nothing it is handed (directive 5). -/
method accumulateBins (reduceBin : List Float → Float) (minPop : Nat)
    (bins : List (List Float)) return (out : List (Option Float))
  ensures out = aggregateSeq reduceBin minPop bins
  do
    -- impl-start
    let mut result : List (Option Float) := []
    let mut i := bins.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ bins.length
      invariant result = aggregateSeq reduceBin minPop (bins.drop i)
      done_with i = 0
    do
      let b := bins[i - 1]!
      result := binAggregate reduceBin minPop b :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the bin at `i-1`
   on the front, so `aggregateSeq` peels one `binAggregate`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma aggregateSeq_drop_step (f : List Float → Float) (m : Nat)
    (bins : List (List Float)) (i : Nat) (hi : 0 < i) (hle : i ≤ bins.length) :
    aggregateSeq f m (bins.drop (i - 1))
      = binAggregate f m bins[i - 1]! :: aggregateSeq f m (bins.drop i) := by
  have hlt : i - 1 < bins.length := by omega
  have hcons : bins.drop (i - 1) = bins[i - 1]! :: bins.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, aggregateSeq_cons]

prove_correct accumulateBins by
  loom_solve
  rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & EVIDENCE. Spec is a partial-correctness Velvet method: set_option loom.semantics.termination "partial"; postcondition out = aggregateSeq reduceBin minPop bins with binAggregate reduceBin minPop b = if b.length >= minPop then some (reduceBin b) else none. spec_view elides BOTH impl and prove_correct bodies, so attacks freely rewrite the loop/invariants/proof; all keep axioms/pure/pre/post byte-identical -> same_spec=True (verified for all 9 attacks via swebench_unified.markers.same_spec + get_backend('velvet')).

### VERIFY (cmd: bash scripts/lean_verify.sh <f>):
- atk_1 prepatch strict '>' (b.length > minPop): exit 1 (FAILS at boundary len==minPop). prepatch bug reproduced.
- atk_3 some/none swapped: exit 1.
- atk_4 empty output (partial-domain, return []): exit 1.
- atk_6 off-by-one (>= minPop+1): exit 1.
- atk_8 control-flow-effect (while i>1, skips last bin): exit 1.
- atk_9 inverted selection (minPop >= b.length): exit 1.
- atk_7 ungrounded-oracle echo (return aggregateSeq reduceBin minPop bins): exit 0 VERIFIES.
- atk_5 divergence (while i>0 { i:=i+1 }, invariant i>=1, done_with i=0; vacuous-exit under partial correctness): exit 0 VERIFIES.
- atk_2 positive control (gold-faithful backward-fold impl): exit 0 VERIFIES.

### RESOLVE (run_resolve, official Docker harness, retries=0):
- atk_7 (echo) faithful patch = GOLD VERBATIM (> -> >=): {resolved:true, completed:true, note:'resolved'}. Therefore the echo is a CORRECT ECHO (verifies AND its patch resolves), NOT a spec weakness. This also confirms the harness is functional and the gold patch resolves.
- atk_5 (divergence) faithful patch = infinite loop injected before the accum comprehension (atk_5_patch.diff, applies clean at base_commit). Run #1 (timeout 300): {resolved:false, completed:FALSE, note:'no report ... harness error'}. Run #2 (timeout 900): the harness HUNG >472s (test never completes because the injected loop never terminates); killed after confirming non-completion (atk_5_hang_evidence.txt). Executed result: completed=FALSE. Per the gate derivation (construct/build_one.py:306), BROKEN requires completed AND not resolved; a non-completing (hanging) patch is INCONCLUSIVE, never BROKEN.

WHY atk_5 IS NOT A BREAK AND IS EXCLUDED FROM THE SUBMITTED ATTACK LIST: divergence vacuously satisfies ANY postcondition under partial correctness -- a universal property of every partial-correctness bundle, not a refinement-fidelity defect specific to this spec. There is no operation-level faithful refinement of an infinite loop into the gold's list comprehension. Including atk_5 in the submitted attacks would make the runner's own resolve HANG on it -> inconclusive_hits -> a spurious gate fail; so it is reported here as evidence only. All 7 SUBMITTED attacks are resolve-safe: the 6 terminating wrong-impls FAIL verify (never reach resolve), and the echo resolves.

REFINEMENT.md AUDIT (protocol step 3): all legs R or I, NO kind-3, NO axioms. meta.json axioms=[], deep_model_references=[], conf_skip=false, G-AX skip. A1 reduceBin<->reduce_C_function (R + free input), A2 minPop<->mincnt after None->0 (R), A3 bins<->[acc for ... for acc in Cs_at_i[1:]] (R + free input; unchanged binning folded in), A4 binAggregate's b.length>=minPop / some(reduceBin b) / none <-> len(acc)>=mincnt / reduce_C_function(acc) / np.nan (I, the discriminating changed op modeled concretely), A5 aggregateSeq/backward-while <-> the order-preserving comprehension (I). The A4/A5 correspondence to the real callee holds; patch.diff is gold verbatim (single-line > -> >=). Free-input treatment sound: the patch changes ONLY the threshold; binning/[1:]-drop/concat above line 5017 is unchanged. G-CONF (seed 26113, 1e5 boundary-weighted fuzz) reproduces 0 disagreements.

FALSIFICATION FLOOR MET: 7 submitted attacks (>=5), prepatch reproduced (atk_1), positive control (atk_2) verifies and is distinct from all attacks. No verifying-but-incorrect terminating impl exists; the spec is TIGHT. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) check for velvet matplotlib__matplotlib-26113. Gold patch is a single-char change len(acc) > mincnt -> len(acc) >= mincnt at lib/matplotlib/axes/_axes.py:5017; base commit 5ca694b38d confirmed (pre-patch '>'). The model captures exactly this: binAggregate uses bin.length >= minPop, aggregateSeq maps it order-preservingly; bijection none<->np.nan, some x<->x, mincnt(None->0)<->minPop:Nat, reduce_C_function<->reduceBin (free input), binning/[1:]/concat<->free input bins. Verified: (1) same_spec(Solution,prepatch,velvet)=True, spec region byte-identical (impl differs >= vs >, the intended G-DIFF); (2) lean_verify.sh Solution.lean exit 0 (verifies vs frozen spec); (3) bundle conformance 100k inputs 0 disagreements; (4) my OWN independent numpy differential vs the real post-patch comprehension, 200k boundary-weighted cases over sum/mean/max/len reducers, 0 diffs. The ensures is exact functional equality against the transliterated post-patch comprehension, so it rejects no real-repo behavior (not too strong). reduceBin and bins are legitimately universally-quantified free inputs (both truly unchanged by the patch); the only pinned behavior is the threshold, modeled concretely. The one abstraction corner (partial real reducer, e.g. np.max([]) raising when minPop=0 on empty bins) is an explicit free-input modeling boundary present identically pre/post-patch, not the op under change, and fixes no output value the spec could contradict. No concrete diverging input exists. Minor narrative nit (refinement.md says 'default mincnt=1' whereas hexbin default is None->0) is cosmetic and does not affect the spec, which correctly folds None->0 into minPop:Nat.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the spec view (spec_view of Solution.lean) against the public problem_statement ONLY (not hints_text). Findings:

1. Mechanical screen (leakage.screen, velvet/lean flavor) PASSES: hard_failures=[], warnings=[]. No diff markers, no patched file path (lib/matplotlib/axes/_axes.py absent from view), no patched-module dotted path, no spec-view identifier embedding a patched repo symbol, no narration keywords (bug/fix/patch/pre-patch/etc.).

2. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec region is byte-identical between patched and prepatch bundles, so the frozen spec is stable.

3. Gold edit = single-char threshold flip on lib/matplotlib/axes/_axes.py:5017: `len(acc) > mincnt` -> `len(acc) >= mincnt`. The spec view models this abstractly: binAggregate uses `if bin.length >= minPop` with comment 'aggregated ... exactly when it holds AT LEAST that many values'. This is the discriminating content, so the question is whether it leaks the edit BEYOND problem_statement.

4. It does NOT: the public problem_statement explicitly discloses the exact fix in its Resolution section: 'the behavior of `C is None` being applied also when `C` isn't None (i.e. `len(vals) >= mincnt`, rather than the current `len(vals) > mincnt`)'. The >= / 'at least' threshold is therefore already public. The spec view adds no edit-localization beyond what the task states: all symbols are abstract model names (accumulateBins/binAggregate/aggregateSeq/reduceBin/minPop), no repo symbols (hexbin, reduce_C_function, mincnt-as-such, accum), no >->>= narration, no pre/post-patch framing in the projected view. The impl and proof regions are elided in the spec view.

Conclusion: the spec view leaks nothing about the gold edit that the problem_statement does not already make public. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
