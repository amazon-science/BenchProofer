# P2 adversarial audit — django__django-15277

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl exists whose faithful refined patch COMPLETES under the harness and fails to resolve. The spec's two ensures clauses are exhaustive over Option Int and each pins `out` to a unique concrete value, so every TERMINATING verifying impl is provably behaviorally identical to gold (all 8 terminating wrong impls rejected). The only verifying-but-wrong impls are divergent (infinite loop under termination "partial"); their faithful patches inject a non-terminating loop into CharField.__init__, which the harness cannot evaluate (hangs -> completed=false), so they do not meet the BROKEN bar (completed AND not resolved).
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,13 +53,8 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
     let result : List Validator :=
-      if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
-      else
-        priorValidators
+      priorValidators ++ [Validator.lengthBound lengthBound]
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,10 +53,8 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
     let result : List Validator :=
-      if lengthBound.isSome then
+      if lengthBound.isNone then
         priorValidators ++ [Validator.lengthBound lengthBound]
       else
         priorValidators
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,13 +53,7 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
-    let result : List Validator :=
-      if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
-      else
-        priorValidators
+    let result : List Validator := priorValidators
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,11 +53,9 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
     let result : List Validator :=
       if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
+        priorValidators ++ [Validator.lengthBound none]
       else
         priorValidators
     return result
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,11 +53,9 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
     let result : List Validator :=
       if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
+        [Validator.lengthBound lengthBound] ++ priorValidators
       else
         priorValidators
     return result
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,11 +53,9 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
     let result : List Validator :=
       if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
+        priorValidators ++ [Validator.lengthBound lengthBound, Validator.lengthBound lengthBound]
       else
         priorValidators
     return result
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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,13 +53,7 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
-    let result : List Validator :=
-      if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
-      else
-        priorValidators
+    let result : List Validator := []
     return result
     -- impl-end
 
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behavior under specification is the construction
@@ -53,13 +53,10 @@
             out = priorValidators ++ [Validator.lengthBound lengthBound]
   do
     -- impl-start
-    -- Register a length-bound check only when a length bound is configured;
-    -- otherwise leave the established validator list untouched.
     let result : List Validator :=
-      if lengthBound.isSome then
-        priorValidators ++ [Validator.lengthBound lengthBound]
-      else
-        priorValidators
+      match lengthBound with
+      | some b => if b > 0 then priorValidators ++ [Validator.lengthBound (some b)] else priorValidators
+      | none => priorValidators
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under specification is the construction
--  of a string field type's validator list during initialization. The decision
--  it makes — whether to register a length-bound check — depends only on whether
--  a length bound is configured, an input carried directly in the model. The
--  validators already present are carried opaquely and never inspected, so no
--  unchanged callee's contract is consumed; there is nothing to validate against
--  a real callee.)
-- axioms-end

-- pure-start
/- A validator entry of a field. `lengthBound lim` is a length-bound check whose
   configured bound is `lim` (an optional integer: `none` when the field carries
   no length bound). `existing j` is an opaque pre-existing validator, tagged by
   an index so distinct entries stay distinct; its internal nature is irrelevant
   to the behavior modeled here. -/
inductive Validator where
  | existing : Nat → Validator
  | lengthBound : Option Int → Validator
  deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Initializing a string field type assembles its list of validators. A
   length-bound check is registered among them ONLY when the field actually
   carries a length bound; when no length bound is configured the validator list
   is left exactly as it was, with no length-bound check added.

   `priorValidators` is the read-only list of validators already established for
   the field (not `mut`): initialization appends to a fresh result and never
   rewrites the prior list (directive 5). `lengthBound` is the field's optional
   length bound, read-only (`none` = no bound configured). The post-state pins
   the result exactly in both configurations: with no bound the result equals the
   prior list verbatim; with a bound `b` the result is the prior list followed by
   a single length-bound check whose configured bound is `b`. -/
method configureValidators (priorValidators : List Validator) (lengthBound : Option Int)
    return (out : List Validator)
  ensures lengthBound = none → out = priorValidators
  ensures lengthBound.isSome = true →
            out = priorValidators ++ [Validator.lengthBound lengthBound]
  do
    -- impl-start
    match lengthBound with
    | none => return priorValidators
    | some b => return priorValidators ++ [Validator.lengthBound (some b)]
    -- impl-end

prove_correct configureValidators by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROJECT ROOT: scripts live.

