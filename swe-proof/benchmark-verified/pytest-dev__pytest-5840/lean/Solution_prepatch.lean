import Mathlib
-- imports-end

/-!
Deriving the de-duplication key for the canonical path of a loaded configuration
hook file.

A test runner caches a loaded hook module under a key derived from the file's
canonical (fully resolved, absolute) path, so the same file encountered by two
different routes is only loaded once. The key is computed by a single
transformation of the already-resolved path.

The transformation must PRESERVE the original letter case of the resolved path:
the key is the resolved path verbatim. It must NOT fold the path to lower case.
On case-insensitive (but case-preserving) file systems, folding the path to lower
case produces a key that no longer matches the path's true on-disk casing, which
in turn breaks deriving the module's qualified name from the path (the reported
failure: a path that "was converted to lower case", yielding an import error for
a package whose name contains upper-case characters).

The modeled value here is exactly that key-derivation step: given the canonical
resolved path (a sequence of characters), produce the cache key. The desired
behavior is the identity on the path — every character, including its letter
case, is retained.
-/

-- axioms-start
-- No unchanged callee contributes a property the proof consumes. The path
-- canonicalization (resolving symlinks / making absolute) happens before the
-- modeled step and is taken as the already-resolved input `resolved`; the only
-- modeled behavior is how the cache key is derived from that resolved path. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No shared helper is needed: the key derivation is the identity on the resolved
-- path, and the spec pins the result to the input directly.
-- pure-end

-- post-conditions-start
/-- The cache key for a loaded hook file is exactly its canonical resolved path,
character-for-character — the original letter case of the path is preserved, not
folded. -/
def problem_spec_cacheKey (resolved : List Char) (result : List Char) : Prop :=
  result = resolved
-- post-conditions-end

-- impl-start
def implementation_cacheKey (resolved : List Char) : List Char := Id.run do
  -- PRE-PATCH (buggy): the resolved path is folded to lower case before being
  -- used as the cache key, so the key loses the path's true on-disk letter case.
  let key := resolved.map Char.toLower
  return key
-- impl-end

-- proof-start
theorem correct_cacheKey :
    ∀ (resolved : List Char),
      problem_spec_cacheKey resolved (implementation_cacheKey resolved) := by
  intro resolved
  unfold problem_spec_cacheKey implementation_cacheKey
  rfl
-- proof-end
