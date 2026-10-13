import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of the
--  interpreter path, the warning-option list, the runtime-implementation flag, the
--  list of runtime X-options, and the trailing program arguments. Each input is read
--  directly; nothing about how the relaunched interpreter is subsequently spawned is
--  consulted, so no callee contract is assumed. Every step is an R/I refinement,
--  validated against the real construction by conformance_check.py (G-CONF). See
--  refinement.md §C.)
-- axioms-end

-- pure-start
/- One runtime X-option's value. A bare option (supplied as `-Xkey`) carries no
   value (`bare`); a keyed option (supplied as `-Xkey=value`) carries its value
   string (`eq value`). This is the two shapes a runtime X-option can take. -/
inductive XVal where
  | bare
  | eq (value : List Char)
  deriving DecidableEq

/- The command-line flag a single warning option expands to: the `-W` prefix
   followed by the option text (the pre-existing warning-option forwarding, kept
   verbatim and unchanged). -/
def warnFlag (o : List Char) : List Char := "-W".toList ++ o

/- The command-line flag a single runtime X-option expands to. A bare option
   becomes `-Xkey`; a keyed option becomes `-Xkey=value`. This is the per-option
   serialization the construction applies to every X-option in order. -/
def xFlag (kv : List Char × XVal) : List Char :=
  match kv.2 with
  | XVal.bare    => "-X".toList ++ kv.1
  | XVal.eq value => "-X".toList ++ kv.1 ++ "=".toList ++ value

/- The full argument vector used to relaunch the interpreter under the
   auto-reloader, given: the interpreter path (`executable`); the active warning
   options (`warnopts`); whether the running interpreter is the CPython
   implementation (`isCpython`); the runtime X-options in their configured order
   (`xopts`); and the trailing program arguments (`argv`).

   The vector is the interpreter path, followed by one `-W` flag per warning
   option, followed — only on the CPython implementation — by one `-X` flag per
   configured X-option (in order, each serialized by `xFlag`), followed by the
   trailing program arguments. Off CPython the X-options contribute nothing. -/
def relaunchArgvSpec (executable : List Char) (warnopts : List (List Char))
    (isCpython : Bool) (xopts : List (List Char × XVal))
    (argv : List (List Char)) : List (List Char) :=
  [executable]
    ++ warnopts.map warnFlag
    ++ (if isCpython then xopts.map xFlag else [])
    ++ argv
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the argument vector the auto-reloader uses to relaunch the
   interpreter. The vector begins with the interpreter path and the active warning
   options (each as a `-W` flag), and ends with the program's trailing arguments.

   Desired behaviour: on the CPython implementation, every configured runtime
   X-option must also be forwarded to the relaunched interpreter — each as a `-X`
   flag, in configured order, serialized as `-Xkey` when it carries no value and as
   `-Xkey=value` when it does — placed after the warning options and before the
   trailing arguments. On a non-CPython implementation the X-options are not
   forwarded.

   All inputs are read-only (none `mut`): the construction reads them and emits the
   vector, mutating no input (directive 5). Option/argument text is modeled as
   `List Char`; the vector is a `List (List Char)` of argument strings
   (mapping.md §2). -/
method relaunchArgv (executable : List Char) (warnopts : List (List Char))
    (isCpython : Bool) (xopts : List (List Char × XVal))
    (argv : List (List Char)) return (out : List (List Char))
  ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
  do
    -- impl-start
    -- Start with the interpreter path; append one -W flag per warning option;
    -- then, only on CPython, append one -X flag per configured X-option (in
    -- order); finally append the trailing program arguments.
    let mut args : List (List Char) := [executable]
    args := args ++ warnopts.map warnFlag
    if isCpython then
      args := args ++ xopts.map xFlag
    args := args ++ argv
    return args
    -- impl-end

prove_correct relaunchArgv by
  loom_solve <;>
    simp_all [relaunchArgvSpec, List.append_assoc]
