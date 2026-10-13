import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The rendering of each individual member of the sequence is produced by the
   surrounding recursive renderer, which this operation does NOT change. It is
   therefore treated as opaque already-rendered text: the member renderings are
   the arbitrary inputs `elts`, about which the specification assumes nothing.
   This operation's behavior depends only on HOW those member renderings are
   wrapped and separated as a function of how many there are — never on their
   content — so no callee contract is consumed (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The source rendering of a parenthesized comma-separated sequence, given the
   already-rendered text of each member, as a function of the member count:

     * no members      ↦  the empty pair `()`;
     * exactly one      ↦  the single member wrapped with a trailing comma,
                           `(m,)`, so the one-member sequence stays distinct
                           from the bare parenthesized member `(m)`;
     * two or more      ↦  the members joined by `", "`, wrapped in parens,
                           `(m₁, m₂, …)`.

   The separator joining adjacent members is the two characters comma-space. -/
def renderTuple (elts : List (List Char)) : List Char :=
  match elts with
  | []  => "()".toList
  | [e] => "(".toList ++ e ++ ",)".toList
  | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList

@[grind] lemma renderTuple_nil :
    renderTuple [] = "()".toList := rfl
@[grind] lemma renderTuple_single (e : List Char) :
    renderTuple [e] = "(".toList ++ e ++ ",)".toList := rfl
@[grind] lemma renderTuple_many (a b : List Char) (rest : List (List Char)) :
    renderTuple (a :: b :: rest) =
      "(".toList ++ List.intercalate ", ".toList (a :: b :: rest) ++ ")".toList := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the source form of a parenthesized comma-separated sequence from the
   already-rendered text of its members.

   The result is determined entirely by the member count. The two structural
   end cases — an empty sequence and a one-member sequence — are rendered
   specially: an empty sequence is the bare empty pair `()`, and a one-member
   sequence keeps a trailing comma after its single member, `(m,)`, so that it is
   not confused with a parenthesized member. Every longer sequence is its members
   joined by `", "` inside parentheses.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member renderings and builds a fresh result, mutating
   nothing. -/
method renderSequence (elts : List (List Char)) return (out : List Char)
  ensures out = renderTuple elts
  do
    -- impl-start
    -- Pre-image skeleton: a non-empty sequence is ALWAYS the members joined by
    -- ", " inside parens, with no separate one-member case — so a single member
    -- `m` renders as `(m)`, dropping the trailing comma the frozen spec requires
    -- (renderTuple [e] = "(e,)"). prove_correct MUST fail on the one-member case.
    let result : List Char :=
      if elts == [] then "()".toList
      else "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
    return result
    -- impl-end

prove_correct renderSequence by
  loom_solve
  rfl
