import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

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
    -- Pre-image skeleton: module-launch is recognised ONLY by matching the
    -- invoking script path against the framework's own module file, i.e. only
    -- for the single fixed package "django", and the re-launch then hard-codes
    -- `-m django`. A program started as a module of ANY OTHER package is not
    -- recognised here — it falls through to the script-path branch. The frozen
    -- spec requires the module-launch case to name the program's OWN package, so
    -- prove_correct MUST fail.
    let prefixArgs : List (List Char) := baseArgs interp warnOpts
    let userArgs : List (List Char) := argv.drop 1
    let isDjangoModule : Bool :=
      match entry with
      | .moduleEntry pkg => decide (pkg = "django".toList)
      | _                => false
    let out : Except ArgErr (List (List Char)) :=
      if isDjangoModule then
        Except.ok (prefixArgs ++ (["-m".toList, "django".toList] ++ userArgs))
      else
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
