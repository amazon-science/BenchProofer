import Mathlib
-- imports-end

/-!
Markup rendering of a bound-evaluation expression: a body together with a list
of variable-to-value assignments, displayed as the body restricted by those
assignments.

The renderer receives the already-rendered markup of the body and of each
assignment's left- and right-hand sides (these renderings are produced by a
generic recursive markup routine and are inputs here). It assembles a single
markup string consisting of:

  * the body, displayed as a self-contained delimited group, restricted by
  * the assignment list, each entry shown as `lhs=rhs` and the entries separated
    by a line break, all gathered in a stacked subscript.

The body is always presented as its own delimited group so that, when this
rendering is placed inside a larger surrounding expression, the body reads as a
single unit rather than merging with its surroundings.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The recursive
-- markup of the body and of each assignment side is produced upstream and is
-- supplied to this routine as plain string inputs (`inner`, `lhs`, `rhs`); this
-- routine only assembles those strings into the final layout, so there is no
-- `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- The rendered assignment entries: each `(l, r)` pair from the parallel
left/right rendering lists shown as `l=r`. The pairing truncates to the shorter
list, exactly as a parallel zip does. -/
def subsEntries (lhs rhs : List String) : List String :=
  (lhs.zip rhs).map (fun p => p.1 ++ "=" ++ p.2)

/-- The line-break separator between stacked assignment entries (a markup line
break: two backslashes followed by a space). -/
def subsSep : String := "\\\\ "
-- pure-end

-- post-conditions-start
/-- The assembled markup. The body `inner` is wrapped as its own delimited group
and placed as the restricted quantity; the assignment entries (`subsEntries`),
joined by the line-break separator, fill the stacked subscript. Every fragment of
the output is pinned to the inputs, so the result is fully determined. -/
def problem_spec_renderRestriction
    (inner : String) (lhs rhs : List String) (result : String) : Prop :=
  result =
    "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
      ++ String.intercalate subsSep (subsEntries lhs rhs) ++ " }}"
-- post-conditions-end

-- impl-start
/-- Pre-patch skeleton: the body is placed directly as the restricted quantity,
without being presented as its own delimited group. -/
def implementation_renderRestriction
    (inner : String) (lhs rhs : List String) : String := Id.run do
  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
  return "\\left. " ++ inner ++ " \\right|_{\\substack{ "
    ++ latexSubs ++ " }}"
-- impl-end

-- proof-start
theorem correct_renderRestriction :
    ∀ (inner : String) (lhs rhs : List String),
      problem_spec_renderRestriction inner lhs rhs
        (implementation_renderRestriction inner lhs rhs) := by
  intro inner lhs rhs
  unfold problem_spec_renderRestriction implementation_renderRestriction
  rfl
-- proof-end
