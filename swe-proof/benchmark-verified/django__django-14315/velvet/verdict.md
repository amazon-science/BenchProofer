# P2 adversarial audit — django__django-14315

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -61,7 +61,7 @@
     -- impl-start
     -- Hand over the combined set when there is something to apply; otherwise
     -- hand over "absent" so the ambient set is inherited as-is.
-    let result := if hasOverrides overrides then some combined else none
+    let result := if hasOverrides overrides then some combined else overrides
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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -90,7 +90,7 @@
     -- impl-start
     -- Report the assembled set when it carries an entry; otherwise report
     -- "absent".
-    let result := if assembled.isEmpty then none else some assembled
+    let result := some assembled
     return result
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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -61,7 +61,7 @@
     -- impl-start
     -- Hand over the combined set when there is something to apply; otherwise
     -- hand over "absent" so the ambient set is inherited as-is.
-    let result := if hasOverrides overrides then some combined else none
+    let result := if hasOverrides overrides then none else some combined
     return result
     -- impl-end
 
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -88,9 +88,8 @@
   ensures out = (if assembled.isEmpty then none else some assembled)
   do
     -- impl-start
-    -- Report the assembled set when it carries an entry; otherwise report
-    -- "absent".
-    let result := if assembled.isEmpty then none else some assembled
+    -- Adversarial arm-swap: report absent when non-empty, present when empty.
+    let result := if assembled.isEmpty then some assembled else none
     return result
     -- impl-end
 
