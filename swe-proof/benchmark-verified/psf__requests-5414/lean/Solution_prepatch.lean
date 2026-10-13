import Mathlib
-- imports-end

/-!
Validating the host component of a requested URL.

Before a parsed host string is used to build a network location, it is checked
and, when necessary, re-encoded:

  * A host that contains any non-ASCII code point is handed to a standard
    internationalized-domain-name encoder. If that encoder accepts the name, the
    encoded form is carried forward; if it rejects the name, the host is invalid.
  * A host whose code points are all ASCII is accepted unchanged, UNLESS it
    begins with a reserved leading character — namely a wildcard marker (`*`) or
    an empty leading label introduced by a leading dot (`.`) — in which case the
    host is invalid.

We model the outcome as `Except Unit (List Char)`: `Except.error ()` is the
single "invalid host" rejection (both rejection sites raise the same error), and
`Except.ok h` carries forward the accepted host `h`.
-/

-- axioms-start
/-- A standard internationalized-domain-name encoder applied to a host that
contains non-ASCII code points. It either returns an encoded host (`Except.ok`)
or rejects the name (`Except.error ()`). It is an unchanged outside callee; the
specification constrains none of its inner behavior, only its result shape. -/
opaque idnaEncode : List Char → Except Unit (List Char)
-- axioms-end

-- pure-start
/-- Whether every code point of the host is ASCII (numeric value `< 128`). -/
def isAscii (host : List Char) : Bool :=
  host.all (fun c => decide (c.toNat < 128))

/-- Whether the host begins with a reserved leading character: a wildcard marker
(`*`) or a leading dot (`.`) that would introduce an empty leading label. The
empty host begins with neither. -/
def startsWithInvalid (host : List Char) : Bool :=
  match host with
  | [] => false
  | c :: _ => c == '*' || c == '.'
-- pure-end

-- post-conditions-start
/-- The validation outcome for a parsed host. For an all-ASCII host: rejected
(`Except.error ()`) iff it begins with a reserved leading character, otherwise
accepted unchanged (`Except.ok host`). For a host with non-ASCII code points: the
result is exactly the internationalized-domain-name encoder's outcome on it. -/
def problem_spec_validateHost
    (host : List Char) (result : Except Unit (List Char)) : Prop :=
  if isAscii host then
    (if startsWithInvalid host then result = Except.error () else result = Except.ok host)
  else
    result = idnaEncode host
-- post-conditions-end

-- impl-start
def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
  Id.run do
    let mut h := host
    if !isAscii host then
      match idnaEncode host with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()
    else if (match host with | [] => false | c :: _ => c == '*') then
      return Except.error ()
    return Except.ok h
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- implementation it cannot close: an all-ASCII host beginning with a leading dot
-- (e.g. `.example.com`) is accepted here (`Except.ok`) while the specification
-- requires it be rejected (`Except.error ()`) — the discriminating clause.
theorem correct_validateHost :
    ∀ (host : List Char),
      problem_spec_validateHost host (implementation_validateHost host) := by
  sorry
-- proof-end
