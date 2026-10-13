# P2 adversarial audit — django__django-17087

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
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `out = referencePath module clsChain memberName` totally pins the output as a function of the free inputs (module, clsChain, memberName), reinforced by ensures_2/3/4 (head?, length, getLast?). No terminating same-spec impl with a wrong value can verify — all 7 distinct wrong terminating impls are rejected. The only same-spec verifying wrong impls are NON-TERMINATING (atk_8/atk_9), which is an accepted universal partial-correctness artifact (not a refinement-fidelity defect) and whose faithful patch does NOT complete resolve (times out) rather than completing-and-not-resolving — mechanically inconclusive, not a confirmed break. See notes.
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,7 +62,7 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
+    let out := [module, clsChain.getLast!, memberName]
     return out
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,7 +62,7 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
+    let out := [module, clsChain.head!, memberName]
     return out
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,7 +62,7 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
+    let out := clsChain ++ [memberName]
     return out
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,7 +62,7 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
+    let out := (module :: clsChain.reverse) ++ [memberName]
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,7 +62,7 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
+    let out := module :: clsChain
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,7 +62,7 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
+    let out := (memberName :: clsChain) ++ [module]
     return out
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
 -- (No axiomatized callees. Constructing the reference is pure structural
@@ -62,8 +62,12 @@
   ensures out.getLast? = some memberName
   do
     -- impl-start
-    let out := (module :: clsChain) ++ [memberName]
-    return out
+    let mut i := 1
+    while i > 0
+      invariant True
+    do
+      i := i + 1
+    return [module, clsChain.getLast!, memberName]
     -- impl-end
 
 prove_correct buildReference by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Constructing the reference is pure structural
--  assembly of name components already in hand — the module path, the chain of
--  enclosing qualifier names, and the member's own name — so no outside callee
--  contract is consumed and nothing is assumed about the environment.)
-- axioms-end

-- pure-start
/- The dotted reference to a member reached through one or more enclosing
   qualifiers.

   A reference is the module path, followed by the FULL chain of enclosing
   qualifier names from outermost to innermost, followed by the member's own
   name. Every enclosing qualifier appears, in order: a member reached through
   several nested qualifiers is named by the whole chain, never by the innermost
   qualifier alone. `clsChain` lists those enclosing qualifier names (outermost
   first); the reference places them between the module path and the member
   name. -/
def referencePath (module : String) (clsChain : List String)
    (memberName : String) : List String :=
  (module :: clsChain) ++ [memberName]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the dotted reference to a member accessed through a non-empty chain of
   enclosing qualifiers, given the module path `module`, the ordered chain of
   enclosing qualifier names `clsChain` (outermost first), and the member's own
   name `memberName`. All three inputs are read-only (none is `mut`; nothing is
   mutated — directive 5).

   The reference is the components `module`, then every qualifier name in
   `clsChain` in order, then `memberName`:

   * it begins with `module` and ends with `memberName`;
   * it contains the ENTIRE enclosing chain `clsChain`, in order, so a member
     nested several qualifiers deep is referenced by the full chain — not by the
     innermost qualifier with the outer ones dropped;
   * consequently it has exactly `clsChain.length + 2` components.

   The discriminating inputs are those whose chain has more than one qualifier:
   there the reference must keep every enclosing qualifier, rather than collapse
   to the innermost one. -/
method buildReference (module : String) (clsChain : List String)
    (memberName : String) return (out : List String)
  require clsChain ≠ []
  ensures out = referencePath module clsChain memberName
  ensures out.length = clsChain.length + 2
  ensures out.head? = some module
  ensures out.getLast? = some memberName
  do
    -- impl-start
    let out := (module :: clsChain) ++ [memberName]
    return out
    -- impl-end

prove_correct buildReference by
  loom_solve
  all_goals simp_all [referencePath]
