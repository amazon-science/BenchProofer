"""Twin-artifact model for django__django-11211.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stored value is prepared for use as the lookup key of a globally
  unique identifier field, the prepared key must MATCH the key the target
  record contributes on the other side of the in-Python join a deferred
  relation traversal performs across a heterogeneous holder and its target.

  That join compares keys with the host language's equality, and the target
  side always holds its identifier in the CANONICAL OBJECT FORM, keyed by the
  canonical identity. That equality is sensitive to the FORM as well as to the
  identity: a key not held in the canonical object form never compares equal to
  one that is, however its numeric part reads. Both halves of the target's key
  therefore have to be delivered.

  Concretely: preparing any non-empty value yields a key that is (a) in the
  canonical object form (``Result().is_canon_form``) and (b) numerically the
  canonical identity the value denotes (``Result().key == value.canon``) —
  independent of how that value was stored, so a value held in its textual
  storage form and the same identity held in its already-canonical object form
  prepare to the SAME matchable key. A bare ``None`` (no identity stored)
  prepares to a bare ``None`` key, unchanged in every facet.

A value is modelled as a minimal class carrying only the facets the join
observes: the canonical identity it denotes (``canon``); whether it is held in
the canonical object form (``is_canon_form``) — the form half of its join key;
and the numeric part of the join key its *current* storage form yields
(``key``). Two keys match in the join iff their emptiness, their form flag AND
their numeric part all agree, which is why the form flag is load-bearing: the
numeric part alone cannot tell a canonical identifier apart from a plain number
spelling the same 128 bits, and the real join can. For an already-canonical
value ``key`` and ``canon`` coincide; for a textual storage form they need not.
Two unchanged callees the field invokes are axiomatized: the base preliminary-
coercion step (identity on the relevant facets) and the canonicalizing parser
(yields a value in the canonical object form whose numeric key is the canonical
identity).

Total correctness: preparing a key is bounded, loop-free work that must
actually complete and deliver its result. Nagini checks partial correctness
by default — a diverging body would satisfy every postcondition vacuously —
so every function carries a ``MustTerminate`` obligation (with strictly
decreasing measures for callees) to reject non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Value:
    def __init__(self, is_none: bool, canon: int, key: int,
                 is_canon_form: bool) -> None:
        # Terminates: field initialisation is straight-line work; measure 2
        # lets any caller holding a larger measure construct a value without
        # leaking its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_none) and self.is_none == is_none)          # type: ignore
        Ensures(Acc(self.canon) and self.canon == canon)                # type: ignore
        Ensures(Acc(self.key) and self.key == key)                      # type: ignore
        Ensures(Acc(self.is_canon_form) and                             # type: ignore
                self.is_canon_form == is_canon_form)                    # type: ignore
        self.is_none = is_none
        self.canon = canon
        self.key = key
        self.is_canon_form = is_canon_form


# axioms-start
@ContractOnly
def base_prepare(value: Value) -> Value:
    """The unchanged base preliminary-coercion step the field defers to first.
    On the values this field receives it is the identity on every relevant
    facet: it casts a lazy proxy to its concrete value and otherwise returns
    the value unchanged, so the canonical identity, the numeric part of the
    current join key, the form the value is held in and the emptiness flag are
    all preserved. It is bounded, loop-free work, so it always terminates
    (measure 6, strictly below its caller's, so a body holding the caller's
    obligation can invoke it without leaking it). Provenance + executable
    soundness: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(6))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    Ensures(Result().key == value.key)
    # The form the value is held in is untouched by this step: it neither
    # canonicalizes nor de-canonicalizes.
    Ensures(Result().is_canon_form == value.is_canon_form)


@ContractOnly
def canonicalize(value: Value) -> Value:
    """The unchanged canonicalizing parser the field reuses. It interprets any
    non-empty storage form of an identity and returns that identity IN ITS
    CANONICAL OBJECT FORM — so the result carries the canonical form flag, and
    its numeric join key is, by construction, the canonical identity itself. An
    empty value passes through unchanged, form flag included. Parsing a bounded
    storage form is bounded work, so it always terminates (measure 10, strictly
    below its caller's, so a body holding the caller's obligation can invoke it
    without leaking it). Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(MustTerminate(10))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    # A non-empty value comes back in the canonical object form ...
    Ensures(Implies(not value.is_none, Result().is_canon_form))
    # ... and the canonical form's numeric join key is the canonical identity
    # it denotes.
    Ensures(Implies(not value.is_none, Result().key == value.canon))
    # An empty value is handed straight back, in the same form.
    Ensures(Implies(value.is_none, Result().key == value.key))
    Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
# axioms-end


# pure-start
@Pure
def matches_target_key(prepared: Value, identity: int) -> bool:
    """The join predicate, spelled out: does ``prepared``, used as the holder
    side of the in-Python join, compare EQUAL to the key the target record
    whose canonical identity is ``identity`` contributes?

    The target side is a stored record's own identifier: never empty, always
    held in the canonical object form, and numerically its canonical identity.
    The host language's equality on keys compares form first, so all three
    facets must agree — a prepared key that is numerically right but not held
    in the canonical object form does NOT match, and the traversal yields
    nothing.
    """
    Requires(Acc(prepared.is_none, 1 / 8) and Acc(prepared.key, 1 / 8) and
             Acc(prepared.is_canon_form, 1 / 8))
    return (not prepared.is_none) and prepared.is_canon_form and \
        prepared.key == identity
# pure-end


def prepare_key(value: Value) -> Value:
    # pre-conditions-start
    # TERMINATION: preparing a key is a bounded, loop-free composition of two
    # always-terminating steps and MUST actually complete (total correctness).
    # Under partial-correctness semantics a diverging body (e.g. an endless
    # loop before the return) satisfies every Ensures clause only vacuously
    # yet never delivers the prepared key to its caller; the real preparation
    # always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(14))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    # Faithfulness: the prepared value still denotes the same identity and the
    # same emptiness; preparation must not invent or drop an identity.
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    # THE DISCRIMINATING GUARANTEE, both halves of the target's key. For any
    # non-empty value the prepared key must be the key a target record whose
    # canonical identity is value.canon contributes: held in the canonical
    # object form AND numerically that canonical identity. The two clauses
    # below are the halves; the third states them as the join predicate they
    # exist to satisfy, so the guarantee cannot be met by a key that merely
    # reads the right number while being held in some other form.
    Ensures(Implies(not value.is_none, Result().is_canon_form))
    Ensures(Implies(not value.is_none, Result().key == value.canon))
    Ensures(Implies(not value.is_none, matches_target_key(Result(), value.canon)))
    # An empty value prepares to an empty key, unchanged in every facet.
    Ensures(Implies(value.is_none, Result().key == value.key))
    Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: the field has no preparation of its own and inherits
    # only the base preliminary-coercion step — the canonicalizing parser is
    # never reached, so a textual storage form keeps its as-stored join key and
    # stays in the form it was stored in, matching nothing on the target side.
    return base_prepare(value)
    # impl-end
