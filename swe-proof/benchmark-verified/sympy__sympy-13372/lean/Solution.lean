import Mathlib
-- imports-end

/-!
Reducing the real and imaginary components of a numeric evaluation to a tuple of
machine-float values paired with their precisions.

A numeric evaluation step takes the real part and the imaginary part of an
expression and tries to turn each into a concrete machine-float value:

* a component that is exactly zero contributes no value and carries no
  precision;
* a component that is a concrete number contributes its machine-float value at
  the working precision;
* a component that is neither exactly zero nor a concrete number cannot be
  reduced numerically — when either component is in this state, the whole
  reduction is reported as unsupported, so that a caller may fall back to a
  different strategy.

In addition, if either component still contains an unevaluated symbolic
real/imaginary marker, the reduction is likewise reported as unsupported.

The result, when supported, is the four-tuple of (real value, imaginary value,
real precision, imaginary precision): every one of these four outputs is pinned
to the classification of the corresponding input component, so a supported
result is well-formed in all four positions exactly when both components are
reducible.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The numeric
-- machine-float value a concrete component reduces to is supplied as part of the
-- classified input (the `floatVal` field) and carried through unchanged, so there is
-- no `opaque`/`axiom` callee contract to declare: the control-flow behavior is
-- modeled DEEPLY over the observable classification of each component.
-- axioms-end

-- pure-start
/-- Classification of one component (real part or imaginary part) of the
expression being evaluated. -/
inductive EvalfPartKind
  | zero      -- the component is exactly zero
  | number    -- the component is a concrete number reducible to a float
  | symbolic  -- the component is neither zero nor a concrete number
  deriving DecidableEq, Repr

/-- One classified component: its kind, the machine-float value it reduces to
when it is a concrete number, and whether it still contains an unevaluated
symbolic real/imaginary marker. -/
structure EvalfPart where
  kind : EvalfPartKind
  floatVal : Int          -- the machine-float value (meaningful only for `number`)
  hasUneval : Bool   -- carries an unevaluated symbolic real/imaginary marker
  deriving DecidableEq, Repr

/-- A reduced component value in the output tuple. -/
inductive EvalfPartOut
  | null        -- no value (the component was exactly zero)
  | num (m : Int)  -- a concrete machine-float value
  | sym         -- a still-symbolic, non-reduced value (a malformed output)
  deriving DecidableEq, Repr

/-- The supported reduction result: (real value, imaginary value, real
precision, imaginary precision). -/
abbrev EvalfTuple := EvalfPartOut × EvalfPartOut × Option Nat × Option Nat

/-- The reduced value contributed by a component (used only when the component
is reducible). -/
def evalfPartOut (p : EvalfPart) : EvalfPartOut :=
  match p.kind with
  | .zero => .null
  | .number => .num p.floatVal
  | .symbolic => .sym

/-- The precision contributed by a component: the working precision for a
concrete number, none otherwise. -/
def evalfPartPrec (p : EvalfPart) (prec : Nat) : Option Nat :=
  match p.kind with
  | .number => some prec
  | _ => none

/-- The desired reduction: unsupported (`.error ()`) when either component
carries an unevaluated marker, or when either component is symbolic; otherwise
the well-formed four-tuple. -/
def reduceComponentsToFloat (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple :=
  if rePart.hasUneval || imPart.hasUneval then
    .error ()
  else if rePart.kind = .symbolic then
    .error ()
  else if imPart.kind = .symbolic then
    .error ()
  else
    .ok (evalfPartOut rePart, evalfPartOut imPart, evalfPartPrec rePart prec, evalfPartPrec imPart prec)
-- pure-end

-- post-conditions-start
/-- The reduction produces exactly the supported/unsupported decision and the
fully-pinned four-tuple dictated by the rule above. -/
def problem_spec_reduceComponentsToFloat
    (rePart imPart : EvalfPart) (prec : Nat) (result : Except Unit EvalfTuple) : Prop :=
  result = reduceComponentsToFloat rePart imPart prec
-- post-conditions-end

-- impl-start
def implementation_reduceComponentsToFloat
    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do
  if rePart.hasUneval || imPart.hasUneval then
    return .error ()
  let mut reOut : EvalfPartOut := .sym
  let mut reprec : Option Nat := none
  if rePart.kind = .zero then
    reOut := .null
    reprec := none
  else if rePart.kind = .number then
    reOut := .num rePart.floatVal
    reprec := some prec
  else
    return .error ()
  let mut imOut : EvalfPartOut := .sym
  let mut imprec : Option Nat := none
  if imPart.kind = .zero then
    imOut := .null
    imprec := none
  else if imPart.kind = .number then
    imOut := .num imPart.floatVal
    imprec := some prec
  else
    return .error ()
  return .ok (reOut, imOut, reprec, imprec)
-- impl-end

-- proof-start
theorem correct_reduceComponentsToFloat :
    ∀ (rePart imPart : EvalfPart) (prec : Nat),
      problem_spec_reduceComponentsToFloat rePart imPart prec
        (implementation_reduceComponentsToFloat rePart imPart prec) := by
  intro rePart imPart prec
  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
    reduceComponentsToFloat
  simp only [Id.run, bind, pure]
  by_cases huneval : rePart.hasUneval || imPart.hasUneval
  · simp only [huneval, if_true]
  · simp only [huneval]
    rcases hre : rePart.kind with _ | _ | _ <;>
      rcases him : imPart.kind with _ | _ | _ <;>
      simp [evalfPartOut, evalfPartPrec, hre, him]
-- proof-end
