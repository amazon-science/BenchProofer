"""Twin-artifact model for django__django-13786.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model-creation step and a subsequent model-options step on the same
  model are collapsed into a single model-creation step, the options carried by
  the collapsed step must be EXACTLY the options the model would have after the
  options step is applied to the freshly-created model -- not merely the union
  of the two option mappings.

  The options step distinguishes two kinds of option name:

    * a MANAGED option name (one of the established family of metadata options
      the options step is allowed to set, compare, and clear); and
    * any OTHER option name (a setting outside that family).

  Applying the options step yields, for each option name k:

    (1) if k is provided by the options step, the value the options step gives
        it (the options step's value wins over the creation step's value);
    (2) else if k is a MANAGED option name, k is ABSENT from the result -- a
        managed option the creation step had but the options step does not
        provide is cleared, because the options step's mapping is the complete
        intended set of managed options;
    (3) else (k is an OTHER option name not provided by the options step), k
        keeps the creation step's value if the creation step had it, and is
        absent otherwise.

  The result carries no option name that neither the creation step nor the
  options step mentions. Clause (2) is the behaviour that matters: a managed
  option present on the creation step but omitted by the options step must NOT
  survive into the collapsed creation step.

Modelling choices (Nagini fragment):
  * An option mapping is a ``Dict[int, int]`` from an option-name token to an
    option-value token; only membership and per-name value are observed, so
    integer-keyed identity is the faithful carrier (mapping.md §2).
  * The managed-option family is the deep, definite predicate ``is_managed_
    option`` over a finite family of representative option-name tokens
    (mapping.md §2), not an opaque oracle. ``key_managed_a`` / ``key_managed_b``
    are managed names; ``key_other`` is a name outside the managed family.
    Behaviours (1)/(3) and the no-foreign-name closure are quantified over
    EVERY option name; behaviour (2) is stated per member of the (finite)
    managed family, which covers every managed name.
  * The two unchanged language primitives the step composes -- the mapping
    merge ``{**a, **b}`` and the removal of one name ``d.pop(k, None)`` /
    ``{kk: vv for kk, vv in d.items() if kk != k}`` -- are the axiomatised
    callees ``merge_options`` / ``without_key`` (A-consumed), validated against
    real Python out-of-band (axiom_check.py, G-AX). The NEW logic -- deciding
    which managed names to clear -- is spelled out deeply in the impl region.

Both input mappings are read-only here (the step allocates a fresh result and
never writes either input), so each is held at HALF permission (Required AND
Ensured); the axiomatised callees take only QUARTER permission so quantified
facts about the inputs are preserved across the calls. No string indexing is
used (Nagini bans it). Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@ContractOnly
def merge_options(a: Dict[int, int], b: Dict[int, int]) -> Dict[int, int]:
    """Standard mapping merge ``{**a, **b}`` (an unchanged language primitive
    the step composes): a FRESH mapping holding every name of ``a`` and ``b``;
    ``b``'s value wins where both carry a name, otherwise ``a``'s value. The
    result is a new object, so neither input is mutated (both read-only).
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(a), 1 / 4))
    Requires(Acc(dict_pred(b), 1 / 4))
    Requires(MustTerminate(2))
    Ensures(Acc(dict_pred(a), 1 / 4))
    Ensures(Acc(dict_pred(b), 1 / 4))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # b's value wins where b carries the name ...
    Ensures(Forall(int, lambda k: Implies(k in b, k in Result() and Result()[k] == b[k])))
    # ... a's value carries elsewhere ...
    Ensures(Forall(int, lambda k: Implies(k in a and k not in b,
                                          k in Result() and Result()[k] == a[k])))
    # ... and the result holds no name outside a's and b's names.
    Ensures(Forall(int, lambda k: Implies(k in Result(), k in a or k in b)))


