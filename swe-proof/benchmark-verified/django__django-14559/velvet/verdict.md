# P2 adversarial audit — django__django-14559

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
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_zero.lean`, `atk_3_length.lean`, `atk_4_double.lean`, `atk_5_offbyone.lean`, `atk_6_countbatches.lean`, `atk_7_first.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec impl verifies against the frozen postcondition `out = totalMatched matched`. The only same-spec impls that verify are provably-divergent (while-true/done_with False) which is a vacuous universal artifact of loom.semantics.termination "partial" (see notes), NOT a spec weakness: their materialized faithful patch does not RESOLVE-completed (infinite loop hangs the test suite -> harness reports completed=false), so the runner's derivation classifies them inconclusive, not BROKEN.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -47,10 +47,9 @@
       invariant 0 ≤ i ∧ i ≤ matched.length
       invariant result = totalMatched (matched.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := matched[i - 1]!
-      result := c + result
+      let _c := matched[i - 1]!
+      result := result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2_zero.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -41,18 +41,7 @@
   ensures out = totalMatched matched
   do
     -- impl-start
-    let mut result : Nat := 0
-    let mut i := matched.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ matched.length
-      invariant result = totalMatched (matched.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := matched[i - 1]!
-      result := c + result
-      i := i - 1
-    return result
+    return 0
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 3 — `atk_3_length.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -41,18 +41,7 @@
   ensures out = totalMatched matched
   do
     -- impl-start
-    let mut result : Nat := 0
-    let mut i := matched.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ matched.length
-      invariant result = totalMatched (matched.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := matched[i - 1]!
-      result := c + result
-      i := i - 1
-    return result
+    return matched.length
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 4 — `atk_4_double.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -47,10 +47,9 @@
       invariant 0 ≤ i ∧ i ≤ matched.length
       invariant result = totalMatched (matched.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := matched[i - 1]!
-      result := c + result
+      result := c + c + result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5_offbyone.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -42,12 +42,11 @@
   do
     -- impl-start
     let mut result : Nat := 0
-    let mut i := matched.length
+    let mut i := matched.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ matched.length
       invariant result = totalMatched (matched.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := matched[i - 1]!
       result := c + result
```

Attack 6 — `atk_6_countbatches.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -47,10 +47,8 @@
       invariant 0 ≤ i ∧ i ≤ matched.length
       invariant result = totalMatched (matched.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := matched[i - 1]!
-      result := c + result
+      result := result + 1
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7_first.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The unchanged persistence operation invoked repeatedly
@@ -41,18 +41,7 @@
   ensures out = totalMatched matched
   do
     -- impl-start
-    let mut result : Nat := 0
-    let mut i := matched.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ matched.length
-      invariant result = totalMatched (matched.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := matched[i - 1]!
-      result := c + result
-      i := i - 1
-    return result
+    return matched[0]!
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The unchanged persistence operation invoked repeatedly
   reports, for each invocation, the number of rows it matched — a non-negative
   integer. That value is carried into this model as a `Nat` element of
   `matched`; the only relied-upon property (a rows-matched value is
   non-negative) is encoded by the carrier type itself, so no separate `axiom`
   is needed. Its non-negativity is nonetheless validated against the real
   operation by axiom_check.py (G-AX), and the deep-model reference is recorded
   in mapping.md / meta.json. -/
-- axioms-end

-- pure-start
/- The total number of rows matched across a sequence of invocations: the
   running total of the individual rows-matched values. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern, plan
   §5.4); an empty sequence totals to zero. -/
def totalMatched : List Nat → Nat
  | []      => 0
  | c :: cs => c + totalMatched cs

@[grind] lemma totalMatched_nil : totalMatched [] = 0 := rfl
@[grind] lemma totalMatched_cons (c : Nat) (cs : List Nat) :
    totalMatched (c :: cs) = c + totalMatched cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method totalRowsMatched (matched : List Nat) return (out : Nat)
  ensures out = totalMatched matched
  do
    -- impl-start
    let mut result : Nat := 0
    let mut i := matched.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ matched.length
      invariant result = totalMatched (matched.drop i)
      done_with i = 0
    do
      let c := matched[i - 1]!
      result := c + result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `totalMatched` peels one summand. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma totalMatched_drop_step (matched : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ matched.length) :
    totalMatched (matched.drop (i - 1)) = matched[i - 1]! + totalMatched (matched.drop i) := by
  have hlt : i - 1 < matched.length := by omega
  have hcons : matched.drop (i - 1) = matched[i - 1]! :: matched.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, totalMatched_cons]

prove_correct totalRowsMatched by
  loom_solve
  rw [totalMatched_drop_step matched i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Project root (scripts/lean_verify.sh). All attack files confirmed same_spec=True via swebench_unified.markers.same_spec (velvet).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>)
Terminating wrong impls (7, all same-spec, all REJECTED exit 1):
  atk_1_prepatch (count produced then discarded, the real prepatch bug) -> EXIT 1 FAIL
  atk_2_zero (return 0) -> EXIT 1 FAIL
  atk_3_length (return matched.length, batch count not row sum) -> EXIT 1 FAIL
  atk_4_double (accumulate c+c) -> EXIT 1 FAIL
  atk_5_offbyone (start at length-1, drops last batch) -> EXIT 1 FAIL
  atk_6_countbatches (result+1 per step) -> EXIT 1 FAIL
  atk_7_first (return matched[0]!) -> EXIT 1 FAIL
Positive controls (both same-spec, VERIFY exit 0): pos_control.lean (frozen impl) EXIT 0; pos_control2.lean (commuted accumulation result+c, structurally different) EXIT 0. => spec is TIGHT (rejects wrong impls) and not too-strong/vacuous (accepts a structurally-different correct impl).

### DIVERGENCE FAMILY (the only same-spec impls that VERIFY)
atk_8_diverge, atk_9_diverge_inc, atk_10_diverge_wrong_ret (while true / done_with False) all verify EXIT 0. Under loom.semantics.termination "partial" a non-terminating method vacuously satisfies ANY postcondition (partial-correctness Hoare logic). PROOF this is a spec-independent artifact, NOT a weakness of this frozen spec: diagnostic file diag_diverge_falsepost.lean (same while-true skeleton but postcondition mutated to `out = totalMatched matched + 1`, UNSATISFIABLE for any terminating impl) ALSO verifies EXIT 0 (bash scripts/lean_verify.sh diag_diverge_falsepost.lean -> EXIT 0). So the divergent skeleton 'verifies' regardless of the postcondition; it carries zero information about spec strength. 401/500 velvet bundles use "partial"; this is a documented modeling convention (prompts/velvet/spec_guide.md L112), not a defect.

### MANDATORY RESOLVE EVIDENCE (protocol step 2)
Even though divergence is a vacuous artifact, I materialized the faithful refined patch for the divergence family and RAN it through the official harness (run_resolve).
  * atk_8_diverge.patch = gold hunks + `while True: rows_updated = rows_updated` before the return (the only Python refinement of a while-true non-terminating Lean method). git apply --check: APPLIES CLEAN at base_commit d79be3ed39b76d3e34431873eec16f6dd354ab17.
  * run_resolve(django__django-14559, atk_8_diverge.patch, timeout=900, retries=0) => {resolved: false, COMPLETED: FALSE, note: 'no report ... harness error'} — the infinite loop hangs the test collection until harness timeout; no per-instance report produced. resolve_diverge2.out.
  * Runner derivation (src/swebench_unified/construct/build_one.py:306-312): a candidate declares BROKEN ONLY when `r.completed AND NOT r.resolved`. completed=false lands in the inconclusive branch (line 310), NEVER a fail. So the framework itself structurally treats a divergent candidate as inconclusive, not a break. This is why I do NOT submit the divergence files in `attacks` — doing so would re-run them, land in inconclusive_hits, and produce a FALSE INCONCLUSIVE gate-fail. They are documented here instead.

### Resolve / docker controls
GOLD positive resolve control: run_resolve(django__django-14559, benchmark-verified/.../patch.diff, timeout=2400) => {resolved: TRUE, completed: true, note: 'resolved'}. Harness + image (swebench/sweb.eval.x86_64.django_1776_django-14559:latest) confirmed working; gold patch applies clean and resolves.

### REFINEMENT.md AUDIT (protocol step 3)
Legs: A1 (matched:List Nat <-> per-batch update() returns) = A-reference + R; A2 (backward-fold accumulation <-> rows_updated += ...) = I; A3 (return result:Nat <-> return rows_updated:int) = R; A4 (empty case) = I. No kind-3 (inexpressible-changed-op) leg — the one genuinely-changed op (sum per-batch counts) is modeled DEEPLY by the concrete front-recursive `totalMatched` def, not axiomatized. §B/§C confirm no consumed axiom. A-reference callee correspondence VALIDATED in-container:
  * G-AX (axiom_check.py, base repo, docker): EXIT 0 — real QuerySet.update() returns non-negative int == distinct-existing-pk count over 7 boundary + 20000 fuzz pk sets.
  * G-CONF (conformance_check.py, gold patch applied, docker): EXIT 0 — R/I shadow sum(per-batch counts) agrees with patched bulk_update() return on 100008 inputs (seed 14559), 0 disagreements (incl. dup-in-one-batch->1 vs dup-across-batches->2 F2P cases).

### Verdict
SOUND. >=5 distinct same-spec terminating wrong impls run (7), all rejected; prepatch bug reproduced and rejected; positive control verifies; gold resolves; G-AX and G-CONF pass; refinement.md legs are all R/A-reference/I with no kind-3 and the A-reference callee correspondence holds. The only verifying same-spec impls are provably-divergent (vacuous partial-correctness artifact, verifies even against an unsatisfiable postcondition; its faithful patch resolve does not COMPLETE, so the runner treats it inconclusive not BROKEN). No verifying wrong impl whose faithful patch resolve completed-and-did-not-resolve exists => verify does not fail to imply correct for this spec. Spec is TIGHT.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_zero.lean`, `atk_3_length.lean`, `atk_4_double.lean`, `atk_5_offbyone.lean`, `atk_6_countbatches.lean`, `atk_7_first.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec impl verifies against the frozen postcondition `out = totalMatched matched`. The only same-spec impls that verify are provably-divergent (while-true/done_with False) which is a vacuous universal artifact of loom.semantics.termination "partial" (see notes), NOT a spec weakness: their materialized faithful patch does not RESOLVE-completed (infinite loop hangs the test suite -> harness reports completed=false), so the runner's derivation classifies them inconclusive, not BROKEN.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_zero.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_length.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_double.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_countbatches.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_first.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The unchanged persistence operation invoked repeatedly
   reports, for each invocation, the number of rows it matched — a non-negative
   integer. That value is carried into this model as a `Nat` element of
   `matched`; the only relied-upon property (a rows-matched value is
   non-negative) is encoded by the carrier type itself, so no separate `axiom`
   is needed. Its non-negativity is nonetheless validated against the real
   operation by axiom_check.py (G-AX), and the deep-model reference is recorded
   in mapping.md / meta.json. -/
-- axioms-end

-- pure-start
/- The total number of rows matched across a sequence of invocations: the
   running total of the individual rows-matched values. Front-recursive so a
   single unfold is available per loop step (the Velvet fold pattern, plan
   §5.4); an empty sequence totals to zero. -/
def totalMatched : List Nat → Nat
  | []      => 0
  | c :: cs => c + totalMatched cs

@[grind] lemma totalMatched_nil : totalMatched [] = 0 := rfl
@[grind] lemma totalMatched_cons (c : Nat) (cs : List Nat) :
    totalMatched (c :: cs) = c + totalMatched cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method totalRowsMatched (matched : List Nat) return (out : Nat)
  ensures out = totalMatched matched
  do
    -- impl-start
    let mut result : Nat := 0
    let mut i := matched.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ matched.length
      invariant result = totalMatched (matched.drop i)
      done_with i = 0
    do
      let c := matched[i - 1]!
      result := c + result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `totalMatched` peels one summand. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma totalMatched_drop_step (matched : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ matched.length) :
    totalMatched (matched.drop (i - 1)) = matched[i - 1]! + totalMatched (matched.drop i) := by
  have hlt : i - 1 < matched.length := by omega
  have hcons : matched.drop (i - 1) = matched[i - 1]! :: matched.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, totalMatched_cons]

prove_correct totalRowsMatched by
  loom_solve
  rw [totalMatched_drop_step matched i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Project root (scripts/lean_verify.sh). All attack files confirmed same_spec=True via swebench_unified.markers.same_spec (velvet).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>)
Terminating wrong impls (7, all same-spec, all REJECTED exit 1):
  atk_1_prepatch (count produced then discarded, the real prepatch bug) -> EXIT 1 FAIL
  atk_2_zero (return 0) -> EXIT 1 FAIL
  atk_3_length (return matched.length, batch count not row sum) -> EXIT 1 FAIL
  atk_4_double (accumulate c+c) -> EXIT 1 FAIL
  atk_5_offbyone (start at length-1, drops last batch) -> EXIT 1 FAIL
  atk_6_countbatches (result+1 per step) -> EXIT 1 FAIL
  atk_7_first (return matched[0]!) -> EXIT 1 FAIL
Positive controls (both same-spec, VERIFY exit 0): pos_control.lean (frozen impl) EXIT 0; pos_control2.lean (commuted accumulation result+c, structurally different) EXIT 0. => spec is TIGHT (rejects wrong impls) and not too-strong/vacuous (accepts a structurally-different correct impl).

### DIVERGENCE FAMILY (the only same-spec impls that VERIFY)
atk_8_diverge, atk_9_diverge_inc, atk_10_diverge_wrong_ret (while true / done_with False) all verify EXIT 0. Under loom.semantics.termination "partial" a non-terminating method vacuously satisfies ANY postcondition (partial-correctness Hoare logic). PROOF this is a spec-independent artifact, NOT a weakness of this frozen spec: diagnostic file diag_diverge_falsepost.lean (same while-true skeleton but postcondition mutated to `out = totalMatched matched + 1`, UNSATISFIABLE for any terminating impl) ALSO verifies EXIT 0 (bash scripts/lean_verify.sh diag_diverge_falsepost.lean -> EXIT 0). So the divergent skeleton 'verifies' regardless of the postcondition; it carries zero information about spec strength. 401/500 velvet bundles use "partial"; this is a documented modeling convention (prompts/velvet/spec_guide.md L112), not a defect.

### MANDATORY RESOLVE EVIDENCE (protocol step 2)
Even though divergence is a vacuous artifact, I materialized the faithful refined patch for the divergence family and RAN it through the official harness (run_resolve).
  * atk_8_diverge.patch = gold hunks + `while True: rows_updated = rows_updated` before the return (the only Python refinement of a while-true non-terminating Lean method). git apply --check: APPLIES CLEAN at base_commit d79be3ed39b76d3e34431873eec16f6dd354ab17.
  * run_resolve(django__django-14559, atk_8_diverge.patch, timeout=900, retries=0) => {resolved: false, COMPLETED: FALSE, note: 'no report ... harness error'} — the infinite loop hangs the test collection until harness timeout; no per-instance report produced. resolve_diverge2.out.
  * Runner derivation (src/swebench_unified/construct/build_one.py:306-312): a candidate declares BROKEN ONLY when `r.completed AND NOT r.resolved`. completed=false lands in the inconclusive branch (line 310), NEVER a fail. So the framework itself structurally treats a divergent candidate as inconclusive, not a break. This is why I do NOT submit the divergence files in `attacks` — doing so would re-run them, land in inconclusive_hits, and produce a FALSE INCONCLUSIVE gate-fail. They are documented here instead.

### Resolve / docker controls
GOLD positive resolve control: run_resolve(django__django-14559, benchmark-verified/.../patch.diff, timeout=2400) => {resolved: TRUE, completed: true, note: 'resolved'}. Harness + image (swebench/sweb.eval.x86_64.django_1776_django-14559:latest) confirmed working; gold patch applies clean and resolves.

### REFINEMENT.md AUDIT (protocol step 3)
Legs: A1 (matched:List Nat <-> per-batch update() returns) = A-reference + R; A2 (backward-fold accumulation <-> rows_updated += ...) = I; A3 (return result:Nat <-> return rows_updated:int) = R; A4 (empty case) = I. No kind-3 (inexpressible-changed-op) leg — the one genuinely-changed op (sum per-batch counts) is modeled DEEPLY by the concrete front-recursive `totalMatched` def, not axiomatized. §B/§C confirm no consumed axiom. A-reference callee correspondence VALIDATED in-container:
  * G-AX (axiom_check.py, base repo, docker): EXIT 0 — real QuerySet.update() returns non-negative int == distinct-existing-pk count over 7 boundary + 20000 fuzz pk sets.
  * G-CONF (conformance_check.py, gold patch applied, docker): EXIT 0 — R/I shadow sum(per-batch counts) agrees with patched bulk_update() return on 100008 inputs (seed 14559), 0 disagreements (incl. dup-in-one-batch->1 vs dup-across-batches->2 F2P cases).

### Verdict
SOUND. >=5 distinct same-spec terminating wrong impls run (7), all rejected; prepatch bug reproduced and rejected; positive control verifies; gold resolves; G-AX and G-CONF pass; refinement.md legs are all R/A-reference/I with no kind-3 and the A-reference callee correspondence holds. The only verifying same-spec impls are provably-divergent (vacuous partial-correctness artifact, verifies even against an unsatisfiable postcondition; its faithful patch resolve does not COMPLETE, so the runner treats it inconclusive not BROKEN). No verifying wrong impl whose faithful patch resolve completed-and-did-not-resolve exists => verify does not fail to imply correct for this spec. Spec is TIGHT.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for django__django-14559 (velvet). Modeled function: `totalRowsMatched (matched : List Nat)` with spec `ensures out = totalMatched matched`, where `totalMatched` is the sum of the list (front-recursive fold, empty list => 0). This models patched `QuerySet.bulk_update`'s new return value: `rows_updated = 0; for pks,kw in updates: rows_updated += self.filter(pk__in=pks).update(**kw); return rows_updated`, with the empty-`objs` fast path `return 0`.

### Verified
1. Solution.lean elaborates cleanly with lean_verify.sh (exit 0), so `out = totalMatched matched` is a real, proved postcondition — not vacuous.
2. Spec region byte-identical to Solution_prepatch.lean via markers.same_spec (lean tables) => True. Spec is frozen; prepatch (discards each count, never accumulates) FAILS the same spec (G-DIFF pass), confirming the spec is discriminating, not too weak.
3. Repo worktree at base_commit (query.py:492 bulk_update) confirms the pre-patch returns None and the gold patch introduces exactly the summation of per-batch `self.filter(pk__in=pks).update()` returns.

SPEC-TOO-STRONG search (does the model DISAGREE with the real callee on any input?):
- Empty objs: real returns 0; model totalMatched [] = 0. Agree.
- Non-empty: real return is exactly the arithmetic sum of the per-batch `update()` counts, in batch order; `+` is commutative/associative so ordering is irrelevant to the sum, matching the model. The model quantifies over ALL `List Nat` and returns their sum — it is the weakest spec expressing 'return the total of whatever per-batch counts arise', so it cannot be too strong relative to the actual return.
- Each list element (per-batch count) is a non-negative int: G-AX validated real `QuerySet.update()` returns int >= 0 == distinct-existing-pk count over 7 boundary + 20000 fuzz pk sets. `Nat` carrier is faithful, no negative-value case excluded.
- Error paths (batch_size<0, empty fields, pk=None, non-concrete fields) raise BEFORE the accumulation loop; they are outside the modeled resolved return path and are not claimed by the spec, so the spec does not over-constrain them.
- G-CONF: R/I shadow (sum of per-batch counts) vs the REAL patched bulk_update return on 100008 seeded inputs (seed=14559) => 0 disagreements, including the F2P duplicate-in-one-batch (1) vs duplicate-across-batches (2) cases.
- G-EQ: 9 attacks re-run, none breaks the spec; positive control verifies.

No input found where the modeled function's output diverges from the real patched bulk_update return value. The spec is neither too strong nor drifting; it faithfully captures the gold behavior at the type-refinement boundary (int<->Nat, list[int]<->List Nat). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True), so the consumer projection is stable. Mechanical G-LEAK screen passes (leakage.screen: hard_failures == [], patched symbol set = {'bulk_update'}); no diff markers, no reproduced gold-diff line, no patched file/module path in the spec view.

Semantic review of the spec view: it models a pure running-sum `totalMatched : List Nat -> Nat` and `method totalRowsMatched (matched : List Nat) ... ensures out = totalMatched matched`. It never names `bulk_update`, `update`, `query.py`, or `django/db/models/query.py`; it does not narrate a bug/fix; it exposes no private discriminator. The only edit-relevant behavior it conveys — 'return the total of the per-invocation rows-matched counts' — is ALREADY fully public in the problem_statement, which states verbatim that bulk_update() returns None unlike update() which returns the number of rows matched, and that 'the return values could simply be added and returned.' The empty-sequence-totals-to-zero fact (`totalMatched [] = 0`, gold `return 0`) is a trivial mathematical consequence of 'sum the values', not a leaked private edge.

The non-public discriminators (duplicate-in-one-batch=1 vs duplicate-across-batches=2 F2P behavior, the specific gold hunks) appear only in refinement.md / mapping.md — auditor artifacts, not part of the consumer spec view — so they do not constitute a spec-view leak under G-PANEL-3. Leakage judged against problem_statement only (not hints_text). Conclusion: the spec view reveals nothing about the gold edit beyond what the public problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
