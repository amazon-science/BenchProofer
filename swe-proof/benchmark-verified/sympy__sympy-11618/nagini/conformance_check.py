#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-11618 (nagini).

Refutes (never proves) the refinement leg: does the MODEL in model.py agree with
the REAL gold-patched repository function it claims to model?

SHADOW
  The `# impl-start` / `# impl-end` region of model.py, copied VERBATIM below
  with only the contract calls deleted (`Requires`, `Ensures`, `Invariant`,
  `Assert`, and the `# invariants-start/-end` markers). The `@Pure` helpers the
  region depends on — `coord`, `term`, `psum` — are copied the same way, minus
  their contracts. `lemma_psum_unfold` is NOT copied: its body is `return True`
  and it is referenced only from a stripped `Assert`, so it carries no
  computation. Nothing is renamed, reordered, or "simplified": the accumulation
  loop is kept exactly as written even though the returned value flows through
  `psum` (see LOOP below).

  Nagini carriers: `PSeq[int]` is realized by the immutable-tuple shim below
  (`len` / `[]` / `==`, the operations this impl region uses) and `ToSeq(list)`
  materializes one — same shape as the other nagini bundles in this corpus.

  `root` is `@Pure @ContractOnly`: it has no body to copy. Per mapping.md §3.2
  it axiomatizes the REAL, unchanged `sympy.sqrt`
  (`sympy.functions.elementary.miscellaneous.sqrt`, imported
  `sympy/geometry/point.py:18`, called at `:269`), so the shim below CALLS that
  real function. The axiom is therefore exercised, not assumed, and the shadow
  returns the same kind of exact sympy value the repo function returns — the
  comparison is on the full distance, not on a squared surrogate.

ORACLE
  The REAL patched repo function, CALLED (not transliterated):
  `sympy.geometry.point.Point.distance(self, p)` —
  `sympy/geometry/point.py:237` at base_commit 360290c4c40 (body line 269, the
  site of the gold hunk); mapping.md §1. Neither `Point2D` nor `Point3D`
  overrides `distance` (verified in-container: `'distance' in Point2D.__dict__`
  is False), so this single function is the whole oracle. The gate applies
  patch.diff and sets PYTHONPATH=/testbed, so the import resolves the patched
  in-tree sympy; the script additionally asserts the loaded source contains the
  gold hunk's `type(p) is not type(self)` guard and hard-errors otherwise, so a
  patch-apply failure can never be mistaken for agreement.

TYPE BRIDGE (mapping.md §2, inverted)
  Model side: two `List[int]` coordinate vectors `u`, `v` (carried into the spec
  as `PSeq[int]` via `ToSeq`). Repo side: `self.args` / `p.args`, tuples of
  sympy coordinate expressions. Inversion is `Point(coords)` — the constructor
  sympifies each int to an `Integer` and dispatches on length (len 2 -> Point2D,
  len 3 -> Point3D, anything else -> the generic n-D `Point`), so `len(u)`
  determines both `len(self.args)` and the concrete class. Integer coordinates
  keep every comparison exact (mapping.md §2 R0: the patch changes only WHICH
  squared differences enter the sum, never the arithmetic of one summand).

INPUT DOMAIN — the model's `Requires` is only `Acc(list_pred(u|v), 1/2)`, i.e.
any two int lists, and the domain is infinite, so this runs boundary cases plus
seeded fuzz. The Requires-satisfying domain splits into two regimes, and the
check covers BOTH rather than generating inside one of them:

  (1) MODELED DOMAIN — `len(u) == len(v)` or the two concrete classes differ.
      This is where refinement.md §C claims the model equals the gold. Here the
      script diffs shadow vs the real called function directly, >= 1e5 inputs.

  (2) SCOPE BOUNDARY — same concrete class, different length (reachable only
      for the generic `Point`: lengths 0, 1, 4, 5, ...). refinement.md §C states
      the model is deliberately STRONGER than the gold here, because the gold
      leaves such pairs on its original truncating `zip` path. The script does
      not skip this region: it pins the real behaviour POSITIVELY, asserting
      real == sqrt(psum(u, v, MIN(len u, len v))) (the truncating path) for every
      such pair, and asserting that the documented divergence really does occur
      on the negative-control pair from G-AX. A green run therefore reports a
      checked boundary, not an unexamined one — and if sympy ever padded there,
      or padded differently, these assertions fail loudly.

  So the two regimes together exhaust the Requires domain; no input class is
  quietly avoided. The branch structure of the impl is exercised inside (1):
  `len(v) > n` taken and not taken, `i < len(u)` / `i < len(v)` true and false
  (padding on either side), and `n == 0` (the loop never entered).

