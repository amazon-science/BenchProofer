# P2 adversarial audit — django__django-11292

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,7 @@
   ensures ∀ s, s ∈ commonOptions → s ∈ out
   do
     -- impl-start
-    let out : List String :=
-      if requiresSystemChecks then
-        commonOptions ++ [skipChecksFlag]
-      else
-        commonOptions
+    let out : List String := commonOptions
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,11 +52,7 @@
   ensures ∀ s, s ∈ commonOptions → s ∈ out
   do
     -- impl-start
-    let out : List String :=
-      if requiresSystemChecks then
-        commonOptions ++ [skipChecksFlag]
-      else
-        commonOptions
+    let out : List String := commonOptions ++ [skipChecksFlag]
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
     -- impl-start
     let out : List String :=
       if requiresSystemChecks then
-        commonOptions ++ [skipChecksFlag]
+        [skipChecksFlag] ++ commonOptions
       else
         commonOptions
     return out
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
   ensures result = (requiresSystemChecks && (! skipRequested))
   do
     -- impl-start
-    let result : Bool := requiresSystemChecks && (! skipRequested)
+    let result : Bool := requiresSystemChecks
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
   ensures result = (requiresSystemChecks && (! skipRequested))
   do
     -- impl-start
-    let result : Bool := requiresSystemChecks && (! skipRequested)
+    let result : Bool := (! skipRequested)
     return result
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
   ensures result = (requiresSystemChecks && (! skipRequested))
   do
     -- impl-start
-    let result : Bool := requiresSystemChecks && (! skipRequested)
+    let result : Bool := requiresSystemChecks || (! skipRequested)
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,10 +53,9 @@
   do
     -- impl-start
     let out : List String :=
-      if requiresSystemChecks then
-        commonOptions ++ [skipChecksFlag]
-      else
-        commonOptions
+      match requiresSystemChecks with
+      | true  => commonOptions ++ [skipChecksFlag]
+      | false => commonOptions
     return out
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,7 +73,7 @@
   ensures result = (requiresSystemChecks && (! skipRequested))
   do
     -- impl-start
-    let result : Bool := requiresSystemChecks && (! skipRequested)
+    let result : Bool := if skipRequested then false else requiresSystemChecks
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: both modeled operations are straight-line option-list /
   boolean assembly in the real code and always terminate, so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge every postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled operations are pure boolean / list-frame
--  logic over FREE INPUTS: the set of command-line options a command already
--  recognises, whether the command performs project validation, and whether the
--  user asked to skip that validation. The argument registry and the validation
--  routine are stdlib / command-specific code the operations only invoke, never
--  reshape — so there is no callee contract to assume and nothing for G-AX.)
-- axioms-end

-- pure-start
/- The standard option string that lets a user opt out of the project-validation
   step from the command line. Public token (it is named in the task). -/
def skipChecksFlag : String := "--skip-checks"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the recognised command-line options for a command, modeled as the
   list of accepted option strings (argument acceptance is membership-based;
   ordering only affects help display, not what parses). When the command
   performs project validation, the opt-out option is added to those it already
   recognises so a user can request that the validation be bypassed; when the
   command performs no validation, the opt-out option is not offered and the
   recognised options are unchanged. The options already recognised
   (`commonOptions`) are read-only and all preserved; the command's validation
   flag (`requiresSystemChecks`) is read-only. The opt-out option is assumed not
   to be among the already-recognised ones. -/
method registeredCommandOptions
    (requiresSystemChecks : Bool) (commonOptions : List String)
    return (out : List String)
  require skipChecksFlag ∉ commonOptions
  ensures requiresSystemChecks = true  → out = commonOptions ++ [skipChecksFlag]
  ensures requiresSystemChecks = false → out = commonOptions
  ensures requiresSystemChecks = true  → skipChecksFlag ∈ out
  ensures requiresSystemChecks = false → skipChecksFlag ∉ out
  ensures ∀ s, s ∈ commonOptions → s ∈ out
  do
    -- impl-start
    let out : List String :=
      if requiresSystemChecks then
        commonOptions ++ [skipChecksFlag]
      else
        commonOptions
    return out
    -- impl-end

prove_correct registeredCommandOptions by
  loom_solve