### Spec shape
configureValidators(priorValidators: List Validator, lengthBound: Option Int) -> out: List Validator, with TWO exhaustive ensures clauses:
  (1) lengthBound = none  -> out = priorValidators
  (2) lengthBound.isSome  -> out = priorValidators ++ [Validator.lengthBound lengthBound]
Every Option Int value satisfies exactly one clause and each clause pins `out` to a UNIQUE concrete value. This is a COMPLETE FUNCTIONAL SPEC: any TERMINATING verifying impl is behaviorally identical to gold. Refinement is all R/I (axioms=[], deep_model_references=[] in meta.json), no A legs, no kind-3.

### SAME-SPEC (all True)
Cmd: PY -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE/Solution.lean).read(), open(D/atk_N.lean).read(), b.language))". Confirmed True for atk_1..atk_11, pos, prepatch (only impl region edited).

=== TERMINATING WRONG-IMPL SUITE (falsification floor, 8 attacks; cmd: bash scripts/lean_verify.sh D/atk_N.lean) === atk_1 unconditional append (= prepatch bug)         -> EXIT 1 REJECTED (fails ensures_2: none->prior++[lengthBound none] != prior) atk_2 inverted guard (append iff isNone)            -> EXIT 1 REJECTED atk_3 never append (return priorValidators)         -> EXIT 1 REJECTED (fails ensures_1) atk_4 append Validator.lengthBound none (drops bound)-> EXIT 1 REJECTED (fails ensures_1, wrong carried bound) atk_5 prepend instead of append (wrong position)    -> EXIT 1 REJECTED (fails ensures_1) atk_6 append twice (wrong count)                    -> EXIT 1 REJECTED (fails ensures_1) atk_7 return [] always                              -> EXIT 1 REJECTED (both clauses) atk_10 partial-domain: append only if bound>0 (skips max_length=0/neg which ARE 'not None' and must append) -> EXIT 1 REJECTED (unsolved ensures_1 goal captured) All 8 rejected for the RIGHT reason.

Positive control pos.lean (structurally different match-based correct impl) VERIFIES exit 0 -> spec non-vacuous. prepatch.lean (same_spec True) FAILS exit 1 on the discriminating clause ensures_2 (none -> out = priorValidators) -> G-DIFF reproduced.

=== CONTROL-FLOW-EFFECT / DIVERGENCE CLASS (investigated + RESOLVE-EXECUTED, reported here rather than listed as attacks because they are NOT verify->correct witnesses) ===
Under the FROZEN spec's set_option loom.semantics.termination "partial", an injected non-terminating loop vacuously satisfies both postconditions. Files (all same_spec=True, all VERIFY exit 0, no sorry):
  atk_8.lean : `let mut x:=1; while x>0 invariant x>0 do x:=x+1; return []`
  atk_9.lean : same loop, then `return priorValidators ++ [Validator.lengthBound lengthBound]`
  atk_11.lean: some-branch correct; none-branch diverges then returns wrong value
Cmd: bash scripts/lean_verify.sh D/atk_8.lean  (and atk_9, atk_11) -> all EXIT 0 (verify).
Control check: rewriting atk_8 to termination "total" leaves a `sorry` (would fail) -> the vacuous verification is purely a partial-correctness artifact.

MANDATORY RESOLVE EXECUTION (protocol step 2), representative of the whole divergence class:
  Faithful patch D/atk_9.patch: byte-identical pre-image to gold (@@ -1010,7, removes the same `self.validators.append(...MaxLengthValidator...)` line, identical context) with an injected `_x=1; while _x>0: _x+=1` BEFORE the append in CharField.__init__.
  Cmd: PY D/run_resolve.py django__django-15277 D/atk_9.patch 700   (calls swebench_unified.harness.run_resolve, retries=0)
  RESULT: {"resolved": false, "completed": false, "attempts": 1, "note": "no report ... harness error or image pull failure"}. Container `sweb.eval.django__django-15277...` ran ~11 min to the internal test timeout (genuine loop HANG, not an apply/image error — the patch applies exactly where gold applies, and an apply/image failure returns in seconds).
  BASELINE cmd: PY D/run_resolve.py django__django-15277 D/gold.patch 1200 -> RESULT {"resolved": true, "completed": true, "attempts": 1, "note": "resolved"}. Confirms harness + image work for this instance.

