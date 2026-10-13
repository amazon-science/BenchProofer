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
  have hcond : ((required && initialPresent) || (radioWidget && !blankAllowed)) = true
      ↔ ((required ∧ initialPresent) ∨ (radioWidget ∧ ¬ blankAllowed)) := by
    simp [Bool.or_eq_true, Bool.and_eq_true]
  by_cases h : ((required && initialPresent) || (radioWidget && !blankAllowed)) = true
  · rw [if_pos (hcond.mp h)]
    simp only [Id.run, h, if_true]
    rfl
  · rw [if_neg (fun hp => h (hcond.mpr hp))]
    simp only [Id.run, h, Bool.false_eq_true, if_false]
    rfl
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
-- PRE-PATCH (buggy) skeleton for behavior 2: the empty-value flag is never
-- forwarded, so the `blank` key is absent from the assembled keyword arguments.
def implementation_formKwargs (base : Std.HashMap String KwargVal)
    (blankAllowed : Bool) : Std.HashMap String KwargVal := Id.run do
  let mut d := base
  return d
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl.
theorem correct_formKwargs :
    ∀ (base : Std.HashMap String KwargVal) (blankAllowed : Bool),
      problem_spec_formKwargs base blankAllowed (implementation_formKwargs base blankAllowed) := by
  intro base blankAllowed
  have hrun : implementation_formKwargs base blankAllowed
      = base.insert "blank" (KwargVal.flag blankAllowed) := rfl
  unfold problem_spec_formKwargs
  rw [hrun]
  refine ⟨?_, ?_⟩
  · rw [Std.HashMap.getElem?_insert]; simp
  · intro k hk
    rw [Std.HashMap.getElem?_insert]
    simp [beq_iff_eq, Ne.symm hk]
-- proof-end
