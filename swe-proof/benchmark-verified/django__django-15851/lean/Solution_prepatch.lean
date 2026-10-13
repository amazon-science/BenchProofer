import Mathlib
-- imports-end

/-!
Assembling the command-line argument vector for an interactive database shell.

A database shell is launched by handing a separate client program a vector of
command-line arguments. The vector is built up in a set order:

  * the client program name (always first);
  * connection options derived from the connection settings — the user, the
    host, and the port — each emitted as a flag followed by its value, and only
    when that setting carries a value;
  * any extra free-form parameters the caller supplied; and
  * the database name, when one is available.

The client program requires every option to appear *before* the database name on
the command line; once the database name is seen, trailing tokens are treated as
extra positional arguments and ignored. The caller-supplied parameters are
options in this sense, so they must be placed ahead of the database name in the
vector.

Connection components are optional: a user, host, port, or database name that
carries no value contributes nothing to the vector. The extra parameters are a
(possibly empty) sequence and are always contributed in their given order.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The function
-- reads its connection settings at the I/O boundary; those reads (and the
-- presence/absence "truthiness" of each optional setting) are abstracted into
-- the optional-string inputs. The argument vector is then assembled structurally
-- by list concatenation, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The contribution of an optional flagged connection option to the argument
vector: a setting that carries a value `x` contributes the flag followed by its
value (`[flag, x]`); a setting that carries no value contributes nothing. -/
def optFlag (flag : String) (v : Option String) : List String :=
  match v with
  | none => []
  | some x => [flag, x]
-- pure-end

-- post-conditions-start
/-- The argument vector is exactly, in order: the program name; the user, host,
and port options (each present only when its setting carries a value); the
caller-supplied parameters; and finally the database name (present only when it
carries a value). The extra parameters precede the database name, and every
component is pinned to its input, so the entire vector is determined by the
settings. -/
def problem_spec_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    (result : List String) : Prop :=
  result =
    [executable]
      ++ optFlag "-U" user
      ++ optFlag "-h" host
      ++ optFlag "-p" port
      ++ parameters
      ++ dbname.toList
-- post-conditions-end

-- impl-start
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  if let some d := dbname then
    args := args ++ [d]
  args := args ++ parameters
  return args
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: the database name is appended BEFORE the caller-supplied
-- parameters, so whenever a database name is present and the parameter list is
-- non-empty the assembled vector orders `[..., dbname] ++ parameters`, whereas
-- the specification requires `parameters ++ [dbname]` — the two differ, and the
-- proof does not hold.
theorem correct_shellArgs :
    ∀ (executable : String) (user host port dbname : Option String)
      (parameters : List String),
      problem_spec_shellArgs executable user host port dbname parameters
        (implementation_shellArgs executable user host port dbname parameters) := by
  sorry
-- proof-end