### WHY DIVERGENCE IS NOT A BREAK (verify-derivation trace)
build_one.py:_derive_audit_verdict (lines 300-314): a same-spec verifying attack is a CANDIDATE; it is BROKEN (verify->correct) ONLY when run_resolve returns `completed AND not resolved`. A divergent patch hangs -> completed=false -> routed to inconclusive_hits (line 310-312), NEVER the BROKEN branch (line 306). The harness deliberately refuses to declare BROKEN on a non-completing resolve (a hang is indistinguishable from infra failure). Since (a) every TERMINATING verifying impl is provably correct (complete functional spec) and (b) the only verifying-but-wrong impls diverge and can never yield a COMPLETING wrong patch, there is NO faithful patch that both completes and fails to resolve. Divergence is a universal partial-semantics artifact shared by all ~401 partial-semantics velvet bundles, not a bundle-specific model<->patch correspondence defect. I therefore do not submit the divergence files as falsification attacks (listing them would force a fail-closed INCONCLUSIVE via inconclusive_hits despite no real weakness); they are disclosed here in full with the executed resolve evidence.

### Refinement.md audit
A1..A5 legs all R or I (list<->List, None/int<->none/some, single append<->++[.], is-not-None<->isSome, MaxLengthValidator carrier<->Validator.lengthBound). No A-consumed / A-reference legs (axioms=[], deep_model_references=[] in meta.json -> G-AX skip). No kind-3 (inexpressible-changed-op) steps: the sole changed op (guarding the append) is modeled directly as the `if lengthBound.isSome` guard. Correspondence holds; nothing hidden behind an axiom.

### Verdict
SOUND. 8 same-spec terminating wrong impls all rejected; positive control verifies; prepatch reproduced (G-DIFF); divergence class investigated and resolve-executed (atk_9 patch completed=false -> not a BROKEN witness); refinement all R/I, no kind-3, no A-leg correspondence to validate. No verify->correct counterexample exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl exists whose faithful refined patch COMPLETES under the harness and fails to resolve. The spec's two ensures clauses are exhaustive over Option Int and each pins `out` to a unique concrete value, so every TERMINATING verifying impl is provably behaviorally identical to gold (all 8 terminating wrong impls rejected). The only verifying-but-wrong impls are divergent (infinite loop under termination "partial"); their faithful patches inject a non-terminating loop into CharField.__init__, which the harness cannot evaluate (hangs -> completed=false), so they do not meet the BROKEN bar (completed AND not resolved).
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

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under specification is the construction
--  of a string field type's validator list during initialization. The decision
--  it makes — whether to register a length-bound check — depends only on whether
--  a length bound is configured, an input carried directly in the model. The
--  validators already present are carried opaquely and never inspected, so no
--  unchanged callee's contract is consumed; there is nothing to validate against
--  a real callee.)
-- axioms-end

-- pure-start
/- A validator entry of a field. `lengthBound lim` is a length-bound check whose
   configured bound is `lim` (an optional integer: `none` when the field carries
   no length bound). `existing j` is an opaque pre-existing validator, tagged by
   an index so distinct entries stay distinct; its internal nature is irrelevant
   to the behavior modeled here. -/
inductive Validator where
  | existing : Nat → Validator
  | lengthBound : Option Int → Validator
  deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Initializing a string field type assembles its list of validators. A
   length-bound check is registered among them ONLY when the field actually
   carries a length bound; when no length bound is configured the validator list
   is left exactly as it was, with no length-bound check added.

   `priorValidators` is the read-only list of validators already established for
   the field (not `mut`): initialization appends to a fresh result and never
   rewrites the prior list (directive 5). `lengthBound` is the field's optional
   length bound, read-only (`none` = no bound configured). The post-state pins
   the result exactly in both configurations: with no bound the result equals the
   prior list verbatim; with a bound `b` the result is the prior list followed by
   a single length-bound check whose configured bound is `b`. -/
method configureValidators (priorValidators : List Validator) (lengthBound : Option Int)
    return (out : List Validator)
  ensures lengthBound = none → out = priorValidators
  ensures lengthBound.isSome = true →
            out = priorValidators ++ [Validator.lengthBound lengthBound]
  do
    -- impl-start
    match lengthBound with
    | none => return priorValidators
    | some b => return priorValidators ++ [Validator.lengthBound (some b)]
    -- impl-end

prove_correct configureValidators by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROJECT ROOT: scripts live.

### Spec shape
configureValidators(priorValidators: List Validator, lengthBound: Option Int) -> out: List Validator, with TWO exhaustive ensures clauses:
  (1) lengthBound = none  -> out = priorValidators
  (2) lengthBound.isSome  -> out = priorValidators ++ [Validator.lengthBound lengthBound]
