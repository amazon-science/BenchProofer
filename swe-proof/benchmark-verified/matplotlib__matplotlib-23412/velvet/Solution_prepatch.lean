import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the render-time dash pattern is a pure construction
--  from the values the shape already holds, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A filled outline shape stores its boundary stroke style as a dash pattern: a
   scalar phase (the starting position along the on/off cycle) together with the
   even-length on/off ink-length sequence. When the shape is rendered, the dash
   pattern handed to the drawing back end must be the shape's OWN dash pattern:
   the phase is preserved exactly, and the on/off sequence is preserved exactly,
   element for element, in order.

   In particular, two shapes whose stored dash patterns differ only in their
   phase must be handed dash patterns that still differ in that same phase — the
   phase a caller supplies is honoured, never silently dropped.

   The render-time dash pattern is modeled as a single list whose head is the
   phase handed to the back end and whose tail is the on/off sequence handed to
   the back end. The phase and on/off ink lengths are modeled as exact integers:
   the tested behaviour is solely whether the stored phase is carried through to
   the renderer unchanged versus dropped to zero — a discrete value-vs-zero
   distinction independent of any floating-point magnitude, so an exact integer
   carrier is faithful (see mapping.md). The stored on/off sequence is read-only
   (not `mut`): the construction never mutates it (directive 5). -/
method renderDashPattern (phase : Int) (onoff : List Int) return (out : List Int)
  -- The render-time pattern is the stored phase followed by the stored on/off
  -- sequence, in order: head is the phase exactly, tail is the on/off verbatim.
  ensures out = phase :: onoff
  ensures out.head? = some phase
  ensures out.tail = onoff
  ensures out.length = onoff.length + 1
  do
    -- impl-start
    -- PRE-PATCH BUG: the phase is forced to 0 (the dash offset is ignored),
    -- so a shape with a nonzero stored phase is rendered with phase 0.
    return (0 : Int) :: onoff
    -- impl-end

prove_correct renderDashPattern by
  loom_solve
