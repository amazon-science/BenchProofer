import Mathlib
-- imports-end

/-!
Walking every page of a paginated collection, in order.

A paginated collection is described by four data:

  * the underlying list of items being paged over;
  * how many items make up a full page;
  * how many trailing items may be absorbed into the final page instead of
    spilling onto a page of their own (the orphan allowance);
  * whether an empty collection still presents a single (empty) page.

From these the collection exposes a 1-based numbering of its pages and, for each
page number, the contiguous slice of items shown on that page. Walking the
collection produces, in increasing page-number order, the slice of items
belonging to each page — i.e. exactly the same sequence of page contents one
would obtain by asking for each page number in turn.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The page count, the
-- 1-based page numbering, and the per-page slice are each total, pure functions
-- of the four input data (a length/arithmetic computation and a list slice), so
-- they are modeled directly below rather than abstracted behind an `opaque`
-- contract. Hence no `opaque`/`axiom` callee declaration is required.
-- axioms-end

-- pure-start
/-- The number of pages for a collection of `count` items shown `perPage` at a
time, allowing `orphans` trailing items to be folded into the final page.
`allowEmpty = false` collapses an empty collection to zero pages; otherwise an
empty collection still has one (empty) page. For `perPage ≥ 1` this is the
ceiling of `max 1 (count - orphans)` divided by `perPage`. -/
def pageCount (count perPage orphans : Nat) (allowEmpty : Bool) : Nat :=
  if count = 0 ∧ allowEmpty = false then 0
  else (max 1 (count - orphans) + perPage - 1) / perPage

/-- The 1-based list of page numbers, `[1, 2, …, pageCount]`. -/
def pageNumbers (count perPage orphans : Nat) (allowEmpty : Bool) : List Nat :=
  List.range' 1 (pageCount count perPage orphans allowEmpty)

/-- The contiguous slice of items shown on page `n` (1-based). The window starts
at `(n-1)*perPage` and spans `perPage` items, except that a window whose end is
within `orphans` of the collection's end is extended to absorb those trailing
items. -/
def pageSlice {α : Type} (objectList : List α) (perPage orphans n : Nat) : List α :=
  let count := objectList.length
  let bottom := (n - 1) * perPage
  let top := bottom + perPage
  let top := if top + orphans ≥ count then count else top
  (objectList.drop bottom).take (top - bottom)
-- pure-end

-- post-conditions-start
/-- Walking the collection yields, in increasing page-number order, the slice of
items on each page: the result is exactly the list obtained by mapping the
per-page slice over every page number `[1, …, pageCount]`. This pins the result
fully — its length is the page count and its `k`-th entry is the slice for page
`k+1` — so no output component is left free. -/
def problem_spec_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
    (result : List (List α)) : Prop :=
  result =
    (pageNumbers objectList.length perPage orphans allowEmpty).map
      (fun n => pageSlice objectList perPage orphans n)
-- post-conditions-end

-- impl-start
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) := Id.run do
  -- Pre-fix skeleton: the collection exposed no iteration protocol, so walking
  -- it surfaced no pages at all.
  let mut pages : List (List α) := []
  return pages
-- impl-end

-- proof-start
theorem correct_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
    (hperPage : 1 ≤ perPage) :
    problem_spec_paginatorPages objectList perPage orphans allowEmpty
      (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
  sorry
-- proof-end