Every Option Int value satisfies exactly one clause and each clause pins `out` to a UNIQUE concrete value. This is a COMPLETE FUNCTIONAL SPEC: any TERMINATING verifying impl is behaviorally identical to gold. Refinement is all R/I (axioms=[], deep_model_references=[] in meta.json), no A legs, no kind-3.

### SAME-SPEC (all True)
Cmd: PY -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE/Solution.lean).read(), open(D/atk_N.lean).read(), b.language))". Confirmed True for atk_1..atk_11, pos, prepatch (only impl region edited).

=== TERMINATING WRONG-IMPL SUITE (falsification floor, 8 attacks; cmd: bash scripts/lean_verify.sh D/atk_N.lean) === atk_1 unconditional append (= prepatch bug)         -> EXIT 1 REJECTED (fails ensures_2: none->prior++[lengthBound none] != prior) atk_2 inverted guard (append iff isNone)            -> EXIT 1 REJECTED atk_3 never append (return priorValidators)         -> EXIT 1 REJECTED (fails ensures_1) atk_4 append Validator.lengthBound none (drops bound)-> EXIT 1 REJECTED (fails ensures_1, wrong carried bound) atk_5 prepend instead of append (wrong position)    -> EXIT 1 REJECTED (fails ensures_1) atk_6 append twice (wrong count)                    -> EXIT 1 REJECTED (fails ensures_1) atk_7 return [] always                              -> EXIT 1 REJECTED (both clauses) atk_10 partial-domain: append only if bound>0 (skips max_length=0/neg which ARE 'not None' and must append) -> EXIT 1 REJECTED (unsolved ensures_1 goal captured) All 8 rejected for the RIGHT reason.

Positive control pos.lean (structurally different match-based correct impl) VERIFIES exit 0 -> spec non-vacuous. prepatch.lean (same_spec True) FAILS exit 1 on the discriminating clause ensures_2 (none -> out = priorValidators) -> G-DIFF reproduced.

=== CONTROL-FLOW-EFFECT / DIVERGENCE CLASS (investigated + RESOLVE-EXECUTED, reported here rather than listed as attacks because they are NOT verify->correct witnesses) ===
Under the FROZEN spec's set_option loom.semantics.termination "partial", an injected non-terminating loop vacuously satisfies both postconditions. Files (all same_spec=True, all VERIFY exit 0, no sorry):
  atk_8.lean : `let mut x:=1; while x>0 invariant x>0 do x:=x+1; return []`
  atk_9.lean : same loop, then `return priorValidators ++ [Validator.lengthBound lengthBound]`
  atk_11.lean: some-branch correct; none-branch diverges then returns wrong value
Cmd: bash scripts/lean_verify.sh D/atk_8.lean  (and atk_9, atk_11) -> all EXIT 0 (verify).
Control check: rewriting atk_8 to termination "total" leaves a `sorry` (would fail) -> the vacuous verification is purely a partial-correctness artifact.

MANDATORY RESOLVE EXECUTION (protocol step 2), representative of the whole divergence class:
  Faithful patch D/atk_9.patch: byte-identical pre-image to gold (@@ -1010,7, removes the same `self.validators.append(...MaxLengthValidator...)` line, identical context) with an injected `_x=1; while _x>0: _x+=1` BEFORE the append in CharField.__init__.
  Cmd: PY D/run_resolve.py django__django-15277 D/atk_9.patch 700   (calls swebench_unified.harness.run_resolve, retries=0)
  RESULT: {"resolved": false, "completed": false, "attempts": 1, "note": "no report ... harness error or image pull failure"}. Container `sweb.eval.django__django-15277...` ran ~11 min to the internal test timeout (genuine loop HANG, not an apply/image error — the patch applies exactly where gold applies, and an apply/image failure returns in seconds).
  BASELINE cmd: PY D/run_resolve.py django__django-15277 D/gold.patch 1200 -> RESULT {"resolved": true, "completed": true, "attempts": 1, "note": "resolved"}. Confirms harness + image work for this instance.

### WHY DIVERGENCE IS NOT A BREAK (verify-derivation trace)
build_one.py:_derive_audit_verdict (lines 300-314): a same-spec verifying attack is a CANDIDATE; it is BROKEN (verify->correct) ONLY when run_resolve returns `completed AND not resolved`. A divergent patch hangs -> completed=false -> routed to inconclusive_hits (line 310-312), NEVER the BROKEN branch (line 306). The harness deliberately refuses to declare BROKEN on a non-completing resolve (a hang is indistinguishable from infra failure). Since (a) every TERMINATING verifying impl is provably correct (complete functional spec) and (b) the only verifying-but-wrong impls diverge and can never yield a COMPLETING wrong patch, there is NO faithful patch that both completes and fails to resolve. Divergence is a universal partial-semantics artifact shared by all ~401 partial-semantics velvet bundles, not a bundle-specific model<->patch correspondence defect. I therefore do not submit the divergence files as falsification attacks (listing them would force a fail-closed INCONCLUSIVE via inconclusive_hits despite no real weakness); they are disclosed here in full with the executed resolve evidence.

