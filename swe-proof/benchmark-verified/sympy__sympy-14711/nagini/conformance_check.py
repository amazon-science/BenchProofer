#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-14711 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. There are no @Pure
module-level helpers in this bundle (the pure region is empty). The two
@ContractOnly callees are bridged to the REAL repo functions, as the contract
requires:

  * ``vector_guard``  -> ``sympy.physics.vector.vector._check_vector`` (the
    unchanged operand guard); its raise is re-signalled as the model's
    user-defined ``NotAVector``.
  * ``normalise`` (invoked via ``Vec.__init__``) -> the REAL merging
    ``Vector`` constructor run on the combined term list; the stored carrier
    is the constructor's own arg list.

ORACLE: the REAL repo function the model models per mapping.md --
``sympy.physics.vector.vector.Vector.__add__``. The gate applies the diff to
/testbed before this script runs (PYTHONPATH=/testbed); this script never
applies any diff itself.

Type bridge (mapping.md section 2): the model's ``List[int]`` of opaque
component-family tags abstracts the real ``Vector.args`` list of
(measure, frame) entries. The shadow impl only copies, appends, indexes and
hands the list to the (real) constructor -- it never inspects an element -- so
the real arg entries themselves serve as the opaque carrier elements and
list equality on them is the ToSeq equality of the model. The right operand's
two discriminators map to the runtime facts the modeled function observes:

  Operand.is_scalar_zero  <->  the operand compares equal to the scalar 0
  Operand.is_vector       <->  isinstance(operand, Vector)
  Operand.terms           <->  the operand's .args when it is a Vector

Requires filter: the precondition Implies(is_scalar_zero, not is_vector)
excludes an operand that is BOTH (the zero Vector, which compares equal to 0
and is a Vector); such operands are skipped, everything else is in-domain.

Outcome bridge: a normal return compares the result carriers (shadow terms
list vs real result .args); the shadow's NotAVector maps to the TypeError the
real guard raises.

