# P2 adversarial audit — django__django-13837

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec `problem_spec_getChildArguments` is a TOTAL functional equality `result = childArgsSpec …` against the total pure reference function childArgsSpec. Any impl that diverges from childArgsSpec on any input makes the universally-quantified `correct_getChildArguments` a genuinely false proposition, so by Lean soundness it cannot close with clean axioms. All 7 same-spec wrong impls confirm this: each fails `lean_verify.sh` with exit 1 on a genuine `rfl` semantic-divergence error, and none produced a clean-axiom closing proof. No false-green candidate exists, so no faithful patch needed resolve-running.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,8 +93,8 @@
   let mut args : List String := [executable]
   for o in warnoptions do
     args := args ++ ["-W" ++ o]
-  if launchPackage ≠ "" then
-    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
+  if launchPackage = "django" then
+    return .ok (args ++ ["-m", "django"] ++ argv.tail)
   else if ¬ scriptPresent then
     match exeAlt with
     | some exe => return .ok (exe :: argv.tail)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,7 @@
   for o in warnoptions do
     args := args ++ ["-W" ++ o]
   if launchPackage ≠ "" then
-    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
+    return .ok (args ++ ["-m", "django"] ++ argv.tail)
   else if ¬ scriptPresent then
     match exeAlt with
     | some exe => return .ok (exe :: argv.tail)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,7 +94,7 @@
   for o in warnoptions do
     args := args ++ ["-W" ++ o]
   if launchPackage ≠ "" then
-    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
+    return .ok (args ++ ["-m", launchPackage] ++ argv)
   else if ¬ scriptPresent then
     match exeAlt with
     | some exe => return .ok (exe :: argv.tail)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,15 +93,15 @@
   let mut args : List String := [executable]
   for o in warnoptions do
     args := args ++ ["-W" ++ o]
-  if launchPackage ≠ "" then
-    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
-  else if ¬ scriptPresent then
+  if ¬ scriptPresent then
     match exeAlt with
     | some exe => return .ok (exe :: argv.tail)
     | none =>
       match scriptAlt with
       | some sp => return .ok (args ++ [sp] ++ argv.tail)
       | none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
+  else if launchPackage ≠ "" then
+    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
   else
     return .ok (args ++ argv)
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,11 +96,11 @@
   if launchPackage ≠ "" then
     return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
   else if ¬ scriptPresent then
-    match exeAlt with
-    | some exe => return .ok (exe :: argv.tail)
+    match scriptAlt with
+    | some sp => return .ok (args ++ [sp] ++ argv.tail)
     | none =>
-      match scriptAlt with
-      | some sp => return .ok (args ++ [sp] ++ argv.tail)
+      match exeAlt with
+      | some exe => return .ok (exe :: argv.tail)
       | none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
   else
     return .ok (args ++ argv)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,9 +90,7 @@
     (executable : String) (warnoptions argv : List String)
     (launchPackage : String) (scriptPresent : Bool)
     (exeAlt scriptAlt : Option String) : Except String (List String) := Id.run do
-  let mut args : List String := [executable]
-  for o in warnoptions do
-    args := args ++ ["-W" ++ o]
+  let args : List String := [executable]
   if launchPackage ≠ "" then
     return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
   else if ¬ scriptPresent then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
     | none =>
       match scriptAlt with
       | some sp => return .ok (args ++ [sp] ++ argv.tail)
-      | none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
+      | none => return .error ("Script " ++ (argv.headD "") ++ " does not exist.")
   else
     return .ok (args ++ argv)
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Every environmental fact
-- the routine consults — the interpreter executable, the warning options, the
-- argument vector, the launch-module package label, and the filesystem
-- existence probes for the script and its alternate entrypoints — is modeled as
-- a plain typed input (String / Bool / Option / List). Nothing is axiomatized
-- and there is no deep-model reference callee, so this region is empty. The
-- proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The leading prefix of the relaunch command line: the interpreter executable
followed by one `-W<opt>` token for each active warning option, in order. -/
def warnPrefix (executable : String) (warnoptions : List String) : List String :=
  executable :: warnoptions.map (fun o => "-W" ++ o)

