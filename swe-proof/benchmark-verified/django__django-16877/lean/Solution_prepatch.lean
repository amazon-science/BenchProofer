import Mathlib
-- imports-end

/-!
A template filter that escapes every element of a sequence individually.

Some template filters mark text as safe-for-HTML by escaping the characters that
the HTML engine would otherwise interpret. There is an established filter that
performs this escaping decision on a single value; this bundle models the
companion filter that applies the SAME per-element escaping decision to each
member of a sequence, returning the resulting list.

The desired behavior is:

  * the result is a list with exactly one entry per element of the input
    sequence, in the same order; and

  * each entry is the per-element escaping decision applied to the corresponding
    input element.

The per-element escaping decision is the unchanged, shared HTML-escaping
behavior (a conditional HTML escaper that escapes ordinary text but leaves
content already marked safe untouched). It is referenced opaquely here: the
specification does not pin its concrete output, only that each result entry is
exactly the value that escaper yields for the corresponding input element.
-/

-- axioms-start
/-- An element of the input sequence, modeled by the attributes the per-element
escaper observes about it: whether the element is already marked safe (in which
case the escaper leaves it untouched) and its underlying text. -/
structure Elem where
  /-- Whether this element is already marked safe-for-HTML. -/
  isSafe : Bool
  /-- The underlying text of this element. -/
  text : String
deriving DecidableEq, Repr

/-- The unchanged, shared per-element HTML-escaping decision applied to a single
element. It escapes ordinary text but returns content already marked safe
untouched. It is referenced opaquely: the specification pins each result entry to
its value, but consumes no property of it. -/
opaque condEscape : Elem → String
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the
-- element-wise application of the per-element escaper over the input sequence.
-- pure-end

-- post-conditions-start
/-- Escaping each element of a sequence individually. The result is fully
determined: it is the list obtained by applying the per-element escaper
`condEscape` to every element of `value`, in order. This pins the length (one
entry per input element), the order, and each entry's value; no component of the
result is left unconstrained. -/
def problem_spec_escapeEach (value : List Elem) (result : List String) : Prop :=
  result = value.map condEscape
-- post-conditions-end

-- impl-start
def implementation_escapeEach (value : List Elem) : List String := Id.run do
  -- Pre-patch (buggy) skeleton: the companion sequence filter does not exist, so
  -- the per-element escaping decision is never applied — each element's text is
  -- passed through untouched instead of being escaped individually.
  let mut acc := []
  for obj in value do
    acc := acc ++ [obj.text]
  return acc
-- impl-end

-- proof-start
-- Gold proof body carried over from the patched bundle. Against the buggy impl
-- above it fails to typecheck: the spec demands each entry be `condEscape obj`
-- while the impl yields the raw `obj.text`, which the loop-fold rewrite cannot
-- close. That is exactly the G-DIFF signal: the spec sees the bug.
theorem correct_escapeEach :
    ∀ (value : List Elem),
      problem_spec_escapeEach value (implementation_escapeEach value) := by
  intro value
  unfold problem_spec_escapeEach implementation_escapeEach
  induction value with
  | nil => rfl
  | cons a as ih => simp [List.forIn_cons, ih]
-- proof-end
