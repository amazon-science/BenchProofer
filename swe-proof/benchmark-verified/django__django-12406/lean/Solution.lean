import Mathlib
-- imports-end

/-!
Two related behaviors for a model-backed choice field whose options are drawn
from a queryset.

* The leading empty option ("---------") that a choice field offers must be
  suppressed (set to none) not only when the field is required with an initial
  value, but ALSO when the field is rendered with a radio-style widget and the
  underlying model attribute forbids an empty value. Otherwise the empty
  option is presented with its default label.

* When a relational model attribute builds the keyword arguments for its
  generated form field, it forwards whether the attribute allows an empty value
  under the dedicated `blank` key, leaving every other keyword argument
  untouched.

These are stated abstractly as input→output relations; the implementation and
correctness proof for each are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both modeled behaviors are
-- spelled out with concrete operations (a Boolean decision; a single map update).
-- axioms-end

-- pure-start
/-- Abstraction of the heterogeneous values stored under a form field's keyword
arguments. Only the Boolean-flag value matters for the modeled behavior; other
values (a class, a queryset, an optional name) are kept opaque. -/
inductive KwargVal where
  | obj : KwargVal
  | name : Option String → KwargVal
  | flag : Bool → KwargVal
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The leading empty option is suppressed (`none`) exactly when the field is
required with a present initial value, OR the widget is radio-style and the
model attribute forbids an empty value; otherwise it carries the default
label. -/
def problem_spec_emptyOption (required : Bool) (initialPresent : Bool)
    (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String)
    (result : Option String) : Prop :=
  result = (if (required ∧ initialPresent) ∨ (radioWidget ∧ ¬ blankAllowed)
            then none else some defaultLabel)
-- post-conditions-end

-- impl-start
def implementation_emptyOption (required : Bool) (initialPresent : Bool)
    (radioWidget : Bool) (blankAllowed : Bool) (defaultLabel : String) :
    Option String := Id.run do
  let mut chosen : Option String := some defaultLabel
  if (required && initialPresent) || (radioWidget && !blankAllowed) then
    chosen := none
  else
    chosen := some defaultLabel
  return chosen
-- impl-end

-- proof-start
theorem correct_emptyOption :
    ∀ (required initialPresent radioWidget blankAllowed : Bool) (defaultLabel : String),
      problem_spec_emptyOption required initialPresent radioWidget blankAllowed defaultLabel
        (implementation_emptyOption required initialPresent radioWidget blankAllowed defaultLabel) := by
  intro required initialPresent radioWidget blankAllowed defaultLabel
  unfold problem_spec_emptyOption implementation_emptyOption
  simp only [Id.run, bind, pure]
  split <;> simp_all
-- proof-end

-- post-conditions-start
/-- Forwarding the empty-value flag under the `blank` key sets that key to the
model attribute's flag and leaves every other keyword argument equal to its
incoming value. -/
def problem_spec_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) (result : Std.HashMap String KwargVal) : Prop :=
  result["blank"]? = some (KwargVal.flag blankAllowed) ∧
  (∀ k, k ≠ "blank" → result[k]? = base[k]?)
-- post-conditions-end

-- impl-start
def implementation_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) : Std.HashMap String KwargVal := Id.run do
  let mut d := base
  d := d.insert "blank" (KwargVal.flag blankAllowed)
  return d
-- impl-end

-- proof-start
theorem correct_formKwargs :
    ∀ (base : Std.HashMap String KwargVal) (blankAllowed : Bool),
      problem_spec_formKwargs base blankAllowed (implementation_formKwargs base blankAllowed) := by
  intro base blankAllowed
  unfold problem_spec_formKwargs implementation_formKwargs
  simp only [Id.run, pure]
  refine ⟨?_, ?_⟩
  · rw [Std.HashMap.getElem?_insert]; simp
  · intro k hk
    rw [Std.HashMap.getElem?_insert]
    simp only [beq_iff_eq]
    rw [if_neg (fun h => hk h.symm)]
-- proof-end
