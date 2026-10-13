import Mathlib
-- imports-end

/-!
Wrapping a JSON-encoded value inside a `<script type="application/json">` tag for
safe inclusion in HTML output.

The value is first turned into a safe, escaped JSON body by an encoding step that
is independent of any identifier. The body is then embedded in a script tag. The
caller may optionally supply an identifier string:

  * when a non-empty identifier is supplied, the script tag carries an `id`
    attribute set to that identifier (with the identifier escaped for attribute
    use), and the JSON body follows;
  * when no identifier is supplied (the identifier is absent / empty), the script
    tag is emitted WITHOUT any `id` attribute, the JSON body following directly.

The JSON-encoding step and the attribute-escaping step are the SAME operations in
both cases; here they are taken as arbitrary functions, so the behavior pinned
below is exactly "the presence of an identifier selects whether an `id` attribute
is emitted, and the encoded body is framed by the corresponding script tag."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two unchanged steps are
-- modeled as arbitrary function parameters:
--   * `jsonBody : String → String` — turning the value into its safe, escaped
--     JSON body (the encoder + entity translation step); independent of any
--     identifier, so it is the SAME in both branches.
--   * `escapeId : String → String` — escaping the identifier for safe use inside
--     an attribute value (the same escaping the formatter applies to substituted
--     arguments).
-- Leaving both universally quantified means the spec holds for every encoder /
-- escaper; the modeled change is solely WHETHER the `id` attribute is emitted.
-- Hence the spec needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: each branch's output is a literal
-- frame around the (encoded body, escaped identifier) produced by the abstract
-- steps above.
-- pure-end

-- post-conditions-start
/-- The output script-tag string is fully pinned to the inputs:

  * when the identifier is non-empty, the output is the opening `<script>` tag
    carrying an `id` attribute set to the escaped identifier, then the encoded
    JSON body, then the closing tag;
  * when the identifier is empty (no identifier supplied), the output is the
    opening `<script>` tag WITHOUT any `id` attribute, then the encoded JSON body,
    then the closing tag.

No output component is left free: the literal tag text is constant, the body portion
is pinned to the encoder applied to the value, and (in the with-identifier branch)
the attribute value is pinned to the escaper applied to the identifier. -/
def problem_spec_scriptTag
    (jsonBody : String → String)
    (escapeId : String → String)
    (value optId : String) (result : String) : Prop :=
  result =
    if optId ≠ "" then
      "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
        ++ jsonBody value ++ "</script>"
    else
      "<script type=\"application/json\">" ++ jsonBody value ++ "</script>"
-- post-conditions-end

-- impl-start
def implementation_scriptTag
    (jsonBody : String → String)
    (escapeId : String → String)
    (value optId : String) : String := Id.run do
  -- Encode the value into its safe JSON body once; this step is independent of
  -- any identifier.
  let jsonStr := jsonBody value
  -- Select the script-tag frame: with an `id` attribute when an identifier is
  -- supplied, otherwise without one.
  let mut result := ""
  if optId ≠ "" then
    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
      ++ jsonStr ++ "</script>"
  else
    result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
  return result
-- impl-end

-- proof-start
theorem correct_scriptTag :
    ∀ (jsonBody : String → String) (escapeId : String → String)
      (value optId : String),
      problem_spec_scriptTag jsonBody escapeId value optId
        (implementation_scriptTag jsonBody escapeId value optId) := by
  intro jsonBody escapeId value optId
  unfold problem_spec_scriptTag implementation_scriptTag
  by_cases h : optId ≠ "" <;> simp only [h, if_false, Id.run] <;> rfl
-- proof-end
