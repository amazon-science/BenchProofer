import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees and no deep-model references.

   The rendering of each individual member of a sequence is produced by the
   surrounding recursive renderer, which neither modeled operation changes. Each
   member rendering is therefore treated as opaque already-rendered material: the
   member renderings are the arbitrary inputs `elts`, about which the
   specification assumes nothing. Both operations depend only on HOW those member
   renderings are wrapped and separated as a function of how many there are —
   never on their content — so no callee contract is consumed (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A single member rendering, when the result is a list of display tokens, is one
   list of tokens; each token is opaque text (`List Char`). A whole sequence's
   members is then a `List (List (List Char))`. -/

/- The display-token rendering of a comma-separated sequence, given the
   already-rendered tokens of each member, as a function of the member count:

     * no members  ↦  the two punctuation tokens of an empty pair, `(` then `)`;
     * one or more ↦  the members' token lists concatenated with a single
                      comma-space separator token placed BETWEEN adjacent
                      members (none at the ends).

   The separator between adjacent members is the single token comma-space. -/
def seqTokens (elts : List (List (List Char))) : List (List Char) :=
  match elts with
  | []  => ["(".toList, ")".toList]
  | _   => List.intercalate [", ".toList] elts

@[grind] lemma seqTokens_nil :
    seqTokens [] = ["(".toList, ")".toList] := rfl
@[grind] lemma seqTokens_cons (a : List (List Char)) (rest : List (List (List Char))) :
    seqTokens (a :: rest) = List.intercalate [", ".toList] (a :: rest) := rfl

/- The source-text rendering of a comma-separated sequence, given the
   already-rendered source text of each member, as a function of the member
   count:

     * no members  ↦  the empty pair `()`;
     * one or more ↦  the members' text joined by the two-character separator
                      comma-space, with no separator at the ends and no
                      surrounding wrapping.

   The separator between adjacent members is the two characters comma-space. -/
def seqText (elts : List (List Char)) : List Char :=
  match elts with
  | []  => "()".toList
  | _   => List.intercalate ", ".toList elts

@[grind] lemma seqText_nil :
    seqText [] = "()".toList := rfl
@[grind] lemma seqText_cons (a : List Char) (rest : List (List Char)) :
    seqText (a :: rest) = List.intercalate ", ".toList (a :: rest) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the display tokens of a comma-separated sequence from the
   already-rendered tokens of its members.

   The result is determined entirely by the member count. The empty sequence is
   the structural end case: it renders as the two punctuation tokens of an empty
   pair, `(` then `)`, rather than as no tokens at all. Every non-empty sequence
   is its members' token lists concatenated, with one comma-space separator token
   between adjacent members and none at the ends.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member token lists and builds a fresh result, mutating
   nothing. -/
method renderSequenceTokens (elts : List (List (List Char)))
    return (out : List (List Char))
  ensures out = seqTokens elts
  do
    -- impl-start
    let result : List (List Char) := match elts with
      | []  => ["(".toList, ")".toList]
      | _   => List.intercalate [", ".toList] elts
    return result
    -- impl-end

prove_correct renderSequenceTokens by
  loom_solve
  rfl

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the source text of a comma-separated sequence from the already-rendered
   source text of its members.

   The result is determined entirely by the member count. The empty sequence is
   the structural end case: it renders as the empty pair `()`, rather than as the
   empty string. Every non-empty sequence is its members' text joined by the
   comma-space separator, with no separator at the ends.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member text and builds a fresh result, mutating nothing. -/
method renderSequenceText (elts : List (List Char)) return (out : List Char)
  ensures out = seqText elts
  do
    -- impl-start
    let result : List Char := match elts with
      | []  => "()".toList
      | _   => List.intercalate ", ".toList elts
    return result
    -- impl-end

prove_correct renderSequenceText by
  loom_solve
  rfl
