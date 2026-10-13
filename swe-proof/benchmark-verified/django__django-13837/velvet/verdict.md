# P2 adversarial audit — django__django-13837

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,27 +129,21 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
-    let modPkg : Option (List Char) :=
+    let isDjangoModule : Bool :=
       match entry with
-      | .moduleEntry pkg => some pkg
-      | _                => none
+      | .moduleEntry pkg => decide (pkg = "django".toList)
+      | _                => false
     let out : Except ArgErr (List (List Char)) :=
-      match modPkg with
-      | some pkg =>
-          Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ userArgs))
-      | none =>
-          match probe with
-          | .exists      => Except.ok (prefixArgs ++ argv)
-          | .exeEntry    => Except.ok (exePath :: userArgs)
-          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
-          | .missing     => Except.error .scriptMissing
+      if isDjangoModule then
+        Except.ok (prefixArgs ++ (["-m".toList, "django".toList] ++ userArgs))
+      else
+        match probe with
+        | .exists      => Except.ok (prefixArgs ++ argv)
+        | .exeEntry    => Except.ok (exePath :: userArgs)
+        | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
+        | .missing     => Except.error .scriptMissing
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,22 +129,13 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
-    let modPkg : Option (List Char) :=
+    let out : Except ArgErr (List (List Char)) :=
       match entry with
-      | .moduleEntry pkg => some pkg
-      | _                => none
-    let out : Except ArgErr (List (List Char)) :=
-      match modPkg with
-      | some pkg =>
-          Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ userArgs))
-      | none =>
+      | .moduleEntry pkg =>
+          Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ argv))
+      | _ =>
           match probe with
           | .exists      => Except.ok (prefixArgs ++ argv)
           | .exeEntry    => Except.ok (exePath :: userArgs)
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,17 +129,13 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
     let modPkg : Option (List Char) :=
       match entry with
       | .moduleEntry pkg => some pkg
-      | _                => none
+      | .pathEntry       => some []
+      | .notModule       => none
     let out : Except ArgErr (List (List Char)) :=
       match modPkg with
       | some pkg =>
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,13 +129,8 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
     let modPkg : Option (List Char) :=
       match entry with
       | .moduleEntry pkg => some pkg
@@ -147,7 +142,7 @@
       | none =>
           match probe with
           | .exists      => Except.ok (prefixArgs ++ argv)
-          | .exeEntry    => Except.ok (exePath :: userArgs)
+          | .exeEntry    => Except.ok (prefixArgs ++ (exePath :: userArgs))
           | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
           | .missing     => Except.error .scriptMissing
     return out
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,13 +129,8 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
     let modPkg : Option (List Char) :=
       match entry with
       | .moduleEntry pkg => some pkg
@@ -149,7 +144,7 @@
           | .exists      => Except.ok (prefixArgs ++ argv)
           | .exeEntry    => Except.ok (exePath :: userArgs)
           | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
-          | .missing     => Except.error .scriptMissing
+          | .missing     => Except.ok []
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,13 +129,8 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
     let modPkg : Option (List Char) :=
       match entry with
       | .moduleEntry pkg => some pkg
@@ -146,7 +141,7 @@
           Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ userArgs))
       | none =>
           match probe with
-          | .exists      => Except.ok (prefixArgs ++ argv)
+          | .exists      => Except.ok (prefixArgs ++ userArgs)
           | .exeEntry    => Except.ok (exePath :: userArgs)
           | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
           | .missing     => Except.error .scriptMissing
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,13 +129,8 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
     let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
     let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
     let modPkg : Option (List Char) :=
       match entry with
       | .moduleEntry pkg => some pkg
@@ -147,8 +142,8 @@
       | none =>
           match probe with
           | .exists      => Except.ok (prefixArgs ++ argv)
-          | .exeEntry    => Except.ok (exePath :: userArgs)
-          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
+          | .exeEntry    => Except.ok (scriptPath :: userArgs)
+          | .scriptEntry => Except.ok (prefixArgs ++ ([exePath] ++ userArgs))
           | .missing     => Except.error .scriptMissing
     return out
     -- impl-end
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
 /- No consumed axioms. This routine assembles a child-process argument vector
