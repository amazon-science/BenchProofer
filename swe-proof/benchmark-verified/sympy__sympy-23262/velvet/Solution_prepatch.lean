import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axioms and no deep-model references in this bundle. The routine assembles
--  the rendered text of a sequence purely from the already-rendered texts of
--  its elements: it joins them with a comma-and-space separator and wraps them
--  in the delimiter pair appropriate to the sequence kind. The element
--  renderings are read-only inputs (the result of an unchanged recursive
--  descent, modeled abstractly as opaque element texts — refinement.md A1), so
--  the proof assumes nothing about how they were produced; both the join and
--  the wrap are modeled concretely (`joinComma`/`renderSeq`), not consumed as
--  axioms. The whole assembly IS the modeled behaviour, so it is validated by
--  the differential conformance check (G-CONF), not by an axiom soundness check
--  (there is no unchanged callee to axiomatize). See refinement.md §C /
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- Join a list of already-rendered element texts with a comma-and-space
   separator — the separator appears strictly between adjacent elements, never
   leading or trailing. Front-recursive so the single-element and multi-element
   cases are settled definitionally (the empty list joins to the empty text, a
   one-element list to that element verbatim). -/
def joinComma : List (List Char) → List Char
  | []        => []
  | [s]       => s
  | s :: rest => s ++ ", ".toList ++ joinComma rest

@[grind] lemma joinComma_nil : joinComma [] = [] := rfl
@[grind] lemma joinComma_single (s : List Char) : joinComma [s] = s := rfl

/- The rendered text of a whole sequence: its elements joined with comma-space,
   wrapped in the delimiter pair for the sequence kind. A bracketed sequence
   (`isList = true`) opens with `[` and closes with `]`. A parenthesized
   sequence (`isList = false`) opens with `(` and closes with `)` PRECEDED by a
   comma, so that a sequence carrying a single element renders unambiguously as
   a sequence rather than as its bare element. The opening delimiter, the joined
   body, and the closing delimiter are concatenated in that order. -/
def renderSeq (isList : Bool) (elems : List (List Char)) : List Char :=
  let openD  := if isList then "[".toList else "(".toList
  let closeD := if isList then "]".toList else ",)".toList
  openD ++ joinComma elems ++ closeD
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a sequence of already-rendered element texts into its delimited form.

   `isList` selects the sequence kind: `true` for a bracketed sequence, `false`
   for a parenthesized sequence. `elems` is the read-only list of element texts,
   in order; neither input is mutated (directive 5). The body joins the element
   texts with a comma-and-space separator and wraps the result in the opening
   and closing delimiters for the kind. For a parenthesized sequence the closing
   delimiter carries a comma before the closing parenthesis, so that a sequence
   of exactly one element is still rendered as a sequence (the trailing comma is
   what distinguishes a one-element parenthesized sequence from a parenthesized
   single value). The element texts and their order are modeled as exact
   `List Char` (per-code-point faithful, mapping.md §2); the result is pinned
   exactly as `renderSeq`. -/
method renderSequence (isList : Bool) (elems : List (List Char))
    return (out : List Char)
  ensures out = renderSeq isList elems
  do
    -- impl-start
    -- Pre-image skeleton: the closing delimiter for a parenthesized sequence is
    -- the bare closing parenthesis, with NO comma before it (the delimiter pair
    -- was taken as the two characters of "()", splitting into "(" and ")"). The
    -- frozen spec requires the closing delimiter to carry a comma (renderSeq for
    -- a parenthesized sequence closes with ",)"), so a one-element parenthesized
    -- sequence renders without its distinguishing trailing comma and
    -- prove_correct MUST fail.
    let openD  := if isList then "[".toList else "(".toList
    let closeD := if isList then "]".toList else ")".toList
    let out := openD ++ joinComma elems ++ closeD
    return out
    -- impl-end

prove_correct renderSequence by
  loom_solve
  simp_all [renderSeq]
