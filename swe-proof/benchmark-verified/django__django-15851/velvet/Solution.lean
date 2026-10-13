import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Assembling the command-line argument vector reads
--  three already-available pieces — the leading segment built from the
--  connection settings, an optional database-name token, and the list of
--  caller-supplied extra arguments — and concatenates them. Concatenation and
--  the optional token are modeled directly (List `++` and `Option.toList`); no
--  unchanged callee's contract is consumed and nothing foreign is deep-modeled,
--  so there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The trailing token that names the target database, if one is named at all:
   a singleton holding that name when present, and nothing otherwise. This is
   the optional element that may or may not extend the argument vector. -/
def dbnameToken (dbname : Option String) : List String := dbname.toList

/- The complete command-line argument vector. It begins with the leading
   segment (the executable together with the connection options derived from the
   settings), is then extended by the caller-supplied extra arguments, and ends
   with the optional database-name token. The extra arguments therefore precede
   the database name in the vector; the database name, when present, is last. -/
def builtArgs (leading : List String) (dbname : Option String)
    (parameters : List String) : List String :=
  leading ++ parameters ++ dbnameToken dbname
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the command-line argument vector for invoking the database shell.

   `leading` is the leading segment already built from the connection settings
   (the executable name followed by whatever connection-option flags the
   settings call for); it is read-only here — this step neither inspects nor
   rewrites it, only builds upon it. `dbname` is the optional name of the target
   database: present as `some` when a database is named, `none` when none is.
   `parameters` are the extra arguments the caller passes through to the shell.

   The assembled vector places the caller-supplied extra arguments AFTER the
   leading segment and BEFORE the optional database-name token, so that the
   database name — when present — is the final element of the vector. -/
method buildShellArgs (leading : List String) (dbname : Option String)
    (parameters : List String) return (args : List String)
  ensures args = builtArgs leading dbname parameters
  do
    -- impl-start
    -- Start from the leading segment, append the caller's extra arguments,
    -- then append the optional database-name token last. The extra arguments
    -- are added before the database name, leaving the database name at the end.
    let mut args := leading
    args := args ++ parameters
    args := args ++ dbnameToken dbname
    return args
    -- impl-end

prove_correct buildShellArgs by
  loom_solve
  simp_all [builtArgs, dbnameToken]