/-- POSIX-path string normalization, as performed by rendering a
`pathlib.Path` back to a string (`str(Path(s))`): split on `/`, drop empty
and `.` segments, keep a root of `//` (exactly two leading slashes) or `/`
(one, or three-or-more, leading slashes), and render the empty relative path
as `.`. E.g. `"a/" ↦ "a"`, `"sub//x.py" ↦ "sub/x.py"`, `"a/./b" ↦ "a/b"`,
`"" ↦ "."`. -/
def posixStr (s : String) : String :=
  let segs := (s.splitOn "/").filter (fun p => p != "" && p != ".")
  let root :=
    if s.startsWith "//" && !(s.startsWith "///") then "//"
    else if s.startsWith "/" then "/"
    else ""
  if segs.isEmpty then (if root = "" then "." else root)
  else root ++ String.intercalate "/" segs

/-- Reference description of the relaunch argument vector as a function of the
launch environment.

* `executable`      — the interpreter binary path.
* `warnoptions`     — active warning options (each becomes a `-W<opt>` token).
* `argv`            — the current argument vector; `argv` head is the script,
                      `argv.tail` are the trailing program arguments.
* `launchPackage`   — the top-level package label of the entry-point module when
                      the program was started as a module, or the empty string
                      when it was not started that way.
* `scriptPresent`   — whether the script path is present on disk.
* `exeAlt`          — the alternate executable entrypoint path, when present.
* `scriptAlt`       — the alternate script entrypoint path, when present.

When the program was started as a module (`launchPackage ≠ ""`), the routine
relaunches that same module by name. Otherwise, if the script path is absent it
falls back to the alternate entrypoints (preferring the executable one), failing
with a diagnostic when neither exists — the diagnostic renders the script path
as `Path(sys.argv[0])` does, i.e. POSIX-normalized (`posixStr`). Otherwise it
replays the original argument vector verbatim. -/
def childArgsSpec (executable : String) (warnoptions argv : List String)
    (launchPackage : String) (scriptPresent : Bool)
    (exeAlt scriptAlt : Option String) : Except String (List String) :=
  let args := warnPrefix executable warnoptions
  if launchPackage ≠ "" then
    .ok (args ++ ["-m", launchPackage] ++ argv.tail)
  else if ¬ scriptPresent then
    match exeAlt with
    | some exe => .ok (exe :: argv.tail)
    | none =>
      match scriptAlt with
      | some sp => .ok (args ++ [sp] ++ argv.tail)
      | none => .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
  else
    .ok (args ++ argv)
-- pure-end

-- post-conditions-start
/-- The produced relaunch argument vector is exactly the one described by
`childArgsSpec` for the given launch environment: when the program was started
as a module the relaunch re-invokes that module by its package label, every
unchanged branch (alternate-entrypoint fallback, verbatim replay, missing-script
diagnostic) is preserved, and the executable / warning-option prefix and the
trailing program arguments are carried through unchanged. -/
def problem_spec_getChildArguments
    (executable : String) (warnoptions argv : List String)
    (launchPackage : String) (scriptPresent : Bool)
    (exeAlt scriptAlt : Option String)
    (result : Except String (List String)) : Prop :=
  result = childArgsSpec executable warnoptions argv launchPackage
                         scriptPresent exeAlt scriptAlt
-- post-conditions-end

-- impl-start
def implementation_getChildArguments
    (executable : String) (warnoptions argv : List String)
    (launchPackage : String) (scriptPresent : Bool)
    (exeAlt scriptAlt : Option String) : Except String (List String) := Id.run do
  let mut args : List String := [executable]
  for o in warnoptions do
    args := args ++ ["-W" ++ o]
  if launchPackage ≠ "" then
    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
  else if ¬ scriptPresent then
    match exeAlt with
    | some exe => return .ok (exe :: argv.tail)
    | none =>
      match scriptAlt with
      | some sp => return .ok (args ++ [sp] ++ argv.tail)
      | none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
  else
    return .ok (args ++ argv)
-- impl-end

-- proof-start
/-- The `-W<opt>` accumulator fold rewrites to an append of the mapped options. -/
theorem getChildArguments_foldl_app (xs : List String) (init : List String) :
    xs.foldl (fun args o => args ++ ["-W" ++ o]) init
      = init ++ xs.map (fun o => "-W" ++ o) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih => simp [ih]

/-- The cleaned `forIn` warning-option loop equals the accumulating `List.foldl`. -/
theorem getChildArguments_forIn_loop (warnoptions : List String) (init : List String) :
    (Id.run (forIn warnoptions init (fun o r =>
        (pure (ForInStep.yield (r ++ ["-W" ++ o])) : Id (ForInStep (List String))))))
    = warnoptions.foldl (fun args o => args ++ ["-W" ++ o]) init := by
  induction warnoptions generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.foldl_cons]
    simp only [Id.run, bind] at ih ⊢
    exact ih (init ++ ["-W" ++ a])

