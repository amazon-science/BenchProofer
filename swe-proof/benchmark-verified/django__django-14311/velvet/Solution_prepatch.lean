import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

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
    -- Pre-image skeleton: whenever a parent package name is present, the relaunch
    -- name is taken to be that parent package unconditionally — collapsing even a
    -- genuine deeper dotted module onto its parent. The frozen spec requires
    -- `moduleToReexec`, which keeps a non-package-entry module's own dotted name,
    -- so `prove_correct` MUST fail.
    let mut cmdline := leadingArgs
    let name : String :=
      if parentPackage ≠ "" then parentPackage else moduleName
    cmdline := cmdline ++ ["-m", name]
    cmdline := cmdline ++ trailingArgs
    return cmdline
    -- impl-end

prove_correct relaunchCommand by
  loom_solve
  simp_all [moduleToReexec]
