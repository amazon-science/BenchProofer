import Mathlib
-- imports-end

/-!
Twin-artifact bundle: the per-node emission decision of a code printer that
turns symbolic expressions into target-language source.

When printing a function application, the printer checks whether the function
is one it recognizes as having a direct built-in equivalent in the target
language. If so, it emits the built-in call `name(arg, …)` — the mapped
built-in name followed by the comma-separated, already-printed arguments in
parentheses. If the function has no built-in equivalent, the node is emitted
by the pre-existing surrounding printing machinery; that machinery is
unchanged infrastructure, and its output for the node arrives here as the
read-only input `fallback`, to be returned unaltered.

Desired behaviour: the minimum and maximum operations have built-in
equivalents and therefore render as `min(arg, …)` and `max(arg, …)`
respectively; the absolute-value operation keeps its pre-existing `abs`
rendering; EVERY other function is emitted exactly as the unchanged machinery
would emit it (`fallback`) — nothing but the minimum/maximum emission may
change.

Every branch of the result is pinned to the inputs (the function name, the
argument strings, and the fallback text), so no part of the rendered output is
left free: the specification is total, with no domain restriction.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed. The dispatch test and the built-in
-- call rendering are modeled DEEPLY (spelled out below: the name decision plus
-- a comma-join + parenthesization), so there is no `opaque`/`axiom` callee
-- contract. The per-argument printing is unchanged and abstracted into the
-- `args` strings; likewise the emission the unchanged surrounding machinery
-- produces for a function with no built-in equivalent is unchanged,
-- pre-existing infrastructure whose output arrives as the read-only input
-- `fallback`. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Render a recognized call: the built-in name applied to its already-printed
arguments, comma-separated inside parentheses (`name(a, b, …)`). This is the
unchanged formatting shared by every recognized built-in. -/
def renderCall (fn : String) (args : List String) : String :=
  fn ++ "(" ++ String.intercalate ", " args ++ ")"
-- pure-end

-- post-conditions-start
/-- The emission is fully determined by the inputs:
* the minimum operation renders as a `min(…)` call over its arguments;
* the maximum operation renders as a `max(…)` call over its arguments;
* the absolute-value operation keeps its pre-existing `abs(…)` rendering;
* EVERY other function is emitted exactly as the unchanged surrounding
  machinery emits it — the result is the read-only input `fallback`, verbatim,
  so no behaviour other than the minimum/maximum emission may change.
The four clauses cover every possible name: no output is left unconstrained. -/
def problem_spec_printApp
    (name : String) (args : List String) (fallback : String)
    (result : String) : Prop :=
  (name = "Min" → result = renderCall "min" args) ∧
  (name = "Max" → result = renderCall "max" args) ∧
  (name = "Abs" → result = renderCall "abs" args) ∧
  (name ≠ "Min" → name ≠ "Max" → name ≠ "Abs" → result = fallback)
-- post-conditions-end

-- impl-start
def implementation_printApp
    (name : String) (args : List String) (fallback : String) : String :=
  -- the built-in-equivalent table now maps the minimum and maximum operations;
  -- the absolute-value mapping is pre-existing
  if name = "Min" then renderCall "min" args
  else if name = "Max" then renderCall "max" args
  else if name = "Abs" then renderCall "abs" args
  -- no built-in equivalent: the node keeps the unchanged machinery's emission
  else fallback
-- impl-end

-- proof-start
theorem correct_printApp :
    ∀ (name : String) (args : List String) (fallback : String),
    problem_spec_printApp name args fallback
      (implementation_printApp name args fallback) := by
  intro name args fallback
  unfold problem_spec_printApp implementation_printApp
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro h; simp [h]
  · intro h; simp [h]
  · intro h; simp [h]
  · intro h1 h2 h3; simp [h1, h2, h3]
-- proof-end
