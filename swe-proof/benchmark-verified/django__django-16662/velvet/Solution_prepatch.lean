import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms.) The single operation under specification — ordering a
-- collection of import-statement lines — is modeled DEEPLY below: the token
-- split, the per-character ordering, and the stable sort are all spelled out.
-- The two unchanged primitives they stand in for (a whitespace token split and
-- a stable key-sort of a sequence) are validated as A-references against the
-- real standard-library primitives by axiom_check.py (G-AX); see mapping.md.
-- axioms-end

-- pure-start
/- An import-statement line is carried as its sequence of code points
   (`List Char`). A line is "qualified" when its first whitespace-delimited
   token is the word `from` (i.e. it brings named objects in from a module);
   otherwise it names a whole module directly. The public coding-style rule
   asks that whole-module lines be grouped ahead of qualified lines, and that
   within each group the ordering follows the module token. -/

/- The first whitespace-delimited token of a line. -/
def firstTok : List Char → List Char
  | [] => []
  | c :: cs => if c = ' ' then [] else c :: firstTok cs

/- Everything after the first whitespace-delimited token (its delimiter
   consumed). -/
def afterFirst : List Char → List Char
  | [] => []
  | c :: cs => if c = ' ' then cs else afterFirst cs

/- The second whitespace-delimited token: the module token the ordering keys
   on (the part after the leading keyword). -/
def moduleTok (l : List Char) : List Char := firstTok (afterFirst l)

/- A line is qualified iff its leading token is the word `from`. -/
def isQualified (l : List Char) : Bool := firstTok l == "from".toList

/- Lexicographic order on code-point sequences, by code point. Total: every
   pair is comparable, mirroring value comparison of the module tokens. -/
def lcharLe : List Char → List Char → Bool
  | [], _ => true
  | _ :: _, [] => false
  | a :: u, b :: v =>
      if a.val < b.val then true
      else if b.val < a.val then false
      else lcharLe u v

/- The ordering key: whole-module lines (`isQualified = false`) sort ahead of
   qualified lines (`isQualified = true`); within each group the module token
   under `lcharLe` decides the order. This is the composite-key comparison. -/
def keyLe (x y : List Char) : Bool :=
  if isQualified x = isQualified y then lcharLe (moduleTok x) (moduleTok y)
  else (isQualified x == false)

/- The fully ordered collection: a stable sort of the lines under `keyLe`. -/
def sortImports (l : List (List Char)) : List (List Char) := l.mergeSort keyLe
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method orderImportLines (imports : List (List Char)) return (out : List (List Char))
  ensures out = sortImports imports
  ensures List.Perm out imports
  do
    -- impl-start
    -- Pre-image skeleton: order ONLY by the module token, with no grouping of
    -- whole-module lines ahead of qualified lines. This is the behavior before
    -- the fix; the frozen spec (sortImports / keyLe) demands the grouping, so
    -- prove_correct MUST fail on the `out = sortImports imports` clause.
    let result := imports.mergeSort (fun x y => lcharLe (moduleTok x) (moduleTok y))
    return result
    -- impl-end

prove_correct orderImportLines by
  loom_solve
  · exact (List.mergeSort_perm imports (fun x y => lcharLe (moduleTok x) (moduleTok y)))
  · rfl
