import Mathlib
-- imports-end

/-!
Rendering a template — literal text surrounding a single interpolated value — to
its output string, with attention to whether HTML autoescaping is active.

The interpolated value is turned into display text by a value-rendering step that
depends on a single boolean: whether automatic escaping is in effect. Literal
text on either side of the value passes through unchanged.

Which escaping setting governs the value-rendering step is determined by HOW the
caller supplies the rendering context:

  * when the caller passes a ready-made rendering context, that context's OWN
    escaping setting is the one in effect;
  * when the caller passes plain data (so a fresh rendering context is built for
    it), the escaping setting configured on the rendering engine is the one in
    effect.

The value-rendering step itself (turning a value into escaped-or-plain display
text) is the SAME operation regardless of which branch supplied the flag; here it
is taken as an arbitrary function of the escaping flag and the value, so the
behavior pinned below is exactly "the correct escaping flag reaches the
value-rendering step, and the literal text frames it unchanged."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The downstream
-- value-rendering operation (turning one interpolated value into its display
-- text given whether escaping is active) is modeled as an arbitrary function
-- parameter `renderValue : Bool → String → String`: the modeled change is solely
-- WHICH escaping flag is handed to that step, so the result is pinned for every
-- possible value-renderer. Hence the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the rendered output is the
-- literal-text frame around the value-rendering step applied to the value.
-- pure-end

-- post-conditions-start
/-- The rendered output is fully pinned to the inputs:

  * the escaping flag actually used (`eff`) is the supplied context's own flag
    when a ready-made context is given, and the engine's configured flag when
    plain data is given;
  * the output is exactly the leading literal text, then the value-rendering step
    applied to that flag and the interpolated value, then the trailing literal
    text.

No output component is left free: both the leading and trailing literals are
pinned to their inputs, and the value portion is pinned to the value-renderer at
the correctly-selected flag. -/
def problem_spec_renderToString
    (renderValue : Bool → String → String)
    (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
    (leading value trailing : String) (result : String) : Prop :=
  let eff := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
  result = leading ++ renderValue eff value ++ trailing
-- post-conditions-end

-- impl-start
def implementation_renderToString
    (renderValue : Bool → String → String)
    (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
    (leading value trailing : String) : String := Id.run do
  -- PRE-PATCH (buggy): a ready-made context renders with its own escaping flag,
  -- but plain data renders with the hard-wired default flag (`true`) instead of
  -- the engine's configured flag — the engine's `autoescape` is ignored.
  let mut autoescape := suppliedCtxAutoescape
  if !suppliedIsContext then
    autoescape := true
  return leading ++ renderValue autoescape value ++ trailing
-- impl-end

-- proof-start
theorem correct_renderToString :
    ∀ (renderValue : Bool → String → String)
      (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
      (leading value trailing : String),
      problem_spec_renderToString renderValue engineAutoescape suppliedIsContext
          suppliedCtxAutoescape leading value trailing
        (implementation_renderToString renderValue engineAutoescape suppliedIsContext
          suppliedCtxAutoescape leading value trailing) := by
  intro renderValue engineAutoescape suppliedIsContext suppliedCtxAutoescape
    leading value trailing
  unfold problem_spec_renderToString implementation_renderToString
  simp only [Id.run, bind, pure]
  cases suppliedIsContext <;> simp
-- proof-end
