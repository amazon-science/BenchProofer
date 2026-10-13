import Mathlib
-- imports-end

/-!
Capturing a 2D coordinate handed in at construction time.

Two small helper objects each receive a 2D coordinate as a constructor argument
and keep it for later use. The coordinate is supplied by the caller through a
mutable container, and the caller is free to change the contents of that
container in place AFTER the object has been constructed.

The desired behaviour is that constructing the object must capture the coordinate
*by value*: the two components are read once, at construction time, and the stored
coordinate is a snapshot of exactly those two component values. Consequently, a
subsequent in-place change to the caller's container — so that the same source
later holds a different value — must NOT alter the coordinate already stored on
the object. Reading the stored coordinate back at any later moment yields the
component values that were present when the object was constructed, regardless of
what the source container holds at that later moment.

Both helper objects capture their coordinate the same way, and the requirement is
the same for each: the stored coordinate is frozen at construction and decoupled
from any later mutation of the source.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behaviour
-- modeled is the pure capture of a 2D coordinate's two components at construction
-- time into a fresh stored pair, decoupled from any later change to the source
-- container, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A coordinate pair retained by a helper object, viewed through *what a reader
sees after the source container may have been changed*. There are exactly two
retention behaviours the object can exhibit:

* `snapshot x y` — the pair is detached from the source: reading it always yields
  the captured `(x, y)`, whatever the source container now holds.
* `reference` — the pair stays bound to the source container: reading it yields
  the source's CURRENT contents.

The required (by-value) behaviour is `snapshot`. The two retentions are
observationally distinguishable exactly when the source is changed in place after
capture, which is the public reproduction described in the statement. -/
inductive StoredCoord where
  | snapshot (x y : Rat)
  | reference
  deriving DecidableEq, Repr

/-- Read back a retained coordinate given the source container's CURRENT contents
`later`. A `snapshot` ignores `later`; a `reference` reflects it. -/
def observe : StoredCoord → Rat × Rat → Rat × Rat
  | .snapshot x y, _     => (x, y)
  | .reference,    later => later
-- pure-end

-- post-conditions-start
/-- Capturing the offset-origin coordinate of the first helper object.

`initial` is the coordinate value present in the caller's source container at the
moment the object is constructed. `out` is the retained coordinate the object
holds afterwards.

The capture must be a by-value snapshot: reading the retained coordinate back
under ANY later state `later` of the source container yields the construction-time
value `initial`. Equivalently, the retained coordinate is decoupled from every
possible later mutation of the source — only the detached (`snapshot`) retention
satisfies this; a retained reference would leak `later`. -/
def problem_spec_freezeOffsetOrigin
    (initial : Rat × Rat) (out : StoredCoord) : Prop :=
  ∀ later : Rat × Rat, observe out later = initial
-- post-conditions-end

-- impl-start
def implementation_freezeOffsetOrigin
    (initial : Rat × Rat) : StoredCoord := Id.run do
  -- Pre-patch bug: the source container is stored by reference rather than
  -- snapshotted, so a later read reflects whatever the source holds at that
  -- moment instead of the construction-time value.
  return StoredCoord.reference
-- impl-end

-- proof-start
theorem correct_freezeOffsetOrigin :
    ∀ (initial : Rat × Rat),
      problem_spec_freezeOffsetOrigin initial
        (implementation_freezeOffsetOrigin initial) := by
  intro initial later
  unfold implementation_freezeOffsetOrigin observe
  simp
-- proof-end

-- post-conditions-start
/-- Capturing the anchor-point coordinate of the second helper object.

Identical capture requirement to the first object: `initial` is the
construction-time coordinate and `out` is the retained coordinate. Reading the
retained coordinate back under ANY later state `later` of the source container
must yield `initial` — the retention is detached from every later mutation of the
source (only the `snapshot` retention satisfies this). -/
def problem_spec_freezeAnchorPoint
    (initial : Rat × Rat) (out : StoredCoord) : Prop :=
  ∀ later : Rat × Rat, observe out later = initial
-- post-conditions-end

-- impl-start
def implementation_freezeAnchorPoint
    (initial : Rat × Rat) : StoredCoord := Id.run do
  -- Correct here: this prepatch isolates the first capture site's bug.
  let x := initial.1
  let y := initial.2
  return StoredCoord.snapshot x y
-- impl-end

-- proof-start
theorem correct_freezeAnchorPoint :
    ∀ (initial : Rat × Rat),
      problem_spec_freezeAnchorPoint initial
        (implementation_freezeAnchorPoint initial) := by
  intro initial later
  unfold implementation_freezeAnchorPoint observe
  simp
-- proof-end
