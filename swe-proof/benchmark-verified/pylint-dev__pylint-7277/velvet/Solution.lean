import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two values this routine consults from its
--  environment — the current working directory and the process search-path
--  environment string — are produced by UNCHANGED library lookups whose results
--  are observed here only as the read-only free inputs `cwd` and `envPath`. The
--  spec makes no behavioural claim about those lookups and holds for EVERY value
--  they could return, so there is nothing to validate against a real callee,
--  hence no G-AX. The behaviour under spec — which leading entries of the search
--  path are dropped — is modeled DEEPLY in the `pure`/`impl` regions, with no
--  outside contract consumed. See mapping.md §3 / refinement.md §C.)
-- axioms-end

-- pure-start
/- The search path is a sequence of location strings; the first is the entry
   that the runtime conventionally inserts for the invocation context. -/

/- Drop the leading entry only when it denotes the current execution directory.
   A leading entry denotes the current directory exactly when it is the empty
   string, the single-dot string, or the textual current-directory value `cwd`;
   in every other case the leading entry is a genuine, caller-supplied location
   and must be preserved. (This is the whole point of the guard: a leading entry
   that is some other location is left in place.) -/
def afterFirst (path : List String) (cwd : String) : List String :=
  if path.headD "" = "" ∨ path.headD "" = "." ∨ path.headD "" = cwd then path.tail
  else path

/- The sanitized search path. Starting from `afterFirst` (the conditional drop of
   the current-directory leading entry), a further current-directory entry is
   removed depending on the shape of the search-path environment string:

   * if it begins with the separator `:` — and is not exactly a single
     current-directory entry written as `:<cwd>` or `:.` — the new leading entry
     is itself dropped;
   * otherwise, if it ends with the separator `:` — and is not exactly a single
     current-directory entry written as `<cwd>:` or `.:` — the entry in the
     second position is dropped instead;
   * otherwise nothing further is removed.

   These two cases are mutually exclusive (an else-branch), so at most one extra
   entry is removed. Grounded entirely in the three inputs (directive 8). -/
def sanitizedPath (path : List String) (cwd : String) (envPath : String) : List String :=
  let p1 := afterFirst path cwd
  if envPath.startsWith ":" ∧ envPath ≠ (":" ++ cwd) ∧ envPath ≠ ":." then
    p1.eraseIdx 0
  else if envPath.endsWith ":" ∧ envPath ≠ (cwd ++ ":") ∧ envPath ≠ ".:" then
    p1.eraseIdx 1
  else
    p1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Sanitize the runtime search path before module execution.

   `path` is the search path: a non-empty sequence of location strings, the first
   of which is the entry conventionally inserted for the invocation context.
   `cwd` is the textual current-directory value, and `envPath` is the search-path
   environment string; both are read-only free inputs (the results of unchanged
   environment lookups), and none of `path`/`cwd`/`envPath` is `mut` — the routine
   reads them and returns a fresh sequence, mutating nothing it is handed
   (directive 5).

   Desired behaviour: drop the leading entry ONLY when it denotes the current
   execution directory (empty string, single dot, or `cwd`) — a leading entry
   naming some other location must survive — and then drop a further
   current-directory entry according to whether the search-path environment
   string carries a leading or trailing separator, per `sanitizedPath`. -/
method sanitizePath (path : List String) (cwd : String) (envPath : String)
    return (out : List String)
  require path ≠ []
  ensures out = sanitizedPath path cwd envPath
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct sanitizePath by
  -- proof elided — supplied by the consumer