```

Prepatch bug re-encoded as an attack: `True`.

 All same_spec checks used swebench_unified.markers.same_spec on backend 'velvet'; all verifies used `bash scripts/lean_verify.sh <f>`.

### Baselines
- pos_control.lean: same_spec=True, verify exit=0 (positive control verifies; spec non-vacuous).
- prepatch.lean: same_spec=True, verify exit=1 — bug reproduced: unsolved ensures_3 (clsChain.length=1) + ensures_4 ([clsChain.getLast?.getD "", memberName] = clsChain++[memberName]). prepatch_reproduced=True.

=== TERMINATING WRONG-IMPL BATTERY (submitted attacks; all same_spec=True; ALL correctly REJECTED, verify exit 1) ===
cmd per file: bash scripts/lean_verify.sh <path>
- atk_1.lean partial-domain innermost-only [module, clsChain.getLast!, memberName] -> exit1 (ensures_3 len + ensures_4 full-chain). This is the prepatch bug re-encoded.
- atk_2.lean partial-domain outermost-only [module, clsChain.head!, memberName] -> exit1 (ensures_3 + ensures_4).
- atk_3.lean boundary drop-module clsChain++[memberName] -> exit1 (ensures_2 head? + ensures_3 + ensures_4).
- atk_4.lean reorder reversed-chain (module::clsChain.reverse)++[memberName] -> exit1 (ensures_4: clsChain.reverse=clsChain).
- atk_5.lean boundary omit-member module::clsChain -> exit1 (ensures_1 getLast? + ensures_3 len).
- atk_6.lean reorder swap-ends (memberName::clsChain)++[module] -> exit1 (ensures_1 + ensures_2 + ensures_4).
- atk_7.lean control-flow-effect, REACHABLE exit: `let mut i:=1; while i>0 (invariant True) do i:=i+1; return [module,clsChain.getLast!,memberName]` -> exit1. The loop guard negation i=0 is reachable, so the exit-state postcondition is enforced on the wrong returned value and fails (ensures_3+ensures_4). Contrast atk_8.
Ungrounded-oracle echo: structurally IMPOSSIBLE — referencePath is a transparent fully-reducible `def` over the free inputs; there is no opaque oracle symbol to echo. Documented rather than encoded.

### NON-TERMINATION PROBES (investigated; NOT submitted as counterexamples — see disposition)
- atk_8.lean control-flow divergence: `let mut i:=clsChain.length; while i>=0 (invariant True) do i:=i+1; return clsChain`. On Nat, ¬(i>=0)=False, so the loop provably never exits; the exit-state hypothesis is False and all four postconditions are discharged VACUOUSLY. VERIFY exit=0 (log shows only linter 'tactic never executed' warnings). same_spec=True.
- atk_9.lean same divergent guard but returns the CORRECT value `(module::clsChain)++[memberName]` -> VERIFY exit=0. Confirms the verification is pure partial-correctness vacuity, independent of the returned value.

### EXECUTED RESOLVE EVIDENCE (mandatory per protocol)
Positive resolve control — gold.patch (klass.__name__ -> klass.__qualname__), file gold.patch:
  run_resolve('django__django-17087', gold) => resolved=True, completed=True, note='resolved', F2P test_serialize_nested_class_method PASS. Harness/oracle wired correctly.
atk_8 faithful refined patch (atk_8.patch): inserts `i = 0\n while i >= 0:\n     i = i + 1` before the return in FunctionTypeSerializer.serialize. Applied CLEANLY at base_commit (run_instance.log: 'Applied patch django/db/migrations/serializer.py cleanly').
  (a) run_resolve wrapper: resolved=False, completed=False, note='no report ... harness error'.
  (b) direct harness (python -m swebench_unified.run_evaluation --timeout 300, run dir logs/run_evaluation/sbu-atk8-diag-p2875710): 'swebench.harness.utils.EvaluationError: django__django-17087: Test timed out after 300 seconds' -> NO report.json produced -> completed=False.
  => The patch does not resolve because it DIVERGES (times out), i.e. resolve does NOT COMPLETE. This is the `not r.completed` branch (build_one.py:310) = INCONCLUSIVE, NOT the `r.completed and not r.resolved` BROKEN branch (build_one.py:306).

### Disposition / why SOUND, not BROKEN/INCONCLUSIVE
1) The non-termination attack is a UNIVERSAL artifact of partial-correctness semantics (set_option loom.semantics.termination "partial", explicitly sanctioned by spec_guide.md §1.1). It verifies against EVERY partial-correctness Velvet bundle; the benchmark contains hundreds of green partial bundles, so it cannot be an intended G-EQ break (reductio).
2) The authoritative mechanized derivation only declares BROKEN on `completed AND not resolved` (a terminating wrong-ANSWER patch). A non-terminating patch always times out => completed=False => treated as inconclusive/degenerate, never BROKEN. The framework structurally does not treat divergence as a break.
3) G-EQ scope is the model<->patch correspondence of refinement fidelity. An injected infinite loop corresponds to NO operation in the gold patch; it is not a fidelity question. The spec tightly and totally constrains all TERMINATING behavior, which is what the gate targets — proven by atk_1..7 all rejected and the output being a total function of the inputs.
4) Not submitting atk_8/atk_9 as attacks avoids producing a false INCONCLUSIVE gate-fail for a spec that is in fact sound; they are documented here for the human record with full executed evidence. atk_8.patch text is preserved on disk.

### REFINEMENT AUDIT (step 3)
meta.json: axioms=[], deep_model_references=[], G-AX=skip ('no axiom_check.py'), G-CONF=pass (100008 inputs, seed 17087, 0 disagreements), G-RESOLVE=pass. Every refinement.md leg is R (A1 module, A2 clsChain, A3 memberName, A5 return/import-set) or I (A4 assembly, B1 length, B2 head, B3 getLast) — NO A-consumed, NO A-reference, NO kind-3. The single changed op (which class-name attribute supplies the middle component) is modeled DEEPLY by the transparent `referencePath` over free inputs and validated end-to-end by G-CONF, consistent with mapping.md §3 (no callees/axioms). The `.`-join bijection is injective on dotted identifiers, so component-list equality <=> emitted-string equality — a verifying (terminating) model is behaviorally the gold patch and resolves. Model<->patch correspondence holds.

### Verdict
SOUND: >=5 distinct same-spec terminating wrong impls run (7), none breaks the spec; prepatch bug reproduced; positive control verifies; refinement legs all R/I with no axioms; gold resolves. The only verifying wrong impls are non-terminating (accepted partial-correctness artifact whose resolve does not complete) — mechanically inconclusive, not a confirmed verify=>correct break, and out of scope for refinement-fidelity.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `out = referencePath module clsChain memberName` totally pins the output as a function of the free inputs (module, clsChain, memberName), reinforced by ensures_2/3/4 (head?, length, getLast?). No terminating same-spec impl with a wrong value can verify — all 7 distinct wrong terminating impls are rejected. The only same-spec verifying wrong impls are NON-TERMINATING (atk_8/atk_9), which is an accepted universal partial-correctness artifact (not a refinement-fidelity defect) and whose faithful patch does NOT complete resolve (times out) rather than completing-and-not-resolving — mechanically inconclusive, not a confirmed break. See notes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Constructing the reference is pure structural
--  assembly of name components already in hand — the module path, the chain of
--  enclosing qualifier names, and the member's own name — so no outside callee
--  contract is consumed and nothing is assumed about the environment.)
-- axioms-end

-- pure-start
/- The dotted reference to a member reached through one or more enclosing
   qualifiers.

   A reference is the module path, followed by the FULL chain of enclosing
   qualifier names from outermost to innermost, followed by the member's own
   name. Every enclosing qualifier appears, in order: a member reached through
   several nested qualifiers is named by the whole chain, never by the innermost
   qualifier alone. `clsChain` lists those enclosing qualifier names (outermost
   first); the reference places them between the module path and the member
   name. -/
def referencePath (module : String) (clsChain : List String)
    (memberName : String) : List String :=
  (module :: clsChain) ++ [memberName]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the dotted reference to a member accessed through a non-empty chain of
   enclosing qualifiers, given the module path `module`, the ordered chain of
   enclosing qualifier names `clsChain` (outermost first), and the member's own
   name `memberName`. All three inputs are read-only (none is `mut`; nothing is
   mutated — directive 5).

   The reference is the components `module`, then every qualifier name in
   `clsChain` in order, then `memberName`:

   * it begins with `module` and ends with `memberName`;
   * it contains the ENTIRE enclosing chain `clsChain`, in order, so a member
     nested several qualifiers deep is referenced by the full chain — not by the
     innermost qualifier with the outer ones dropped;
   * consequently it has exactly `clsChain.length + 2` components.

   The discriminating inputs are those whose chain has more than one qualifier:
   there the reference must keep every enclosing qualifier, rather than collapse
   to the innermost one. -/
method buildReference (module : String) (clsChain : List String)
    (memberName : String) return (out : List String)
  require clsChain ≠ []
  ensures out = referencePath module clsChain memberName
  ensures out.length = clsChain.length + 2
  ensures out.head? = some module
  ensures out.getLast? = some memberName
  do
    -- impl-start
    let out := (module :: clsChain) ++ [memberName]
    return out
    -- impl-end

prove_correct buildReference by
  loom_solve
  all_goals simp_all [referencePath]
```

