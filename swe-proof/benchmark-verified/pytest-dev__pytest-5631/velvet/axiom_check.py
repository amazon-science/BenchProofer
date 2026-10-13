#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5631.

This bundle has **no axioms and no A-reference deep models** (see refinement.md
§C, mapping.md §3): the modeled function `countSentinelArgs` calls no unchanged
external operation whose contract is assumed. It is a self-contained scan —
attribute-name truthiness, object-identity comparison against two module-level
sentinels, and a length count — all modeled concretely (R/I only).

There is therefore nothing for G-AX to validate. The differential fidelity of
the deep model against the real callee path is covered entirely by G-CONF
(`conformance_check.py`), which diffs the identity-count shadow against the
patched real `num_mock_patch_args`, including array-like (`__eq__`-raises) values.

We additionally assert the one structural premise the modeling rests on — that
object IDENTITY (`is`) is total and never invokes `__eq__`, even for a value
whose equality raises — so a regression in that assumption would surface here.

Exit 0 (sound / nothing to check). stdlib only.
"""
import sys


class ArrayLike:
    """A value whose __eq__ raises in a truth context (numpy-array-like)."""

    def __eq__(self, other):
        raise ValueError("ambiguous truth value")

    __hash__ = None


def main():
    a = ArrayLike()
    b = ArrayLike()
    sentinel = object()

    # Identity comparisons must be total: they never invoke __eq__, so they
    # never raise — this is the property the fix relies on and the model
    # encodes as the total `valueId == marker` test.
    assert (a is a) is True
    assert (a is b) is False
    assert (a is sentinel) is False
    assert any(a is s for s in [sentinel, object()]) is False

    # Sanity: equality on this value DOES raise (so the prepatch path that uses
    # equality membership is genuinely the buggy one).
    raised = False
    try:
        bool(a == sentinel)
    except ValueError:
        raised = True
    assert raised, "ArrayLike.__eq__ should raise — modeling premise broken"

    print("G-AX OK: no axioms / no A-reference deep models for this bundle "
          "(fully R/I; identity-is-total premise holds). Fidelity covered by "
          "G-CONF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