LOOP — the impl accumulates `acc` in a loop and then returns `root(psum(...))`;
model.py ties the two together with `Assert(acc == total)`, which is a contract
call and is stripped here. So that the copied loop is genuinely exercised
instead of being dead weight, the driver additionally replays the loop verbatim
(`impl_loop_acc`) and checks `acc == total` on every input — the stripped Assert
becomes a checked observation.

>= 1e5 Requires-satisfying inputs. Pinned seed: 11618 (recorded in mapping.md
under `## G-CONF`). Exit 0 iff zero disagreements; on a disagreement the input
and both outputs are printed and the exit code is 1. stdlib + sympy (the repo
package under change) only.
"""
import json
import random
import sys

SEED = 11618
N_MODELED = 100_000          # >= 1e5 modeled-domain differential inputs
N_BOUNDARY_FUZZ = 5_000      # scope-boundary (same-class, differing-length)


# --- Nagini carrier shims ----------------------------------------------------

class PSeq:
    """Immutable sequence carrier (`PSeq[int]`): the operations the copied impl
    region and pure helpers use are `len` and `[]` (plus `==`)."""
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(xs):
    """`ToSeq(list)` materializes the `PSeq` the specification is carried by."""
    return PSeq(*xs)


# --- @ContractOnly callee: the REAL repo function it axiomatizes -------------

def root(x):
    """model.py `root` is `@Pure @ContractOnly` — no body to copy. mapping.md
    §3.2 binds it to the unchanged `sympy.sqrt`, so call the real one."""
    from sympy import Integer, sqrt
    return sqrt(Integer(x))


# --- @Pure helpers from model.py, contracts stripped, otherwise verbatim -----

def coord(s, i):
    if i < len(s):
        return s[i]
    return 0


def term(u, v, i):
    return (coord(u, i) - coord(v, i)) * (coord(u, i) - coord(v, i))


def psum(u, v, k):
    if k == 0:
        return 0
    return psum(u, v, k - 1) + term(u, v, k - 1)


# --- the impl region of model.py, VERBATIM, contract calls stripped ----------

def point_distance(u, v):
    # impl-start
    n = len(u)
    if len(v) > n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    total = psum(ToSeq(u), ToSeq(v), len(u) if len(u) >= len(v) else len(v))
    return root(total)
    # impl-end


def impl_loop_acc(u, v):
    """The impl region's accumulation loop, copied verbatim from the same
    region, returning the accumulator. Exists only so the stripped
    `Assert(acc == total)` is checked on every input rather than assumed."""
    n = len(u)
    if len(v) > n:
        n = len(v)
    acc = 0
    i = 0
    while i < n:
        cu = 0
        if i < len(u):
            cu = u[i]
        cv = 0
        if i < len(v):
            cv = v[i]
        acc = acc + (cu - cv) * (cu - cv)
        i = i + 1
    return acc


# --- type bridge: model List[int] -> real sympy Point ------------------------

def to_point(Point, coords):
    """mapping.md §2 inverted. `Point(list)` sympifies the ints and dispatches
    on length: 2 -> Point2D, 3 -> Point3D, otherwise the generic n-D Point."""
    return Point(list(coords))


def same_class(Point, u, v):
    return type(to_point(Point, u)) is type(to_point(Point, v))


def in_modeled_domain(Point, u, v):
    """refinement.md §C: the gold computes the padded sum exactly when the two
    dimensions are equal or the two concrete classes differ."""
    return len(u) == len(v) or not same_class(Point, u, v)


# --- comparison --------------------------------------------------------------

def _exprs_equal(a, b):
    if a == b:
        return True
    from sympy import simplify
    try:
        return simplify(a - b) == 0
    except Exception:
        return False


def check_modeled(Point, u, v):
    """Shadow (contract-stripped impl region) vs the REAL patched
    Point.distance. Returns an error string, or None on agreement."""
    shadow = point_distance(u, v)
    real = to_point(Point, u).distance(to_point(Point, v))
    if not _exprs_equal(shadow, real):
        return ("DISAGREEMENT (modeled domain)\n"
                "  u=%r  v=%r  (classes %s / %s)\n"
                "  shadow point_distance = %r\n"
                "  real   Point.distance = %r"
                % (u, v, type(to_point(Point, u)).__name__,
                   type(to_point(Point, v)).__name__, shadow, real))
    # the stripped Assert(acc == total), checked rather than assumed
    acc = impl_loop_acc(u, v)
    total = psum(ToSeq(u), ToSeq(v), max(len(u), len(v)))
    if acc != total:
        return ("DISAGREEMENT (impl loop vs psum)\n"
                "  u=%r  v=%r  loop acc=%r  psum=%r" % (u, v, acc, total))
    return None


def check_scope_boundary(Point, u, v):
    """Same concrete class, differing dimension: refinement.md §C says the gold
    stays on its truncating pairwise path here (the model is deliberately
    stronger). Pin that POSITIVELY: real == sqrt(psum over MIN length)."""
    real = to_point(Point, u).distance(to_point(Point, v))
    truncated = root(psum(ToSeq(u), ToSeq(v), min(len(u), len(v))))
    if not _exprs_equal(real, truncated):
        return ("DISAGREEMENT (scope boundary: real is not the truncating "
                "path refinement.md §C claims)\n"
                "  u=%r  v=%r  real=%r  sqrt(psum min)=%r"
                % (u, v, real, truncated))
    return None


# --- inputs ------------------------------------------------------------------

def boundary_cases():
    """Boundary + F2P shapes. Each impl branch is taken at least once: the
    `len(v) > n` update taken (v longer) and not taken (u longer / equal), the
    padding `i < len(u)` / `i < len(v)` false on either side, and n == 0."""
    return [
        ([], []),                       # n == 0: loop never entered
        ([], [3, 4]),                   # u empty, v longer (padding on u)
        ([1, 2, 3], []),                # v empty, u longer (padding on v)
        ([0], [0]),                     # singletons, equal
        ([5], [7]),                      # singletons, generic Point both
        ([1, 0, 2], [2, 0]),            # F2P test_issue_11617 -> sqrt(5)
        ([2, 0], [1, 0, 2]),            # ... and its mirror
        ([2, 0], [1, 0]),               # Point2D vs Point2D
        ([1, 1], [4, 5]),               # 3-4-5 -> 5
        ([1, 2, 3], [1, 2, 3]),         # identical -> 0
        ([1, 0, 2], [3, 4, 5]),         # Point3D vs Point3D
        ([0, 0], [0, 0, 0]),            # origins, differing class
        ([1, 2, 3, 4], [5, 6]),         # generic Point(4) vs Point2D
        ([1, 2], [3, 4, 5, 6]),         # Point2D vs generic Point(4)
        ([1, 2, 3], [4, 5, 6, 7, 8]),   # Point3D vs generic Point(5)
        ([0, 0, 0, 0, 5], [0, 0]),      # long zero tail with a non-zero axis
        ([1, 2, 3, 4], [1, 0, 2]),      # generic Point(4) vs Point3D
        ([-6, 6], [6, -6]),             # negatives
        ([10 ** 6, -10 ** 6], [1, 1]),  # large magnitudes
        ([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]),   # equal, dim 6
    ]


def scope_boundary_cases():
    """Same-class, differing-dimension pairs (only the generic `Point` admits
    them: lengths 0, 1, 4, 5, 6, ...), including the G-AX negative control."""
    return [
        ([0], [0, 0, 0, 0, 5]),         # the G-AX negative control
        ([], [1]),
        ([], [1, 2, 3, 4]),
        ([7], [1, 2, 3, 4]),
        ([1, 2, 3, 4], [5]),
        ([1, 2, 3, 4], [5, 6, 7, 8, 9]),
        ([1, 2, 3, 4, 5], [0, 0, 0, 0]),
    ]


def rand_vec(rng):
    d = rng.choice([0, 1, 2, 3, 4, 5, 6])
    if rng.random() < 0.03:
        return [rng.randint(-10 ** 6, 10 ** 6) for _ in range(d)]
    return [rng.randint(-6, 6) for _ in range(d)]


# --- driver ------------------------------------------------------------------

def main():
    try:
        import inspect
        from sympy.geometry.point import Point, Point2D, Point3D
    except Exception as e:
        print("G-CONF ERROR: cannot import the patched sympy Point: %r" % e)
        return 2
    src = inspect.getsource(Point.distance)
    if "type(p) is not type(self)" not in src:
        print("G-CONF ERROR: loaded Point.distance lacks the gold hunk "
              "(patch not applied / stale module) - refusing to report "
              "agreement")
        return 2
    for cls in (Point2D, Point3D):
        if "distance" in cls.__dict__:
            print("G-CONF ERROR: %s overrides distance; the oracle binding in "
                  "mapping.md §1 is incomplete" % cls.__name__)
            return 2

    rng = random.Random(SEED)
    modeled = 0
    boundary = 0

    # 1) modeled domain: shadow vs the REAL patched function
    for u, v in boundary_cases():
        if not in_modeled_domain(Point, u, v):
            print("G-CONF ERROR: boundary case %r/%r is not in the modeled "
                  "domain" % (u, v))
            return 2
        err = check_modeled(Point, u, v)
        if err:
            print(err)
            print(json.dumps({"checked": modeled, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1
        modeled += 1
    n_boundary_cases = modeled

    while modeled < N_MODELED:
        u, v = rand_vec(rng), rand_vec(rng)
        if not in_modeled_domain(Point, u, v):
            # same-class differing-dim: handled by the scope-boundary pass
            if boundary < N_BOUNDARY_FUZZ:
                err = check_scope_boundary(Point, u, v)
                if err:
                    print(err)
                    print(json.dumps({"checked": modeled, "disagreements": 1,
                                      "seed": SEED, "status": "fail"}))
                    return 1
                boundary += 1
            continue
        err = check_modeled(Point, u, v)
        if err:
            print(err)
            print(json.dumps({"checked": modeled, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1
        modeled += 1

    # 2) scope boundary: pin the real (truncating) behaviour positively
    for u, v in scope_boundary_cases():
        if in_modeled_domain(Point, u, v):
            print("G-CONF ERROR: scope-boundary case %r/%r is actually in the "
                  "modeled domain" % (u, v))
            return 2
        err = check_scope_boundary(Point, u, v)
        if err:
            print(err)
            print(json.dumps({"checked": modeled, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1
        boundary += 1

    # 3) negative control (same pair G-AX uses): the documented divergence must
    #    really occur, i.e. the model IS strictly stronger off-domain. If this
    #    ever agreed, refinement.md §C's scoping would be describing a
    #    boundary that does not exist.
    cu, cv = [0], [0, 0, 0, 0, 5]
    real_off = to_point(Point, cu).distance(to_point(Point, cv))
    model_off = point_distance(cu, cv)
    if _exprs_equal(real_off, model_off):
        print("G-CONF FAIL: negative control agreed - the same-class "
              "differing-dimension pair %r/%r was expected to diverge "
              "(real=%r, model=%r) per refinement.md §C"
              % (cu, cv, real_off, model_off))
        print(json.dumps({"checked": modeled, "disagreements": 1,
                          "seed": SEED, "status": "fail"}))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py (root -> real "
          "sympy.sqrt) == real patched Point.distance on %d modeled-domain "
          "inputs (%d boundary + fuzz, seed=%d), impl loop acc == psum on all "
          "of them; %d same-class differing-dim pairs confirmed to follow the "
          "gold's truncating path (scope boundary, refinement.md §C) with "
          "the negative control %r/%r diverging as documented (real=%r, "
          "model=%r); 0 disagreements."
          % (modeled, n_boundary_cases, SEED, boundary, cu, cv,
             real_off, model_off))
    print(json.dumps({"checked": modeled, "scope_boundary_checked": boundary,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "sympy.geometry.point.Point.distance (called)",
                      "status": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