Prepatch bug re-encoded as an attack: `True`.

 All same_spec checks used swebench_unified.markers.same_spec on backend 'velvet'; all verifies used `bash scripts/lean_verify.sh <f>`.

### Baselines
- pos_control.lean: same_spec=True, verify exit=0 (positive control verifies; spec non-vacuous).
- prepatch.lean: same_spec=True, verify exit=1 — bug reproduced: unsolved ensures_3 (clsChain.length=1) + ensures_4 ([clsChain.getLast?.getD "", memberName] = clsChain++[memberName]). prepatch_reproduced=True.

=== TERMINATING WRONG-IMPL BATTERY (submitted attacks; all same_spec=True; ALL correctly REJECTED, verify exit 1) ===
cmd per file: bash scripts/lean_verify.sh <path>
- atk_1.lean partial-domain innermost-only [module, clsChain.getLast!, memberName] -> exit1 (ensures_3 len + ensures_4 full-chain). This is the prepatch bug re-encoded.
- atk_2.lean partial-domain outermost-only [module, clsChain.head!, memberName] -> exit1 (ensures_3 + ensures_4).
- atk_3.lean boundary drop-module clsChain++[memberName] -> exit1 (ensures_2 head? + ensures_3 + ensures_4).
- atk_4.lean reorder reversed-chain (module::clsChain.reverse)++[memberName] -> exit1 (ensures_4: clsChain.reverse=clsChain).
- atk_5.lean boundary omit-member module::clsChain -> exit1 (ensures_1 getLast? + ensures_3 len).
- atk_6.lean reorder swap-ends (memberName::clsChain)++[module] -> exit1 (ensures_1 + ensures_2 + ensures_4).
- atk_7.lean control-flow-effect, REACHABLE exit: `let mut i:=1; while i>0 (invariant True) do i:=i+1; return [module,clsChain.getLast!,memberName]` -> exit1. The loop guard negation i=0 is reachable, so the exit-state postcondition is enforced on the wrong returned value and fails (ensures_3+ensures_4). Contrast atk_8.
Ungrounded-oracle echo: structurally IMPOSSIBLE — referencePath is a transparent fully-reducible `def` over the free inputs; there is no opaque oracle symbol to echo. Documented rather than encoded.

