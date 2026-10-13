# P2 adversarial audit — django__django-14311

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_boundary_mainonly.lean`, `atk_3_always_module.lean`, `atk_4_order_swap.lean`, `atk_5_drop_guard.lean`, `atk_6_wrong_flag.lean`, `atk_7_drop_trailing.lean`, `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec WRONG implementation verifies against the frozen spec; therefore there is no verifying wrong impl whose faithful patch could be materialized/resolved. The spec's postcondition is a strict total-functional equality (ensures cmdline = leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs) with no precondition, so any behavioral deviation leaves an unprovable residual goal.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -61,10 +61,7 @@
     -- impl-start
     let mut cmdline := leadingArgs
     let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
-      then parentPackage
-      else moduleName
+      if parentPackage ≠ "" then parentPackage else moduleName
     cmdline := cmdline ++ ["-m", name]
     cmdline := cmdline ++ trailingArgs
     return cmdline
```

Attack 2 — `atk_2_boundary_mainonly.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -61,8 +61,7 @@
     -- impl-start
     let mut cmdline := leadingArgs
     let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
+      if (moduleName == "__main__") && parentPackage ≠ ""
       then parentPackage
       else moduleName
     cmdline := cmdline ++ ["-m", name]
```

Attack 3 — `atk_3_always_module.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -60,12 +60,7 @@
   do
     -- impl-start
     let mut cmdline := leadingArgs
-    let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
-      then parentPackage
-      else moduleName
-    cmdline := cmdline ++ ["-m", name]
+    cmdline := cmdline ++ ["-m", moduleName]
     cmdline := cmdline ++ trailingArgs
     return cmdline
     -- impl-end
```

Attack 4 — `atk_4_order_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -59,13 +59,8 @@
     leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs
   do
     -- impl-start
-    let mut cmdline := leadingArgs
-    let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
-      then parentPackage
-      else moduleName
-    cmdline := cmdline ++ ["-m", name]
+    let mut cmdline := ["-m", moduleToReexec moduleName parentPackage]
+    cmdline := cmdline ++ leadingArgs
     cmdline := cmdline ++ trailingArgs
     return cmdline
     -- impl-end
```

Attack 5 — `atk_5_drop_guard.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -61,8 +61,7 @@
     -- impl-start
     let mut cmdline := leadingArgs
     let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
+      if (moduleName == "__main__") || moduleName.endsWith ".__main__"
       then parentPackage
       else moduleName
     cmdline := cmdline ++ ["-m", name]
```

Attack 6 — `atk_6_wrong_flag.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -60,12 +60,7 @@
   do
     -- impl-start
     let mut cmdline := leadingArgs
-    let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
-      then parentPackage
-      else moduleName
-    cmdline := cmdline ++ ["-m", name]
+    cmdline := cmdline ++ ["-c", moduleToReexec moduleName parentPackage]
     cmdline := cmdline ++ trailingArgs
     return cmdline
     -- impl-end
```

Attack 7 — `atk_7_drop_trailing.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -60,13 +60,7 @@
   do
     -- impl-start
     let mut cmdline := leadingArgs
-    let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
-      then parentPackage
-      else moduleName
-    cmdline := cmdline ++ ["-m", name]
-    cmdline := cmdline ++ trailingArgs
+    cmdline := cmdline ++ ["-m", moduleToReexec moduleName parentPackage]
     return cmdline
     -- impl-end
 
```

Attack 8 — `atk_8_echo.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation reads a module's reported dotted name
@@ -59,14 +59,9 @@
     leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs
   do
     -- impl-start
+    let name : String := moduleToReexec moduleName parentPackage
     let mut cmdline := leadingArgs
-    let name : String :=
-      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
-            && parentPackage ≠ ""
-      then parentPackage
-      else moduleName
-    cmdline := cmdline ++ ["-m", name]
-    cmdline := cmdline ++ trailingArgs
+    cmdline := cmdline ++ ["-m", name] ++ trailingArgs
     return cmdline
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads a module's reported dotted name
--  and its parent package — both ordinary strings already in hand — and decides
--  which dotted name to hand back for an interpreter relaunch via `-m`. The
--  decision is a pure predicate on those two strings and the assembly is plain
--  list concatenation; there is no unchanged foreign callee whose contract the
--  proof consumes and nothing deep-modeled, so there is nothing to axiomatize.
--  See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The dotted module name an interpreter relaunched with `-m` must be given,
   from the entry module's own reported dotted name and the dotted name of its
   parent package.

   A module run as a *package entry point* reports its own name as the package
   sentinel `__main__` (top-level) or as `<pkg>.__main__` (nested), while its
   parent package carries the dotted name the user actually typed after `-m`; in
   that case the relaunch must use the parent package. Any other module reports
   its own genuine dotted name (e.g. `foo.bar.baz` for a `baz.py` living under
   `foo/bar`), and the relaunch must use that name verbatim — so a deeper dotted
   target is reproduced exactly rather than collapsed onto its parent.

   The package-entry test is `name == "__main__"` OR `name` ends with the dotted
   sentinel `".__main__"`, AND a parent package name is actually present. -/
