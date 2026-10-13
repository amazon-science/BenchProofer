# P2 adversarial audit — django__django-14311

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2_always_module.lean`, `atk_3_or.lean`, `atk_4_swap.lean`, `atk_5_eq_only.lean`, `atk_6_prepatch.lean`, `atk_7_always_parent.lean`, `atk_8_prefix.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition pins result to an EXACT deterministic function of the inputs: result = (if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage else moduleName). Any same-spec implementation whose correct_ proof closes MUST be extensionally equal to gold, so a verifying-but-wrong impl cannot exist. The only verifying attack (atk_1_echo, the literal spec RHS) is extensionally identical to gold; its faithful patch is the gold patch and it RESOLVES=True under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2_always_module.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,12 +32,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
-    return parentPackage
-  else
-    return moduleName
+  return moduleName
 -- impl-end
 
 -- proof-start
@@ -46,8 +44,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 2 — `atk_3_or.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,9 +32,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
+  if isMainEntry moduleName || !parentPackage.isEmpty then
     return parentPackage
   else
     return moduleName
@@ -46,8 +47,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 3 — `atk_4_swap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,12 +32,13 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
   if isMainEntry moduleName && !parentPackage.isEmpty then
+    return moduleName
+  else
     return parentPackage
-  else
-    return moduleName
 -- impl-end
 
 -- proof-start
@@ -46,8 +47,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 4 — `atk_5_eq_only.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,9 +32,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
+  if moduleName == "__main__".toList && !parentPackage.isEmpty then
     return parentPackage
   else
     return moduleName
@@ -46,8 +47,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 5 — `atk_6_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,9 +32,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
+  if !parentPackage.isEmpty then
     return parentPackage
   else
     return moduleName
