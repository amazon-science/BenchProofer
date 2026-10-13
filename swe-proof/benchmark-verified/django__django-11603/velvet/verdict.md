# P2 adversarial audit — django__django-11603

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
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,9 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
+    let acceptsDistinct : Bool := false
     if distinct && !acceptsDistinct then
       return Except.error InitErr.distinctNotAccepted
     else
@@ -81,7 +79,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
+    let acceptsDistinct : Bool := false
     if distinct && !acceptsDistinct then
       return Except.error InitErr.distinctNotAccepted
     else
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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,13 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "AVG", distinct := distinct }
+    return Except.ok { function := "AVG", distinct := false }
     -- impl-end
 
 prove_correct avgInit by
@@ -81,11 +75,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "SUM", distinct := distinct }
+    return Except.ok { function := "SUM", distinct := false }
     -- impl-end
 
 prove_correct sumInit by
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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,13 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "AVG", distinct := distinct }
+    return Except.ok { function := "SUM", distinct := distinct }
     -- impl-end
 
 prove_correct avgInit by
@@ -81,11 +75,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "SUM", distinct := distinct }
+    return Except.ok { function := "AVG", distinct := distinct }
     -- impl-end
 
 prove_correct sumInit by
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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,13 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "AVG", distinct := distinct }
+    return Except.ok { function := "AVG", distinct := true }
     -- impl-end
 
 prove_correct avgInit by
@@ -81,11 +75,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "SUM", distinct := distinct }
+    return Except.ok { function := "SUM", distinct := true }
     -- impl-end
 
 prove_correct sumInit by
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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,13 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "AVG", distinct := distinct }
+    return Except.ok { function := "AVG", distinct := !distinct }
     -- impl-end
 
 prove_correct avgInit by
@@ -81,11 +75,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "SUM", distinct := distinct }
+    return Except.ok { function := "SUM", distinct := !distinct }
     -- impl-end
 
 prove_correct sumInit by
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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,13 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "AVG", distinct := distinct }
+    return Except.error InitErr.distinctNotAccepted
     -- impl-end
 
 prove_correct avgInit by
@@ -81,11 +75,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
-      return Except.error InitErr.distinctNotAccepted
-    else
-      return Except.ok { function := "SUM", distinct := distinct }
+    return Except.error InitErr.distinctNotAccepted
     -- impl-end
 
 prove_correct sumInit by
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The shared construction-time guard that the two modeled
@@ -60,10 +60,7 @@
   ensures out = construct "AVG" true distinct
   do
     -- impl-start
-    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
-    -- accepts the duplicate-elimination option.
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
+    if !distinct then
       return Except.error InitErr.distinctNotAccepted
     else
       return Except.ok { function := "AVG", distinct := distinct }
@@ -81,8 +78,7 @@
   ensures out = construct "SUM" true distinct
   do
     -- impl-start
-    let acceptsDistinct : Bool := true
-    if distinct && !acceptsDistinct then
+    if !distinct then
       return Except.error InitErr.distinctNotAccepted
     else
       return Except.ok { function := "SUM", distinct := distinct }
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The shared construction-time guard that the two modeled
   aggregates route through — refuse a duplicate-elimination request for a kind
   that does not accept it, otherwise build and record the request — is modeled
   DEEPLY in the `pure` region (`construct`). The per-kind capability is concrete
   data, validated against the real classes by G-CONF; there is no module-level
   `axiom`. -/
-- axioms-end

-- pure-start
/- Refusing a construction because a duplicate-elimination request was made of a
   kind that does not accept that option. The only construction outcome the
   desired behaviour distinguishes from success. -/
inductive InitErr where
  | distinctNotAccepted
  deriving DecidableEq

/- The observable content of a constructed aggregate: which aggregate it is (its
   SQL function name) and whether it was asked to aggregate over the set of
   DISTINCT input values. These are the only fields the desired behaviour
   constrains; everything else about the aggregate is orthogonal (mapping.md
   §2). -/
