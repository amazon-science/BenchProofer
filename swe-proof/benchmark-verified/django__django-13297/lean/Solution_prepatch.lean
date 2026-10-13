import Mathlib
-- imports-end

/-!
Deferring the URL keyword arguments that are handed to a template's context.

When a class-based template renderer receives the keyword arguments captured
from a URL route, those arguments are not placed into the template context
eagerly. Each one is wrapped in a DEFERRED value: the underlying value is only
produced the first time the wrapper is actually consumed, and producing it also
emits a one-time notice — keyed to that argument's name — announcing that
reaching these arguments through the context is being phased out.

A deferred wrapper must behave, to every downstream consumer, exactly like the
value it stands for. Concretely, for each captured argument the wrapper must:

  * resolve to precisely the original value (nothing added, nothing dropped);
  * carry the notice keyed to that same argument's name;
  * present the SAME type interface as the underlying value.

The last point is the one that matters in practice. A consumer that performs a
type-directed operation on the wrapper — passing it where a string, an integer,
etc. is expected — relies on the wrapper exposing the underlying value's type,
not some generic placeholder type. If the wrapper advertised only an opaque
deferred-object type, such a consumer would be handed something it cannot use.

The order of the captured arguments, and their names, are preserved exactly.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The act of
-- building a deferred wrapper is modeled structurally over the data each
-- captured argument carries (its name, its underlying value, and that value's
-- type identity); the resolved value and the keyed notice enter directly. Hence
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- One captured URL keyword argument's underlying value, restricted to the two
observable facets a deferred wrapper must preserve:
* `pytype` — the type identity of the value (an injective tag over the distinct
  runtime types; only equality of type identities is observed);
* `data`   — the value's content. -/
structure UrlValue where
  pytype : Nat
  data : String
deriving DecidableEq, Repr

/-- A deferred wrapper standing in for one captured argument's value:
* `presentedType` — the type identity the wrapper exposes to consumers;
* `resolved`      — the value produced when the wrapper is consumed;
* `noticeKey`     — the argument name the emitted notice is keyed to. -/
structure DeferredValue where
  presentedType : Nat
  resolved : UrlValue
  noticeKey : String
deriving Repr

/-- The per-argument contract a deferred wrapper must meet, relating one input
`(name, value)` pair to its output `(name, wrapper)` pair: the name is carried
through, the wrapper resolves to exactly the original value, its notice is keyed
to that name, and — the decisive facet — the type it presents to consumers is
the underlying value's own type identity. -/
def wrapsValue (inp : String × UrlValue) (out : String × DeferredValue) : Prop :=
  out.1 = inp.1 ∧
  out.2.resolved = inp.2 ∧
  out.2.noticeKey = inp.1 ∧
  out.2.presentedType = inp.2.pytype
-- pure-end

-- post-conditions-start
/-- The collection of deferred wrappers is fully pinned to the captured
arguments: it has the same length, the same order, and the same names, and each
wrapper meets the per-argument contract (`wrapsValue`) against the argument in
the matching position. `List.Forall₂` simultaneously pins the length, the
positional pairing (hence the order), and the element-wise relation, so no
output entry is left free. -/
def problem_spec_wrapContextKwargs
    (urlKwargs : List (String × UrlValue))
    (result : List (String × DeferredValue)) : Prop :=
  List.Forall₂ wrapsValue urlKwargs result
-- post-conditions-end

-- impl-start
/-- The opaque, generic deferred-object type identity: a single placeholder type
shared by every wrapper, independent of the value it stands for. -/
def genericDeferredType : Nat := 0

def implementation_wrapContextKwargs
    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do
  let mut context := []
  for (key, value) in urlKwargs do
    -- Bind this argument into a deferred wrapper that exposes only the generic
    -- deferred-object type identity, the same for every argument.
    let wrapper : DeferredValue := {
      presentedType := genericDeferredType,
      resolved := value,
      noticeKey := key }
    context := context ++ [(key, wrapper)]
  return context
-- impl-end

-- proof-start
theorem correct_wrapContextKwargs :
    ∀ (urlKwargs : List (String × UrlValue)),
      problem_spec_wrapContextKwargs urlKwargs
        (implementation_wrapContextKwargs urlKwargs) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
