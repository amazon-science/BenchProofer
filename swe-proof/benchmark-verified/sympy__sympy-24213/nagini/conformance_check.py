#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24213 (nagini).

SHADOW -- the impl region of `model.py`, copied VERBATIM below with only the
contract calls removed (this bundle's impl region carries `Invariant(...)` calls
and the `# invariants-start/-end` markers; there are no `Assert`/`Fold`/`Unfold`
calls in it).  The `@Pure` helper the region calls, `equivalent`, is copied over
minus its contracts.  No `PSeq` appears in this model -- the carrier is
`List[int]`, so no sequence shim is needed.

  model.py impl region                        shadow below
  ------------------------------------------  --------------------------------
  i = 1                                       identical
  while i < len(surf): <invariants stripped>   identical
      if not equivalent(red[0], red[i]):       identical
          raise DimensionMismatch()            identical
      i = i + 1                                identical
  return red[0]                                identical

The one `@ContractOnly` callee, `reduction_of` (mapping.md 3.2), has no body to
copy.  It is *not* called from the impl region -- it appears only in the
precondition `red[i] == reduction_of(surf[i])`.  So it is realized here as the
REAL repo function it axiomatizes,
`DimensionSystem.get_dimensional_dependencies` (sympy/physics/units/
dimensions.py:422), interned to an int; every generated input is then CHECKED to
satisfy `red[i] == reduction_of(surf[i])` with that real engine in the loop.
The axiom is therefore exercised on real repo values, not assumed.

ORACLE -- the REAL patched repo function, CALLED, not transliterated:
`UnitSystem._collect_factor_and_dimension` (sympy/physics/units/
unitsystem.py:152, the `Add` branch at :173-184 whose guard at :178 the gold
patch changes to `not self.get_dimension_system().equivalent_dims(dim,
addend_dim)`).  The gate applies patch.diff to /testbed before this script runs
and PYTHONPATH=/testbed makes the patched module importable, so `SI` here is
the patched system.  We drive it on a real `Add` expression of real
`Quantity`-valued terms and observe the two things the model observes: whether
it returns or raises `ValueError`, and (on return) which dimension it reports.
Nothing is reimplemented: the velvet sibling replicated the Add loop in-process,
this check does not.

