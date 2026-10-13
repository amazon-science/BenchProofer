import Mathlib
-- imports-end

/-!
Emitting a grouping marker so an annotation-box artist's gid reaches the output.

When a composite annotation-box artist is drawn onto a renderer it produces an
ordered sequence of drawing operations. The artist can carry an optional group
id (gid); for that id to survive into a structured output document (e.g. an SVG),
the artist must surround the drawing of its parts with a group-start marker that
carries the gid and a matching group-end marker.

The artist draws as follows:

* if it is not visible, or its position cannot be resolved, it draws nothing;
* otherwise it draws, in order:
  * a group-start marker tagged with the artist's class name and carrying its
    optional gid;
  * the connecting arrow, but only when the artist has one;
  * its background box;
  * the wrapped offset box;
  * a group-end marker tagged with the same class name.

The desired behavior is that the whole sequence of part-draws is enclosed
between the group-start (carrying the gid) and the group-end, so the gid labels
the group as a whole. Position resolution happens before any part is drawn and
contributes no marker of its own.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The drawing
-- behavior is modeled DEEPLY as the ordered trace of emitted operations over the
-- observable flags of the artist (visible, position-resolvable, has-an-arrow),
-- its class name, and its optional group id, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A single drawing operation emitted onto the renderer while drawing the
artist.

* `groupStart gname gid` — open a named group tagged with the optional group id;
* `groupEnd gname` — close the group with the matching name;
* `drawArrow` — draw the connecting arrow;
* `drawPatch` — draw the background box;
* `drawOffsetbox` — draw the wrapped offset box. -/
inductive RenderOp where
  | groupStart (gname : String) (gid : Option String)
  | groupEnd (gname : String)
  | drawArrow
  | drawPatch
  | drawOffsetbox
deriving DecidableEq, Repr

/-- The ordered sequence of drawing operations the artist emits.

* `visible` — the artist is visible;
* `posResolvable` — the artist's position could be resolved;
* `hasArrow` — the artist has a connecting arrow;
* `clsName` — the artist's class name (used to tag the group markers);
* `gid` — the artist's optional group id. -/
def drawTrace (visible posResolvable hasArrow : Bool)
    (clsName : String) (gid : Option String) : List RenderOp :=
  if !visible || !posResolvable then
    []
  else
    [RenderOp.groupStart clsName gid]
      ++ (if hasArrow then [RenderOp.drawArrow] else [])
      ++ [RenderOp.drawPatch, RenderOp.drawOffsetbox]
      ++ [RenderOp.groupEnd clsName]
-- pure-end

-- post-conditions-start
/-- The emitted trace is exactly the ordered sequence above: nothing when the
artist is not drawn, otherwise the part-draws enclosed between a group-start
carrying the gid and a matching group-end. -/
def problem_spec_drawAnnotationBbox
    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String)
    (result : List RenderOp) : Prop :=
  result = drawTrace visible posResolvable hasArrow clsName gid
-- post-conditions-end

-- impl-start
def implementation_drawAnnotationBbox
    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :
    List RenderOp := Id.run do
  if !visible || !posResolvable then
    return []
  let mut trace : List RenderOp := []
  trace := trace ++ [RenderOp.groupStart clsName gid]
  -- position resolution happens here and emits no marker
  if hasArrow then
    trace := trace ++ [RenderOp.drawArrow]
  trace := trace ++ [RenderOp.drawPatch]
  trace := trace ++ [RenderOp.drawOffsetbox]
  trace := trace ++ [RenderOp.groupEnd clsName]
  return trace
-- impl-end

-- proof-start
theorem correct_drawAnnotationBbox :
    ∀ (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String),
      problem_spec_drawAnnotationBbox visible posResolvable hasArrow clsName gid
        (implementation_drawAnnotationBbox visible posResolvable hasArrow clsName gid) := by
  intro visible posResolvable hasArrow clsName gid
  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace
  simp only [Id.run, bind, pure]
  by_cases h : (!visible || !posResolvable) = true <;>
    by_cases ha : hasArrow = true <;>
    simp [h, ha]
-- proof-end