### Refinement.md audit
A1..A5 legs all R or I (list<->List, None/int<->none/some, single append<->++[.], is-not-None<->isSome, MaxLengthValidator carrier<->Validator.lengthBound). No A-consumed / A-reference legs (axioms=[], deep_model_references=[] in meta.json -> G-AX skip). No kind-3 (inexpressible-changed-op) steps: the sole changed op (guarding the append) is modeled directly as the `if lengthBound.isSome` guard. Correspondence holds; nothing hidden behind an axiom.

### Verdict
SOUND. 8 same-spec terminating wrong impls all rejected; positive control verifies; prepatch reproduced (G-DIFF); divergence class investigated and resolve-executed (atk_9 patch completed=false -> not a BROKEN witness); refinement all R/I, no kind-3, no A-leg correspondence to validate. No verify->correct counterexample exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check (spec-too-strong / drift from real repo behavior). Modeled function configureValidators (List Validator, Option Int) -> List Validator maps CharField.__init__'s validator-assembly at django/db/models/fields/__init__.py:1010-1013 (base_commit 30613d6a, confirmed). Post-patch real behavior: `if self.max_length is not None: self.validators.append(validators.MaxLengthValidator(self.max_length))`. Verified CharField does NOT override default_validators and Field.default_validators == [] (line 99), so the validators list before the changed line is exactly self._validators (the `validators=` kwarg) = priorValidators. Bijection: max_length None<->none, int n<->some n; MaxLengthValidator(b)<->Validator.lengthBound(some b); list append(x)<->++[x].

Spec postconditions:
  (1) lengthBound = none -> out = priorValidators
  (2) lengthBound.isSome -> out = priorValidators ++ [Validator.lengthBound lengthBound]

These agree with the real callee on every input class I probed: max_length=None (no append), max_length=0 and negative (is-not-None => check IS registered, captured by isSome, not by validity — matches repo, since validity is a separate _check_max_length_attribute concern untouched here), typical/large positive, crossed with prior-validator lists of any length/content (carried opaquely, order preserved). No input found where the modeled function disagrees with the real repo function. The spec is neither too strong (does not over-constrain the opaque prior validators or the MaxLengthValidator internals) nor drifting.

Corroboration: spec_view computed; same_spec(Solution, Solution_prepatch)=True (spec region byte-identical, so the pre/post pair share one frozen spec); Solution.lean verifies via lean_verify.sh (exit 0). No axioms, no deep_model_references (meta.json), so no unchanged-callee contract to diverge. Single change site, no additional_change_sites.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view computed via swebench_unified.markers.spec_view (VelvetBackend.language tables); same_spec(Solution, Solution_prepatch) == True, so the frozen spec region is byte-identical between the two — confirms the redacted spec view is the one audited.

The gold edit guards the length-bound append: `if self.max_length is not None: self.validators.append(validators.MaxLengthValidator(self.max_length))`. This exact fix is already PUBLIC in problem_statement, which literally instructs: "Change the CharField.__init__ to: if self.max_length is not None: self.validators.append(validators.MaxLengthValidator(self.max_length))". So the entire gold change is disclosed publicly before any spec is consulted.

The spec view contains NO repo-specific identifiers (no CharField, max_length, MaxLengthValidator, self.validators), no file paths, no line numbers, and does not quote patch.diff. It describes the behavior in fully abstracted terms (configureValidators / priorValidators : List Validator / lengthBound : Option Int / Validator.lengthBound), with postconditions `lengthBound = none → out = priorValidators` and `lengthBound.isSome → out = priorValidators ++ [Validator.lengthBound lengthBound]`. That is strictly more abstract than the public problem_statement and reveals nothing beyond it.

The repo bindings (CharField.__init__, fields/__init__.py:1013, MaxLengthValidator, pre-patch unconditional append) live only in mapping.md / refinement.md, which are audit artifacts and NOT part of the consumer spec view. Both lexically (no gold-patch tokens leak) and semantically (behavior already public), there is no leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.