structure AggState where
  function : String
  distinct : Bool
  deriving DecidableEq

/- The shared construction guard, modeled deeply. `acceptsDistinct` is the
   per-kind capability the guard consults: when a duplicate-elimination option
   is requested of a kind that does not accept it, construction is refused;
   otherwise the aggregate is built and the requested option is recorded on it
   unchanged. Pinned by each method's `ensures`. -/
def construct (function : String) (acceptsDistinct : Bool) (distinct : Bool) :
    Except InitErr AggState :=
  if distinct && !acceptsDistinct then Except.error .distinctNotAccepted
  else Except.ok { function := function, distinct := distinct }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct an averaging aggregate over a source expression, optionally over
   the set of DISTINCT input values. Desired behaviour: an averaging aggregate
   accepts a duplicate-elimination request, so construction with the option set
   must SUCCEED and the built aggregate must carry that option through unchanged
   (a downstream aggregation over distinct values depends on it being recorded
   faithfully, not merely accepted). -/
method avgInit (distinct : Bool) return (out : Except InitErr AggState)
  ensures out = construct "AVG" true distinct
  do
    -- impl-start
    if distinct then
      return Except.ok { distinct := true, function := "AVG" }
    else
      return Except.ok { distinct := false, function := "AVG" }
    -- impl-end

prove_correct avgInit by
  loom_solve <;> simp_all [construct]

/- Construct a summing aggregate over a source expression, optionally over the
   set of DISTINCT input values. Same desired behaviour as the averaging
   aggregate: a duplicate-elimination request must succeed and be recorded on
   the built aggregate unchanged. -/
method sumInit (distinct : Bool) return (out : Except InitErr AggState)
  ensures out = construct "SUM" true distinct
  do
    -- impl-start
    if distinct then
      return Except.ok { distinct := true, function := "SUM" }
    else
      return Except.ok { distinct := false, function := "SUM" }
    -- impl-end

prove_correct sumInit by
  loom_solve <;> simp_all [construct]
