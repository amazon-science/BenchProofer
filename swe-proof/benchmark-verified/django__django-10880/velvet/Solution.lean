import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this operation invokes — the
   generic SQL function-call renderer that substitutes a function name, an
   optional leading qualifier, and the rendered argument text into the call
   template `NAME(QUALIFIER ARGS)` — is modeled DEEPLY (the `renderCall`
   concatenation in the `pure` region) and validated equal to the real callee
   by axiom_check.py (G-AX, an A-reference). Provenance: mapping.md §3. -/
-- axioms-end

-- pure-start
/- The leading qualifier text emitted before the argument list of an aggregate
   SQL call. When the aggregate is asked to deduplicate its input, the qualifier
   is the keyword `DISTINCT` FOLLOWED BY A SEPARATOR, so that it never abuts the
   argument text that follows it; otherwise no qualifier is emitted. The
   separator is what keeps `NAME(DISTINCT <args>)` a syntactically valid call
   rather than gluing the keyword onto the first argument token. -/
def distinctQualifier (distinct : Bool) : List Char :=
  if distinct then "DISTINCT ".toList else []

/- The rendered aggregate SQL call: the function name, an opening parenthesis,
   the leading qualifier, the rendered argument text, and a closing parenthesis,
   concatenated in order. This is the deep model of the generic function-call
   renderer applied to this module's call template `NAME(QUALIFIER ARGS)`
   (mapping.md §3.1, validated == the real renderer by G-AX). -/
def renderCall (function : List Char) (distinct : Bool) (expressions : List Char) :
    List Char :=
  function ++ ['('] ++ distinctQualifier distinct ++ expressions ++ [')']

@[grind] lemma distinctQualifier_true :
    distinctQualifier true = "DISTINCT ".toList := rfl
@[grind] lemma distinctQualifier_false :
    distinctQualifier false = [] := rfl
@[grind] lemma renderCall_eq (function : List Char) (distinct : Bool)
    (expressions : List Char) :
    renderCall function distinct expressions =
      function ++ ['('] ++ distinctQualifier distinct ++ expressions ++ [')'] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method aggregateAsSql (function : List Char) (distinct : Bool)
    (expressions : List Char) return (out : List Char)
  ensures out = renderCall function distinct expressions
  do
    -- impl-start
    let qualifier : List Char := if distinct then "DISTINCT ".toList else []
    let out := function ++ ['('] ++ qualifier ++ expressions ++ [')']
    return out
    -- impl-end

prove_correct aggregateAsSql by
  loom_solve
