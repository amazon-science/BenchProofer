import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axioms. The two rendered fragments consumed below are free inputs — the
--  outputs of unchanged upstream renderers — so there is no callee contract to
--  assert or validate. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The character sequence of the notation for an expression displayed together
   with a list of evaluation assignments. The rendered body is enclosed in a
   matched pair of size-adjusting delimiters before the evaluation bar and the
   stacked assignment list are appended. Spelled out concretely (a deep model of
   the assembled sequence) so the implementation below is the identical
   concatenation. The delimiter-enclosure of the body is the behaviour pinned
   here. -/
def subsNotationLatex (body subsList : List Char) : List Char :=
  "\\left. \\left(".toList ++ body
    ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
    ++ " }}".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the notation for an expression shown evaluated against a list of
   assignments: the already-rendered `body` sequence, enclosed in a matched pair
   of size-adjusting delimiters, followed by the evaluation bar and the rendered
   `subsList` assignments inside the stacking group.

   `body` and `subsList` are read-only rendered fragments (the outputs of
   unchanged upstream renderers); they are NOT `mut` and the routine mutates
   nothing (directive 5). The result must be exactly the delimiter-enclosing
   assembly `subsNotationLatex body subsList` — in particular the body is
   wrapped in its own enclosing delimiter pair, not emitted bare. -/
method renderSubsNotation (body : List Char) (subsList : List Char) return (out : List Char)
  ensures out = subsNotationLatex body subsList
  do
    -- impl-start
    -- Pre-image skeleton: the body is emitted bare between the evaluation
    -- delimiter and the bar, WITHOUT its own enclosing `\left( ... \right)`
    -- pair. The frozen spec requires subsNotationLatex (which encloses the
    -- body), so prove_correct MUST fail.
    let out : List Char :=
      "\\left. ".toList ++ body
        ++ " \\right|_{\\substack{ ".toList ++ subsList
        ++ " }}".toList
    return out
    -- impl-end

prove_correct renderSubsNotation by
  loom_solve
  simp [subsNotationLatex]
