import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the enclosing-group commands and the child renderings
--  are modeled directly as the command stream the render handed to the back end;
--  no unchanged callee's contract is consumed by the proof.)
-- axioms-end

-- pure-start
/- A single drawing command handed to the rendering back end while a composite
   artist is rendered.

     * `beginGroup gid` — start a grouping element tagged with the artist's own
        identifier `gid` (absent when the artist has none);
     * `endGroup`       — finish the grouping element opened most recently;
     * `child`          — one of the drawing commands emitted by a contained
        sub-artist (its concrete payload is opaque to this model; only its
        position in the stream matters here).

   The command stream is the observable the back end turns into output, so it is
   the carrier of the rendering behaviour. -/
inductive RenderCmd where
  | beginGroup (gid : Option String)
  | endGroup
  | child (tag : Nat)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rendering a composite artist that is to be drawn (its visibility/placement
   guard already passed). The artist exposes an optional identifier `gid` and a
   contained drawing `children` — the in-order command stream produced by its
   sub-renderings. The rendering of the whole composite must be enclosed as a
   single addressable unit tagged with the artist's OWN identifier: the stream
   opens with a grouping element carrying `gid`, then contains the children's
   commands unchanged and in order, then closes that grouping element. Thus the
   artist's identifier reaches the back end and labels the composite as a whole
   in the output.

   `gid` and `children` are read-only inputs (neither is `mut`): the rendering
   neither invents nor alters the identifier and reproduces the children's
   command stream verbatim (directive 5). -/
method groupedRender (gid : Option String) (children : List RenderCmd)
    return (out : List RenderCmd)
  -- The full enclosed stream: open-tag(gid), then the children verbatim and in
  -- order, then the matching close-tag.
  ensures out = RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])
  -- The stream OPENS with a grouping element carrying the artist's own
  -- identifier (the discriminating observable: the identifier is passed on).
  ensures out.head? = some (RenderCmd.beginGroup gid)
  -- The enclosing grouping element is closed (the stream ends with the matching
  -- close-tag), so the children are bracketed as one unit.
  ensures out.getLast? = some RenderCmd.endGroup
  -- The children are carried through unchanged, in order, bracketed by the two
  -- enclosing commands.
  ensures out.tail = children ++ [RenderCmd.endGroup]
  ensures out.length = children.length + 2
  do
    -- impl-start
    -- PRE-PATCH: the composite emits only its children's drawing commands; it
    -- never opens an enclosing grouping element carrying the artist's
    -- identifier, so that identifier never reaches the back end.
    let mut trace : List RenderCmd := []
    trace := trace ++ children
    return trace
    -- impl-end

prove_correct groupedRender by
  loom_solve