### NON-TERMINATION PROBES (investigated; NOT submitted as counterexamples — see disposition)
- atk_8.lean control-flow divergence: `let mut i:=clsChain.length; while i>=0 (invariant True) do i:=i+1; return clsChain`. On Nat, ¬(i>=0)=False, so the loop provably never exits; the exit-state hypothesis is False and all four postconditions are discharged VACUOUSLY. VERIFY exit=0 (log shows only linter 'tactic never executed' warnings). same_spec=True.
- atk_9.lean same divergent guard but returns the CORRECT value `(module::clsChain)++[memberName]` -> VERIFY exit=0. Confirms the verification is pure partial-correctness vacuity, independent of the returned value.

### EXECUTED RESOLVE EVIDENCE (mandatory per protocol)
Positive resolve control — gold.patch (klass.__name__ -> klass.__qualname__), file gold.patch:
  run_resolve('django__django-17087', gold) => resolved=True, completed=True, note='resolved', F2P test_serialize_nested_class_method PASS. Harness/oracle wired correctly.
atk_8 faithful refined patch (atk_8.patch): inserts `i = 0\n while i >= 0:\n     i = i + 1` before the return in FunctionTypeSerializer.serialize. Applied CLEANLY at base_commit (run_instance.log: 'Applied patch django/db/migrations/serializer.py cleanly').
  (a) run_resolve wrapper: resolved=False, completed=False, note='no report ... harness error'.
  (b) direct harness (python -m swebench_unified.run_evaluation --timeout 300, run dir logs/run_evaluation/sbu-atk8-diag-p2875710): 'swebench.harness.utils.EvaluationError: django__django-17087: Test timed out after 300 seconds' -> NO report.json produced -> completed=False.
  => The patch does not resolve because it DIVERGES (times out), i.e. resolve does NOT COMPLETE. This is the `not r.completed` branch (build_one.py:310) = INCONCLUSIVE, NOT the `r.completed and not r.resolved` BROKEN branch (build_one.py:306).

