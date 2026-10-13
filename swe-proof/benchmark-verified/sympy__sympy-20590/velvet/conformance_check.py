#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20590 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* runtime, via the mapping.md bijection
              (a type's resolution order ↔ `List Bool` of closed-layout flags; a
              type declaring a closed slot set ↔ flag `true`). The shadow
              assembles the value type's flag chain and evaluates the model's
              `instanceAdmitsNamespace` / `bindUndeclared`.
  * ORACLE  — the behaviour `patch.diff` produces: with the shared printing
              contributor declaring an empty closed slot set, the value type's
              instances must carry no open namespace and must refuse binding an
              undeclared attribute name. We reproduce this with the real
              interpreter object model by building class chains with the
              matching slot layout and observing `hasattr(inst, '__dict__')` and
              the binding outcome.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container; stdlib only. The fuzz seed is pinned for a deterministic
verdict.
"""
import random
import sys

SEED = 20590
N_FUZZ = 4000


# --- the R/I shadow: Solution.lean allClosedLayout/instanceAdmitsNamespace ----
# transliterated to Python (the impl region's chain assembly + decision).
def shadow_all_closed_layout(chain):
    # front-recursive conjunction allClosedLayout
    for flag in chain:
        if not flag:
            return False
    return True


def shadow_instance_admits_namespace(chain):
    return not shadow_all_closed_layout(chain)


def shadow_bind_refused(chain):
    # bindUndeclared returns error (refused) iff allClosedLayout chain
    return shadow_all_closed_layout(chain)


# --- the oracle: the real interpreter object model on the matching layout -----
def build_leaf(chain):
    """Build a linear type chain whose non-root classes carry the given closed-
    layout flags (leaf-first, matching the model's chain head = most-derived).
    flag True -> the class declares a closed (empty) slot set; flag False -> it
    omits the slot declaration. Returns the leaf class to instantiate."""
    cls = object
    for flag in reversed(chain):
        ns = {'__slots__': ()} if flag else {}
        cls = type('C', (cls,), ns)
    return cls


def oracle_instance_admits_namespace(chain):
    return hasattr(build_leaf(chain)(), '__dict__')


def oracle_bind_refused(chain):
    inst = build_leaf(chain)()
    try:
        inst.some_undeclared_name = 1
    except AttributeError:
        return True
    return False


def chains(n, rng):
    # boundary: the gold value-type shape [True, True, True] and the prepatch
    # shape [True, True, False], plus small layouts.
    yield []
    yield [True]
    yield [False]
    yield [True, True]
    yield [True, False]
    yield [False, True]
    yield [True, True, True]
    yield [True, True, False]
    for _ in range(n):
        k = rng.randint(0, 6)
        yield [rng.random() < 0.5 for _ in range(k)]


def main():
    rng = random.Random(SEED)
    checked = 0
    disagreements = 0
    for chain in chains(N_FUZZ, rng):
        s_ns = shadow_instance_admits_namespace(chain)
        o_ns = oracle_instance_admits_namespace(chain)
        s_rf = shadow_bind_refused(chain)
        o_rf = oracle_bind_refused(chain)
        if s_ns != o_ns or s_rf != o_rf:
            disagreements += 1
            if disagreements <= 5:
                print("DISAGREE chain=%r shadow(ns=%r,refused=%r) "
                      "oracle(ns=%r,refused=%r)" % (chain, s_ns, s_rf, o_ns, o_rf),
                      file=sys.stderr)
        checked += 1

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements" % (disagreements, checked))
        return 1
    print("G-CONF OK: R/I shadow of the chain/namespace/binding model agrees "
          "with the real interpreter on %d chains (seed=%d), 0 disagreements."
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
