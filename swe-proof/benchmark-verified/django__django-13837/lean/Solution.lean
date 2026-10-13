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