def moduleToReexec (moduleName : String) (parentPackage : String) : String :=
  if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
        && parentPackage ≠ ""
  then parentPackage
  else moduleName
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the argument vector that relaunches the interpreter on the same
   module: the leading arguments (interpreter executable and any propagated
   warning flags), then the `-m` switch with the dotted name chosen
   by `moduleToReexec`, then the unchanged trailing program arguments.

   `leadingArgs` and `trailingArgs` are read-only carriers reproduced verbatim
   around the injected `-m <name>`; the only computed element is the dotted name,
   which is `moduleToReexec moduleName parentPackage`. -/
method relaunchCommand (leadingArgs : List String)
    (moduleName : String) (parentPackage : String) (trailingArgs : List String)
    return (cmdline : List String)
  ensures cmdline =
    leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs
  do
    -- impl-start
    let mut cmdline := leadingArgs
    let name : String :=
      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
            && parentPackage ≠ ""
      then parentPackage
      else moduleName
    cmdline := cmdline ++ ["-m", name]
    cmdline := cmdline ++ trailingArgs
    return cmdline
    -- impl-end

prove_correct relaunchCommand by
  loom_solve
  simp_all [moduleToReexec]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL executed with project root, PATH including the swebench-lean venv. same_spec confirmed True for all 9 files via swebench_unified.markers.same_spec + get_backend('velvet').language. Verification command per file: `bash scripts/lean_verify.sh <path>` (exit 0=verifies, 1=error, 3=sorry, 124=timeout), run concurrently in batches of 4.

### Results
- pos_control (exact Solution.lean impl): EXIT=0 VERIFIES.
- atk_1_prepatch (parent whenever present -> collapses deeper module; reproduces the prepatch/G-DIFF bug): EXIT=1. Residual goal is exactly the behavioral difference (if p!="" then p else m) vs moduleToReexec. This matches Solution_prepatch.lean's recorded G-DIFF fail = PREPATCH REPRODUCED.
- atk_2_boundary_mainonly (only exact "__main__", drop .endsWith('.__main__')): EXIT=1.
- atk_3_always_module (never remap to parent): EXIT=1.
- atk_4_order_swap (leading args placed after -m): EXIT=1.
- atk_5_drop_guard (drop parentPackage!="" guard): EXIT=1, residual goal (if A then p else m)=(if A & p!="" then p else m), unprovable.
- atk_6_wrong_flag ("-c" instead of "-m"): EXIT=1.
- atk_7_drop_trailing (omit trailingArgs): EXIT=1.
- atk_8_echo (behaviorally CORRECT let-binding reformulation): EXIT=1 due to proof-script brittleness ('No goals to be solved' at simp_all — loom_solve already closed the goal). This is the harmless correct-does-not-verify direction, NOT a spec weakness; it does not admit a wrong impl.

Because NO same-spec WRONG impl verifies, step 2 (materialize faithful patch + run_resolve) has no candidate to run — there is nothing that verifies-but-fails-to-resolve. patches={} accordingly.

REFINEMENT AUDIT (refinement.md / mapping.md): All legs A1-A9 are R (str<->String, list<->List, spec.parent truthiness<->!="") or I (concrete ==, String.endsWith literal-suffix, ++) or I+R (A7). There are ZERO A-consumed / A-reference legs: the modeled slice contains no axiomatized foreign callee; __main__.__spec__.name/.parent are input-delivery (bridged by the mapping.md §2 bijection), correctly NOT modeled as computational callees. NO kind-3 (inexpressible-changed-op): the single genuinely-changed op (the -m dotted-name choice) is modeled DEEPLY and spelled out as moduleToReexec (leg A8), whose branch structure exactly mirrors patch.diff's `if (spec.name=='__main__' or spec.name.endswith('.__main__')) and spec.parent: name=spec.parent else name=spec.name`. Model<->patch correspondence holds. G-AX=skip is justified (no axioms). Recorded gates consistent: G-RESOLVE=pass(resolved), G-DIFF=pass, G-GOLD=pass, G-CONF=pass(100000 inputs seed 14311, 0 disagreements).

