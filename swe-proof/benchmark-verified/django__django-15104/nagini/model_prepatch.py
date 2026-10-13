"""Twin-artifact model for django__django-15104.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the rename detector reduces a field's deconstructed keyword mapping to
  the relation-agnostic form, it must DROP the related-target keyword (the key
  whose value names what a relation points at, written `to` below) so that two
  otherwise-identical relations that merely point at different targets compare
  equal. Dropping that keyword must be applicable to EVERY input mapping the
  detector is given -- including a mapping that does not carry the target
  keyword at all (a relation field whose deconstruction legitimately omits it).
  The reduction must never be undefined on such an input.

  Concretely, for a field that participates in a relation (the relation flag
  below is true), the resulting mapping:
    * never carries the target keyword;
    * carries every OTHER keyword the input mapping had, with the same value;
    * carries no keyword the input mapping did not have.
  For a field that does not participate in a relation, the resulting mapping is
  the input mapping unchanged: every keyword -- including the target keyword, if
  any -- survives with its value.

Modelling choices (Nagini fragment):
  * A deconstructed keyword mapping is a ``Dict[int, int]`` from a keyword-name
    token to an opaque value token; only membership and per-name value are
    observed, so integer-keyed/valued identity is the faithful carrier
    (mapping.md §2). ``TO`` is the token for the related-target keyword.
  * The reduction is modelled functionally: the relation-agnostic mapping is
    returned and related directly to the input, so the input is READ-ONLY and
    held at fractional permission (directive 5). (The detector edits the
    deconstruction in place and keeps it; returning the equal mapping is
    observationally identical for the value comparison the detector performs --
    refinement.md, tag R.)
  * Two keyword-removal primitives are modelled deeply as the A-reference
    callees ``pop_default`` (applicable to any mapping) and ``del_present``
    (applicable only to a mapping that already carries the named keyword, its
    precondition ``k in d``). Both are validated against real Python out-of-band
    (axiom_check.py, G-AX). The contracted function uses the broadly-applicable
    primitive; the surrounding field iteration is identical and elided.
  * The reduction is a bounded, straight-line computation and MUST terminate
    (a total-correctness obligation, carried as ``MustTerminate`` in the
    precondition). Nagini is a partial-correctness verifier by default, so
    without this obligation a non-terminating implementation (e.g. bare
    self-recursion) satisfies every ``Ensures`` vacuously; the real reduction
    always delivers its relation-agnostic mapping to the detector.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def del_present(d: Dict[int, int], k: int) -> Dict[int, int]:
    """Keyword removal whose contract is applicable only to a mapping that
    already carries ``k`` (precondition ``k in d``): it returns a fresh mapping
    equal to ``d`` with exactly ``k`` removed, every other keyword/value
    preserved and none introduced; ``d`` is read-only. A deep model of one
    keyword-removal primitive (A-reference). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 2))
    Requires(k in d)
    # The real `del d[k]` is a single bounded primitive step; the strictly
    # smaller measure (1 < 2) lets the contracted caller holding
    # MustTerminate(2) invoke it without leaking its own obligation.
    Requires(MustTerminate(1))
    Ensures(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(Result()), 1 / 4))
    Ensures(Result() is not None)
    Ensures(k not in Result())
    Ensures(Forall(int, lambda j: Implies(j != k and j in d,
                                          j in Result() and Result()[j] == d[j])))
    Ensures(Forall(int, lambda j: Implies(j in Result(),
                                          j != k and j in d and Result()[j] == d[j])))


@ContractOnly
def pop_default(d: Dict[int, int], k: int) -> Dict[int, int]:
    """Keyword removal applicable to EVERY mapping (no precondition on the
    presence of ``k``): it returns a fresh mapping equal to ``d`` with ``k``
    absent, every other keyword/value preserved and none introduced, whether or
    not ``k`` was present beforehand; ``d`` is read-only. A deep model of one
    keyword-removal primitive (A-reference). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 2))
    # The real `d.pop(k, None)` is a single bounded primitive step; the
    # strictly smaller measure (1 < 2) lets the contracted caller holding
    # MustTerminate(2) invoke it without leaking its own obligation.
    Requires(MustTerminate(1))
    Ensures(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(Result()), 1 / 4))
    Ensures(Result() is not None)
    Ensures(k not in Result())
    Ensures(Forall(int, lambda j: Implies(j != k and j in d,
                                          j in Result() and Result()[j] == d[j])))
    Ensures(Forall(int, lambda j: Implies(j in Result(),
                                          j != k and j in d and Result()[j] == d[j])))
# axioms-end


# pure-start
@Pure
def TO() -> int:
    # The token for the related-target keyword (the one dropped from the
    # relation-agnostic form). A distinguished keyword-name token.
    return 0
# pure-end


def reduce_to_relation_agnostic(kwargs: Dict[int, int], is_relation: bool) -> Dict[int, int]:
    # pre-conditions-start
    # The mapping is read-only here (the result is related to it): fractional
    # permission (directive 5).
    Requires(Acc(dict_pred(kwargs), 1 / 2))
    # TERMINATION: the reduction must actually ANSWER (deliver the
    # relation-agnostic mapping to the detector) — it is a bounded, straight-
    # line computation over one mapping. Nagini is a partial-correctness
    # verifier by default, so without this obligation a non-terminating
    # implementation (e.g. bare self-recursion) satisfies every Ensures
    # vacuously; the real per-field body always returns. The measure (2)
    # strictly exceeds the primitives' (1), so the impl may call them but may
    # NOT re-invoke this routine itself without a smaller measure — the
    # postcondition cannot be discharged by echoing this routine's own
    # contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(kwargs), 1 / 4))
    Ensures(Acc(dict_pred(Result()), 1 / 4))
    Ensures(Result() is not None)
    # A relation field's resulting mapping never carries the target keyword,
    # for EVERY input mapping -- including one that did not carry it.
    Ensures(Implies(is_relation, TO() not in Result()))
    # Every other keyword the input had is carried through with its value ...
    Ensures(Forall(int, lambda j: Implies(j != TO() and j in kwargs,
                                          j in Result() and Result()[j] == kwargs[j])))
    # ... and the result introduces no keyword the input did not have.
    Ensures(Forall(int, lambda j: Implies(j in Result(),
                                          j in kwargs and Result()[j] == kwargs[j])))
    # A non-relation field's mapping is the input unchanged: even the target
    # keyword survives.
    Ensures(Implies(not is_relation,
                    Forall(int, lambda j: Implies(j in kwargs,
                                                  j in Result() and Result()[j] == kwargs[j]))))
    # post-conditions-end
    # impl-start
    if is_relation:
        return del_present(kwargs, TO())
    return kwargs
    # impl-end