@@ -46,8 +47,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 6 — `atk_7_always_parent.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,12 +32,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
-    return parentPackage
-  else
-    return moduleName
+  return parentPackage
 -- impl-end
 
 -- proof-start
@@ -46,8 +44,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 7 — `atk_8_prefix.lean` → rejected (same spec, does not verify — good)

```diff
@@ -32,9 +32,10 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
     (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
+  if (moduleName == "__main__".toList || (".__main__".toList).isPrefixOf moduleName) && !parentPackage.isEmpty then
     return parentPackage
   else
     return moduleName
@@ -46,8 +47,8 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  unfold problem_spec_relaunchModule implementation_relaunchModule isMainEntry
+  simp_all [Id.run]
+  <;> try rfl
+  <;> try decide
 -- proof-end
```

Attack 8 — `atk_1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,12 +32,11 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_relaunchModule
-    (moduleName parentPackage : List Char) : List Char := Id.run do
-  if isMainEntry moduleName && !parentPackage.isEmpty then
-    return parentPackage
-  else
-    return moduleName
+    (moduleName parentPackage : List Char) : List Char :=
+  if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage
+  else moduleName
 -- impl-end
 
 -- proof-start
@@ -46,8 +45,5 @@
     problem_spec_relaunchModule moduleName parentPackage
       (implementation_relaunchModule moduleName parentPackage) := by
   intro moduleName parentPackage
-  unfold problem_spec_relaunchModule implementation_relaunchModule
-  simp only [Id.run]
-  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
-    simp only [h, if_true, pure]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the module-name selection
-- is a pure decision over the executed module's fully-qualified name and its
-- parent package, modeled DEEPLY below (string equality + suffix test + emptiness
-- test) rather than axiomatized. The proof agent may add `_prop` axioms only if it
-- gets genuinely stuck.
-- axioms-end

-- pure-start
/-- A module's fully-qualified name identifies a top-level entry point when it is
exactly the conventional entry-point name, or when it is a submodule whose final
dotted component is that conventional entry-point name. -/
def isMainEntry (moduleName : List Char) : Bool :=
  moduleName == "__main__".toList || (".__main__".toList).isSuffixOf moduleName
-- pure-end

-- post-conditions-start
/-- When a program is relaunched as a module (`-m`), the module name to pass is
chosen from the executed module's own fully-qualified name and the name of its
parent package. If the executed module is an entry-point module AND a parent
package is present, the parent package's name is used; otherwise the module's own
fully-qualified name is used verbatim. The chosen name is the sole output and is
pinned to the inputs in every case. -/
def problem_spec_relaunchModule
    (moduleName parentPackage : List Char) (result : List Char) : Prop :=
  result =
    (if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage
     else moduleName)
-- post-conditions-end

-- impl-start

def implementation_relaunchModule
    (moduleName parentPackage : List Char) : List Char := Id.run do
  if isMainEntry moduleName && !parentPackage.isEmpty then
    return parentPackage
  else
    return moduleName
-- impl-end

-- proof-start
theorem correct_relaunchModule :
    ∀ (moduleName parentPackage : List Char),
    problem_spec_relaunchModule moduleName parentPackage
      (implementation_relaunchModule moduleName parentPackage) := by
  intro moduleName parentPackage
  unfold problem_spec_relaunchModule implementation_relaunchModule
  simp only [Id.run]
  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
    simp only [h, if_true, if_false, pure] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True confirmed for all 8 attacks + positive control (spec/axioms/pure/pre/post regions byte-identical; only impl+proof edited).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- atk_1_echo (literal spec RHS; extensionally = gold): EXIT=0 (verifies). #print axioms correct_relaunchModule => 'does not depend on any axioms' (CLEAN). This is the ONLY closing wrong-shaped/echo impl.
- atk_2_always_module (return moduleName unconditionally; partial-domain): EXIT=1, genuine unsolved goal (pure moduleName = parentPackage on entry+parent case).
- atk_3_or (|| instead of &&; boundary): EXIT=1, genuine false goal.
- atk_4_swap (branches swapped; control-flow-effect): EXIT=1, genuine false goal.
- atk_5_eq_only (drops .__main__ suffix branch): EXIT=1, genuine false goal.
- atk_6_prepatch (parent whenever nonempty; the ACTUAL prepatch bug): EXIT=1, genuine false goal. Re-ran with max-effort proof (simp_all + split/omega/tauto/rfl) atk_6_maxeffort.lean => EXIT=1 still unsolved. Prepatch reproduced (matches Solution_prepatch.lean bug + G-DIFF).
- atk_7_always_parent (return parentPackage unconditionally; ungrounded-oracle): EXIT=1; max-effort atk_7_maxeffort.lean => EXIT=1 still unsolved.
- atk_8_prefix (isPrefixOf instead of isSuffixOf): EXIT=1, genuine false goal.
- pos_control (gold impl): EXIT=0; #print axioms => [propext] (CLEAN).

RESOLVE (protocol step 2 — executed, not speculated): for the one verifying attack atk_1_echo, materialized its faithful refined patch (byte-identical to gold post-patch; meta.patch_equals_gold=True) at atk_1_echo.patch and ran run_resolve('django__django-14311', patch, timeout=1800, retries=1) via python => RESOLVED=True, FLAKY=False. So the verifying attack's faithful patch DOES resolve => verify⇒correct holds; nothing breaks the spec.

REFINEMENT AUDIT (refinement.md): rows 1-2 = R (str<->List Char bijection; empty str<->[]). rows 3-6 = I (identical ops: string ==, isSuffixOf<->endswith, boolean &&, two-way selection). NO A-consumed, NO A-reference legs (axioms region empty, G-AX declared skip stub — consistent with impl having no UNCHANGED opaque callee; all ops modeled deeply). NO kind-3 (changed-inexpressible) legs. spec.parent is always a str ('' for top-level), so !parentPackage.isEmpty faithfully models spec.parent truthiness. mapping.md scope note correctly handles the moved parent-truthiness guard: modeled decision returns moduleName in the no-parent case, matching post-patch name=spec.name. Correspondence to real callees (str.endswith, str ==, bool and) holds. All legs R/A/I; audit passes.

VERDICT: SOUND. >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle, suffix->prefix, prepatch) all fail to verify with genuine false goals; the sole verifying attack is a gold-equivalent echo whose faithful patch RESOLVES. The exact-equality postcondition leaves no room for a verifying-but-wrong impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2_always_module.lean`, `atk_3_or.lean`, `atk_4_swap.lean`, `atk_5_eq_only.lean`, `atk_6_prepatch.lean`, `atk_7_always_parent.lean`, `atk_8_prefix.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition pins result to an EXACT deterministic function of the inputs: result = (if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage else moduleName). Any same-spec implementation whose correct_ proof closes MUST be extensionally equal to gold, so a verifying-but-wrong impl cannot exist. The only verifying attack (atk_1_echo, the literal spec RHS) is extensionally identical to gold; its faithful patch is the gold patch and it RESOLVES=True under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2_always_module.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3_or.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4_swap.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_eq_only.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_always_parent.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8_prefix.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_1_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the module-name selection
-- is a pure decision over the executed module's fully-qualified name and its
-- parent package, modeled DEEPLY below (string equality + suffix test + emptiness
-- test) rather than axiomatized. The proof agent may add `_prop` axioms only if it
-- gets genuinely stuck.
-- axioms-end