/- Decide whether to run the project-validation step before handling a command.
   Validation runs exactly when the command performs validation AND the user has
   not requested to skip it; if either the command performs no validation or the
   user asked to skip, it does not run. Both inputs are read-only. -/
method shouldRunSystemChecks
    (requiresSystemChecks : Bool) (skipRequested : Bool)
    return (result : Bool)
  ensures result = (requiresSystemChecks && (! skipRequested))
  do
    -- impl-start
    let result : Bool := requiresSystemChecks && (! skipRequested)
    return result
    -- impl-end

prove_correct shouldRunSystemChecks by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output in every branch of the input domain via structural equalities: method1 `registeredCommandOptions` ensures out=commonOptions++[--skip-checks] (requiresSystemChecks=true) / out=commonOptions (false) plus membership+frame corollaries; method2 `shouldRunSystemChecks` ensures result=(requiresSystemChecks && !skipRequested). Any same-spec verifying impl is therefore extensionally identical to gold, so its faithful refined patch equals the gold patch and resolves.

Protocol executed:
- Positive control positive.lean: `bash scripts/lean_verify.sh .../positive.lean` -> EXIT 0 (verifies).
- Prepatch prepatch.lean (op1 reverted to `out := commonOptions`): EXIT 1, unsolved goals on ensures_3/ensures_5 -> prepatch bug REPRODUCED, spec catches it (G-DIFF).
- 8 same-spec attacks (same_spec=True for all after impl-only edits; verified via swebench_unified.markers.same_spec / get_backend('velvet').language):
  atk_1 prepatch-bug (never add flag): verify EXIT 1 (unsolved ensures_3/5).
  atk_2 partial-domain (always add flag, ignore guard): EXIT 1 (unsolved ensures_2/4).
  atk_3 boundary/order ([flag]++commonOptions in the true branch): EXIT 1 (unsolved ensures_5).
  atk_4 control-flow-effect method2 (result=requiresSystemChecks, drop skip): EXIT 1 (unsolved ensures_1).
  atk_5 ungrounded-oracle echo method2 (result=!skipRequested): EXIT 1 (unsolved ensures_1).
  atk_6 control-flow-effect method2 (|| instead of &&): EXIT 1 (unsolved ensures_1).
  atk_7 VERIFYING (method1 via `match requiresSystemChecks`): EXIT 0.
  atk_8 VERIFYING (method2 via `if skipRequested then false else requiresSystemChecks`): EXIT 0.
  (verify cmd: `bash scripts/lean_verify.sh <file>`; ran 4-concurrent.)
- For BOTH verifying candidates (atk_7, atk_8) the faithful refined patch = gold patch (they are extensionally identical to gold). Materialized faithful_atk_7.diff / faithful_atk_8.diff and RAN the official harness: `run_resolve('django__django-11292', patch, timeout=1800, retries=0)` -> RESOLVED=True, COMPLETED=True, note='resolved'. Docker oracle confirmed available (swe_bench_verified, supports_docker_oracle=True). No verifying wrong impl whose faithful patch fails to resolve => no verify-does-not-imply-correct gap.

refinement.md audit: 4 legs. op1 R (create_parser guarded add_argument('--skip-checks')), op2 I (add_arguments;return parser), op3 R (execute gate `requires_system_checks and not options['skip_checks']`), op4 R (self.check() invocation decision). No axioms => no A-legs (nothing for G-AX); no kind-3 (changed-inexpressible). Model<->patch correspondence holds; commonOptions treated as free frame input (only conditional membership addition is load-bearing; stdlib argparse/add_arguments unchanged, not load-bearing). R/I legs G-CONF-covered.

>=5 attacks run, none breaks the spec; all needed resolve runs completed. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: both modeled operations are straight-line option-list /
   boolean assembly in the real code and always terminate, so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge every postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled operations are pure boolean / list-frame
--  logic over FREE INPUTS: the set of command-line options a command already
--  recognises, whether the command performs project validation, and whether the
--  user asked to skip that validation. The argument registry and the validation
--  routine are stdlib / command-specific code the operations only invoke, never
--  reshape — so there is no callee contract to assume and nothing for G-AX.)
-- axioms-end

