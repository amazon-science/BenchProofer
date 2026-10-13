import Mathlib
-- imports-end

/-!
Assembling the invocation of an interactive command-line client for a PostgreSQL
database from a mapping of connection parameters.

The invocation has two observable components:

* the **command-line argument vector** passed to the client executable, built
  from the connection's user, host, port and database name; and
* the **child-process environment**, into which the connection's secret and
  transport-security parameters are injected under the specific environment
  variable names the client library reads them from.

Each connection parameter is optional: a parameter is "supplied" exactly when its
string value is non-empty. A supplied user/host/port contributes its flag pair to
the argument vector; the database name is always appended last. A supplied
password and each supplied transport-security parameter (the security mode, the
trusted-authority certificate, the client certificate, and the client private
key) is injected into the environment under its corresponding library variable,
so the interactive client honors the same authentication and mutual transport
security the application's own connections use.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature or a consumed axiom here. Every
-- operation the modeled function performs is a primitive: reading an optional
-- string parameter (empty string = absent), a non-emptiness test, list
-- concatenation, and appending a (name, value) pair to the environment. These
-- are modeled as identical concrete ops (I) / a type refinement (R), so there is
-- no deeply-modeled outside callee (A-reference) and no consumed callee axiom
-- (A-consumed). The proof agent may add `_prop` axioms only if genuinely stuck.
-- (No outside callee is deeply modeled as an A-reference either.)
-- axioms-end

-- pure-start
/-- The connection parameters the invocation reads. Each is an optional string;
the empty string denotes an absent parameter (the mapping's default). -/
structure ConnParams where
  host        : String := ""
  port        : String := ""
  dbname      : String := ""
  user        : String := ""
  password    : String := ""
  sslmode     : String := ""
  sslrootcert : String := ""
  sslcert     : String := ""
  sslkey      : String := ""
  deriving Repr, DecidableEq

/-- The observable result: the command-line argument vector and the
environment entries (name/value pairs, in the order they are injected) the
invocation contributes for the child process. -/
structure ShellInvocation where
  args  : List String
  pgEnv : List (String × String)
  deriving Repr, DecidableEq

/-- Specification of the argument vector: start with the executable name, then
append the user/host/port flag pairs for each supplied parameter, then always
append the database name last. -/
def specArgs (cp : ConnParams) : List String :=
  let a0 : List String := ["psql"]
  let a1 := if cp.user ≠ "" then a0 ++ ["-U", cp.user] else a0
  let a2 := if cp.host ≠ "" then a1 ++ ["-h", cp.host] else a1
  let a3 := if cp.port ≠ "" then a2 ++ ["-p", cp.port] else a2
  a3 ++ [cp.dbname]

/-- Specification of the injected environment entries: for each supplied
parameter, in this listed order, the corresponding library variable is bound to
the parameter's value; an absent parameter contributes nothing. -/
def specPgEnv (cp : ConnParams) : List (String × String) :=
  let e0 : List (String × String) := []
  let e1 := if cp.password    ≠ "" then e0 ++ [("PGPASSWORD",    cp.password)]    else e0
  let e2 := if cp.sslmode     ≠ "" then e1 ++ [("PGSSLMODE",     cp.sslmode)]     else e1
  let e3 := if cp.sslrootcert ≠ "" then e2 ++ [("PGSSLROOTCERT", cp.sslrootcert)] else e2
  let e4 := if cp.sslcert     ≠ "" then e3 ++ [("PGSSLCERT",     cp.sslcert)]     else e3
  if cp.sslkey ≠ "" then e4 ++ [("PGSSLKEY", cp.sslkey)] else e4
-- pure-end

-- post-conditions-start
/-- The result's argument vector and injected environment are exactly those
determined by the supplied connection parameters: every component is pinned to
its input (frame discipline), so no parameter is dropped and no extraneous
entry is introduced. -/
def problem_spec_runShell (cp : ConnParams) (result : ShellInvocation) : Prop :=
  result.args = specArgs cp ∧ result.pgEnv = specPgEnv cp
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) invocation: only the password is injected into the
environment; the four transport-security parameters are never propagated to
their library variables. -/
def implementation_runShell (cp : ConnParams) : ShellInvocation := Id.run do
  let mut args : List String := ["psql"]
  if cp.user ≠ "" then args := args ++ ["-U", cp.user]
  if cp.host ≠ "" then args := args ++ ["-h", cp.host]
  if cp.port ≠ "" then args := args ++ ["-p", cp.port]
  args := args ++ [cp.dbname]
  let mut pgEnv : List (String × String) := []
  if cp.password ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD", cp.password)]
  return { args := args, pgEnv := pgEnv }
-- impl-end

-- proof-start
theorem correct_runShell : ∀ cp : ConnParams,
    problem_spec_runShell cp (implementation_runShell cp) := by
  intro cp
  refine ⟨?_, ?_⟩
  · simp [implementation_runShell, specArgs]
  · simp [implementation_runShell, specPgEnv]   -- UNCLOSABLE: impl drops the SSL env entries (G-DIFF)
-- proof-end