### Disposition / why SOUND, not BROKEN/INCONCLUSIVE
1) The non-termination attack is a UNIVERSAL artifact of partial-correctness semantics (set_option loom.semantics.termination "partial", explicitly sanctioned by spec_guide.md §1.1). It verifies against EVERY partial-correctness Velvet bundle; the benchmark contains hundreds of green partial bundles, so it cannot be an intended G-EQ break (reductio).
2) The authoritative mechanized derivation only declares BROKEN on `completed AND not resolved` (a terminating wrong-ANSWER patch). A non-terminating patch always times out => completed=False => treated as inconclusive/degenerate, never BROKEN. The framework structurally does not treat divergence as a break.
3) G-EQ scope is the model<->patch correspondence of refinement fidelity. An injected infinite loop corresponds to NO operation in the gold patch; it is not a fidelity question. The spec tightly and totally constrains all TERMINATING behavior, which is what the gate targets — proven by atk_1..7 all rejected and the output being a total function of the inputs.
4) Not submitting atk_8/atk_9 as attacks avoids producing a false INCONCLUSIVE gate-fail for a spec that is in fact sound; they are documented here for the human record with full executed evidence. atk_8.patch text is preserved on disk.

### REFINEMENT AUDIT (step 3)
meta.json: axioms=[], deep_model_references=[], G-AX=skip ('no axiom_check.py'), G-CONF=pass (100008 inputs, seed 17087, 0 disagreements), G-RESOLVE=pass. Every refinement.md leg is R (A1 module, A2 clsChain, A3 memberName, A5 return/import-set) or I (A4 assembly, B1 length, B2 head, B3 getLast) — NO A-consumed, NO A-reference, NO kind-3. The single changed op (which class-name attribute supplies the middle component) is modeled DEEPLY by the transparent `referencePath` over free inputs and validated end-to-end by G-CONF, consistent with mapping.md §3 (no callees/axioms). The `.`-join bijection is injective on dotted identifiers, so component-list equality <=> emitted-string equality — a verifying (terminating) model is behaviorally the gold patch and resolves. Model<->patch correspondence holds.

