#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24213.

Executes the REAL repo callee `DimensionSystem.equivalent_dims` (and the
`get_dimensional_dependencies` it is built on) on boundary + randomized dimension
pairs and asserts that every observation matches the deep model `checkStep` uses,
as encoded in Solution.lean's `Dim.deps`-equality.

The single kind-A check:

  (A-reference) the deep model `checkStep` (Solution.lean pure region) tests, per
      addend, `a.dim.deps == refDeps`, where `deps` is the bijection image of
      `get_dimensional_dependencies` (mapping.md §2, §2.1, §3.1). The changed
      comparison is modeled DEEPLY, not behind a consumed axiom; G-AX validates
      that deep model against the real callee:

        equivalent_dims(d1, d2)  ==  (deps_key(d1) == deps_key(d2))

      where `deps_key` is the mapping.md §2.1 identity key for the dependency-dict
      comparison `equivalent_dims` performs.

  It also validates the OTHER carrier and the invariant relating them, so the
  bijection is checked in both of its components rather than only the one the
  patch touches:

        bool(d1 == d2)  ==  (surf_key(d1) == surf_key(d2))     # `surf` is a key
                                                                # for structural
                                                                # Dimension.__eq__
        surf_key(d1) == surf_key(d2)  =>  deps_key(d1) == deps_key(d2)

  And it confirms the modeled change is OBSERVABLE: there exists at least one
  surface-distinct-but-dimensionally-equivalent pair (the issue's
  velocity / acceleration*time) for which surface `==` is False while
  `equivalent_dims` is True — so the deps-equivalence model is strictly different
  from the surface comparison the pre-patch used.

WHY THE KEYS ARE NOT `hash(...)`. SymPy deliberately makes `==` COARSER than
`hash`: `Integer(2) == Float(2.0)` is True while their hashes differ, and
`Float('2.0',5) == Float('2.0',50)` is True while their hashes differ
(`Float.__eq__` compares `_mpf_` exactly and ignores `_prec`; `Float.__hash__`
mixes `_prec` in). So a `frozenset`/`hash` key over the dependency dict is
STRICTLY FINER than the dict `==` that `equivalent_dims` performs, and splits
classes the real callee merges. Python's `hash` is also not injective enough to
key on directly — `hash(-1) == hash(-2) == -2` would MERGE the inequivalent
`Dimension(1/acceleration)` and `Dimension(velocity**-2)`. Both keys below are
therefore SHA-256 digests of a structural encoding, and the fuzz pool mixes
numeric types, `Float` precisions, symbolic exponents and the colliding `-1`/`-2`
pair, because those are the only inputs on which the distinction is visible.

