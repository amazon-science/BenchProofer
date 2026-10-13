import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled decisions are changed functions whose
--  new logic is a pure boolean combination of their inputs, modeled deeply. The
--  per-element classification test at each site is UNCHANGED and is observed
--  only through its per-element boolean result, which is the input carrier — so
--  there is nothing to axiomatize and nothing to validate against a real callee
--  (no axiom_check.py; meta.json G-AX skip).)
-- axioms-end

-- pure-start
/- Whether every element of a sequence of per-element classification results is
   affirmative. Front-recursive over the list of results. The empty sequence is
   vacuously affirmative — `allTrue [] = true` — which is the crux: a universal
   quantification over no elements holds for every predicate. -/
def allTrue : List Bool → Bool
  | []      => true
  | b :: bs => b && allTrue bs

@[grind] lemma allTrue_nil : allTrue [] = true := rfl
@[grind] lemma allTrue_cons (b : Bool) (bs : List Bool) :
    allTrue (b :: bs) = (b && allTrue bs) := rfl

/- The decision to emit the advisory notice, given the per-element classification
   results for the supplied collection. The notice is emitted exactly when the
   collection is NON-EMPTY and every element's classification is affirmative.

   The non-emptiness condition is essential and is NOT implied by the affirmative
   aggregate: over an empty collection the aggregate is vacuously affirmative
   (`allTrue [] = true`), yet there is no element the advisory could meaningfully
   describe, so the notice must be withheld. The notice fires iff BOTH the
   collection has at least one element AND the aggregate is affirmative. -/
def noticeFires (flags : List Bool) : Bool :=
  !flags.isEmpty && allTrue flags

@[grind] lemma noticeFires_def (flags : List Bool) :
    noticeFires flags = (!flags.isEmpty && allTrue flags) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Site A. A string-to-number unit converter, given a collection of values,
   decides whether to emit a one-time advisory notice that numeric values are
   being routed through it. Each value contributes one classification result:
   affirmative iff that value is number-like and is not itself a textual value.
   The converter emits the advisory exactly when the collection is non-empty and
   every value's classification is affirmative; on an empty collection it emits
   nothing. The collection of results is read-only (not `mut`); this query
   computes a single boolean and mutates nothing (directive 5). -/
method numericNoticeFires (numlikeFlags : List Bool) return (out : Bool)
  ensures out = noticeFires numlikeFlags
  do
    -- impl-start
    -- Pre-image (site A): the converter emitted the advisory whenever the
    -- per-element aggregate was affirmative, WITHOUT requiring the collection to
    -- be non-empty. Over an empty collection the aggregate is vacuously
    -- affirmative, so this skeleton emits the advisory on empty input and MUST
    -- fail the frozen spec there (noticeFires [] = false).
    return allTrue numlikeFlags
    -- impl-end

prove_correct numericNoticeFires by
  loom_solve

/- Site B. A routine that maps a collection of textual labels to integer ids
   decides whether to emit a one-time advisory that the labels all look like
   numbers. Each unique label contributes one classification result: affirmative
   iff that label parses as a number or a date. The advisory is emitted exactly
   when the supplied collection is non-empty and every label's classification is
   affirmative; on an empty collection it emits nothing. The collection of
   results is read-only (not `mut`); this query computes a single boolean and
   mutates nothing (directive 5). -/
method numericLabelNoticeFires (parsableFlags : List Bool) return (out : Bool)
  ensures out = noticeFires parsableFlags
  do
    -- impl-start
    -- Emit only over a non-empty collection whose every label classifies
    -- affirmatively; the empty collection yields no advisory.
    return !parsableFlags.isEmpty && allTrue parsableFlags
    -- impl-end

prove_correct numericLabelNoticeFires by
  loom_solve
