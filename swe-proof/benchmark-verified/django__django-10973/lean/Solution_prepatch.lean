import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Both observable outputs —
-- the client command-line vector and the password handed to the child process —
-- are produced by literal-driven list assembly and a single conditional, so they
-- are modeled concretely rather than abstracted behind an axiom. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No shared functional helper is required; the postcondition states the two
-- output components structurally in terms of the inputs.
-- pure-end

-- post-conditions-start
/-- The shell invocation is described by two components.

The first is the argument vector for the client program: it always begins with
the client executable name, then — for each of the user, host, and port
connection parameters that is non-empty — appends that parameter preceded by its
corresponding option flag, in that exact order, and finally appends the database
name unconditionally.

The second is the password made available to the child process: it is the
connection password exactly when a password is supplied (non-empty), and is
absent otherwise. Both components are pinned to the inputs; nothing about the
argument vector depends on the password. -/
def problem_spec_dbShellCommand
    (host port dbname user passwd : String)
    (result : List String × Option String) : Prop :=
  result.1 =
      ["psql"]
        ++ (if user ≠ "" then ["-U", user] else [])
        ++ (if host ≠ "" then ["-h", host] else [])
        ++ (if port ≠ "" then ["-p", port] else [])
        ++ [dbname]
  ∧ result.2 = (if passwd = "" then none else some passwd)
-- post-conditions-end

-- impl-start
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  -- Pre-patch behavior: the supplied password is routed through a side channel
  -- (a temporary credentials file) rather than the child-process password slot,
  -- so the observed process password is always absent regardless of `passwd`.
  let passwordEnv : Option String := none
  return (args, passwordEnv)
-- impl-end

-- proof-start
theorem correct_dbShellCommand :
    ∀ (host port dbname user passwd : String),
    problem_spec_dbShellCommand host port dbname user passwd
      (implementation_dbShellCommand host port dbname user passwd) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
