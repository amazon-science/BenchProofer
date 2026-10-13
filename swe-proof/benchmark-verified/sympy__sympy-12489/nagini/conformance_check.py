#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12489 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Requires/Ensures removed from ``Arrangement.__init__``; the
``make`` / ``combine`` impl regions contain no contract lines). There are no
@Pure helpers, no @ContractOnly callees, and no PSeq usage in this bundle;
the carriers are a plain int (``kind``) and a plain ``List[int]``
(``array``), so no shim is needed.

ORACLE: the REAL patched repo functions the model models per mapping.md —
``Permutation._af_new`` (the internal builder, model ``make``) and
``Permutation.__mul__`` (the binary combination, model ``combine``). The
gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable. This script does NOT
apply any patch itself.

Type bridge (mapping.md "Type abstraction"):
  * the runtime class of a constructed value <-> ``kind: int``: the base
    family ``Permutation`` <-> 0, each derived family (a genuine subclass)
    <-> a fixed distinct nonzero kind (here 1 and 2);
  * ``_array_form`` (list of points) <-> ``array: List[int]``, compared with
    ``==`` on lists (the real accessor returns a copy, so identity is
    bridged to content equality);
  * ``make``'s ``kind`` parameter <-> the family the real builder is reached
    through (the class ``_af_new`` is invoked on);
  * ``combine``'s ``product`` parameter <-> the combined numeric content of
    the two operands' array forms. That content computation is UNCHANGED
    machinery abstracted into the carrier (mapping.md section 2), so the
    bridge recomputes it here: the shorter operand acts as the identity on
    the excess points, and the combined array applies the left operand's
    array first, then the right's. The shadow's content claim
    (result array == product) is then checked against the real result's
    array form — a wrong bridge direction would show up as a disagreement.

Input domain (the model's Requires are permission-only; the bridge domain is
the real routines' intended domain): finished permutation arrays of points
0..n-1, over the base family and two derived families. Boundary: exhaustive
arrays of sizes 0..5 for the builder and exhaustive equal-size pairs of
sizes 1..4 for the combination, over every family (pairing). Fuzz: random
arrays up to size 12 (builder) and random, possibly UNEQUAL-size pairs up
to size 10 (combination), over random families.

>= 1e5 Requires-satisfying inputs: 462 + 5553 boundary + 2 x 50000 fuzz
= 106015. Pinned fuzz seed: 12489.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import itertools
import random
import sys

SEED = 12489
N_FUZZ = 50_000


# --- the impl region of model.py, verbatim (contracts stripped) --------------

class Arrangement:
    def __init__(self, kind, array):
        self.kind = kind
        self.array = array


def make(kind, array):
    result = Arrangement(kind, array)
    return result


def combine(self, other, product):
    result = make(self.kind, product)
    return result


# --- oracle setup: the real patched repo classes ------------------------------

from sympy.combinatorics.permutations import Permutation  # noqa: E402


class DerivedA(Permutation):
    """A genuine derived family (model kind 1). No construction routine is
    overridden, so the result class observed below is decided purely by the
    real builder / combination under test."""


class DerivedB(Permutation):
    """A second derived family (model kind 2), exercising 'any other int is
    a distinct derived family'."""


FAMILIES = ((Permutation, 0), (DerivedA, 1), (DerivedB, 2))
CLASS_OF_KIND = {kind: cls for cls, kind in FAMILIES}
KIND_OF_CLASS = {cls: kind for cls, kind in FAMILIES}


def combined_content(a, b):
    """The unchanged numeric content carried by the ``product`` parameter
    (mapping.md section 2): apply the left array first, then the right; the
    shorter operand is the identity on the excess points."""
    a = list(a)
    b = list(b)
    b.extend(range(len(b), len(a)))
    return [b[i] for i in a] + b[len(a):]


def real_make(kind, array):
    """Run the REAL internal builder through the family ``kind`` maps to and
    observe (family identifier of the result, its array content)."""
    built = CLASS_OF_KIND[kind]._af_new(list(array))
    return KIND_OF_CLASS.get(type(built)), list(built.array_form)


def real_combine(self_kind, self_array, other_kind, other_array):
    """Run the REAL binary combination on operands of the two families and
    observe (family identifier of the result, its array content)."""
    left = CLASS_OF_KIND[self_kind]._af_new(list(self_array))
    right = CLASS_OF_KIND[other_kind]._af_new(list(other_array))
    result = left * right
    return KIND_OF_CLASS.get(type(result)), list(result.array_form)


# --- differential checks ------------------------------------------------------

def check_make(kind, array):
    out = make(kind, list(array))
    shadow = (out.kind, list(out.array))
    real = real_make(kind, array)
    if shadow != real:
        return ("DISAGREEMENT (make)\n  kind=%r array=%r\n  shadow=%r\n  real=%r"
                % (kind, array, shadow, real))
    return None


def check_combine(self_kind, self_array, other_kind, other_array):
    product = combined_content(self_array, other_array)
    self_sh = Arrangement(self_kind, list(self_array))
    other_sh = Arrangement(other_kind, list(other_array))
    out = combine(self_sh, other_sh, product)
    shadow = (out.kind, list(out.array))
    real = real_combine(self_kind, self_array, other_kind, other_array)
    if shadow != real:
        return ("DISAGREEMENT (combine)\n"
                "  self=(kind=%r, array=%r) other=(kind=%r, array=%r) product=%r\n"
                "  shadow=%r\n  real=%r"
                % (self_kind, self_array, other_kind, other_array, product,
                   shadow, real))
    return None


def perms_of_size(n):
    return [list(p) for p in itertools.permutations(range(n))]


def main():
    checked = 0

    # --- boundary: builder, exhaustive sizes 0..5 x every family -----------
    for n in range(0, 6):
        for perm in perms_of_size(n):
            for _, kind in FAMILIES:
                err = check_make(kind, perm)
                if err:
                    print(err)
                    return 1
                checked += 1

    # --- boundary: combination, exhaustive equal-size pairs sizes 1..4 x
    # every family pairing --------------------------------------------------
    for n in range(1, 5):
        ps = perms_of_size(n)
        for a in ps:
            for b in ps:
                for _, ka in FAMILIES:
                    for _, kb in FAMILIES:
                        err = check_combine(ka, a, kb, b)
                        if err:
                            print(err)
                            return 1
                        checked += 1

    # --- fuzz: builder ------------------------------------------------------
    rng = random.Random(SEED)
    kinds = [kind for _, kind in FAMILIES]
    for _ in range(N_FUZZ):
        n = rng.randint(0, 12)
        a = list(range(n))
        rng.shuffle(a)
        err = check_make(rng.choice(kinds), a)
        if err:
            print(err)
            return 1
        checked += 1

    # --- fuzz: combination (possibly unequal sizes) -------------------------
    for _ in range(N_FUZZ):
        n = rng.randint(0, 10)
        m = rng.randint(0, 10)
        a = list(range(n))
        rng.shuffle(a)
        b = list(range(m))
        rng.shuffle(b)
        err = check_combine(rng.choice(kinds), a, rng.choice(kinds), b)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real builder/combination on %d inputs "
          "(seed %d)." % (checked, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