>= 1e5 Requires-satisfying inputs: structured boundary cases (the F2P operand
shapes, every postcondition clause: scalar-zero identity, vector combine with
same-frame merge and cancellation, non-vector rejection) plus 100000 fuzz
configurations drawn from a prebuilt operand pool. Pinned fuzz seed: 147110.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + the repo under test only (random; no
hypothesis needed).
"""
import json
import random
import sys

SEED = 147110
N_FUZZ = 100_000


class NotAVector(Exception):
    """The model's reject signal (stands in for the builtin exception the
    real operand guard raises; see mapping.md section 2)."""
    pass


# --- @ContractOnly callee bridges: call the REAL repo functions ---------------

def _real_symbols():
    from sympy.physics.vector.vector import Vector, _check_vector
    return Vector, _check_vector


def normalise(terms):
    """Bridge for the `normalise` @ContractOnly callee: the REAL merging
    constructor run on the term list; the stored carrier is its arg list."""
    Vector, _ = _real_symbols()
    return list(Vector(list(terms)).args)


def vector_guard(other):
    """Bridge for the `vector_guard` @ContractOnly callee: the REAL operand
    guard. Returns the operand as a Vec carrier when it is a vector; raises
    NotAVector when the real guard rejects it."""
    _, _check_vector = _real_symbols()
    try:
        checked = _check_vector(other.payload)
    except TypeError:
        raise NotAVector()
    v = Vec.__new__(Vec)  # the guard returns the operand UNCHANGED (no re-normalise)
    v.terms = list(checked.args)
    return v


# --- model classes (carrier shells; Vec.__init__ normalises via the bridge) ---

class Vec(object):
    def __init__(self, terms):
        self.terms = normalise(terms)


class Operand(object):
    def __init__(self, is_scalar_zero, is_vector, terms, payload):
        self.is_scalar_zero = is_scalar_zero
        self.is_vector = is_vector
        self.terms = list(terms)
        # the real object this Operand abstracts (consumed only by the
        # vector_guard bridge, which hands it to the real guard)
        self.payload = payload


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def vec_add(self, other):
    if other.is_scalar_zero:
        return self
    checked = vector_guard(other)
    combined = list(self.terms)
    j = 0
    while j < len(checked.terms):
        combined.append(checked.terms[j])
        j = j + 1
    result = Vec(combined)
    return result


# --- bridge: real inputs <-> model carriers; outcome comparison ---------------

def make_operand(obj):
    """Abstract a real right-hand operand into the model's Operand. Returns
    None when the operand violates the model's precondition (an operand that
    is both the scalar zero and a vector, i.e. the zero Vector)."""
    Vector, _ = _real_symbols()
    try:
        is_scalar_zero = bool(obj == 0)
    except Exception:
        is_scalar_zero = False
    is_vector = isinstance(obj, Vector)
    if is_scalar_zero and is_vector:
        return None  # outside the modeled domain (precondition excludes it)
    terms = list(obj.args) if is_vector else []
    return Operand(is_scalar_zero, is_vector, terms, obj)


def real_outcome(self_v, obj):
    """Run the REAL modeled function and map the observable outcome:
    ('return', args-list) on a normal return, ('raise',) on the guard's
    rejection."""
    Vector, _ = _real_symbols()
    try:
        res = Vector.__add__(self_v, obj)
    except TypeError:
        return ("raise",)
    return ("return", list(res.args))


def shadow_outcome(self_v, operand):
    sv = Vec.__new__(Vec)
    sv.terms = list(self_v.args)
    try:
        res = vec_add(sv, operand)
    except NotAVector:
        return ("raise",)
    return ("return", list(res.terms))


def check_one(self_v, obj):
    """Diff shadow vs real on one (left vector, right operand) input.
    Returns an error string on disagreement, None on agreement, and the
    sentinel 'skip' for an out-of-domain operand."""
    operand = make_operand(obj)
    if operand is None:
        return "skip"
    shadow = shadow_outcome(self_v, operand)
    real = real_outcome(self_v, obj)
    agree = (shadow[0] == real[0]
             and (shadow[0] != "return" or shadow[1] == real[1]))
    if not agree:
        return ("DISAGREEMENT\n  self=%r\n  other=%r\n"
                "  operand bits (is_scalar_zero=%r, is_vector=%r, |terms|=%d)\n"
                "  shadow=%r\n  real=%r"
                % (self_v, obj, operand.is_scalar_zero, operand.is_vector,
                   len(operand.terms), shadow, real))
    return None


def main():
    from sympy import symbols, S, sqrt, Integer, Float, Rational, sympify
    from sympy.physics.vector import ReferenceFrame, Vector

    x, y, z = symbols('x y z')
    N = ReferenceFrame('N')
    A = N.orientnew('A', 'Axis', [x, N.x])
    B = N.orientnew('B', 'Axis', [y, N.y])

    zero_vec = N.x - N.x

    # left-operand pool: empty/zero vectors, single components, same-frame and
    # mixed-frame sums, numeric/symbolic/irrational coefficients
    left_pool = [
        N.x, N.y, N.z, A.x, A.y, A.z, B.x,
        zero_vec, Vector(0), Vector([]),
        x * N.x,
        x * A.x + y * A.y + z * A.z,           # the F2P left operand shape
        x ** 2 * A.x + y ** 2 * A.y + z ** 2 * A.z,
        N.x + N.y,
        2 * N.x - 3 * N.y + N.z,
        sqrt(2) * N.z,
        x * N.x + y * A.y,
        N.x + A.x + B.x,
        (x + 1) * N.x,
        Rational(1, 3) * N.y,
    ]
    # right-operand vector pool (same shapes; includes cancellation partners)
    right_vec_pool = left_pool + [
        (-x) * A.x,
        -N.x,
        (-2) * N.x + 3 * N.y - N.z,
    ]
    scalar_zeros = [0, S(0), S.Zero, Integer(0), sympify(0), 0.0, Float(0),
                    Rational(0), False]
    nonvectors = [
        1, -1, 2, 100, S(1), Integer(5), sympify(3),
        1.5, -2.0, Float(3.14), Rational(2, 7),
        x, y, x + y, x * y, x ** 2, sqrt(x),
        "vector", "", "0",
        [], [1, 2, 3], (1, 2), {}, {"a": 1}, set(),
        None, True, complex(1, 2),
    ]

    checked = 0
    skipped = 0

    def run_case(self_v, obj):
        err = check_one(self_v, obj)
        if err == "skip":
            return "skip"
        if err:
            print(err)
            return "fail"
        return "ok"

    # --- boundary cases: every clause, on every left-pool shape --------------
    boundary_ops = (scalar_zeros + nonvectors + right_vec_pool
                    + [zero_vec, Vector(0)])  # zero Vectors -> domain skip
    for self_v in left_pool:
        for obj in boundary_ops:
            r = run_case(self_v, obj)
            if r == "fail":
                return 1
            if r == "skip":
                skipped += 1
            else:
                checked += 1
    n_boundary = checked

    # --- fuzz: pinned seed ----------------------------------------------------
    rng = random.Random(SEED)
    coeffs = [x, y, z, S(1), S(2), S(-1), sqrt(2), x ** 2, x + y,
              Rational(1, 2)]
    frames = [N, A, B]
    basis = {N: [N.x, N.y, N.z], A: [A.x, A.y, A.z], B: [B.x, B.y, B.z]}

    def rand_vec():
        v = zero_vec
        for _ in range(rng.randint(0, 4)):
            fr = rng.choice(frames)
            v = v + rng.choice(coeffs) * rng.choice(basis[fr])
        return v

    # small extension of the operand pools so fuzz sees fresh shapes too
    fuzz_left = list(left_pool) + [rand_vec() for _ in range(30)]
    fuzz_right_vec = list(right_vec_pool) + [rand_vec() for _ in range(30)]

    while checked < n_boundary + N_FUZZ:
        self_v = rng.choice(fuzz_left)
        kind = rng.random()
        if kind < 0.20:
            obj = rng.choice(scalar_zeros)
        elif kind < 0.60:
            obj = rng.choice(nonvectors)
        elif kind < 0.62:
            obj = rng.choice([zero_vec, Vector(0), Vector([])])
        else:
            obj = rng.choice(fuzz_right_vec)
        r = run_case(self_v, obj)
        if r == "fail":
            return 1
        if r == "skip":
            skipped += 1
        else:
            checked += 1

    print("G-CONF OK: shadow impl == real vector-add operator on %d "
          "Requires-satisfying inputs (%d boundary + %d fuzz, seed %d; "
          "%d out-of-domain operands skipped)."
          % (checked, n_boundary, checked - n_boundary, SEED, skipped))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "skipped_out_of_domain": skipped,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees call the real repo "
                                "functions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