-- pure-start
/- The standard option string that lets a user opt out of the project-validation
   step from the command line. Public token (it is named in the task). -/
def skipChecksFlag : String := "--skip-checks"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the recognised command-line options for a command, modeled as the
   list of accepted option strings (argument acceptance is membership-based;
   ordering only affects help display, not what parses). When the command
   performs project validation, the opt-out option is added to those it already
   recognises so a user can request that the validation be bypassed; when the
   command performs no validation, the opt-out option is not offered and the
   recognised options are unchanged. The options already recognised
   (`commonOptions`) are read-only and all preserved; the command's validation
   flag (`requiresSystemChecks`) is read-only. The opt-out option is assumed not
   to be among the already-recognised ones. -/
method registeredCommandOptions
    (requiresSystemChecks : Bool) (commonOptions : List String)
    return (out : List String)
  require skipChecksFlag ∉ commonOptions
  ensures requiresSystemChecks = true  → out = commonOptions ++ [skipChecksFlag]
  ensures requiresSystemChecks = false → out = commonOptions
  ensures requiresSystemChecks = true  → skipChecksFlag ∈ out
  ensures requiresSystemChecks = false → skipChecksFlag ∉ out
  ensures ∀ s, s ∈ commonOptions → s ∈ out
  do
    -- impl-start
    let out : List String :=
      if requiresSystemChecks then
        commonOptions ++ [skipChecksFlag]
      else
        commonOptions
    return out
    -- impl-end

prove_correct registeredCommandOptions by
  loom_solve

/- Decide whether to run the project-validation step before handling a command.
   Validation runs exactly when the command performs validation AND the user has
   not requested to skip it; if either the command performs no validation or the
   user asked to skip, it does not run. Both inputs are read-only. -/
method shouldRunSystemChecks
    (requiresSystemChecks : Bool) (skipRequested : Bool)
    return (result : Bool)
  ensures result = (requiresSystemChecks && (! skipRequested))
  do
    -- impl-start
    let result : Bool := requiresSystemChecks && (! skipRequested)
    return result
    -- impl-end

prove_correct shouldRunSystemChecks by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins output in every branch of the input domain via structural equalities: method1 `registeredCommandOptions` ensures out=commonOptions++[--skip-checks] (requiresSystemChecks=true) / out=commonOptions (false) plus membership+frame corollaries; method2 `shouldRunSystemChecks` ensures result=(requiresSystemChecks && !skipRequested). Any same-spec verifying impl is therefore extensionally identical to gold, so its faithful refined patch equals the gold patch and resolves.

Protocol executed:
- Positive control positive.lean: `bash scripts/lean_verify.sh .../positive.lean` -> EXIT 0 (verifies).
- Prepatch prepatch.lean (op1 reverted to `out := commonOptions`): EXIT 1, unsolved goals on ensures_3/ensures_5 -> prepatch bug REPRODUCED, spec catches it (G-DIFF).
- 8 same-spec attacks (same_spec=True for all after impl-only edits; verified via swebench_unified.markers.same_spec / get_backend('velvet').language):
  atk_1 prepatch-bug (never add flag): verify EXIT 1 (unsolved ensures_3/5).
  atk_2 partial-domain (always add flag, ignore guard): EXIT 1 (unsolved ensures_2/4).
  atk_3 boundary/order ([flag]++commonOptions in the true branch): EXIT 1 (unsolved ensures_5).
  atk_4 control-flow-effect method2 (result=requiresSystemChecks, drop skip): EXIT 1 (unsolved ensures_1).
  atk_5 ungrounded-oracle echo method2 (result=!skipRequested): EXIT 1 (unsolved ensures_1).
  atk_6 control-flow-effect method2 (|| instead of &&): EXIT 1 (unsolved ensures_1).
  atk_7 VERIFYING (method1 via `match requiresSystemChecks`): EXIT 0.
  atk_8 VERIFYING (method2 via `if skipRequested then false else requiresSystemChecks`): EXIT 0.
  (verify cmd: `bash scripts/lean_verify.sh <file>`; ran 4-concurrent.)