-- pure-start
/-- A module's fully-qualified name identifies a top-level entry point when it is
exactly the conventional entry-point name, or when it is a submodule whose final
dotted component is that conventional entry-point name. -/
def isMainEntry (moduleName : List Char) : Bool :=
  moduleName == "__main__".toList || (".__main__".toList).isSuffixOf moduleName
-- pure-end

-- post-conditions-start
/-- When a program is relaunched as a module (`-m`), the module name to pass is
chosen from the executed module's own fully-qualified name and the name of its
parent package. If the executed module is an entry-point module AND a parent
package is present, the parent package's name is used; otherwise the module's own
fully-qualified name is used verbatim. The chosen name is the sole output and is
pinned to the inputs in every case. -/
def problem_spec_relaunchModule
    (moduleName parentPackage : List Char) (result : List Char) : Prop :=
  result =
    (if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage
     else moduleName)
-- post-conditions-end

-- impl-start

def implementation_relaunchModule
    (moduleName parentPackage : List Char) : List Char := Id.run do
  if isMainEntry moduleName && !parentPackage.isEmpty then
    return parentPackage
  else
    return moduleName
-- impl-end

-- proof-start
theorem correct_relaunchModule :
    ∀ (moduleName parentPackage : List Char),
    problem_spec_relaunchModule moduleName parentPackage
      (implementation_relaunchModule moduleName parentPackage) := by
  intro moduleName parentPackage
  unfold problem_spec_relaunchModule implementation_relaunchModule
  simp only [Id.run]
  by_cases h : isMainEntry moduleName && !parentPackage.isEmpty <;>
    simp only [h, if_true, if_false, pure] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec=True confirmed for all 8 attacks + positive control (spec/axioms/pure/pre/post regions byte-identical; only impl+proof edited).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- atk_1_echo (literal spec RHS; extensionally = gold): EXIT=0 (verifies). #print axioms correct_relaunchModule => 'does not depend on any axioms' (CLEAN). This is the ONLY closing wrong-shaped/echo impl.
- atk_2_always_module (return moduleName unconditionally; partial-domain): EXIT=1, genuine unsolved goal (pure moduleName = parentPackage on entry+parent case).
- atk_3_or (|| instead of &&; boundary): EXIT=1, genuine false goal.
- atk_4_swap (branches swapped; control-flow-effect): EXIT=1, genuine false goal.
- atk_5_eq_only (drops .__main__ suffix branch): EXIT=1, genuine false goal.
- atk_6_prepatch (parent whenever nonempty; the ACTUAL prepatch bug): EXIT=1, genuine false goal. Re-ran with max-effort proof (simp_all + split/omega/tauto/rfl) atk_6_maxeffort.lean => EXIT=1 still unsolved. Prepatch reproduced (matches Solution_prepatch.lean bug + G-DIFF).
- atk_7_always_parent (return parentPackage unconditionally; ungrounded-oracle): EXIT=1; max-effort atk_7_maxeffort.lean => EXIT=1 still unsolved.
- atk_8_prefix (isPrefixOf instead of isSuffixOf): EXIT=1, genuine false goal.
- pos_control (gold impl): EXIT=0; #print axioms => [propext] (CLEAN).

