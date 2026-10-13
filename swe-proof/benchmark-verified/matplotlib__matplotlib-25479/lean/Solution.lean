import Mathlib
-- imports-end

/-!
Colormap identity and name registration.

A colormap carries a human-readable *display name* together with the data that
determines how it maps values to colors: a small auxiliary attribute and a
lookup table. Two behaviors are modeled.

* **Equality of colormaps.** Two colormaps are considered equal exactly when
  their color-determining content matches — that is, when their auxiliary
  attribute is equal AND their lookup tables are equal, element for element. The
  display name is *not* part of this comparison: two colormaps that differ only
  in their display name are equal. (Equality is decided purely by the
  color-producing content; relabelling a colormap does not change what it is.)

* **Registering a colormap under a name.** When a colormap is stored in the
  registry under a chosen lookup name, the stored colormap must carry that very
  name as its display name, so that a later lookup by the registered name yields
  a colormap that reports the name it was registered under. All of the stored
  colormap's color-determining content (the auxiliary attribute and the lookup
  table) is that of the colormap being registered — only the display name is set
  to the registration name.

The two behaviors interact: after registering a colormap under a name different
from its original display name, the looked-up colormap both reports the
registration name and compares equal to the colormap that was registered.
-/

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behaviors. Duplicating a
-- colormap before storing it is structural (it preserves every modeled field),
-- and comparing two lookup tables is ordinary element-wise list equality; both
-- are modeled directly below rather than axiomatized. Hence no `opaque` callee
-- and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- A colormap, modeled by the fields that the modeled behaviors touch:
* `name`   — the display name (a string);
* `flag`   — a small comparable auxiliary attribute that participates in equality
             (modeled as an integer code; see mapping.md for the bijection);
* `table`  — the lookup table that participates in equality, compared as a
             whole (modeled as a list of rows of integer entries, so that two
             tables compare equal exactly when they have the same shape and
             agree entry-for-entry).
Other colormap fields are irrelevant to the modeled behaviors and omitted. -/
structure Colormap where
  name  : String
  flag  : Int
  table : List (List Int)
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Equality of two colormaps: the result is `true` exactly when the
color-determining content of the two colormaps agrees — their auxiliary
attribute is equal and their lookup tables are equal element-wise. The display
name does not enter the comparison. The result is fully pinned by the inputs:
nothing about it is left unconstrained. -/
def problem_spec_colormapEq (a b : Colormap) (result : Bool) : Prop :=
  result = ((a.flag == b.flag) && (a.table == b.table))
-- post-conditions-end

-- impl-start
def implementation_colormapEq (a b : Colormap) : Bool := Id.run do
  if a.flag != b.flag then
    return false
  return a.table == b.table
-- impl-end

-- proof-start
theorem correct_colormapEq : ∀ a b : Colormap,
    problem_spec_colormapEq a b (implementation_colormapEq a b) := by
  intro a b
  unfold problem_spec_colormapEq implementation_colormapEq
  simp only [Id.run, bind, bne]
  by_cases h : a.flag == b.flag <;> simp [pure, h]
-- proof-end

-- post-conditions-start
/-- Storing a colormap under a registration name: the stored colormap reports the
registration name as its display name, while its color-determining content (the
auxiliary attribute and the lookup table) is exactly that of the colormap being
registered. Every output component is pinned to its input: the name to the
registration name, the remaining content to the registered colormap. -/
def problem_spec_register (name : String) (cmap : Colormap) (result : Colormap) : Prop :=
  result.name = name ∧ result.flag = cmap.flag ∧ result.table = cmap.table
-- post-conditions-end

-- impl-start
def implementation_register (name : String) (cmap : Colormap) : Colormap := Id.run do
  -- A duplicate of the colormap is what gets stored (structural copy).
  let mut stored := cmap
  -- The stored colormap should report the registration name, even when its own
  -- display name differs.
  if stored.name != name then
    stored := { stored with name := name }
  return stored
-- impl-end

-- proof-start
theorem correct_register : ∀ (name : String) (cmap : Colormap),
    problem_spec_register name cmap (implementation_register name cmap) := by
  intro name cmap
  unfold problem_spec_register implementation_register
  simp only [Id.run, bind, bne]
  by_cases h : cmap.name == name <;> simp [pure, h]
  exact beq_iff_eq.mp h
-- proof-end
