#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20438 (nagini).

SHADOW: the impl regions of model.py's `product_subset_of_finite`,
`finite_sets_equal` and `simplify_equality_route`, copied VERBATIM below with
the contract calls (Requires/Ensures/Invariant/Assert) stripped.  The @Pure
helpers `all_in`, `ARITH_PATH` and `collection_outcome` copy over as plain
functions (a minimal `PSeq`/`ToSeq` tuple shim realizes the sequence type the
fold recurses on).  The single @ContractOnly callee `member` calls the REAL
repo membership test through the handle registry (see the bridge below) — the
axiom claims only determinism + totality, and the real callee supplies the
actual membership fact, exactly as in the verified model.

ORACLE: the REAL patched repo decisions the model models per mapping.md —
  (1) `ProductSet.is_subset(FiniteSet)` (the containment decision),
  (2) `Eq(A, B).simplify()` on two concrete collections (the set-equality
      decision: a definite truth value),
  (3) `Eq(A, B).simplify()` routing: for collection (non-Expr) operands the
      result is the definite collection-equality value and the call must not
      raise; for arithmetic (Expr) operands the arithmetic path is taken and
      its value is opaque to the routing model.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2): a collection is registered under an
integer id (`SETS`), and each concrete element (a number or a tuple drawn
from a Cartesian product's enumeration) is interned to an integer handle
(`ELEMS`).  `member(setid, el)` is then the real membership test
`SETS[setid].contains(ELEMS[el])`, required to be a definite truth value on
this concrete domain (a non-definite answer is reported as a disagreement —
it would fall outside the modeled domain).  The model's `List[int]` of
element handles is the ordered enumeration `list(product_set)` /
`list(finite_set)`.  `both_arith` is `isinstance(lhs, Expr) and
isinstance(rhs, Expr)`.  Outcome tokens: 0 = arithmetic path, 1/2 = the
collection-equality truth value (true/false).

Input domain: exactly the model's Requires — any lists of interned element
handles with valid collection ids; realized as concrete finite sets of small
numbers, Cartesian products of 1..3 such factors, and their tuple universes
(subsets, supersets with alien elements, wrong-arity aliens, scalar/tuple
mixes, empty sets).  All membership facts are decidable on this domain.

>= 1e5 Requires-satisfying inputs: boundary cases (incl. the F2P witnesses)
+ fuzz.  Pinned fuzz seed: 204380.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib + the repo under test only.
"""
import json
import random
import sys
from typing import List

SEED = 204380
N_SUBSET = 55_000
N_EQUAL = 25_000
N_ROUTE_COLLECTION = 15_000
N_ROUTE_ARITH = 5_000


# --- bridge registries: collection ids and element handles --------------------

SETS = []    # setid -> real sympy set object
ELEMS = []   # handle -> real concrete element (number or tuple)
_HIDX = {}   # element -> handle (interning)

_S = None    # sympy singleton registry, bound in main()


class BridgeError(Exception):
    """A membership fact came back non-definite on the concrete domain."""


def reset_bridge():
    del SETS[:]
    del ELEMS[:]
    _HIDX.clear()


def reg_set(s) -> int:
    SETS.append(s)
    return len(SETS) - 1


def handle(e) -> int:
    h = _HIDX.get(e)
    if h is None:
        ELEMS.append(e)
        h = len(ELEMS) - 1
        _HIDX[e] = h
    return h


def handles(elems) -> List[int]:
    return [handle(e) for e in elems]


# --- @ContractOnly callee: the REAL repo membership test ----------------------

def member(setid: int, el: int) -> bool:
    """The membership oracle, realized by the real repo callee through the
    registries.  Must be a definite truth value on this concrete domain."""
    c = SETS[setid].contains(ELEMS[el])
    if c is _S.true:
        return True
    if c is _S.false:
        return False
    raise BridgeError("membership not definite: %r in %r -> %r"
                      % (ELEMS[el], SETS[setid], c))


# --- shim for the sequence type the pure fold recurses on ---------------------

class PSeq(tuple):
    def drop(self, n):
        return PSeq(tuple.__getitem__(self, slice(n, None)))


def ToSeq(lst):
    return PSeq(lst)


# --- @Pure helpers from model.py, contracts stripped --------------------------

def all_in(s, setid: int) -> bool:
    """Whether every enumerated element handle in `s` belongs to the collection
    `setid`.  Front-recursive so a single unfold is available per loop step:
    empty enumerates to True; otherwise the head must be a member AND the tail
    must all be members."""
    if len(s) == 0:
        return True
    return member(setid, s[0]) and all_in(s.drop(1), setid)


def ARITH_PATH() -> int:
    """Outcome token meaning the arithmetic-reduction path was taken (the
    unchanged behaviour for two arithmetic operands -- its result is opaque to
    this routing model)."""
    return 0


def collection_outcome(equal: bool) -> int:
    """Outcome token of the collection-equality decision: a definite truth value
    (distinct from the arithmetic-path token).  `equal` is the collection
    equality of behaviour (2)."""
    return 1 if equal else 2


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def product_subset_of_finite(elems: List[int], finite_id: int) -> bool:
    res = True
    i = len(elems)
    while i > 0:
        e = elems[i - 1]
        res = member(finite_id, e) and res
        i = i - 1
    return res


def finite_sets_equal(elems_a: List[int], id_a: int,
                      elems_b: List[int], id_b: int) -> bool:
    a_sub_b = product_subset_of_finite(elems_a, id_b)
    b_sub_a = product_subset_of_finite(elems_b, id_a)
    return a_sub_b and b_sub_a


def simplify_equality_route(both_arith: bool,
                            elems_a: List[int], id_a: int,
                            elems_b: List[int], id_b: int) -> int:
    if both_arith:
        # Both operands arithmetic: take the unchanged arithmetic-reduction path.
        return ARITH_PATH()
    # At least one operand is a collection: do NOT attempt the arithmetic
    # reduction (which has no defined result for a collection operand); defer to
    # the collection-equality decision of behaviour (2).
    equal = finite_sets_equal(elems_a, id_a, elems_b, id_b)
    return collection_outcome(equal)


# --- differential drivers ------------------------------------------------------

def check_subset(sy, prod, finite):
    """Containment decision: shadow vs the real `prod.is_subset(finite)`."""
    reset_bridge()
    elems = list(prod)
    try:
        shadow = product_subset_of_finite(handles(elems), reg_set(finite))
    except BridgeError as exc:
        return ("DISAGREEMENT (bridge: %s)\n  input: prod=%r finite=%r"
                % (exc, prod, finite))
    real = prod.is_subset(finite)
    if real is not True and real is not False:
        return ("DISAGREEMENT (oracle not definite)\n  input: prod=%r finite=%r"
                "\n  shadow=%r\n  real=%r" % (prod, finite, shadow, real))
    if shadow != real:
        return ("DISAGREEMENT (subset)\n  input: prod=%r finite=%r"
                "\n  shadow=%r\n  real=%r" % (prod, finite, shadow, real))
    return None


def check_equal(sy, A, B):
    """Equality decision: shadow vs the real `Eq(A, B).simplify()` value."""
    reset_bridge()
    try:
        shadow = finite_sets_equal(handles(list(A)), reg_set(A),
                                   handles(list(B)), reg_set(B))
    except BridgeError as exc:
        return ("DISAGREEMENT (bridge: %s)\n  input: A=%r B=%r" % (exc, A, B))
    try:
        real = sy.Eq(A, B).simplify()
    except Exception as exc:
        return ("DISAGREEMENT (oracle raised)\n  input: A=%r B=%r"
                "\n  shadow=%r\n  real raised %s: %s"
                % (A, B, shadow, type(exc).__name__, exc))
    if real is not sy.S.true and real is not sy.S.false:
        return ("DISAGREEMENT (oracle not definite)\n  input: A=%r B=%r"
                "\n  shadow=%r\n  real=%r" % (A, B, shadow, real))
    if shadow != (real is sy.S.true):
        return ("DISAGREEMENT (equality)\n  input: A=%r B=%r"
                "\n  shadow=%r\n  real=%r" % (A, B, shadow, real))
    return None


def check_route(sy, Expr, A, B):
    """Routing decision: shadow outcome token vs the real routed result.
    For collection operands the real result must be the definite
    collection-equality value (token 1/2, never the arithmetic token); for
    arithmetic operands the arithmetic path is taken (token 0, value opaque).
    In both cases the real call must not raise."""
    both_arith = isinstance(A, Expr) and isinstance(B, Expr)
    reset_bridge()
    if both_arith:
        shadow = simplify_equality_route(True, [], reg_set(A), [], reg_set(B))
    else:
        try:
            shadow = simplify_equality_route(False,
                                             handles(list(A)), reg_set(A),
                                             handles(list(B)), reg_set(B))
        except BridgeError as exc:
            return ("DISAGREEMENT (bridge: %s)\n  input: A=%r B=%r"
                    % (exc, A, B))
    try:
        real = sy.Eq(A, B).simplify()
    except Exception as exc:
        return ("DISAGREEMENT (oracle raised on routing)\n  input: A=%r B=%r "
                "both_arith=%r\n  shadow token=%r\n  real raised %s: %s"
                % (A, B, both_arith, shadow, type(exc).__name__, exc))
    if both_arith:
        if shadow != ARITH_PATH():
            return ("DISAGREEMENT (routing: arithmetic operands must take the "
                    "arithmetic path)\n  input: A=%r B=%r\n  shadow token=%r"
                    % (A, B, shadow))
        return None
    # collection case: the real result is the definite equality value
    if real is sy.S.true:
        real_token = 1
    elif real is sy.S.false:
        real_token = 2
    else:
        return ("DISAGREEMENT (routing: collection result not definite)"
                "\n  input: A=%r B=%r\n  shadow token=%r\n  real=%r"
                % (A, B, shadow, real))
    if shadow == ARITH_PATH() or shadow != real_token:
        return ("DISAGREEMENT (routing)\n  input: A=%r B=%r"
                "\n  shadow token=%r\n  real token=%r (real=%r)"
                % (A, B, shadow, real_token, real))
    return None


# --- input generation -----------------------------------------------------------

POOL = [-2, -1, 0, 1, 2, 3, 4]


def rand_finite(sy, rng, lo=0, hi=4):
    n = rng.randint(lo, hi)
    return sy.FiniteSet(*rng.sample(POOL, n)) if n else sy.FiniteSet()


def rand_product(sy, rng, max_factors=3):
    k = rng.randint(1, max_factors)
    factors = [sy.FiniteSet(*rng.sample(POOL, rng.randint(1, 3)))
               for _ in range(k)]
    return sy.ProductSet(*factors), k


def rand_target(sy, rng, prod, k):
    """A finite target built from the product's tuple universe, possibly
    perturbed with removals and alien elements so both answers occur."""
    universe = list(prod)
    m = rng.randint(0, len(universe))
    chosen = rng.sample(universe, m)
    r = rng.random()
    if r < 0.25:
        chosen.append(tuple([sy.Integer(9)] * k) if k > 1 else sy.Integer(9))
    elif r < 0.35:
        chosen.append(tuple([sy.Integer(9)] * (k + 1)))  # wrong arity
    elif r < 0.45 and k > 1:
        chosen.append(sy.Integer(7))                      # scalar in tuple set
    if k == 1:
        # elements of a 1-factor product enumerate as 1-tuples; sometimes give
        # a bare-scalar target instead (membership is then definitely false)
        if rng.random() < 0.2:
            chosen = [t[0] if isinstance(t, tuple) else t for t in chosen]
    return sy.FiniteSet(*chosen) if chosen else sy.FiniteSet()


def boundary_subsets(sy):
    a = sy.FiniteSet(1, 2)
    b = sy.ProductSet(a, a)
    c = sy.FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
    d = sy.FiniteSet(1)
    p1 = sy.ProductSet(sy.FiniteSet(1, 2))
    p3 = sy.ProductSet(sy.FiniteSet(0, 1), sy.FiniteSet(0, 1),
                       sy.FiniteSet(0, 1))
    return [
        (b, c),                                        # full universe: subset
        (b, d),                                        # scalar target: not
        (b, sy.FiniteSet((1, 1), (2, 2))),             # partial universe
        (b, sy.FiniteSet(*(list(c) + [(9, 9)]))),      # superset with alien
        (b, sy.FiniteSet()),                           # empty target
        (sy.EmptySet, c),                              # empty product side
        (p1, sy.FiniteSet((1,), (2,))),                # 1-factor, tuple target
        (p1, sy.FiniteSet(1, 2)),                      # 1-factor, scalar target
        (p3, sy.FiniteSet(*list(p3))),                 # 3-factor universe
        (p3, sy.FiniteSet(*list(p3)[:-1])),            # 3-factor minus one
    ]


def boundary_equalities(sy):
    a = sy.FiniteSet(1, 2)
    b = sy.ProductSet(a, a)
    c = sy.FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
    return [
        (c, b), (b, c),                                # tuple set vs product
        (a, c),                                        # scalar set vs tuple set
        (a, a),                                        # identical
        (sy.FiniteSet(), sy.FiniteSet()),              # both empty
        (sy.FiniteSet(), sy.FiniteSet(1)),             # empty vs nonempty
        (b, sy.ProductSet(sy.FiniteSet(2, 1), sy.FiniteSet(2, 1))),
        (b, sy.ProductSet(sy.FiniteSet(1, 2), sy.FiniteSet(3))),
        (sy.FiniteSet(*(list(c) + [(9, 9)])), b),      # alien breaks equality
        (sy.FiniteSet((1, 1), 3), b),                  # scalar/tuple mix
    ]


def main():
    import sympy as sy
    from sympy.core.expr import Expr
    global _S
    _S = sy.S

    rng = random.Random(SEED)
    checked = 0
    counts = {"subset": 0, "equal": 0, "route_collection": 0,
              "route_arith": 0, "boundary": 0}

    def run(err):
        if err:
            print(err)
            sys.exit(1)

    # boundary cases (incl. the F2P witness shapes)
    for prod, fin in boundary_subsets(sy):
        run(check_subset(sy, prod, fin))
        checked += 1
        counts["boundary"] += 1
    for A, B in boundary_equalities(sy):
        run(check_equal(sy, A, B))
        run(check_route(sy, Expr, A, B))
        checked += 2
        counts["boundary"] += 2
    for A, B in [(sy.Integer(1), sy.Integer(1)),
                 (sy.Integer(1), sy.Integer(2)),
                 (sy.Rational(1, 2), sy.Rational(1, 2)),
                 (sy.Integer(0), sy.Rational(-3, 7))]:
        run(check_route(sy, Expr, A, B))
        checked += 1
        counts["boundary"] += 1

    # fuzz: containment decisions
    for _ in range(N_SUBSET):
        prod, k = rand_product(sy, rng)
        fin = rand_target(sy, rng, prod, k)
        run(check_subset(sy, prod, fin))
        checked += 1
        counts["subset"] += 1

    # fuzz: equality decisions (scalar sets, tuple sets vs products,
    # product vs product)
    def rand_eq_pair():
        r = rng.random()
        if r < 0.5:
            A = rand_finite(sy, rng)
            B = A if rng.random() < 0.3 else rand_finite(sy, rng)
            return A, B
        if r < 0.8:
            prod, k = rand_product(sy, rng, max_factors=2)
            fin = rand_target(sy, rng, prod, k)
            return (fin, prod) if rng.random() < 0.5 else (prod, fin)
        p1, _ = rand_product(sy, rng, max_factors=2)
        p2, _ = rand_product(sy, rng, max_factors=2)
        return p1, (p1 if rng.random() < 0.3 else p2)

    for _ in range(N_EQUAL):
        A, B = rand_eq_pair()
        run(check_equal(sy, A, B))
        checked += 1
        counts["equal"] += 1

    # fuzz: routing — collection operands (must reach the definite
    # collection-equality value, never the arithmetic token, never raise)
    for _ in range(N_ROUTE_COLLECTION):
        A, B = rand_eq_pair()
        run(check_route(sy, Expr, A, B))
        checked += 1
        counts["route_collection"] += 1

    # fuzz: routing — arithmetic operands (arithmetic token, value opaque)
    for _ in range(N_ROUTE_ARITH):
        A = sy.Rational(rng.randint(-9, 9), rng.randint(1, 9))
        B = sy.Rational(rng.randint(-9, 9), rng.randint(1, 9)) \
            if rng.random() < 0.5 else sy.Integer(rng.randint(-9, 9))
        run(check_route(sy, Expr, A, B))
        checked += 1
        counts["route_arith"] += 1

    print("G-CONF OK: shadow impl == real containment/equality/routing "
          "decisions on %d inputs (%d boundary + %d subset + %d equality + "
          "%d collection-routing + %d arithmetic-routing fuzz, seed %d)."
          % (checked, counts["boundary"], counts["subset"], counts["equal"],
             counts["route_collection"], counts["route_arith"], SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions; "
                                "member bridges to the real repo callee)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
