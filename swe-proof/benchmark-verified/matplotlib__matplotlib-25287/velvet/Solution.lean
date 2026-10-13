import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed pure decision
--  over two configured color settings — the axis's tick color and its tick-label
--  color — yielding the color used to paint the secondary exponent (offset) text
--  for that axis. The downstream consumer that actually paints the text with the
--  chosen color is an UNCHANGED continuation reached identically on both branches,
--  so nothing about it is assumed: it is neither consumed as a contract nor
--  deep-modeled. There is no `axiom` declaration and no A-reference. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The color used to paint an axis's secondary exponent (offset) text, given the
   axis's tick color and its tick-label color.

   A tick-label color of the sentinel value "inherit" means "no distinct label
   color was configured — take the color from the tick color." Any other value
   is an explicitly configured label color and governs directly.

   This is the single behaviour at issue: the exponent text must follow
   the configured tick-LABEL color, falling back to the tick color only when the
   label color is left at the inherit sentinel — rather than always following the
   tick color and ignoring an explicitly configured label color. Grounded
   entirely in the two input color settings (directive 8): the result is one of
   them, selected by whether the label color is the inherit sentinel. -/
def offsetColor (tickColor labelColor : String) : String :=
  if labelColor = "inherit" then tickColor else labelColor
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the color of the secondary exponent (offset) text shown at the end
   of the horizontal axis. `tickColor` is the axis's configured tick color and
   `labelColor` is its configured tick-label color; both are read-only color
   settings (neither is `mut`) and neither is altered.

   Desired behaviour: an explicitly configured tick-label color governs the
   exponent text directly; the inherit sentinel falls back to — and therefore
   follows — the tick color. Always using the tick color, ignoring a configured
   label color, is the defect this pins out. -/
method xAxisOffsetColor (tickColor : String) (labelColor : String)
    return (out : String)
  ensures out = offsetColor tickColor labelColor
  do
    -- impl-start
    -- Follow the configured tick-label color, falling back to the tick color
    -- only when the label color is left at the inherit sentinel.
    if labelColor = "inherit" then
      return tickColor
    else
      return labelColor
    -- impl-end

prove_correct xAxisOffsetColor by
  loom_solve <;> simp only [offsetColor] <;> split <;> simp_all

/- Determine the color of the secondary exponent (offset) text shown at the end
   of the vertical axis. Same desired behaviour as the horizontal axis: the
   configured tick-label color governs, and the inherit sentinel falls back to
   the tick color. `tickColor` and `labelColor` are read-only color settings
   (neither `mut`); neither is altered. -/
method yAxisOffsetColor (tickColor : String) (labelColor : String)
    return (out : String)
  ensures out = offsetColor tickColor labelColor
  do
    -- impl-start
    if labelColor = "inherit" then
      return tickColor
    else
      return labelColor
    -- impl-end

prove_correct yAxisOffsetColor by
  loom_solve <;> simp only [offsetColor] <;> split <;> simp_all
