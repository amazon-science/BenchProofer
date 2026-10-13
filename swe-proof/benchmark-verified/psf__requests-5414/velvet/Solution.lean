import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The acceptance decision is a pure property of the
--  candidate host's leading code point, modeled deeply in the `pure` region.
--  The all-ASCII screen `isAsciiHost` is a deep model of the unchanged
--  community predicate that selects this code path; it is validated against
--  that real predicate by axiom_check.py (G-AX) as an A-reference, NOT a
--  consumed axiom — it appears only in a `require` to scope the decision to the
--  all-ASCII case, and the proof never relies on its internal structure.)
-- axioms-end

-- pure-start
/- Whether every code point of the host is in the 7-bit ASCII range
   (code point < 128). Front-recursive so a single unfold is available per
   element (the Velvet fold pattern). This selects the all-ASCII handling path
   for a host string. -/
def isAsciiHost : List Char → Bool
  | []      => true
  | c :: cs => decide (c.toNat < 128) && isAsciiHost cs

@[grind] lemma isAsciiHost_nil : isAsciiHost [] = true := rfl
@[grind] lemma isAsciiHost_cons (c : Char) (cs : List Char) :
    isAsciiHost (c :: cs) = (decide (c.toNat < 128) && isAsciiHost cs) := rfl

/- The host carries an invalid leading label exactly when its first code point
   is the wildcard `*` (U+002A) or the label-separator `.` (U+002E). A label is
   the dot-delimited segment of a host; a host that opens with either of these
   code points has an empty or wildcard first label, which is not a valid host
   label. Decided purely from the head of the code-point sequence. -/
def startsWithInvalidLabel (host : List Char) : Bool :=
  host.head? == some '*' || host.head? == some '.'

/- An all-ASCII host is accepted exactly when it does NOT open with an invalid
   leading label; otherwise it is rejected. Expressed structurally over the
   input's leading code point. -/
def hostAccepted (host : List Char) : Bool :=
  !startsWithInvalidLabel host

@[grind] lemma hostAccepted_def (host : List Char) :
    hostAccepted host = !(host.head? == some '*' || host.head? == some '.') := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The leading-label acceptance decision for a host that is being handled along
   the all-ASCII path, modeled over its code-point sequence: accept (return
   `true`) iff the host does not open with an invalid leading label — i.e. its
   first code point is neither the wildcard `*` nor the separator `.`; otherwise
   reject (return `false`). A reject corresponds to signalling an invalid-URL
   condition at this point.

   `host` is read-only (not `mut`); the decision computes a single boolean and
   mutates nothing (directive 5). The host reaching this decision is non-empty
   (`require host.length > 0`) and entirely ASCII (`require isAsciiHost host`):
   these scope the decision to exactly the path this branch governs. Input is a
   code-point sequence (`List Char`); the result is a `Bool`. -/
method validateAsciiHostLabel (host : List Char) return (out : Bool)
  require host.length > 0
  require isAsciiHost host = true
  ensures out = hostAccepted host
  do
    -- impl-start
    -- Reject iff the host opens with an invalid leading label, i.e. its first
    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
    return !startsBad
    -- impl-end

prove_correct validateAsciiHostLabel by
  loom_solve