```

Prepatch bug re-encoded as an attack: `True`.

SUMMARY: 8 same-spec wrong impls encoded (all same_spec=True, verified against Solution.lean via swebench_unified.markers.same_spec, velvet LanguageTables). Verify cmd for each: `bash scripts/lean_verify.sh <file>`. All 7 TERMINATING wrong impls are REJECTED (EXIT=1); positive control verifies (EXIT=0); prepatch bug reproduced (atk_1). No same-spec, verifying, TERMINATING wrong impl exists -> the spec is TIGHT and SOUND.

SPEC SHAPE: total, deterministic, fully-transparent functional equality `out = construct "AVG"/"SUM" true distinct`, where `construct` is a concrete pure fn (no axioms, no opaque oracle, no `:|` stub). For every terminating impl the postcondition pins BOTH the function name AND that the requested flag is recorded unchanged (`distinct:=distinct`).

### ATTACK RESULTS (EXIT code):
- atk_1 prepatch bug (acceptsDistinct:=false both kinds; refuse distinct): EXIT=1 rejected (at distinct=true spec demands Except.ok, impl gives Except.error -> goal False). This IS the prepatch bug -> prepatch_reproduced=true.
- atk_2 flag-drop (distinct:=false always): EXIT=1 rejected (residual goal distinct=false) -- confirms the load-bearing `distinct:=distinct` clause.
- atk_3 swapped names AVG<->SUM: EXIT=1 rejected (string mismatch).
- atk_4 hardcoded distinct:=true: EXIT=1 rejected (fails at distinct=false).
- atk_5 negated flag distinct:=!distinct: EXIT=1 rejected.
- atk_6 always Except.error (terminating ungrounded refusal): EXIT=1 rejected.
- atk_8 inverted control-flow guard (if !distinct then error): EXIT=1 rejected.
- atk_pos (POSITIVE CONTROL, structurally different but correct; reversed field order; proof `loom_solve <;> simp_all [construct]`): same_spec=True, EXIT=0 verifies -> spec non-vacuous.

DIVERGENCE PROBE (partial-correctness escape hatch) -- RUN, NOT SPECULATED:
- atk_7 = atk_7.lean: byte-identical to atk_6 (returns Except.error) but preceded by a non-terminating `let mut i:=0; while i = i invariant True do i:=i+1`. Under `set_option loom.semantics.termination "partial"` the postcondition is vacuously satisfied on the divergent path. same_spec=True, verify EXIT=0 (VERIFIES). proof `prove_correct ... by loom_solve`.
- DECISIVE CONTRAST: atk_6 (identical error return, TERMINATING) is REJECTED; atk_7 (same return, made non-terminating) VERIFIES. Hence atk_7 verifies PURELY via the partial-correctness vacuity hatch, not via any weakness of THIS spec. Divergence vacuously satisfies ANY postcondition under `termination partial` -- a universal semantic property affecting every velvet partial-correctness bundle equally, not a per-spec defect.
- PER PROTOCOL I materialized atk_7's faithful refined patch (atk_7.patch: adds allow_distinct=True to Avg and Sum AND a divergent `def __init__: i=0; while i==i: i=i+1`) and RAN it through the official harness via run_resolve("django__django-11603", patch, timeout=900, retries=0).
  RESULT: {"resolved": false, "completed": false, "note": "no report ... harness error", "wall_s": 970.8}. The divergent __init__ hangs the F2P tests until the harness test-timeout, so NO report is produced -> completed=false = INCONCLUSIVE, NOT a clean `completed && not resolved`.
  GOLD CONTROL: run_resolve on benchmark-verified/django__django-11603/patch.diff -> {"resolved": true, "completed": true, "wall_s": 73.4} -> harness works for this instance.
- WHY THIS IS NOT A BREAK: verify=>correct falsification requires a same-spec verifying impl whose faithful patch RUNS to completion and FAILS the hidden tests (completed && not resolved). atk_7's patch does not fail tests -- it fails to terminate, which the mechanized derivation (construct/build_one.py: BROKEN iff `r.completed and not r.resolved`) records as inconclusive, never as a break. A hanging patch is evidence of nontermination (permitted by partial-correctness by design), not evidence the spec admits an incorrect BEHAVIOR. Admitting it would falsely 'break' every velvet bundle. Precedent: neighboring django-11490's divergence/empty attack also returned completed=false and that bundle still PASSED G-EQ. atk_7 is therefore documented but EXCLUDED from the gate-counting attack list.

REFINEMENT.md AUDIT (step 3): NO A-legs -- confirmed no `axiom` and no `:|` stub in Solution.lean; G-AX genuinely VACUOUS. Every leg is R or I; NO kind-3 (no inexpressible changed op hand-waved). The only changed datum (allow_distinct=True) is modeled as concrete data (acceptsDistinct:=true, an I op) consumed by the deeply-modeled `construct`; the orthogonal super().__init__ is a legitimate R-identity (gold patch does not touch __init__). refinement.md legs 1-4 for avgInit/sumInit correspond faithfully to the gold hunks (add allow_distinct=True to Avg/Sum) routed through the unchanged Aggregate.__init__ guard. mapping.md bijections (bool<->Bool, function/distinct fields, TypeError<->Except.error) are correct.

FLOOR: 7 terminating attacks (>=5), prepatch reproduced (atk_1), positive control verifies (atk_pos). Gold resolves. -> clean SOUND pass. My verdict is advisory; the runner re-runs the 7 rejected attacks + positive control.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The shared construction-time guard that the two modeled
   aggregates route through — refuse a duplicate-elimination request for a kind
   that does not accept it, otherwise build and record the request — is modeled
   DEEPLY in the `pure` region (`construct`). The per-kind capability is concrete
   data, validated against the real classes by G-CONF; there is no module-level
   `axiom`. -/
-- axioms-end

-- pure-start
/- Refusing a construction because a duplicate-elimination request was made of a
   kind that does not accept that option. The only construction outcome the
   desired behaviour distinguishes from success. -/
inductive InitErr where
  | distinctNotAccepted
  deriving DecidableEq

/- The observable content of a constructed aggregate: which aggregate it is (its
   SQL function name) and whether it was asked to aggregate over the set of
   DISTINCT input values. These are the only fields the desired behaviour
   constrains; everything else about the aggregate is orthogonal (mapping.md
   §2). -/
structure AggState where
  function : String
  distinct : Bool
  deriving DecidableEq

/- The shared construction guard, modeled deeply. `acceptsDistinct` is the
   per-kind capability the guard consults: when a duplicate-elimination option
   is requested of a kind that does not accept it, construction is refused;
   otherwise the aggregate is built and the requested option is recorded on it
   unchanged. Pinned by each method's `ensures`. -/
def construct (function : String) (acceptsDistinct : Bool) (distinct : Bool) :
    Except InitErr AggState :=
  if distinct && !acceptsDistinct then Except.error .distinctNotAccepted
  else Except.ok { function := function, distinct := distinct }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct an averaging aggregate over a source expression, optionally over
   the set of DISTINCT input values. Desired behaviour: an averaging aggregate
   accepts a duplicate-elimination request, so construction with the option set
   must SUCCEED and the built aggregate must carry that option through unchanged
   (a downstream aggregation over distinct values depends on it being recorded
   faithfully, not merely accepted). -/
method avgInit (distinct : Bool) return (out : Except InitErr AggState)
  ensures out = construct "AVG" true distinct
  do
    -- impl-start
    if distinct then
      return Except.ok { distinct := true, function := "AVG" }
    else
      return Except.ok { distinct := false, function := "AVG" }
    -- impl-end

prove_correct avgInit by
  loom_solve <;> simp_all [construct]

/- Construct a summing aggregate over a source expression, optionally over the
   set of DISTINCT input values. Same desired behaviour as the averaging
   aggregate: a duplicate-elimination request must succeed and be recorded on
   the built aggregate unchanged. -/
method sumInit (distinct : Bool) return (out : Except InitErr AggState)
  ensures out = construct "SUM" true distinct
  do
    -- impl-start
    if distinct then
      return Except.ok { distinct := true, function := "SUM" }
    else
      return Except.ok { distinct := false, function := "SUM" }
    -- impl-end

prove_correct sumInit by
  loom_solve <;> simp_all [construct]
```

