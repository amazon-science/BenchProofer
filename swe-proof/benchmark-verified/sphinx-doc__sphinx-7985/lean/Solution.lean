import Mathlib
-- imports-end

/-!
Network-free classification of a single hyperlink reference.

A documentation hyperlink checker, before contacting any server, classifies a
reference string by inspecting only the string itself plus two purely local
observations. The classification yields one of a closed set of outcomes:

* references that the checker deliberately skips (empty, in-page anchors, and
  mail addresses) are reported as `.unchecked`;
* a reference that does NOT denote a web resource (it has no `http`/`https`
  prefix) is classified locally:
    - if it carries an explicit URI scheme of the shape "letters followed by
      `://`" (e.g. a transfer scheme other than the web ones), the checker has
      no way to inspect it and reports `.unchecked`;
    - otherwise it is treated as a path relative to the source tree: if that
      path is present the reference is reported as working; if the path is
      absent, it is reported as ignored when it matches one of the configured
      skip patterns, and as an unresolved/missing target when it matches none;
* a reference that DOES denote a web resource is handed to the (unchanged)
  network-resolution stage, whose outcome is taken as given here.

The reference is modeled per code point as `List Char`. The presence of the
relative path in the source tree and a match against the skip-pattern set are
each a single boolean observation. The outcome of the web-resolution stage is
likewise taken as a given status value.
-/

-- axioms-start
-- No unchanged callee is consumed as a proof axiom. The local-path presence
-- check and the skip-pattern match are abstracted to the boolean observations
-- `localFileExists` / `ignoreMatch` (consumed directly by the impl); the
-- explicit-scheme test is modeled deeply below (`hasUriScheme`), validated
-- equal to the real matcher by G-AX (A-reference); the web-resolution stage is
-- abstracted to its observed status `httpResult` and frame-pinned.
-- axioms-end

-- pure-start
/-- The classification outcome of a hyperlink reference. -/
inductive LinkStatus
  | unchecked
  | working
  | broken
  | ignored
  | localLink
  | redirected
deriving DecidableEq, Repr

/-- Whether a character is a lowercase ASCII letter. -/
def isLower (c : Char) : Bool := decide ('a' ≤ c ∧ c ≤ 'z')

/-- A reference the checker deliberately skips by prefix: an in-page anchor or a
mail address. -/
def startsWithHashMailto (uri : List Char) : Bool :=
  ['#'].isPrefixOf uri || "mailto:".toList.isPrefixOf uri

/-- A reference that denotes a web resource. -/
def startsWithHttp (uri : List Char) : Bool :=
  "http:".toList.isPrefixOf uri || "https:".toList.isPrefixOf uri

/-- Whether the reference begins with an explicit URI scheme of the shape
"one-or-more lowercase letters immediately followed by `://`". The leading
lowercase run is maximal, so the only candidate is the maximal lowercase prefix
followed directly by `://`. -/
def hasUriScheme (uri : List Char) : Bool :=
  let run := uri.takeWhile isLower
  !run.isEmpty && "://".toList.isPrefixOf (uri.dropWhile isLower)
-- pure-end

-- post-conditions-start
/-- Specification of the network-free classification.

`localFileExists` is whether the reference, taken as a source-relative path, is
present; `ignoreMatch` is whether it matches a configured skip pattern;
`httpResult` is the outcome the web-resolution stage would report. Every branch
pins the result completely (frame discipline). -/
def problem_spec_checkLink
    (uri : List Char) (localFileExists ignoreMatch : Bool) (httpResult : LinkStatus)
    (result : LinkStatus) : Prop :=
  if uri.isEmpty || startsWithHashMailto uri then
    result = LinkStatus.unchecked
  else if !startsWithHttp uri then
    if hasUriScheme uri then
      result = LinkStatus.unchecked
    else if localFileExists then
      result = LinkStatus.working
    else if ignoreMatch then
      result = LinkStatus.ignored
    else
      result = LinkStatus.broken
  else
    result = httpResult
-- post-conditions-end

-- impl-start
def implementation_checkLink
    (uri : List Char) (localFileExists ignoreMatch : Bool)
    (httpResult : LinkStatus) : LinkStatus := Id.run do
  if uri.isEmpty || startsWithHashMailto uri then
    return LinkStatus.unchecked
  if !startsWithHttp uri then
    if hasUriScheme uri then
      return LinkStatus.unchecked
    else
      if localFileExists then
        return LinkStatus.working
      else
        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.broken
  return httpResult
-- impl-end

-- proof-start
theorem correct_checkLink :
    ∀ (uri : List Char) (localFileExists ignoreMatch : Bool) (httpResult : LinkStatus),
      problem_spec_checkLink uri localFileExists ignoreMatch httpResult
        (implementation_checkLink uri localFileExists ignoreMatch httpResult) := by
  intro uri localFileExists ignoreMatch httpResult
  unfold problem_spec_checkLink implementation_checkLink
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · rfl
  · split <;> rename_i h2
    · split <;> rename_i h3
      · rfl
      · split <;> rename_i h4
        · rfl
        · split <;> rfl
    · rfl
-- proof-end