RESOLVE (protocol step 2 — executed, not speculated): for the one verifying attack atk_1_echo, materialized its faithful refined patch (byte-identical to gold post-patch; meta.patch_equals_gold=True) at atk_1_echo.patch and ran run_resolve('django__django-14311', patch, timeout=1800, retries=1) via python => RESOLVED=True, FLAKY=False. So the verifying attack's faithful patch DOES resolve => verify⇒correct holds; nothing breaks the spec.

REFINEMENT AUDIT (refinement.md): rows 1-2 = R (str<->List Char bijection; empty str<->[]). rows 3-6 = I (identical ops: string ==, isSuffixOf<->endswith, boolean &&, two-way selection). NO A-consumed, NO A-reference legs (axioms region empty, G-AX declared skip stub — consistent with impl having no UNCHANGED opaque callee; all ops modeled deeply). NO kind-3 (changed-inexpressible) legs. spec.parent is always a str ('' for top-level), so !parentPackage.isEmpty faithfully models spec.parent truthiness. mapping.md scope note correctly handles the moved parent-truthiness guard: modeled decision returns moduleName in the no-parent case, matching post-patch name=spec.name. Correspondence to real callees (str.endswith, str ==, bool and) holds. All legs R/A/I; audit passes.

VERDICT: SOUND. >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle, suffix->prefix, prepatch) all fail to verify with genuine false goals; the sole verifying attack is a gold-equivalent echo whose faithful patch RESOLVES. The exact-equality postcondition leaves no room for a verifying-but-wrong impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-14311/lean. Modeled function: the post-patch `-m` module-name selection inside get_child_arguments (django/utils/autoreload.py @ base_commit, worktree). Real callee: name = spec.parent if (spec.name=='__main__' or spec.name.endswith('.__main__')) and spec.parent else spec.name. Spec problem_spec_relaunchModule pins result = (if isMainEntry moduleName && !parentPackage.isEmpty then parentPackage else moduleName), with isMainEntry = (moduleName=='__main__' || '.__main__'.isSuffixOf moduleName) — an exact op-for-op transliteration of the Python, not a weakened relation.

Checks performed:
1. Lean verify: scripts/lean_verify.sh exit 0, no sorry.
2. #print axioms correct_relaunchModule => [propext] only; NO sorryAx, proof is genuine.
3. same_spec(Solution, Solution_prepatch, lean backend) = True; spec region byte-identical, so the fix lives only in impl. G-DIFF: prepatch fails (correct signal, matches F2P test_run_as_non_django_module_non_package).
4. Differential faithfulness test spec-semantics vs real repo over 256 adversarial edge pairs (empty/whitespace parents ' '/'\t', '.__main__', 'a.__main__', '__main__.x', trailing-space '__main__ ', case variants '__MAIN__', 'foo.__main__x') => 0 divergences. Python spec.parent truthiness (any non-empty str incl. whitespace) maps correctly to Lean !parentPackage.isEmpty.
5. G-CONF: 120009 inputs, 0 disagreements (seed 14311).

The spec is neither too strong (it does not forbid any real behavior) nor drifted: on every input the modeled Prop agrees with the real callee. Could find no diverging input. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced, no patched path django/utils/autoreload.py, no identifier embedding get_child_arguments, no narration). same_spec(patched, prepatch)=True — spec view byte-identical; the prepatch 'buggy' comment sits inside the elided impl region and never reaches the spec view. Spec view uses only abstract invented names (moduleName, parentPackage, isMainEntry, relaunchModule) with zero repo-localization symbols (__spec__, spec.parent/name, autoreload.py), so the solver cannot recover WHERE to edit. Comments describe behavior, not the edit. The __main__ / entry-point / foo.bar.baz-truncation content the spec encodes is already public in problem_statement; the endswith('.__main__') mechanism lives only in hints_text, which is correctly NOT a leakage baseline, and the spec formalizes the public concept rather than echoing hint wording. Encoding the correct selection rule in the post-condition is intrinsic to a formal spec (it is the correctness oracle) and does not reveal the gold diff beyond the public task. Meta records G-LEAK=pass, G-PANEL-1/2/3=pass, G-EQ=pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