Prepatch bug re-encoded as an attack: `True`.

SUMMARY: 8 same-spec wrong impls encoded (all same_spec=True, verified against Solution.lean via swebench_unified.markers.same_spec, velvet LanguageTables). Verify cmd for each: `bash scripts/lean_verify.sh <file>`. All 7 TERMINATING wrong impls are REJECTED (EXIT=1); positive control verifies (EXIT=0); prepatch bug reproduced (atk_1). No same-spec, verifying, TERMINATING wrong impl exists -> the spec is TIGHT and SOUND.

SPEC SHAPE: total, deterministic, fully-transparent functional equality `out = construct "AVG"/"SUM" true distinct`, where `construct` is a concrete pure fn (no axioms, no opaque oracle, no `:|` stub). For every terminating impl the postcondition pins BOTH the function name AND that the requested flag is recorded unchanged (`distinct:=distinct`).

### ATTACK RESULTS (EXIT code):
- atk_1 prepatch bug (acceptsDistinct:=false both kinds; refuse distinct): EXIT=1 rejected (at distinct=true spec demands Except.ok, impl gives Except.error -> goal False). This IS the prepatch bug -> prepatch_reproduced=true.
- atk_2 flag-drop (distinct:=false always): EXIT=1 rejected (residual goal distinct=false) -- confirms the load-bearing `distinct:=distinct` clause.
- atk_3 swapped names AVG<->SUM: EXIT=1 rejected (string mismatch).
- atk_4 hardcoded distinct:=true: EXIT=1 rejected (fails at distinct=false).
- atk_5 negated flag distinct:=!distinct: EXIT=1 rejected.
- atk_6 always Except.error (terminating ungrounded refusal): EXIT=1 rejected.
- atk_8 inverted control-flow guard (if !distinct then error): EXIT=1 rejected.
- atk_pos (POSITIVE CONTROL, structurally different but correct; reversed field order; proof `loom_solve <;> simp_all [construct]`): same_spec=True, EXIT=0 verifies -> spec non-vacuous.

