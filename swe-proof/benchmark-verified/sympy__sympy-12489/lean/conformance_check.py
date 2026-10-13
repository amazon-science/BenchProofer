#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of `implementation_mul` against
the REAL post-patch `Permutation.__mul__`.

Runs INSIDE the instance image WITH THE GOLD PATCH APPLIED (PYTHONPATH=/testbed).

The arrangement object is modeled `Arr { arr : List Int, fam : Nat }` where `arr`
is the array form and `fam` is the runtime class/family (base = 0, a derived
subclass = 1; see mapping.md). The Lean impl's observable is the pair
`(result.fam, result.arr)`:

  * result.arr = composeArr self.arr other.arr   -- A-reference: left as the REAL
        repo product's array form (exactly what post-patch `_af_new(perm)` binds)
  * result.fam = self.fam                          -- R: the family of the LEFT
        operand (the class-threading fix)

We compare that shadow against the REAL post-patch `__mul__` outcome
`(family_of(type(a*b)), (a*b).array_form)` over boundary cases + >=1e5 fuzzed
random permutations, with operand classes drawn from {base, subclass} so the
discriminating clause (type of the product) is hit hard. exit 0 iff zero
disagreements. stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 12489
N_RANDOM = 120_000  # >= 1e5


def _classes():
    from sympy.combinatorics.permutations import Permutation

    class CustomPermutation(Permutation):
        # A minimal faithful subclass (mirrors the F2P test's subclass intent):
        # adds nothing to construction, so any class difference in the product is
        # attributable purely to the object-creation machinery under test.
        def __eq__(self, other):
            if isinstance(other, Permutation):
                return self._hashable_content() == other._hashable_content()
            return super(CustomPermutation, self).__eq__(other)

        def __hash__(self):
            return super(CustomPermutation, self).__hash__()

    # family tags: base class -> 0, the derived subclass -> 1
    return Permutation, CustomPermutation


def family_of(cls, base, sub):
    if cls is base:
        return 0
    if cls is sub:
        return 1
    return -1  # unexpected third class -> forced disagreement


def real_outcome(make_a, make_b, base, sub):
    """REAL post-patch leg: build the two operands, multiply, observe
    (family_of(type(product)), product.array_form)."""
    a = make_a()
    b = make_b()
    prod = a * b
    return (family_of(type(prod), base, sub), list(prod.array_form))


def shadow_outcome(fam_a, arr_a, fam_b, arr_b, base, sub):
    """R/I shadow of implementation_mul.

    family: R leg -> family of the LEFT operand (fam_a).
    array : A-reference -> the REAL repo product's array form. We realize it by
            building the operands with the SAME classes/arrays and reading
            (a*b).array_form: this is the genuine post-patch `_af_new(perm)`
            payload, which the patch leaves unchanged. The shadow asserts only
            that this array is paired with the LEFT family (fam_a)."""
    cls_a = base if fam_a == 0 else sub
    cls_b = base if fam_b == 0 else sub
    a = cls_a(list(arr_a))
    b = cls_b(list(arr_b))
    prod_arr = list((a * b).array_form)
    return (fam_a, prod_arr)


def rand_perm(rng, n):
    p = list(range(n))
    rng.shuffle(p)
    return p


def main() -> int:
    base, sub = _classes()
    rng = random.Random(SEED)

    # (fam_a, arr_a, fam_b, arr_b)
    cases = [
        (1, [1, 2, 3, 0], 0, [1, 2, 3, 0]),   # subclass * base  -> product subclass
        (0, [1, 2, 3, 0], 1, [1, 2, 3, 0]),   # base * subclass  -> product base
        (0, [], 0, []),
        (1, [0], 1, [0]),
        (0, [2, 1, 0], 1, [1, 0, 2]),
        (1, [1, 0, 2], 0, [1, 0]),            # mismatched sizes
        (0, [1, 0], 1, [2, 1, 0, 3]),
        (1, [0, 1, 2, 3, 4], 0, []),          # empty right operand
    ]
    for _ in range(N_RANDOM):
        na = rng.randint(0, 8)
        nb = rng.randint(0, 8)
        fa = rng.randint(0, 1)
        fb = rng.randint(0, 1)
        cases.append((fa, rand_perm(rng, na), fb, rand_perm(rng, nb)))

    disagreements = 0
    checked = 0
    examples = []
    for fa, arr_a, fb, arr_b in cases:
        cls_a = base if fa == 0 else sub
        cls_b = base if fb == 0 else sub
        try:
            got = real_outcome(lambda: cls_a(list(arr_a)),
                               lambda: cls_b(list(arr_b)), base, sub)
        except Exception as e:
            got = ("error", type(e).__name__)
        try:
            exp = shadow_outcome(fa, arr_a, fb, arr_b, base, sub)
        except Exception as e:
            exp = ("error", type(e).__name__)
        checked += 1
        if got != exp:
            disagreements += 1
            if len(examples) < 5:
                examples.append((fa, arr_a, fb, arr_b, got, exp))

    for fa, arr_a, fb, arr_b, got, exp in examples:
        print(f"MISMATCH a=(fam{fa},{arr_a}) b=(fam{fb},{arr_b}) "
              f"real={got} shadow={exp}")

    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements, "
              f"seed={SEED})")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