/-- The desugared loop, run from the singleton `[executable]`, yields exactly
`warnPrefix`. -/
theorem getChildArguments_keyEq (executable : String) (warnoptions : List String) :
    (forIn warnoptions [executable] fun o r =>
      (pure (ForInStep.yield (r ++ ["-W" ++ o])) : Id (ForInStep (List String))))
    = warnPrefix executable warnoptions := by
  have h := getChildArguments_forIn_loop warnoptions [executable]
  simp only [Id.run] at h
  rw [h, getChildArguments_foldl_app]
  rfl

theorem correct_getChildArguments :
    ∀ (executable : String) (warnoptions argv : List String)
      (launchPackage : String) (scriptPresent : Bool)
      (exeAlt scriptAlt : Option String),
    problem_spec_getChildArguments executable warnoptions argv launchPackage
      scriptPresent exeAlt scriptAlt
      (implementation_getChildArguments executable warnoptions argv launchPackage
        scriptPresent exeAlt scriptAlt) := by
  intro executable warnoptions argv launchPackage scriptPresent exeAlt scriptAlt
  unfold problem_spec_getChildArguments implementation_getChildArguments childArgsSpec
  simp only [Id.run, bind, getChildArguments_keyEq]
  split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec check (swebench_unified.markers.same_spec, backend lean): ALL 8 files True (atk_1..7 + pos) — impl region is the ONLY edit; axioms/pure/pre/post byte-identical.

Positive control pos.lean (exact gold impl): `bash scripts/lean_verify.sh .../pos.lean` -> exit 0. `#print axioms correct_getChildArguments` -> depends on axioms: [propext, Quot.sound] (standard, no sorry, no custom/_prop axioms). Clean.

Attacks (all `bash scripts/lean_verify.sh .../atk_N.lean`, run concurrently in 2 batches of 4/3):
- atk_1 (prepatch bug: module branch fires only for literal launchPackage="django", emits literal "django"): EXIT 1, rfl fail LHS `Except.ok (warnPrefix ++ ["-m","django"] ++ argv.tail)` (guard launchPackage="django") vs RHS spec branch on launchPackage≠"". This is exactly Solution_prepatch.lean's impl -> PREPATCH REPRODUCED. Diverges on any module launch with launchPackage∉{"","django"} (the F2P test_run_as_non_django_module).
- atk_2 (partial-domain: guard launchPackage≠"" correct but emits literal "django" instead of launchPackage): EXIT 1, rfl fail `["-m","django"]` vs `["-m",launchPackage]`.
- atk_3 (boundary: module branch uses full argv instead of argv.tail): EXIT 1, rfl fail `++ argv` vs `++ argv.tail`.
- atk_4 (control-flow-effect: tests ¬scriptPresent fallback BEFORE the module-launch guard): EXIT 1, rfl fail — branch order swapped, diverges when launchPackage≠"" ∧ ¬scriptPresent.
- atk_5 (ungrounded-oracle echo / priority swap: prefers scriptAlt over exeAlt in the missing-script fallback): EXIT 1, rfl fail — match order reversed, diverges when both exeAlt,scriptAlt = some.
- atk_6 (drop warnoptions loop: args=[executable] only): EXIT 1, rfl fail `[executable] ++ …` vs `warnPrefix executable warnoptions ++ …`; also unused-variable warning on warnoptions.
- atk_7 (raw argv[0] in error, no posixStr — the pre-2026-08-03 G-PANEL-2 bug): EXIT 1, rfl fail `argv.headD ""` vs `posixStr (argv.headD "")`.

Every wrong impl fails to verify; positive control verifies with clean axioms => verify⇒correct holds for all attacks tried => SOUND. No attack produced a closing clean-axiom proof, so patches={} and no run_resolve was required.