- For BOTH verifying candidates (atk_7, atk_8) the faithful refined patch = gold patch (they are extensionally identical to gold). Materialized faithful_atk_7.diff / faithful_atk_8.diff and RAN the official harness: `run_resolve('django__django-11292', patch, timeout=1800, retries=0)` -> RESOLVED=True, COMPLETED=True, note='resolved'. Docker oracle confirmed available (swe_bench_verified, supports_docker_oracle=True). No verifying wrong impl whose faithful patch fails to resolve => no verify-does-not-imply-correct gap.

refinement.md audit: 4 legs. op1 R (create_parser guarded add_argument('--skip-checks')), op2 I (add_arguments;return parser), op3 R (execute gate `requires_system_checks and not options['skip_checks']`), op4 R (self.check() invocation decision). No axioms => no A-legs (nothing for G-AX); no kind-3 (changed-inexpressible). Model<->patch correspondence holds; commonOptions treated as free frame input (only conditional membership addition is load-bearing; stdlib argparse/add_arguments unchanged, not load-bearing). R/I legs G-CONF-covered.

>=5 attacks run, none breaks the spec; all needed resolve runs completed. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec with velvet LanguageTables = True; diff confined to impl-start/impl-end). Solution.lean verifies (exit 0, total-correctness/demonic); prepatch fails on ensures_3/ensures_5, so the spec is non-vacuous and has real behavioral content (G-DIFF holds).

Both modeled functions faithfully match the real repo at base_commit eb16c726 under the gold patch:
- registeredCommandOptions ↔ create_parser: gold adds `if self.requires_system_checks: parser.add_argument('--skip-checks', ...)`. For requiresSystemChecks=true the flag joins the accepted set (out = commonOptions ++ ['--skip-checks']); for false it is not registered (out = commonOptions). Membership modeling of the argparse accepted-option set is sound; order/help/action are incidental. Precondition '--skip-checks' ∉ commonOptions is realistic — base framework options never contain it and add_arguments for the tested set_option command does not; a command re-registering it would itself raise an argparse conflict, correctly outside the modeled domain.
- shouldRunSystemChecks ↔ execute gate `requires_system_checks and not options['skip_checks']`: result = requiresSystemChecks && (!skipRequested) matches on the whole 2-bit cube. Python short-circuit means the `['skip_checks']` key access never KeyErrors (flag is registered exactly when requires_system_checks is True; otherwise the second operand is skipped), so the Bool carrier is faithful.

Searched for a diverging input across both carriers; none exists. Spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec under the velvet LanguageTables (True); impl regions and prove_correct bodies are properly collapsed in the rendered spec_view. (2) Mechanical leakage.screen over the actual spec view returns PASSED with zero hard failures.

Reviewed the full spec view against the PUBLIC problem_statement only (hints_text is empty/excluded). Public problem_statement already exposes: 'skip_checks' stealth option, the '--skip-checks' proposal to expose it on the command line, 'system checks', and running commands from the command line. The spec view stays within these public tokens plus abstract Lean model symbols.

No leakage beyond problem_statement:
- No diff markers, no 'base.py' path, no patched dotted module path in the view.
- No patched repo symbol echoed: gold touches create_parser, execute, DjangoHelpFormatter/_reordered_actions, add_argument, self.check(), base_stealth_options, requires_system_checks. Spec view uses only abstract camelCase model names (registeredCommandOptions, shouldRunSystemChecks, requiresSystemChecks, commonOptions, skipRequested); none embeds a patched Python identifier.
- No bug/fix narration terms in any comment/docstring.
- Only concrete literal is '--skip-checks', which is the public problem-statement title verbatim.
- Comments are behavioral abstractions ('opt-out option', 'project-validation step', 'recognised command-line options') — no gold source quoted (no argparse/add_argument/self.check()/options.get), no file:line, no verbatim problem-statement sentence.

The modeled content (conditional registration guarded by requiresSystemChecks; the requiresSystemChecks && !skipRequested gate) constitutes the SPECIFICATION stated as abstract pre/postconditions with impl and proof elided — the sanctioned spec-to-verify task, not out-of-band disclosure of the gold edit. Reconstructing an impl from a complete behavioral contract is the intended task, not illegitimate gold leakage. meta.json is not a relaxed bundle (relaxed_leakage None, G-LEAK status 'pass'), so the strict standard applies and is met.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
