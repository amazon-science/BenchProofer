import Mathlib
-- imports-end

/-!
Arranging a regular grid of sub-panels inside a figure with requested spacing
between them.

A figure is divided into `nrows × ncols` sub-panels of equal share. The caller
may request a horizontal spacing `wspace` and a vertical spacing `hspace`, each a
non-negative fraction of the average panel width/height, to be left as gaps
between adjacent panels. The panels together with the gaps exactly fill the unit
square of figure-fraction coordinates `[0,1] × [0,1]`.

For a requested spacing the layout is determined as follows. Along a direction
with `k` panels and spacing `s`, every panel has the same extent
`c = 1 / (k + s·(k-1))` and consecutive panels are separated by a gap `s·c`, so
panel `i` (counting from the left/no-gap edge) starts at `i·(c + s·c)` and ends a
panel-extent later. Vertically the rows are placed from the top downwards (row
`0` is the topmost). The result lists, for each panel, its rectangle
`(x0, y0, x1, y1)` — left, bottom, right, top — in figure-fraction coordinates,
so that varying the requested spacing visibly changes the panel rectangles.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the panel-rectangle
-- geometry (the per-direction equal-extent / proportional-gap tiling of the unit
-- interval) is spelled out concretely as closed-form arithmetic on the inputs, so
-- there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- A rectangle in figure-fraction coordinates: lower-left `(x0, y0)` and
upper-right `(x1, y1)`. -/
structure Rect where
  x0 : ℚ
  y0 : ℚ
  x1 : ℚ
  y1 : ℚ
deriving DecidableEq, Repr

/-- Build a rectangle from its four extents: left, bottom, right, top. -/
def Rect.ofExtents (left bottom right top : ℚ) : Rect := ⟨left, bottom, right, top⟩

/-- The common extent of a single panel along a direction holding `k` panels with
spacing `s`: `1 / (k + s·(k-1))`. -/
def panelExtent (k : Nat) (s : ℚ) : ℚ := 1 / ((k : ℚ) + s * ((k : ℚ) - 1))

/-- The gap left between two adjacent panels: `s` times the panel extent. -/
def panelGap (k : Nat) (s : ℚ) : ℚ := s * panelExtent k s

/-- Left edge of column `i` (`0`-based from the left): `i·(extent + gap)`. -/
def colLeft (ncols : Nat) (wspace : ℚ) (i : Nat) : ℚ :=
  (i : ℚ) * (panelExtent ncols wspace + panelGap ncols wspace)

/-- Right edge of column `i`: its left edge plus one panel extent. -/
def colRight (ncols : Nat) (wspace : ℚ) (i : Nat) : ℚ :=
  colLeft ncols wspace i + panelExtent ncols wspace

/-- Top edge of row `j` (`0`-based from the top): `1 - j·(extent + gap)`. -/
def rowTop (nrows : Nat) (hspace : ℚ) (j : Nat) : ℚ :=
  1 - (j : ℚ) * (panelExtent nrows hspace + panelGap nrows hspace)

/-- Bottom edge of row `j`: its top edge minus one panel extent. -/
def rowBottom (nrows : Nat) (hspace : ℚ) (j : Nat) : ℚ :=
  rowTop nrows hspace j - panelExtent nrows hspace

/-- The full grid of panel rectangles, row-major (row `0` topmost). -/
def gridRects (nrows ncols : Nat) (wspace hspace : ℚ) : List (List Rect) :=
  (List.range nrows).map (fun j =>
    (List.range ncols).map (fun i =>
      Rect.ofExtents (colLeft ncols wspace i) (rowBottom nrows hspace j)
                     (colRight ncols wspace i) (rowTop nrows hspace j)))
-- pure-end

-- post-conditions-start
/-- A grid of `nrows × ncols` panels with horizontal spacing `wspace` and vertical
spacing `hspace` lays out exactly the rectangles `gridRects`: each panel `(j, i)`
gets the rectangle whose left/right edges are column `i`'s edges and whose
bottom/top edges are row `j`'s edges, under the equal-extent / proportional-gap
tiling of the unit square. Pinning the whole grid leaves no panel rectangle
unconstrained — the spacing necessarily shifts and shrinks every panel. -/
def problem_spec_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ)
    (result : List (List Rect)) : Prop :=
  result = gridRects nrows ncols wspace hspace
-- post-conditions-end

-- impl-start
-- Faithful skeleton of the fix: first obtain the grid line positions
-- (lefts/rights/bottoms/tops) for the requested spacing, then walk the rows and
-- columns building, for each panel, the rectangle from those four extents
-- (mirrors the nested `zip` loop that calls `from_extents` per subfigure).
def implementation_subfigureGrid (nrows ncols : Nat) (wspace hspace : ℚ) :
    List (List Rect) := Id.run do
  let lefts := (List.range ncols).map (fun i => colLeft ncols wspace i)
  let rights := (List.range ncols).map (fun i => colRight ncols wspace i)
  let bottoms := (List.range nrows).map (fun j => rowBottom nrows hspace j)
  let tops := (List.range nrows).map (fun j => rowTop nrows hspace j)
  let mut grid : List (List Rect) := []
  for j in [0:nrows] do
    let bottom := bottoms[j]!
    let top := tops[j]!
    let mut row : List Rect := []
    for i in [0:ncols] do
      let left := lefts[i]!
      let right := rights[i]!
      row := row ++ [Rect.ofExtents left bottom right top]
    grid := grid ++ [row]
  return grid
-- impl-end


-- proof-start
theorem correct_subfigureGrid :
    ∀ (nrows ncols : Nat) (wspace hspace : ℚ),
      1 ≤ nrows → 1 ≤ ncols → 0 ≤ wspace → 0 ≤ hspace →
      problem_spec_subfigureGrid nrows ncols wspace hspace
        (implementation_subfigureGrid nrows ncols wspace hspace) := by
  intro nrows ncols wspace hspace h1 h2 h3 h4
  have hf : ∀ {α β : Type} (f : α → β) (l : List α),
      (l.map (fun x => [f x])).flatten = l.map f := by
    intro α β f l
    induction l with
    | nil => rfl
    | cons a t ih => simp [ih]
  unfold problem_spec_subfigureGrid implementation_subfigureGrid gridRects
  simp only [Id.run]
  simp only [List.range_eq_range']
  simp [hf]
  apply List.map_congr_left
  intro j hj
  rw [List.mem_range'] at hj
  apply List.map_congr_left
  intro i hi
  rw [List.mem_range'] at hi
  rw [List.getElem?_range' (by omega : j < nrows), List.getElem?_range' (by omega : i < ncols)]
  simp

-- proof-end
