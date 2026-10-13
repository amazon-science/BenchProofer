import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The reversal of a sequence of element keys: the reversal of its tail followed
   by its head. Front-recursive (one unfold per element) so a backward loop that
   appends the head element each step can discharge it (the Velvet fold pattern,
   plan §5.4). This is the deep model of the backward enumeration's net effect —
   spelled out as the reversal, not hidden behind a callee axiom. -/
def revSeq : List Int → List Int
  | []      => []
  | c :: cs => revSeq cs ++ [c]

@[grind] lemma revSeq_nil : revSeq [] = [] := rfl
@[grind] lemma revSeq_cons (c : Int) (cs : List Int) :
    revSeq (c :: cs) = revSeq cs ++ [c] := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Backward enumeration of an insertion-ordered collection of distinct element
   keys, observed through the traversal handles the operation hands back.

   `elements` is the forward enumeration — the keys in insertion order. One
   consumer obtains a handle and interrogates that one handle, in this order: it
   asks the handle ITSELF for one single element; then asks for `demand` further
   single elements one at a time; and afterwards asks the SAME handle, twice in a
   row, to yield everything it has left. Four further consumers each obtain their
   own fresh handle from the same, unchanged collection: one asks its handle for
   the element AT A POSITION, one simply asks its handle to yield everything, one
   tries to collect the elements BY POSITION — asking for the element at
   position 0, then 1, then 2, and so on, until the handle refuses — and one
   asks its handle TWICE OVER to supply the thing that is to be stepped, then
   counts how many DISTINCT things it is left holding, the handle included.

   The eight results are pinned together, because a self-consuming traversal is
   the observable being specified and no one of them determines it alone:

   * the handle answers a single-element request BY ITSELF: the consumer puts
     that request to the very handle it was handed — not to some further
     traversal it first derives from it — and receives an element, not a
     refusal. The element received is the FIRST element of the backward
     enumeration, i.e. the LAST element of the forward one; only for an empty
     collection does the handle answer that it has nothing to give. So the
     handle IS the traversal: it advances itself, one element per request, and a
     consumer holding it needs nothing further in order to take the elements one
     at a time;
   * the `demand` further single elements drawn one at a time are the ones that
     FOLLOW, in the backward enumeration, the element the handle has already
     given — the handle resumes from where its own answer left it (element k of
     the backward enumeration is element (n-1-k) of the forward one), and asking
     past the end simply yields fewer;
   * what the same handle yields afterwards is the REST — so the handle carries
     its own progress: the elements already drawn one at a time are gone from
     it, and no element is repeated or skipped across the boundary between the
     two ways of asking;
   * asking that same, now-spent handle a second time yields nothing at all —
     the traversal is one-shot rather than re-startable, so a consumer cannot
     obtain the elements twice from one handle;
   * a request for the element AT A POSITION is refused, and refused on a handle
     that is holding every element it will ever give: the handle has no positions
     to be read at, only the place it has currently reached, so there is no way
     to take an element from it except by advancing it;
   * a handle that is asked to yield everything WITHOUT first being asked to
     advance yields the whole backward enumeration, in that order — the elements
     are already there to be had, so the handle is a traversal that has not
     started rather than one that has nothing to give until it is stepped;
   * a consumer that tries to collect the elements BY POSITION — taking the
     element at position 0, then 1, then 2, and so on until the handle refuses,
     which is the OTHER way a consumer is allowed to obtain the elements of
     something that has positions — collects NOTHING WHATEVER, however many
     elements the collection holds. The positional refusal is therefore total
     rather than confined to the one position asked about above: the handle
     serves no position, so position-by-position collection is not merely
     awkward but unavailable, and the only channel that ever yields an element
     is advancing the handle.
   * a consumer that asks its handle to supply THE THING IT IS TO STEP — the
     request every consumer makes before it starts drawing, and the one a
     for-each walk makes on its behalf — is handed the handle ITSELF, and is
     handed it again if it asks a second time. So of the handle and the two
     answers it gave, the consumer is left holding exactly ONE distinct thing.
     This is what the previous observation cannot say: it reports which of the
     two channels — advancing, or reading at a position — produced elements,
     whereas this one reports WHAT the handle nominates as the thing to be
     stepped, which is the fact that makes the handle a traversal in its own
     right rather than a source a traversal is spun off from. A handle that
     nominates something OTHER than itself — a separate walker built over it, so
     that the consumer ends up holding a second and a third distinct thing —
     is not the traversal a consumer was handed; it is a container standing
     behind one, and the count is 3 rather than 1. Counting is deliberate: it
     leaves the handle no way to be right about this by declining one question,
     since the answer is a fact about which OBJECT comes back, not about which
     requests are honoured.

   Together these say the handle is a self-advancing, single-use traversal
   positioned by what has already been taken from it — one that answers the
   single-element request itself, that nominates ITSELF as the thing a consumer
   steps, that cannot be read at a position instead of being advanced NOR
   collected position by position, that yields its whole enumeration to a
   consumer who only drains it, and that is not a re-readable snapshot of the
   elements, which would answer the later questions with the whole sequence over
   again. The collection's own contents are read-only throughout: `elements` is
   never mutated. -/
