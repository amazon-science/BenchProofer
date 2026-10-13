# P2 adversarial audit — django__django-14493

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
@@ -43,14 +43,13 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
+    let mut exhausted := true
     let mut i := 0
     while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
       invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
+      invariant 0 < i → exhausted = flags[i - 1]!
       invariant ∀ j, j + 1 < i → flags[j]! = true
       done_with exhausted = overBudget flags limit
-      decreasing limit - i
     do
       exhausted := flags[i]!
       i := i + 1
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
@@ -43,18 +43,7 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    return true
     -- impl-end
 
 prove_correct passBudgetExceeded by
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
@@ -43,18 +43,7 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    return false
     -- impl-end
 
 prove_correct passBudgetExceeded by
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
@@ -43,18 +43,7 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    return decide (0 < limit)
     -- impl-end
 
 prove_correct passBudgetExceeded by
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
 -- axioms-end
@@ -43,18 +43,7 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    return settledThrough flags limit
     -- impl-end
 
 prove_correct passBudgetExceeded by
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
 -- axioms-end
@@ -43,18 +43,7 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    return overBudget flags (limit - 1)
     -- impl-end
 
 prove_correct passBudgetExceeded by
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
 -- axioms-end
@@ -43,18 +43,10 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    if limit = 0 then
+      return true
+    else
+      return overBudget flags limit
     -- impl-end
 
 prove_correct passBudgetExceeded by
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
@@ -43,18 +43,7 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
-    let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
-      invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
-    do
-      exhausted := flags[i]!
-      i := i + 1
-    return exhausted
+    return overBudget flags (limit + 1)
     -- impl-end
 
 prove_correct passBudgetExceeded by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
@@ -43,16 +43,13 @@
   ensures out = overBudget flags limit
   do
     -- impl-start
-    let mut exhausted := false
+    let mut exhausted := true
     let mut i := 0
-    while i < limit ∧ (i = 0 ∨ flags[i - 1]! = true)
+    while i < limit
       invariant i ≤ limit
-      invariant exhausted = (decide (0 < i) && flags[i - 1]!)
-      invariant ∀ j, j + 1 < i → flags[j]! = true
-      done_with exhausted = overBudget flags limit
-      decreasing limit - i
+      invariant exhausted = settledThrough flags i
     do
-      exhausted := flags[i]!
+      exhausted := exhausted && flags[i]!
       i := i + 1
     return exhausted
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A bounded sequence of refinement passes is driven by a per-pass flag telling
   whether that pass still produced a change. The summary observation reported
   after the whole sequence is: did the sequence run out of its pass budget while
   changes were still happening? That holds exactly when the budget is positive
   AND every pass inside the budget still reported a change, so the sequence
   never settled. With a zero budget no pass runs, nothing changes, and the
   reported value must be `false`. -/
def settledThrough (flags : List Bool) (limit : Nat) : Bool :=
  decide (∀ j, j < limit → flags[j]! = true)

def overBudget (flags : List Bool) (limit : Nat) : Bool :=
  decide (0 < limit) && settledThrough flags limit

@[grind] lemma settledThrough_iff (flags : List Bool) (limit : Nat) :
    settledThrough flags limit = true ↔ ∀ j, j < limit → flags[j]! = true := by
  simp [settledThrough]

@[grind] lemma overBudget_iff (flags : List Bool) (limit : Nat) :
    overBudget flags limit = true ↔ (0 < limit ∧ ∀ j, j < limit → flags[j]! = true) := by
  simp [overBudget, settledThrough]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method passBudgetExceeded (flags : List Bool) (limit : Nat) return (out : Bool)
  require limit ≤ flags.length
  ensures out = overBudget flags limit
  do
    -- impl-start
    return overBudget flags limit
    -- impl-end

prove_correct passBudgetExceeded by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Real project root; tooling run there + venv swebench-lean.

