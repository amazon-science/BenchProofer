import Velvet.Std
-- imports-end

-- Total correctness: assembling the inserted lines is a straight-line
-- computation over finite inputs that always terminates and returns, so a
-- diverging implementation must NOT satisfy the spec (partial correctness
-- would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The registered text transform applied while inserting
--  spliced-in content is an ARBITRARY consumer-supplied function — modeled as the
--  universally-quantified parameter `transform`, about which the spec assumes
--  nothing. The downstream consumer of the assembled lines behaves identically on
--  the produced lines, so it is out of frame.)
-- axioms-end

-- pure-start
/- The host language's line-boundary set: LF, VT, FF, CR, FS, GS, RS, NEL,
   LINE SEPARATOR, PARAGRAPH SEPARATOR. -/
def isLineBreak (c : Char) : Bool :=
  c == '\n' || c == '\x0b' || c == '\x0c' || c == '\r' ||
  c == '\x1c' || c == '\x1d' || c == '\x1e' || c == '\x85' ||
  c == ' ' || c == ' '

/- Worker: accumulate the current line (reversed) while scanning; a CR
   immediately followed by LF is a single line boundary; a trailing line
   boundary produces no extra empty field. -/
def splitLinesAux : List Char → List Char → List (List Char)
  | cur, [] => if cur == [] then [] else [cur.reverse]
  | cur, '\r' :: '\n' :: rest => cur.reverse :: splitLinesAux [] rest
  | cur, c :: rest =>
    if isLineBreak c then cur.reverse :: splitLinesAux [] rest
    else splitLinesAux (c :: cur) rest

/- Split a character sequence into lines at the host language's line
   boundaries (isLineBreak, with CR-LF a single boundary), dropping the empty
   field a terminating boundary would produce. This is the value-level model
   of the host language's line splitter on ARBITRARY text — total on the full
   character domain, because it is applied to the output of the
   universally-quantified `transform`, which may emit any character:
   `""` ↦ `[]`, `"a\nb"` ↦ `["a","b"]`, `"a\nb\n"` ↦ `["a","b"]`,
   `"\n"` ↦ `[""]`, `"a\r\nb"` ↦ `["a","b"]`, `"a\rb"` ↦ `["a","b"]`.
   See mapping.md §3.1 for the provenance and reference vectors. -/
def splitLines (s : List Char) : List (List Char) :=
  splitLinesAux [] s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the line sequence to hand to the line inserter when separate
   content is being spliced in, while a content transform is registered.

   The trailing two entries of `lines` are structural end-markers introduced by
   the line reader; they carry no document content and MUST survive untouched.
   Everything before them is the document content: it is re-joined into a single
   text, offered to the registered `transform`, and the (possibly rewritten)
   text is split back into lines. The two end-markers are then reattached
   verbatim.

   `transform` and `lines` are read-only inputs (directive 5): neither is `mut`,
   and the two end-markers are pinned unchanged in the postcondition's tail
   (`lines.drop (lines.length - 2)`) — the result's frame outside the content is
   exactly the original markers. This is the behavior an arbitrary registered
   transform must observe on inserted content, for every `transform`. -/
method assembleInsertedLines
    (transform : List Char → List Char) (lines : List (List Char))
    return (out : List (List Char))
  ensures out =
    splitLines (transform (List.intercalate ['\n'] (lines.dropLast.dropLast)))
      ++ lines.drop (lines.length - 2)
  do
    -- impl-start
    let content := lines.dropLast.dropLast
    let text := transform (List.intercalate ['\n'] content)
    let assembled := splitLines text ++ lines.drop (lines.length - 2)
    return assembled
    -- impl-end

prove_correct assembleInsertedLines by
  loom_solve
