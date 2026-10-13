#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-14711.

Executes the REAL repo callees that the `vec_add` model depends on
(`sympy/physics/vector/vector.py`) on inputs satisfying each axiom's domain
(boundary cases plus randomized fuzz) and asserts every observation matches the
axiom as encoded in model.py.

Two kind-A checks:

  (A-consumed) `vector_guard` axiom models the unchanged guard `_check_vector`:
        * a Vector operand  -> returned UNCHANGED (is-identity), `is_vector`;
        * a non-Vector operand -> raises (TypeError, modeled as NotAVector). In
          particular the scalar zero `0`/`S(0)` is NOT a Vector and MUST raise --
          exactly why the pre-patch `__add__` failed on `A.x + 0`.

  (A-reference) `normal_form` / `normalise` axioms model the unchanged merging
        constructor `Vector.__init__`, which `__add__` calls on
        `self.args + other.args`. The constructor frame-merges (sums same-frame
        terms, drops cancelling frames), so it is NOT verbatim concatenation. The
        model encodes two faithful properties of this constructor:
          (i)  it never invents a component, i.e.
                   len(Vector(a.args + b.args).args) <= len(a.args) + len(b.args)
               (the never-grows length bound), AND
          (ii) it is a DETERMINISTIC FUNCTION of the whole argument list: equal
               argument lists yield equal `.args` (so the normal form of BOTH
               operands' components together -- the post `normal_form(self ++
               other)` -- is well defined and is NOT the normal form of `self`
               alone unless `other` contributes nothing). `model.py` encodes (ii)
               as `normal_form` being a `@Pure` function; we validate it here by
               running the real constructor on equal vs. unequal argument lists.
        We assert (i) for every constructed sum (including the merge cases that
        the F2P test exercises), AND we falsify the naive "length is preserved"
        over-claim by exhibiting a same-frame merge that strictly shrinks --
        proving the `<=` bound is genuinely the faithful one, not a vacuous one.
        We assert (ii) by checking the constructor returns equal `.args` on the
        same argument list and, on the F2P merge, returns a DIFFERENT `.args`
        from the normal form of `self` alone (so the pinned post genuinely
        distinguishes "combined both operands" from "dropped the other operand").

Imports only `sympy` (the repo under test); the same module path the gold patch
edits. Exit 0 iff every obligation holds.
"""
import random
import sys


def _check_vector_obs(other):
    """Run the real callee; return ('return', obj) or ('raise', exc_type)."""
    from sympy.physics.vector.vector import _check_vector
    try:
        out = _check_vector(other)
        return ("return", out)
    except TypeError:
        return ("raise", TypeError)


def check_vector_returns_identity(vec):
    """vector_guard Ensures: a Vector operand is returned UNCHANGED (identity)."""
    kind, payload = _check_vector_obs(vec)
    assert kind == "return", (
        "vector_guard unsound: _check_vector raised on a genuine Vector %r"
        % (vec,))
    assert payload is vec, (
        "vector_guard unsound: _check_vector did not return the operand "
        "unchanged for %r (got %r)" % (vec, payload))


def check_nonvector_raises(obj):
    """vector_guard Exsures: a non-Vector operand raises (TypeError->NotAVector)."""
    kind, payload = _check_vector_obs(obj)
    assert kind == "raise", (
        "vector_guard unsound: _check_vector did NOT raise on the non-Vector "
        "%r (returned %r); the axiom's not-a-vector Exsures is over-claimed"
        % (obj, payload))


def check_normalise_never_grows(a, b):
    """normalise Ensures: the merging constructor `Vector(a.args + b.args)`
    never invents a component, so its arg list is no longer than the
    concatenation `a.args + b.args`. We invoke the REAL constructor via the same
    expression `__add__` uses (`Vector(self.args + other.args)`)."""
    from sympy.physics.vector import Vector
    result = Vector(a.args + b.args)
    assert len(result.args) <= len(a.args) + len(b.args), (
        "normalise unsound: Vector(a.args + b.args) GREW the component list "
        "(%d > %d + %d) for a=%r, b=%r -- the `len(result) <= len(input)` "
        "contract is over-claimed" % (len(result.args), len(a.args),
                                      len(b.args), a, b))


def check_normal_form_deterministic(a, b):
    """normal_form Ensures (determinism): the constructor is a function of the
    whole argument list, so building `Vector` from the SAME concatenated arg
    list twice yields the SAME `.args` (this is the `@Pure normal_form`
    property the post `normal_form(self ++ other)` leans on)."""
    from sympy.physics.vector import Vector
    arglist = a.args + b.args
    r1 = Vector(list(arglist))
    r2 = Vector(list(arglist))
    assert r1.args == r2.args, (
        "normal_form unsound: Vector(arglist) is NOT a deterministic function "
        "of its argument list -- got %r vs %r for arglist=%r"
        % (r1.args, r2.args, arglist))


def check_combined_distinguishes_other(a, b):
    """The pinned post `normal_form(self ++ other)` genuinely COMBINES the
    other operand: the constructor's result on `self.args + other.args` differs
    from its result on `self.args` alone whenever the other operand contributes
    a non-cancelling component. We assert the constructor distinguishes them on
    the F2P merge -- which is exactly why `return self` (the dropped-other
    attack) cannot satisfy the post."""
    from sympy.physics.vector import Vector
    combined = Vector(a.args + b.args)
    self_only = Vector(list(a.args))
    return combined.args != self_only.args


def main():
    from sympy import symbols, S, sqrt, Integer, Float, sympify
    from sympy.physics.vector import ReferenceFrame, Vector

    x, y, z = symbols('x y z')
    N = ReferenceFrame('N')
    A = N.orientnew('A', 'Axis', [x, N.x])

    # ===================================================================== #
    # (A-consumed) vector_guard == _check_vector                            #
    # ===================================================================== #
    # --- genuine Vectors: must be returned unchanged ----------------------
    vectors = [
        N.x, N.y, N.z,
        A.x, A.y, A.z,
        x * N.x,
        x * N.x + y * N.y + z * N.z,
        0 * N.x,                 # a Vector that happens to be the zero vector
        N.x - N.x,               # the zero vector via subtraction
        Vector(0),               # the explicit zero Vector
        Vector([]),              # empty-arg Vector
        sqrt(2) * N.z,
        (x ** 2) * N.x + (y ** 2) * N.y,
    ]
    for v in vectors:
        assert isinstance(v, Vector), "test setup: %r is not a Vector" % (v,)
        check_vector_returns_identity(v)

    # --- the scalar zero is NOT a Vector and MUST raise -------------------
    scalar_zeros = [0, S(0), S.Zero, Integer(0), sympify(0), 0.0, Float(0)]
    for zero in scalar_zeros:
        assert not isinstance(zero, Vector), (
            "test setup: %r unexpectedly a Vector" % (zero,))
        check_nonvector_raises(zero)

    # --- other non-Vector objects: boundary cases -------------------------
    nonvectors = [
        1, -1, 2, 100, S(1), Integer(5), sympify(3),
        1.5, -2.0, Float(3.14),
        x, y, x + y, x * y, x ** 2, sqrt(x),
        "vector", "", "0",
        [], [1, 2, 3], (1, 2), {}, {"a": 1}, set(),
        None, True, False,
        complex(1, 2),
    ]
    for obj in nonvectors:
        if isinstance(obj, Vector):
            continue
        check_nonvector_raises(obj)

    # --- randomized fuzz over non-Vector objects --------------------------
    rng = random.Random(14711)
    syms = [x, y, z]
    for _ in range(2000):
        choice = rng.randint(0, 6)
        if choice == 0:
            obj = rng.randint(-1000, 1000)
        elif choice == 1:
            obj = rng.uniform(-1000.0, 1000.0)
        elif choice == 2:
            obj = S(rng.randint(-1000, 1000))
        elif choice == 3:
            obj = rng.choice(syms) ** rng.randint(0, 5)
        elif choice == 4:
            obj = rng.choice(syms) * rng.randint(-10, 10)
        elif choice == 5:
            obj = [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]
        else:
            obj = "".join(rng.choice("abc0&<> ") for _ in range(rng.randint(0, 6)))
        if isinstance(obj, Vector):
            continue
        check_nonvector_raises(obj)

    # ===================================================================== #
    # (A-reference) normalise == Vector.__init__ (the merging constructor)  #
    # ===================================================================== #
    # Faithfulness: `len(Vector(a.args + b.args).args) <= len(a)+len(b)` on a
    # spread of operand pairs, including the same-frame merge and cancellation
    # cases the F2P test_Vector exercises.
    zero = N.x - N.x
    base_pairs = [
        # the exact F2P additions (both operands entirely in frame A -> merge)
        (x * A.x + y * A.y + z * A.z, x ** 2 * A.x + y ** 2 * A.y + z ** 2 * A.z),
        (A.x, 0 * A.x),                      # A.x + 0-vector
        (x * A.x, x ** 2 * A.x),             # same-frame, same-basis -> merge
        (x * A.x, (-x) * A.x),               # cancellation -> length 0
        (N.x, A.y),                          # distinct frames -> no merge
        (N.x + N.y, A.z),                    # one merged operand + distinct frame
        (zero, zero),                        # zero + zero
        (N.x, N.x),                          # N.x + N.x -> merge
        (x * N.x + y * N.y, x * N.x),        # partial same-frame overlap
        (sqrt(2) * N.z, N.z),                # irrational coeff merge
    ]
    n_merge_witnessed = 0
    n_distinguished = 0
    for a, b in base_pairs:
        assert isinstance(a, Vector) and isinstance(b, Vector)
        check_normalise_never_grows(a, b)
        check_normal_form_deterministic(a, b)
        # count cases where the constructor STRICTLY shrinks (a real merge/cancel)
        result = Vector(a.args + b.args)
        if len(result.args) < len(a.args) + len(b.args):
            n_merge_witnessed += 1
        # count cases where normal_form(self ++ other) differs from
        # normal_form(self) alone -- the property that makes "return self" wrong
        if check_combined_distinguishes_other(a, b):
            n_distinguished += 1

    # Tightness: the naive "length is preserved" over-claim must be FALSE.
    # x*A.x + y*A.y is two same-frame terms that the constructor folds into one.
    merged = Vector((x * A.x).args + (y * A.y).args)
    assert len(merged.args) < len((x * A.x).args) + len((y * A.y).args), (
        "test setup: expected a same-frame merge to strictly shrink the arg "
        "list (got %d args)" % (len(merged.args),))
    assert n_merge_witnessed >= 3, (
        "test setup: expected several strict merges/cancellations among the "
        "operand pairs (saw %d); the `<=` bound would be vacuously an `==`"
        % (n_merge_witnessed,))

    # Distinguisher: the pinned post `normal_form(self ++ other)` must genuinely
    # combine `other` -- i.e. the constructor's result on `self.args + other.args`
    # must DIFFER from its result on `self.args` alone for the F2P merge. This is
    # exactly the property that makes the `return self` / `Vec(self.terms)` /
    # `Vec([])` attacks (which drop `other`) FAIL clause (2). The F2P additions
    # `v1 = x*A.x + y*A.y + z*A.z`, `v2 = x**2*A.x + …`: `v1 + v2` differs from
    # `v1` alone, observable as `dot(v3, A.x) == x**2 + x` (not `== x`).
    v1 = x * A.x + y * A.y + z * A.z
    v2 = x ** 2 * A.x + y ** 2 * A.y + z ** 2 * A.z
    combined_args = Vector(v1.args + v2.args).args
    self_only_args = Vector(list(v1.args)).args
    assert combined_args != self_only_args, (
        "normal_form unsound: the constructor did NOT distinguish `v1 + v2` from "
        "`v1` alone -- the pinned post `normal_form(self ++ other)` would admit a "
        "`return self` impl (got combined=%r, self-only=%r)"
        % (combined_args, self_only_args))
    assert n_distinguished >= 3, (
        "test setup: expected several operand pairs where normal_form(self ++ "
        "other) differs from normal_form(self) alone (saw %d); otherwise the "
        "content-bearing post would not exclude the dropped-other attacks"
        % (n_distinguished,))

    # randomized fuzz: build random same-/mixed-frame vectors and check the
    # never-grows bound on their constructor-merged sum.
    frames = [N, A]
    basis = {N: [N.x, N.y, N.z], A: [A.x, A.y, A.z]}
    coeffs = [x, y, z, S(1), S(2), S(-1), sqrt(2), x ** 2]
    rng2 = random.Random(20180512)
    for _ in range(500):
        def rand_vec():
            v = zero
            for _ in range(rng2.randint(0, 4)):
                fr = rng2.choice(frames)
                v = v + rng2.choice(coeffs) * rng2.choice(basis[fr])
            return v
        a, b = rand_vec(), rand_vec()
        check_normalise_never_grows(a, b)
        check_normal_form_deterministic(a, b)

    print("G-AX OK: vector_guard (== _check_vector) sound on %d Vector inputs "
          "(identity), %d scalar-zero inputs (raise), %d boundary non-Vectors "
          "+ 2000 fuzz (raise); normal_form/normalise (== Vector.__init__) "
          "never-grows bound holds on %d boundary pairs (>=%d strict merges) + "
          "500 fuzz, the length-preservation over-claim is falsified by a "
          "same-frame merge, the constructor is a deterministic function of its "
          "argument list, and normal_form(self ++ other) differs from "
          "normal_form(self) alone on >=%d pairs (incl. the F2P merge) -- so the "
          "content-bearing post excludes the dropped-other attacks."
          % (len(vectors), len(scalar_zeros), len(nonvectors),
             len(base_pairs), n_merge_witnessed, n_distinguished))
    return 0


if __name__ == "__main__":
    sys.exit(main())