@@ -129,27 +129,8 @@
   ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
   do
     -- impl-start
-    -- The leading interpreter+warning-flags prefix, assembled once.
-    let prefixArgs : List (List Char) := baseArgs interp warnOpts
-    -- The forwarded user arguments: everything after the invoking script path.
-    let userArgs : List (List Char) := argv.drop 1
-    -- The module package, when the entry descriptor names a non-empty one: this
-    -- is the documented test for "started as a module", and the package it
-    -- yields is what the module-execution re-launch must name.
-    let modPkg : Option (List Char) :=
-      match entry with
-      | .moduleEntry pkg => some pkg
-      | _                => none
     let out : Except ArgErr (List (List Char)) :=
-      match modPkg with
-      | some pkg =>
-          Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ userArgs))
-      | none =>
-          match probe with
-          | .exists      => Except.ok (prefixArgs ++ argv)
-          | .exeEntry    => Except.ok (exePath :: userArgs)
-          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
-          | .missing     => Except.error .scriptMissing
+      childArgsSpec interp warnOpts entry probe argv exePath scriptPath
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_gold.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. This routine assembles a child-process argument vector
   purely from values it is handed — the interpreter path, the active warning
   options, the full invoking argument vector, the program-entry descriptor, and
   the on-disk probe outcome for the invoking script path (plus the two
   host-derived alternative paths). Each of those is a read-only input (an
   R-refinement of the corresponding runtime/host query); none is an unchanged
   callee whose behavior the proof must assume, so there is no module-level
   `axiom`. Refinement fidelity is checked mechanically by conformance_check.py
   (G-CONF). (mapping.md §1, §3.) -/
-- axioms-end

-- pure-start
/- The program-entry descriptor: how the top-level program was started.
   `notModule`  — the program was NOT launched via the module-execution form
                  (there is no module entry descriptor for it); detection by the
                  script path is what then applies.
   `pathEntry`  — launched from a filesystem path entry (a directory or archive)
                  rather than a named module: an entry descriptor exists, but it
                  names no package (its package name is empty).
   `moduleEntry pkg` — launched via the module-execution form for package `pkg`:
                  the entry descriptor exists and names that non-empty package.
   This mirrors the documented entry-point descriptor whose package field is
   absent when not started as a module, empty when started from a path entry,
   and equal to the package name when started as a module. -/
inductive EntryDesc where
  | notModule
  | pathEntry
  | moduleEntry (pkg : List Char)
  deriving DecidableEq