Spec shape: single method passBudgetExceeded (flags:List Bool) (limit:Nat), require limit ≤ flags.length, ensures out = overBudget flags limit where overBudget flags limit = decide(0<limit) && (∀ j<limit, flags[j]! = true) — a transparent, fully-computable pure function of the actual carriers. No axioms, no oracle.

ATTACK BATTERY (9 distinct same-spec wrong impls, all same_spec=True vs frozen Solution.lean via markers.same_spec/velvet; each verified with scripts/lean_verify.sh <f>, launched concurrently ≤4/batch):
- atk_1 prepatch bug (exhausted:=true init, prepatch invariants): exit 1 — unsolved done_1 'exhausted = overBudget flags limit' (fails at limit=0: returns true, spec demands false). PREPATCH REPRODUCED.
- atk_2 return true: exit 1 — ⊢ true = overBudget flags limit.
- atk_3 return false: exit 1 — ⊢ false = overBudget flags limit.
- atk_4 return decide(0<limit) (drops all-flags conjunct): exit 1 — ⊢ decide(0<limit) = overBudget flags limit.
- atk_5 return settledThrough flags limit (drops 0<limit guard; wrong at limit=0): exit 1 — ⊢ settledThrough = overBudget.
- atk_6 off-by-one return overBudget flags (limit-1): exit 1.
- atk_7 partial-domain: if limit=0 then return true else overBudget (echoes UnboundLocal bug only at boundary): exit 1 — ⊢ true = overBudget flags limit.
- atk_8 off-by-one other dir return overBudget flags (limit+1): exit 1.
- atk_9 control-flow-effect: loop computing settledThrough via AND-fold, drops 0<limit guard: exit 1 — ⊢ i_1 = overBudget flags limit at exit.
Covers: partial-domain (atk_7), boundary (atk_5/atk_7), control-flow-effect (atk_1/atk_9), ungrounded-oracle constants (atk_2/atk_3), off-by-one (atk_6/atk_8), conjunct-drop (atk_4/atk_5).

EVERY wrong impl FAILS to verify (exit 1) on the postcondition clause 'out = overBudget flags limit' (loop variants on the done_1 exit clause) — the exact discriminating clause. Positive control pc.lean (return overBudget flags limit) VERIFIES exit 0 (non-vacuous). Spec is TIGHT.

RESOLVE STEP: since NO wrong impl verifies, the mandatory set of {verifying-wrong-impl → faithful patch → run_resolve} is EMPTY (patches={}); there is no verify⇏correct witness to exhibit. To confirm the positive correspondence (verify⇒resolve) and that the harness is live (rule out INCONCLUSIVE), I ran the positive control's faithful patch = the gold patch through the official harness: swebench_unified.harness.run_resolve('django__django-14493', gold_patch) → RESOLVED=True, COMPLETED=True, note='resolved'. Docker oracle reachable via `docker` (283 images, instance image present).

REFINEMENT AUDIT: refinement.md legs A1–A6 all R or I; no kind-3 (inexpressible-changed-op); §B explicitly states no axiom / no deep-model reference; the only repo callee in the loop (self._post_process) is UNCHANGED by the patch and abstracted into input flags. Confirmed against meta.json: axioms=[], deep_model_references=[], conf_skip=false; Solution.lean axioms-start/end block empty. Model↔code correspondence validated against real base-commit source (storage.py:263-273 pulled from instance image): outer loop 'for i in range(max_post_process_passes): substitutions=False; ...; substitutions=substitutions or subst; if not substitutions: break' then 'if substitutions: yield RuntimeError' — post-loop value is exactly (0<limit) ∧ (all passes 0..limit-1 changed) = overBudget, and False at limit=0 (the fix). Gold F2P test sets max_post_process_passes=0 and asserts no crash — matches overBudget flags 0 = false.

No A-leg correspondence defect, no verifying-but-wrong impl, no broken resolve. ≥5 (=9) distinct attacks run and none breaks the spec; gold resolve confirmed live. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A bounded sequence of refinement passes is driven by a per-pass flag telling
   whether that pass still produced a change. The summary observation reported
   after the whole sequence is: did the sequence run out of its pass budget while
   changes were still happening? That holds exactly when the budget is positive
   AND every pass inside the budget still reported a change, so the sequence
   never settled. With a zero budget no pass runs, nothing changes, and the
   reported value must be `false`. -/
