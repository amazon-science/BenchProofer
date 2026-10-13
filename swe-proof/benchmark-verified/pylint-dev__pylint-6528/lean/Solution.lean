import Mathlib
-- imports-end

/-!
Recursively discovering the Python source files under a directory tree.

A directory tree is traversed top-down. The traversal is described by the
sequence of visited directories, each paired with the file names it directly
contains. A set of *ignore settings* says which directories (and the files
beneath them) must be excluded from the discovered set:

* a list of plain base names to skip (matched against the final path
  component);
* a list of patterns matched against the final path component;
* a list of patterns matched against the whole path.

A directory is *excluded* when its base name is one of the skipped names, or its
base name matches a base-name pattern, or its whole path matches a path pattern.
When a directory is excluded, neither it nor anything beneath it is discovered;
likewise everything beneath an already-recorded package directory is pruned.

For each directory that is reached and not excluded: if it directly contains an
`__init__.py` file it is itself recorded as a package (and its subtree pruned);
otherwise each of its directly-contained `.py` files is recorded by its full
path. The discovered list preserves traversal order.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- Whether a single pattern matches a string, under the standard library's
pattern-matching semantics (anchored at the start of the string). This is the
unchanged matching primitive; its result depends only on the pattern and the
string. -/
opaque regexMatch : String → String → Bool
-- axioms-end

-- pure-start
/-- Final component of a `/`-separated path (the base name). Mirrors taking the
text after the last separator; a trailing separator yields the empty component. -/
def baseName (s : String) : String := (s.splitOn "/").getLastD ""

/-- Join a directory path and a directly-contained file name (a name without
separators). Mirrors the standard path join: a separator is inserted unless the
directory path is empty or already ends with one. -/
def joinPath (root f : String) : String :=
  if root.isEmpty || root.endsWith "/" then root ++ f else root ++ "/" ++ f

/-- A string matches at least one pattern of a collection. Reuses the single
matching primitive for each pattern. -/
def matchesAny (element : String) (pats : List String) : Bool :=
  pats.any (fun p => regexMatch p element)

/-- A path is excluded by the ignore settings when its base name is one of the
listed names, or its base name matches a base-name pattern, or the whole path
matches a path pattern. -/
def ignoreDecision (element : String) (ignoreNames rePats pathPats : List String) : Bool :=
  ignoreNames.contains (baseName element)
    || matchesAny (baseName element) rePats
    || matchesAny element pathPats

/-- One traversal step over the running state `(pruned, acc)`: `pruned` is the
list of directory prefixes whose subtrees are pruned, `acc` is the discovered
paths so far. `entry` is a visited directory paired with its directly-contained
file names. -/
def scanStep (ignoreNames rePats pathPats : List String)
    (st : List String × List String) (entry : String × List String) :
    List String × List String :=
  let pruned := st.1
  let acc := st.2
  let root := entry.1
  let files := entry.2
  if pruned.any (fun s => root.startsWith s) then
    (pruned, acc)
  else if ignoreDecision root ignoreNames rePats pathPats then
    (pruned ++ [root], acc)
  else if files.contains "__init__.py" then
    (pruned ++ [root], acc ++ [root])
  else
    (pruned, acc ++ (files.filter (fun f => f.endsWith ".py")).map (fun f => joinPath root f))

/-- Discovered paths: fold the traversal steps over the visited directories,
starting from no pruned prefixes and an empty discovered list, and read off the
accumulated discoveries. -/
def scanFold (entries : List (String × List String))
    (ignoreNames rePats pathPats : List String) : List String :=
  (entries.foldl (scanStep ignoreNames rePats pathPats) ([], [])).2
-- pure-end

-- post-conditions-start
/-- The discovered list is exactly the traversal that, in order, prunes the
subtree of any excluded or already-recorded package directory, records a
package directory by its own path, and records every directly-contained `.py`
file of a non-package directory by its full path. -/
def problem_spec_scanTree (entries : List (String × List String))
    (ignoreNames rePats pathPats : List String) (result : List String) : Prop :=
  result = scanFold entries ignoreNames rePats pathPats
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end


-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