method reverseEnum (elements : List Int) (demand : Nat)
    return (out : Option Int × List Int × List Int × List Int × Option Int ×
                  List Int × List Int × Nat)
  ensures out.1 = (revSeq elements).head?
  ensures out.2.1 = List.take demand (revSeq elements).tail
  ensures out.2.2.1 = List.drop demand (revSeq elements).tail
  ensures out.2.2.2.1 = []
  ensures out.2.2.2.2.1 = none
  ensures out.2.2.2.2.2.1 = revSeq elements
  ensures out.2.2.2.2.2.2.1 = []
  ensures out.2.2.2.2.2.2.2 = 1
  do
    -- impl-start
    -- Pre-image skeleton: the collection exposes no backward enumeration and no
    -- positional access, so the only traversal available hands the elements back
    -- in the FORWARD (insertion) order. That forward handle is itself a proper
    -- traversal — it nominates itself as the thing a consumer steps — so the
    -- last observation is the same 1 it is for a backward one; nothing about the
    -- handle's shape distinguishes the pre-image. Observing those handles the
    -- same eight ways still yields the forward order, which the frozen spec's
    -- reversal clauses reject, so prove_correct MUST fail (the spec sensing the
    -- absence of a backward enumeration).
    let mut result : List Int := []
    let mut i := 0
    while i < elements.length
      invariant 0 ≤ i ∧ i ≤ elements.length
      invariant result = elements.take i
      done_with i = elements.length
      decreasing elements.length - i
    do
      let e := elements[i]!
      result := result ++ [e]
      i := i + 1
    let given := result.head?
    let remaining := result.tail
    let mut j := 0
    while j < demand ∧ j < remaining.length
      invariant j ≤ demand
      invariant j ≤ remaining.length
      done_with j = demand ∨ j = remaining.length
      decreasing demand - j
    do
      j := j + 1
    let drawn := List.take j remaining
    let mut k := j
    while k < remaining.length
      invariant j ≤ k ∧ k ≤ remaining.length
      done_with k = remaining.length
      decreasing remaining.length - k
    do
      k := k + 1
    let firstDrain := List.drop j remaining
    let secondDrain := List.drop k remaining
    let positional : Option Int := none
    let freshDrain := result
    let byPosition : List Int := []
    let heldDistinct : Nat := 1
    return (given, drawn, firstDrain, secondDrain, positional, freshDrain,
      byPosition, heldDistinct)
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `revSeq` peels one head off the end of its output.
   This is the single goal `loom_solve` leaves for the backward loop body. -/
lemma revSeq_drop_step (elements : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ elements.length) :
    revSeq (elements.drop (i - 1)) = revSeq (elements.drop i) ++ [elements[i - 1]!] := by
  have hlt : i - 1 < elements.length := by omega
  have hcons : elements.drop (i - 1) = elements[i - 1]! :: elements.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, revSeq_cons]

prove_correct reverseEnum by
  loom_solve
  all_goals
    (try (rw [List.take_succ, List.getElem?_eq_getElem (by omega),
              Option.toList_some, List.getElem!_eq_getElem?_getD,
              List.getElem?_eq_getElem (by omega), Option.getD_some]))
  all_goals (try simp_all)
  all_goals (try omega)
  all_goals (try rfl)
  all_goals (try grind)
