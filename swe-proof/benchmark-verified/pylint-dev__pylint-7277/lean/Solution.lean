import Mathlib
-- imports-end

/-!
Pruning the working-directory entry from a module-import search-path list.

When a tool is launched as a Python module, the search-path list it inherits may
begin with an entry that denotes the current working directory — the empty
string `""`, the dot `"."`, or the literal working-directory path. Such an entry
must be stripped, because leaving the working directory on the search path lets
user code shadow standard-library or tool-internal modules of the same name.

This routine inspects the list together with two pieces of environment state — a
colon-separated environment path string and the working-directory path — and
removes entries as follows:

  * The very first entry is removed only when it actually denotes the working
    directory (it is `""`, `"."`, or the working-directory path). A first entry
    that names some other location is left in place.
  * Independently, the working directory may be carried implicitly by a leading
    or trailing colon in the environment path string. When the environment path
    string starts with a colon (and is neither just the working directory nor the
    dot prefixed by a colon), one further leading entry is removed. Otherwise,
    when it ends with a colon (and is neither the working directory nor the dot
    suffixed by a colon), the entry now sitting in second position is removed.

The leading-colon and trailing-colon cases are mutually exclusive, and the
environment-path adjustment is applied to the list as it stands after the first
adjustment. Every entry not selected by one of these rules is preserved in its
original relative order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The routine
-- reads two pieces of environment state (passed in as the inputs `pythonpath`
-- and `cwd`), performs prefix/suffix tests on the environment string, equality
-- tests against the working directory, and list-front removals. All are modeled
-- directly (`String.startsWith`/`endsWith`, `BEq`, `List.drop`/`take`), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The leading entry denotes the working directory: it is empty, the dot, or the
working-directory path itself. -/
def headIsCwd (path : List String) (cwd : String) : Bool :=
  let h := path.headD ""
  h == "" || h == "." || h == cwd

/-- The environment path string carries the working directory as an implicit
leading entry: it begins with a colon and is not exactly the working directory
or the dot prefixed by a colon. -/
def leadingColon (pythonpath cwd : String) : Bool :=
  pythonpath.startsWith ":" && pythonpath != (":" ++ cwd) && pythonpath != ":."

/-- The environment path string carries the working directory as an implicit
trailing entry: it ends with a colon and is not exactly the working directory or
the dot suffixed by a colon. -/
def trailingColon (pythonpath cwd : String) : Bool :=
  pythonpath.endsWith ":" && pythonpath != (cwd ++ ":") && pythonpath != ".:"
-- pure-end

-- post-conditions-start
/-- The pruned search-path list. Let `afterFirst` be the list after the
first-entry rule (the leading entry dropped exactly when it denotes the working
directory, otherwise the list unchanged). Then:

  * if the environment path string carries a leading-colon working directory, the
    result drops one further front entry of `afterFirst`;
  * otherwise, if it carries a trailing-colon working directory, the result
    removes the entry in second position of `afterFirst`;
  * otherwise the result is `afterFirst` unchanged.

The three environment-path cases are exhaustive and mutually exclusive, so the
result is fully determined by the inputs (directive 5 frame: every retained entry
is pinned to its input position). -/
def problem_spec_modifySysPath
    (path : List String) (pythonpath cwd : String) (result : List String) : Prop :=
  let afterFirst := if headIsCwd path cwd then path.drop 1 else path
  (leadingColon pythonpath cwd = true → result = afterFirst.drop 1) ∧
  (leadingColon pythonpath cwd = false ∧ trailingColon pythonpath cwd = true →
      result = afterFirst.take 1 ++ afterFirst.drop 2) ∧
  (leadingColon pythonpath cwd = false ∧ trailingColon pythonpath cwd = false →
      result = afterFirst)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