refinement.md audit: 9 legs, all tagged R (type refinement). warnPrefix/posixStr are pure helpers shared by impl AND spec childArgsSpec (not axiomatized unchanged callees). Environment probes (launchPackage, scriptPresent, exeAlt, scriptAlt) are reified as typed inputs, not deep-model reference callees. NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs — consistent with the empty axioms region. A-legs vacuous, nothing to falsify there. Discriminating clause (rows 3-4) correctly corresponds to the F2P test_run_as_non_django_module and to the patch's __main__.__spec__.parent change.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec `problem_spec_getChildArguments` is a TOTAL functional equality `result = childArgsSpec …` against the total pure reference function childArgsSpec. Any impl that diverges from childArgsSpec on any input makes the universally-quantified `correct_getChildArguments` a genuinely false proposition, so by Lean soundness it cannot close with clean axioms. All 7 same-spec wrong impls confirm this: each fails `lean_verify.sh` with exit 1 on a genuine `rfl` semantic-divergence error, and none produced a clean-axiom closing proof. No false-green candidate exists, so no faithful patch needed resolve-running.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Every environmental fact
-- the routine consults — the interpreter executable, the warning options, the
-- argument vector, the launch-module package label, and the filesystem
-- existence probes for the script and its alternate entrypoints — is modeled as
-- a plain typed input (String / Bool / Option / List). Nothing is axiomatized
-- and there is no deep-model reference callee, so this region is empty. The
-- proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The leading prefix of the relaunch command line: the interpreter executable
followed by one `-W<opt>` token for each active warning option, in order. -/
def warnPrefix (executable : String) (warnoptions : List String) : List String :=
  executable :: warnoptions.map (fun o => "-W" ++ o)

/-- POSIX-path string normalization, as performed by rendering a
`pathlib.Path` back to a string (`str(Path(s))`): split on `/`, drop empty
and `.` segments, keep a root of `//` (exactly two leading slashes) or `/`
(one, or three-or-more, leading slashes), and render the empty relative path
as `.`. E.g. `"a/" ↦ "a"`, `"sub//x.py" ↦ "sub/x.py"`, `"a/./b" ↦ "a/b"`,
`"" ↦ "."`. -/
def posixStr (s : String) : String :=
  let segs := (s.splitOn "/").filter (fun p => p != "" && p != ".")
  let root :=
    if s.startsWith "//" && !(s.startsWith "///") then "//"
    else if s.startsWith "/" then "/"
    else ""
  if segs.isEmpty then (if root = "" then "." else root)
  else root ++ String.intercalate "/" segs

/-- Reference description of the relaunch argument vector as a function of the
launch environment.

* `executable`      — the interpreter binary path.
* `warnoptions`     — active warning options (each becomes a `-W<opt>` token).
* `argv`            — the current argument vector; `argv` head is the script,
                      `argv.tail` are the trailing program arguments.
* `launchPackage`   — the top-level package label of the entry-point module when
                      the program was started as a module, or the empty string
                      when it was not started that way.
* `scriptPresent`   — whether the script path is present on disk.
* `exeAlt`          — the alternate executable entrypoint path, when present.
* `scriptAlt`       — the alternate script entrypoint path, when present.

When the program was started as a module (`launchPackage ≠ ""`), the routine
relaunches that same module by name. Otherwise, if the script path is absent it
falls back to the alternate entrypoints (preferring the executable one), failing
with a diagnostic when neither exists — the diagnostic renders the script path
as `Path(sys.argv[0])` does, i.e. POSIX-normalized (`posixStr`). Otherwise it
replays the original argument vector verbatim. -/
def childArgsSpec (executable : String) (warnoptions argv : List String)
    (launchPackage : String) (scriptPresent : Bool)
    (exeAlt scriptAlt : Option String) : Except String (List String) :=
  let args := warnPrefix executable warnoptions
  if launchPackage ≠ "" then
    .ok (args ++ ["-m", launchPackage] ++ argv.tail)
  else if ¬ scriptPresent then
    match exeAlt with
    | some exe => .ok (exe :: argv.tail)
    | none =>
      match scriptAlt with
      | some sp => .ok (args ++ [sp] ++ argv.tail)
      | none => .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
  else
    .ok (args ++ argv)
-- pure-end

-- post-conditions-start
/-- The produced relaunch argument vector is exactly the one described by
`childArgsSpec` for the given launch environment: when the program was started
as a module the relaunch re-invokes that module by its package label, every
unchanged branch (alternate-entrypoint fallback, verbatim replay, missing-script
diagnostic) is preserved, and the executable / warning-option prefix and the
trailing program arguments are carried through unchanged. -/
def problem_spec_getChildArguments
    (executable : String) (warnoptions argv : List String)
    (launchPackage : String) (scriptPresent : Bool)
    (exeAlt scriptAlt : Option String)
    (result : Except String (List String)) : Prop :=
  result = childArgsSpec executable warnoptions argv launchPackage
                         scriptPresent exeAlt scriptAlt
-- post-conditions-end