/- The on-disk probe of the invoking script path, when the program was NOT
   started as a module. Mutually exclusive outcomes, in the order the routine
   consults them:
   `exists`     — the script path exists as given;
   `exeEntry`   — it does not exist as given, but the same path with the native
                  executable suffix does (a path-extension quirk on some hosts);
   `scriptEntry`— neither of the above, but a sibling generated launcher script
                  (the path's name with a launcher suffix) exists;
   `missing`    — none exist (an invalid invocation). -/
inductive ScriptProbe where
  | exists
  | exeEntry
  | scriptEntry
  | missing
  deriving DecidableEq

/- Failure: the invoking script path names nothing that can be executed. -/
inductive ArgErr where
  | scriptMissing
  deriving DecidableEq

/- One re-emitted command-line flag per active warning option: each option `o`
   becomes the flag `-W` followed by `o`. Front-recursive over the options so it
   composes by `++`; preserves order. -/
def warnFlags : List (List Char) → List (List Char)
  | []      => []
  | o :: os => ("-W".toList ++ o) :: warnFlags os

/- The leading, always-present portion of the child argument vector: the
   interpreter path followed by the warning-option flags. -/
def baseArgs (interp : List Char) (warnOpts : List (List Char)) : List (List Char) :=
  interp :: warnFlags warnOpts

/- The intended child argument vector, as a total function of the environment
   the routine observes. `argv` is the full original argument vector (its head
   is the invoking script path; `argv.drop 1` are the user arguments forwarded
   to the child).

   The single behavioral pivot of this change: the program is treated as
   "started as a module" exactly when its entry descriptor names a non-empty
   package — `moduleEntry pkg` — and the re-launch then uses the module-execution
   form for *that* package, followed by the forwarded arguments. The descriptor's
   absence (`notModule`) and a path-entry start (`pathEntry`, whose package is
   empty) are BOTH "not a module" and fall through to the script-path-based
   assembly: run the script as given if it exists, else an executable sibling,
   else a generated launcher-script sibling, else fail. -/
def childArgsSpec
    (interp : List Char) (warnOpts : List (List Char))
    (entry : EntryDesc) (probe : ScriptProbe)
    (argv : List (List Char))            -- the full original argument vector
    (exePath scriptPath : List Char)     -- host-derived alternative paths
    : Except ArgErr (List (List Char)) :=
  match entry with
  | .moduleEntry pkg =>
      Except.ok (baseArgs interp warnOpts ++ (["-m".toList, pkg] ++ argv.drop 1))
  | _ =>
      match probe with
      | .exists      => Except.ok (baseArgs interp warnOpts ++ argv)
      | .exeEntry    => Except.ok (exePath :: argv.drop 1)
      | .scriptEntry => Except.ok (baseArgs interp warnOpts ++ ([scriptPath] ++ argv.drop 1))
      | .missing     => Except.error .scriptMissing

@[grind] lemma childArgsSpec_module
    (interp : List Char) (warnOpts : List (List Char)) (pkg : List Char)
    (probe : ScriptProbe) (argv : List (List Char))
    (exePath scriptPath : List Char) :
    childArgsSpec interp warnOpts (.moduleEntry pkg) probe argv exePath scriptPath
      = Except.ok (baseArgs interp warnOpts ++ (["-m".toList, pkg] ++ argv.drop 1)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the argument vector used to re-launch the running program when the
   file watcher restarts it. Every parameter is a read-only observation of the
   environment (none is `mut`; nothing is mutated, directive 5). The desired
   behaviour is `childArgsSpec`: in particular, when the program was started as a
   module of some package, the re-launch must request THAT package by name — not
   a single predetermined one — so command-line programs other than the
   framework's own can be reloaded correctly. -/
method buildChildArgs
    (interp : List Char) (warnOpts : List (List Char))
    (entry : EntryDesc) (probe : ScriptProbe)
    (argv : List (List Char))
    (exePath : List Char) (scriptPath : List Char)
    return (out : Except ArgErr (List (List Char)))
  ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
  do
    -- impl-start
    -- The leading interpreter+warning-flags prefix, assembled once.
    let prefixArgs : List (List Char) := baseArgs interp warnOpts
    -- The forwarded user arguments: everything after the invoking script path.
    let userArgs : List (List Char) := argv.drop 1
    -- The module package, when the entry descriptor names a non-empty one: this
    -- is the documented test for "started as a module", and the package it
    -- yields is what the module-execution re-launch must name.
    let modPkg : Option (List Char) :=
      match entry with
      | .moduleEntry pkg => some pkg
      | _                => none
    let out : Except ArgErr (List (List Char)) :=
      match modPkg with
      | some pkg =>
          Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ userArgs))
      | none =>
          match probe with
          | .exists      => Except.ok (prefixArgs ++ argv)
          | .exeEntry    => Except.ok (exePath :: userArgs)
          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
          | .missing     => Except.error .scriptMissing
    return out
    -- impl-end

prove_correct buildChildArgs by
  loom_solve
  cases entry <;> simp_all [childArgsSpec, baseArgs]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tight extensional-equality contract `ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath`, where childArgsSpec/baseArgs/warnFlags are total, fully-concrete, AXIOM-FREE functions entirely visible in the spec view. pre/post-conditions regions are EMPTY (region_text len=0) => no domain narrowing; there is no opaque oracle and no answer-key input. Verify therefore forces the impl to be extensionally equal to childArgsSpec on the complete input partition EntryDesc x ScriptProbe x argv x exePath x scriptPath.

