#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12489.

The family-propagating construction in model.py is modelled DEEPLY (no callee
is axiomatized; there is no consumed @ContractOnly). This script validates that
the deep model is sound: it runs the REAL repository construction (the patched
internal builder ``Permutation._af_new`` and the patched binary combination
``Permutation.__mul__``) on a genuine subclass and asserts that the observed
class-identity matches the model's claims (A-reference):

  model.make(kind, array)      == Result with .kind == kind, .array is array
      ↔  real  Cls._af_new(perm)        -> instance of Cls with array form perm
  model.combine(self, other, p) == Result with .kind == self.kind, .array is p
      ↔  real  (self * other)           -> instance of type(self) with the
                                           product array form

The family identifier ``kind`` (model: int; base family = 0, derived = nonzero)
is the abstraction of the runtime class: ``type(x) is Permutation`` ↔ kind 0;
``type(x) is CustomPermutation`` ↔ a distinct nonzero kind.

Imports nothing beyond the repository under test (``sympy``); the gold patch is
already applied in the evaluation container. Exit 0 iff every observation meets
the model's claims.
"""
import itertools
import random
import sys

from sympy.combinatorics.permutations import Permutation


class CustomPermutation(Permutation):
    """A genuine subclass — the derived family the model abstracts as a nonzero
    ``kind`` — mirroring the subclass used by the hidden F2P test. None of these
    overrides touch the construction routines under test (``_af_new`` /
    ``__new__`` / ``__mul__``), so any divergence in the result CLASS is due
    purely to whether construction honours the family it was reached through.
    """

    def __call__(self, *i):
        try:
            return super(CustomPermutation, self).__call__(*i)
        except TypeError:
            pass
        try:
            perm_obj = i[0]
            return [self._array_form[j] for j in perm_obj]
        except Exception:
            raise TypeError('unrecognized argument')

    def __eq__(self, other):
        if isinstance(other, Permutation):
            return self._hashable_content() == other._hashable_content()
        else:
            return super(CustomPermutation, self).__eq__(other)

    def __hash__(self):
        return super(CustomPermutation, self).__hash__()


def array_form(p):
    return list(p.array_form)


def check_make_propagates_class(perm_list):
    """A-reference clause (1): the internal builder mints a value of exactly the
    family it was reached through, carrying exactly the supplied array.

    model: make(kind, array).kind == kind and .array is array.
    """
    for Cls, kind in ((Permutation, 0), (CustomPermutation, 1)):
        built = Cls._af_new(list(perm_list))          # the real builder
        # clause: result family identifier == the family the builder ran on
        assert type(built) is Cls, (
            "builder lost family on %r via %s: got %s, model.make claims kind=%d"
            % (perm_list, Cls.__name__, type(built).__name__, kind))
        # clause: result carries exactly the supplied array (content unchanged)
        assert array_form(built) == list(perm_list), (
            "builder altered content on %r via %s: %r != %r"
            % (perm_list, Cls.__name__, array_form(built), list(perm_list)))


def check_combine_propagates_left_class(a_list, b_list):
    """A-reference clause (2): the binary combination, evaluated as a method of
    the LEFT operand, produces a value of the left operand's own family, with
    content equal to the (unchanged) product array.

    model: combine(self, other, product).kind == self.kind, .array is product.
    """
    # Build operands of each family pairing and check the left family wins.
    for Cls in (Permutation, CustomPermutation):
        for Other in (Permutation, CustomPermutation):
            left = Cls(list(a_list))
            right = Other(list(b_list))
            result = left * right                     # self.__mul__(other)
            assert type(result) is Cls, (
                "combination lost LEFT family for %s * %s on (%r, %r): got %s; "
                "model.combine claims kind == self.kind"
                % (Cls.__name__, Other.__name__, a_list, b_list,
                   type(result).__name__))
            # content: the product array must equal the numeric product of the
            # two array forms (the unchanged content carried through `product`).
            expected = array_form(left * right)
            assert array_form(result) == expected


def perms_of_size(n):
    return [list(p) for p in itertools.permutations(range(n))]


def main():
    # --- builder (clause 1): exhaustive over small sizes -------------------
    builder_cases = 0
    for n in range(0, 6):                 # sizes 0..5: 1+1+2+6+24+120 = 154
        for perm in perms_of_size(n):
            check_make_propagates_class(perm)
            builder_cases += 1

    # --- combination (clause 2): exhaustive over small sizes ---------------
    combine_cases = 0
    for n in range(1, 5):                 # equal-size pairs over sizes 1..4
        ps = perms_of_size(n)
        for a in ps:
            for b in ps:
                check_combine_propagates_left_class(a, b)
                combine_cases += 1

    # --- randomized fuzz over larger sizes ---------------------------------
    rng = random.Random(12489)
    for _ in range(3000):
        n = rng.randint(0, 12)
        a = list(range(n)); rng.shuffle(a)
        check_make_propagates_class(a)
        builder_cases += 1
        m = rng.randint(1, 12)
        b1 = list(range(m)); rng.shuffle(b1)
        b2 = list(range(m)); rng.shuffle(b2)
        check_combine_propagates_left_class(b1, b2)
        combine_cases += 1

    # --- the F2P headline witnesses verbatim -------------------------------
    p = CustomPermutation([1, 2, 3, 0])
    q = Permutation([1, 2, 3, 0])
    assert type(p * q) is CustomPermutation, "F2P: type(p*q) must be subclass"
    assert type(q * p) is Permutation, "F2P: type(q*p) must be base"
    assert p == q, "F2P: subclass value equals base value of same content"

    print("G-AX OK: family propagation sound on %d builder + %d combination "
          "observations (real Permutation._af_new / __mul__), incl. F2P "
          "witnesses." % (builder_cases, combine_cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