-- impl-start
def implementation_getChildArguments
    (executable : String) (warnoptions argv : List String)
    (launchPackage : String) (scriptPresent : Bool)
    (exeAlt scriptAlt : Option String) : Except String (List String) := Id.run do
  let mut args : List String := [executable]
  for o in warnoptions do
    args := args ++ ["-W" ++ o]
  if launchPackage ≠ "" then
    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)
  else if ¬ scriptPresent then
    match exeAlt with
    | some exe => return .ok (exe :: argv.tail)
    | none =>
      match scriptAlt with
      | some sp => return .ok (args ++ [sp] ++ argv.tail)
      | none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")
  else
    return .ok (args ++ argv)
-- impl-end

-- proof-start
/-- The `-W<opt>` accumulator fold rewrites to an append of the mapped options. -/
theorem getChildArguments_foldl_app (xs : List String) (init : List String) :
    xs.foldl (fun args o => args ++ ["-W" ++ o]) init
      = init ++ xs.map (fun o => "-W" ++ o) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih => simp [ih]

/-- The cleaned `forIn` warning-option loop equals the accumulating `List.foldl`. -/
theorem getChildArguments_forIn_loop (warnoptions : List String) (init : List String) :
    (Id.run (forIn warnoptions init (fun o r =>
        (pure (ForInStep.yield (r ++ ["-W" ++ o])) : Id (ForInStep (List String))))))
    = warnoptions.foldl (fun args o => args ++ ["-W" ++ o]) init := by
  induction warnoptions generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.foldl_cons]
    simp only [Id.run, bind] at ih ⊢
    exact ih (init ++ ["-W" ++ a])

/-- The desugared loop, run from the singleton `[executable]`, yields exactly
`warnPrefix`. -/
theorem getChildArguments_keyEq (executable : String) (warnoptions : List String) :
    (forIn warnoptions [executable] fun o r =>
      (pure (ForInStep.yield (r ++ ["-W" ++ o])) : Id (ForInStep (List String))))
    = warnPrefix executable warnoptions := by
  have h := getChildArguments_forIn_loop warnoptions [executable]
  simp only [Id.run] at h
  rw [h, getChildArguments_foldl_app]
  rfl

theorem correct_getChildArguments :
    ∀ (executable : String) (warnoptions argv : List String)
      (launchPackage : String) (scriptPresent : Bool)
      (exeAlt scriptAlt : Option String),
    problem_spec_getChildArguments executable warnoptions argv launchPackage
      scriptPresent exeAlt scriptAlt
      (implementation_getChildArguments executable warnoptions argv launchPackage
        scriptPresent exeAlt scriptAlt) := by
  intro executable warnoptions argv launchPackage scriptPresent exeAlt scriptAlt
  unfold problem_spec_getChildArguments implementation_getChildArguments childArgsSpec
  simp only [Id.run, bind, getChildArguments_keyEq]
  split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec check (swebench_unified.markers.same_spec, backend lean): ALL 8 files True (atk_1..7 + pos) — impl region is the ONLY edit; axioms/pure/pre/post byte-identical.

Positive control pos.lean (exact gold impl): `bash scripts/lean_verify.sh .../pos.lean` -> exit 0. `#print axioms correct_getChildArguments` -> depends on axioms: [propext, Quot.sound] (standard, no sorry, no custom/_prop axioms). Clean.

Attacks (all `bash scripts/lean_verify.sh .../atk_N.lean`, run concurrently in 2 batches of 4/3):
- atk_1 (prepatch bug: module branch fires only for literal launchPackage="django", emits literal "django"): EXIT 1, rfl fail LHS `Except.ok (warnPrefix ++ ["-m","django"] ++ argv.tail)` (guard launchPackage="django") vs RHS spec branch on launchPackage≠"". This is exactly Solution_prepatch.lean's impl -> PREPATCH REPRODUCED. Diverges on any module launch with launchPackage∉{"","django"} (the F2P test_run_as_non_django_module).
- atk_2 (partial-domain: guard launchPackage≠"" correct but emits literal "django" instead of launchPackage): EXIT 1, rfl fail `["-m","django"]` vs `["-m",launchPackage]`.
- atk_3 (boundary: module branch uses full argv instead of argv.tail): EXIT 1, rfl fail `++ argv` vs `++ argv.tail`.
- atk_4 (control-flow-effect: tests ¬scriptPresent fallback BEFORE the module-launch guard): EXIT 1, rfl fail — branch order swapped, diverges when launchPackage≠"" ∧ ¬scriptPresent.
- atk_5 (ungrounded-oracle echo / priority swap: prefers scriptAlt over exeAlt in the missing-script fallback): EXIT 1, rfl fail — match order reversed, diverges when both exeAlt,scriptAlt = some.
- atk_6 (drop warnoptions loop: args=[executable] only): EXIT 1, rfl fail `[executable] ++ …` vs `warnPrefix executable warnoptions ++ …`; also unused-variable warning on warnoptions.
- atk_7 (raw argv[0] in error, no posixStr — the pre-2026-08-03 G-PANEL-2 bug): EXIT 1, rfl fail `argv.headD ""` vs `posixStr (argv.headD "")`.