DIVERGENCE PROBE (partial-correctness escape hatch) -- RUN, NOT SPECULATED:
- atk_7 = atk_7.lean: byte-identical to atk_6 (returns Except.error) but preceded by a non-terminating `let mut i:=0; while i = i invariant True do i:=i+1`. Under `set_option loom.semantics.termination "partial"` the postcondition is vacuously satisfied on the divergent path. same_spec=True, verify EXIT=0 (VERIFIES). proof `prove_correct ... by loom_solve`.
- DECISIVE CONTRAST: atk_6 (identical error return, TERMINATING) is REJECTED; atk_7 (same return, made non-terminating) VERIFIES. Hence atk_7 verifies PURELY via the partial-correctness vacuity hatch, not via any weakness of THIS spec. Divergence vacuously satisfies ANY postcondition under `termination partial` -- a universal semantic property affecting every velvet partial-correctness bundle equally, not a per-spec defect.
- PER PROTOCOL I materialized atk_7's faithful refined patch (atk_7.patch: adds allow_distinct=True to Avg and Sum AND a divergent `def __init__: i=0; while i==i: i=i+1`) and RAN it through the official harness via run_resolve("django__django-11603", patch, timeout=900, retries=0).
  RESULT: {"resolved": false, "completed": false, "note": "no report ... harness error", "wall_s": 970.8}. The divergent __init__ hangs the F2P tests until the harness test-timeout, so NO report is produced -> completed=false = INCONCLUSIVE, NOT a clean `completed && not resolved`.
  GOLD CONTROL: run_resolve on benchmark-verified/django__django-11603/patch.diff -> {"resolved": true, "completed": true, "wall_s": 73.4} -> harness works for this instance.
- WHY THIS IS NOT A BREAK: verify=>correct falsification requires a same-spec verifying impl whose faithful patch RUNS to completion and FAILS the hidden tests (completed && not resolved). atk_7's patch does not fail tests -- it fails to terminate, which the mechanized derivation (construct/build_one.py: BROKEN iff `r.completed and not r.resolved`) records as inconclusive, never as a break. A hanging patch is evidence of nontermination (permitted by partial-correctness by design), not evidence the spec admits an incorrect BEHAVIOR. Admitting it would falsely 'break' every velvet bundle. Precedent: neighboring django-11490's divergence/empty attack also returned completed=false and that bundle still PASSED G-EQ. atk_7 is therefore documented but EXCLUDED from the gate-counting attack list.

REFINEMENT.md AUDIT (step 3): NO A-legs -- confirmed no `axiom` and no `:|` stub in Solution.lean; G-AX genuinely VACUOUS. Every leg is R or I; NO kind-3 (no inexpressible changed op hand-waved). The only changed datum (allow_distinct=True) is modeled as concrete data (acceptsDistinct:=true, an I op) consumed by the deeply-modeled `construct`; the orthogonal super().__init__ is a legitimate R-identity (gold patch does not touch __init__). refinement.md legs 1-4 for avgInit/sumInit correspond faithfully to the gold hunks (add allow_distinct=True to Avg/Sum) routed through the unchanged Aggregate.__init__ guard. mapping.md bijections (bool<->Bool, function/distinct fields, TypeError<->Except.error) are correct.

FLOOR: 7 terminating attacks (>=5), prepatch reproduced (atk_1), positive control verifies (atk_pos). Gold resolves. -> clean SOUND pass. My verdict is advisory; the runner re-runs the 7 rejected attacks + positive control.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11603 velvet bundle.

