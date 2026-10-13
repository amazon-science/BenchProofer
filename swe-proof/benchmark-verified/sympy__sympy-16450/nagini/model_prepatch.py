"""Twin-artifact model for sympy__sympy-16450.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A free quantity whose sign is not yet decided is replaced, for the purpose of
  more aggressive symbolic processing, by a fresh stand-in quantity that is
  declared strictly greater than zero. The declaration the stand-in is built
  from is the union of

      * the new declaration "greater than zero" (always added), and
      * EVERY property the original quantity already stated about itself.

  The fresh quantity's effective properties are then EXACTLY whatever the
  standard property-inference engine derives from that combined declaration --
  no more and no less. The consequence that matters: any property the original
  quantity stated (for example, that it is bounded / not infinite, or that it
  is a whole number, rational, even, prime, ...) is part of the combined
  declaration, so the inference engine still derives it for the stand-in.
  Replacing the original quantity must therefore NOT silently discard a stated
  property, NOR fabricate any property the engine did not derive; the only
  declaration the replacement adds is "greater than zero".

  In particular: if the original quantity stated it is bounded (not infinite),
  the stand-in is still derived to be bounded; the replacement does not erase
  that, and the stand-in carries no spurious property beyond the engine's
  derivation.

Modelling choices (Nagini fragment):
  * A quantity's stated properties are a ``Dict[int, bool]`` from a
    property-name token to the truth value the quantity declares for it
    (``True`` / ``False``). A property absent from the map is simply unstated.
    Distinguished tokens: ``POSITIVE`` (the "greater than zero" declaration the
    replacement adds) and ``FINITE`` (the "bounded / not infinite" property the
    issue centres on); other tokens stand for any further stated property.
  * The property-inference engine that turns a declaration into the fresh
    quantity's effective properties is an unchanged callee. It is modelled as a
    pure mathematical function ``derived`` (the deterministic effective-property
    map of a declaration) paired with the effectful ``resolve`` that returns the
    engine's actual output object; ``resolve``'s result IS ``derived`` of its
    declaration, so the stand-in's properties are pinned to exactly the engine's
    derivation. ``resolve`` is given a base declaration (the original quantity's
    stated properties, which may be empty) and a flag for whether the new
    "greater than zero" property is added. Its relevant guarantees are that it
    never drops a fact in the base declaration, derives the added property when
    the flag is set, and yields exactly the engine's effective-property map
    (engine soundness validated against the real engine out-of-band by
    axiom_check.py / G-AX).
  * The engine's output is read, never mutated, by the replacement (the stand-in
    is built once and its properties are only consulted), so the result is held
    at fractional permission: the modelled operation may not overwrite or extend
    the engine's derivation.
  * The original quantity is the one being replaced precisely because it has
    NOT stated its sign, so ``POSITIVE`` is not among its stated properties; the
    added "greater than zero" therefore never conflicts with a stated property.

No string indexing is used (Nagini bans it). Dict access is guarded by an
explicit membership test before subscription. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def derived(base: Dict[int, bool], add_positive: bool) -> Dict[int, bool]:
    """The standard property-inference engine as a pure mathematical function:
    the deterministic map from a declaration to the effective (derived)
    properties. The declaration is the ``base`` map together with, when
    ``add_positive`` holds, the new "greater than zero" property. This pins what
    the effective properties of a stand-in built from that declaration ARE --
    the engine's derivation and nothing else (release-specific closure content
    is left abstract; only that the result is exactly this map). Provenance +
    executable soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 4))
    Requires(Implies(add_positive, not (POSITIVE() in base)))


@ContractOnly
def resolve(base: Dict[int, bool], add_positive: bool) -> Dict[int, bool]:
    """The standard property-inference engine (the unchanged callee that derives
    a quantity's effective properties from a declaration) as the effectful call
    that returns the engine's actual output object. The declaration is the
    ``base`` map together with, when ``add_positive`` holds, the new "greater
    than zero" property. Guarantees the proof needs: the engine's output IS the
    pure effective-property map ``derived(base, add_positive)`` (so the
    stand-in's properties are exactly the engine's derivation -- no fact is
    dropped and none is fabricated), each ``base`` key is derived with the same
    truth value, and "greater than zero" is derived exactly when asked. The
    ``base`` map is read-only; the engine's output is itself read-only to the
    caller (fractional permission). Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(Implies(add_positive, not (POSITIVE() in base)))
    Requires(MustTerminate(2))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Implies(add_positive, not (POSITIVE() in base)))
    # The engine's output is read-only to the caller (it is consulted, never
    # mutated), so only fractional permission is yielded.
    Ensures(Acc(dict_pred(Result()), 1 / 2))
    # The result IS the engine's pure effective-property map: exactly its
    # derivation, with no key added, removed, or altered by the operation.
    Ensures(Result() is derived(base, add_positive))
    # The engine carries every fact stated in the base declaration unchanged.
    Ensures(Forall(int, lambda k: (Implies(k in base,
                                           (k in Result()) and Result()[k] == base[k]))))
    # The added "greater than zero" is derived exactly when requested.
    Ensures(Implies(add_positive, (POSITIVE() in Result()) and Result()[POSITIVE()] == True))
# axioms-end


# pure-start
@Pure
def POSITIVE() -> int:
    # token for the "greater than zero" declaration the replacement adds
    return 0


@Pure
def FINITE() -> int:
    # token for the "bounded / not infinite" property the issue centres on
    return 1
# pure-end


def positive_standin_properties(stated: Dict[int, bool]) -> Dict[int, bool]:
    # pre-conditions-start
    Requires(Acc(dict_pred(stated), 1 / 2))
    # The quantity is replaced precisely because its sign is undecided, so it
    # has not stated POSITIVE about itself.
    Requires(not (POSITIVE() in stated))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(stated), 1 / 2))
    Ensures(not (POSITIVE() in stated))
    # The stand-in's effective properties are read-only (the engine's output is
    # consulted, not mutated): fractional permission on the result.
    Ensures(Acc(dict_pred(Result()), 1 / 2))
    # Totality / closure clause: the replacement's effective properties are
    # EXACTLY the engine's derivation of the combined declaration -- no property
    # is fabricated and none beyond the engine's output is carried. This pins
    # the whole result (including engine-derived keys the quantity never stated),
    # so an implementation cannot add, drop, or alter any derived property.
    Ensures(Result() is derived(stated, True))
    # The replacement is declared greater than zero, and the engine derives it.
    Ensures(POSITIVE() in Result() and Result()[POSITIVE()] == True)
    # Discriminating clause: EVERY property the original quantity stated is
    # carried into the replacement's effective properties with the same truth
    # value -- none is silently discarded. In particular a stated FINITE
    # survives the replacement.
    Ensures(Forall(int, lambda k: (Implies(k in stated,
                                           (k in Result()) and Result()[k] == stated[k]))))
    # post-conditions-end
    # impl-start
    # Pre-patch (buggy) skeleton: the stand-in is built from ONLY the added
    # "greater than zero", discarding the original quantity's stated properties
    # -- the empty base map reaches the engine instead of `stated`.
    empty = {}  # type: Dict[int, bool]
    return resolve(empty, True)
    # impl-end
