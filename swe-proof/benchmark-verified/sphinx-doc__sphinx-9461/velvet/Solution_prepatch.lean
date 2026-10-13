import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The assembled token list is a pure function of two
--  independent boolean flags; the only library operation involved is the
--  constant space-join of the assembled list, which is unchanged and identical
--  on both sides (an R/I identity, checked by G-CONF). There is no unchanged
--  library callee whose contract the proof must consume.)
-- axioms-end

-- pure-start
/- The ordered list of optional annotation tokens for a documented entity, built
   from two independent boolean flags plus one always-present trailing token.
   Each flag, when set, contributes exactly one token, placed in a
   predetermined left-to-right order; when unset it contributes nothing. The trailing token is
   always present and always last. The two flags are independent: either, both,
   or neither may be set. -/
def annotationTokens (firstFlag secondFlag : Bool) : List String :=
  (if firstFlag  then ["abstract"] else []) ++
  (if secondFlag then ["class"]    else []) ++
  ["property"]

@[grind] lemma annotationTokens_eq (firstFlag secondFlag : Bool) :
    annotationTokens firstFlag secondFlag =
      (if firstFlag then ["abstract"] else []) ++
      (if secondFlag then ["class"] else []) ++ ["property"] := rfl

/- When the second flag is set, its token "class" is among the produced tokens
   regardless of the first flag. Each flag is observed independently of the
   other. -/
@[grind] lemma annotationTokens_secondFlag_present (firstFlag : Bool) :
    "class" ∈ annotationTokens firstFlag true := by
  unfold annotationTokens
  cases firstFlag <;> simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the ordered annotation-token list for a documented entity from two
   independent boolean flags. Each set flag contributes its own token in a
   predetermined order ahead of the always-present trailing token; the flags are independent
   (both, either, or neither). The flags are read-only inputs (not `mut`): the
   routine assembles a fresh list and mutates nothing (directive 5). -/
method assembleModifierTokens (firstFlag : Bool) (secondFlag : Bool) return (out : List String)
  ensures out = annotationTokens firstFlag secondFlag
  ensures secondFlag = true → "class" ∈ out
  ensures out ≠ [] ∧ out.getLast! = "property"
  do
    -- impl-start
    -- Pre-image skeleton: the trailing token seeds the list and only the FIRST
    -- flag can prepend its token; the SECOND flag has no branch, so when it is
    -- set its token is silently dropped. The frozen spec requires
    -- `annotationTokens` (which contributes the second flag's "class" token), so
    -- `prove_correct` MUST fail on the secondFlag case.
    let mut toks : List String := ["property"]
    if firstFlag then
      toks := ["abstract"] ++ toks
    return toks
    -- impl-end

prove_correct assembleModifierTokens by
  loom_solve