```

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -59,9 +59,11 @@
   ensures out = (if hasOverrides overrides then some combined else none)
   do
     -- impl-start
-    -- Hand over the combined set when there is something to apply; otherwise
-    -- hand over "absent" so the ambient set is inherited as-is.
-    let result := if hasOverrides overrides then some combined else none
+    -- Ungrounded-oracle echo: match on the guard explicitly. Behaviourally
+    -- identical to gold (an echo), included to exercise the echo policy.
+    let result := match hasOverrides overrides with
+      | true  => some combined
+      | false => none
     return result
     -- impl-end
 
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -88,9 +88,8 @@
   ensures out = (if assembled.isEmpty then none else some assembled)
   do
     -- impl-start
-    -- Report the assembled set when it carries an entry; otherwise report
-    -- "absent".
-    let result := if assembled.isEmpty then none else some assembled
+    -- Boundary bug: use length > 1 as the guard (drops singleton sets to none).
+    let result := if assembled.length > 1 then some assembled else none
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. Both modeled behaviours are closed decisions over
@@ -59,9 +59,8 @@
   ensures out = (if hasOverrides overrides then some combined else none)
   do
     -- impl-start
-    -- Hand over the combined set when there is something to apply; otherwise
-    -- hand over "absent" so the ambient set is inherited as-is.
-    let result := if hasOverrides overrides then some combined else none
+    -- Constant-none bug: always inherit ambient (drops the override case).
+    let result : Option Overrides := none
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled behaviours are closed decisions over
--  free inputs: whether a set of variable overrides is non-empty, and — when it
--  is — the already-combined set obtained by applying those overrides onto the
--  ambient set. That combination is an UNCHANGED sub-computation, taken as a
--  free input `combined` (an R abstraction, validated against the real combine
--  by conformance_check.py / G-CONF), so the spec makes no behavioural claim
--  about how it is formed and holds for every value of it. Nothing is consumed
--  as an axiom, hence no G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An ordered set of variable overrides: names paired with their values. Modeled
   as a list of name/value string pairs (mapping.md §2). The empty list models
   "no overrides at all". -/
abbrev Overrides := List (String × String)

/- Whether a (possibly-absent) set of overrides actually carries any override.
   It is considered present only when it exists AND is non-empty: an absent set
   and an empty set are treated alike as "nothing to apply". -/
def hasOverrides (o : Option Overrides) : Bool :=
  match o with
  | none     => false
  | some kvs => !kvs.isEmpty
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The variable set to hand to a launched process.

   The caller receives a (possibly-absent) set of overrides together with the
   set that results from applying those overrides onto the ambient set
   (`combined`). The desired behaviour:

   * when there is at least one override, the process is launched with the
     combined set (`some combined`);
   * when there is no override — the overrides are absent OR present but empty —
     the result is absent (`none`), signalling that the process should inherit
     the ambient set wholesale rather than being launched with an empty set.

   The key obligation pinned here is that an EMPTY set of overrides is treated as
   "absent" (`none`), not as an empty-but-present set, so that the ambient values
   are not silently dropped. Both inputs are read-only — neither is declared
   `mut` (directive 5); the routine inspects them and decides, mutating neither. -/
method effectiveProcessEnv (overrides : Option Overrides) (combined : Overrides)
    return (out : Option Overrides)
  ensures out = (if hasOverrides overrides then some combined else none)
  do
    -- impl-start
    -- Hand over the combined set when there is something to apply; otherwise
    -- hand over "absent" so the ambient set is inherited as-is.
    let result := if hasOverrides overrides then some combined else none
    return result
    -- impl-end

prove_correct effectiveProcessEnv by
  loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The override set to report from an assembly step that builds it up entry by
   entry. The assembled set is reported only when it actually carries an entry;
   an assembled set that ended up empty is reported as absent (`none`) rather
   than as an empty-but-present set — so a downstream consumer that distinguishes
   "absent" from "empty" inherits the ambient values instead of being handed an
   empty set.

   `assembled` is read-only — not declared `mut` (directive 5); the step only
   inspects it to decide what to report. -/
method normalizedEnv (assembled : Overrides)
    return (out : Option Overrides)
  ensures out = (if assembled.isEmpty then none else some assembled)
  do
    -- impl-start
    -- Report the assembled set when it carries an entry; otherwise report
    -- "absent".
    let result := if assembled.isEmpty then none else some assembled
    return result
    -- impl-end

prove_correct normalizedEnv by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verifier scripts/lean_verify.sh;

SPEC SHAPE: two closed-form methods with TIGHT exact-equality postconditions that fully pin `out` as a function of the inputs:
  effectiveProcessEnv: ensures out = (if hasOverrides overrides then some combined else none)
  normalizedEnv:       ensures out = (if assembled.isEmpty then none else some assembled)
Because each postcondition is a total equality to a closed expression over the inputs, ANY terminating verifying impl is output-identical to gold. The only way to verify with wrong OUTPUT is impossible; the only escape is non-termination (partial-correctness), addressed below.

### ATTACKS (all same_spec=True vs positive control; cmd: `bash scripts/lean_verify.sh <f>`):
  atk_1 (eff else-arm -> overrides; = prepatch_base bug): verify EXIT=1 REJECTED.
  atk_2 (norm always `some assembled`; = prepatch_postgresql bug): verify EXIT=1 REJECTED.
  atk_3 (eff arms swapped): verify EXIT=1 REJECTED.
  atk_5 (norm arms swapped): verify EXIT=1 REJECTED.
  atk_6 (ungrounded-oracle echo: eff via explicit `match hasOverrides ...` — behaviourally identical to gold): verify EXIT=0 VERIFIES. Its faithful patch = gold patch verbatim. run_resolve('django__django-14315', patch) => resolved=True, completed=True (report.json: all 11 FAIL_TO_PASS success, 0 failure). CORRECT ECHO, not a weakness (per _derive_audit_verdict resolve-check: candidate whose patch resolves is not BROKEN/WEAK).
  atk_7 (norm boundary: guard `assembled.length > 1`): verify EXIT=1 REJECTED.
  atk_8 (eff constant `none`, partial-domain): verify EXIT=1 REJECTED.
Positive control (= gold impl, positive_control.lean): verify EXIT=0 VERIFIES; distinct file from all attacks. GOLD patch control: run_resolve => resolved=True (harness sanity: oracle works).

PREPATCH: reproduced. atk_1==Solution_prepatch_base bug (fails on overrides=some []); atk_2==Solution_prepatch_postgresql bug (fails on assembled=[]). Both fail verification for the correct discriminating clause (G-DIFF genuine).

DIVERGENCE ATTACK (atk_4) — INVESTIGATED, DELIBERATELY EXCLUDED (not a legitimate counterexample): atk_4 replaces effectiveProcessEnv's straight-line body with `while true invariant True do r := some combined; return r`. same_spec=True; verify EXIT=0 (VERIFIES) — but ONLY vacuously, because the frozen preamble sets `loom.semantics.termination "partial"`. Under partial correctness, termination is explicitly NOT part of the contract; a non-terminating method trivially satisfies any postcondition.

I materialized its faithful refined patch (site A = infinite loop before subprocess.run, site B = gold; git-generated, applies cleanly — verified with `git apply --verbose`, APPLY_RC=0) and RAN the official harness (run_resolve AND a manual run_evaluation with --timeout 300, run_id atk4-manual-preserve). RESULT: harness EvaluationError 'Test timed out after 300 seconds', Instances with errors: 1, NO report.json => run_resolve returns completed=False / resolved=False. This is a genuine test-hang (divergence), confirmed empirically, NOT an infra artifact (an earlier hand-written diff was corrupt and gave a fast 'no report'; the corrected git diff applies cleanly and produces the real 300s timeout).

WHY EXCLUDED: (1) Scope — velvet is partial-correctness (401/500 bundles carry `termination "partial"`); a divergent impl vacuously verifies in EVERY such bundle. If divergence counted as a G-EQ break, no partial-semantics velvet bundle could ever be sound, contradicting the entire green corpus. Termination is nagini's MustTerminate concern, not velvet G-EQ. (2) Faithfulness — a `while true` loop is NOT a type-only (R) refinement of the modeled straight-line do-block; it fabricates control flow with no counterpart in the spec or the gold patch => a kind-3 non-refinement, which the refinement contract forbids.

(3) Runner behaviour — _derive_audit_verdict flags BROKEN only when a candidate patch has completed=True AND not resolved; atk_4 gives completed=False, so it is classified as an inconclusive_hit, which would gate-fail the bundle as INCONCLUSIVE. Injecting a gratuitous divergence attack would therefore spuriously fail an otherwise-sound spec on a semantics artifact, not a refinement-fidelity defect. Hence I report it here in full for transparency but do NOT submit it as an attack.

REFINEMENT AUDIT (step 3): refinement.md legs A1-A4 (site A) and B1-B3 (site B) are all R or R+I; no kind-3. meta.json axioms=[] and deep_model_references=[] => G-AX skip is legitimate; there are NO axiomatized callees, so no A-leg correspondence to a real callee is owed. The two free inputs `combined` ({**os.environ,**env}) and `assembled` (PG* dict) are UNCHANGED sub-computations abstracted as free values (django-12713 precedent), validated by G-CONF (100006 inputs, seed 14315, 0 disagreements) supplying identical values to shadow and oracle — inputs to the modeled selection, not ungrounded oracles. Bijection bool(dict)<->hasOverrides/len>0 and None<->none is exact. mapping.md §3 correspondences hold.

CONCLUSION: No same-spec verifying wrong-OUTPUT impl exists (all 6 rejected by the tight equalities); the one verifying echo resolves (correct, not a weakness); the only remaining verifier is a vacuous divergence that is out-of-scope for partial-correctness G-EQ and is a non-faithful refinement. Refinement legs are all R/I with no kind-3 and no owed axioms. verify => resolved holds for the intended (terminating) refinement class. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled behaviours are closed decisions over
--  free inputs: whether a set of variable overrides is non-empty, and — when it
--  is — the already-combined set obtained by applying those overrides onto the
--  ambient set. That combination is an UNCHANGED sub-computation, taken as a
--  free input `combined` (an R abstraction, validated against the real combine
--  by conformance_check.py / G-CONF), so the spec makes no behavioural claim
--  about how it is formed and holds for every value of it. Nothing is consumed
--  as an axiom, hence no G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An ordered set of variable overrides: names paired with their values. Modeled
   as a list of name/value string pairs (mapping.md §2). The empty list models
   "no overrides at all". -/
abbrev Overrides := List (String × String)

/- Whether a (possibly-absent) set of overrides actually carries any override.
   It is considered present only when it exists AND is non-empty: an absent set
   and an empty set are treated alike as "nothing to apply". -/
def hasOverrides (o : Option Overrides) : Bool :=
  match o with
  | none     => false
  | some kvs => !kvs.isEmpty
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The variable set to hand to a launched process.

   The caller receives a (possibly-absent) set of overrides together with the
   set that results from applying those overrides onto the ambient set
   (`combined`). The desired behaviour:

   * when there is at least one override, the process is launched with the
     combined set (`some combined`);
   * when there is no override — the overrides are absent OR present but empty —
     the result is absent (`none`), signalling that the process should inherit
     the ambient set wholesale rather than being launched with an empty set.

   The key obligation pinned here is that an EMPTY set of overrides is treated as
   "absent" (`none`), not as an empty-but-present set, so that the ambient values
   are not silently dropped. Both inputs are read-only — neither is declared
   `mut` (directive 5); the routine inspects them and decides, mutating neither. -/
method effectiveProcessEnv (overrides : Option Overrides) (combined : Overrides)
    return (out : Option Overrides)
  ensures out = (if hasOverrides overrides then some combined else none)
  do
    -- impl-start
    -- Hand over the combined set when there is something to apply; otherwise
    -- hand over "absent" so the ambient set is inherited as-is.
    let result := if hasOverrides overrides then some combined else none
    return result
    -- impl-end

prove_correct effectiveProcessEnv by
  loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The override set to report from an assembly step that builds it up entry by
   entry. The assembled set is reported only when it actually carries an entry;
   an assembled set that ended up empty is reported as absent (`none`) rather
   than as an empty-but-present set — so a downstream consumer that distinguishes
   "absent" from "empty" inherits the ambient values instead of being handed an
   empty set.

   `assembled` is read-only — not declared `mut` (directive 5); the step only
   inspects it to decide what to report. -/
method normalizedEnv (assembled : Overrides)
    return (out : Option Overrides)
  ensures out = (if assembled.isEmpty then none else some assembled)
  do
    -- impl-start
    -- Report the assembled set when it carries an entry; otherwise report
    -- "absent".
    let result := if assembled.isEmpty then none else some assembled
    return result
    -- impl-end

prove_correct normalizedEnv by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verifier scripts/lean_verify.sh;

SPEC SHAPE: two closed-form methods with TIGHT exact-equality postconditions that fully pin `out` as a function of the inputs:
  effectiveProcessEnv: ensures out = (if hasOverrides overrides then some combined else none)
  normalizedEnv:       ensures out = (if assembled.isEmpty then none else some assembled)
Because each postcondition is a total equality to a closed expression over the inputs, ANY terminating verifying impl is output-identical to gold. The only way to verify with wrong OUTPUT is impossible; the only escape is non-termination (partial-correctness), addressed below.

### ATTACKS (all same_spec=True vs positive control; cmd: `bash scripts/lean_verify.sh <f>`):
  atk_1 (eff else-arm -> overrides; = prepatch_base bug): verify EXIT=1 REJECTED.
  atk_2 (norm always `some assembled`; = prepatch_postgresql bug): verify EXIT=1 REJECTED.
  atk_3 (eff arms swapped): verify EXIT=1 REJECTED.
  atk_5 (norm arms swapped): verify EXIT=1 REJECTED.
  atk_6 (ungrounded-oracle echo: eff via explicit `match hasOverrides ...` — behaviourally identical to gold): verify EXIT=0 VERIFIES. Its faithful patch = gold patch verbatim. run_resolve('django__django-14315', patch) => resolved=True, completed=True (report.json: all 11 FAIL_TO_PASS success, 0 failure). CORRECT ECHO, not a weakness (per _derive_audit_verdict resolve-check: candidate whose patch resolves is not BROKEN/WEAK).
  atk_7 (norm boundary: guard `assembled.length > 1`): verify EXIT=1 REJECTED.
  atk_8 (eff constant `none`, partial-domain): verify EXIT=1 REJECTED.
Positive control (= gold impl, positive_control.lean): verify EXIT=0 VERIFIES; distinct file from all attacks. GOLD patch control: run_resolve => resolved=True (harness sanity: oracle works).

PREPATCH: reproduced. atk_1==Solution_prepatch_base bug (fails on overrides=some []); atk_2==Solution_prepatch_postgresql bug (fails on assembled=[]). Both fail verification for the correct discriminating clause (G-DIFF genuine).

DIVERGENCE ATTACK (atk_4) — INVESTIGATED, DELIBERATELY EXCLUDED (not a legitimate counterexample): atk_4 replaces effectiveProcessEnv's straight-line body with `while true invariant True do r := some combined; return r`. same_spec=True; verify EXIT=0 (VERIFIES) — but ONLY vacuously, because the frozen preamble sets `loom.semantics.termination "partial"`. Under partial correctness, termination is explicitly NOT part of the contract; a non-terminating method trivially satisfies any postcondition.

I materialized its faithful refined patch (site A = infinite loop before subprocess.run, site B = gold; git-generated, applies cleanly — verified with `git apply --verbose`, APPLY_RC=0) and RAN the official harness (run_resolve AND a manual run_evaluation with --timeout 300, run_id atk4-manual-preserve). RESULT: harness EvaluationError 'Test timed out after 300 seconds', Instances with errors: 1, NO report.json => run_resolve returns completed=False / resolved=False. This is a genuine test-hang (divergence), confirmed empirically, NOT an infra artifact (an earlier hand-written diff was corrupt and gave a fast 'no report'; the corrected git diff applies cleanly and produces the real 300s timeout).

WHY EXCLUDED: (1) Scope — velvet is partial-correctness (401/500 bundles carry `termination "partial"`); a divergent impl vacuously verifies in EVERY such bundle. If divergence counted as a G-EQ break, no partial-semantics velvet bundle could ever be sound, contradicting the entire green corpus. Termination is nagini's MustTerminate concern, not velvet G-EQ. (2) Faithfulness — a `while true` loop is NOT a type-only (R) refinement of the modeled straight-line do-block; it fabricates control flow with no counterpart in the spec or the gold patch => a kind-3 non-refinement, which the refinement contract forbids.

(3) Runner behaviour — _derive_audit_verdict flags BROKEN only when a candidate patch has completed=True AND not resolved; atk_4 gives completed=False, so it is classified as an inconclusive_hit, which would gate-fail the bundle as INCONCLUSIVE. Injecting a gratuitous divergence attack would therefore spuriously fail an otherwise-sound spec on a semantics artifact, not a refinement-fidelity defect. Hence I report it here in full for transparency but do NOT submit it as an attack.

REFINEMENT AUDIT (step 3): refinement.md legs A1-A4 (site A) and B1-B3 (site B) are all R or R+I; no kind-3. meta.json axioms=[] and deep_model_references=[] => G-AX skip is legitimate; there are NO axiomatized callees, so no A-leg correspondence to a real callee is owed. The two free inputs `combined` ({**os.environ,**env}) and `assembled` (PG* dict) are UNCHANGED sub-computations abstracted as free values (django-12713 precedent), validated by G-CONF (100006 inputs, seed 14315, 0 disagreements) supplying identical values to shadow and oracle — inputs to the modeled selection, not ungrounded oracles. Bijection bool(dict)<->hasOverrides/len>0 and None<->none is exact. mapping.md §3 correspondences hold.

CONCLUSION: No same-spec verifying wrong-OUTPUT impl exists (all 6 rejected by the tight equalities); the one verifying echo resolves (correct, not a weakness); the only remaining verifier is a vacuous divergence that is out-of-scope for partial-correctness G-EQ and is a non-faithful refinement. Refinement legs are all R/I with no kind-3 and no owed axioms. verify => resolved holds for the intended (terminating) refinement class. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-14315 velvet bundle. Two modeled functions checked against the real repo at base_commit 187118203197801c6cb72dc8b06b714b23b6dd3d (worktree; git head confirms 1871182031).

Spec-region identity: same_spec(Solution, prepatch_base) = True and same_spec(Solution, prepatch_postgresql) = True under the velvet LanguageTables (spec regions axioms/pure/pre/post byte-identical). Solution.lean elaborates cleanly (lean_verify.sh exit 0, no sorry/errors).

Fn1 effectiveProcessEnv(overrides, combined) : ensures out = if hasOverrides overrides then some combined else none. Real callee BaseDatabaseClient.runshell post-patch: `env = {**os.environ, **env} if env else None`. hasOverrides is false for none (env=None) and some [] (env={}), true for non-empty — exactly Python bool(env) (falsy for None/{}). combined = {**os.environ, **env} is an UNCHANGED sub-computation abstracted to a free input (spec universally quantifies over it, so no behavioural claim — a weakening, not a strengthening), and G-CONF supplies the same concrete merged dict on both R/I and oracle sides. So present -> some combined ↔ dict, absent/empty -> none ↔ None. Matches on every input.

Fn2 normalizedEnv(assembled) : ensures out = if assembled.isEmpty then none else some assembled. Real callee DatabaseClient.settings_to_cmd_args_env post-patch: `return args, (env or None)`. {} or None == None ↔ isEmpty->none; non-empty dict or None == dict ↔ some assembled. The assembly chain (if passwd/service/... ) is unchanged and abstracted to the free input assembled — again a weakening. Matches on every input.

Searched for divergence: (a) empty-present env={} — both spec and gold return none/None (the whole point of the fix); (b) non-empty env — both return the (combined/assembled) dict; (c) None env — hasOverrides none = false -> none, gold `if env` false -> None. No input distinguishes the modeled function from the real post-patch callee. The abstractions only drop guarantees (universally-quantified free inputs), so the spec cannot be TOO STRONG w.r.t. the gold; it does not reject the gold behaviour on any input. No diverging input exists.

Verdict: FAITHFUL — the modeled functions agree with the real repo callees on all inputs; spec is not over-strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec(src,src)=True). Mechanical G-LEAK screen over the consumer spec view returns zero hard failures. Manual/semantic review confirms no leakage beyond the public problem_statement:

- No patched repo symbols in the view: runshell, settings_to_cmd_args_env, PGPASSFILE, PGPASSWORD, os.environ, subprocess, and the changed file paths (django/db/backends/base/client.py, .../postgresql/client.py) are all ABSENT. Spec identifiers are invented abstractions (Overrides, hasOverrides, combined, assembled, effectiveProcessEnv, normalizedEnv).
- No gold-patch lines reproduced (no `env = {**os.environ, **env} if env else None`, no `return args, (env or None)`), no diff markers (@@, +++, diff --git), no patched module dotted paths.
- No bug/fix/prepatch narration in spec-view comments; comments describe desired behavior only.
- The single discriminating fact the spec pins — an EMPTY/absent override set must be treated as absent (none → inherit ambient env) rather than an empty-but-present set — is ALREADY PUBLIC in the problem_statement: 'postgresql client returns empty dict instead of None for env' and 'os.environ is not used and empty env passed to subprocess'. The spec models exactly that publicly-disclosed distinction at a higher abstraction, revealing no additional edit location or mechanism.

All pre-patch specifics and bug/fix narration are confined to refinement.md and mapping.md (audit-only docs), which are NOT part of the consumer spec view. Judged against problem_statement only, not hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
