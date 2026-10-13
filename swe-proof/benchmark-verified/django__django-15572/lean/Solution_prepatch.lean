import Mathlib
-- imports-end

/-!
Collect the set of directory paths that the template watcher should observe.

Two sources contribute directory entries: a list of configured directories, and
a list of loader-provided directories. Each entry is normalized to an absolute
path. Loader entries that point inside the framework's own tree are excluded.
A directory entry that is empty contributes nothing. The collected paths form a
set (membership only; order and repetition are irrelevant).
-/

-- axioms-start
-- Two unchanged path-handling callees, modeled as universally-quantified
-- parameters (the contract holds for ANY such function, so the proof consumes
-- no property of either):
--   * `resolveDir`      : normalize a directory entry to an absolute path.
--   * `isFrameworkPath` : true when a path lies inside the framework's own tree.
-- No `_prop` axiom is required (both callees are passthrough parameters).
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- A normalized path `p` belongs to the collected set exactly when it is the
normalization of some non-empty configured directory, or of some non-empty
loader directory that is not inside the framework tree. Membership is the only
observable (a set), so the predicate characterizes `result` up to order and
duplication. -/
def problem_spec_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) (result : List String) : Prop :=
  ∀ p : String,
    p ∈ result ↔
      ((∃ d ∈ dirs, d ≠ "" ∧ resolveDir d = p) ∨
       (∃ d ∈ loaderDirs, d ≠ "" ∧ isFrameworkPath d = false ∧ resolveDir d = p))
-- post-conditions-end

-- impl-start
def implementation_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) : List String := Id.run do
  let mut items : List String := []
  for dir in dirs do
    items := items ++ [resolveDir dir]
  for directory in loaderDirs do
    if isFrameworkPath directory = false then
      items := items ++ [resolveDir directory]
  return items
-- impl-end

-- proof-start
-- Prepatch (pre-fix) skeleton: the empty-directory guard is absent at both
-- collection sites, so an empty configured/loader entry is normalized and
-- enters the result. The gold proof carried here by the proof agent cannot
-- close against this impl — the spec's membership characterization excludes
-- normalizations of empty entries, which this impl produces (G-DIFF).
theorem correct_collectTemplateDirs :
    ∀ (resolveDir : String → String) (isFrameworkPath : String → Bool)
      (dirs loaderDirs : List String),
      problem_spec_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
        (implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs) := by
  sorry
-- proof-end