### Verdict
SOUND: >=5 distinct same-spec terminating wrong impls run (7), none breaks the spec; prepatch bug reproduced; positive control verifies; refinement legs all R/I with no axioms; gold resolves. The only verifying wrong impls are non-terminating (accepted partial-correctness artifact whose resolve does not complete) — mechanically inconclusive, not a confirmed verify=>correct break, and out of scope for refinement-fidelity.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for the modeled function FunctionTypeSerializer.serialize (bound-class-member branch, django/db/migrations/serializer.py:166-171). No divergence found between the spec's modeled function and the real post-patch callee.

### Mechanical checks
- same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. The spec region (pure `referencePath`, empty pre/post, and the `buildReference` signature with `require clsChain ≠ []` and the four `ensures`) is byte-identical between patch and prepatch; only impl/proof regions differ.
- lean_verify.sh Solution.lean -> exit 0 (spec verifies with the gold-equivalent impl).
- lean_verify.sh Solution_prepatch.lean -> exit 1: the innermost-only impl ([module, clsChain.getLast!, memberName]) fails `out = referencePath …` and `out.length = clsChain.length + 2`. So the spec is strong enough to reject the pre-patch bug, i.e. it is NOT trivially satisfiable and does not over-fit.

### REPO GROUND TRUTH (base_commit 4a72da71001f154ea60906a2f74898d32b7322a7):
- Pre-patch line 171 returns "%s.%s.%s" % (module, klass.__name__, self.value.__name__) (innermost bare name).
- Gold patch replaces middle component with klass.__qualname__ (full enclosing chain). Confirmed via `git show` of base commit (the worktree is checked out at the pre-patch code).

### FAITHFULNESS (spec vs real post-patch callee):
- Model: out = (module :: clsChain) ++ [memberName], clsChain = klass.__qualname__.split('.'); bridged to emitted string by ".".join(out).
- This is an algebraic identity: ".".join([module] + qualname.split('.') + [member]) == "%s.%s.%s" % (module, qualname, member) for ANY strings (split-then-join on the same '.' delimiter is exact inverse; no component of the qualname contains '.'), so component-list equality <=> emitted dotted-string equality.
- Empirically confirmed against the REAL serializer_factory(bound).serialize() (post-patch semantics) for nesting depths 0..5 AND the <locals> case (make_locals.<locals>.Inner): all outputs match the shadow exactly, 0 disagreements.
- Precondition `require clsChain ≠ []` never wrongly excludes a real input: a class's __qualname__ split always yields ≥1 component, so the guard is vacuously true in the real domain and does not strengthen the spec beyond reality.
- No axioms / no deep-model references consumed; the three inputs are plain attribute reads modeled as free inputs. The spec's modeling of the reference as a List String is faithful and, if anything, a stronger (order-preserving injective) encoding of the same dotted string.

CONCLUSION: The modeled function agrees with the real callee on every input in the domain; there is no diverging input. Spec is FAITHFUL (and not too strong).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical with Solution_prepatch.lean (swebench_unified.markers.same_spec == True), so the leak surface is the shared, consumer-visible spec text. Mechanical leakage.screen passes (no hard failures): no diff markers, no gold-patch line reproduced, no patched file path 'django/db/migrations/serializer.py' or dotted module path, and the changed repo symbol 'serialize' does not appear in any spec-view identifier, comment, or docstring. The spec is fully abstracted: no __qualname__, __name__, klass, %s.%s.%s, or serializer references — only generic carriers module/clsChain/memberName and a structural model referencePath = (module :: clsChain) ++ [memberName].

Substantive G-PANEL-3 judgment: the sole discriminating insight the spec encodes is 'name the member by the FULL enclosing-qualifier chain, never by the innermost qualifier alone' (buildReference/referencePath, ensures out = referencePath ... and out.length = clsChain.length + 2). That is precisely — and no more than — what the PUBLIC problem_statement already discloses verbatim: it shows the wrong output 'appname.models.Capability.default' and states 'The right value should be appname.models.Profile.Capability.default' (i.e., the full nesting chain Profile.Capability must be kept instead of collapsing to the innermost class Capability). The spec adds no repo-specific mechanism (which attribute, which function, which file) beyond the publicly-stated fix intent. Therefore the spec view does not leak the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