REFINEMENT.MD AUDIT (A-legs focus per plan §4): all 9 legs are R / R+I / I (A1=R, A2=R+I, A3=R, A4=I, A5-A9=R/R+I). There are NO A-consumed and NO A-reference legs, and NO kind-3 (inexpressible-changed-op) steps. The A-leg correspondence obligation is thus vacuously satisfied: the changed operation (module-start detection + the package it names) is modeled DIRECTLY in `childArgsSpec`/`modPkg` + the `["-m", pkg]` emission, not behind any callee axiom. Solution.lean declares no module-level `axiom` (grep confirmed); G-AX=skip is legitimate. R/I fidelity is mechanically covered by G-CONF (recorded pass: 100,057 inputs, 0 disagreements vs the REAL gold-patched get_child_arguments over the full 7x4 entry×probe space + the exact F2P scenario).

ATTACKS (all same_spec=True vs frozen Solution.lean — impl-region-only edits, axioms/pure/pre/post byte-identical; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug / ungrounded — module branch emits literal ["-m","django"] for ANY module; the F2P bug test_run_as_non_django_module): exit 1 REJECTED.
- atk_2 (module branch appends full argv instead of argv.drop 1): exit 1 REJECTED.
- atk_3 (boundary — pathEntry (empty parent) wrongly treated as module `some []`): exit 1 REJECTED.
- atk_4 (control-flow-effect — exeEntry branch wrongly prepends prefixArgs; gold returns [exe]++argv.drop1): exit 1 REJECTED.
- atk_5 (partial-domain — missing returns Except.ok [] instead of Except.error .scriptMissing): exit 1 REJECTED.
- atk_6 (exists branch drops the script path: prefixArgs ++ userArgs): exit 1 REJECTED.
- atk_7 (boundary swap — exeEntry uses scriptPath, scriptEntry uses exePath): exit 1 REJECTED.
- atk_8 (ungrounded-oracle ECHO — impl literally returns `childArgsSpec interp warnOpts entry probe argv exePath scriptPath`): exit 1 — fails ONLY on the frozen proof script (`loom_solve` closes the goal, then the frozen `cases entry` errors `No goals to be solved`). This is a proof-automation artifact, NOT a verifying counterexample: it does not verify, so no patch to resolve.

RESOLVE OBLIGATION: vacuously discharged. Zero wrong impls verified, so there is no verifying-but-wrong impl whose faithful refined patch would need to be materialized + run through the harness. `patches` is empty accordingly.

POSITIVE CONTROLS (verify=0, exit 0): pos_control_gold.lean (exact byte copy of frozen Solution.lean) and pos_control_alt.lean (behaviorally correct but structurally different — outer `match entry` with notModule/pathEntry as separate explicit branches, baseArgs inlined via prefixArgs). Spec is non-vacuous and not over-fit to the gold's syntactic form.

PARALLELISM: attacks verified in two concurrent background batches of 4 (atk_1..4, then atk_5..8), positive controls concurrently; all commands `bash scripts/lean_verify.sh <path>`.

Recorded gates: G-EQ pass, G-PANEL-1/2/3 pass, G-CONF pass, G-RESOLVE pass, G-AX skip, G-PBT skip. Verify⇒(extensionally equal to childArgsSpec = gold)⇒resolve. No counterexample; the equality spec cannot be satisfied by any behaviorally-divergent impl. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_gold.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. This routine assembles a child-process argument vector
   purely from values it is handed — the interpreter path, the active warning
   options, the full invoking argument vector, the program-entry descriptor, and
   the on-disk probe outcome for the invoking script path (plus the two
   host-derived alternative paths). Each of those is a read-only input (an
   R-refinement of the corresponding runtime/host query); none is an unchanged
   callee whose behavior the proof must assume, so there is no module-level
   `axiom`. Refinement fidelity is checked mechanically by conformance_check.py
   (G-CONF). (mapping.md §1, §3.) -/
-- axioms-end

-- pure-start
/- The program-entry descriptor: how the top-level program was started.
   `notModule`  — the program was NOT launched via the module-execution form
                  (there is no module entry descriptor for it); detection by the
                  script path is what then applies.
   `pathEntry`  — launched from a filesystem path entry (a directory or archive)
                  rather than a named module: an entry descriptor exists, but it
                  names no package (its package name is empty).
   `moduleEntry pkg` — launched via the module-execution form for package `pkg`:
                  the entry descriptor exists and names that non-empty package.
   This mirrors the documented entry-point descriptor whose package field is
   absent when not started as a module, empty when started from a path entry,
   and equal to the package name when started as a module. -/
