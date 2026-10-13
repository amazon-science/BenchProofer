# P2 adversarial audit — django__django-16256

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -35,7 +35,6 @@
   ensures related = relatedOld ++ [newObj]
   do
     -- impl-start
-    related := related ++ [newObj]
     return newObj
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -35,7 +35,7 @@
   ensures related = relatedOld ++ [newObj]
   do
     -- impl-start
-    related := related ++ [newObj]
+    related := related ++ [newObj] ++ [newObj]
     return newObj
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -36,7 +36,7 @@
   do
     -- impl-start
     related := related ++ [newObj]
-    return newObj
+    return 0
     -- impl-end
 
 /- Return an object owned by the parent, producing and settling a new one only
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -52,6 +52,7 @@
   do
     -- impl-start
     if preexists then
+      related := related ++ [existingObj]
       return (existingObj, false)
     else
       related := related ++ [newObj]
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -52,7 +52,7 @@
   do
     -- impl-start
     if preexists then
-      return (existingObj, false)
+      return (existingObj, true)
     else
       related := related ++ [newObj]
       return (newObj, true)
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -54,7 +54,6 @@
     if preexists then
       return (existingObj, false)
     else
-      related := related ++ [newObj]
       return (newObj, true)
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -71,7 +71,7 @@
   do
     -- impl-start
     if preexists then
-      return (existingObj, false)
+      return (newObj, false)
     else
       related := related ++ [newObj]
       return (newObj, true)
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -35,7 +35,7 @@
   ensures related = relatedOld ++ [newObj]
   do
     -- impl-start
-    related := related ++ [newObj]
+    related := [newObj] ++ related
     return newObj
     -- impl-end
 
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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -74,7 +74,7 @@
       return (existingObj, false)
     else
       related := related ++ [newObj]
-      return (newObj, true)
+      return (existingObj, true)
     -- impl-end
 
 prove_correct aCreate by
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -35,8 +35,11 @@
   ensures related = relatedOld ++ [newObj]
   do
     -- impl-start
-    related := related ++ [newObj]
-    return newObj
+    if newObj ∈ related then
+      return 0
+    else
+      related := related ++ [newObj]
+      return newObj
     -- impl-end
 
 /- Return an object owned by the parent, producing and settling a new one only
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -35,7 +35,7 @@
   ensures related = relatedOld ++ [newObj]
   do
     -- impl-start
-    related := related ++ [newObj]
+    related := related ++ [newObj + 1]
     return newObj
     -- impl-end
 
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms. The asynchronous bridge that runs the relation-managing
@@ -55,7 +55,7 @@
       return (existingObj, false)
     else
       related := related ++ [newObj]
-      return (newObj, true)
+      return (newObj, false)
     -- impl-end
 
 /- Return an object owned by the parent — refreshing the matching one when it
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The asynchronous bridge that runs the relation-managing
-- operation and returns its value (and its effect on the parent's collection)
-- is observationally the operation itself; its soundness is validated against
-- the real bridge by axiom_check.py (G-AX, an A-reference — mapping.md §3.1).
-- axioms-end

-- pure-start
-- pure-end

/- A parent owns a collection of related object identities (`related`). The
   three operations below each settle one object into that collection and
   report what they did. Each is a coroutine: it awaits the relation-managing
   step and yields its result, so the observable content is exactly that
   synchronous effect (mapping.md §2). -/

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

/- Settle a freshly produced object into the parent's collection, then report
   its identity. A fresh object is one not already owned by the parent. -/
method aCreate (mut related : List Nat) (newObj : Nat) return (out : Nat)
  require newObj ∉ related
  ensures out = newObj
  ensures related = relatedOld ++ [newObj]
  do
    -- impl-start
    related := related ++ [newObj]
    return newObj
    -- impl-end

/- Return an object owned by the parent, producing and settling a new one only
   when no matching object is already owned. The second component reports
   whether a new object had to be produced. When a matching object already
   exists the parent's collection is left exactly as it was. -/
method aGetOrCreate (mut related : List Nat)
    (preexists : Bool) (existingObj : Nat) (newObj : Nat) return (out : Nat × Bool)
  require preexists → existingObj ∈ related
  require ¬ preexists → newObj ∉ related
  ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)
  ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj])
  do
    -- impl-start
    if preexists then
      return (existingObj, false)
    else
      related := related ++ [newObj]
      return (newObj, true)
    -- impl-end

