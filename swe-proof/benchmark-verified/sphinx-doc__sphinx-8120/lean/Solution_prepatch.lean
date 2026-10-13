import Mathlib
-- imports-end

/-!
Assembling the ordered list of directories in which a resource loader will look
for override files.

The assembly is given:

  * a list of caller-supplied directories, in the order the caller provided
    them;
  * a single built-in (bundled) directory shipped with the tool.

The loader that consumes this list walks it front-to-back, and an entry found
earlier takes precedence over one found later. The desired ordering of the
assembled list is therefore:

  * a leading system-default sentinel (written as the absent value), so the
    host system's own location is consulted first;
  * then every caller-supplied directory, in the caller's order;
  * then the single built-in directory, last.

In particular each caller-supplied directory appears ahead of the built-in
directory, so a caller's own files take precedence over the bundled ones; and
no directory is dropped, duplicated, or reordered relative to its group.
-/

-- axioms-start
-- No unchanged outside callee is consumed: the caller-supplied directories and
-- the built-in directory enter as plain data, and the only operation performed
-- is the construction of the ordered search list (a leading sentinel, the
-- caller's directories, then the built-in directory). The downstream loader that
-- interprets list order as precedence is unchanged and is not invoked here, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The search list assembled from the caller-supplied directories and the single
built-in directory: a leading system-default sentinel (`none`), then the
caller's directories in order (each a present value), then the built-in
directory last. -/
def assembleSearchDirs (userDirs : List String) (bundledDir : String) :
    List (Option String) :=
  none :: (userDirs.map some ++ [some bundledDir])
-- pure-end

-- post-conditions-start
/-- The assembled search list is fully pinned to the inputs:

  * its head is the system-default sentinel `none`;
  * the remainder is exactly the caller-supplied directories (each made present)
    in their given order, followed by the single built-in directory;

so every caller-supplied directory precedes the built-in directory, and the list
is determined for every input (no component is left free). -/
def problem_spec_searchDirs
    (userDirs : List String) (bundledDir : String)
    (result : List (Option String)) : Prop :=
  result = assembleSearchDirs userDirs bundledDir
-- post-conditions-end

-- impl-start
def implementation_searchDirs
    (userDirs : List String) (bundledDir : String) : List (Option String) :=
  Id.run do
    let mut searchDirs : List (Option String) := [none, some bundledDir]
    searchDirs := searchDirs ++ userDirs.map some
    return searchDirs
-- impl-end

-- proof-start
theorem correct_searchDirs :
    ∀ (userDirs : List String) (bundledDir : String),
      problem_spec_searchDirs userDirs bundledDir
        (implementation_searchDirs userDirs bundledDir) := by
  intro userDirs bundledDir
  unfold problem_spec_searchDirs implementation_searchDirs assembleSearchDirs
  simp only [Id.run, pure, List.nil_append, List.cons_append]
-- proof-end