VERDICT SOUND: 8 attacks encoded+verified (incl. prepatch bug + a correct echo control), none verifies; positive control verifies; no verifying wrong impl exists so verify=>correct is not falsified; refinement A-legs (none) and model<->patch correspondence hold.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_boundary_mainonly.lean`, `atk_3_always_module.lean`, `atk_4_order_swap.lean`, `atk_5_drop_guard.lean`, `atk_6_wrong_flag.lean`, `atk_7_drop_trailing.lean`, `atk_8_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec WRONG implementation verifies against the frozen spec; therefore there is no verifying wrong impl whose faithful patch could be materialized/resolved. The spec's postcondition is a strict total-functional equality (ensures cmdline = leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs) with no precondition, so any behavioral deviation leaves an unprovable residual goal.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary_mainonly.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_always_module.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_order_swap.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_drop_guard.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_wrong_flag.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_drop_trailing.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation reads a module's reported dotted name
--  and its parent package — both ordinary strings already in hand — and decides
--  which dotted name to hand back for an interpreter relaunch via `-m`. The
--  decision is a pure predicate on those two strings and the assembly is plain
--  list concatenation; there is no unchanged foreign callee whose contract the
--  proof consumes and nothing deep-modeled, so there is nothing to axiomatize.
--  See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The dotted module name an interpreter relaunched with `-m` must be given,
   from the entry module's own reported dotted name and the dotted name of its
   parent package.

   A module run as a *package entry point* reports its own name as the package
   sentinel `__main__` (top-level) or as `<pkg>.__main__` (nested), while its
   parent package carries the dotted name the user actually typed after `-m`; in
   that case the relaunch must use the parent package. Any other module reports
   its own genuine dotted name (e.g. `foo.bar.baz` for a `baz.py` living under
   `foo/bar`), and the relaunch must use that name verbatim — so a deeper dotted
   target is reproduced exactly rather than collapsed onto its parent.

   The package-entry test is `name == "__main__"` OR `name` ends with the dotted
   sentinel `".__main__"`, AND a parent package name is actually present. -/
def moduleToReexec (moduleName : String) (parentPackage : String) : String :=
  if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
        && parentPackage ≠ ""
  then parentPackage
  else moduleName
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the argument vector that relaunches the interpreter on the same
   module: the leading arguments (interpreter executable and any propagated
   warning flags), then the `-m` switch with the dotted name chosen
   by `moduleToReexec`, then the unchanged trailing program arguments.

   `leadingArgs` and `trailingArgs` are read-only carriers reproduced verbatim
   around the injected `-m <name>`; the only computed element is the dotted name,
   which is `moduleToReexec moduleName parentPackage`. -/
method relaunchCommand (leadingArgs : List String)
    (moduleName : String) (parentPackage : String) (trailingArgs : List String)
    return (cmdline : List String)
  ensures cmdline =
    leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs
  do
    -- impl-start
    let mut cmdline := leadingArgs
    let name : String :=
      if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
            && parentPackage ≠ ""
      then parentPackage
      else moduleName
    cmdline := cmdline ++ ["-m", name]
    cmdline := cmdline ++ trailingArgs
    return cmdline
    -- impl-end

prove_correct relaunchCommand by
  loom_solve
  simp_all [moduleToReexec]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL executed with project root, PATH including the swebench-lean venv. same_spec confirmed True for all 9 files via swebench_unified.markers.same_spec + get_backend('velvet').language. Verification command per file: `bash scripts/lean_verify.sh <path>` (exit 0=verifies, 1=error, 3=sorry, 124=timeout), run concurrently in batches of 4.

### Results
- pos_control (exact Solution.lean impl): EXIT=0 VERIFIES.
- atk_1_prepatch (parent whenever present -> collapses deeper module; reproduces the prepatch/G-DIFF bug): EXIT=1. Residual goal is exactly the behavioral difference (if p!="" then p else m) vs moduleToReexec. This matches Solution_prepatch.lean's recorded G-DIFF fail = PREPATCH REPRODUCED.
- atk_2_boundary_mainonly (only exact "__main__", drop .endsWith('.__main__')): EXIT=1.
- atk_3_always_module (never remap to parent): EXIT=1.
- atk_4_order_swap (leading args placed after -m): EXIT=1.
- atk_5_drop_guard (drop parentPackage!="" guard): EXIT=1, residual goal (if A then p else m)=(if A & p!="" then p else m), unprovable.
- atk_6_wrong_flag ("-c" instead of "-m"): EXIT=1.
- atk_7_drop_trailing (omit trailingArgs): EXIT=1.
- atk_8_echo (behaviorally CORRECT let-binding reformulation): EXIT=1 due to proof-script brittleness ('No goals to be solved' at simp_all — loom_solve already closed the goal). This is the harmless correct-does-not-verify direction, NOT a spec weakness; it does not admit a wrong impl.