inductive EntryDesc where
  | notModule
  | pathEntry
  | moduleEntry (pkg : List Char)
  deriving DecidableEq

/- The on-disk probe of the invoking script path, when the program was NOT
   started as a module. Mutually exclusive outcomes, in the order the routine
   consults them:
   `exists`     — the script path exists as given;
   `exeEntry`   — it does not exist as given, but the same path with the native
                  executable suffix does (a path-extension quirk on some hosts);
   `scriptEntry`— neither of the above, but a sibling generated launcher script
                  (the path's name with a launcher suffix) exists;
   `missing`    — none exist (an invalid invocation). -/
inductive ScriptProbe where
  | exists
  | exeEntry
  | scriptEntry
  | missing
  deriving DecidableEq

/- Failure: the invoking script path names nothing that can be executed. -/
inductive ArgErr where
  | scriptMissing
  deriving DecidableEq

/- One re-emitted command-line flag per active warning option: each option `o`
   becomes the flag `-W` followed by `o`. Front-recursive over the options so it
   composes by `++`; preserves order. -/
def warnFlags : List (List Char) → List (List Char)
  | []      => []
  | o :: os => ("-W".toList ++ o) :: warnFlags os

/- The leading, always-present portion of the child argument vector: the
   interpreter path followed by the warning-option flags. -/
def baseArgs (interp : List Char) (warnOpts : List (List Char)) : List (List Char) :=
  interp :: warnFlags warnOpts

/- The intended child argument vector, as a total function of the environment
   the routine observes. `argv` is the full original argument vector (its head
   is the invoking script path; `argv.drop 1` are the user arguments forwarded
   to the child).

   The single behavioral pivot of this change: the program is treated as
   "started as a module" exactly when its entry descriptor names a non-empty
   package — `moduleEntry pkg` — and the re-launch then uses the module-execution
   form for *that* package, followed by the forwarded arguments. The descriptor's
   absence (`notModule`) and a path-entry start (`pathEntry`, whose package is
   empty) are BOTH "not a module" and fall through to the script-path-based
   assembly: run the script as given if it exists, else an executable sibling,
   else a generated launcher-script sibling, else fail. -/
def childArgsSpec
    (interp : List Char) (warnOpts : List (List Char))
    (entry : EntryDesc) (probe : ScriptProbe)
    (argv : List (List Char))            -- the full original argument vector
    (exePath scriptPath : List Char)     -- host-derived alternative paths
    : Except ArgErr (List (List Char)) :=
  match entry with
  | .moduleEntry pkg =>
      Except.ok (baseArgs interp warnOpts ++ (["-m".toList, pkg] ++ argv.drop 1))
  | _ =>
      match probe with
      | .exists      => Except.ok (baseArgs interp warnOpts ++ argv)
      | .exeEntry    => Except.ok (exePath :: argv.drop 1)
      | .scriptEntry => Except.ok (baseArgs interp warnOpts ++ ([scriptPath] ++ argv.drop 1))
      | .missing     => Except.error .scriptMissing

@[grind] lemma childArgsSpec_module
    (interp : List Char) (warnOpts : List (List Char)) (pkg : List Char)
    (probe : ScriptProbe) (argv : List (List Char))
    (exePath scriptPath : List Char) :
    childArgsSpec interp warnOpts (.moduleEntry pkg) probe argv exePath scriptPath
      = Except.ok (baseArgs interp warnOpts ++ (["-m".toList, pkg] ++ argv.drop 1)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the argument vector used to re-launch the running program when the
   file watcher restarts it. Every parameter is a read-only observation of the
   environment (none is `mut`; nothing is mutated, directive 5). The desired
   behaviour is `childArgsSpec`: in particular, when the program was started as a
   module of some package, the re-launch must request THAT package by name — not
   a single predetermined one — so command-line programs other than the
   framework's own can be reloaded correctly. -/
method buildChildArgs
    (interp : List Char) (warnOpts : List (List Char))
    (entry : EntryDesc) (probe : ScriptProbe)
    (argv : List (List Char))
    (exePath : List Char) (scriptPath : List Char)
    return (out : Except ArgErr (List (List Char)))
  ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath
  do
    -- impl-start
    -- The leading interpreter+warning-flags prefix, assembled once.
    let prefixArgs : List (List Char) := baseArgs interp warnOpts
    -- The forwarded user arguments: everything after the invoking script path.
    let userArgs : List (List Char) := argv.drop 1
    -- The module package, when the entry descriptor names a non-empty one: this
    -- is the documented test for "started as a module", and the package it
    -- yields is what the module-execution re-launch must name.
    let modPkg : Option (List Char) :=
      match entry with
      | .moduleEntry pkg => some pkg
      | _                => none
    let out : Except ArgErr (List (List Char)) :=
      match modPkg with
      | some pkg =>
          Except.ok (prefixArgs ++ (["-m".toList, pkg] ++ userArgs))
      | none =>
          match probe with
          | .exists      => Except.ok (prefixArgs ++ argv)
          | .exeEntry    => Except.ok (exePath :: userArgs)
          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))
          | .missing     => Except.error .scriptMissing
    return out
    -- impl-end