@ContractOnly
def without_key(d: Dict[int, int], k: int) -> Dict[int, int]:
    """Standard removal of one name ``{kk: vv for kk, vv in d.items() if kk != k}``
    / ``d.pop(k, None)`` returning the residue (an unchanged language primitive):
    a FRESH mapping equal to ``d`` with the single name ``k`` removed. ``d`` is
    read-only (the result is a new object). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 4))
    Requires(MustTerminate(6))
    Ensures(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # the removed name is gone ...
    Ensures(k not in Result())
    # ... every other name of d is carried through with its value ...
    Ensures(Forall(int, lambda j: Implies(j != k and j in d,
                                          j in Result() and Result()[j] == d[j])))
    # ... and the result introduces no name d did not have.
    Ensures(Forall(int, lambda j: Implies(j in Result(),
                                          j != k and j in d and Result()[j] == d[j])))
# axioms-end


# pure-start
@Pure
def key_managed_a() -> int:
    # A representative MANAGED option name (one the options step may set/clear).
    return 0


@Pure
def key_managed_b() -> int:
    # A second, distinct representative MANAGED option name.
    return 1


@Pure
def key_other() -> int:
    # A representative option name OUTSIDE the managed family (the options step
    # neither compares nor clears it).
    return 2


@Pure
def is_managed_option(k: int) -> bool:
    """The definite membership test for the managed-option family: exactly the
    representative managed names. A managed name omitted by the options step is
    the one that must be cleared from the collapsed result."""
    return k == key_managed_a() or k == key_managed_b()
# pure-end


def reduced_create_options(self_options: Dict[int, int],
                           operation_options: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both inputs are read-only here: HALF permission, never written. (Held
    # read-only so the operation cannot satisfy its postcondition by overwriting
    # an input; the result is a fresh mapping.)
    Requires(Acc(dict_pred(self_options), 1 / 2))
    Requires(Acc(dict_pred(operation_options), 1 / 2))
    # Carrier integrity: an option-name token is a genuine int. (bool is a
    # subtype of int in Python; a bool key would be a distinct mapping key that
    # still compares int-equal to a name token, i.e. an object outside the
    # option-name carrier. Both inputs carry name tokens only.)
    Requires(Forall(int, lambda k: Implies(k in self_options,
                                           not isinstance(k, bool))))
    Requires(Forall(int, lambda k: Implies(k in operation_options,
                                           not isinstance(k, bool))))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned untouched at the same half permission.
    Ensures(Acc(dict_pred(self_options), 1 / 2))
    Ensures(Acc(dict_pred(operation_options), 1 / 2))
    # A fresh, full-permission result mapping.
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The clauses below cover EVERY option name k (the managed family is
    # finite -- exactly the is_managed_option members -- so its clause is
    # stated pointwise per member; the others quantify over all names).
    # Together they pin Result() as a total function of the two inputs: for
    # each k exactly one clause's antecedent applies, so no behaviourally-
    # distinct implementation can satisfy them.
    # (1) EVERY name provided by the options step -> the options step's value
    #     wins over the creation step's value.
    Ensures(Forall(int, lambda k: Implies(k in operation_options,
                                          k in Result()
                                          and Result()[k] == operation_options[k])))
    # (2) EVERY MANAGED name NOT provided by the options step -> cleared, even
    #     if the creation step carried it. The managed family is exactly
    #     {key_managed_a, key_managed_b} (= is_managed_option), so these two
    #     clauses cover every managed name.
    Ensures(Implies(key_managed_a() not in operation_options,
                    key_managed_a() not in Result()))
    Ensures(Implies(key_managed_b() not in operation_options,
                    key_managed_b() not in Result()))
    # (3) EVERY OTHER (non-managed) name not provided by the options step but on
    #     the creation step -> the creation step's value is kept.
    Ensures(Forall(int, lambda k: Implies(not is_managed_option(k)
                                          and k not in operation_options
                                          and k in self_options,
                                          k in Result()
                                          and Result()[k] == self_options[k])))
    # No foreign name: the result mentions nothing neither step does (with (3),
    # this also gives: a name on neither step, or a non-managed name omitted by
    # the options step and absent from the creation step, is absent).
    Ensures(Forall(int, lambda k: Implies(k in Result(),
                                          k in self_options or k in operation_options)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the collapsed step's options are merely the union of
    # the two option mappings, with no step clearing managed names the options
    # step does not provide. A managed name the creation step carried therefore
    # survives even when the options step omits it -- violating clause (2).
    options = merge_options(self_options, operation_options)
    return options
    # impl-end