def settledThrough (flags : List Bool) (limit : Nat) : Bool :=
  decide (∀ j, j < limit → flags[j]! = true)

def overBudget (flags : List Bool) (limit : Nat) : Bool :=
  decide (0 < limit) && settledThrough flags limit

@[grind] lemma settledThrough_iff (flags : List Bool) (limit : Nat) :
    settledThrough flags limit = true ↔ ∀ j, j < limit → flags[j]! = true := by
  simp [settledThrough]

@[grind] lemma overBudget_iff (flags : List Bool) (limit : Nat) :
    overBudget flags limit = true ↔ (0 < limit ∧ ∀ j, j < limit → flags[j]! = true) := by
  simp [overBudget, settledThrough]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method passBudgetExceeded (flags : List Bool) (limit : Nat) return (out : Bool)
  require limit ≤ flags.length
  ensures out = overBudget flags limit
  do
    -- impl-start
    return overBudget flags limit
    -- impl-end

prove_correct passBudgetExceeded by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Real project root; tooling run there + venv swebench-lean.

Spec shape: single method passBudgetExceeded (flags:List Bool) (limit:Nat), require limit ≤ flags.length, ensures out = overBudget flags limit where overBudget flags limit = decide(0<limit) && (∀ j<limit, flags[j]! = true) — a transparent, fully-computable pure function of the actual carriers. No axioms, no oracle.

ATTACK BATTERY (9 distinct same-spec wrong impls, all same_spec=True vs frozen Solution.lean via markers.same_spec/velvet; each verified with scripts/lean_verify.sh <f>, launched concurrently ≤4/batch):
- atk_1 prepatch bug (exhausted:=true init, prepatch invariants): exit 1 — unsolved done_1 'exhausted = overBudget flags limit' (fails at limit=0: returns true, spec demands false). PREPATCH REPRODUCED.
- atk_2 return true: exit 1 — ⊢ true = overBudget flags limit.
- atk_3 return false: exit 1 — ⊢ false = overBudget flags limit.
- atk_4 return decide(0<limit) (drops all-flags conjunct): exit 1 — ⊢ decide(0<limit) = overBudget flags limit.
- atk_5 return settledThrough flags limit (drops 0<limit guard; wrong at limit=0): exit 1 — ⊢ settledThrough = overBudget.
- atk_6 off-by-one return overBudget flags (limit-1): exit 1.
- atk_7 partial-domain: if limit=0 then return true else overBudget (echoes UnboundLocal bug only at boundary): exit 1 — ⊢ true = overBudget flags limit.
- atk_8 off-by-one other dir return overBudget flags (limit+1): exit 1.
- atk_9 control-flow-effect: loop computing settledThrough via AND-fold, drops 0<limit guard: exit 1 — ⊢ i_1 = overBudget flags limit at exit.
Covers: partial-domain (atk_7), boundary (atk_5/atk_7), control-flow-effect (atk_1/atk_9), ungrounded-oracle constants (atk_2/atk_3), off-by-one (atk_6/atk_8), conjunct-drop (atk_4/atk_5).

EVERY wrong impl FAILS to verify (exit 1) on the postcondition clause 'out = overBudget flags limit' (loop variants on the done_1 exit clause) — the exact discriminating clause. Positive control pc.lean (return overBudget flags limit) VERIFIES exit 0 (non-vacuous). Spec is TIGHT.

RESOLVE STEP: since NO wrong impl verifies, the mandatory set of {verifying-wrong-impl → faithful patch → run_resolve} is EMPTY (patches={}); there is no verify⇏correct witness to exhibit. To confirm the positive correspondence (verify⇒resolve) and that the harness is live (rule out INCONCLUSIVE), I ran the positive control's faithful patch = the gold patch through the official harness: swebench_unified.harness.run_resolve('django__django-14493', gold_patch) → RESOLVED=True, COMPLETED=True, note='resolved'. Docker oracle reachable via `docker` (283 images, instance image present).

