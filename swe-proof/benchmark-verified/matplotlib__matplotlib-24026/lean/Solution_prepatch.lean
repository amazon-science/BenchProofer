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
-- PRE-PATCH (buggy) skeleton: the palette is first pushed through a validator
-- that rejects any cycle-reference token (a 'C' followed by a single digit),
-- raising an error instead of accepting it. Only when no such token is present
-- does the cyclic coloring proceed. Thus a palette containing such a token
-- fails outright rather than being colored.
def isCycleRef (s : String) : Bool :=
  match s.toList with
  | ['C', d] => d.isDigit
  | _ => false

def implementation_stackplotColors
    (colors : List String) (n : Nat) : Except String (List String) := Id.run do
  for c in colors do
    if isCycleRef c then
      return Except.error "Cannot put cycle reference in prop_cycler"
  let mut r : List String := []
  for i in [0:n] do
    r := r ++ [nthColor colors i]
  return Except.ok r
-- impl-end

-- proof-start
-- Gold proof body carried over by the proof agent; it does NOT close against
-- the buggy impl (left as `sorry` at construction time).
theorem correct_stackplotColors :
    ∀ (colors : List String) (n : Nat), colors ≠ [] →
      problem_spec_stackplotColors colors n
        (implementation_stackplotColors colors n) := by
  sorry
-- proof-end