TYPE BRIDGE (mapping.md 2, inverted).  The model carries two int facets per
addend; the repo carries a `Dimension` object per addend.

  repo -> model:  for each `d` in `[dim for _, dim in map(collect, expr.args)]`
                  (the unchanged recursive sub-collection, exactly mapping.md
                  2's "the recursion's first addend expr.args[0]" row),
                    surf[i] = SURFACE.intern(d)      -- keyed by structural
                              `Dimension.__eq__`, the pre-patch `dim !=
                              addend_dim` observation
                    red[i]  = REDUCTION.intern(frozenset(
                                get_dimensional_dependencies(d).items()))
                              -- keyed by the canonical dependency multiset,
                              exactly what `equivalent_dims` compares
  model -> repo:  the shadow's return value `red[0]` is compared against
                  REDUCTION.intern(...) of the dimension the real function
                  reports; `DimensionMismatch` is compared against `ValueError`.

Generation runs in the repo->model direction (build real sums, derive the
facets) so every input satisfies the Requires *by construction*: `len(surf) ==
len(red) >= 1` holds, and `red[i] == reduction_of(surf[i])` holds because both
facets are functions of the same real `Dimension` -- which is also asserted
per-input rather than trusted.  Inputs whose addends the real engine cannot
reduce (`TypeError`: symbolic/non-integer Pow, mapping.md 3.2 "out of the
modeled domain") are outside the Requires and are counted and reported, not
silently dropped.

INPUT DOMAIN.  The modeled space (int lists) is infinite, so this is not an
exhaustive check; but the *shape* space over a fixed 14-term catalog is
enumerated exhaustively for sums of length 1, 2 and 3 (14 + 196 + 2744 = 2954
sums) before fuzzing over lengths 1..6 fills the count to >= 1e5.  The catalog
is built so that distinct surface dimensions share a canonical reduction
(`velocity` vs `acceleration*time` vs `length/time`; `force` vs
`mass*acceleration`; `length` vs `acceleration*time**2`; `Dimension(1)` vs
`length/length`) -- that pair class is the branch the gold patch changed, and a
run that failed to exercise it would certify nothing, so it is tracked as a
coverage obligation and a miss is a hard failure.  Every branch of the impl
region (loop never entered; loop completes; reject at i == 1; reject at i > 1)
plus the F2P shape `A1*T1 + V1` (test_issue_24211) are likewise obligations.

Pinned fuzz seed: 24213 (recorded in mapping.md under "## G-CONF").
stdlib + sympy (the repo under test) only.  Exit 0 iff zero disagreements.
"""
import json
import random
import sys

SEED = 24213
N_TARGET = 100_000
MAX_REPORT = 5

# Coverage obligations: a green run must have exercised each of these.
OBLIGATIONS = (
    "loop-not-entered",            # len(surf) == 1: return red[0] with no test
    "loop-completes",              # every addend equivalent -> return red[0]
    "reject-at-first-addend",      # not equivalent(red[0], red[1]) -> raise
    "reject-after-accepting",      # reject at i > 1 (some addends accepted)
    "accept-surface-distinct",     # THE patched branch: surf differs, red same
    "reject-surface-distinct",     # surf differs AND red differs
    "f2p-shape",                   # A1*T1 + V1  (test_issue_24211)
)


class DimensionMismatch(Exception):
    """model.py's user-defined rejection exception; the repo signals the same
    rejection with `raise ValueError(...)` (unitsystem.py:179-182)."""
    pass


# --- @Pure helper from model.py, contracts stripped ---------------------------

def equivalent(red_a, red_b):
    return red_a == red_b


# --- the impl region of model.py, VERBATIM, contract calls stripped -----------

def collect_sum_dimension(surf, red):
    i = 1
    while i < len(surf):
        if not equivalent(red[0], red[i]):
            raise DimensionMismatch()
        i = i + 1
    return red[0]


# --- type bridge: repo Dimension -> the model's two int facets ----------------

class Interner:
    """Stable int identity for a hashable key; the model's `surf`/`red` ints."""

    def __init__(self):
        self._ids = {}
        self._keys = []

    def intern(self, key):
        got = self._ids.get(key)
        if got is None:
            got = len(self._ids)
            self._ids[key] = got
            self._keys.append(key)
        return got

    def key_of(self, ident):
        return self._keys[ident]


SURFACE = Interner()
REDUCTION = Interner()


class Bridge:
    def __init__(self, ds):
        self.ds = ds

    def surf_of(self, dim):
        # structural Dimension identity: the pre-patch `dim != addend_dim`
        # observation (sympy Basic hashing/equality is structural).
        return SURFACE.intern(dim)

    def reduction_of_dim(self, dim):
        """The REAL `reduction_of` axiom body: the repo engine
        get_dimensional_dependencies, interned. Raises on out-of-domain dims."""
        deps = self.ds.get_dimensional_dependencies(dim)
        return REDUCTION.intern(frozenset(deps.items()))

    def reduction_of_surf(self, surf_id):
        """`reduction_of(surface)` as the model states it: a function of the
        SURFACE identity alone. Backed by the real engine via the interned
        Dimension object, so equal surf ids must yield equal reductions."""
        return self.reduction_of_dim(SURFACE.key_of(surf_id))


# --- ORACLE: the real patched repo function, called --------------------------

def oracle(SI, expr):
    """Drive the patched UnitSystem._collect_factor_and_dimension on the real
    Add expression; report ("ok", dim) or ("raise", None)."""
    try:
        _factor, dim = SI._collect_factor_and_dimension(expr)
    except ValueError:
        return ("raise", None)
    return ("ok", dim)


def shadow(surf, red):
    try:
        return ("ok", collect_sum_dimension(surf, red))
    except DimensionMismatch:
        return ("raise", None)


class Differ:
    def __init__(self, SI, bridge):
        self.SI = SI
        self.bridge = bridge
        self.count = 0
        self.skipped = 0
        self.bad = []
        self.covered = set()

    def check(self, label, terms):
        """One trial: build the real sum, bridge it to the model carrier, run
        both sides. Returns True if the trial was in-domain and checked."""
        from sympy.core.add import Add

        SI, br = self.SI, self.bridge
        if len(terms) == 1:
            # A one-addend sum is not representable as a sympy Add (Add(x)
            # collapses to x), yet it IS in the model's domain (len(surf) >= 1).
            # The Add branch on a length-1 args tuple computes exactly
            # `collect(args[0])` with an empty loop, so the oracle for this
            # shape is the collection of that single term.
            expr = terms[0]
            args = (terms[0],)
        else:
            expr = Add(*terms, evaluate=False)
            if not getattr(expr, "is_Add", False) or len(expr.args) < 2:
                self.skipped += 1     # collapsed/cancelled: not a sum any more
                return False
            args = expr.args

        # The unchanged recursive sub-collection supplies each addend's
        # Dimension (mapping.md 1: `(addend_factor, addend_dim)`).
        try:
            dims = [SI._collect_factor_and_dimension(a)[1] for a in args]
            surf = [br.surf_of(d) for d in dims]
            red = [br.reduction_of_dim(d) for d in dims]
        except (TypeError, ValueError):
            self.skipped += 1         # engine cannot reduce it: out of domain
            return False

        # --- the Requires, checked (not assumed) on every input --------------
        assert len(surf) == len(red) and len(surf) >= 1, (surf, red)
        for i in range(len(surf)):
            # red[i] == reduction_of(surf[i]) with reduction_of = the REAL
            # get_dimensional_dependencies: exercises the axiom.
            if red[i] != br.reduction_of_surf(surf[i]):
                self.bad.append(
                    "BRIDGE/AXIOM VIOLATION %s: red[%d]=%d but "
                    "reduction_of(surf[%d]=%d)=%d"
                    % (label, i, red[i], i, surf[i],
                       br.reduction_of_surf(surf[i])))
                return False

        got = shadow(surf, red)
        want = oracle(SI, expr)
        self.count += 1
        self._record_coverage(surf, red, got, label)

        if got[0] != want[0]:
            self._fail(label, args, surf, red, got, want)
            return True
        if got[0] == "ok":
            # bridge the shadow's int result back to the reported Dimension
            try:
                want_red = br.reduction_of_dim(want[1])
            except (TypeError, ValueError):
                self._fail(label, args, surf, red, got, want)
                return True
            if got[1] != want_red:
                self._fail(label, args, surf, red, got,
                           ("ok", "%s -> red=%d" % (want[1], want_red)))
        return True

    def _fail(self, label, args, surf, red, got, want):
        if len(self.bad) < MAX_REPORT:
            self.bad.append(
                "DISAGREE %s: addends=%r surf=%r red=%r shadow=%r oracle=%r"
                % (label, [str(a) for a in args], surf, red, got, want))
        else:
            self.bad.append("DISAGREE %s (suppressed)" % label)

    def _record_coverage(self, surf, red, got, label):
        c = self.covered
        if len(surf) == 1:
            c.add("loop-not-entered")
        if got[0] == "ok" and len(surf) > 1:
            c.add("loop-completes")
        # index of the first rejected addend, as the impl region walks it
        first_bad = None
        for i in range(1, len(red)):
            if red[i] != red[0]:
                first_bad = i
                break
        if first_bad == 1:
            c.add("reject-at-first-addend")
        elif first_bad is not None and first_bad > 1:
            c.add("reject-after-accepting")
        for i in range(1, len(surf)):
            if surf[i] != surf[0]:
                if red[i] == red[0]:
                    c.add("accept-surface-distinct")
                else:
                    c.add("reject-surface-distinct")
        if label == "f2p":
            c.add("f2p-shape")


def build_catalog(SI):
    """Real Quantity terms whose collected dimensions cover: surface-distinct
    pairs sharing a canonical reduction, surface-distinct pairs with different
    reductions, and dimensionless."""
    from sympy.physics.units import (
        Quantity, meter, second, kilogram,
        velocity, acceleration, time as time_dim, length, mass,
    )
    from sympy.core.add import Add

    def q(name, dim, sf):
        x = Quantity(name)
        SI.set_quantity_dimension(x, dim)
        SI.set_quantity_scale_factor(x, sf)
        return x

    V1 = q("cf_V1", velocity, 1 * meter / second)
    A1 = q("cf_A1", acceleration, 1 * meter / second ** 2)
    T1 = q("cf_T1", time_dim, 1 * second)
    L1 = q("cf_L1", length, 1 * meter)
    M1 = q("cf_M1", mass, 1 * kilogram)

    terms = [
        ("V1", V1),                     # Dimension(velocity)
        ("A1*T1", A1 * T1),             # acceleration*time  == velocity
        ("L1/T1", L1 / T1),             # length/time        == velocity
        ("A1", A1),                     # acceleration
        ("L1/T1**2", L1 / T1 ** 2),     # length/time**2     == acceleration
        ("T1", T1),                     # time
        ("L1", L1),                     # length
        ("A1*T1**2", A1 * T1 ** 2),     # acceleration*time^2 == length
        ("M1", M1),                     # mass
        ("M1*A1", M1 * A1),             # mass*acceleration  (force-like)
        ("M1*L1/T1**2", M1 * L1 / T1 ** 2),   # == mass*acceleration
        ("L1/L1", L1 / L1),             # dimensionless, surface length/time-free
        ("3", 3),                       # plain number -> Dimension(1)
        ("(V1+A1*T1)", Add(V1, A1 * T1, evaluate=False)),   # nested sum addend
    ]
    return terms, (V1, A1, T1)


def main():
    from sympy.physics.units.systems.si import SI

    ds = SI.get_dimension_system()
    bridge = Bridge(ds)
    d = Differ(SI, bridge)

    terms, (V1, A1, T1) = build_catalog(SI)
    names = [n for n, _ in terms]
    vals = {n: v for n, v in terms}

    # --- boundary: the F2P shape, singletons, the discriminating pairs -------
    n_boundary = 0
    d.check("f2p", [A1 * T1, V1])          # test_issue_24211, must NOT raise
    n_boundary += 1
    for label, chosen in [
        ("f2p-reversed", ["V1", "A1*T1"]),
        ("single-V1", ["V1"]),
        ("single-3", ["3"]),
        ("equiv-3way", ["V1", "A1*T1", "L1/T1"]),
        ("reject-i1", ["V1", "M1"]),
        ("reject-i2", ["V1", "A1*T1", "M1"]),
        ("reject-i3", ["V1", "A1*T1", "L1/T1", "L1"]),
        ("force-pair", ["M1*A1", "M1*L1/T1**2"]),
        ("length-pair", ["A1*T1**2", "L1"]),
        ("accel-pair", ["A1", "L1/T1**2"]),
        ("dimensionless-pair", ["L1/L1", "3"]),
        ("nested", ["(V1+A1*T1)", "V1"]),
        ("identical", ["V1", "V1"]),
        ("max-len", names[:6]),
    ]:
        d.check(label, [vals[n] for n in chosen])
        n_boundary += 1

    # --- exhaustive over the catalog's sums of length 1, 2 and 3 -------------
    n_exhaustive = 0
    for a in names:
        d.check("ex1", [vals[a]])
        n_exhaustive += 1
        for b in names:
            d.check("ex2", [vals[a], vals[b]])
            n_exhaustive += 1
            for c in names:
                d.check("ex3", [vals[a], vals[b], vals[c]])
                n_exhaustive += 1

    # --- seeded fuzz over lengths 1..6 to fill the count --------------------
    rng = random.Random(SEED)
    n_fuzz = 0
    while d.count < N_TARGET:
        k = rng.randint(1, 6)
        chosen = [vals[rng.choice(names)] for _ in range(k)]
        d.check("fuzz", chosen)
        n_fuzz += 1

    missed = [o for o in OBLIGATIONS if o not in d.covered]
    if missed and not d.bad:
        d.bad.append("COVERAGE MISS: obligation(s) never exercised: %s "
                     "(a green verdict would certify nothing)"
                     % ", ".join(missed))

    if d.bad:
        print("G-CONF FAIL: %d problem(s) over %d Requires-satisfying inputs"
              % (len(d.bad), d.count))
        for line in d.bad[:MAX_REPORT]:
            print("  " + line)
        print(json.dumps({"checked": d.count, "disagreements": len(d.bad),
                          "seed": SEED, "skipped_out_of_domain": d.skipped,
                          "obligations_missed": missed,
                          "shadow": "direct (contract-stripped impl region)"}))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py "
          "(collect_sum_dimension) agrees with the REAL patched "
          "UnitSystem._collect_factor_and_dimension Add branch "
          "(sympy/physics/units/unitsystem.py:173-184, called) on %d "
          "Requires-satisfying inputs (%d boundary + %d exhaustive "
          "length-1/2/3 sums over a 14-term catalog + %d seeded fuzz, "
          "seed=%d); %d out-of-domain inputs skipped; all %d coverage "
          "obligations exercised incl. the surface-distinct/reduction-equal "
          "branch the patch changed and the F2P shape A1*T1+V1; "
          "0 disagreements."
          % (d.count, n_boundary, n_exhaustive, n_fuzz, SEED, d.skipped,
             len(OBLIGATIONS)))
    print(json.dumps({
        "checked": d.count, "disagreements": 0, "seed": SEED,
        "skipped_out_of_domain": d.skipped,
        "obligations": sorted(d.covered),
        "shadow": "direct (contract-stripped impl region of model.py)",
        "oracle": ("called: UnitSystem._collect_factor_and_dimension "
                   "(sympy/physics/units/unitsystem.py:152, Add branch :173-184, "
                   "gold-patched)"),
        "axiom_reduction_of": ("called: DimensionSystem."
                               "get_dimensional_dependencies "
                               "(sympy/physics/units/dimensions.py:422)"),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
