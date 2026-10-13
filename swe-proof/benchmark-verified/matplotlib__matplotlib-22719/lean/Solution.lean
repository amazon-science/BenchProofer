import Mathlib
-- imports-end

/-!
Deciding whether to emit an advisory notification when categorical (string) unit
conversion is asked to handle a sequence of values.

Two independent notifications are governed by the same rule. In each case a
boolean "flag" is computed by scanning every element of the incoming sequence and
checking a per-element property:

* one notification concerns a sequence whose elements are *all* non-string
  numeric values — the situation in which numbers are being pushed through a
  string-oriented converter (an advisory deprecation notice);
* the other concerns a sequence of strings that are *all* individually parsable
  as a number or a date — the situation in which the strings might really have
  been meant as numbers (an informational notice).

A per-element "all" check over an EMPTY sequence is vacuously satisfied, so the
flag alone is `true` even when there is nothing to convert. The desired behavior
is that neither notification fires for an empty sequence: a notification is
emitted exactly when the sequence is non-empty AND its flag holds. This avoids a
spurious, non-actionable notice (and the failure it triggered downstream) when an
empty data structure is plotted on a categorically-united axis.
-/

-- axioms-start
/-- Whether a single string "looks numeric" — i.e. is individually parsable as a
number or a date. This is an unchanged library helper; the notification rule does
not depend on HOW it decides, only on the sequence-level conjunction of its
results, so it is left abstract here. -/
opaque looksNumeric : String → Bool
-- axioms-end

-- pure-start
/-- A classification of one incoming element of a to-be-converted sequence: a
non-string numeric value, versus anything else (a string or other categorical
value). -/
inductive Element where
  | numeric
  | categorical

/-- The per-element property tested for the numeric-passthrough notification:
the element is a non-string numeric value. -/
def isNumeric : Element → Bool
  | .numeric => true
  | .categorical => false
-- pure-end

-- post-conditions-start
/-- The numeric-passthrough advisory fires exactly when the sequence is non-empty
and every element is a non-string numeric value. -/
def problem_spec_numericPassthrough (values : List Element) (result : Bool) : Prop :=
  result = (!values.isEmpty && values.all isNumeric)
-- post-conditions-end

-- impl-start
def implementation_numericPassthrough (values : List Element) : Bool := Id.run do
  let mut isNumlike := true
  for v in values do
    if !isNumeric v then
      isNumlike := false
  return (!values.isEmpty && isNumlike)
-- impl-end

-- proof-start
/-- The scanning loop sets its boolean accumulator to `init && values.all p`,
where `p` is the per-element predicate tested in the loop body. Generalized over
the accumulator so the cons step's IH applies. -/
private theorem flag_loop {α : Type} (p : α → Bool) (values : List α) (init : Bool) :
    (forIn (m := Id) values init fun v r =>
      if (!p v) = true then pure (ForInStep.yield false)
      else pure (ForInStep.yield r)) = (init && values.all p) := by
  induction values generalizing init with
  | nil => simp [List.forIn_nil, pure]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    by_cases h : (!p a) = true
    · simp only [h, if_true, List.all_cons, ih]
      simp only [Bool.not_eq_true'] at h
      simp [h]
    · simp only [h, List.all_cons, ih]
      simp only [Bool.not_eq_true, Bool.not_eq_false'] at h
      simp [h]

theorem correct_numericPassthrough :
    ∀ (values : List Element),
      problem_spec_numericPassthrough values
        (implementation_numericPassthrough values) := by
  intro values
  unfold problem_spec_numericPassthrough implementation_numericPassthrough
  simp only [Id.run, bind]
  rw [flag_loop isNumeric values true]
  rfl
-- proof-end

-- post-conditions-start
/-- The parsable-strings informational notice fires exactly when the sequence is
non-empty and every string in it individually looks numeric. -/
def problem_spec_parsableInfo (data : List String) (result : Bool) : Prop :=
  result = (!data.isEmpty && data.all looksNumeric)
-- post-conditions-end

-- impl-start
def implementation_parsableInfo (data : List String) : Bool := Id.run do
  let mut convertible := true
  for val in data do
    if !looksNumeric val then
      convertible := false
  return (!data.isEmpty && convertible)
-- impl-end

-- proof-start
theorem correct_parsableInfo :
    ∀ (data : List String),
      problem_spec_parsableInfo data
        (implementation_parsableInfo data) := by
  intro data
  unfold problem_spec_parsableInfo implementation_parsableInfo
  simp only [Id.run, bind]
  rw [flag_loop looksNumeric data true]
  rfl
-- proof-end
