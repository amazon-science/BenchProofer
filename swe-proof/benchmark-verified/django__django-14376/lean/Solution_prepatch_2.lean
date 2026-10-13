import Mathlib
-- imports-end

/-!
Selecting connection identifiers for a MySQL-style database client.

Two small, independent pieces of behavior are specified here.

## 1. The trailing database-name argument of the shell command

When a database shell is launched, its command-line argument vector ends with the
database name (when one is available). The database name to use is chosen from
several possible sources, in a definite order of precedence:

  * a primary option, if that option key is present in the connection options;
  * otherwise a fallback option, if that key is present;
  * otherwise the database name configured on the connection itself.

Crucially, "present" means the option key is supplied at all — an option supplied
with an *empty* value is still chosen (it short-circuits the lower-precedence
sources), and an empty chosen value contributes no trailing argument. The
database name is appended only when the chosen value is non-empty.

## 2. The connection-parameter mapping for name and password

When connection parameters are assembled as a key→value mapping for the database
driver, the configured database name (when non-empty) is carried under the key
`"database"`, and the configured password (when non-empty) under the key
`"password"`. Each entry is contributed only when its underlying setting carries
a non-empty value.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by either specification. Both pieces of
-- behavior are modeled DEEPLY and structurally: the database-name choice is a
-- precedence selection among optional sources (option-key presence is the
-- `Option`, value emptiness the truthiness test), and the connection-parameter
-- mapping is built by list construction of key/value pairs. No `opaque`/`axiom`
-- callee contract is needed, so `axiom_check.py` is a skip stub and G-AX skips.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required; both selections are expressed inline.)
-- pure-end

-- post-conditions-start
/-- The trailing database-name argument. The chosen value is the primary option
when its key is present (`optDatabase = some _`), otherwise the fallback option
when present (`optDb = some _`), otherwise the configured `name`. The result is
that chosen value when it is non-empty, and nothing otherwise. Note an option
supplied with an empty value (`some ""`) is still chosen and, being empty,
contributes nothing — it does not fall through to a lower-precedence source. -/
def problem_spec_dbArg
    (optDatabase optDb : Option String) (name : String)
    (result : Option String) : Prop :=
  result =
    (let chosen := optDatabase.getD (optDb.getD name)
     if chosen = "" then none else some chosen)
-- post-conditions-end

-- impl-start
def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD name)
  if database ≠ "" then
    return some database
  return none
-- impl-end

-- proof-start
theorem correct_dbArg :
    ∀ (optDatabase optDb : Option String) (name : String),
      problem_spec_dbArg optDatabase optDb name
        (implementation_dbArg optDatabase optDb name) := by
  sorry
-- proof-end

-- post-conditions-start
/-- The connection-parameter mapping entries contributed by the database name and
the password. The configured database name, when non-empty (`name = some n` with
`n ≠ ""`), is carried under the key `"database"`; the configured password, when
non-empty (`password = some p` with `p ≠ ""`), under the key `"password"`. Each
entry is present exactly when its underlying setting carries a non-empty value
(an absent or empty setting contributes nothing), in this order. -/
def problem_spec_connParams
    (name password : Option String)
    (result : List (String × String)) : Prop :=
  result =
    (match name with | some n => if n = "" then [] else [("database", n)] | none => [])
      ++ (match password with | some p => if p = "" then [] else [("password", p)] | none => [])
-- post-conditions-end

-- impl-start
def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  -- PRE-PATCH (buggy): the database name and password are carried under the
  -- deprecated keys "db"/"passwd" instead of "database"/"password".
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("db", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("passwd", p)]
  return kwargs
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- buggy impl it cannot close: whenever the database name is present and non-empty
-- the spec requires the entry key "database" but this impl emits "db" (and
-- "passwd" vs "password" for the password) — the produced mapping differs.
theorem correct_connParams :
    ∀ (name password : Option String),
      problem_spec_connParams name password
        (implementation_connParams name password) := by
  sorry
-- proof-end