Every wrong impl fails to verify; positive control verifies with clean axioms => verify⇒correct holds for all attacks tried => SOUND. No attack produced a closing clean-axiom proof, so patches={} and no run_resolve was required.

refinement.md audit: 9 legs, all tagged R (type refinement). warnPrefix/posixStr are pure helpers shared by impl AND spec childArgsSpec (not axiomatized unchanged callees). Environment probes (launchPackage, scriptPresent, exeAlt, scriptAlt) are reified as typed inputs, not deep-model reference callees. NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs — consistent with the empty axioms region. A-legs vacuous, nothing to falsify there. Discriminating clause (rows 3-4) correctly corresponds to the F2P test_run_as_non_django_module and to the patch's __main__.__spec__.parent change.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found between modeled childArgsSpec and the real post-patch django.utils.autoreload.get_child_arguments() (base 415f5029 + patch.diff). Checks: (1) same_spec(post,pre,LeanBackend.language)=True — spec region byte-identical; prepatch differs only in impl/proof (buggy launchPackage="django" guard, correct G-DIFF for test_run_as_non_django_module). (2) Lean compiles clean, #print axioms = [propext, Quot.sound], no sorryAx — real proof. (3) posixStr fuzzed vs Python str(PurePosixPath(s)): exhaustive small + 300k random inputs, 0 mismatches (the previously-flagged raw-argv[0] issue is fixed). (4) End-to-end fuzz of modeled vs faithful transliteration of real function over 500k random 7-tuples (empty/'django'/arbitrary launchPackage, script-absent fallback chain, exeAlt/scriptAlt None-or-path): 0 mismatches. launchPackage!="" faithfully encodes '__spec__ is not None and __spec__.parent' (only "" is falsy for a str). Reified env observations (scriptPresent/exeAlt/scriptAlt) do not over-constrain. Only degenerate case argv=[] (real Python IndexErrors) is unreachable since sys.argv always has >=1 element — not a meaningful divergence. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the SOLVER-VISIBLE problem_statement only (not hints_text), over the consumer spec view = Solution.lean's non-elided regions (impl+proof collapsed to placeholders; refinement.md/mapping.md are NOT part of the spec view). Verified spec_view() output directly and confirmed markers.same_spec(Solution, Solution_prepatch)=True and the mechanical leakage.screen()=passed (no hard failures).

Gold edit: replace hard-coded `python -m django` detection (script-path == django.__main__ file) with the general `__main__.__spec__.parent` mechanism, relaunching ANY launched module by its package label (`args += ['-m', __main__.__spec__.parent]`).

The public problem_statement ALREADY fully discloses this fix: it names get_child_arguments, states the goal (allow `python -m pkg_other_than_django runserver`), and explicitly prescribes the documented mechanism — '__main__.__spec__.parent ... Python was started with -m pkg if and only if __main__.__spec__.parent == "pkg"'. So the spec view revealing that a module launch re-invokes `launchPackage` reveals nothing beyond the public task.

Spec-view content check:
- childArgsSpec / problem_spec describe post-patch behavior abstractly via typed input `launchPackage` (`launchPackage ≠ "" → ["-m", launchPackage]`) — exactly the public algorithm, no `"django"` literal, no pre-patch behavior, no diff.
- No patched file path (django/utils/autoreload.py) or diff markers in the view.
- Comments describe behavior only; no bug/fix/pre-patch/regression narration (narration screen clean).
- Unchanged branches (alt-entrypoint fallback, verbatim replay, missing-script diagnostic incl. posixStr normalization) are context, not the gold edit, and are not tied to the specific gold change.

The discriminating `"django"` literal and pre-patch narration live only in Solution_prepatch.lean's impl region (elided from the spec view) and in refinement.md/mapping.md (not part of the spec view). Nothing leaks the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
