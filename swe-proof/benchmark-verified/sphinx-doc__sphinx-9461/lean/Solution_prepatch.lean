import Mathlib
-- imports-end

/-!
Behavior: rendering the leading modifier words shown before a documented
read-only attribute. The available modifier toggles are an "abstract" flag and a
"class-level" flag. The rendered text is the present modifier words, in a set
order, followed by the base word, joined by single spaces, with one trailing
space. This module pins exactly which words appear and in what order for every
combination of the two toggles.
-/

-- axioms-start
-- No outside callees are consumed: the behavior is modeled deeply from its
-- inputs (the two boolean toggles), so there are no opaque declarations and no
-- consumed/`_prop` axioms.
-- axioms-end

-- pure-start
/-- The ordered list of words rendered before joining. The optional modifier
words precede the base word in a set order. -/
def prefixWords (isAbstract isClassLevel : Bool) : List String :=
  (if isAbstract then ["abstract"] else []) ++
  (if isClassLevel then ["class"] else []) ++
  ["property"]
-- pure-end

-- post-conditions-start
/-- The rendered prefix is the ordered modifier words joined by single spaces,
with one trailing space appended. Both toggles independently control whether
their word appears, the base word is always present and always last, and the
order is: abstract, then class-level, then base. -/
def problem_spec_propertyPrefix
    (isAbstract isClassLevel : Bool) (result : String) : Prop :=
  result = String.intercalate " " (prefixWords isAbstract isClassLevel) ++ " "
-- post-conditions-end

-- impl-start
def implementation_propertyPrefix
    (isAbstract isClassLevel : Bool) : String := Id.run do
  -- Pre-patch behavior: the base word seeds the list and only the "abstract"
  -- toggle prepends a word; the class-level toggle is ignored entirely, so a
  -- class-level read-only attribute renders identically to a plain one.
  let mut words : List String := ["property"]
  if isAbstract then
    words := ["abstract"] ++ words
  return String.intercalate " " words ++ " "
-- impl-end

-- proof-start
theorem correct_propertyPrefix : ∀ (isAbstract isClassLevel : Bool),
    problem_spec_propertyPrefix isAbstract isClassLevel
      (implementation_propertyPrefix isAbstract isClassLevel) := by
  intro isAbstract isClassLevel
  unfold problem_spec_propertyPrefix implementation_propertyPrefix prefixWords
  cases isAbstract <;> cases isClassLevel <;> rfl
-- proof-end
