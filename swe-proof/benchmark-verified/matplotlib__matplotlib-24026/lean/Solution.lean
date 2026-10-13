import Mathlib
-- imports-end

/-!
Assigning colors to a sequence of stacked regions from a caller-supplied
palette.

When a non-empty palette of colors is supplied, the regions of the plot are
colored by walking the palette in order and wrapping around once it is
exhausted: the color of region `i` is the palette entry at position
`i mod (palette size)`. Supplying a palette always succeeds and produces exactly
one color per region — every entry the caller provides is accepted verbatim as a
color, with no further validation that could reject otherwise-meaningful color
tokens.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the cycling behavior is
-- spelled out concretely (modular indexing into the palette over a count of
-- regions), so there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- The color assigned to region `i` when cycling through `colors`: the palette
entry at index `i mod (palette size)`. For a non-empty palette this is always a
genuine palette entry. -/
def nthColor (colors : List String) (i : Nat) : String :=
  colors[i % colors.length]!
-- pure-end

-- post-conditions-start
/-- Coloring `n` stacked regions from a non-empty palette always succeeds and
yields exactly the `n`-long list whose `i`-th entry is the palette color for
region `i` (cyclic, wrapping at the palette size). The success carrier pins both
the length and every element to the input palette, so no other coloring — and no
failure — satisfies it. -/
def problem_spec_stackplotColors
    (colors : List String) (n : Nat) (result : Except String (List String)) : Prop :=
  result = Except.ok ((List.range n).map (fun i => nthColor colors i))
-- post-conditions-end

-- impl-start
def implementation_stackplotColors
    (colors : List String) (n : Nat) : Except String (List String) := Id.run do
  let mut r : List String := []
  for i in [0:n] do
    r := r ++ [nthColor colors i]
  return Except.ok r
-- impl-end

-- proof-start
/-- The accumulating append-loop equals prepending the accumulator to the map. -/
theorem foldl_append_eq_map (colors : List String) (xs : List Nat) (acc : List String) :
    xs.foldl (fun r i => r ++ [nthColor colors i]) acc
      = acc ++ xs.map (fun i => nthColor colors i) := by
  induction xs generalizing acc with
  | nil => simp
  | cons a as ih => simp [List.foldl_cons, ih, List.append_assoc]

theorem correct_stackplotColors :
    ∀ (colors : List String) (n : Nat), colors ≠ [] →
      problem_spec_stackplotColors colors n
        (implementation_stackplotColors colors n) := by
  intro colors n _
  unfold problem_spec_stackplotColors
  have h : implementation_stackplotColors colors n
      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by
    unfold implementation_stackplotColors
    simp [List.range_eq_range']
  rw [h, foldl_append_eq_map, List.nil_append]
-- proof-end
