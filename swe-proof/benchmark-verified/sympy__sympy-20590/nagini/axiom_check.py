#!/usr/bin/env python3
"""G-AX check for sympy__sympy-20590 (A-reference validation).

The bundle has NO consumed @ContractOnly axiom. Its single A-reference is the
deep model of the CPython object-model rule that `model.py` spells out:

    instance_admits_namespace(chain) == not all_closed_layout(chain)

where `chain` is the sequence of closed-layout flags for the classes in an
instance's MRO (root `object` excluded), and a flag is True iff that class
declares `__slots__`. The two observable consequences the model pins:

    instance_admits_namespace(chain) == hasattr(instance, '__dict__')
    (not instance_admits_namespace(chain)) ==> setting an undeclared attribute
                                                raises AttributeError

This script validates that modelled rule == the REAL interpreter, by building
class hierarchies with every combination of slotted / un-slotted layers
(boundary + fuzz), instantiating, and comparing the interpreter's observed
behaviour to the model's prediction. stdlib-only; exit 0 iff sound.

This is the construction-time mirror of what G-AX runs in-container.
"""
import random
import sys


# ---- the modelled rule, transcribed from model.py (the deep model) ----------

def all_closed_layout(chain):
    """True iff every flag is True (front-recursive conjunction in model.py)."""
    for flag in chain:
        if not flag:
            return False
    return True


def model_instance_admits_namespace(chain):
    return not all_closed_layout(chain)


# ---- the real interpreter: build a class chain from a flag list -------------

def build_class_chain(chain):
    """Build a linear inheritance chain whose non-object classes have the given
    fixed-layout flags. Flag True -> the class declares `__slots__ = ()`;
    False -> the class omits `__slots__` (so it contributes a `__dict__`).
    `chain[0]` is the most-derived (leaf) class; the leaf is the one we
    instantiate. Returns the leaf class."""
    # Build from base to leaf. `chain` is leaf-first (matching model's chain,
    # whose head is the most-derived class), so reverse to base-first.
    cls = object
    for flag in reversed(chain):
        if flag:
            ns = {'__slots__': ()}
        else:
            ns = {}
        cls = type('C', (cls,), ns)
    return cls


def real_instance_admits_namespace(chain):
    """Observe whether a real instance carries a `__dict__`."""
    leaf = build_class_chain(chain)
    inst = leaf()
    return hasattr(inst, '__dict__')


def real_undeclared_assignment_raises(chain):
    """Observe whether binding an undeclared attribute raises AttributeError."""
    leaf = build_class_chain(chain)
    inst = leaf()
    try:
        inst.some_undeclared_name = 1
    except AttributeError:
        return True
    return False


# ---- the comparison ----------------------------------------------------------

def check_chain(chain):
    predicted_dict = model_instance_admits_namespace(chain)
    observed_dict = real_instance_admits_namespace(chain)
    assert predicted_dict == observed_dict, (
        "namespace mismatch on chain %r: model=%r interpreter=%r"
        % (chain, predicted_dict, observed_dict))

    # When the model predicts NO namespace, undeclared assignment must raise;
    # when it predicts a namespace, undeclared assignment must succeed.
    observed_raises = real_undeclared_assignment_raises(chain)
    assert observed_raises == (not predicted_dict), (
        "assignment-raise mismatch on chain %r: model_no_namespace=%r "
        "interpreter_raises=%r" % (chain, not predicted_dict, observed_raises))


def main():
    checked = 0

    # Boundary cases.
    boundary = [
        [],                 # empty chain (only object): all_fixed -> no dict
        [True],             # one slotted layer
        [False],            # one un-slotted layer -> dict
        [True, True],       # the patched Basic+trait shape, both slotted
        [True, False],      # leaf slotted, base un-slotted (the BUG shape:
                            #   Basic slotted, Printable un-slotted) -> dict
        [False, True],      # leaf un-slotted, base slotted -> dict
        [True, True, True], # the gold Basic chain (Basic, abstract base, trait)
        [True, True, False],# the prepatch Basic chain (trait un-slotted) -> dict
    ]
    for chain in boundary:
        check_chain(chain)
        checked += 1

    # Fuzz: random multi-layer chains.
    rng = random.Random(20590)
    for _ in range(4000):
        n = rng.randint(0, 6)
        chain = [rng.random() < 0.5 for _ in range(n)]
        check_chain(chain)
        checked += 1

    print("G-AX OK: modelled __slots__/__dict__ rule matches the interpreter "
          "on %d chains (boundary + fuzz)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