Because NO same-spec WRONG impl verifies, step 2 (materialize faithful patch + run_resolve) has no candidate to run — there is nothing that verifies-but-fails-to-resolve. patches={} accordingly.

REFINEMENT AUDIT (refinement.md / mapping.md): All legs A1-A9 are R (str<->String, list<->List, spec.parent truthiness<->!="") or I (concrete ==, String.endsWith literal-suffix, ++) or I+R (A7). There are ZERO A-consumed / A-reference legs: the modeled slice contains no axiomatized foreign callee; __main__.__spec__.name/.parent are input-delivery (bridged by the mapping.md §2 bijection), correctly NOT modeled as computational callees. NO kind-3 (inexpressible-changed-op): the single genuinely-changed op (the -m dotted-name choice) is modeled DEEPLY and spelled out as moduleToReexec (leg A8), whose branch structure exactly mirrors patch.diff's `if (spec.name=='__main__' or spec.name.endswith('.__main__')) and spec.parent: name=spec.parent else name=spec.name`. Model<->patch correspondence holds. G-AX=skip is justified (no axioms). Recorded gates consistent: G-RESOLVE=pass(resolved), G-DIFF=pass, G-GOLD=pass, G-CONF=pass(100000 inputs seed 14311, 0 disagreements).

VERDICT SOUND: 8 attacks encoded+verified (incl. prepatch bug + a correct echo control), none verifies; positive control verifies; no verifying wrong impl exists so verify=>correct is not falsified; refinement A-legs (none) and model<->patch correspondence hold.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed to find drift. Setup: bundle patch.diff is EMPTY, but the SWE-bench dataset gold patch for django__django-14311 matches refinement.md §A verbatim (the get_child_arguments __spec__-present -m branch rewrite). Applied it to a fresh git worktree at base_commit 5a8e8f80bb82a867eab7e4d9d099f21d0a976d22. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; G-DIFF prepatch correctly fails (prepatch always takes parent when present, collapsing deeper dotted modules). Ran an INDEPENDENT differential (my own fuzzer, seed 999 — NOT the bundle's 14311 — with adversarial vocabulary: '.__main__', '__main__.__main__', empty name/parent, name==parent, 'my__main__', '__main__x', 'x__main__', varied warnoptions and argv) comparing the Lean spec transliteration [moduleToReexec(name,parent)= parent if (name=='__main__' or name.endswith('.__main__')) and parent!='' else name; cmdline = leading ++ ['-m',name] ++ trailing] against the REAL patched autoreload.get_child_arguments() over 200000 inputs: ZERO disagreements. Spec matches the F2P test_run_as_non_django_module_non_package expectation (-m utils_tests.test_module.main_module, own name not parent). Modeling boundary sound: spec.parent truthiness (incl. None) ↔ parentPackage != ''; literal-suffix str.endswith ↔ String.endsWith; leading/trailing carriers reproduced verbatim matching [sys.executable]+['-W%s'%o] and sys.argv[1:]. No axioms/A-refs, so no hidden strengthening. Spec is neither too strong nor drifting relative to the real callee's modeled -m branch.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec = True); only the impl/proof regions differ. Mechanical G-LEAK screen (leakage.screen over the velvet spec view) passes with zero hard failures. Reviewed spec view directly for semantic gold reconstruction beyond the public problem_statement: (1) patched file path django/utils/autoreload.py absent; (2) patched symbol get_child_arguments absent — renamed relaunchCommand; (3) no verbatim gold-patch line reproduced (spec uses moduleName.endsWith ".__main__" / moduleToReexec, distinct identifiers, no normalized collision with spec.name.endswith('.__main__') etc.); (4) no diff markers; (5) no bug/fix narration. The distinguishing behavior encoded by the spec — package-entry name (__main__ / *.__main__ with parent) collapses to parent, but a genuine deeper dotted module (foo.bar.baz) keeps its own name rather than collapsing to foo.bar — is exactly what the public problem_statement already states verbatim (it gives the foo.bar.baz / foo/bar example and calls the -m foo.bar collapse 'uncalled for'). The .__main__ sentinel appears only as behavioral spec, not as an edit disclosure, and is derivable from the public task + Python semantics; leakage is correctly judged against problem_statement only, not hints_text. No relaxation flag in play (relaxed_leakage None). No reconstruction advantage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
