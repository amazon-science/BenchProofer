import Mathlib
-- imports-end

-- axioms-start
-- Two UNCHANGED standard-library path callees the routine uses are kept as
-- opaque signatures so they appear in the executable impl; their meaning is
-- pinned by the refinement to the real callees (validated by G-AX / G-CONF).
-- `normalizePath` is the standard-library filesystem-path normalizer (collapses
-- redundant separators and `.`/`..` segments, dropping a leading `./`).
-- `baseNameOf` is the standard-library final-path-component extractor.
-- No `_prop` axiom is consumed by the proof; the proof agent may add one only
-- if stuck.
opaque normalizePath : String → String
opaque baseNameOf : String → String
-- axioms-end

-- pure-start
/-- A compiled match-pattern is modeled as the boolean matcher it induces
(`pattern.match(s)` ↦ a `String → Bool`). `anyMatch s pats` holds iff some
pattern in `pats` matches `s`. -/
def anyMatch (s : String) (patterns : List (String → Bool)) : Bool :=
  patterns.any (fun m => m s)
-- pure-end

-- post-conditions-start
/-- The decision whether to skip a path element. The element is taken in its
normalized form; the result is true exactly when its final component is listed
literally, or its final component matches one of the name patterns, or the
normalized element itself matches one of the path patterns. Every check is taken
against the normalized element — both the literal/name checks (via its final
component) and the whole-path check. -/
def problem_spec_isIgnoredFile
    (element : String) (ignoreList : List String)
    (ignoreListRe ignoreListPathsRe : List (String → Bool))
    (result : Bool) : Prop :=
  result =
    (ignoreList.contains (baseNameOf (normalizePath element))
      || anyMatch (baseNameOf (normalizePath element)) ignoreListRe
      || anyMatch (normalizePath element) ignoreListPathsRe)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