REFINEMENT AUDIT: refinement.md legs A1–A6 all R or I; no kind-3 (inexpressible-changed-op); §B explicitly states no axiom / no deep-model reference; the only repo callee in the loop (self._post_process) is UNCHANGED by the patch and abstracted into input flags. Confirmed against meta.json: axioms=[], deep_model_references=[], conf_skip=false; Solution.lean axioms-start/end block empty. Model↔code correspondence validated against real base-commit source (storage.py:263-273 pulled from instance image): outer loop 'for i in range(max_post_process_passes): substitutions=False; ...; substitutions=substitutions or subst; if not substitutions: break' then 'if substitutions: yield RuntimeError' — post-loop value is exactly (0<limit) ∧ (all passes 0..limit-1 changed) = overBudget, and False at limit=0 (the fix). Gold F2P test sets max_post_process_passes=0 and asserts no crash — matches overBudget flags 0 = false.

No A-leg correspondence defect, no verifying-but-wrong impl, no broken resolve. ≥5 (=9) distinct attacks run and none breaks the spec; gold resolve confirmed live. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec vs real repo) verified for django__django-14493 velvet bundle.

### Spec integrity
- same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True — spec region is byte-identical between patched and prepatch (only the impl region / init value differs: `let mut exhausted := false` vs `true`).
- lean_verify.sh on Solution.lean: exit 0 (elaborates, no sorry/error; prove_correct discharged).

### MODELED FUNCTION vs REAL CALLEE:
- Modeled function `overBudget flags limit = decide(0<limit) && (∀ j<limit, flags[j]! = true)` models the value of local `substitutions` read at the trailing `if substitutions:` test in the PATCHED ManifestFilesMixin.post_process (django/contrib/staticfiles/storage.py). Real base worktree confirms the pre-patch bug (substitutions bound only inside `for i in range(max_post_process_passes)`, giving UnboundLocalError at limit==0); the gold patch adds `substitutions = False` before the loop.
- Real patched semantics: substitutions=False; for i in range(limit): substitutions=<pass i aggregate = flags[i]>; if not substitutions: break — then read substitutions. This equals `(0<limit) and all(flags[0..limit-1])`.
- Exhaustive brute force: for all flag lists length 0..8 and all limits 0..len (honoring the require limit<=len), model vs from-scratch real replication → 0 divergences. Includes the limit=0 boundary (both return false).
- conformance_check.py (seed 14493, 100010 inputs incl. boundary cases): 0 disagreements between R/I shadow and patched-oracle, exit 0.

REQUIRE CLAUSE not a strengthening cheat: `require limit ≤ flags.length` cannot exclude a reachable input because the loop only inspects passes 0..limit-1, which always exist by construction of the abstraction (mapping.md §2). No spec drift or over-strengthening found; no diverging input exists.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical across the patched/prepatch pair: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True; the only difference is inside the elided impl-start/impl-end region. Mechanical leakage.screen(...) over velvet LanguageTables passes with no hard_failures/warnings. Semantic review of the spec view: (1) all spec identifiers are abstract (passBudgetExceeded, flags, limit, overBudget, settledThrough, exhausted) and none echoes the patched repo symbol `substitutions` or the patched file path; (2) no diff markers or reproduced gold-diff line (`+ substitutions = False`); (3) the pure-block comment states behavioral semantics only ('zero budget -> reported value must be false') with no bug/fix/patch narration tokens. The public problem_statement already discloses the entire crux (max_post_process_passes=0, the exact `if substitutions:` UnboundLocalError, and 'substitutions is only set if the loop is entered at least once'), so the spec's zero-budget->false contract is directly derivable from solver-visible text and reveals no gold edit beyond it. The prepatch file's 'bug' narration comment sits in the elided impl region, not the consumer spec view. Judged against problem_statement only, not hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
