import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two modeled functions decide how an alias entry
--  is documented; both decisions read the SAME two observations of the alias:
--  whether it is being documented as an alias at all, and the optional
--  doc-comment attached to the alias name in its source module. The doc-comment
--  lookup is an added helper whose result is carried here as the read-only input
--  `varComment : Option (List String)` (an R refinement, validated against the
--  real lookup by conformance_check.py / G-CONF); the documentation produced by
--  the ordinary, non-alias path is likewise carried as the read-only input
--  `normalDoc` (R), and the rendered alias label as `aliasLabel` (R). Every
--  observable is a closed function of these inputs — nothing is borrowed from an
--  oracle, and there is no unchanged library callee whose contract the proof must
--  axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether a doc-comment attached to an alias name is to be treated as present.
   The lookup yields an optional sequence of comment lines: it is ABSENT (`none`)
   when the alias's source could not be analysed, and otherwise a (possibly empty)
   sequence of lines. A comment counts as present exactly when that sequence is
   actually non-empty — so both "could not analyse" and "analysed but no comment"
   count as ABSENT. -/
@[grind] def commentPresent : Option (List String) → Bool
  | none    => false
  | some xs => !xs.isEmpty

/- The documentation an alias entry exposes.

   * For an alias (`isAlias = true`): if a doc-comment is present, the entry
     exposes an EMPTY docstring container (`some []`) — a real, if empty, body
     that lets the comment attached to the alias name be rendered as the entry's
     documentation; if no comment is present, the entry exposes NO docstring
     container at all (`none`), the long-standing behaviour for a bare alias.
   * Otherwise (`isAlias = false`): the entry exposes exactly the documentation
     produced by the ordinary documentation path (`normalDoc`), untouched.

   The distinction between `some []` (an empty container) and `none` (no
   container) is the whole point: they are genuinely different results and drive
   different downstream rendering. -/
@[grind] def docForAlias (isAlias : Bool) (varComment : Option (List String))
    (normalDoc : Option (List (List String))) : Option (List (List String)) :=
  if isAlias then
    (if commentPresent varComment then some [] else none)
  else
    normalDoc

/- The content forwarded for an alias entry. When the entry is an alias AND has
   no doc-comment present, its content is OVERRIDDEN with the rendered alias label
   (the "alias of …" line). In every other case — not an alias, or an alias that
   does carry a doc-comment — the incoming content is forwarded unchanged, so an
   alias with a doc-comment keeps its own documentation rather than being replaced
   by the alias label. -/
@[grind] def contentForAlias (isAlias : Bool) (varComment : Option (List String))
    (incoming aliasLabel : List String) : List String :=
  if isAlias && !commentPresent varComment then aliasLabel else incoming
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The documentation an entry exposes, for an entry that may be an alias.

   `isAlias` (read-only) selects the regime. When it is false, the entry exposes
   the ordinary documentation `normalDoc` unchanged. When it is true, the entry
   is an alias and the result is governed by the OPTIONAL doc-comment `varComment`
   attached to the alias name:
   - when a comment is PRESENT (a non-empty line sequence), the entry exposes an
     empty docstring container `some []`, so the comment can be shown as the
     entry's documentation;
   - when NO comment is present (the lookup is absent, or present but empty), the
     entry exposes no docstring container, `none`.

   The optional comment is modeled as `Option (List String)` so that "could not
   analyse the source" (`none`) and "analysed, no comment" (`some []`) are
   genuinely different inputs that nonetheless agree on the decision; the result
   is `Option (List (List String))` so that "an empty container" (`some []`) and
   "no container" (`none`) are genuinely different outputs. `isAlias`,
   `varComment` and `normalDoc` are read-only (not `mut`): a fresh result is
   built and none of them is mutated (directive 5). -/
method aliasDocstrings (isAlias : Bool) (varComment : Option (List String))
    (normalDoc : Option (List (List String)))
    return (out : Option (List (List String)))
  ensures out = docForAlias isAlias varComment normalDoc
  ensures (isAlias = true ∧ commentPresent varComment = true) → out = some []
  ensures (isAlias = true ∧ commentPresent varComment = false) → out = none
  do
    -- impl-start
    -- Pre-image skeleton: an alias entry NEVER exposes a docstring container,
    -- regardless of any doc-comment attached to the alias name — it always
    -- reports `none`. The frozen spec requires `some []` when a comment is
    -- present, so prove_correct MUST fail.
    if isAlias then
      return none
    else
      return normalDoc
    -- impl-end

prove_correct aliasDocstrings by
  loom_solve

/- The content forwarded for an entry that may be an alias.

   `isAlias` (read-only) says whether the entry is being documented as an alias.
   When it is, the content is replaced by the rendered alias label `aliasLabel`
   ONLY when no doc-comment is present for the alias name; if a doc-comment IS
   present, the incoming content `incoming` is forwarded unchanged so the alias
   keeps its own documentation instead of being replaced by the alias label. When
   the entry is not an alias, the incoming content is always forwarded unchanged.

   `isAlias`, `varComment`, `incoming` and `aliasLabel` are read-only (not `mut`):
   the routine chooses which sequence to forward and mutates none of its inputs
   (directive 5). The incoming content is pinned to be forwarded unchanged
   whenever the override does not apply, so no result component is left free. -/
method aliasContentOverride (isAlias : Bool) (varComment : Option (List String))
    (incoming : List String) (aliasLabel : List String)
    return (out : List String)
  ensures out = contentForAlias isAlias varComment incoming aliasLabel
  ensures (isAlias = true ∧ commentPresent varComment = true) → out = incoming
  ensures (isAlias = true ∧ commentPresent varComment = false) → out = aliasLabel
  do
    -- impl-start
    if isAlias && !commentPresent varComment then
      return aliasLabel
    else
      return incoming
    -- impl-end

prove_correct aliasContentOverride by
  loom_solve
