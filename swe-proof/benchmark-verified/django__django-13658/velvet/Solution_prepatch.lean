import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees, and no consumed axioms. The two operations a program
--  name is derived by — taking the final path component and the special-case
--  rename of a module entry point — are modeled DEEPLY below (`basename`,
--  `progNameOf`), as concrete code. Their equality to the corresponding real
--  callees is an A-reference validated by axiom_check.py (G-AX), not a contract
--  the proof assumes. Nothing here is consumed by `prove_correct`.)
-- axioms-end

-- pure-start
/- The final component of a filesystem-style path: the longest suffix that
   contains no path separator. (`a/b/c ↦ c`, `c ↦ c`, `a/b/ ↦ ""`, `/ ↦ ""`.)
   Deep model of the standard-library path-basename routine (POSIX separators);
   validated == the real callee by axiom_check.py (mapping.md §3.1). -/
def basename (path : List Char) : List Char :=
  (path.reverse.takeWhile (fun c => c ≠ '/')).reverse

/- The program name derived from an invocation argument vector: the final path
   component of its first entry, except that a bare module entry point is
   displayed under the package's friendly invocation name instead. This is the
   whole derivation the program name undergoes; validated == the real value the
   utility records by axiom_check.py (mapping.md §3.2). -/
def progNameOf (argv : List String) : List Char :=
  let b := basename (argv.headD "").toList
  if b = "__main__.py".toList then "python -m django".toList else b

@[grind] lemma progNameOf_def (argv : List String) :
    progNameOf argv =
      (let b := basename (argv.headD "").toList
       if b = "__main__.py".toList then "python -m django".toList else b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the program name presented in command-line usage messages while
   preprocessing the early options of an invocation.

   The invocation carries its own argument vector (`argv`); the process also
   exposes a global argument vector (`processArgv`). The program name MUST be
   derived from the invocation's own vector, so that an invocation supplying its
   own arguments is reported under its own program name regardless of what the
   process global happens to hold. Both vectors are read-only and the global
   vector does not influence the result at all.

   `require argv ≠ []`: the invocation vector has a first entry to name the
   program (the upstream resolution that supplies a default vector is unchanged
   and out of scope here). -/
method usageProgName
    (argv : List String) (processArgv : List String)
    return (out : List Char)
  require argv ≠ []
  ensures out = progNameOf argv
  do
    -- impl-start
    -- Pre-image skeleton: the program name is left to default to the process
    -- global argument vector rather than the invocation's own, so the option
    -- parser names the program after `processArgv` instead of `argv`. The
    -- frozen spec requires `progNameOf argv`, so prove_correct MUST fail.
    let out : List Char := progNameOf processArgv
    return out
    -- impl-end

prove_correct usageProgName by
  loom_solve