prove_correct buildChildArgs by
  loom_solve
  cases entry <;> simp_all [childArgsSpec, baseArgs]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tight extensional-equality contract `ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath`, where childArgsSpec/baseArgs/warnFlags are total, fully-concrete, AXIOM-FREE functions entirely visible in the spec view. pre/post-conditions regions are EMPTY (region_text len=0) => no domain narrowing; there is no opaque oracle and no answer-key input. Verify therefore forces the impl to be extensionally equal to childArgsSpec on the complete input partition EntryDesc x ScriptProbe x argv x exePath x scriptPath.

REFINEMENT.MD AUDIT (A-legs focus per plan §4): all 9 legs are R / R+I / I (A1=R, A2=R+I, A3=R, A4=I, A5-A9=R/R+I). There are NO A-consumed and NO A-reference legs, and NO kind-3 (inexpressible-changed-op) steps. The A-leg correspondence obligation is thus vacuously satisfied: the changed operation (module-start detection + the package it names) is modeled DIRECTLY in `childArgsSpec`/`modPkg` + the `["-m", pkg]` emission, not behind any callee axiom. Solution.lean declares no module-level `axiom` (grep confirmed); G-AX=skip is legitimate. R/I fidelity is mechanically covered by G-CONF (recorded pass: 100,057 inputs, 0 disagreements vs the REAL gold-patched get_child_arguments over the full 7x4 entry×probe space + the exact F2P scenario).

ATTACKS (all same_spec=True vs frozen Solution.lean — impl-region-only edits, axioms/pure/pre/post byte-identical; command: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug / ungrounded — module branch emits literal ["-m","django"] for ANY module; the F2P bug test_run_as_non_django_module): exit 1 REJECTED.
- atk_2 (module branch appends full argv instead of argv.drop 1): exit 1 REJECTED.
- atk_3 (boundary — pathEntry (empty parent) wrongly treated as module `some []`): exit 1 REJECTED.
- atk_4 (control-flow-effect — exeEntry branch wrongly prepends prefixArgs; gold returns [exe]++argv.drop1): exit 1 REJECTED.
- atk_5 (partial-domain — missing returns Except.ok [] instead of Except.error .scriptMissing): exit 1 REJECTED.
- atk_6 (exists branch drops the script path: prefixArgs ++ userArgs): exit 1 REJECTED.
- atk_7 (boundary swap — exeEntry uses scriptPath, scriptEntry uses exePath): exit 1 REJECTED.
- atk_8 (ungrounded-oracle ECHO — impl literally returns `childArgsSpec interp warnOpts entry probe argv exePath scriptPath`): exit 1 — fails ONLY on the frozen proof script (`loom_solve` closes the goal, then the frozen `cases entry` errors `No goals to be solved`). This is a proof-automation artifact, NOT a verifying counterexample: it does not verify, so no patch to resolve.

RESOLVE OBLIGATION: vacuously discharged. Zero wrong impls verified, so there is no verifying-but-wrong impl whose faithful refined patch would need to be materialized + run through the harness. `patches` is empty accordingly.