Modeled functions:
  avgInit d = construct "AVG" true d
  sumInit d = construct "SUM" true d
  construct fn accepts d = if d && !accepts then Except.error .distinctNotAccepted else Except.ok {function:=fn, distinct:=d}
With accepts=true the error branch is dead: both methods always return Except.ok {fn, d}.

Real callee (from `git show f618e033:django/db/models/aggregates.py` + gold patch): Aggregate.__init__ has guard `if distinct and not self.allow_distinct: raise TypeError; self.distinct = distinct`. Base Aggregate.allow_distinct=False; Avg/Sum do NOT override it pre-patch (inherit False). Gold patch (verbatim in refinement.md/mapping.md) adds `allow_distinct = True` to Avg and Sum. So patched Avg/Sum have allow_distinct=True.

Input space is finite & total: {AVG,SUM} x {False,True}. Enumerated all 4:
  (AVG,F)->ok{AVG,F}; (AVG,T)->ok{AVG,T}; (SUM,F)->ok{SUM,F}; (SUM,T)->ok{SUM,T}. Patched real constructors produce identical observable (function name + bool(self.distinct)) on all 4 — success on every input, distinct recorded == request. No divergence.

The spec is NOT too strong: it pins `distinct := distinct` on success, which exactly matches `self.distinct = distinct` in the real guard (load-bearing for F2P test_distinct_on_aggregate). The error variant existing in the model is not spurious strength — it is simply never reachable for these two patched kinds (allow_distinct=True), matching reality. No orthogonal field (filter, source_expressions) is constrained by the spec, so no over-specification there.

Corroboration: same_spec across Solution.lean / Solution_prepatch.lean / Solution_prepatch_2.lean = True (spec region byte-identical); spec_view confirms frozen region. Lean verify Solution.lean exit 0. Recorded G-CONF: 100004 inputs, seed 11603, 0 disagreements — consistent with my independent full-cross-product enumeration. (Note: worktree currently has unresolved git merge-conflict markers in forms/models.py so I could not import the ORM live; I relied on the authoritative base-commit source via `git show` and reasoned the total finite input space by hand.)

Verdict: FAITHFUL — modeled functions agree with the real patched callee on every input in the total input domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: G-LEAK is a lexical screen over the SPEC VIEW (spec_signature over the axioms/pure/pre/post regions + method obligation headers; impl and prove_correct bodies elided). Verified byte-identity of the spec across all three files: same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True, so the frozen spec is stable and the prepatch variants differ only in the elided impl region.

Gold edit: add `allow_distinct = True` to the Avg and Sum classes in django/db/models/aggregates.py (patch.diff / dataset patch).

Public problem_statement already discloses essentially the whole edit in prose: 'Add DISTINCT support for Avg and Sum aggregates... This change would just involve setting these classes as allowing DISTINCT.' It names both target classes (Avg, Sum) and the desired capability (allow DISTINCT).

Spec view content: abstract carriers `AggState {function, distinct}`, `InitErr.distinctNotAccepted`, a deep guard `construct function acceptsDistinct distinct`, and the two method obligations `ensures out = construct "AVG" true distinct` / `construct "SUM" true distinct`. The only behavioural fact pinned beyond bare existence is that AVG/SUM accept distinct (capability arg = true) and record the flag — which is exactly the behaviour the public problem_statement already states. The spec view does NOT expose anything beyond problem_statement: no real attribute name `allow_distinct`, no file/line, no `Aggregate.__init__`, no `TypeError` string (only an abstract error variant), no gold-patch phrasing. The `function := "AVG"/"SUM"` strings are SQL function names inherent to naming the aggregates the problem statement already names, not the gold edit.

The concrete gold-edit specifics (`allow_distinct = True`, aggregates.py:22/99/142, the verbatim hunks, the TypeError guard) appear ONLY in refinement.md and mapping.md, which are NOT part of the spec view screened by G-LEAK. Conclusion: nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
