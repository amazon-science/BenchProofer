import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The two shapes the assembly of a per-class sparse coefficient layout can take:

     * `ok m` — a sparse matrix `m` was produced;
     * `error zeroDivision` — the layout could not be produced because the
       per-row stride that lays out the index pointers was zero, which makes the
       arithmetic that derives the pointer sequence ill-defined (a division by
       zero). The desired behavior must never end in this shape.

   This is exactly the success/failure distinction the public problem statement
   draws (a `ZeroDivisionError` versus an empty result). -/
inductive FitErr where
  | zeroDivision
  deriving DecidableEq

/- The observable content of a built sparse coefficient matrix (compressed-row
   form): how many stored entries it has, its per-element column-index sequence,
   its per-row index-pointer sequence, and its row/column dimensions. These are
   the only fields the surrounding computation and the consuming code read. -/
structure SparseCoef where
  dataLen : Nat
  indices : List Nat
  indptr  : List Nat
  rows    : Nat
  cols    : Nat
  deriving DecidableEq

/- Deep model of the unchanged standard array-range helper used to lay out the
   row index-pointers: from a count of rows `nClass` and a count of columns
   `nSV` it produces the evenly-strided pointer sequence `0, nSV, 2·nSV, …,
   nClass·nSV`. The stride is `(nSV·nClass) / nClass`, which is `0` exactly when
   `nSV = 0`; a zero stride leaves the range arithmetic ill-defined, modeled as
   `error zeroDivision`. This is a model of a library callee, NOT a consumed
   axiom — validated == the real range helper by axiom_check.py (G-AX);
   provenance in mapping.md §3. -/
def arangeIndptr (nSV nClass : Nat) : Except FitErr (List Nat) :=
  if nSV = 0 then Except.error FitErr.zeroDivision
  else Except.ok ((List.range (nClass + 1)).map (· * nSV))
-- axioms-end

-- pure-start
/- The per-element column-index sequence: the column indices `0 … nSV-1`
   repeated once per row (`nClass` copies, concatenated). Deep model of the
   unchanged tile-of-range construction; validated == the real construction by
   axiom_check.py (G-AX). -/
def tileRange (nSV nClass : Nat) : List Nat :=
  (List.replicate nClass (List.range nSV)).flatten

/- The degenerate result produced when there are no rows to lay out: an empty
   sparse container — no stored entries, no column indices, a single trivial
   row, zero columns. (The exact internals of an empty compressed-row container;
   confirmed == the real empty container by axiom_check.py, G-AX.) -/
def emptyResult : SparseCoef :=
  { dataLen := 0, indices := [], indptr := [0, 0], rows := 1, cols := 0 }

/- The result produced when there is at least one row: a compressed-row matrix
   carrying the `dataLen` stored values, the tiled column indices, the strided
   index-pointers, and the `nClass × nSV` shape. -/
def builtResult (nSV nClass dataLen : Nat) : SparseCoef :=
  { dataLen := dataLen,
    indices := tileRange nSV nClass,
    indptr  := (List.range (nClass + 1)).map (· * nSV),
    rows    := nClass,
    cols    := nSV }

/- The intended outcome of assembling the per-class sparse coefficient matrix:

     * when there are no rows (`nSV = 0`), the empty container is produced — the
       assembly succeeds and yields a matrix with no stored entries;
     * otherwise the strided compressed-row matrix is built.

   In neither case does the assembly end in the `zeroDivision` failure shape:
   the degenerate count of rows is handled before the strided arithmetic is
   reached. -/
def sparseFitSpec (nSV nClass dataLen : Nat) : Except FitErr SparseCoef :=
  if nSV = 0 then Except.ok emptyResult
  else Except.ok (builtResult nSV nClass dataLen)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the per-class sparse coefficient matrix from the count of support
   rows `nSV`, the count of classes `nClass` (at least one), and the number of
   stored coefficient values `dataLen`.

   Desired behavior: when there are no support rows the result must be the empty
   sparse container (`dataLen = 0`, no stored entries) rather than a failure;
   when there is at least one support row the strided compressed-row layout is
   built exactly as the per-class index-pointer arithmetic prescribes. The
   degenerate no-rows case is the missing behavior the public problem statement
   reports.

   `nSV`, `nClass`, `dataLen` are read-only counts: the assembly computes a
   result and mutates no input (directive 5). -/
method buildSparseCoef (nSV : Nat) (nClass : Nat) (dataLen : Nat)
    return (out : Except FitErr SparseCoef)
  require 1 ≤ nClass
  ensures out = sparseFitSpec nSV nClass dataLen
  do
    -- impl-start
    -- Pre-image skeleton: the index-pointer layout is consulted unconditionally,
    -- with no separate handling of the no-rows case. The strided arithmetic is
    -- reached even when there are zero rows, where it is ill-defined — so the
    -- assembly ends in the `zeroDivision` failure shape instead of yielding the
    -- empty container. The frozen spec requires the empty container at `nSV = 0`,
    -- so prove_correct MUST fail.
    let indices := tileRange nSV nClass
    let result : Except FitErr SparseCoef :=
      match arangeIndptr nSV nClass with
      | Except.ok indptr =>
          Except.ok { dataLen := dataLen, indices := indices,
                      indptr := indptr, rows := nClass, cols := nSV }
      | Except.error e => Except.error e
    return result
    -- impl-end

prove_correct buildSparseCoef by
  loom_solve
  simp_all [sparseFitSpec, arangeIndptr, builtResult]
