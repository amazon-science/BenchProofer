import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Each modeled function is a changed function whose new
--  behaviour is a single binary combination of its already-forced operands,
--  modeled deeply and directly. The only callee involved is the unchanged
--  forcing step that yields the underlying value; it is represented by the input
--  already holding that value — an R-refinement (mapping.md §2), not an axiom.)
-- axioms-end

-- pure-start
/- The two possible results of combining a deferred value with another value
   under binary addition: either the combination succeeds and yields a value, or
   the combination is rejected. A correct deferred value never rejects a
   combination its underlying value would accept, so the success constructor is
   the only outcome the contracts below permit. -/
inductive AddOutcome where
  | unsupported
deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A deferred character-sequence value standing on the LEFT of a binary addition.
   Once its underlying sequence is in hand (`forced`), combining it with the
   other operand must produce the underlying sequence followed by the other
   operand — the very same sequence that combining two ordinary character
   sequences in this order would produce — and must NOT be rejected. Operand
   order is significant for character sequences, so `forced` precedes `other`.
   Both operands are read-only (not `mut`); nothing is mutated (directive 5).
   The result is reported as a success carrying the combined sequence. -/
method deferredConcatLeft (forced : List Char) (other : List Char)
    return (out : Except AddOutcome (List Char))
  ensures out = Except.ok (forced ++ other)
  do
    -- impl-start
    return Except.ok (forced ++ other)
    -- impl-end

prove_correct deferredConcatLeft by
  loom_solve

/- A deferred character-sequence value standing on the RIGHT of a binary
   addition. Once its underlying sequence is in hand (`forced`), combining it
   with the other (left) operand must produce the other operand followed by the
   underlying sequence — preserving the left-to-right operand order — and must
   NOT be rejected, even when the left operand cannot by itself combine with a
   deferred value. This right-operand case is what lets an ordinary value on the
   left be joined to a deferred value on the right. Both operands are read-only
   (not `mut`); nothing is mutated (directive 5). -/
method deferredConcatRight (forced : List Char) (other : List Char)
    return (out : Except AddOutcome (List Char))
  ensures out = Except.ok (other ++ forced)
  do
    -- impl-start
    return Except.ok (other ++ forced)
    -- impl-end

prove_correct deferredConcatRight by
  loom_solve

/- A deferred numeric value standing on the LEFT of a binary addition. Once its
   underlying number is in hand (`forced`), combining it with the other operand
   must produce their numeric sum and must NOT be rejected. Both operands are
   read-only (not `mut`); nothing is mutated (directive 5). The result is a
   success carrying the sum. -/
method deferredSumLeft (forced : Int) (other : Int)
    return (out : Except AddOutcome Int)
  ensures out = Except.ok (forced + other)
  do
    -- impl-start
    return Except.ok (forced + other)
    -- impl-end

prove_correct deferredSumLeft by
  loom_solve

/- A deferred numeric value standing on the RIGHT of a binary addition. Once its
   underlying number is in hand (`forced`), combining it with the other (left)
   operand must produce their numeric sum and must NOT be rejected, even when the
   left operand is itself a deferred value. Both operands are read-only (not
   `mut`); nothing is mutated (directive 5). -/
method deferredSumRight (forced : Int) (other : Int)
    return (out : Except AddOutcome Int)
  ensures out = Except.ok (other + forced)
  do
    -- impl-start
    return Except.ok (other + forced)
    -- impl-end

prove_correct deferredSumRight by
  loom_solve
