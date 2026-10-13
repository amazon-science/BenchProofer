import Mathlib
-- imports-end

/-!
Collecting the chunk sizes of a collection of array-like variables.

Each variable in the collection may be *chunked*: if so it exposes, for each of
its named dimensions, the block length along that dimension. `get_chunksizes`
walks the collection and builds a single mapping from dimension name to block
length:

* a variable that is not chunked contributes nothing;
* a chunked variable contributes one entry per dimension; if a dimension has
  already been recorded with a *different* block length the collection has
  inconsistent chunking and the whole operation is rejected;
* recording a dimension whose block length already agrees with the stored value
  leaves the mapping unchanged.

The resulting mapping lists dimensions in the order they were first encountered.

Crucially, deciding whether a variable is chunked is a question about the
variable's chunk metadata only: it must be answerable by inspecting that
metadata and must never force the variable's contents to be loaded into memory.
The outcome therefore depends solely on each variable's chunk metadata, and is
the same whether or not loading a variable's contents would succeed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- variable is chunked, and the per-dimension block lengths it then exposes, are
-- observable properties of the variable supplied directly as inputs; the
-- accumulation and the inconsistency rejection are modeled deeply over those
-- inputs. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched observable properties of one array-like variable.

* `hasChunks` — whether the variable is chunked (answerable from chunk metadata
  alone, without loading the variable's contents);
* `chunksizes` — when chunked, the per-dimension block lengths, as
  `(dimension name, block lengths)` pairs in dimension order;
* `isDuckArray` — whether the variable already holds an in-place array handle;
* `materializeRaises` — whether forcing the variable's contents into memory
  would fail (e.g. an unreachable backing store).

`isDuckArray` and `materializeRaises` describe what happens if the variable's
contents are loaded; a correct computation of the chunk-size mapping never needs
them, and the specification below is deliberately independent of both. -/
structure XVar where
  hasChunks : Bool
  chunksizes : List (String × List Nat)
  isDuckArray : Bool
  materializeRaises : Bool

/-- Record one `(dimension, block lengths)` entry into the accumulated mapping.
A new dimension is appended (preserving first-seen order); a dimension already
present with the *same* block lengths leaves the mapping unchanged; a dimension
present with *different* block lengths makes the collection inconsistent. -/
def insertChunk (acc : List (String × List Nat)) (p : String × List Nat) :
    Except Unit (List (String × List Nat)) :=
  match acc.lookup p.1 with
  | some c' => if c' = p.2 then .ok acc else .error ()
  | none    => .ok (acc ++ [p])

/-- Fold a single chunked variable's entries into the accumulator, rejecting on
the first inconsistency. -/
def mergePairs : List (String × List Nat) → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | acc, []      => .ok acc
  | acc, p :: ps =>
    match insertChunk acc p with
    | .error _ => .error ()
    | .ok acc' => mergePairs acc' ps

/-- The reference chunk-size mapping for a collection of variables, threaded
front-to-back. Non-chunked variables are skipped; chunked variables fold their
entries in, rejecting on the first inconsistency. Depends only on each
variable's chunk metadata (`hasChunks`, `chunksizes`). -/
def mergeVars : List XVar → List (String × List Nat) →
    Except Unit (List (String × List Nat))
  | [],      acc => .ok acc
  | v :: vs, acc =>
    if v.hasChunks then
      match mergePairs acc v.chunksizes with
      | .error _ => .error ()
      | .ok acc' => mergeVars vs acc'
    else mergeVars vs acc
-- pure-end

-- post-conditions-start
/-- The collected mapping is exactly the reference fold over the variables'
chunk metadata: each non-chunked variable contributes nothing, each chunked
variable contributes its per-dimension block lengths, inconsistent block lengths
for the same dimension are rejected, and dimensions appear in first-seen order.
The outcome is independent of whether loading any variable's contents would
succeed. -/
def problem_spec_getChunksizes (vars : List XVar)
    (result : Except Unit (List (String × List Nat))) : Prop :=
  result = mergeVars vars []
-- post-conditions-end

-- impl-start
def implementation_getChunksizes (vars : List XVar) :
    Except Unit (List (String × List Nat)) := Id.run do
  let mut chunks : List (String × List Nat) := []
  for v in vars do
    -- Pre-patch behavior: deciding whether a variable is chunked goes through the
    -- accessor that returns the variable's in-place contents, which for a variable
    -- without an in-place handle forces the whole array to be loaded into memory.
    -- When loading would fail (e.g. an unreachable backing store) the entire
    -- operation aborts — even though the variable contributes nothing to the
    -- chunk map. The chunked-ness verdict itself is unchanged.
    if !v.isDuckArray && v.materializeRaises then return .error ()
    if v.hasChunks then
      for p in v.chunksizes do
        match chunks.lookup p.1 with
        | some c' => if c' ≠ p.2 then return .error ()
        | none    => chunks := chunks ++ [p]
  return .ok chunks
-- impl-end

-- proof-start
theorem correct_getChunksizes : ∀ vars,
    problem_spec_getChunksizes vars (implementation_getChunksizes vars) := by
  sorry
-- proof-end

#print axioms correct_getChunksizes