POSITIVE CONTROLS (verify=0, exit 0): pos_control_gold.lean (exact byte copy of frozen Solution.lean) and pos_control_alt.lean (behaviorally correct but structurally different — outer `match entry` with notModule/pathEntry as separate explicit branches, baseArgs inlined via prefixArgs). Spec is non-vacuous and not over-fit to the gold's syntactic form.

PARALLELISM: attacks verified in two concurrent background batches of 4 (atk_1..4, then atk_5..8), positive controls concurrently; all commands `bash scripts/lean_verify.sh <path>`.

Recorded gates: G-EQ pass, G-PANEL-1/2/3 pass, G-CONF pass, G-RESOLVE pass, G-AX skip, G-PBT skip. Verify⇒(extensionally equal to childArgsSpec = gold)⇒resolve. No counterexample; the equality spec cannot be satisfied by any behaviorally-divergent impl. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified rigorously: (1) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend)=True — spec region byte-identical (SPEC_REGIONS axioms/pure/pre/post). Examined the real patched callee at base_commit 2c7846d992 django/utils/autoreload.py:213 get_child_arguments. childArgsSpec faithfully models its control flow: outer branch on __main__.__spec__ (None->notModule, present+empty .parent->pathEntry, present+non-empty->moduleEntry pkg); module branch emits [interp]+['-W'+o...]+['-m', pkg]+argv[1:] naming the DETECTED package (not literal 'django'), independent of the on-disk probe; non-module branches fall through the exists/exeEntry/scriptEntry/missing ladder in the exact order the elif/if ladder consults them, with RuntimeError<->Except.error scriptMissing. (3) Ran an independent Python differential (shadow transliteration vs real oracle under mocked sys.executable/argv/warnoptions/__main__) over all entry x probe x warnopt x rest combinations: 0 disagreements — matches the recorded G-CONF pass (100057 inputs, seed=13837, 0 disagreements). (4) warnFlags deeply models the '-W%s'%o comprehension preserving order; exePath/scriptPath modeled as free host-derived inputs consistent with with_suffix('.exe')/with_name('%s-script.py'). (5) No axioms (G-AX skip legitimate — all inputs are read-only observations the harness controls, not assumed callees). The spec is neither too strong nor too weak relative to real repo behavior on any realizable input. G-DIFF also confirms prepatch (modPkg = some pkg only if pkg='django') correctly fails on the F2P moduleEntry 'utils_tests.test_module' scenario.

Counterexample / evidence:

```
N/A — no in-domain input where childArgsSpec disagrees with the real patched get_child_arguments.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> hard_failures=[]) and spec region is byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec = True). Reviewed the solver-visible spec view (spec_view projection) semantically for gold-edit leakage beyond the public problem_statement (hints_text is EMPTY, so no hints-echo concern).

Gold edit: in get_child_arguments, replace `py_script == django_main_path` / literal `['-m','django']` with `if __main__.__spec__ is not None and __main__.__spec__.parent: args += ['-m', __main__.__spec__.parent]`.

The problem_statement is itself highly disclosive: it already names get_child_arguments, prescribes using __main__.__spec__, states __spec__ is not None iff launched with -m or a path entry, that __spec__.parent == '' for a directory/zipfile start, and 'Python was started with -m pkg iff __main__.__spec__.parent == pkg'. Leakage must be judged as excess OVER this public text.

The spec view abstracts the three __spec__ states as EntryDesc.{notModule, pathEntry, moduleEntry pkg} — a direct paraphrase of the three cases the problem statement already enumerates (None / empty parent / non-empty parent==pkg), and is in fact MORE abstract than the statement (it drops the concrete __spec__/__main__/parent identifiers entirely). The ScriptProbe ladder and baseArgs prefix model UNCHANGED surrounding context (the pre-existing elif/else fallback), not the gold edit. The 'single behavioral pivot' comment describes naming the detected package rather than a literal, which the problem statement itself states.

No diff markers, no patched file path (django/utils/autoreload.py), no dotted module path, no reproduced gold-patch line, and no echo of the prepatch-only discriminators (django_main_path, literal 'django', __file__). Those prepatch discriminators appear only in refinement.md/mapping.md, which are NOT part of the G-LEAK spec view. The single distinctive patched symbol get_child_arguments does not appear verbatim in the spec view and is public via the problem statement anyway. Nothing in the spec view reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