/- Return an object owned by the parent — refreshing the matching one when it
   already exists, or producing and settling a new one otherwise. The second
   component reports whether a new object had to be produced. Refreshing an
   existing object leaves the parent's collection membership unchanged. -/
method aUpdateOrCreate (mut related : List Nat)
    (preexists : Bool) (existingObj : Nat) (newObj : Nat) return (out : Nat × Bool)
  require preexists → existingObj ∈ related
  require ¬ preexists → newObj ∉ related
  ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)
  ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj])
  do
    -- impl-start
    if preexists then
      return (existingObj, false)
    else
      related := related ++ [newObj]
      return (newObj, true)
    -- impl-end

prove_correct aCreate by
  loom_solve

prove_correct aGetOrCreate by
  loom_solve

prove_correct aUpdateOrCreate by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VELVET G-EQ adversarial audit for django__django-16256. Env: python; docker via `docker` (image swebench/sweb.eval.x86_64.django_1776_django-16256:latest present).

**SPEC SHAPE:** three methods over carrier `related : List Nat` (parent's related collection), identities as Nat. EMPTY axioms region (no consumed axiom, no opaque oracle). Postconditions pin BOTH out and frame as TOTAL equalities over the precondition-satisfying domain:
  aCreate: out=newObj AND related=relatedOld++[newObj]
  aGetOrCreate/aUpdateOrCreate: preexists->(out=(existingObj,false) AND related=relatedOld); ¬preexists->(out=(newObj,true) AND related=relatedOld++[newObj])
Because every observable is pinned by an equality and there is no oracle symbol to echo, any verifying impl is forced to reproduce gold's carrier behavior exactly; the only slack is precondition-dead code (see atk_10), which cannot alter the faithful patch on the reachable domain.

ATTACKS (12; all same_spec=True verified via swebench_unified.markers.same_spec with velvet backend; each built by editing ONLY impl regions, axioms/pure/pre/post byte-identical). Verified with `bash scripts/lean_verify.sh <f>` run concurrently in batches of 4. exit 0=verifies, 1=error. atk_1  aCreate omits append (=prepatch bug)            -> exit 1 (unsolved: relatedOld = relatedOld++[newObj]) atk_2  aCreate appends twice                            -> exit 1 (list inequality) atk_3  aCreate returns 0                                -> exit 1 (out=newObj) atk_4  aGetOrCreate preexists ALSO appends              -> exit 1 (preexists->related=relatedOld) atk_5  aGetOrCreate wrong created flag (true)           -> exit 1 (out=(existingObj,false)) atk_6  aGetOrCreate else omits append (bug)             -> exit 1 (¬preexists frame) atk_7  aUpdateOrCreate preexists returns newObj         -> exit 1 (out=(existingObj,false)) atk_8  aCreate prepends [newObj]++related               -> exit 1 (exact list position) atk_9  aUpdateOrCreate else returns existingObj         -> exit 1 (out=(newObj,true)) atk_10 aCreate branches on newObj∈related; ∈-branch returns 0, else gold.

Precondition-shielded dead branch -> exit 0 VERIFIES (behaviorally = gold on reachable domain) atk_11 aCreate appends newObj+1 (boundary/off-by-one)   -> exit 1 (relatedOld++[newObj+1] != relatedOld++[newObj]) atk_12 aGetOrCreate else returns (newObj,false)         -> exit 1 (created flag must be true) All 11 genuinely-wrong impls (atk_1..9,11,12) REJECTED, each on the discriminating clause (confirmed by reading unsolved-goal text). Ungrounded-oracle echo attack impossible: axioms region empty; atk_3/5/7/9/12 confirm each output component individually pinned.

POSITIVE CONTROL atk_pos (= Solution.lean; structurally-correct impl): same_spec=True, exit 0 -> spec NON-VACUOUS.

MANDATORY RESOLVE (executed, not speculated): the ONLY verifying impls are atk_pos (correct control) and atk_10 (precondition-dead-branch, behaviorally = gold). Their faithful refined patch is the gold patch (sha1 7c5119b… identical to benchmark-verified/django__django-16256/patch.diff — atk_10's dead ∈-branch has NO Python counterpart since the fresh-object precondition newObj∉related is structurally guaranteed by create/get_or_create's new-row semantics). Materialized faithful_atk_10.patch and ran run_resolve('django__django-16256', patch, timeout=1800, retries=1) under `docker`:
  RESOLVE completed=True resolved=True attempts=1 flaky=False note=resolved
So every verifying wrong-impl's faithful patch RESOLVES. verify⇒correct holds; spec NOT broken.

**PREPATCH:** prepatch_1.lean (copy of Solution_prepatch_1.lean) -> exit 1, unsolved goal `related = relatedOld ++ [newObj]` — the un-settled-link bug the issue describes. prepatch_reproduced=true.

**REFINEMENT.MD AUDIT:** every leg is R / A-reference / I; NO kind-3.
  R legs: A1,A2,A3,A5,B1 (collection↔List Nat, pk↔Nat, (obj,created)↔Nat×Bool, freshness precondition) — clean bijections, G-CONF territory.
  I+R: B2 (concrete preexists branch, frame=relatedOld).
  A-reference: A4,B3 — awaited sync_to_async(self.<member>) modeled as synchronous append. Correspondence to the REAL callee is legitimate: axiom_check.py imports the genuine asgiref.sync.sync_to_async (the actual UNCHANGED callee the gold patch imports — NOT a stub, NOT patched repo code) and asserts value- AND side-effect-preservation over boundary + both branches + 2500 fuzz callables, plus link-vs-no-link observability. No consumed axiom exists; empty axioms region. conf_skip=true is legitimate (only non-trivial impl op is the A-reference append; no DB-free R/I computation to differential-test).

**VERDICT:** SOUND. 12 same-spec attacks run (11 genuinely-wrong all rejected on the discriminating clause; 1 precondition-dead verifies but is behaviorally gold), positive control verifies, prepatch reproduces the bug, and the sole verifying impls' materialized faithful patch was EXECUTED through the official harness and RESOLVED (completed=True, resolved=True). No verifying-but-wrong impl whose faithful patch fails to resolve exists. refinement.md is R/A-reference/I with sound A-reference correspondence to the real unchanged callee.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The asynchronous bridge that runs the relation-managing
-- operation and returns its value (and its effect on the parent's collection)
-- is observationally the operation itself; its soundness is validated against
-- the real bridge by axiom_check.py (G-AX, an A-reference — mapping.md §3.1).
-- axioms-end

-- pure-start
-- pure-end

/- A parent owns a collection of related object identities (`related`). The
   three operations below each settle one object into that collection and
   report what they did. Each is a coroutine: it awaits the relation-managing
   step and yields its result, so the observable content is exactly that
   synchronous effect (mapping.md §2). -/

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

/- Settle a freshly produced object into the parent's collection, then report
   its identity. A fresh object is one not already owned by the parent. -/
method aCreate (mut related : List Nat) (newObj : Nat) return (out : Nat)
  require newObj ∉ related
  ensures out = newObj
  ensures related = relatedOld ++ [newObj]
  do
    -- impl-start
    related := related ++ [newObj]
    return newObj
    -- impl-end

/- Return an object owned by the parent, producing and settling a new one only
   when no matching object is already owned. The second component reports
   whether a new object had to be produced. When a matching object already
   exists the parent's collection is left exactly as it was. -/
method aGetOrCreate (mut related : List Nat)
    (preexists : Bool) (existingObj : Nat) (newObj : Nat) return (out : Nat × Bool)
  require preexists → existingObj ∈ related
  require ¬ preexists → newObj ∉ related
  ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)
  ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj])
  do
    -- impl-start
    if preexists then
      return (existingObj, false)
    else
      related := related ++ [newObj]
      return (newObj, true)
    -- impl-end

