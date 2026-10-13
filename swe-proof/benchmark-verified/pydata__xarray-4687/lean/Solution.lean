import Mathlib
-- imports-end

/-!
Elementwise conditional selection between two attributed arrays.

Each operand is an array of integer values carrying a set of metadata
attributes (modeled as an association list of name/value pairs). Given a boolean
condition array and two operands `x` and `y`, the result takes, position by
position, the value from `x` where the condition holds and from `y` otherwise.

Alongside the selected data, the operation accepts a three-valued flag
governing whether the result retains metadata attributes:

* when the flag is left unset, an ambient default policy decides;
* when it requests retention, the result carries the attributes of the operand
  chosen where the condition is true (here, `x`);
* otherwise the result carries no attributes.

The desired behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- The ambient default attribute-retention policy, consulted only when the
caller leaves the retention flag unset. Its concrete value comes from the
surrounding configuration; the behavior is specified for whatever value it
yields. -/
opaque getKeepAttrsDefault : Bool
-- axioms-end

-- pure-start
/-- An array of integer values together with its metadata attributes (an
association list of name/value pairs). -/
structure DataArr where
  values : List Int
  attrs  : List (String × String)

/-- Elementwise conditional selection: at each position keep the value from
`xs` when the condition is true, otherwise the value from `ys`. -/
def selVals (cond : List Bool) (xs ys : List Int) : List Int :=
  (cond.zip (xs.zip ys)).map (fun p => if p.1 then p.2.1 else p.2.2)

/-- Whether the result should retain attributes: the caller's flag when given,
otherwise the ambient default policy. -/
def keptAttrs (keepAttrs : Option Bool) : Bool :=
  match keepAttrs with
  | none   => getKeepAttrsDefault
  | some b => b
-- pure-end

-- post-conditions-start
/-- The result's values are the elementwise conditional selection of `x` and
`y` under `cond`; its attributes are those of `x` exactly when attribute
retention is in effect, and empty otherwise. -/
def problem_spec_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) (result : DataArr) : Prop :=
  result.values = selVals cond x.values y.values ∧
  result.attrs = (if keptAttrs keepAttrs then x.attrs else [])
-- post-conditions-end

-- impl-start
def implementation_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) : DataArr := Id.run do
  let mut ka : Option Bool := keepAttrs
  if ka == none then
    ka := some getKeepAttrsDefault
  let kept : Bool := match ka with
    | some true => true
    | _         => false
  let attrs := if kept then x.attrs else []
  return { values := selVals cond x.values y.values, attrs := attrs }
-- impl-end

-- proof-start
theorem correct_condSelect :
    ∀ (cond : List Bool) (x y : DataArr) (keepAttrs : Option Bool),
      problem_spec_condSelect cond x y keepAttrs
        (implementation_condSelect cond x y keepAttrs) := by
  intro cond x y keepAttrs
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  cases keepAttrs with
  | none =>
    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
    cases h : getKeepAttrsDefault <;> simp
  | some b =>
    cases b <;> simp [Id.run, bind, pure]
-- proof-end