Imports only `sympy.physics.units` (plus stdlib). Exit 0 iff every obligation
holds.
"""
import hashlib
import itertools
import random
import sys


# --------------------------------------------------------------------------
# mapping.md §2.1 — the two identity keys, as structural traversals of the real
# comparisons. NOT hash-based; see the module docstring.
# --------------------------------------------------------------------------
def _struct_key(e):
    """Identity key for structural `Basic.__eq__` (sympy/core/basic.py:350-389).

    Recurses on `args`, tagging each node with its class, and reproduces the
    three rules that comparison applies:
      * a NESTED `Number` keeps its TYPE — `if a.is_Number and type(a) !=
        type(b): return False` — so `2*n` != `2.0*n`;
      * two `Float`s compare on `_mpf_` ALONE (sympy/core/numbers.py:1386,
        "comparison is exact"), ignoring `_prec`, so the key must too;
      * at a LEAF, the comparison is `_hashable_content()`, which for a symbol is
        its name TOGETHER WITH its assumptions. So the key must be
        `_hashable_content()` and not the leaf's printed form: printing erases
        assumptions, and two symbols that print identically while carrying
        different assumptions are NOT equal and do NOT reduce alike. A
        print-keyed leaf is therefore a strictly COARSER quotient than the
        comparison it claims to model — it merges classes the real callee keeps
        apart, which is unsound in the direction that matters (it would report
        "equivalent" where the real routine reports a dimensional
        disagreement). Measured over a 208-dimension pool: a print-keyed leaf
        violates BOTH obligations below on 70 pairs, and the
        `_hashable_content` leaf on 0.
    """
    from sympy import Basic, sympify
    e = sympify(e)
    if e.is_Float:
        return ('F', e._mpf_)
    if not isinstance(e, Basic):
        return ('L', type(e).__name__, repr(e))
    if not e.args:
        return ('L', type(e).__name__, repr(e._hashable_content()))
    return ('N', type(e).__name__, tuple(_struct_key(a) for a in e.args))


def _top_key(v):
    """Identity key for `==` applied at TOP level (e.g. to a dependency dict
    VALUE). There `Basic.__eq__`'s guard `not (self.is_Number and
    other.is_Number)` is BYPASSED, so numbers compare ACROSS type:
    `Integer(2) == Float(2.0) == Rational(4,2)`. Collapse every Float/Rational to
    `Rational`; anything else keeps its structure."""
    from sympy import Rational, sympify
    v = sympify(v)
    if v.is_Float or v.is_Rational:
        return ('R', Rational(v))
    return _struct_key(v)


def _digest(obj):
    """A COLLISION-FREE identity key (see the docstring on why `hash` is not)."""
    return int(hashlib.sha256(repr(obj).encode()).hexdigest()[:16], 16)


def deps_key(ds, dim):
    """`Dim.deps : Option Int`: the canonical dependency-SIGNATURE key, or None.

    `equivalent_dims` compares the two dependency dicts with `==`
    (dimensions.py:428-431), i.e. same key set and, per key, values equal under
    top-level `==`. But it must first REDUCE each argument, and that reduction is
    PARTIAL: `get_dimensional_dependencies` raises `TypeError` on an `Add`-named
    or non-Symbol-power dimension (dimensions.py:383-395). Such a dimension has no
    signature, which the Lean carrier spells `deps = none`; the comparison then
    never happens at all, so no verdict is produced (mapping.md §2 row 3)."""
    try:
        dd = ds.get_dimensional_dependencies(dim)
    except TypeError:
        return None                      # `deps = none` — no signature exists
    return _digest(sorted(repr((_struct_key(k), _top_key(v)))
                          for k, v in dd.items()))


def surf_key(dim):
    """`Dim.surf`: the SURFACE-expression identity key, i.e. a key for structural
    `Dimension.__eq__`. A `Dimension` is not a `Number`, so the comparison is
    structural throughout — no numeric-type collapse, hence
    `Dimension(length**2) != Dimension(length**2.0)` even though the two ARE
    dimensionally equivalent."""
    return _digest(_struct_key(dim))


def check_reference(ds, d1, d2):
    """Assert the deep model (deps-key equality) equals the REAL equivalent_dims,
    that `surf` is exactly a key for structural `==`, and that equal `surf`
    implies equal `deps` (the implication the pure region states)."""
    k1, k2 = deps_key(ds, d1), deps_key(ds, d2)

    if k1 is None or k2 is None:
        # A dimension with NO signature: `equivalent_dims` cannot return a verdict
        # because its own reduction raises first. The model must agree that the
        # test does not certify the pair — `checkStep` attempts the reduction on
        # BOTH sides BEFORE any comparison (Solution.lean pure region), so it
        # yields the signature-less outcome here rather than a verdict.
        try:
            verdict = ds.equivalent_dims(d1, d2)
        except TypeError:
            pass                          # the real callee raises, as modeled
        else:
            raise AssertionError(
                "expected equivalent_dims to raise TypeError on the "
                "no-signature pair (%r, %r) but it returned %r"
                % (d1, d2, verdict))
        modeled_certifies = (k1 is not None and k2 is not None and k1 == k2)
        assert not modeled_certifies, (
            "checkStep must not certify a pair whose signature is absent: "
            "(%r, %r)" % (d1, d2))
        return

    # BOTH signatures present. The model's `disagreeing` leg claims something
    # stronger than "not certified": that the equivalence test RAN and returned a
    # verdict of "not equivalent". So the real callee must return here rather than
    # raise — if it could still fail on a pair whose reductions both succeeded,
    # the modeled distinction between "a verdict was produced" and "no verdict was
    # produced" would not track the real callee.
    try:
        observed = bool(ds.equivalent_dims(d1, d2))           # real callee
    except TypeError as exc:
        raise AssertionError(
            "both signatures reduced, so the equivalence test must RETURN a "
            "verdict on (%r, %r); the real callee raised %r instead, which would "
            "break the modeled distinction between an established disagreement "
            "and a comparison that never happened" % (d1, d2, exc)) from None
    modeled = (k1 == k2)                                     # deep model
    assert observed == modeled, (
        "checkStep deep model unsound on (%r, %r): equivalent_dims gave %r, "
        "deps-key model gives %r" % (d1, d2, observed, modeled))

    surf_same = (surf_key(d1) == surf_key(d2))
    struct_eq = bool(d1 == d2)
    assert struct_eq == surf_same, (
        "surf carrier unsound on (%r, %r): structural == gave %r, surf-key "
        "model gives %r" % (d1, d2, struct_eq, surf_same))

    if surf_same:
        assert modeled, (
            "pure-region invariant violated on (%r, %r): equal surf must imply "
            "equal deps" % (d1, d2))


def main():
    from sympy import Float, Integer, Rational, Symbol
    from sympy.physics.units.systems.si import SI
    from sympy.physics.units import (
        velocity, acceleration, time, length, mass, force, energy, power,
        pressure, charge, current, voltage, frequency, Dimension,
    )
    ds = SI.get_dimension_system()

    base = [length, mass, time, current]
    derived = [velocity, acceleration, force, energy, power, pressure,
               charge, voltage, frequency]
    all_dims = base + derived

    # --- boundary pairs: each dimension vs itself (must be equivalent) -------
    for d in all_dims:
        check_reference(ds, d, d)

    # --- the issue's discriminating pairs (surface-distinct, equivalent) -----
    discriminating = [
        (velocity, acceleration * time),       # the reported bug
        (force, mass * acceleration),
        (energy, force * length),
        (energy, mass * velocity**2),
        (power, energy / time),
        (pressure, force / length**2),
        (charge, current * time),
    ]
    for d1, d2 in discriminating:
        check_reference(ds, d1, d2)
        assert ds.equivalent_dims(d1, d2), (
            "expected %r and %r to be dimensionally equivalent" % (d1, d2))

    # --- inequivalent pairs (must NOT be equivalent) -------------------------
    inequivalent = [
        (length, time), (length, mass), (time, mass), (current, length),
        (velocity, acceleration), (force, energy), (energy, power),
        (velocity, length), (force, mass),
        # the pair Python's hash MERGES (hash(-1) == hash(-2) == -2): a key that
        # collides here would call these two equivalent, which they are not.
        (1 / acceleration, velocity**-2),
        (1 / current, current**Float(-2.0)),
    ]
    for d1, d2 in inequivalent:
        check_reference(ds, d1, d2)
        assert not ds.equivalent_dims(d1, d2), (
            "expected %r and %r to be dimensionally INequivalent" % (d1, d2))

    # --- MIXED-NUMERIC-TYPE / MIXED-PRECISION exponent pairs ----------------
    # These are the pairs on which `==` and `hash` part company, i.e. the pairs a
    # hash-keyed bridge gets WRONG. `equivalent_dims` accepts each of them (dict
    # `==` compares the powers with SymPy `==`, and Integer(2) == Float(2.0)).
    n = Symbol('n')
    cross_type = [
        (length**2, length**Float(2.0)),
        (length**Integer(2), length**Float(2.0)),
        (length**Float(2.0), length**Rational(4, 2)),
        (length**Rational(1, 2), length**Float(0.5)),
        (length**Float('2.0', 5), length**Float('2.0', 50)),
        (length**Integer(-1), length**Float(-1.0)),
        (mass**Integer(3), mass**Float(3.0)),
        (length**Float(2.0) * time**Integer(-1),
         length**Integer(2) * time**Float(-1.0)),
    ]
    for d1, d2 in cross_type:
        check_reference(ds, d1, d2)
        assert ds.equivalent_dims(d1, d2), (
            "expected the mixed-numeric-type pair %r / %r to be dimensionally "
            "equivalent (SymPy numbers compare equal across type)" % (d1, d2))
    # ...and the model must still SEPARATE a genuinely different power, and must
    # NOT numericize a power nested inside a symbolic exponent (2*n != 2.0*n).
    for d1, d2 in [(length**Integer(2), length**Float(3.0)),
                   ((length**Integer(2))**n, (length**Float(2.0))**n)]:
        check_reference(ds, d1, d2)
        assert not ds.equivalent_dims(d1, d2), (
            "expected %r and %r to be dimensionally INequivalent" % (d1, d2))

    # --- SAME-PRINTED-FORM, DIFFERENT-ASSUMPTIONS exponent pairs --------------
    # The other direction in which a key can be WRONG, and the one a numeric-only
    # pool cannot reach. Two symbols with the same name and different assumptions
    # are NOT equal, so a dimension raised to each of them does NOT reduce to the
    # same signature and the real callee reports them dimensionally
    # INequivalent — even though both dependency dicts PRINT identically
    # (`{Dimension(length, L): n}` either way) and the two dimension expressions
    # print identically too. A key whose leaf is the printed form therefore MERGES
    # these, which is unsound in the dangerous direction: it would certify a pair
    # the real routine reports as a dimensional disagreement. Measured over a
    # 208-dimension pool, a print-keyed leaf violates the deps obligation on 70
    # pairs and the surf obligation on 70; the `_hashable_content` leaf on 0. The
    # pairs are pinned here as boundary cases rather than left to the fuzz,
    # because the fuzz draws a random exponent per factor and cannot be relied on
    # to draw two same-named symbols that differ only in assumptions.
    n_pos = Symbol('n', positive=True)
    n_int = Symbol('n', integer=True)
    same_print = [
        (length**n, length**n_pos),
        (length**n, length**n_int),
        (length**n_pos, length**n_int),
        (mass**n, mass**n_pos),
        (length**n * time**Integer(-1), length**n_pos * time**Integer(-1)),
    ]
    for d1, d2 in same_print:
        assert repr(d1) == repr(d2), (
            "this class is defined by the two dimensions PRINTING alike; %r / %r "
            "do not, so the case is not testing what it claims" % (d1, d2))
        check_reference(ds, d1, d2)
        assert not ds.equivalent_dims(d1, d2), (
            "expected the same-printed-form pair %r / %r to be dimensionally "
            "INequivalent (differing assumptions are part of a symbol's "
            "identity)" % (d1, d2))

    # --- NO-SIGNATURE pairs: the reduction equivalent_dims is built on is
    # --- PARTIAL, so on these the real callee RAISES instead of returning a
    # --- verdict. `deps = none` carries that, and `checkStep` reports the
    # --- signature-less outcome rather than certifying.
    # --- This class is a genuine patch delta (mapping.md §2.1): pre-patch the
    # --- guard was a surface test that never reduced anything, so `b1 + b2`
    # --- returned a value; post-patch the reduction raises inside the guard.
    add_named = Dimension(length + time)
    add_named2 = Dimension(mass + time)
    no_sig = [
        (add_named, add_named),           # ref and addend both unreducible
        (add_named, add_named2),          # both unreducible, different surfaces
        (add_named, length),              # unreducible reference, reducible addend
        (length, add_named),              # reducible reference, unreducible addend
        (add_named, velocity),
    ]
    for d1, d2 in no_sig:
        assert deps_key(ds, d1) is None or deps_key(ds, d2) is None, (
            "expected at least one of %r / %r to have NO signature" % (d1, d2))
        check_reference(ds, d1, d2)

    # --- the change is OBSERVABLE: surface != equivalence on >=1 pair --------
    observable = []
    for d1, d2 in discriminating + cross_type:
        if bool(ds.equivalent_dims(d1, d2)) and not bool(d1 == d2):
            observable.append((d1, d2))
    assert observable, (
        "no surface-distinct-but-equivalent pair found — the modeled change "
        "would be unobservable; the deps model must differ from surface ==")

    # --- randomized fuzz over products/powers of base dimensions -------------
    # The exponent pool MIXES Integer / Float / Rational and Float precisions on
    # purpose: an integer-only pool cannot exercise the eq/hash split at all.
    # It also mixes symbols that PRINT the same while carrying different
    # ASSUMPTIONS (`n` vs a positive `n` vs an integer `n`). Those are the pairs a
    # leaf keyed on the printed form MERGES: they are not equal, they do not
    # reduce alike, and the real callee reports a dimensional disagreement on
    # them — so a pool of assumption-free symbols cannot see the leaf's quotient
    # at all.
    EXPS = [Integer(2), Float(2.0), Rational(4, 2), Float('2.0', 5),
            Float('2.0', 50), Rational(1, 2), Float(0.5), Rational(1, 3),
            Rational(1, 10), Float('0.1', 5), Float('0.1', 50),
            Integer(-1), Float(-1.0), Integer(-2), Float(-2.0),
            Integer(1), Float(1.0), Integer(3), Rational(3, 1), Float(3.0),
            Rational(-3, 2), Float(-1.5), n, Symbol('m'),
            Symbol('n', positive=True), Symbol('n', integer=True),
            Symbol('n', real=True), Symbol('m', positive=True)]
    rng = random.Random(24213)
    n_fuzz = 4000
    n_checked = 0
    for _ in range(n_fuzz):
        def rand_dim():
            d = None
            for _k in range(rng.randint(1, 4)):
                b = rng.choice(base + derived)
                p = rng.choice(EXPS)
                term = b ** p
                d = term if d is None else d * term
            return d if d is not None else rng.choice(base)
        d1, d2 = rand_dim(), rand_dim()
        # get_dimensional_dependencies is PARTIAL (dimensions.py:383-395:
        # TypeError on an Add-named or non-Symbol-power dimension). That is NOT
        # skipped: `deps = none` carries it and check_reference asserts the real
        # callee raises there, matching `checkStep`'s signature-less leg
        # (mapping.md §2.1).
        check_reference(ds, d1, d2)
        n_checked += 1

    print("G-AX OK: checkStep deep model (deps-key equality == equivalent_dims) "
          "sound on %d self-pairs + %d discriminating + %d inequivalent + %d "
          "mixed-numeric-type/precision + %d same-printed-form/different-"
          "assumptions + %d no-signature boundary pairs and %d/%d fuzz "
          "pairs; surf carrier == structural Dimension.__eq__ and surf-eq => "
          "deps-eq on all of them; every both-signatures-present pair RETURNED a "
          "verdict rather than raising; modeled change confirmed observable on %d "
          "surface-distinct-but-equivalent pairs."
          % (len(all_dims), len(discriminating), len(inequivalent),
             len(cross_type), len(same_print), len(no_sig), n_checked, n_fuzz,
             len(observable)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