/- Return an object owned by the parent — refreshing the matching one when it
   already exists, or producing and settling a new one otherwise. The second
   component reports whether a new object had to be produced. Refreshing an
   existing object leaves the parent's collection membership unchanged. -/
method aUpdateOrCreate (mut related : List Nat)
    (preexists : Bool) (existingObj : Nat) (newObj : Nat) return (out : Nat × Bool)
  require preexists → existingObj ∈ related
  require ¬ preexists → newObj ∉ related
  ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)
  ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj])
  do
    -- impl-start
    if preexists then
      return (existingObj, false)
    else
      related := related ++ [newObj]
      return (newObj, true)
    -- impl-end

prove_correct aCreate by
  loom_solve

prove_correct aGetOrCreate by
  loom_solve

prove_correct aUpdateOrCreate by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VELVET G-EQ adversarial audit for django__django-16256. Env: python; docker via `docker` (image swebench/sweb.eval.x86_64.django_1776_django-16256:latest present).

**SPEC SHAPE:** three methods over carrier `related : List Nat` (parent's related collection), identities as Nat. EMPTY axioms region (no consumed axiom, no opaque oracle). Postconditions pin BOTH out and frame as TOTAL equalities over the precondition-satisfying domain:
  aCreate: out=newObj AND related=relatedOld++[newObj]
  aGetOrCreate/aUpdateOrCreate: preexists->(out=(existingObj,false) AND related=relatedOld); ¬preexists->(out=(newObj,true) AND related=relatedOld++[newObj])
Because every observable is pinned by an equality and there is no oracle symbol to echo, any verifying impl is forced to reproduce gold's carrier behavior exactly; the only slack is precondition-dead code (see atk_10), which cannot alter the faithful patch on the reachable domain.

ATTACKS (12; all same_spec=True verified via swebench_unified.markers.same_spec with velvet backend; each built by editing ONLY impl regions, axioms/pure/pre/post byte-identical). Verified with `bash scripts/lean_verify.sh <f>` run concurrently in batches of 4. exit 0=verifies, 1=error. atk_1  aCreate omits append (=prepatch bug)            -> exit 1 (unsolved: relatedOld = relatedOld++[newObj]) atk_2  aCreate appends twice                            -> exit 1 (list inequality) atk_3  aCreate returns 0                                -> exit 1 (out=newObj) atk_4  aGetOrCreate preexists ALSO appends              -> exit 1 (preexists->related=relatedOld) atk_5  aGetOrCreate wrong created flag (true)           -> exit 1 (out=(existingObj,false)) atk_6  aGetOrCreate else omits append (bug)             -> exit 1 (¬preexists frame) atk_7  aUpdateOrCreate preexists returns newObj         -> exit 1 (out=(existingObj,false)) atk_8  aCreate prepends [newObj]++related               -> exit 1 (exact list position) atk_9  aUpdateOrCreate else returns existingObj         -> exit 1 (out=(newObj,true)) atk_10 aCreate branches on newObj∈related; ∈-branch returns 0, else gold.

Precondition-shielded dead branch -> exit 0 VERIFIES (behaviorally = gold on reachable domain) atk_11 aCreate appends newObj+1 (boundary/off-by-one)   -> exit 1 (relatedOld++[newObj+1] != relatedOld++[newObj]) atk_12 aGetOrCreate else returns (newObj,false)         -> exit 1 (created flag must be true) All 11 genuinely-wrong impls (atk_1..9,11,12) REJECTED, each on the discriminating clause (confirmed by reading unsolved-goal text). Ungrounded-oracle echo attack impossible: axioms region empty; atk_3/5/7/9/12 confirm each output component individually pinned.

POSITIVE CONTROL atk_pos (= Solution.lean; structurally-correct impl): same_spec=True, exit 0 -> spec NON-VACUOUS.

MANDATORY RESOLVE (executed, not speculated): the ONLY verifying impls are atk_pos (correct control) and atk_10 (precondition-dead-branch, behaviorally = gold). Their faithful refined patch is the gold patch (sha1 7c5119b… identical to benchmark-verified/django__django-16256/patch.diff — atk_10's dead ∈-branch has NO Python counterpart since the fresh-object precondition newObj∉related is structurally guaranteed by create/get_or_create's new-row semantics). Materialized faithful_atk_10.patch and ran run_resolve('django__django-16256', patch, timeout=1800, retries=1) under `docker`:
  RESOLVE completed=True resolved=True attempts=1 flaky=False note=resolved
So every verifying wrong-impl's faithful patch RESOLVES. verify⇒correct holds; spec NOT broken.

**PREPATCH:** prepatch_1.lean (copy of Solution_prepatch_1.lean) -> exit 1, unsolved goal `related = relatedOld ++ [newObj]` — the un-settled-link bug the issue describes. prepatch_reproduced=true.

**REFINEMENT.MD AUDIT:** every leg is R / A-reference / I; NO kind-3.
  R legs: A1,A2,A3,A5,B1 (collection↔List Nat, pk↔Nat, (obj,created)↔Nat×Bool, freshness precondition) — clean bijections, G-CONF territory.
  I+R: B2 (concrete preexists branch, frame=relatedOld).
  A-reference: A4,B3 — awaited sync_to_async(self.<member>) modeled as synchronous append. Correspondence to the REAL callee is legitimate: axiom_check.py imports the genuine asgiref.sync.sync_to_async (the actual UNCHANGED callee the gold patch imports — NOT a stub, NOT patched repo code) and asserts value- AND side-effect-preservation over boundary + both branches + 2500 fuzz callables, plus link-vs-no-link observability. No consumed axiom exists; empty axioms region. conf_skip=true is legitimate (only non-trivial impl op is the A-reference append; no DB-free R/I computation to differential-test).

**VERDICT:** SOUND. 12 same-spec attacks run (11 genuinely-wrong all rejected on the discriminating clause; 1 precondition-dead verifies but is behaviorally gold), positive control verifies, prepatch reproduces the bug, and the sole verifying impls' materialized faithful patch was EXECUTED through the official harness and RESOLVED (completed=True, resolved=True). No verifying-but-wrong impl whose faithful patch fails to resolve exists. refinement.md is R/A-reference/I with sound A-reference correspondence to the real unchanged callee.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16256 (velvet). No spec-vs-repo divergence found on the modeled observable; no diverging input exists.

**SPEC FROZEN:** same_spec(VelvetBackend tables) = True for Solution.lean vs all 3 prepatches — spec region (axioms/pure/pre/post + method signatures/require/ensures) byte-identical; impl and prove_correct bodies elided in spec_view, so only impl differs.

### Checks re-run independently
- **G-VERIFY:** Solution.lean verifies, exit 0 via scripts/lean_verify.sh (400s).
- **G-DIFF:** prepatch_1 fails, exit 1, on exactly `⊢ relatedOld = relatedOld ++ [newObj]` — the inherited-QuerySet bug (produce-but-never-link) is correctly refuted by the frozen spec. All three prepatches share this shape.

FAITHFULNESS ANALYSIS vs real callees @ base 76e37513 (related_descriptors.py + contenttypes/fields.py), inspected:
- Carrier: parent's related collection -> List Nat of object identities; membership is exactly the F2P observable (acount/aget/assertEqual(new.simple,s1)). Sound abstraction; async machinery (event loop/thread) abstracted away via sync_to_async being behaviour-preserving (G-AX pass, exit 0 against real asgiref.sync 3.12.1: awaited result == sync result AND external collection identical).
- aCreate <-> acreate: real .create always produces a brand-new pk and links exactly once (reverse-FK: kwargs[field]=instance; m2m: super().create then self.add(new_obj); generic: sets ct+oid). Precondition newObj∉related always holds on the create path; post related=relatedOld++[newObj] matches.
- aGetOrCreate <-> aget_or_create: CONFIRMED in source. m2m get_or_create scopes get() to the related queryset (core_filters) and does `if created: self.add(...)`. created=False ⇔ object already in the related set → no add, membership unchanged → models preexists→existingObj∈related ∧ related=relatedOld. created=True ⇔ fresh object added → models ¬preexists→newObj∉related ∧ related=relatedOld++[newObj]. Matches on membership on both branches.
- aUpdateOrCreate <-> aupdate_or_create: identical shape; field refresh on the matching branch (defaults/through_defaults) is an out-of-carrier field write on an already-linked row (test_aupdate_or_create asserts field=3 but acount stays 1). Parent-collection membership unchanged → model keeps related=relatedOld. Matches.

Searched boundary + branch inputs (preexists/¬preexists, fresh/duplicate identities, all three relation carriers reverse-FK/forward-m2m/generic) for a membership-level disagreement between the modeled function and the real callee; none exists. Spec is neither too strong nor drifted from repo behavior on the tested observable. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution, prepatch_{1,2,3}) = True against VelvetBackend.language tables; spec region is frozen and impl/proof elided in the spec view. Baseline: the PUBLIC problem_statement is already maximally explicit — it quotes the gold patch verbatim ('async def acreate(self, **kwargs): return await sync_to_async(self.create)(**kwargs)'), names all three methods (acreate/aget_or_create/aupdate_or_create), states they must delegate to the related manager's OWN create/get_or_create/update_or_create through sync_to_async, and shows the added hunks at reverse-FK/forward-m2m sites. So the gold edit's content, intent, and shape are all public independent of this spec. Examined the spec view: it models three abstract methods over `related : List Nat` with postconditions settling a fresh object (related = relatedOld ++ [newObj]) and preexists/created branch semantics — behavioral correctness that is inherent to any spec and already fully described publicly. Comments reference the sync_to_async bridge concept (public), axiom_check.py, and mapping.md §2 (spec-internal pointers). No repo file:line specifics, no field/method names, and no gold-patch code appear in the spec view beyond what the problem_statement already discloses. Nothing in the spec view leaks the gold edit beyond the public problem_statement (hints_text excluded from baseline). Bundle is not relaxed (no RELAXED_LEAKAGE.md), so this is a straight NO-LEAKAGE, not a deferral.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
