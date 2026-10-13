#!/usr/bin/env python3
"""G-AX check for sympy__sympy-20590 (A-reference validation).

The bundle has NO consumed axiom. Its single A-reference is the deep model of
the host runtime's object-model rule that Solution.lean spells out:

    instanceAdmitsNamespace(chain) == not allClosedLayout(chain)

where `chain` is the sequence of closed-layout flags for the contributing types
in an instance's resolution order (the universal root excluded), and a flag is
True iff that type declares a closed (fixed) instance slot layout. The two
observable consequences the model pins:

    instanceAdmitsNamespace(chain) == hasattr(instance, '__dict__')
    (not instanceAdmitsNamespace(chain)) ==> binding an undeclared attribute
                                             name raises AttributeError
    bindUndeclared(chain) refuses (error) iff allClosedLayout(chain)

This script validates that modelled rule == the REAL interpreter, by building
type chains with every combination of closed-layout / open-layout layers
(boundary + fuzz), instantiating, and comparing the interpreter's observed
behaviour to the model's prediction. stdlib-only; exit 0 iff sound.

This is the construction-time mirror of what G-AX runs in-container.
"""
import random
import sys


# ---- the modelled rule, transcribed from Solution.lean (the deep model) -----

def all_closed_layout(chain):
    """True iff every flag is True (the front-recursive conjunction
    allClosedLayout in Solution.lean)."""
    for flag in chain:
        if not flag:
            return False
    return True


def model_instance_admits_namespace(chain):
    """instanceAdmitsNamespace = not allClosedLayout."""
    return not all_closed_layout(chain)


def model_bind_refused(chain):
    """bindUndeclared refuses (error) iff allClosedLayout(chain)."""
    return all_closed_layout(chain)


# ---- the real interpreter: build a type chain from a flag list --------------

def build_leaf(chain):
    """Build a linear inheritance chain whose non-root classes carry the given
    closed-layout flags. Flag True -> the class declares a closed (empty) slot
    set (`__slots__ = ()`); False -> the class omits the slot declaration (so it
    contributes an open per-instance namespace). `chain[0]` is leaf-first
    (matching the model's chain head = most-derived); reverse to build base
    first. Returns the leaf class to instantiate."""
    cls = object
    for flag in reversed(chain):
        ns = {'__slots__': ()} if flag else {}
        cls = type('C', (cls,), ns)
    return cls


def real_instance_admits_namespace(chain):
    return hasattr(build_leaf(chain)(), '__dict__')


def real_undeclared_binding_refused(chain):
    inst = build_leaf(chain)()
    try:
        inst.some_undeclared_name = 1
    except AttributeError:
        return True
    return False


# ---- the comparison ----------------------------------------------------------

def check_chain(chain):
    pred_ns = model_instance_admits_namespace(chain)
    obs_ns = real_instance_admits_namespace(chain)
    assert pred_ns == obs_ns, (
        "namespace mismatch on chain %r: model=%r interpreter=%r"
        % (chain, pred_ns, obs_ns))

    pred_refused = model_bind_refused(chain)
    obs_refused = real_undeclared_binding_refused(chain)
    assert pred_refused == obs_refused, (
        "binding-refusal mismatch on chain %r: model=%r interpreter=%r"
        % (chain, pred_refused, obs_refused))
    # consistency of the two observables: refused iff no namespace.
    assert obs_refused == (not obs_ns), (
        "interpreter self-inconsistency on chain %r" % (chain,))


def main():
    checked = 0
    boundary = [
        [],                  # only the root: closed -> no namespace
        [True],              # one closed layer
        [False],             # one open layer -> namespace
        [True, True],        # both closed
        [True, False],       # leaf closed, base open -> namespace (the bug shape)
        [False, True],       # leaf open, base closed -> namespace
        [True, True, True],  # the gold value-type chain shape
        [True, True, False], # the prepatch chain shape -> namespace
    ]
    for chain in boundary:
        check_chain(chain)
        checked += 1

    rng = random.Random(20590)
    for _ in range(4000):
        n = rng.randint(0, 6)
        chain = [rng.random() < 0.5 for _ in range(n)]
        check_chain(chain)
        checked += 1

    print("G-AX OK: modelled closed-layout/open-namespace rule matches the "
          "interpreter on %d chains (boundary + fuzz)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
